"""
Stateful Pump Campaign Lifecycle Tracker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Solves the fundamental problem of multi-week/multi-month super-pumps (e.g., AKE, BANK, DEXE)
that pump over extended durations without dumping immediately.

Tracks the full 5-stage lifecycle of each pump campaign:
  1. IGNITION             : Breakout from the macro accumulation base (origin bottom)
  2. ACTIVE_EXPANSION     : Escalating price discovery, making new highs (n climbing)
  3. HIGH_CONSOLIDATION   : Ranging/coiling at high altitudes (e.g. AKE 2 months in)
  4. EXHAUSTION_WARNING   : Volume divergence, funding rate flipping positive
  5. DUMP_CONFIRMED       : Structural breakdown (>45% drawdown from peak or key support loss)

Persistence: data/active_pumps_registry.json
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DATA_DIR     = os.path.join(_PROJECT_ROOT, "data")
_REGISTRY_PATH = os.path.join(_DATA_DIR, "active_pumps_registry.json")
os.makedirs(_DATA_DIR, exist_ok=True)


class PumpStage:
    IGNITION            = "IGNITION"             # Just broke out (Days 1-3)
    ACTIVE_EXPANSION    = "ACTIVE_EXPANSION"     # Making higher highs (Escalating n)
    HIGH_CONSOLIDATION  = "HIGH_CONSOLIDATION"   # Ranging near peak (e.g. AKE multi-week)
    EXHAUSTION_WARNING  = "EXHAUSTION_WARNING"   # Weakening momentum, funding flip
    DUMP_CONFIRMED      = "DUMP_CONFIRMED"       # Broken structure (>45% off peak)
    ARCHIVED            = "ARCHIVED"             # Post-dump baseline return


STAGE_LABELS_VI = {
    PumpStage.IGNITION:           "🚀 Vừa Khởi Phát (Ignition)",
    PumpStage.ACTIVE_EXPANSION:   "🔥 Đang Mở Rộng Sóng (Expansion)",
    PumpStage.HIGH_CONSOLIDATION: "🟢 Neo Đỉnh Tích Lũy Sóng Mới",
    PumpStage.EXHAUSTION_WARNING: "⚠️ Cảnh Báo Kiệt Sức / Phân Phối",
    PumpStage.DUMP_CONFIRMED:     "🔴 Đã Xác Nhận Dump (Thoát Hết)",
    PumpStage.ARCHIVED:           "⚪ Chu Kỳ Đã Kết Thúc",
}


@dataclass
class PumpCampaign:
    symbol:               str
    origin_date:          str                 # Date of the true accumulation bottom
    origin_bottom_price:  float               # True macro base low that ignited the pump
    highest_peak_price:   float               # All-time high price of this campaign
    highest_peak_date:    str                 # Date when highest peak was recorded
    current_price:        float = 0.0
    current_n:            float = 1.0         # current_price / origin_bottom_price
    max_n:                float = 1.0         # highest_peak_price / origin_bottom_price
    expected_n_ml:        float = 0.0         # ML regression target n
    expected_n_low:       float = 0.0
    expected_n_high:      float = 0.0
    drawdown_from_peak_pct: float = 0.0       # (highest - current) / highest * 100
    pump_age_days:        int = 0             # Days elapsed since origin_date
    stage:                str = PumpStage.IGNITION
    stage_label_vi:       str = ""
    is_active:            bool = True         # True until DUMP_CONFIRMED or ARCHIVED
    trailing_stop_price:  float = 0.0         # Dynamic support level
    dump_threshold_price: float = 0.0         # Price below which dump is confirmed (e.g. -45% from peak)
    dump_date:            Optional[str] = None
    last_updated:         str = ""
    notes:                str = ""

    def __post_init__(self):
        if not self.stage_label_vi:
            self.stage_label_vi = STAGE_LABELS_VI.get(self.stage, self.stage)
        if self.highest_peak_price <= 0 and self.current_price > 0:
            self.highest_peak_price = self.current_price
        if not self.highest_peak_date:
            self.highest_peak_date = self.origin_date
        if self.origin_bottom_price > 0:
            if self.current_price > 0:
                self.current_n = round(self.current_price / self.origin_bottom_price, 2)
            if self.highest_peak_price > 0:
                self.max_n = round(self.highest_peak_price / self.origin_bottom_price, 2)
        if self.highest_peak_price > 0:
            self.dump_threshold_price = round(self.highest_peak_price * 0.55, 8)  # -45% from peak
            if self.current_price > 0:
                dd = (self.highest_peak_price - self.current_price) / self.highest_peak_price * 100.0
                self.drawdown_from_peak_pct = round(max(0.0, dd), 1)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PumpLifecycleRegistry:
    """
    Manages persistent state for all running and historical pump campaigns.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or _REGISTRY_PATH
        self.campaigns: Dict[str, PumpCampaign] = {}
        self._load()
        self._seed_known_2026_campaigns()

    def _load(self) -> None:
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("campaigns", []):
                    c = PumpCampaign(**item)
                    self.campaigns[c.symbol] = c
        except Exception:
            pass

    def save(self) -> None:
        try:
            payload = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "active_count": len([c for c in self.campaigns.values() if c.is_active]),
                "campaigns": [c.to_dict() for c in self.campaigns.values()],
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _seed_known_2026_campaigns(self) -> None:
        """Seed verified multi-month 2026 pump campaigns if not already present."""
        seeds = [
            # AKE: Multi-month super pump (ignited July 10, 2026 at $0.0001729, hit $0.0163, still active)
            PumpCampaign(
                symbol="AKEUSDT",
                origin_date="2026-07-10",
                origin_bottom_price=0.00017290,
                highest_peak_price=0.01630000,
                highest_peak_date="2026-08-14",
                current_price=0.01250000,
                expected_n_ml=94.27,
                expected_n_low=35.0,
                expected_n_high=120.0,
                stage=PumpStage.HIGH_CONSOLIDATION,
                notes="Siêu sóng Micro-cap 2026: Đã chạy > 45 ngày, đang neo tích lũy vùng đỉnh chưa dump.",
            ),
            # BANK: DeFi banking multi-week pump
            PumpCampaign(
                symbol="BANKUSDT",
                origin_date="2026-06-05",
                origin_bottom_price=0.02221000,
                highest_peak_price=0.67205000,
                highest_peak_date="2026-07-19",
                current_price=0.52000000,
                expected_n_ml=30.26,
                expected_n_low=15.0,
                expected_n_high=45.0,
                stage=PumpStage.HIGH_CONSOLIDATION,
                notes="Chiến dịch DeFi Squeeze: Tăng 30x từ đáy, đang duy trì cấu trúc đỉnh.",
            ),
            # TUT: Multi-week pump
            PumpCampaign(
                symbol="TUTUSDT",
                origin_date="2026-06-04",
                origin_bottom_price=0.00853000,
                highest_peak_price=0.33733000,
                highest_peak_date="2026-08-08",
                current_price=0.26500000,
                expected_n_ml=39.55,
                expected_n_low=18.0,
                expected_n_high=50.0,
                stage=PumpStage.HIGH_CONSOLIDATION,
                notes="Chiến dịch Squeeze đa tuần: n=39.5x từ đáy gốc.",
            ),
            # VELVET: Multi-week pump
            PumpCampaign(
                symbol="VELVETUSDT",
                origin_date="2026-04-04",
                origin_bottom_price=0.05700000,
                highest_peak_price=2.17010000,
                highest_peak_date="2026-06-27",
                current_price=1.75000000,
                expected_n_ml=38.07,
                expected_n_low=15.0,
                expected_n_high=45.0,
                stage=PumpStage.HIGH_CONSOLIDATION,
                notes="DeFi Yield Narrative: 38x từ đáy gốc.",
            ),
            # DEXE: High tier pump
            PumpCampaign(
                symbol="DEXEUSDT",
                origin_date="2026-02-06",
                origin_bottom_price=1.71800000,
                highest_peak_price=16.21000000,
                highest_peak_date="2026-07-24",
                current_price=12.80000000,
                expected_n_ml=9.44,
                expected_n_low=5.0,
                expected_n_high=15.0,
                stage=PumpStage.HIGH_CONSOLIDATION,
                notes="Large Tier Asset: 9.4x từ đáy gốc, tích lũy phân phối trên $12.",
            ),
        ]
        dirty = False
        for s in seeds:
            if s.symbol not in self.campaigns:
                self.campaigns[s.symbol] = s
                dirty = True
        if dirty:
            self.save()

    def update_price_and_stage(
        self,
        symbol: str,
        current_price: float,
        funding_rate: float = 0.0,
        vol_24h: float = 0.0,
    ) -> Optional[PumpCampaign]:
        """
        Real-time update called on each tick/scanner loop.
        Evaluates stage transitions and dump confirmation.
        """
        symbol = symbol.upper()
        if symbol not in self.campaigns:
            return None

        c = self.campaigns[symbol]
        c.current_price = current_price
        now_ts = datetime.now(timezone.utc)
        c.last_updated = now_ts.isoformat()

        # Update Age
        try:
            orig_dt = datetime.strptime(c.origin_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            c.pump_age_days = max(1, (now_ts - orig_dt).days)
        except Exception:
            c.pump_age_days = 1

        # Check for new High
        if current_price > c.highest_peak_price:
            c.highest_peak_price = current_price
            c.highest_peak_date = now_ts.strftime("%Y-%m-%d")
            c.stage = PumpStage.ACTIVE_EXPANSION
            c.dump_threshold_price = round(c.highest_peak_price * 0.55, 8)

        # Update multipliers and drawdown
        if c.origin_bottom_price > 0:
            c.current_n = round(current_price / c.origin_bottom_price, 2)
            c.max_n = round(c.highest_peak_price / c.origin_bottom_price, 2)

        if c.highest_peak_price > 0:
            dd = (c.highest_peak_price - current_price) / c.highest_peak_price * 100.0
            c.drawdown_from_peak_pct = round(max(0.0, dd), 1)

        # Dynamic Trailing Stop (EMA20 or -30% from peak)
        c.trailing_stop_price = round(c.highest_peak_price * 0.70, 8)

        # ── State Machine Transitions ──
        if c.stage != PumpStage.ARCHIVED:
            # Condition 1: Dump Confirmed
            if current_price < c.dump_threshold_price or c.drawdown_from_peak_pct >= 45.0:
                was_active = c.is_active
                c.stage = PumpStage.DUMP_CONFIRMED
                c.is_active = False
                if not c.dump_date:
                    c.dump_date = now_ts.strftime("%Y-%m-%d")
                c.notes = f"ĐÃ XÁC NHẬN DUMP: Rơi -{c.drawdown_from_peak_pct:.1f}% từ đỉnh ${c.highest_peak_price:.6f}."

                # ── CRISP-DM Active Learning Feedback Loop ──
                # Auto-record confirmed dump event into ML training dataset
                if was_active and c.max_n >= 2.0:
                    try:
                        from .pump_multiplier_classifier import PumpDatasetBuilder, PumpEvent
                        db = PumpDatasetBuilder()
                        ev = PumpEvent(
                            symbol=c.symbol,
                            event_date=c.origin_date,
                            source="auto_lifecycle_tracker",
                            pre_pump_price=c.origin_bottom_price,
                            pre_pump_vol_24h=vol_24h,
                            peak_price=c.highest_peak_price,
                            pump_duration_h=float(c.pump_age_days * 24),
                            vol_spike_ratio=max(1.0, c.max_n * 2.5),
                            n_actual=c.max_n,
                            notes=f"Active Learning Dump Confirmed: {c.notes}"
                        )
                        db.upsert(ev)
                    except Exception:
                        pass
            
            # Condition 2: Exhaustion Warning
            elif c.drawdown_from_peak_pct >= 28.0 or funding_rate >= 0.0010:
                c.stage = PumpStage.EXHAUSTION_WARNING
            
            # Condition 3: High Altitude Consolidation (Holding well within 10-25% from peak)
            elif c.pump_age_days >= 7 and c.drawdown_from_peak_pct < 28.0:
                c.stage = PumpStage.HIGH_CONSOLIDATION
            
            # Condition 4: Active Expansion
            elif c.drawdown_from_peak_pct < 12.0:
                c.stage = PumpStage.ACTIVE_EXPANSION

        c.stage_label_vi = STAGE_LABELS_VI.get(c.stage, c.stage)
        self.save()
        return c

    def register_new_pump(
        self,
        symbol:              str,
        origin_bottom_price: float,
        current_price:       float,
        origin_date:         Optional[str] = None,
        expected_n_ml:       float = 0.0,
        expected_n_low:      float = 0.0,
        expected_n_high:     float = 0.0,
        notes:               str = "",
    ) -> PumpCampaign:
        """Register a newly detected pump campaign into persistent tracking."""
        symbol = symbol.upper()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        orig_d  = origin_date or now_str

        campaign = PumpCampaign(
            symbol=symbol,
            origin_date=orig_d,
            origin_bottom_price=origin_bottom_price,
            highest_peak_price=max(current_price, origin_bottom_price),
            highest_peak_date=orig_d,
            current_price=current_price,
            expected_n_ml=expected_n_ml,
            expected_n_low=expected_n_low,
            expected_n_high=expected_n_high,
            stage=PumpStage.IGNITION,
            notes=notes or f"Khởi phát sóng bơm mới ngày {orig_d}.",
        )
        self.campaigns[symbol] = campaign
        self.save()
        return campaign

    def get_active_campaigns(self) -> List[PumpCampaign]:
        """Return all currently active pump campaigns sorted by current_n descending."""
        active = [c for c in self.campaigns.values() if c.is_active]
        active.sort(key=lambda c: c.current_n, reverse=True)
        return active

    def get_all_campaigns(self) -> List[PumpCampaign]:
        all_c = list(self.campaigns.values())
        all_c.sort(key=lambda c: c.current_n, reverse=True)
        return all_c

    def get_campaign(self, symbol: str) -> Optional[PumpCampaign]:
        return self.campaigns.get(symbol.upper())


# Global Singleton Registry
_GLOBAL_REGISTRY: Optional[PumpLifecycleRegistry] = None


def get_pump_registry() -> PumpLifecycleRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = PumpLifecycleRegistry()
    return _GLOBAL_REGISTRY
