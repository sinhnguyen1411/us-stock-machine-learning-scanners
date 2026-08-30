"""
Stateful Lifecycle Tracker & State Machine Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Comprehensive testing for:
1. Stage transitions (IGNITION -> ACTIVE_EXPANSION -> HIGH_CONSOLIDATION -> EXHAUSTION_WARNING -> DUMP_CONFIRMED)
2. Trailing stop and dump threshold calculations
3. Super-pump retention and ACE integration
4. Delisted coin handling and persistence
5. Campaign age tracking and multiplier metrics
"""

import os
import sys
import tempfile
import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage


@pytest.fixture
def temp_registry():
    """Provides an isolated registry instance pointing to a temporary file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name
    
    # Initialize registry with empty data
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump({"updated_at": "", "campaigns": {}}, f)
    
    reg = PumpLifecycleRegistry(file_path=temp_path)
    # Clear any auto-loaded seed campaigns to have a pristine test environment
    reg.campaigns = {}
    yield reg
    
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


class TestLifecycleStateMachineTransitions:
    """Test transitions across all 5 core pump stages."""

    def test_register_and_initial_ignition_stage(self, temp_registry):
        """Newly registered pump starts at IGNITION stage."""
        camp = temp_registry.register_new_pump(
            symbol="ALPHAUSDT",
            origin_bottom_price=0.01,
            current_price=0.012,
            expected_n_ml=10.0,
            expected_n_low=4.0,
            expected_n_high=25.0,
        )
        assert camp.symbol == "ALPHAUSDT"
        assert camp.stage == PumpStage.IGNITION
        assert camp.is_active is True
        assert camp.current_n == 1.2
        assert camp.max_n == 1.2

    def test_ignition_to_active_expansion(self, temp_registry):
        """Price increase making new high transitions stage to ACTIVE_EXPANSION."""
        temp_registry.register_new_pump(
            symbol="ALPHAUSDT",
            origin_bottom_price=0.01,
            current_price=0.01,
        )
        
        # Price explodes 3x higher -> creates new peak
        c = temp_registry.update_price_and_stage("ALPHAUSDT", 0.03)
        assert c.stage == PumpStage.ACTIVE_EXPANSION
        assert c.highest_peak_price == 0.03
        assert c.max_n == 3.0
        assert c.current_n == 3.0
        assert c.drawdown_from_peak_pct == 0.0
        assert c.is_active is True

    def test_active_expansion_to_high_consolidation(self, temp_registry):
        """Campaign older than 7 days holding near peak enters HIGH_CONSOLIDATION."""
        origin_date = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
        temp_registry.register_new_pump(
            symbol="AKEUSDT",
            origin_bottom_price=0.00017,
            current_price=0.015,
            origin_date=origin_date,
        )
        # Establish high peak at 0.0163
        temp_registry.update_price_and_stage("AKEUSDT", 0.0163)
        
        # Price consolidates slightly at 0.0145 (drawdown ~11% < 28%, age 14d >= 7d)
        c = temp_registry.update_price_and_stage("AKEUSDT", 0.0145)
        assert c.stage == PumpStage.HIGH_CONSOLIDATION
        assert c.is_active is True
        assert c.pump_age_days >= 7

    def test_high_consolidation_to_exhaustion_warning_by_drawdown(self, temp_registry):
        """Drawdown >= 28% triggers EXHAUSTION_WARNING."""
        temp_registry.register_new_pump(
            symbol="BETAUSDT",
            origin_bottom_price=1.0,
            current_price=5.0,
        )
        temp_registry.update_price_and_stage("BETAUSDT", 10.0) # peak = 10.0
        
        # Pullback to 7.0 (-30% drawdown >= 28%)
        c = temp_registry.update_price_and_stage("BETAUSDT", 7.0)
        assert c.stage == PumpStage.EXHAUSTION_WARNING
        assert c.drawdown_from_peak_pct == 30.0
        assert c.is_active is True

    def test_exhaustion_warning_by_positive_funding_flip(self, temp_registry):
        """Crowded longs (funding_rate >= +0.10%) trigger EXHAUSTION_WARNING."""
        temp_registry.register_new_pump(
            symbol="BETAUSDT",
            origin_bottom_price=1.0,
            current_price=5.0,
        )
        temp_registry.update_price_and_stage("BETAUSDT", 10.0)
        
        # Price slightly down -15%, but extreme funding +0.15%
        c = temp_registry.update_price_and_stage("BETAUSDT", 8.5, funding_rate=0.0015)
        assert c.stage == PumpStage.EXHAUSTION_WARNING

    def test_exhaustion_to_dump_confirmed_by_drawdown(self, temp_registry):
        """Drawdown >= 45% confirms structural breakdown into DUMP_CONFIRMED."""
        temp_registry.register_new_pump(
            symbol="GAMMALUSDT",
            origin_bottom_price=1.0,
            current_price=10.0,
        )
        temp_registry.update_price_and_stage("GAMMALUSDT", 10.0)
        
        # Crash to 5.0 (-50% drawdown >= 45%)
        c = temp_registry.update_price_and_stage("GAMMALUSDT", 5.0)
        assert c.stage == PumpStage.DUMP_CONFIRMED
        assert c.is_active is False
        assert c.dump_date is not None
        assert "ĐÃ XÁC NHẬN DUMP" in c.notes

    def test_dump_confirmed_by_price_below_dump_threshold(self, temp_registry):
        """Price dropping below dump_threshold_price (< 55% of peak) confirms DUMP."""
        temp_registry.register_new_pump(
            symbol="DELTAUSDT",
            origin_bottom_price=0.5,
            current_price=2.0,
        )
        temp_registry.update_price_and_stage("DELTAUSDT", 10.0)
        # Peak = 10.0, dump threshold = 5.5
        c = temp_registry.update_price_and_stage("DELTAUSDT", 5.4)
        assert c.stage == PumpStage.DUMP_CONFIRMED
        assert c.is_active is False

    def test_no_retrograde_from_dump_confirmed(self, temp_registry):
        """Once DUMP_CONFIRMED, subsequent dead-cat bounces do NOT reactivate the campaign."""
        temp_registry.register_new_pump(
            symbol="DEADPUMPUSDT",
            origin_bottom_price=1.0,
            current_price=10.0,
        )
        temp_registry.update_price_and_stage("DEADPUMPUSDT", 10.0)
        temp_registry.update_price_and_stage("DEADPUMPUSDT", 4.0) # Dumped!
        
        # Dead cat bounce back to 7.0
        c = temp_registry.update_price_and_stage("DEADPUMPUSDT", 7.0)
        assert c.stage == PumpStage.DUMP_CONFIRMED
        assert c.is_active is False

    def test_delisted_coin_permanently_inactive(self, temp_registry):
        """Known delisted symbols are automatically locked into DELISTED."""
        temp_registry.register_new_pump(
            symbol="UNFIUSDT",  # in _KNOWN_DELISTED
            origin_bottom_price=0.01,
            current_price=0.05,
        )
        c = temp_registry.update_price_and_stage("UNFIUSDT", 0.08)
        assert c.stage == PumpStage.DELISTED
        assert c.is_active is False


class TestCalculationsAndProperties:
    """Test dynamic metrics, trailing stops, and ACE super-pump detection."""

    def test_trailing_stop_recalculation(self, temp_registry):
        """Trailing stop is strictly 70% of highest peak price."""
        temp_registry.register_new_pump("TESTUSDT", 1.0, 1.0)
        temp_registry.update_price_and_stage("TESTUSDT", 10.0)
        c = temp_registry.get_campaign("TESTUSDT")
        assert c.trailing_stop_price == pytest.approx(7.0, rel=1e-5)
        
        # Higher peak -> stop rises
        temp_registry.update_price_and_stage("TESTUSDT", 20.0)
        c = temp_registry.get_campaign("TESTUSDT")
        assert c.trailing_stop_price == pytest.approx(14.0, rel=1e-5)

    def test_dump_threshold_calculation(self, temp_registry):
        """Dump threshold price is strictly 55% of highest peak price."""
        temp_registry.register_new_pump("TESTUSDT", 1.0, 1.0)
        temp_registry.update_price_and_stage("TESTUSDT", 10.0)
        c = temp_registry.get_campaign("TESTUSDT")
        assert c.dump_threshold_price == pytest.approx(5.5, rel=1e-5)

    def test_super_pump_in_progress_flagging(self, temp_registry):
        """Reaching >= 95% of expected ML multiplier sets is_super_pump_in_progress."""
        temp_registry.register_new_pump(
            symbol="SUPERUSDT",
            origin_bottom_price=1.0,
            current_price=1.0,
            expected_n_ml=10.0, # threshold = 9.5x
        )
        c = temp_registry.update_price_and_stage("SUPERUSDT", 9.6)
        assert c.is_super_pump_in_progress is True
        assert c.super_pump_detected_at is not None

    def test_get_active_and_dumped_campaigns(self, temp_registry):
        """Registry correctly partitions active vs dumped campaigns."""
        temp_registry.register_new_pump("RUNNING1USDT", 1.0, 3.0)
        temp_registry.register_new_pump("RUNNING2USDT", 1.0, 4.0)
        temp_registry.register_new_pump("DUMPED1USDT", 1.0, 10.0)
        temp_registry.update_price_and_stage("DUMPED1USDT", 4.0) # dump
        
        active = temp_registry.get_active_campaigns()
        dumped = temp_registry.get_dumped_campaigns()
        
        assert len(active) == 2
        assert len(dumped) == 1
        assert active[0].symbol in ("RUNNING1USDT", "RUNNING2USDT")
        assert dumped[0].symbol == "DUMPED1USDT"
