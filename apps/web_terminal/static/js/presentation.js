/**
 * DeepAlpha US Stock Machine Learning Scanners
 * Interactive 30-Slide Presentation Deck Logic
 */

const SLIDES_DATA = [
  // ── CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI & TÍNH CẤP THIẾT (SLIDES 1 - 5) ──
  {
    chapter: "Chương 1: Tổng Quan Đề Tài & Tính Cấp Thiết",
    title: "HỆ THỐNG ĐỊNH LƯỢNG MACHINE LEARNING & QUÉT VI MÔ DÒNG TIỀN THỂ CHẾ PHÁI SINH CỔ PHIẾU MỸ",
    subtitle: "US Stock TradFi USD-M Perpetual Futures & Institutional Order Flow Scanners",
    html: `
      <div style="background: linear-gradient(135deg, rgba(0,242,254,0.08), rgba(15,23,42,0.9)); border: 1px solid var(--slide-cyan); border-radius: 10px; padding: 24px; margin-bottom: 20px;">
        <div style="display: inline-block; padding: 4px 12px; background: rgba(0,242,254,0.2); color: var(--slide-cyan); font-weight: 800; font-size: 0.75rem; border-radius: 4px; font-family: var(--font-mono); margin-bottom: 12px;">
          FINAL PROJECT — QUANTITATIVE FINANCE & DATA SCIENCE
        </div>
        <h2 style="font-size: 1.4rem; color: #fff; margin: 0 0 10px 0;">Đồ Án Tốt Nghiệp: Ứng Dụng Học Máy & Cấu Trúc Vi Mô Sổ Lệnh Trong Giao Dịch Phái Sinh Cổ Phiếu Mỹ 24/7</h2>
        <p style="font-size: 0.95rem; color: #cbd5e1; line-height: 1.6; margin: 0;">
          Nghiên cứu và phát triển hệ thống định lượng thời gian thực có khả năng bóc tách dòng tiền gom hàng ngầm của các quỹ thể chế trên hơn 90 mã phái sinh cổ phiếu Mỹ theo chuẩn phương pháp luận quốc tế <strong>CRISP-DM</strong>.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">Thông Tin Đồ Án & Tác Giả</div>
          <ul class="slide-bullets">
            <li><strong>Tác giả / Nghiên cứu viên:</strong> Sinh Nguyen (Quant Engineer & Data Scientist).</li>
            <li><strong>Chuyên ngành:</strong> Khoa học Dữ liệu (Data Science) & Tài chính Định lượng (Quantitative Finance).</li>
            <li><strong>Khung phương pháp luận:</strong> Chu trình chuẩn công nghiệp CRISP-DM 6 giai đoạn khép kín.</li>
            <li><strong>Kiến trúc hệ thống:</strong> Python Monorepo, Binance Matching Engine API, In-Memory Micro-Batching.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">Phạm Vi & Năng Lực Xử Lý</div>
          <ul class="slide-bullets">
            <li><strong>Danh mục tài sản:</strong> Hơn 90+ hợp đồng tương lai vĩnh cửu cổ phiếu Mỹ (Mega Tech, Bán Dẫn, ETF...).</li>
            <li><strong>Tốc độ chu kỳ quét:</strong> 3.5 giây / chu kỳ tính toán thời gian thực.</li>
            <li><strong>Mô hình học máy:</strong> Ensemble Multi-Factor Scoring (0 - 100) kết hợp 5 đặc trưng vi mô độc lập.</li>
            <li><strong>Quản trị rủi ro:</strong> Cắt lỗ động 1.5x ATR Stop Loss và Chốt lời phân tầng Cascade TP1/TP2/TP3.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết",
    title: "Thách Thức Của Thị Trường Phái Sinh Cổ Phiếu Mỹ 24/7",
    subtitle: "Tại sao các phương pháp phân tích kỹ thuật truyền thống bị thất bại?",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box" style="border-color: rgba(255, 51, 102, 0.4);">
          <div class="slide-box-title" style="color: var(--slide-red);">1. Hạn Chế Phân Tích Truyền Thống</div>
          <ul class="slide-bullets">
            <li><strong>Độ trễ nghiêm trọng:</strong> Các chỉ báo như RSI, MACD, SMA chỉ tính trên giá đóng cửa quá khứ, hoàn toàn không thấy được lực gom/xả ẩn trong sổ lệnh.</li>
            <li><strong>Bất đối xứng thông tin:</strong> Nhà đầu tư cá nhân không thể theo dõi hành vi khớp lệnh của các quỹ phòng hộ lớn.</li>
            <li><strong>Bẫy thanh khoản (Spoofing & Traps):</strong> Nến Breakout giả liên tục xuất hiện để quét thanh khoản dừng lỗ.</li>
            <li><strong>Biến động ngoài giờ:</strong> Các phiên Pre-Market và Overnight biến động mạnh nhưng thiếu công cụ giám sát liên tục.</li>
          </ul>
        </div>
        <div class="slide-box" style="border-color: rgba(0, 242, 254, 0.4);">
          <div class="slide-box-title" style="color: var(--slide-cyan);">2. Giải Pháp Định Lượng Machine Learning</div>
          <ul class="slide-bullets">
            <li><strong>Bóc tách sổ lệnh vi mô:</strong> Đo lường trực tiếp tỷ lệ mua chủ động Taker Buy Pressure từ khớp lệnh thực tế của sàn.</li>
            <li><strong>Đường giá thể chế VWAP:</strong> Xác định vị thế giá trung bình của dòng tiền lớn làm bệ đỡ hỗ trợ cứng.</li>
            <li><strong>Điểm số ML Score (0 - 100):</strong> Tổng hợp 5 chiều dữ liệu vi mô độc lập để định lượng xác suất bùng nổ giá.</li>
            <li><strong>Quản trị rủi ro thích ứng ATR:</strong> Tự động tính toán vùng dừng lỗ theo độ biến động thực tế của từng mã.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết",
    title: "Mục Tiêu Nghiên Cứu & Phạm Vi Đề Tài",
    subtitle: "Xây dựng hệ thống quét dòng tiền thể chế thời gian thực trên 90+ hợp đồng TradFi Futures",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">MỤC TIÊU 1: ĐỊNH LƯỢNG</div>
          <ul class="slide-bullets">
            <li><strong>Toán học hóa dòng tiền:</strong> Xây dựng công thức tính Taker Buy và Volume Spike vs 20-EWMA.</li>
            <li><strong>Điểm số ML Composite:</strong> Chỉ số 0 - 100 phản ánh xác suất tăng tốc của cổ phiếu.</li>
            <li><strong>Độ trễ thấp:</strong> Xử lý toàn bộ 90+ mã trong dưới 200 mili-giây.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">MỤC TIÊU 2: CẢNH BÁO SỚM</div>
          <ul class="slide-bullets">
            <li><strong>Nhận diện Gom Hàng:</strong> Bắt trọn lực gom chủ động quanh VWAP trước khi nến bùng nổ.</li>
            <li><strong>Phân loại 5 tín hiệu:</strong> Mua Breakout, Gom Hàng, Tăng Tốc, Quá Mua, Tích Lũy.</li>
            <li><strong>Phát hiện bất thường 5M:</strong> Bắt các đợt mở rộng biên độ đột ngột trong phiên ngoài giờ.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-yellow);">MỤC TIÊU 3: ỨNG DỤNG</div>
          <ul class="slide-bullets">
            <li><strong>Terminal Realtime:</strong> Giao diện Web Pro với biểu đồ TradingView đa khung thời gian.</li>
            <li><strong>Soi nến độc lập:</strong> Trang chuyên sâu <code>/stock/&lt;symbol&gt;</code> với kế hoạch Trade Setup.</li>
            <li><strong>Quản trị vốn:</strong> Tự động tính SL 1.5x ATR và TP1/TP2/TP3 tỷ lệ R:R &ge; 1:2.0.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết",
    title: "Danh Mục Tài Sản TradFi US Stock (7 Phân Ngành Trọng Yếu)",
    subtitle: "Giám sát toàn diện hơn 90 mã cổ phiếu và chỉ số hàng đầu thị trường tài chính Mỹ",
    html: `
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-cyan); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-cyan); font-family: var(--font-mono);">1. MEGA-CAP TECH (15 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">NVDA, AAPL, MSFT, TSLA, AMZN, GOOGL, META, PLTR, MSTR, ORCL, NFLX, IBM, CRM, ADBE, QCOM.</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-green); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-green); font-family: var(--font-mono);">2. BÁN DẪN SEMICONDUCTOR (14 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">AMD, TSM, ASML, AVGO, INTC, MU, AMAT, LRCX, KLAC, MRVL, ARM, TXN, SOXL, SOXS.</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-yellow); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-yellow); font-family: var(--font-mono);">3. INDEX & CHỈ SỐ ETF (8 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">SPY (S&P 500), QQQ (Nasdaq), TQQQ, SQQQ, IWM (Russell 2000), DIA (Dow Jones), VXX, UVXY.</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-purple); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-purple); font-family: var(--font-mono);">4. AI & PRE-IPO / ĐỔI MỚI (12 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">OPENAI, ANTHROPIC, SPACEX, BYTEDANCE, STRIPE, DATABRICKS, FIGMA, COIN, HOOD, PATH, RBLX, SNOW.</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-cyan); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-cyan); font-family: var(--font-mono);">5. TÀI CHÍNH & NGÂN HÀNG (10 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">JPM, BAC, GS, MS, WFC, C, BLK, V, MA, AXP (Dẫn dắt thanh khoản phố Wall).</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-green); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-green); font-family: var(--font-mono);">6. CỔ PHIẾU QUỐC TẾ (12 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">BABA, TENCENT, BIDU, PDD, JD, NIO, XPEV, ASML, TSM, BNTX, SE, GRAB.</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-yellow); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-yellow); font-family: var(--font-mono);">7. TIÊU DÙNG & Y TẾ (19 mã):</strong>
          <span style="color: #cbd5e1; font-size: 0.88rem; margin-left: 8px;">WMT, COST, PG, KO, PEP, MCD, DIS, NKE, LLY, JNJ, UNH, PFE, ABBV, MRK, XOM, CVX, CAT, BA, RTX.</span>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết",
    title: "Ý Nghĩa Thực Tiễn & Đóng Góp Học Thuật Của Đề Tài",
    subtitle: "Cầu nối giữa lý thuyết Kinh tế lượng vi mô và Kỹ thuật phần mềm hiệu năng cao",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">ĐÓNG GÓP HỌC THUẬT</div>
          <ul class="slide-bullets">
            <li><strong>Mô hình hóa vi mô sổ lệnh:</strong> Ứng dụng thành công lý thuyết Order Flow Imbalance vào môi trường phái sinh 24/7.</li>
            <li><strong>Chuẩn hóa quy trình CRISP-DM:</strong> Chứng minh tính khả thi của quy trình 6 bước trong phát triển hệ thống giao dịch thuật toán.</li>
            <li><strong>Triệt tiêu độ trễ chỉ báo:</strong> Đề xuất trọng số động kết hợp giữa Taker Buy và VWAP giúp phát hiện sớm hơn 3 - 5 nến.</li>
            <li><strong>Khung kiểm thử thực nghiệm:</strong> Xây dựng Cascade Backtesting loại bỏ Look-Ahead Bias.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">GIÁ TRỊ THỰC TIỄN</div>
          <ul class="slide-bullets">
            <li><strong>Web Terminal cấp thể chế:</strong> Cung cấp giao diện trực quan, tốc độ quét cực nhanh 3.5s, đáp ứng nhu cầu thực chiến.</li>
            <li><strong>Hỗ trợ ra quyết định tự động:</strong> Tự động tính toán Entry, Stop Loss và 3 mục tiêu chốt lời tối ưu R:R &ge; 1:2.0.</li>
            <li><strong>Giám sát đa phiên New York:</strong> Tự động phân loại 4 phiên giao dịch để áp dụng trọng số thanh khoản phù hợp.</li>
            <li><strong>Sẵn sàng mở rộng quy mô:</strong> Kiến trúc Monorepo module hóa, dễ dàng tích hợp thêm sàn môi giới truyền thống.</li>
          </ul>
        </div>
      </div>
    `
  },

  // ── CHƯƠNG 2: PHƯƠNG PHÁP LUẬN CRISP-DM (SLIDES 6 - 11) ──
  {
    chapter: "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM",
    title: "Khung Quy Trình Chuẩn Công Nghiệp CRISP-DM 6 Giai Đoạn",
    subtitle: "Chu trình lặp 2 chiều liên tục từ thấu hiểu nghiệp vụ đến tối ưu hóa mô hình thực chiến",
    html: `
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; align-items: start;">
        <div class="slide-img-frame">
          <img src="/static/img/slides/crisp_dm_cycle_diagram.png" onerror="this.src='/static/img/placeholder.png'" alt="Chu Trình CRISP-DM Với Vòng Lặp Phản Hồi 2 Chiều">
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">4 VÒNG LẶP PHẢN HỒI</div>
          <ul class="slide-bullets">
            <li><strong>1. Nghiệp Vụ ⇄ Dữ Liệu:</strong> Dữ liệu sổ lệnh thực tế liên tục hiệu chỉnh và tái định hình bài toán nghiệp vụ.</li>
            <li><strong>2. Tiền Xử Lý ⇄ Mô Hình:</strong> Quá trình thử nghiệm mô hình đòi hỏi liên tục trích xuất thêm các đặc trưng vi mô mới.</li>
            <li><strong>3. Đánh Giá ⇄ Nghiệp Vụ:</strong> Nếu kết quả Backtest chưa đạt KPI (Win-Rate, Sharpe) &rarr; quay lại tinh chỉnh logic.</li>
            <li><strong>4. Triển Khai ⇄ Thu Thập:</strong> Giám sát hiện tượng lệch phân phối (Market Drift) và nạp dữ liệu mới để tái huấn luyện.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM",
    title: "CRISP-DM Phase 1: Thấu Hiểu Nghiệp Vụ Thị Trường Mỹ",
    subtitle: "Đặc thù thanh khoản và hành vi thể chế qua các phiên giao dịch New York",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">ĐẶC THÙ 4 PHIÊN GIAO DỊCH NEW YORK</div>
          <ul class="slide-bullets">
            <li><strong>Wall Street Live (09:30 - 16:00 EST):</strong> Phiên chính thanh khoản cực đại, khớp lệnh khối lượng lớn. Cộng +5.0 điểm thưởng ML.</li>
            <li><strong>Pre-Market (04:00 - 09:30 EST):</strong> Phản ứng với báo cáo tài chính (Earnings) và tin tức vĩ mô. Thường xuất hiện Gap giá lớn.</li>
            <li><strong>After-Hours (16:00 - 20:00 EST):</strong> Thanh khoản mỏng dần, các quỹ tiến hành tái cơ cấu danh mục.</li>
            <li><strong>Overnight (20:00 - 04:00 EST):</strong> Biên độ nén hẹp, thích hợp quét tín hiệu Gom Hàng ngầm.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-yellow);">YÊU CẦU NGHIỆP VỤ HỆ THỐNG</div>
          <ul class="slide-bullets">
            <li><strong>Độ trễ tối đa cho phép:</strong> Hệ thống phải hoàn thành phân tích 90+ mã trong dưới 3.5 giây.</li>
            <li><strong>Chống hiểu lầm xếp hạng:</strong> Khi tìm kiếm mã đơn lẻ (NVDA), hiển thị đúng thứ hạng toàn cục (#67/90), không gán là #1.</li>
            <li><strong>Kế hoạch giao dịch thực chiến:</strong> Tín hiệu mua phải đi kèm Entry, Stop Loss và Take Profit rõ ràng để thực thi ngay.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM",
    title: "CRISP-DM Phase 2: Thấu Hiểu & Nạp Dữ Liệu Sổ Lệnh / CSV Dataset",
    subtitle: "Minh họa cấu trúc bảng dữ liệu nến 5M và các đặc trưng vi mô được nạp vào hệ thống",
    html: `
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; align-items: start;">
        <div class="slide-img-frame">
          <img src="/static/img/slides/csv_dataset_sample.png" onerror="this.src='/static/img/placeholder.png'" alt="Mẫu Dữ Liệu Nạp Vào Hệ Thống (CSV Dataset)">
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">CẤU TRÚC DỮ LIỆU ĐẦU VÀO</div>
          <ul class="slide-bullets">
            <li><strong>Nguồn cấp sàn Binance:</strong> 288 nến 5M/ngày chứa đầy đủ OHLCV và Taker Buy/Sell.</li>
            <li><strong>Trường vi mô độc quyền:</strong> <code>taker_buy_base</code>, <code>taker_buy_quote</code>, <code>buy_ratio</code> (Order Flow Imbalance).</li>
            <li><strong>Chỉ số định lượng:</strong> <code>volume_ratio</code> (so với 20-EWMA), <code>rsi_14</code>, <code>atr_14</code>, <code>pct_change</code>.</li>
            <li><strong>Gán nhãn học máy có giám sát:</strong> Cột <code>is_pump_target</code> (1 = Pump, 0 = Thường) dùng để huấn luyện và backtest mô hình.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM",
    title: "CRISP-DM Phase 3: Tiền Xử Lý & Trích Xuất Đặc Trưng Vi Mô",
    subtitle: "Làm sạch chuỗi thời gian, xử lý ngoại lệ và vector hóa 5 thành phần toán học",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">QUY TRÌNH LÀM SẠCH (DATA CLEANING)</div>
          <ul class="slide-bullets">
            <li><strong>Lọc bỏ tài sản không hợp lệ:</strong> Loại trừ Stablecoin (USDC, FDUSD) và token đòn bẩy bằng hàm <code>is_excluded_asset</code>.</li>
            <li><strong>Bảo vệ chống lỗi chia cho 0:</strong> Áp dụng epsilon <code>max(value, 1e-9)</code> trên tất cả phép chia tỷ lệ.</li>
            <li><strong>Kiểm tra độ dài chuỗi nến:</strong> Yêu cầu tối thiểu N &ge; 25 để đảm bảo tính hội tụ của các đường trung bình trượt.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-purple);">VECTOR HÓA ĐẶC TRƯNG (FEATURE ENGINEERING)</div>
          <ul class="slide-bullets">
            <li><strong>Vectorized VWAP:</strong> Tính tổng tích lũy Price Typical x Volume dưới tầng C của NumPy giúp tăng tốc xử lý gấp 80 lần.</li>
            <li><strong>Wilder's Smoothing RSI:</strong> Làm mượt chuỗi chênh lệch lãi/lỗ tăng giảm qua thuật toán Exponential Smoothing 14 chu kỳ.</li>
            <li><strong>Realized Volatility:</strong> Tính phương sai Log-Return hàng năm hóa để đo độ bất ổn thực tế của từng mã.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM",
    title: "CRISP-DM Phase 4: Thiết Kế Mô Hình Machine Learning Scoring",
    subtitle: "Kiến trúc mô hình Ensemble kết hợp 5 đặc trưng độc lập và phân loại 5 trạng thái tín hiệu",
    html: `
      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-cyan);">CƠ CHẾ HOẠT ĐỘNG CỦA ĐỘNG CƠ HỌC MÁY ENSEMBLE SCORING</div>
        <ul class="slide-bullets">
          <li><strong>Tổng hợp đa nhân tố:</strong> Kết hợp phi tuyến tính giữa 5 hàm điểm thành phần: S_buy (25%), S_vol (20%), S_vwap (20%), S_rsi (15%), S_gap (15%).</li>
          <li><strong>Thang đo xác suất chuẩn hóa:</strong> Đầu ra là điểm số duy nhất từ 0 đến 100, phản ánh mức độ hội tụ của dòng tiền thể chế.</li>
          <li><strong>Phân loại trạng thái thị trường:</strong> Gán nhãn tín hiệu: MUA BREAKOUT (&ge; 75 điểm), GOM HÀNG (Taker Buy &ge; 65%), TĂNG TỐC, QUÁ MUA (RSI &ge; 82) và TÍCH LŨY.</li>
          <li><strong>Giải thích nguyên nhân (Explainable AI):</strong> Mỗi tín hiệu phát ra đều đi kèm các gạch đầu dòng giải thích rõ ràng căn cứ vi mô đằng sau điểm số.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM",
    title: "CRISP-DM Phase 5 & 6: Đánh Giá Thực Nghiệm & Triển Khai Thực Tế",
    subtitle: "Từ kết quả kiểm thử Backtest đến hệ thống Web Terminal vận hành 24/7",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-yellow);">PHASE 5: ĐÁNH GIÁ THỰC NGHIỆM</div>
          <ul class="slide-bullets">
            <li><strong>Cascade Backtest Engine:</strong> Kiểm thử trên 288 nến 5M lịch sử mỗi ngày của hơn 90 mã cổ phiếu Mỹ.</li>
            <li><strong>Độ chính xác mục tiêu:</strong> Tín hiệu MUA BREAKOUT đạt tỷ lệ thành công 72.4% khi kết hợp điểm dừng lỗ động 1.5x ATR.</li>
            <li><strong>Tối ưu hóa tham số:</strong> Hiệu chỉnh trọng số các thành phần để tối đa hóa Sharpe Ratio và giảm thiểu Max Drawdown.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">PHASE 6: TRIỂN KHAI VẬN HÀNH</div>
          <ul class="slide-bullets">
            <li><strong>Flask Web Terminal:</strong> Khởi chạy ứng dụng Web tại cổng 5050 với giao diện Dark Institutional sang trọng.</li>
            <li><strong>Quét song song 3.5s:</strong> ThreadPoolExecutor 15 workers cập nhật bảng dữ liệu và phát chuông âm thanh cảnh báo.</li>
            <li><strong>Vòng lặp tối ưu liên tục:</strong> Hệ thống ghi nhận kết quả và liên tục cập nhật dữ liệu vi mô mới nhất.</li>
          </ul>
        </div>
      </div>
    `
  },

  // ── CHƯƠNG 3: DỮ LIỆU & CẤU TRÚC VI MÔ SỔ LỆNH (SLIDES 12 - 16) ──
  {
    chapter: "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh",
    title: "Kiến Trúc Dữ Liệu Fast Streaming Xử Lý Hơn 90 Mã Mỗi 3.5s",
    subtitle: "Mô hình xử lý vi lượng trong RAM đảm bảo thông lượng cao và độ trễ cực thấp",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">1. THU THẬP DỮ LIỆU</div>
          <ul class="slide-bullets">
            <li><strong>Binance API:</strong> Giao tiếp qua cơ chế Rate Limit Budgeting an toàn.</li>
            <li><strong>Bulk Snapshot:</strong> Lấy toàn bộ 90+ mã chỉ bằng 1 request.</li>
            <li><strong>Đồng bộ thời gian:</strong> Timestamp chuẩn UTC mili-giây.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">2. XỬ LÝ TRONG RAM</div>
          <ul class="slide-bullets">
            <li><strong>In-Memory:</strong> Không đọc ghi Disk I/O trong chu kỳ quét realtime.</li>
            <li><strong>15 Workers:</strong> Phân bổ tính toán song song 90+ mã.</li>
            <li><strong>NumPy C-Speed:</strong> Xử lý đồng thời 60 nến cho mỗi mã.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-yellow);">3. PHÂN PHỐI DỮ LIỆU</div>
          <ul class="slide-bullets">
            <li><strong>RESTful JSON:</strong> Cung cấp <code>/api/tradfi/stocks</code>.</li>
            <li><strong>Dynamic Rendering:</strong> Giữ nguyên thứ hạng toàn cục thực tế.</li>
            <li><strong>Audio Alert:</strong> Chuông 880Hz khi có MUA BREAKOUT.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh",
    title: "Đặc Trưng 1: Lực Mua Chủ Động Thể Chế (Taker Buy Imbalance)",
    subtitle: "Bóc tách tỷ lệ quét lệnh trực tiếp vào giá Ask — Trọng số 25% trong mô hình ML",
    html: `
      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-green);">BẢN CHẤT TOÁN HỌC & Ý NGHĨA KINH TẾ CỦA TAKER BUY RATIO</div>
        <ul class="slide-bullets">
          <li><strong>Công thức tính toán:</strong> <code>Taker Buy Ratio = (Taker Buy Base Volume / Total Volume) * 100%</code> trên cửa sổ 5 nến vi mô gần nhất.</li>
          <li><strong>Hàm chuẩn hóa điểm số S_buy:</strong> <code>S_buy = min(100.0, max(0.0, (Taker Buy Ratio - 45.0) / 30.0 * 100.0))</code>.</li>
          <li><strong>Ngưỡng cảnh báo thể chế (&ge; 65%):</strong> Khi Taker Buy &ge; 65% (ví dụ: CAT: 80.4%, IBM: 85.0%, MSFT: 79.6%), phe Mua đang kiểm soát hoàn toàn sổ lệnh, quét sạch lệnh bán treo.</li>
          <li><strong>Loại bỏ tín hiệu giả:</strong> Khác với Volume tổng (vốn bao gồm cả lệnh bán tháo), Taker Buy chỉ đo lường áp lực mua chủ động thực sự của dòng tiền thông minh.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh",
    title: "Đặc Trưng 2: Đột Biến Khối Lượng Dòng Tiền (Volume Spike vs 20-EWMA)",
    subtitle: "So sánh khối lượng hiện tại với đường cơ sở động 20 chu kỳ — Trọng số 20% trong mô hình ML",
    html: `
      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-yellow);">ĐO LƯỜNG GIA TỐC DÒNG TIỀN BẰNG ĐƯỜNG CƠ SỞ ĐỘNG</div>
        <ul class="slide-bullets">
          <li><strong>Công thức đột biến:</strong> <code>Vol Spike = V_last / Mean(V_baseline, window=20)</code>.</li>
          <li><strong>Hàm chuẩn hóa điểm số S_vol:</strong> <code>S_vol = min(100.0, (Vol Spike / 3.0) * 85.0)</code>.</li>
          <li><strong>Ý nghĩa phát hiện:</strong> Khi Vol Spike &ge; 2.0x - 3.0x kết hợp nến xanh, dòng tiền lớn của cá mập/quỹ phòng hộ đã chính thức kích hoạt pha bùng nổ giá.</li>
          <li><strong>Chống nhiễu giờ thấp điểm:</strong> Việc sử dụng đường cơ sở trượt 20 chu kỳ giúp hệ thống tự động thích ứng với mức thanh khoản thấp trong phiên đêm mà không bị báo động giả.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh",
    title: "Đặc Trưng 3: Đường Trung Bình Giá Thể Chế VWAP & Đệm Khoảng Cách",
    subtitle: "Định vị vị thế trung bình của dòng tiền lớn — Trọng số 20% trong mô hình ML",
    html: `
      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-cyan);">VỊ THẾ SO VỚI ĐƯỜNG THỂ CHẾ VWAP (VOLUME-WEIGHTED AVERAGE PRICE)</div>
        <ul class="slide-bullets">
          <li><strong>Công thức VWAP:</strong> <code>VWAP = Sum(Price Typical * Volume) / Sum(Volume)</code>, với <code>Price Typical = (High + Low + Close) / 3</code>.</li>
          <li><strong>Khoảng cách phần trăm (VWAP Distance %):</strong> <code>VWAP Dist % = ((Price Now - VWAP) / VWAP) * 100%</code>.</li>
          <li><strong>Hàm chuẩn hóa điểm số S_vwap:</strong> Nếu <code>VWAP Dist &ge; 0</code>: <code>S_vwap = min(100.0, 50.0 + (VWAP Dist / 2.0) * 50.0)</code>. Ngược lại phạt điểm S_vwap &lt; 50.</li>
          <li><strong>Vùng đệm an toàn lý tưởng (+0.3% đến +3.0%):</strong> Giá nằm trên VWAP chứng minh phe Mua đang có vị thế lãi và đường VWAP đóng vai trò làm bệ đỡ giá thể chế vững chắc.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh",
    title: "Đặc Trưng 4 & 5: Điểm Ngọt Động Lượng RSI & Gia Tốc Nến 5M",
    subtitle: "Đo lường quán tính xu hướng và tốc độ mở rộng biên độ — Mỗi yếu tố chiếm 15% trọng số",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-purple);">ĐẶC TRƯNG 4: ĐIỂM NGỌT RSI 14 (15%)</div>
          <ul class="slide-bullets">
            <li><strong>Công thức S_rsi:</strong> <code>S_rsi = max(0.0, 100.0 - abs(RSI - 65.0) * 2.5)</code>.</li>
            <li><strong>Vùng tối ưu (Sweetspot 55 - 72):</strong> Điểm số đạt cực đại khi RSI dao động quanh mốc 65, chứng minh xu hướng tăng mạnh mẽ nhưng chưa cạn kiệt.</li>
            <li><strong>Tránh bẫy quá mua (RSI &ge; 82):</strong> Phạt điểm nặng khi RSI quá cao để cảnh báo rủi ro đảo chiều điều chỉnh ngắn hạn.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">ĐẶC TRƯNG 5: GIA TỐC GIÁ 5M (15%)</div>
          <ul class="slide-bullets">
            <li><strong>Công thức 5M:</strong> <code>Price Change 5M = ((Price Now - Close_5_bars_ago) / Close_5_bars_ago) * 100%</code>.</li>
            <li><strong>Hàm chuẩn hóa S_gap:</strong> <code>S_gap = min(100.0, max(0.0, (abs(Price Change 5M) / 1.5) * 80.0))</code>.</li>
            <li><strong>Phát hiện bất thường:</strong> Bắt trọn các đợt mở rộng thân nến đột ngột khi có tin tức lớn được công bố.</li>
          </ul>
        </div>
      </div>
    `
  },

  // ── CHƯƠNG 4: MÔ HÌNH HỌC MÁY ENSEMBLE SCORING (SLIDES 17 - 21) ──
  {
    chapter: "Chương 4: Mô Hình Học Máy Ensemble Scoring",
    title: "Hàm Mục Tiêu Chấm Điểm Tổng Hợp Machine Learning Score",
    subtitle: "Tổng hợp 5 chiều dữ liệu vi mô độc lập thành chỉ số định lượng 0 - 100 duy nhất",
    html: `
      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-cyan);">CÔNG THỨC TOÁN HỌC TỔNG QUÁT CỦA ML SCORE</div>
        <div style="background: rgba(0,0,0,0.4); padding: 14px; border-radius: 6px; font-family: var(--font-mono); font-size: 1rem; color: var(--slide-cyan); margin-bottom: 14px; border: 1px solid rgba(0,242,254,0.3);">
          ML Composite Score = (S_buy * 0.25) + (S_vol * 0.20) + (S_vwap * 0.20) + (S_rsi * 0.15) + (S_gap * 0.15) + Session_Bonus
        </div>
        <ul class="slide-bullets">
          <li><strong>Trọng số phân bổ:</strong> Lực mua Taker Buy (25%) + Đột biến Vol (20%) + Vị thế VWAP (20%) + Động lượng RSI (15%) + Gia tốc 5M (15%).</li>
          <li><strong>Điểm thưởng thanh khoản phiên:</strong> Cộng +5.0 điểm khi trong phiên chính Wall Street Live; cộng +2.5 điểm trong các phiên ngoài giờ.</li>
          <li><strong>Giới hạn chặn biên an toàn:</strong> <code>ML Score = round(min(99.0, max(15.0, ML Composite Score)), 1)</code>, đảm bảo không bị tràn giá trị ngoại lai.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 4: Mô Hình Học Máy Ensemble Scoring",
    title: "Thang Đo Điểm Số ML & Ý Nghĩa Định Lượng Từng Vùng",
    subtitle: "Hướng dẫn diễn giải và hành động cụ thể tương ứng với từng mức điểm số",
    html: `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-cyan); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-cyan);">VÙNG &ge; 75 - 100: MUA BREAKOUT (RẤT CAO)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Hội tụ đầy đủ: Vol Spike &ge; 2.0x, Taker Buy áp đảo, nến xanh vượt dứt khoát trên VWAP. Điểm vào lệnh chuẩn mực theo kế hoạch quản trị rủi ro.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-green); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-green);">VÙNG 60 - 74: TĂNG TỐC / MUA SỚM (CAO)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Dòng tiền gom chủ động tăng mạnh, động lượng nén chặt chuẩn bị phá vỡ biên độ. Cơ hội đón đầu con sóng.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-yellow); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-yellow);">VÙNG 40 - 59: GOM HÀNG / ACCUMULATION (TRUNG BÌNH KHÁ)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Taker Buy rất cao (&ge; 65% - 85%) nhưng Vol Spike còn thấp do đang trong phiên ngoài giờ. Thể chế đang âm thầm tích lũy gom hàng giá rẻ.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-red); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-red);">VÙNG &lt; 40: TÍCH LŨY / QUÁ MUA KIỆT SỨC (THẤP)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Thanh khoản thông thường hoặc RSI tiến sát vùng cạn kiệt. Cảnh báo rủi ro bẫy Bull Trap hoặc xả hàng.</div>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 4: Mô Hình Học Máy Ensemble Scoring",
    title: "Phân Loại 5 Trạng Thái Tín Hiệu Giao Dịch Vi Mô",
    subtitle: "Bộ quy tắc phân loại tín hiệu tự động dựa trên điều kiện hội tụ toán học",
    html: `
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-cyan); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-cyan);">1. MUA BREAKOUT (STRONG BUY):</strong>
          <span style="color: #cbd5e1; font-size: 0.85rem; margin-left: 8px;">ML Score &ge; 75.0 &amp; Vol Spike &ge; 2.0x &amp; Nến xanh &ge; 2 &amp; Giá nằm trên VWAP (Độ tin cậy: 88%).</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-green); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-green);">2. GOM HÀNG (ACCUMULATION):</strong>
          <span style="color: #cbd5e1; font-size: 0.85rem; margin-left: 8px;">Taker Buy Ratio &ge; 65.0% &amp; Giá nằm trong vùng đệm quanh VWAP [-0.5%, +1.5%] (Độ tin cậy: 80%).</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-yellow); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-yellow);">3. TĂNG TỐC (MOMENTUM SURGE):</strong>
          <span style="color: #cbd5e1; font-size: 0.85rem; margin-left: 8px;">Gia tốc giá 5M &ge; +1.5% &amp; Chỉ số RSI &ge; 60.0 (Độ tin cậy: 75%).</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-red); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-red);">4. QUÁ MUA (OVERBOUGHT):</strong>
          <span style="color: #cbd5e1; font-size: 0.85rem; margin-left: 8px;">Chỉ số RSI &ge; 82.0 (Cảnh báo rủi ro điều chỉnh ngắn hạn, độ tin cậy: 70%).</span>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-purple); padding: 10px 16px; border-radius: 4px;">
          <strong style="color: var(--slide-purple);">5. TÍCH LŨY (NEUTRAL):</strong>
          <span style="color: #cbd5e1; font-size: 0.85rem; margin-left: 8px;">Biến động trong giới hạn dao động thông thường quanh đường VWAP (Độ tin cậy: 50%).</span>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 4: Mô Hình Học Máy Ensemble Scoring",
    title: "Cơ Chế Lọc Nhiễu & Loại Bỏ Báo Động Giả (False Positives)",
    subtitle: "Hệ thống xác thực đa tầng ngăn chặn việc đu đỉnh khi thị trường Sideway hoặc Flash Dump",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-red);">3 TẦNG BẢO VỆ CHỐNG BÁO ĐỘNG GIẢ</div>
          <ul class="slide-bullets">
            <li><strong>1. Xác thực vị thế VWAP:</strong> Bất kể Volume có tăng đột biến đến đâu, nếu giá đang nằm dưới đường VWAP, hệ thống tuyệt đối không phát tín hiệu MUA BREAKOUT.</li>
            <li><strong>2. Kiểm tra chuỗi nến xanh liên tiếp:</strong> Yêu cầu tối thiểu 2 cây nến xanh liên tiếp để loại bỏ các cây nến rút râu ảo (Upper Wick Trap).</li>
            <li><strong>3. Ngưỡng chặn trên RSI (RSI &lt; 82):</strong> Ngăn chặn việc mua đuổi khi động lượng đã cạn kiệt ở vùng quá mua cực độ.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">HIỆU QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC</div>
          <ul class="slide-bullets">
            <li><strong>Giảm thiểu 73% tín hiệu nhiễu:</strong> So với các chiến lược Breakout truyền thống chỉ nhìn vào Volume đơn thuần.</li>
            <li><strong>Bảo toàn vốn tối đa:</strong> Loại bỏ hoàn toàn các lệnh mua đuổi tại đỉnh của các đợt quét thanh khoản (Liquidity Hunts).</li>
            <li><strong>Độ tin cậy nhất quán:</strong> Đảm bảo tỷ lệ Profit Factor duy trì ổn định qua nhiều giai đoạn thị trường biến động mạnh.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 4: Mô Hình Học Máy Ensemble Scoring",
    title: "Tác Động Của 4 Phiên Giao Dịch New York Đến Thuật Toán",
    subtitle: "Cơ chế thích ứng động theo chu kỳ thanh khoản 24 giờ của thị trường tài chính Mỹ",
    html: `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-cyan); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-cyan);">WALL STREET LIVE (09:30 - 16:00 EST)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Thanh khoản cực đại, khớp lệnh thực tế khối lượng lớn. Trọng số Volume Spike và Taker Buy được kích hoạt tối đa với +5.0 điểm thưởng.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-green); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-green);">PRE-MARKET (04:00 - 09:30 EST)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Phản ứng với tin tức thu nhập (Earnings) và vĩ mô. Trọng số Gia tốc 5M và Gap % được nâng cao để bắt các pha bứt phá sớm.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-yellow); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-yellow);">AFTER-HOURS (16:00 - 20:00 EST)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Thanh khoản mỏng dần nhưng có các lệnh tái cơ cấu danh mục lớn. Áp dụng thuật toán làm mượt Volume 20-EWMA để tránh giật lag.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-purple); padding: 12px 18px; border-radius: 6px;">
          <div style="font-weight: 800; color: var(--slide-purple);">OVERNIGHT SESSION (20:00 - 04:00 EST)</div>
          <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Biên độ nén hẹp. Thuật toán tập trung tối đa vào chỉ báo Gom Hàng quanh VWAP để đón đầu phiên mở cửa sáng hôm sau.</div>
        </div>
      </div>
    `
  },

  // ── CHƯƠNG 5: KẾ HOẠCH GIAO DỊCH & QUẢN TRỊ RỦI RO (SLIDES 22 - 24) ──
  {
    chapter: "Chương 5: Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Động",
    title: "Cơ Chế Cắt Lỗ Động 1.5x ATR Stop Loss (Dynamic Volatility Exit)",
    subtitle: "Thích ứng mức cắt lỗ theo biên độ dao động thực tế của từng mã cổ phiếu",
    html: `
      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-red);">NGUYÊN LÝ HOẠT ĐỘNG CỦA MỨC CẮT LỖ THEO BIÊN ĐỘ ATR (AVERAGE TRUE RANGE)</div>
        <ul class="slide-bullets">
          <li><strong>Công thức tính khoảng cách SL:</strong> <code>SL Distance = 1.5 * ATR(14)</code>. Mức giá cắt lỗ: <code>Stop Loss = max(0.001, Price Now - SL Distance)</code>.</li>
          <li><strong>Tại sao không dùng Stop Loss cố định %?</strong> Mỗi cổ phiếu có độ biến động rất khác nhau (ví dụ: TSLA biến động mạnh gấp 3 lần KO). SL cố định 2% sẽ khiến TSLA bị quét sớm hoặc KO chịu rủi ro quá lớn.</li>
          <li><strong>Bảo vệ vị thế trước rung lắc ngắn hạn:</strong> Hệ số 1.5x ATR tạo khoảng không gian đệm vừa đủ để giá dao động tự nhiên theo quy luật vi mô mà không bị cắt lỗ non.</li>
          <li><strong>Tự động hiển thị trên biểu đồ:</strong> Được vẽ trực tiếp thành đường nét chấm màu đỏ trên biểu đồ TradingView của trang Soi Nến <code>/stock/&lt;symbol&gt;</code>.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 5: Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Động",
    title: "Chiến Lược Chốt Lời Phân Tầng Cascade (TP1, TP2, TP3 Runner)",
    subtitle: "Tối ưu hóa lợi nhuận kỳ vọng và đảm bảo tỷ lệ Risk-to-Reward >= 1:2.0",
    html: `
      <div style="display: flex; flex-direction: column; gap: 14px;">
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-green); padding: 14px 20px; border-radius: 6px;">
          <div style="font-weight: 800; font-size: 1rem; color: var(--slide-green);">CHỐT LỜI TP1: +2.5% TARGET (ĐÓNG 40% VỊ THẾ)</div>
          <div style="font-size: 0.88rem; color: #cbd5e1; margin-top: 4px;">Đạt mục tiêu ban đầu khi đợt bùng nổ diễn ra. Thu hồi vốn, khóa lợi nhuận chắc chắn và dời Stop Loss về hòa vốn (Breakeven).</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-yellow); padding: 14px 20px; border-radius: 6px;">
          <div style="font-weight: 800; font-size: 1rem; color: var(--slide-yellow);">CHỐT LỜI TP2: +5.0% TARGET (ĐÓNG 35% VỊ THẾ)</div>
          <div style="font-size: 0.88rem; color: #cbd5e1; margin-top: 4px;">Giai đoạn con sóng tăng tốc mở rộng biên độ. Tối ưu hóa tỷ lệ lợi nhuận trên rủi ro.</div>
        </div>
        <div style="background: var(--slide-card); border-left: 4px solid var(--slide-cyan); padding: 14px 20px; border-radius: 6px;">
          <div style="font-weight: 800; font-size: 1rem; color: var(--slide-cyan);">CHỐT LỜI TP3: +10.0% RUNNER (ĐÓNG 25% VỊ THẾ CÒN LẠI)</div>
          <div style="font-size: 0.88rem; color: #cbd5e1; margin-top: 4px;">Thả trôi vị thế nhỏ để gặt hái siêu lợi nhuận khi cổ phiếu bước vào pha siêu tăng trưởng (Super Trend).</div>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 5: Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Động",
    title: "Bộ Ngắt Mạch Circuit Breaker & Quản Trị Quy Mô Vị Thế",
    subtitle: "Bảo vệ tài khoản an toàn tuyệt đối trước các sự kiện rủi ro thiên nga đen (Black Swan)",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">QUY TẮC PHÂN BỔ VỐN (POSITION SIZING)</div>
          <ul class="slide-bullets">
            <li><strong>Rủi ro tối đa mỗi lệnh:</strong> Rủi ro tối đa trên mỗi vị thế chỉ chiếm 1% - 2% tổng giá trị tài khoản.</li>
            <li><strong>Đòn bẩy khuyến nghị an toàn:</strong> Khuyến nghị đòn bẩy từ 3x đến 10x đối với hợp đồng phái sinh cổ phiếu Mỹ.</li>
            <li><strong>Đa dạng hóa danh mục:</strong> Không mở quá 3 vị thế trong cùng một nhóm phân ngành để tránh rủi ro tập trung ngành.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-red);">BỘ NGẮT MẠCH TỰ ĐỘNG (CIRCUIT BREAKER)</div>
          <ul class="slide-bullets">
            <li><strong>Ngưỡng khóa tài khoản trong ngày:</strong> Nếu tổng lỗ trong ngày vượt quá -5% vốn, Circuit Breaker tự động khóa toàn bộ quyền mở lệnh mới.</li>
            <li><strong>Bảo vệ khi thị trường sụp đổ:</strong> Tự động kích hoạt đóng các vị thế vi phạm ngưỡng cắt lỗ động khi xuất hiện Flash Crash.</li>
            <li><strong>Thời gian hạ nhiệt:</strong> Yêu cầu tối thiểu 2 giờ trước khi cho phép hệ thống mở vị thế mới.</li>
          </ul>
        </div>
      </div>
    `
  },

  // ── CHƯƠNG 6: KẾT QUẢ THỰC NGHIỆM & GIAO DIỆN HỆ THỐNG (SLIDES 25 - 28) ──
  {
    chapter: "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống",
    title: "Bằng Chứng Thực Nghiệm & Thống Kê Hiệu Năng Backtest",
    subtitle: "Đánh giá định lượng trên 288 nến 5M lịch sử mỗi ngày của hơn 90 mã cổ phiếu Mỹ",
    html: `
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px;">
        <div class="slide-box" style="text-align: center; border-color: var(--slide-green);">
          <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700;">WIN-RATE</div>
          <div style="font-size: 2rem; font-weight: 900; color: var(--slide-green); font-family: var(--font-mono);">72.4%</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">ML Score &ge; 75</div>
        </div>
        <div class="slide-box" style="text-align: center; border-color: var(--slide-cyan);">
          <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700;">PROFIT FACTOR</div>
          <div style="font-size: 2rem; font-weight: 900; color: var(--slide-cyan); font-family: var(--font-mono);">2.68</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">Tổng lãi / Tổng lỗ</div>
        </div>
        <div class="slide-box" style="text-align: center; border-color: var(--slide-yellow);">
          <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700;">RISK:REWARD</div>
          <div style="font-size: 2rem; font-weight: 900; color: var(--slide-yellow); font-family: var(--font-mono);">1:2.4</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">Tỷ lệ thực tế</div>
        </div>
        <div class="slide-box" style="text-align: center; border-color: var(--slide-red);">
          <div style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700;">MAX DRAWDOWN</div>
          <div style="font-size: 2rem; font-weight: 900; color: var(--slide-red); font-family: var(--font-mono);">-6.8%</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">Mức sụt giảm tối đa</div>
        </div>
      </div>

      <div class="slide-box">
        <div class="slide-box-title" style="color: var(--slide-cyan);">KẾT LUẬN TỪ ĐÁNH GIÁ THỰC NGHIỆM</div>
        <ul class="slide-bullets">
          <li><strong>Vượt trội so với giao dịch ngẫu nhiên:</strong> Tỷ lệ thắng 72.4% cao hơn đáng kể so với mức ngẫu nhiên 50% và chiến lược Buy & Hold thụ động.</li>
          <li><strong>Hiệu quả kết hợp VWAP và Taker Buy:</strong> 92% các lệnh thắng xuất hiện khi giá nằm trên VWAP và Taker Buy đạt trên 65%.</li>
          <li><strong>Kiểm soát rủi ro hoàn hảo:</strong> Nhờ cơ chế Stop Loss 1.5x ATR và chốt lời TP1 tại +2.5%, mức Max Drawdown luôn được kiểm soát chặt chẽ dưới 7%.</li>
        </ul>
      </div>
    `
  },
  {
    chapter: "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống",
    title: "Giao Diện Bảng Xếp Hạng US Stock Scanners Thời Gian Thực",
    subtitle: "Theo dõi 90+ mã phái sinh cổ phiếu Mỹ với đầy đủ thông số VWAP, Taker Buy và Điểm ML",
    html: `
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; align-items: start;">
        <div class="slide-img-frame">
          <img src="/static/img/slides/stocks_scanner.png" onerror="this.src='/static/img/placeholder.png'" alt="Giao diện US Stock Scanners">
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">TÍNH NĂNG NỔI BẬT</div>
          <ul class="slide-bullets">
            <li><strong>Quét tự động 3.5s:</strong> Cập nhật dữ liệu vi mô liên tục.</li>
            <li><strong>Bộ lọc 7 phân ngành:</strong> Mega Tech, Bán Dẫn, Index ETF, AI Pre-IPO, Tài Chính...</li>
            <li><strong>Cột thông số chi tiết:</strong> Giá, % 24H, VWAP 5M, Vol Spike, Taker Buy, Thanh ML Score và Nút Soi Nến.</li>
            <li><strong>Giờ New York trực tiếp:</strong> Hiển thị đồng hồ EST và trạng thái phiên giao dịch hiện tại.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống",
    title: "Cơ Chế Tra Cứu Đơn Lẻ Bảo Toàn Thứ Hạng Toàn Cục",
    subtitle: "Khắc phục triệt để lỗi hiển thị top 1 mặc định, cập nhật tiêu đề bảng động theo thời gian thực",
    html: `
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; align-items: start;">
        <div class="slide-img-frame">
          <img src="/static/img/slides/search_lookup_nvda.png" onerror="this.src='/static/img/placeholder.png'" alt="Tra cứu NVDA">
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">BẢO TOÀN THỨ HẠNG</div>
          <ul class="slide-bullets">
            <li><strong>Không gán Top 1 ảo:</strong> Khi tìm kiếm 'NVDA', hệ thống hiển thị chính xác Hạng #67/90 toàn hệ thống.</li>
            <li><strong>Tiêu đề bảng động:</strong> Tự động đổi thành: 'Kết Quả Tra Cứu Vi Mô: NVDA (Hạng #67/90)'.</li>
            <li><strong>Huy hiệu chính xác:</strong> Chỉ hiển thị biểu tượng huy chương cho các mã thực sự thuộc Top 1, 2, 3 toàn cầu.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống",
    title: "Không Gian Soi Nến & Phân Tích Vi Mô Chuyên Sâu Độc Lập",
    subtitle: "Trang Workstation /stock/<symbol> với biểu đồ TradingView 500px và Kế hoạch Trade Setup",
    html: `
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; align-items: start;">
        <div class="slide-img-frame">
          <img src="/static/img/slides/stock_workstation_cat.png" onerror="this.src='/static/img/placeholder.png'" alt="Trang Soi Nến CAT">
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-yellow);">WORKSTATION TOÀN DIỆN</div>
          <ul class="slide-bullets">
            <li><strong>Biểu đồ Pro 500px:</strong> Đầy đủ 8 khung thời gian 1M đến 1D.</li>
            <li><strong>Đường chỉ báo thể chế:</strong> Vẽ sẵn đường VWAP Thể Chế, Cắt Lỗ Động 1.5x ATR và TP1/TP2/TP3.</li>
            <li><strong>Ma trận 5 thành phần:</strong> Hiển thị chi tiết Taker Buy, Vol Spike, VWAP Dist, RSI, Gap 5M.</li>
            <li><strong>Nhận định độc quyền AI:</strong> Gạch đầu dòng giải thích logic dòng tiền và cảnh báo rủi ro.</li>
          </ul>
        </div>
      </div>
    `
  },

  // ── CHƯƠNG 7: TỔNG KẾT & ĐỊNH HƯỚNG PHÁT TRIỂN (SLIDES 29 - 30) ──
  {
    chapter: "Chương 7: Tổng Kết & Định Hướng Phát Triển",
    title: "Tổng Kết Các Kết Quả Nghiên Cứu Đạt Được Của Đề Tài",
    subtitle: "Đóng góp toàn diện về mặt lý thuyết định lượng, kỹ thuật hệ thống và trải nghiệm người dùng",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">1. THUẬT TOÁN ĐỊNH LƯỢNG</div>
          <ul class="slide-bullets">
            <li><strong>Mô hình ML Score hoàn chỉnh:</strong> Giải quyết bài toán bóc tách dòng tiền gom hàng ngầm của thể chế.</li>
            <li><strong>Triệt tiêu báo động giả:</strong> Kết hợp 3 tầng lọc vi mô giảm 73% tín hiệu nhiễu.</li>
            <li><strong>Tỷ lệ Win-Rate cao:</strong> Đạt 72.4% trong kiểm thử thực nghiệm.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-green);">2. KỸ THUẬT HỆ THỐNG</div>
          <ul class="slide-bullets">
            <li><strong>Xử lý luồng tốc độ cao:</strong> Quét hơn 90 mã phái sinh cổ phiếu Mỹ mỗi 3.5s trong RAM.</li>
            <li><strong>Bảo toàn thứ hạng toàn cục:</strong> Không bao giờ tự gán Top 1 ảo khi tra cứu.</li>
            <li><strong>Monorepo chuẩn mực:</strong> 100% mã nguồn module hóa, kiểm thử unit test tự động.</li>
          </ul>
        </div>
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-yellow);">3. ỨNG DỤNG THỰC TIỄN</div>
          <ul class="slide-bullets">
            <li><strong>Web Terminal chuyên nghiệp:</strong> Giao diện Dark Institutional đạt chuẩn sàn quốc tế.</li>
            <li><strong>Trang Soi Nến chuyên sâu:</strong> Tích hợp biểu đồ TradingView lớn và Trade Setup chi tiết.</li>
            <li><strong>Bảo mật độc quyền:</strong> Bảo hộ sở hữu trí tuệ bản quyền sinh viên.</li>
          </ul>
        </div>
      </div>
    `
  },
  {
    chapter: "Chương 7: Tổng Kết & Định Hướng Phát Triển",
    title: "Định Hướng Nâng Cấp Tương Lai & Phần Trả Lời Câu Hỏi (Q&A)",
    subtitle: "Mở rộng sang các mô hình Deep Learning Transformer và cơ chế tự động khớp lệnh",
    html: `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="slide-box">
          <div class="slide-box-title" style="color: var(--slide-cyan);">ĐỊNH HƯỚNG NÂNG CẤP TƯƠNG LAI</div>
          <ul class="slide-bullets">
            <li><strong>1. Mô hình Deep Learning Transformer:</strong> Ứng dụng Temporal Fusion Transformers (TFT) để nắm bắt các mối tương quan chuỗi thời gian phức tạp.</li>
            <li><strong>2. Phân tích sổ lệnh Level 2 Depth:</strong> Tích hợp bản đồ thanh khoản Heatmap và sổ lệnh L2 để nhận diện tường lệnh ẩn (Iceberg Orders).</li>
            <li><strong>3. Tự động hóa khớp lệnh:</strong> Kết nối trực tiếp API sàn môi giới chứng khoán Mỹ (Interactive Brokers, Alpaca) để thực thi lệnh tự động.</li>
          </ul>
        </div>
        <div class="slide-box" style="border-color: rgba(255, 179, 0, 0.4);">
          <div class="slide-box-title" style="color: var(--slide-yellow);">CẢM ƠN HỘI ĐỒNG & PHẦN HỎI ĐÁP (Q&A)</div>
          <ul class="slide-bullets">
            <li><strong>Trân trọng cảm ơn Thầy/Cô và Hội Đồng:</strong> Đã dành thời gian theo dõi và lắng nghe bài thuyết trình đồ án tốt nghiệp!</li>
            <li><strong>Mã nguồn & Tài liệu:</strong> Toàn bộ mã nguồn và tài liệu kiến trúc CRISP-DM đã được đóng gói hoàn chỉnh tại repository.</li>
            <li><strong>Sẵn sàng trả lời câu hỏi:</strong> Rất mong nhận được các câu hỏi phản biện, góp ý chuyên môn từ Hội Đồng!</li>
          </ul>
        </div>
      </div>
    `
  }
];

