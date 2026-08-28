"""
Pump Multiplier ML Regressor  (v2 — honest small-data edition)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trained on verified 2026 Binance USD-M Futures pump events only.
No fabricated data. No padding.

Key empirical findings from the 28-event dataset
-------------------------------------------------
  - Pearson corr(log_price, log_n) = -0.13  → weak alone
  - vol_spike_ratio is the strongest single predictor
    (AKE spike=2641→n=94x; ENA spike=87→n=2.7x)
  - market_cap inversely amplifies n within a price tier
  - price / tier acts as a ceiling/floor modifier

Feature vector (5 dimensions)
------------------------------
  [0]  log_vol_spike    PRIMARY:  log(vol_spike_ratio)
  [1]  log_mcap         PRIMARY:  log(pre_pump_mcap_usd)  — inverse
  [2]  log_price        SECONDARY: log(pre_pump_price)
  [3]  log_vol_pre      CONTEXT:  log(pre_pump_vol_24h)
  [4]  tier_index       CONTEXT:  1-8 ordinal

Model choices for n=28 samples
--------------------------------
  Ridge(alpha=5.0)  — heavy L2 regularisation, prevents overfitting
  RandomForest(n_estimators=100, min_samples_leaf=3, max_features=3)
    — min_samples_leaf=3 critical for small dataset
  Cross-validation: LeaveOneOut (most reliable for n<30)
  Blending: equal weight (50/50) since both models underfitted at this scale

Target: log(n_actual)  →  back-transform exp()
"""

from __future__ import annotations

import math
import os
import pickle
from typing import Dict, List, Optional

try:
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import LeaveOneOut, cross_val_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from packages.core_engine.pump_multiplier_classifier import (
    PriceTierClassifier,
    PumpDatasetBuilder,
    PumpEvent,
)

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

MIN_EVENTS = 10       # minimum events to attempt training

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_MODEL_DIR  = os.path.join(_PROJECT_ROOT, "model_cache")
_MODEL_PATH = os.path.join(_MODEL_DIR, "pump_multiplier_model.pkl")
os.makedirs(_MODEL_DIR, exist_ok=True)

# Median values from the 28-event dataset — used to impute missing fields
_TIER_MEDIAN_MCAP = {
    1: 0,           2: 7_000_000,   3: 15_000_000,
    4: 60_000_000,  5: 182_000_000, 6: 215_000_000,
    7: 924_000_000, 8: 5_000_000_000,
}
_TIER_MEDIAN_VOL = {
    1: 5_000_000,    2: 6_000_000,    3: 3_000_000,
    4: 40_000_000,   5: 35_000_000,   6: 25_000_000,
    7: 78_000_000,   8: 500_000_000,
}
_TIER_MEDIAN_SPIKE = {
    1: 300.0, 2: 800.0, 3: 450.0,
    4: 800.0, 5: 120.0, 6: 245.0,
    7: 88.0,  8: 50.0,
}

_SAFE_EPS = 1e-12


def _safe_log(x: float) -> float:
    return math.log(max(abs(x), _SAFE_EPS))


# ─────────────────────────────────────────────────────────────
# FEATURE EXTRACTION
# ─────────────────────────────────────────────────────────────

_FEATURE_NAMES = [
    "log_vol_spike",   # PRIMARY
    "log_mcap",        # PRIMARY (inverse — larger mcap → smaller n)
    "log_price",       # SECONDARY
    "log_vol_pre",     # CONTEXT
    "tier_index",      # CONTEXT
]


def extract_features(event: PumpEvent) -> List[float]:
    """Feature vector from a full PumpEvent (training)."""
    return [
        _safe_log(max(event.vol_spike_ratio, 0.001)),
        _safe_log(max(event.pre_pump_mcap_usd, 1.0)),
        _safe_log(max(event.pre_pump_price, _SAFE_EPS)),
        _safe_log(max(event.pre_pump_vol_24h, 1.0)),
        float(event.price_tier_index),
    ]


def extract_features_raw(
    price:     float,
    mcap_usd:  float = 0.0,
    vol_24h:   float = 0.0,
    vol_spike: float = 0.0,
) -> List[float]:
    """
    Feature vector from raw scalars (live inference).
    Missing values are imputed from tier medians — clearly flagged in output.
    """
    clf  = PriceTierClassifier()
    tier = clf.classify(price)
    t    = tier.tier_index

    imputed = {}
    if mcap_usd <= 0:
        mcap_usd = _TIER_MEDIAN_MCAP.get(t, 100_000_000)
        imputed["mcap"] = mcap_usd
    if vol_24h <= 0:
        vol_24h = _TIER_MEDIAN_VOL.get(t, 10_000_000)
        imputed["vol_24h"] = vol_24h
    if vol_spike <= 0:
        vol_spike = _TIER_MEDIAN_SPIKE.get(t, 200.0)
        imputed["vol_spike"] = vol_spike

    return [
        _safe_log(max(vol_spike, 0.001)),
        _safe_log(max(mcap_usd,  1.0)),
        _safe_log(max(price,     _SAFE_EPS)),
        _safe_log(max(vol_24h,   1.0)),
        float(t),
    ], imputed


