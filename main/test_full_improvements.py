# -*- coding: utf-8 -*-
"""
測試全面改進的圖形模式
1. 完全並行路線（無重疊）
2. 多彩顏色系統
3. 支持斜線
4. 智能連接點
5. 禁用拖拽
6. 更大的圓形
"""

import tkinter as tk
from tkinter import Canvas
import math

def calculate_optimal_points(x1, y1, r1, x2, y2, r2):
    """計算最佳連接點"""
    dx = x2 - x1
    dy = y2 - y1
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < 0.001:
        return (x1, y1 + r1, x2, y2 - r2)
    
    nx = dx / distance
    ny = dy / distance
    
    start_x = x1 + nx * r1
    start_y = y1 + ny * r1
    end_x = x2 - nx * r2
    end_y = y2 - ny * r2
    
    return (start_x, start_y, end_x, end_y)

def calculate_path_with_diagonal(x1, y1, x2, y2, offset):
    """計算帶斜線的路徑"""
    dx = x2 - x1
    dy = y2 - y1
    abs_dx = abs(dx)
    abs_dy = abs(dy)
    
    if offset == 0:
        if abs_dx < 20:
            return [x1, y1, x2, y2]  # 垂直
        elif abs_dy < 20:
            return [x1, y1, x2, y2]  # 水平
        elif abs(abs_dx - abs_dy) < 30:
            return [x1, y1, x2, y2]  # 斜線！
        else:
            mid_y = (y1 + y2) / 2
            return [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
    else:
        channel_x = x1 + offset
        
        if abs_dy < 20:
            offset_y = offset * 0.5
            mid_y = (y1 + y2) / 2 + offset_y
            return [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
        elif abs_dx < 20:
            return [x1, y1, channel_x, y1, channel_x, y2, x2, y2]
        elif abs(abs_dx - abs_dy) < 50:
            # 平行斜線！
            angle = abs_dy / abs_dx if abs_dx > 0 else 1
            perp_offset_x = offset / (1 + angle)
            perp_offset_y = offset * angle / (1 + angle)
            
            start_offset_x = perp_offset_x if dy * dx > 0 else -perp_offset_x
            start_offset_y = -perp_offset_y
            
            return [
                x1, y1,
                x1 + start_offset_x, y1 + start_offset_y,
                x2 + start_offset_x, y2 + start_offset_y,
                x2, y2
            ]
        else:
            first_segment = min(abs_dy * 0.25, 40)
            mid_y = (y1 + y2) / 2
            
            return [
                x1, y1,
                channel_x, y1,
                channel_x, y1 + first_segment,
                channel_x, mid_y,
                channel_x, y2 - first_segment,
                channel_x, y2,
                x2, y2
            ]

def draw_test():
    """繪製測試"""
    root = tk.Tk()
    root.title("全面改進測試")
    root.geometry("1000x800")
    
    canvas = Canvas(root, bg="#f5f5f5", width=1000, height=800)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 標題
    canvas.create_text(
        500, 30,
        text="🎨 ChroLens 圖形模式全面改進",
        font=("LINE Seed TW", 18, "bold"),
        fill="#333333"
    )
    
    # 多彩顏色
    colors = [
        "#00d084", "#0077be", "#f77f00", "#e63946", "#9d4edd",
        "#06ffa5", "#ffbe0b", "#fb5607", "#8338ec", "#3a86ff"
    ]
    
    # 節點（更大的圓形：基礎45px）
    nodes = {
        'A': {'x': 150, 'y': 150, 'conn': 2, 'radius': 51},  # 45+6
        'B': {'x': 450, 'y': 150, 'conn': 3, 'radius': 54},  # 45+9
        'C': {'x': 750, 'y': 150, 'conn': 1, 'radius': 48},  # 45+3
        'D': {'x': 150, 'y': 400, 'conn': 2, 'radius': 51},
        'E': {'x': 450, 'y': 400, 'conn': 5, 'radius': 60},  # 45+15
        'F': {'x': 750, 'y': 400, 'conn': 2, 'radius': 51},
        'G': {'x': 450, 'y': 650, 'conn': 3, 'radius': 54},
    }
    
    # 連接（帶通道偏移）
    connections = [
        ('A', 'B', 0),
        ('A', 'D', 0),
        ('B', 'E', -50),
        ('B', 'E', 0),
        ('B', 'E', 50),
        ('C', 'F', 0),
        ('D', 'E', 0),
        ('E', 'G', -50),
        ('E', 'G', 0),
        ('E', 'G', 50),
        ('F', 'G', 0),
    ]
    
    # 繪製連接線
    for idx, (from_label, to_label, offset) in enumerate(connections):
        from_node = nodes[from_label]
        to_node = nodes[to_label]
        
        # 智能計算連接點
        start_x, start_y, end_x, end_y = calculate_optimal_points(
            from_node['x'], from_node['y'], from_node['radius'],
            to_node['x'], to_node['y'], to_node['radius']
        )
        
        # 計算路徑
        points = calculate_path_with_diagonal(start_x, start_y, end_x, end_y, offset)
        
        # 多彩顏色
        color = colors[idx % len(colors)]
        
        # 繪製線路
        canvas.create_line(
            *points,
            fill=color,
            width=5,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=False
        )
        
        # 箭頭
        canvas.create_oval(
            end_x - 6, end_y - 6,
            end_x + 6, end_y + 6,
            fill=color, outline=color
        )
    
    # 繪製節點
    for label, node in nodes.items():
        x, y = node['x'], node['y']
        radius = node['radius']
        
        # 顏色根據連接數
        if node['conn'] <= 2:
            color = "#0077be"
        elif node['conn'] <= 4:
            color = "#f77f00"
        else:
            color = "#e63946"
        
        canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="#ffffff",
            width=4
        )
        
        # 文字
        font_size = 12 if radius < 55 else 14
        canvas.create_text(
            x, y,
            text=label,
            fill="#ffffff",
            font=("LINE Seed TW", font_size, "bold")
        )
    
    # 說明
    info_y = 720
    infos = [
        "✓ 完全並行路線（50px間距）",
        "✓ 10種多彩顏色循環",
        "✓ 支持45度斜線",
        "✓ 智能連接點（最短距離）",
        "✓ 禁用拖拽（只能看）",
        "✓ 更大圓形（基礎45px）"
    ]
    
    for i, info in enumerate(infos):
        x = 80 + (i % 3) * 320
        y = info_y + (i // 3) * 25
        canvas.create_text(
            x, y,
            text=info,
            font=("LINE Seed TW", 10),
            fill="#333333",
            anchor="w"
        )
    
    # 圖例
    legend_x = 850
    legend_y = 500
    
    canvas.create_text(
        legend_x, legend_y,
        text="節點大小：",
        font=("LINE Seed TW", 11, "bold"),
        fill="#333333",
        anchor="w"
    )
    
    sizes = [
        ("小", 48, "#0077be"),
        ("中", 54, "#f77f00"),
        ("大", 60, "#e63946")
    ]
    
    for i, (label, r, c) in enumerate(sizes):
        y = legend_y + 30 + i * 35
        
        canvas.create_oval(
            legend_x - r, y - r,
            legend_x + r, y + r,
            fill=c, outline="#ffffff", width=3
        )
        
        canvas.create_text(
            legend_x + 70, y,
            text=label,
            font=("LINE Seed TW", 10),
            fill="#666666",
            anchor="w"
        )
    
    root.mainloop()

if __name__ == "__main__":
    print("🎨 測試全面改進...")
    print()
    print("改進內容：")
    print("1. ✅ 完全並行路線（通道間距50px）")
    print("2. ✅ 10種多彩顏色循環使用")
    print("3. ✅ 支持45度斜線（更美觀）")
    print("4. ✅ 智能連接點（最短距離原則）")
    print("5. ✅ 禁用拖拽功能（只能查看）")
    print("6. ✅ 更大圓形（基礎45px，能容納4個中文字）")
    print()
    
    try:
        draw_test()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
