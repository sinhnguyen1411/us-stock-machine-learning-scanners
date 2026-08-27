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

EXCLUDED_STABLECOINS = {
    # USD Stablecoins
    "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT", "USDPUSDT",
    "DAIUSDT", "USDEUSDT", "PYUSDUSDT", "USTCUSDT", "STABLEUSDT",
    "STBLUSDT", "FRAXUSDT", "LUSDUSDT", "GUSDUSDT", "CUSDUSDT",
    "USDUSDT", "USDSUSDT", "USD1USDT", "USD0USDT", "USDDUSDT",
    "MIMUSDT", "ALUSDUSDT", "OUSDUSDT", "SUSDUSDT", "USDJUSDT",
    # EUR & Fiat Stables
    "EURUSDT", "AEURUSDT", "EURSUSDT", "GBPUSDT", "AUDUSDT",
    # Gold & Commodity Pegged
    "PAXGUSDT", "XAUTUSDT", "XAGUSDT", "XPTUSDT",
    # Staked / Wrapped Pegged Tokens
    "WBETHUSDT", "BTCSTUSDT", "BETHUSDT",
}

STABLECOIN_BASES = {
    "USD", "USDC", "FDUSD", "TUSD", "BUSD", "USDP", "DAI", "USDE",
    "PYUSD", "USTC", "STABLE", "STBL", "FRAX", "LUSD", "GUSD",
    "USDS", "EUR", "AEUR", "PAXG", "XAUT", "XAG", "XPT", "WBETH"
}


EXCLUDED_STOCKS_AND_ETFS = {
    # US Tech & Mega Caps
    "AAPLUSDT", "MSFTUSDT", "GOOGLUSDT", "GOOGUSDT", "AMZNUSDT", "NVDAUSDT", 
    "TSLAUSDT", "METAUSDT", "NFLXUSDT", "AMDUSDT", "INTCUSDT", "AVGOUSDT",
    "CSCOUSDT", "ORCLUSDT", "ADBEUSDT", "CRMUSDT", "PYPLUSDT", "QCOMUSDT",
    "TXNUSDT", "IBMUSDT", "MUUSDT", "AMATUSDT", "KLACUSDT", "MRVLUSDT", 
    "LRCXUSDT", "ASMLUSDT", "DELLUSDT", "HPQUSDT", "SNOWUSDT", "PLTRUSDT",
    "UBERUSDT", "ABNBUSDT", "COINUSDT", "MSTRUSDT", "HOODUSDT", "RDDTUSDT",
    "RBLXUSDT", "DKNGUSDT", "PANWUSDT", "CRWDUSDT", "FTNTUSDT", "ZMUSDT",
    "DOCUUSDT", "ROKUUSDT", "PINSUSDT", "SNAPUSDT", "SQUSDT", "SHOPUSDT",
    "SEUSDT", "GRABUSDT", "BABAUSDT", "JDUSDT", "PDDUSDT", "BIDUUSDT",
    "NIOUSDT", "XPEVUSDT", "LIUSDT", "FUTUUSDT", "TENCENTUSDT", "ANTHROPICUSDT",
    "OPENAIUSDT", "SPACEXUSDT", "SPCXUSDT", "FWDIUSDT", "MVLLUSDT", "POPMARTUSDT",
    # Traditional Equities & Global Conglomerates
    "BRKBUSDT", "JPMUSDT", "VUSDT", "MAUSDT", "BACUSDT", "WFCUSDT", "CUSDT",
    "GSUSDT", "MSUSDT", "BLKUSDT", "AXPUSDT", "WMTUSDT", "COSTUSDT", "TGTUSDT",
    "HDUSDT", "LOWUSDT", "NKEUSDT", "MCDUSDT", "SBUXUSDT", "DISUSDT", "KOUSDT",
    "PEPUSDT", "PGUSDT", "JNJUSDT", "UNHUSDT", "PFEUSDT", "ABBVUSDT", "MRKUSDT",
    "LLYUSDT", "BMYUSDT", "AMGNUSDT", "GILDUSDT", "CATUSDT", "BAUSDT", "GEUSDT",
    "HONUSDT", "UPSUSDT", "FDXUSDT", "LMTUSDT", "RTXUSDT", "XOMUSDT", "CVXUSDT",
    "COPUSDT", "SLBUSDT", "EOGUSDT", "BPUSDT", "SHELUSDT", "TTEUSDT", "RIOUSDT",
    "BHPUSDT", "VALEUSDT", "FCXUSDT", "NEMUSDT", "FUSDT", "GMUSDT", "TMUSDT",
    "HMCUSDT", "SAMSUNGUSDT", "HYUNDAIUSDT", "SONYUSDT", "TSMCUSDT", "TSMUSDT",
    "CSOPSAMSUNG2LUSDT", "CSOPSKHYNIX2LUSDT", "SKHYNIXUSDT", "SKHYUSDT", "FOXAUSDT",
    "BZUSDT", "CLUSDT", "CCUSDT", "TBTUSDT", "ZBTUSDT", "RKLBUSDT", "WDCUSDT", "BILLUSDT",
    # ETFs, Indexes & Leveraged Products
    "SPYUSDT", "QQQUSDT", "TQQQUSDT", "SQQQUSDT", "SOXLUSDT", "SOXSUSDT",
    "IWMUSDT", "DIAUSDT", "ARKKUSDT", "XLFUSDT", "XLEUSDT", "XLKUSDT", 
    "GDXUSDT", "TLTUSDT", "UVXYUSDT", "VXXUSDT", "SVIXUSDT", "BITOUSDT", 
    "ETHIUSDT", "GLDUSDT", "SLVUSDT", "USOUSDT", "UNGUSDT", "EEMUSDT", 
    "FXIUSDT", "KWEBUSDT", "MCHIUSDT", "EWZUSDT", "INDAUSDT", "EWGUSDT", 
    "EWUUSDT", "EWJUSDT", "ACWIUSDT", "VTUSDT", "VTIUSDT", "VOOUSDT"
}



