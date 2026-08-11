"""
Binance Futures (USDT-M) Connector & Session Manager
"""

import os
import requests
from typing import List, Dict, Any, Optional
from binance.client import Client


class BinanceFuturesConnector:
    """Robust client wrapper for Binance Futures USDT-M REST APIs."""

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


    def get_all_usdt_tickers(self, min_quote_volume: float = 500000.0) -> List[Dict[str, Any]]:
        """Fetch all 24-hour ticker statistics for USDT-M perpetual contracts (excluding stablecoins, stocks & ETFs)."""
        tickers = self.client.futures_ticker()
        from core_engine.classifier import is_excluded_asset
        return [
            t for t in tickers
            if t["symbol"].endswith("USDT")
            and not is_excluded_asset(t["symbol"])
            and float(t.get("quoteVolume", 0)) >= min_quote_volume
        ]

    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 60) -> List[Any]:
        """Fetch historical kline/candlestick bars for a given symbol."""
        return self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)

    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch 24-hour rolling ticker data for a single symbol."""
        return self.client.futures_ticker(symbol=symbol)

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

