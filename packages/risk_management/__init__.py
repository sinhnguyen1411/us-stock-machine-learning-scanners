"""
Risk Management Package — Cascade Take-Profit, ATR Stops, Cooldowns & Simulation
"""

from .cascade_tp import calculate_trade_plan, TradePlan
from .circuit_breaker import CircuitBreakerManager
from .backtest_engine import CascadeBacktestEngine

__all__ = [
    "calculate_trade_plan",
    "TradePlan",
    "CircuitBreakerManager",
    "CascadeBacktestEngine",
]
