"""
Price-Tier × Pump Multiplier (n) Classifier & Dataset Builder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implements an 8-tier logarithmic price classification system and a JSON-backed
pump event database. Used by PumpMultiplierRegressor to learn the empirical
power-law relationship:

    log(n) ≈ α  -  β·log(price_pre)  +  γ·log(vol_pump / vol_pre)

where n = peak_price / pre_pump_price is the pump multiplier.

Key classes
-----------
PriceTier        – dataclass describing one price tier
PriceTierClassifier – classifies a price into its tier
PumpEvent        – dataclass representing one observed pump event (one training row)
PumpDatasetBuilder – reads/writes pump_events_db.json; filters by condition
"""

from __future__ import annotations

import json
import math
import os
import shutil
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

_DB_LOCK = threading.RLock()


# ══════════════════════════════════════════════════════════════
# 1.  PRICE TIER DEFINITIONS  (8 tiers, log-scale)
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PriceTier:
    tier_index: int          # 1 (cheapest) … 8 (most expensive)
    code: str                # e.g. "ULTRA_MICRO"
    label: str               # human-readable label
    price_min: float         # inclusive lower bound (0 means no lower bound)
    price_max: float         # exclusive upper bound (inf means no upper bound)
    n_expected_low: float    # empirical lower bound for n
    n_expected_high: float   # empirical upper bound for n
    n_median: float          # median expected n (geometric mean of bounds)

    def in_range(self, price: float) -> bool:
        return self.price_min <= price < self.price_max

    def to_dict(self) -> dict:
        return asdict(self)


# Ordered from cheapest to most expensive
PRICE_TIERS: List[PriceTier] = [
    PriceTier(1, "ULTRA_MICRO", "Ultra Micro  (< $0.0001)",   0.0,        0.0001,  50,   500,  158),
    PriceTier(2, "MICRO",       "Micro ($0.0001 – $0.001)",   0.0001,     0.001,   30,   150,   67),
    PriceTier(3, "NANO",        "Nano ($0.001 – $0.01)",      0.001,      0.01,    15,    80,   35),
    PriceTier(4, "SMALL",       "Small ($0.01 – $0.1)",       0.01,       0.1,      8,    40,   18),
    PriceTier(5, "MID",         "Mid ($0.1 – $1)",            0.1,        1.0,      4,    20,    9),
    PriceTier(6, "LARGE",       "Large ($1 – $10)",           1.0,       10.0,      2,    10,  4.5),
    PriceTier(7, "XLARGE",      "XLarge ($10 – $100)",       10.0,      100.0,    1.5,     5,  2.7),
    PriceTier(8, "MEGA",        "Mega (> $100)",             100.0,   1_000_000,  1.2,     3,  1.9),
]


class PriceTierClassifier:
    """Classify a pre-pump price into one of the 8 logarithmic tiers."""

    def classify(self, price: float) -> PriceTier:
        """
        Return the PriceTier that contains `price`.
        Prices <= 0 are clamped to Tier 1.
        Prices > $1 000 000 fall into Tier 8.
        """
        if price <= 0:
            return PRICE_TIERS[0]
        for tier in PRICE_TIERS:
            if tier.in_range(price):
                return tier
        return PRICE_TIERS[-1]   # catch-all for price > $100

    def get_expected_n(self, price: float) -> dict:
        """Return median, low, and high expected-n for a given price."""
        tier = self.classify(price)
        return {
            "tier_code":   tier.code,
            "tier_label":  tier.label,
            "tier_index":  tier.tier_index,
            "n_low":       tier.n_expected_low,
            "n_median":    tier.n_median,
            "n_high":      tier.n_expected_high,
        }


# ══════════════════════════════════════════════════════════════
# 2.  PUMP EVENT DATACLASS  (one training observation)
# ══════════════════════════════════════════════════════════════

