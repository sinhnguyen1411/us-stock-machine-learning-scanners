"""
Microstructure Technical Indicators & Confirmation Detectors
"""

from typing import List, Dict, Any


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI) across price series."""
    if len(closes) < period + 1:
        return 50.0

    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))

    recent_gains = gains[-period:]
    recent_losses = losses[-period:]
    avg_gain = sum(recent_gains) / period
    avg_loss = sum(recent_losses) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 1)


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calculate Average True Range (ATR) for dynamic volatility stop calculation."""
    if len(closes) < period + 1:
        return (highs[-1] - lows[-1]) if highs and lows else 0.0

    trs = []
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        pc = closes[i - 1]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)

    recent_trs = trs[-period:]
    return sum(recent_trs) / len(recent_trs) if recent_trs else 0.0


def evaluate_confirmation_layers(
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    taker_buy_volumes: List[float],
    open_interest: float = 0.0,
    funding_rate: float = 0.0,
    baseline_window: int = 20,
    price_window: int = 5,
    req_vol_spike: float = 5.0,
    req_price_spike: float = 0.03,
    req_buy_ratio: float = 0.65,
) -> Dict[str, Any]:
    """Evaluate author's 7-layer confirmation framework."""
    if len(closes) < max(baseline_window + 1, price_window + 1):
        raise ValueError("Insufficient candle data for 7-layer evaluation")

    # 1. Volume Spike (1M vs. 20-period baseline)
    last_vol = volumes[-1]
    baseline_vols = volumes[-(baseline_window + 1):-1]
    baseline_mean = (sum(baseline_vols) / len(baseline_vols)) if baseline_vols else 1.0
    vol_ratio = round(last_vol / max(baseline_mean, 1e-8), 2)

    # 2. 5-Minute Price Velocity
    p_start = closes[-min(price_window, len(closes))]
    p_now = closes[-1]
    price_change_5m = round(((p_now - p_start) / p_start) * 100.0, 2)

    # 3. Taker Buy Pressure Ratio
    recent_vols = volumes[-min(price_window, len(volumes)):]
    recent_buy_vols = taker_buy_volumes[-min(price_window, len(taker_buy_volumes)):]
    total_recent_vol = sum(recent_vols)
    total_buy_vol = sum(recent_buy_vols)
    buy_ratio = round((total_buy_vol / total_recent_vol * 100.0) if total_recent_vol > 0 else 50.0, 1)

    # 4. RSI (14)
    rsi = calculate_rsi(closes, period=14)

    # 5. Consecutive Bullish / Bearish Candles
    green_candles = 0
    for i in range(1, min(4, len(closes) + 1)):
        if closes[-i] >= opens[-i]:
            green_candles += 1
        else:
            break

    red_candles = 0
    for i in range(1, min(4, len(closes) + 1)):
        if closes[-i] < opens[-i]:
            red_candles += 1
        else:
            break

    # 6. ATR Volatility
    atr = calculate_atr(highs, lows, closes, period=14)

    # 7. Decision Verdict
    reasons = []
    action = "NEUTRAL"
    confidence = 35.0

    is_pump = (
        vol_ratio >= req_vol_spike
        and (price_change_5m / 100.0) >= req_price_spike
        and 60.0 <= rsi <= 85.0
        and green_candles >= 3
        and (buy_ratio / 100.0) >= req_buy_ratio
    )

    is_dump = (
        vol_ratio >= (req_vol_spike * 0.8)
        and rsi >= 82.0
        and (price_change_5m / 100.0) >= (req_price_spike * 1.5)
        and red_candles >= 1
    )

    if is_pump:
        action = "PUMP_LONG"
        confidence = 88.0
        reasons.append(f"Volume spike {vol_ratio}x >= {req_vol_spike}x threshold")
        reasons.append(f"5M price surge +{price_change_5m}% >= {req_price_spike*100}% threshold")
        reasons.append(f"Taker buy pressure {buy_ratio}% >= {req_buy_ratio*100}% threshold")
        reasons.append(f"RSI in optimal momentum zone ({rsi}) with 3/3 consecutive green candles")
    elif is_dump:
        action = "DUMP_SHORT"
        confidence = 78.0
        reasons.append(f"Overbought exhaustion (RSI {rsi} > 82)")
        reasons.append(f"Volume surge {vol_ratio}x with distribution candle")
    elif rsi < 25.0:
        action = "OVERSOLD_REBOUND"
        confidence = 65.0
        reasons.append(f"Deep oversold condition (RSI {rsi} < 25)")
    else:
        reasons.append("Market is consolidating. Microstructure metrics within normal baseline bounds.")

    return {
        "scorecard": {
            "vol_ratio": vol_ratio,
            "price_change_5m": price_change_5m,
            "buy_ratio": buy_ratio,
            "rsi": rsi,
            "green_candles": green_candles,
            "red_candles": red_candles,
            "atr": round(atr, 6),
            "open_interest": open_interest,
            "funding_rate": funding_rate,
        },
        "verdict": {
            "action": action,
            "confidence": confidence,
            "reasons": reasons,
        }
    }
