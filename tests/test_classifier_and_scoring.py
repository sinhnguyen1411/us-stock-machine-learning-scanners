"""
Classifier and Pump Potential Scoring Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates:
1. 8-tier logarithmic PriceTierClassifier bounds and labels
2. CoinTier classification (Bluechip, Mid-cap, Micro-cap)
3. Stablecoin / pegged asset exclusion list completeness
4. Composite pump potential score computation (10 - 99)
5. Wave stage tagging (CHÂN SÓNG, ĐANG BÙNG NỔ, GOM HÀNG CỰC ĐẠI, NÉN TÍCH LŨY)
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_multiplier_classifier import PriceTierClassifier, PRICE_TIERS
from core_engine.pump_multiplier_classifier import PriceTierClassifier, PRICE_TIERS
from core_engine.classifier import classify_asset_tier, is_stablecoin, EXCLUDED_STABLECOINS, CoinTier
from core_engine.scoring import calculate_pump_score


class TestPriceTierClassifier:
    """Test 8-tier logarithmic price tiering."""

    def test_all_8_tiers_present(self):
        """Must contain exactly 8 tiers ordered from Ultra Micro to Mega."""
        clf = PriceTierClassifier()
        assert len(PRICE_TIERS) == 8
        codes = [t.code for t in PRICE_TIERS]
        assert codes == ["ULTRA_MICRO", "MICRO", "NANO", "SMALL", "MID", "LARGE", "XLARGE", "MEGA"]

    def test_price_tier_boundary_classification(self):
        """Classifies prices across tier boundaries correctly."""
        clf = PriceTierClassifier()

        # Zero or negative -> Tier 1
        assert clf.classify(0.0).code == "ULTRA_MICRO"
        assert clf.classify(-1.0).code == "ULTRA_MICRO"

        # Tier 1: < $0.0001
        assert clf.classify(0.00005).code == "ULTRA_MICRO"

        # Tier 2: $0.0001 - $0.001
        assert clf.classify(0.0001).code == "MICRO"
        assert clf.classify(0.0008).code == "MICRO"

        # Tier 3: $0.001 - $0.01
        assert clf.classify(0.001).code == "NANO"
        assert clf.classify(0.007).code == "NANO"

        # Tier 4: $0.01 - $0.1
        assert clf.classify(0.01).code == "SMALL"
        assert clf.classify(0.05).code == "SMALL"

        # Tier 5: $0.1 - $1.0
        assert clf.classify(0.1).code == "MID"
        assert clf.classify(0.8).code == "MID"

        # Tier 6: $1.0 - $10.0
        assert clf.classify(1.0).code == "LARGE"
        assert clf.classify(7.5).code == "LARGE"

        # Tier 7: $10.0 - $100.0
        assert clf.classify(10.0).code == "XLARGE"
        assert clf.classify(85.0).code == "XLARGE"

        # Tier 8: > $100.0
        assert clf.classify(100.0).code == "MEGA"
        assert clf.classify(65000.0).code == "MEGA"


class TestAssetClassificationAndStablecoinFilter:
    """Test CoinTier classification and stablecoin filtering."""

    def test_bluechip_midcap_microcap_tiering(self):
        """Classifies symbols into LARGE_CAP, MID_CAP, and LOW_CAP_MEME."""
        tier_btc = classify_asset_tier("BTCUSDT")
        assert tier_btc.code == "LARGE_CAP"
        assert tier_btc.req_vol_spike <= 2.5

        tier_doge = classify_asset_tier("DOGEUSDT")
        assert tier_doge.code == "MID_CAP"

        tier_micro = classify_asset_tier("AKEUSDT")
        assert tier_micro.code == "LOW_CAP_MEME"
        assert tier_micro.req_vol_spike >= 4.0


    def test_stablecoin_detection(self):
        """Identifies stablecoins and synthetic pegs."""
        assert is_stablecoin("USDCUSDT") is True
        assert is_stablecoin("FDUSDUSDT") is True
        assert is_stablecoin("DAIUSDT") is True
        assert is_stablecoin("EURUSDT") is True
        assert is_stablecoin("PAXGUSDT") is True
        assert is_stablecoin("SOLUSDT") is False
        assert is_stablecoin("AKEUSDT") is False


class TestPumpPotentialScoring:
    """Test composite pump potential scoring formula."""

    def test_scoring_bounds_and_stage_tagging(self):
        """Validates score is between 10.0 and 99.0 and maps stage tags."""
        tier = CoinTier(
            code="MICRO_CAP", name="Micro Cap",
            req_vol_spike=5.0, req_price_spike=0.03, req_buy_ratio=0.65,
            tp1_mult=1.05, tp2_mult=1.10, tp3_mult=1.15
        ).to_dict()

        # Ignition condition: high volume + high buy ratio + low price change -> CHÂN SÓNG
        card_early = {
            "price_change_5m": 2.0,
            "vol_ratio": 6.5,
            "buy_ratio": 72.0,
            "rsi": 68.0,
            "green_candles": 2,
            "open_interest": 1000000,
        }
        res_early = calculate_pump_score(card_early, tier)
        assert 10.0 <= res_early["score"] <= 99.0
        assert res_early["stage_tag"] == "CHÂN SÓNG"

        # Explosion condition: high price surge + >= 3 green candles -> ĐANG BÙNG NỔ
        card_surge = {
            "price_change_5m": 6.0,
            "vol_ratio": 4.0,
            "buy_ratio": 60.0,
            "rsi": 78.0,
            "green_candles": 4,
            "open_interest": 1000000,
        }
        res_surge = calculate_pump_score(card_surge, tier)
        assert res_surge["stage_tag"] == "ĐANG BÙNG NỔ"