def is_stock_or_etf(symbol: str) -> bool:
    """Return True if the symbol is a traditional company stock, ETF, or index contract."""
    if not symbol:
        return False
    sym = symbol.strip().upper()
    if sym in EXCLUDED_STOCKS_AND_ETFS:
        return True
    if sym.startswith("CSOP") or sym.startswith("ETF") or "INDEX" in sym or "2LUSDT" in sym or "2SUSDT" in sym:
        return True
    return False


def is_stablecoin(symbol: str) -> bool:
    """Return True if the symbol is a stablecoin, fiat-pegged, or commodity-pegged asset."""
    if not symbol:
        return False
    sym = symbol.strip().upper()
    if sym in EXCLUDED_STABLECOINS:
        return True

    for quote in ("USDT", "USDC", "BUSD", "FDUSD"):
        if sym.endswith(quote):
            base = sym[:-len(quote)]
            if base in STABLECOIN_BASES:
                return True
            if base.startswith("USD") or base.startswith("EUR"):
                return True
    return False


def is_excluded_asset(symbol: str) -> bool:
    """Unified check: return True if symbol is stablecoin, fiat, commodity, or company stock / ETF."""
    return is_stablecoin(symbol) or is_stock_or_etf(symbol)


def classify_asset_tier(symbol: str, quote_vol_24h: float = 0.0, pct_24h: float = 0.0) -> CoinTier:


    """Classify asset into Bluechip, Mid-Cap, or High-Volatility / Meme tier."""
    sym = symbol.upper()

    if sym in BLUECHIP_SYMBOLS:
        return CoinTier(
            code="LARGE_CAP",
            name="Bluechip Large-Cap",
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
            name="Mid-Cap Trending",
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
            name="High-Volatility / Meme",
            req_vol_spike=5.0,
            req_price_spike=0.030,  # +3.0%
            req_buy_ratio=0.65,
            tp1_mult=0.05,          # +5.0%
            tp2_mult=0.10,          # +10.0%
            tp3_mult=0.20,          # +20.0%
        )
