"""
SQLite Local Persistence & Checkpoint Storage (Offline-Tolerant Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides durable, crash-resilient ACID storage for DeepAlpha lifecycle tracker,
telemetry checkpoints, hourly snapshots, and ML retraining logs.

Database File: data/deepalpha_lifecycle.db
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
_DB_PATH = os.path.join(_DATA_DIR, "deepalpha_lifecycle.db")
os.makedirs(_DATA_DIR, exist_ok=True)


class DatabaseStorage:
    """
    Thread-safe SQLite manager for state checkpoints, klines ledger, and campaign history.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")  # High concurrency & write-ahead logging
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes."""
        with self._get_connection() as conn:
            # 1. System Checkpoints
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checkpoint_type TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    downtime_seconds REAL DEFAULT 0,
                    details_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Campaign Historical Snapshots
            conn.execute("""
                CREATE TABLE IF NOT EXISTS campaign_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    snapshot_time_utc TEXT NOT NULL,
                    origin_bottom_price REAL NOT NULL,
                    highest_peak_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    current_n REAL NOT NULL,
                    max_n REAL NOT NULL,
                    drawdown_from_peak_pct REAL NOT NULL,
                    stage TEXT NOT NULL,
                    is_active INTEGER NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Gap Fill Sync Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gap_fill_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_time_utc TEXT NOT NULL,
                    downtime_hours REAL NOT NULL,
                    campaigns_scanned INTEGER NOT NULL,
                    peaks_updated_count INTEGER NOT NULL,
                    dumps_detected_count INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Indexes for ultra-fast lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snap_symbol_time ON campaign_snapshots(symbol, snapshot_time_utc);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chk_type_time ON system_checkpoints(checkpoint_type, timestamp_utc);")
            conn.commit()

    def log_checkpoint(self, checkpoint_type: str, details: Optional[Dict[str, Any]] = None, downtime_sec: float = 0.0) -> None:
        """Logs a system heartbeat or shutdown checkpoint."""
        now_utc = datetime.now(timezone.utc).isoformat()
        details_str = json.dumps(details or {}, ensure_ascii=False)
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_checkpoints (checkpoint_type, timestamp_utc, downtime_seconds, details_json)
                    VALUES (?, ?, ?, ?);
                """, (checkpoint_type, now_utc, downtime_sec, details_str))
                conn.commit()
        except Exception as e:
            logger.debug(f"[DB] Error logging checkpoint: {e}")

    def log_gap_fill_result(self, summary: Dict[str, Any]) -> None:
        """Logs the result of a startup gap fill synchronization."""
        now_utc = datetime.now(timezone.utc).isoformat()
        summary_str = json.dumps(summary, ensure_ascii=False)
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO gap_fill_logs (sync_time_utc, downtime_hours, campaigns_scanned, peaks_updated_count, dumps_detected_count, summary_json)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (
                    now_utc,
                    summary.get("downtime_hours", 0.0),
                    summary.get("campaigns_scanned", 0),
                    len(summary.get("peaks_updated", [])),
                    len(summary.get("dumps_detected", [])),
                    summary_str
                ))
                conn.commit()
        except Exception as e:
            logger.debug(f"[DB] Error logging gap fill result: {e}")

    def record_campaign_snapshot(self, campaign: Any) -> None:
        """Records an hourly snapshot of a campaign's state."""
        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO campaign_snapshots (
                        symbol, snapshot_time_utc, origin_bottom_price, highest_peak_price,
                        current_price, current_n, max_n, drawdown_from_peak_pct, stage, is_active, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    campaign.symbol,
                    now_utc,
                    campaign.origin_bottom_price,
                    campaign.highest_peak_price,
                    campaign.current_price,
                    campaign.current_n,
                    campaign.max_n,
                    campaign.drawdown_from_peak_pct,
                    campaign.stage,
                    1 if campaign.is_active else 0,
                    getattr(campaign, "notes", "")
                ))
                conn.commit()
        except Exception as e:
            logger.debug(f"[DB] Error saving campaign snapshot for {getattr(campaign, 'symbol', '')}: {e}")

    def get_latest_gap_fill_summary(self) -> Optional[Dict[str, Any]]:
        """Retrieves the latest gap fill sync summary."""
        try:
            with self._get_connection() as conn:
                cur = conn.execute("SELECT summary_json FROM gap_fill_logs ORDER BY id DESC LIMIT 1;")
                row = cur.fetchone()
                if row:
                    return json.loads(row["summary_json"])
        except Exception as e:
            logger.debug(f"[DB] Error fetching latest gap fill summary: {e}")
        return None


# Global singleton
_DB_STORAGE_INSTANCE: Optional[DatabaseStorage] = None

def get_db_storage() -> DatabaseStorage:
    global _DB_STORAGE_INSTANCE
    if _DB_STORAGE_INSTANCE is None:
        _DB_STORAGE_INSTANCE = DatabaseStorage()
    return _DB_STORAGE_INSTANCE