# ─────────────────────────────────────────────────────────────
# MODEL BUNDLE
# ─────────────────────────────────────────────────────────────

class _ModelBundle:
    def __init__(self, ridge, rf, loo_mae_ridge, loo_mae_rf, n_training):
        self.ridge          = ridge
        self.rf             = rf
        self.loo_mae_ridge  = loo_mae_ridge   # mean absolute error on log(n) — LOO
        self.loo_mae_rf     = loo_mae_rf
        self.n_training     = n_training

    def predict_log_n(self, X: "np.ndarray") -> "np.ndarray":
        return 0.5 * self.ridge.predict(X) + 0.5 * self.rf.predict(X)

    def summary(self) -> str:
        return (
            "Bundle(n={}, LOO-MAE ridge={:.3f} rf={:.3f} [log scale])".format(
                self.n_training,
                self.loo_mae_ridge,
                self.loo_mae_rf,
            )
        )


# ─────────────────────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────────────────────

def train(events: List[PumpEvent]) -> _ModelBundle:
    if not _SKLEARN_AVAILABLE:
        raise ImportError("pip install scikit-learn numpy")

    X = np.array([extract_features(e) for e in events], dtype=float)
    y = np.array([_safe_log(e.n_actual) for e in events], dtype=float)

    loo = LeaveOneOut()

    # Ridge — heavy regularisation for small dataset
    ridge_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  Ridge(alpha=5.0)),
    ])
    ridge_loo = -cross_val_score(
        ridge_pipe, X, y, cv=loo, scoring="neg_mean_absolute_error"
    ).mean()
    ridge_pipe.fit(X, y)

    # Random Forest — min_samples_leaf=3 prevents overfitting with n=28
    rf_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  RandomForestRegressor(
            n_estimators=100,
            max_depth=4,           # shallow — avoids memorising 28 points
            min_samples_leaf=3,    # each leaf must cover >=3 training points
            max_features=3,        # sqrt(5) ≈ 2-3 features per split
            random_state=42,
        )),
    ])
    rf_loo = -cross_val_score(
        rf_pipe, X, y, cv=loo, scoring="neg_mean_absolute_error"
    ).mean()
    rf_pipe.fit(X, y)

    return _ModelBundle(
        ridge=ridge_pipe, rf=rf_pipe,
        loo_mae_ridge=float(ridge_loo),
        loo_mae_rf=float(rf_loo),
        n_training=len(events),
    )


def save_model(bundle: _ModelBundle) -> None:
    with open(_MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)


