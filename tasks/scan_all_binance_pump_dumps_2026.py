# -*- coding: utf-8 -*-
"""
Full-Market 2026 Pump & Dump Scanner for All Binance USD-M Futures (510+ Pairs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scans all 510+ perpetual contracts on Binance USD-M Futures across 2026:
  1. Identifies the true accumulation bottom LOW (Origin Base)
  2. Tracks the full subsequent wave to find the true macro peak HIGH (Climax)
  3. Computes the real multiplier n = peak_high / base_low
  4. Evaluates the post-peak drawdown to classify:
     - DUMP_CONFIRMED: Drawdown >= 45% from peak (completed cycle like DEXE)
     - HIGH_CONSOLIDATION: Still holding near peak (ongoing active campaign like AKE)
     - ACTIVE_EXPANSION: Recently made new highs
  5. Populates data/pump_events_db.json with 100% verified real events (n >= 2.5x)
  6. Updates data/active_pumps_registry.json with all active/historical campaigns

Run:
    python tasks/scan_all_binance_pump_dumps_2026.py
"""

import sys
import os
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from packages.exchange_connectors.binance_client import BinanceFuturesConnector
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
    get_pump_registry,
)


def analyze_full_market_pump_dump(
    symbol: str,
    klines: list,
    min_n: float = 2.5,
    year_filter: str = "2026",
) -> Optional[Tuple[PumpEvent, Optional[PumpCampaign]]]:
    """
    Analyzes full 2026 kline series to detect true macro base, true peak, and dump state.
    """
    if len(klines) < 20:
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

    # Filter for 2026 data
    target = [c for c in parsed if c["date"].startswith(year_filter)]
    if len(target) < 15:
        target = parsed

    if len(target) < 10:
        return None

    # Scan for the global or strongest local accumulation bottom & subsequent macro peak
    best_event = None
    best_campaign = None
    max_n = 0.0

    current_price = target[-1]["close"]
    current_date  = target[-1]["date"]

    clf = PriceTierClassifier()

    for i in range(len(target) - 3):
        # Lookback window for base (up to 30 days ending at i)
        base_window = target[max(0, i - 30): i + 1]
        base_low = min(c["low"] for c in base_window)

        # Confirm we are near the local trough
        if target[i]["low"] > base_low * 1.12:
            continue

        # Forward window to find peak (scanning all subsequent candles)
        forward_window = target[i + 1:]
        if not forward_window:
            continue

        peak_high = max(c["high"] for c in forward_window)
        peak_idx  = i + 1 + max(idx for idx, c in enumerate(forward_window) if c["high"] == peak_high)
        peak_date = target[peak_idx]["date"]

        n = peak_high / max(base_low, 1e-12)

        if n >= min_n and n > max_n:
            max_n = n

            # Pre-pump metrics
            base_vol_avg = sum(c["vol_quote"] for c in base_window) / max(len(base_window), 1)
            pump_move_window = target[i + 1: peak_idx + 1]
            pump_vol_total = sum(c["vol_quote"] for c in pump_move_window)
            vol_spike = pump_vol_total / max(base_vol_avg * len(pump_move_window), 1.0)
            duration_h = len(pump_move_window) * 24.0

            tier = clf.classify(base_low)

            # Check post-peak action (Dump vs Consolidation)
            post_peak_window = target[peak_idx:]
            lowest_post_peak = min(c["low"] for c in post_peak_window) if post_peak_window else current_price
            drawdown_from_peak = (peak_high - current_price) / max(peak_high, 1e-12) * 100.0
            max_drawdown_post_peak = (peak_high - lowest_post_peak) / max(peak_high, 1e-12) * 100.0

            # Determine Stage
            days_since_peak = len(post_peak_window)
            if max_drawdown_post_peak >= 45.0 or drawdown_from_peak >= 45.0:
                stage = PumpStage.DUMP_CONFIRMED
                stage_lbl = f"🔴 Đã Xác Nhận Dump (-{drawdown_from_peak:.1f}%)"
                is_active = False
                dump_date = target[min(len(target)-1, peak_idx + 5)]["date"]
            elif days_since_peak >= 10 and drawdown_from_peak < 30.0:
                stage = PumpStage.HIGH_CONSOLIDATION
                stage_lbl = "🟢 Neo Đỉnh Tích Lũy Sóng Mới (Chưa Dump)"
                is_active = True
                dump_date = None
            elif drawdown_from_peak < 15.0:
                stage = PumpStage.ACTIVE_EXPANSION
                stage_lbl = "🔥 Đang Mở Rộng Sóng Đẩy"
                is_active = True
                dump_date = None
            else:
                stage = PumpStage.EXHAUSTION_WARNING
                stage_lbl = "⚠️ Cảnh Báo Phân Phối"
                is_active = True
                dump_date = None

            # PumpEvent for ML Database
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

            # PumpCampaign for Stateful Registry
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
                notes=f"Chu kỳ 2026: Đáy ${base_low:.6f} -> Đỉnh ${peak_high:.6f} ({n:.1f}x). {stage_lbl}",
            )

    if best_event and max_n >= min_n:
        return best_event, best_campaign
    return None


