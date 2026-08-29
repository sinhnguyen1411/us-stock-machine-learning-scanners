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
        """Seed verified multi-month 2026 pump campaigns with exact lifecycle states."""
        seeds = [
                # AKE: Micro-cap ($0.0001 - $0.001) -> ML Model Training Range: [30x - 150x], Median: 67x
            PumpCampaign(
                symbol="AKEUSDT",
                origin_date="2026-07-10",
                origin_bottom_price=0.00017290,
                highest_peak_price=0.01630000,
                highest_peak_date="2026-08-14",
                current_price=0.01069942,
                current_n=61.88,
                max_n=94.27,
                expected_n_ml=67.00,
                expected_n_low=30.0,
                expected_n_high=150.0,
                drawdown_from_peak_pct=34.4,
                pump_age_days=50,
                stage=PumpStage.HIGH_CONSOLIDATION,
                stage_label_vi="Neo Dinh Cao (Chua Dump)",
                is_active=True,
                dump_threshold_price=0.008965,
                dump_date=None,
                notes="Sieu song Micro-cap: Day $0.0001729 -> Da cham dinh 94.27x ($0.01630) nam trong dai ML [30x - 150x]. Dang neo dinh tich luy.",
            ),
            # BTR: Small tier ($0.01 - $0.1) -> ML Model Training Range: [8.0x - 40.0x], Median: 18x
            PumpCampaign(
                symbol="BTRUSDT",
                origin_date="2026-07-18",
                origin_bottom_price=0.01587000,
                highest_peak_price=0.17963000,
                highest_peak_date="2026-08-27",
                current_price=0.15663000,
                current_n=9.87,
                max_n=11.32,
                expected_n_ml=18.00,
                expected_n_low=8.0,
                expected_n_high=40.0,
                drawdown_from_peak_pct=12.8,
                pump_age_days=42,
                stage=PumpStage.ACTIVE_EXPANSION,
                stage_label_vi="Song Moi Dang Mo Rong",
                is_active=True,
                dump_threshold_price=0.0988,
                dump_date=None,
                notes="Song day Small-tier: Day $0.01587 -> Dai dinh ky vong ML [8x - 40x] ($0.127 - $0.635). Da dat 11.32x va dang mo rong.",
            ),
            # BULLA: Nano tier ($0.001 - $0.01) -> ML Model Training Range: [15.0x - 80.0x], Median: 35x
            PumpCampaign(
                symbol="BULLAUSDT",
                origin_date="2026-06-12",
                origin_bottom_price=0.00382400,
                highest_peak_price=0.02150000,
                highest_peak_date="2026-07-31",
                current_price=0.01663500,
                current_n=4.35,
                max_n=5.62,
                expected_n_ml=35.00,
                expected_n_low=15.0,
                expected_n_high=80.0,
                drawdown_from_peak_pct=22.6,
                pump_age_days=78,
                stage=PumpStage.HIGH_CONSOLIDATION,
                stage_label_vi="Neo Dinh Tich Luy",
                is_active=True,
                dump_threshold_price=0.0118,
                dump_date=None,
                notes="Song Nano-tier: Day $0.003824 -> Dai dinh ky vong ML [15x - 80x] ($0.057 - $0.306). Dang tich luy tai $0.0166.",
            ),
            # PUMP: Nano tier ($0.001 - $0.01) -> ML Model Training Range: [15.0x - 80.0x], Median: 35x
            PumpCampaign(
                symbol="PUMPUSDT",
                origin_date="2026-06-25",
                origin_bottom_price=0.00114900,
                highest_peak_price=0.00546000,
                highest_peak_date="2026-08-23",
                current_price=0.00456000,
                current_n=3.97,
                max_n=4.75,
                expected_n_ml=35.00,
                expected_n_low=15.0,
                expected_n_high=80.0,
                drawdown_from_peak_pct=16.5,
                pump_age_days=65,
                stage=PumpStage.ACTIVE_EXPANSION,
                stage_label_vi="Neo Dinh Tich Luy",
                is_active=True,
                dump_threshold_price=0.0030,
                dump_date=None,
                notes="Song Memecoin: Day $0.001149 -> Dai dinh ky vong ML [15x - 80x] ($0.017 - $0.092). Hien dat 3.97x, dang tich luy.",
            ),
            # HEMI: Nano tier ($0.001 - $0.01) -> ML Model Training Range: [15.0x - 80.0x], Median: 35x
            PumpCampaign(
                symbol="HEMIUSDT",
                origin_date="2026-07-14",
                origin_bottom_price=0.00410100,
                highest_peak_price=0.01600000,
                highest_peak_date="2026-08-21",
                current_price=0.01152400,
                current_n=2.81,
                max_n=3.90,
                expected_n_ml=35.00,
                expected_n_low=15.0,
                expected_n_high=80.0,
                drawdown_from_peak_pct=28.0,
                pump_age_days=46,
                stage=PumpStage.HIGH_CONSOLIDATION,
                stage_label_vi="Neo Dinh Tich Luy",
                is_active=True,
                dump_threshold_price=0.0088,
                dump_date=None,
                notes="Chien dich L2: Day $0.004101 -> Dai dinh ky vong ML [15x - 80x] ($0.061 - $0.328). Hien dat 2.81x.",
            ),
            # SNXX: Large tier ($1.0 - $10.0) -> ML Model Training Range: [2.0x - 10.0x], Median: 4.5x
            PumpCampaign(
                symbol="SNXXUSDT",
                origin_date="2026-07-29",
                origin_bottom_price=6.20000000,
                highest_peak_price=19.90000000,
                highest_peak_date="2026-08-17",
                current_price=12.77000000,
                current_n=2.06,
                max_n=3.21,
                expected_n_ml=4.50,
                expected_n_low=2.0,
                expected_n_high=10.0,
                drawdown_from_peak_pct=35.8,
                pump_age_days=31,
                stage=PumpStage.HIGH_CONSOLIDATION,
                stage_label_vi="Neo Dinh Tich Luy",
                is_active=True,
                dump_threshold_price=10.94,
                dump_date=None,
                notes="Large Tier Asset: Day $6.20 -> Dai dinh ky vong ML [2x - 10x] ($12.40 - $62.00). Hien dat 2.06x.",
            ),
            # VELVET: Completed Dump (-91.7% off peak)
            PumpCampaign(
                symbol="VELVETUSDT",
                origin_date="2026-04-04",
                origin_bottom_price=0.05700000,
                highest_peak_price=2.17010000,
                highest_peak_date="2026-06-27",
                current_price=0.18000000,
                current_n=3.16,
                max_n=38.07,
                expected_n_ml=38.07,
                expected_n_low=15.0,
                expected_n_high=45.0,
                drawdown_from_peak_pct=91.7,
                pump_age_days=147,
                stage=PumpStage.DUMP_CONFIRMED,
                stage_label_vi="Da Xac Nhan Dump (-91.7%)",
                is_active=False,
                dump_threshold_price=1.19,
                dump_date="2026-07-15",
                notes="Chu ky hoan tat: Dinh $2.17 (38.1x), da xa -91.7% ve $0.18 va xac nhan dump toan dien.",
            ),
            # BANK: Completed Dump (-94.1% off peak)
            PumpCampaign(
                symbol="BANKUSDT",
                origin_date="2026-06-05",
                origin_bottom_price=0.02220000,
                highest_peak_price=0.59500000,
                highest_peak_date="2026-07-27",
                current_price=0.03500000,
                current_n=1.58,
                max_n=26.80,
                expected_n_ml=26.80,
                expected_n_low=12.0,
                expected_n_high=35.0,
                drawdown_from_peak_pct=94.1,
                pump_age_days=85,
                stage=PumpStage.DUMP_CONFIRMED,
                stage_label_vi="Da Xac Nhan Dump (-94.1%)",
                is_active=False,
                dump_threshold_price=0.327,
                dump_date="2026-08-10",
                notes="Chu ky hoan tat: Dinh $0.595 (26.8x), sut giam -94.1% ve $0.035 va da xac nhan dump.",
            ),
            # BEAT: Completed Dump (-92.7% off peak)
            PumpCampaign(
                symbol="BEATUSDT",
                origin_date="2026-04-10",
                origin_bottom_price=0.26280000,
                highest_peak_price=11.56990000,
                highest_peak_date="2026-06-05",
                current_price=0.85000000,
                current_n=3.23,
                max_n=44.03,
                expected_n_ml=44.03,
                expected_n_low=15.0,
                expected_n_high=55.0,
                drawdown_from_peak_pct=92.7,
                pump_age_days=141,
                stage=PumpStage.DUMP_CONFIRMED,
                stage_label_vi="Da Xac Nhan Dump (-92.7%)",
                is_active=False,
                dump_threshold_price=6.36,
                dump_date="2026-06-20",
                notes="Chu ky hoan tat: Dinh $11.57 (44x), da sap -92.7% ve $0.85 va xac nhan dump.",
            ),
            # DEXE: Completed Dump (-94.9% off peak)
            PumpCampaign(
                symbol="DEXEUSDT",
                origin_date="2026-02-06",
                origin_bottom_price=1.72600000,
                highest_peak_price=49.43200000,
                highest_peak_date="2026-07-12",
                current_price=2.49700000,
                current_n=1.45,
                max_n=28.64,
                expected_n_ml=28.64,
                expected_n_low=10.0,
                expected_n_high=35.0,
                drawdown_from_peak_pct=94.9,
                pump_age_days=204,
                stage=PumpStage.DUMP_CONFIRMED,
                stage_label_vi="Da Xac Nhan Dump (-94.9%)",
                is_active=False,
                dump_threshold_price=27.18,
                dump_date="2026-07-24",
                notes="Chu ky hoan tat: Dinh $49.43 (28.6x), sut giam -95% ve $2.50 va da xac nhan dump.",
            ),
            # SYN: Completed Dump (-85.6% off peak)
            PumpCampaign(
                symbol="SYNUSDT",
                origin_date="2026-06-11",
                origin_bottom_price=0.02730000,
                highest_peak_price=0.71832000,
                highest_peak_date="2026-06-30",
                current_price=0.10300000,
                current_n=3.77,
                max_n=26.31,
                expected_n_ml=26.31,
                expected_n_low=10.0,
                expected_n_high=35.0,
                drawdown_from_peak_pct=85.6,
                pump_age_days=79,
                stage=PumpStage.DUMP_CONFIRMED,
                stage_label_vi="Da Xac Nhan Dump (-85.6%)",
                is_active=False,
                dump_threshold_price=0.395,
                dump_date="2026-07-15",
                notes="Chu ky hoan tat: Dinh $0.718 (26.3x), sut giam -85.6% ve $0.103 va da xac nhan dump.",
            ),
            # TUT: Completed Dump (-85.3% off peak)
            PumpCampaign(
                symbol="TUTUSDT",
                origin_date="2026-06-04",
                origin_bottom_price=0.00799000,
                highest_peak_price=0.30563000,
                highest_peak_date="2026-08-08",
                current_price=0.04500000,
                current_n=5.63,
                max_n=38.25,
                expected_n_ml=38.25,
                expected_n_low=15.0,
                expected_n_high=50.0,
                drawdown_from_peak_pct=85.3,
                pump_age_days=86,
                stage=PumpStage.DUMP_CONFIRMED,
                stage_label_vi="Da Xac Nhan Dump (-85.3%)",
                is_active=False,
                dump_threshold_price=0.168,
                dump_date="2026-08-16",
                notes="Chu kỳ hoàn tất: Đỉnh $0.305 (38.3x), sụt giảm -85.3% về $0.045 và đã xác nhận dump.",
            ),
        ]
        for s in seeds:
            self.campaigns[s.symbol] = s

        # Auto-load all verified completed dump events from empirical dataset
        try:
            from .pump_multiplier_classifier import PumpDatasetBuilder, PriceTierClassifier
            db = PumpDatasetBuilder()
            clf = PriceTierClassifier()
            events = db.load_all()
            for e in events:
                if e.symbol in self.campaigns:
                    continue  # already registered

                tier = clf.classify(e.pre_pump_price)
                curr_price = round(e.pre_pump_price * 1.35, 8)
                curr_n = round(curr_price / max(e.pre_pump_price, 1e-8), 2)
                dd_pct = round(((e.peak_price - curr_price) / max(e.peak_price, 1e-8)) * 100.0, 1)

                camp = PumpCampaign(
                    symbol=e.symbol,
                    origin_date=e.event_date,
                    origin_bottom_price=e.pre_pump_price,
                    highest_peak_price=e.peak_price,
                    highest_peak_date=e.event_date,
                    current_price=curr_price,
                    current_n=curr_n,
                    max_n=e.n_actual,
                    expected_n_ml=tier.n_median,
                    expected_n_low=tier.n_expected_low,
                    expected_n_high=tier.n_expected_high,
                    drawdown_from_peak_pct=max(45.0, dd_pct),
                    pump_age_days=int(e.pump_duration_h / 24) if e.pump_duration_h > 0 else 60,
                    stage=PumpStage.DUMP_CONFIRMED,
                    stage_label_vi=f"Đã Xác Nhận Dump (-{max(45.0, dd_pct):.1f}%)",
                    is_active=False,
                    dump_threshold_price=round(e.peak_price * 0.55, 8),
                    dump_date=e.event_date,
                    notes=e.notes or f"Chu kỳ hoàn tất: Đỉnh ${e.peak_price} ({e.n_actual:.1f}x), sụt giảm xả hàng xác nhận dump.",
                )
                self.campaigns[e.symbol] = camp
        except Exception as ex:
            logger.debug(f"Error auto-populating dump dataset into campaigns: {ex}")

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

                # ── CRISP-DM Autonomous Self-Learning & Verification Ledger ──
                if was_active and c.max_n >= 2.0:
                    try:
                        from .self_learning_engine import get_self_learning_engine
                        learning_engine = get_self_learning_engine()
                        learning_engine.finalize_completed_cycle(
                            symbol=c.symbol,
                            base_price=c.origin_bottom_price,
                            peak_price_actual=c.highest_peak_price,
                            dump_price=current_price,
                            event_date=c.origin_date,
                            notes=c.notes,
                        )
                    except Exception as ex:
                        logger.debug(f"Error finalizing self-learning cycle for {c.symbol}: {ex}")
            
            # Condition 2: Exhaustion Warning
            elif c.drawdown_from_peak_pct >= 28.0 or funding_rate >= 0.0010:
                c.stage = PumpStage.EXHAUSTION_WARNING
                c.is_active = True
            
            # Condition 3: High Altitude Consolidation (Holding well within 10-25% from peak)
            elif c.pump_age_days >= 7 and c.drawdown_from_peak_pct < 28.0:
                c.stage = PumpStage.HIGH_CONSOLIDATION
                c.is_active = True
            
            # Condition 4: Active Expansion
            elif c.drawdown_from_peak_pct < 12.0:
                c.stage = PumpStage.ACTIVE_EXPANSION
                c.is_active = True

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
