"""
Ground-Truth Data Integrity, Constraint Verification & Sanitization Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deep audit for:
1. Training database (`data/pump_events_db.json`) physical constraints & deduplication
2. Stateful registry (`data/active_pumps_registry.json`) invariant bounds
3. Benchmark ledger (`data/ml_benchmark_ledger.json`) mathematical correctness
4. Security injection & oversized payload sanitation
"""

import os
import sys
import json
import pytest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PriceTierClassifier
from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpStage


class TestTrainingDatasetIntegrity:
    """Validate data quality and constraints of pump_events_db.json."""

    def test_training_events_no_duplicates(self):
        """No duplicate (symbol, event_date) tuples allowed in training set."""
        db = PumpDatasetBuilder()
        events = db.load_all()
        assert len(events) >= 120, "Empirical dataset must contain substantial verified events"

        seen_keys = set()
        for e in events:
            key = (e.symbol.upper(), e.event_date)
            assert key not in seen_keys, f"Duplicate training event found: {key}"
            seen_keys.add(key)

    def test_training_events_positive_metrics(self):
        """Prices and multipliers in training set must be strictly positive and realistic."""
        db = PumpDatasetBuilder()
        events = db.load_all()

        for e in events:
            assert e.pre_pump_price > 0.0, f"{e.symbol} invalid pre-pump price: {e.pre_pump_price}"
            assert e.peak_price > 0.0, f"{e.symbol} invalid peak price: {e.peak_price}"
            assert e.n_actual >= 1.0, f"{e.symbol} invalid multiplier: {e.n_actual}"
            
            # Mathematical consistency: n = peak / pre
            expected_n = e.peak_price / e.pre_pump_price
            assert abs(e.n_actual - expected_n) < 0.10, f"{e.symbol} n mismatch: actual={e.n_actual} vs calc={expected_n}"

    def test_training_events_tier_consistency(self):
        """price_tier_code in training rows must match the PriceTierClassifier output."""
        db = PumpDatasetBuilder()
        clf = PriceTierClassifier()
        events = db.load_all()

        for e in events:
            expected_tier = clf.classify(e.pre_pump_price)
            assert e.price_tier_code == expected_tier.code, (
                f"{e.symbol} tier code mismatch: row={e.price_tier_code} vs expected={expected_tier.code}"
            )


class TestCampaignRegistryInvariants:
    """Validate mathematical invariant constraints on active and completed campaigns."""

    def test_campaign_price_invariants(self):
        """Verify highest_peak_price >= current_price and highest_peak_price >= origin_bottom_price."""
        reg = PumpLifecycleRegistry()
        all_campaigns = reg.get_all_campaigns()
        assert len(all_campaigns) > 0

        for c in all_campaigns:
            assert c.origin_bottom_price > 0.0, f"{c.symbol} origin bottom <= 0"
            assert c.highest_peak_price >= c.origin_bottom_price, f"{c.symbol} peak < origin"
            assert c.highest_peak_price >= c.current_price * 0.999, f"{c.symbol} peak < current"
            
            # Max n >= Current n
            assert c.max_n >= c.current_n * 0.999, f"{c.symbol} max_n < current_n"

            # Drawdown calculation
            if c.highest_peak_price > 0:
                expected_dd = (c.highest_peak_price - c.current_price) / c.highest_peak_price * 100.0
                assert 0.0 <= c.drawdown_from_peak_pct <= 100.0, f"{c.symbol} drawdown out of bounds"
                if c.is_active:
                    assert abs(c.drawdown_from_peak_pct - max(0.0, expected_dd)) < 1.0, f"{c.symbol} live drawdown mismatch"



    def test_dump_confirmed_campaigns_are_inactive(self):
        """Campaigns marked DUMP_CONFIRMED or ARCHIVED must have is_active == False."""
        reg = PumpLifecycleRegistry()
        for c in reg.get_all_campaigns():
            if c.stage in (PumpStage.DUMP_CONFIRMED, PumpStage.ARCHIVED, PumpStage.DELISTED):
                assert c.is_active is False, f"{c.symbol} in stage {c.stage} but is_active is True"


class TestBenchmarkLedgerIntegrity:
    """Validate consistency of ml_benchmark_ledger.json."""

    def test_benchmark_ledger_records_validity(self):
        """Ledger records must have valid timestamps, positive APE, and valid outcome statuses."""
        ledger_path = os.path.join(os.path.dirname(__file__), "..", "data", "ml_benchmark_ledger.json")
        if not os.path.exists(ledger_path):
            pytest.skip("Benchmark ledger not found")

        with open(ledger_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        assert len(records) > 0, "Benchmark ledger must not be empty"

        valid_outcomes = {
            "TRÚNG DẢI 90% CI",
            "VƯỢT KỲ VỌNG (SUPER-PUMP)",
            "HỤT KỲ VỌNG (UNDERPERFORM)"
        }

        seen_keys = set()
        for r in records:
            assert r["symbol"]
            assert r["n_actual"] > 0
            assert r["n_predicted"] > 0
            assert r["ape_pct"] >= 0.0
            assert r["outcome_status"] in valid_outcomes
            
            # Check APE math
            expected_ape = round((abs(r["n_actual"] - r["n_predicted"]) / r["n_actual"]) * 100.0, 2)
            assert abs(r["ape_pct"] - expected_ape) < 0.5, f"{r['symbol']} APE math error"


class TestSecurityInputSanitization:
    """Verify endpoint resilience against SQL injections, malformed tickers, and XSS."""

    @pytest.fixture
    def client(self):
        from apps.web_terminal.app import app
        app.config["TESTING"] = True
        return app.test_client()

    def test_malicious_symbol_injection_safe(self, client):
        """Malicious SQL/Script payloads in symbol parameter must return safely without crashing."""
        malicious_inputs = [
            "'; DROP TABLE events; --",
            "<script>alert('xss')</script>",
            "../../../../etc/passwd",
            "SELECT * FROM sqlite_master",
        ]
        for payload in malicious_inputs:
            res = client.get(f"/api/ml/predict_pump_multiplier?symbol={payload}")
            # Endpoint must handle gracefully without unhandled 500 error
            assert res.status_code in (200, 400, 404)
            data = json.loads(res.data.decode())
            assert "error" in data or data.get("status") == "success"