@dataclass
class PumpEvent:
    """
    One complete pump observation used as a training row.

    All 'pre_pump_*' fields are measured at the last candle
    *before* the ignition candle (i.e., baseline state).
    All 'pump_*' fields describe the pump itself.
    """
    # ── Identification ──────────────────────────────────────
    symbol:             str                  # e.g. "DEXEUSDT"
    event_date:         str                  # ISO-8601 date "2026-04-15"
    source:             str = "manual"       # "manual" | "auto_scanner" | "api_fetch"

    # ── Pre-pump State ───────────────────────────────────────
    pre_pump_price:     float = 0.0          # USDT price just before pump
    pre_pump_mcap_usd:  float = 0.0          # Estimated market cap (USD) — circulating supply × price
    pre_pump_vol_24h:   float = 0.0          # 24h quote volume (USDT) just before pump
    pre_pump_oi:        float = 0.0          # Open interest (USDT) just before pump (0 if unknown)
    pre_pump_funding:   float = 0.0          # Funding rate just before pump (decimal, e.g. -0.003)

    # ── Price Tier (auto-computed) ───────────────────────────
    price_tier_code:    str = ""             # e.g. "LARGE"
    price_tier_index:   int = 0             # 1–8

    # ── Pump Characteristics ─────────────────────────────────
    peak_price:         float = 0.0          # Absolute peak price reached during pump
    pump_duration_h:    float = 0.0          # Hours from ignition to peak
    pump_vol_total:     float = 0.0          # Total USDT volume *during* the pump
    vol_spike_ratio:    float = 0.0          # pump_vol_total / pre_pump_vol_24h

    # ── Target Variable ──────────────────────────────────────
    n_actual:           float = 0.0          # peak_price / pre_pump_price  (the "n")
    log_n:              float = field(init=False, default=0.0)  # log(n) — computed

    # ── Derived Log-Scale & Derivative Features ─────────────
    log_price:          float = field(init=False, default=0.0)
    log_mcap:           float = field(init=False, default=0.0)
    log_vol_pre:        float = field(init=False, default=0.0)
    log_vol_spike:      float = field(init=False, default=0.0)
    elasticity:         float = field(init=False, default=0.0)
    funding_pressure:   float = field(init=False, default=0.0)

    # ── Notes ────────────────────────────────────────────────
    notes:              str = ""

    def __post_init__(self):
        self._compute_derived()

    def _compute_derived(self):
        """Recompute all derived log-scale fields and tier after raw values are set."""
        # Compute n if not already set but peak_price and pre_pump_price are known
        if self.peak_price > 0 and self.pre_pump_price > 0 and self.n_actual == 0:
            self.n_actual = self.peak_price / self.pre_pump_price

        # Compute log-scale target
        self.log_n = math.log(max(self.n_actual, 1.0001))

        # Compute log-scale features
        self.log_price    = math.log(max(self.pre_pump_price, 1e-12))
        self.log_mcap     = math.log(max(self.pre_pump_mcap_usd, 1.0))
        self.log_vol_pre  = math.log(max(self.pre_pump_vol_24h, 1.0))
        self.log_vol_spike = math.log(max(self.vol_spike_ratio, 0.0001))
        self.elasticity   = self.log_vol_spike / max(self.log_vol_pre - 5.0, 1.0)
        self.funding_pressure = abs(min(self.pre_pump_funding, 0.0)) * max(self.vol_spike_ratio, 1.0)

        # Auto-classify tier if not already set
        if not self.price_tier_code and self.pre_pump_price > 0:
            clf = PriceTierClassifier()
            tier = clf.classify(self.pre_pump_price)
            self.price_tier_code  = tier.code
            self.price_tier_index = tier.tier_index

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PumpEvent":
        """Reconstruct from a dict (e.g., loaded from JSON)."""
        # Only pass known init fields to avoid issues with derived fields
        init_fields = {
            "symbol", "event_date", "source",
            "pre_pump_price", "pre_pump_mcap_usd", "pre_pump_vol_24h",
            "pre_pump_oi", "pre_pump_funding",
            "price_tier_code", "price_tier_index",
            "peak_price", "pump_duration_h", "pump_vol_total", "vol_spike_ratio",
            "n_actual", "notes",
        }
        filtered = {k: v for k, v in d.items() if k in init_fields}
        return cls(**filtered)


# ══════════════════════════════════════════════════════════════
# 3.  PUMP DATASET BUILDER  (JSON flat-file database)
# ══════════════════════════════════════════════════════════════

# Default path relative to project root
_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "pump_events_db.json"
)


