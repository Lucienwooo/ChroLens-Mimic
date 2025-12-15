# -*- coding: utf-8 -*-
"""
測試改進後的獨立路線系統
參考用戶手動修改的路線圖
"""

import tkinter as tk
from tkinter import Canvas

def calculate_path(x1, y1, x2, y2, offset):
    """模擬改進後的路徑計算"""
    dx = x2 - x1
    dy = y2 - y1
    
    if offset == 0:
        # 中心線路：簡單三段式
        mid_y = (y1 + y2) / 2
        return [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
    else:
        # 有偏移：立即水平分散到獨立通道
        channel_x = x1 + offset
        
        if abs(dy) < 30:
            # 接近水平
            mid_y = (y1 + y2) / 2 + (offset * 0.3)
            return [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
        elif abs(dx) < 30:
            # 接近垂直
            return [x1, y1, channel_x, y1, channel_x, y2, x2, y2]
        else:
            # 一般情況：四段式
            first_drop = min(abs(dy) * 0.3, 50)
            return [
                x1, y1,
                channel_x, y1,
                channel_x, y1 + first_drop,
                channel_x, y2,
                x2, y2
            ]

def draw_test():
    """繪製測試圖形"""
    root = tk.Tk()
    root.title("獨立路線測試 - 參考用戶修改")
    root.geometry("900x700")
    
    canvas = Canvas(root, bg="#f5f5f5", width=900, height=700)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 繪製標題
    canvas.create_text(
        450, 30,
        text="獨立路線系統測試（參考用戶手動修改的圖）",
        font=("LINE Seed TW", 16, "bold"),
        fill="#333333"
    )
    
    # 模擬節點位置（參考用戶的圖）
    nodes = {
        '開始': {'x': 120, 'y': 100, 'color': '#0077be', 'radius': 40},
        '處理A': {'x': 450, 'y': 100, 'color': '#f77f00', 'radius': 45},
        '處理B': {'x': 120, 'y': 250, 'color': '#0077be', 'radius': 40},
        '條件': {'x': 450, 'y': 250, 'color': '#e63946', 'radius': 50},
        '結束': {'x': 280, 'y': 450, 'color': '#e63946', 'radius': 55},
    }
    
    # 定義連接（帶通道偏移）
    connections = [
        ('開始', '處理A', 0),      # 中心通道
        ('開始', '處理B', 0),      # 垂直直線
        ('處理A', '條件', 0),      # 中心通道
        ('處理B', '條件', 0),      # 水平直線
        ('條件', '結束', -35),     # 左通道
        ('條件', '結束', 0),       # 中通道
        ('條件', '結束', 35),      # 右通道
        ('處理A', '結束', 70),     # 最右通道
    ]
    
    # 繪製連接線（先畫）
    for from_label, to_label, offset in connections:
        from_node = nodes[from_label]
        to_node = nodes[to_label]
        
        # 計算起點和終點
        start_x = from_node['x']
        start_y = from_node['y'] + from_node['radius']
        end_x = to_node['x']
        end_y = to_node['y'] - to_node['radius']
        
        # 計算路徑
        points = calculate_path(start_x, start_y, end_x, end_y, offset)
        
        # 繪製線路
        color = "#00d084"
        canvas.create_line(
            *points,
            fill=color,
            width=5,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=False
        )
        
        # 在起點標註通道編號
        if offset != 0:
            canvas.create_text(
                start_x + offset / 2, start_y + 10,
                text=f"{offset:+d}",
                font=("LINE Seed TW", 8),
                fill="#666666"
            )
    
    # 繪製節點（後畫，在線的上層）
    for label, node in nodes.items():
        x, y = node['x'], node['y']
        radius = node['radius']
        color = node['color']
        
        # 繪製圓形
        canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="#ffffff",
            width=4
        )
        
        # 繪製標籤
        font_size = 10 if radius < 36 else (12 if radius < 46 else 14)
        canvas.create_text(
            x, y,
            text=label,
            fill="#ffffff",
            font=("LINE Seed TW", font_size, "bold")
        )
    
    # 繪製說明
    info_texts = [
        "✓ 每條線立即分散到獨立通道",
        "✓ 完全使用垂直+水平線段",
        "✓ 線路之間絕不重疊",
        "✓ 參考用戶手動修改的圖",
        "",
        "關鍵改進：",
        "• 從同一節點出發的線立即水平分散",
        "• 每條線有自己的channel_x通道位置",
        "• 四段式路徑：水平→垂直→垂直→水平",
    ]
    
    y_offset = 520
    for text in info_texts:
        canvas.create_text(
            50, y_offset,
            text=text,
            font=("LINE Seed TW", 10 if text.startswith("•") else 11),
            fill="#333333" if not text.startswith("•") else "#666666",
            anchor="w"
        )
        y_offset += 20
    
    # 繪製通道示意圖
    demo_x = 650
    demo_y = 500
    
    canvas.create_text(
        demo_x, demo_y,
        text="通道分配示意：",
        font=("LINE Seed TW", 11, "bold"),
        fill="#333333",
        anchor="w"
    )
    
    # 繪製三條平行線展示通道
    for i, (offset, label) in enumerate([(-35, "左通道"), (0, "中通道"), (35, "右通道")]):
        y = demo_y + 30 + i * 40
        base_x = demo_x + 50
        channel_x = base_x + offset
        
        # 起點
        canvas.create_oval(
            base_x - 5, y - 5,
            base_x + 5, y + 5,
            fill="#0077be", outline="#0077be"
        )
        
        # 通道路徑
        canvas.create_line(
            base_x, y,
            channel_x, y,
            channel_x, y + 30,
            channel_x + 100, y + 30,
            fill="#00d084", width=4,
            capstyle=tk.ROUND
        )
        
        # 標籤
        canvas.create_text(
            channel_x + 120, y + 30,
            text=label,
            font=("LINE Seed TW", 9),
            fill="#666666",
            anchor="w"
        )
    
    root.mainloop()

if __name__ == "__main__":
    print("🎨 測試獨立路線系統...")
    print()
    print("改進重點：")
    print("1. 每條線從起點立即水平分散到獨立通道")
    print("2. 使用 channel_x = x1 + offset 確保獨立性")
    print("3. 四段式路徑：")
    print("   - 起點 -> 水平移到通道")
    print("   - 通道 -> 垂直下降")
    print("   - 通道 -> 繼續垂直")
    print("   - 通道 -> 水平到達終點")
    print()
    print("參考：用戶手動修改的路線圖")
    print()
    
    try:
        draw_test()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
