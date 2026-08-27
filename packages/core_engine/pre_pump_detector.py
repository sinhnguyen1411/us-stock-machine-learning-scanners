"""
Pre-Pump Leading Indicators & Short Squeeze Detector (5-Pillar Quantitative Engine)
Calibrated for institutional compression, volume ignition, negative funding traps,
open interest expansion, and Wyckoff sideways accumulation structure.
"""

from typing import Dict, Any, Optional


def calculate_pre_pump_index(
    symbol: str,
    current_price: float,
    funding_rate: float = 0.0,
    open_interest: float = 0.0,
    quote_vol_24h: float = 0.0,
    pct_24h: float = 0.0,
    range_1h_avg: float = 5.0,
    vol_spike_1h: float = 1.0,
    taker_buy_1h: float = 50.0,
    depth_ratio: float = 1.0,
    next_funding_time: Optional[int] = None,
    atr: float = 0.0,
    candle_1h_pct: float = 0.0,
    macro_cycle_pos: float = 50.0,
    # â”€â”€ Pillar 5: Wyckoff Accumulation Quality â”€â”€
    drift_1d_pct: float = 0.0,          # 14-day price drift % (0~+12% = sideways-to-up = best)
    higher_low_quality: float = 1.0,    # recent_low / prev_low ratio (>= 1.0 = higher low structure)
    adr_contraction: float = 1.0,       # recent ADR / prev ADR (< 0.70 = tightening = nÃ©n Ä‘Ã¡y)
) -> Dict[str, Any]:
    """
    Computes institutional Pre-Pump Squeeze Anomaly Score (0 to 100) across 5 Core Pillars:
      1. Pillar 1: Negative Funding Squeeze (Max 30 pts)
      2. Pillar 2: Ignition Candle Trigger (Max 25 pts) - Bullish breakout only
      3. Pillar 3: Volatility Coiling & Compression (Max 25 pts)
      4. Pillar 4: Leverage Ratio (OI / Vol 24h) & Ask Vacuum (Max 20 pts)
      5. Pillar 5: Wyckoff Accumulation Quality (Max +20 pts) â€” sideways drift + higher low + ADR contraction
         Macro Cycle Base Guard: +10 pts bottom (<= 35%), -15 pts top peak (>= 70%)
    """
    breakdown = {}
    total_score = 0.0

    # â”€â”€ PILLAR 1: Negative Funding Rate Squeeze (Max 30 pts) â”€â”€
    funding_score = 0.0
    funding_pct = funding_rate * 100.0

    if funding_rate <= -0.015:   # <= -1.5%
        funding_score = 30.0
    elif funding_rate <= -0.010: # <= -1.0%
        funding_score = 26.0
    elif funding_rate <= -0.005: # <= -0.5%
        funding_score = 22.0
    elif funding_rate <= -0.002: # <= -0.2%
        funding_score = 16.0
    elif funding_rate <= -0.0008:# <= -0.08%
        funding_score = 12.0
    elif funding_rate <= -0.0002:# <= -0.02%
        funding_score = 8.0
    elif funding_rate < 0:
        funding_score = 5.0
    else:
        funding_score = 0.0

    breakdown["funding_score"] = round(funding_score, 1)
    total_score += funding_score

    # â”€â”€ PILLAR 2: Ignition Candle Trigger (Max 25 pts) â”€â”€
    # High volume spike in 1H candle â€” MUST be bullish or absorption candle, NOT a dump!
    ignition_score = 0.0
    is_bullish_ignition = (candle_1h_pct >= 0.0 and taker_buy_1h >= 48.0) or (candle_1h_pct >= -0.3 and taker_buy_1h >= 55.0)

    if is_bullish_ignition:
        if vol_spike_1h >= 3.0:
            ignition_score = 25.0
        elif vol_spike_1h >= 2.0:
            ignition_score = 20.0
        elif vol_spike_1h >= 1.5:
            ignition_score = 14.0
        elif vol_spike_1h >= 1.2:
            ignition_score = 8.0
        else:
            ignition_score = 0.0

        # Taker buy boost if bull dominance
        if taker_buy_1h >= 52.0 and ignition_score > 0:
            ignition_score = min(25.0, ignition_score + 3.0)
    else:
        # Dump candle with high volume is a sell-off, not pre-pump ignition!
        ignition_score = 0.0

    breakdown["ignition_score"] = round(ignition_score, 1)
    total_score += ignition_score

    # â”€â”€ PILLAR 3: Volatility Coiling & Compression (Max 25 pts) â”€â”€
    # Tight 1H candle ranges (< 3.5%) in the 24h prior to expansion
    coiling_score = 0.0
    if range_1h_avg <= 2.0:   # Ultra-compression
        coiling_score = 25.0
    elif range_1h_avg <= 3.5: # Tight coiling
        coiling_score = 20.0
    elif range_1h_avg <= 5.0:
        coiling_score = 14.0
    elif range_1h_avg <= 8.0:
        coiling_score = 8.0
    else:
        coiling_score = 4.0

    breakdown["coiling_score"] = round(coiling_score, 1)
    total_score += coiling_score

    # â”€â”€ PILLAR 4: Leverage Ratio & High Volume Squeeze Fuel (Max 20 pts) â”€â”€
    oi_usd = open_interest * current_price if current_price > 0 else 0.0
    oi_vol_ratio = (oi_usd / max(quote_vol_24h, 1.0)) if quote_vol_24h > 0 else 0.0

    leverage_score = 0.0
    if oi_vol_ratio >= 1.0 or depth_ratio >= 2.5 or (quote_vol_24h >= 8_000_000.0 and funding_rate < 0):
        leverage_score = 20.0
    elif oi_vol_ratio >= 0.5 or depth_ratio >= 1.8 or quote_vol_24h >= 4_000_000.0:
        leverage_score = 15.0
    elif oi_vol_ratio >= 0.1 or depth_ratio >= 1.2 or quote_vol_24h >= 1_000_000.0:
        leverage_score = 10.0
    else:
        leverage_score = 4.0

    breakdown["leverage_score"] = round(leverage_score, 1)
    total_score += leverage_score

    # â”€â”€ PILLAR 5: Wyckoff Accumulation Quality (Max ~20 pts, penalizes downtrends) â”€â”€

    # 5A. 14-day Drift Score â€” sideways-to-up is the holy grail
    wyckoff_drift_score = 0.0
    if 0.0 <= drift_1d_pct <= 12.0:
        # Perfect Wyckoff Base: sideways with slight upward bias
        wyckoff_drift_score = 10.0
    elif 12.0 < drift_1d_pct <= 25.0:
        # Already trending up â€” may be entering late
        wyckoff_drift_score = 4.0
    elif drift_1d_pct > 25.0:
        # Already pumped significantly â€” distribution risk
        wyckoff_drift_score = 0.0
    elif -8.0 <= drift_1d_pct < 0.0:
        # Mild pullback â€” neutral, not penalized
        wyckoff_drift_score = 0.0
    else:
        # drift < -8%: Actively declining â€” NOT a base, penalize
        wyckoff_drift_score = -10.0

    # 5B. Higher Low Structure Score
    wyckoff_hl_score = 0.0
    if higher_low_quality >= 1.00:
        # True higher low: recent bottom > previous bottom (Wyckoff Phase B/C)
        wyckoff_hl_score = 5.0
    elif higher_low_quality >= 0.95:
        # Near-equal lows: holding the base, acceptable
        wyckoff_hl_score = 2.0
    elif higher_low_quality >= 0.90:
        # Slightly lower low: mild concern
        wyckoff_hl_score = 0.0
    else:
        # Breaking down: price making consecutive lower lows â€” penalize
        wyckoff_hl_score = -5.0

    # 5C. ADR Contraction Score â€” daily range narrowing = coiling for breakout
    wyckoff_adr_score = 0.0
    if adr_contraction <= 0.55:
        # Extreme contraction: ATR shrinking dramatically
        wyckoff_adr_score = 5.0
    elif adr_contraction <= 0.70:
        # Strong contraction
        wyckoff_adr_score = 3.0
    elif adr_contraction <= 0.85:
        # Mild contraction
        wyckoff_adr_score = 1.0
    elif adr_contraction > 1.10:
        # Expanding volatility: uncertain direction
        wyckoff_adr_score = -3.0

    wyckoff_score = wyckoff_drift_score + wyckoff_hl_score + wyckoff_adr_score
    breakdown["wyckoff_score"] = round(wyckoff_score, 1)
    breakdown["wyckoff_drift_score"] = round(wyckoff_drift_score, 1)
    breakdown["wyckoff_hl_score"] = round(wyckoff_hl_score, 1)
    breakdown["wyckoff_adr_score"] = round(wyckoff_adr_score, 1)
    total_score += wyckoff_score

    # â”€â”€ MACRO CYCLE BASE GUARD (Reward Bottom, Penalize Distribution Peak) â”€â”€
    macro_score = 0.0
    if macro_cycle_pos <= 35.0:
        # True cycle base / bottom accumulation zone
        macro_score = 10.0
    elif macro_cycle_pos >= 70.0:
        # High plateau / distribution zone — reduced from -22 to -15 (Wyckoff now covers slope)
        macro_score = -15.0

    breakdown["macro_base_score"] = round(macro_score, 1)
    total_score += macro_score

    # Squeeze Momentum Bonus (breaking out with negative funding)
    if funding_rate < 0 and pct_24h >= 10.0 and is_bullish_ignition:
        total_score += 10.0

    # Final Score (0 - 100)
    final_score = min(100.0, max(0.0, round(total_score, 1)))

    # ── MARKET PHASES CLASSIFICATION ──

    # 1. Squeeze Expansion: Active short squeeze in progress
    if (pct_24h >= 8.0 and (funding_rate < 0 or final_score >= 65.0) and vol_spike_1h >= 1.8) or (pct_24h >= 20.0 and vol_spike_1h >= 2.5):
        phase = "SQUEEZE_EXPANSION"
        phase_tag = "SHORT SQUEEZE (10X-40X)"
        phase_class = "phase-squeeze"
        recommendation = "BẪY THANH LÝ: Phe Short chịu phí âm, máy xay thanh lý ép giá dựng cột. Kích hoạt Trailing Stop 12% để gồng."

    # 2. Ignition Triggered: Volume spike breakout with bullish candle
    elif vol_spike_1h >= 2.2 and is_bullish_ignition and pct_24h >= -3.0:
        phase = "IGNITION_TRIGGERED"
        phase_tag = "VỪA MỒI LỬA (IGNITION)"
        phase_class = "phase-ignition"
        recommendation = "CƠ HỘI VÀNG: Cây nến mồi lửa bùng nổ (Vol Spike > 2.2x, nến xanh). Đã thoát khỏi vùng nén, dòng tiền cá voi đã kích hoạt."

    # 3. Wyckoff Base: Sideways accumulation with upward drift
    elif wyckoff_score >= 10.0 and adr_contraction <= 0.85 and macro_cycle_pos <= 55.0 and drift_1d_pct >= -5.0:
        phase = "WYCKOFF_BASE"
        phase_tag = "NỀN WYCKOFF (SIDEWAYS BASE)"
        phase_class = "phase-coiling"
        recommendation = (
            f"CẤU TRÚC NỀN WYCKOFF: Giá đang tích lũy ngang hơi hướng lên ({drift_1d_pct:+.1f}% / 14 ngày), "
            f"biên độ ngày co lại ({adr_contraction:.2f}x), đáy đang tôn trọng (HL={higher_low_quality:.2f}). "
            f"Đây là mô hình nền trước khi bơm 10-40x. Chờ nến mồi lửa Volume để vào lệnh."
        )

    # 4. High Plateau Warning: Price at cycle peak, likely distribution
    elif macro_cycle_pos >= 70.0 and range_1h_avg <= 5.0:
        phase = "TOP_HIGH_PLATEAU"
        phase_tag = "NÉN VÙNG ĐỈNH (HIGH PLATEAU)"
        phase_class = "phase-normal"
        recommendation = f"CẢNH BÁO VÙNG CAO: Giá đang neo tại vùng đỉnh chu kỳ ({macro_cycle_pos:.1f}%). Khả năng nén phân phối chốt lời. Rủi ro cao khi Long."

    # 5. Pre-Ignition Coiling & Negative Funding Trap
    elif range_1h_avg <= 4.0 or funding_rate <= -0.0005:
        phase = "PRE_IGNITION_COILING"
        if funding_rate <= -0.002:
            phase_tag = "BẪY PHÍ ÂM (SHORT TRAP)"
            phase_class = "phase-coiling"
            recommendation = "BẪY SHORT CỰC NẶNG: Phe Short bu đông (Funding âm sâu < -0.2%), nhưng CHƯA có nến mồi xanh. Chờ nến mồi Volume xác nhận để Long."
        elif candle_1h_pct <= -1.5 and vol_spike_1h >= 2.0:
            phase_tag = "ĐANG NÉN ĐÁY (COILING)"
            phase_class = "phase-coiling"
            recommendation = f"ÁP LỰC XẢ: Nổ Volume 1H ({vol_spike_1h:.1f}x) nhưng là nến đỏ giảm ({candle_1h_pct:+.1f}%) phe bán xả hàng. Chờ lực đỡ hỗ trợ."
        else:
            phase_tag = "ĐANG NÉN ĐÁY (COILING)"
            phase_class = "phase-coiling"
            recommendation = f"TÍCH LŨY NỀN ĐÁY ({macro_cycle_pos:.1f}%): Nằm tại vùng gom hàng chu kỳ, biên độ 1H nén phẳng (< 3.5%), volume cạn kiệt. Chuẩn bị cho nhịp mồi lửa."

    # 6. Normal
    else:
        phase = "NORMAL"
        phase_tag = "BÌNH THƯỜNG"
        phase_class = "phase-normal"
        recommendation = "Chưa phát hiện sự bất đối xứng thanh khoản hay tín hiệu mồi lửa rõ rệt."

    # Suggested Trade Setup
    sl_distance = (atr * 1.5) if atr > 0 else (current_price * 0.05)
    suggested_sl = max(0.000001, current_price - sl_distance)
    tp1 = current_price * 1.20  # +20%
    tp2 = current_price * 1.50  # +50%

    return {
        "symbol": symbol,
        "price": current_price,
        "pct_24h": pct_24h,
        "funding_rate": funding_rate,
        "funding_pct": round(funding_pct, 4),
        "range_1h_avg": round(range_1h_avg, 2),
        "vol_spike_1h": round(vol_spike_1h, 1),
        "taker_buy_1h": round(taker_buy_1h, 1),
        "candle_1h_pct": round(candle_1h_pct, 2),
        "is_bullish_ignition": is_bullish_ignition,
        "open_interest": open_interest,
        "oi_usd": round(oi_usd, 2),
        "oi_vol_ratio": round(oi_vol_ratio, 2),
        "depth_ratio": round(depth_ratio, 2),
        "pre_pump_score": final_score,
        "macro_cycle_pos": round(macro_cycle_pos, 1),
        "wyckoff_score": round(wyckoff_score, 1),
        "drift_1d_pct": round(drift_1d_pct, 2),
        "higher_low_quality": round(higher_low_quality, 3),
        "adr_contraction": round(adr_contraction, 3),
        "phase": phase,
        "phase_tag": phase_tag,
        "phase_class": phase_class,
        "recommendation": recommendation,
        "breakdown": breakdown,
        "next_funding_time": next_funding_time,
        "trade_plan": {
            "entry": current_price,
            "sl": round(suggested_sl, 6),
            "tp1": round(tp1, 6),
            "tp2": round(tp2, 6),
            "trailing_stop_pct": 12.0,
        }
    }
