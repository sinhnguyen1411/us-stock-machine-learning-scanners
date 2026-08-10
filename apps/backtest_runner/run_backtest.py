"""
DeepAlpha Standalone Batch Backtest Runner
"""

import sys
import argparse
from pathlib import Path

# Add packages directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from risk_management import CascadeBacktestEngine
from exchange_connectors import BinanceFuturesConnector


def main():
    parser = argparse.ArgumentParser(description="Run historical backtest simulation on Binance Futures")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading pair symbol (default: BTCUSDT)")
    parser.add_argument("--days", type=int, default=7, help="Historical lookback days (default: 7)")
    parser.add_argument("--balance", type=float, default=1000.0, help="Initial balance (default: 1000.0)")
    args = parser.parse_args()

    connector = BinanceFuturesConnector()
    engine = CascadeBacktestEngine(client=connector.client)

    print(f"Running Cascade TP Backtest for {args.symbol} over past {args.days} days...")
    res = engine.run_backtest(symbol=args.symbol, days=args.days, initial_balance=args.balance)

    if "error" in res:
        print(f"Error: {res['error']}")
        return

    print("=" * 60)
    print(f"  BACKTEST RESULTS FOR {res['symbol']} ({res['days']} DAYS)")
    print("=" * 60)
    print(f"  Initial Balance  : ${res['initial_balance']:,.2f}")
    print(f"  Final Balance    : ${res['final_balance']:,.2f}")
    print(f"  Net Profit       : ${res['net_profit']:+,.2f} ({res['return_pct']:+.2f}%)")
    print(f"  Win Rate         : {res['win_rate']}% ({res['winning_trades']} wins / {res['losing_trades']} losses)")
    print(f"  Profit Factor    : {res['profit_factor']}")
    print(f"  Max Drawdown     : {res['max_drawdown_pct']}%")
    print(f"  Total Trades     : {res['total_trades']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
