"""
Unit tests for Pre-Pump 4-Pillar Quantitative Engine & Phase Detection
"""

import sys
import unittest
from pathlib import Path

# Add packages directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from core_engine import calculate_pre_pump_index


class TestPrePumpDetector(unittest.TestCase):

    def test_ignition_triggered_phase(self):
        """Test that Ignition Triggered phase is accurately detected with vol spike 4.2x."""
        res = calculate_pre_pump_index(
            symbol="TUTUSDT",
            current_price=0.035,
            funding_rate=-0.001,  # -0.1%
            open_interest=2_000_000,
            quote_vol_24h=5_000_000,
            pct_24h=4.5,
            range_1h_avg=3.2,
            vol_spike_1h=4.2,
            taker_buy_1h=56.5,
        )
        self.assertEqual(res["phase"], "IGNITION_TRIGGERED")
        self.assertGreaterEqual(res["pre_pump_score"], 55.0)
        self.assertEqual(res["breakdown"]["ignition_score"], 25.0)
        self.assertEqual(res["breakdown"]["coiling_score"], 20.0)

    def test_pre_ignition_coiling_phase(self):
        """Test that ultra-tight compression (e.g. BMT 1.19%) triggers PRE_IGNITION_COILING."""
        res = calculate_pre_pump_index(
            symbol="BMTUSDT",
            current_price=0.012,
            funding_rate=0.0001,
            open_interest=500_000,
            quote_vol_24h=1_000_000,
            pct_24h=0.8,
            range_1h_avg=1.19,  # Ultra-compression
            vol_spike_1h=0.9,
            taker_buy_1h=50.0,
        )
        self.assertEqual(res["phase"], "PRE_IGNITION_COILING")
        self.assertEqual(res["breakdown"]["coiling_score"], 25.0)

    def test_extreme_short_squeeze_phase(self):
        """Test that negative funding <= -0.5% triggers SQUEEZE_EXPANSION with high leverage."""
        res = calculate_pre_pump_index(
            symbol="BANKUSDT",
            current_price=0.55,
            funding_rate=-0.012,  # -1.2%
            open_interest=15_000_000,
            quote_vol_24h=6_000_000,
            pct_24h=35.0,
            range_1h_avg=7.5,
            vol_spike_1h=5.5,
            taker_buy_1h=62.0,
            depth_ratio=2.6,
        )
        self.assertEqual(res["phase"], "SQUEEZE_EXPANSION")
        self.assertGreaterEqual(res["pre_pump_score"], 75.0)
        self.assertEqual(res["breakdown"]["funding_score"], 26.0)
        self.assertEqual(res["breakdown"]["leverage_score"], 20.0)


if __name__ == "__main__":
    unittest.main()
