"""
Deep Machine Learning Multiplier Regressor Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Comprehensive mathematical and structural validation:
1. Power law inverse-price monotonicity (cheaper price -> higher n)
2. Confidence Interval (90% CI) ordering: n_low <= n_expected <= n_high
3. Micro-cap Bayesian squeeze multiplier on volume spikes
4. In-flight progress calculation and 4-tier stage recommendation
5. Negative funding rate squeeze boost
6. Theoretical tier ceiling caps
7. Dynamic event appending, deduplication, and retrain pipeline
"""

import math
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_multiplier_regressor import PumpMultiplierRegressor, get_pump_multiplier_regressor
from core_engine.pump_multiplier_classifier import PriceTierClassifier


@pytest.fixture(scope="module")
def regressor():
    """Provides a trained instance of PumpMultiplierRegressor."""
    reg = PumpMultiplierRegressor()
    return reg


class TestMLMathematicalMonotonicity:
    """Validate power-law physics: cheaper pre-pump asset -> larger capacity for nX."""

    def test_power_law_monotonicity_across_tiers(self, regressor):
        """Micro-cap tokens (<$0.001) must have strictly higher n_expected than Large-cap tokens (>$10)."""
        p_ultra_micro = 0.00005  # Tier 1
        p_nano        = 0.005    # Tier 3
        p_mid         = 0.50     # Tier 5
        p_xlarge      = 50.0     # Tier 7

        pred_ultra = regressor.predict(symbol="ULTRA", current_price=p_ultra_micro)
        pred_nano  = regressor.predict(symbol="NANO",  current_price=p_nano)
        pred_mid   = regressor.predict(symbol="MID",   current_price=p_mid)
        pred_xl    = regressor.predict(symbol="XL",    current_price=p_xlarge)

        assert pred_ultra.n_expected > pred_nano.n_expected, "Tier 1 n must exceed Tier 3"
        assert pred_nano.n_expected > pred_mid.n_expected, "Tier 3 n must exceed Tier 5"
        assert pred_mid.n_expected > pred_xl.n_expected, "Tier 5 n must exceed Tier 7"

    def test_90_ci_bounds_strictly_ordered(self, regressor):
        """For any price point from $0.00001 to $10,000, n_low <= n_expected <= n_high."""
        test_prices = [0.00003, 0.0005, 0.008, 0.05, 0.75, 4.5, 45.0, 350.0]
        
        for price in test_prices:
            pred = regressor.predict(symbol="CHECK", current_price=price)
            assert pred.n_low <= pred.n_expected, f"n_low ({pred.n_low}) > n_exp ({pred.n_expected}) at ${price}"
            assert pred.n_expected <= pred.n_high, f"n_exp ({pred.n_expected}) > n_high ({pred.n_high}) at ${price}"
            assert pred.expected_peak_low <= pred.expected_peak_price <= pred.expected_peak_high

    def test_theoretical_tier_cap_respected(self, regressor):
        """n_expected must not exceed tier.n_expected_high * 1.35."""
        clf = PriceTierClassifier()
        test_prices = [0.00008, 0.002, 0.03, 0.4, 3.0, 30.0]

        for p in test_prices:
            tier = clf.classify(p)
            pred = regressor.predict(symbol="CAP", current_price=p, vol_spike_ratio=50.0)
            max_allowed_cap = tier.n_expected_high * 1.35
            assert pred.n_expected <= max_allowed_cap + 0.01, f"Exceeded tier ceiling at ${p}"


