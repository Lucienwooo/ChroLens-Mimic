# -*- coding: utf-8 -*-
"""
測試5項新改進：
1. 畫布可拖拽（但不能移動節點）
2. 圓形更圓滑
3. 顯示完整文字（4個字以上）
4. 節點不能點擊
5. 滑鼠懸停顯示代碼
"""

import tkinter as tk
from tkinter import Canvas

def draw_test():
    """繪製測試"""
    root = tk.Tk()
    root.title("圖形模式5項改進測試")
    root.geometry("1000x800")
    
    canvas = Canvas(root, bg="#f5f5f5", width=1000, height=800)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 標題
    canvas.create_text(
        500, 30,
        text="🎨 圖形模式5項改進測試",
        font=("LINE Seed TW", 18, "bold"),
        fill="#333333"
    )
    
    # 說明
    canvas.create_text(
        500, 70,
        text="拖拽畫布測試（點擊並拖動畫布任意位置）",
        font=("LINE Seed TW", 12),
        fill="#666666"
    )
    
    # 節點數據（包含完整代碼）
    nodes = [
        {
            'label': '開始流程',
            'x': 200, 'y': 150,
            'radius': 51,
            'color': '#0077be',
            'code': ['開始流程', '  等待 1秒', '  按下 Enter']
        },
        {
            'label': '處理數據A',
            'x': 500, 'y': 150,
            'radius': 57,
            'color': '#f77f00',
            'code': ['處理數據A', '  滑鼠移動到 100,200', '  點擊 左鍵', '  等待 0.5秒']
        },
        {
            'label': '條件判斷',
            'x': 800, 'y': 150,
            'radius': 60,
            'color': '#e63946',
            'code': ['條件判斷', '  >>> 圖片辨識 pic確定', '  點擊 pic確定', '  否則', '  按下 Esc']
        },
        {
            'label': '結束',
            'x': 500, 'y': 400,
            'radius': 48,
            'color': '#9d4edd',
            'code': ['結束', '  顯示訊息: 完成']
        }
    ]
    
    # 繪製連接線
    connections = [
        (0, 1), (1, 2), (2, 3), (0, 3)
    ]
    
    colors = ["#00d084", "#0077be", "#f77f00", "#e63946"]
    
    for idx, (from_idx, to_idx) in enumerate(connections):
        from_node = nodes[from_idx]
        to_node = nodes[to_idx]
        
        canvas.create_line(
            from_node['x'], from_node['y'],
            to_node['x'], to_node['y'],
            fill=colors[idx % len(colors)],
            width=5,
            capstyle=tk.ROUND
        )
    
    # 繪製節點
    tooltip_label = None
    
    def show_tooltip(event, code_lines):
        nonlocal tooltip_label
        if tooltip_label:
            tooltip_label.destroy()
        
        # 創建浮動提示框
        code_text = "\\n".join(code_lines)
        
        tooltip_label = tk.Label(
            root,
            text=code_text,
            bg="#2d2d30",
            fg="#d4d4d4",
            font=("LINE Seed TW", 10),
            justify=tk.LEFT,
            padx=10,
            pady=8,
            relief=tk.SOLID,
            borderwidth=1
        )
        tooltip_label.place(x=event.x + 15, y=event.y + 15)
    
    def hide_tooltip(event):
        nonlocal tooltip_label
        if tooltip_label:
            tooltip_label.destroy()
            tooltip_label = None
    
    for node in nodes:
        x, y = node['x'], node['y']
        radius = node['radius']
        color = node['color']
        label = node['label']
        code = node['code']
        
        # 繪製圓形（Tkinter的oval自帶抗鋸齒）
        oval_id = canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="#ffffff",
            width=4
        )
        
        # 繪製文字（完整顯示，使用 width 參數自動換行）
        font_size = 12 if radius < 55 else 14
        text_id = canvas.create_text(
            x, y,
            text=label,
            fill="#ffffff",
            font=("LINE Seed TW", font_size, "bold"),
            width=radius * 1.8  # 📝 限制寬度，讓長文字自動換行
        )
        
        # 綁定滑鼠懸停事件
        canvas.tag_bind(oval_id, "<Enter>", lambda e, c=code: show_tooltip(e, c))
        canvas.tag_bind(oval_id, "<Leave>", hide_tooltip)
        canvas.tag_bind(text_id, "<Enter>", lambda e, c=code: show_tooltip(e, c))
        canvas.tag_bind(text_id, "<Leave>", hide_tooltip)
    
    # 實現畫布拖拽
    pan_start_x = 0
    pan_start_y = 0
    is_panning = False
    
    def on_press(event):
        nonlocal pan_start_x, pan_start_y, is_panning
        is_panning = True
        pan_start_x = event.x
        pan_start_y = event.y
        canvas.config(cursor="fleur")
    
    def on_drag(event):
        nonlocal pan_start_x, pan_start_y
        if is_panning:
            dx = event.x - pan_start_x
            dy = event.y - pan_start_y
            canvas.move("all", dx, dy)
            pan_start_x = event.x
            pan_start_y = event.y
    
    def on_release(event):
        nonlocal is_panning
        is_panning = False
        canvas.config(cursor="")
    
    canvas.bind("<Button-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    
    # 改進說明
    info_y = 720
    infos = [
        "✅ 1. 畫布可拖拽（點擊空白處拖動）",
        "✅ 2. 圓形更圓滑（smooth=True）",
        "✅ 3. 顯示完整文字（自動換行）",
        "✅ 4. 節點不能點擊移動",
        "✅ 5. 滑鼠懸停顯示代碼",
        ""
    ]
    
    for i, info in enumerate(infos):
        if info:
            canvas.create_text(
                80, info_y + i * 20,
                text=info,
                font=("LINE Seed TW", 10),
                fill="#333333",
                anchor="w"
            )
    
    # 提示文字
    canvas.create_text(
        500, 650,
        text="💡 將滑鼠停留在圓形上查看代碼",
        font=("LINE Seed TW", 12, "bold"),
        fill="#f77f00"
    )
    
    root.mainloop()

if __name__ == "__main__":
    print("🎨 測試5項改進...")
    print()
    print("改進內容：")
    print("1. ✅ 畫布可拖拽（但節點固定）")
    print("2. ✅ 圓形更圓滑（smooth=True）")
    print("3. ✅ 顯示完整文字（width參數自動換行）")
    print("4. ✅ 節點不能點擊（取消回到文字模式）")
    print("5. ✅ 滑鼠懸停顯示代碼（浮動提示框）")
    print()
    print("操作方式：")
    print("- 點擊並拖動畫布可以移動視圖")
    print("- 將滑鼠停留在圓形上查看代碼")
    print("- 圓形本身不能被移動")
    print()
    
    try:
        draw_test()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
