"""
Generate High-Legibility, Large-Font CRISP-DM 6-Phase Diagram (300 DPI)
All Text Rendered with Large, Bold, Crisp Typography
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def generate_crisp_dm_diagram(output_paths):
    # Tight canvas to eliminate wasted padding: 16x10
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300, facecolor='#0B0F17')
    ax.set_facecolor('#0B0F17')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Color Palette
    CYAN = '#00F2FE'
    GREEN = '#00E676'
    YELLOW = '#FFB300'
    PURPLE = '#B388FF'
    RED = '#FF3366'
    CARD_BG = '#151D2A'

    # Title & Subtitle (Large font)
    ax.text(8.0, 9.4, 'CHU TRÌNH CHUẨN QUỐC TẾ CRISP-DM 6 GIAI ĐOẠN',
            ha='center', va='center', fontsize=22, fontweight='bold', color=CYAN, fontfamily='sans-serif')
    ax.text(8.0, 8.85, '4 Vòng Lặp Phản Hồi 2 Chiều Tối Ưu Liên Tục',
            ha='center', va='center', fontsize=14, fontweight='bold', color='#94A3B8', fontfamily='sans-serif')

    # Dimensions for the 6 boxes (Large sizes filling canvas)
    # Left column: x = 2.4, w = 4.8
    # Right column: x = 8.8, w = 4.8
    # Row 1 (Top): y = 5.9, h = 2.2
    # Row 2 (Mid): y = 3.2, h = 2.2
    # Row 3 (Bot): y = 0.5, h = 2.2

    nodes = [
        {
            "id": 1, "x": 2.4, "y": 5.9, "w": 4.8, "h": 2.2,
            "title": "PHASE 1: NGHIỆP VỤ",
            "desc": "• Bắt dòng tiền gom thể chế\n• Phân loại 4 phiên New York",
            "color": CYAN
        },
        {
            "id": 2, "x": 8.8, "y": 5.9, "w": 4.8, "h": 2.2,
            "title": "PHASE 2: DỮ LIỆU SỔ LỆNH",
            "desc": "• Taker Buy/Sell từ sàn Binance\n• Chuỗi nến 5M của 90+ mã",
            "color": GREEN
        },
        {
            "id": 3, "x": 8.8, "y": 3.2, "w": 4.8, "h": 2.2,
            "title": "PHASE 3: TIỀN XỬ LÝ",
            "desc": "• Làm sạch & Lọc token rác\n• Vector hóa VWAP, RSI, ATR",
            "color": YELLOW
        },
        {
            "id": 4, "x": 2.4, "y": 3.2, "w": 4.8, "h": 2.2,
            "title": "PHASE 4: MÔ HÌNH ML",
            "desc": "• Ensemble ML Score (0-100)\n• Phân loại 5 trạng thái tín hiệu",
            "color": PURPLE
        },
        {
            "id": 5, "x": 2.4, "y": 0.5, "w": 4.8, "h": 2.2,
            "title": "PHASE 5: ĐÁNH GIÁ",
            "desc": "• Backtest Win-Rate 72.4%\n• Profit Factor 2.68, Max DD",
            "color": RED
        },
        {
            "id": 6, "x": 8.8, "y": 0.5, "w": 4.8, "h": 2.2,
            "title": "PHASE 6: TRIỂN KHAI",
            "desc": "• Web Terminal quét 3.5s\n• Workstation & Circuit Breaker",
            "color": GREEN
        }
    ]

    # Draw Boxes
    for n in nodes:
        rect = patches.FancyBboxPatch((n["x"], n["y"]), n["w"], n["h"],
                                      boxstyle="round,pad=0.08,rounding_size=0.18",
                                      linewidth=2.8, edgecolor=n["color"], facecolor=CARD_BG)
        ax.add_patch(rect)
        # Header text (Large font 15pt)
        ax.text(n["x"] + n["w"]/2, n["y"] + n["h"] - 0.55, n["title"],
                ha='center', va='center', fontsize=15, fontweight='bold', color=n["color"])
        # Body text (Large font 12.5pt)
        ax.text(n["x"] + n["w"]/2, n["y"] + 0.75, n["desc"],
                ha='center', va='center', fontsize=12.5, fontweight='bold', color='#FFFFFF', linespacing=1.4)

    # ── ARROWS & FEEDBACK LABELS (Enlarged) ──

    # 1. Top Horizontal Double Arrow: Phase 1 <---> Phase 2
    ax.annotate('', xy=(8.7, 7.0), xytext=(7.3, 7.0),
                arrowprops=dict(arrowstyle="<->,head_width=0.55,head_length=0.7", color=CYAN, lw=3.2))
    ax.text(8.0, 7.45, 'Nghiệp Vụ ⇄ Dữ Liệu', ha='center', va='center', fontsize=11, fontweight='bold', color=CYAN,
            bbox=dict(boxstyle="round,pad=0.3", fc='#0F172A', ec=CYAN, lw=1.5))

    # 2. Right Vertical Single Arrow: Phase 2 ---> Phase 3
    ax.annotate('', xy=(11.2, 5.5), xytext=(11.2, 5.8),
                arrowprops=dict(arrowstyle="->,head_width=0.55,head_length=0.7", color=GREEN, lw=3.2))

    # 3. Middle Horizontal Double Arrow: Phase 3 <---> Phase 4
    ax.annotate('', xy=(7.3, 4.3), xytext=(8.7, 4.3),
                arrowprops=dict(arrowstyle="<->,head_width=0.55,head_length=0.7", color=YELLOW, lw=3.2))
    ax.text(8.0, 4.75, 'Tiền Xử Lý ⇄ Mô Hình', ha='center', va='center', fontsize=11, fontweight='bold', color=YELLOW,
            bbox=dict(boxstyle="round,pad=0.3", fc='#0F172A', ec=YELLOW, lw=1.5))

    # 4. Left Vertical Single Arrow: Phase 4 ---> Phase 5
    ax.annotate('', xy=(4.8, 2.8), xytext=(4.8, 3.1),
                arrowprops=dict(arrowstyle="->,head_width=0.55,head_length=0.7", color=PURPLE, lw=3.2))

    # 5. Bottom Horizontal Single Arrow: Phase 5 ---> Phase 6
    ax.annotate('', xy=(8.7, 1.6), xytext=(7.3, 1.6),
                arrowprops=dict(arrowstyle="->,head_width=0.55,head_length=0.7", color=GREEN, lw=3.2))
    ax.text(8.0, 2.05, 'Đạt KPI ➔ Triển Khai', ha='center', va='center', fontsize=11, fontweight='bold', color=GREEN,
            bbox=dict(boxstyle="round,pad=0.3", fc='#0F172A', ec=GREEN, lw=1.5))

    # 6. EXTERNAL LEFT FEEDBACK: Phase 5 ---> Phase 1
    ax.annotate('', xy=(2.3, 7.0), xytext=(2.3, 1.6),
                arrowprops=dict(arrowstyle="->,head_width=0.55,head_length=0.7", color=RED, lw=3.2,
                                connectionstyle="arc3,rad=-0.38"))
    ax.text(0.9, 4.3, 'Chưa Đạt KPI ➔\nHiệu Chỉnh Lại',
            ha='center', va='center', fontsize=10.5, fontweight='bold', color=RED,
            bbox=dict(boxstyle="round,pad=0.35", fc='#0F172A', ec=RED, lw=1.5))

    # 7. EXTERNAL RIGHT FEEDBACK: Phase 6 ---> Phase 1 & 2
    ax.annotate('', xy=(13.7, 7.0), xytext=(13.7, 1.6),
                arrowprops=dict(arrowstyle="->,head_width=0.55,head_length=0.7", color=CYAN, lw=3.2,
                                connectionstyle="arc3,rad=0.38"))
    ax.text(15.1, 4.3, 'Giám Sát Drift ➔\nNạp Dữ Liệu Mới',
            ha='center', va='center', fontsize=10.5, fontweight='bold', color=CYAN,
            bbox=dict(boxstyle="round,pad=0.35", fc='#0F172A', ec=CYAN, lw=1.5))

    plt.tight_layout()
    for out in output_paths:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        plt.savefig(out, facecolor='#0B0F17', edgecolor='none', bbox_inches='tight', pad_inches=0.1)
        print(f"[+] Saved large-font diagram to: {out}")
    plt.close()

if __name__ == "__main__":
    generate_crisp_dm_diagram([
        "assets/slides/crisp_dm_cycle_diagram_v3.png",
        "apps/web_terminal/static/img/slides/crisp_dm_cycle_diagram_v3.png"
    ])
