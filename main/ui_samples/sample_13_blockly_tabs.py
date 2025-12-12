# -*- coding: utf-8 -*-
"""
UI Sample 13: Blockly 分類標籤風格
特色：使用標籤頁分類積木工具箱
"""

import tkinter as tk

def create_sample_13():
    window = tk.Toplevel()
    window.title("Sample 13 - Blockly 標籤分類")
    window.geometry("1600x900")
    window.configure(bg="#f0f0f0")
    
    # 頂部
    toolbar = tk.Frame(window, bg="#5c6bc0", height=55)
    toolbar.pack(fill="x")
    toolbar.pack_propagate(False)
    
    tk.Label(toolbar, text="🎯 ChroLens 積木編輯器", bg="#5c6bc0", fg="white",
            font=("Microsoft JhengHei", 15, "bold")).pack(side="left", padx=20)
    
    # 主區域
    main = tk.Frame(window, bg="#f0f0f0")
    main.pack(fill="both", expand=True, padx=5, pady=5)
    
    # 左側標籤工具箱
    toolbox_frame = tk.Frame(main, bg="white", width=260, relief="solid", bd=1)
    toolbox_frame.pack(side="left", fill="y", padx=(0, 5))
    toolbox_frame.pack_propagate(False)
    
    # 標籤列
    tabs = tk.Frame(toolbox_frame, bg="white")
    tabs.pack(fill="x")
    
    tab_names = ["操作", "邏輯", "變數", "事件"]
    for i, tab in enumerate(tab_names):
        bg = "#5c6bc0" if i == 0 else "#e0e0e0"
        fg = "white" if i == 0 else "#666666"
        tk.Label(tabs, text=tab, bg=bg, fg=fg,
                font=("Microsoft JhengHei", 9, "bold"),
                padx=15, pady=10).pack(side="left")
    
    # 積木列表
    blocks_area = tk.Frame(toolbox_frame, bg="white")
    blocks_area.pack(fill="both", expand=True, padx=10, pady=10)
    
    operation_blocks = [
        ("移動滑鼠", "#42a5f5"),
        ("點擊滑鼠", "#42a5f5"),
        ("按下鍵盤", "#66bb6a"),
        ("輸入文字", "#66bb6a"),
        ("等待時間", "#ffa726"),
        ("截圖", "#ab47bc"),
    ]
    
    for block_name, color in operation_blocks:
        block = tk.Frame(blocks_area, bg=color, cursor="hand2", relief="raised", bd=2)
        block.pack(fill="x", pady=5)
        tk.Label(block, text=block_name, bg=color, fg="white",
                font=("Microsoft JhengHei", 10)).pack(pady=10)
    
    # 中央畫布
    canvas_frame = tk.Frame(main, bg="#fafafa")
    canvas_frame.pack(side="left", fill="both", expand=True, padx=5)
    
    canvas = tk.Canvas(canvas_frame, bg="#fafafa", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    
    # 網格
    for i in range(0, 1200, 30):
        canvas.create_line(i, 0, i, 800, fill="#e8e8e8")
    for j in range(0, 800, 30):
        canvas.create_line(0, j, 1200, j, fill="#e8e8e8")
    
    # 積木流程
    y = 100
    for text, color in [("開始", "#5c6bc0"), ("移動(100,200)", "#42a5f5"),
                        ("點擊", "#42a5f5"), ("等待2秒", "#ffa726")]:
        canvas.create_rectangle(200, y, 400, y+50, fill=color, outline="white", width=3)
        canvas.create_text(300, y+25, text=text, fill="white",
                          font=("Microsoft JhengHei", 11, "bold"))
        y += 70
    
    # 右側屬性
    props = tk.Frame(main, bg="white", width=280, relief="solid", bd=1)
    props.pack(side="left", fill="y")
    props.pack_propagate(False)
    
    tk.Label(props, text="⚙️ 屬性設定", bg="white", fg="#5c6bc0",
            font=("Microsoft JhengHei", 12, "bold")).pack(pady=15)
    
    content = tk.Frame(props, bg="white")
    content.pack(fill="x", padx=15, pady=10)
    
    for label in ["操作類型:", "X 座標:", "Y 座標:", "延遲(秒):"]:
        tk.Label(content, text=label, bg="white", fg="#666",
                font=("Microsoft JhengHei", 9)).pack(anchor="w", pady=5)
        tk.Entry(content, bg="#f5f5f5", bd=1, relief="solid").pack(fill="x", pady=(0,10))

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    create_sample_13()
    root.mainloop()
