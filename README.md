# DeepAlpha Binance Futures Pump Scanner & Real-Time Terminal

An automated market microstructure scanner, momentum anomaly detector, and multi-tier trading terminal designed specifically for Binance Futures (USDT-M) perpetual contracts.

---

## Overview

DeepAlpha Binance Futures Pump Scanner continuously monitors orderflow anomalies and volume breakouts across 500+ USDT-Margined perpetual contracts on Binance Futures. 

By analyzing early 1-minute candlestick spikes against rolling volume baselines alongside taker buy ratios and open interest delta, the engine distinguishes genuine institutional buy pressure from low-liquidity wash trades and price exhaustion.

```
[ 526 Binance Futures USDT-M Pairs ]
                 |
  (Fast Two-Stage Multi-Threaded Engine)
                 |
                 +--> 1. Volume Spike (1M vs. 20-period EWMA Baseline)
                 +--> 2. Taker Buy Pressure Ratio (>= 65% - 80%)
                 +--> 3. 5-Minute Price Velocity (>= +1.0% to +3.0%)
                 +--> 4. RSI Momentum Sweetspot (60 - 85)
                 +--> 5. 3 Consecutive Bullish Candles
                 +--> 6. Open Interest Expansion (Delta OI > 0)
                 +--> 7. Volatility Expansion (1.5x ATR)
                 |
                 +-----------------------+-----------------------+
                 |                                               |
                 v                                               v
     [ Top 10 Pump Candidates ]                      [ Cascade Take-Profit Engine ]
   - Composite Score (0-100)                       - TP1 (+5%): Close 40% & Breakeven SL (+0.2%)
   - Wave Stage Classification                     - TP2 (+10%): Close 30% & 3% Trailing Stop
   - One-Click Terminal Navigation                 - TP3 (+20%): Close Remaining Position
```

---

## Key Features

### 1. Multi-Factor Pump Scoring Engine
- Computes a normalized composite score (0 to 100) per symbol based on weighted microstructure variables:
  - Volume Spike Ratio (25% weight)
  - Taker Buy Volume Ratio (25% weight)
  - 5-Minute Price Momentum (20% weight)
  - RSI Sweetspot Distance (15% weight)
  - Consecutive Bullish Candles (10% weight)
  - Open Interest Acceleration (5% weight)
- Automatically classifies market structure into wave phases: Early Breakout, Momentum Surge, Heavy Accumulation, and Compression.

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
python web_app.py
```
Open your browser and navigate to:
```
http://localhost:5050
```

### Running the Standalone CLI Scanner
For headless server environments or automated command-line execution:
```bash
python binance_pump_scanner.py
```

---

## Project Structure

```
crypto-pump-scanner/
|-- web_app.py                  # Core backend server, scanner threads, and REST API
|-- backtest_engine.py          # Historical simulation and strategy validation engine
|-- binance_pump_scanner.py     # Standalone CLI scanner and paper trading execution
|-- templates/
|   `-- index.html              # Frontend terminal interface
|-- static/
|   |-- css/
|   |   `-- style.css           # Terminal stylesheet
|   `-- js/
|       |-- app.js              # Client state, data synchronization, and UI logic
|       `-- lightweight-charts.js # Standalone TradingView charting bundle
|-- requirements.txt            # Python package dependencies
|-- README.md                   # Project documentation
`-- LICENSE                     # MIT License
```

---

## Disclaimer

This software is intended for research, educational, and simulation purposes. Cryptocurrency futures trading involves significant market risk. Always test strategies thoroughly using paper trading before considering live deployment.

---

## License

This project is licensed under the [MIT License](LICENSE).
