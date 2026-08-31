"""
QA Test Suite: Atomic Persistence, Thread-Safe Concurrency, and Self-Healing Resilience
"""

import os
import sys
import json
import time
import shutil
import tempfile
import threading
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PumpEvent
from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage



class TestAtomicPersistenceAndConcurrency:
    """Validate thread-safety and atomic disk writes across high-frequency read/write operations."""

    def test_concurrent_multithreaded_atomic_writes(self):
        """50 concurrent threads writing to the database never cause corruption or partial writes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = os.path.join(tmpdir, "test_events.json")
            builder = PumpDatasetBuilder(db_path=test_db_path)

            def worker_write(thread_id):
                for i in range(10):
                    ev = PumpEvent(
                        symbol=f"COIN_{thread_id}_{i}USDT",
                        event_date="2026-08-31",
                        pre_pump_price=1.0 + thread_id,
                        peak_price=5.0 + thread_id,
                        n_actual=5.0,
                    )
                    builder.add_event(ev, deduplicate=False)
                    time.sleep(0.001)

            threads = [threading.Thread(target=worker_write, args=(t,)) for t in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Verify file integrity and JSON validness
            assert os.path.exists(test_db_path)
            with open(test_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data.get("events", [])) == 200

    def test_self_healing_from_corrupted_truncated_json(self):
        """Simulate unexpected power loss causing truncated JSON syntax error, verify self-healing recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db_path = os.path.join(tmpdir, "test_corrupt.json")
            builder = PumpDatasetBuilder(db_path=test_db_path)

            # Seed 5 valid events
            events = [
                PumpEvent(symbol=f"TEST_{i}USDT", event_date="2026-08-31", pre_pump_price=1.0, peak_price=3.0, n_actual=3.0)
                for i in range(5)
            ]
            builder.save_all(events)

            # Intentionally corrupt the file by appending broken truncated JSON
            with open(test_db_path, "a", encoding="utf-8") as f:
                f.write("\n    : 4.9614450499054845,\n    }\n  ]\n}")

            # Now load_all() must self-heal via regex or backup
            recovered = builder.load_all()
            assert len(recovered) == 5
            assert all(isinstance(e, PumpEvent) for e in recovered)

            # Verify file was cleaned up and is now valid JSON
            with open(test_db_path, "r", encoding="utf-8") as f:
                clean_data = json.load(f)
            assert len(clean_data.get("events", [])) == 5

    def test_registry_atomic_persistence_and_backup_fallback(self):
        """Verify that PumpLifecycleRegistry maintains .bak and recovers on crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reg_path = os.path.join(tmpdir, "active_pumps.json")
            registry = PumpLifecycleRegistry(file_path=reg_path)

            # Add sample campaign
            c = PumpCampaign(
                campaign_id="BTRUSDT_2026-08-01",
                symbol="BTRUSDT",
                origin_date="2026-08-01",
                origin_bottom_price=0.01,
                highest_peak_price=0.14,
                highest_peak_date="2026-08-05",
                current_price=0.10,
                current_n=10.0,
                max_n=14.0,
                stage=PumpStage.HIGH_CONSOLIDATION,
                is_active=True
            )

            registry.campaigns[c.campaign_id] = c
            registry.save(update_heartbeat=False)
            registry.save(update_heartbeat=False)

            assert os.path.exists(reg_path)
            assert os.path.exists(f"{reg_path}.bak")


            # Corrupt main file
            with open(reg_path, "w", encoding="utf-8") as f:
                f.write("BROKEN_CORRUPT_DATA{{{{")

            # Reload
            new_reg = PumpLifecycleRegistry(file_path=reg_path)
            rec = new_reg.get_campaign("BTRUSDT_2026-08-01")
            assert rec is not None
            assert rec.symbol == "BTRUSDT"
            assert rec.highest_peak_price == 0.14
            assert rec.is_active is True


class TestScannerTelemetryAndFastBootstrap:
    """Validate real-time scanner telemetry and fast bootstrap capabilities."""

    def test_scanner_telemetry_payload_contract(self):
        """Ensure get_sync_status returns complete telemetry schema for frontend."""
        from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner
        scanner = AutonomousSuperPumpScanner()
        status = scanner.get_sync_status()

        assert "status" in status
        assert "is_syncing" in status
        assert "progress_pct" in status
        assert "scanned_symbols" in status
        assert "total_symbols" in status
        assert "active_campaigns_count" in status
        assert isinstance(status["is_syncing"], bool)
        assert isinstance(status["progress_pct"], (int, float))

    def test_sync_status_api_endpoint(self):
        """Test Flask /api/ml/sync_status HTTP route."""
        from apps.web_terminal.app import app
        client = app.test_client()
        response = client.get("/api/ml/sync_status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get("status") == "success"
        assert "sync" in data
        assert "progress_pct" in data["sync"]


