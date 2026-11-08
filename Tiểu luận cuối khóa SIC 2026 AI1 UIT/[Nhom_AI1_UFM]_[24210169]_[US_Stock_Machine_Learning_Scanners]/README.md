# HỒ SƠ NỘP BÀI ĐỒ ÁN CUỐI KHÓA — SIC 2026 AI1 UIT

- **Cơ sở đào tạo:** Trường Đại học Công nghệ Thông tin — Đại học Quốc gia TP.HCM (UIT)
- **Khoa chuyên trách:** Khoa Khoa học và Kỹ thuật Thông tin
- **Đơn vị quản lý / Hệ đào tạo:** Văn bằng 2 — Trung tâm Phát triển Công nghệ Thông tin (CITD)
- **Học phần:** Trí tuệ Nhân tạo Ứng dụng & Khoa học Dữ liệu (SIC 2026)
- **Lớp khóa học:** Lớp SIC 2026: AI1 UFM
- **Tên đề tài:** Hệ Thống Định Lượng Machine Learning & Quét Vi Mô Dòng Tiền Thể Chế Phái Sinh Cổ Phiếu Mỹ (TradFi US Stock USD-M 24/7) Dựa Trên Dữ Liệu Lớn Thời Gian Thực Và Chu Trình Chuẩn CRISP-DM
- **Học viên thực hiện:** NGUYỄN DƯƠNG MẠNH SINH
- **Mã số sinh viên (MSSV):** 24210169
- **Giảng viên hướng dẫn:** ThS. Trần Mạnh Tường
- **Thời gian thực hiện:** Tháng 06/2026 – Tháng 10/2026
- **Trạng thái đóng góp:** 100% — Đã hoàn thành
- **Kho lưu trữ GitHub (Public):** [https://github.com/sinhnguyen1411/us-stock-machine-learning-scanners](https://github.com/sinhnguyen1411/us-stock-machine-learning-scanners)

---

## 1. Danh Mục Các Tệp Trong Hồ Sơ Nộp Bài

Thư mục này được tổ chức đầy đủ và chuẩn xác theo quy định tại Mục 1.2 của tài liệu Hướng dẫn và Rubric chấm điểm của UIT:

| Tên tệp / Thư mục | Định dạng | Mô tả nội dung | Ghi chú quy chuẩn |
|:---|:---:|:---|:---|
| **`tieu_luan_cuoi_khoa_us_stock_ml_scanners.qmd`** | Quarto | Báo cáo tiểu luận nguồn đầy đủ 6 phần nội dung, bảng phân công nhiệm vụ, tuyên bố liêm chính AI, trang bìa học thuật đôi TikZ, căn lề 30-20-25-25 mm chuẩn XeLaTeX. | Tiêu chí 1, 2, 3, 4 |
| **`US_Stock_ML_Scanners_CRISP_DM.ipynb`** | Jupyter Notebook | Mã nguồn thực thi 6 pha CRISP-DM đã chạy sạch toàn bộ (Restart & Run All) lưu sẵn đầy đủ bảng số liệu, outputs và kết quả phân tích. | Tiêu chí 6 |
| **`US_Stock_ML_Scanners_Final_Project_30_Slides.pptx`** | PowerPoint | Slide trình chiếu bảo vệ đồ án 30 trang đồng bộ đầy đủ nhận diện học thuật UIT, biểu đồ và kiến trúc hệ thống. | Trình bày & Demo |
| **`figures/`** | Thư mục PNG | Chứa 15 hình ảnh, biểu đồ định lượng 300 DPI và ảnh chụp thực tế từ Web Terminal Scanner của dự án. | Minh chứng trực quan |
| **`data/`** | Thư mục CSV | Chứa tập dữ liệu thực tế nến vi mô 5M (`NVDAUSDT_5m_288candles_20260827.csv`) trích xuất từ Binance Futures Matching Engine API. | Điểm thưởng dữ liệu thực tế |
| **`huong_dan_tieu_luan_va_rubric_cuoi_khoa.pdf`** | PDF | Tài liệu gốc hướng dẫn viết tiểu luận và rubric chấm điểm 12 trang của giảng viên. | Tham chiếu gốc |
| **`huong_dan_tieu_luan_va_rubric_cuoi_khoa.qmd`** | Quarto | Bản số hóa Quarto Markdown đầy đủ của rubric môn học để đối soát 1:1. | Đối soát chuẩn hóa |
| **`README.md`** | Markdown | Tài liệu hướng dẫn tổng quan và đối soát hồ sơ nộp bài. | Chỉ mục tra cứu |

---

## 2. Hướng Dẫn Mở & Kiểm Tra Nhanh

1. **Xem Báo cáo Tiểu luận Quarto (`.qmd`):**
   - Mở tệp `tieu_luan_cuoi_khoa_us_stock_ml_scanners.qmd` bằng VS Code, RStudio hoặc trình soạn thảo văn bản hỗ trợ Quarto.
   - Để biên dịch sang PDF: Thực thi lệnh `quarto render tieu_luan_cuoi_khoa_us_stock_ml_scanners.qmd --to pdf`.
2. **Kiểm tra Notebook (`.ipynb`):**
   - Mở tệp `US_Stock_ML_Scanners_CRISP_DM.ipynb` trên Jupyter Lab, VS Code hoặc Google Colab. Toàn bộ 11 ô lệnh đều đã được thực thi và hiển thị sẵn kết quả đầy đủ.
3. **Xem Slide trình chiếu (`.pptx`):**
   - Mở tệp `US_Stock_ML_Scanners_Final_Project_30_Slides.pptx` bằng Microsoft PowerPoint hoặc Google Slides.
4. **Kiểm tra hình ảnh & dữ liệu:**
   - Thư mục `figures/` chứa 15 biểu đồ độ phân giải cao phục vụ cho báo cáo.
   - Thư mục `data/` chứa tệp dữ liệu chuỗi thời gian nến 5M của cổ phiếu NVIDIA (NVDA).

---

## 3. Tóm Tắt Kết Quả Mô Hình Hóa Chính

- **Mô hình triển khai:** LightGBM Classifier kết hợp tối ưu hóa siêu tham số Bayesian qua Optuna (100 trials).
- **Hiệu năng kiểm định ngoài mẫu (Out-of-Sample):**
  - $Precision = 83.5\%$ (Giảm thiểu báo động giả so với Baseline $51.2\%$).
  - $PR-AUC = 0.868$ | $ROC-AUC = 0.914$ | $F_1\text{-Score} = 81.3\%$.
  - Khoảng cách tổng quát hóa (Generalization Gap) $< 0.033$ (chống Overfitting hiệu quả).
- **Giải thích mô hình (XAI):** Tích hợp TreeSHAP giải thích đóng góp của 5 đặc trưng vi mô ($VWAP_{dist}$, $Vol_{spike}$, $Coiling$, $TakerBuy_{ratio}$, $ATR_{rel}$).
- **Kiểm soát rủi ro:** Cơ chế ngắt mạch Circuit Breaker tự động dừng mở vị thế khi mức sụt giảm vượt $-\$50$, đi kèm kế hoạch chốt lời từng phần Cascade Take-Profit (TP1 $+2.5\%$, TP2 $+5.0\%$, TP3 $+10.0\%$).
