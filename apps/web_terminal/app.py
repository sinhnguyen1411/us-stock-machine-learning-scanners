"""
DeepAlpha Binance Futures Web Terminal Application
"""

import os
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# Add packages directory to sys.path for monorepo imports
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from core_engine import (
    classify_asset_tier,
    evaluate_confirmation_layers,
    calculate_pump_score,
    calculate_pre_pump_index,
    is_stablecoin,
    is_stock_or_etf,
    is_excluded_asset,
    get_tradfi_stock_info,
    get_us_market_session,
    SECTOR_LABELS,
    TRADFI_STOCK_DIRECTORY,
    evaluate_tradfi_ml_metrics,
)
from exchange_connectors import BinanceFuturesConnector

from risk_management import calculate_trade_plan, CascadeBacktestEngine, CircuitBreakerManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WebTerminal")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True
app.json.ensure_ascii = False          # Flask 3.x: output Vietnamese & emoji as-is in JSON


connector = BinanceFuturesConnector()
circuit_mgr = CircuitBreakerManager()

PAPER_PORTFOLIO = {
    "equity": 1000.0,
    "active_positions": {},
    "trade_history": [],
}

LIVE_RADAR_SIGNALS = []
TOP_10_PUMP_CANDIDATES = []
PRE_PUMP_RADAR_ITEMS = []
TRADFI_STOCKS_CACHE = []
TRADFI_ML_SIGNALS = []