class TestMicrocapAndFundingSqueeze:
    """Validate non-linear Bayesian squeeze adjustments."""

    def test_microcap_volume_spike_squeeze(self, regressor):
        """Volume spike >= 10x on low-tier tokens triggers dynamic squeeze boost."""
        pred_normal = regressor.predict(symbol="MICRO", current_price=0.0005, vol_spike_ratio=1.5)
        pred_spike  = regressor.predict(symbol="MICRO", current_price=0.0005, vol_spike_ratio=25.0)

        assert pred_spike.n_expected >= pred_normal.n_expected, "Volume spike must increase or maintain n"

    def test_in_flight_negative_funding_boost(self, regressor):
        """Heavy negative funding rate (<= -0.5%) expands upside target."""
        res_neutral = regressor.predict_in_flight(
            symbol="FUND", base_price=0.01, current_price=0.02, funding_rate=0.0001
        )
        res_squeeze = regressor.predict_in_flight(
            symbol="FUND", base_price=0.01, current_price=0.02, funding_rate=-0.0150 # -1.5%
        )

        assert res_squeeze["n_expected"] >= res_neutral["n_expected"], "Negative funding must trigger short squeeze boost"
        assert res_squeeze["target_peak_price"] >= res_neutral["target_peak_price"]


class TestInFlightStagesAndProgress:
    """Validate in-flight progress calculation and risk level mappings."""

    def test_stage_recommendations_and_progress(self, regressor):
        """Check all 4 lifecycle risk levels based on target completion percentage."""
        base = 1.0
        
        # Test progress < 45% -> PHA ĐẨY MẠNH (LOW_RISK)
        res_push = regressor.predict_in_flight(
            symbol="STG", base_price=base, current_price=base * 1.2
        )
        assert res_push["progress_pct"] < 45.0
        assert "PHA ĐẨY MẠNH" in res_push["stage_recommendation"]
        assert res_push["risk_level"] == "LOW_RISK"

        # Test progress 45% - 80% -> PHA TRƯỞNG THÀNH (MEDIUM_RISK)
        n_target = res_push["n_expected"]
        res_mature = regressor.predict_in_flight(
            symbol="STG", base_price=base, current_price=base * (n_target * 0.60)
        )
        assert 45.0 <= res_mature["progress_pct"] <= 80.0
        assert "PHA TRƯỞNG THÀNH" in res_mature["stage_recommendation"]
        assert res_mature["risk_level"] == "MEDIUM_RISK"

        # Test progress 80% - 105% -> TIỆM CẬN ĐỈNH ML (HIGH_RISK)
        res_peak = regressor.predict_in_flight(
            symbol="STG", base_price=base, current_price=base * (n_target * 0.95)
        )
        assert 80.0 <= res_peak["progress_pct"] <= 105.0
        assert "TIỆM CẬN ĐỈNH ML" in res_peak["stage_recommendation"]
        assert res_peak["risk_level"] == "HIGH_RISK"

        # Test progress > 105% -> VƯỢT MỤC TIÊU ML (CRITICAL_EXHAUSTION)
        res_over = regressor.predict_in_flight(
            symbol="STG", base_price=base, current_price=base * (n_target * 1.50)
        )
        assert res_over["progress_pct"] > 105.0
        assert "VƯỢT MỤC TIÊU ML" in res_over["stage_recommendation"]
        assert res_over["risk_level"] == "CRITICAL_EXHAUSTION"


class TestEventAppendingAndRetraining:
    """Validate dynamic dataset expansion and retraining."""

    def test_append_verified_event_and_deduplication(self, regressor):
        """Adding verified event adds to memory and ignores identical (symbol, date)."""
        initial_count = len(regressor.events)
        
        regressor.append_verified_event(
            symbol="TESTNEWPUMP",
            pre_pump_price=0.01,
            peak_price=0.35,
            n_actual=35.0,
            event_date="2026-08-01",
        )
        assert len(regressor.events) == initial_count + 1

        # Attempt to add duplicate
        regressor.append_verified_event(
            symbol="TESTNEWPUMP",
            pre_pump_price=0.01,
            peak_price=0.35,
            n_actual=35.0,
            event_date="2026-08-01",
        )
        assert len(regressor.events) == initial_count + 1, "Duplicate must be rejected"

    def test_model_summary_contract(self, regressor):
        """get_model_summary returns complete metadata schema."""
        summary = regressor.get_model_summary()
        assert summary["is_trained"] is True
        assert "Tri-Ensemble" in summary["architecture"]
        assert summary["5fold_mae"] > 0
        assert summary["geometric_factor_error"] >= 1.0
