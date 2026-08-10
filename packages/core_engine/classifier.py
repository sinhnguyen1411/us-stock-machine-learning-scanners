"""
Asset Tier Classifier & Adaptive Threshold Calibration
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CoinTier:
    code: str
    name: str
    req_vol_spike: float
    req_price_spike: float
    req_buy_ratio: float
    tp1_mult: float
    tp2_mult: float
    tp3_mult: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "req_vol_spike": self.req_vol_spike,
            "req_price_spike": self.req_price_spike,
            "req_buy_ratio": self.req_buy_ratio,
            "tp1_mult": self.tp1_mult,
            "tp2_mult": self.tp2_mult,
            "tp3_mult": self.tp3_mult,
        }


BLUECHIP_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", 
    "XRPUSDT", "ADAUSDT", "AVAXUSDT"
}

MID_CAP_SYMBOLS = {
    "DOGEUSDT", "LINKUSDT", "DOTUSDT", "NEARUSDT", 
    "SUIUSDT", "APTUSDT", "TRXUSDT", "LTCUSDT"
}


def classify_asset_tier(symbol: str, quote_vol_24h: float = 0.0, pct_24h: float = 0.0) -> CoinTier:
    """Classify asset into Bluechip, Mid-Cap, or High-Volatility / Meme tier."""
    sym = symbol.upper()

    if sym in BLUECHIP_SYMBOLS:
        return CoinTier(
            code="LARGE_CAP",
            name="👑 Bluechip Large-Cap",
            req_vol_spike=2.0,
            req_price_spike=0.010,  # +1.0%
            req_buy_ratio=0.60,
            tp1_mult=0.02,          # +2.0%
            tp2_mult=0.04,          # +4.0%
            tp3_mult=0.08,          # +8.0%
        )
    elif sym in MID_CAP_SYMBOLS or (quote_vol_24h >= 200_000_000 and abs(pct_24h) < 15.0):
        return CoinTier(
            code="MID_CAP",
            name="⚡ Mid-Cap Trending",
            req_vol_spike=3.5,
            req_price_spike=0.020,  # +2.0%
            req_buy_ratio=0.62,
            tp1_mult=0.035,         # +3.5%
            tp2_mult=0.07,          # +7.0%
            tp3_mult=0.15,          # +15.0%
        )
    else:
        return CoinTier(
            code="LOW_CAP_MEME",
            name="🚀 High-Volatility / Meme",
            req_vol_spike=5.0,
            req_price_spike=0.030,  # +3.0%
            req_buy_ratio=0.65,
            tp1_mult=0.05,          # +5.0%
            tp2_mult=0.10,          # +10.0%
            tp3_mult=0.20,          # +20.0%
        )