def analyze_symbol(symbol: str, interval: str = "1m") -> dict:
    """Analyze a single symbol through the core confirmation engine."""
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym += "USDT"

    if is_excluded_asset(sym):
        return {"error": f"{sym} là stablecoin / cổ phiếu / ETF và đã bị loại trừ khỏi hệ thống"}

    try:
        klines = connector.get_klines(symbol=sym, interval=interval, limit=60)


        if not klines or len(klines) < 25:
            return {"error": f"Không đủ dữ liệu nến cho {sym}"}

        ticker_24h = connector.get_24h_ticker(symbol=sym)
        price_now = float(ticker_24h.get("lastPrice", klines[-1][4]))
        pct_24h = float(ticker_24h.get("priceChangePercent", 0))
        high_24h = float(ticker_24h.get("highPrice", 0))
        low_24h = float(ticker_24h.get("lowPrice", 0))
        quote_vol_24h = float(ticker_24h.get("quoteVolume", 0))

        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        taker_buys = [float(k[9]) for k in klines]

        funding_rate = connector.get_funding_rate(sym)
        open_interest = connector.get_open_interest(sym)

        # Asset classification & dynamic thresholds
        tier = classify_asset_tier(sym, quote_vol_24h=quote_vol_24h, pct_24h=pct_24h)

        # Confirmation evaluation
        eval_result = evaluate_confirmation_layers(
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            taker_buy_volumes=taker_buys,
            open_interest=open_interest,
            funding_rate=funding_rate,
            req_vol_spike=tier.req_vol_spike,
            req_price_spike=tier.req_price_spike,
            req_buy_ratio=tier.req_buy_ratio,
        )

        scorecard = eval_result["scorecard"]
        verdict = eval_result["verdict"]

        trade_plan = calculate_trade_plan(
            current_price=price_now,
            atr=scorecard["atr"],
            tp1_mult=tier.tp1_mult,
            tp2_mult=tier.tp2_mult,
            tp3_mult=tier.tp3_mult,
        )

        candles_data = [
            {
                "time": k[0] // 1000,
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
            for k in klines
        ]

        return {
            "symbol": sym,
            "interval": interval,
            "price": price_now,
            "pct_24h": pct_24h,
            "high_24h": high_24h,
            "low_24h": low_24h,
            "quote_vol_24h": quote_vol_24h,
            "tier": tier.to_dict(),
            "scorecard": scorecard,
            "verdict": verdict,
            "trade_plan": trade_plan.to_dict(),
            "candles": candles_data,
        }
    except Exception as e:
        logger.error(f"Error analyzing {sym}: {e}", exc_info=True)
        return {"error": str(e)}


def analyze_tradfi_symbol(symbol: str, interval: str = "5m") -> dict:
    """Analyze a single US Stock / TradFi Futures contract with ML features."""
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym += "USDT"

    try:
        klines = connector.get_klines(symbol=sym, interval=interval, limit=60)
        if not klines or len(klines) < 5:
            return {"error": f"Không đủ dữ liệu nến cho mã TradFi {sym}"}

        ticker_24h = connector.get_24h_ticker(symbol=sym)
        price_now = float(ticker_24h.get("lastPrice", klines[-1][4]))
        pct_24h = float(ticker_24h.get("priceChangePercent", 0))
        high_24h = float(ticker_24h.get("highPrice", 0))
        low_24h = float(ticker_24h.get("lowPrice", 0))
        quote_vol_24h = float(ticker_24h.get("quoteVolume", 0))

        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        taker_buys = [float(k[9]) for k in klines]

        funding_rate = connector.get_funding_rate(sym)
        open_interest = connector.get_open_interest(sym)

        eval_result = evaluate_tradfi_ml_metrics(
            symbol=sym,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            taker_buy_volumes=taker_buys,
            price_now=price_now,
            pct_24h=pct_24h,
            quote_vol_24h=quote_vol_24h,
            open_interest=open_interest,
            funding_rate=funding_rate,
        )

        candles_data = [
            {
                "time": k[0] // 1000,
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
            for k in klines
        ]
        eval_result["candles"] = candles_data
        eval_result["interval"] = interval
        eval_result["high_24h"] = high_24h
        eval_result["low_24h"] = low_24h
        return eval_result
    except Exception as e:
        logger.error(f"Error analyzing TradFi stock {sym}: {e}", exc_info=True)
        return {"error": str(e)}


@app.route("/")
def index():
    return render_template("index.html", active_page="terminal")


@app.route("/top")
def page_top():
    return render_template("top.html", active_page="top")


@app.route("/pre-pump")
@app.route("/pre_pump")
def page_pre_pump():
    return render_template("pre_pump.html", active_page="pre_pump")


@app.route("/stocks")
@app.route("/tradfi")
def page_stocks():
    return render_template("stocks.html", active_page="stocks")


@app.route("/stock/<symbol>")
@app.route("/stocks/<symbol>")
def page_stock_detail(symbol):
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    stock_info = get_tradfi_stock_info(sym)
    session_info = get_us_market_session()
    ticker = stock_info.ticker if stock_info else sym.replace("USDT", "")
    return render_template(
        "stock_detail.html",
        symbol=sym,
        ticker=ticker,
        stock_info=stock_info,
        session_info=session_info,
        active_page="stocks",
    )


@app.route("/slides")
@app.route("/presentation")
def page_presentation():
    return render_template("presentation.html", active_page="presentation")


@app.route("/api/download/pptx")
def api_download_pptx():
    from flask import send_file
    pptx_path = ROOT_DIR / "final_project_us_stock_30_slides.pptx"
    if os.path.exists(pptx_path):
        return send_file(
            pptx_path,
            as_attachment=True,
            download_name="US_Stock_ML_Scanners_Final_Project_30_Slides.pptx"
        )
    return jsonify({"error": "Presentation file not found"}), 404


@app.route("/api/tradfi/sectors")
def api_tradfi_sectors():
    return jsonify({
        "sectors": SECTOR_LABELS,
        "session": get_us_market_session(),
        "total_directory": len(TRADFI_STOCK_DIRECTORY),
    })


@app.route("/api/tradfi/stocks")
def api_tradfi_stocks():
    sector_filter = request.args.get("sector", "ALL").upper()
    search = request.args.get("search", "").strip().upper()
    sort_by = request.args.get("sortBy", "ml_score")
    sort_order = request.args.get("sortOrder", "desc")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 50))

    items = TRADFI_STOCKS_CACHE[:]
    if sector_filter != "ALL":
        items = [x for x in items if x.get("sector") == sector_filter]

    if search:
        items = [
            x for x in items 
            if search in x.get("symbol", "") or search in x.get("ticker", "") or search in x.get("name", "").upper()
        ]

    # Sort
    reverse = (sort_order == "desc")
    if sort_by in ["ml_score", "pct_24h", "quote_vol_24h", "vol_spike", "taker_buy_ratio", "price", "vwap_distance_pct"]:
        items = sorted(items, key=lambda x: float(x.get(sort_by, 0)), reverse=reverse)

    total_items = len(items)
    start_idx = (page - 1) * page_size
    paged_data = items[start_idx:start_idx + page_size]

    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "session": get_us_market_session(),
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total_items + page_size - 1) // page_size),
        "data": paged_data,
    })


