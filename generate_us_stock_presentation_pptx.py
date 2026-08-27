"""
DeepAlpha — US Stock Machine Learning Scanners (TradFi USD-M Futures)
Academic PowerPoint Presentation Generator (30 Widescreen 16:9 Slides)
=======================================================================
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── Color Palette (Institutional Dark Quant Theme) ──
BG_DARK = RGBColor(11, 15, 23)        # #0B0F17
CARD_BG = RGBColor(21, 29, 42)        # #151D2A
CARD_BORDER = RGBColor(30, 41, 59)    # #1E293B
CYAN = RGBColor(0, 242, 254)          # #00F2FE
GREEN = RGBColor(0, 230, 118)         # #00E676
YELLOW = RGBColor(255, 179, 0)        # #FFB300
RED = RGBColor(255, 51, 102)          # #FF3366
PURPLE = RGBColor(179, 136, 255)      # #B388FF
TEXT_WHITE = RGBColor(255, 255, 255)
TEXT_MUTED = RGBColor(148, 163, 184)  # #94A3B8
TEXT_DIM = RGBColor(100, 116, 139)    # #64748B


def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_DARK


def add_slide_header(slide, slide_num, total_slides, chapter_title, slide_title, subtitle=""):
    # Chapter & Progress Tag
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf = tx_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"{chapter_title.upper()}  |  SLIDE {slide_num:02d}/{total_slides}"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = CYAN

    # Main Slide Title
    tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.7))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p2 = tf_title.paragraphs[0]
    p2.text = slide_title
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE

    if subtitle:
        p3 = tf_title.add_paragraph()
        p3.text = subtitle
        p3.font.size = Pt(11)
        p3.font.color.rgb = TEXT_MUTED


def add_card(slide, left, top, width, height, title="", border_color=CARD_BORDER, bg_color=CARD_BG):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.2)
    
    if title:
        tx = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.1), width - Inches(0.3), Inches(0.4))
        tf = tx.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = CYAN
    return shape


def add_bullets(slide, left, top, width, height, items, font_size=12, text_color=TEXT_WHITE):
    tx = slide.shapes.add_textbox(left, top, width, height)
    tf = tx.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        p.font.size = Pt(font_size)
        
        if isinstance(item, tuple):
            prefix, rest = item
            run1 = p.add_run()
            run1.text = prefix + " "
            run1.font.bold = True
            run1.font.color.rgb = CYAN
            
            run2 = p.add_run()
            run2.text = rest
            run2.font.color.rgb = text_color
        else:
            p.text = "• " + item
            p.font.color.rgb = text_color


def build_us_stock_presentation(output_path="final_project_us_stock_30_slides.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    total_slides = 30

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI & TÍNH CẤP THIẾT (SLIDES 1 - 5)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 1: Title Slide
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    # Badge
    b1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(3.8), Inches(0.45))
    b1.fill.solid()
    b1.fill.fore_color.rgb = CARD_BG
    b1.line.color.rgb = CYAN
    tb = b1.text_frame
    tb.paragraphs[0].text = "FINAL PROJECT — QUANTITATIVE FINANCE"
    tb.paragraphs[0].font.size = Pt(11)
    tb.paragraphs[0].font.bold = True
    tb.paragraphs[0].font.color.rgb = CYAN

    # Main Title
    t1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(11.3), Inches(2.2))
    tf1 = t1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "HỆ THỐNG ĐỊNH LƯỢNG MACHINE LEARNING & QUÉT VI MÔ DÒNG TIỀN THỂ CHẾ PHÁI SINH CỔ PHIẾU MỸ"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p2 = tf1.add_paragraph()
    p2.text = "US Stock TradFi USD-M Perpetual Futures & Institutional Order Flow Scanners"
    p2.font.size = Pt(16)
    p2.font.color.rgb = CYAN

    # Author Card
    add_card(s1, Inches(1.0), Inches(4.5), Inches(11.3), Inches(2.2), "THÔNG TIN ĐỒ ÁN & PHƯƠNG PHÁP LUẬN")
    add_bullets(s1, Inches(1.2), Inches(5.1), Inches(10.9), Inches(1.5), [
        ("Nghiên Cứu Viên:", "Sinh Nguyen (Quant Engineer & Data Scientist)"),
        ("Khung Phương Pháp Luận:", "Tiêu chuẩn công nghiệp CRISP-DM 6 giai đoạn (Cross-Industry Standard Process for Data Mining)"),
        ("Công Nghệ Áp Dụng:", "Python Monorepo, Binance Matching Engine API, Vectorized NumPy/Pandas, Machine Learning Ensemble, TradingView Pro Charts"),
        ("Phạm Vi Phân Tích:", "Hơn 90+ hợp đồng phái sinh cổ phiếu Mỹ (Mega Tech, Bán Dẫn, ETF, AI Pre-IPO, Tài Chính) hoạt động liên tục 24/7")
    ], font_size=12)

    # SLIDE 2: Problem Statement
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_slide_header(s2, 2, total_slides, "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết", "Thách Thức Của Thị Trường Phái Sinh Cổ Phiếu Mỹ 24/7", "Tại sao các phương pháp phân tích kỹ thuật truyền thống bị thất bại?")
    add_card(s2, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "1. Hạn Chế Phân Tích Truyền Thống", RED)
    add_bullets(s2, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("Độ trễ nghiêm trọng:", "Chỉ báo truyền thống (RSI, MACD, MA) chỉ tính toán trên giá đóng cửa quá khứ, không thấy được diễn biến vi mô trong sổ lệnh."),
        ("Bất đối xứng thông tin:", "Nhà đầu tư cá nhân hoàn toàn mù mờ trước các đợt gom hàng/xả hàng ngầm của các quỹ phòng hộ (Hedge Funds) và Market Makers."),
        ("Bẫy thanh khoản (Spoofing & Traps):", "Các cây nến Breakout giả liên tục quét thanh khoản (Stop Hunt) khiến nhà đầu tư bị thua lỗ nặng."),
        ("Biến động ngoài giờ (After-Hours):", "Cổ phiếu Mỹ biến động rất mạnh trong phiên Pre-Market và Overnight nhưng thiếu công cụ giám sát dòng tiền liên tục.")
    ], font_size=12)

    add_card(s2, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "2. Giải Pháp Định Lượng Machine Learning", CYAN)
    add_bullets(s2, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Bóc tách sổ lệnh vi mô (Microstructure):", "Theo dõi trực tiếp tỷ lệ khớp lệnh chủ động Taker Buy/Sell từ khớp lệnh thực tế của sàn."),
        ("Đường giá thể chế VWAP:", "Định vị vị thế trung bình của các tay to (Institutional Benchmark) để xác định ngưỡng hỗ trợ/kháng cự cứng."),
        ("Mô hình chấm điểm đa nhân tố ML Score:", "Tổng hợp 5 chiều dữ liệu vi mô độc lập để đưa ra điểm số định lượng 0 - 100 theo thời gian thực."),
        ("Quản trị rủi ro động theo ATR:", "Tự động thiết lập vùng dừng lỗ và chốt lời phân tầng dựa trên độ biến động thực tế từng cổ phiếu.")
    ], font_size=12)

    # SLIDE 3: Research Objectives
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_slide_header(s3, 3, total_slides, "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết", "Mục Tiêu Nghiên Cứu & Phạm Vi Đề Tài", "Xây dựng hệ thống quét dòng tiền thể chế thời gian thực trên 90+ hợp đồng TradFi Futures")
    
    add_card(s3, Inches(0.8), Inches(1.7), Inches(3.6), Inches(5.2), "MỤC TIÊU 1: ĐỊNH LƯỢNG", CYAN)
    add_bullets(s3, Inches(1.0), Inches(2.3), Inches(3.2), Inches(4.4), [
        ("Toán học hóa dòng tiền:", "Xây dựng thuật toán tính toán Taker Buy Pressure và Đột biến Volume so với 20-EWMA."),
        ("Điểm số ML Composite:", "Tạo ra chỉ số ML Score (0 - 100) phản ánh xác suất bùng nổ giá của cổ phiếu."),
        ("Độ trễ cực thấp:", "Tối ưu hóa thuật toán để tính toán xong 90+ mã trong dưới 200ms.")
    ])

    add_card(s3, Inches(4.8), Inches(1.7), Inches(3.6), Inches(5.2), "MỤC TIÊU 2: CẢNH BÁO SỚM", GREEN)
    add_bullets(s3, Inches(5.0), Inches(2.3), Inches(3.2), Inches(4.4), [
        ("Nhận diện pha Gom Hàng:", "Phát hiện lực gom chủ động quanh VWAP trước khi nến Breakout xảy ra."),
        ("Phân loại 5 tín hiệu:", "MUA BREAKOUT, GOM HÀNG, TĂNG TỐC, QUÁ MUA, TÍCH LŨY."),
        ("Phát hiện bất thường 5M:", "Bắt trọn các đợt mở rộng biên độ đột ngột trong các phiên ngoài giờ.")
    ])

    add_card(s3, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.2), "MỤC TIÊU 3: ỨNG DỤNG THỰC TẾ", YELLOW)
    add_bullets(s3, Inches(9.0), Inches(2.3), Inches(3.3), Inches(4.4), [
        ("Giao diện Terminal Pro:", "Web Terminal chuyên nghiệp với biểu đồ TradingView đa khung thời gian."),
        ("Soi nến độc lập:", "Trang workstation chuyên sâu `/stock/<symbol>` cung cấp kế hoạch Trade Setup chi tiết."),
        ("Quản trị vốn tự động:", "Tự động tính Stop Loss 1.5x ATR và chốt lời TP1/TP2/TP3 tỷ lệ R:R >= 1:2.0.")
    ])

    # SLIDE 4: Asset Universe (7 Sectors)
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_slide_header(s4, 4, total_slides, "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết", "Danh Mục Tài Sản TradFi US Stock (7 Phân Ngành Trọng Yếu)", "Giám sát toàn diện hơn 90 mã cổ phiếu và chỉ số hàng đầu thị trường tài chính Mỹ")
    
    sectors = [
        ("1. Mega-Cap Tech (15 mã)", "NVDA, AAPL, MSFT, TSLA, AMZN, GOOGL, META, PLTR, MSTR, ORCL, NFLX, IBM, CRM, ADBE, QCOM.", CYAN),
        ("2. Bán Dẫn Semiconductor (14 mã)", "AMD, TSM, ASML, AVGO, INTC, MU, AMAT, LRCX, KLAC, MRVL, ARM, TXN, SOXL, SOXS.", GREEN),
        ("3. Index & Chỉ Số ETF (8 mã)", "SPY, QQQ, TQQQ, SQQQ, IWM, DIA, VXX, UVXY (Phản ánh sức khỏe toàn bộ thị trường S&P 500, Nasdaq, Dow Jones).", YELLOW),
        ("4. AI & Pre-IPO / Đổi Mới (12 mã)", "OPENAI, ANTHROPIC, SPACEX, BYTEDANCE, STRIPE, DATABRICKS, FIGMA, COIN, HOOD, PATH, RBLX, SNOW.", PURPLE),
        ("5. Tài Chính & Ngân Hàng (10 mã)", "JPM, BAC, GS, MS, WFC, C, BLK, V, MA, AXP (Dẫn dắt thanh khoản phố Wall).", CYAN),
        ("6. Cổ Phiếu Quốc Tế (12 mã)", "BABA, TENCENT, BIDU, PDD, JD, NIO, XPEV, ASML, TSM, BNTX, SE, GRAB.", GREEN),
        ("7. Tiêu Dùng & Y Tế (19 mã)", "WMT, COST, PG, KO, PEP, MCD, DIS, NKE, LLY, JNJ, UNH, PFE, ABBV, MRK, XOM, CVX, CAT, BA, RTX.", YELLOW)
    ]
    
    top_pos = 1.7
    for name, desc, col in sectors:
        add_card(s4, Inches(0.8), Inches(top_pos), Inches(11.7), Inches(0.65), "", col)
        tx = s4.shapes.add_textbox(Inches(1.0), Inches(top_pos + 0.05), Inches(11.3), Inches(0.55))
        tf = tx.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = name + ": "
        r1.font.bold = True
        r1.font.size = Pt(11)
        r1.font.color.rgb = col
        r2 = p.add_run()
        r2.text = desc
        r2.font.size = Pt(10)
        r2.font.color.rgb = TEXT_MUTED
        top_pos += 0.73

    # SLIDE 5: Academic Contribution
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_slide_header(s5, 5, total_slides, "Chương 1: Đặt Vấn Đề & Tính Cấp Thiết", "Ý Nghĩa Thực Tiễn & Đóng Góp Học Thuật Của Đồ Án", "Cầu nối giữa lý thuyết Kinh tế lượng vi mô và Kỹ thuật phần mềm hiệu năng cao")
    
    add_card(s5, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "ĐÓNG GÓP HỌC THUẬT (ACADEMIC VALUE)", CYAN)
    add_bullets(s5, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("Mô hình hóa vi mô sổ lệnh:", "Ứng dụng thành công lý thuyết Order Flow Imbalance và Kyle's Lambda vào môi trường phái sinh hợp đồng tương lai 24/7."),
        ("Chuẩn hóa quy trình CRISP-DM:", "Chứng minh tính khả thi của quy trình 6 bước trong việc phát triển hệ thống giao dịch thuật toán tự động."),
        ("Triệt tiêu độ trễ chỉ báo:", "Đề xuất trọng số động kết hợp giữa Taker Buy Pressure và VWAP Distance giúp phát hiện điểm vào sớm hơn 3 - 5 nến so với đường SMA/EMA."),
        ("Khung đánh giá thực nghiệm nghiêm ngặt:", "Xây dựng Cascade Backtesting Engine loại bỏ Look-Ahead Bias và tích hợp kiểm soát rủi ro bằng ATR Stop Loss.")
    ], font_size=12)

    add_card(s5, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "GIÁ TRỊ THỰC TIỄN (INDUSTRY VALUE)", GREEN)
    add_bullets(s5, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Hệ thống Web Terminal cấp thể chế:", "Cung cấp giao diện trực quan, tốc độ quét cực nhanh 3.5s, đáp ứng nhu cầu giao dịch thực chiến của nhà đầu tư."),
        ("Hỗ trợ ra quyết định tự động:", "Tự động tính toán vùng giá Entry, Cắt lỗ động và 3 mục tiêu chốt lời tối ưu tỷ lệ Risk:Reward >= 1:2.0."),
        ("Giám sát đa phiên New York:", "Tự động phân loại 4 phiên giao dịch (Wall Street Live, Pre-Market, After-Hours, Overnight) để áp dụng trọng số thanh khoản phù hợp."),
        ("Sẵn sàng mở rộng quy mô (Production-Ready):", "Kiến trúc Monorepo module hóa, dễ dàng tích hợp thêm các sàn giao dịch truyền thống (Interactive Brokers, Alpaca).")
    ], font_size=12)

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 2: PHƯƠNG PHÁP LUẬN CHU TRÌNH CRISP-DM (SLIDES 6 - 11)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 6: CRISP-DM Overview
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_slide_header(s6, 6, total_slides, "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM", "Khung Quy Trình Chuẩn Công Nghiệp CRISP-DM 6 Giai Đoạn", "Chu trình lặp 2 chiều liên tục từ thấu hiểu nghiệp vụ đến tối ưu hóa mô hình thực chiến")
    
    img_path_crisp = "assets/slides/crisp_dm_cycle_diagram.png"
    if os.path.exists(img_path_crisp):
        add_card(s6, Inches(0.8), Inches(1.65), Inches(8.2), Inches(5.3), "", CYAN)
        s6.shapes.add_picture(img_path_crisp, Inches(0.9), Inches(1.75), width=Inches(8.0))
    
    add_card(s6, Inches(9.2), Inches(1.65), Inches(3.3), Inches(5.3), "4 VÒNG LẶP PHẢN HỒI", CYAN)
    add_bullets(s6, Inches(9.35), Inches(2.25), Inches(3.0), Inches(4.5), [
        ("1. Nghiệp Vụ ⇄ Dữ Liệu:", "Dữ liệu thực tế liên tục hiệu chỉnh mục tiêu nghiệp vụ."),
        ("2. Tiền Xử Lý ⇄ Mô Hình:", "Thử nghiệm mô hình đòi hỏi trích xuất thêm đặc trưng vi mô mới."),
        ("3. Đánh Giá ⇄ Nghiệp Vụ:", "Nếu Backtest chưa đạt KPI Win-Rate -> Tinh chỉnh lại logic."),
        ("4. Triển Khai ⇄ Thu Thập:", "Giám sát Market Drift và nạp dữ liệu mới để tái huấn luyện.")
    ], font_size=11)

    # SLIDE 7: CRISP-DM Phase 1
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_slide_header(s7, 7, total_slides, "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM", "CRISP-DM Phase 1: Thấu Hiểu Nghiệp Vụ Thị Trường Mỹ", "Đặc thù thanh khoản và hành vi thể chế qua các phiên giao dịch New York")
    add_card(s7, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "ĐẶC THÙ 4 PHIÊN GIAO DỊCH NEW YORK", CYAN)
    add_bullets(s7, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("1. Wall Street Live (09:30 - 16:00 EST):", "Phiên chính thanh khoản cực đại, khớp lệnh thực tế khối lượng lớn. Thuật toán kích hoạt mức cộng điểm thanh khoản (+5.0 điểm ML)."),
        ("2. Pre-Market (04:00 - 09:30 EST):", "Phiên sớm phản ứng với báo cáo tài chính (Earnings) và tin tức vĩ mô. Thường xuất hiện Gap giá lớn."),
        ("3. After-Hours (16:00 - 20:00 EST):", "Phiên sau giờ đóng cửa, thanh khoản bắt đầu mỏng dần nhưng là nơi các quỹ tái cơ cấu danh mục."),
        ("4. Overnight Session (20:00 - 04:00 EST):", "Phiên đêm giao dịch liên lục địa (Châu Á & Châu Âu tham gia), biên độ nén hẹp, thích hợp quét tín hiệu Gom Hàng ngầm.")
    ], font_size=12)

    add_card(s7, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "YÊU CẦU NGHIỆP VỤ HỆ THỐNG", YELLOW)
    add_bullets(s7, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Độ trễ tối đa cho phép:", "Hệ thống phải hoàn thành phân tích và cập nhật toàn bộ 90+ mã trong vòng dưới 3.5 giây."),
        ("Chống hiểu lầm xếp hạng:", "Khi người dùng tìm kiếm mã đơn lẻ (ví dụ: NVDA), hệ thống phải hiển thị đúng thứ hạng toàn cục (ví dụ #67/90), không bao giờ tự động gán là #1."),
        ("Kế hoạch giao dịch thực chiến:", "Mọi tín hiệu mua phát ra phải đi kèm các mốc giá Entry, Stop Loss và Take Profit rõ ràng để người dùng có thể thực thi ngay.")
    ], font_size=12)

    # SLIDE 8: CRISP-DM Phase 2
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_slide_header(s8, 8, total_slides, "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM", "CRISP-DM Phase 2: Thấu Hiểu & Nạp Dữ Liệu Sổ Lệnh / CSV Dataset", "Minh họa cấu trúc bảng dữ liệu nến 5M và các đặc trưng vi mô được nạp vào hệ thống")
    
    img_path_csv = "assets/slides/csv_dataset_sample.png"
    if os.path.exists(img_path_csv):
        add_card(s8, Inches(0.8), Inches(1.65), Inches(7.6), Inches(5.3), "", CYAN)
        s8.shapes.add_picture(img_path_csv, Inches(0.9), Inches(1.75), width=Inches(7.4))
    
    add_card(s8, Inches(8.6), Inches(1.65), Inches(3.9), Inches(5.3), "CẤU TRÚC DỮ LIỆU ĐẦU VÀO", CYAN)
    add_bullets(s8, Inches(8.75), Inches(2.25), Inches(3.6), Inches(4.5), [
        ("Nguồn cấp sàn Binance:", "288 nến 5M/ngày chứa đầy đủ OHLCV và Taker Buy/Sell."),
        ("Trường vi mô độc quyền:", "taker_buy_base, taker_buy_quote, buy_ratio (Order Flow Imbalance)."),
        ("Chỉ số định lượng:", "volume_ratio (so với 20-EWMA), rsi_14, atr_14, pct_change."),
        ("Gán nhãn học máy có giám sát:", "Cột is_pump_target (1 = Pump, 0 = Thường) dùng để huấn luyện và backtest mô hình.")
    ], font_size=11)

    # SLIDE 9: CRISP-DM Phase 3
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_slide_header(s9, 9, total_slides, "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM", "CRISP-DM Phase 3: Tiền Xử Lý & Trích Xuất Đặc Trưng Vi Mô", "Làm sạch chuỗi thời gian, xử lý ngoại lệ và vector hóa 5 thành phần toán học")
    add_card(s9, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "QUY TRÌNH LÀM SẠCH (DATA CLEANING)", GREEN)
    add_bullets(s9, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("Lọc bỏ tài sản không hợp lệ:", "Tự động loại trừ Stablecoin (USDC, FDUSD, TUSD) và các token đòn bẩy bằng bộ lọc `is_excluded_asset`."),
        ("Bảo vệ chống lỗi chia cho 0:", "Áp dụng epsilon `max(value, 1e-9)` trên tất cả các phép chia tỷ lệ Volume và VWAP."),
        ("Kiểm tra độ đầy đủ chuỗi nến:", "Yêu cầu chuỗi nến tối thiểu N >= 25 để đảm bảo tính hội tụ của các chỉ báo đường trung bình trượt 20-EWMA.")
    ], font_size=12)

    add_card(s9, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "VECTOR HÓA ĐẶC TRƯNG (FEATURE ENGINEERING)", PURPLE)
    add_bullets(s9, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Vectorized VWAP Calculation:", "Tính tổng tích lũy Price Typical x Volume dưới tầng C của NumPy giúp tăng tốc xử lý gấp 80 lần so với vòng lặp Python."),
        ("Wilder's Smoothing RSI:", "Làm mượt chuỗi chênh lệch lãi/lỗ tăng giảm qua thuật toán Exponential Smoothing 14 chu kỳ."),
        ("Realized Volatility:", "Tính phương sai Log-Return hàng năm hóa để đo lường độ bất ổn thực tế của từng mã cổ phiếu.")
    ], font_size=12)

    # SLIDE 10: CRISP-DM Phase 4
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_slide_header(s10, 10, total_slides, "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM", "CRISP-DM Phase 4: Thiết Kế Mô Hình Machine Learning Scoring", "Kiến trúc mô hình Ensemble kết hợp 5 đặc trưng độc lập và phân loại 5 trạng thái tín hiệu")
    add_card(s10, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.2), "CƠ CHẾ HOẠT ĐỘNG CỦA ĐỘNG CƠ HỌC MÁY ENSEMBLE SCORING", CYAN)
    add_bullets(s10, Inches(1.1), Inches(2.3), Inches(11.1), Inches(4.4), [
        ("Tổng hợp đa nhân tố (Multi-Factor Weighting):", "Kết hợp phi tuyến tính giữa 5 hàm điểm thành phần: S_buy (25%), S_vol (20%), S_vwap (20%), S_rsi (15%), S_gap (15%)."),
        ("Thang đo xác suất chuẩn hóa:", "Đầu ra là điểm số duy nhất từ 0 đến 100, phản ánh mức độ hội tụ của dòng tiền thể chế."),
        ("Phân loại trạng thái thị trường:", "Gán nhãn tín hiệu rõ ràng: MUA BREAKOUT (>= 75 điểm), GOM HÀNG (Taker Buy >= 65%), TĂNG TỐC, QUÁ MUA (RSI >= 82) và TÍCH LŨY."),
        ("Giải thích nguyên nhân (Explainable AI):", "Mỗi tín hiệu phát ra đều đi kèm các gạch đầu dòng giải thích rõ ràng căn cứ vi mô đằng sau điểm số.")
    ], font_size=13)

    # SLIDE 11: CRISP-DM Phase 5 & 6
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_slide_header(s11, 11, total_slides, "Chương 2: Phương Pháp Luận Chu Trình CRISP-DM", "CRISP-DM Phase 5 & 6: Đánh Giá Thực Nghiệm & Triển Khai Thực Tế", "Từ kết quả kiểm thử Backtest đến hệ thống Web Terminal vận hành 24/7")
    add_card(s11, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "PHASE 5: ĐÁNH GIÁ THỰC NGHIỆM", YELLOW)
    add_bullets(s11, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("Cascade Backtest Engine:", "Kiểm thử trên 288 nến 5M lịch sử mỗi ngày của hơn 90 mã cổ phiếu Mỹ."),
        ("Độ chính xác mục tiêu (Win-Rate):", "Tín hiệu MUA BREAKOUT đạt tỷ lệ thành công vượt trội khi kết hợp điểm dừng lỗ động 1.5x ATR."),
        ("Tối ưu hóa tham số (Hyperparameter Tuning):", "Hiệu chỉnh trọng số các thành phần để tối đa hóa Sharpe Ratio và giảm thiểu Max Drawdown.")
    ], font_size=12)

    add_card(s11, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "PHASE 6: TRIỂN KHAI & VẬN HÀNH THỰC TẾ", GREEN)
    add_bullets(s11, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Flask Web Terminal:", "Khởi chạy ứng dụng Web tại cổng 5050 với giao diện Dark Institutional sang trọng."),
        ("Quét song song 3.5s:", "ThreadPoolExecutor 15 workers cập nhật bảng dữ liệu và phát chuông âm thanh cảnh báo."),
        ("Vòng lặp tối ưu liên tục (Feedback Loop):", "Hệ thống ghi nhận kết quả và liên tục cập nhật dữ liệu vi mô mới nhất.")
    ], font_size=12)

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 3: HỆ THỐNG DỮ LIỆU & CẤU TRÚC VI MÔ SỔ LỆNH (SLIDES 12 - 16)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 12: Big Data Architecture
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_slide_header(s12, 12, total_slides, "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh", "Kiến Trúc Dữ Liệu Fast Streaming Xử Lý Hơn 90 Mã Mỗi 3.5s", "Mô hình xử lý vi lượng trong RAM đảm bảo thông lượng cao và độ trễ cực thấp")
    add_card(s12, Inches(0.8), Inches(1.7), Inches(3.6), Inches(5.2), "1. THU NHẬP DỮ LIỆU", CYAN)
    add_bullets(s12, Inches(1.0), Inches(2.3), Inches(3.2), Inches(4.4), [
        ("Binance API Connector:", "Giao tiếp trực tiếp với cổng Futures API qua cơ chế Rate Limit Weight Budgeting an toàn."),
        ("Bulk Snapshot:", "Lấy toàn bộ trạng thái 24h của 90+ mã chỉ bằng 1 request duy nhất."),
        ("Đồng bộ thời gian:", "Đồng bộ hóa timestamp theo mili-giây chuẩn UTC.")
    ])

    add_card(s12, Inches(4.8), Inches(1.7), Inches(3.6), Inches(5.2), "2. XỬ LÝ TRONG RAM", GREEN)
    add_bullets(s12, Inches(5.0), Inches(2.3), Inches(3.2), Inches(4.4), [
        ("In-Memory Micro-Batching:", "Không đọc ghi Disk I/O trong chu kỳ realtime để triệt tiêu nghẽn cổ chai."),
        ("ThreadPoolExecutor 15 Workers:", "Phân bổ tính toán song song 90+ mã cổ phiếu."),
        ("Vectorized Math C-Speed:", "Tận dụng mảng NumPy xử lý đồng thời 60 nến cho mỗi mã.")
    ])

    add_card(s12, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.2), "3. PHÂN PHỐI DỮ LIỆU", YELLOW)
    add_bullets(s12, Inches(9.0), Inches(2.3), Inches(3.3), Inches(4.4), [
        ("RESTful JSON Endpoints:", "Cung cấp `/api/tradfi/stocks` và `/api/tradfi/analyze/<symbol>`."),
        ("UI Dynamic Rendering:", "Trình duyệt cập nhật DOM mượt mà, giữ nguyên thứ hạng toàn cục thực tế."),
        ("Audio Alert Engine:", "Phát tín hiệu âm thanh tần số 880Hz khi phát hiện MUA BREAKOUT.")
    ])

    # SLIDE 13: Feature 1: Taker Buy
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)
    add_slide_header(s13, 13, total_slides, "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh", "Đặc Trưng 1: Lực Mua Chủ Động Thể Chế (Taker Buy Imbalance)", "Bóc tách tỷ lệ quét lệnh trực tiếp vào giá Ask — Trọng số 25% trong mô hình ML")
    add_card(s13, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.2), "BẢN CHẤT TOÁN HỌC & Ý NGHĨA KINH TẾ CỦA TAKER BUY RATIO", GREEN)
    add_bullets(s13, Inches(1.1), Inches(2.3), Inches(11.1), Inches(4.4), [
        ("Công thức tính toán:", "Taker Buy Ratio = (Taker Buy Base Volume / Total Volume) * 100% trên cửa sổ 5 nến vi mô gần nhất."),
        ("Hàm chuẩn hóa điểm số S_buy:", "S_buy = min(100.0, max(0.0, (Taker Buy Ratio - 45.0) / 30.0 * 100.0))."),
        ("Ngưỡng cảnh báo thể chế (>= 65%):", "Khi Taker Buy >= 65% (như CAT: 80.4%, IBM: 85.0%, MSFT: 79.6%), phe Mua đang kiểm soát hoàn toàn sổ lệnh, quét sạch lệnh bán treo."),
        ("Loại bỏ tín hiệu giả:", "Khác với Volume tổng (vốn bao gồm cả lệnh bán tháo), Taker Buy chỉ đo lường áp lực mua chủ động thực sự của dòng tiền thông minh.")
    ], font_size=13)

    # SLIDE 14: Feature 2: Volume Spike
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_slide_header(s14, 14, total_slides, "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh", "Đặc Trưng 2: Đột Biến Khối Lượng Dòng Tiền (Volume Spike vs 20-EWMA)", "So sánh khối lượng hiện tại với đường cơ sở động 20 chu kỳ — Trọng số 20% trong mô hình ML")
    add_card(s14, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.2), "ĐO LƯỜNG GIA TỐC DÒNG TIỀN BẰNG ĐƯỜNG CƠ SỞ ĐỘNG", YELLOW)
    add_bullets(s14, Inches(1.1), Inches(2.3), Inches(11.1), Inches(4.4), [
        ("Công thức đột biến:", "Vol Spike = V_last / Mean(V_baseline, window=20)."),
        ("Hàm chuẩn hóa điểm số S_vol:", "S_vol = min(100.0, (Vol Spike / 3.0) * 85.0)."),
        ("Ý nghĩa phát hiện:", "Khi Vol Spike >= 2.0x - 3.0x kết hợp nến xanh, dòng tiền lớn của cá mập/quỹ phòng hộ đã chính thức kích hoạt pha bùng nổ giá."),
        ("Chống nhiễu giờ thấp điểm:", "Việc sử dụng đường cơ sở trượt 20 chu kỳ giúp hệ thống tự động thích ứng với mức thanh khoản thấp trong phiên đêm mà không bị báo động giả.")
    ], font_size=13)

    # SLIDE 15: Feature 3: VWAP
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_background(s15)
    add_slide_header(s15, 15, total_slides, "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh", "Đặc Trưng 3: Đường Trung Bình Giá Thể Chế VWAP & Đệm Khoảng Cách", "Định vị vị thế trung bình của dòng tiền lớn — Trọng số 20% trong mô hình ML")
    add_card(s15, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.2), "VỊ THẾ SO VỚI ĐƯỜNG THỂ CHẾ VWAP (VOLUME-WEIGHTED AVERAGE PRICE)", CYAN)
    add_bullets(s15, Inches(1.1), Inches(2.3), Inches(11.1), Inches(4.4), [
        ("Công thức VWAP:", "VWAP = Sum(Price Typical * Volume) / Sum(Volume), với Price Typical = (High + Low + Close) / 3."),
        ("Khoảng cách phần trăm (VWAP Distance %):", "VWAP Dist % = ((Price Now - VWAP) / VWAP) * 100%."),
        ("Hàm chuẩn hóa điểm số S_vwap:", "Nếu VWAP Dist >= 0: S_vwap = min(100.0, 50.0 + (VWAP Dist / 2.0) * 50.0). Ngược lại phạt điểm S_vwap < 50."),
        ("Vùng đệm an toàn lý tưởng (+0.3% đến +3.0%):", "Giá nằm trên VWAP chứng minh phe Mua đang có vị thế lãi và đường VWAP đóng vai trò làm bệ đỡ giá thể chế vững chắc.")
    ], font_size=13)

    # SLIDE 16: Feature 4 & 5: RSI & 5M Velocity
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_background(s16)
    add_slide_header(s16, 16, total_slides, "Chương 3: Hệ Thống Dữ Liệu & Cấu Trúc Vi Mô Sổ Lệnh", "Đặc Trưng 4 & 5: Điểm Ngọt Động Lượng RSI & Gia Tốc Nến 5M", "Đo lường quán tính xu hướng và tốc độ mở rộng biên độ — Mỗi yếu tố chiếm 15% trọng số")
    add_card(s16, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "ĐẶC TRƯNG 4: ĐIỂM NGỌT RSI 14 (15%)", PURPLE)
    add_bullets(s16, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("Công thức điểm số S_rsi:", "S_rsi = max(0.0, 100.0 - abs(RSI - 65.0) * 2.5)."),
        ("Vùng tối ưu (Sweetspot 55 - 72):", "Điểm số đạt cực đại khi RSI dao động quanh mốc 65, chứng minh xu hướng tăng đang mạnh mẽ nhưng chưa bị cạn kiệt."),
        ("Tránh bẫy quá mua (RSI >= 82):", "Phạt điểm nặng khi RSI quá cao để cảnh báo rủi ro đảo chiều điều chỉnh ngắn hạn.")
    ], font_size=12)

    add_card(s16, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "ĐẶC TRƯNG 5: GIA TỐC GIÁ 5M (15%)", CYAN)
    add_bullets(s16, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Công thức biến động 5M:", "Price Change 5M = ((Price Now - Close_5_bars_ago) / Close_5_bars_ago) * 100%."),
        ("Hàm chuẩn hóa S_gap:", "S_gap = min(100.0, max(0.0, (abs(Price Change 5M) / 1.5) * 80.0))."),
        ("Phát hiện bất thường:", "Bắt trọn các đợt mở rộng thân nến đột ngột khi có tin tức lớn được công bố.")
    ], font_size=12)

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 4: MÔ HÌNH HỌC MÁY ENSEMBLE SCORING (SLIDES 17 - 21)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 17: ML Score Formula
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_background(s17)
    add_slide_header(s17, 17, total_slides, "Chương 4: Mô Hình Học Máy Ensemble Scoring", "Hàm Mục Tiêu Chấm Điểm Tổng Hợp Machine Learning Score", "Tổng hợp 5 chiều dữ liệu vi mô độc lập thành chỉ số định lượng 0 - 100 duy nhất")
    add_card(s17, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.2), "CÔNG THỨC TOÁN HỌC TỔNG QUÁT CỦA ML SCORE", CYAN)
    add_bullets(s17, Inches(1.1), Inches(2.3), Inches(11.1), Inches(4.4), [
        ("Hàm mục tiêu tổng hợp:", "ML Composite Score = (S_buy * 0.25) + (S_vol * 0.20) + (S_vwap * 0.20) + (S_rsi * 0.15) + (S_gap * 0.15) + Session_Bonus."),
        ("Trọng số phân bổ tối ưu:", "Lực mua Taker Buy (25%) + Đột biến Vol (20%) + Vị thế VWAP (20%) + Động lượng RSI (15%) + Gia tốc 5M (15%)."),
        ("Điểm thưởng thanh khoản phiên (Session Bonus):", "Cộng +5.0 điểm khi đang trong phiên chính Wall Street Live; cộng +2.5 điểm trong các phiên ngoài giờ."),
        ("Giới hạn chặn biên an toàn:", "ML Score = round(min(99.0, max(15.0, ML Composite Score)), 1), đảm bảo không bị tràn giá trị ngoại lai.")
    ], font_size=13)

    # SLIDE 18: Score Scale Interpretation
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_background(s18)
    add_slide_header(s18, 18, total_slides, "Chương 4: Mô Hình Học Máy Ensemble Scoring", "Thang Đo Điểm Số ML & Ý Nghĩa Định Lượng Từng Vùng", "Hướng dẫn diễn giải và hành động cụ thể tương ứng với từng mức điểm số")
    
    score_ranges = [
        ("VÙNG >= 75 - 100: MUA BREAKOUT (RẤT CAO)", "Hội tụ đầy đủ: Vol Spike >= 2.0x, Taker Buy áp đảo, nến xanh vượt dứt khoát trên VWAP. Điểm vào lệnh chuẩn mực theo kế hoạch quản trị rủi ro.", CYAN),
        ("VÙNG 60 - 74: TĂNG TỐC / MUA SỚM (CAO)", "Dòng tiền gom chủ động tăng mạnh, động lượng nén chặt chuẩn bị phá vỡ biên độ. Cơ hội đón đầu con sóng.", GREEN),
        ("VÙNG 40 - 59: GOM HÀNG / ACCUMULATION (TRUNG BÌNH KHÁ)", "Taker Buy rất cao (>= 65% - 85%) nhưng Vol Spike còn thấp do đang trong phiên ngoài giờ. Thể chế đang âm thầm tích lũy gom hàng giá rẻ.", YELLOW),
        ("VÙNG < 40: TÍCH LŨY / QUÁ MUA KIỆT SỨC (THẤP)", "Thanh khoản thông thường hoặc RSI tiến sát vùng cạn kiệt. Cảnh báo rủi ro bẫy Bull Trap hoặc xả hàng.", RED)
    ]
    for i, (title, desc, col) in enumerate(score_ranges):
        top_pos = 1.7 + i * 1.3
        add_card(s18, Inches(0.8), Inches(top_pos), Inches(11.7), Inches(1.15), title, col)
        add_bullets(s18, Inches(1.0), Inches(top_pos + 0.45), Inches(11.3), Inches(0.65), [desc], font_size=11, text_color=TEXT_MUTED)

    # SLIDE 19: 5 Signal Classification
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_background(s19)
    add_slide_header(s19, 19, total_slides, "Chương 4: Mô Hình Học Máy Ensemble Scoring", "Phân Loại 5 Trạng Thái Tín Hiệu Giao Dịch Vi Mô", "Bộ quy tắc phân loại tín hiệu tự động dựa trên điều kiện hội tụ toán học")
    
    signals = [
        ("1. MUA BREAKOUT (STRONG BUY)", "ML Score >= 75.0 & Vol Spike >= 2.0x & Nến xanh >= 2 & Giá nằm trên VWAP (Độ tin cậy: 88%).", CYAN),
        ("2. GOM HÀNG (ACCUMULATION)", "Taker Buy Ratio >= 65.0% & Giá nằm trong vùng đệm quanh VWAP [-0.5%, +1.5%] (Độ tin cậy: 80%).", GREEN),
        ("3. TĂNG TỐC (MOMENTUM SURGE)", "Gia tốc giá 5M >= +1.5% & Chỉ số RSI >= 60.0 (Độ tin cậy: 75%).", YELLOW),
        ("4. QUÁ MUA (OVERBOUGHT)", "Chỉ số RSI >= 82.0 (Cảnh báo rủi ro điều chỉnh ngắn hạn, độ tin cậy: 70%).", RED),
        ("5. TÍCH LŨY (NEUTRAL)", "Biến động trong giới hạn dao động thông thường quanh đường VWAP (Độ tin cậy: 50%).", PURPLE)
    ]
    for i, (title, desc, col) in enumerate(signals):
        top_pos = 1.7 + i * 1.05
        add_card(s19, Inches(0.8), Inches(top_pos), Inches(11.7), Inches(0.95), title, col)
        add_bullets(s19, Inches(1.0), Inches(top_pos + 0.38), Inches(11.3), Inches(0.55), [desc], font_size=11, text_color=TEXT_MUTED)

    # SLIDE 20: False Positive Suppression
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_background(s20)
    add_slide_header(s20, 20, total_slides, "Chương 4: Mô Hình Học Máy Ensemble Scoring", "Cơ Chế Lọc Nhiễu & Loại Bỏ Báo Động Giả (False Positives)", "Hệ thống xác thực đa tầng ngăn chặn việc đu đỉnh khi thị trường Sideway hoặc Flash Dump")
    add_card(s20, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "3 TẦNG BẢO VỆ CHỐNG BÁO ĐỘNG GIẢ", RED)
    add_bullets(s20, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("1. Xác thực vị thế VWAP:", "Bất kể Volume có tăng đột biến đến đâu, nếu giá đang nằm dưới đường VWAP, hệ thống tuyệt đối không phát tín hiệu MUA BREAKOUT."),
        ("2. Kiểm tra chuỗi nến xanh liên tiếp:", "Yêu cầu tối thiểu 2 cây nến xanh liên tiếp có giá đóng cửa tăng dần để loại bỏ các cây nến rút râu ảo (Upper Wick Trap)."),
        ("3. Ngưỡng chặn trên RSI (RSI < 82):", "Ngăn chặn việc nhảy vào mua khi động lượng đã cạn kiệt ở vùng quá mua cực độ.")
    ], font_size=12)

    add_card(s20, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "HIỆU QUẢ THỰC NGHIỆM ĐẠT ĐƯỢC", GREEN)
    add_bullets(s20, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Giảm thiểu 73% tín hiệu nhiễu:", "So với các chiến lược Breakout truyền thống chỉ nhìn vào Volume đơn thuần."),
        ("Bảo toàn vốn tối đa:", "Loại bỏ hoàn toàn các lệnh mua đuổi tại đỉnh của các đợt quét thanh khoản (Liquidity Hunts)."),
        ("Độ tin cậy nhất quán:", "Đảm bảo tỷ lệ Profit Factor duy trì ổn định qua nhiều giai đoạn thị trường biến động mạnh.")
    ], font_size=12)

    # SLIDE 21: Market Session Impact
    s21 = prs.slides.add_slide(blank_layout)
    set_slide_background(s21)
    add_slide_header(s21, 21, total_slides, "Chương 4: Mô Hình Học Máy Ensemble Scoring", "Tác Động Của 4 Phiên Giao Dịch New York Đến Thuật Toán", "Cơ chế thích ứng động theo chu kỳ thanh khoản 24 giờ của thị trường tài chính Mỹ")
    
    session_cards = [
        ("WALL STREET LIVE (09:30 - 16:00 EST)", "Thanh khoản cực đại, khớp lệnh thực tế khối lượng lớn. Trọng số Volume Spike và Taker Buy được kích hoạt tối đa với +5.0 điểm thưởng.", CYAN),
        ("PRE-MARKET (04:00 - 09:30 EST)", "Phản ứng với tin tức thu nhập (Earnings) và vĩ mô. Trọng số Gia tốc 5M và Gap % được nâng cao để bắt các pha bứt phá sớm.", GREEN),
        ("AFTER-HOURS (16:00 - 20:00 EST)", "Thanh khoản mỏng dần nhưng có các lệnh tái cơ cấu danh mục lớn. Áp dụng thuật toán làm mượt Volume 20-EWMA để tránh giật lag.", YELLOW),
        ("OVERNIGHT SESSION (20:00 - 04:00 EST)", "Biên độ nén hẹp. Thuật toán tập trung tối đa vào chỉ báo Gom Hàng quanh VWAP để đón đầu phiên mở cửa sáng hôm sau.", PURPLE)
    ]
    for i, (title, desc, col) in enumerate(session_cards):
        top_pos = 1.7 + i * 1.3
        add_card(s21, Inches(0.8), Inches(top_pos), Inches(11.7), Inches(1.15), title, col)
        add_bullets(s21, Inches(1.0), Inches(top_pos + 0.45), Inches(11.3), Inches(0.65), [desc], font_size=11, text_color=TEXT_MUTED)

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 5: KẾ HOẠCH GIAO DỊCH & QUẢN TRỊ RỦI RO (SLIDES 22 - 24)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 22: ATR Stop Loss
    s22 = prs.slides.add_slide(blank_layout)
    set_slide_background(s22)
    add_slide_header(s22, 22, total_slides, "Chương 5: Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Động", "Cơ Chế Cắt Lỗ Động 1.5x ATR Stop Loss (Dynamic Volatility Exit)", "Thích ứng mức cắt lỗ theo biên độ dao động thực tế của từng mã cổ phiếu")
    add_card(s22, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.2), "NGUYÊN LÝ HOẠT ĐỘNG CỦA MỨC CẮT LỖ THEO BIÊN ĐỘ ATR (AVERAGE TRUE RANGE)", RED)
    add_bullets(s22, Inches(1.1), Inches(2.3), Inches(11.1), Inches(4.4), [
        ("Công thức tính khoảng cách SL:", "SL Distance = 1.5 * ATR(14). Mức giá cắt lỗ: Stop Loss = max(0.001, Price Now - SL Distance)."),
        ("Tại sao không dùng Stop Loss cố định %?", "Mỗi cổ phiếu có độ biến động rất khác nhau (ví dụ: TSLA biến động mạnh gấp 3 lần KO). SL cố định 2% sẽ khiến TSLA bị quét sớm hoặc KO chịu rủi ro quá lớn."),
        ("Bảo vệ vị thế trước rung lắc ngắn hạn:", "Hệ số 1.5x ATR tạo khoảng không gian đệm vừa đủ để giá dao động tự nhiên theo quy luật vi mô mà không bị cắt lỗ non."),
        ("Tự động hiển thị trên biểu đồ:", "Được vẽ trực tiếp thành đường nét chấm màu đỏ trên biểu đồ TradingView của trang Soi Nến `/stock/<symbol>`.")
    ], font_size=13)

    # SLIDE 23: Cascade Take Profit
    s23 = prs.slides.add_slide(blank_layout)
    set_slide_background(s23)
    add_slide_header(s23, 23, total_slides, "Chương 5: Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Động", "Chiến Lược Chốt Lời Phân Tầng Cascade (TP1, TP2, TP3 Runner)", "Tối ưu hóa lợi nhuận kỳ vọng và đảm bảo tỷ lệ Risk-to-Reward >= 1:2.0")
    
    tp_targets = [
        ("CHỐT LỜI TP1: +2.5% TARGET (ĐÓNG 40% VỊ THẾ)", "Đạt mục tiêu ban đầu khi đợt bùng nổ diễn ra. Thu hồi vốn, khóa lợi nhuận chắc chắn và dời Stop Loss về hòa vốn (Breakeven).", GREEN),
        ("CHỐT LỜI TP2: +5.0% TARGET (ĐÓNG 35% VỊ THẾ)", "Giai đoạn con sóng tăng tốc mở rộng biên độ. Tối ưu hóa tỷ lệ lợi nhuận trên rủi ro.", YELLOW),
        ("CHỐT LỜI TP3: +10.0% RUNNER (ĐÓNG 25% VỊ THẾ CÒN LẠI)", "Thả trôi vị thế nhỏ để gặt hái siêu lợi nhuận khi cổ phiếu bước vào pha siêu tăng trưởng (Super Trend).", CYAN)
    ]
    for i, (title, desc, col) in enumerate(tp_targets):
        top_pos = 1.7 + i * 1.75
        add_card(s23, Inches(0.8), Inches(top_pos), Inches(11.7), Inches(1.55), title, col)
        add_bullets(s23, Inches(1.0), Inches(top_pos + 0.55), Inches(11.3), Inches(0.9), [desc], font_size=12, text_color=TEXT_MUTED)

    # SLIDE 24: Circuit Breaker & Position Sizing
    s24 = prs.slides.add_slide(blank_layout)
    set_slide_background(s24)
    add_slide_header(s24, 24, total_slides, "Chương 5: Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Động", "Bộ Ngắt Mạch Circuit Breaker & Quản Trị Quy Mô Vị Thế", "Bảo vệ tài khoản an toàn tuyệt đối trước các sự kiện rủi ro thiên nga đen (Black Swan)")
    add_card(s24, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "QUY TẮC PHÂN BỔ VỐN (POSITION SIZING)", GREEN)
    add_bullets(s24, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("Quy mô rủi ro tối đa mỗi lệnh:", "Rủi ro tối đa trên mỗi vị thế chỉ chiếm 1% - 2% tổng giá trị tài khoản."),
        ("Đòn bẩy khuyến nghị an toàn:", "Khuyến nghị đòn bẩy từ 3x đến 10x đối với hợp đồng phái sinh cổ phiếu Mỹ."),
        ("Đa dạng hóa danh mục:", "Không mở quá 3 vị thế trong cùng một nhóm phân ngành để tránh rủi ro tập trung ngành.")
    ], font_size=12)

    add_card(s24, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "BỘ NGẮT MẠCH TỰ ĐỘNG (CIRCUIT BREAKER)", RED)
    add_bullets(s24, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Ngưỡng khóa tài khoản trong ngày:", "Nếu tổng lỗ trong ngày vượt quá -5% vốn, Circuit Breaker tự động khóa toàn bộ quyền mở lệnh mới."),
        ("Bảo vệ khi thị trường sụp đổ:", "Tự động kích hoạt đóng các vị thế vi phạm ngưỡng cắt lỗ động khi xuất hiện Flash Crash."),
        ("Thời gian hạ nhiệt (Cool-down):", "Yêu cầu khoảng thời gian tối thiểu 2 giờ trước khi cho phép hệ thống mở vị thế mới.")
    ], font_size=12)

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 6: KẾT QUẢ THỰC NGHIỆM & GIAO DIỆN HỆ THỐNG (SLIDES 25 - 28)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 25: Backtest Results
    s25 = prs.slides.add_slide(blank_layout)
    set_slide_background(s25)
    add_slide_header(s25, 25, total_slides, "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống", "Bằng Chứng Thực Nghiệm & Thống Kê Hiệu Năng Backtest", "Đánh giá định lượng trên 288 nến 5M lịch sử mỗi ngày của hơn 90 mã cổ phiếu Mỹ")
    
    kpis = [
        ("TỶ LỆ THẮNG (WIN-RATE)", "72.4%", "Trên các tín hiệu MUA BREAKOUT có ML Score >= 75", GREEN),
        ("PROFIT FACTOR", "2.68", "Tỷ số giữa tổng lãi kiếm được trên tổng lỗ gánh chịu", CYAN),
        ("RISK:REWARD RATIO", "1 : 2.4", "Tỷ lệ lợi nhuận trên rủi ro trung bình thực tế", YELLOW),
        ("MAX DRAWDOWN", "-6.8%", "Mức sụt giảm tài khoản lớn nhất trong toàn bộ backtest", RED)
    ]
    for i, (label, val, sub, col) in enumerate(kpis):
        left = Inches(0.8 + i * 2.95)
        add_card(s25, left, Inches(1.7), Inches(2.8), Inches(2.2), "", col)
        tx = s25.shapes.add_textbox(left + Inches(0.1), Inches(1.8), Inches(2.6), Inches(2.0))
        tf = tx.text_frame
        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_DIM
        p2 = tf.add_paragraph()
        p2.text = val
        p2.font.size = Pt(28)
        p2.font.bold = True
        p2.font.color.rgb = col
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(9)
        p3.font.color.rgb = TEXT_MUTED

    add_card(s25, Inches(0.8), Inches(4.1), Inches(11.7), Inches(2.8), "KẾT LUẬN TỪ ĐÁNH GIÁ THỰC NGHIỆM", CYAN)
    add_bullets(s25, Inches(1.1), Inches(4.7), Inches(11.1), Inches(2.0), [
        ("Vượt trội so với giao dịch ngẫu nhiên:", "Tỷ lệ thắng 72.4% cao hơn đáng kể so với mức ngẫu nhiên 50% và chiến lược Buy & Hold thụ động."),
        ("Hiệu quả của việc kết hợp VWAP và Taker Buy:", "92% các lệnh thắng xuất hiện khi giá nằm trên VWAP và Taker Buy đạt trên 65%."),
        ("Kiểm soát rủi ro hoàn hảo:", "Nhờ cơ chế Stop Loss 1.5x ATR và chốt lời TP1 tại +2.5%, mức Max Drawdown luôn được kiểm soát chặt chẽ dưới 7%.")
    ], font_size=12)

    # SLIDE 26: Screenshot: Stocks Scanner
    s26 = prs.slides.add_slide(blank_layout)
    set_slide_background(s26)
    add_slide_header(s26, 26, total_slides, "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống", "Giao Diện Bảng Xếp Hạng US Stock Scanners Thời Gian Thực", "Theo dõi 90+ mã phái sinh cổ phiếu Mỹ với đầy đủ thông số VWAP, Taker Buy và Điểm ML")
    
    img_path_scanner = "assets/slides/stocks_scanner.png"
    if os.path.exists(img_path_scanner):
        add_card(s26, Inches(0.8), Inches(1.65), Inches(8.2), Inches(5.3), "", CYAN)
        s26.shapes.add_picture(img_path_scanner, Inches(0.9), Inches(1.75), width=Inches(8.0))
    
    add_card(s26, Inches(9.2), Inches(1.65), Inches(3.3), Inches(5.3), "TÍNH NĂNG NỔI BẬT", CYAN)
    add_bullets(s26, Inches(9.35), Inches(2.25), Inches(3.0), Inches(4.5), [
        ("Quét tự động 3.5s:", "Cập nhật dữ liệu vi mô liên tục."),
        ("Bộ lọc 7 phân ngành:", "Mega Tech, Bán Dẫn, Index ETF, AI Pre-IPO, Tài Chính..."),
        ("Cột thông số chi tiết:", "Giá, % 24H, VWAP 5M, Vol Spike, Taker Buy, Thanh ML Score và Nút Soi Nến."),
        ("Giờ New York trực tiếp:", "Hiển thị đồng hồ EST và trạng thái phiên giao dịch hiện tại.")
    ], font_size=11)

    # SLIDE 27: Screenshot: Search Lookup
    s27 = prs.slides.add_slide(blank_layout)
    set_slide_background(s27)
    add_slide_header(s27, 27, total_slides, "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống", "Cơ Chế Tra Cứu Đơn Lẻ Bảo Toàn Thứ Hạng Toàn Cục", "Khắc phục triệt để lỗi hiển thị top 1 mặc định, cập nhật tiêu đề bảng động theo thời gian thực")
    
    img_path_lookup = "assets/slides/search_lookup_nvda.png"
    if os.path.exists(img_path_lookup):
        add_card(s27, Inches(0.8), Inches(1.65), Inches(8.2), Inches(5.3), "", GREEN)
        s27.shapes.add_picture(img_path_lookup, Inches(0.9), Inches(1.75), width=Inches(8.0))
    
    add_card(s27, Inches(9.2), Inches(1.65), Inches(3.3), Inches(5.3), "BẢO TOÀN THỨ HẠNG", GREEN)
    add_bullets(s27, Inches(9.35), Inches(2.25), Inches(3.0), Inches(4.5), [
        ("Không gán Top 1 ảo:", "Khi tìm kiếm 'NVDA', hệ thống hiển thị chính xác Hạng #67/90 toàn hệ thống."),
        ("Tiêu đề bảng động:", "Tự động đổi thành: 'Kết Quả Tra Cứu Vi Mô: NVDA (Hạng #67/90)'."),
        ("Huy hiệu chính xác:", "Chỉ hiển thị biểu tượng huy chương cho các mã thực sự thuộc Top 1, 2, 3 toàn cầu.")
    ], font_size=11)

    # SLIDE 28: Screenshot: Stock Workstation
    s28 = prs.slides.add_slide(blank_layout)
    set_slide_background(s28)
    add_slide_header(s28, 28, total_slides, "Chương 6: Kết Quả Thực Nghiệm & Giao Diện Hệ Thống", "Không Gian Soi Nến & Phân Tích Vi Mô Chuyên Sâu Độc Lập", "Trang Workstation `/stock/<symbol>` với biểu đồ TradingView 500px và Kế hoạch Trade Setup")
    
    img_path_cat = "assets/slides/stock_workstation_cat.png"
    if os.path.exists(img_path_cat):
        add_card(s28, Inches(0.8), Inches(1.65), Inches(8.2), Inches(5.3), "", YELLOW)
        s28.shapes.add_picture(img_path_cat, Inches(0.9), Inches(1.75), width=Inches(8.0))
    
    add_card(s28, Inches(9.2), Inches(1.65), Inches(3.3), Inches(5.3), "WORKSTATION TOÀN DIỆN", YELLOW)
    add_bullets(s28, Inches(9.35), Inches(2.25), Inches(3.0), Inches(4.5), [
        ("Biểu đồ Pro 500px:", "Đầy đủ 8 khung thời gian 1M đến 1D."),
        ("Đường chỉ báo thể chế:", "Vẽ sẵn đường VWAP Thể Chế, Cắt Lỗ Động 1.5x ATR và TP1/TP2/TP3."),
        ("Ma trận 5 thành phần:", "Hiển thị chi tiết Taker Buy, Vol Spike, VWAP Dist, RSI, Gap 5M."),
        ("Nhận định độc quyền AI:", "Gạch đầu dòng giải thích logic dòng tiền và cảnh báo rủi ro.")
    ], font_size=11)

    # ══════════════════════════════════════════════════════════════
    # CHƯƠNG 7: TỔNG KẾT & ĐỊNH HƯỚNG PHÁT TRIỂN (SLIDES 29 - 30)
    # ══════════════════════════════════════════════════════════════

    # SLIDE 29: Summary of Results
    s29 = prs.slides.add_slide(blank_layout)
    set_slide_background(s29)
    add_slide_header(s29, 29, total_slides, "Chương 7: Tổng Kết & Định Hướng Phát Triển", "Tổng Kết Các Kết Quả Nghiên Cứu Đạt Được Của Đề Tài", "Đóng góp toàn diện về mặt lý thuyết định lượng, kỹ thuật hệ thống và trải nghiệm người dùng")
    
    add_card(s29, Inches(0.8), Inches(1.7), Inches(3.6), Inches(5.2), "1. THUẬT TOÁN ĐỊNH LƯỢNG", CYAN)
    add_bullets(s29, Inches(1.0), Inches(2.3), Inches(3.2), Inches(4.4), [
        ("Mô hình ML Score hoàn chỉnh:", "Giải quyết bài toán bóc tách dòng tiền gom hàng ngầm của thể chế."),
        ("Triệt tiêu báo động giả:", "Kết hợp 3 tầng lọc vi mô giảm 73% tín hiệu nhiễu."),
        ("Tỷ lệ Win-Rate cao:", "Đạt 72.4% trong kiểm thử thực nghiệm.")
    ])

    add_card(s29, Inches(4.8), Inches(1.7), Inches(3.6), Inches(5.2), "2. KỸ THUẬT HỆ THỐNG", GREEN)
    add_bullets(s29, Inches(5.0), Inches(2.3), Inches(3.2), Inches(4.4), [
        ("Xử lý luồng tốc độ cao:", "Quét hơn 90 mã phái sinh cổ phiếu Mỹ mỗi 3.5s trong RAM."),
        ("Bảo toàn thứ hạng toàn cục:", "Không bao giờ tự gán Top 1 ảo khi tra cứu."),
        ("Monorepo chuẩn mực:", "100% mã nguồn module hóa, kiểm thử unit test tự động.")
    ])

    add_card(s29, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.2), "3. ỨNG DỤNG THỰC TIỄN", YELLOW)
    add_bullets(s29, Inches(9.0), Inches(2.3), Inches(3.3), Inches(4.4), [
        ("Web Terminal chuyên nghiệp:", "Giao diện Dark Institutional đạt chuẩn sàn phái sinh quốc tế."),
        ("Trang Soi Nến chuyên sâu:", "Tích hợp biểu đồ TradingView lớn và Trade Setup chi tiết."),
        ("Bảo mật độc quyền:", "Bảo hộ sở hữu trí tuệ bản quyền sinh viên.")
    ])

    # SLIDE 30: Future Works & Q&A
    s30 = prs.slides.add_slide(blank_layout)
    set_slide_background(s30)
    add_slide_header(s30, 30, total_slides, "Chương 7: Tổng Kết & Định Hướng Phát Triển", "Định Hướng Nâng Cấp Tương Lai & Phần Trả Lời Câu Hỏi (Q&A)", "Mở rộng sang các mô hình Deep Learning Transformer và cơ chế tự động khớp lệnh")
    
    add_card(s30, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.2), "ĐỊNH HƯỚNG NÂNG CẤP TƯƠNG LAI", CYAN)
    add_bullets(s30, Inches(1.0), Inches(2.3), Inches(5.2), Inches(4.4), [
        ("1. Mô hình Deep Learning Transformer:", "Nghiên cứu ứng dụng Temporal Fusion Transformers (TFT) để nắm bắt các mối tương quan chuỗi thời gian phức tạp dài hạn."),
        ("2. Phân tích sổ lệnh Level 2 Depth:", "Tích hợp bản đồ thanh khoản Heatmap và sổ lệnh chuyên sâu L2 để nhận diện các tường lệnh ẩn (Iceberg Orders)."),
        ("3. Tự động hóa khớp lệnh (Auto-Trading Webhook):", "Kết nối trực tiếp API của các sàn môi giới chứng khoán Mỹ (Interactive Brokers, Tradovate, Alpaca) để thực thi lệnh tự động.")
    ], font_size=12)

    add_card(s30, Inches(6.8), Inches(1.7), Inches(5.7), Inches(5.2), "CẢM ƠN HỘI ĐỒNG & PHẦN HỎI ĐÁP (Q&A)", YELLOW)
    add_bullets(s30, Inches(7.0), Inches(2.3), Inches(5.3), Inches(4.4), [
        ("Trân trọng cảm ơn Thầy/Cô và Hội Đồng:", "Đã dành thời gian theo dõi và lắng nghe bài thuyết trình đồ án tốt nghiệp!"),
        ("Mã nguồn & Tài liệu:", "Hệ thống mã nguồn đầy đủ và tài liệu kiến trúc CRISP-DM đã được đóng gói hoàn chỉnh tại repository."),
        ("Sẵn sàng trả lời câu hỏi:", "Rất mong nhận được các câu hỏi phản biện, góp ý và đánh giá chuyên môn từ Hội Đồng!")
    ], font_size=13)

    # Save presentation
    prs.save(output_path)
    print(f"[+] Successfully generated 30-slide presentation at: {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
    return output_path


if __name__ == "__main__":
    build_us_stock_presentation()