class PumpDatasetBuilder:
    """
    Read / write pump events to a JSON flat-file database.

    Usage
    -----
    db = PumpDatasetBuilder()
    events = db.load_all()
    db.add_event(pump_event)
    df = db.to_dataframe()    # returns pandas DataFrame if pandas is installed
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = os.path.abspath(db_path or _DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    # ── I/O ─────────────────────────────────────────────────

    def load_all(self) -> List[PumpEvent]:
        """Load all events from the JSON database with automatic self-healing resilience."""
        with _DB_LOCK:
            if not os.path.exists(self.db_path):
                # Try fallback from .bak if main is missing
                bak_path = f"{self.db_path}.bak"
                if os.path.exists(bak_path):
                    try:
                        shutil.copy2(bak_path, self.db_path)
                    except Exception:
                        pass
                if not os.path.exists(self.db_path):
                    return []

            needs_resave = False
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
            except Exception:
                needs_resave = True
                # Self-healing fallback: extract valid event JSON blocks via regex
                try:
                    import re
                    with open(self.db_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    raw_blocks = re.findall(r'\{\s*"symbol":\s*"[^"]+".*?\n    \}', content, re.DOTALL)
                    recovered = []
                    for b in raw_blocks:
                        try:
                            obj = json.loads(b)
                            if "symbol" in obj and "n_actual" in obj:
                                recovered.append(obj)
                        except Exception:
                            pass
                    raw = {"events": recovered}
                except Exception:
                    raw = {"events": []}

            events = []
            for record in raw.get("events", []):
                try:
                    events.append(PumpEvent.from_dict(record))
                except Exception:
                    pass   # skip malformed records

            if needs_resave and events:
                try:
                    self.save_all(events)
                except Exception:
                    pass

            return events

    def save_all(self, events: List[PumpEvent]) -> None:
        """Overwrite the entire database using thread-safe POSIX/Windows atomic replace."""
        with _DB_LOCK:
            payload = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(events),
                "events": [e.to_dict() for e in events],
            }

            # 1. Maintain last known good backup (.bak)
            bak_path = f"{self.db_path}.bak"
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 100:
                try:
                    shutil.copy2(self.db_path, bak_path)
                except Exception:
                    pass

            # 2. Atomic Temp Write: write, flush, fsync, then atomic replace
            temp_file = f"{self.db_path}.tmp.{os.getpid()}.{time.time_ns()}"
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_file, self.db_path)
            except Exception:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                raise

    def add_event(self, event: PumpEvent, deduplicate: bool = True) -> None:
        """Append a new event thread-safely; optionally skip if same symbol+date already exists."""
        with _DB_LOCK:
            events = self.load_all()
            if deduplicate:
                key = (event.symbol.upper(), event.event_date)
                existing_keys = {(e.symbol.upper(), e.event_date) for e in events}
                if key in existing_keys:
                    return
            events.append(event)
            self.save_all(events)

    def add_events_bulk(self, new_events: List[PumpEvent], deduplicate: bool = True) -> int:
        """Bulk insert thread-safely; returns count of events actually added."""
        with _DB_LOCK:
            events = self.load_all()
            existing_keys = {(e.symbol.upper(), e.event_date) for e in events} if deduplicate else set()
            added = 0
            for ev in new_events:
                if deduplicate:
                    key = (ev.symbol.upper(), ev.event_date)
                    if key in existing_keys:
                        continue
                    existing_keys.add(key)
                events.append(ev)
                added += 1
            if added > 0:
                self.save_all(events)
            return added


    def upsert(self, event: PumpEvent) -> None:
        """Insert or update a single event by (symbol, event_date)."""
        events = self.load_all()
        updated = False
        target_key = (event.symbol.upper(), event.event_date)
        for idx, e in enumerate(events):
            if (e.symbol.upper(), e.event_date) == target_key:
                events[idx] = event
                updated = True
                break
        if not updated:
            events.append(event)
        self.save_all(events)

    # ── Filtering ────────────────────────────────────────────

    def filter(
        self,
        min_n: float = 1.0,
        max_n: float = 10_000.0,
        tier_code: Optional[str] = None,
        symbol: Optional[str] = None,
        since_date: Optional[str] = None,     # "YYYY-MM-DD"
    ) -> List[PumpEvent]:
        """Return filtered subset of events."""
        events = self.load_all()
        result = []
        for e in events:
            if not (min_n <= e.n_actual <= max_n):
                continue
            if tier_code and e.price_tier_code != tier_code:
                continue
            if symbol and e.symbol.upper() != symbol.upper():
                continue
            if since_date and e.event_date < since_date:
                continue
            result.append(e)
        return result

    # ── Summary ──────────────────────────────────────────────

    def summary(self) -> dict:
        """Print a quick summary of the database."""
        events = self.load_all()
        if not events:
            return {"count": 0}
        ns = [e.n_actual for e in events]
        tier_counts: dict = {}
        for e in events:
            tier_counts[e.price_tier_code] = tier_counts.get(e.price_tier_code, 0) + 1
        return {
            "count": len(events),
            "n_min": round(min(ns), 2),
            "n_max": round(max(ns), 2),
            "n_mean": round(sum(ns) / len(ns), 2),
            "by_tier": tier_counts,
        }

    def to_dataframe(self):
        """Return events as a pandas DataFrame (requires pandas)."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_dataframe(). Run: pip install pandas")
        events = self.load_all()
        return pd.DataFrame([e.to_dict() for e in events])
