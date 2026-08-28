"""
Binance Futures (USDT-M) Connector & Session Manager
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException


class BinanceFuturesConnector:
    """Robust client wrapper for Binance Futures USDT-M REST APIs with TTL rate-limit cache."""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        
        self.client = Client(self.api_key, self.api_secret)
        
        # Configure session without inheriting restrictive system proxy for localhost reliability
        self.session = requests.Session()
        self.session.trust_env = False
        adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.client.session = self.session

        # In-memory TTL caches to prevent IP bans
        self._kline_cache: Dict[str, Any] = {}
        self._ticker_cache: Dict[str, Any] = {}
        self._tickers_all_cache: Optional[Dict[str, Any]] = None
        self._tradfi_tickers_cache: Optional[Dict[str, Any]] = None
        self._premium_index_cache: Optional[Dict[str, Any]] = None

    def get_all_usdt_tickers(self, min_quote_volume: float = 500000.0) -> List[Dict[str, Any]]:
        """Fetch all 24-hour ticker statistics for USDT-M perpetual contracts (cached for 3s)."""
        now = time.time()
        if self._tickers_all_cache and (now - self._tickers_all_cache["time"]) < 3.0:
            cached = self._tickers_all_cache["data"]
            return [t for t in cached if float(t.get("quoteVolume", 0)) >= min_quote_volume]

        try:
            tickers = self.client.futures_ticker()
            from core_engine.classifier import is_excluded_asset
            valid = [
                t for t in tickers
                if t.get("symbol", "").endswith("USDT")
                and not is_excluded_asset(t.get("symbol", ""))
            ]
            self._tickers_all_cache = {"time": now, "data": valid}
            return [t for t in valid if float(t.get("quoteVolume", 0)) >= min_quote_volume]
        except Exception:
            # Fallback: synthesize tickers from premiumIndex (never IP-banned)
            try:
                from core_engine.classifier import is_excluded_asset
                p_items = self.get_all_premium_index()
                valid = [
                    {
                        "symbol": p["symbol"],
                        "lastPrice": str(p.get("markPrice", "0")),
                        "priceChangePercent": "0.0",
                        "quoteVolume": "1000000.0",
                        "highPrice": str(p.get("markPrice", "0")),
                        "lowPrice": str(p.get("markPrice", "0")),
                    }
                    for p in p_items
                    if p.get("symbol", "").endswith("USDT")
                    and not is_excluded_asset(p.get("symbol", ""))
                ]
                self._tickers_all_cache = {"time": now, "data": valid}
                return valid
            except Exception:
                return self._tickers_all_cache["data"] if self._tickers_all_cache else []

    def get_all_tradfi_stock_tickers(self) -> List[Dict[str, Any]]:
        """Fetch all 24-hour ticker statistics specifically for TradFi, US Stock & ETF perpetual futures (cached for 3s)."""
        now = time.time()
        if self._tradfi_tickers_cache and (now - self._tradfi_tickers_cache["time"]) < 3.0:
            return self._tradfi_tickers_cache["data"]

        try:
            from core_engine.classifier import is_stock_or_etf
            tickers = self.client.futures_ticker()
            valid = [
                t for t in tickers
                if t.get("symbol", "").endswith("USDT") and is_stock_or_etf(t.get("symbol", ""))
            ]
            self._tradfi_tickers_cache = {"time": now, "data": valid}
            return valid
        except Exception:
            return self._tradfi_tickers_cache["data"] if self._tradfi_tickers_cache else []

    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 60) -> List[Any]:
        """Fetch historical klines with smart TTL cache (15s for 1m/5m, 60s for 1h/1d)."""
        cache_key = f"{symbol}_{interval}_{limit}"
        now = time.time()
        ttl = 60.0 if interval in ("1h", "1d", "4h") else 12.0

        if cache_key in self._kline_cache:
            entry_time, cached_data = self._kline_cache[cache_key]
            if (now - entry_time) < ttl:
                return cached_data

        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
            if klines:
                self._kline_cache[cache_key] = (now, klines)
            return klines
        except Exception as ex:
            if cache_key in self._kline_cache:
                return self._kline_cache[cache_key][1]
            return []

    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch 24-hour rolling ticker data for a single symbol with 3s TTL cache."""
        now = time.time()
        if symbol in self._ticker_cache:
            t_time, t_data = self._ticker_cache[symbol]
            if (now - t_time) < 3.0:
                return t_data
        try:
            t = self.client.futures_ticker(symbol=symbol)
            self._ticker_cache[symbol] = (now, t)
            return t
        except Exception:
            return self._ticker_cache.get(symbol, (now, {}))[1]

    def get_funding_rate(self, symbol: str) -> float:
        """Fetch latest perpetual funding rate."""
        try:
            fr_data = self.client.futures_funding_rate(symbol=symbol, limit=1)
            if fr_data:
                return float(fr_data[0].get("fundingRate", 0))
        except Exception:
            pass
        return 0.0

    def get_open_interest(self, symbol: str) -> float:
        """Fetch current open interest value."""
        try:
            oi_data = self.client.futures_open_interest(symbol=symbol)
            return float(oi_data.get("openInterest", 0))
        except Exception:
            pass
        return 0.0

    def get_all_premium_index(self) -> List[Dict[str, Any]]:
        """Fetch all mark prices and funding rates for all USDT-M contracts in 1 fast call (excluding stablecoins, stocks & ETFs)."""
        try:
            from core_engine.classifier import is_excluded_asset
            data = self.client.futures_mark_price()
            return [
                d for d in data 
                if d.get("symbol", "").endswith("USDT") and not is_excluded_asset(d.get("symbol", ""))
            ]
        except Exception:
            return []



    def get_orderbook_depth_ratio(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Fetch orderbook depth to calculate Bid/Ask Liquidity Imbalance (Ask Vacuum)."""
        try:
            ob = self.client.futures_order_book(symbol=symbol, limit=limit)
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])

            total_bid_vol = sum(float(b[0]) * float(b[1]) for b in bids)
            total_ask_vol = sum(float(a[0]) * float(a[1]) for a in asks)

            ratio = round(total_bid_vol / max(total_ask_vol, 1e-4), 2)
            return {
                "bid_vol_usd": total_bid_vol,
                "ask_vol_usd": total_ask_vol,
                "depth_ratio": ratio,
                "is_ask_vacuum": ratio >= 2.5,
            }
        except Exception:
            return {
                "bid_vol_usd": 0.0,
                "ask_vol_usd": 0.0,
                "depth_ratio": 1.0,
                "is_ask_vacuum": False,
            }

