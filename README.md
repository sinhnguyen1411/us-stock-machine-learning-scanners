<div align="center">

# DeepAlpha Binance Futures (USDT-M) Pump Scanner & AI Terminal

### Hệ thống Quét Sóng Đột Biến & Bảng Xếp Hạng Top 10 Real-Time Cho 526 Cặp Binance Futures

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Binance](https://img.shields.io/badge/Exchange-Binance%20Futures%20(USDT--M)-F0B90B.svg)](https://www.binance.com)
[![TradingView](https://img.shields.io/badge/Charts-Lightweight%20Charts-00f2fe.svg)](https://tradingview.github.io/lightweight-charts/)

</div>

---

## 🌟 Tổng Quan Hệ Thống

**DeepAlpha Binance Futures Pump Scanner** là hệ thống phân tích dòng tiền vi mô (Orderflow Microstructure) và phát hiện chân sóng Pump thời gian thực trên toàn bộ **526 cặp Binance Futures (USDT-M)**.

```
[ 526 Cặp Binance Futures (USDT-M) ] ──> Quét Song Song (10 Threads / 3s)
                      │
                      ├──> [ 1. Volume Spike 1M (≥ 2.0x - 5.0x vs 20m EWMA) ]
                      ├──> [ 2. Taker Buy Pressure (≥ 65% - 80%) ]
                      ├──> [ 3. Gia Tốc Giá 5M (≥ +1.0% - +3.0%) ]
                      ├──> [ 4. RSI Vùng Ngọt Động Lượng (60 - 85) ]
                      ├──> [ 5. Chuỗi 3 Nến Xanh Liên Tiếp ]
                      └──> [ 6. Open Interest Expansion & Funding Rate ]
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
    [ 🔥 TOP 10 ỨNG VIÊN SẮP PUMP ]               [ 🎯 CASCADE TP & RISK ENGINE ]
  • Pump Potential Score (0 - 100)              • TP1 (+5%): Chốt 40% & SL Hòa Vốn (+0.2%)
  • Nhãn Sóng: Chân Sóng, Gom Hàng, Bùng Nổ     • TP2 (+10%): Chốt 30% & Trailing 3%
  • Tương tác 1-chạm soi nến & vào lệnh         • TP3 (+20%): Chốt toàn bộ vị thế
```

---

## ✨ Tính Năng Nổi Bật

### 1. 🧮 Thuật Toán Chấm Điểm Động Lượng (Pump Potential Score: $0 \to 100$)
- Tự động chấm điểm và xếp hạng liên tục **Top 10 Cặp Có Xác Suất Pump Cao Nhất**.
- Gắn nhãn giai đoạn sóng tự động:
  - `🚀 CHÂN SÓNG`: Volume gom đột biến, Taker Buy $\ge 65\%$, giá vừa chớm tăng $\le 2\%$.
  - `⚡ ĐANG BÙNG NỔ`: Đủ 3 nến xanh, gia tốc giá dốc đứng, RSI bứt phá $> 65$.
  - `🔥 GOM HÀNG CỰC ĐẠI`: Taker Buy áp đảo $\ge 70\%$, cá mập vét cạn sổ lệnh.
  - `⏳ NÉN TÍCH LŨY`: Động lượng chuẩn bị vào nhịp bứt phá.

### 2. 👑 Cơ Chế Thích Ứng Theo Nhóm Coin (Adaptive Tier Engine)
- **Bluechip Large-Cap (`BTC`, `ETH`, `SOL`, `BNB`...)**: Vol $\ge 2.0\times$, Giá $5\text{m} \ge +1.0\%$.
- **Mid-Cap Trending (`DOGE`, `LINK`, `NEAR`...)**: Vol $\ge 3.5\times$, Giá $5\text{m} \ge +2.0\%$.
- **High-Volatility / Meme (`TUT`, `AKE`, `CAP`...)**: Vol $\ge 5.0\times$, Giá $5\text{m} \ge +3.0\%$.

### 3. 📊 Giao Diện Terminal Chuyên Nghiệp (TradingView Lightweight Charts)
- Tích hợp 100% thư viện Offline cục bộ, không phụ thuộc mạng CDN.
- Vẽ trực tiếp đường giá **Stop Loss (Đỏ đứt đoạn)**, **TP1 (Xanh lá)**, **TP2 (Xanh Cyan Trailing)** trên biểu đồ.
- Hỗ trợ đầy đủ **9 khung thời gian**: `1M`, `3M`, `5M`, `15M`, `30M`, `1H`, `2H`, `4H`, `1D`.
- Thanh truy cập nhanh **20 mã vừa tra gần đây** lưu trữ qua `localStorage`.

### 4. 🧪 Engine Backtest Lịch Sử (Cascade Take Profit Simulator)
- Mô phỏng chính xác chiến lược Cascade TP trên dữ liệu nến 1m lịch sử của Binance Futures.
- Đo lường chi tiết: Tổng lợi nhuận ($), Tỷ lệ thắng (Win Rate %), Profit Factor, Max Drawdown và Trade Log.

### 5. 🛡️ Quản Trị Rủi Ro Chặt Chẽ
- **Stop Loss Động**: Cắt lỗ theo $1.5\times$ ATR.
- **Hạn Vị Thế 2H**: Tự động thoát lệnh sau 120 phút.
- **Cooldown 30M**: Khóa coin chống đu đỉnh lại nhịp xả.
- **Circuit Breaker**: Dừng giao dịch khi lỗ ngày chạm $-\$50$.
- **Cảnh Báo Âm Thanh**: Web Audio API Synthesizer phát chuông khi có tín hiệu $\ge 75\%$.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Cài đặt môi trường
```bash
git clone https://github.com/<your-username>/crypto-pump-scanner.git
cd crypto-pump-scanner
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Tạo file `.env` từ `.env.example`:
```bash
cp .env.example .env
```
*(Chỉ cần điền API Key nếu muốn chạy chế độ Live Trading, chế độ Paper Trade & Radar Scanner hoạt động trực tiếp không cần API Key).*

### 3. Khởi chạy Web Dashboard
```bash
python web_app.py
```
👉 Mở trình duyệt truy cập: **`http://localhost:5050`**

### 4. Khởi chạy CLI Scanner (Tùy chọn)
```bash
python binance_pump_scanner.py
```

---

## 📁 Cấu Trúc Mã Nguồn

```
crypto-pump-scanner/
├── web_app.py                  # Flask Backend Server, Adaptive Engine & Radar Thread
├── backtest_engine.py          # Vector/Loop Cascade TP Historical Simulator
├── binance_pump_scanner.py     # Standalone CLI Scanner & Paper Trading
├── templates/
│   └── index.html              # HTML Dashboard (Top 10, Radar, Charts, Backtest Modal)
├── static/
│   ├── css/style.css           # Dark Glassmorphism Stylesheet
│   └── js/
│       ├── app.js              # Client Frontend Logic & Real-time WebSocket/Polling
│       └── lightweight-charts.js # Local TradingView Charts Bundle
├── tasks/                      # Project Specifications & Todo Checklists
└── requirements.txt            # Python Dependencies (Flask, python-binance, etc.)
```

---

## 📄 License
Phát hành theo giấy phép [MIT License](LICENSE).
