"""
QA Phase 1: Discovery & Extreme Market Data Edge Cases Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies:
1. Nano-decimal token precision (SHIB/PEPE scale 10^-8) without float underflow.
2. New listings (<15 candles) handling without exceptions or crashes.
3. Flash-wick resilience (intraday spike down vs daily close confirmation).
4. Multi-peak / Double-top expansion waves without early cutoff.
5. Corrupted, NaN, negative, and malformed kline sanitization.
6. Zero-volatility flatlined asset exclusion.
"""

import os
import sys
import time
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner
from core_engine.pump_lifecycle_tracker import PumpStage


class TestNanoDecimalPrecision:
    """Test tokens priced at 10^-8 to 10^-5 scale."""

    def test_nano_decimal_tokens_no_precision_loss(self):
        """Micro-cap meme token with base $0.000000012345 pumping 50x."""
        base = 0.000000012345
        peak = 0.000000617250  # Exactly 50.0x
        curr = 0.000000555525  # 45.0x, -10% from peak

        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        for i in range(40):
            t = now_ms - (40 - i) * day_ms
            if i < 10:
                klines.append([t, f"{base:.12f}", f"{base*1.1:.12f}", f"{base:.12f}", f"{base:.12f}", "10000"])
            elif i < 30:
                p = base + (i - 10) * ((peak - base) / 20)
                klines.append([t, f"{p:.12f}", f"{p*1.05:.12f}", f"{p*0.95:.12f}", f"{p:.12f}", "50000"])
            else:
                klines.append([t, f"{curr:.12f}", f"{curr*1.02:.12f}", f"{curr*0.98:.12f}", f"{curr:.12f}", "60000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(klines, min_multiplier=3.0)
        assert len(cycles) == 1, "Nano-decimal token must be detected"
        c = cycles[0]
        expected_bottom = base * 0.95
        assert abs(c["origin_bottom_price"] - expected_bottom) < 1e-12
        assert abs(c["peak_n"] - round(peak / expected_bottom, 2)) < 0.5
        assert abs(c["current_n"] - round(curr / expected_bottom, 2)) < 0.5
        assert c["is_active"] is True
        assert c["drawdown_pct"] <= 15.0



class TestNewListingsAndShortHistory:
    """Test tokens with incomplete or very short trading histories."""

    def test_new_listings_under_15_candles_safe(self):
        """Tokens with 0, 3, or 10 candles must return empty list safely without crash."""
        assert AutonomousSuperPumpScanner.segment_macro_cycles([]) == []
        assert AutonomousSuperPumpScanner.segment_macro_cycles(None) == []

        now_ms = int(time.time() * 1000)
        short_klines = [[now_ms - i * 86400000, "1.0", "5.0", "0.5", "4.0", "1000"] for i in range(5)]
        assert AutonomousSuperPumpScanner.segment_macro_cycles(short_klines) == []

    def test_scan_symbol_cycle_short_history_returns_none(self):
        """scan_symbol_cycle with short API response returns None gracefully."""
        scanner = AutonomousSuperPumpScanner()
        with patch("urllib.request.urlopen") as mock_url:
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.read.return_value = json.dumps([[1700000000000, "1.0", "2.0", "0.5", "1.5", "1000"]]).encode()
            mock_url.return_value = mock_conn

            res = scanner.scan_symbol_cycle("NEWCOINUSDT")
            assert res is None


class TestFlashWickVsDailyCloseDump:
    """Test that a 1-day intraday wick down does not prematurely kill a multi-month bull run."""

    def test_flash_wick_does_not_falsely_terminate_active_wave(self):
        """A single day where low dips -50% but close recovers to -10% must remain ACTIVE."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        # Days 0-20: Base $1.0 -> Peak $10.0
        for i in range(20):
            t = now_ms - (50 - i) * day_ms
            p = 1.0 + i * 0.45
            klines.append([t, str(p), str(p + 0.5), str(p - 0.2), str(p), "10000"])

        # Day 20: Flash wick day (Peak $10.0, Low $4.5 (-55%), but Close $9.0 (-10%))
        t_wick = now_ms - (50 - 20) * day_ms
        klines.append([t_wick, "9.5", "10.0", "4.5", "9.0", "100000"])

        # Days 21-40: Resumes expansion to $15.0
        for i in range(21, 40):
            t = now_ms - (50 - i) * day_ms
            p = 9.0 + (i - 20) * 0.3
            klines.append([t, str(p), str(p + 0.4), str(p - 0.2), str(p), "20000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(klines, min_multiplier=3.0)
        assert len(cycles) == 1, "Should maintain single active expansion cycle"
        c = cycles[0]
        assert c["is_active"] is True
        assert c["highest_peak_price"] >= 14.5
        assert c["peak_n"] >= 14.0


class TestMultiPeakAndDoubleTopExpansion:
    """Test multi-phase expansion within a macro super wave."""

    def test_double_top_and_escalation_wave(self):
        """Wave hits $5.0 (5x), pulls back -25% (to $3.75), then surges to $15.0 (15x)."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        # Base: $1.0
        for i in range(10):
            t = now_ms - (60 - i) * day_ms
            klines.append([t, "1.0", "1.1", "0.95", "1.0", "5000"])

        # Run 1: $1.0 -> $5.0
        for i in range(10, 25):
            t = now_ms - (60 - i) * day_ms
            p = 1.0 + (i - 10) * 0.266
            klines.append([t, str(p), str(p + 0.2), str(p - 0.1), str(p), "20000"])

        # Consolidation: $5.0 -> $3.75 (-25% drawdown, not a dump)
        for i in range(25, 35):
            t = now_ms - (60 - i) * day_ms
            klines.append([t, "4.0", "4.2", "3.75", "3.9", "8000"])

        # Run 2: $3.9 -> $15.0 (15x)
        for i in range(35, 60):
            t = now_ms - (60 - i) * day_ms
            p = 3.9 + (i - 35) * 0.444
            klines.append([t, str(p), str(p + 0.5), str(p - 0.2), str(p), "50000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(klines, min_multiplier=3.0)
        assert len(cycles) == 1
        c = cycles[0]
        assert c["is_active"] is True
        assert c["peak_n"] >= 14.5
        assert abs(c["origin_bottom_price"] - 0.95) < 0.1


class TestMalformedAndCorruptedKlines:
    """Test system resilience against corrupted, string NaN, negative prices, and bad types."""

    def test_corrupted_candles_sanitized_safely(self):
        """Mixed valid candles with corrupted None/NaN/Zero rows."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        bad_klines = []
        for i in range(50):
            t = now_ms - (50 - i) * day_ms
            if i % 7 == 0:
                # Corrupted row
                bad_klines.append([t, "None", "NaN", "0.0", "-1.0", None])
            elif i % 11 == 0:
                bad_klines.append([t])  # Short array
            else:
                p = 1.0 + i * 0.1  # Rises to 5.0
                bad_klines.append([t, str(p), str(p + 0.2), str(p - 0.1), str(p), "10000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(bad_klines, min_multiplier=3.0)
        assert len(cycles) == 1, "Should filter corrupted rows and detect valid wave"
        assert cycles[0]["is_active"] is True


class TestZeroVolatilityFlatlineAsset:
    """Test flatlined zero-volatility assets like stablecoins."""

    def test_flatline_asset_rejected(self):
        """Asset with price $1.0000 for 120 days must produce 0 cycles."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        flat_klines = [
            [now_ms - i * day_ms, "1.0000", "1.0001", "0.9999", "1.0000", "500000"]
            for i in range(120)
        ]
        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(flat_klines, min_multiplier=3.0)
        assert len(cycles) == 0
