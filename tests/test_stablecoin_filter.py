import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from core_engine.classifier import is_stablecoin, is_stock_or_etf, is_excluded_asset, EXCLUDED_STABLECOINS, EXCLUDED_STOCKS_AND_ETFS


class TestStablecoinAndStockFilter(unittest.TestCase):
    def test_known_stablecoins(self):
        stables = [
            "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "BUSDUSDT", "USDPUSDT",
            "EURUSDT", "DAIUSDT", "AEURUSDT", "USDEUSDT", "PYUSDUSDT",
            "USTCUSDT", "STABLEUSDT", "STBLUSDT", "FRAXUSDT", "LUSDUSDT",
            "PAXGUSDT", "XAUTUSDT", "WBETHUSDT"
        ]
        for s in stables:
            self.assertTrue(is_stablecoin(s), f"{s} should be identified as a stablecoin/pegged asset")
            self.assertTrue(is_excluded_asset(s), f"{s} should be excluded by is_excluded_asset")

    def test_known_stocks_and_etfs(self):
        stocks = [
            "FWDIUSDT", "TQQQUSDT", "SPCXUSDT", "SAMSUNGUSDT", "AAPLUSDT",
            "MSFTUSDT", "GOOGLUSDT", "NVDAUSDT", "TSLAUSDT", "BRKBUSDT",
            "COSTUSDT", "DELLUSDT", "INTCUSDT", "SOXLUSDT", "SPYUSDT",
            "TENCENTUSDT", "HYUNDAIUSDT", "CSOPSAMSUNG2LUSDT"
        ]
        for s in stocks:
            self.assertTrue(is_stock_or_etf(s), f"{s} should be identified as a stock/ETF")
            self.assertTrue(is_excluded_asset(s), f"{s} should be excluded by is_excluded_asset")

    def test_crypto_symbols_not_excluded(self):
        crypto_coins = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "MAVUSDT", "KAITOUSDT",
            "STORJUSDT", "1000BONKUSDT", "RVNUSDT", "OGNUSDT", "TUTUSDT",
            "DOGEUSDT", "NEARUSDT", "SUIUSDT", "APTUSDT", "1INCHUSDT"
        ]
        for s in crypto_coins:
            self.assertFalse(is_excluded_asset(s), f"{s} should NOT be excluded")


if __name__ == "__main__":
    unittest.main()

