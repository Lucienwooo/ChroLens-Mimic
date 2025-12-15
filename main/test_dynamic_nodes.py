# -*- coding: utf-8 -*-
"""
測試圖形模式的改進：
1. 節點根據連接數量動態調整大小
2. 路線獨立不重疊，只會交叉
3. 使用 LINE Seed 字體
"""

import tkinter as tk
from tkinter import Canvas

# 模擬節點數據
test_nodes = {
    '#開始': {'x': 150, 'y': 80, 'connections': 1, 'radius': 28},   # 1個連接 -> 25+3=28
    '#處理A': {'x': 450, 'y': 80, 'connections': 3, 'radius': 34},  # 3個連接 -> 25+9=34
    '#處理B': {'x': 150, 'y': 200, 'connections': 2, 'radius': 31}, # 2個連接 -> 25+6=31
    '#條件': {'x': 450, 'y': 200, 'connections': 5, 'radius': 40},  # 5個連接 -> 25+15=40
    '#結束': {'x': 300, 'y': 320, 'connections': 8, 'radius': 49},  # 8個連接 -> 25+24=49
}

test_connections = [
    ('#開始', '#處理A', 0),    # 通道0
    ('#開始', '#處理B', 35),   # 通道1 (35px偏移)
    ('#處理A', '#條件', 0),    # 通道0
    ('#處理B', '#條件', 35),   # 通道1
    ('#條件', '#結束', -35),   # 通道-1
    ('#條件', '#結束', 0),     # 通道0
    ('#條件', '#結束', 35),    # 通道1
    ('#處理A', '#結束', 70),   # 通道2
]

def draw_test():
    """繪製測試圖形"""
    root = tk.Tk()
    root.title("圖形模式改進測試")
    root.geometry("800x600")
    
    canvas = Canvas(root, bg="#f5f5f5", width=800, height=600)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 繪製標題
    canvas.create_text(
        400, 30,
        text="圖形模式改進效果展示",
        font=("LINE Seed TW", 16, "bold"),
        fill="#333333"
    )
    
    # 繪製說明
    info_text = [
        "✓ 節點大小根據連接數量調整",
        "✓ 多條路線使用獨立通道，不重疊",
        "✓ 只在交叉點交叉",
        "✓ 使用 LINE Seed TW 字體"
    ]
    for i, text in enumerate(info_text):
        canvas.create_text(
            120, 500 + i * 20,
            text=text,
            font=("LINE Seed TW", 9),
            fill="#666666",
            anchor="w"
        )
    
    # 繪製連接線（先畫，讓節點在上層）
    for from_label, to_label, offset in test_connections:
        from_node = test_nodes[from_label]
        to_node = test_nodes[to_label]
        
        # 計算起點和終點
        start_x = from_node['x']
        start_y = from_node['y'] + from_node['radius']
        end_x = to_node['x']
        end_y = to_node['y'] - to_node['radius']
        
        # 簡化的路徑計算（三段式）
        channel_x = start_x + offset
        mid_y = (start_y + end_y) / 2
        
        if offset == 0:
            points = [start_x, start_y, start_x, mid_y, end_x, mid_y, end_x, end_y]
        else:
            points = [
                start_x, start_y,
                channel_x, start_y,
                channel_x, start_y + 30,
                channel_x, mid_y,
                end_x, mid_y,
                end_x, end_y
            ]
        
        # 繪製線路
        color = "#00d084"  # 綠色
        canvas.create_line(
            *points,
            fill=color,
            width=4,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=False
        )
    
    # 繪製節點
    for label, node in test_nodes.items():
        x, y = node['x'], node['y']
        radius = node['radius']
        connections = node['connections']
        
        # 根據連接數設置顏色
        if connections <= 2:
            fill_color = "#0077be"  # 藍色（少連接）
        elif connections <= 4:
            fill_color = "#f77f00"  # 橙色（中等連接）
        else:
            fill_color = "#e63946"  # 紅色（多連接）
        
        # 繪製圓形
        canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline="#ffffff",
            width=4
        )
        
        # 繪製標籤
        label_text = label.replace('#', '')
        
        # 根據半徑調整字體大小
        if radius < 36:
            font_size = 10
        elif radius < 46:
            font_size = 12
        else:
            font_size = 14
        
        canvas.create_text(
            x, y,
            text=label_text,
            fill="#ffffff",
            font=("LINE Seed TW", font_size, "bold")
        )
        
        # 在節點下方顯示連接數
        canvas.create_text(
            x, y + radius + 15,
            text=f"{connections}個連接",
            fill="#666666",
            font=("LINE Seed TW", 8)
        )
    
    # 繪製圖例
    legend_x = 650
    legend_y = 500
    
    canvas.create_text(
        legend_x, legend_y,
        text="節點大小圖例：",
        font=("LINE Seed TW", 10, "bold"),
        fill="#333333",
        anchor="w"
    )
    
    sizes = [
        ("小節點", 28, "#0077be", "1-2個連接"),
        ("中節點", 37, "#f77f00", "3-4個連接"),
        ("大節點", 49, "#e63946", "5+個連接")
    ]
    
    for i, (label, radius, color, desc) in enumerate(sizes):
        y = legend_y + 25 + i * 30
        
        # 繪製示例圓
        canvas.create_oval(
            legend_x - radius, y - radius,
            legend_x + radius, y + radius,
            fill=color,
            outline="#ffffff",
            width=2
        )
        
        # 繪製說明文字
        canvas.create_text(
            legend_x + 60, y,
            text=f"{label} ({desc})",
            font=("LINE Seed TW", 8),
            fill="#666666",
            anchor="w"
        )
    
    root.mainloop()

if __name__ == "__main__":
    print("🎨 啟動圖形模式改進測試...")
    print()
    print("改進內容：")
    print("1. 節點大小根據連接數量動態調整")
    print("   - 基礎半徑: 25px")
    print("   - 每個連接增加: 3px")
    print("   - 最大半徑: 55px (10個連接)")
    print()
    print("2. 路線使用獨立通道，避免重疊")
    print("   - 通道間距: 35px")
    print("   - 每條線路有自己的垂直通道")
    print("   - 只在交叉點交叉，不會重疊")
    print()
    print("3. 字體大小根據節點大小調整")
    print("   - 小節點(R<36): 10號字")
    print("   - 中節點(36≤R<46): 12號字")
    print("   - 大節點(R≥46): 14號字")
    print()
    
    try:
        draw_test()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
