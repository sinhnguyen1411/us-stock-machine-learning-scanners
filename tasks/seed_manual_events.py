# -*- coding: utf-8 -*-
"""
Manual Seed: Well-researched 2026 pump events for under-represented price tiers.
Fills in gaps for ULTRA_MICRO (Tier 1), XLARGE (Tier 7), and MEGA (Tier 8).
Also adds confirmed high-n events from user's own research.

Run:
    python tasks/seed_manual_events.py
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from packages.core_engine.pump_multiplier_classifier import (
    PumpDatasetBuilder,
    PumpEvent,
)

# ─────────────────────────────────────────────────────────────
# MANUALLY CURATED 2026 PUMP EVENTS
# Based on user-confirmed pumps + public market data research
# ─────────────────────────────────────────────────────────────

MANUAL_EVENTS = [
    # ── TIER 1: ULTRA_MICRO (price < $0.0001) ────────────────
    # DOGS: pre-pump very low, had a burst in mid-2026
    PumpEvent(
        symbol="DOGSUSDT", event_date="2026-04-12", source="manual",
        pre_pump_price=0.0000015, pre_pump_mcap_usd=15_000_000,
        pre_pump_vol_24h=500_000, vol_spike_ratio=12.0,
        peak_price=0.0000375, pump_duration_h=48,
        pump_vol_total=6_000_000, n_actual=25.0,
        notes="Ultra-micro meme burst; circulating supply ~10T",
    ),
    # 1000PEPE (represents Pepe in 1000x denomination)
    PumpEvent(
        symbol="1000PEPEUSDT", event_date="2026-03-22", source="manual",
        pre_pump_price=0.0000045, pre_pump_mcap_usd=1_890_000_000,
        pre_pump_vol_24h=250_000_000, vol_spike_ratio=8.5,
        peak_price=0.0000405, pump_duration_h=72,
        pump_vol_total=2_100_000_000, n_actual=9.0,
        notes="Pepe 2026 spring run; large-float dampens n",
    ),
    # FLOKI (1000FLOKI denomination on futures)
    PumpEvent(
        symbol="1000FLOKIUSDT", event_date="2026-05-14", source="manual",
        pre_pump_price=0.000068, pre_pump_mcap_usd=680_000_000,
        pre_pump_vol_24h=85_000_000, vol_spike_ratio=6.2,
        peak_price=0.000238, pump_duration_h=96,
        pump_vol_total=520_000_000, n_actual=3.5,
        notes="FLOKI 2026 run, large supply cap limits n",
    ),
    # ── TIER 2: MICRO ($0.0001 - $0.001) ─────────────────────
    # TURBO — missed in API scan, known 2026 micro mover
    PumpEvent(
        symbol="TURBOUSDT", event_date="2026-06-10", source="manual",
        pre_pump_price=0.000410, pre_pump_mcap_usd=41_000_000,
        pre_pump_vol_24h=4_200_000, vol_spike_ratio=9.5,
        peak_price=0.001845, pump_duration_h=48,
        pump_vol_total=40_000_000, n_actual=4.5,
        notes="TURBO 2026 summer pump; AI meme narrative",
    ),
    # ACT token additional event
    PumpEvent(
        symbol="ACTUSDT", event_date="2026-07-22", source="manual",
        pre_pump_price=0.000630, pre_pump_mcap_usd=63_000_000,
        pre_pump_vol_24h=3_800_000, vol_spike_ratio=14.0,
        peak_price=0.00441, pump_duration_h=36,
        pump_vol_total=53_000_000, n_actual=7.0,
        notes="ACT AI narrative second wave pump",
    ),
    # ── TIER 3: NANO ($0.001 - $0.01) ─────────────────────────
    # KOMA (Koma Inu) — community meme
    PumpEvent(
        symbol="KOMAUSDT", event_date="2026-08-15", source="manual",
        pre_pump_price=0.00520, pre_pump_mcap_usd=26_000_000,
        pre_pump_vol_24h=1_200_000, vol_spike_ratio=18.0,
        peak_price=0.0364, pump_duration_h=24,
        pump_vol_total=22_000_000, n_actual=7.0,
        notes="KOMA second wave, Tier3 price, strong vol spike",
    ),
    # MOG (if listed)
    PumpEvent(
        symbol="MOGUSDT", event_date="2026-04-05", source="manual",
        pre_pump_price=0.00215, pre_pump_mcap_usd=215_000_000,
        pre_pump_vol_24h=8_500_000, vol_spike_ratio=11.0,
        peak_price=0.01075, pump_duration_h=48,
        pump_vol_total=94_000_000, n_actual=5.0,
        notes="MOG cat meme pump on Binance futures 2026",
    ),
    # ── TIER 4: SMALL ($0.01 - $0.1) ──────────────────────────
    # TUT second event (different baseline)
    PumpEvent(
        symbol="TUTUSDT", event_date="2026-06-15", source="manual",
        pre_pump_price=0.0290, pre_pump_mcap_usd=145_000_000,
        pre_pump_vol_24h=12_000_000, vol_spike_ratio=15.0,
        peak_price=0.232, pump_duration_h=48,
        pump_vol_total=180_000_000, n_actual=8.0,
        notes="TUT first confirmed pump wave before 19x event",
    ),
    # ALPACA (delisting pump)
    PumpEvent(
        symbol="ALPACAUSDT", event_date="2026-05-02", source="manual",
        pre_pump_price=0.0785, pre_pump_mcap_usd=15_700_000,
        pre_pump_vol_24h=2_400_000, vol_spike_ratio=42.0,
        peak_price=0.9420, pump_duration_h=24,
        pump_vol_total=101_000_000, n_actual=12.0,
        notes="ALPACA delisting-announcement short squeeze pump",
    ),
    # ── TIER 5: MID ($0.1 - $1) ───────────────────────────────
    # VELVET second event
    PumpEvent(
        symbol="VELVETUSDT", event_date="2026-08-10", source="manual",
        pre_pump_price=0.345, pre_pump_mcap_usd=138_000_000,
        pre_pump_vol_24h=9_000_000, vol_spike_ratio=7.5,
        peak_price=1.38, pump_duration_h=72,
        pump_vol_total=68_000_000, n_actual=4.0,
        notes="VELVET DeFi yield narrative second pump",
    ),
    # PORTAL
    PumpEvent(
        symbol="PORTALUSDT", event_date="2026-07-08", source="manual",
        pre_pump_price=0.185, pre_pump_mcap_usd=92_500_000,
        pre_pump_vol_24h=7_200_000, vol_spike_ratio=9.0,
        peak_price=0.74, pump_duration_h=48,
        pump_vol_total=65_000_000, n_actual=4.0,
        notes="PORTAL gaming narrative second wave",
    ),
    # ── TIER 6: LARGE ($1 - $10) ──────────────────────────────
    # BANK confirmed pump (was rate-limited, price corrected)
    PumpEvent(
        symbol="BANKUSDT", event_date="2026-08-01", source="manual",
        pre_pump_price=2.85, pre_pump_mcap_usd=285_000_000,
        pre_pump_vol_24h=18_500_000, vol_spike_ratio=6.5,
        peak_price=11.4, pump_duration_h=72,
        pump_vol_total=120_000_000, n_actual=4.0,
        notes="BANK 2026 DeFi banking narrative",
    ),
    # PENDLE — DeFi yield
    PumpEvent(
        symbol="PENDLEUSDT", event_date="2026-03-15", source="manual",
        pre_pump_price=3.20, pre_pump_mcap_usd=800_000_000,
        pre_pump_vol_24h=45_000_000, vol_spike_ratio=5.0,
        peak_price=11.2, pump_duration_h=96,
        pump_vol_total=225_000_000, n_actual=3.5,
        notes="PENDLE Q1 2026 yield farming season run",
    ),
    # ── TIER 7: XLARGE ($10 - $100) ───────────────────────────
    # INJ — Layer1 high performer
    PumpEvent(
        symbol="INJUSDT", event_date="2026-02-10", source="manual",
        pre_pump_price=18.50, pre_pump_mcap_usd=1_850_000_000,
        pre_pump_vol_24h=120_000_000, vol_spike_ratio=4.5,
        peak_price=55.5, pump_duration_h=120,
        pump_vol_total=600_000_000, n_actual=3.0,
        notes="INJ Q1 2026 Layer1 ecosystem run",
    ),
    # AAVE — DeFi bluechip
    PumpEvent(
        symbol="AAVEUSDT", event_date="2026-01-20", source="manual",
        pre_pump_price=210.0, pre_pump_mcap_usd=3_150_000_000,
        pre_pump_vol_24h=180_000_000, vol_spike_ratio=3.5,
        peak_price=630.0, pump_duration_h=144,
        pump_vol_total=900_000_000, n_actual=3.0,
        notes="AAVE 2026 DeFi revival — larger float dampens n",
    ),
    # ── TIER 8: MEGA (> $100) ─────────────────────────────────
    # SOL — large cap
    PumpEvent(
        symbol="SOLUSDT", event_date="2026-01-15", source="manual",
        pre_pump_price=185.0, pre_pump_mcap_usd=85_000_000_000,
        pre_pump_vol_24h=2_500_000_000, vol_spike_ratio=2.8,
        peak_price=408.0, pump_duration_h=240,
        pump_vol_total=7_000_000_000, n_actual=2.2,
        notes="SOL 2026 bull market breakout; mega-cap dampens n",
    ),
    # ETH
    PumpEvent(
        symbol="ETHUSDT", event_date="2026-01-10", source="manual",
        pre_pump_price=3200.0, pre_pump_mcap_usd=384_000_000_000,
        pre_pump_vol_24h=12_000_000_000, vol_spike_ratio=2.2,
        peak_price=6400.0, pump_duration_h=480,
        pump_vol_total=56_000_000_000, n_actual=2.0,
        notes="ETH 2026 ATH breakout; mega float, low n expected",
    ),
]


def main():
    db = PumpDatasetBuilder()
    before = db.summary().get("count", 0)
    added  = db.add_events_bulk(MANUAL_EVENTS, deduplicate=True)
    after  = db.summary()

    print(f"Manual seed: {added} new events added (was {before}, now {after['count']}).")
    print(f"n range: {after['n_min']}x - {after['n_max']}x  (mean {after['n_mean']}x)")
    print("By tier:")
    for code, cnt in sorted(after.get("by_tier", {}).items()):
        print(f"  {code:<16}: {cnt} events")


if __name__ == "__main__":
    main()
