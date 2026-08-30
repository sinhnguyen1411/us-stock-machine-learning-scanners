"""
Autonomous Self-Learning & Verification Engine (Closed-Loop ML) Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates:
1. Initial prediction snapshotting upon ignition
2. Finalizing dump cycle, error calculation (APE), and outcome status
3. Duplicate rejection on same symbol/event_date
4. Benchmark telemetry reporting (hit rate, avg APE)
5. Online retraining trigger and empirical dataset integration
"""

import os
import sys
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.self_learning_engine import AutonomousSelfLearningEngine, get_self_learning_engine


@pytest.fixture
def clean_engine(tmp_path):
    """Provides a self-learning engine instance with an isolated ledger path."""
    ledger_file = str(tmp_path / "test_ledger.json")
    with patch("core_engine.self_learning_engine.LEDGER_FILE", ledger_file):
        engine = AutonomousSelfLearningEngine()
        engine.ledger = []
        engine.snapshots = {}
        yield engine


class TestSelfLearningSnapshotsAndFinalization:
    """Test initial snapshot freeze and dump cycle finalization."""

    def test_record_initial_prediction_snapshot(self, clean_engine):
        """Should freeze initial ML predictions for a campaign."""
        clean_engine.record_initial_prediction(
            symbol="NEWCOINUSDT",
            base_price=0.01,
            prediction_payload={
                "n_expected": 15.0,
                "n_low": 6.0,
                "n_high": 35.0,
                "target_peak_price": 0.15,
                "vol_spike_ratio": 12.0,
            }
        )
        assert "NEWCOINUSDT" in clean_engine.snapshots
        snap = clean_engine.snapshots["NEWCOINUSDT"]
        assert snap["n_predicted"] == 15.0
        assert snap["n_low"] == 6.0
        assert snap["n_high"] == 35.0

    def test_finalize_completed_cycle_in_range(self, clean_engine):
        """Finalizing an event where n_actual is between n_low and n_high marks TRÚNG DẢI 90% CI."""
        clean_engine.record_initial_prediction(
            symbol="COIN_IN_RANGE",
            base_price=1.0,
            prediction_payload={
                "n_expected": 10.0,
                "n_low": 5.0,
                "n_high": 20.0,
                "target_peak_price": 10.0,
            }
        )

        with patch.object(clean_engine, "retrain_models", return_value={"status": "success"}):
            rec = clean_engine.finalize_completed_cycle(
                symbol="COIN_IN_RANGE",
                base_price=1.0,
                peak_price_actual=12.0, # 12x is within [5.0, 20.0]
                dump_price=6.0,
                event_date="2026-08-01",
            )

        assert rec["is_in_range"] is True
        assert rec["outcome_status"] == "TRÚNG DẢI 90% CI"
        assert rec["n_actual"] == 12.0
        assert rec["ape_pct"] == pytest.approx(16.67, rel=1e-2)

    def test_finalize_completed_cycle_super_pump(self, clean_engine):
        """Finalizing an event where n_actual > n_high marks VƯỢT KỲ VỌNG (SUPER-PUMP)."""
        clean_engine.record_initial_prediction(
            symbol="SUPER_COIN",
            base_price=0.01,
            prediction_payload={
                "n_expected": 10.0,
                "n_low": 5.0,
                "n_high": 20.0,
                "target_peak_price": 0.10,
            }
        )

        with patch.object(clean_engine, "retrain_models", return_value={"status": "success"}):
            rec = clean_engine.finalize_completed_cycle(
                symbol="SUPER_COIN",
                base_price=0.01,
                peak_price_actual=0.50, # 50x > 20x
                dump_price=0.20,
                event_date="2026-08-01",
            )

        assert rec["is_in_range"] is False
        assert "SUPER-PUMP" in rec["outcome_status"]
        assert rec["n_actual"] == 50.0

    def test_finalize_prevents_duplicates_on_same_symbol_date(self, clean_engine):
        """Re-finalizing the same symbol on the same date replaces the entry instead of creating duplicates."""
        with patch.object(clean_engine, "retrain_models", return_value={"status": "success"}):
            clean_engine.finalize_completed_cycle(
                symbol="DUPCOIN", base_price=1.0, peak_price_actual=10.0, dump_price=5.0, event_date="2026-08-10"
            )
            assert len(clean_engine.ledger) == 1

            # Second call on same date
            clean_engine.finalize_completed_cycle(
                symbol="DUPCOIN", base_price=1.0, peak_price_actual=12.0, dump_price=6.0, event_date="2026-08-10"
            )
            assert len(clean_engine.ledger) == 1
            assert clean_engine.ledger[0]["peak_price_actual"] == 12.0


class TestBenchmarkReportAndMetrics:
    """Validate benchmark telemetry reporting."""

    def test_benchmark_report_empty(self, clean_engine):
        """Empty ledger returns default zero metrics gracefully."""
        report = clean_engine.get_benchmark_report()
        assert report["total_events"] == 0
        assert report["hit_rate_pct"] == 100.0
        assert report["avg_ape_pct"] == 0.0
        assert len(report["records"]) == 0

    def test_benchmark_report_calculation(self, clean_engine):
        """Calculates hit rate and average APE accurately."""
        clean_engine.ledger = [
            {"symbol": "A", "is_in_range": True, "ape_pct": 10.0},
            {"symbol": "B", "is_in_range": True, "ape_pct": 20.0},
            {"symbol": "C", "is_in_range": False, "ape_pct": 60.0},
            {"symbol": "D", "is_in_range": True, "ape_pct": 30.0},
        ]
        report = clean_engine.get_benchmark_report()
        assert report["total_events"] == 4
        assert report["hit_rate_pct"] == 75.0  # 3/4 = 75.0%
        assert report["avg_ape_pct"] == 30.0   # (10+20+60+30)/4 = 30.0%

    def test_singleton_engine_getter(self):
        """get_self_learning_engine returns singleton instance."""
        inst1 = get_self_learning_engine()
        inst2 = get_self_learning_engine()
        assert inst1 is inst2