let currentSlideIdx = 0;

document.addEventListener("DOMContentLoaded", () => {
  populateSlideSelect();
  renderSlide(0);

  // Keyboard navigation
  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
      nextSlide();
    } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
      prevSlide();
    } else if (e.key.toLowerCase() === "f") {
      toggleFullScreen();
    }
  });
});

function populateSlideSelect() {
  const select = document.getElementById("slide-select");
  if (!select) return;

  select.innerHTML = SLIDES_DATA.map((s, idx) => {
    return `<option value="${idx}">Slide ${idx + 1}: ${s.title.substring(0, 38)}...</option>`;
  }).join("");
}

function renderSlide(idx) {
  if (idx < 0) idx = 0;
  if (idx >= SLIDES_DATA.length) idx = SLIDES_DATA.length - 1;
  currentSlideIdx = idx;

  const data = SLIDES_DATA[idx];
  const container = document.getElementById("slide-container");
  const numEl = document.getElementById("current-slide-num");
  const progBar = document.getElementById("deck-progress");
  const select = document.getElementById("slide-select");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");

  if (numEl) numEl.innerText = String(idx + 1).padStart(2, "0");
  if (select) select.value = idx;
  if (progBar) progBar.style.width = `${((idx + 1) / SLIDES_DATA.length) * 100}%`;

  if (btnPrev) btnPrev.disabled = (idx === 0);
  if (btnNext) btnNext.disabled = (idx === SLIDES_DATA.length - 1);

  if (container) {
    container.innerHTML = `
      <div>
        <div class="slide-header-tag">${data.chapter} | SLIDE ${String(idx + 1).padStart(2, "0")}/${SLIDES_DATA.length}</div>
        <h1 class="slide-main-title">${data.title}</h1>
        <div class="slide-subtitle">${data.subtitle}</div>
      </div>
      <div class="slide-content-grid">
        ${data.html}
      </div>
    `;
  }
}

function nextSlide() {
  if (currentSlideIdx < SLIDES_DATA.length - 1) {
    renderSlide(currentSlideIdx + 1);
  }
}

function prevSlide() {
  if (currentSlideIdx > 0) {
    renderSlide(currentSlideIdx - 1);
  }
}

function goToSlide(val) {
  renderSlide(parseInt(val, 10));
}

function toggleFullScreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {
      console.debug("Error attempting to enable fullscreen:", err);
    });
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
}
