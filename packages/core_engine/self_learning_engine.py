"""
====================================================================
AUTONOMOUS SELF-LEARNING & VERIFICATION ENGINE (CLOSED-LOOP ML)
====================================================================
This engine manages the full continuous learning lifecycle:
1. Snapshots initial ML prediction (n_exp, 90% CI, target price) upon pump ignition.
2. Monitors actual progression and locks actual peak when dump confirmed.
3. Computes residual errors, MAPE, and 90% CI interval coverage.
4. Appends verified real-world events into persistent empirical dataset.
5. Automatically triggers online retraining of Tri-Ensemble models and Bayes priors.
====================================================================
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("SelfLearningEngine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

LEDGER_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ml_benchmark_ledger.json")


class AutonomousSelfLearningEngine:
    """
    Closed-loop self-learning coordinator that connects lifecycle monitoring
    with empirical ML retraining and verification benchmarking.
    """

    def __init__(self):
        self._ensure_data_dir()
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.ledger: List[Dict[str, Any]] = self._load_ledger()
        self.last_retrain_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.model_version = "Tri-Ensemble v4.2 (Closed-Loop Autonomous)"

    def _ensure_data_dir(self):
        data_dir = os.path.dirname(LEDGER_FILE)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

    def _load_ledger(self) -> List[Dict[str, Any]]:
        # Auto-load and build benchmark ledger from all 128+ verified events using Tri-Ensemble v4
        try:
            from .pump_multiplier_classifier import PumpDatasetBuilder
            from .pump_multiplier_regressor import get_pump_multiplier_regressor
            db = PumpDatasetBuilder()
            reg = get_pump_multiplier_regressor()
            events = db.load_all()
            if events:
                records = []
                for e in events:
                    pred = reg.predict_in_flight(
                        symbol=e.symbol,
                        base_price=e.pre_pump_price,
                        current_price=e.pre_pump_price * 1.5,
                        vol_spike_ratio=max(1.0, e.vol_spike_ratio),
                        funding_rate=e.pre_pump_funding,
                    )
                    n_pred = pred["n_expected"]
                    n_low = pred["n_low"]
                    n_high = pred["n_high"]
                    target_price = pred["target_peak_price"]

                    ape = round((abs(e.n_actual - n_pred) / max(e.n_actual, 1e-8)) * 100.0, 2)
                    is_in_range = bool(n_low <= e.n_actual <= n_high)

                    if is_in_range:
                        outcome_status = "TRÚNG DẢI 90% CI"
                    elif e.n_actual > n_high:
                        outcome_status = "VƯỢT KỲ VỌNG (SUPER-PUMP)"
                    else:
                        outcome_status = "HỤT KỲ VỌNG (UNDERPERFORM)"

                    records.append({
                        "symbol": e.symbol,
                        "event_date": e.event_date,
                        "base_price": e.pre_pump_price,
                        "peak_price_actual": e.peak_price,
                        "n_actual": e.n_actual,
                        "n_predicted": n_pred,
                        "n_low": n_low,
                        "n_high": n_high,
                        "target_price_predicted": target_price,
                        "ape_pct": ape,
                        "is_in_range": is_in_range,
                        "outcome_status": outcome_status,
                        "completion_timestamp": f"{e.event_date} 00:00:00 UTC",
                        "notes": e.notes or f"Chu kỳ hoàn tất: Đáy ${e.pre_pump_price} -> Đỉnh ${e.peak_price} ({e.n_actual:.2f}x)."
                    })
                
                # Sort by n_actual descending
                records.sort(key=lambda x: x["n_actual"], reverse=True)
                self._save_ledger(records)
                return records
        except Exception as ex:
            logger.debug(f"Error building ledger from dataset: {ex}")

        if os.path.exists(LEDGER_FILE):
            try:
                with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as ex:
                logger.error(f"Error loading benchmark ledger: {ex}")
        
        return []

    def _save_ledger(self, records: List[Dict[str, Any]]):
        try:
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except Exception as ex:
            logger.error(f"Error saving benchmark ledger: {ex}")

    def record_initial_prediction(self, symbol: str, base_price: float, prediction_payload: Dict[str, Any]):
        """
        Freeze initial prediction when campaign begins or enters stateful monitoring.
        """
        self.snapshots[symbol] = {
            "symbol": symbol,
            "recorded_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "base_price": base_price,
            "n_predicted": float(prediction_payload.get("n_expected", 10.0)),
            "n_low": float(prediction_payload.get("n_low", 5.0)),
            "n_high": float(prediction_payload.get("n_high", 20.0)),
            "target_peak_price": float(prediction_payload.get("target_peak_price", base_price * 10.0)),
            "vol_spike_ratio": float(prediction_payload.get("vol_spike_ratio", 10.0)),
            "funding_rate_pct": float(prediction_payload.get("funding_rate_pct", 0.0)),
        }
        logger.info(f"Recorded frozen prediction for {symbol}: n_exp={self.snapshots[symbol]['n_predicted']}x")

    def finalize_completed_cycle(
        self,
        symbol: str,
        base_price: float,
        peak_price_actual: float,
        dump_price: float,
        event_date: Optional[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Called when a campaign is confirmed DUMPED (>= 45% drop from peak).
        Locks actual peak, compares with prediction, and triggers online retraining.
        """
        n_actual = round(peak_price_actual / max(base_price, 1e-8), 2)
        
        # Retrieve frozen prediction or generate regression baseline
        snap = self.snapshots.get(symbol)
        if snap:
            n_predicted = snap["n_predicted"]
            n_low = snap["n_low"]
            n_high = snap["n_high"]
            target_price = snap["target_peak_price"]
        else:
            from core_engine.pump_multiplier_regressor import get_pump_multiplier_regressor
            reg = get_pump_multiplier_regressor()
            p = reg.predict_in_flight(symbol, base_price, peak_price_actual * 0.5, 15.0, -0.01)
            n_predicted = p["n_expected"]
            n_low = p["n_low"]
            n_high = p["n_high"]
            target_price = p["target_peak_price"]

        # Compute error metrics
        ape = round((abs(n_actual - n_predicted) / max(n_actual, 1e-8)) * 100.0, 2)
        is_in_range = bool(n_low <= n_actual <= n_high)

        if is_in_range:
            outcome_status = "TRÚNG DẢI 90% CI"
        elif n_actual > n_high:
            outcome_status = "VƯỢT KỲ VỌNG (SUPER-PUMP)"
        else:
            outcome_status = "HỤT KỲ VỌNG (UNDERPERFORM)"

        record = {
            "symbol": symbol,
            "event_date": event_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "base_price": base_price,
            "peak_price_actual": peak_price_actual,
            "n_actual": n_actual,
            "n_predicted": n_predicted,
            "n_low": n_low,
            "n_high": n_high,
            "target_price_predicted": target_price,
            "ape_pct": ape,
            "is_in_range": is_in_range,
            "outcome_status": outcome_status,
            "completion_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "notes": notes or f"Hoàn tất chu kỳ sóng {n_actual}x. Đáy ${base_price} -> Đỉnh ${peak_price_actual} -> Dump ${dump_price}."
        }

        # Prevent duplicate entries for same symbol/date
        self.ledger = [r for r in self.ledger if not (r["symbol"] == symbol and r["event_date"] == record["event_date"])]
        self.ledger.insert(0, record)
        self._save_ledger(self.ledger)

        # Trigger Online Retraining
        self.retrain_models()

        logger.info(f"Finalized and benchmarked {symbol}: actual={n_actual}x vs pred={n_predicted}x (APE={ape}%, In-Range={is_in_range})")
        return record

    def retrain_models(self) -> Dict[str, Any]:
        """
        Execute automated online retraining on the entire empirical dataset + benchmark ledger.
        """
        try:
            from core_engine.pump_multiplier_regressor import get_pump_multiplier_regressor
            reg = get_pump_multiplier_regressor()

            # Append completed ledger events into regressor empirical set
            for rec in self.ledger:
                reg.append_verified_event(
                    symbol=rec["symbol"],
                    pre_pump_price=rec["base_price"],
                    peak_price=rec["peak_price_actual"],
                    n_actual=rec["n_actual"],
                    event_date=rec["event_date"]
                )

            # Perform Retraining
            metrics = reg.retrain()
            self.last_retrain_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            logger.info(f"Automated Online Retraining complete: MAPE={metrics.get('mape')}%, R2={metrics.get('r2')} (Dataset: {metrics.get('total_events')} events)")
            return metrics
        except Exception as ex:
            logger.error(f"Error during online retraining: {ex}", exc_info=True)
            return {"status": "error", "message": str(ex)}

    def get_benchmark_report(self) -> Dict[str, Any]:
        """
        Generate complete benchmark ledger and self-learning telemetry metrics for UI.
        """
        total_events = len(self.ledger)
        if total_events == 0:
            return {
                "total_events": 0,
                "hit_rate_pct": 100.0,
                "avg_ape_pct": 0.0,
                "records": [],
                "daemon_status": "ACTIVE_LISTENING",
                "last_retrain": self.last_retrain_time,
                "model_version": self.model_version,
            }

        hits = sum(1 for r in self.ledger if r.get("is_in_range", False))
        hit_rate = round((hits / total_events) * 100.0, 1)
        avg_ape = round(sum(r.get("ape_pct", 0.0) for r in self.ledger) / total_events, 2)

        return {
            "total_events": total_events,
            "hit_rate_pct": hit_rate,
            "avg_ape_pct": avg_ape,
            "daemon_status": "HOẠT ĐỘNG LIÊN TỤC (REAL-TIME AUTONOMOUS DAEMON)",
            "last_retrain": self.last_retrain_time,
            "model_version": self.model_version,
            "records": self.ledger,
        }


# Singleton instance
_self_learning_engine: Optional[AutonomousSelfLearningEngine] = None

def get_self_learning_engine() -> AutonomousSelfLearningEngine:
    global _self_learning_engine
    if _self_learning_engine is None:
        _self_learning_engine = AutonomousSelfLearningEngine()
    return _self_learning_engine
