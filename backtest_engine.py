"""
Backtest Engine for Binance Futures (USDT-M) Pump & Dump Strategy
==================================================================
Simulates author's exact 7-layer pump detection and 3-stage cascade TP strategy
on historical 1m candlestick data.
"""

import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from binance.client import Client


class CascadeBacktestEngine:
    def __init__(self, client: Client = None):
        self.client = client or Client()

    def run_backtest(
        self,
        symbol: str = "BTCUSDT",
        days: int = 7,
        initial_balance: float = 1000.0,
        leverage: int = 5,
        risk_budget_pct: float = 0.05,
        vol_spike_mult: float = 5.0,
        price_spike_pct: float = 0.03,
        tp1_pct: float = 0.05,
        tp2_pct: float = 0.10,
        tp3_pct: float = 0.20,
        trailing_pct: float = 0.03,
        sl_atr_mult: float = 1.5,
        max_hold_candles: int = 120,  # 2 hours in 1m candles
        cooldown_candles: int = 30,   # 30 min cooldown
    ) -> dict:
        symbol = symbol.strip().upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"

        start_str = f"{days} days ago UTC"
        raw_klines = self.client.futures_historical_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1MINUTE,
            start_str=start_str
        )

        if not raw_klines or len(raw_klines) < 60:
            return {"error": f"Không đủ dữ liệu nến 1m lịch sử cho {symbol}"}

        # Convert to numpy arrays for high-speed vector/loop operations
        times = [k[0] // 1000 for k in raw_klines]
        opens = np.array([float(k[1]) for k in raw_klines])
        highs = np.array([float(k[2]) for k in raw_klines])
        lows = np.array([float(k[3]) for k in raw_klines])
        closes = np.array([float(k[4]) for k in raw_klines])
        volumes = np.array([float(k[5]) for k in raw_klines])
        taker_buys = np.array([float(k[9]) for k in raw_klines])

        n_candles = len(closes)
        balance = initial_balance
        equity_curve = [balance]
        trades = []

        cooldown_until = 0
        in_position = False
        pos_entry = 0.0
        pos_qty = 0.0
        pos_orig_qty = 0.0
        pos_open_idx = 0
        pos_sl = 0.0
        pos_tp1 = 0.0
        pos_tp2 = 0.0
        pos_tp3 = 0.0
        pos_tp1_hit = False
        pos_tp2_hit = False
        pos_tp3_hit = False
        pos_trailing_active = False
        pos_trailing_high = 0.0

        for i in range(25, n_candles - 1):
            curr_price = closes[i]

            # ── 1. Quản lý vị thế đang mở ──
            if in_position:
                hold_duration = i - pos_open_idx
                exit_price = None
                exit_reason = None

                # Check Stop Loss
                if lows[i] <= pos_sl:
                    exit_price = pos_sl
                    exit_reason = "STOP_LOSS"
                # Check Max Hold Time (2 hours)
                elif hold_duration >= max_hold_candles:
                    exit_price = curr_price
                    exit_reason = "TIME_EXIT_2H"
                else:
                    # Check TP1 (+5% -> close 40% + breakeven SL)
                    if not pos_tp1_hit and highs[i] >= pos_tp1:
                        pos_tp1_hit = True
                        close_part_qty = pos_orig_qty * 0.4
                        pnl_part = (pos_tp1 - pos_entry) * close_part_qty
                        balance += pnl_part
                        pos_qty -= close_part_qty
                        pos_sl = pos_entry * 1.002  # Move SL to breakeven + 0.2%

                    # Check TP2 (+10% -> close 30% + activate trailing stop)
                    if not pos_tp2_hit and pos_tp1_hit and highs[i] >= pos_tp2:
                        pos_tp2_hit = True
                        close_part_qty = pos_orig_qty * 0.3
                        pnl_part = (pos_tp2 - pos_entry) * close_part_qty
                        balance += pnl_part
                        pos_qty -= close_part_qty
                        pos_trailing_active = True
                        pos_trailing_high = highs[i]

                    # Check TP3 (+20% -> close remaining 30%)
                    if not pos_tp3_hit and pos_tp2_hit and highs[i] >= pos_tp3:
                        pos_tp3_hit = True
                        exit_price = pos_tp3
                        exit_reason = "TP3_TARGET"

                    # Check Trailing Stop
                    if pos_trailing_active:
                        if highs[i] > pos_trailing_high:
                            pos_trailing_high = highs[i]
                        trailing_sl = pos_trailing_high * (1.0 - trailing_pct)
                        if lows[i] <= trailing_sl:
                            exit_price = trailing_sl
                            exit_reason = "TRAILING_STOP"

                # Execute Full Close
                if exit_price is not None:
                    pnl_remaining = (exit_price - pos_entry) * pos_qty
                    balance += pnl_remaining
                    total_pnl = balance - (equity_curve[-1])
                    total_pnl_pct = (exit_price / pos_entry - 1.0) * 100.0 * leverage

                    trades.append({
                        "entry_time": datetime.fromtimestamp(times[pos_open_idx], timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "exit_time": datetime.fromtimestamp(times[i], timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "entry_price": round(pos_entry, 6),
                        "exit_price": round(exit_price, 6),
                        "pnl": round(total_pnl, 2),
                        "pnl_pct": round(total_pnl_pct, 2),
                        "reason": exit_reason,
                        "duration_m": hold_duration,
                    })

                    in_position = False
                    cooldown_until = i + cooldown_candles
                    equity_curve.append(round(balance, 2))

                continue

            # ── 2. Kiểm tra tín hiệu vào lệnh (7 Tầng của Tác Giả) ──
            if i < cooldown_until:
                continue

            # Layer 1: Volume Spike
            last_vol = volumes[i]
            base_vol = np.mean(volumes[i-20:i])
            vol_ratio = last_vol / max(base_vol, 1e-9)
            if vol_ratio < vol_spike_mult:
                continue

            # Layer 2: Price Spike (5m window)
            price_5m_ago = closes[i-5]
            price_change = (closes[i] - price_5m_ago) / price_5m_ago
            if price_change < price_spike_pct:
                continue

            # Layer 3: 3 Green Candles
            green_candles = sum(1 for k in range(i-2, i+1) if closes[k] > opens[k])
            if green_candles < 3:
                continue

            # Layer 4: RSI 14 in [60, 85]
            deltas = np.diff(closes[i-15:i+1])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            rs = np.mean(gains) / max(np.mean(losses), 1e-9)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            if rsi < 60.0 or rsi > 85.0:
                continue

            # Layer 5: Taker Buy Ratio >= 65%
            recent_buy = np.sum(taker_buys[i-4:i+1])
            recent_tot = np.sum(volumes[i-4:i+1])
            buy_ratio = recent_buy / max(recent_tot, 1e-9)
            if buy_ratio < 0.65:
                continue

            # Layer 6: ATR Calculation for SL
            trs = [
                max(highs[k] - lows[k], abs(highs[k] - closes[k-1]), abs(lows[k] - closes[k-1]))
                for k in range(i-13, i+1)
            ]
            atr = float(np.mean(trs))

            # Open Position
            in_position = True
            pos_entry = closes[i]
            notional = balance * risk_budget_pct * leverage
            pos_orig_qty = notional / pos_entry
            pos_qty = pos_orig_qty
            pos_open_idx = i

            pos_sl = pos_entry - (atr * sl_atr_mult)
            pos_tp1 = pos_entry * (1.0 + tp1_pct)
            pos_tp2 = pos_entry * (1.0 + tp2_pct)
            pos_tp3 = pos_entry * (1.0 + tp3_pct)
            pos_tp1_hit = False
            pos_tp2_hit = False
            pos_tp3_hit = False
            pos_trailing_active = False
            pos_trailing_high = pos_entry

        # ── 3. Thống kê kết quả ──
        total_trades = len(trades)
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

        total_profit = sum(t["pnl"] for t in wins)
        total_loss = abs(sum(t["pnl"] for t in losses))
        profit_factor = (total_profit / total_loss) if total_loss > 0 else (99.0 if total_profit > 0 else 0.0)

        # Max Drawdown Calculation
        peak = initial_balance
        max_dd = 0.0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        return {
            "symbol": symbol,
            "days": days,
            "candles_analyzed": n_candles,
            "initial_balance": initial_balance,
            "final_balance": round(balance, 2),
            "net_profit": round(balance - initial_balance, 2),
            "return_pct": round((balance / initial_balance - 1.0) * 100.0, 2),
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "trades": trades,
        }
