"""
Binance Futures (USDT-M) Historical Dataset Downloader
======================================================
Downloads historical candlestick data with native taker buy volume,
computes derivative features (RSI, ATR, Buy Ratio, Volume Ratio),
and generates pump/dump labels for Machine Learning / AI training.

Usage:
    python download_historical_data.py --symbol BTCUSDT --days 7 --interval 1m
    python download_historical_data.py --symbol ETHUSDT --start "1 Jan, 2024" --end "15 Jan, 2024" --interval 5m
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from binance.client import Client


def download_futures_data(
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    days: int = 7,
    start_str: str = None,
    end_str: str = None,
    output_dir: str = "data",
    label_pump: bool = True
) -> str:
    """Download historical klines and calculate ML features."""
    client = Client()
    os.makedirs(output_dir, exist_ok=True)

    if not start_str:
        start_str = f"{days} days ago UTC"

    print(f"[*] Downloading Binance Futures [{symbol}] {interval} klines from '{start_str}' to '{end_str or 'NOW'}'...")
    start_t = time.time()

    raw_klines = client.futures_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_str,
        end_str=end_str
    )

    if not raw_klines:
        print(f"[!] No data returned for {symbol}")
        return ""

    elapsed = time.time() - start_t
    print(f"[+] Downloaded {len(raw_klines):,} candles in {elapsed:.2f}s")

    # Define columns
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ]
    df = pd.DataFrame(raw_klines, columns=columns)

    # Cast numeric types
    numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # Convert timestamps
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    df.drop(columns=["ignore"], inplace=True)

    # ── Feature Engineering for AI / Prediction ──
    print("[*] Computing Technical & Order Flow Indicators...")

    # 1. Exact Taker Buy Ratio
    df["buy_ratio"] = df["taker_buy_base"] / df["volume"].replace(0, 1e-9)

    # 2. Volume Ratio (vs 20-period rolling mean)
    rolling_vol = df["volume"].rolling(window=20).mean().shift(1)
    df["volume_ratio"] = df["volume"] / rolling_vol.replace(0, 1e-9)

    # 3. 14-period RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    df["rsi_14"] = 100.0 - (100.0 / (1.0 + rs))

    # 4. 14-period ATR
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(window=14).mean()

    # 5. Price changes across multiple horizons
    df["pct_change_1"] = df["close"].pct_change(1)
    df["pct_change_5"] = df["close"].pct_change(5)
    df["pct_change_15"] = df["close"].pct_change(15)

    # 6. Upper wick ratio
    body = (df["close"] - df["open"]).abs()
    candle_range = df["high"] - df["low"]
    upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
    df["upper_wick_ratio"] = upper_wick / candle_range.replace(0, 1e-9)

    # 7. Pump Target Labeling (For ML training)
    if label_pump:
        # Future max return in next 10 candles
        future_high_10 = df["high"].shift(-10).rolling(10).max()
        future_return = (future_high_10 - df["close"]) / df["close"]
        # Label 1 if price moves >= +3% in next 10 candles, else 0
        df["is_pump_target"] = (future_return >= 0.03).astype(int)

    # Save to file
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_filename = f"{symbol}_{interval}_{len(df)}candles_{date_str}.csv"
    out_path = os.path.join(output_dir, out_filename)
    df.to_csv(out_path)

    print(f"[+] Saved clean dataset to: {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Download Binance Futures Historical Dataset")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Symbol to download (e.g. BTCUSDT, ETHUSDT)")
    parser.add_argument("--interval", type=str, default="1m", help="Candle interval: 1m, 5m, 15m, 1h, 4h, 1d")
    parser.add_argument("--days", type=int, default=7, help="Number of past days to download")
    parser.add_argument("--start", type=str, default=None, help="Start date (e.g. '1 Jan, 2024')")
    parser.add_argument("--end", type=str, default=None, help="End date (e.g. '15 Jan, 2024')")
    parser.add_argument("--output_dir", type=str, default="data", help="Output directory")

    args = parser.parse_args()
    download_futures_data(
        symbol=args.symbol.upper(),
        interval=args.interval,
        days=args.days,
        start_str=args.start,
        end_str=args.end,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
