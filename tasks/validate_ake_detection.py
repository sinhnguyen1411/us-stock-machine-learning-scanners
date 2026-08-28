# -*- coding: utf-8 -*-
"""
Validate corrected algorithm against user-confirmed AKE data:
  - True bottom: $0.0001729
  - True peak:   $0.0163
  - Expected n:  ~94.3x
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv; load_dotenv(os.path.join("..", ".env"))
from packages.exchange_connectors.binance_client import BinanceFuturesConnector
from tasks.fetch_pump_events_2026 import detect_true_pump

connector = BinanceFuturesConnector()
print("Fetching AKEUSDT daily klines (365 days)...")
klines = connector.client.futures_klines(symbol="AKEUSDT", interval="1d", limit=365)
print("Got {} candles.".format(len(klines)))

event = detect_true_pump("AKEUSDT", klines, year_filter="2026",
                          base_lookback=30, peak_forward=90, min_n=2.0)

if event:
    print()
    print("=== AKE DETECTION RESULT ===")
    print("  Bottom date   : {}".format(event.event_date))
    print("  True bottom   : ${:.10f}".format(event.pre_pump_price))
    print("  True peak     : ${:.10f}".format(event.peak_price))
    print("  n_actual      : {:.2f}x".format(event.n_actual))
    print("  Tier          : {}".format(event.price_tier_code))
    print("  Notes         : {}".format(event.notes))
    print()
    print("User-confirmed: bottom=$0.0001729, peak=$0.0163, n~94.3x")
    expected_n = 0.0163 / 0.0001729
    print("Expected n    : {:.2f}x".format(expected_n))
    err = abs(event.n_actual - expected_n) / expected_n * 100
    print("Deviation     : {:.1f}%".format(err))
    if err < 10:
        print("STATUS: PASS - algorithm matches user data")
    else:
        print("STATUS: FAIL - algorithm does not match, need further tuning")
else:
    print("ERROR: No pump detected for AKE. Algorithm needs adjustment.")
    # Show raw candle data near the expected bottom
    from datetime import datetime, timezone
    print("\nRaw daily candles for AKE (showing lows):")
    for k in klines[-60:]:
        d = datetime.fromtimestamp(int(k[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        if d.startswith("2026"):
            print("  {} | low={:.10f} | high={:.10f} | close={:.10f}".format(
                d, float(k[3]), float(k[2]), float(k[4])))
