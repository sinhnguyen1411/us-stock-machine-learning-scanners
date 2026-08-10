"""
Bybit USDT Perpetual Connector
"""

import os
from typing import Optional


class BybitConnector:
    """Bybit perpetual client interface."""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv("BYBIT_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET", "")
        self.testnet = os.getenv("TESTNET", "false").lower() == "true"
