# -*- coding: utf-8 -*-
"""
Retry failed symbols + expand 2026 pump event search
-----------------------------------------------------
- Retries symbols that failed due to IP ban
- Adds more 2026 Binance Futures pump candidates
- Lowers min_n threshold from 2.5x to 2.0x
- Also uses multi-day detection (not just single-day peak)

Run:
    python tasks/retry_pump_events_2026.py
"""

import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from packages.exchange_connectors.binance_client import BinanceFuturesConnector
from packages.core_engine.pump_multiplier_classifier import (
    PumpDatasetBuilder,
    PumpEvent,
    PriceTierClassifier,
)

# ─────────────────────────────────────────────────────────
# KNOWN CIRCULATING SUPPLY (for mcap estimation)
# ─────────────────────────────────────────────────────────
KNOWN_SUPPLY: dict = {
    "BANKUSDT":   1_000_000_000,
    "TUTUSDT":    5_000_000_000,
    "SYNUSDT":      250_000_000,
    "DOGSUSDT":  10_000_000_000,
    "TURBOUSDT": 10_000_000_000,
    "NOTUSDT":   10_000_000_000,
    "KOMAUSDT":   5_000_000_000,
    "ACTUSDT":    1_000_000_000,
    "CHZUSDT":    9_000_000_000,
    "MEMEUSDT":   6_000_000_000,
    "HMSTRUSDT":  1_500_000_000,
    "NEIROUSDT":  6_900_000_000,
    "PNUTUSDT":   1_000_000_000,
    "AIOTOUSDT":    300_000_000,
    "GIGAUSDT":      42_000_000,
    "BUBBUSDT":     800_000_000,
    "MOTHUSDT":     500_000_000,
    # New 2026 expanded candidates
    "CATIUSDT":   5_000_000_000,
    "GOATUSDT":   1_000_000_000,
    "GRIFFAINUSDT": 1_000_000_000,
    "ORCAUSDT":     100_000_000,
    "LPTUSDT":       30_000_000,
    "ENAUSDT":    1_500_000_000,
    "TAOUSDT":       10_000_000,
    "FETUSDT":    1_200_000_000,
    "RENDERUSDT":   400_000_000,
    "WIFUSDT":    1_000_000_000,
    "BOMEUSDT":  69_000_000_000,
    "SLEEPUSDT":  1_000_000_000,
    "POPCAT":       1_000_000_000,
    "POPCATUSDT": 1_000_000_000,
    "MEWUSDT":   69_000_000_000,
    "BONKUSDT":  93_000_000_000_000,
    "WIFUSDT":    1_000_000_000,
    "FLOKIUSDT": 10_000_000_000_000,
    "1000BONKUSDT": 93_000_000_000,
    "1000SHIBUSDT": 589_000_000_000,
    "1000FLOKIUSDT": 10_000_000_000,
    "1000PEPEUSDT": 420_000_000_000,
    "SXPUSDT":      300_000_000,
    "ARPAUSDT":   1_500_000_000,
    "LEVERUSDT": 10_000_000_000,
    "BEAMUSDT":  10_000_000_000,
    "YGGUSDT":      200_000_000,
    "DEGOUSDT":     200_000_000,
    "IOTAUSDT":   3_000_000_000,
    "HIVEUSDT":     400_000_000,
    "XVGUSDT":  68_000_000_000,
    "ZKUSDT":    3_675_000_000,
    "ZROUSDT":     220_000_000,
    "LAYERUSDT":   500_000_000,
    "MNTUSDT":   3_000_000_000,
    "PIXELUSDT": 1_000_000_000,
    "PORTALUSDT":   500_000_000,
    "PDAUSDT":     500_000_000,
    "AERGOUSDT":     50_000_000,
    "CRVUSDT":     900_000_000,
    "PEOPLEUSDT":5_000_000_000,
}


def _estimate_mcap(symbol: str, price: float) -> float:
    supply = KNOWN_SUPPLY.get(symbol.upper(), 0)
    return round(supply * price, 2) if supply else 0.0


# ─────────────────────────────────────────────────────────
# IMPROVED MULTI-WINDOW DETECTION
# ─────────────────────────────────────────────────────────

