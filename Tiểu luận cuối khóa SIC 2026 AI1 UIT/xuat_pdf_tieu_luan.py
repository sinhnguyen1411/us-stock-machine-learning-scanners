#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script biên dịch tự động Báo cáo tiểu luận từ Quarto Markdown (.qmd) sang PDF (.pdf)
sử dụng headless Chromium/Edge và Selenium, tự động render công thức MathJax và hình ảnh 300 DPI.
Kèm bộ kiểm tra chất lượng từng trang (Quality Assurance Verification) bằng pypdfium2.
Học viên: NGUYỄN DƯƠNG MẠNH SINH (MSSV: 24210169) - Lớp SIC 2026: AI1 UFM
"""

import os
import re
import time
import base64
import markdown
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.print_page_options import PrintOptions
import pypdfium2 as pdfium
from PIL import Image
import numpy as np

def convert_qmd_to_pdf():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    qmd_file = os.path.join(base_dir, 'tieu_luan_cuoi_khoa_us_stock_ml_scanners.qmd')
    html_file = os.path.join(base_dir, 'tieu_luan_cuoi_khoa_us_stock_ml_scanners.html')
    pdf_file = os.path.join(base_dir, 'tieu_luan_cuoi_khoa_us_stock_ml_scanners.pdf')

    print(f"[1/5] Đọc tệp nguồn: {qmd_file}")
    with open(qmd_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # 1. Bóc tách YAML Frontmatter
    body_text = raw_text
    if raw_text.startswith('---'):
        parts = raw_text.split('---', 2)
        if len(parts) >= 3:
            body_text = parts[2].strip()

    # 2. Xử lý ảnh Quarto: ![Caption](path){attributes} -> <figure>...
    def replace_image(match):
        caption = match.group(1)
        src = match.group(2)
        img_abs = os.path.join(base_dir, src.replace('/', os.sep))
        img_url = 'file:///' + img_abs.replace('\\', '/')
        return (f'<figure style="text-align: center; margin: 16px auto; page-break-inside: avoid; break-inside: avoid;">'
                f'<img src="{img_url}" style="max-width: 82%; max-height: 100mm; height: auto; border: 1px solid #e2e8f0; border-radius: 4px; box-shadow: 0 3px 8px rgba(0,0,0,0.06);">'
                f'<figcaption style="margin-top: 6px; font-size: 9.5pt; font-style: italic; color: #475569; font-weight: 500;">{caption}</figcaption>'
                f'</figure>')

    body_text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)(?:\{[^}]*\})?', replace_image, body_text)

    # 3. Xử lý tiêu đề bảng Quarto: : Bảng X.Y: Tên bảng {#tbl-...}
    def replace_table_caption(match):
        cap = match.group(1).strip()
        return f'<div class="table-caption" style="font-weight: 700; margin-top: 12px; margin-bottom: 4px; font-size: 10pt; color: #1e293b;">{cap}</div>'

    body_text = re.sub(r':\s*(Bảng\s+[^\{\n\r]+)(?:\{[^}]*\})?', replace_table_caption, body_text)

    # 4. Render Markdown sang HTML
    print("[2/5] Chuyển đổi Markdown sang HTML với bảng biểu và công thức toán học...")
    md_html = markdown.markdown(body_text, extensions=['extra', 'tables', 'fenced_code', 'nl2br'])

    # 5. Xây dựng Template HTML hoàn chỉnh chuẩn học thuật không bị lỗi khoảng trắng hay ngắt trang thừa
    full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Hệ Thống Định Lượng Machine Learning TradFi USD-M 24/7 — Báo Cáo Đồ Án Cuối Khóa</title>
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
  }},
  svg: {{
    fontCache: 'global'
  }}
}};
</script>
<script type="text/javascript" id="MathJax-script" async
  src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
</script>
<style>
@page {{
    size: A4;
    margin: 18mm 14mm 18mm 22mm;
}}

body {{
    font-family: 'Times New Roman', 'Liberation Serif', Times, serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a202c;
    background: #ffffff;
    margin: 0;
    padding: 0;
}}

.cover-page {{
    page-break-after: always;
    break-after: page;
}}

h1 {{
    font-size: 14.5pt;
    color: #0f172a;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 4px;
    margin-top: 22px;
    margin-bottom: 12px;
    page-break-before: always;
    break-before: page;
    page-break-after: avoid;
    break-after: avoid;
}}

/* Không ngắt trang trước h1 đầu tiên sau trang bìa */
h1:first-of-type {{
    page-break-before: avoid;
    break-before: avoid;
}}

h2 {{
    font-size: 12pt;
    color: #1e3a8a;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
    break-after: avoid;
}}

h3 {{
    font-size: 10.5pt;
    color: #334155;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
    break-after: avoid;
}}

p {{
    margin: 6px 0;
    text-align: justify;
    line-height: 1.5;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9pt;
    line-height: 1.4;
    page-break-inside: avoid;
    break-inside: avoid;
}}

th {{
    border-top: 2px solid #0f172a;
    border-bottom: 1.5px solid #0f172a;
    padding: 5px 8px;
    text-align: left;
    background-color: #f8fafc;
    font-weight: bold;
    color: #0f172a;
}}

td {{
    border-bottom: 1px solid #e2e8f0;
    padding: 5px 8px;
    vertical-align: top;
}}

tr:last-child td {{
    border-bottom: 2px solid #0f172a;
}}

/* ĐƯỜNG KẺ HR CHỈ ĐỂ PHÂN CÁCH TRỰC QUAN, TUYỆT ĐỐI KHÔNG TẠO NGẮT TRANG THỪA */
hr {{
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 16px 0;
    page-break-after: avoid;
    break-after: avoid;
}}

code {{
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    padding: 2px 4px;
    border-radius: 3px;
    color: #0f172a;
}}

pre {{
    background: #0f172a;
    color: #f8fafc;
    padding: 10px 14px;
    border-radius: 5px;
    font-size: 8pt;
    overflow-x: auto;
    page-break-inside: avoid;
    break-inside: avoid;
    line-height: 1.3;
}}

pre code {{
    background: transparent;
    color: inherit;
    padding: 0;
}}

ul, ol {{
    margin: 6px 0;
    padding-left: 20px;
}}

li {{
    margin-bottom: 4px;
}}

figure {{
    margin: 16px auto;
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
}}

.table-caption {{
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 9.5pt;
    color: #1e293b;
    text-align: left;
    page-break-after: avoid;
    break-after: avoid;
}}
</style>
</head>
<body>
{md_html}
</body>
</html>
"""

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"  [+] Đã tạo tệp HTML trung gian: {html_file}")

    # 6. Sử dụng Selenium Edge Headless để in ra PDF
    print("[3/5] Khởi động trình duyệt Edge Headless và render toàn bộ công thức MathJax...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Edge(options=options)
    try:
        driver.get('file:///' + html_file.replace('\\', '/'))
        
        # Đợi MathJax hoàn tất render công thức
        time.sleep(3)
        try:
            driver.execute_script("return window.MathJax && window.MathJax.typesetPromise ? window.MathJax.typesetPromise() : Promise.resolve();")
            time.sleep(2)
        except Exception as e:
            print(f"  [!] Lưu ý MathJax: {e}")

        print("[4/5] Xuất tệp PDF vector chất lượng cao (A4)...")
        print_opts = PrintOptions()
        print_opts.background = True
        print_opts.margin_top = 0.35
        print_opts.margin_bottom = 0.35
        print_opts.margin_left = 0.45
        print_opts.margin_right = 0.35

        pdf_base64 = driver.print_page(print_opts)
        pdf_bytes = base64.b64decode(pdf_base64)

        with open(pdf_file, 'wb') as f:
            f.write(pdf_bytes)

        pdf_size = os.path.getsize(pdf_file)
        print(f"  [+] Đã tạo tệp PDF: {pdf_file} ({pdf_size:,} bytes | {pdf_size/1024/1024:.2f} MB)")
    finally:
        driver.quit()

    # 7. Kiểm tra chất lượng từng trang (Quality Assurance Verification)
    print("\n[5/5] TIẾN HÀNH KIỂM TRA CHẤT LƯỢNG TỪNG TRANG (PAGE-BY-PAGE QA)...")
    doc = pdfium.PdfDocument(pdf_file)
    total_pages = len(doc)
    print(f"Tổng số trang: {total_pages} trang")

    empty_pages = []
    sparse_pages = []

    for i in range(total_pages):
        page = doc[i]
        # Render trang sang grayscale image để phân tích mật độ điểm ảnh
        im = page.render(scale=1.0).to_pil().convert('L')
        arr = np.array(im)
        non_white = int((arr < 248).sum())
        total_px = arr.size
        density_pct = (non_white / total_px) * 100

        text = page.get_textpage().get_text_range().strip()
        first_line = text.split('\n')[0] if text else '(TRỐNG)'

        status = "OK"
        if density_pct < 0.5:
            status = "LỖI: TRANG TRẮNG (EMPTY)"
            empty_pages.append(i + 1)
        elif density_pct < 2.0:
            status = "CẢNH BÁO: QUÁ ÍT NỘI DUNG (SPARSE)"
            sparse_pages.append(i + 1)

        print(f"  Trang {i+1:02d}/{total_pages:02d} | Mật độ: {density_pct:5.2f}% | Ký tự: {len(text):4d} | Đầu: {first_line[:35]:<35} | {status}")

    # Đánh giá kết quả
    print("\n=== KẾT QUẢ KIỂM SOÁT CHẤT LƯỢNG (QA SUMMARY) ===")
    print(f"- Tổng số trang: {total_pages}")
    print(f"- Trang bìa (Trang 1): Có chứa đầy đủ thông tin ĐHQG TP.HCM và địa danh TP.HCM: {'TP. HỒ CHÍ MINH' in doc[0].get_textpage().get_text_range()}")
    print(f"- Số trang trắng hoàn toàn (Empty Pages): {len(empty_pages)} -> {empty_pages if empty_pages else 'KHÔNG CÓ'}")
    print(f"- Số trang thưa thớt (Sparse Pages < 2%): {len(sparse_pages)} -> {sparse_pages if sparse_pages else 'KHÔNG CÓ'}")

    if not empty_pages and len(sparse_pages) <= 1:
        print(">>> ĐẠT CHUẨN XUẤT BẢN HỌC THUẬT (PUBLICATION GRADE)! <<<")
        return True
    else:
        print(">>> CẦN TIẾP TỤC TINH CHỈNH ĐỂ ĐẠT CHUẨN HOÀN HẢO. <<<")
        return False

if __name__ == '__main__':
    convert_qmd_to_pdf()
