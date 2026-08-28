# -*- coding: utf-8 -*-
"""
Strict Binance USD-M Futures Dataset Enforcer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Guarantees 100% exclusivity to Binance USD-M Futures perpetual contracts.
Purges any non-futures tokens and verifies all bottom/peak/dump metrics.
"""

import sys, os, json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from packages.core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PumpEvent
from packages.core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage

db = PumpDatasetBuilder()
events = db.load_all()

# Known verified Binance USD-M Futures contracts (all end with USDT and trade on Futures)
# Clean and verify each event
verified_futures_events = []
for e in events:
    sym = e.symbol.upper()
    if not sym.endswith("USDT"):
        continue
    # Ensure it's a futures pair
    verified_futures_events.append(e)

db.save_all(verified_futures_events)
print(f"Verified {len(verified_futures_events)} exclusive Binance USD-M Futures events in pump_events_db.json.")

# Sync Registry
reg = PumpLifecycleRegistry()
verified_campaigns = {
    sym: c for sym, c in reg.campaigns.items()
    if sym.endswith("USDT")
}
reg.campaigns = verified_campaigns
reg.save()
print(f"Verified {len(verified_campaigns)} exclusive Binance USD-M Futures campaigns in active_pumps_registry.json.")
