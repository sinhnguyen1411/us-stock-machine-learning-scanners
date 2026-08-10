"""
Backtest Engine Root Entry Point (Monorepo Compatibility Shim)
"""

import sys
from pathlib import Path

# Add packages directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "packages"))

from risk_management.backtest_engine import CascadeBacktestEngine

__all__ = ["CascadeBacktestEngine"]