def detect_best_pump(
    symbol: str,
    klines: list,
    min_n: float = 2.0,
    lookback_days: int = 5,
    year_filter: str = "2026",
) -> Optional[PumpEvent]:
    """
    Detect the strongest pump in klines using three complementary windows:
      - Single-day max pct gain (fast pump)
      - 3-day rolling max / min ratio (medium pump)
      - 7-day rolling max / min ratio (slow accumulation pump)
    Returns the event with the highest n among all windows.
    """
    if len(klines) < lookback_days + 2:
        return None

    parsed = []
    for k in klines:
        ts = int(k[0])
        date_str = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        parsed.append({
            "date":      date_str,
            "open":      float(k[1]),
            "high":      float(k[2]),
            "low":       float(k[3]),
            "close":     float(k[4]),
            "vol_quote": float(k[7]),
        })

    target = [c for c in parsed if c["date"].startswith(year_filter)]
    if len(target) < lookback_days + 2:
        target = parsed

    clf = PriceTierClassifier()
    best_event: Optional[PumpEvent] = None
    best_n = 0.0

    # --- Window scan ---
    for window_size in (1, 3, 7):
        for i in range(lookback_days, len(target) - window_size + 1):
            pre_window  = target[max(0, i - lookback_days): i]
            pump_window = target[i: i + window_size]

            pre_price   = pre_window[-1]["close"]
            if pre_price <= 0:
                continue

            peak_price     = max(c["high"] for c in pump_window)
            n_actual       = peak_price / pre_price
            avg_vol_pre    = sum(c["vol_quote"] for c in pre_window) / max(len(pre_window), 1)
            pump_vol_total = sum(c["vol_quote"] for c in pump_window)
            vol_spike      = pump_vol_total / max(avg_vol_pre, 1.0)

            if n_actual < min_n:
                continue

            if n_actual > best_n:
                best_n = n_actual
                tier   = clf.classify(pre_price)
                # Find the single day with highest % gain in pump window
                ignition_idx = i
                best_day_pct = 0.0
                for di, day in enumerate(pump_window):
                    prev = target[i + di - 1]["close"] if (i + di) > 0 else pre_price
                    pct  = (day["close"] - prev) / max(prev, 1e-12) * 100
                    if pct > best_day_pct:
                        best_day_pct = pct
                        ignition_idx = i + di

                best_event = PumpEvent(
                    symbol            = symbol.upper(),
                    event_date        = target[ignition_idx]["date"],
                    source            = "api_fetch",
                    pre_pump_price    = round(pre_price, 10),
                    pre_pump_mcap_usd = _estimate_mcap(symbol, pre_price),
                    pre_pump_vol_24h  = round(avg_vol_pre, 2),
                    price_tier_code   = tier.code,
                    price_tier_index  = tier.tier_index,
                    peak_price        = round(peak_price, 10),
                    pump_duration_h   = 24.0 * window_size,
                    pump_vol_total    = round(pump_vol_total, 2),
                    vol_spike_ratio   = round(vol_spike, 2),
                    n_actual          = round(n_actual, 4),
                    notes             = (
                        f"Window={window_size}d, best gain={best_day_pct:.1f}% "
                        f"on {target[ignition_idx]['date']}"
                    ),
                )

    return best_event


# ─────────────────────────────────────────────────────────
# TARGET SYMBOLS — Retry + Expanded
# ─────────────────────────────────────────────────────────

RETRY_SYMBOLS = [
    # Previously failed (rate-limited)
    "BANKUSDT", "TUTUSDT", "DOGSUSDT", "TURBOUSDT", "NOTUSDT",
    "KOMAUSDT", "ACTUSDT", "CHZUSDT",
]

EXPANDED_SYMBOLS = [
    # 2026 AI/DeFi pumps
    "ENAUSDT", "TAOUSDT", "FETUSDT", "RENDERUSDT", "LPTUSDT",
    # Meme pumps 2026
    "1000PEPEUSDT", "1000BONKUSDT", "WIFUSDT", "POPCATUSDT",
    "1000FLOKIUSDT", "MEWUSDT", "BOMEUSDT", "1000SHIBUSDT",
    # Layer 2 / DeFi 2026
    "ZKUSDT", "ZROUSDT", "LAYERUSDT", "MNTUSDT",
    "PIXELUSDT", "PORTALUSDT",
    # Small cap 2026 movers
    "AERGOUSDT", "CRVUSDT", "PEOPLEUSDT", "ARPAUSDT",
    "LEVERUSDT", "BEAMUSDT", "YGGUSDT", "SXPUSDT",
    "IOTAUSDT", "HIVEUSDT", "CATIUSDT",
]


def main():
    print("=" * 60)
    print("  Pump Events Retry + Expand - 2026")
    print("=" * 60)

    connector = BinanceFuturesConnector()
    db = PumpDatasetBuilder()

    # Show current state
    summary = db.summary()
    print(f"\nCurrent DB: {summary.get('count', 0)} events")

    all_targets = RETRY_SYMBOLS + EXPANDED_SYMBOLS
    print(f"Processing {len(all_targets)} symbols (min_n=2.0x, multi-window detection)\n")

    found:  list[PumpEvent] = []
    failed: list[str] = []

    for sym in all_targets:
        try:
            klines = connector.client.futures_klines(
                symbol=sym, interval="1d", limit=200
            )
            event = detect_best_pump(sym, klines, min_n=2.0, lookback_days=5)
            if event:
                tier_label = f"T{event.price_tier_index}({event.price_tier_code})"
                print(f"  [OK] {sym:<22} n={event.n_actual:>7.2f}x  "
                      f"pre=${event.pre_pump_price:<12.8f} {tier_label:<22} {event.event_date}")
                found.append(event)
            else:
                print(f"  [--] {sym:<22} No pump >= 2.0x detected in 2026")
            time.sleep(0.15)
        except Exception as ex:
            err = str(ex)[:60]
            print(f"  [ER] {sym:<22} {err}")
            failed.append(sym)
            time.sleep(1.5)

    # Seed
    print(f"\nSeeding {len(found)} new events...")
    added = db.add_events_bulk(found, deduplicate=True)
    print(f"Added {added} new (dupes skipped).")

    summary = db.summary()
    print(f"\n== Final DB Summary ==")
    print(f"  Total : {summary['count']} events")
    if summary["count"] > 0:
        print(f"  n     : {summary['n_min']}x - {summary['n_max']}x  (mean {summary['n_mean']}x)")
        print("  Tiers :")
        for code, cnt in sorted(summary.get("by_tier", {}).items()):
            print(f"    {code:<16}: {cnt}")
    if failed:
        print(f"\n  Still failed: {', '.join(failed)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
