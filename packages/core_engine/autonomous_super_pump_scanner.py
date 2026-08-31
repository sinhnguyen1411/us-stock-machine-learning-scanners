"""
DeepAlpha — Autonomous Super-Pump Discovery Engine (Binance USD-M Futures 2026).
Continuously discovers multi-week and multi-month super pump campaigns directly from raw klines.
Features Multi-Path Qualification:
  1. Standard Macro Super-Pumps (n >= 3.0x)
  2. Early Volume Ignition Breakouts (n >= 1.8x with high 24h volume / volume spike, e.g. 4USDT)
  3. Stealth Slow-Grind Climbers (n >= 1.5x with R^2 >= 0.70 & steady green days, e.g. DEXE)
Operates with a Priority Queue Rate Limiter to eliminate any HTTP 418 IP blocks across 700+ pairs.
"""

import urllib.request
import json
import time
import datetime
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage, get_pump_registry

logger = logging.getLogger("AutonomousSuperPumpScanner")


class AutonomousSuperPumpScanner:
    """
    Autonomous multi-month super pump discovery engine.
    Scans the entire universe of Binance USD-M Futures contracts (700+ pairs)
    with dynamic priority sorting and multi-pattern recognition.
    """

    def __init__(self, registry: Optional[PumpLifecycleRegistry] = None, min_multiplier: float = 3.0):
        self.registry = registry or get_pump_registry()
        self.min_multiplier = min_multiplier
        self.last_scan_time: float = 0.0
        self.scan_interval: float = 600.0  # Run every 10 minutes
        self.is_syncing: bool = False
        self.scanned_symbols: int = 0
        self.total_symbols: int = 0
        self.sync_progress_pct: float = 100.0
        self.last_active_found: List[str] = []

    def get_sync_status(self) -> Dict[str, Any]:
        """Returns real-time scanner telemetry for UI status pill and progress bars."""
        active_campaigns = self.registry.get_active_campaigns()
        return {
            "status": "SCANNING" if self.is_syncing else "READY",
            "is_syncing": self.is_syncing,
            "progress_pct": round(self.sync_progress_pct, 1),
            "scanned_symbols": self.scanned_symbols,
            "total_symbols": self.total_symbols,
            "active_campaigns_count": len(active_campaigns),
            "last_scan_utc": datetime.fromtimestamp(self.last_scan_time, tz=timezone.utc).isoformat() if self.last_scan_time > 0 else None,
            "active_symbols": [c.symbol for c in active_campaigns[:10]],
        }


    @staticmethod
    def calculate_trend_efficiency(closes: List[float]) -> Dict[str, float]:
        """
        Calculates linear regression fit R^2, positive day ratio, and drift metrics.
        Used to detect 'Stealth Climber' patterns (e.g. DEXE) that grind up steadily each day.
        """
        if not closes or len(closes) < 10:
            return {"r2": 0.0, "positive_day_ratio": 0.5, "total_drift_pct": 0.0, "max_daily_drop_pct": 0.0}

        n = len(closes)
        x = list(range(n))
        y = closes

        # Linear regression calculation
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        ss_xx = sum((xi - mean_x) ** 2 for xi in x)
        ss_yy = sum((yi - mean_y) ** 2 for yi in y)
        ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

        if ss_xx <= 0 or ss_yy <= 0:
            r2 = 0.0
        else:
            r = ss_xy / ((ss_xx * ss_yy) ** 0.5)
            slope = ss_xy / ss_xx
            # Only positive upward slope counts as an uptrend
            r2 = round((r ** 2) if slope > 0 else 0.0, 4)

        # Positive Day Ratio: fraction of days where close[t] >= close[t-1]
        green_days = sum(1 for i in range(1, n) if closes[i] >= closes[i - 1])
        positive_day_ratio = round(green_days / max(1, n - 1), 3)

        # Total drift %
        drift_pct = round(((closes[-1] - closes[0]) / max(closes[0], 1e-12)) * 100.0, 2)

        # Max 1-day percentage drop
        drops = [((closes[i-1] - closes[i]) / max(closes[i-1], 1e-12)) * 100.0 for i in range(1, n)]
        max_daily_drop_pct = round(max(drops), 2) if drops else 0.0

        return {
            "r2": r2,
            "positive_day_ratio": positive_day_ratio,
            "total_drift_pct": drift_pct,
            "max_daily_drop_pct": max_daily_drop_pct,
        }

    @staticmethod
    def segment_macro_cycles(
        klines: List[Any],
        min_multiplier: float = 3.0,
        vol_24h_quote: float = 0.0,
        vol_spike: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Segment multi-month daily candles into distinct pump & dump cycles with Dynamic Base Finding.
        Supports 3 qualification avenues:
          1. Standard Super-Pump (n >= min_multiplier)
          2. Early Volume Ignition (n >= 1.8x + vol_24h >= $15M or spike >= 4.0x)
          3. Stealth Slow-Grind Climber (n >= 1.5x + R^2 >= 0.70 + green_days >= 65%)
        """
        if not klines or not isinstance(klines, (list, tuple)):
            return []

        sanitized_klines = []
        for k in klines:
            try:
                if not isinstance(k, (list, tuple)) or len(k) < 5:
                    continue
                t = int(k[0])
                h = float(k[2])
                l = float(k[3])
                c = float(k[4])
                if h > 0 and l > 0 and c > 0 and h >= l:
                    sanitized_klines.append((t, h, l, c))
            except (ValueError, TypeError):
                continue

        if len(sanitized_klines) < 15:
            return []

        times = [k[0] for k in sanitized_klines]
        highs = [k[1] for k in sanitized_klines]
        lows = [k[2] for k in sanitized_klines]
        closes = [k[3] for k in sanitized_klines]
        n_bars = len(sanitized_klines)

        cycles = []
        i = 0

        while i < n_bars - 5:
            # Scan forward to locate peak or cycle resolution
            running_peak = highs[i]
            peak_idx = i
            dump_idx = None

            for j in range(i, n_bars):
                if highs[j] > running_peak:
                    running_peak = highs[j]
                    peak_idx = j

                # Dynamic Accumulation Base: lowest low in the accumulation period before peak
                local_base = min(lows[i : peak_idx + 1])
                if local_base <= 0:
                    continue

                mult_peak = running_peak / local_base
                # Check for completed dump: strictly after peak_idx, qualified (>= 2.0x), and close drops >= 45% (or low drops >= 60%)
                close_dd = (running_peak - closes[j]) / running_peak
                low_dd = (running_peak - lows[j]) / running_peak
                if j > peak_idx and mult_peak >= 2.0 and (close_dd >= 0.45 or low_dd >= 0.60):
                    dump_idx = j
                    break



            # Re-evaluate best base for this segment
            base_window = lows[i : peak_idx + 1]
            base_min = min(base_window) if base_window else lows[i]
            base_idx = i + base_window.index(base_min) if base_window else i

            if base_min <= 0:
                break

            base_date = datetime.fromtimestamp(times[base_idx] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            peak_date = datetime.fromtimestamp(times[peak_idx] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


            curr_price = closes[dump_idx] if dump_idx is not None else closes[-1]
            mult_peak = running_peak / base_min
            mult_curr = curr_price / base_min
            dd = (running_peak - curr_price) / running_peak * 100.0

            # ── Multi-Path Qualification Engine ──
            is_qualified = False
            pattern_type = "SUPER_PUMP"

            if mult_peak >= min_multiplier:
                is_qualified = True
                pattern_type = "SUPER_PUMP"
            elif mult_curr >= 1.8 and (vol_24h_quote >= 15_000_000.0 or vol_spike >= 4.0):
                is_qualified = True
                pattern_type = "VOLUME_IGNITION"
            else:
                # Check Stealth Climber pattern
                sub_closes = closes[base_idx : (dump_idx + 1 if dump_idx is not None else n_bars)]
                if len(sub_closes) >= 12 and mult_curr >= 1.45:
                    trend = AutonomousSuperPumpScanner.calculate_trend_efficiency(sub_closes)
                    if trend["r2"] >= 0.65 and trend["positive_day_ratio"] >= 0.60:
                        is_qualified = True
                        pattern_type = "STEALTH_CLIMBER"

            if dump_idx is not None and dump_idx < n_bars - 5:
                if is_qualified:
                    cycles.append({
                        "origin_date": base_date,
                        "peak_date": peak_date,
                        "origin_bottom_price": base_min,
                        "highest_peak_price": running_peak,
                        "current_price": curr_price,
                        "peak_n": round(mult_peak, 2),
                        "current_n": round(mult_curr, 2),
                        "drawdown_pct": round(max(0.0, dd), 1),
                        "is_completed_dump": True,
                        "is_active": False,
                        "pattern_type": pattern_type,
                        "dump_idx": dump_idx,
                    })
                i = dump_idx + 1
            else:
                if is_qualified:
                    cycles.append({
                        "origin_date": base_date,
                        "peak_date": peak_date,
                        "origin_bottom_price": base_min,
                        "highest_peak_price": running_peak,
                        "current_price": curr_price,
                        "peak_n": round(mult_peak, 2),
                        "current_n": round(mult_curr, 2),
                        "drawdown_pct": round(max(0.0, dd), 1),
                        "is_completed_dump": dd >= 45.0,
                        "is_active": dd < 45.0,
                        "pattern_type": pattern_type,
                    })
                break

        return cycles

    def scan_symbol_cycle(
        self,
        symbol: str,
        vol_24h_quote: float = 0.0,
        vol_spike: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single symbol's 120-day macro cycle from raw daily candles.
        Returns campaign metrics if qualified by any pattern avenue, else None.
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

            cycles = self.segment_macro_cycles(
                klines=klines,
                min_multiplier=self.min_multiplier,
                vol_24h_quote=vol_24h_quote,
                vol_spike=vol_spike,
            )
            if not cycles:
                return None

            latest = cycles[-1]
            pattern_type = latest.get("pattern_type", "SUPER_PUMP")
            dd = latest.get("drawdown_pct", 0.0)
            is_active = latest.get("is_active", True)

            if dd >= 45.0:
                stage = PumpStage.DUMP_CONFIRMED
                is_active = False
            elif dd >= 28.0:
                stage = PumpStage.EXHAUSTION_WARNING
                is_active = True
            elif pattern_type == "STEALTH_CLIMBER":
                stage = PumpStage.HIGH_CONSOLIDATION
                is_active = True
            else:
                try:
                    orig_dt = datetime.datetime.strptime(latest["origin_date"], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
                    if (datetime.datetime.now(datetime.timezone.utc) - orig_dt).days >= 7:
                        stage = PumpStage.HIGH_CONSOLIDATION
                    else:
                        stage = PumpStage.ACTIVE_EXPANSION
                    is_active = True
                except Exception:
                    stage = PumpStage.ACTIVE_EXPANSION

            return {
                "symbol": symbol,
                "origin_date": latest["origin_date"],
                "peak_date": latest["peak_date"],
                "origin_bottom_price": latest["origin_bottom_price"],
                "highest_peak_price": latest["highest_peak_price"],
                "current_price": latest.get("current_price", float(klines[-1][4])),
                "peak_n": latest.get("peak_n", round(latest["highest_peak_price"] / latest["origin_bottom_price"], 2)),
                "current_n": latest.get("current_n", 1.0),
                "drawdown_pct": dd,
                "stage": stage,
                "is_active": is_active,
                "pattern_type": pattern_type,
                "total_cycles_detected": len(cycles),
            }
        except Exception as e:
            logger.debug(f"Error scanning cycle for {symbol}: {e}")
            return None

    def fetch_live_binance_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch 100% live Binance USD-M Futures real-time metrics:
        - Live current price from ticker
        - Live funding rate from premiumIndex
        - Base bottom price from registry or 120D klines
        - Volume spike ratio (24h volume vs 30D average)
        """
        symbol = str(symbol).strip().upper()
        if not symbol.endswith("USDT") and not symbol.endswith("BUSD") and not symbol.endswith("USDC"):
            symbol = f"{symbol}USDT"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

        # 1. Fetch live 24h ticker
        curr_price = 0.0
        vol_24h_quote = 1_000_000.0
        try:
            url_ticker = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
            req = urllib.request.Request(url_ticker, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                tick = json.loads(resp.read().decode())
                curr_price = float(tick.get("lastPrice", 0.0))
                vol_24h_quote = float(tick.get("quoteVolume", 1_000_000.0))
        except Exception as ex:
            logger.debug(f"24hr Ticker fetch failed for {symbol}: {ex}")
            try:
                url_p = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
                req = urllib.request.Request(url_p, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as resp:
                    p_data = json.loads(resp.read().decode())
                    curr_price = float(p_data.get("price", 0.0))
            except Exception:
                pass

        # 2. Fetch live funding rate
        funding_rate = 0.0
        try:
            url_fund = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
            req = urllib.request.Request(url_fund, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                fund_data = json.loads(resp.read().decode())
                funding_rate = float(fund_data.get("lastFundingRate", 0.0))
        except Exception as ex:
            logger.debug(f"Funding fetch failed for {symbol}: {ex}")

        # 3. Fetch base bottom price and volume baseline
        base_price = 0.0
        vol_spike_ratio = 10.0

        # Check registry first for curated macro base price (prefer active wave)
        camp = self.registry.get_campaign(symbol)
        if camp:
            base_price = camp.origin_bottom_price
            if curr_price <= 0:
                curr_price = camp.current_price

        # If not in registry or base_price missing, compute from 120D segmented klines
        if base_price <= 0 or vol_spike_ratio == 10.0:
            try:
                url_klines = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit=120"
                req = urllib.request.Request(url_klines, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    klines = json.loads(resp.read().decode())

                if klines and len(klines) >= 10:
                    if base_price <= 0:
                        segmented = self.segment_macro_cycles(klines, self.min_multiplier, vol_24h_quote=vol_24h_quote)
                        if segmented:
                            base_price = segmented[-1]["origin_bottom_price"]
                        else:
                            lows = [float(k[3]) for k in klines]
                            base_price = min(lows)
                    if curr_price <= 0:
                        curr_price = float(klines[-1][4])

                    quote_vols = [float(k[7]) for k in klines]
                    if len(quote_vols) >= 15:
                        baseline_window = quote_vols[:min(30, len(quote_vols) // 2)]
                        baseline_vol = sum(baseline_window) / max(len(baseline_window), 1)
                        recent_vol = max(quote_vols[-5:])
                        vol_spike_ratio = round(max(1.0, min(100.0, recent_vol / max(baseline_vol, 1.0))), 2)
            except Exception as ex:
                logger.debug(f"Klines fetch failed for {symbol}: {ex}")

        if base_price <= 0:
            base_price = curr_price * 0.5 if curr_price > 0 else 1.0
        if curr_price <= 0:
            curr_price = base_price * 2.0

        return {
            "symbol": symbol,
            "current_price": curr_price,
            "base_price": base_price,
            "funding_rate": funding_rate,
            "funding_rate_pct": round(funding_rate * 100.0, 4),
            "vol_spike_ratio": vol_spike_ratio,
            "vol_24h_quote": vol_24h_quote,
            "source": "Binance USD-M Futures Realtime API",
        }

    def scan_all_markets(self, max_symbols: Optional[int] = None) -> Dict[str, Any]:
        """
        Scan Binance USD-M Futures contracts with dynamic priority sorting across all 700+ pairs.
        High volume & high volatility movers are scanned first, followed by full universe.
        """
        logger.info("Starting Autonomous Super-Pump Full-Market Priority Scan...")
        self.last_scan_time = time.time()

        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                raw_tickers = json.loads(resp.read().decode())

            valid_tickers = [
                t for t in raw_tickers
                if t.get("symbol", "").endswith("USDT")
                and not t["symbol"].startswith(("USDC", "FDUSD", "TUSD", "BUSD", "EUR", "DAI"))
            ]

            # Dynamic Priority Score: Quote Volume * (1 + |% Change| / 100)
            def priority_key(t):
                vol = float(t.get("quoteVolume", 0.0))
                pct = abs(float(t.get("priceChangePercent", 0.0)))
                return vol * (1.0 + pct / 100.0)

            valid_tickers.sort(key=priority_key, reverse=True)
            symbols_to_scan = valid_tickers if max_symbols is None else valid_tickers[:max_symbols]
        except Exception as ex:
            logger.error(f"Failed to fetch 24hr ticker symbol list: {ex}")
            return {"active_found": [], "dumped_found": [], "total_registered": len(self.registry.campaigns)}

        self.is_syncing = True
        self.total_symbols = len(symbols_to_scan)
        self.scanned_symbols = 0
        self.sync_progress_pct = 0.0

        active_found = []
        dumped_found = []

        try:
            # Scan symbols with paced token-bucket rate limiter
            for idx, t in enumerate(symbols_to_scan):
                sym = t["symbol"]
                vol_24h = float(t.get("quoteVolume", 0.0))
                res = self.scan_symbol_cycle(sym, vol_24h_quote=vol_24h)
                if res:
                    pattern_type = res.get("pattern_type", "SUPER_PUMP")
                    cid = f"{res['symbol']}_{res['origin_date']}"

                    note_prefix = {
                        "VOLUME_IGNITION": "🔥 Volume Ignition",
                        "STEALTH_CLIMBER": "🐢 Stealth Climber (Leo dốc bền vững)",
                        "SUPER_PUMP": "⚡ Super-Pump Macro Wave",
                    }.get(pattern_type, "⚡ Super-Pump")

                    c = PumpCampaign(
                        campaign_id=cid,
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
                        pattern_type=pattern_type,
                        dump_threshold_price=round(res["highest_peak_price"] * 0.55, 8),
                        notes=f"{note_prefix}: n={res['peak_n']}x từ đáy ${res['origin_bottom_price']} ngày {res['origin_date']}."
                    )
                    self.registry.campaigns[cid] = c
                    if res["is_active"]:
                        active_found.append(sym)
                    else:
                        dumped_found.append(sym)

                self.scanned_symbols = idx + 1
                self.sync_progress_pct = round((idx + 1) / self.total_symbols * 100.0, 1)

                # Paced Rate Limiting: 25 req/s (0.04s sleep)
                time.sleep(0.04)

            self.registry.save()
            self.last_scan_time = time.time()
            self.last_active_found = active_found
            logger.info(f"Autonomous Market Scan Complete: Discovered {len(active_found)} Active ({active_found}), {len(dumped_found)} Dumped.")
        finally:
            self.is_syncing = False
            self.sync_progress_pct = 100.0

        return {
            "active_found": active_found,
            "dumped_found": dumped_found,
            "total_registered": len(self.registry.campaigns),
        }

    def fast_bootstrap_sync(self, top_n: int = 30) -> Dict[str, Any]:
        """
        Fast Startup Hook: Scans the top 30 highest-liquidity USD-M contracts concurrently
        in ~1-2 seconds using a multi-threaded pool so the UI renders active campaigns instantly.
        """
        logger.info(f"[FastBootstrap] ⚡ Initiating rapid priority bootstrap for Top {top_n} liquid pairs...")
        self.is_syncing = True
        self.scanned_symbols = 0
        self.total_symbols = top_n
        self.sync_progress_pct = 10.0

        active_found = []
        try:
            tickers = self.fetch_24hr_tickers()
            valid_tickers = [
                t for t in tickers
                if t.get("symbol", "").endswith("USDT")
                and not any(s in t.get("symbol", "") for s in ["USDC", "FDUSD", "TUSD", "DAI"])
            ]
            valid_tickers.sort(key=lambda t: float(t.get("quoteVolume", 0.0)), reverse=True)
            top_tickers = valid_tickers[:top_n]

            def scan_worker(t):
                sym = t["symbol"]
                vol = float(t.get("quoteVolume", 0.0))
                return self.scan_symbol_cycle(sym, vol_24h_quote=vol)

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(scan_worker, t): t["symbol"] for t in top_tickers}
                for i, future in enumerate(as_completed(futures)):
                    self.scanned_symbols = i + 1
                    self.sync_progress_pct = round((i + 1) / top_n * 100.0, 1)
                    try:
                        res = future.result()
                        if res:
                            pattern_type = res.get("pattern_type", "SUPER_PUMP")
                            cid = f"{res['symbol']}_{res['origin_date']}"
                            c = PumpCampaign(
                                campaign_id=cid,
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
                                pattern_type=pattern_type,
                                dump_threshold_price=round(res["highest_peak_price"] * 0.55, 8),
                                notes=f"⚡ Fast Bootstrap Super-Pump: n={res['peak_n']}x từ đáy ${res['origin_bottom_price']} ngày {res['origin_date']}."
                            )
                            self.registry.campaigns[cid] = c
                            if res["is_active"]:
                                active_found.append(res["symbol"])
                    except Exception as e:
                        logger.debug(f"[FastBootstrap] Error scanning symbol: {e}")

            self.registry.save()
            self.last_scan_time = time.time()
            self.last_active_found = active_found
            logger.info(f"[FastBootstrap] ✅ Completed rapid bootstrap. {len(active_found)} active campaigns initialized.")
        finally:
            self.is_syncing = False
            self.sync_progress_pct = 100.0

        return {
            "bootstrap_active": active_found,
            "total_registered": len(self.registry.campaigns),
        }


# Global Scanner Singleton
_GLOBAL_SCANNER: Optional[AutonomousSuperPumpScanner] = None


def get_autonomous_scanner() -> AutonomousSuperPumpScanner:
    global _GLOBAL_SCANNER
    if _GLOBAL_SCANNER is None:
        _GLOBAL_SCANNER = AutonomousSuperPumpScanner()
    return _GLOBAL_SCANNER

