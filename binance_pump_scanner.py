"""
DeepAlpha — Binance Futures (USDT-M) Pump & Dump Scanner
==========================================================
Scans ALL Binance USDT-M Perpetual contracts every 3 seconds for volume/price anomalies,
rides the pump Long with 7-layer confirmation (including native Taker Buy Ratio & Open Interest),
and shorts the dump after exhaustion.

Features:
- Full support for both Simulation Mode (Paper Trading, no API key needed) and Live/Testnet Trading.
- 7-Layer Detection Engine (Volume Spike, Price Spike, Momentum, RSI, Taker Buy Ratio, Open Interest, Confidence).
- Multi-target Cascade TP (+5%, +10%, +20%) with Trailing Stop and Breakeven SL.
- Dump Short Exhaustion Detection (RSI > 80, Volume decline, Funding extreme, Upper wick rejection).
- New listing detection on Binance Futures.
- Daily Loss Circuit Breaker & Automatic 30m Cooldown per coin.
- Telegram Alerts & JSON Trade Logging.
"""

import json
import logging
import os
import re
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import requests
from binance.client import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("binance_pump_scanner")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Binance Futures Pump Scanner
# ═══════════════════════════════════════════════════════════════════════════

# --- Mode & Credentials ---
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"
INITIAL_SIMULATION_EQUITY = float(os.getenv("INITIAL_SIMULATION_EQUITY", "1000.0"))

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
BINANCE_TESTNET = os.getenv("BINANCE_TESTNET", "false").lower() == "true"

# --- Detection Thresholds ---
SCAN_INTERVAL_SEC = int(os.getenv("PUMP_SCAN_INTERVAL", "3"))
VOLUME_SPIKE_MULT = float(os.getenv("PUMP_VOL_SPIKE_MULT", "5.0"))
PRICE_SPIKE_PCT = float(os.getenv("PUMP_PRICE_SPIKE_PCT", "0.03"))
PRICE_WINDOW_CANDLES = int(os.getenv("PUMP_PRICE_WINDOW", "5"))
MIN_DOLLAR_VOLUME = float(os.getenv("PUMP_MIN_DOLLAR_VOL", "500000"))
MIN_24H_CHANGE_PCT = float(os.getenv("PUMP_MIN_24H_CHANGE_PCT", "5.0"))

# --- Fakeout Filters ---
CONFIRM_CANDLES = int(os.getenv("PUMP_CONFIRM_CANDLES", "3"))
MIN_RSI_ENTRY = float(os.getenv("PUMP_MIN_RSI_ENTRY", "60"))
MAX_RSI_ENTRY = float(os.getenv("PUMP_MAX_RSI_ENTRY", "85"))
MIN_BUY_RATIO = float(os.getenv("PUMP_MIN_BUY_RATIO", "0.65"))
MIN_OI_CONFIRM = os.getenv("PUMP_MIN_OI_CONFIRM", "true").lower() == "true"

# --- Position Management ---
PUMP_LEVERAGE = int(os.getenv("PUMP_LEVERAGE", "5"))
PUMP_RISK_BUDGET_PCT = float(os.getenv("PUMP_RISK_BUDGET_PCT", "0.05"))
PUMP_MAX_POSITIONS = int(os.getenv("PUMP_MAX_POSITIONS", "2"))
MIN_NOTIONAL = float(os.getenv("PUMP_MIN_NOTIONAL", "5.0"))

# --- Take Profit / Stop Loss ---
PUMP_SL_ATR_MULT = float(os.getenv("PUMP_SL_ATR_MULT", "1.5"))
PUMP_TP1_PCT = float(os.getenv("PUMP_TP1_PCT", "0.05"))
PUMP_TP2_PCT = float(os.getenv("PUMP_TP2_PCT", "0.10"))
PUMP_TP3_PCT = float(os.getenv("PUMP_TP3_PCT", "0.20"))
PUMP_TRAILING_PCT = float(os.getenv("PUMP_TRAILING_PCT", "0.03"))
MAX_HOLD_SEC = int(os.getenv("PUMP_MAX_HOLD_SEC", "7200"))

# --- Dump Short Settings ---
SHORT_RSI_THRESHOLD = float(os.getenv("PUMP_SHORT_RSI", "80"))
SHORT_VOL_DECLINE_PCT = float(os.getenv("PUMP_SHORT_VOL_DECLINE", "0.40"))
SHORT_FUNDING_EXTREME = float(os.getenv("PUMP_SHORT_FUNDING", "0.001"))
SHORT_SL_ATR_MULT = float(os.getenv("PUMP_SHORT_SL_ATR", "2.0"))
SHORT_TP_PCT = float(os.getenv("PUMP_SHORT_TP_PCT", "0.05"))

# --- New Listing Detection ---
LISTING_CHECK_INTERVAL = int(os.getenv("PUMP_LISTING_CHECK", "30"))
LISTING_BUY_DELAY_SEC = int(os.getenv("PUMP_LISTING_DELAY", "5"))
LISTING_RISK_PCT = float(os.getenv("PUMP_LISTING_RISK", "0.02"))