@app.route("/api/tradfi/analyze/<symbol>")
def api_tradfi_analyze(symbol):
    interval = request.args.get("interval", "5m")
    data = analyze_tradfi_symbol(symbol, interval=interval)
    if "error" in data:
        return jsonify({
            "error": {
                "code": "TRADFI_ANALYSIS_ERROR",
                "message": data["error"]
            }
        }), 400
    return jsonify(data)


@app.route("/api/tradfi/ml_signals")
def api_tradfi_ml_signals():
    min_confidence = float(request.args.get("minConfidence", 70.0))
    signals = [s for s in TRADFI_ML_SIGNALS if s.get("confidence", 0) >= min_confidence]
    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "count": len(signals),
        "signals": signals[:15],
    })


@app.route("/api/pre_pump_radar")
def api_pre_pump_radar():
    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "total_analyzed": len(PRE_PUMP_RADAR_ITEMS),
        "candidates": PRE_PUMP_RADAR_ITEMS,
    })


@app.route("/api/ml/pump_multiplier_research")
def api_pump_multiplier_research():
    try:
        from core_engine.pump_multiplier_classifier import PumpDatasetBuilder, PRICE_TIERS
        from core_engine.pump_multiplier_regressor import PumpMultiplierRegressor
        
        db = PumpDatasetBuilder()
        events = db.load_all()
        from core_engine.pump_multiplier_regressor import get_pump_multiplier_regressor
        reg = get_pump_multiplier_regressor()
        summary = reg.get_model_summary()
        
        events_data = [
            {
                "symbol": e.symbol,
                "event_date": e.event_date,
                "pre_pump_price": e.pre_pump_price,
                "peak_price": e.peak_price,
                "n_actual": e.n_actual,
                "tier_code": e.price_tier_code,
                "tier_index": e.price_tier_index,
                "vol_spike_ratio": e.vol_spike_ratio,
                "pre_pump_mcap_usd": e.pre_pump_mcap_usd,
                "pre_pump_vol_24h": e.pre_pump_vol_24h,
                "pump_duration_h": e.pump_duration_h,
                "notes": e.notes,
            }
            for e in sorted(events, key=lambda x: x.pre_pump_price)
        ]
        
        tiers_info = [t.to_dict() for t in PRICE_TIERS]
        
        return jsonify({
            "status": "success",
            "events_count": len(events_data),
            "model_summary": summary,
            "events": events_data,
            "tiers": tiers_info,
        })
    except Exception as ex:
        logger.error(f"Error in api_pump_multiplier_research: {ex}")
        return jsonify({"status": "error", "message": str(ex)}), 500


@app.route("/api/ml/active_pump_campaigns")
def api_active_pump_campaigns():
    try:
        from core_engine import get_pump_registry
        registry = get_pump_registry()
        active = registry.get_active_campaigns()
        all_c = registry.get_all_campaigns()
        return jsonify({
            "status": "success",
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "active_count": len(active),
            "active_campaigns": [c.to_dict() for c in active],
            "all_campaigns": [c.to_dict() for c in all_c],
        })
    except Exception as ex:
        logger.error(f"Error in api_active_pump_campaigns: {ex}")
        return jsonify({"status": "error", "message": str(ex)}), 500


@app.route("/api/analyze/<symbol>")
def api_analyze(symbol):

    interval = request.args.get("interval", "1m")
    data = analyze_symbol(symbol, interval=interval)
    if "error" in data:
        return jsonify(data), 400
    return jsonify(data)


