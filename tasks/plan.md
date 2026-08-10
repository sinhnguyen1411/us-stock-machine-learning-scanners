# Kế Hoạch: Xây Dựng Tab Top 10 Ứng Cử Viên Sắp Pump Mạnh Nhất (Binance Futures USDT-M)

## 1. Mục Tiêu Dự Án
Xây dựng module tính điểm tổng hợp **Pump Potential Score ($0 \to 100$)** và bảng xếp hạng **Top 10 Ứng Cử Viên Sắp Pump Mạnh Nhất** được quét liên tục từ hơn 500 cặp Binance Futures (USDT-M).

---

## 2. Thuật Toán Chấm Điểm Tiềm Năng Pump (Pump Potential Score)

Mỗi cặp coin được đánh giá theo công thức trọng số đa tầng:

$$\text{PumpScore} = (S_{\text{vol}} \times 0.25) + (S_{\text{buy}} \times 0.25) + (S_{\text{price}} \times 0.20) + (S_{\text{rsi}} \times 0.15) + (S_{\text{green}} \times 0.10) + (S_{\text{oi}} \times 0.05)$$

| Thành Phần Điểm | Trọng Số | Công Thức Quy Đổi ($0 \to 100$) |
| :--- | :---: | :--- |
| **1. Volume Spike ($S_{\text{vol}}$)** | **25%** | $S_{\text{vol}} = \min(100, (\text{vol\_ratio} / 5.0) \times 100)$ |
| **2. Taker Buy Ratio ($S_{\text{buy}}$)** | **25%** | $S_{\text{buy}} = \min(100, \max(0, (\text{buy\_ratio} - 0.50) / 0.35 \times 100))$ |
| **3. Price Spike 5M ($S_{\text{price}}$)** | **20%** | $S_{\text{price}} = \min(100, (\text{price\_change\_5m} / 0.03) \times 100)$ |
| **4. RSI Sweetspot ($S_{\text{rsi}}$)** | **15%** | Điểm cao nhất khi $65 \le \text{RSI} \le 75$; giảm dần khi ra xa |
| **5. Chuỗi Nến Xanh ($S_{\text{green}}$)** | **10%** | 1 nến: 33đ, 2 nến: 66đ, 3 nến: 100đ |
| **6. Open Interest ($S_{\text{oi}}$)** | **5%** | Tăng trưởng $\Delta\text{OI}$ |

---

## 3. Kiến Trúc Xử Lý 2 Giai Đoạn (Two-Stage Fast Pipeline)

```
[ 526 Cặp Binance Futures ] 
            │
            ▼ (Stage 1: Lọc thô trong 0.5s theo Volume 24h & Biến động)
[ Top 40 Cặp Tiềm Năng Nhất ]
            │
            ▼ (Stage 2: Quét sâu nến 1m, Taker Buy, RSI, ATR song song)
[ Bảng Xếp Hạng PumpScore 0-100 ]
            │
            ▼ (Stage 3: Chọn Top 10 Điểm Cao Nhất)
[ API /api/top_pump_candidates & Tab Giao Diện Realtime ]
```

---

## 4. Danh Sách Các Giai Đoạn Triển Khai (Phases & Tasks)

### Phase 1: Backend Pump Scoring Engine
- [ ] **Task 1.1**: Viết hàm `calculate_pump_score(metrics, tier)` tính điểm chuẩn hóa từ $0 \to 100$.
- [ ] **Task 1.2**: Tích hợp thuật toán quét 2 giai đoạn (Two-Stage Pipeline) trong tiến trình ngầm `web_app.py`.
- [ ] **Task 1.3**: Xây dựng API endpoint `GET /api/top_pump_candidates` trả về Top 10 coin kèm điểm số chi tiết và nhãn trạng thái (`🚀 CHÂN SÓNG`, `⚡ ĐANG BÙNG NỔ`, `🔥 GOM HÀNG CỰC ĐẠI`).

### Phase 2: Thiết Kế Tab & Bảng Xếp Hạng Top 10 Trên Web UI
- [ ] **Task 2.1**: Thêm Panel / Tab **"🔥 TOP 10 ỨNG VIÊN SẮP PUMP MẠNH NHẤT (REALTIME)"** trên `templates/index.html`.
- [ ] **Task 2.2**: Thiết kế giao diện thanh điểm Gradient Progress Bar, huy hiệu vàng/bạc/đồng cho Top 1-2-3 trong `static/css/style.css`.
- [ ] **Task 2.3**: Xây dựng hàm `loadTopPumpCandidates()` trong `static/js/app.js` tự động làm mới mỗi 4 giây, hỗ trợ click soi nến và nút mở vị thế nhanh 1-chạm.

### Phase 3: Kiểm Thử & Nghiệm Thu
- [ ] **Task 3.1**: Kiểm tra API trả về đủ 10 coin với PumpScore được sắp xếp giảm dần.
- [ ] **Task 3.2**: Xác nhận giao diện hiển thị đúng các thanh điểm màu sắc và tương tác soi nến mượt mà.