# --- Circuit Breaker & Cooldown ---
PUMP_COOLDOWN_SEC = int(os.getenv("PUMP_COOLDOWN_SEC", "1800"))
MAX_DAILY_PUMP_LOSS = float(os.getenv("PUMP_MAX_DAILY_LOSS", "-50.0"))

# --- Telegram Alerts ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PumpSignal:
    """Detected pump event on Binance Futures."""
    symbol: str
    coin: str
    signal_type: str              # "pump_long", "dump_short", "new_listing"
    detected_at: float
    price_at_detection: float
    volume_ratio: float
    rsi: float
    atr: float
    buy_ratio: float
    confidence: float
    metadata: dict = field(default_factory=dict)


@dataclass
class PumpPosition:
    """Active pump position being managed."""
    symbol: str
    coin: str
    side: str                     # "long" or "short"
    entry_price: float
    quantity: float
    original_quantity: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    trailing_active: bool = False
    trailing_extreme: float = 0.0 # highest price for long, lowest for short
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    opened_at: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════
# CORE BINANCE FUTURES SCANNER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class BinancePumpScanner:
    """
    Real-time pump detection and execution engine for Binance Futures (USDT-M).
    """

    def __init__(self, client: Optional[Client] = None, simulation_mode: bool = SIMULATION_MODE):
        self.simulation_mode = simulation_mode
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Initialize Binance Client
        if client is not None:
            self.client = client
        elif self.simulation_mode or not BINANCE_API_KEY or not BINANCE_API_SECRET:
            logger.info("Operating in SIMULATION MODE (Paper Trading)")
            self.client = Client()
            self.simulation_mode = True
        else:
            logger.info(f"Connecting to Binance Futures API (Testnet={BINANCE_TESTNET})...")
            self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=BINANCE_TESTNET)

        # Simulation equity
        self._simulated_equity = INITIAL_SIMULATION_EQUITY

        # Symbol precision and filter limits
        self._symbol_precisions: dict[str, dict] = {}
        self._all_symbols: list[str] = []

        # State tracking
        self.price_history: dict[str, list[float]] = defaultdict(list)
        self.pump_positions: dict[str, PumpPosition] = {}
        self.cooldowns: dict[str, float] = {}
        self.known_symbols: set[str] = set()
        self._daily_pump_pnl: float = 0.0
        self._daily_pump_pnl_date: str = ""

        # Pending new listing
        self._pending_listing: Optional[dict] = None

        # Blacklist of stock/pre-market tokens
        self._blacklist = {
            'TSLA', 'TSM', 'INTC', 'HOOD', 'AAPL', 'AMZN', 'GOOG', 'GOOGL',
            'MSFT', 'NVDA', 'META', 'NFLX', 'AMD', 'COIN', 'MSTR', 'PLTR',
        }

        # Persistent seen listings
        self._seen_listings_file = os.path.join(os.path.dirname(__file__), "binance_seen_listings.json")
        self._seen_listings: set[str] = set()
        try:
            with open(self._seen_listings_file, "r") as f:
                self._seen_listings = set(json.load(f))
        except Exception:
            pass

    # ─── Lifecycle ──────────────────────────────────────────────────────

    def start(self):
        """Start the scanner background thread."""
        if self._running:
            logger.warning("BinancePumpScanner is already running")
            return
        self._running = True
        self._load_exchange_info()
        self._thread = threading.Thread(target=self._main_loop, daemon=True, name="BinancePumpScanner")
        self._thread.start()

        mode_str = "SIMULATION (Paper Trading)" if self.simulation_mode else "LIVE TRADING"
        msg = f"BINANCE FUTURES PUMP SCANNER STARTED [{mode_str}] — Monitoring {len(self._all_symbols)} USDT-M pairs"
        logger.info(msg)
        self._alert(msg)

    def stop(self):
        """Stop the scanner."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("BinancePumpScanner stopped")

    # ─── Exchange Info & Symbol Discovery ──────────────────────────────

    def _load_exchange_info(self):
        """Load all active USDT-M Perpetual contracts and precision rules."""
        try:
            info = self.client.futures_exchange_info()
            symbols = []
            precisions = {}

            for s in info.get("symbols", []):
                sym = s["symbol"]
                if (s.get("quoteAsset") == "USDT" and
                    s.get("status") == "TRADING" and
                    s.get("contractType") == "PERPETUAL"):
                    
                    coin = s.get("baseAsset", sym.replace("USDT", ""))
                    if coin in self._blacklist:
                        continue

                    symbols.append(sym)

                    # Extract precision and step size filters
                    qty_precision = int(s.get("quantityPrecision", 4))
                    price_precision = int(s.get("pricePrecision", 4))
                    min_qty = 0.0
                    step_size = 10 ** (-qty_precision)

                    for f in s.get("filters", []):
                        if f.get("filterType") == "LOT_SIZE":
                            min_qty = float(f.get("minQty", 0))
                            step_size = float(f.get("stepSize", step_size))

                    precisions[sym] = {
                        "qty_precision": qty_precision,
                        "price_precision": price_precision,
                        "min_qty": min_qty,
                        "step_size": step_size,
                        "base_asset": coin,
                    }

            with self._lock:
                self._all_symbols = symbols
                self._symbol_precisions = precisions
                self.known_symbols = set(symbols)
                # Seed seen listings with all currently known symbols to avoid false alerts on startup
                for sym in symbols:
                    coin = sym.replace("USDT", "")
                    self._seen_listings.add(coin)

            logger.info(f"Loaded {len(symbols)} active Binance USDT-M Perpetual pairs")
        except Exception as e:
            logger.error(f"Failed to load exchange info: {e}")

    # ─── Main Scanning Loop ─────────────────────────────────────────────

    def _main_loop(self):
        """Main scanner loop executed every SCAN_INTERVAL_SEC."""
        listing_check_last = 0

        while self._running:
            try:
                loop_start = time.time()

                # 1. Reset daily PnL at midnight UTC
                self._maybe_reset_daily_pnl()

                # 2. Check for new listings periodically
                if time.time() - listing_check_last > LISTING_CHECK_INTERVAL:
                    self._check_new_listings()
                    listing_check_last = time.time()

                # 3. Handle pending new listing order execution
                if self._pending_listing and time.time() >= self._pending_listing["time"]:
                    sym = self._pending_listing["symbol"]
                    self._pending_listing = None
                    self._execute_listing_buy(sym)

                # 4. Fast bulk scan across all 700+ tickers in 1 API call
                tickers = self._fetch_all_tickers()
                if not tickers:
                    time.sleep(SCAN_INTERVAL_SEC)
                    continue

                # 5. Scan for pump anomalies
                signals = self._scan_for_pumps(tickers)

                # 6. Execute confirmed signals
                for signal in signals:
                    self._execute_signal(signal)

                # 7. Manage open positions (TP/SL/Trailing)
                self._manage_positions(tickers)

                # 8. Sleep remainder of interval
                elapsed = time.time() - loop_start
                sleep_time = max(0.1, SCAN_INTERVAL_SEC - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(3)

    def _maybe_reset_daily_pnl(self):
        """Reset daily PnL counter at midnight UTC."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._daily_pump_pnl_date != today:
            if self._daily_pump_pnl_date:
                logger.info(f"Daily PnL reset (Previous: ${self._daily_pump_pnl:.2f})")
            self._daily_pump_pnl = 0.0
            self._daily_pump_pnl_date = today

    # ─── Data Fetching & Detection ──────────────────────────────────────

    def _fetch_all_tickers(self) -> dict[str, dict]:
        """Fetch 24h tickers for all contracts in 1 request."""
        try:
            raw_tickers = self.client.futures_ticker()
            tickers = {}
            for t in raw_tickers:
                sym = t.get("symbol")
                if sym in self._symbol_precisions:
                    tickers[sym] = {
                        "last": float(t.get("lastPrice", 0)),
                        "pct_change": float(t.get("priceChangePercent", 0)),
                        "quote_vol": float(t.get("quoteVolume", 0)),
                    }
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch 24h tickers: {e}")
            return {}

    def _scan_for_pumps(self, tickers: dict[str, dict]) -> list[PumpSignal]:
        """Scan tickers and validate potential pump/dump signals."""
        signals: list[PumpSignal] = []
        now = time.time()

        for sym, t in tickers.items():
            coin = self._symbol_precisions[sym]["base_asset"]

            with self._lock:
                if sym in self.cooldowns and now < self.cooldowns[sym]:
                    continue
                if sym in self.pump_positions:
                    continue

            last_price = t["last"]
            quote_vol = t["quote_vol"]
            pct_change = t["pct_change"]

            # Pre-filter: liquidity & activity
            if last_price <= 0 or quote_vol < MIN_DOLLAR_VOLUME:
                continue

            # Update rolling price history
            self.price_history[sym].append(last_price)
            if len(self.price_history[sym]) > 100:
                self.price_history[sym] = self.price_history[sym][-100:]

            # Fast filter: only examine candle details for active movers
            if abs(pct_change) < MIN_24H_CHANGE_PCT:
                continue

            try:
                # Fetch 30 1m candles
                klines = self.client.futures_klines(symbol=sym, interval="1m", limit=30)
                if not klines or len(klines) < 20:
                    continue

                closes = np.array([float(k[4]) for k in klines])
                opens = np.array([float(k[1]) for k in klines])
                highs = np.array([float(k[2]) for k in klines])
                lows = np.array([float(k[3]) for k in klines])
                volumes = np.array([float(k[5]) for k in klines])
                taker_buy_base = np.array([float(k[9]) for k in klines])

                last_vol = volumes[-1]
                prev_avg_vol = np.mean(volumes[-20:-1])
                volume_ratio = last_vol / max(prev_avg_vol, 1e-9)

                # Price change over window (5m)
                price_change = (closes[-1] - closes[-PRICE_WINDOW_CANDLES]) / closes[-PRICE_WINDOW_CANDLES]

                # ── PRIMARY PUMP DETECTION (Volume Spike + Price Spike) ──
                if volume_ratio >= VOLUME_SPIKE_MULT and price_change >= PRICE_SPIKE_PCT:
                    signal = self._validate_pump(sym, coin, closes, opens, highs, lows, volumes, taker_buy_base, volume_ratio, price_change)
                    if signal:
                        signals.append(signal)

                # ── DUMP SHORT DETECTION (Pump Exhaustion) ──
                elif volume_ratio >= (VOLUME_SPIKE_MULT * 0.4) and len(closes) >= 20:
                    signal = self._check_dump_short(sym, coin, closes, opens, highs, lows, volumes, volume_ratio)
                    if signal:
                        signals.append(signal)

            except Exception as e:
                logger.debug(f"Scan check failed for {sym}: {e}")
                continue

        return signals

    def _validate_pump(self, sym: str, coin: str, closes: np.ndarray, opens: np.ndarray,
                       highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray,
                       taker_buy_base: np.ndarray, volume_ratio: float, price_change: float) -> Optional[PumpSignal]:
        """Validate pump signal with 7 confirmation layers."""
        try:
            # 1. Consecutive green candles check
            green_count = sum(1 for i in range(-1, -CONFIRM_CANDLES - 1, -1) if closes[i] > opens[i])
            if green_count < CONFIRM_CANDLES:
                return None

            # 2. RSI (14)
            rsi = self._calc_rsi(closes, period=14)
            if rsi < MIN_RSI_ENTRY or rsi > MAX_RSI_ENTRY:
                return None

            # 3. Exact Taker Buy Ratio (Last 5 candles)
            recent_buy = np.sum(taker_buy_base[-5:])
            recent_tot = np.sum(volumes[-5:])
            buy_ratio = recent_buy / max(recent_tot, 1e-9)
            if buy_ratio < MIN_BUY_RATIO:
                return None

            # 4. Open Interest Confirmation (Check if fresh money enters)
            oi_change = 0.0
            if MIN_OI_CONFIRM:
                try:
                    oi_hist = self.client.futures_open_interest_hist(symbol=sym, period="5m", limit=3)
                    if len(oi_hist) >= 2:
                        oi_curr = float(oi_hist[-1].get("sumOpenInterest", 0))
                        oi_prev = float(oi_hist[-2].get("sumOpenInterest", 0))
                        if oi_prev > 0:
                            oi_change = (oi_curr - oi_prev) / oi_prev
                except Exception:
                    pass

            # 5. ATR (14)
            atr = self._calc_atr(highs, lows, closes, period=14)

            # 6. Composite Confidence Score (0.0 to 1.0)
            conf_vol = min(volume_ratio / (VOLUME_SPIKE_MULT * 2), 1.0)
            conf_price = min(price_change / (PRICE_SPIKE_PCT * 3), 1.0)
            conf_rsi = max(0.0, 1.0 - abs(rsi - 70) / 30)
            conf_buy = min(buy_ratio / 0.85, 1.0)
            conf_oi = 1.0 if oi_change > 0 else 0.5

            confidence = (conf_vol * 0.25 + conf_price * 0.25 + conf_rsi * 0.2 + conf_buy * 0.2 + conf_oi * 0.1)
            if confidence < 0.50:
                return None

            logger.info(
                f"PUMP DETECTED: {sym} | Vol: {volume_ratio:.1f}x | "
                f"+{price_change*100:.1f}% in 5m | RSI: {rsi:.0f} | "
                f"BuyRatio: {buy_ratio:.0%} | Conf: {confidence:.2f}"
            )

            return PumpSignal(
                symbol=sym,
                coin=coin,
                signal_type="pump_long",
                detected_at=time.time(),
                price_at_detection=closes[-1],
                volume_ratio=volume_ratio,
                rsi=rsi,
                atr=atr,
                buy_ratio=buy_ratio,
                confidence=confidence,
                metadata={
                    "price_change": price_change,
                    "oi_change": oi_change,
                    "green_candles": green_count,
                },
            )
        except Exception as e:
            logger.error(f"Pump validation error for {sym}: {e}")
            return None

    def _check_dump_short(self, sym: str, coin: str, closes: np.ndarray, opens: np.ndarray,
                          highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray,
                          volume_ratio: float) -> Optional[PumpSignal]:
        """Detect pump exhaustion to enter a short position."""
        try:
            # 1. RSI must be overbought
            rsi = self._calc_rsi(closes, period=14)
            if rsi < SHORT_RSI_THRESHOLD:
                return None

            # 2. Volume decline from peak
            recent_vol = np.mean(volumes[-5:])
            peak_vol = np.max([np.mean(volumes[i:i+5]) for i in range(len(volumes)-10, len(volumes)-5)])
            vol_decline = 1.0 - (recent_vol / max(peak_vol, 1e-9))
            if vol_decline < SHORT_VOL_DECLINE_PCT:
                return None

            # 3. Funding rate
            funding = 0.0
            try:
                fr_data = self.client.futures_funding_rate(symbol=sym, limit=1)
                if fr_data:
                    funding = float(fr_data[0].get("fundingRate", 0))
            except Exception:
                pass

            # 4. Upper wick ratio (Rejection from top)
            wick_scores = []
            for i in range(-3, 0):
                upper_wick = highs[i] - max(closes[i], opens[i])
                tot_range = highs[i] - lows[i]
                if tot_range > 0:
                    wick_scores.append(upper_wick / tot_range)
            avg_wick = np.mean(wick_scores) if wick_scores else 0.0

            # Confidence score
            score_rsi = min((rsi - 75) / 25, 1.0)
            score_vol = min(vol_decline / 0.6, 1.0)
            score_funding = min(abs(funding) / SHORT_FUNDING_EXTREME, 1.0) if funding > 0 else 0.2
            score_wick = min(avg_wick / 0.4, 1.0)

            confidence = (score_rsi * 0.3 + score_vol * 0.3 + score_funding * 0.2 + score_wick * 0.2)
            if confidence < 0.50:
                return None

            atr = self._calc_atr(highs, lows, closes, period=14)

            logger.info(
                f"DUMP SHORT SIGNAL: {sym} | RSI: {rsi:.0f} | "
                f"VolDecline: {vol_decline:.0%} | Funding: {funding:.4%} | "
                f"WickRatio: {avg_wick:.2f} | Conf: {confidence:.2f}"
            )

            return PumpSignal(
                symbol=sym,
                coin=coin,
                signal_type="dump_short",
                detected_at=time.time(),
                price_at_detection=closes[-1],
                volume_ratio=volume_ratio,
                rsi=rsi,
                atr=atr,
                buy_ratio=0.0,
                confidence=confidence,
                metadata={
                    "vol_decline": vol_decline,
                    "funding": funding,
                    "avg_wick": avg_wick,
                },
            )
        except Exception as e:
            logger.error(f"Dump short check error for {sym}: {e}")
            return None

    # ─── Trade Execution & Sizing ───────────────────────────────────────

    def _execute_signal(self, signal: PumpSignal):
        """Execute or simulate a pump / dump signal."""
        with self._lock:
            if len(self.pump_positions) >= PUMP_MAX_POSITIONS:
                return

        # Daily loss circuit breaker
        if self._daily_pump_pnl <= MAX_DAILY_PUMP_LOSS:
            logger.warning(f"Daily loss limit reached (${self._daily_pump_pnl:.2f}), skipping {signal.symbol}")
            return

        equity = self._get_equity()
        if equity <= 0:
            return

        try:
            if signal.signal_type == "pump_long":
                self._open_position(signal, equity, side="long")
            elif signal.signal_type == "dump_short":
                self._open_position(signal, equity, side="short")
            elif signal.signal_type == "new_listing":
                self._open_position(signal, equity, side="long", is_listing=True)
        except Exception as e:
            logger.error(f"Failed to execute signal for {signal.symbol}: {e}")
            with self._lock:
                self.cooldowns[signal.symbol] = time.time() + 300

    def _open_position(self, signal: PumpSignal, equity: float, side: str, is_listing: bool = False):
        """Open a position (Live or Simulated)."""
        sym = signal.symbol
        price = signal.price_at_detection
        atr = signal.atr if signal.atr > 0 else price * 0.02

        risk_frac = LISTING_RISK_PCT if is_listing else (PUMP_RISK_BUDGET_PCT * signal.confidence)
        if side == "short":
            risk_frac *= 0.7  # Smaller risk budget for counter-trend shorts

        notional = equity * risk_frac * PUMP_LEVERAGE
        if notional < MIN_NOTIONAL:
            return

        raw_qty = notional / price
        qty = self._round_qty(sym, raw_qty)
        if qty <= 0:
            return

        # Execute Live or Simulated
        fill_price = price
        if not self.simulation_mode:
            try:
                # Set leverage on Binance Futures
                self.client.futures_change_leverage(symbol=sym, leverage=PUMP_LEVERAGE)
                order_side = "BUY" if side == "long" else "SELL"
                order = self.client.futures_create_order(
                    symbol=sym,
                    side=order_side,
                    type="MARKET",
                    quantity=qty
                )
                fill_price = float(order.get("avgPrice", price) or price)
            except Exception as e:
                logger.error(f"Live order failed for {sym}: {e}")
                return

        # Calculate TP / SL levels
        if side == "long":
            sl = fill_price - (atr * PUMP_SL_ATR_MULT)
            tp1 = fill_price * (1.0 + PUMP_TP1_PCT)
            tp2 = fill_price * (1.0 + PUMP_TP2_PCT)
            tp3 = fill_price * (1.0 + PUMP_TP3_PCT)
        else:
            sl = fill_price + (atr * SHORT_SL_ATR_MULT)
            tp1 = fill_price * (1.0 - SHORT_TP_PCT * 0.5)
            tp2 = fill_price * (1.0 - SHORT_TP_PCT)
            tp3 = fill_price * (1.0 - SHORT_TP_PCT * 1.5)

        pos = PumpPosition(
            symbol=sym,
            coin=signal.coin,
            side=side,
            entry_price=fill_price,
            quantity=qty,
            original_quantity=qty,
            stop_loss=sl,
            tp1=tp1,
            tp2=tp2,
            tp3=tp3,
            trailing_extreme=fill_price,
            opened_at=time.time(),
        )

        with self._lock:
            self.pump_positions[sym] = pos

        mode_tag = "[SIMULATION]" if self.simulation_mode else "[LIVE]"
        msg = (
            f"{mode_tag} {side.upper()} OPENED: {sym}\n"
            f"Entry: ${fill_price:.4f} | Qty: {qty}\n"
            f"SL: ${sl:.4f} | TP1: ${tp1:.4f} | TP2: ${tp2:.4f} | TP3: ${tp3:.4f}\n"
            f"Notional: ${notional:.1f} | Lev: {PUMP_LEVERAGE}x | Conf: {signal.confidence:.0%}"
        )
        logger.info(msg)
        self._alert(msg)

    # ─── Position Management & Multi-target Cascade TP ─────────────────

    def _manage_positions(self, tickers: dict[str, dict]):
        """Monitor active positions for SL, TP cascade, and trailing stop."""
        with self._lock:
            positions_snapshot = list(self.pump_positions.items())

        for sym, pos in positions_snapshot:
            t = tickers.get(sym)
            if not t:
                continue

            current_price = t["last"]
            if current_price <= 0:
                continue

            is_long = pos.side == "long"

            # 1. Stop Loss check
            if (is_long and current_price <= pos.stop_loss) or (not is_long and current_price >= pos.stop_loss):
                self._close_position(sym, "SL HIT", current_price)
                continue

            # 2. Time-based exit (Max 2 hours)
            if time.time() - pos.opened_at > MAX_HOLD_SEC:
                self._close_position(sym, "TIME EXIT (2h)", current_price)
                continue

            # 3. Cascade TP (Long)
            if is_long:
                # TP1: Close 40% + Move SL to Breakeven
                if not pos.tp1_hit and current_price >= pos.tp1:
                    close_qty = self._round_qty(sym, pos.original_quantity * 0.4)
                    close_qty = min(close_qty, pos.quantity)
                    if close_qty > 0:
                        self._partial_close(sym, close_qty, "TP1 (+5%)", "SELL")
                        pos.quantity = max(0.0, pos.quantity - close_qty)
                        pos.tp1_hit = True
                        pos.stop_loss = pos.entry_price * 1.002  # Breakeven + 0.2%

                # TP2: Close 30% + Activate Trailing Stop
                if not pos.tp2_hit and pos.tp1_hit and current_price >= pos.tp2:
                    close_qty = self._round_qty(sym, pos.original_quantity * 0.3)
                    close_qty = min(close_qty, pos.quantity)
                    if close_qty > 0:
                        self._partial_close(sym, close_qty, "TP2 (+10%)", "SELL")
                        pos.quantity = max(0.0, pos.quantity - close_qty)
                        pos.tp2_hit = True
                        pos.trailing_active = True
                        pos.trailing_extreme = current_price

                # TP3: Close remaining 30%
                if not pos.tp3_hit and pos.tp2_hit and current_price >= pos.tp3:
                    pos.tp3_hit = True
                    self._close_position(sym, "TP3 (+20%)", current_price)
                    continue

                # Trailing stop execution
                if pos.trailing_active:
                    if current_price > pos.trailing_extreme:
                        pos.trailing_extreme = current_price
                    trailing_sl = pos.trailing_extreme * (1.0 - PUMP_TRAILING_PCT)
                    if current_price <= trailing_sl:
                        self._close_position(sym, "TRAILING STOP", current_price)
                        continue

            # 4. Cascade TP (Short)
            else:
                if not pos.tp1_hit and current_price <= pos.tp1:
                    close_qty = self._round_qty(sym, pos.original_quantity * 0.4)
                    close_qty = min(close_qty, pos.quantity)
                    if close_qty > 0:
                        self._partial_close(sym, close_qty, "TP1 (Short)", "BUY")
                        pos.quantity = max(0.0, pos.quantity - close_qty)
                        pos.tp1_hit = True
                        pos.stop_loss = pos.entry_price * 0.998

                if not pos.tp2_hit and pos.tp1_hit and current_price <= pos.tp2:
                    close_qty = self._round_qty(sym, pos.original_quantity * 0.3)
                    close_qty = min(close_qty, pos.quantity)
                    if close_qty > 0:
                        self._partial_close(sym, close_qty, "TP2 (Short)", "BUY")
                        pos.quantity = max(0.0, pos.quantity - close_qty)
                        pos.tp2_hit = True
                        pos.trailing_active = True
                        pos.trailing_extreme = current_price

                if not pos.tp3_hit and pos.tp2_hit and current_price <= pos.tp3:
                    pos.tp3_hit = True
                    self._close_position(sym, "TP3 (Short)", current_price)
                    continue

                if pos.trailing_active:
                    if current_price < pos.trailing_extreme:
                        pos.trailing_extreme = current_price
                    trailing_sl = pos.trailing_extreme * (1.0 + PUMP_TRAILING_PCT)
                    if current_price >= trailing_sl:
                        self._close_position(sym, "TRAILING STOP (Short)", current_price)
                        continue

    def _partial_close(self, sym: str, qty: float, reason: str, side: str):
        """Execute or simulate a partial close."""
        if not self.simulation_mode:
            try:
                self.client.futures_create_order(
                    symbol=sym,
                    side=side,
                    type="MARKET",
                    quantity=qty
                )
            except Exception as e:
                logger.error(f"Live partial close failed for {sym}: {e}")
        
        mode_tag = "[SIMULATION]" if self.simulation_mode else "[LIVE]"
        msg = f"{mode_tag} {sym} {reason}: Partial close {qty} contracts"
        logger.info(msg)
        self._alert(msg)

    def _close_position(self, sym: str, reason: str, exit_price: float):
        """Fully close position, calculate PnL, log trade, and set cooldown."""
        with self._lock:
            pos = self.pump_positions.get(sym)
        if not pos:
            return

        if not self.simulation_mode and pos.quantity > 0:
            try:
                side = "SELL" if pos.side == "long" else "BUY"
                qty = self._round_qty(sym, pos.quantity)
                if qty > 0:
                    self.client.futures_create_order(
                        symbol=sym,
                        side=side,
                        type="MARKET",
                        quantity=qty
                    )
            except Exception as e:
                logger.error(f"Live full close failed for {sym}: {e}")

        # Calculate PnL
        if pos.side == "long":
            pnl = (exit_price - pos.entry_price) * pos.original_quantity
            pnl_pct = (exit_price / pos.entry_price - 1.0) * 100.0 * PUMP_LEVERAGE
        else:
            pnl = (pos.entry_price - exit_price) * pos.original_quantity
            pnl_pct = (1.0 - exit_price / pos.entry_price) * 100.0 * PUMP_LEVERAGE

        self._daily_pump_pnl += pnl
        if self.simulation_mode:
            self._simulated_equity += pnl

        duration_min = (time.time() - pos.opened_at) / 60.0
        mode_tag = "[SIMULATION]" if self.simulation_mode else "[LIVE]"

        msg = (
            f"{mode_tag} POSITION CLOSED: {sym} ({pos.side.upper()}) | {reason}\n"
            f"Entry: ${pos.entry_price:.4f} -> Exit: ${exit_price:.4f}\n"
            f"PnL: ${pnl:+.2f} ({pnl_pct:+.1f}%) | Duration: {duration_min:.1f}m\n"
            f"Daily PnL: ${self._daily_pump_pnl:.2f} | Equity: ${self._get_equity():.2f}"
        )
        logger.info(msg)
        self._alert(msg)

        # Save trade record to JSON
        self._save_trade_record({
            "symbol": sym,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "exit_price": exit_price,
            "quantity": pos.original_quantity,
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 1),
            "reason": reason,
            "duration_min": round(duration_min, 1),
            "is_simulation": self.simulation_mode,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        })

        # Remove from active positions & add cooldown
        with self._lock:
            self.pump_positions.pop(sym, None)
            self.cooldowns[sym] = time.time() + PUMP_COOLDOWN_SEC

    def _save_trade_record(self, record: dict):
        """Append trade record to binance_pump_trades.json."""
        try:
            log_path = os.path.join(os.path.dirname(__file__), "binance_pump_trades.json")
            trades = []
            try:
                with open(log_path, "r") as f:
                    trades = json.load(f)
            except Exception:
                trades = []
            trades.append(record)
            if len(trades) > 300:
                trades = trades[-300:]
            with open(log_path, "w") as f:
                json.dump(trades, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save trade record: {e}")

    # ─── New Listing Detection ──────────────────────────────────────────

    def _check_new_listings(self):
        """Check for newly listed Binance USDT-M Perpetual contracts."""
        try:
            info = self.client.futures_exchange_info()
            current_symbols = {
                s["symbol"] for s in info.get("symbols", [])
                if s.get("quoteAsset") == "USDT" 
                and s.get("status") == "TRADING"
                and s.get("contractType") == "PERPETUAL"
            }

            with self._lock:
                new_symbols = current_symbols - self.known_symbols

            for sym in new_symbols:
                coin = sym.replace("USDT", "")
                if coin in self._blacklist or coin in self._seen_listings:
                    continue

                self._seen_listings.add(coin)
                try:
                    with open(self._seen_listings_file, "w") as f:
                        json.dump(list(self._seen_listings), f)
                except Exception:
                    pass

                logger.info(f"NEW LISTING DETECTED: {sym} — Preparing order in {LISTING_BUY_DELAY_SEC}s")
                self._alert(f"NEW LISTING DETECTED: {sym} — Preparing order in {LISTING_BUY_DELAY_SEC}s")

                self._pending_listing = {
                    "symbol": sym,
                    "time": time.time() + LISTING_BUY_DELAY_SEC,
                }

            with self._lock:
                self.known_symbols = current_symbols
                self._all_symbols = list(current_symbols)

        except Exception as e:
            logger.debug(f"New listing check error: {e}")

    def _execute_listing_buy(self, sym: str):
        """Execute buy on new listing after stabilization delay."""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=sym)
            price = float(ticker.get("price", 0))
            if price <= 0:
                return

            coin = sym.replace("USDT", "")
            signal = PumpSignal(
                symbol=sym,
                coin=coin,
                signal_type="new_listing",
                detected_at=time.time(),
                price_at_detection=price,
                volume_ratio=0.0,
                rsi=50.0,
                atr=price * 0.03,
                buy_ratio=0.7,
                confidence=0.75,
                metadata={"source": "new_listing"},
            )
            self._execute_signal(signal)
        except Exception as e:
            logger.error(f"Failed to execute new listing buy for {sym}: {e}")

    # ─── Technical Indicators ───────────────────────────────────────────

    @staticmethod
    def _calc_rsi(closes: np.ndarray, period: int = 14) -> float:
        """Calculate 14-period RSI."""
        if len(closes) < period + 1:
            return 50.0
        deltas = np.diff(closes[-(period + 1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100.0 - (100.0 / (1.0 + rs)))

    @staticmethod
    def _calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """Calculate 14-period Average True Range (ATR)."""
        if len(highs) < period + 1:
            return 0.0
        trs = [
            max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
            for i in range(-period, 0)
        ]
        return float(np.mean(trs))

    # ─── Utilities ──────────────────────────────────────────────────────

    def _get_equity(self) -> float:
        """Return available equity (Simulated or Real)."""
        if self.simulation_mode:
            return self._simulated_equity
        try:
            bal = self.client.futures_account_balance()
            for b in bal:
                if b.get("asset") == "USDT":
                    return float(b.get("balance", 0))
            return 0.0
        except Exception:
            return 0.0

    def _round_qty(self, sym: str, qty: float) -> float:
        """Round quantity to contract precision and step size."""
        prec_info = self._symbol_precisions.get(sym)
        if not prec_info:
            return round(qty, 3)
        precision = prec_info.get("qty_precision", 3)
        step_size = prec_info.get("step_size", 0.001)
        min_qty = prec_info.get("min_qty", 0.0)

        # Round down to nearest step size
        qty = np.floor(qty / step_size) * step_size
        qty = round(qty, precision)
        return qty if qty >= min_qty else 0.0

    def _alert(self, message: str):
        """Send Telegram alert."""
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                requests.post(
                    url,
                    json={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "text": f"[BINANCE PUMP SCANNER]\n{message}",
                        "parse_mode": "HTML",
                    },
                    timeout=5
                )
            except Exception:
                pass

    def get_status(self) -> dict:
        """Get live scanner status summary."""
        with self._lock:
            return {
                "running": self._running,
                "mode": "Simulation" if self.simulation_mode else "Live",
                "equity": self._get_equity(),
                "symbols_monitored": len(self._all_symbols),
                "active_positions": len(self.pump_positions),
                "daily_pnl": self._daily_pump_pnl,
                "active_cooldowns": sum(1 for t in self.cooldowns.values() if t > time.time()),
            }


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    # Reconfigure stdout for unicode safety
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("""
============================================================
  DeepAlpha — Binance Futures (USDT-M) Pump Scanner
  Real-time Pump & Dump Detection / Auto-Trading Engine
============================================================
    """)

    scanner = BinancePumpScanner()
    scanner.start()

    try:
        while True:
            time.sleep(30)
            status = scanner.get_status()
            logger.info(
                f"[STATUS] Mode: {status['mode']} | Equity: ${status['equity']:.2f} | "
                f"Active Pos: {status['active_positions']}/{PUMP_MAX_POSITIONS} | "
                f"Daily PnL: ${status['daily_pnl']:+.2f} | Cooldowns: {status['active_cooldowns']}"
            )
    except KeyboardInterrupt:
        print("\nStopping scanner...")
        scanner.stop()
