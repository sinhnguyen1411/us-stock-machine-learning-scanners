# -*- coding: utf-8 -*-
"""
Analyse the verified 28-event database.
Show the actual relationship between price tier and n,
and identify what other features drive the variance.
"""
import sys, os, math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from packages.core_engine.pump_multiplier_classifier import PumpDatasetBuilder

db     = PumpDatasetBuilder()
events = db.load_all()
events.sort(key=lambda e: e.pre_pump_price)

print("=" * 80)
print("  VERIFIED 2026 PUMP EVENTS — Data Analysis")
print("=" * 80)
print()
print("{:<22} {:>12} {:>10} {:>12} {:>10} {:>8}  {}".format(
    "Symbol", "Bottom $", "n_actual", "McapUSD", "Vol24h", "VolSpike", "Tier"))
print("-" * 100)
for e in events:
    mcap_str  = "${:.0f}M".format(e.pre_pump_mcap_usd / 1e6) if e.pre_pump_mcap_usd > 0 else "  N/A"
    vol_str   = "${:.0f}M".format(e.pre_pump_vol_24h  / 1e6) if e.pre_pump_vol_24h  > 0 else "  N/A"
    print("{:<22} {:>12.8f} {:>10.2f}x {:>12} {:>10} {:>8.1f}  {}".format(
        e.symbol,
        e.pre_pump_price,
        e.n_actual,
        mcap_str,
        vol_str,
        e.vol_spike_ratio,
        e.price_tier_code,
    ))

print()
print("=" * 80)
print("  TIER STATISTICS")
print("=" * 80)

from collections import defaultdict
tiers = defaultdict(list)
for e in events:
    tiers[e.price_tier_code].append(e.n_actual)

tier_order = ["ULTRA_MICRO","MICRO","NANO","SMALL","MID","LARGE","XLARGE","MEGA"]
print("{:<16} {:>6} {:>10} {:>10} {:>10}".format(
    "Tier", "Count", "n_min", "n_mean", "n_max"))
print("-" * 55)
for t in tier_order:
    if t not in tiers:
        continue
    ns    = tiers[t]
    n_min = min(ns)
    n_max = max(ns)
    n_mean= sum(ns) / len(ns)
    print("{:<16} {:>6} {:>10.2f}x {:>10.2f}x {:>10.2f}x".format(
        t, len(ns), n_min, n_mean, n_max))

print()
print("=" * 80)
print("  KEY OBSERVATIONS for model design")
print("=" * 80)
# Check: is log(n) correlated with log(price)?
import math as m
pairs = [(m.log(e.pre_pump_price) if e.pre_pump_price > 0 else None,
          m.log(e.n_actual) if e.n_actual > 0 else None)
         for e in events]
pairs = [(lp, ln) for lp, ln in pairs if lp is not None and ln is not None]
n_pts = len(pairs)
mean_x = sum(p[0] for p in pairs) / n_pts
mean_y = sum(p[1] for p in pairs) / n_pts
cov    = sum((p[0]-mean_x)*(p[1]-mean_y) for p in pairs) / n_pts
std_x  = (sum((p[0]-mean_x)**2 for p in pairs) / n_pts) ** 0.5
std_y  = (sum((p[1]-mean_y)**2 for p in pairs) / n_pts) ** 0.5
corr   = cov / (std_x * std_y) if std_x * std_y > 0 else 0

print()
print("  Pearson correlation: log(price) vs log(n) = {:.4f}".format(corr))
print("  (Target > |0.5| for meaningful relationship)")
print()
print("  HIGH VARIANCE CASES (n much higher/lower than tier median):")
for e in events:
    tier_ns = tiers[e.price_tier_code]
    tier_med = sorted(tier_ns)[len(tier_ns)//2]
    ratio = e.n_actual / tier_med if tier_med > 0 else 0
    if ratio > 2.5 or ratio < 0.4:
        print("  ** {:<22} n={:.1f}x  tier_median={:.1f}x  ratio={:.1f}x  mcap=${:.0f}M".format(
            e.symbol, e.n_actual, tier_med,
            ratio, e.pre_pump_mcap_usd / 1e6 if e.pre_pump_mcap_usd else 0))
