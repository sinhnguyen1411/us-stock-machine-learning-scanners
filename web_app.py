"""
Binance Futures (USDT-M) Real-Time Scanner & Trading Web UI
============================================================
Flask Backend serving live Binance Futures data, 7-layer pump/dump analysis,
interactive charts, and paper trading execution.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from binance.client import Client
from flask import Flask, jsonify, render_template, request

# Reconfigure stdout for unicode safety
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("web_app")

app = Flask(__name__)

# Initialize Binance Client (Public read access)
client = Client()

# In-memory Paper Trading Portfolio
PAPER_PORTFOLIO = {
    "equity": 1000.0,
    "initial_equity": 1000.0,
    "active_positions": {},  # symbol -> position dict
    "trade_history": [],
}

# Cache for symbols
_SYMBOLS_CACHE = {
    "timestamp": 0,
    "symbols": [],
}


def get_all_usdt_perp_symbols():
    """Fetch and cache all active Binance USDT-M Perpetual symbols."""
    now = time.time()
    if _SYMBOLS_CACHE["symbols"] and (now - _SYMBOLS_CACHE["timestamp"] < 300):
        return _SYMBOLS_CACHE["symbols"]

    try:
        info = client.futures_exchange_info()
        symbols = [
            s["symbol"] for s in info.get("symbols", [])
            if s.get("quoteAsset") == "USDT"
            and s.get("status") == "TRADING"
            and s.get("contractType") == "PERPETUAL"
        ]
        _SYMBOLS_CACHE["symbols"] = sorted(symbols)
        _SYMBOLS_CACHE["timestamp"] = now
        return _SYMBOLS_CACHE["symbols"]
    except Exception as e:
        logger.error(f"Error loading symbols: {e}")
        return _SYMBOLS_CACHE["symbols"] or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "TUTUSDT", "BMTUSDT", "CAPUSDT"]


def analyze_symbol(symbol: str, interval: str = "1m"):
    """Perform comprehensive 7-layer pump/dump analysis on a symbol."""
    symbol = symbol.strip().upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"

    # 1. 24h Ticker info
    try:
        ticker = client.futures_ticker(symbol=symbol)
    except Exception as e:
        return {"error": f"Symbol '{symbol}' not found on Binance Futures USDT-M: {str(e)}"}

    price = float(ticker.get("lastPrice", 0))
    pct_24h = float(ticker.get("priceChangePercent", 0))
    high_24h = float(ticker.get("highPrice", 0))
    low_24h = float(ticker.get("lowPrice", 0))
    quote_vol_24h = float(ticker.get("quoteVolume", 0))

    # 2. Fetch candlesticks
    limit = 60
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    if not klines or len(klines) < 20:
        return {"error": f"Insufficient candle data for {symbol}"}

    candles_data = []
    closes, opens, highs, lows, volumes, taker_buys = [], [], [], [], [], []

    for k in klines:
        t_ms = k[0]
        o = float(k[1])
        h = float(k[2])
        l = float(k[3])
        c = float(k[4])
        v = float(k[5])
        tb = float(k[9])

        closes.append(c)
        opens.append(o)
        highs.append(h)
        lows.append(l)
        volumes.append(v)
        taker_buys.append(tb)

        candles_data.append({
            "time": t_ms // 1000,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
            "taker_buy": tb,
        })

    closes = np.array(closes)
    opens = np.array(opens)
    highs = np.array(highs)
    lows = np.array(lows)
    volumes = np.array(volumes)
    taker_buys = np.array(taker_buys)

    # 3. Metrics calculation
    last_vol = volumes[-1]
    baseline_vol = np.mean(volumes[-20:-1]) if len(volumes) > 1 else 1.0
    vol_ratio = last_vol / max(baseline_vol, 1e-9)

    recent_buy_vol = np.sum(taker_buys[-5:])
    recent_tot_vol = np.sum(volumes[-5:])
    buy_ratio = recent_buy_vol / max(recent_tot_vol, 1e-9)

    price_change_5m = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else (pct_24h / 100.0)

    # 14-period RSI
    deltas = np.diff(closes[-15:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    rs = avg_gain / max(avg_loss, 1e-9)
    rsi = float(100.0 - (100.0 / (1.0 + rs)))

    # 14-period ATR
    trs = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(-14, 0)
    ]
    atr = float(np.mean(trs))

    # Consecutive green candles
    green_candles = sum(1 for i in range(-1, -4, -1) if closes[i] > opens[i])
    red_candles = sum(1 for i in range(-1, -4, -1) if closes[i] < opens[i])

    # Derivatives data (OI & Funding)
    funding_rate = 0.0
    try:
        fr_data = client.futures_funding_rate(symbol=symbol, limit=1)
        if fr_data:
            funding_rate = float(fr_data[0].get("fundingRate", 0))
    except Exception:
        pass

    open_interest = 0.0
    try:
        oi_data = client.futures_open_interest(symbol=symbol)
        open_interest = float(oi_data.get("openInterest", 0))
    except Exception:
        pass

    # 4. Adaptive Coin Classification & Dynamic Thresholds
    bluechip_caps = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT"}
    mid_caps = {"DOGEUSDT", "LINKUSDT", "DOTUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "TRXUSDT", "LTCUSDT"}

    if symbol in bluechip_caps:
        tier_code = "LARGE_CAP"
        tier_name = "👑 Bluechip Large-Cap"
        req_vol_spike = 2.0
        req_price_spike = 0.010  # +1.0%
        req_buy_ratio = 0.60
        tp1_mult = 0.02  # +2.0%
        tp2_mult = 0.04  # +4.0%
        tp3_mult = 0.08  # +8.0%
    elif symbol in mid_caps or (quote_vol_24h >= 200_000_000 and abs(pct_24h) < 15.0):
        tier_code = "MID_CAP"
        tier_name = "⚡ Mid-Cap Trending"
        req_vol_spike = 3.5
        req_price_spike = 0.020  # +2.0%
        req_buy_ratio = 0.62
        tp1_mult = 0.035 # +3.5%
        tp2_mult = 0.07  # +7.0%
        tp3_mult = 0.15  # +15.0%
    else:
        tier_code = "LOW_CAP_MEME"
        tier_name = "🚀 High-Volatility / Meme"
        req_vol_spike = 5.0
        req_price_spike = 0.030  # +3.0%
        req_buy_ratio = 0.65
        tp1_mult = 0.05  # +5.0%
        tp2_mult = 0.10  # +10.0%
        tp3_mult = 0.20  # +20.0%

    # 5. Signal Scoring & Decision Logic
    is_pump = False
    is_dump = False
    is_oversold = False
    verdict = "NEUTRAL"
    confidence = 0.0
    reasons = []

    # Check Pump Long
    if vol_ratio >= req_vol_spike and price_change_5m >= req_price_spike and buy_ratio >= req_buy_ratio and 55 <= rsi <= 85:
        is_pump = True
        verdict = "PUMP_LONG"
        confidence = min(0.96, (vol_ratio / (req_vol_spike * 1.5)) * 0.3 + (buy_ratio / 0.8) * 0.3 + (price_change_5m / (req_price_spike * 1.5)) * 0.2 + (rsi / 75.0) * 0.2)
        reasons.append(f"Volume đột biến {vol_ratio:.1f}x (Chuẩn {tier_name}: ≥{req_vol_spike}x)")
        reasons.append(f"Taker Buy Ratio áp đảo {buy_ratio:.1%} (Chuẩn: ≥{req_buy_ratio:.0%})")
        reasons.append(f"Biến động 5M đạt {price_change_5m:+.2%} (Chuẩn: ≥{req_price_spike:+.1%})")
        reasons.append(f"RSI({rsi:.0f}) nằm trong vùng động lượng tăng mạnh")
    # Check Dump Short
    elif rsi >= 78 and buy_ratio <= 0.45:
        is_dump = True
        verdict = "DUMP_SHORT"
        confidence = min(0.90, (rsi / 85.0) * 0.4 + (1.0 - buy_ratio) * 0.3 + (abs(funding_rate) / 0.001) * 0.3)
        reasons.append(f"RSI({rsi:.0f}) rơi vào vùng quá mua cực đại")
        reasons.append(f"Lực mua suy giảm, Taker Buy chỉ còn {buy_ratio:.1%}")
        if funding_rate > 0.0005:
            reasons.append(f"Funding rate (+{funding_rate:.4%}) quá cao, nguy cơ xả ép Long")
    # Check Oversold Rebound
    elif rsi <= 25:
        is_oversold = True
        verdict = "OVERSOLD_REBOUND"
        confidence = min(0.85, (30.0 - rsi) / 20.0 * 0.8 + 0.2)
        reasons.append(f"RSI({rsi:.0f}) rơi vào vùng quá bán sâu (Tiềm năng hồi kỹ thuật)")
    else:
        confidence = 0.35
        reasons.append(f"Thị trường đang tích lũy, các chỉ số chưa đạt ngưỡng kích hoạt ({tier_name})")

    # Suggested Trade Plan (Adaptive Cascade TP)
    sl_price = closes[-1] - (atr * 1.5) if verdict != "DUMP_SHORT" else closes[-1] + (atr * 2.0)
    tp1 = closes[-1] * (1.0 + tp1_mult) if verdict != "DUMP_SHORT" else closes[-1] * (1.0 - tp1_mult)
    tp2 = closes[-1] * (1.0 + tp2_mult) if verdict != "DUMP_SHORT" else closes[-1] * (1.0 - tp2_mult)
    tp3 = closes[-1] * (1.0 + tp3_mult) if verdict != "DUMP_SHORT" else closes[-1] * (1.0 - tp3_mult)

    return {
        "symbol": symbol,
        "price": price,
        "pct_24h": pct_24h,
        "tier": {
            "code": tier_code,
            "name": tier_name,
            "req_vol_spike": req_vol_spike,
            "req_price_spike": req_price_spike,
            "req_buy_ratio": req_buy_ratio,
        },
        "pct_24h": pct_24h,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "quote_vol_24h": quote_vol_24h,
        "interval": interval,
        "candles": candles_data,
        "scorecard": {
            "vol_ratio": round(vol_ratio, 2),
            "price_change_5m": round(price_change_5m * 100.0, 2),
            "buy_ratio": round(buy_ratio * 100.0, 1),
            "rsi": round(rsi, 1),
            "atr": round(atr, 6),
            "green_candles": green_candles,
            "red_candles": red_candles,
            "funding_rate": round(funding_rate * 100.0, 4),
            "open_interest": round(open_interest, 2),
        },
        "verdict": {
            "action": verdict,
            "confidence": round(confidence * 100.0, 1),
            "reasons": reasons,
        },
        "trade_plan": {
            "entry": price,
            "stop_loss": round(sl_price, 6),
            "tp1": round(tp1, 6),
            "tp2": round(tp2, 6),
            "tp3": round(tp3, 6),
            "leverage": 5,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Render main trading dashboard."""
    return render_template("index.html")


