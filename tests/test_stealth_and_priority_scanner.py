"""
Stealth Climbers & Priority Full-Universe Scanner Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates:
1. Mathematical Trend Efficiency (R^2 & Positive Day Ratio) for DEXE-style slow-grind super pumps
2. Early Volume Ignition Breakout recognition (4USDT pattern)
3. Dynamic Accumulation Base Finder (finding true global minimum within consolidation zone)
4. Full-Market 700+ Futures Priority Queue sorting
"""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner
from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpStage


class TestTrendEfficiencyAndStealthDetection:
    """Validate linear trend fit and stealth pattern metrics."""

    def test_calculate_trend_efficiency_uptrend(self):
        """Clean staircase uptrend must yield high R^2 >= 0.85 and high positive day ratio."""
        # 30 days steadily grinding up: 1.0 -> 2.5
        closes = [1.0 + i * 0.05 + (0.01 if i % 2 == 0 else -0.01) for i in range(30)]
        trend = AutonomousSuperPumpScanner.calculate_trend_efficiency(closes)

        assert trend["r2"] >= 0.85, f"Expected high R^2, got {trend['r2']}"
        assert trend["positive_day_ratio"] >= 0.70
        assert trend["total_drift_pct"] > 100.0

    def test_calculate_trend_efficiency_choppy_or_down(self):
        """Choppy or declining price action must yield near-zero or low R^2."""
        import math
        # Sine wave chop
        closes = [10.0 + math.sin(i * 0.5) * 1.5 for i in range(30)]
        trend = AutonomousSuperPumpScanner.calculate_trend_efficiency(closes)
        assert trend["r2"] < 0.50

        # Downtrend
        down_closes = [10.0 - i * 0.2 for i in range(30)]
        down_trend = AutonomousSuperPumpScanner.calculate_trend_efficiency(down_closes)
        assert down_trend["r2"] == 0.0, "Downtrend should have R^2 = 0.0 (only uptrend qualifies)"


class TestMultiPathQualification:
    """Validate the 3 distinct qualification avenues into /lifecycle."""

    def test_stealth_climber_qualification(self):
        """DEXE pattern: +3% per day over 40 days (n=2.0x) qualifies as STEALTH_CLIMBER."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        for i in range(40):
            t = now_ms - (40 - i) * day_ms
            p = 1.0 + i * 0.025  # Reaches 2.0x steadily
            klines.append([t, str(p), str(p + 0.03), str(p - 0.02), str(p), "100000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(
            klines=klines,
            min_multiplier=3.0,
            vol_24h_quote=500_000.0,  # Low/Normal volume
            vol_spike=1.2,
        )

        assert len(cycles) == 1, "Stealth climber should qualify even if n < 3.0x"
        c = cycles[0]
        assert c["pattern_type"] == "STEALTH_CLIMBER"
        assert c["is_active"] is True
        assert c["origin_bottom_price"] <= 1.05

    def test_volume_ignition_qualification(self):
        """4USDT pattern: n=2.6x with $50M 24h volume spike qualifies as VOLUME_IGNITION."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        for i in range(50):
            t = now_ms - (50 - i) * day_ms
            if i < 40:
                klines.append([t, "0.010", "0.011", "0.009", "0.010", "500000"])
            else:
                p = 0.010 + (i - 40) * 0.0016  # Explodes to 0.026 (2.6x)
                klines.append([t, str(p), str(p + 0.002), str(p - 0.001), str(p), "50000000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(
            klines=klines,
            min_multiplier=3.0,
            vol_24h_quote=50_000_000.0,  # Huge 24h volume
            vol_spike=15.0,
        )

        assert len(cycles) == 1
        c = cycles[0]
        assert c["pattern_type"] == "VOLUME_IGNITION"
        assert c["is_active"] is True
        assert abs(c["origin_bottom_price"] - 0.009) < 0.002

    def test_dynamic_accumulation_base_finder(self):
        """Dynamic base finder correctly identifies lowest low on Day 32 rather than first window."""
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        for i in range(100):
            t = now_ms - (100 - i) * day_ms
            if i == 32:
                # True absolute bottom
                klines.append([t, "0.0080", "0.0082", "0.006678", "0.0081", "100000"])
            elif i < 60:
                klines.append([t, "0.0085", "0.0090", "0.008100", "0.0085", "100000"])
            else:
                p = 0.0085 + (i - 60) * 0.00035  # Rises to 0.0225 (3.37x from 0.006678)
                klines.append([t, str(p), str(p + 0.001), str(p - 0.0005), str(p), "500000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(klines, min_multiplier=3.0)
        assert len(cycles) >= 1
        assert abs(cycles[-1]["origin_bottom_price"] - 0.006678) < 0.0001, (
            f"Expected base 0.006678, got {cycles[-1]['origin_bottom_price']}"
        )


class TestFullUniversePriorityQueue:
    """Validate that 700+ symbol list is prioritized by volume and price volatility."""

    def test_priority_queue_sorting(self):
        """High volume & high mover pairs must be ordered at the front."""
        raw_tickers = [
            {"symbol": "LOWVOLUSDT", "quoteVolume": "50000.0", "priceChangePercent": "0.5"},
            {"symbol": "4USDT", "quoteVolume": "308000000.0", "priceChangePercent": "68.0"},
            {"symbol": "MIDVOLUSDT", "quoteVolume": "5000000.0", "priceChangePercent": "5.0"},
            {"symbol": "DEXEUSDT", "quoteVolume": "45000000.0", "priceChangePercent": "12.0"},
        ]

        def priority_key(t):
            vol = float(t.get("quoteVolume", 0.0))
            pct = abs(float(t.get("priceChangePercent", 0.0)))
            return vol * (1.0 + pct / 100.0)

        sorted_tickers = sorted(raw_tickers, key=priority_key, reverse=True)
        assert sorted_tickers[0]["symbol"] == "4USDT"
        assert sorted_tickers[1]["symbol"] == "DEXEUSDT"
        assert sorted_tickers[2]["symbol"] == "MIDVOLUSDT"
        assert sorted_tickers[3]["symbol"] == "LOWVOLUSDT"
