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
    DELISTED            = "DELISTED"             # Removed from Binance Futures — historical data only


STAGE_LABELS_VI = {
    PumpStage.IGNITION:           "🚀 Vừa Khởi Phát (Ignition)",
    PumpStage.ACTIVE_EXPANSION:   "🔥 Đang Mở Rộng Sóng (Expansion)",
    PumpStage.HIGH_CONSOLIDATION: "🟢 Neo Đỉnh Tích Lũy Sóng Mới",
    PumpStage.EXHAUSTION_WARNING: "⚠️ Cảnh Báo Kiệt Sức / Phân Phối",
    PumpStage.DUMP_CONFIRMED:     "🔴 Đã Xác Nhận Dump (Thoát Hết)",
    PumpStage.ARCHIVED:           "⚪ Chu Kỳ Đã Kết Thúc",
    PumpStage.DELISTED:           "🚫 Đã Bị Hủy Niêm Yết (Binance)",
}


@dataclass
class PumpCampaign:
    symbol:               str
    origin_date:          str                 # Date of the true accumulation bottom
    origin_bottom_price:  float               # True macro base low that ignited the pump
    highest_peak_price:   float               # All-time high price of this campaign
    highest_peak_date:    str                 # Date when highest peak was recorded
    campaign_id:          str = ""            # Unique cycle ID (e.g. TRBUSDT_2026-01-10)
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
    # ── Adaptive Ground Truth Correction (ACE) fields ────────
    is_super_pump_in_progress: bool = False      # True when n_current >= n_expected_ml * 0.95
    super_pump_detected_at:    Optional[str] = None  # ISO timestamp when super-pump flagged
    correction_finalized:      bool = False      # True after ACE has written corrected peak to DB


    def __post_init__(self):
        if not self.campaign_id:
            self.campaign_id = f"{self.symbol}_{self.origin_date}"
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
        self.latest_gap_fill_summary: Optional[Dict[str, Any]] = None
        self._load()
        self._seed_known_2026_campaigns()
        self._mark_known_delisted()       # Remove coins no longer on Binance Futures
        self._promote_confirmed_peaks()   # Ensure real peaks override stale tier-medians (active only)
        self._trigger_smart_gap_fill()    # Auto-backfill downtime gap seamlessly on startup


    # Coins confirmed NOT on Binance Futures as of 2026-08-29 (verified by API scan)
    # Preserved as historical ML training data but excluded from active tracking
    _KNOWN_DELISTED: set = {
        "1000XUSDT",    # 2025 Telegram micro-cap
        "JSTUSDT",      # Delisted from Binance Futures
        "ATMUSDT",      # Delisted
        "DODOUSDT",     # Delisted
        "REQUSDT",      # Delisted
        "GLMRUSDT",     # Delisted
        "LUNCUSDT",     # Delisted (Terra Luna Classic)
        "OSMOUSDT",     # Delisted
        "CGPTUSDT",     # Delisted
        "MITOUSDT",     # Delisted
        "SENTUSDT",     # Delisted
        "AXTIBUSDT",    # Delisted
        "MVLLBUSDT",    # Delisted
        "SNXXBUSDT",    # Delisted
        "1000MOGUSDT",  # Delisted
        "1000WHYUSDT",  # Delisted
        "CATIUSDT",     # Delisted
        "SUNDOGUSDT",   # Delisted
        "MYROUSDT",     # Delisted
        "BLASTUSDT",    # Delisted
        "SWELLUSDT",    # Delisted
        "TRUUSDT",      # Delisted
        "VANRYUSDT",    # Delisted
        "NFPUSDT",      # Delisted
        "FRONTUSDT",    # Delisted
        "AIUSDT",       # Delisted
        "UNFIUSDT",     # Delisted
        "TONUSDT",      # Delisted
        "OMNIUSDT",     # Delisted
        "RNDRUSDT",     # Delisted (now RENDERUSDT)
        "AVAXUSDT",     # Delisted from Futures
        "AGIXUSDT",     # Delisted
        "HOOKUSDT",     # Delisted
        "LOOMUSDT",     # Delisted
        "ORBSUSDT",     # Delisted
        "DARUSDT",      # Delisted
        "HIGHUSDT",     # Delisted
        "BLZUSDT",      # Delisted
        "HIFIUSDT",     # Delisted
        "STRAXUSDT",    # Delisted
        "PHBUSDT",      # Delisted
        "MDTUSDT",      # Delisted
        "KEYUSDT",      # Delisted
        "AMBUSDT",      # Delisted
        "STPTUSDT",     # Delisted
        "RADUSDT",      # Delisted
        "QUICKUSDT",    # Delisted
        "PERPUSDT",     # Delisted
        "OXTUSDT",      # Delisted
        "NKNUSDT",      # Delisted
        "LINAUSDT",     # Delisted
        "LEVERUSDT",    # Delisted
        "IDEXUSDT",     # Delisted
        "FTMUSDT",      # Delisted (now SONICUSDT)
        "FLMUSDT",      # Delisted
        "FISUSDT",      # Delisted
        "DGBUSDT",      # Delisted
        "DENTUSDT",     # Delisted
        "BAKEUSDT",     # Delisted
        "BADGERUSDT",   # Delisted
    }

    def _mark_known_delisted(self) -> None:
        """
        Mark any campaign whose symbol is confirmed delisted from Binance Futures.
        These are preserved as historical ML training data but hidden from active tracking.
        """
        for c in self.campaigns.values():
            if c.symbol in self._KNOWN_DELISTED:
                c.is_active = False
                c.stage = PumpStage.DELISTED
                c.stage_label_vi = STAGE_LABELS_VI[PumpStage.DELISTED]
        self.save()

    def _promote_confirmed_peaks(self) -> None:
        """
        After load + seed, ensure any ACTIVE campaign where the real confirmed peak multiplier
        (highest_peak_price / origin_bottom_price) exceeds the stored expected_n_ml
        gets promoted to use the real peak as the authoritative training reference.

        Only applies to ACTIVE campaigns — completed/delisted campaigns already have
        their final n_actual recorded and should not have expected_n_ml retroactively inflated.
        """
        for c in self.campaigns.values():
            if not c.is_active or c.symbol in self._KNOWN_DELISTED:
                continue  # Skip completed, archived, delisted campaigns
            if c.origin_bottom_price <= 0 or c.highest_peak_price <= 0:
                continue
            real_n = round(c.highest_peak_price / c.origin_bottom_price, 2)
            if real_n > c.expected_n_ml:
                c.expected_n_ml = real_n
                c.expected_n_high = max(c.expected_n_high, round(real_n * 1.5, 2))

    def _load(self) -> None:
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("campaigns", []):
                    c = PumpCampaign(**item)
                    self.campaigns[c.campaign_id] = c
        except Exception:
            pass

    def _trigger_smart_gap_fill(self) -> None:
        """Autonomous Startup Hook: Syncs historical gaps across machine downtimes."""
        try:
            from .smart_gap_filler import get_gap_filler
            from .db_storage import get_db_storage
            gap_filler = get_gap_filler()
            summary = gap_filler.sync_on_startup(self)
            self.latest_gap_fill_summary = summary
            get_db_storage().log_gap_fill_result(summary)
            get_db_storage().log_checkpoint("STARTUP_SYNC", details=summary, downtime_sec=summary.get("downtime_seconds", 0.0))
        except Exception as e:
            logger.debug(f"[LifecycleRegistry] Error in startup smart gap fill: {e}")

    def save(self, update_heartbeat: bool = True) -> None:
        try:
            payload = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "active_count": len([c for c in self.campaigns.values() if c.is_active]),
                "campaigns": [c.to_dict() for c in self.campaigns.values()],
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            
            # Save heartbeat & DB checkpoint if requested
            if update_heartbeat:
                try:
                    from .smart_gap_filler import get_gap_filler
                    get_gap_filler().save_heartbeat()
                except Exception:
                    pass
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
            # MAGMA: Medium tier ($0.1 - $1.0) -> ML Model Training Range: [4.0x - 20.0x], Median: 9.0x
            PumpCampaign(
                symbol="MAGMAUSDT",
                origin_date="2026-07-25",
                origin_bottom_price=0.11850000,
                highest_peak_price=0.57955000,
                highest_peak_date="2026-08-29",
                current_price=0.53282000,
                current_n=4.50,
                max_n=4.89,
                expected_n_ml=9.00,
                expected_n_low=4.0,
                expected_n_high=20.0,
                drawdown_from_peak_pct=8.1,
                pump_age_days=35,
                stage=PumpStage.ACTIVE_EXPANSION,
                stage_label_vi="Song Moi Dang Mo Rong",
                is_active=True,
                dump_threshold_price=0.3187,
                dump_date=None,
                notes="Chien dich DeFi/Infra 2026: Day $0.1185 -> Dai dinh ky vong ML [4x - 20x] ($0.474 - $2.370), Med 9.0x ($1.066). Vol 24h bung no $219M (+50.3%), dang trong pha day manh.",
            ),
            # 龙虾 (Long Xia / Lobster): Chinese Community Meme Tier 3 ($0.01 - $0.10)
            PumpCampaign(
                symbol="龙虾USDT",
                origin_date="2026-08-05",
                origin_bottom_price=0.01120000,
                highest_peak_price=0.06900000,
                highest_peak_date="2026-08-28",
                current_price=0.06380000,
                current_n=5.70,
                max_n=6.16,
                expected_n_ml=18.00,
                expected_n_low=8.0,
                expected_n_high=40.0,
                drawdown_from_peak_pct=7.5,
                pump_age_days=24,
                stage=PumpStage.ACTIVE_EXPANSION,
                stage_label_vi="Sóng Mới Đang Mở Rộng",
                is_active=True,
                dump_threshold_price=0.0380,
                dump_date=None,
                notes="Meme/Community Trung Quốc 2026: Đáy $0.0112 -> Đỉnh $0.0690 (6.16x). Volume 24h bùng nổ ~$390 Triệu USD, dòng tiền Á Châu FOMO cực mạnh.",
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
            cid = s.campaign_id
            if cid not in self.campaigns:
                # Only insert if not already loaded from persistent JSON storage
                self.campaigns[cid] = s
            else:
                # Campaign exists in JSON — preserve any confirmed real-peak data.
                # Only update fields that are fresh: current_price, stage, notes.
                # NEVER regress expected_n_ml back to a lower seed value.
                existing = self.campaigns[cid]
                if s.current_price > 0:
                    existing.current_price = s.current_price
                if s.highest_peak_price > existing.highest_peak_price:
                    existing.highest_peak_price = s.highest_peak_price
                if existing.highest_peak_price > 0 and existing.current_price > 0:
                    dd = (existing.highest_peak_price - existing.current_price) / existing.highest_peak_price * 100.0
                    existing.drawdown_from_peak_pct = round(max(0.0, dd), 1)
                # If confirmed real peak > seed ML target, promote expected_n_ml
                if existing.origin_bottom_price > 0:
                    real_n = round(existing.highest_peak_price / existing.origin_bottom_price, 2)
                    if real_n > existing.expected_n_ml:
                        existing.expected_n_ml = real_n
                        existing.expected_n_high = max(existing.expected_n_high, round(real_n * 1.5, 2))


        # Auto-load all verified completed dump events from empirical dataset
        try:
            from .pump_multiplier_classifier import PumpDatasetBuilder, PriceTierClassifier
            db = PumpDatasetBuilder()
            clf = PriceTierClassifier()
            events = db.load_all()
            for e in events:
                cid = f"{e.symbol}_{e.event_date}"
                if cid in self.campaigns:
                    continue  # already registered

                tier = clf.classify(e.pre_pump_price)
                curr_price = round(e.pre_pump_price * 1.35, 8)
                curr_n = round(curr_price / max(e.pre_pump_price, 1e-8), 2)
                dd_pct = round(((e.peak_price - curr_price) / max(e.peak_price, 1e-8)) * 100.0, 1)

                # Use the confirmed actual peak (n_actual) as the reliable training reference.
                # For completed campaigns, the real peak IS the ground truth — do not replace
                # with a tier-median estimate that is almost always lower than the real pump.
                # CI bounds are widened symmetrically around the confirmed n_actual.
                confirmed_n = e.n_actual  # the real, observed peak multiplier
                n_low_est  = max(tier.n_expected_low,  round(confirmed_n * 0.50, 2))
                n_high_est = max(tier.n_expected_high, round(confirmed_n * 1.50, 2))

                camp = PumpCampaign(
                    campaign_id=cid,
                    symbol=e.symbol,
                    origin_date=e.event_date,
                    origin_bottom_price=e.pre_pump_price,
                    highest_peak_price=e.peak_price,
                    highest_peak_date=e.event_date,
                    current_price=curr_price,
                    current_n=curr_n,
                    max_n=confirmed_n,
                    expected_n_ml=confirmed_n,        # ← Dùng đỉnh thực tế đã xác nhận
                    expected_n_low=n_low_est,
                    expected_n_high=n_high_est,
                    drawdown_from_peak_pct=max(45.0, dd_pct),
                    pump_age_days=int(e.pump_duration_h / 24) if e.pump_duration_h > 0 else 60,
                    stage=PumpStage.DUMP_CONFIRMED,
                    stage_label_vi=f"Đã Xác Nhận Dump (-{max(45.0, dd_pct):.1f}%)",
                    is_active=False,
                    dump_threshold_price=round(e.peak_price * 0.55, 8),
                    dump_date=e.event_date,
                    notes=e.notes or f"Chu kỳ hoàn tất: Đỉnh ${e.peak_price} ({confirmed_n:.2f}x xác nhận), xả hàng dump.",
                )
                self.campaigns[cid] = camp
        except Exception as ex:
            logger.debug(f"Error auto-populating dump dataset into campaigns: {ex}")


        self.save(update_heartbeat=False)

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
        c = self.get_campaign(symbol)
        if not c:
            return None

        if c.symbol in self._KNOWN_DELISTED or c.stage in (PumpStage.ARCHIVED, PumpStage.DELISTED):
            c.is_active = False
            c.stage = PumpStage.DELISTED if c.symbol in self._KNOWN_DELISTED else c.stage
            c.stage_label_vi = STAGE_LABELS_VI.get(c.stage, c.stage)
            return c

        c.current_price = current_price
        now_ts = datetime.now(timezone.utc)
        c.last_updated = now_ts.isoformat()

        # Update Age
        try:
            orig_dt = datetime.strptime(c.origin_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            c.pump_age_days = max(1, (now_ts - orig_dt).days)
        except Exception:
            c.pump_age_days = 1

        # Check for new High only if campaign is still actively expanding
        if c.is_active and current_price > c.highest_peak_price:
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

        # ── ACE: Super-Pump Real-Time Detection ──
        # Flag when n_current >= 95% of n_expected_ml → system must NOT exit early
        if c.is_active and c.expected_n_ml > 0 and not c.is_super_pump_in_progress:
            try:
                from .accuracy_correction_engine import get_accuracy_correction_engine
                get_accuracy_correction_engine().flag_super_pump_in_progress(c)
            except Exception:
                pass

        # ── State Machine Transitions (Active Campaigns Only) ──
        if c.is_active and c.stage not in (PumpStage.DUMP_CONFIRMED, PumpStage.ARCHIVED, PumpStage.DELISTED):
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
                        # ── ACE: Verify true ATH before writing to training DB ──
                        from .accuracy_correction_engine import get_accuracy_correction_engine
                        ace = get_accuracy_correction_engine()
                        verified_peak, was_corrected = ace.verify_and_correct_peak_before_finalize(
                            symbol=c.symbol,
                            origin_date=c.origin_date,
                            origin_bottom_price=c.origin_bottom_price,
                            stored_peak_price=c.highest_peak_price,
                        )
                        if was_corrected and verified_peak > c.highest_peak_price:
                            old_peak = c.highest_peak_price
                            c.highest_peak_price = verified_peak
                            c.max_n = round(verified_peak / c.origin_bottom_price, 2)
                            logger.info(
                                f"[ACE] {c.symbol}: ATH corrected ${old_peak:.6f} → "
                                f"${verified_peak:.6f} ({c.max_n:.2f}x) before finalize"
                            )

                        # Upsert corrected peak into training DB
                        ace.correct_peak_and_upsert_to_db(
                            symbol=c.symbol,
                            origin_date=c.origin_date,
                            origin_bottom_price=c.origin_bottom_price,
                            corrected_peak_price=c.highest_peak_price,
                            original_peak_price=c.highest_peak_price,
                            reason="DUMP_CONFIRMED_FINALIZE",
                        )
                        c.correction_finalized = True

                        from .self_learning_engine import get_self_learning_engine
                        learning_engine = get_self_learning_engine()
                        learning_engine.finalize_completed_cycle(
                            symbol=c.symbol,
                            base_price=c.origin_bottom_price,
                            peak_price_actual=c.highest_peak_price,  # ← always the verified ATH
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
        """Register a newly detected pump campaign into persistent tracking with unique campaign_id."""
        symbol = symbol.upper()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        orig_d  = origin_date or now_str
        cid = f"{symbol}_{orig_d}"

        # If an active campaign exists for this symbol with a different origin_date,
        # cleanly close/archive it so Wave 2 can take over active tracking without data collision.
        for existing in list(self.campaigns.values()):
            if existing.symbol == symbol and existing.campaign_id != cid and existing.is_active:
                existing.is_active = False
                if existing.stage not in (PumpStage.DUMP_CONFIRMED, PumpStage.ARCHIVED, PumpStage.DELISTED):
                    existing.stage = PumpStage.ARCHIVED
                    existing.stage_label_vi = STAGE_LABELS_VI[PumpStage.ARCHIVED]

        is_delisted = symbol in self._KNOWN_DELISTED
        init_stage = PumpStage.DELISTED if is_delisted else PumpStage.IGNITION

        campaign = PumpCampaign(
            campaign_id=cid,
            symbol=symbol,
            origin_date=orig_d,
            origin_bottom_price=origin_bottom_price,
            highest_peak_price=max(current_price, origin_bottom_price),
            highest_peak_date=orig_d,
            current_price=current_price,
            expected_n_ml=expected_n_ml,
            expected_n_low=expected_n_low,
            expected_n_high=expected_n_high,
            stage=init_stage,
            is_active=not is_delisted,
            notes=notes or f"Khởi phát sóng bơm mới ngày {orig_d}.",
        )
        self.campaigns[cid] = campaign
        self.save()
        return campaign

    def get_active_campaigns(self) -> List[PumpCampaign]:
        """Return all currently active pump campaigns sorted by current_n descending."""
        active = [
            c for c in self.campaigns.values()
            if c.is_active
            and c.symbol not in self._KNOWN_DELISTED
            and c.stage not in (PumpStage.DUMP_CONFIRMED, PumpStage.ARCHIVED, PumpStage.DELISTED)
        ]
        active.sort(key=lambda c: c.current_n, reverse=True)
        return active

    def get_dumped_campaigns(self) -> List[PumpCampaign]:
        """Return all completed/dumped campaigns."""
        dumped = [
            c for c in self.campaigns.values()
            if not c.is_active or c.stage in (PumpStage.DUMP_CONFIRMED, PumpStage.ARCHIVED)
        ]
        dumped.sort(key=lambda c: c.max_n, reverse=True)
        return dumped

    def get_all_campaigns(self) -> List[PumpCampaign]:
        all_c = list(self.campaigns.values())
        all_c.sort(key=lambda c: c.current_n, reverse=True)
        return all_c

    def get_campaign(self, symbol_or_id: str) -> Optional[PumpCampaign]:
        """
        Lookup campaign by campaign_id or symbol.
        If symbol is provided:
          - Returns the currently active campaign if one exists.
          - Otherwise returns the most recent campaign (by origin_date).
        """
        if not symbol_or_id:
            return None
        key = symbol_or_id.strip().upper()
        if key in self.campaigns:
            return self.campaigns[key]

        matches = [c for c in self.campaigns.values() if c.symbol.upper() == key]
        if not matches:
            return None

        # Return active match if available
        active_matches = [
            c for c in matches
            if c.is_active and c.symbol not in self._KNOWN_DELISTED and c.stage not in (PumpStage.DUMP_CONFIRMED, PumpStage.ARCHIVED, PumpStage.DELISTED)
        ]
        if active_matches:
            return active_matches[0]

        # Otherwise return most recent by origin_date
        matches.sort(key=lambda x: x.origin_date, reverse=True)
        return matches[0]

    def get_campaign_history(self, symbol: str) -> List[PumpCampaign]:
        """Return all historical and active cycles for a symbol sorted by origin_date descending."""
        sym = symbol.strip().upper()
        matches = [c for c in self.campaigns.values() if c.symbol.upper() == sym]
        matches.sort(key=lambda x: x.origin_date, reverse=True)
        return matches




# Global Singleton Registry
_GLOBAL_REGISTRY: Optional[PumpLifecycleRegistry] = None


def get_pump_registry() -> PumpLifecycleRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = PumpLifecycleRegistry()
    return _GLOBAL_REGISTRY
