"""
Multi-Cycle Pump & Dump Isolation and Lifecycle Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deep QA testing for multi-wave pump campaigns on the same symbol:
1. Dual identification via campaign_id = f"{symbol}_{origin_date}"
2. Zero data collision / overwrite between Wave 1 and Wave 2
3. Macro cycle segmentation from multi-month klines
4. Lookup precedence: get_campaign() returns active wave while history preserves all waves
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core_engine.pump_lifecycle_tracker import PumpLifecycleRegistry, PumpCampaign, PumpStage
from core_engine.autonomous_super_pump_scanner import AutonomousSuperPumpScanner
from core_engine.accuracy_correction_engine import AccuracyCorrectionEngine


class TestMultiCycleLifecycleCoexistence:
    """Validate that multiple waves of the same coin coexist without overwriting."""

    @pytest.fixture
    def temp_registry(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        reg = PumpLifecycleRegistry(file_path=tmp.name)
        reg.campaigns.clear()  # Start with empty state for clean multi-cycle testing
        yield reg
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    def test_multi_wave_campaign_coexistence(self, temp_registry):
        """Wave 1 dumped and Wave 2 active must coexist peacefully under unique campaign_ids."""
        reg = temp_registry

        # ── Step 1: Register Wave 1 (January 2026) ──
        w1 = reg.register_new_pump(
            symbol="TRBUSDT",
            origin_bottom_price=9.50,
            current_price=28.50,
            origin_date="2026-01-10",
            expected_n_ml=30.0,
            notes="Wave 1 Ignition from $9.50",
        )
        assert w1.campaign_id == "TRBUSDT_2026-01-10"
        assert w1.is_active is True

        # Wave 1 reaches peak $285.00 (30x)
        reg.update_price_and_stage("TRBUSDT_2026-01-10", current_price=285.00)
        assert w1.highest_peak_price == 285.00
        assert w1.max_n == 30.0

        # Wave 1 dumps to $140.00 (-50.9% from peak)
        reg.update_price_and_stage("TRBUSDT_2026-01-10", current_price=140.00)
        assert w1.stage == PumpStage.DUMP_CONFIRMED
        assert w1.is_active is False

        # ── Step 2: Register Wave 2 (May 2026) ──
        w2 = reg.register_new_pump(
            symbol="TRBUSDT",
            origin_bottom_price=45.00,
            current_price=90.00,
            origin_date="2026-05-15",
            expected_n_ml=4.0,
            notes="Wave 2 Ignition from new accumulation base $45.00",
        )
        assert w2.campaign_id == "TRBUSDT_2026-05-15"
        assert w2.is_active is True
        assert w2.origin_bottom_price == 45.00

        # ── Step 3: Assert Zero Overwrite & Dual Presence ──
        all_c = reg.get_all_campaigns()
        assert len(all_c) == 2, "Both waves must exist in registry"

        active_c = reg.get_active_campaigns()
        assert len(active_c) == 1
        assert active_c[0].campaign_id == "TRBUSDT_2026-05-15"
        assert active_c[0].current_n == 2.0  # $90 / $45

        dumped_c = reg.get_dumped_campaigns()
        assert len(dumped_c) == 1
        assert dumped_c[0].campaign_id == "TRBUSDT_2026-01-10"
        assert dumped_c[0].highest_peak_price == 285.00
        assert dumped_c[0].max_n == 30.0

        # ── Step 4: Lookup Precedence ──
        # Querying by symbol "TRBUSDT" returns the active Wave 2
        lookup_active = reg.get_campaign("TRBUSDT")
        assert lookup_active is not None
        assert lookup_active.campaign_id == "TRBUSDT_2026-05-15"

        # Querying by specific campaign_id returns Wave 1
        lookup_w1 = reg.get_campaign("TRBUSDT_2026-01-10")
        assert lookup_w1 is not None
        assert lookup_w1.stage == PumpStage.DUMP_CONFIRMED

        # History returns both waves sorted by origin_date descending
        history = reg.get_campaign_history("TRBUSDT")
        assert len(history) == 2
        assert history[0].campaign_id == "TRBUSDT_2026-05-15"
        assert history[1].campaign_id == "TRBUSDT_2026-01-10"

    def test_multi_wave_persistence(self, temp_registry):
        """Saving and reloading multi-cycle campaigns must preserve all campaign_ids and stages."""
        reg = temp_registry

        reg.register_new_pump("PEPEUSDT", 0.000001, 0.000005, origin_date="2026-02-01")
        reg.update_price_and_stage("PEPEUSDT_2026-02-01", 0.000010)
        reg.update_price_and_stage("PEPEUSDT_2026-02-01", 0.000004)  # Dump confirmed

        reg.register_new_pump("PEPEUSDT", 0.000003, 0.000008, origin_date="2026-06-01")

        # Reload into a new registry instance
        reloaded = PumpLifecycleRegistry(file_path=reg.file_path)
        assert len(reloaded.get_all_campaigns()) >= 2

        w1 = reloaded.get_campaign("PEPEUSDT_2026-02-01")
        w2 = reloaded.get_campaign("PEPEUSDT_2026-06-01")
        assert w1 is not None and w1.is_active is False
        assert w2 is not None and w2.is_active is True
        assert reloaded.get_campaign("PEPEUSDT").campaign_id == "PEPEUSDT_2026-06-01"


class TestMacroCycleSegmentation:
    """Validate algorithm that decomposes multi-month daily klines into distinct cycles."""

    def test_two_distinct_pump_cycles_segmented(self):
        """Synthetic 120-day klines with 2 pumps and dumps must be cleanly segmented."""
        # Construct synthetic klines: [timestamp, open, high, low, close, volume, ...]
        import time
        now_ms = int(time.time() * 1000)
        day_ms = 86400 * 1000

        klines = []
        # Cycle 1: Day 0 to 40 (Base $1.0 -> Peak $10.0 -> Dump to $4.0)
        for i in range(40):
            t = now_ms - (120 - i) * day_ms
            if i < 10:
                klines.append([t, "1.0", "1.1", "0.95", "1.0", "10000"])
            elif i < 20:
                p = 1.0 + (i - 10) * 0.9  # Rises to 10.0
                klines.append([t, str(p), str(p + 0.5), str(p - 0.2), str(p), "50000"])
            else:
                p = max(4.0, 10.0 - (i - 20) * 0.6)  # Dumps to 4.0 (-60%)
                klines.append([t, str(p), str(p + 0.2), str(p - 0.3), str(p), "30000"])

        # Consolidation between cycles: Day 40 to 70 (coiling around $4.0)
        for i in range(40, 70):
            t = now_ms - (120 - i) * day_ms
            klines.append([t, "4.0", "4.3", "3.9", "4.1", "12000"])

        # Cycle 2: Day 70 to 120 (Base $4.0 -> Peak $20.0 -> Current $18.0)
        for i in range(70, 120):
            t = now_ms - (120 - i) * day_ms
            if i < 100:
                p = 4.0 + (i - 70) * 0.53  # Rises to 20.0
                klines.append([t, str(p), str(p + 0.4), str(p - 0.2), str(p), "80000"])
            else:
                klines.append([t, "18.0", "19.0", "17.5", "18.0", "60000"])

        cycles = AutonomousSuperPumpScanner.segment_macro_cycles(klines, min_multiplier=2.5)
        assert len(cycles) == 2, f"Expected 2 segmented cycles, got {len(cycles)}"

        c1 = cycles[0]
        assert c1["is_completed_dump"] is True
        assert abs(c1["origin_bottom_price"] - 0.95) < 0.2
        assert abs(c1["highest_peak_price"] - 10.0) < 1.0

        c2 = cycles[1]
        assert c2["is_active"] is True
        assert abs(c2["origin_bottom_price"] - 3.9) < 0.5
        assert abs(c2["highest_peak_price"] - 20.0) < 1.0
        assert c2["current_price"] == 18.0


class TestACEWindowIsolation:
    """Validate ACE peak correction respects custom date range."""

    def test_verify_and_correct_accepts_end_date(self):
        """ACE peak verification accepts end_date to avoid bleeding across cycles."""
        ace = AccuracyCorrectionEngine()
        peak, corrected = ace.verify_and_correct_peak_before_finalize(
            symbol="BTRUSDT",
            origin_date="2026-07-18",
            origin_bottom_price=0.01587,
            stored_peak_price=0.17963,
            end_date="2026-08-28",
        )
        assert peak > 0.0
        assert isinstance(corrected, bool)