@app.route("/api/top_movers")
def api_top_movers():
    try:
        usdt_tickers = connector.get_all_usdt_tickers(min_quote_volume=1_000_000.0)
        sorted_tickers = sorted(
            usdt_tickers,
            key=lambda x: float(x.get("priceChangePercent", 0)),
            reverse=True
        )

        gainers = [
            {
                "symbol": t["symbol"],
                "price": float(t.get("lastPrice", 0)),
                "pct_change": float(t.get("priceChangePercent", 0)),
                "volume": float(t.get("quoteVolume", 0)),
            }
            for t in sorted_tickers[:10]
        ]

        losers = [
            {
                "symbol": t["symbol"],
                "price": float(t.get("lastPrice", 0)),
                "pct_change": float(t.get("priceChangePercent", 0)),
                "volume": float(t.get("quoteVolume", 0)),
            }
            for t in sorted_tickers[-10:]
        ]

        return jsonify({"top_gainers": gainers, "top_losers": losers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/top_pump_candidates")
def api_top_pump_candidates():
    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "total_analyzed": len(TOP_10_PUMP_CANDIDATES),
        "candidates": TOP_10_PUMP_CANDIDATES,
    })


@app.route("/api/live_signals")
def api_live_signals():
    return jsonify({
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "count": len(LIVE_RADAR_SIGNALS),
        "signals": LIVE_RADAR_SIGNALS,
    })


@app.route("/api/portfolio")
def api_portfolio():
    for sym, pos in PAPER_PORTFOLIO["active_positions"].items():
        try:
            ticker = connector.get_24h_ticker(symbol=sym)
            curr = float(ticker.get("lastPrice", pos["entry"]))
            pos["current_price"] = curr
            if pos["side"] == "LONG":
                pos["unrealized_pnl"] = (curr - pos["entry"]) * pos["quantity"]
                pos["pnl_pct"] = (curr / pos["entry"] - 1.0) * 100.0 * pos["leverage"]
            else:
                pos["unrealized_pnl"] = (pos["entry"] - curr) * pos["quantity"]
                pos["pnl_pct"] = (1.0 - curr / pos["entry"]) * 100.0 * pos["leverage"]
        except Exception:
            pass

    return jsonify({
        "equity": PAPER_PORTFOLIO["equity"],
        "active_positions": list(PAPER_PORTFOLIO["active_positions"].values()),
        "trade_history": PAPER_PORTFOLIO["trade_history"],
    })


@app.route("/api/trade", methods=["POST"])
def api_trade():
    data = request.json or {}
    symbol = data.get("symbol", "").upper()
    side = data.get("side", "LONG").upper()
    notional = float(data.get("notional", 100.0))
    leverage = int(data.get("leverage", 5))

    if not symbol:
        return jsonify({"error": "Symbol là bắt buộc"}), 400

    if symbol in PAPER_PORTFOLIO["active_positions"]:
        return jsonify({"error": f"Đã có vị thế đang mở cho {symbol}"}), 400

    try:
        ticker = connector.get_24h_ticker(symbol=symbol)
        price = float(ticker.get("lastPrice", 0))
    except Exception as e:
        return jsonify({"error": f"Không thể lấy giá {symbol}: {e}"}), 400

    quantity = (notional * leverage) / price
    pos = {
        "symbol": symbol,
        "side": side,
        "entry": price,
        "current_price": price,
        "quantity": quantity,
        "notional": notional,
        "leverage": leverage,
        "unrealized_pnl": 0.0,
        "pnl_pct": 0.0,
        "opened_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
    }
    PAPER_PORTFOLIO["active_positions"][symbol] = pos

    return jsonify({"success": True, "message": f"Đã mở vị thế {side} cho {symbol} @ ${price:,.4f}", "position": pos})


@app.route("/api/close_trade", methods=["POST"])
def api_close_trade():
    data = request.json or {}
    symbol = data.get("symbol", "").upper()

    if symbol not in PAPER_PORTFOLIO["active_positions"]:
        return jsonify({"error": "Không tìm thấy vị thế để đóng"}), 404

    pos = PAPER_PORTFOLIO["active_positions"].pop(symbol)
    try:
        ticker = connector.get_24h_ticker(symbol=symbol)
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
    circuit_mgr.register_exit(symbol, pnl)

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

    return jsonify({"success": True, "message": f"Đã đóng vị thế {symbol}. PnL: ${pnl:+.2f} ({pnl_pct:+.1f}%)", "record": record})