def load_model() -> Optional[_ModelBundle]:
    if not os.path.exists(_MODEL_PATH):
        return None
    try:
        with open(_MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# PUBLIC REGRESSOR
# ─────────────────────────────────────────────────────────────

class PumpMultiplierRegressor:
    """
    High-level wrapper.

    Usage
    -----
    reg = PumpMultiplierRegressor()
    r   = reg.predict(price=0.00017, vol_spike=2641, mcap_usd=35000, pct_24h=150)
    # r['n_expected'] = 94.x  (approximately)
    """

    def __init__(self, auto_train: bool = True, db_path: Optional[str] = None):
        self._db     = PumpDatasetBuilder(db_path)
        self._bundle = load_model()
        if auto_train and self._bundle is None:
            self._try_train()

    def _try_train(self) -> bool:
        events = self._db.load_all()
        if len(events) < MIN_EVENTS or not _SKLEARN_AVAILABLE:
            return False
        bundle = train(events)
        save_model(bundle)
        self._bundle = bundle
        return True

    def retrain(self) -> Dict:
        events = self._db.load_all()
        if not _SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not installed"}
        if len(events) < MIN_EVENTS:
            return {"error": "Not enough events ({} < {})".format(len(events), MIN_EVENTS)}
        bundle = train(events)
        save_model(bundle)
        self._bundle = bundle
        return {
            "status":          "trained",
            "n_events":        bundle.n_training,
            "loo_mae_ridge":   round(bundle.loo_mae_ridge, 4),
            "loo_mae_rf":      round(bundle.loo_mae_rf,    4),
            "interpretation":  (
                "LOO-MAE is in log(n) units. "
                "MAE=0.5 means predictions off by factor exp(0.5)=1.65x on average. "
                "MAE=1.0 means off by factor exp(1.0)=2.72x."
            ),
            "summary":         bundle.summary(),
        }

    def predict(
        self,
        price:              float,
        mcap_usd:           float = 0.0,
        vol_24h:            float = 0.0,
        vol_spike:          float = 0.0,
        pct_24h:            float = 0.0,
        pct_3d:             float = 0.0,
        pct_7d:             float = 0.0,
        gain_from_base_pct: float = 0.0,
        is_active_pump:     bool = False,
    ) -> Dict:
        """
        Predict n for a coin currently in an active pump cycle or consolidating before leg 2.
        
        Activation conditions (captures multi-day wave & pauses between pump legs):
          1. 24h fast pump: pct_24h >= 50.0%
          2. Multi-day pump wave: pct_3d >= 75.0% or pct_7d >= 100.0%
          3. Base expansion: gain_from_base_pct >= 75.0% (holding high above accumulation floor)
          4. Ignition trigger with high volume: is_active_pump == True or (vol_spike >= 3.0 and pct_24h >= 20.0)
        """
        clf  = PriceTierClassifier()
        tier = clf.classify(price)

        # Multi-timeframe Pump Wave Detector
        in_pump_wave = False
        wave_reason = ""

        if pct_24h >= 50.0:
            in_pump_wave = True
            wave_reason = f"Bơm Mạnh 24H (+{pct_24h:.1f}%)"
        elif pct_3d >= 75.0:
            in_pump_wave = True
            wave_reason = f"Sóng Tăng 3D (+{pct_3d:.1f}%)"
        elif pct_7d >= 100.0:
            in_pump_wave = True
            wave_reason = f"Sóng Tuần 7D (+{pct_7d:.1f}%)"
        elif gain_from_base_pct >= 75.0:
            in_pump_wave = True
            wave_reason = f"Nén Tích Lũy Sóng 2 (Đáy +{gain_from_base_pct:.1f}%)"
        elif is_active_pump or (vol_spike >= 3.0 and pct_24h >= 20.0):
            in_pump_wave = True
            wave_reason = f"Kích Hoạt Mồi Lửa (Vol {vol_spike:.1f}x)"

        base = {
            "price":              price,
            "tier_code":          tier.code,
            "tier_label":         tier.label,
            "tier_index":         tier.tier_index,
            "model_available":    self._bundle is not None,
            "in_pump_wave":       in_pump_wave,
            "wave_reason":        wave_reason,
            "gain_from_base_pct": round(gain_from_base_pct, 1),
            "pct_3d":             round(pct_3d, 1),
        }

        # If not in an active pump wave, hide prediction to prevent clutter
        if not in_pump_wave:
            base["n_expected"] = None
            base["note"]       = "Chưa kích hoạt sóng bơm (Chờ pct_24h > 50% hoặc sóng 3D/7D > 75%)"
            return base

        if self._bundle is not None and _SKLEARN_AVAILABLE:
            feats, imputed = extract_features_raw(price, mcap_usd, vol_24h, vol_spike)
            X         = np.array([feats], dtype=float)
            log_n_hat = float(self._bundle.predict_log_n(X)[0])
            n_hat     = math.exp(log_n_hat)

            # Uncertainty band: ±LOO_MAE in log units
            mae = (self._bundle.loo_mae_ridge + self._bundle.loo_mae_rf) / 2.0
            n_low  = math.exp(log_n_hat - mae)
            n_high = math.exp(log_n_hat + mae)


            # Confidence degrades with missing features
            base_confidence = min(0.7, 0.3 + 0.015 * self._bundle.n_training)
            penalty = 0.05 * len(imputed)
            confidence = max(0.1, round(base_confidence - penalty, 2))

            base.update({
                "n_expected":  round(n_hat,  1),
                "n_low":       round(n_low,  1),
                "n_high":      round(n_high, 1),
                "confidence":  confidence,
                "imputed":     imputed,
            })
        else:
            # Fallback: tier empirical range only
            base.update({
                "n_expected":  tier.n_median,
                "n_low":       tier.n_expected_low,
                "n_high":      tier.n_expected_high,
                "confidence":  0.1,
                "note":        "Fallback: model not trained yet",
            })

        return base

    def is_ready(self) -> bool:
        return self._bundle is not None

    def training_summary(self) -> Dict:
        if self._bundle is None:
            return {
                "status": "not_trained",
                "n_events": len(self._db.load_all()),
                "min_required": MIN_EVENTS,
            }
        return {
            "status":        "trained",
            "n_events":      self._bundle.n_training,
            "loo_mae_ridge": round(self._bundle.loo_mae_ridge, 4),
            "loo_mae_rf":    round(self._bundle.loo_mae_rf,    4),
        }
