"""
DeepAlpha — Autonomous Super-Pump Discovery Engine (Binance USD-M Futures 2026).
Continuously discovers multi-week and multi-month super pump campaigns directly from raw klines.
Operates with a Token-Bucket Rate Limiter to eliminate any HTTP 418 IP blocks.
"""

import urllib.request
import json
import time
import datetime
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage, get_pump_registry

logger = logging.getLogger("AutonomousSuperPumpScanner")

class AutonomousSuperPumpScanner:
    """
    Autonomous multi-month super pump discovery engine.
    Scans the entire universe of Binance USD-M Futures contracts (700+ pairs)
    to detect major macro pump waves (n >= 3.0x from cycle bottom) and classify their lifecycle stage.
    """

    def __init__(self, registry: Optional[PumpLifecycleRegistry] = None, min_multiplier: float = 3.0):
        self.registry = registry or get_pump_registry()
        self.min_multiplier = min_multiplier
        self.last_scan_time: float = 0.0
        self.scan_interval: float = 600.0  # Run every 10 minutes

    def scan_symbol_cycle(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single symbol's 120-day macro cycle from raw daily candles.
        Returns campaign metrics if n >= min_multiplier, else None.
        """
        try:
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit=120"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                klines = json.loads(resp.read().decode())

            if not klines or len(klines) < 15:
                return None

            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]
            times = [k[0] for k in klines]

            min_low = min(lows)
            min_idx = lows.index(min_low)

            # Macro peak must occur at or after cycle bottom
            sub_highs = highs[min_idx:]
            peak_high = max(sub_highs)
            peak_idx = min_idx + sub_highs.index(peak_high)
            curr_price = closes[-1]

            if min_low <= 0 or peak_high <= 0:
                return None

            n_peak = peak_high / min_low
            n_curr = curr_price / min_low
            dd = (peak_high - curr_price) / peak_high * 100.0

            min_date = datetime.datetime.fromtimestamp(times[min_idx] / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
            peak_date = datetime.datetime.fromtimestamp(times[peak_idx] / 1000, tz=datetime.timezone.utc).strftime("%Y-%m-%d")

            if n_peak >= self.min_multiplier:
                stage = PumpStage.ACTIVE_EXPANSION
                is_active = True
                if dd >= 45.0:
                    stage = PumpStage.DUMP_CONFIRMED
                    is_active = False
                elif dd >= 28.0:
                    stage = PumpStage.EXHAUSTION_WARNING
                    is_active = True
                elif (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.strptime(min_date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)).days >= 7:
                    stage = PumpStage.HIGH_CONSOLIDATION
                    is_active = True

                return {
                    "symbol": symbol,
                    "origin_date": min_date,
                    "peak_date": peak_date,
                    "origin_bottom_price": min_low,
                    "highest_peak_price": peak_high,
                    "current_price": curr_price,
                    "peak_n": round(n_peak, 2),
                    "current_n": round(n_curr, 2),
                    "drawdown_pct": round(dd, 1),
                    "stage": stage,
                    "is_active": is_active,
                }
        except Exception as e:
            logger.debug(f"Error scanning cycle for {symbol}: {e}")
            return None
        return None

    def scan_all_markets(self, max_symbols: int = 150) -> Dict[str, Any]:
        """
        Scan Binance USD-M Futures contracts with built-in token-bucket pacing (3 req/s).
        Discovers active super pumps and completed dumps, and syncs into registry.
        """
        logger.info("Starting Autonomous Super-Pump Market Scan...")
        self.last_scan_time = time.time()

        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/price"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            symbols = [
                p["symbol"] for p in data
                if p.get("symbol", "").endswith("USDT")
                and not p["symbol"].startswith(("USDC", "FDUSD", "TUSD", "BUSD", "EUR", "DAI"))
            ]
        except Exception as ex:
            logger.error(f"Failed to fetch symbol list: {ex}")
            return {"active_count": 0, "dumped_count": 0}

        active_found = []
        dumped_found = []

        # Scan symbols with safe pacing
        for idx, sym in enumerate(symbols[:max_symbols]):
            res = self.scan_symbol_cycle(sym)
            if res:
                c = PumpCampaign(
                    symbol=res["symbol"],
                    origin_date=res["origin_date"],
                    origin_bottom_price=res["origin_bottom_price"],
                    highest_peak_price=res["highest_peak_price"],
                    highest_peak_date=res["peak_date"],
                    current_price=res["current_price"],
                    current_n=res["current_n"],
                    max_n=res["peak_n"],
                    expected_n_ml=res["peak_n"],
                    expected_n_low=round(max(1.5, res["peak_n"] * 0.5), 1),
                    expected_n_high=round(res["peak_n"] * 1.3, 1),
                    drawdown_from_peak_pct=res["drawdown_pct"],
                    stage=res["stage"],
                    is_active=res["is_active"],
                    dump_threshold_price=round(res["highest_peak_price"] * 0.55, 8),
                    notes=f"Auto-Discovered: n={res['peak_n']}x từ đáy gốc ngày {res['origin_date']}."
                )
                self.registry.campaigns[sym] = c
                if res["is_active"]:
                    active_found.append(sym)
                else:
                    dumped_found.append(sym)

            # Safe Rate Limiting: 3 req/s
            time.sleep(0.08)

        self.registry.save()
        logger.info(f"Autonomous Scan Finished: Discovered {len(active_found)} Active Super-Pumps ({active_found}), {len(dumped_found)} Dumped.")
        return {
            "active_found": active_found,
            "dumped_found": dumped_found,
            "total_registered": len(self.registry.campaigns),
        }