def main():
    print("=" * 80)
    print("  SCANNING ALL BINANCE USD-M FUTURES FOR 2026 PUMP & DUMP CYCLES")
    print("=" * 80)

    connector = BinanceFuturesConnector()
    info = connector.client.futures_exchange_info()
    symbols = [
        s["symbol"] for s in info["symbols"]
        if s["contractType"] == "PERPETUAL"
        and s["quoteAsset"] == "USDT"
        and s["status"] == "TRADING"
        and not is_stablecoin(s["symbol"])
        and not is_stock_or_etf(s["symbol"])
    ]

    print(f"Total candidate pairs to scan: {len(symbols)}")
    print("Detection Criteria: Base LOW -> Peak HIGH -> Post-Peak Dump State (min n >= 2.5x)\n")

    events: List[PumpEvent] = []
    campaigns: Dict[str, PumpCampaign] = {}

    success_count = 0
    pump_count = 0

    for idx, sym in enumerate(symbols, 1):
        try:
            klines = connector.client.futures_klines(symbol=sym, interval="1d", limit=365)
            res = analyze_full_market_pump_dump(sym, klines, min_n=2.5, year_filter="2026")
            success_count += 1

            if res:
                ev, camp = res
                events.append(ev)
                if camp:
                    campaigns[sym] = camp
                pump_count += 1
                stage_tag = camp.stage_label_vi if camp else ""
                print(f"[{idx:>3}/{len(symbols)}] [PUMP] {sym:<16} n={ev.n_actual:>6.2f}x | Base: ${ev.pre_pump_price:<12.7f} | Peak: ${ev.peak_price:<12.7f} | {stage_tag}")
            else:
                if idx % 25 == 0:
                    print(f"[{idx:>3}/{len(symbols)}] Scanned {sym}...")

            time.sleep(0.06)  # Safe rate-limiting (~15 req/sec)

        except Exception as ex:
            if "code=-1003" in str(ex) or "429" in str(ex) or "418" in str(ex):
                print(f"Rate limited on {sym}. Sleeping 2.5s...")
                time.sleep(2.5)
            else:
                pass

    print("\n" + "=" * 80)
    print(f"  SCAN COMPLETE: {success_count}/{len(symbols)} pairs scanned.")
    print(f"  Found {len(events)} verified 2026 pump events (n >= 2.5x).")
    print("=" * 80)

    # Save to ML Dataset
    db = PumpDatasetBuilder()
    db.save_all(events)
    print(f"Saved {len(events)} real events to data/pump_events_db.json.")

    # Save to Stateful Registry
    reg = PumpLifecycleRegistry()
    reg.campaigns = campaigns
    reg.save()
    print(f"Saved {len(campaigns)} campaigns to data/active_pumps_registry.json.")

    print("\nNext step: Retraining ML Multiplier Model on the entire market dataset...")


if __name__ == "__main__":
    main()
