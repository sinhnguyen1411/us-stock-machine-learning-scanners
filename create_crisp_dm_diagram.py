"""
Generate High-Resolution CRISP-DM 6-Phase Lifecycle Diagram with Bidirectional Iterative Loops
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def generate_crisp_dm_diagram(output_paths):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300, facecolor='#0B0F17')
    ax.set_facecolor('#0B0F17')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Color Palette
    CYAN = '#00F2FE'
    GREEN = '#00E676'
    YELLOW = '#FFB300'
    PURPLE = '#B388FF'
    RED = '#FF3366'
    CARD_BG = '#151D2A'
    BORDER_COL = '#1E293B'
    TEXT_WHITE = '#FFFFFF'
    TEXT_MUTED = '#94A3B8'
    TEXT_DIM = '#64748B'

    # Title & Header
    ax.text(8.0, 8.4, 'CHU TRÌNH CHUẨN QUỐC TẾ CRISP-DM VỚI VÒNG LẶP PHẢN HỒI 2 CHIỀU',
            ha='center', va='center', fontsize=18, fontweight='bold', color=CYAN, fontfamily='sans-serif')
    ax.text(8.0, 7.95, 'Cross-Industry Standard Process for Data Mining — Continuous Improvement & Model Optimization',
            ha='center', va='center', fontsize=11, color=TEXT_MUTED, fontfamily='sans-serif')

    # Define Node positions (Circular / Cycle Layout)
    # 1: Top Left (Business)
    # 2: Top Right (Data)
    # 3: Mid-Bottom Right (Data Prep)
    # 4: Mid-Bottom Left (Modeling)
    # 5: Bottom Left (Evaluation)
    # 6: Bottom Right (Deployment)

    nodes = [
        {"id": 1, "x": 2.2, "y": 5.4, "w": 3.6, "h": 1.6, "title": "PHASE 1: THẤU HIỂU NGHIỆP VỤ", "sub": "Xác định mục tiêu bắt dòng tiền thể chế\nPhân loại 4 phiên giao dịch New York", "color": CYAN},
        {"id": 2, "x": 10.2, "y": 5.4, "w": 3.6, "h": 1.6, "title": "PHASE 2: THẤU HIỂU DỮ LIỆU", "sub": "Sổ lệnh, luồng khớp Taker Buy/Sell\nChuỗi nến 5M từ Binance Matching API", "color": GREEN},
        {"id": 3, "x": 10.2, "y": 2.7, "w": 3.6, "h": 1.6, "title": "PHASE 3: TIỀN XỬ LÝ DỮ LIỆU", "sub": "Làm sạch nến, lọc token đòn bẩy\nVector hóa VWAP, RSI 14, ATR, EWMA", "color": YELLOW},
        {"id": 4, "x": 2.2, "y": 2.7, "w": 3.6, "h": 1.6, "title": "PHASE 4: XÂY DỰNG MÔ HÌNH", "sub": "Thuật toán Ensemble ML Score (0-100)\nPhân loại 5 trạng thái tín hiệu vi mô", "color": PURPLE},
        {"id": 5, "x": 2.2, "y": 0.5, "w": 3.6, "h": 1.5, "title": "PHASE 5: ĐÁNH GIÁ THỰC NGHIỆM", "sub": "Cascade Backtest (Win-Rate 72.4%)\nĐo lường Profit Factor, Max Drawdown", "color": RED},
        {"id": 6, "x": 10.2, "y": 0.5, "w": 3.6, "h": 1.5, "title": "PHASE 6: TRIỂN KHAI & GIÁM SÁT", "sub": "Web Terminal 3.5s, Workstation Soi Nến\nCircuit Breaker khóa rủi ro tự động", "color": GREEN},
    ]

    # Draw Nodes
    for n in nodes:
        rect = patches.FancyBboxPatch((n["x"], n["y"]), n["w"], n["h"],
                                      boxstyle="round,pad=0.15,rounding_size=0.2",
                                      linewidth=1.8, edgecolor=n["color"], facecolor=CARD_BG)
        ax.add_patch(rect)
        ax.text(n["x"] + n["w"]/2, n["y"] + n["h"] - 0.35, n["title"],
                ha='center', va='center', fontsize=11, fontweight='bold', color=n["color"])
        ax.text(n["x"] + n["w"]/2, n["y"] + (n["h"] - 0.35)/2, n["sub"],
                ha='center', va='center', fontsize=8.8, color='#CBD5E1', linespacing=1.3)

    # ── ARROWS & FEEDBACK LOOPS ──

    def draw_double_arrow(x1, y1, x2, y2, color, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="<->,head_width=0.45,head_length=0.6", color=color, lw=2.5))
        if label:
            mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mid_x, mid_y + 0.25, label, ha='center', va='center', fontsize=8.5, fontweight='bold', color=color,
                    bbox=dict(boxstyle="round,pad=0.2", fc='#0F172A', ec=color, lw=1))

    def draw_single_arrow(x1, y1, x2, y2, color, label="", rad=0.0):
        con = f"arc3,rad={rad}" if rad != 0 else "arc3"
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.6", color=color, lw=2.5, connectionstyle=con))
        if label:
            mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mid_x, mid_y, label, ha='center', va='center', fontsize=8.5, fontweight='bold', color=color,
                    bbox=dict(boxstyle="round,pad=0.2", fc='#0F172A', ec=color, lw=1))

    # 1. Phase 1 <---> Phase 2 (Bidirectional Business ⇄ Data)
    draw_double_arrow(6.1, 6.2, 9.9, 6.2, CYAN, label="1. Nghiệp Vụ ⇄ Dữ Liệu")

    # 2. Phase 2 ---> Phase 3 (Data -> Data Prep)
    draw_single_arrow(12.0, 5.2, 12.0, 4.5, GREEN)

    # 3. Phase 3 <---> Phase 4 (Bidirectional Prep ⇄ Modeling)
    draw_double_arrow(9.9, 3.5, 6.1, 3.5, YELLOW, label="2. Tiền Xử Lý ⇄ Mô Hình")

    # 4. Phase 4 ---> Phase 5 (Modeling -> Evaluation)
    draw_single_arrow(4.0, 2.5, 4.0, 2.2, PURPLE)

    # 5. Phase 5 <---> Phase 1 (Evaluation Feedback Loop to Business)
    ax.annotate('', xy=(1.9, 6.2), xytext=(1.9, 1.2),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.6", color=RED, lw=2.2, connectionstyle="arc3,rad=0.35"))
    ax.text(0.65, 3.7, '3. Phản Hồi Đánh Giá ⇄ Nghiệp Vụ\n(Chưa đạt KPI -> Tinh chỉnh)',
            ha='center', va='center', fontsize=8, fontweight='bold', color=RED,
            bbox=dict(boxstyle="round,pad=0.2", fc='#0F172A', ec=RED, lw=1))

    # 6. Phase 5 ---> Phase 6 (Evaluation -> Deployment when Approved)
    draw_single_arrow(6.1, 1.2, 9.9, 1.2, GREEN, label="Đạt chuẩn -> Triển khai")

    # 7. Phase 6 ---> Phase 1 & 2 (Continuous Production Improvement Loop)
    ax.annotate('', xy=(14.1, 6.2), xytext=(14.1, 1.2),
                arrowprops=dict(arrowstyle="->,head_width=0.45,head_length=0.6", color=CYAN, lw=2.2, connectionstyle="arc3,rad=-0.35"))
    ax.text(15.35, 3.7, '4. Vận Hành ⇄ Thu Thập Mới\n(Giám sát Drift & Cải tiến)',
            ha='center', va='center', fontsize=8, fontweight='bold', color=CYAN,
            bbox=dict(boxstyle="round,pad=0.2", fc='#0F172A', ec=CYAN, lw=1))

    # Center summary banner
    center_box = patches.FancyBboxPatch((6.4, 4.3), 3.2, 1.2,
                                        boxstyle="round,pad=0.1,rounding_size=0.15",
                                        linewidth=1.2, edgecolor=CYAN, facecolor='#111C2E')
    ax.add_patch(center_box)
    ax.text(8.0, 5.15, 'TẬP TRUNG VÀO DỮ LIỆU', ha='center', va='center', fontsize=9.5, fontweight='bold', color=CYAN)
    ax.text(8.0, 4.65, 'Tối ưu liên tục qua 4 vòng lặp\nphản hồi 2 chiều khép kín', ha='center', va='center', fontsize=8, color='#E2E8F0')

    plt.tight_layout()
    for out in output_paths:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        plt.savefig(out, facecolor='#0B0F17', edgecolor='none', bbox_inches='tight', pad_inches=0.2)
        print(f"[+] Saved diagram to: {out}")
    plt.close()

if __name__ == "__main__":
    generate_crisp_dm_diagram([
        "assets/slides/crisp_dm_cycle_diagram.png",
        "apps/web_terminal/static/img/slides/crisp_dm_cycle_diagram.png"
    ])
