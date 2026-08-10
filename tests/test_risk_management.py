"""
Unit Tests for Risk Management Package
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "packages"))

from risk_management import calculate_trade_plan, CircuitBreakerManager


def test_calculate_trade_plan():
    plan = calculate_trade_plan(current_price=100.0, atr=2.0, tp1_mult=0.05, tp2_mult=0.10, tp3_mult=0.20)
    assert plan.entry == 100.0
    assert plan.stop_loss == 97.0   # 100 - (2.0 * 1.5)
    assert plan.tp1 == 105.0        # +5%
    assert plan.tp2 == 110.0        # +10%
    assert plan.tp3 == 120.0        # +20%


def test_circuit_breaker():
    mgr = CircuitBreakerManager(max_daily_loss=50.0, cooldown_seconds=60)
    assert not mgr.is_circuit_tripped()

    mgr.register_exit("BTCUSDT", pnl=-20.0)
    assert not mgr.is_circuit_tripped()
    assert mgr.is_symbol_in_cooldown("BTCUSDT")

    mgr.register_exit("ETHUSDT", pnl=-35.0)
    assert mgr.is_circuit_tripped()  # -55.0 <= -50.0


if __name__ == "__main__":
    test_calculate_trade_plan()
    test_circuit_breaker()
    print("All risk management unit tests passed successfully!")
