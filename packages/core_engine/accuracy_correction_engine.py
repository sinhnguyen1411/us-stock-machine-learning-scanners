"""
====================================================================
ADAPTIVE GROUND TRUTH CORRECTION ENGINE
====================================================================
Solves the critical "Circular Bias" problem in ML training data:

ROOT CAUSE:
  When a coin pumps BEYOND the ML prediction and eventually dumps,
  the system may record a "stale peak" — a peak LOWER than the true
  All-Time-High the coin actually reached. This creates:

  1. CIRCULAR BIAS: ML trains on low peaks → predicts low → records
     low peaks → perpetually conservative, never converging upward.

  2. SURVIVOR BIAS (inverted): The most valuable super-pump events
     (PNUT 52x, TRB 63x, AKE 94x) teach the model about REAL upper
     limits per tier — but only if their TRUE ATH is recorded.

  3. CONFIDENCE INTERVAL SHRINKAGE: 90% CI n_high is pulled downward
     by incorrect peaks → users get "near peak" warnings too early
     and exit profitable positions prematurely.

SOLUTION:
  1. Detect when n_current > n_expected_ml * 0.95 → flag SUPER_PUMP
  2. NEVER finalize before dump is confirmed
  3. On DUMP_CONFIRMED, verify Binance ATH for the full campaign period
  4. If Binance ATH > stored peak → correct peak BEFORE writing to DB
  5. Upsert corrected event into pump_events_db.json
  6. Trigger immediate ML retraining
  7. Log all corrections to SQLite audit log
====================================================================
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import urllib.request

logger = logging.getLogger("AccuracyCorrectionEngine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
_CORRECTION_AUDIT_FILE = os.path.join(_DATA_DIR, "correction_audit_log.json")
_BINANCE_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"

# Threshold: when current_n reaches this fraction of n_expected_ml, flag as super-pump
SUPER_PUMP_THRESHOLD = 0.95  # 95% of predicted target


class AccuracyCorrectionEngine:
    """
    Adaptive Ground Truth Correction Engine.

    Continuously monitors active campaigns for super-pump behavior,
    corrects stale peaks in training data, and maintains training
    data quality integrity across all lifecycle events.
    """

    def __init__(self):
        os.makedirs(_DATA_DIR, exist_ok=True)
        self.correction_audit: List[Dict[str, Any]] = self._load_audit_log()
        self.total_corrections_applied: int = len(self.correction_audit)

    # ─────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────

    def flag_super_pump_in_progress(self, campaign) -> bool:
        """
        Check if a campaign is exceeding its ML prediction.
        Returns True if it was newly flagged (first detection).

        Called from update_price_and_stage() on every price tick.
        """
        if campaign.expected_n_ml <= 0 or campaign.origin_bottom_price <= 0:
            return False

        current_n = campaign.current_price / max(campaign.origin_bottom_price, 1e-12)
        threshold = campaign.expected_n_ml * SUPER_PUMP_THRESHOLD

        if current_n >= threshold and not campaign.is_super_pump_in_progress:
            campaign.is_super_pump_in_progress = True
            campaign.super_pump_detected_at = datetime.now(timezone.utc).isoformat()
            logger.info(
                f"[SuperPump] {campaign.symbol} VƯỢT ĐÍCH ML "
                f"{campaign.expected_n_ml:.1f}x @ {current_n:.2f}x "
                f"(ngưỡng phát hiện: {threshold:.2f}x)"
            )
            return True  # newly flagged
        return False

    def verify_and_correct_peak_before_finalize(
        self,
        symbol: str,
        origin_date: str,
        origin_bottom_price: float,
        stored_peak_price: float,
    ) -> Tuple[float, bool]:
        """
        Before finalizing a completed campaign into training data,
        query Binance to confirm the true ATH over the full campaign period.

        Returns:
            (corrected_peak_price, was_corrected: bool)
        """
        try:
            # Compute campaign start timestamp (ms)
            try:
                start_dt = datetime.strptime(origin_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                start_ms = int(start_dt.timestamp() * 1000)
            except Exception:
                start_ms = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000)

            end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

            klines = self._fetch_klines_range(symbol, start_ms, end_ms, interval="1d")
            if not klines:
                return stored_peak_price, False

            binance_ath = max(float(k[2]) for k in klines)  # k[2] = high

            if binance_ath > stored_peak_price * 1.005:  # >0.5% higher = meaningful correction
                correction_pct = round((binance_ath - stored_peak_price) / stored_peak_price * 100.0, 2)
                logger.info(
                    f"[ATHCorrection] {symbol}: Binance ATH ${binance_ath:.8f} > "
                    f"stored peak ${stored_peak_price:.8f} "
                    f"(+{correction_pct}% correction)"
                )
                return binance_ath, True

        except Exception as e:
            logger.debug(f"[AccuracyEngine] Error verifying ATH for {symbol}: {e}")

        return stored_peak_price, False

    def correct_peak_and_upsert_to_db(
        self,
        symbol: str,
        origin_date: str,
        origin_bottom_price: float,
        corrected_peak_price: float,
        original_peak_price: float,
        reason: str = "ATH_VERIFICATION",
    ) -> bool:
        """
        Upsert a corrected PumpEvent into pump_events_db.json.
        Records the correction in the audit log.

        Returns True if upsert was performed.
        """
        try:
            from .pump_multiplier_classifier import PumpDatasetBuilder, PumpEvent, PriceTierClassifier

            clf = PriceTierClassifier()
            tier = clf.classify(origin_bottom_price)

            n_actual_corrected = round(corrected_peak_price / max(origin_bottom_price, 1e-12), 2)

            corrected_event = PumpEvent(
                symbol=symbol.upper(),
                event_date=origin_date,
                source="auto_lifecycle_tracker_corrected",
                pre_pump_price=origin_bottom_price,
                peak_price=corrected_peak_price,
                n_actual=n_actual_corrected,
                price_tier_code=tier.code,
                price_tier_index=tier.tier_index,
                vol_spike_ratio=15.0,
                pre_pump_vol_24h=1_500_000.0,
                notes=(
                    f"[ACE-CORRECTED] Đỉnh chỉnh sửa từ ${original_peak_price:.8f} "
                    f"→ ${corrected_peak_price:.8f} ({n_actual_corrected:.2f}x). "
                    f"Lý do: {reason}."
                ),
            )

            db = PumpDatasetBuilder()
            db.upsert(corrected_event)

            # Log correction to audit trail
            audit_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "event_date": origin_date,
                "original_peak": original_peak_price,
                "corrected_peak": corrected_peak_price,
                "original_n": round(original_peak_price / max(origin_bottom_price, 1e-12), 2),
                "corrected_n": n_actual_corrected,
                "correction_pct": round((corrected_peak_price - original_peak_price) / original_peak_price * 100.0, 2),
                "reason": reason,
            }
            self.correction_audit.append(audit_entry)
            self._save_audit_log(self.correction_audit)
            self.total_corrections_applied += 1

            logger.info(
                f"[ACE] Corrected & upserted {symbol}: "
                f"{round(original_peak_price / max(origin_bottom_price, 1e-12), 2):.2f}x "
                f"→ {n_actual_corrected:.2f}x into training DB"
            )
            return True

        except Exception as e:
            logger.error(f"[ACE] Error correcting peak for {symbol}: {e}", exc_info=True)
            return False

    def detect_and_correct_stale_peaks(self, registry) -> Dict[str, Any]:
        """
        Scan all DUMP_CONFIRMED campaigns. Compare stored peak vs Binance ATH.
        If stale, correct and upsert. Returns correction summary.

        Designed to run on startup or manually via API.
        """
        corrected = []
        scanned = 0

        for symbol, c in registry.campaigns.items():
            if c.is_active or c.stage not in ("DUMP_CONFIRMED", "ARCHIVED"):
                continue
            if c.origin_bottom_price <= 0 or c.highest_peak_price <= 0:
                continue

            scanned += 1

            # Skip if very recently corrected (< 24h ago)
            if c.correction_finalized:
                continue

            try:
                corrected_peak, was_corrected = self.verify_and_correct_peak_before_finalize(
                    symbol=symbol,
                    origin_date=c.origin_date,
                    origin_bottom_price=c.origin_bottom_price,
                    stored_peak_price=c.highest_peak_price,
                )

                if was_corrected:
                    old_peak = c.highest_peak_price
                    c.highest_peak_price = corrected_peak
                    c.max_n = round(corrected_peak / c.origin_bottom_price, 2)
                    c.correction_finalized = True

                    self.correct_peak_and_upsert_to_db(
                        symbol=symbol,
                        origin_date=c.origin_date,
                        origin_bottom_price=c.origin_bottom_price,
                        corrected_peak_price=corrected_peak,
                        original_peak_price=old_peak,
                        reason="STALE_PEAK_DETECTED_ON_STARTUP",
                    )
                    corrected.append({
                        "symbol": symbol,
                        "old_peak": old_peak,
                        "new_peak": corrected_peak,
                        "new_max_n": c.max_n,
                    })

                time.sleep(0.12)  # Rate limit: ~8 req/s

            except Exception as e:
                logger.debug(f"[ACE] Error scanning {symbol}: {e}")

        if corrected:
            # Trigger retraining with corrected data
            try:
                from .self_learning_engine import get_self_learning_engine
                get_self_learning_engine().retrain_models()
            except Exception as e:
                logger.debug(f"[ACE] Error triggering retrain after stale peak correction: {e}")

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "campaigns_scanned": scanned,
            "corrections_applied": len(corrected),
            "corrected_symbols": corrected,
        }

    def retroactive_correct_all(self, max_events: int = 500) -> Dict[str, Any]:
        """
        One-shot batch correction: query Binance ATH for all events in
        pump_events_db.json and correct any stale peaks.

        This is a SLOW operation (~5-10 minutes for 388 events due to rate limits).
        Run manually via POST /api/ml/retroactive_correct
        """
        try:
            from .pump_multiplier_classifier import PumpDatasetBuilder
        except Exception:
            return {"status": "error", "message": "Could not load PumpDatasetBuilder"}

        db = PumpDatasetBuilder()
        events = db.load_all()

        corrected_events = []
        skipped = 0
        errors = 0

        for i, event in enumerate(events[:max_events]):
            try:
                if event.pre_pump_price <= 0 or event.peak_price <= 0:
                    skipped += 1
                    continue

                # Compute campaign period bounds
                try:
                    start_dt = datetime.strptime(event.event_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except Exception:
                    skipped += 1
                    continue

                start_ms = int(start_dt.timestamp() * 1000)
                # End: event_date + 90 days or today, whichever is earlier
                end_dt = min(start_dt + timedelta(days=90), datetime.now(timezone.utc))
                end_ms = int(end_dt.timestamp() * 1000)

                klines = self._fetch_klines_range(event.symbol, start_ms, end_ms, interval="1d")
                if not klines:
                    skipped += 1
                    time.sleep(0.15)
                    continue

                binance_ath = max(float(k[2]) for k in klines)

                if binance_ath > event.peak_price * 1.005:
                    old_peak = event.peak_price
                    old_n = event.n_actual
                    correction_pct = round((binance_ath - old_peak) / old_peak * 100.0, 2)

                    # Update in-memory event
                    event.peak_price = binance_ath
                    event.n_actual = round(binance_ath / max(event.pre_pump_price, 1e-12), 2)
                    event.notes = (
                        f"[RETROACTIVE-CORRECTED +{correction_pct:.1f}%] "
                        f"Đỉnh thực ${binance_ath:.8f} ({event.n_actual:.2f}x) vs "
                        f"ghi sai ${old_peak:.8f} ({old_n:.2f}x). | "
                        + (event.notes or "")
                    )
                    event.source = "auto_lifecycle_tracker_corrected"

                    corrected_events.append({
                        "symbol": event.symbol,
                        "event_date": event.event_date,
                        "old_peak": old_peak,
                        "new_peak": binance_ath,
                        "old_n": old_n,
                        "new_n": event.n_actual,
                        "correction_pct": correction_pct,
                    })

                    # Log to audit trail
                    self.correction_audit.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "symbol": event.symbol,
                        "event_date": event.event_date,
                        "original_peak": old_peak,
                        "corrected_peak": binance_ath,
                        "original_n": old_n,
                        "corrected_n": event.n_actual,
                        "correction_pct": correction_pct,
                        "reason": "RETROACTIVE_BATCH_CORRECTION",
                    })

                time.sleep(0.15)  # ~6.7 req/s (well within Binance 1200/min limit)

            except Exception as e:
                errors += 1
                logger.debug(f"[ACE] Retroactive error for {event.symbol}: {e}")
                time.sleep(0.2)

        # Save corrected dataset and audit log
        db.save_all(events)
        self._save_audit_log(self.correction_audit)
        self.total_corrections_applied += len(corrected_events)

        # Trigger retraining
        retrain_result = {}
        if corrected_events:
            try:
                from .self_learning_engine import get_self_learning_engine
                retrain_result = get_self_learning_engine().retrain_models()
            except Exception as e:
                logger.debug(f"[ACE] Retrain error after retroactive correction: {e}")

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events_scanned": len(events[:max_events]),
            "corrections_applied": len(corrected_events),
            "skipped": skipped,
            "errors": errors,
            "corrected_events": corrected_events,
            "retrain_result": retrain_result,
            "status": "COMPLETED",
        }

    def audit_training_data_quality(self) -> Dict[str, Any]:
        """
        Audit report on training data quality.
        Checks consistency and flags likely stale peaks.
        Does NOT make API calls — purely data analysis.
        """
        try:
            from .pump_multiplier_classifier import PumpDatasetBuilder, PriceTierClassifier
        except Exception:
            return {"status": "error", "message": "Cannot load modules"}

        db = PumpDatasetBuilder()
        clf = PriceTierClassifier()
        events = db.load_all()

        if not events:
            return {"status": "empty", "total_events": 0}

        super_pumps = []
        corrected_events = []
        tier_ceiling_violations = []

        for e in events:
            tier = clf.classify(e.pre_pump_price)
            if e.n_actual > tier.n_expected_high:
                tier_ceiling_violations.append({
                    "symbol": e.symbol,
                    "event_date": e.event_date,
                    "n_actual": round(e.n_actual, 2),
                    "tier_ceiling": tier.n_expected_high,
                    "exceeded_by": round(e.n_actual / tier.n_expected_high, 2),
                    "source": e.source,
                })
            if "corrected" in (e.source or "").lower():
                corrected_events.append(e.symbol)

        # Correction coverage
        corrections_in_audit = len(self.correction_audit)
        quality_score = round(
            100.0 * (1.0 - len(tier_ceiling_violations) / max(len(events), 1)),
            1
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events),
            "super_pumps_beyond_tier_ceiling": len(tier_ceiling_violations),
            "corrected_events_in_db": len(corrected_events),
            "corrections_in_audit_log": corrections_in_audit,
            "total_corrections_ever_applied": self.total_corrections_applied,
            "data_quality_score_pct": quality_score,
            "tier_ceiling_violations": tier_ceiling_violations[:20],  # top 20
        }

    # ─────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────────

    def _fetch_klines_range(
        self,
        symbol: str,
        start_time_ms: int,
        end_time_ms: int,
        interval: str = "1d",
        limit: int = 500,
    ) -> List[List]:
        """Fetch klines from Binance Futures REST API for a given time range."""
        try:
            url = (
                f"{_BINANCE_KLINES_URL}"
                f"?symbol={symbol.upper()}"
                f"&interval={interval}"
                f"&startTime={start_time_ms}"
                f"&endTime={end_time_ms}"
                f"&limit={limit}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "DeepAlpha-ACE/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug(f"[ACE] Klines fetch error for {symbol}: {e}")
            return []

    def _load_audit_log(self) -> List[Dict[str, Any]]:
        if os.path.exists(_CORRECTION_AUDIT_FILE):
            try:
                with open(_CORRECTION_AUDIT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_audit_log(self, log: List[Dict[str, Any]]) -> None:
        try:
            with open(_CORRECTION_AUDIT_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"[ACE] Error saving audit log: {e}")


# ─────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────
_ACE_INSTANCE: Optional[AccuracyCorrectionEngine] = None


def get_accuracy_correction_engine() -> AccuracyCorrectionEngine:
    global _ACE_INSTANCE
    if _ACE_INSTANCE is None:
        _ACE_INSTANCE = AccuracyCorrectionEngine()
    return _ACE_INSTANCE
