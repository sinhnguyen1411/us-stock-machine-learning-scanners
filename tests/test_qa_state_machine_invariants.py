"""
QA Phase 2: State Machine Invariants & Lifecycle Integrity Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifies:
1. Monotonic peak invariant (ATH peak never regresses when price retraces).
2. Dump lock invariant (DUMP_CONFIRMED is an absorbing terminal state for that wave).
3. Dynamic floor escalation (dump threshold & trailing stop rise with new peaks).
4. Delisted token isolation (permanently excluded from active radar).
5. Exhaustion warning transitions (via drawdown and positive funding rate flip).
6. Multi-cycle coexistence and historical tracking order.
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage


@pytest.fixture
def clean_registry():
    """Create a temporary isolated registry file for clean state machine testing."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name
    reg = PumpLifecycleRegistry(file_path=temp_path)
    reg.campaigns.clear()
    yield reg
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


class TestStateMachineInvariants:
    """Validate core mathematical and state machine invariants."""

    def test_monotonic_peak_price_invariant(self, clean_registry):
        """highest_peak_price must never decrease when price retraces."""
        c = clean_registry.register_new_pump(
            symbol="TESTMONO",
            origin_bottom_price=1.0,
            current_price=10.0,
            origin_date="2026-08-01",
        )
        assert c.highest_peak_price == 10.0
        assert c.max_n == 10.0

        # Price drops from $10.0 -> $7.5 -> $6.0
        clean_registry.update_price_and_stage("TESTMONO", current_price=7.5)
        c = clean_registry.get_campaign("TESTMONO")
        assert c.highest_peak_price == 10.0, "Peak price must remain 10.0"
        assert c.max_n == 10.0
        assert c.current_n == 7.5
        assert c.drawdown_from_peak_pct == 25.0

        clean_registry.update_price_and_stage("TESTMONO", current_price=6.0)
        c = clean_registry.get_campaign("TESTMONO")
        assert c.highest_peak_price == 10.0
        assert c.max_n == 10.0

    def test_dump_confirmed_lock_cannot_be_reverted(self, clean_registry):
        """A confirmed dump cannot magically revert to ACTIVE_EXPANSION on temporary price bounce."""
        c = clean_registry.register_new_pump(
            symbol="TESTDUMP",
            origin_bottom_price=1.0,
            current_price=10.0,
            origin_date="2026-08-01",
        )
        # Price drops -50% to $5.0 (below dump threshold $5.50)
        clean_registry.update_price_and_stage("TESTDUMP", current_price=5.0)
        c = clean_registry.get_campaign("TESTDUMP")
        assert c.stage == PumpStage.DUMP_CONFIRMED
        assert c.is_active is False
        assert c.dump_date is not None

        # Price bounces to $9.0 in the same cycle
        clean_registry.update_price_and_stage("TESTDUMP", current_price=9.0)
        c = clean_registry.get_campaign("TESTDUMP")
        assert c.stage == PumpStage.DUMP_CONFIRMED, "Must remain DUMP_CONFIRMED"
        assert c.is_active is False

    def test_dynamic_threshold_escalation(self, clean_registry):
        """dump_threshold_price and trailing_stop_price must escalate with higher peaks."""
        c = clean_registry.register_new_pump(
            symbol="TESTESCALATE",
            origin_bottom_price=1.0,
            current_price=10.0,
            origin_date="2026-08-01",
        )
        assert c.dump_threshold_price == 5.50  # 10.0 * 0.55
        assert c.trailing_stop_price == 7.00   # 10.0 * 0.70

        # Push to new Peak: $20.0
        clean_registry.update_price_and_stage("TESTESCALATE", current_price=20.0)
        c = clean_registry.get_campaign("TESTESCALATE")
        assert c.highest_peak_price == 20.0
        assert c.dump_threshold_price == 11.00  # 20.0 * 0.55
        assert c.trailing_stop_price == 14.00   # 20.0 * 0.70

        # Push to new Peak: $50.0
        clean_registry.update_price_and_stage("TESTESCALATE", current_price=50.0)
        c = clean_registry.get_campaign("TESTESCALATE")
        assert c.highest_peak_price == 50.0
        assert c.dump_threshold_price == 27.50  # 50.0 * 0.55
        assert c.trailing_stop_price == 35.00   # 50.0 * 0.70

    def test_delisted_token_isolation(self, clean_registry):
        """Known delisted coins must be completely excluded from active lifecycle tracking."""
        for delisted_sym in ["LINAUSDT", "WAVESUSDT", "OMGUSDT", "REEFUSDT"]:
            c = clean_registry.register_new_pump(
                symbol=delisted_sym,
                origin_bottom_price=0.01,
                current_price=0.10,
                origin_date="2026-05-01",
            )
            assert c.stage == PumpStage.DELISTED
            assert c.is_active is False

        active_list = clean_registry.get_active_campaigns()
        for act in active_list:
            assert act.symbol not in ["LINAUSDT", "WAVESUSDT", "OMGUSDT", "REEFUSDT"]

    def test_exhaustion_warning_transitions(self, clean_registry):
        """Exhaustion warning is triggered by 28% drawdown or high positive funding."""
        # Case A: Drawdown >= 28%
        c = clean_registry.register_new_pump(
            symbol="TESTEXHAUST_DD",
            origin_bottom_price=1.0,
            current_price=10.0,
            origin_date="2026-08-01",
        )
        clean_registry.update_price_and_stage("TESTEXHAUST_DD", current_price=7.0)  # -30%
        c = clean_registry.get_campaign("TESTEXHAUST_DD")
        assert c.stage == PumpStage.EXHAUSTION_WARNING
        assert c.is_active is True

        # Case B: Positive funding flip (>= +0.10%)
        c2 = clean_registry.register_new_pump(
            symbol="TESTEXHAUST_FUND",
            origin_bottom_price=1.0,
            current_price=10.0,
            origin_date="2026-08-01",
        )
        clean_registry.update_price_and_stage("TESTEXHAUST_FUND", current_price=9.5, funding_rate=0.0015)
        c2 = clean_registry.get_campaign("TESTEXHAUST_FUND")
        assert c2.stage == PumpStage.EXHAUSTION_WARNING
        assert c2.is_active is True

    def test_multi_cycle_coexistence_and_history(self, clean_registry):
        """Registering Wave 2 cleanly archives Wave 1 and preserves history."""
        # Wave 1: Jan 2026
        clean_registry.register_new_pump(
            symbol="TRBUSDT",
            origin_bottom_price=10.0,
            current_price=80.0,
            origin_date="2026-01-10",
        )
        # Wave 1 dumps
        clean_registry.update_price_and_stage("TRBUSDT", current_price=35.0)

        # Wave 2: Aug 2026
        clean_registry.register_new_pump(
            symbol="TRBUSDT",
            origin_bottom_price=40.0,
            current_price=160.0,
            origin_date="2026-08-15",
        )

        # Active lookup returns Wave 2
        active_trb = clean_registry.get_campaign("TRBUSDT")
        assert active_trb.campaign_id == "TRBUSDT_2026-08-15"
        assert active_trb.origin_bottom_price == 40.0
        assert active_trb.is_active is True

        # Full history returns both waves (newest first)
        history = clean_registry.get_campaign_history("TRBUSDT")
        assert len(history) == 2
        assert history[0].campaign_id == "TRBUSDT_2026-08-15"
        assert history[1].campaign_id == "TRBUSDT_2026-01-10"

