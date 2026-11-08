#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script đóng gói tự động hồ sơ đồ án cuối khóa SIC 2026 AI1 UIT
Học viên: NGUYỄN DƯƠNG MẠNH SINH (MSSV: 24210169) - Lớp: AI1 UFM
"""

import os
import zipfile

def package_submission():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_name = '[Nhom_AI1_UFM]_[24210169]_[US_Stock_Machine_Learning_Scanners].zip'
    zip_path = os.path.join(base_dir, zip_name)

    files_to_pack = [
        'tieu_luan_cuoi_khoa_us_stock_ml_scanners.pdf',
        'tieu_luan_cuoi_khoa_us_stock_ml_scanners.qmd',
        'US_Stock_ML_Scanners_CRISP_DM.ipynb',
        'US_Stock_ML_Scanners_Final_Project_30_Slides.pptx',
        'README.md',
    ]

    print(f'Bắt đầu đóng gói hồ sơ nộp bài vào: {zip_name}...')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files_to_pack:
            full_p = os.path.join(base_dir, f)
            if os.path.exists(full_p):
                z.write(full_p, arcname=f)
                print(f'  [+] Đã thêm tệp: {f}')
        
        # Thêm thư mục figures/
        fig_dir = os.path.join(base_dir, 'figures')
        if os.path.exists(fig_dir):
            count = 0
            for f in os.listdir(fig_dir):
                if f.endswith('.png'):
                    z.write(os.path.join(fig_dir, f), arcname=os.path.join('figures', f))
                    count += 1
            print(f'  [+] Đã thêm thư mục figures/ ({count} biểu đồ/hình ảnh)')
        
        # Thêm thư mục data/
        data_dir = os.path.join(base_dir, 'data')
        if os.path.exists(data_dir):
            count = 0
            for f in os.listdir(data_dir):
                if f.endswith('.csv'):
                    z.write(os.path.join(data_dir, f), arcname=os.path.join('data', f))
                    count += 1
            print(f'  [+] Đã thêm thư mục data/ ({count} tệp dữ liệu CSV)')

    zip_size = os.path.getsize(zip_path)
    print(f'Hoàn tất! Kích thước file nén: {zip_size:,} bytes ({zip_size/1024/1024:.2f} MB)')

if __name__ == '__main__':
    package_submission()