@app.route("/api/backtest", methods=["POST"])
def api_backtest():
    try:
        data = request.json or {}
        symbol = data.get("symbol", "BTCUSDT")
        days = int(data.get("days", 7))
        initial_balance = float(data.get("initial_balance", 1000.0))

        engine = CascadeBacktestEngine(client=connector.client)
        result = engine.run_backtest(
            symbol=symbol,
            days=days,
            initial_balance=initial_balance
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Backtest error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def _analyze_candidate(sym: str):
    """Worker function for concurrent candidate analysis."""
    if is_excluded_asset(sym):
        return None, None
    try:
        res = analyze_symbol(sym, interval="1m")
        if res.get("error"):
            return None, None


        sc = res.get("scorecard", {})
        vd = res.get("verdict", {})
        tier = res.get("tier", {})
        vol_r = sc.get("vol_ratio", 0)
        action = vd.get("action", "NEUTRAL")

        ps = calculate_pump_score(sc, tier)
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


def _analyze_pre_pump_symbol(item_tuple):
    """Worker function to analyze 1H microstructure & 4 pillars for pre-pump candidate."""
    p, t_info = item_tuple
    sym = p.get("symbol", "")
    if is_excluded_asset(sym):
        return None

    fr = float(p.get("lastFundingRate", 0))
    mark_p = float(p.get("markPrice", 0))
    next_ft = p.get("nextFundingTime")
    pct_24h = float(t_info.get("priceChangePercent", 0)) if t_info else 0.0
    quote_vol = float(t_info.get("quoteVolume", 0)) if t_info else 0.0


    try:
        klines_1h = connector.get_klines(sym, interval="1h", limit=25)
        if klines_1h and len(klines_1h) >= 10:
            open_times = [int(k[0]) for k in klines_1h]
            opens = [float(k[1]) for k in klines_1h]
            highs = [float(k[2]) for k in klines_1h]
            lows = [float(k[3]) for k in klines_1h]
            closes = [float(k[4]) for k in klines_1h]
            volumes = [float(k[5]) for k in klines_1h]
            taker_buys = [float(k[9]) for k in klines_1h]

            # 1. 24h Average 1H Range (Compression)
            ranges = [(h - l) / max(l, 1e-9) * 100.0 for h, l in zip(highs[:-1], lows[:-1])]
            range_1h_avg = sum(ranges) / len(ranges) if ranges else 5.0

            # 2. Closed candle (N-1) stats:
            closed_vol = volumes[-2]
            base_vols_closed = volumes[-22:-2] if len(volumes) >= 22 else volumes[:-2]
            base_mean_closed = sum(base_vols_closed) / len(base_vols_closed) if base_vols_closed else 1.0
            spike_closed = closed_vol / max(base_mean_closed, 1e-9)
            taker_buy_closed = (taker_buys[-2] / max(closed_vol, 1e-9)) * 100.0
            candle_chg_closed = ((closes[-2] - opens[-2]) / max(opens[-2], 1e-9)) * 100.0

            # 3. Current running candle (N) stats (projected by elapsed minutes):
            curr_vol = volumes[-1]
            base_vols_curr = volumes[-21:-1] if len(volumes) >= 21 else volumes[:-1]
            base_mean_curr = sum(base_vols_curr) / len(base_vols_curr) if base_vols_curr else 1.0
            now_ms = int(time.time() * 1000)
            mins_elapsed = max(2.0, min(60.0, (now_ms - open_times[-1]) / 60000.0))
            projected_curr_vol = curr_vol * (60.0 / mins_elapsed)
            spike_curr = projected_curr_vol / max(base_mean_curr, 1e-9)
            taker_buy_curr = (taker_buys[-1] / max(curr_vol, 1e-9)) * 100.0
            candle_chg_curr = ((closes[-1] - opens[-1]) / max(opens[-1], 1e-9)) * 100.0

            # Continuous representation: preserve confirmed ignition from recently closed candle
            if spike_closed >= spike_curr or mins_elapsed < 15.0:
                vol_spike_1h = max(spike_closed, spike_curr)
                taker_buy_1h = taker_buy_closed if spike_closed >= spike_curr else taker_buy_curr
                candle_1h_pct = candle_chg_closed if spike_closed >= spike_curr else candle_chg_curr
            else:
                vol_spike_1h = spike_curr
                taker_buy_1h = taker_buy_curr
                candle_1h_pct = candle_chg_curr

            atr = (highs[-1] - lows[-1])

        else:
            range_1h_avg = 5.0
            vol_spike_1h = 1.0
            taker_buy_1h = 50.0
            candle_1h_pct = 0.0
            atr = 0.0
    except Exception as ex:
        logger.error(f"Error in _analyze_pre_pump_symbol for {sym}: {ex}")
        range_1h_avg = 5.0
        vol_spike_1h = 1.0
        taker_buy_1h = 50.0
        candle_1h_pct = 0.0
        atr = 0.0


    macro_cycle_pos = 50.0
    drift_1d_pct = 0.0
    higher_low_quality = 1.0
    adr_contraction = 1.0
    pct_3d = pct_24h
    pct_7d = pct_24h
    gain_from_base_pct = 0.0

    try:
        klines_1d = connector.get_klines(sym, interval="1d", limit=45)
        if klines_1d and len(klines_1d) >= 5:
            d_closes = [float(k[4]) for k in klines_1d]
            d_highs  = [float(k[2]) for k in klines_1d]
            d_lows   = [float(k[3]) for k in klines_1d]

            # Macro Cycle Position (price position within 45-day range)
            h_max = max(d_highs)
            l_min = min(d_lows)
            macro_cycle_pos = (mark_p - l_min) / max(h_max - l_min, 1e-9) * 100.0

            # Wyckoff Signal 1: 14-day drift direction
            # 0~+12% = sideways-to-up = Wyckoff Base pattern
            if len(d_closes) >= 15:
                drift_start = d_closes[-15]
                drift_1d_pct = (d_closes[-1] - drift_start) / max(drift_start, 1e-9) * 100.0

            # Wyckoff Signal 2: Higher Low Structure
            # Recent low = min of last 3 daily bars
            # Prev low = min of daily bars from 7-14 days ago
            recent_lows = [float(k[3]) for k in klines_1d[-4:-1]] if len(klines_1d) >= 4 else []
            prev_lows   = [float(k[3]) for k in klines_1d[-14:-7]] if len(klines_1d) >= 14 else []
            if recent_lows and prev_lows:
                recent_low_val = min(recent_lows)
                prev_low_val   = min(prev_lows)
                higher_low_quality = recent_low_val / max(prev_low_val, 1e-9)

            # Wyckoff Signal 3: ADR Contraction
            # Recent ADR (7d) vs Historical ADR (8-21 days ago) — compressing = nén đáy
            ranges_7d   = [(float(k[2]) - float(k[3])) / max(float(k[3]), 1e-9) * 100.0
                           for k in klines_1d[-8:-1]] if len(klines_1d) >= 8 else []
            ranges_prev = [(float(k[2]) - float(k[3])) / max(float(k[3]), 1e-9) * 100.0
                           for k in klines_1d[-22:-8]] if len(klines_1d) >= 22 else []
            if ranges_7d and ranges_prev:
                adr_7d   = sum(ranges_7d)   / len(ranges_7d)
                adr_prev = sum(ranges_prev) / len(ranges_prev)
                adr_contraction = adr_7d / max(adr_prev, 0.001)

            # Multi-day pump wave metrics (eliminates 24h rollover blindspot during consolidation pauses)
            if len(d_closes) >= 4:
                pct_3d = (mark_p - d_closes[-4]) / max(d_closes[-4], 1e-9) * 100.0
            else:
                pct_3d = pct_24h

            if len(d_closes) >= 8:
                pct_7d = (mark_p - d_closes[-8]) / max(d_closes[-8], 1e-9) * 100.0
            else:
                pct_7d = pct_3d

            # Lowest low of last 7-14 days as base floor
            recent_base_low = min(d_lows[-7:]) if len(d_lows) >= 7 else min(d_lows)
            gain_from_base_pct = (mark_p - recent_base_low) / max(recent_base_low, 1e-9) * 100.0

    except Exception:
        macro_cycle_pos    = 50.0
        drift_1d_pct       = 0.0
        higher_low_quality = 1.0
        adr_contraction    = 1.0
        pct_3d             = pct_24h
        pct_7d             = pct_24h
        gain_from_base_pct = 0.0

    # Sync with stateful pump lifecycle registry
    try:
        from core_engine import get_pump_registry
        get_pump_registry().update_price_and_stage(sym, mark_p, fr, quote_vol)
    except Exception:
        pass

    return calculate_pre_pump_index(
        symbol=sym,
        current_price=mark_p,
        funding_rate=fr,
        open_interest=0.0,
        quote_vol_24h=quote_vol,
        pct_24h=pct_24h,
        range_1h_avg=range_1h_avg,
        vol_spike_1h=vol_spike_1h,
        taker_buy_1h=taker_buy_1h,
        depth_ratio=1.0,
        next_funding_time=next_ft,
        atr=atr,
        candle_1h_pct=candle_1h_pct,
        macro_cycle_pos=macro_cycle_pos,
        drift_1d_pct=drift_1d_pct,
        higher_low_quality=higher_low_quality,
        adr_contraction=adr_contraction,
        pct_3d=pct_3d,
        pct_7d=pct_7d,
        gain_from_base_pct=gain_from_base_pct,
    )





def _analyze_tradfi_worker(ticker_item):
    """Worker to analyze one TradFi ticker with 5m klines."""
    sym = ticker_item.get("symbol", "")
    if not sym:
        return None, None
    try:
        klines = connector.get_klines(sym, interval="5m", limit=30)
        if not klines or len(klines) < 5:
            return None, None

        price_now = float(ticker_item.get("lastPrice", klines[-1][4]))
        pct_24h = float(ticker_item.get("priceChangePercent", 0))
        quote_vol_24h = float(ticker_item.get("quoteVolume", 0))

        opens = [float(k[1]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        taker_buys = [float(k[9]) for k in klines]

        res = evaluate_tradfi_ml_metrics(
            symbol=sym,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            taker_buy_volumes=taker_buys,
            price_now=price_now,
            pct_24h=pct_24h,
            quote_vol_24h=quote_vol_24h,
        )

        signal = None
        if res.get("signal") in ["STRONG_BUY_BREAKOUT", "INSTITUTIONAL_ACCUMULATION", "MOMENTUM_SURGE"]:
            signal = {
                "symbol": sym,
                "ticker": res.get("ticker"),
                "name": res.get("name"),
                "sector": res.get("sector"),
                "sector_name": res.get("sector_name"),
                "price": price_now,
                "pct_24h": pct_24h,
                "ml_score": res.get("ml_score"),
                "signal": res.get("signal"),
                "signal_tag": res.get("signal_tag"),
                "confidence": res.get("confidence"),
                "vol_spike": res.get("vol_spike"),
                "taker_buy_ratio": res.get("taker_buy_ratio"),
                "vwap_distance_pct": res.get("vwap_distance_pct"),
                "detected_at": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            }

        return res, signal
    except Exception:
        return None, None


def radar_scanner_loop():
    """Continuous high-speed background thread scanning pairs, top candidates, and pre-pump anomalies."""
    import concurrent.futures
    logger.info("High-speed Radar, Top 10, Pre-Pump & TradFi background scanner thread started.")
    global LIVE_RADAR_SIGNALS, TOP_10_PUMP_CANDIDATES, PRE_PUMP_RADAR_ITEMS, TRADFI_STOCKS_CACHE, TRADFI_ML_SIGNALS

    loop_count = 0

    while True:
        try:
            # 1. Fetch 24h tickers
            usdt_tickers = connector.get_all_usdt_tickers(min_quote_volume=300000.0)
            ticker_map = {t["symbol"]: t for t in usdt_tickers}

            # 2. Pre-Pump Anomaly Scanner (Multi-Bucket Selection across Negative Funding, Movers & Volume)
            try:
                premium_indices = connector.get_all_premium_index()
                premium_map = {p["symbol"]: p for p in premium_indices if p.get("symbol")}

                target_syms = set()

                # Bucket A: Top 70 Negative Funding (Short Trap candidates)
                neg_fundings = sorted(
                    [p for p in premium_indices if float(p.get("lastFundingRate", 0)) < 0 and not is_excluded_asset(p.get("symbol", "")) and p.get("symbol") not in ("BTCUSDT", "ETHUSDT")],
                    key=lambda x: float(x.get("lastFundingRate", 0))
                )[:70]
                for p in neg_fundings:
                    target_syms.add(p["symbol"])

                # Bucket B: Top 60 Volatility & Movers (Ignition & Breakouts like MAV, OGN)
                gainers_movers = sorted(
                    [t for t in usdt_tickers if not is_excluded_asset(t["symbol"]) and t["symbol"] not in ("BTCUSDT", "ETHUSDT")],
                    key=lambda x: abs(float(x.get("priceChangePercent", 0))),
                    reverse=True
                )[:60]
                for t in gainers_movers:
                    target_syms.add(t["symbol"])

                # Bucket C: Top 40 Volume Leaders (Whale flow)
                vol_movers = sorted(
                    [t for t in usdt_tickers if not is_excluded_asset(t["symbol"]) and t["symbol"] not in ("BTCUSDT", "ETHUSDT")],
                    key=lambda x: float(x.get("quoteVolume", 0)),
                    reverse=True
                )[:40]
                for t in vol_movers:
                    target_syms.add(t["symbol"])

                scan_targets = [
                    (premium_map.get(s, {"symbol": s, "lastFundingRate": 0.0, "markPrice": 0.0}), ticker_map.get(s, {}))
                    for s in target_syms
                ]

                if scan_targets:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pre_exec:
                        raw_list = list(pre_exec.map(_analyze_pre_pump_symbol, scan_targets))
                        pre_pump_list = [item for item in raw_list if item is not None and not is_excluded_asset(item.get("symbol", ""))]
                        if pre_pump_list:
                            PRE_PUMP_RADAR_ITEMS = sorted(pre_pump_list, key=lambda x: x["pre_pump_score"], reverse=True)[:50]

            except Exception as ex:
                logger.debug(f"Pre-pump scan error: {ex}")

            # 3. Top 10 Candidates & Live Radar Signals
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

            candidate_syms = list(set([t["symbol"] for t in sorted_by_change + sorted_by_vol]))

            all_scored = []
            signals = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(_analyze_candidate, candidate_syms)
                for item, signal in results:
                    if item:
                        all_scored.append(item)
                    if signal:
                        signals.append(signal)

            if all_scored:
                TOP_10_PUMP_CANDIDATES = sorted(all_scored, key=lambda x: x["pump_score"], reverse=True)[:15]

            if signals:
                LIVE_RADAR_SIGNALS = sorted(signals, key=lambda x: x["confidence"], reverse=True)[:10]

            # 4. TradFi US Stock Derivatives & ML Scanner
            try:
                tradfi_tickers = connector.get_all_tradfi_stock_tickers()
                if tradfi_tickers:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as tf_exec:
                        tf_results = list(tf_exec.map(_analyze_tradfi_worker, tradfi_tickers))
                        tf_stocks = []
                        tf_signals = []
                        for item, sig in tf_results:
                            if item:
                                tf_stocks.append(item)
                            if sig:
                                tf_signals.append(sig)

                        if tf_stocks:
                            TRADFI_STOCKS_CACHE = sorted(tf_stocks, key=lambda x: x["ml_score"], reverse=True)
                        if tf_signals:
                            TRADFI_ML_SIGNALS = sorted(tf_signals, key=lambda x: x["confidence"], reverse=True)
            except Exception as ex:
                logger.debug(f"TradFi scan loop error: {ex}")

            time.sleep(3.0)

        except Exception as e:
            logger.error(f"Error in radar scan loop: {e}")
            time.sleep(5.0)


if __name__ == "__main__":
    import threading
    radar_thread = threading.Thread(target=radar_scanner_loop, daemon=True)
    radar_thread.start()

    port = int(os.getenv("PORT", 5050))
    print(f"""
============================================================
  DEEPALPHA BINANCE FUTURES MONOREPO WEB TERMINAL RUNNING!
  Access Web UI at: http://localhost:{port}
============================================================
    """)
    app.run(host="127.0.0.1", port=port, debug=False)
