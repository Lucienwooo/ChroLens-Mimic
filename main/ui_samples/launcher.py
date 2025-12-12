# -*- coding: utf-8 -*-
"""
UI Samples 啟動器
提供 11 種完全不同佈局結構的 UI 樣本
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def launch_sample(sample_num):
    """啟動指定的 sample"""
    try:
        if sample_num == 0:
            from sample_0_figma_base import create_sample_0
            create_sample_0()
        elif sample_num == 1:
            from sample_1_blender_multiview import create_sample_1
            create_sample_1()
        elif sample_num == 2:
            from sample_2_unity_dockable import create_sample_2
            create_sample_2()
        elif sample_num == 3:
            from sample_3_photoshop_sidebar import create_sample_3
            create_sample_3()
        elif sample_num == 4:
            from sample_4_premiere_timeline import create_sample_4
            create_sample_4()
        elif sample_num == 5:
            from sample_5_miro_infinite import create_sample_5
            create_sample_5()
        elif sample_num == 6:
            from sample_6_vscode_editor import create_sample_6
            create_sample_6()
        elif sample_num == 7:
            from sample_7_notion_database import create_sample_7
            create_sample_7()
        elif sample_num == 8:
            from sample_8_android_studio import create_sample_8
            create_sample_8()
        elif sample_num == 9:
            from sample_9_xmind_mindmap import create_sample_9
            create_sample_9()
        elif sample_num == 10:
            from sample_10_substance_nodes import create_sample_10
            create_sample_10()
        elif sample_num == 11:
            from sample_11_blockly_classic import create_sample_11
            create_sample_11()
        elif sample_num == 12:
            from sample_12_blockly_dark import create_sample_12
            create_sample_12()
        elif sample_num == 13:
            from sample_13_blockly_tabs import create_sample_13
            create_sample_13()
        elif sample_num == 14:
            from sample_14_blockly_horizontal import create_sample_14
            create_sample_14()
        elif sample_num == 15:
            from sample_15_blockly_compact import create_sample_15
            create_sample_15()
        elif sample_num == 16:
            from sample_16_chrolens_full import create_sample_16
            create_sample_16()
        elif sample_num == 17:
            from sample_17_chrolens_tabs import create_sample_17
            create_sample_17()
        elif sample_num == 18:
            from sample_18_chrolens_timeline import create_sample_18
            create_sample_18()
        elif sample_num == 19:
            from sample_19_chrolens_dual import create_sample_19
            create_sample_19()
        elif sample_num == 20:
            from sample_20_chrolens_dashboard import create_sample_20
            create_sample_20()
    except Exception as e:
        messagebox.showerror("錯誤", f"無法啟動 Sample {sample_num}:\n{e}")

def main():
    root = tk.Tk()
    root.title("ChroLens UI 佈局展示")
    root.geometry("1000x800")
    root.configure(bg="#1e1e1e")
    
    # 標題
    title_label = tk.Label(
        root,
        text="ChroLens 多風格 UI 佈局庫",
        font=("Microsoft JhengHei", 20, "bold"),
        bg="#1e1e1e",
        fg="#0d99ff"
    )
    title_label.pack(pady=30)
    
    subtitle = tk.Label(
        root,
        text="21 種完全不同的佈局結構：11種參考軟體 + 5種Blockly視覺程式 + 5種完整功能版本",
        font=("Microsoft JhengHei", 10),
        bg="#1e1e1e",
        fg="#b4b4b4"
    )
    subtitle.pack(pady=(0, 20))
    
    # 創建Canvas和滾動條
    canvas = tk.Canvas(root, bg="#1e1e1e", highlightthickness=0)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True, padx=30)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # 樣本容器
    samples_frame = tk.Frame(canvas, bg="#1e1e1e")
    canvas.create_window((0, 0), window=samples_frame, anchor="nw", width=920)
    
    # 樣本列表
    samples = [
        {
            "num": 0,
            "name": "Figma 浮動面板",
            "desc": "可拖曳浮動面板設計，彈性佈局，現代設計工具風格",
            "color": "#0d99ff"
        },
        {
            "num": 1,
            "name": "Blender 多視窗",
            "desc": "四分割獨立視窗，3D 建模軟體風格，多視角同步編輯",
            "color": "#ff6600"
        },
        {
            "num": 2,
            "name": "Unity 可停靠面板",
            "desc": "遊戲引擎風格，可停靠面板系統，階層式場景管理",
            "color": "#0078d7"
        },
        {
            "num": 3,
            "name": "Photoshop 側邊工具列",
            "desc": "垂直工具箱設計，圖層式屬性面板，專業圖像編輯風格",
            "color": "#31a8ff"
        },
        {
            "num": 4,
            "name": "Premiere 時間軸",
            "desc": "上下分割佈局，時間軸編輯器，影片剪輯軟體風格",
            "color": "#9999ff"
        },
        {
            "num": 5,
            "name": "Miro 無限畫布",
            "desc": "無限滾動白板，浮動圓形工具盤，協作看板風格",
            "color": "#4262ff"
        },
        {
            "num": 6,
            "name": "VS Code 編輯器",
            "desc": "側邊活動欄，檔案樹狀結構，底部終端面板",
            "color": "#4fc1ff"
        },
        {
            "num": 7,
            "name": "Notion 資料庫",
            "desc": "看板卡片式佈局，側邊導航欄，筆記軟體風格",
            "color": "#000000"
        },
        {
            "num": 8,
            "name": "Android Studio",
            "desc": "三欄式佈局，組件樹視圖，可視化設計預覽",
            "color": "#3ddc84"
        },
        {
            "num": 9,
            "name": "XMind 心智圖",
            "desc": "中心放射狀佈局，樹狀節點結構，思維導圖風格",
            "color": "#8855ee"
        },
        {
            "num": 10,
            "name": "Substance 節點編輯器",
            "desc": "節點式工作流，網格背景畫布，材質編輯器風格",
            "color": "#98c379"
        },
        {
            "num": 11,
            "name": "Blockly 經典風格",
            "desc": "Google Blockly 視覺程式設計，左側工具箱分類，拼圖式程式積木",
            "color": "#4285f4"
        },
        {
            "num": 12,
            "name": "Blockly 深色主題",
            "desc": "暗黑主題 Blockly，程式積木連接節點，適合夜間使用",
            "color": "#1e1e1e"
        },
        {
            "num": 13,
            "name": "Blockly 分頁工具箱",
            "desc": "分頁式積木組織，紫色系配色，更清晰的分類管理",
            "color": "#5c6bc0"
        },
        {
            "num": 14,
            "name": "Blockly 水平流程",
            "desc": "橫向工作流設計，上方分類欄，強調左右流程連接",
            "color": "#17a2b8"
        },
        {
            "num": 15,
            "name": "Blockly 緊湊設計",
            "desc": "極簡空間效率，窄面板設計，小型積木與網格",
            "color": "#28a745"
        },
        {
            "num": 16,
            "name": "ChroLens 經典完整版",
            "desc": "完整錄製/播放功能，浮動面板設計，參數設定齊全",
            "color": "#0d99ff"
        },
        {
            "num": 17,
            "name": "ChroLens 分頁介面",
            "desc": "腳本編輯器、參數、事件、進階選項分頁，列表管理",
            "color": "#1976d2"
        },
        {
            "num": 18,
            "name": "ChroLens 時間軸編輯器",
            "desc": "視覺化事件時間軸，軌道式編輯，播放指針即時定位",
            "color": "#00d4ff"
        },
        {
            "num": 19,
            "name": "ChroLens 雙欄並排",
            "desc": "左右對稱佈局，左側腳本編輯器，右側參數與事件列表",
            "color": "#4caf50"
        },
        {
            "num": 20,
            "name": "ChroLens 儀表板風格",
            "desc": "卡片式儀表板，控制/狀態/腳本/參數模組化設計",
            "color": "#1976d2"
        }
    ]
    
    for sample in samples:
        # 每個樣本的容器
        sample_frame = tk.Frame(samples_frame, bg="#2c2c2c", relief="solid", bd=1)
        sample_frame.pack(fill="x", pady=8)
        
        # 內容區域
        content_frame = tk.Frame(sample_frame, bg="#2c2c2c")
        content_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # 左側：色塊指示器
        color_indicator = tk.Frame(content_frame, bg=sample['color'], width=5)
        color_indicator.pack(side="left", fill="y", padx=(0, 15))
        
        # 中間：資訊
        info_frame = tk.Frame(content_frame, bg="#2c2c2c")
        info_frame.pack(side="left", fill="both", expand=True)
        
        name_label = tk.Label(
            info_frame,
            text=f"Sample {sample['num']} - {sample['name']}",
            font=("Microsoft JhengHei", 12, "bold"),
            bg="#2c2c2c",
            fg=sample['color'],
            anchor="w"
        )
        name_label.pack(fill="x")
        
        desc_label = tk.Label(
            info_frame,
            text=sample['desc'],
            font=("Microsoft JhengHei", 9),
            bg="#2c2c2c",
            fg="#b4b4b4",
            anchor="w",
            wraplength=600,
            justify="left"
        )
        desc_label.pack(fill="x", pady=(5, 0))
        
        # 右側：按鈕
        btn = tk.Button(
            content_frame,
            text="▶ 預覽",
            font=("Microsoft JhengHei", 10, "bold"),
            bg=sample['color'],
            fg="#000000" if sample['num'] in [2, 4, 9, 10] else "#ffffff",
            width=12,
            height=2,
            relief="flat",
            cursor="hand2",
            command=lambda n=sample['num']: launch_sample(n)
        )
        btn.pack(side="right", padx=10)
    
    # 更新滾動區域
    samples_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    
    # 底部資訊
    bottom_frame = tk.Frame(root, bg="#1e1e1e")
    bottom_frame.pack(fill="x", pady=15, side="bottom")
    
    info_label = tk.Label(
        bottom_frame,
        text="💡 Samples 0-10: 參考業界軟體佈局 | 11-15: Blockly視覺程式 | 16-20: 完整功能版本",
        font=("Microsoft JhengHei", 9),
        bg="#1e1e1e",
        fg="#00d084"
    )
    info_label.pack()
    
    # 全部預覽按鈕
    preview_all_btn = tk.Button(
        bottom_frame,
        text="🎨 全部預覽 (21個視窗)",
        font=("Microsoft JhengHei", 11, "bold"),
        bg="#0d99ff",
        fg="#ffffff",
        width=30,
        height=2,
        relief="flat",
        cursor="hand2",
        command=lambda: [launch_sample(i) for i in range(21)]
    )
    preview_all_btn.pack(pady=(10, 0))
    
    root.mainloop()

if __name__ == "__main__":
    main()
