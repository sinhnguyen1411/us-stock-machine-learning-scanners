# -*- coding: utf-8 -*-
"""
Fetch + Re-detect 2026 Pump Events from Binance USD-M Futures
-------------------------------------------------------------
METHODOLOGY (corrected):

  pre_pump_price = lowest LOW candle in the accumulation base
                   (true bottom, NOT average close)
  peak_price     = highest HIGH candle reached AFTER that bottom,
                   scanning the full subsequent pump move
  n              = peak_price / pre_pump_price  (true multiplier)

Validated against user-confirmed data:
  AKE: bottom $0.0001729, peak $0.0163 -> n = 94.3x

Run:
    python tasks/fetch_pump_events_2026.py
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


# ══════════════════════════════════════════════════════════════
# CORRECT PUMP DETECTION ALGORITHM
# ══════════════════════════════════════════════════════════════

def detect_true_pump(
    symbol: str,
    klines: list,
    year_filter: str = "2026",
    base_lookback: int = 30,    # days to scan for accumulation base
    peak_forward:  int = 60,    # max days after bottom to look for peak
    min_n:         float = 3.0, # minimum meaningful pump multiplier
) -> Optional[PumpEvent]:
    """
    Detect the TRUE pump event:
      1. Find the local minimum LOW (true accumulation bottom)
         in a rolling window across all 2026 candles
      2. After that bottom, find the absolute maximum HIGH
         within peak_forward days (true pump peak)
      3. n = true_peak_high / true_bottom_low

    This correctly captures events like AKE:
      bottom LOW = $0.0001729, peak HIGH = $0.0163 -> n = 94.3x
    """
    if len(klines) < base_lookback + 5:
        return None

    # Parse klines
    parsed = []
    for k in klines:
        date_str = datetime.fromtimestamp(
            int(k[0]) / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        parsed.append({
            "date":      date_str,
            "open":      float(k[1]),
            "high":      float(k[2]),
            "low":       float(k[3]),
            "close":     float(k[4]),
            "vol_quote": float(k[7]),
        })

    # Prefer 2026 data; fall back to full history if insufficient
    target = [c for c in parsed if c["date"].startswith(year_filter)]
    if len(target) < base_lookback + 5:
        target = parsed

    clf = PriceTierClassifier()
    best_event: Optional[PumpEvent] = None
    best_n = 0.0

    # Slide a window: for each candle as potential bottom,
    # look for the maximum peak in the following peak_forward days.
    for bottom_idx in range(base_lookback, len(target) - 3):
        # True bottom = minimum LOW in base_lookback window ending here
        base_window = target[max(0, bottom_idx - base_lookback): bottom_idx + 1]
        true_bottom = min(c["low"] for c in base_window)

        # The bottom must be this candle's LOW (or very close to it)
        # to ensure we are at the actual trough, not mid-way
        if target[bottom_idx]["low"] > true_bottom * 1.15:
            continue   # this candle is not near the bottom

        # True peak = maximum HIGH in peak_forward days after bottom
        forward = target[bottom_idx + 1: min(bottom_idx + 1 + peak_forward, len(target))]
        if not forward:
            continue
        true_peak = max(c["high"] for c in forward)
        peak_idx  = bottom_idx + 1 + max(
            i for i, c in enumerate(forward) if c["high"] == true_peak
        )

        n_actual = true_peak / max(true_bottom, 1e-15)
        if n_actual < min_n:
            continue

        if n_actual > best_n:
            best_n = n_actual

            # Pre-pump baseline: use bottom candle's LOW as pre_pump_price
            pre_pump_price  = true_bottom
            pre_pump_vol_24h = sum(
                c["vol_quote"] for c in base_window
            ) / max(len(base_window), 1)

            pump_window    = target[bottom_idx + 1: peak_idx + 1]
            pump_vol_total = sum(c["vol_quote"] for c in pump_window)
            vol_spike      = pump_vol_total / max(pre_pump_vol_24h, 1.0)
            pump_duration  = len(pump_window) * 24.0

            tier = clf.classify(pre_pump_price)
            best_event = PumpEvent(
                symbol             = symbol.upper(),
                event_date         = target[bottom_idx]["date"],
                source             = "api_fetch",
                pre_pump_price     = round(pre_pump_price, 12),
                pre_pump_mcap_usd  = _estimate_mcap(symbol, pre_pump_price),
                pre_pump_vol_24h   = round(pre_pump_vol_24h, 2),
                price_tier_code    = tier.code,
                price_tier_index   = tier.tier_index,
                peak_price         = round(true_peak, 12),
                pump_duration_h    = pump_duration,
                pump_vol_total     = round(pump_vol_total, 2),
                vol_spike_ratio    = round(vol_spike, 2),
                n_actual           = round(n_actual, 4),
                notes              = (
                    "TrueBottom={} TruePeak={} on {}".format(
                        round(true_bottom, 10),
                        round(true_peak, 10),
                        target[peak_idx]["date"] if peak_idx < len(target) else "?",
                    )
                ),
            )

    return best_event


# ══════════════════════════════════════════════════════════════
# APPROXIMATE CIRCULATING SUPPLY TABLE
# ══════════════════════════════════════════════════════════════

KNOWN_SUPPLY: dict = {
    "AKEUSDT":      200_000_000,
    "DEXEUSDT":      97_000_000,
    "BANKUSDT":   1_000_000_000,
    "TUTUSDT":    5_000_000_000,
    "SYNUSDT":      250_000_000,
    "BTWUSDT":      300_000_000,
    "BEATUSDT":   2_000_000_000,
    "VELVETUSDT":   400_000_000,
    "KOMAUSDT":   5_000_000_000,
    "ACTUSDT":    1_000_000_000,
    "NOTUSDT":   10_000_000_000,
    "BOMEUSDT":  68_000_000_000,
    "PIXELUSDT":  1_000_000_000,
    "PORTALUSDT":   500_000_000,
    "DOGSUSDT":  10_000_000_000,
    "ENAUSDT":    1_500_000_000,
    "APEUSDT":    1_000_000_000,
    "AAVEUSDT":      16_000_000,
    "INJUSDT":      100_000_000,
    "SEIUSDT":    9_000_000_000,
    "JUPUSDT":    1_350_000_000,
    "PENDLEUSDT":   250_000_000,
    "EIGENUSDT":    280_000_000,
    "STRKUSDT":     220_000_000,
    "REZUSDT":    1_000_000_000,
    "WLDUSDT":      200_000_000,
    "TIAUSDT":      300_000_000,
    "ALTUSDT":    1_000_000_000,
    "MOVEUSDT":     500_000_000,
    "THEUSDT":      150_000_000,
    "ZETAUSDT":     600_000_000,
    "SCRUSDT":      300_000_000,
    "VIRTUALUSDT":  900_000_000,
    "KAIAUSDT":     300_000_000,
    "SOLVUSDT":     500_000_000,
    "NEIROUSDT":  6_900_000_000,
    "HMSTRUSDT":  1_500_000_000,
    "MOODENGUSDT":  400_000_000,
    "CVCUSDT":    1_000_000_000,
    "ALPACAUSDT":   200_000_000,
    "CHZUSDT":    9_000_000_000,
}


def _estimate_mcap(symbol: str, price: float) -> float:
    supply = KNOWN_SUPPLY.get(symbol.upper(), 0)
    return round(supply * price, 2) if supply else 0.0


# ══════════════════════════════════════════════════════════════
# TARGET SYMBOLS — User-suggested + API-confirmed from earlier
# ══════════════════════════════════════════════════════════════

TARGET_SYMBOLS = [
    # User-suggested 2026 pumps
    "AKEUSDT", "DEXEUSDT", "BANKUSDT", "TUTUSDT",
    "SYNUSDT", "BTWUSDT", "BEATUSDT", "VELVETUSDT",
    # Previously API-detected (re-fetch with correct algorithm)
    "DOGSUSDT", "NOTUSDT", "BOMEUSDT", "PIXELUSDT",
    "KOMAUSDT", "PORTALUSDT", "ACTUSDT", "ENAUSDT",
    "APEUSDT",
    # Additional 2026 Binance Futures candidates
    "AAVEUSDT", "INJUSDT", "SEIUSDT", "JUPUSDT",
    "PENDLEUSDT", "EIGENUSDT", "STRKUSDT", "WLDUSDT",
    "THEUSDT", "ZETAUSDT", "ALTUSDT", "MOVEUSDT",
    "SCRUSDT", "SOLVUSDT", "NEIROUSDT", "HMSTRUSDT",
    "MOODENGUSDT", "KAIAUSDT", "VIRTUALUSDT", "REZUSDT",
    "CVCUSDT", "ALPACAUSDT", "TIAUSDT",
]


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  Binance Futures Pump Event Fetcher — Corrected Algorithm")
    print("=" * 65)
    print()
    print("  Methodology:")
    print("  - pre_pump_price = TRUE bottom LOW (accumulation minimum)")
    print("  - peak_price     = TRUE peak HIGH after that bottom")
    print("  - n              = peak_price / pre_pump_price")
    print()
    print("  Validation: AKE bottom=$0.0001729 peak=$0.0163 -> n~94x")
    print()

    connector = BinanceFuturesConnector()
    db        = PumpDatasetBuilder()

    # Start fresh — only real re-fetched data
    print("[1/2] Fetching klines for {} symbols...".format(len(TARGET_SYMBOLS)))
    print()

    found:  list = []
    failed: list = []

    for sym in TARGET_SYMBOLS:
        try:
            klines = connector.client.futures_klines(
                symbol=sym, interval="1d", limit=365
            )
            event = detect_true_pump(
                sym, klines,
                year_filter  = "2026",
                base_lookback= 30,
                peak_forward = 90,
                min_n        = 2.0,
            )
            if event:
                print("  [OK] {:22s} n={:>8.2f}x  bottom=${:<14.8f}  peak=${:<14.8f}  {}".format(
                    sym,
                    event.n_actual,
                    event.pre_pump_price,
                    event.peak_price,
                    event.event_date,
                ))
                found.append(event)
            else:
                print("  [--] {:22s} No pump >= 2.0x found in 2026".format(sym))
            time.sleep(0.15)
        except Exception as ex:
            print("  [ER] {:22s} {}".format(sym, str(ex)[:70]))
            failed.append(sym)
            time.sleep(1.0)

    # Clear old data, save fresh results
    print()
    print("[2/2] Saving {} verified events to database...".format(len(found)))
    db.save_all(found)   # replace all — only real data

    s = db.summary()
    print()
    print("== Final DB ==")
    print("  Total  : {} events".format(s.get("count", 0)))
    if s.get("count", 0) > 0:
        print("  n range: {}x - {}x  (mean {}x)".format(
            s.get("n_min"), s.get("n_max"), s.get("n_mean")))
        print("  Tiers  :")
        for code, cnt in sorted(s.get("by_tier", {}).items()):
            print("    {:16s}: {}".format(code, cnt))

    if failed:
        print()
        print("  Failed: {}".format(", ".join(failed)))

    print()
    print("Done. Next: python tasks/train_and_validate_model.py")


if __name__ == "__main__":
    main()
