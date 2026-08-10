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
        self.client.session = self.session

    def get_all_usdt_tickers(self, min_quote_volume: float = 500000.0) -> List[Dict[str, Any]]:
        """Fetch all 24-hour ticker statistics for USDT-M perpetual contracts."""
        tickers = self.client.futures_ticker()
        return [
            t for t in tickers
            if t["symbol"].endswith("USDT")
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
