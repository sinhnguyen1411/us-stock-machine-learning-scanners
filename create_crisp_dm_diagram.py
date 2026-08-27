"""
Generate Pixel-Perfect, Academic CRISP-DM 6-Phase Lifecycle Diagram
Standard Canonical Flow with Bidirectional Iterative Loops and NO Text Overlaps or Clipping
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def generate_crisp_dm_diagram(output_paths):
    # Canvas size: 18x10 for generous margins
    fig, ax = plt.subplots(figsize=(18, 10), dpi=300, facecolor='#0B0F17')
    ax.set_facecolor('#0B0F17')
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Color Palette
    CYAN = '#00F2FE'
    GREEN = '#00E676'
    YELLOW = '#FFB300'
    PURPLE = '#B388FF'
    RED = '#FF3366'
    CARD_BG = '#151D2A'
    TEXT_WHITE = '#FFFFFF'
    TEXT_MUTED = '#94A3B8'

    # Title & Subtitle
    ax.text(9.0, 9.35, 'CHU TRÌNH CHUẨN QUỐC TẾ CRISP-DM (6 GIAI ĐOẠN KHÉP KÍN)',
            ha='center', va='center', fontsize=18, fontweight='bold', color=CYAN, fontfamily='sans-serif')
    ax.text(9.0, 8.85, 'Cross-Industry Standard Process for Data Mining — 4 Vòng Lặp Phản Hồi 2 Chiều Tối Ưu Liên Tục',
            ha='center', va='center', fontsize=12, color=TEXT_MUTED, fontfamily='sans-serif')

    # Coordinates for the 6 boxes (Center around x=9.0)
    # Left Column: x = 3.6, w = 4.4 (Right edge = 8.0)
    # Right Column: x = 10.0, w = 4.4 (Left edge = 10.0)
    # Gap between columns: 2.0 (from 8.0 to 10.0)
    # Row 1 (Top): y = 6.0, h = 1.7
    # Row 2 (Mid): y = 3.4, h = 1.7
    # Row 3 (Bot): y = 0.8, h = 1.7

    nodes = [
        {
            "id": 1, "x": 3.6, "y": 6.0, "w": 4.4, "h": 1.7,
            "title": "PHASE 1: THẤU HIỂU NGHIỆP VỤ",
            "desc": "Xác định mục tiêu bắt dòng tiền thể chế\nPhân loại 4 phiên giao dịch New York",
            "color": CYAN
        },
        {
            "id": 2, "x": 10.0, "y": 6.0, "w": 4.4, "h": 1.7,
            "title": "PHASE 2: THẤU HIỂU DỮ LIỆU",
            "desc": "Thu thập sổ lệnh, Taker Buy/Sell\nChuỗi nến 5M từ Binance Matching API",
            "color": GREEN
        },
        {
            "id": 3, "x": 10.0, "y": 3.4, "w": 4.4, "h": 1.7,
            "title": "PHASE 3: TIỀN XỬ LÝ DỮ LIỆU",
            "desc": "Làm sạch nến, lọc token đòn bẩy\nVector hóa VWAP, RSI 14, ATR, EWMA",
            "color": YELLOW
        },
        {
            "id": 4, "x": 3.6, "y": 3.4, "w": 4.4, "h": 1.7,
            "title": "PHASE 4: XÂY DỰNG MÔ HÌNH",
            "desc": "Thuật toán Ensemble ML Score (0-100)\nPhân loại 5 trạng thái tín hiệu vi mô",
            "color": PURPLE
        },
        {
            "id": 5, "x": 3.6, "y": 0.8, "w": 4.4, "h": 1.7,
            "title": "PHASE 5: ĐÁNH GIÁ THỰC NGHIỆM",
            "desc": "Cascade Backtest (Win-Rate 72.4%)\nĐo lường Profit Factor, Max Drawdown",
            "color": RED
        },
        {
            "id": 6, "x": 10.0, "y": 0.8, "w": 4.4, "h": 1.7,
            "title": "PHASE 6: TRIỂN KHAI & GIÁM SÁT",
            "desc": "Web Terminal 3.5s, Workstation Soi Nến\nCircuit Breaker khóa rủi ro tự động",
            "color": GREEN
        }
    ]

    # Draw Boxes
    for n in nodes:
        rect = patches.FancyBboxPatch((n["x"], n["y"]), n["w"], n["h"],
                                      boxstyle="round,pad=0.1,rounding_size=0.15",
                                      linewidth=2.2, edgecolor=n["color"], facecolor=CARD_BG)
        ax.add_patch(rect)
        # Header text
        ax.text(n["x"] + n["w"]/2, n["y"] + n["h"] - 0.42, n["title"],
                ha='center', va='center', fontsize=11.5, fontweight='bold', color=n["color"])
        # Body text
        ax.text(n["x"] + n["w"]/2, n["y"] + 0.6, n["desc"],
                ha='center', va='center', fontsize=9.8, color='#E2E8F0', linespacing=1.35)

    # ── ARROWS & FEEDBACK LOOPS ──

    # 1. Top Horizontal Double Arrow: Phase 1 <---> Phase 2
    ax.annotate('', xy=(9.9, 6.85), xytext=(8.1, 6.85),
                arrowprops=dict(arrowstyle="<->,head_width=0.45,head_length=0.55", color=CYAN, lw=2.5))
    ax.text(9.0, 7.25, 'Nghiệp Vụ ⇄ Dữ Liệu', ha='center', va='center', fontsize=9.0, fontweight='bold', color=CYAN,
            bbox=dict(boxstyle="round,pad=0.25", fc='#0F172A', ec=CYAN, lw=1.2))

    # 2. Right Vertical Single Arrow: Phase 2 ---> Phase 3
    ax.annotate('', xy=(12.2, 5.2), xytext=(12.2, 5.9),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.55", color=GREEN, lw=2.5))

    # 3. Middle Horizontal Double Arrow: Phase 3 <---> Phase 4
    ax.annotate('', xy=(8.1, 4.25), xytext=(9.9, 4.25),
                arrowprops=dict(arrowstyle="<->,head_width=0.45,head_length=0.55", color=YELLOW, lw=2.5))
    ax.text(9.0, 4.65, 'Tiền Xử Lý ⇄ Mô Hình', ha='center', va='center', fontsize=9.0, fontweight='bold', color=YELLOW,
            bbox=dict(boxstyle="round,pad=0.25", fc='#0F172A', ec=YELLOW, lw=1.2))

    # 4. Left Vertical Single Arrow: Phase 4 ---> Phase 5
    ax.annotate('', xy=(5.8, 2.6), xytext=(5.8, 3.3),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.55", color=PURPLE, lw=2.5))

    # 5. Bottom Horizontal Single Arrow: Phase 5 ---> Phase 6 (Đạt chuẩn -> Triển khai)
    ax.annotate('', xy=(9.9, 1.65), xytext=(8.1, 1.65),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.55", color=GREEN, lw=2.5))
    ax.text(9.0, 2.05, 'Đạt Chuẩn KPI ➔ Triển Khai', ha='center', va='center', fontsize=9.0, fontweight='bold', color=GREEN,
            bbox=dict(boxstyle="round,pad=0.25", fc='#0F172A', ec=GREEN, lw=1.2))

    # 6. EXTERNAL LEFT FEEDBACK LOOP: Phase 5 (Evaluation) ---> Phase 1 (Business Understanding)
    # Left margin curve (from x=3.5 down to x=3.5 up, looping around x=1.8)
    ax.annotate('', xy=(3.5, 6.85), xytext=(3.5, 1.65),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.55", color=RED, lw=2.5,
                                connectionstyle="arc3,rad=-0.42"))
    ax.text(1.8, 4.25, 'Phản Hồi Đánh Giá\n(Chưa Đạt KPI ➔\nHiệu Chỉnh Nghiệp Vụ)',
            ha='center', va='center', fontsize=8.8, fontweight='bold', color=RED,
            bbox=dict(boxstyle="round,pad=0.3", fc='#0F172A', ec=RED, lw=1.2))

    # 7. EXTERNAL RIGHT FEEDBACK LOOP: Phase 6 (Deployment) ---> Phase 1 & 2 (Continuous Online Data)
    # Right margin curve (from x=14.5 down to x=14.5 up, looping around x=16.2)
    ax.annotate('', xy=(14.5, 6.85), xytext=(14.5, 1.65),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.55", color=CYAN, lw=2.5,
                                connectionstyle="arc3,rad=0.42"))
    ax.text(16.2, 4.25, 'Vòng Lặp Vận Hành\n(Giám Sát Drift ➔\nNạp Dữ Liệu Mới)',
            ha='center', va='center', fontsize=8.8, fontweight='bold', color=CYAN,
            bbox=dict(boxstyle="round,pad=0.3", fc='#0F172A', ec=CYAN, lw=1.2))

    plt.tight_layout()
    for out in output_paths:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        plt.savefig(out, facecolor='#0B0F17', edgecolor='none', bbox_inches='tight', pad_inches=0.2)
        print(f"[+] Successfully saved clean CRISP-DM diagram to: {out}")
    plt.close()

if __name__ == "__main__":
    generate_crisp_dm_diagram([
        "assets/slides/crisp_dm_cycle_diagram_v3.png",
        "apps/web_terminal/static/img/slides/crisp_dm_cycle_diagram_v3.png"
    ])
