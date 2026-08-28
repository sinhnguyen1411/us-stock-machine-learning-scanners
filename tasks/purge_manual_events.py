# -*- coding: utf-8 -*-
"""Remove all manual/fabricated events. Keep only verified api_fetch events."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from packages.core_engine.pump_multiplier_classifier import PumpDatasetBuilder

db = PumpDatasetBuilder()
all_events = db.load_all()
api_only   = [e for e in all_events if e.source == "api_fetch"]
removed    = len(all_events) - len(api_only)
db.save_all(api_only)

s = db.summary()
print("Removed {} fabricated manual events.".format(removed))
print("Kept {} verified API-fetched events.".format(s.get("count", 0)))
print("n range: {}x - {}x  (mean {}x)".format(
    s.get("n_min","?"), s.get("n_max","?"), s.get("n_mean","?")))
print("By tier:")
for code, cnt in sorted(s.get("by_tier", {}).items()):
    print("  {:16s}: {}".format(code, cnt))
print()
print("Verified real events:")
for e in sorted(api_only, key=lambda x: x.pre_pump_price):
    print("  {:22s} n={:6.2f}x  pre=${:<12.8f}  {}".format(
        e.symbol, e.n_actual, e.pre_pump_price, e.event_date))
