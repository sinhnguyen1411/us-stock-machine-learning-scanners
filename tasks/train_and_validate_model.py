# -*- coding: utf-8 -*-
"""
Train and validate the v2 pump multiplier model.
Tests with real known pump parameters from verified events.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv; load_dotenv(".env")

from packages.core_engine.pump_multiplier_regressor import PumpMultiplierRegressor

reg    = PumpMultiplierRegressor(auto_train=False)
result = reg.retrain()

print("=== TRAINING RESULT (v2 — LOO-CV, honest small-data) ===")
for k, v in result.items():
    print("  {:20s}: {}".format(k, v))

print()
print("Interpretation:")
print("  LOO-MAE in log(n) units:")
mae_ridge = result.get("loo_mae_ridge", 0)
mae_rf    = result.get("loo_mae_rf",    0)
mae_avg   = (mae_ridge + mae_rf) / 2
import math
print("  Ridge : MAE={:.3f} -> avg prediction off by factor {:.2f}x".format(
    mae_ridge, math.exp(mae_ridge)))
print("  RF    : MAE={:.3f} -> avg prediction off by factor {:.2f}x".format(
    mae_rf, math.exp(mae_rf)))
print("  Blend : MAE={:.3f} -> avg prediction off by factor {:.2f}x".format(
    mae_avg, math.exp(mae_avg)))

print()
print("=== PREDICTIONS vs REAL DATA (verified events) ===")
print("{:<22} {:>10} {:>10} {:>10} {:>10} {:>8}".format(
    "Symbol", "Real_n", "Pred_n", "n_low", "n_high", "Tier"))
print("-" * 80)

# Test with real known values from the 28-event database
from packages.core_engine.pump_multiplier_classifier import PumpDatasetBuilder
db     = PumpDatasetBuilder()
events = db.load_all()
events.sort(key=lambda e: e.pre_pump_price)

for e in events:
    r = reg.predict(
        price     = e.pre_pump_price,
        mcap_usd  = e.pre_pump_mcap_usd,
        vol_24h   = e.pre_pump_vol_24h,
        vol_spike = e.vol_spike_ratio,
        pct_24h   = 150.0,  # force display
    )
    n_pred = r.get("n_expected") or 0
    n_low  = r.get("n_low")      or 0
    n_high = r.get("n_high")     or 0
    err    = abs(n_pred - e.n_actual) / e.n_actual * 100 if e.n_actual > 0 else 0
    flag   = "  <-- HIGH ERR" if err > 100 else ""
    print("{:<22} {:>10.2f}x {:>10.2f}x {:>10.2f}x {:>10.2f}x {:>8}{}".format(
        e.symbol,
        e.n_actual,
        n_pred,
        n_low,
        n_high,
        e.price_tier_code,
        flag,
    ))
