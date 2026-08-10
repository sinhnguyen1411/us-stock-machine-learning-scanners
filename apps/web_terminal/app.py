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

from core_engine import classify_asset_tier, evaluate_confirmation_layers, calculate_pump_score
from exchange_connectors import BinanceFuturesConnector
from risk_management import calculate_trade_plan, CascadeBacktestEngine, CircuitBreakerManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WebTerminal")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)

connector = BinanceFuturesConnector()
circuit_mgr = CircuitBreakerManager()

PAPER_PORTFOLIO = {
    "equity": 1000.0,
    "active_positions": {},
    "trade_history": [],
}

LIVE_RADAR_SIGNALS = []
TOP_10_PUMP_CANDIDATES = []


def analyze_symbol(symbol: str, interval: str = "1m") -> dict:
    """Analyze a single symbol through the core confirmation engine."""
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym += "USDT"

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


@app.route("/")
def index():
    return render_template("index.html")


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


def radar_scanner_loop():
    """Continuous high-speed background thread scanning 526 pairs in parallel."""
    import concurrent.futures
    logger.info("High-speed Radar & Top 10 background scanner thread started.")
    global LIVE_RADAR_SIGNALS, TOP_10_PUMP_CANDIDATES

    while True:
        try:
            usdt_tickers = connector.get_all_usdt_tickers(min_quote_volume=500000.0)

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
                TOP_10_PUMP_CANDIDATES = sorted(all_scored, key=lambda x: x["pump_score"], reverse=True)[:10]

            if signals:
                LIVE_RADAR_SIGNALS = sorted(signals, key=lambda x: x["confidence"], reverse=True)[:10]

            time.sleep(3)
        except Exception as e:
            logger.debug(f"Radar/Top10 scanner error: {e}")
            time.sleep(4)


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
