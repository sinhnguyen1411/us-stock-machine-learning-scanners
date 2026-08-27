# DeepAlpha Binance Futures Pump Scanner & Real-Time Terminal (Monorepo)

An automated market microstructure scanner, momentum anomaly detector, and multi-tier trading terminal designed specifically for Binance Futures (USDT-M) perpetual contracts, organized as a modular enterprise monorepo.

---

## Architecture Overview

This project is structured as a scalable Python monorepo separating presentation applications (`apps/`) from reusable domain packages (`packages/`):

```
crypto-pump-scanner/ (Monorepo Root)
|-- apps/
|   |-- web-terminal/            # Flask Web Application & Real-Time Terminal UI
|   |   |-- app.py               # Web server entrypoint
|   |   |-- templates/           # Jinja2 HTML templates
|   |   `-- static/              # CSS, JavaScript & Offline TradingView bundle
|   |
|   |-- cli-scanner/             # Headless Autonomous CLI Scanner & Worker
|   |   `-- main.py              # CLI scanner execution script
|   |
|   `-- backtest-runner/         # Standalone Batch Strategy Backtester
|       `-- run_backtest.py      # Backtest script
|
|-- packages/                    # Reusable Domain Libraries
|   |-- core-engine/             # 7-Layer Confirmation Engine & Adaptive Tiers
|   |   |-- detector.py          # Microstructure anomaly detectors (RSI, ATR, Vol Spike)
|   |   |-- scoring.py           # Pump Potential Score (0-100) & Wave Stage Tagging
|   |   `-- classifier.py       # Bluechip vs. Mid-Cap vs. Meme Tier Classifier
|   |
|   |-- exchange-connectors/     # Exchange Clients & Session Managers
|   |   |-- binance_client.py    # Binance Futures USDT-M connector
|   |   `-- bybit_client.py      # Bybit Perpetual connector
|   |
|   `-- risk-management/         # Cascade Take-Profit & Safety Management
|       |-- cascade_tp.py        # 3-tier partial TP & Trailing Stop Calculator
|       |-- circuit_breaker.py   # Daily loss limit & cooldown manager
|       `-- backtest_engine.py   # Vectorized historical simulator
|
|-- tests/                       # Automated Unit & Integration Test Suite
|   |-- test_core_engine.py
|   `-- test_risk_management.py
|
|-- pyproject.toml               # Monorepo workspace configuration
|-- requirements.txt             # Aggregate dependencies
`-- README.md                    # Project documentation
```

---

## Key Features

### 1. Multi-Factor Pump Potential Scoring
- Computes a normalized composite score (0 to 100) per symbol based on weighted microstructure variables:
  - Volume Spike Ratio (25% weight)
  - Taker Buy Volume Ratio (25% weight)
  - 5-Minute Price Momentum (20% weight)
  - RSI Sweetspot Distance (15% weight)
  - Consecutive Bullish Candles (10% weight)
  - Open Interest Acceleration (5% weight)
- Automatically tags market structure into wave phases: Early Breakout, Momentum Surge, Heavy Accumulation, and Compression.

### 2. Adaptive Asset Classification
Applies calibrated sensitivity thresholds depending on market capitalization and liquidity depth:
- **Bluechip Large-Cap** (`BTC`, `ETH`, `SOL`, `BNB`, `XRP`, `ADA`, `AVAX`):
  - Volume Threshold: >= 2.0x baseline
  - 5M Price Velocity: >= +1.0%
  - Target Scale: TP1 +2.0% / TP2 +4.0% / TP3 +8.0%
- **Mid-Cap Trending** (`DOGE`, `LINK`, `NEAR`, `SUI`, `APT`, `TRX`):
  - Volume Threshold: >= 3.5x baseline
  - 5M Price Velocity: >= +2.0%
  - Target Scale: TP1 +3.5% / TP2 +7.0% / TP3 +15.0%
- **High-Volatility & Small-Cap / Meme** (`TUT`, `AKE`, `BMT`, `CAP`, `PEPE`):
  - Volume Threshold: >= 5.0x baseline
  - 5M Price Velocity: >= +3.0%
  - Target Scale: TP1 +5.0% / TP2 +10.0% / TP3 +20.0%

### 3. Integrated TradingView Lightweight Charts
- Fully local offline bundle without external CDN dependencies.
- Dynamic price lines rendered directly on the chart for Stop Loss (1.5x ATR), Take Profit 1 (+5%), and Take Profit 2 (+10%).
- Full multi-timeframe switching across 9 standard intervals: `1M`, `3M`, `5M`, `15M`, `30M`, `1H`, `2H`, `4H`, `1D`.
- Auto-scaling price precision for micro-priced assets (down to 8 decimals).
- Persistent 20-symbol recent lookup history stored via browser localStorage.

### 4. Historical Cascade Backtest Engine
- High-speed historical backtesting module for 1-minute historical klines.
- Evaluates entry signals, partial take-profits, trailing stop adjustments, and maximum holding duration limits.
- Generates detailed performance metrics: Net Profit ($), Return (%), Win Rate (%), Profit Factor, Maximum Drawdown (%), and granular execution logs.

### 5. Risk Management Architecture
- **ATR-Based Dynamic Stop Loss**: Position stop level calculated dynamically from 14-period Average True Range.
- **2-Hour Maximum Holding Time**: Automatic time-stop limit to avoid prolonged capital stagnation.
- **30-Minute Cooldown Filter**: Prevents re-entry on recently traded symbols to avoid distribution traps.
- **Daily Loss Circuit Breaker**: Hard safety stop when daily unrealized/realized loss exceeds predefined thresholds.

---

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Git

### 1. Clone Repository
```bash
git clone https://github.com/sinhnguyen1411/crypto-pump-scanner.git
cd crypto-pump-scanner
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy the sample environment file:
```bash
cp .env.example .env
```
*Note: API keys are optional for paper trading, backtesting, and market scanning. Binance public market data endpoints do not require authenticated credentials.*

---

## Usage

### Running the Web Terminal
Start the Flask web dashboard:
```bash
python apps/web_terminal/app.py
# Or use the root launcher:
python web_app.py
```
Open your browser and navigate to:
```
http://localhost:5050
```

### Running the Autonomous CLI Scanner
```bash
python apps/cli_scanner/main.py
# Or use the root launcher:
python binance_pump_scanner.py
```

### Running Batch Backtests
```bash
python apps/backtest_runner/run_backtest.py --symbol BTCUSDT --days 7 --balance 1000.0
```

### Running Unit Tests
```bash
python tests/test_core_engine.py
python tests/test_risk_management.py
```

---

## License

Copyright &copy; 2026 Sinh Nguyen. All rights reserved. **Proprietary & Confidential**.

