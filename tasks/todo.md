# Task Checklist: Monorepo Architecture & Binance Futures Terminal (COMPLETED)

## Phase 1: Core Domain Packages (`packages/`)
- [x] Task 1.1: `packages/core_engine/`: 7-Layer Confirmation Engine, RSI (14), ATR (14), Pump Potential Scoring (0-100), and Adaptive Tier Classification (Bluechip vs Mid-Cap vs Meme).
- [x] Task 1.2: `packages/exchange_connectors/`: Binance Futures (USDT-M) REST/WebSocket client and Bybit connector wrapper.
- [x] Task 1.3: `packages/risk_management/`: 3-stage Cascade Take-Profit, Dynamic ATR Stop Loss, Circuit Breaker ($-\$50$), 2h max hold limit, 30m cooldown, and Historical Backtest Engine.

## Phase 2: Executable Applications (`apps/`)
- [x] Task 2.1: `apps/web_terminal/`: Full-stack Flask Web Dashboard with Top 10 Pump Candidates ranking, 526-pair Live Radar, Offline TradingView Lightweight Charts, and Backtest Modal.
- [x] Task 2.2: `apps/cli_scanner/`: Autonomous headless CLI scanner for 500+ pairs with paper trading.
- [x] Task 2.3: `apps/backtest_runner/`: Standalone batch strategy backtest simulator CLI.

## Phase 3: Automated Testing & Packaging
- [x] Task 3.1: Unit tests in `tests/test_core_engine.py` and `tests/test_risk_management.py` (100% passing).
- [x] Task 3.2: Monorepo workspace configuration via `pyproject.toml`.
- [x] Task 3.3: 100% Technical English `README.md` without emoji spam.
- [x] Task 3.4: Committed and pushed to GitHub repository `sinhnguyen1411/crypto-pump-scanner`.
