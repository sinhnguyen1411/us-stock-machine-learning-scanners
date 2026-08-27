"""
US Stock & TradFi Derivatives Machine Learning & Microstructure Anomaly Detector
Features: VWAP deviation, Institutional Order Flow, Opening Gap, Volatility Regime & ML Score (0-100)
"""

import math
from typing import List, Dict, Any, Optional
from .detector import calculate_rsi, calculate_atr
from .tradfi_classifier import get_tradfi_stock_info, get_us_market_session


def calculate_vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> float:
    """Calculate Volume-Weighted Average Price (VWAP) across series."""
    if not closes or not volumes:
        return 0.0

    cum_tp_vol = 0.0
    cum_vol = 0.0
    for h, l, c, v in zip(highs, lows, closes, volumes):
        typical_price = (h + l + c) / 3.0
        cum_tp_vol += (typical_price * v)
        cum_vol += v

    return (cum_tp_vol / cum_vol) if cum_vol > 0 else closes[-1]


def calculate_realized_volatility(closes: List[float], window: int = 20) -> float:
    """Calculate annualized realized volatility percentage proxy."""
    if len(closes) < 3:
        return 15.0

    sub = closes[-min(window, len(closes)):]
    log_returns = [math.log(sub[i] / sub[i - 1]) for i in range(1, len(sub))]
    if not log_returns:
        return 15.0

    mean_ret = sum(log_returns) / len(log_returns)
    variance = sum((r - mean_ret) ** 2 for r in log_returns) / max(1, len(log_returns) - 1)
    std_dev = math.sqrt(variance)
    # Annualize assuming 252 trading days or 365 continuous days (approx ~252 * 390 min)
    annualized = std_dev * math.sqrt(252 * 390) * 100.0
    return round(min(150.0, max(5.0, annualized)), 2)


