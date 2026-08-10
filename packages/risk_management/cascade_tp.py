"""
Cascade Take-Profit & Dynamic ATR Stop Loss Calculation
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TradePlan:
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    tp1_pct: float
    tp2_pct: float
    tp3_pct: float
    leverage: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry": self.entry,
            "stop_loss": self.stop_loss,
            "tp1": self.tp1,
            "tp2": self.tp2,
            "tp3": self.tp3,
            "tp1_pct": self.tp1_pct,
            "tp2_pct": self.tp2_pct,
            "tp3_pct": self.tp3_pct,
            "leverage": self.leverage,
        }


def calculate_trade_plan(
    current_price: float,
    atr: float,
    tp1_mult: float = 0.05,
    tp2_mult: float = 0.10,
    tp3_mult: float = 0.20,
    atr_multiplier: float = 1.5,
    leverage: int = 5,
) -> TradePlan:
    """Calculate Cascade TP targets and ATR dynamic stop loss level."""
    entry = current_price
    atr_val = atr if atr > 0 else (entry * 0.02)
    sl = max(0.0, entry - (atr_val * atr_multiplier))

    tp1 = entry * (1.0 + tp1_mult)
    tp2 = entry * (1.0 + tp2_mult)
    tp3 = entry * (1.0 + tp3_mult)

    return TradePlan(
        entry=round(entry, 8),
        stop_loss=round(sl, 8),
        tp1=round(tp1, 8),
        tp2=round(tp2, 8),
        tp3=round(tp3, 8),
        tp1_pct=round(tp1_mult * 100.0, 2),
        tp2_pct=round(tp2_mult * 100.0, 2),
        tp3_pct=round(tp3_mult * 100.0, 2),
        leverage=leverage,
    )