@app.route("/api/symbols")
def api_symbols():
    """Get list of active symbols."""
    symbols = get_all_usdt_perp_symbols()
    return jsonify({"symbols": symbols})


@app.route("/api/top_movers")
def api_top_movers():
    """Get real-time top movers and pump candidates."""
    try:
        tickers = client.futures_ticker()
        pumps = []
        dumps = []

        for t in tickers:
            sym = t.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            pct = float(t.get("priceChangePercent", 0) or 0)
            vol = float(t.get("quoteVolume", 0) or 0)
            price = float(t.get("lastPrice", 0) or 0)

            if vol >= 500000 and abs(pct) >= 3.0:
                item = {
                    "symbol": sym,
                    "price": price,
                    "pct_24h": pct,
                    "volume": vol,
                }
                if pct > 0:
                    pumps.append(item)
                else:
                    dumps.append(item)

        pumps.sort(key=lambda x: x["pct_24h"], reverse=True)
        dumps.sort(key=lambda x: x["pct_24h"])

        return jsonify({
            "top_gainers": pumps[:8],
            "top_losers": dumps[:8],
            "total_active": len(tickers),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/<symbol>")
def api_analyze(symbol: str):
    """Analyze a single symbol."""
    interval = request.args.get("interval", "1m")
    result = analyze_symbol(symbol, interval=interval)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/portfolio")
def api_portfolio():
    """Get paper trading portfolio and positions."""
    # Update active positions unrealized PnL
    positions_list = []
    total_unrealized_pnl = 0.0

    for sym, pos in list(PAPER_PORTFOLIO["active_positions"].items()):
        try:
            ticker = client.futures_ticker(symbol=sym)
            curr_price = float(ticker.get("lastPrice", pos["entry"]))
            side = pos["side"]
            qty = pos["quantity"]

            if side == "LONG":
                pnl = (curr_price - pos["entry"]) * qty
                pnl_pct = (curr_price / pos["entry"] - 1.0) * 100.0 * pos["leverage"]
            else:
                pnl = (pos["entry"] - curr_price) * qty
                pnl_pct = (1.0 - curr_price / pos["entry"]) * 100.0 * pos["leverage"]

            pos["current_price"] = curr_price
            pos["unrealized_pnl"] = round(pnl, 2)
            pos["pnl_pct"] = round(pnl_pct, 2)
            total_unrealized_pnl += pnl
            positions_list.append(pos)
        except Exception:
            positions_list.append(pos)

    return jsonify({
        "equity": round(PAPER_PORTFOLIO["equity"] + total_unrealized_pnl, 2),
        "balance": round(PAPER_PORTFOLIO["equity"], 2),
        "unrealized_pnl": round(total_unrealized_pnl, 2),
        "active_positions": positions_list,
        "history": PAPER_PORTFOLIO["trade_history"][-15:],
    })


@app.route("/api/trade", methods=["POST"])
def api_trade():
    """Open a simulated paper position."""
    data = request.json or {}
    symbol = data.get("symbol", "").upper()
    side = data.get("side", "LONG").upper()
    notional = float(data.get("notional", 100.0))
    leverage = int(data.get("leverage", 5))

    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400

    if symbol in PAPER_PORTFOLIO["active_positions"]:
        return jsonify({"error": f"Vị thế trên {symbol} đã tồn tại!"}), 400

    try:
        ticker = client.futures_ticker(symbol=symbol)
        price = float(ticker.get("lastPrice", 0))
        if price <= 0:
            return jsonify({"error": "Không thể lấy giá của symbol này"}), 400

        qty = (notional * leverage) / price

        position = {
            "symbol": symbol,
            "side": side,
            "entry": price,
            "quantity": qty,
            "notional": notional,
            "leverage": leverage,
            "opened_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "sl": data.get("sl", price * 0.95 if side == "LONG" else price * 1.05),
            "tp": data.get("tp", price * 1.10 if side == "LONG" else price * 0.90),
        }

        PAPER_PORTFOLIO["active_positions"][symbol] = position

        return jsonify({
            "success": True,
            "message": f"Đã mở vị thế Paper Trade {side} {symbol} tại giá ${price:.4f}",
            "position": position
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/close_trade", methods=["POST"])
def api_close_trade():
    """Close a simulated paper position."""
    data = request.json or {}
    symbol = data.get("symbol", "").upper()

    if symbol not in PAPER_PORTFOLIO["active_positions"]:
        return jsonify({"error": "Không tìm thấy vị thế để đóng"}), 404

    pos = PAPER_PORTFOLIO["active_positions"].pop(symbol)
    try:
        ticker = client.futures_ticker(symbol=symbol)
        exit_price = float(ticker.get("lastPrice", pos["entry"]))
    except Exception:
        exit_price = pos["entry"]

    if pos["side"] == "LONG":
        pnl = (exit_price - pos["entry"]) * pos["quantity"]
        pnl_pct = (exit_price / pos["entry"] - 1.0) * 100.0 * pos["leverage"]
    else:
        pnl = (pos["entry"] - exit_price) * pos["quantity"]
        pnl_pct = (1.0 - exit_price / pos["entry"]) * 100.0 * pos["leverage"]

    PAPER_PORTFOLIO["equity"] += pnl
    record = {
        "symbol": symbol,
        "side": pos["side"],
        "entry": pos["entry"],
        "exit": exit_price,
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "closed_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
    }
    PAPER_PORTFOLIO["trade_history"].append(record)

    return jsonify({
        "success": True,
        "message": f"Đã đóng vị thế {symbol}. PnL: ${pnl:+.2f} ({pnl_pct:+.1f}%)",
        "record": record
    })


@app.route("/api/live_signals")
def api_live_signals():
    """Return real-time pump/dump signals detected across all 526 pairs."""
    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "count": len(LIVE_RADAR_SIGNALS),
        "signals": LIVE_RADAR_SIGNALS,
    })


@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    """Run historical backtest of Cascade TP strategy on 1m candles."""
    try:
        from backtest_engine import CascadeBacktestEngine
        data = request.json or {}
        symbol = data.get("symbol", "BTCUSDT")
        days = int(data.get("days", 7))
        initial_balance = float(data.get("initial_balance", 1000.0))

        engine = CascadeBacktestEngine(client=client)
        result = engine.run_backtest(
            symbol=symbol,
            days=days,
            initial_balance=initial_balance
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Backtest error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def calculate_pump_score(res: dict) -> dict:
    """Calculate composite Pump Potential Score (0-100) and identify wave stage."""
    sc = res.get("scorecard", {})
    tier = res.get("tier", {})
    price_change_5m = sc.get("price_change_5m", 0.0) / 100.0
    vol_ratio = sc.get("vol_ratio", 1.0)
    buy_ratio = sc.get("buy_ratio", 50.0) / 100.0
    rsi = sc.get("rsi", 50.0)
    green_candles = sc.get("green_candles", 1)

    req_vol = tier.get("req_vol_spike", 5.0)
    req_price = tier.get("req_price_spike", 0.03)
    req_buy = tier.get("req_buy_ratio", 0.65)

    # 1. Volume Score (25%)
    s_vol = min(100.0, (vol_ratio / max(req_vol, 1.0)) * 75.0)

    # 2. Buy Ratio Score (25%)
    s_buy = min(100.0, max(0.0, (buy_ratio - 0.45) / 0.35 * 100.0))

    # 3. Price Spike Score (20%)
    s_price = min(100.0, max(0.0, (price_change_5m / max(req_price, 0.01)) * 70.0))

    # 4. RSI Sweetspot Score (15%) - Optimal between 65-75
    s_rsi = max(0.0, 100.0 - abs(rsi - 70.0) * 2.8)

    # 5. Green Candles Score (10%)
    s_green = min(100.0, (green_candles / 3.0) * 100.0)

    # 6. Open Interest / Funding (5%)
    s_oi = 75.0 if sc.get("open_interest", 0) > 0 else 50.0

    composite_score = (s_vol * 0.25) + (s_buy * 0.25) + (s_price * 0.20) + (s_rsi * 0.15) + (s_green * 0.10) + (s_oi * 0.05)
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


# ─── Background Live Radar & Top 10 Pump Candidates Scanner Thread ────
LIVE_RADAR_SIGNALS = []
TOP_10_PUMP_CANDIDATES = []

def _analyze_candidate(sym: str):
    """Worker function for concurrent candidate analysis."""
    try:
        res = analyze_symbol(sym, interval="1m")
        if res.get("error"):
            return None, None

        sc = res.get("scorecard", {})
        vd = res.get("verdict", {})
        tier = res.get("tier", {})
        vol_r = sc.get("vol_ratio", 0)
        action = vd.get("action", "NEUTRAL")

        # Calculate Pump Potential Score
        ps = calculate_pump_score(res)
        score_val = ps["score"]

        item = {
            "symbol": sym,
            "price": res.get("price", 0),
            "pct_24h": res.get("pct_24h", 0),
            "tier": tier,
            "pump_score": score_val,
            "stage_tag": ps["stage_tag"],
            "stage_class": ps["stage_class"],
            "vol_ratio": vol_r,
            "buy_ratio": sc.get("buy_ratio", 50),
            "rsi": sc.get("rsi", 50),
            "price_change_5m": sc.get("price_change_5m", 0),
            "green_candles": sc.get("green_candles", 1),
            "action": action,
            "confidence": vd.get("confidence", 50),
            "breakdown": ps["breakdown"],
            "updated_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        }

        signal = None
        if action in ["PUMP_LONG", "DUMP_SHORT", "OVERSOLD_REBOUND"] or vol_r >= 3.0:
            signal = {
                "symbol": sym,
                "price": res.get("price", 0),
                "pct_24h": res.get("pct_24h", 0),
                "action": action,
                "confidence": vd.get("confidence", 50),
                "vol_ratio": vol_r,
                "buy_ratio": sc.get("buy_ratio", 50),
                "rsi": sc.get("rsi", 50),
                "detected_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            }

        return item, signal
    except Exception:
        return None, None


def radar_scanner_loop():
    """Continuous high-speed background thread scanning 526 pairs in parallel."""
    import concurrent.futures
    logger.info("High-speed Radar & Top 10 background scanner thread started.")
    global LIVE_RADAR_SIGNALS, TOP_10_PUMP_CANDIDATES

    while True:
        try:
            tickers = client.futures_ticker()
            usdt_tickers = [
                t for t in tickers
                if t["symbol"].endswith("USDT")
                and float(t.get("quoteVolume", 0)) >= 500000.0
            ]

            # Top active movers for Stage 2 micro-analysis
            sorted_by_change = sorted(
                usdt_tickers,
                key=lambda x: abs(float(x.get("priceChangePercent", 0))),
                reverse=True
            )[:20]

            sorted_by_vol = sorted(
                usdt_tickers,
                key=lambda x: float(x.get("quoteVolume", 0)),
                reverse=True
            )[:15]

            # Combined candidate pool (up to 35 unique symbols)
            candidate_syms = list(set([t["symbol"] for t in sorted_by_change + sorted_by_vol]))

            all_scored = []
            signals = []

            # Parallel analysis using ThreadPoolExecutor for sub-second execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(_analyze_candidate, candidate_syms)
                for item, signal in results:
                    if item:
                        all_scored.append(item)
                    if signal:
                        signals.append(signal)

            # Update Top 10 Pump Candidates (Sorted by PumpScore descending)
            if all_scored:
                TOP_10_PUMP_CANDIDATES = sorted(all_scored, key=lambda x: x["pump_score"], reverse=True)[:10]

            if signals:
                LIVE_RADAR_SIGNALS = sorted(signals, key=lambda x: x["confidence"], reverse=True)[:10]

            time.sleep(3)
        except Exception as e:
            logger.debug(f"Radar/Top10 scanner error: {e}")
            time.sleep(4)


@app.route("/api/top_pump_candidates")
def api_top_pump_candidates():
    """Return real-time Top 10 High-Probability Pump Candidates ranked across 526 pairs."""
    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "total_analyzed": len(TOP_10_PUMP_CANDIDATES),
        "candidates": TOP_10_PUMP_CANDIDATES,
    })


if __name__ == "__main__":
    import threading
    radar_thread = threading.Thread(target=radar_scanner_loop, daemon=True)
    radar_thread.start()

    port = int(os.getenv("PORT", 5050))
    print(f"""
============================================================
  DEEPALPHA BINANCE FUTURES SCANNER & RADAR TERMINAL RUNNING!
  Truy cập giao diện Web tại: http://localhost:{port}
============================================================
    """)
    app.run(host="127.0.0.1", port=port, debug=False)
