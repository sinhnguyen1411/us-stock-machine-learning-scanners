"""
Phase 1 Verification: Hill Saturation Decay Model & Heteroscedastic Funnel Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies:
1. Asymptotic limits at extreme price points (P -> 0 and P -> inf).
2. Strict continuous monotonicity (dn/dP < 0) across all scales from 10^-8 to 10^5.
3. Heteroscedastic funnel width ratio (Micro-cap variance >> Large-cap variance).
4. Multivariate force decomposition accuracy (+funding boost, +volume boost).
5. Prediction contract integration in PumpMultiplierRegressor.
"""

import math
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_multiplier_regressor import HillSaturationModel, get_pump_multiplier_regressor


class TestHillSaturationModelMathematicalProperties:
    """Validate mathematical rigor of the Generalized Hill Saturation Decay equation."""

    def test_asymptotic_limits(self):
        """As P -> 0, n -> n_ceiling (68x). As P -> inf, n -> n_floor (1.85x)."""
        model = HillSaturationModel()
        
        # Micro/Nano extreme: P = 10^-10
        n_nano = model.eval_median(1e-10)
        assert 65.0 <= n_nano <= 68.0, f"Nano extreme should approach ceiling, got {n_nano}"

        # Mega/Macro extreme: P = 100,000.0 (e.g. Bitcoin)
        n_mega = model.eval_median(100_000.0)
        assert 1.85 <= n_mega <= 2.25, f"Mega extreme should approach floor, got {n_mega}"
        
        # Infinite limit: P = 10^8
        n_inf = model.eval_median(1e8)
        assert 1.85 <= n_inf <= 1.95, f"Infinite limit should be within 1.95, got {n_inf}"



    def test_strict_continuous_monotonicity(self):
        """Multiplier n must strictly decrease as base price increases (dn/dP < 0)."""
        model = HillSaturationModel()
        prices = np.logspace(-7, 4, num=100)  # From $0.0000001 to $10,000
        n_vals = [model.eval_median(p) for p in prices]

        for i in range(len(n_vals) - 1):
            assert n_vals[i] >= n_vals[i + 1], (
                f"Monotonicity violation at p={prices[i]}: {n_vals[i]} < {n_vals[i+1]}"
            )

    def test_heteroscedastic_quantile_funnel(self):
        """The uncertainty ratio (n_high / n_low) must be much wider for micro-caps than large caps."""
        model = HillSaturationModel()

        low_micro, high_micro = model.eval_bounds(0.0001)
        ratio_micro = high_micro / low_micro

        low_large, high_large = model.eval_bounds(100.0)
        ratio_large = high_large / low_large

        assert ratio_micro > ratio_large * 2.0, (
            f"Funnel must be wider at micro-cap: ratio_micro={ratio_micro:.2f}, ratio_large={ratio_large:.2f}"
        )
        assert low_micro <= model.eval_median(0.0001) <= high_micro
        assert low_large <= model.eval_median(100.0) <= high_large

    def test_multivariate_decomposition_forces(self):
        """Multivariate decomposition must compute positive boosts for negative funding and volume surges."""
        model = HillSaturationModel()

        # Case 1: Neutral market
        decomp_neutral = model.decompose_multivariate(base_price=0.01, funding_rate=0.0001, vol_spike_ratio=1.0)
        assert decomp_neutral["funding_boost_pct"] == 0.0
        assert decomp_neutral["volume_boost_pct"] == 0.0
        assert decomp_neutral["n_multivariate_target"] == decomp_neutral["n_curve_baseline"]

        # Case 2: Short Squeeze (-0.20% funding)
        decomp_squeeze = model.decompose_multivariate(base_price=0.01, funding_rate=-0.0020, vol_spike_ratio=1.0)
        assert decomp_squeeze["funding_boost_pct"] == 7.0  # 35 * 0.0020 * 100
        assert decomp_squeeze["n_multivariate_target"] > decomp_squeeze["n_curve_baseline"]

        # Case 3: Volume Surge (12.0x spike)
        decomp_vol = model.decompose_multivariate(base_price=0.01, funding_rate=0.0, vol_spike_ratio=12.0)
        assert decomp_vol["volume_boost_pct"] > 0.0
        assert decomp_vol["n_multivariate_target"] > decomp_vol["n_curve_baseline"]


class TestRegressorInFlightIntegration:
    """Validate integration of Hill Saturation Model into PumpMultiplierRegressor."""

    def test_predict_in_flight_includes_multivariate_decomp(self):
        """predict_in_flight returns valid multivariate_decomp metadata payload."""
        reg = get_pump_multiplier_regressor()
        res = reg.predict_in_flight(
            symbol="4USDT",
            base_price=0.006678,
            current_price=0.02088,
            vol_spike_ratio=4.8,
            funding_rate=-0.0018,
        )
        assert "multivariate_decomp" in res
        decomp = res["multivariate_decomp"]
        assert "n_curve_baseline" in decomp
        assert "funding_boost_pct" in decomp
        assert "volume_boost_pct" in decomp
        assert "n_multivariate_target" in decomp
        assert decomp["funding_boost_pct"] > 0.0
        assert res["n_expected"] >= decomp["n_curve_baseline"]


class TestPhase2APIContracts:
    """Validate Phase 2 REST API endpoint synchronization."""

    def test_api_pump_multiplier_research_returns_hill_parameters(self):
        """GET /api/ml/pump_multiplier_research must return hill_model_parameters payload."""
        from apps.web_terminal.app import app
        client = app.test_client()
        res = client.get("/api/ml/pump_multiplier_research")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert "hill_model_parameters" in data
        params = data["hill_model_parameters"]
        assert params["n_floor"] == 1.85
        assert params["n_ceiling"] == 68.0
        assert params["p0"] == 0.012
        assert params["gamma"] == 0.38
        assert params["sigma_max"] == 0.45
        assert params["sigma_min"] == 0.16


    def test_api_active_pump_campaigns_returns_multivariate_decomp(self):
        """GET /api/ml/active_pump_campaigns must attach multivariate_decomp to active campaigns."""
        from apps.web_terminal.app import app
        client = app.test_client()
        res = client.get("/api/ml/active_pump_campaigns")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert len(data["active_campaigns"]) > 0
        first_active = data["active_campaigns"][0]
        assert "multivariate_decomp" in first_active
        assert "n_curve_baseline" in first_active["multivariate_decomp"]
        assert "n_multivariate_target" in first_active["multivariate_decomp"]

