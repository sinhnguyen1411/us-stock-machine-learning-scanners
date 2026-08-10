"""
Circuit Breaker, Daily Loss Limit, Cooldown & Holding Limits
"""

import time
from typing import Dict


class CircuitBreakerManager:
    """Manages daily loss stops, per-symbol cooldowns, and holding time limits."""

    def __init__(
        self,
        max_daily_loss: float = 50.0,
        max_holding_seconds: int = 7200,   # 2 hours
        cooldown_seconds: int = 1800,      # 30 minutes
    ):
        self.max_daily_loss = max_daily_loss
        self.max_holding_seconds = max_holding_seconds
        self.cooldown_seconds = cooldown_seconds
        
        self.daily_realized_pnl = 0.0
        self.cooldown_registry: Dict[str, float] = {}

    def is_circuit_tripped(self) -> bool:
        """Check if daily loss exceeds safety circuit limit."""
        return self.daily_realized_pnl <= -abs(self.max_daily_loss)

    def is_symbol_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is currently locked in cooldown period."""
        last_time = self.cooldown_registry.get(symbol.upper(), 0.0)
        return (time.time() - last_time) < self.cooldown_seconds

    def register_exit(self, symbol: str, pnl: float):
        """Record trade exit and trigger cooldown."""
        self.daily_realized_pnl += pnl
        self.cooldown_registry[symbol.upper()] = time.time()

    def reset_daily_pnl(self):
        """Reset daily PnL counter on UTC 00:00."""
        self.daily_realized_pnl = 0.0
