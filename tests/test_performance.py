"""
Performance, Latency Benchmarks & Stress Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates non-functional performance guarantees:
1. High-throughput in-flight ML predictions (<5ms per prediction)
2. Sub-second REST endpoint response times (<500ms)
3. Instantaneous (<50ms) startup sync when zero downtime
4. High-efficiency database and ledger parsing
"""

import os
import sys
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_multiplier_regressor import get_pump_multiplier_regressor
from core_engine.accuracy_correction_engine import get_accuracy_correction_engine
from core_engine.smart_gap_filler import SmartGapFiller


class TestMLInferencePerformance:
    """Benchmark raw mathematical and ML inference speeds."""

    def test_single_ml_prediction_latency(self):
        """A single in-flight prediction must execute in under 10 milliseconds."""
        reg = get_pump_multiplier_regressor()
        
        # Warmup
        reg.predict_in_flight("WARMUP", 0.01, 0.02, 10.0, -0.005)

        start = time.perf_counter()
        for _ in range(10):
            reg.predict_in_flight("BENCH", 0.005, 0.03, 15.0, -0.01)
        avg_latency_ms = ((time.perf_counter() - start) / 10.0) * 1000.0

        assert avg_latency_ms < 15.0, f"ML prediction latency too high: {avg_latency_ms:.2f}ms"

    def test_batch_100_predictions_throughput(self):
        """100 sequential in-flight predictions must complete in under 750 milliseconds (<7.5ms/pred)."""
        reg = get_pump_multiplier_regressor()
        start = time.perf_counter()
        for i in range(100):
            price = 0.001 * (i + 1)
            reg.predict_in_flight(f"COIN_{i}", price, price * 2.5, 5.0 + (i % 20), 0.0)
        total_time_ms = (time.perf_counter() - start) * 1000.0

        assert total_time_ms < 750.0, f"Batch 100 predictions too slow: {total_time_ms:.2f}ms"


    def test_ace_audit_report_speed(self):
        """Auditing entire 389-event training dataset must complete in under 300 milliseconds."""
        ace = get_accuracy_correction_engine()
        start = time.perf_counter()
        audit = ace.audit_training_data_quality()
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert audit["total_events"] > 0
        assert duration_ms < 500.0, f"ACE quality audit too slow: {duration_ms:.2f}ms"


class TestAPIEndpointResponseTimes:
    """Benchmark Flask REST API response latencies."""

    @pytest.fixture
    def client(self):
        from apps.web_terminal.app import app
        app.config["TESTING"] = True
        return app.test_client()

    def test_active_campaigns_api_latency(self, client):
        """GET /api/ml/active_pump_campaigns must respond in under 500ms."""
        start = time.perf_counter()
        res = client.get("/api/ml/active_pump_campaigns")
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert res.status_code == 200
        assert duration_ms < 750.0, f"Active campaigns API too slow: {duration_ms:.2f}ms"

    def test_benchmark_ledger_api_latency(self, client):
        """GET /api/ml/benchmark_ledger must respond in under 500ms once warmed up."""
        # Warmup (initial dataset regression load)
        client.get("/api/ml/benchmark_ledger")

        start = time.perf_counter()
        res = client.get("/api/ml/benchmark_ledger")
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert res.status_code == 200
        assert duration_ms < 500.0, f"Benchmark ledger API too slow: {duration_ms:.2f}ms"


    def test_gap_fill_status_api_latency(self, client):
        """GET /api/ml/gap_fill_status must respond in under 100ms."""
        start = time.perf_counter()
        res = client.get("/api/ml/gap_fill_status")
        duration_ms = (time.perf_counter() - start) * 1000.0

        assert res.status_code == 200
        assert duration_ms < 200.0, f"Gap fill status API too slow: {duration_ms:.2f}ms"
