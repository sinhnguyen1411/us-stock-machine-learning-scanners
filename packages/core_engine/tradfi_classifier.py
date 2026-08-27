"""
US Stock & TradFi Futures Asset Classifier, Sector Mapping & Market Session Engine
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional


@dataclass
class TradFiStockInfo:
    symbol: str
    ticker: str
    name: str
    sector: str
    sector_name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "ticker": self.ticker,
            "name": self.name,
            "sector": self.sector,
            "sector_name": self.sector_name,
            "description": self.description,
        }


TRADFI_STOCK_DIRECTORY: Dict[str, TradFiStockInfo] = {
    # ── 1. Mega-Cap Tech & Cloud ──
    "NVDAUSDT": TradFiStockInfo("NVDAUSDT", "NVDA", "NVIDIA Corporation", "MEGA_TECH", "Mega-Cap Tech", "GPU & AI Compute Leader"),
    "AAPLUSDT": TradFiStockInfo("AAPLUSDT", "AAPL", "Apple Inc.", "MEGA_TECH", "Mega-Cap Tech", "Consumer Tech & Ecosystem"),
    "MSFTUSDT": TradFiStockInfo("MSFTUSDT", "MSFT", "Microsoft Corporation", "MEGA_TECH", "Mega-Cap Tech", "Cloud, OS & Enterprise AI"),
    "AMZNUSDT": TradFiStockInfo("AMZNUSDT", "AMZN", "Amazon.com Inc.", "MEGA_TECH", "Mega-Cap Tech", "E-Commerce & AWS Cloud"),
    "GOOGLUSDT": TradFiStockInfo("GOOGLUSDT", "GOOGL", "Alphabet Inc. (Google)", "MEGA_TECH", "Mega-Cap Tech", "Search, Cloud & DeepMind AI"),
    "GOOGUSDT": TradFiStockInfo("GOOGUSDT", "GOOG", "Alphabet Inc. Class C", "MEGA_TECH", "Mega-Cap Tech", "Search & Tech Ecosystem"),
    "METAUSDT": TradFiStockInfo("METAUSDT", "META", "Meta Platforms Inc.", "MEGA_TECH", "Mega-Cap Tech", "Social Networks & Llama AI"),
    "TSLAUSDT": TradFiStockInfo("TSLAUSDT", "TSLA", "Tesla Inc.", "MEGA_TECH", "Mega-Cap Tech", "EV, Autopilot FSD & Energy"),
    "PLTRUSDT": TradFiStockInfo("PLTRUSDT", "PLTR", "Palantir Technologies", "MEGA_TECH", "Mega-Cap Tech", "Enterprise AI & Defense Analytics"),
    "MSTRUSDT": TradFiStockInfo("MSTRUSDT", "MSTR", "MicroStrategy Inc.", "MEGA_TECH", "Mega-Cap Tech", "Bitcoin Treasury & Enterprise Analytics"),
    "COINUSDT": TradFiStockInfo("COINUSDT", "COIN", "Coinbase Global Inc.", "MEGA_TECH", "Mega-Cap Tech", "US Crypto Exchange & Custody"),
    "NFLXUSDT": TradFiStockInfo("NFLXUSDT", "NFLX", "Netflix Inc.", "MEGA_TECH", "Mega-Cap Tech", "Streaming Media Leader"),
    "CRMUSDT": TradFiStockInfo("CRMUSDT", "CRM", "Salesforce Inc.", "MEGA_TECH", "Mega-Cap Tech", "Enterprise CRM & Cloud"),
    "ADBEUSDT": TradFiStockInfo("ADBEUSDT", "ADBE", "Adobe Inc.", "MEGA_TECH", "Mega-Cap Tech", "Creative Cloud & Generative AI"),
    "ORCLUSDT": TradFiStockInfo("ORCLUSDT", "ORCL", "Oracle Corporation", "MEGA_TECH", "Mega-Cap Tech", "Enterprise Cloud & Database"),
    "IBMUSDT": TradFiStockInfo("IBMUSDT", "IBM", "International Business Machines", "MEGA_TECH", "Mega-Cap Tech", "Hybrid Cloud & Enterprise AI"),
    "DELLUSDT": TradFiStockInfo("DELLUSDT", "DELL", "Dell Technologies", "MEGA_TECH", "Mega-Cap Tech", "AI Servers & Enterprise Hardware"),
    "UBERUSDT": TradFiStockInfo("UBERUSDT", "UBER", "Uber Technologies Inc.", "MEGA_TECH", "Mega-Cap Tech", "Ride Sharing & Mobility Delivery"),
    "RDDTUSDT": TradFiStockInfo("RDDTUSDT", "RDDT", "Reddit Inc.", "MEGA_TECH", "Mega-Cap Tech", "Community Platform & AI Training Data"),
    "SHOPUSDT": TradFiStockInfo("SHOPUSDT", "SHOP", "Shopify Inc.", "MEGA_TECH", "Mega-Cap Tech", "Global E-Commerce Infrastructure"),
    "HOODUSDT": TradFiStockInfo("HOODUSDT", "HOOD", "Robinhood Markets", "MEGA_TECH", "Mega-Cap Tech", "Retail Brokerage & Fintech Trading"),

    # ── 2. Semiconductors & Chip Hardware ──
    "AMDUSDT": TradFiStockInfo("AMDUSDT", "AMD", "Advanced Micro Devices", "SEMICONDUCTORS", "Semiconductors", "High-Performance CPU & GPU"),
    "INTCUSDT": TradFiStockInfo("INTCUSDT", "INTC", "Intel Corporation", "SEMICONDUCTORS", "Semiconductors", "Semiconductor Foundry & Processors"),
    "AVGOUSDT": TradFiStockInfo("AVGOUSDT", "AVGO", "Broadcom Inc.", "SEMICONDUCTORS", "Semiconductors", "Custom AI Silicon & Infrastructure"),
    "ASMLUSDT": TradFiStockInfo("ASMLUSDT", "ASML", "ASML Holding N.V.", "SEMICONDUCTORS", "Semiconductors", "EUV Lithography Machine Leader"),
    "QCOMUSDT": TradFiStockInfo("QCOMUSDT", "QCOM", "Qualcomm Inc.", "SEMICONDUCTORS", "Semiconductors", "Mobile Processors & AI Snapdragon"),
    "MUUSDT": TradFiStockInfo("MUUSDT", "MU", "Micron Technology", "SEMICONDUCTORS", "Semiconductors", "HBM3E & High-Bandwidth Memory"),
    "TXNUSDT": TradFiStockInfo("TXNUSDT", "TXN", "Texas Instruments", "SEMICONDUCTORS", "Semiconductors", "Analog & Embedded Processing"),
    "AMATUSDT": TradFiStockInfo("AMATUSDT", "AMAT", "Applied Materials", "SEMICONDUCTORS", "Semiconductors", "Wafer Fab Equipment Leader"),
    "LRCXUSDT": TradFiStockInfo("LRCXUSDT", "LRCX", "Lam Research Corporation", "SEMICONDUCTORS", "Semiconductors", "Etch & Deposition Semiconductor Gear"),
    "MRVLUSDT": TradFiStockInfo("MRVLUSDT", "MRVL", "Marvell Technology", "SEMICONDUCTORS", "Semiconductors", "Data Infrastructure Semiconductor"),
    "KLACUSDT": TradFiStockInfo("KLACUSDT", "KLAC", "KLA Corporation", "SEMICONDUCTORS", "Semiconductors", "Process Control & Yield Diagnostics"),
    "TSMUSDT": TradFiStockInfo("TSMUSDT", "TSM", "Taiwan Semiconductor (TSMC)", "SEMICONDUCTORS", "Semiconductors", "World #1 Pure-Play Foundry"),
    "SOXLUSDT": TradFiStockInfo("SOXLUSDT", "SOXL", "Direxion Daily Semi Bull 3X", "SEMICONDUCTORS", "Semiconductors", "3X Leveraged Semiconductor ETF"),
    "SOXSUSDT": TradFiStockInfo("SOXSUSDT", "SOXS", "Direxion Daily Semi Bear 3X", "SEMICONDUCTORS", "Semiconductors", "3X Inverse Semiconductor ETF"),

    # ── 3. Index, Macro & Leveraged ETFs ──
    "SPYUSDT": TradFiStockInfo("SPYUSDT", "SPY", "SPDR S&P 500 ETF Trust", "INDEX_AND_ETFS", "Index & ETFs", "S&P 500 Benchmark Index"),
    "QQQUSDT": TradFiStockInfo("QQQUSDT", "QQQ", "Invesco QQQ Trust", "INDEX_AND_ETFS", "Index & ETFs", "Nasdaq-100 Tech Benchmark"),
    "TQQQUSDT": TradFiStockInfo("TQQQUSDT", "TQQQ", "ProShares UltraPro QQQ (3X)", "INDEX_AND_ETFS", "Index & ETFs", "3X Leveraged Nasdaq-100 ETF"),
    "SQQQUSDT": TradFiStockInfo("SQQQUSDT", "SQQQ", "ProShares UltraPro Short QQQ (-3X)", "INDEX_AND_ETFS", "Index & ETFs", "-3X Inverse Nasdaq-100 ETF"),
    "IWMUSDT": TradFiStockInfo("IWMUSDT", "IWM", "iShares Russell 2000 ETF", "INDEX_AND_ETFS", "Index & ETFs", "US Small-Cap Benchmark"),
    "DIAUSDT": TradFiStockInfo("DIAUSDT", "DIA", "SPDR Dow Jones Industrial ETF", "INDEX_AND_ETFS", "Index & ETFs", "Dow Jones 30 Benchmark"),
    "UVXYUSDT": TradFiStockInfo("UVXYUSDT", "UVXY", "ProShares Ultra VIX Short-Term", "INDEX_AND_ETFS", "Index & ETFs", "1.5X Leveraged S&P 500 VIX Volatility"),
    "BITOUSDT": TradFiStockInfo("BITOUSDT", "BITO", "ProShares Bitcoin Strategy ETF", "INDEX_AND_ETFS", "Index & ETFs", "SEC-Regulated Bitcoin Futures ETF"),
    "GDXUSDT": TradFiStockInfo("GDXUSDT", "GDX", "VanEck Gold Miners ETF", "INDEX_AND_ETFS", "Index & ETFs", "Gold Mining Industry ETF"),
    "XLEUSDT": TradFiStockInfo("XLEUSDT", "XLE", "Energy Select Sector SPDR", "INDEX_AND_ETFS", "Index & ETFs", "US Oil & Energy Majors ETF"),
    "EWZUSDT": TradFiStockInfo("EWZUSDT", "EWZ", "iShares MSCI Brazil ETF", "INDEX_AND_ETFS", "Index & ETFs", "Brazil Equities Benchmark"),
    "EWJUSDT": TradFiStockInfo("EWJUSDT", "EWJ", "iShares MSCI Japan ETF", "INDEX_AND_ETFS", "Index & ETFs", "Japan Nikkei Equities ETF"),

    # ── 4. AI & Pre-IPO / Synthetic Equities ──
    "OPENAIUSDT": TradFiStockInfo("OPENAIUSDT", "OPENAI", "OpenAI Pre-IPO Index", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Generative AI ChatGPT Creator"),
    "ANTHROPICUSDT": TradFiStockInfo("ANTHROPICUSDT", "ANTHROPIC", "Anthropic Pre-IPO Index", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Claude AI & Constitutional AI Pioneer"),
    "SPACEXUSDT": TradFiStockInfo("SPACEXUSDT", "SPACEX", "SpaceX Pre-IPO Index", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Aerospace & Starlink Satellite"),
    "SPCXUSDT": TradFiStockInfo("SPCXUSDT", "SPCX", "SpaceX Derivatives Index", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Private Space Tech Synthetic Contract"),
    "FWDIUSDT": TradFiStockInfo("FWDIUSDT", "FWDI", "Forward Industries Synthetic", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Tech Manufacturing & Pre-IPO Flow"),
    "RKLBUSDT": TradFiStockInfo("RKLBUSDT", "RKLB", "Rocket Lab USA Inc.", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Small Satellite Launch & Space Systems"),
    "MVLLUSDT": TradFiStockInfo("MVLLUSDT", "MVLL", "Marvel Synthetic Index", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Digital Entertainment & IP"),
    "POPMARTUSDT": TradFiStockInfo("POPMARTUSDT", "POPMART", "Pop Mart International", "AI_AND_PRE_IPO", "AI & Pre-IPO", "Global Designer Toy & IP Culture"),

    # ── 5. Traditional Financials & Conglomerates ──
    "BRKBUSDT": TradFiStockInfo("BRKBUSDT", "BRK.B", "Berkshire Hathaway Inc.", "FINANCIALS", "Financials & Conglomerate", "Warren Buffett Value Conglomerate"),
    "JPMUSDT": TradFiStockInfo("JPMUSDT", "JPM", "JPMorgan Chase & Co.", "FINANCIALS", "Financials & Conglomerate", "Largest US Commercial & Investment Bank"),
    "GSUSDT": TradFiStockInfo("GSUSDT", "GS", "Goldman Sachs Group", "FINANCIALS", "Financials & Conglomerate", "Global Investment Bank & Market Maker"),
    "MSUSDT": TradFiStockInfo("MSUSDT", "MS", "Morgan Stanley", "FINANCIALS", "Financials & Conglomerate", "Wealth Management & Trading"),
    "VUSDT": TradFiStockInfo("VUSDT", "V", "Visa Inc.", "FINANCIALS", "Financials & Conglomerate", "Global Payments & Settlement Network"),
    "PYPLUSDT": TradFiStockInfo("PYPLUSDT", "PYPL", "PayPal Holdings Inc.", "FINANCIALS", "Financials & Conglomerate", "Digital Payments & Venmo"),

    # ── 6. Global Tech & Asian Mega-Caps ──
    "BABAUSDT": TradFiStockInfo("BABAUSDT", "BABA", "Alibaba Group Holding", "GLOBAL_EQUITIES", "Global Equities", "Chinese E-Commerce & Cloud Giant"),
    "TENCENTUSDT": TradFiStockInfo("TENCENTUSDT", "TENCENT", "Tencent Holdings", "GLOBAL_EQUITIES", "Global Equities", "Gaming, WeChat & Asian Tech Conglomerate"),
    "SAMSUNGUSDT": TradFiStockInfo("SAMSUNGUSDT", "SAMSUNG", "Samsung Electronics", "GLOBAL_EQUITIES", "Global Equities", "Global Memory Chips & Consumer Tech"),
    "HYUNDAIUSDT": TradFiStockInfo("HYUNDAIUSDT", "HYUNDAI", "Hyundai Motor Company", "GLOBAL_EQUITIES", "Global Equities", "Automotive & Robotics"),
    "SONYUSDT": TradFiStockInfo("SONYUSDT", "SONY", "Sony Group Corporation", "GLOBAL_EQUITIES", "Global Equities", "PlayStation Gaming, Entertainment & Sensors"),
    "SKHYNIXUSDT": TradFiStockInfo("SKHYNIXUSDT", "SKHYNIX", "SK Hynix Inc.", "GLOBAL_EQUITIES", "Global Equities", "AI High-Bandwidth Memory (HBM) Supplier"),
    "CSOPSAMSUNG2LUSDT": TradFiStockInfo("CSOPSAMSUNG2LUSDT", "CSOP2L", "CSOP Samsung 2X Leveraged", "GLOBAL_EQUITIES", "Global Equities", "2X Leveraged Asian Tech ETF"),
    "CSOPSKHYNIX2LUSDT": TradFiStockInfo("CSOPSKHYNIX2LUSDT", "CSOP2L", "CSOP SK Hynix 2X Leveraged", "GLOBAL_EQUITIES", "Global Equities", "2X Leveraged HBM Semiconductor ETF"),

    # ── 7. Consumer, Healthcare & Industrial ──
    "WMTUSDT": TradFiStockInfo("WMTUSDT", "WMT", "Walmart Inc.", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "World Largest Retailer"),
    "COSTUSDT": TradFiStockInfo("COSTUSDT", "COST", "Costco Wholesale", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Membership Warehouse Club"),
    "DISUSDT": TradFiStockInfo("DISUSDT", "DIS", "The Walt Disney Company", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Entertainment, Parks & Disney+"),
    "KOUSDT": TradFiStockInfo("KOUSDT", "KO", "The Coca-Cola Company", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Global Beverage Leader"),
    "LLYUSDT": TradFiStockInfo("LLYUSDT", "LLY", "Eli Lilly and Company", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Biopharma & GLP-1 Weight Loss Drugs"),
    "CATUSDT": TradFiStockInfo("CATUSDT", "CAT", "Caterpillar Inc.", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Heavy Machinery & Construction Equipment"),
    "CVXUSDT": TradFiStockInfo("CVXUSDT", "CVX", "Chevron Corporation", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Integrated Global Energy & Oil Major"),
    "HDUSDT": TradFiStockInfo("HDUSDT", "HD", "The Home Depot Inc.", "CONSUMER_AND_HEALTHCARE", "Consumer & Healthcare", "Home Improvement Retail Leader"),
}


SECTOR_LABELS: Dict[str, str] = {
    "ALL": "Tất Cả Cổ Phiếu / ETF",
    "MEGA_TECH": "Mega-Cap Tech",
    "SEMICONDUCTORS": "Semiconductors",
    "INDEX_AND_ETFS": "Index & ETFs",
    "AI_AND_PRE_IPO": "AI & Pre-IPO",
    "FINANCIALS": "Financials",
    "GLOBAL_EQUITIES": "Global Equities",
    "CONSUMER_AND_HEALTHCARE": "Consumer & Healthcare",
}


def get_tradfi_stock_info(symbol: str) -> TradFiStockInfo:
    """Return metadata for a given TradFi/Stock symbol, or generic fallback."""
    sym = symbol.strip().upper()
    if sym in TRADFI_STOCK_DIRECTORY:
        return TRADFI_STOCK_DIRECTORY[sym]

    # Dynamic fallback for unknown stock symbols
    ticker = sym.replace("USDT", "").replace("2L", "").replace("2S", "")
    return TradFiStockInfo(
        symbol=sym,
        ticker=ticker,
        name=f"{ticker} US Equity Contract",
        sector="OTHER_TRADFI",
        sector_name="TradFi Derivatives",
        description="US Stock / TradFi Perpetual Futures Contract"
    )


def get_us_market_session(now_dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculate current US Stock Market Trading Session according to New York time (EST/EDT):
      - PRE_MARKET: 04:00 - 09:30 EST
      - REGULAR_HOURS: 09:30 - 16:00 EST (Main Wall Street Cash Session)
      - AFTER_HOURS: 16:00 - 20:00 EST
      - OVERNIGHT_24_7: 20:00 - 04:00 EST (Crypto-Futures Continual Trading)
    """
    if now_dt is None:
        now_dt = datetime.now(timezone.utc)

    # Convert UTC to US Eastern Time (UTC-4 in Daylight Saving, UTC-5 in Standard)
    est_hour = (now_dt.hour - 4) % 24
    est_minute = now_dt.minute
    est_time_decimal = est_hour + (est_minute / 60.0)
    weekday = now_dt.weekday() # 0 = Monday, 6 = Sunday

    is_weekend = weekday in (5, 6)

    if is_weekend:
        session_code = "OVERNIGHT_24_7"
        session_name = "24/7 Futures (Thị Trường Cơ Sở Đóng Cửa Cuối Tuần)"
        session_badge = "session-weekend"
        is_cash_open = False
    elif 9.5 <= est_time_decimal < 16.0:
        session_code = "REGULAR_HOURS"
        session_name = "PHIÊN CHÍNH WALL STREET (09:30 - 16:00 EST)"
        session_badge = "session-regular"
        is_cash_open = True
    elif 4.0 <= est_time_decimal < 9.5:
        session_code = "PRE_MARKET"
        session_name = "PHIÊN TIỀN THỊ TRƯỜNG PRE-MARKET (04:00 - 09:30 EST)"
        session_badge = "session-pre"
        is_cash_open = False
    elif 16.0 <= est_time_decimal < 20.0:
        session_code = "AFTER_HOURS"
        session_name = "PHIÊN SAU GIỜ AFTER-HOURS (16:00 - 20:00 EST)"
        session_badge = "session-after"
        is_cash_open = False
    else:
        session_code = "OVERNIGHT_24_7"
        session_name = "PHIÊN ĐÊM OVERNIGHT (20:00 - 04:00 EST / 24/7 Futures)"
        session_badge = "session-overnight"
        is_cash_open = False

    return {
        "session_code": session_code,
        "session_name": session_name,
        "session_badge": session_badge,
        "is_cash_open": is_cash_open,
        "est_time": f"{int(est_hour):02d}:{int(est_minute):02d} EST",
        "utc_time": now_dt.strftime("%H:%M:%S UTC"),
    }
