# -*- coding: utf-8 -*-
"""
UI Sample 0: Figma 風格基礎範本
參考：Figma 設計工具
特色：
- 可自由移動的浮動工具箱
- 中央畫布式編輯區
- 屬性面板隨選項變化
- 現代設計工具風格
"""

import tkinter as tk
from tkinter import scrolledtext

def create_sample_0():
    window = tk.Toplevel()
    window.title("Sample 0 - Figma 風格基礎範本")
    window.geometry("1500x900")
    window.configure(bg="#1e1e1e")
    
    # 頂部主工具列
    top_toolbar = tk.Frame(window, bg="#2c2c2c", height=48)
    top_toolbar.pack(fill="x")
    top_toolbar.pack_propagate(False)
    
    # Logo
    tk.Label(top_toolbar, text="◆ ChroLens", bg="#2c2c2c", fg="white",
            font=("Microsoft JhengHei", 11, "bold")).pack(side="left", padx=15)
    
    # 檔案名稱
    tk.Label(top_toolbar, text="script_1.json", bg="#2c2c2c", fg="#b4b4b4",
            font=("Microsoft JhengHei", 10)).pack(side="left", padx=20)
    
    # 中央工具
    center_tools = tk.Frame(top_toolbar, bg="#2c2c2c")
    center_tools.pack(expand=True)
    
    tools = ["🔲", "⭕", "✏️", "↔️", "✋", "💬"]
    for tool in tools:
        btn = tk.Button(center_tools, text=tool, bg="#3c3c3c", fg="white",
                       relief="flat", font=("Arial", 12), width=3, height=1)
        btn.pack(side="left", padx=2)
    
    # 右側控制
    right_controls = tk.Frame(top_toolbar, bg="#2c2c2c")
    right_controls.pack(side="right", padx=15)
    
    tk.Button(right_controls, text="分享", bg="#0d99ff", fg="white",
             relief="flat", font=("Microsoft JhengHei", 9, "bold"),
             padx=15, pady=5).pack(side="left", padx=5)
    tk.Button(right_controls, text="▶", bg="#00d084", fg="white",
             relief="flat", font=("Arial", 14, "bold"),
             width=3).pack(side="left", padx=5)
    
    # 主畫布區域
    canvas_area = tk.Frame(window, bg="#1e1e1e")
    canvas_area.pack(fill="both", expand=True)
    
    # 左側浮動工具面板
    create_floating_panel(canvas_area, "圖層", 20, 60, 220, 300, [
        "📄 script_1",
        "  └ 鍵盤操作群組",
        "  └ 滑鼠操作群組",
        "  └ 圖片辨識群組",
        "📄 script_2"
    ])
    
    # 中央編輯畫布
    canvas = tk.Canvas(canvas_area, bg="#252526", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=250, pady=20)
    
    # 畫布內容 - 視覺化腳本流程
    create_canvas_content(canvas)
    
    # 右側屬性面板
    create_floating_panel(canvas_area, "屬性", 1260, 60, 220, 400, [])
    
    # 自訂屬性內容
    props_content = tk.Frame(canvas_area, bg="#2c2c2c")
    props_content.place(x=1260, y=100, width=220, height=350)
    
    tk.Label(props_content, text="指令類型", bg="#2c2c2c", fg="#888888",
            font=("Microsoft JhengHei", 8)).pack(anchor="w", padx=10, pady=(5, 2))
    tk.Label(props_content, text="鍵盤操作", bg="#2c2c2c", fg="white",
            font=("Microsoft JhengHei", 10, "bold")).pack(anchor="w", padx=10, pady=(0, 10))
    
    tk.Label(props_content, text="按鍵", bg="#2c2c2c", fg="#888888",
            font=("Microsoft JhengHei", 8)).pack(anchor="w", padx=10, pady=(5, 2))
    tk.Entry(props_content, bg="#3c3c3c", fg="white", bd=0,
            font=("Microsoft JhengHei", 9)).pack(fill="x", padx=10, pady=(0, 10), ipady=5)
    
    tk.Label(props_content, text="延遲 (ms)", bg="#2c2c2c", fg="#888888",
            font=("Microsoft JhengHei", 8)).pack(anchor="w", padx=10, pady=(5, 2))
    tk.Entry(props_content, bg="#3c3c3c", fg="white", bd=0,
            font=("Microsoft JhengHei", 9)).pack(fill="x", padx=10, pady=(0, 10), ipady=5)
    
    tk.Button(props_content, text="應用變更", bg="#0d99ff", fg="white",
             relief="flat", font=("Microsoft JhengHei", 9)).pack(fill="x", padx=10, pady=10)
    
    # 底部浮動工具列
    bottom_toolbar = tk.Frame(window, bg="#2c2c2c", height=40)
    bottom_toolbar.pack(fill="x", side="bottom")
    bottom_toolbar.pack_propagate(False)
    
    # 縮放控制
    zoom_frame = tk.Frame(bottom_toolbar, bg="#2c2c2c")
    zoom_frame.pack(side="left", padx=15)
    
    tk.Button(zoom_frame, text="-", bg="#3c3c3c", fg="white",
             relief="flat", width=2).pack(side="left", padx=2)
    tk.Label(zoom_frame, text="100%", bg="#2c2c2c", fg="white",
            font=("Microsoft JhengHei", 9)).pack(side="left", padx=10)
    tk.Button(zoom_frame, text="+", bg="#3c3c3c", fg="white",
             relief="flat", width=2).pack(side="left", padx=2)
    
    # 狀態
    tk.Label(bottom_toolbar, text="✓ 已儲存", bg="#2c2c2c", fg="#00d084",
            font=("Microsoft JhengHei", 9)).pack(side="right", padx=15)

