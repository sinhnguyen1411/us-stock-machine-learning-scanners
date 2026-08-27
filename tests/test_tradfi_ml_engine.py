"""
Unit Tests for TradFi US Stock Machine Learning Engine & Sector Classification
"""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from core_engine import (
    TRADFI_STOCK_DIRECTORY,
    SECTOR_LABELS,
    get_tradfi_stock_info,
    get_us_market_session,
    calculate_vwap,
    calculate_realized_volatility,
    evaluate_tradfi_ml_metrics,
    is_stock_or_etf,
)


class TestTradFiMLEngine(unittest.TestCase):

    def test_tradfi_stock_directory_and_sectors(self):
        """Verify that key US stocks, semiconductor, ETF and AI pre-IPO tickers exist and map to valid sectors."""
        sample_tickers = [
            ("NVDAUSDT", "NVDA", "MEGA_TECH"),
            ("AAPLUSDT", "AAPL", "MEGA_TECH"),
            ("TSLAUSDT", "TSLA", "MEGA_TECH"),
            ("AMDUSDT", "AMD", "SEMICONDUCTORS"),
            ("SOXLUSDT", "SOXL", "SEMICONDUCTORS"),
            ("SPYUSDT", "SPY", "INDEX_AND_ETFS"),
            ("QQQUSDT", "QQQ", "INDEX_AND_ETFS"),
            ("TQQQUSDT", "TQQQ", "INDEX_AND_ETFS"),
            ("OPENAIUSDT", "OPENAI", "AI_AND_PRE_IPO"),
            ("ANTHROPICUSDT", "ANTHROPIC", "AI_AND_PRE_IPO"),
            ("BRKBUSDT", "BRK.B", "FINANCIALS"),
            ("WMTUSDT", "WMT", "CONSUMER_AND_HEALTHCARE"),
        ]
        for sym, exp_ticker, exp_sector in sample_tickers:
            info = get_tradfi_stock_info(sym)
            self.assertEqual(info.ticker, exp_ticker, f"Ticker mismatch for {sym}")
            self.assertEqual(info.sector, exp_sector, f"Sector mismatch for {sym}")
            self.assertTrue(is_stock_or_etf(sym), f"{sym} should be identified as stock/ETF")

    def test_us_market_session_calculator(self):
        """Test market session calculation for various UTC times."""
        # 14:00 UTC = 10:00 EST on a Wednesday (Weekday = 2) -> REGULAR_HOURS (Cash open)
        dt_regular = datetime(2026, 4, 15, 14, 0, 0, tzinfo=timezone.utc)
        res = get_us_market_session(dt_regular)
        self.assertEqual(res["session_code"], "REGULAR_HOURS")
        self.assertTrue(res["is_cash_open"])

        # 10:00 UTC = 06:00 EST on a Wednesday -> PRE_MARKET
        dt_pre = datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc)
        res_pre = get_us_market_session(dt_pre)
        self.assertEqual(res_pre["session_code"], "PRE_MARKET")
        self.assertFalse(res_pre["is_cash_open"])

        # 21:00 UTC = 17:00 EST on a Wednesday -> AFTER_HOURS
        dt_after = datetime(2026, 4, 15, 21, 0, 0, tzinfo=timezone.utc)
        res_after = get_us_market_session(dt_after)
        self.assertEqual(res_after["session_code"], "AFTER_HOURS")
        self.assertFalse(res_after["is_cash_open"])

        # Sunday (Weekday = 6) -> OVERNIGHT_24_7
        dt_weekend = datetime(2026, 4, 19, 15, 0, 0, tzinfo=timezone.utc)
        res_weekend = get_us_market_session(dt_weekend)
        self.assertEqual(res_weekend["session_code"], "OVERNIGHT_24_7")
        self.assertFalse(res_weekend["is_cash_open"])

    def test_calculate_vwap_and_volatility(self):
        """Test VWAP calculation and realized volatility."""
        highs = [102.0, 104.0, 105.0, 106.0]
        lows = [98.0, 99.0, 101.0, 103.0]
        closes = [100.0, 103.0, 104.0, 105.0]
        volumes = [1000.0, 2000.0, 1500.0, 3000.0]

        vwap = calculate_vwap(highs, lows, closes, volumes)
        self.assertGreater(vwap, 100.0)
        self.assertLess(vwap, 106.0)

        vol = calculate_realized_volatility(closes)
        self.assertGreaterEqual(vol, 5.0)

    def test_evaluate_tradfi_ml_metrics(self):
        """Test ML evaluation and anomaly score generation for NVDAUSDT."""
        n = 30
        opens = [120.0 + i * 0.5 for i in range(n)]
        highs = [o + 1.0 for o in opens]
        lows = [o - 0.5 for o in opens]
        closes = [o + 0.8 for o in opens]
        volumes = [1000.0] * (n - 1) + [5000.0]  # 5x volume spike on last candle
        taker_buys = [700.0] * (n - 1) + [4000.0]  # 80% buy ratio

        res = evaluate_tradfi_ml_metrics(
            symbol="NVDAUSDT",
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes,
            taker_buy_volumes=taker_buys,
            price_now=closes[-1],
            pct_24h=4.5,
            quote_vol_24h=50_000_000.0,
        )

        self.assertEqual(res["symbol"], "NVDAUSDT")
        self.assertEqual(res["ticker"], "NVDA")
        self.assertEqual(res["sector"], "MEGA_TECH")
        self.assertGreaterEqual(res["ml_score"], 70.0)
        self.assertEqual(res["signal"], "STRONG_BUY_BREAKOUT")
        self.assertIn("trade_plan", res)
        self.assertGreater(res["trade_plan"]["tp1"], res["price"])
        self.assertLess(res["trade_plan"]["sl"], res["price"])


if __name__ == "__main__":
    unittest.main()
