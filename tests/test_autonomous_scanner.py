"""
Autonomous Super-Pump Discovery Engine Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates:
1. Live Binance metric fetching (price, funding rate, volume spike)
2. Macro cycle discovery from 120D klines
3. Stage classification during cycle analysis
4. Stablecoin and fiat pair filtering
5. Market scan pacing and registry integration
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner
from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpStage


@pytest.fixture
def mock_scanner(tmp_path):
    """Provides an AutonomousSuperPumpScanner with an isolated temporary registry."""
    reg_file = str(tmp_path / "test_reg.json")
    with open(reg_file, "w", encoding="utf-8") as f:
        json.dump({"updated_at": "", "campaigns": {}}, f)
    reg = PumpLifecycleRegistry(file_path=reg_file)
    reg.campaigns = {}
    return AutonomousSuperPumpScanner(registry=reg, min_multiplier=3.0)


class TestAutonomousScannerMetrics:
    """Test metric extraction and live data normalization."""

    def test_fetch_live_binance_metrics_mocked(self, mock_scanner):
        """Validates payload schema when querying live endpoints."""
        mock_ticker_resp = json.dumps({"lastPrice": "0.0150", "quoteVolume": "50000000.0"}).encode()
        mock_fund_resp = json.dumps({"lastFundingRate": "-0.0025"}).encode()
        
        # Mock 20 daily candles
        mock_klines = []
        for i in range(20):
            mock_klines.append([
                1700000000000 + i * 86400000,
                "0.001", "0.020", "0.001", "0.015", "1000",
                1700086400000 + i * 86400000, "10000000", 500
            ])
        mock_klines_resp = json.dumps(mock_klines).encode()

        with patch("urllib.request.urlopen") as mock_url:
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.read.side_effect = [mock_ticker_resp, mock_fund_resp, mock_klines_resp]
            mock_url.return_value = mock_conn

            metrics = mock_scanner.fetch_live_binance_metrics("TESTUSDT")

        assert metrics["symbol"] == "TESTUSDT"
        assert metrics["current_price"] == 0.0150
        assert metrics["funding_rate"] == -0.0025
        assert metrics["funding_rate_pct"] == -0.25
        assert metrics["base_price"] > 0
        assert metrics["vol_spike_ratio"] >= 1.0


class TestMacroCycleAnalysis:
    """Test 120-day macro cycle discovery and stage classification."""

    def test_scan_symbol_cycle_discovers_active_pump(self, mock_scanner):
        """Detects a 10x pump that is currently in ACTIVE_EXPANSION."""
        mock_klines = []
        for i in range(30):
            # bottom at index 5 ($0.01), peak at index 28 ($0.10, 10x), close at $0.095 (dd < 10%)
            low = 0.01 if i == 5 else 0.05
            high = 0.10 if i == 28 else 0.08
            close = 0.095 if i == 29 else 0.05
            mock_klines.append([
                1700000000000 + i * 86400000,
                "0.05", str(high), str(low), str(close), "1000",
                1700086400000 + i * 86400000, "5000000", 500
            ])

        with patch("urllib.request.urlopen") as mock_url:
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.read.return_value = json.dumps(mock_klines).encode()
            mock_url.return_value = mock_conn

            res = mock_scanner.scan_symbol_cycle("BOOMUSDT")

        assert res is not None
        assert res["symbol"] == "BOOMUSDT"
        assert res["origin_bottom_price"] == 0.01
        assert res["highest_peak_price"] == 0.10
        assert res["peak_n"] == 10.0
        assert res["stage"] in (PumpStage.ACTIVE_EXPANSION, PumpStage.HIGH_CONSOLIDATION)
        assert res["is_active"] is True

    def test_scan_symbol_cycle_detects_dump(self, mock_scanner):
        """Detects a 15x pump that has crashed >45% from peak and classifies as DUMP_CONFIRMED."""
        mock_klines = []
        for i in range(30):
            low = 0.01 if i == 2 else 0.05
            high = 0.15 if i == 15 else 0.06
            # Crash close to 0.04 (drawdown from 0.15 is -73% >= 45%)
            close = 0.04 if i == 29 else 0.05
            mock_klines.append([
                1700000000000 + i * 86400000,
                "0.05", str(high), str(low), str(close), "1000",
                1700086400000 + i * 86400000, "5000000", 500
            ])

        with patch("urllib.request.urlopen") as mock_url:
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.read.return_value = json.dumps(mock_klines).encode()
            mock_url.return_value = mock_conn

            res = mock_scanner.scan_symbol_cycle("CRASHUSDT")

        assert res is not None
        assert res["peak_n"] == 15.0
        assert res["drawdown_pct"] >= 45.0
        assert res["stage"] == PumpStage.DUMP_CONFIRMED
        assert res["is_active"] is False
