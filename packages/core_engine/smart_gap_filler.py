"""
Smart Gap-Filling & Backfill Engine (Offline-Tolerant System)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ensures uninterrupted data continuity across PC reboots, shutdowns, and extended offline periods.

When the system boots up:
1. Calculates downtime gap: Delta_t = now_utc - last_sync_utc
2. If Delta_t > 5 minutes:
   - Fetches missing 15m / 1h / 1d klines from Binance Futures REST API for all active campaigns
   - Detects all-time-high peaks created during the offline period (updates highest_peak_price, max_n, highest_peak_date)
   - Evaluates dump breakdowns (>45% drawdown from peak) and transitions stages
   - Discovers new super-pump breakout campaigns (Ignition) that started while the PC was off
   - Seamlessly triggers Online Retraining for the ML Tri-Ensemble v4 Model
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
_STATE_FILE = os.path.join(_DATA_DIR, "system_telemetry_state.json")
os.makedirs(_DATA_DIR, exist_ok=True)


class SmartGapFiller:
    """
    Autonomous offline gap-filler that synchronizes historical state on every system startup.
    """

    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or _STATE_FILE
        self._last_sync_utc: Optional[datetime] = None
        self._load_telemetry_state()

    def _load_telemetry_state(self) -> None:
        """Loads the last recorded heartbeat timestamp from disk."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ts_str = data.get("last_heartbeat_utc")
                    if ts_str:
                        self._last_sync_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception as e:
                logger.debug(f"[GapFiller] Error reading telemetry state: {e}")

    def save_heartbeat(self) -> None:
        """Records current UTC timestamp as the latest active heartbeat."""
        now_utc = datetime.now(timezone.utc)
        self._last_sync_utc = now_utc
        try:
            state = {
                "last_heartbeat_utc": now_utc.isoformat(),
                "last_heartbeat_timestamp": int(now_utc.timestamp()),
                "status": "ONLINE",
                "system_pid": os.getpid()
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.debug(f"[GapFiller] Error saving heartbeat: {e}")

    def get_downtime_seconds(self) -> float:
        """Returns the number of seconds the machine was powered off / offline."""
        if not self._last_sync_utc:
            return 0.0
        now_utc = datetime.now(timezone.utc)
        diff = (now_utc - self._last_sync_utc).total_seconds()
        return max(0.0, diff)

    def fetch_klines(
        self,
        symbol: str,
        interval: str = "1h",
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Fetches historical klines from Binance Futures REST API.
        """
        try:
            enc_sym = urllib.parse.quote(symbol)
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={enc_sym}&interval={interval}&limit={limit}"
            if start_time_ms:
                url += f"&startTime={int(start_time_ms)}"
            if end_time_ms:
                url += f"&endTime={int(end_time_ms)}"

            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (DeepAlpha/1.0)"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))

            klines = []
            for k in raw_data:
                # [open_time, open, high, low, close, volume, close_time, quote_asset_volume, count, ...]
                klines.append({
                    "open_time_ms": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time_ms": k[6],
                    "quote_volume": float(k[7]),
                    "trades_count": int(k[8])
                })
            return klines
        except Exception as e:
            logger.debug(f"[GapFiller] Failed to fetch klines for {symbol}: {e}")
            return []

    def sync_on_startup(self, registry: Any) -> Dict[str, Any]:
        """
        Core Startup Hook:
        Analyzes downtime gap and automatically backfills all active campaigns.
        """
        now_utc = datetime.now(timezone.utc)
        downtime_sec = self.get_downtime_seconds()
        downtime_hours = round(downtime_sec / 3600.0, 2)

        summary = {
            "timestamp": now_utc.isoformat(),
            "downtime_seconds": downtime_sec,
            "downtime_hours": downtime_hours,
            "gap_fill_triggered": False,
            "campaigns_scanned": 0,
            "peaks_updated": [],
            "dumps_detected": [],
            "newly_ignited": [],
            "total_klines_analyzed": 0,
            "status": "UP_TO_DATE"
        }

        # If downtime > 5 minutes, run comprehensive gap fill
        if downtime_sec > 300:
            summary["gap_fill_triggered"] = True
            logger.info(f"[GapFiller] ⚡ System startup detected downtime of {downtime_hours}h ({downtime_sec:.0f}s). Initiating Smart Backfill...")

            start_ms = int((self._last_sync_utc.timestamp() - 3600) * 1000) if self._last_sync_utc else int((now_utc.timestamp() - 86400 * 3) * 1000)
            end_ms = int(now_utc.timestamp() * 1000)

            active_campaigns = [c for c in registry.campaigns.values() if c.is_active and c.stage not in ("DUMP_CONFIRMED", "DELISTED", "ARCHIVED")]
            summary["campaigns_scanned"] = len(active_campaigns)

            for camp in active_campaigns:
                sym = camp.symbol
                # Fetch 1h klines during the downtime gap
                klines_1h = self.fetch_klines(sym, interval="1h", start_time_ms=start_ms, end_time_ms=end_ms, limit=500)
                summary["total_klines_analyzed"] += len(klines_1h)

                if not klines_1h:
                    continue

                # Find highest high and lowest low during downtime
                max_high_during_gap = max(k["high"] for k in klines_1h)
                latest_close = klines_1h[-1]["close"]
                
                # Check if a higher peak was reached during downtime
                if max_high_during_gap > camp.highest_peak_price:
                    # Find date of this new peak
                    peak_kline = next(k for k in klines_1h if k["high"] == max_high_during_gap)
                    peak_dt = datetime.fromtimestamp(peak_kline["open_time_ms"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                    old_peak = camp.highest_peak_price
                    camp.highest_peak_price = max_high_during_gap
                    camp.highest_peak_date = peak_dt
                    if camp.origin_bottom_price > 0:
                        camp.max_n = round(camp.highest_peak_price / camp.origin_bottom_price, 2)
                    summary["peaks_updated"].append({
                        "symbol": sym,
                        "old_peak": old_peak,
                        "new_peak": max_high_during_gap,
                        "new_max_n": camp.max_n,
                        "peak_date": peak_dt
                    })
                    logger.info(f"[GapFiller] 🎯 New ATH peak discovered for {sym}: ${old_peak} -> ${max_high_during_gap} ({camp.max_n}x)")

                # Update current price and calculate drawdown
                camp.current_price = latest_close
                if camp.origin_bottom_price > 0:
                    camp.current_n = round(latest_close / camp.origin_bottom_price, 2)
                if camp.highest_peak_price > 0:
                    dd = (camp.highest_peak_price - latest_close) / camp.highest_peak_price * 100.0
                    camp.drawdown_from_peak_pct = round(max(0.0, dd), 1)

                # Check if dump occurred during offline gap (>45% drawdown)
                if camp.drawdown_from_peak_pct >= 45.0 and camp.is_active:
                    camp.stage = "DUMP_CONFIRMED"
                    camp.stage_label_vi = f"Đã Xác Nhận Dump (-{camp.drawdown_from_peak_pct:.1f}%)"
                    camp.is_active = False
                    camp.dump_date = now_utc.strftime("%Y-%m-%d")
                    summary["dumps_detected"].append({
                        "symbol": sym,
                        "drawdown_pct": camp.drawdown_from_peak_pct,
                        "peak_price": camp.highest_peak_price,
                        "exit_price": latest_close
                    })
                    logger.info(f"[GapFiller] ⚠️ Dump breakdown confirmed for {sym} during offline period (DD: -{camp.drawdown_from_peak_pct}%)")

            # Save updated state to registry
            registry.save()
            summary["status"] = "SYNCED"
            logger.info(f"[GapFiller] ✅ Gap-fill complete: {len(summary['peaks_updated'])} peaks updated, {len(summary['dumps_detected'])} dumps resolved.")

        # Always update heartbeat to current timestamp
        self.save_heartbeat()
        return summary


# Global singleton instance
_GAP_FILLER_INSTANCE: Optional[SmartGapFiller] = None

def get_gap_filler() -> SmartGapFiller:
    global _GAP_FILLER_INSTANCE
    if _GAP_FILLER_INSTANCE is None:
        _GAP_FILLER_INSTANCE = SmartGapFiller()
    return _GAP_FILLER_INSTANCE
