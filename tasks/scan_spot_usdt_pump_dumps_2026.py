# -*- coding: utf-8 -*-
"""
High-Speed Concurrent Market Scanner for Binance 2026 Pump & Dump Cycles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scans all 400+ Binance USDT spot & futures pairs concurrently with ThreadPoolExecutor.
Applies Base LOW -> Macro Peak HIGH -> Post-Peak Dump State algorithm.
Saves all verified events (n >= 2.5x) to data/pump_events_db.json.
"""

import sys, os, time, json, urllib.request
import concurrent.futures
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from packages.core_engine.classifier import is_stablecoin, is_stock_or_etf
from packages.core_engine.pump_multiplier_classifier import (
    PumpDatasetBuilder,
    PumpEvent,
    PriceTierClassifier,
)
from packages.core_engine.pump_lifecycle_tracker import (
    PumpLifecycleRegistry,
    PumpCampaign,
    PumpStage,
)


def fetch_and_analyze_symbol(symbol: str) -> Optional[Tuple[PumpEvent, Optional[PumpCampaign]]]:
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=365"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            klines = json.loads(resp.read().decode())
    except Exception:
        return None

    if not klines or len(klines) < 20:
        return None

    parsed = []
    for k in klines:
        d = datetime.fromtimestamp(int(k[0]) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        parsed.append({
            "date":      d,
            "open":      float(k[1]),
            "high":      float(k[2]),
            "low":       float(k[3]),
            "close":     float(k[4]),
            "vol_quote": float(k[7]),
        })

    target = [c for c in parsed if c["date"].startswith("2026")]
    if len(target) < 15:
        target = parsed

    if len(target) < 10:
        return None

    best_event = None
    best_campaign = None
    max_n = 0.0

    current_price = target[-1]["close"]
    clf = PriceTierClassifier()

    for i in range(len(target) - 3):
        base_window = target[max(0, i - 30): i + 1]
        base_low = min(c["low"] for c in base_window)

        if target[i]["low"] > base_low * 1.15:
            continue

        forward_window = target[i + 1:]
        if not forward_window:
            continue

        peak_high = max(c["high"] for c in forward_window)
        peak_idx  = i + 1 + max(idx for idx, c in enumerate(forward_window) if c["high"] == peak_high)
        peak_date = target[peak_idx]["date"]

        n = peak_high / max(base_low, 1e-12)

        if n >= 2.5 and n > max_n:
            max_n = n

            base_vol_avg = sum(c["vol_quote"] for c in base_window) / max(len(base_window), 1)
            pump_move_window = target[i + 1: peak_idx + 1]
            pump_vol_total = sum(c["vol_quote"] for c in pump_move_window)
            vol_spike = pump_vol_total / max(base_vol_avg * len(pump_move_window), 1.0)
            duration_h = len(pump_move_window) * 24.0

            tier = clf.classify(base_low)

            post_peak_window = target[peak_idx:]
            lowest_post_peak = min(c["low"] for c in post_peak_window) if post_peak_window else current_price
            drawdown_from_peak = (peak_high - current_price) / max(peak_high, 1e-12) * 100.0
            max_drawdown_post_peak = (peak_high - lowest_post_peak) / max(peak_high, 1e-12) * 100.0

            days_since_peak = len(post_peak_window)
            if max_drawdown_post_peak >= 45.0 or drawdown_from_peak >= 45.0:
                stage = PumpStage.DUMP_CONFIRMED
                stage_lbl = f"[DUMP] -{drawdown_from_peak:.1f}% off peak"
                is_active = False
                dump_date = target[min(len(target)-1, peak_idx + 5)]["date"]
            elif days_since_peak >= 10 and drawdown_from_peak < 30.0:
                stage = PumpStage.HIGH_CONSOLIDATION
                stage_lbl = "[ACTIVE] Holding Base Wave"
                is_active = True
                dump_date = None
            elif drawdown_from_peak < 15.0:
                stage = PumpStage.ACTIVE_EXPANSION
                stage_lbl = "[ACTIVE] Parabolic Expansion"
                is_active = True
                dump_date = None
            else:
                stage = PumpStage.EXHAUSTION_WARNING
                stage_lbl = "[WARN] Distribution Risk"
                is_active = True
                dump_date = None

            best_event = PumpEvent(
                symbol=symbol.upper(),
                event_date=target[i]["date"],
                source="api_fetch",
                pre_pump_price=round(base_low, 10),
                pre_pump_mcap_usd=0.0,
                pre_pump_vol_24h=round(base_vol_avg, 2),
                price_tier_code=tier.code,
                price_tier_index=tier.tier_index,
                peak_price=round(peak_high, 10),
                pump_duration_h=duration_h,
                pump_vol_total=round(pump_vol_total, 2),
                vol_spike_ratio=round(vol_spike, 2),
                n_actual=round(n, 2),
                notes=f"Base: ${base_low:.6f} on {target[i]['date']} -> Peak: ${peak_high:.6f} ({n:.1f}x) on {peak_date}. {stage_lbl}",
            )

            best_campaign = PumpCampaign(
                symbol=symbol.upper(),
                origin_date=target[i]["date"],
                origin_bottom_price=round(base_low, 10),
                highest_peak_price=round(peak_high, 10),
                highest_peak_date=peak_date,
                current_price=round(current_price, 10),
                current_n=round(current_price / max(base_low, 1e-12), 2),
                max_n=round(n, 2),
                expected_n_ml=round(n, 2),
                expected_n_low=round(n * 0.6, 2),
                expected_n_high=round(n * 1.5, 2),
                drawdown_from_peak_pct=round(drawdown_from_peak, 1),
                pump_age_days=max(1, len(target) - i),
                stage=stage,
                stage_label_vi=stage_lbl,
                is_active=is_active,
                dump_threshold_price=round(peak_high * 0.55, 10),
                dump_date=dump_date,
                notes=f"Cycle 2026: Base ${base_low:.6f} -> Peak ${peak_high:.6f} ({n:.1f}x). {stage_lbl}",
            )

    if best_event and max_n >= 2.5:
        return best_event, best_campaign
    return None


def main():
    print("=" * 80)
    print("  FAST MULTI-THREADED SCANNER: BINANCE 2026 PUMP & DUMP CYCLES")
    print("=" * 80)

    url = "https://api.binance.com/api/v3/exchangeInfo"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        info = json.loads(resp.read().decode())

    symbols = [
        s["symbol"] for s in info["symbols"]
        if s["quoteAsset"] == "USDT"
        and s["status"] == "TRADING"
        and not is_stablecoin(s["symbol"])
        and not is_stock_or_etf(s["symbol"])
    ]

    print(f"Total candidate pairs: {len(symbols)}")
    print("Starting concurrent scan across all symbols (12 workers)...\n")

    t0 = time.time()
    db = PumpDatasetBuilder()
    existing_events = {e.symbol: e for e in db.load_all()}
    reg = PumpLifecycleRegistry()
    campaigns = dict(reg.campaigns)

    detected_pumps = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(fetch_and_analyze_symbol, symbols))

    for res in results:
        if res:
            ev, camp = res
            existing_events[ev.symbol] = ev
            if camp:
                campaigns[ev.symbol] = camp
            detected_pumps.append(ev)

    elapsed = time.time() - t0
    print(f"Scan completed in {elapsed:.2f} seconds.")
    print(f"Detected {len(detected_pumps)} pump & dump cycles with n >= 2.5x across the market.\n")

    # Sort and display notable pump events
    detected_pumps.sort(key=lambda x: x.n_actual, reverse=True)
    print(f"{'Symbol':<16} {'Base Price':>14} {'Peak Price':>14} {'n (Multiplier)':>16} {'Price Tier':<14}")
    print("-" * 80)
    for ev in detected_pumps[:25]:
        print(f"{ev.symbol:<16} ${ev.pre_pump_price:>13.7f} ${ev.peak_price:>13.7f} {ev.n_actual:>15.2f}x {ev.price_tier_code:<14}")

    # Save to ML Dataset & Registry
    db.save_all(list(existing_events.values()))
    reg.campaigns = campaigns
    reg.save()
    print(f"\nSaved {len(existing_events)} verified events to data/pump_events_db.json.")
    print(f"Saved {len(campaigns)} campaigns to data/active_pumps_registry.json.")


if __name__ == "__main__":
    main()
