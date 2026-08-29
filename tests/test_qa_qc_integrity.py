"""
DeepAlpha — Comprehensive QA/QC & Data Integrity Certification Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automated quality assurance and validation suite covering:
1. Binance USD-M Futures Live API integration and numerical bounds.
2. Machine Learning Tri-Ensemble v4 Regressor mathematical consistency.
3. Multi-Month Lifecycle State Machine transitions and dump detection.
4. Zero-Static Mock/Dummy HTML Template leak scanner.
5. Benchmark Ledger Ground-Truth data fidelity.
6. Flask REST API response schema contracts.
"""

import os
import sys
import re
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner
from core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PriceTierClassifier
from core_engine.pump_multiplier_regressor import PumpMultiplierRegressor, get_pump_multiplier_regressor
from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpStage
from core_engine.self_learning_engine import AutonomousSelfLearningEngine


class TestBinanceLiveAPIIntegrity(unittest.TestCase):
    """Test 100% Live Binance Futures API metrics integration and scale."""

    def test_fetch_live_binance_metrics_btr(self):
        scanner = AutonomousSuperPumpScanner()
        metrics = scanner.fetch_live_binance_metrics("BTRUSDT")

        self.assertEqual(metrics["symbol"], "BTRUSDT")
        self.assertGreater(metrics["current_price"], 0, "Current price must be positive float from live ticker")
        self.assertGreater(metrics["base_price"], 0, "Base price must be positive float from 120D klines")
        self.assertTrue(-0.10 <= metrics["funding_rate"] <= 0.10, "Funding rate must be within realistic bounds (-10% to +10%)")
        self.assertEqual(metrics["funding_rate_pct"], round(metrics["funding_rate"] * 100.0, 4))
        self.assertGreaterEqual(metrics["vol_spike_ratio"], 1.0, "Vol spike ratio must be at least 1.0x")
        self.assertEqual(metrics["source"], "Binance USD-M Futures Realtime API")

    def test_fetch_live_binance_metrics_ake(self):
        scanner = AutonomousSuperPumpScanner()
        metrics = scanner.fetch_live_binance_metrics("AKEUSDT")

        self.assertEqual(metrics["symbol"], "AKEUSDT")
        self.assertGreater(metrics["current_price"], 0)
        self.assertGreater(metrics["base_price"], 0)
        self.assertIsInstance(metrics["vol_spike_ratio"], (int, float))


class TestMLMultiplierRegressorBounds(unittest.TestCase):
    """Test ML Mathematical Bounds and Monotonic Consistency."""

    def test_in_flight_prediction_bounds(self):
        reg = get_pump_multiplier_regressor()
        pred = reg.predict_in_flight(
            symbol="BTRUSDT",
            base_price=0.01587,
            current_price=0.1650,
            vol_spike_ratio=25.0,
            funding_rate=0.0005,
        )

        self.assertEqual(pred["symbol"], "BTRUSDT")
        self.assertEqual(pred["base_price"], 0.01587)
        self.assertEqual(pred["current_price"], 0.1650)
        self.assertGreater(pred["current_n"], 1.0)

        # Boundary checks
        self.assertTrue(pred["n_low"] <= pred["n_expected"] <= pred["n_high"], "n_expected must be within [n_low, n_high]")
        self.assertTrue(pred["target_price_low"] <= pred["target_peak_price"] <= pred["target_price_high"])
        self.assertEqual(pred["target_peak_price"], round(pred["base_price"] * pred["n_expected"], 8))
        self.assertTrue(0.0 <= pred["progress_pct"] <= 100.0)
        self.assertGreaterEqual(pred["remaining_upside_pct"], 0.0)
        self.assertNotEqual(pred["stage_recommendation"], "")


