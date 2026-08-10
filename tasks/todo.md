# Task Checklist: Top 10 High-Probability Pump Candidates Tab (COMPLETED)

## Phase 1: Backend Pump Scoring Engine
- [x] Task 1.1: Viết hàm `calculate_pump_score()` trong `web_app.py` chấm điểm từ $0 \to 100$ dựa trên 7 biểu hiện vi mô.
- [x] Task 1.2: Xây dựng pipeline quét 2 giai đoạn (Two-Stage Fast Pipeline) quét 526 cặp trong background thread.
- [x] Task 1.3: Cung cấp API `GET /api/top_pump_candidates` trả về Top 10 kèm điểm PumpScore và nhãn giai đoạn.
- [x] Checkpoint 1: Kiểm thử API trả về danh sách 10 coin có điểm PumpScore cao nhất.

## Phase 2: Giao Diện Tab & Bảng Xếp Hạng Top 10 Realtime
- [x] Task 2.1: Thêm Section/Tab Top 10 Ứng Viên Pump trong `templates/index.html`.
- [x] Task 2.2: Bổ sung CSS styles cho Rank Badges (Huy hiệu 1, 2, 3), thanh điểm Progress Bar và hiệu ứng Glow trong `static/css/style.css`.
- [x] Task 2.3: Viết logic `loadTopPumpCandidates()` trong `static/js/app.js`, tự động refresh mỗi 4s và liên kết soi nến/vào lệnh nhanh.
- [x] Checkpoint 2: Xác nhận giao diện hiển thị bảng Top 10 sinh động, trực quan và bấm vào là soi nến ngay.
