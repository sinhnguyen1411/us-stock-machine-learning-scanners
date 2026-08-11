"""
DeepAlpha Binance Futures Autonomous CLI Scanner & Worker
"""

import sys
import time
import logging
from pathlib import Path

# Add packages directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from core_engine import classify_asset_tier, evaluate_confirmation_layers, calculate_pump_score, is_excluded_asset
from exchange_connectors import BinanceFuturesConnector
from risk_management import calculate_trade_plan, CircuitBreakerManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CLIScanner")


def run_scanner_loop():
    logger.info("Starting DeepAlpha Binance Futures Autonomous Scanner...")
    connector = BinanceFuturesConnector()
    circuit_mgr = CircuitBreakerManager()

    while True:
        try:
            if circuit_mgr.is_circuit_tripped():
                logger.warning("Circuit breaker active! Daily loss threshold reached. Pausing...")
                time.sleep(60)
                continue

            tickers = connector.get_all_usdt_tickers(min_quote_volume=1_000_000.0)
            logger.info(f"Scanning {len(tickers)} USDT-M perpetual contracts...")

            for t in tickers[:50]:
                sym = t["symbol"]
                if is_excluded_asset(sym) or circuit_mgr.is_symbol_in_cooldown(sym):
                    continue



                try:
                    klines = connector.get_klines(sym, interval="1m", limit=35)
                    if not klines or len(klines) < 25:
                        continue

                    opens = [float(k[1]) for k in klines]
                    highs = [float(k[2]) for k in klines]
                    lows = [float(k[3]) for k in klines]
                    closes = [float(k[4]) for k in klines]
                    volumes = [float(k[5]) for k in klines]
                    taker_buys = [float(k[9]) for k in klines]

                    tier = classify_asset_tier(sym, quote_vol_24h=float(t.get("quoteVolume", 0)))
                    eval_result = evaluate_confirmation_layers(
                        opens, highs, lows, closes, volumes, taker_buys,
                        req_vol_spike=tier.req_vol_spike,
                        req_price_spike=tier.req_price_spike,
                        req_buy_ratio=tier.req_buy_ratio,
                    )

                    verdict = eval_result["verdict"]
                    if verdict["action"] == "PUMP_LONG" and verdict["confidence"] >= 75:
                        sc = eval_result["scorecard"]
                        trade_plan = calculate_trade_plan(closes[-1], sc["atr"], tier.tp1_mult, tier.tp2_mult, tier.tp3_mult)
                        logger.info(f"🚀 [SIGNAL DETECTED] {sym} | Vol: {sc['vol_ratio']}x | Buy: {sc['buy_ratio']}% | Entry: ${trade_plan.entry} | SL: ${trade_plan.stop_loss} | TP1: ${trade_plan.tp1}")
                except Exception:
                    continue

            time.sleep(5)
        except Exception as e:
            logger.error(f"Scanner iteration error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_scanner_loop()
