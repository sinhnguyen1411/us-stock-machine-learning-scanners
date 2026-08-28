# -*- coding: utf-8 -*-
"""
Audit & Update DEXE in pump_events_db.json and active_pumps_registry.json
Reflects the full macro cycle of DEXE:
  - Origin Base: $1.718 on 2026-02-06
  - Parabolic Climax Peak: $49.99 on 2026-07-12
  - True Multiplier n: 49.99 / 1.718 = 29.10x
  - Catastrophic Dump: $49.99 -> $1.287 on 2026-07-24 (-95% drawdown)
  - Lifecycle Stage: DUMP_CONFIRMED / ARCHIVED
"""

import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PumpEvent
from packages.core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage

# 1. Update pump_events_db.json
db = PumpDatasetBuilder()
events = db.load_all()

# Find and update DEXE
updated_events = []
dexe_found = False
for e in events:
    if e.symbol == "DEXEUSDT":
        dexe_found = True
        updated_events.append(PumpEvent(
            symbol="DEXEUSDT",
            event_date="2026-02-06",
            source="api_fetch",
            pre_pump_price=1.71800000,
            pre_pump_mcap_usd=166_646_000.0,
            pre_pump_vol_24h=2_500_000.0,
            price_tier_code="LARGE",
            price_tier_index=6,
            peak_price=49.99000000,
            pump_duration_h=3744.0,  # ~156 days full cycle
            pump_vol_total=850_000_000.0,
            vol_spike_ratio=340.0,
            n_actual=29.10,
            notes="Full 2026 Macro Cycle: Bottom $1.718 -> Peak $49.99 (29.1x) -> Dump $1.287 (-95%)"
        ))
    else:
        updated_events.append(e)

if not dexe_found:
    updated_events.append(PumpEvent(
        symbol="DEXEUSDT",
        event_date="2026-02-06",
        source="api_fetch",
        pre_pump_price=1.71800000,
        pre_pump_mcap_usd=166_646_000.0,
        pre_pump_vol_24h=2_500_000.0,
        price_tier_code="LARGE",
        price_tier_index=6,
        peak_price=49.99000000,
        pump_duration_h=3744.0,
        pump_vol_total=850_000_000.0,
        vol_spike_ratio=340.0,
        n_actual=29.10,
        notes="Full 2026 Macro Cycle: Bottom $1.718 -> Peak $49.99 (29.1x) -> Dump $1.287 (-95%)"
    ))

db.save_all(updated_events)
print("[1/2] Updated DEXE in pump_events_db.json: Bottom $1.718 -> Peak $49.99 (29.1x).")

# 2. Update active_pumps_registry.json
reg = PumpLifecycleRegistry()
dexe_campaign = PumpCampaign(
    symbol="DEXEUSDT",
    origin_date="2026-02-06",
    origin_bottom_price=1.71800000,
    highest_peak_price=49.99000000,
    highest_peak_date="2026-07-12",
    current_price=2.49700000,
    current_n=1.45,
    max_n=29.10,
    expected_n_ml=25.0,
    expected_n_low=12.0,
    expected_n_high=40.0,
    drawdown_from_peak_pct=95.0,
    pump_age_days=156,
    stage=PumpStage.DUMP_CONFIRMED,
    stage_label_vi="🔴 Đã Xác Nhận Dump (-95%)",
    is_active=False,
    dump_threshold_price=27.49,
    dump_date="2026-07-24",
    notes="Chu kỳ hoàn tất: Đỉnh $49.99 (29.1x), sụt giảm -95% về $1.287 và đã xác nhận dump toàn diện."
)
reg.campaigns["DEXEUSDT"] = dexe_campaign
reg.save()
print("[2/2] Updated DEXE in active_pumps_registry.json: Marked as DUMP_CONFIRMED.")
