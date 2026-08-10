"""
Composite Pump Potential Scoring & Wave Stage Tagging
"""

from typing import Dict, Any


def calculate_pump_score(scorecard: Dict[str, Any], tier: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate normalized Pump Potential Score (0-100) and wave stage."""
    price_change_5m = scorecard.get("price_change_5m", 0.0) / 100.0
    vol_ratio = scorecard.get("vol_ratio", 1.0)
    buy_ratio = scorecard.get("buy_ratio", 50.0) / 100.0
    rsi = scorecard.get("rsi", 50.0)
    green_candles = scorecard.get("green_candles", 1)

    req_vol = tier.get("req_vol_spike", 5.0)
    req_price = tier.get("req_price_spike", 0.03)
    req_buy = tier.get("req_buy_ratio", 0.65)

    # 1. Volume Score (25% weight)
    s_vol = min(100.0, (vol_ratio / max(req_vol, 1.0)) * 75.0)

    # 2. Buy Ratio Score (25% weight)
    s_buy = min(100.0, max(0.0, (buy_ratio - 0.45) / 0.35 * 100.0))

    # 3. Price Spike Score (20% weight)
    s_price = min(100.0, max(0.0, (price_change_5m / max(req_price, 0.01)) * 70.0))

    # 4. RSI Sweetspot Score (15% weight) - Optimal between 65-75
    s_rsi = max(0.0, 100.0 - abs(rsi - 70.0) * 2.8)

    # 5. Green Candles Score (10% weight)
    s_green = min(100.0, (green_candles / 3.0) * 100.0)

    # 6. Open Interest / Funding Score (5% weight)
    s_oi = 75.0 if scorecard.get("open_interest", 0) > 0 else 50.0

    composite_score = (
        (s_vol * 0.25)
        + (s_buy * 0.25)
        + (s_price * 0.20)
        + (s_rsi * 0.15)
        + (s_green * 0.10)
        + (s_oi * 0.05)
    )
    composite_score = round(min(99.0, max(10.0, composite_score)), 1)

    # Wave Stage Tagging
    if vol_ratio >= req_vol and buy_ratio >= req_buy and price_change_5m <= req_price * 1.2:
        stage_tag = "🚀 CHÂN SÓNG"
        stage_class = "stage-early"
    elif price_change_5m >= req_price and green_candles >= 3:
        stage_tag = "⚡ ĐANG BÙNG NỔ"
        stage_class = "stage-surge"
    elif buy_ratio >= 0.70 and vol_ratio >= 2.5:
        stage_tag = "🔥 GOM HÀNG CỰC ĐẠI"
        stage_class = "stage-accum"
    else:
        stage_tag = "⏳ NÉN TÍCH LŨY"
        stage_class = "stage-compress"

    return {
        "score": composite_score,
        "stage_tag": stage_tag,
        "stage_class": stage_class,
        "breakdown": {
            "vol": round(s_vol, 1),
            "buy": round(s_buy, 1),
            "price": round(s_price, 1),
            "rsi": round(s_rsi, 1),
            "green": round(s_green, 1),
        }
    }
