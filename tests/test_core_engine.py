"""
Unit Tests for Core Engine Package
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from core_engine import (
    classify_asset_tier,
    calculate_rsi,
    calculate_atr,
    calculate_pump_score,
    evaluate_confirmation_layers,
)


def test_classify_asset_tier():
    btc_tier = classify_asset_tier("BTCUSDT")
    assert btc_tier.code == "LARGE_CAP"
    assert btc_tier.req_vol_spike == 2.0

    doge_tier = classify_asset_tier("DOGEUSDT")
    assert doge_tier.code == "MID_CAP"
    assert doge_tier.req_vol_spike == 3.5

    meme_tier = classify_asset_tier("TUTUSDT")
    assert meme_tier.code == "LOW_CAP_MEME"
    assert meme_tier.req_vol_spike == 5.0


def test_calculate_rsi():
    # Constant prices -> RSI should be neutral
    closes = [100.0] * 30
    assert calculate_rsi(closes) == 50.0

    # Strictly rising prices -> RSI should approach 100
    rising = [100.0 + i * 2.0 for i in range(30)]
    assert calculate_rsi(rising) == 100.0


def test_calculate_pump_score():
    scorecard = {
        "price_change_5m": 3.5,
        "vol_ratio": 6.0,
        "buy_ratio": 75.0,
        "rsi": 70.0,
        "green_candles": 3,
        "open_interest": 1000000,
    }
    tier = {
        "req_vol_spike": 5.0,
        "req_price_spike": 0.03,
        "req_buy_ratio": 0.65,
    }

    result = calculate_pump_score(scorecard, tier)
    assert result["score"] >= 70.0
    assert result["stage_tag"] in ["🚀 CHÂN SÓNG", "⚡ ĐANG BÙNG NỔ"]


if __name__ == "__main__":
    test_classify_asset_tier()
    test_calculate_rsi()
    test_calculate_pump_score()
    print("All core engine unit tests passed successfully!")