def create_floating_panel(parent, title, x, y, width, height, items):
    """創建浮動面板"""
    panel = tk.Frame(parent, bg="#2c2c2c", relief="solid", bd=1)
    panel.place(x=x, y=y, width=width, height=height)
    
    # 標題列
    header = tk.Frame(panel, bg="#2c2c2c", height=35)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    tk.Label(header, text=title, bg="#2c2c2c", fg="white",
            font=("Microsoft JhengHei", 9, "bold")).pack(side="left", padx=10)
    tk.Button(header, text="−", bg="#2c2c2c", fg="#888888",
             relief="flat", font=("Arial", 12)).pack(side="right", padx=5)
    
    # 內容
    content = tk.Frame(panel, bg="#252526")
    content.pack(fill="both", expand=True, padx=1, pady=1)
    
    for item in items:
        tk.Label(content, text=item, bg="#252526", fg="#cccccc",
                font=("Microsoft JhengHei", 9), anchor="w").pack(fill="x", padx=5, pady=2)

def create_canvas_content(canvas):
    """創建畫布內容 - 視覺化流程"""
    # 創建節點
    nodes = [
        (200, 100, "開始", "#4caf50"),
        (200, 200, "按鍵 Ctrl+C", "#2196f3"),
        (200, 300, "移動至(100,200)", "#ff9800"),
        (200, 400, "圖片辨識", "#9c27b0"),
        (200, 500, "結束", "#f44336")
    ]
    
    # 繪製連接線
    for i in range(len(nodes) - 1):
        x1, y1 = nodes[i][0] + 75, nodes[i][1] + 40
        x2, y2 = nodes[i+1][0] + 75, nodes[i+1][1]
        canvas.create_line(x1, y1, x2, y2, fill="#666666", width=2, arrow=tk.LAST)
    
    # 繪製節點
    for x, y, text, color in nodes:
        canvas.create_rectangle(x, y, x+150, y+40, fill=color, outline="white", width=2)
        canvas.create_text(x+75, y+20, text=text, fill="white",
                          font=("Microsoft JhengHei", 10, "bold"))

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    create_sample_0()
    root.mainloop()