def evaluate_tradfi_ml_metrics(
    symbol: str,
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    taker_buy_volumes: List[float],
    price_now: float,
    pct_24h: float,
    quote_vol_24h: float = 0.0,
    open_interest: float = 0.0,
    funding_rate: float = 0.0,
    baseline_window: int = 20,
) -> Dict[str, Any]:
    """
    Compute TradFi Machine Learning & Institutional Microstructure Metrics:
      - VWAP & Institutional Bands
      - Volume Ignition Ratio
      - Taker Buy Institutional Pressure
      - Opening Gap & Session Velocity
      - Composite ML Anomaly Score (0 - 100)
    """
    stock_info = get_tradfi_stock_info(symbol)
    session_info = get_us_market_session()

    if len(closes) < 5:
        return {
            "symbol": symbol,
            "stock_info": stock_info.to_dict(),
            "price": price_now,
            "pct_24h": pct_24h,
            "ml_score": 50.0,
            "signal": "NEUTRAL",
            "confidence": 50.0,
        }

    # 1. VWAP & Distance
    vwap = calculate_vwap(highs, lows, closes, volumes)
    vwap_distance_pct = round(((price_now - vwap) / max(vwap, 1e-9)) * 100.0, 2)

    # 2. Volume Spike Ratio
    last_vol = volumes[-1]
    base_vols = volumes[-(baseline_window + 1):-1] if len(volumes) > baseline_window else volumes[:-1]
    base_vol_mean = (sum(base_vols) / len(base_vols)) if base_vols else 1.0
    vol_spike = round(last_vol / max(base_vol_mean, 1e-9), 2)

    # 3. Taker Buy Pressure Ratio
    recent_vols = volumes[-5:]
    recent_buys = taker_buy_volumes[-5:]
    tot_vol = sum(recent_vols)
    tot_buy = sum(recent_buys)
    taker_buy_ratio = round((tot_buy / tot_vol * 100.0) if tot_vol > 0 else 50.0, 1)

    # 4. Technical Momentum Indicators
    rsi = calculate_rsi(closes, period=14)
    atr = calculate_atr(highs, lows, closes, period=14)
    realized_vol = calculate_realized_volatility(closes, window=20)

    # 5. Price Momentum & Gap
    p_start = closes[-min(5, len(closes))]
    price_change_5m = round(((price_now - p_start) / max(p_start, 1e-9)) * 100.0, 2)
    gap_pct = round(((closes[-1] - opens[0]) / max(opens[0], 1e-9)) * 100.0, 2)

    # 6. Consecutive Green / Red Candles
    green_candles = 0
    for i in range(1, min(4, len(closes) + 1)):
        if closes[-i] >= opens[-i]:
            green_candles += 1
        else:
            break

    # ── Machine Learning Composite Scoring (0 to 100) ──
    # S_vol: Volume anomaly (Target >= 3.0x -> max score)
    s_vol = min(100.0, (vol_spike / 3.0) * 85.0)

    # S_buy: Institutional buyer dominance (Target >= 60% -> max score)
    s_buy = min(100.0, max(0.0, (taker_buy_ratio - 45.0) / 30.0 * 100.0))

    # S_vwap: Price trading above VWAP with healthy cushion (+0.3% to +3.0%)
    if vwap_distance_pct >= 0.0:
        s_vwap = min(100.0, 50.0 + (vwap_distance_pct / 2.0) * 50.0)
    else:
        s_vwap = max(0.0, 50.0 + (vwap_distance_pct / 2.0) * 50.0)

    # S_rsi: Optimal trend continuation sweetspot (RSI 55 - 72)
    s_rsi = max(0.0, 100.0 - abs(rsi - 65.0) * 2.5)

    # S_gap: Price expansion velocity
    s_gap = min(100.0, max(0.0, (abs(price_change_5m) / 1.5) * 80.0))

    ml_composite_score = (
        (s_vol * 0.20)
        + (s_buy * 0.25)
        + (s_vwap * 0.20)
        + (s_rsi * 0.15)
        + (s_gap * 0.15)
        + (5.0 if session_info["is_cash_open"] else 2.5) # Session liquidity bonus
    )
    ml_score = round(min(99.0, max(15.0, ml_composite_score)), 1)

    # ── Signal Determination ──
    reasons = []
    if ml_score >= 75.0 and vol_spike >= 2.0 and green_candles >= 2 and vwap_distance_pct >= 0:
        signal = "STRONG_BUY_BREAKOUT"
        signal_tag = "MUA ĐỘT PHÁ MẠNH (ML BUY)"
        signal_class = "tradfi-signal-buy"
        confidence = 88.0
        reasons.append(f"Volume bùng nổ {vol_spike}x với {green_candles} nến xanh liên tiếp")
        reasons.append(f"Giá nằm trên đường thể chế VWAP ({vwap_distance_pct:+.2f}%)")
        reasons.append(f"Lực gom thể chế Taker Buy {taker_buy_ratio}%")
    elif taker_buy_ratio >= 65.0 and -0.5 <= vwap_distance_pct <= 1.5:
        signal = "INSTITUTIONAL_ACCUMULATION"
        signal_tag = "THỂ CHẾ GOM HÀNG (ACCUMULATION)"
        signal_class = "tradfi-signal-accum"
        confidence = 80.0
        reasons.append(f"Taker Buy mua chủ động đạt {taker_buy_ratio}% quanh mốc VWAP")
        reasons.append("Đang nén chặt chuẩn bị cho pha bùng nổ biên độ")
    elif price_change_5m >= 1.5 and rsi >= 60.0:
        signal = "MOMENTUM_SURGE"
        signal_tag = "SÓNG TĂNG TỐC (MOMENTUM)"
        signal_class = "tradfi-signal-surge"
        confidence = 75.0
        reasons.append(f"Đà tăng 5M ({price_change_5m:+.2f}%) với RSI tích cực ({rsi})")
    elif rsi >= 82.0:
        signal = "OVERBOUGHT_EXHAUSTION"
        signal_tag = "QUÁ MUA (EXHAUSTION)"
        signal_class = "tradfi-signal-exhaust"
        confidence = 70.0
        reasons.append(f"RSI chạm vùng quá mua ({rsi}), rủi ro điều chỉnh ngắn hạn")
    else:
        signal = "NEUTRAL"
        signal_tag = "BÌNH THƯỜNG / TÍCH LŨY"
        signal_class = "tradfi-signal-neutral"
        confidence = 50.0
        reasons.append("Biến động trong giới hạn dao động thông thường")

    # Trade Targets (ATR based)
    sl_dist = (atr * 1.5) if atr > 0 else (price_now * 0.015)
    tp1 = price_now * 1.025  # +2.5% for stock futures
    tp2 = price_now * 1.050  # +5.0%
    tp3 = price_now * 1.100  # +10.0%

    return {
        "symbol": symbol,
        "ticker": stock_info.ticker,
        "name": stock_info.name,
        "sector": stock_info.sector,
        "sector_name": stock_info.sector_name,
        "description": stock_info.description,
        "price": price_now,
        "pct_24h": pct_24h,
        "quote_vol_24h": quote_vol_24h,
        "vwap": round(vwap, 4),
        "vwap_distance_pct": vwap_distance_pct,
        "vol_spike": vol_spike,
        "taker_buy_ratio": taker_buy_ratio,
        "price_change_5m": price_change_5m,
        "gap_pct": gap_pct,
        "rsi": rsi,
        "atr": round(atr, 4),
        "realized_vol_pct": realized_vol,
        "ml_score": ml_score,
        "signal": signal,
        "signal_tag": signal_tag,
        "signal_class": signal_class,
        "confidence": confidence,
        "reasons": reasons,
        "session": session_info,
        "breakdown": {
            "vol_score": round(s_vol, 1),
            "buy_score": round(s_buy, 1),
            "vwap_score": round(s_vwap, 1),
            "rsi_score": round(s_rsi, 1),
            "gap_score": round(s_gap, 1),
        },
        "trade_plan": {
            "entry": price_now,
            "sl": round(max(0.001, price_now - sl_dist), 4),
            "tp1": round(tp1, 4),
            "tp2": round(tp2, 4),
            "tp3": round(tp3, 4),
        }
    }
