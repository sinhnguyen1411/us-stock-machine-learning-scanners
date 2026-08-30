"""
SQLite DatabaseStorage Unit Tests (Offline-Tolerant Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates:
1. Automatic table creation and indexing
2. WAL (Write-Ahead Logging) concurrency mode
3. Checkpoint logging and persistence
4. Gap fill log serialization and retrieval
5. Campaign snapshot recording
6. Thread-safe concurrent writing without database locked errors
"""

import os
import sys
import tempfile
import json
import sqlite3
import threading
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.db_storage import DatabaseStorage, get_db_storage
from core_engine.pump_lifecycle_tracker import PumpCampaign, PumpStage


@pytest.fixture
def temp_db(tmp_path):
    """Provides a fresh isolated SQLite DatabaseStorage instance."""
    db_file = str(tmp_path / "test_deepalpha.db")
    storage = DatabaseStorage(db_path=db_file)
    yield storage


class TestDatabaseStorageSchemaAndMode:
    """Test schema initialization and SQLite WAL mode."""

    def test_db_creates_tables_and_indexes(self, temp_db):
        """Should create system_checkpoints, campaign_snapshots, gap_fill_logs tables and indexes."""
        with temp_db._get_connection() as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row["name"] for row in cur.fetchall()}
            assert "system_checkpoints" in tables
            assert "campaign_snapshots" in tables
            assert "gap_fill_logs" in tables

            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index';")
            indexes = {row["name"] for row in cur.fetchall()}
            assert "idx_snap_symbol_time" in indexes
            assert "idx_chk_type_time" in indexes

    def test_wal_journal_mode_enabled(self, temp_db):
        """SQLite connections must operate in WAL journal mode."""
        with temp_db._get_connection() as conn:
            cur = conn.execute("PRAGMA journal_mode;")
            mode = cur.fetchone()[0]
            assert mode.lower() == "wal"


class TestDatabaseStorageOperations:
    """Test logging and retrieval operations."""

    def test_log_checkpoint_and_persistence(self, temp_db):
        """Logs a checkpoint and verifies row count and columns."""
        temp_db.log_checkpoint(
            checkpoint_type="HEARTBEAT",
            details={"active_count": 5, "cpu_pct": 12.5},
            downtime_sec=120.0
        )
        with temp_db._get_connection() as conn:
            cur = conn.execute("SELECT * FROM system_checkpoints WHERE checkpoint_type='HEARTBEAT';")
            row = cur.fetchone()
            assert row is not None
            assert row["checkpoint_type"] == "HEARTBEAT"
            assert row["downtime_seconds"] == 120.0
            data = json.loads(row["details_json"])
            assert data["active_count"] == 5

    def test_log_gap_fill_result_and_query_latest(self, temp_db):
        """Logs gap fill summaries and queries the latest record."""
        assert temp_db.get_latest_gap_fill_summary() is None

        summary_1 = {
            "downtime_hours": 2.5,
            "campaigns_scanned": 10,
            "peaks_updated": [{"symbol": "BTR", "new_peak": 0.5}],
            "dumps_detected": [],
            "status": "SYNCED"
        }
        temp_db.log_gap_fill_result(summary_1)

        latest = temp_db.get_latest_gap_fill_summary()
        assert latest is not None
        assert latest["downtime_hours"] == 2.5
        assert latest["peaks_updated"][0]["symbol"] == "BTR"

    def test_record_campaign_snapshot(self, temp_db):
        """Records an hourly snapshot of a PumpCampaign."""
        camp = PumpCampaign(
            symbol="SNAPUSDT",
            origin_date="2026-08-01",
            origin_bottom_price=0.01,
            highest_peak_price=0.25,
            highest_peak_date="2026-08-15",
            current_price=0.20,
            current_n=20.0,
            max_n=25.0,
            stage=PumpStage.ACTIVE_EXPANSION,
            is_active=True,
            notes="Snapshot test note"
        )
        temp_db.record_campaign_snapshot(camp)

        with temp_db._get_connection() as conn:
            cur = conn.execute("SELECT * FROM campaign_snapshots WHERE symbol='SNAPUSDT';")
            row = cur.fetchone()
            assert row is not None
            assert row["symbol"] == "SNAPUSDT"
            assert row["highest_peak_price"] == 0.25
            assert row["current_n"] == 20.0
            assert row["stage"] == PumpStage.ACTIVE_EXPANSION
            assert row["is_active"] == 1

    def test_concurrent_writes_thread_safety(self, temp_db):
        """Multiple concurrent threads inserting records must not raise database locked error."""
        errors = []

        def worker(thread_id):
            try:
                for i in range(25):
                    temp_db.log_checkpoint(
                        checkpoint_type=f"THREAD_{thread_id}",
                        details={"iteration": i},
                        downtime_sec=float(i)
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors encountered: {errors}"
        with temp_db._get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM system_checkpoints;")
            count = cur.fetchone()[0]
            assert count == 125  # 5 threads * 25 records

    def test_singleton_get_db_storage(self):
        """get_db_storage returns valid singleton instance."""
        inst1 = get_db_storage()
        inst2 = get_db_storage()
        assert inst1 is inst2
