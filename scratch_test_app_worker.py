import sys
from pathlib import Path
ROOT_DIR = Path(".")
sys.path.insert(0, str(ROOT_DIR / "apps/web_terminal"))
sys.path.insert(0, str(ROOT_DIR / "packages"))

from app import _analyze_pre_pump_symbol, connector

p = {"symbol": "OGNUSDT", "lastFundingRate": -0.000198, "markPrice": 0.0168}
t = {"priceChangePercent": 0.60, "quoteVolume": 1100000.0}

res = _analyze_pre_pump_symbol((p, t))
print("OGNUSDT Score:", res["pre_pump_score"])
print("OGNUSDT Phase:", res["phase"])
print("OGNUSDT VolSpike:", res["vol_spike_1h"])
print("OGNUSDT BuyRatio:", res["taker_buy_1h"])
print("OGNUSDT Candle1hPct:", res["candle_1h_pct"])
