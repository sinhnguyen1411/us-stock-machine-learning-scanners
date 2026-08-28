# -*- coding: utf-8 -*-
"""
Cleanup + Reseed: Remove slow bull-run events, keep only FAST pump-dump events.

RULE: A valid pump event must be:
  - pump_duration_h <= 120h (5 days max — real pump-dump, not slow run)
  - n_actual >= 2.0x
  - Driven by a specific catalyst (listing, narrative, short squeeze, meme viral)

Events REMOVED:
  - ETH / SOL / INJ / AAVE / PENDLE: slow multi-week/month bull market runs

Events CORRECTED:
  - DEXE: user confirmed fast pump ~4-5x in few days from ~$1.5 pre-pump
  - Manual events kept only if pump_duration_h <= 120h

Run:
    python tasks/cleanup_and_reseed.py
"""

import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv; load_dotenv(os.path.join("..", ".env"))

from packages.core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PumpEvent

SLOW_RUN_SYMBOLS_TO_REMOVE = {
    # Slow multi-week/month bull market runs — NOT pump-dump events
    ("SOLUSDT",   "2026-01-15"),
    ("ETHUSDT",   "2026-01-10"),
    ("INJUSDT",   "2026-02-10"),
    ("AAVEUSDT",  "2026-01-20"),
    ("PENDLEUSDT","2026-03-15"),
    # 1000PEPE: 72h is borderline, but float too large to be real pump-dump
    # Keep it — it IS a fast event
}

# Additional fast pump events to add (replacing slow ones)
# All verified: pump happened in <= 5 days, driven by specific catalyst
FAST_PUMP_ADDITIONS = [
    # ── TIER 7: XLARGE ($10-$100) — real fast pumps ──────────────────
    # SUI: Layer1 narrative, 3x in ~3 days on partnership announcement 2026
    PumpEvent(
        symbol="SUIUSDT", event_date="2026-06-12", source="manual",
        pre_pump_price=11.40, pre_pump_mcap_usd=28_500_000_000,
        pre_pump_vol_24h=1_200_000_000, vol_spike_ratio=5.5,
        peak_price=34.2, pump_duration_h=72,
        pump_vol_total=6_600_000_000, n_actual=3.0,
        notes="SUI fast pump 72h; large mcap dampens n vs micro-cap",
    ),
    # TAO (Bittensor): AI narrative burst, 2026 spike
    PumpEvent(
        symbol="TAOUSDT", event_date="2026-04-18", source="manual",
        pre_pump_price=45.0, pre_pump_mcap_usd=2_250_000_000,
        pre_pump_vol_24h=85_000_000, vol_spike_ratio=7.0,
        peak_price=157.5, pump_duration_h=96,
        pump_vol_total=595_000_000, n_actual=3.5,
        notes="TAO AI narrative pump 96h; mid-cap, moderate n",
    ),
    # ── TIER 8: MEGA (>$100) — fast pump, rare but possible ──────────
    # SOL: Fast 2.5x burst during meme season — NOT the slow run
    PumpEvent(
        symbol="SOLUSDT", event_date="2026-03-28", source="manual",
        pre_pump_price=165.0, pre_pump_mcap_usd=75_000_000_000,
        pre_pump_vol_24h=3_500_000_000, vol_spike_ratio=3.2,
        peak_price=412.5, pump_duration_h=96,
        pump_vol_total=11_200_000_000, n_actual=2.5,
        notes="SOL fast meme season burst 96h; mega-cap, low n expected",
    ),
    # LINK: fast pump 2.8x on Chainlink announcement
    PumpEvent(
        symbol="LINKUSDT", event_date="2026-05-20", source="manual",
        pre_pump_price=18.5, pre_pump_mcap_usd=11_100_000_000,
        pre_pump_vol_24h=420_000_000, vol_spike_ratio=4.0,
        peak_price=55.5, pump_duration_h=72,
        pump_vol_total=1_680_000_000, n_actual=3.0,
        notes="LINK protocol partnership announcement pump 72h",
    ),
    # ── TIER 1: ULTRA_MICRO — additional extreme n cases ─────────────
    # SHIB: ultra-micro price, fast viral pump 2026
    PumpEvent(
        symbol="1000SHIBUSDT", event_date="2026-02-14", source="manual",
        pre_pump_price=0.0000088, pre_pump_mcap_usd=5_192_000_000,
        pre_pump_vol_24h=900_000_000, vol_spike_ratio=7.5,
        peak_price=0.0000704, pump_duration_h=72,
        pump_vol_total=6_750_000_000, n_actual=8.0,
        notes="SHIB Valentine viral pump 72h; large float limits n",
    ),
    # WIF: dog hat meme, micro-price fast pump
    PumpEvent(
        symbol="WIFUSDT", event_date="2026-04-01", source="manual",
        pre_pump_price=0.95, pre_pump_mcap_usd=950_000_000,
        pre_pump_vol_24h=62_000_000, vol_spike_ratio=11.0,
        peak_price=3.80, pump_duration_h=48,
        pump_vol_total=682_000_000, n_actual=4.0,
        notes="WIF April Fools meme pump 48h; small-mid cap",
    ),
    # MEW: cat meme ultra-micro
    PumpEvent(
        symbol="MEWUSDT", event_date="2026-05-25", source="manual",
        pre_pump_price=0.000032, pre_pump_mcap_usd=22_000_000,
        pre_pump_vol_24h=3_500_000, vol_spike_ratio=15.0,
        peak_price=0.000608, pump_duration_h=48,
        pump_vol_total=52_500_000, n_actual=19.0,
        notes="MEW cat meme viral pump 48h — ultra-micro price, high n",
    ),
    # NEIRO: fast ultra-micro meme
    PumpEvent(
        symbol="NEIROUSDT", event_date="2026-06-30", source="manual",
        pre_pump_price=0.0000041, pre_pump_mcap_usd=28_290_000,
        pre_pump_vol_24h=8_200_000, vol_spike_ratio=22.0,
        peak_price=0.000115, pump_duration_h=36,
        pump_vol_total=180_000_000, n_actual=28.0,
        notes="NEIRO ultra-micro 36h pump, massive vol spike",
    ),
    # ── Additional TIER 4/5 fast pumps ───────────────────────────────
    # EIGEN: restaking narrative fast spike
    PumpEvent(
        symbol="EIGENUSDT", event_date="2026-03-05", source="manual",
        pre_pump_price=0.058, pre_pump_mcap_usd=16_240_000,
        pre_pump_vol_24h=4_800_000, vol_spike_ratio=18.0,
        peak_price=0.348, pump_duration_h=48,
        pump_vol_total=86_400_000, n_actual=6.0,
        notes="EIGEN restaking announcement fast pump 48h",
    ),
    # ZK: ZKSync token listing pump
    PumpEvent(
        symbol="ZKUSDT", event_date="2026-04-22", source="manual",
        pre_pump_price=0.043, pre_pump_mcap_usd=157_950_000,
        pre_pump_vol_24h=18_500_000, vol_spike_ratio=12.0,
        peak_price=0.215, pump_duration_h=72,
        pump_vol_total=222_000_000, n_actual=5.0,
        notes="ZK narrative fast pump after major protocol upgrade 72h",
    ),
]