class TestLifecycleStateMachineTransitions(unittest.TestCase):
    """Test Multi-Month Pump Campaign lifecycle transition accuracy."""

    def test_dump_confirmation_threshold(self):
        tracker = PumpLifecycleRegistry()
        tracker.campaigns.clear()

        # Register test campaign
        tracker.register_new_pump(
            symbol="TESTUSDT",
            origin_bottom_price=1.0,
            current_price=10.0,
            origin_date="2026-08-01",
        )
        camp = tracker.campaigns["TESTUSDT"]
        camp.highest_peak_price = 10.0
        camp.max_n = 10.0

        # Case 1: Healthy consolidation (-20% from peak) -> HIGH_CONSOLIDATION or ACTIVE
        tracker.update_price_and_stage("TESTUSDT", current_price=8.0)
        self.assertTrue(tracker.campaigns["TESTUSDT"].is_active)
        self.assertIn(tracker.campaigns["TESTUSDT"].stage, [PumpStage.HIGH_CONSOLIDATION, PumpStage.ACTIVE_EXPANSION, PumpStage.EXHAUSTION_WARNING])

        # Case 2: Exhaustion Warning (-30% from peak) -> EXHAUSTION_WARNING
        tracker.update_price_and_stage("TESTUSDT", current_price=7.0)
        self.assertEqual(tracker.campaigns["TESTUSDT"].stage, PumpStage.EXHAUSTION_WARNING)
        self.assertTrue(tracker.campaigns["TESTUSDT"].is_active)

        # Case 3: Confirmed Dump (-50% from peak >= 45%) -> DUMP_CONFIRMED
        tracker.update_price_and_stage("TESTUSDT", current_price=5.0)
        self.assertEqual(tracker.campaigns["TESTUSDT"].stage, PumpStage.DUMP_CONFIRMED)
        self.assertFalse(tracker.campaigns["TESTUSDT"].is_active)
        self.assertIsNotNone(tracker.campaigns["TESTUSDT"].dump_date)


class TestTemplateZeroMockLeak(unittest.TestCase):
    """Scan all HTML templates to ensure NO static dummy placeholder leaks."""

    def test_no_hardcoded_dummy_placeholders_in_html(self):
        template_dir = os.path.join(os.path.dirname(__file__), "..", "apps", "web_terminal", "templates")
        self.assertTrue(os.path.exists(template_dir))

        forbidden_patterns = [
            re.compile(r"-1\.20%"),  # Old static placeholder
            re.compile(r"18\.5x"),   # Old static placeholder
            re.compile(r"\$0\.15663"), # Old static price
            re.compile(r"dummy_data", re.IGNORECASE),
        ]

        for fname in os.listdir(template_dir):
            if not fname.endswith(".html"):
                continue
            fpath = os.path.join(template_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            for pat in forbidden_patterns:
                match = pat.search(content)
                self.assertIsNone(match, f"Found forbidden dummy/placeholder pattern '{pat.pattern}' in {fname}")


class TestBenchmarkLedgerFidelity(unittest.TestCase):
    """Test 128-event ground-truth empirical dataset integrity."""

    def test_events_db_completeness(self):
        db = PumpDatasetBuilder()
        events = db.load_all()

        self.assertGreaterEqual(len(events), 120, "Empirical database must contain >= 120 verified USD-M pump events")
        
        symbols_dates = set()
        for e in events:
            key = (e.symbol, e.event_date)
            self.assertNotIn(key, symbols_dates, f"Duplicate event found: {key}")
            symbols_dates.add(key)
            self.assertGreater(e.pre_pump_price, 0, f"Invalid pre-pump price for {e.symbol}")
            self.assertGreater(e.peak_price, 0, f"Invalid peak price for {e.symbol}")
            self.assertGreaterEqual(e.n_actual, 1.0, f"Invalid n_actual for {e.symbol}")


class TestFlaskAPIContracts(unittest.TestCase):
    """Test Flask Web Terminal REST Endpoints Contract and JSON Structure."""

    def setUp(self):
        from apps.web_terminal.app import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_api_active_pump_campaigns(self):
        res = self.client.get("/api/ml/active_pump_campaigns")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode())
        self.assertEqual(data["status"], "success")
        self.assertIn("all_campaigns", data)
        self.assertGreater(len(data["all_campaigns"]), 0)

    def test_api_benchmark_ledger(self):
        res = self.client.get("/api/ml/benchmark_ledger")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode())
        self.assertEqual(data["status"], "success")
        report = data["report"]
        self.assertGreaterEqual(report["total_events"], 120)
        self.assertGreater(report["hit_rate_pct"], 0.0)
        self.assertGreater(report["avg_ape_pct"], 0.0)

    def test_api_predict_pump_multiplier(self):
        res = self.client.get("/api/ml/predict_pump_multiplier?symbol=BTRUSDT")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode())
        self.assertEqual(data["status"], "success")
        self.assertIn("prediction", data)
        self.assertIn("live_metrics", data)
        self.assertEqual(data["live_metrics"]["symbol"], "BTRUSDT")
        self.assertGreater(data["live_metrics"]["current_price"], 0)


if __name__ == "__main__":
    unittest.main()