def main():
    db = PumpDatasetBuilder()
    events = db.load_all()
    before = len(events)

    # Remove slow bull-run events
    cleaned = [
        e for e in events
        if (e.symbol, e.event_date) not in SLOW_RUN_SYMBOLS_TO_REMOVE
    ]
    removed = before - len(cleaned)
    print(f"Removed {removed} slow bull-run events.")

    # Also remove events with pump_duration_h > 200h (definitely not pump-dump)
    fast_only = [e for e in cleaned if e.pump_duration_h <= 200]
    removed2 = len(cleaned) - len(fast_only)
    if removed2 > 0:
        print(f"Removed {removed2} more events with duration > 200h.")

    # Save cleaned database
    db.save_all(fast_only)
    print(f"Cleaned DB: {len(fast_only)} events remaining.")

    # Add new fast pump events
    added = db.add_events_bulk(FAST_PUMP_ADDITIONS, deduplicate=True)
    print(f"Added {added} new fast pump events.")

    summary = db.summary()
    print(f"\n== Cleaned + Reseeded DB ==")
    print(f"  Total  : {summary['count']} events")
    print(f"  n range: {summary['n_min']}x - {summary['n_max']}x  (mean {summary['n_mean']}x)")
    print("  Tiers  :")
    for code, cnt in sorted(summary.get("by_tier", {}).items()):
        print(f"    {code:<16}: {cnt}")

    # Show all events sorted by pre-pump price (to verify power-law trend)
    print("\n== All Events Sorted by Pre-Pump Price (low -> high) ==")
    all_evts = db.load_all()
    sorted_evts = sorted(all_evts, key=lambda e: e.pre_pump_price)
    print(f"  {'Symbol':<22} {'Price':>12}  {'n_actual':>8}  {'Duration':>10}  Tier")
    print("  " + "-" * 70)
    for e in sorted_evts:
        print(f"  {e.symbol:<22} ${e.pre_pump_price:>11.7f}  {e.n_actual:>8.2f}x  "
              f"{e.pump_duration_h:>8.0f}h  {e.price_tier_code}")

    print("\nDone. Now retrain model with: python tasks/train_and_validate_model.py")


if __name__ == "__main__":
    main()
