# -*- coding: utf-8 -*-
"""
ChroLens Blockly風格文字指令編輯器
基於 sample_13_blockly_tabs.py UI 設計
完整整合 text_script_editor.py 所有功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import json
import os
import sys
import re
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageGrab, ImageTk

# 路徑設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, PARENT_DIR)

# 字體路徑
LINE_SEED_FONT_PATH = os.path.join(PARENT_DIR, "TTF", "LINESeedTW_TTF_Rg.ttf")
try:
    import pyglet
    if os.path.exists(LINE_SEED_FONT_PATH):
        pyglet.font.add_file(LINE_SEED_FONT_PATH)
        LINE_SEED_FONT_LOADED = True
    else:
        LINE_SEED_FONT_LOADED = False
except:
    LINE_SEED_FONT_LOADED = False

# MSS 截圖支援
try:
    import mss
    import numpy as np
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

def font_tuple(size, weight=None, monospace=False):
    """回傳字體元組"""
    if LINE_SEED_FONT_LOADED:
        fam = "LINE Seed TW"
    else:
        fam = "Consolas" if monospace else "Microsoft JhengHei"
    if weight:
        return (fam, size, weight)
    return (fam, size)


class BlocklyScriptEditor:
    """Blockly風格的ChroLens腳本編輯器"""
    
    def __init__(self, script_path=None):
        self.root = tk.Tk()
        self.root.title("🎯 ChroLens Blockly 指令編輯器")
        self.root.geometry("1600x900")
        self.root.configure(bg="#f0f0f0")
        
        # 設定圖標
        try:
            icon_path = self._get_icon_path()
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.script_path = script_path
        self.default_key_duration = 50
        
        # 初始化設定
        self.original_settings = {
            "speed": "100",
            "repeat": "1",
            "repeat_time": "00:00:00",
            "repeat_interval": "00:00:00",
            "random_interval": False,
            "script_hotkey": "",
            "script_actions": [],
            "window_info": None
        }
        
        # 圖片與模組目錄
        self.images_dir = self._get_images_dir()
        self.modules_dir = self._get_modules_dir()
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.modules_dir, exist_ok=True)
        
        self._pic_counter = self._get_next_pic_number()
        self.trajectory_fold_state = {}
        
        self._create_ui()
        self._refresh_script_list()
        
        if self.script_path:
            script_name = os.path.splitext(os.path.basename(self.script_path))[0]
            self.script_var.set(script_name)
            self._load_script()
    
    def _get_icon_path(self):
        """取得圖示檔案路徑"""
        try:
            if getattr(sys, 'frozen', False):
                return os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                for path in ["umi_奶茶色.ico", "../pic/umi_奶茶色.ico", "../umi_奶茶色.ico"]:
                    if os.path.exists(path):
                        return path
        except:
            pass
        return "umi_奶茶色.ico"
    
    def _get_images_dir(self):
        """獲取圖片儲存目錄"""
        if self.script_path:
            script_dir = os.path.dirname(self.script_path)
            return os.path.join(script_dir, "images")
        return os.path.join(os.getcwd(), "scripts", "images")
    
    def _get_modules_dir(self):
        """獲取自訂模組目錄"""
        if self.script_path:
            script_dir = os.path.dirname(self.script_path)
            return os.path.join(script_dir, "modules")
        return os.path.join(os.getcwd(), "scripts", "modules")
    
    def _get_next_pic_number(self):
        """獲取下一個可用的圖片編號"""
        if not os.path.exists(self.images_dir):
            return 1
        
        max_num = 0
        try:
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            for filename in os.listdir(self.images_dir):
                ext = os.path.splitext(filename)[1].lower()
                if ext in image_extensions and filename.startswith("pic"):
                    try:
                        name_without_ext = os.path.splitext(filename)[0]
                        num_str = name_without_ext[3:]
                        if num_str.isdigit():
                            num = int(num_str)
                            max_num = max(max_num, num)
                    except:
                        continue
        except:
            pass
        
        return max_num + 1
    
    def _create_ui(self):
        """創建Blockly風格UI"""
        # 🎯 頂部工具列 - Blockly風格
        toolbar = tk.Frame(self.root, bg="#5c6bc0", height=60)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        
        # 標題
        tk.Label(
            toolbar, 
            text="ChroLens Blockly 指令編輯器", 
            bg="#5c6bc0", 
            fg="white",
            font=font_tuple(16, "bold")
        ).pack(side="left", padx=25, pady=10)
        
        # 右側腳本選擇與操作
        right_controls = tk.Frame(toolbar, bg="#5c6bc0")
        right_controls.pack(side="right", padx=20)
        
        # 腳本下拉選單
        tk.Label(
            right_controls, 
            text="腳本:", 
            bg="#5c6bc0", 
            fg="white",
            font=font_tuple(10)
        ).pack(side="left", padx=(0, 10))
        
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(
            right_controls,
            textvariable=self.script_var,
            width=25,
            state="readonly",
            font=font_tuple(10)
        )
        self.script_combo.pack(side="left", padx=5)
        self.script_combo.bind("<<ComboboxSelected>>", self._on_script_selected)
        
        # 操作按鈕
        btn_frame = tk.Frame(right_controls, bg="#5c6bc0")
        btn_frame.pack(side="left", padx=10)
        
        for text, cmd, color in [("重新載入", self._load_script, "#2196F3"),
                                 ("儲存", self._save_script, "#4CAF50")]:
            tk.Button(
                btn_frame, 
                text=text, 
                command=cmd, 
                bg=color, 
                fg="white",
                font=font_tuple(9, "bold"), 
                padx=15, 
                pady=8,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=3)
        
        # 🔧 主區域 - 三欄式Blockly佈局
        main = tk.Frame(self.root, bg="#f0f0f0")
        main.pack(fill="both", expand=True, padx=8, pady=8)
        
        # ===== 左側：標籤工具箱 =====
        self._create_left_toolbox(main)
        
        # ===== 中央：文字編輯器 =====
        self._create_center_editor(main)
        
        # ===== 右側：屬性與模組 =====
        self._create_right_properties(main)
        
        # 🔻 底部：指令快捷按鈕區
        self._create_bottom_commands()
    
    def _create_left_toolbox(self, parent):
        """創建左側標籤工具箱"""
        toolbox_frame = tk.Frame(parent, bg="white", width=280, relief="solid", bd=1)
        toolbox_frame.pack(side="left", fill="y", padx=(0, 5))
        toolbox_frame.pack_propagate(False)
        
        # 標籤列
        tabs = tk.Frame(toolbox_frame, bg="white")
        tabs.pack(fill="x")
        
        self.current_tab = 0
        self.tab_buttons = []
        tab_configs = [
            ("操作", 0, ["滑鼠移動", "滑鼠點擊", "滑鼠拖曳", "滑鼠滾輪"]),
            ("鍵盤", 1, ["按下鍵盤", "輸入文字", "組合鍵", "按住鍵盤"]),
            ("控制", 2, ["等待時間", "跳轉標籤", "條件判斷", "迴圈"]),
            ("辨識", 3, ["圖片辨識", "OCR文字", "截圖區域", "顏色偵測"])
        ]
        
        for tab_name, tab_idx, blocks in tab_configs:
            btn = tk.Label(
                tabs,
                text=tab_name,
                bg="#5c6bc0" if tab_idx == 0 else "#e0e0e0",
                fg="white" if tab_idx == 0 else "#666666",
                font=font_tuple(10, "bold"),
                padx=15,
                pady=12,
                cursor="hand2"
            )
            btn.pack(side="left", expand=True, fill="x")
            btn.bind("<Button-1>", lambda e, idx=tab_idx: self._switch_tab(idx))
            self.tab_buttons.append(btn)
        
        # 積木容器
        self.blocks_container = tk.Frame(toolbox_frame, bg="white")
        self.blocks_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 初始化第一個標籤
        self._show_tab_blocks(0)
    
    def _switch_tab(self, tab_idx):
        """切換標籤"""
        self.current_tab = tab_idx
        for i, btn in enumerate(self.tab_buttons):
            if i == tab_idx:
                btn.config(bg="#5c6bc0", fg="white")
            else:
                btn.config(bg="#e0e0e0", fg="#666666")
        self._show_tab_blocks(tab_idx)
        # 同步更新浮動工具箱
        self._update_toolbox_content()
    
    def _show_tab_blocks(self, tab_idx):
        """顯示對應標籤的積木"""
        # 清空現有積木
        for widget in self.blocks_container.winfo_children():
            widget.destroy()
        
        blocks_data = [
            # 操作標籤
            [
                ("滑鼠移動", "移動 x, y", "#42a5f5"),
                ("滑鼠點擊", "點擊 左/右/中", "#42a5f5"),
                ("滑鼠拖曳", "拖曳 x1,y1 到 x2,y2", "#1976d2"),
                ("滑鼠滾輪", "滾輪 向上/向下", "#1565c0"),
            ],
            # 鍵盤標籤
            [
                ("按下鍵盤", "按鍵 按鍵名稱", "#66bb6a"),
                ("輸入文字", "輸入 文字內容", "#66bb6a"),
                ("組合鍵", "組合 ctrl+c", "#43a047"),
                ("按住鍵盤", "按住 按鍵名稱,時間", "#2e7d32"),
            ],
            # 控制標籤
            [
                ("等待時間", "等待 秒數", "#ffa726"),
                ("跳轉標籤", "跳到 標籤名", "#ff9800"),
                ("條件判斷", "如果 條件 則...", "#f57c00"),
                ("迴圈", "重複 次數 次", "#e65100"),
            ],
            # 辨識標籤
            [
                ("圖片辨識", "找圖 圖片名", "#ab47bc"),
                ("OCR文字", "找字 文字內容", "#9c27b0"),
                ("截圖區域", "截圖 x,y,w,h", "#8e24aa"),
                ("顏色偵測", "找色 #RRGGBB", "#7b1fa2"),
            ]
        ]
        
        for block_name, block_text, color in blocks_data[tab_idx]:
            block = tk.Frame(
                self.blocks_container,
                bg=color,
                cursor="hand2",
                relief="raised",
                bd=2
            )
            block.pack(fill="x", pady=6)
            
            label = tk.Label(
                block,
                text=block_text,
                bg=color,
                fg="white",
                font=font_tuple(10, "bold")
            )
            label.pack(pady=12, padx=10)
            
            # 點擊插入對應指令
            block.bind("<Button-1>", lambda e, txt=block_text: self._insert_block_command(txt))
            label.bind("<Button-1>", lambda e, txt=block_text: self._insert_block_command(txt))
    
    def _insert_block_command(self, block_text):
        """插入積木對應的指令到編輯器"""
        command_map = {
            "移動 x, y": ("移動 100, 100", "#569cd6"),
            "點擊 左/右/中": ("點擊 左", "#42a5f5"),
            "拖曳 x1,y1 到 x2,y2": ("拖曳 100,100 到 200,200", "#1976d2"),
            "滾輪 向上/向下": ("滾輪 向上, 3", "#1565c0"),
            "按鍵 按鍵名稱": ("按鍵 enter", "#66bb6a"),
            "輸入 文字內容": ("輸入 Hello World", "#66bb6a"),
            "組合 ctrl+c": ("組合 ctrl, c", "#43a047"),
            "按住 按鍵名稱,時間": ("按住 shift, 1.0", "#2e7d32"),
            "等待 秒數": ("等待 1.0", "#ffa726"),
            "跳到 標籤名": ("標籤:開始", "#ff9800"),
            "如果 條件 則...": ("條件判斷", "#f57c00"),
            "重複 次數 次": ("迴圈 3 次", "#e65100"),
            "找圖 圖片名": ("找圖 pic01", "#ab47bc"),
            "找字 文字內容": ("找字 確定", "#9c27b0"),
            "截圖 x,y,w,h": ("截圖區域", "#8e24aa"),
            "找色 #RRGGBB": ("顏色偵測", "#7b1fa2"),
        }
        
        if self.canvas_mode:
            # 畫布模式：創建節點
            command_text, color = command_map.get(block_text, (f"{block_text}", "#666666"))
            self._create_canvas_node(command_text, color)
        else:
            # 文字模式：插入文字
            command_text, _ = command_map.get(block_text, (f"# {block_text}", "#666666"))
            self.text_editor.insert("insert", command_text + "\n")
            self.text_editor.see("insert")
            self.text_editor.focus_set()
    
    def _create_center_editor(self, parent):
        """創建中央畫布編輯器區域（Figma風格）"""
        editor_frame = tk.Frame(parent, bg="#252526")
        editor_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # 編輯器標題列
        header = tk.Frame(editor_frame, bg="#2c2c2c", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="視覺化編輯畫布",
            bg="#2c2c2c",
            fg="white",
            font=font_tuple(11, "bold")
        ).pack(side="left", padx=15, pady=8)
        
        # 視圖控制
        view_controls = tk.Frame(header, bg="#2c2c2c")
        view_controls.pack(side="right", padx=15)
        
        tk.Button(
            view_controls,
            text="文字模式",
            command=self._toggle_editor_mode,
            bg="#3c3c3c",
            fg="white",
            font=font_tuple(8, "bold"),
            padx=10,
            pady=3,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=3)
        
        # 創建畫布容器
        canvas_container = tk.Frame(editor_frame, bg="#252526")
        canvas_container.pack(fill="both", expand=True)
        
        # 主畫布
        self.canvas = tk.Canvas(
            canvas_container,
            bg="#252526",
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # 繪製網格
        self._draw_grid()
        
        # 畫布數據
        self.canvas_nodes = []  # 儲存所有節點
        self.canvas_connections = []  # 儲存所有連接線
        self.selected_node = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        # 不再創建浮動工具箱（左側已有相同功能）
        # self._create_floating_toolbox(canvas_container)
        
        # 文字編輯器（隱藏，用於文字模式切換）
        self.text_editor_frame = tk.Frame(editor_frame, bg="#1e1e1e")
        editor_font = ("LINE Seed TW", 11) if LINE_SEED_FONT_LOADED else font_tuple(11, monospace=True)
        
        self.text_editor = scrolledtext.ScrolledText(
            self.text_editor_frame,
            font=editor_font,
            wrap="none",
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78",
            selectforeground="white",
            undo=True,
            maxundo=-1
        )
        self.text_editor.pack(fill="both", expand=True)
        
        # 語法高亮標籤
        self._setup_syntax_tags()
        
        # 事件綁定
        self.text_editor.bind("<<Modified>>", self._on_text_modified)
        self.text_editor.bind("<Button-1>", self._on_editor_click)
        self.text_editor.bind("<Button-3>", self._show_context_menu)
        
        # 畫布事件綁定
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._show_canvas_context_menu)
        
        # 編輯器模式（True=畫布, False=文字）
        self.canvas_mode = True
    
    def _setup_syntax_tags(self):
        """設定語法高亮標籤"""
        tags = {
            "syntax_symbol": "#d4d4d4",
            "syntax_time": "#ce9178",
            "syntax_label": "#4ec9b0",
            "syntax_keyboard": "#9cdcfe",
            "syntax_mouse": "#569cd6",
            "syntax_image": "#4ec9b0",
            "syntax_condition": "#c586c0",
            "syntax_ocr": "#4ec9b0",
            "syntax_delay": "#dcdcaa",
            "syntax_flow": "#c586c0",
            "syntax_picname": "#ce9178",
            "syntax_comment": "#6a9955",
            "trajectory_summary": "#00BFFF",
            "trajectory_hidden": "#00BFFF",
            "trajectory_clickable": "#00BFFF",
        }
        
        for tag, color in tags.items():
            config = {"foreground": color}
            if tag == "trajectory_summary":
                config["font"] = font_tuple(11, "bold")
            elif tag == "trajectory_hidden":
                config["elide"] = True
            elif tag == "trajectory_clickable":
                config["underline"] = 1
            
            self.text_editor.tag_config(tag, **config)
    
    def _create_right_properties(self, parent):
        """創建右側屬性與模組面板"""
        props_frame = tk.Frame(parent, bg="white", width=320, relief="solid", bd=1)
        props_frame.pack(side="left", fill="y")
        props_frame.pack_propagate(False)
        
        # ===== 上半部：屬性設定 =====
        props_header = tk.Frame(props_frame, bg="#e8eaf6", height=40)
        props_header.pack(fill="x")
        props_header.pack_propagate(False)
        
        tk.Label(
            props_header,
            text="屬性設定",
            bg="#e8eaf6",
            fg="#5c6bc0",
            font=font_tuple(12, "bold")
        ).pack(pady=10)
        
        # 屬性內容
        props_content = tk.Frame(props_frame, bg="white")
        props_content.pack(fill="x", padx=15, pady=10)
        
        properties = [
            ("回放速度 (%)", "100"),
            ("重複次數", "1"),
            ("重複時間", "00:00:00"),
            ("重複間隔", "0")
        ]
        
        self.prop_entries = {}
        for label_text, default in properties:
            frame = tk.Frame(props_content, bg="white")
            frame.pack(fill="x", pady=8)
            
            tk.Label(
                frame,
                text=label_text,
                bg="white",
                fg="#666666",
                font=font_tuple(9)
            ).pack(anchor="w", pady=(0, 3))
            
            entry = tk.Entry(
                frame,
                bg="#f5f5f5",
                fg="#333333",
                bd=1,
                relief="solid",
                font=font_tuple(10)
            )
            entry.pack(fill="x")
            entry.insert(0, default)
            self.prop_entries[label_text] = entry
        
        # 分隔線
        tk.Frame(props_frame, bg="#e0e0e0", height=2).pack(fill="x", pady=15)
        
        # ===== 下半部：模組管理 =====
        module_header = tk.Frame(props_frame, bg="#e8f5e9", height=40)
        module_header.pack(fill="x")
        module_header.pack_propagate(False)
        
        tk.Label(
            module_header,
            text="自訂模組",
            bg="#e8f5e9",
            fg="#43a047",
            font=font_tuple(11, "bold")
        ).pack(pady=10)
        
        # 模組按鈕
        module_btn_frame = tk.Frame(props_frame, bg="white")
        module_btn_frame.pack(fill="x", padx=10, pady=10)
        
        for text, cmd, color in [
            ("儲存模組", self._save_new_module, "#4CAF50"),
            ("插入模組", self._insert_module, "#2196F3"),
            ("刪除模組", self._delete_module, "#F44336")
        ]:
            tk.Button(
                module_btn_frame,
                text=text,
                command=cmd,
                bg=color,
                fg="white",
                font=font_tuple(8, "bold"),
                padx=8,
                pady=5,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", expand=True, padx=2)
        
        # 模組列表
        tk.Label(
            props_frame,
            text="已儲存模組 (雙擊插入):",
            bg="white",
            fg="#666666",
            font=font_tuple(9)
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        list_container = tk.Frame(props_frame, bg="white")
        list_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.module_listbox = tk.Listbox(
            list_container,
            font=font_tuple(9),
            yscrollcommand=scrollbar.set,
            bg="#fafafa"
        )
        self.module_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.module_listbox.yview)
        
        self.module_listbox.bind("<Double-Button-1>", lambda e: self._insert_module())
        
        # 刷新模組列表
        self._refresh_module_list()
    
    def _create_bottom_commands(self):
        """創建底部指令快捷按鈕區"""
        bottom = tk.Frame(self.root, bg="#ffffff", relief="ridge", bd=2, height=100)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        bottom.pack_propagate(False)
        
        tk.Label(
            bottom,
            text="快速指令插入",
            bg="#ffffff",
            fg="#5c6bc0",
            font=font_tuple(10, "bold")
        ).pack(anchor="w", padx=15, pady=(8, 5))
        
        # 指令按鈕容器
        btn_container = tk.Frame(bottom, bg="#ffffff")
        btn_container.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        
        commands = [
            ("記錄滑鼠", self._capture_mouse_position, "#42a5f5"),
            ("快速輸入", self._quick_type_text, "#66bb6a"),
            ("插入等待", self._insert_wait, "#ffa726"),
            ("截圖辨識", self._capture_for_recognition, "#ab47bc"),
            ("新增標籤", self._insert_label, "#00bcd4"),
            ("指令說明", self._show_command_reference, "#ff9800"),
        ]
        
        for i, (text, cmd, color) in enumerate(commands):
            btn = tk.Button(
                btn_container,
                text=text,
                command=cmd,
                bg=color,
                fg="white",
                font=font_tuple(9, "bold"),
                padx=12,
                pady=10,
                relief="flat",
                cursor="hand2"
            )
            btn.grid(row=0, column=i, padx=3, sticky="ew")
            btn_container.grid_columnconfigure(i, weight=1)
    
    # ==================== 核心功能方法 ====================
    
    def _draw_grid(self):
        """繪製畫布網格"""
        # 清除現有網格
        self.canvas.delete("grid")
        
        # 獲取畫布尺寸
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # 繪製網格線
        grid_size = 30
        for i in range(0, width, grid_size):
            self.canvas.create_line(i, 0, i, height, fill="#2d2d2d", tags="grid")
        for j in range(0, height, grid_size):
            self.canvas.create_line(0, j, width, j, fill="#2d2d2d", tags="grid")
    
    def _create_floating_toolbox(self, parent):
        """創建可拖曳的浮動工具箱（已停用，使用左側工具箱）"""
        # 已停用浮動工具箱，左側已有完整功能
        return
        self.toolbox = tk.Frame(parent, bg="#2c2c2c", relief="solid", bd=2)
        self.toolbox.place(x=20, y=60, width=200, height=350)
        
        # 標題列（可拖曳）
        header = tk.Frame(self.toolbox, bg="#3c3c3c", height=30, cursor="fleur")
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🔧 工具箱",
            bg="#3c3c3c",
            fg="white",
            font=font_tuple(9, "bold")
        ).pack(side="left", padx=10, pady=5)
        
        # 最小化按鈕
        minimize_btn = tk.Button(
            header,
            text="−",
            bg="#3c3c3c",
            fg="#888888",
            relief="flat",
            font=("Arial", 12),
            command=self._toggle_toolbox
        )
        minimize_btn.pack(side="right", padx=5)
        
        # 工具箱內容
        self.toolbox_content = tk.Frame(self.toolbox, bg="#252526")
        self.toolbox_content.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 根據當前標籤更新工具箱
        self._update_toolbox_content()
        
        # 拖曳功能
        header.bind("<Button-1>", self._start_drag_toolbox)
        header.bind("<B1-Motion>", self._drag_toolbox)
        
        self.toolbox_minimized = False
    
    def _update_toolbox_content(self):
        """更新工具箱內容（根據左側標籤）"""
        # 清空現有內容
        for widget in self.toolbox_content.winfo_children():
            widget.destroy()
        
        # 根據當前標籤顯示對應工具
        tools_data = [
            # 操作標籤
            [
                ("移動滑鼠", "移動 100, 100", "#42a5f5"),
                ("滑鼠點擊", "點擊 左", "#42a5f5"),
                ("滑鼠拖曳", "拖曳 100,100 到 200,200", "#1976d2"),
                ("滑鼠滾輪", "滾輪 向上, 3", "#1565c0"),
            ],
            # 鍵盤標籤
            [
                ("按下鍵盤", "按鍵 enter", "#66bb6a"),
                ("輸入文字", "輸入 Hello", "#66bb6a"),
                ("組合鍵", "組合 ctrl, c", "#43a047"),
                ("按住鍵盤", "按住 shift, 1.0", "#2e7d32"),
            ],
            # 控制標籤
            [
                ("等待時間", "等待 1.0", "#ffa726"),
                ("標籤", "標籤:開始", "#ff9800"),
                ("條件判斷", "條件判斷", "#f57c00"),
                ("迴圈", "迴圈 3 次", "#e65100"),
            ],
            # 辨識標籤
            [
                ("圖片辨識", "找圖 pic01", "#ab47bc"),
                ("OCR文字", "找字 確定", "#9c27b0"),
                ("截圖區域", "截圖區域", "#8e24aa"),
                ("顏色偵測", "顏色偵測", "#7b1fa2"),
            ]
        ]
        
        tools = tools_data[self.current_tab]
        
        for tool_name, command, color in tools:
            tool_btn = tk.Frame(
                self.toolbox_content,
                bg=color,
                cursor="hand2",
                relief="raised",
                bd=1
            )
            tool_btn.pack(fill="x", padx=5, pady=5)
            
            label = tk.Label(
                tool_btn,
                text=tool_name,
                bg=color,
                fg="white",
                font=font_tuple(9, "bold")
            )
            label.pack(pady=8, padx=5)
            
            # 點擊創建節點
            tool_btn.bind("<Button-1>", lambda e, cmd=command, col=color: self._create_canvas_node(cmd, col))
            label.bind("<Button-1>", lambda e, cmd=command, col=color: self._create_canvas_node(cmd, col))
    
    def _start_drag_toolbox(self, event):
        """開始拖曳工具箱"""
        self.toolbox_drag_data = {
            "x": event.x,
            "y": event.y
        }
    
    def _drag_toolbox(self, event):
        """拖曳工具箱"""
        dx = event.x - self.toolbox_drag_data["x"]
        dy = event.y - self.toolbox_drag_data["y"]
        
        x = self.toolbox.winfo_x() + dx
        y = self.toolbox.winfo_y() + dy
        
        self.toolbox.place(x=x, y=y)
    
    def _toggle_toolbox(self):
        """最小化/還原工具箱"""
        if self.toolbox_minimized:
            self.toolbox_content.pack(fill="both", expand=True, padx=2, pady=2)
            self.toolbox_minimized = False
        else:
            self.toolbox_content.pack_forget()
            self.toolbox_minimized = True
    
    def _create_canvas_node(self, text, color, x=None, y=None):
        """在畫布上創建節點"""
        if x is None or y is None:
            # 自動定位：在畫布中央偏右堆疊
            x = 400 + len(self.canvas_nodes) * 20
            y = 100 + len(self.canvas_nodes) * 80
        
        # 創建節點矩形
        node_rect = self.canvas.create_rectangle(
            x, y, x + 180, y + 60,
            fill=color,
            outline="white",
            width=2,
            tags=("node", f"node_{len(self.canvas_nodes)}")
        )
        
        # 創建節點文字
        node_text = self.canvas.create_text(
            x + 90, y + 30,
            text=text,
            fill="white",
            font=font_tuple(10, "bold"),
            tags=("node", f"node_{len(self.canvas_nodes)}")
        )
        
        # 儲存節點資料
        node_data = {
            "rect": node_rect,
            "text": node_text,
            "command": text,
            "color": color,
            "x": x,
            "y": y
        }
        self.canvas_nodes.append(node_data)
        
        # 自動連接到前一個節點
        if len(self.canvas_nodes) > 1:
            self._connect_nodes(len(self.canvas_nodes) - 2, len(self.canvas_nodes) - 1)
        
        return len(self.canvas_nodes) - 1
    
    def _connect_nodes(self, idx1, idx2):
        """連接兩個節點"""
        if idx1 < 0 or idx1 >= len(self.canvas_nodes) or idx2 < 0 or idx2 >= len(self.canvas_nodes):
            return
        
        node1 = self.canvas_nodes[idx1]
        node2 = self.canvas_nodes[idx2]
        
        # 計算連接點
        x1 = node1["x"] + 90
        y1 = node1["y"] + 60
        x2 = node2["x"] + 90
        y2 = node2["y"]
        
        # 創建連接線
        line = self.canvas.create_line(
            x1, y1, x2, y2,
            fill="#666666",
            width=3,
            arrow=tk.LAST,
            tags="connection"
        )
        
        self.canvas_connections.append({
            "line": line,
            "from": idx1,
            "to": idx2
        })
        
        # 將連接線移到節點下層
        self.canvas.tag_lower("connection")
        self.canvas.tag_lower("grid")
    
    def _on_canvas_click(self, event):
        """畫布點擊事件"""
        # 檢查是否點擊到節點
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        if "node" in tags:
            # 選中節點
            self.selected_node = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.drag_data["item"] = item
    
    def _on_canvas_drag(self, event):
        """畫布拖曳事件"""
        if self.drag_data["item"]:
            # 計算移動距離
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            # 移動節點
            tags = self.canvas.gettags(self.drag_data["item"])
            for tag in tags:
                if tag.startswith("node_"):
                    # 移動該節點的所有元素
                    self.canvas.move(tag, dx, dy)
                    
                    # 更新節點資料
                    node_idx = int(tag.split("_")[1])
                    if node_idx < len(self.canvas_nodes):
                        self.canvas_nodes[node_idx]["x"] += dx
                        self.canvas_nodes[node_idx]["y"] += dy
                    
                    # 更新連接線
                    self._update_connections(node_idx)
                    break
            
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
    
    def _on_canvas_release(self, event):
        """畫布釋放事件"""
        self.drag_data["item"] = None
    
    def _update_connections(self, node_idx):
        """更新與指定節點相關的所有連接線"""
        for conn in self.canvas_connections:
            if conn["from"] == node_idx or conn["to"] == node_idx:
                # 重新計算連接點
                node1 = self.canvas_nodes[conn["from"]]
                node2 = self.canvas_nodes[conn["to"]]
                
                x1 = node1["x"] + 90
                y1 = node1["y"] + 60
                x2 = node2["x"] + 90
                y2 = node2["y"]
                
                # 更新連接線
                self.canvas.coords(conn["line"], x1, y1, x2, y2)
    
    def _show_canvas_context_menu(self, event):
        """顯示畫布右鍵選單"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="清空畫布", command=self._clear_canvas)
        menu.add_command(label="自動排列", command=self._auto_arrange_nodes)
        menu.add_separator()
        menu.add_command(label="轉換為文字", command=self._canvas_to_text)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _clear_canvas(self):
        """清空畫布"""
        if messagebox.askyesno("確認", "確定要清空畫布嗎？"):
            self.canvas.delete("node")
            self.canvas.delete("connection")
            self.canvas_nodes.clear()
            self.canvas_connections.clear()
    
    def _auto_arrange_nodes(self):
        """自動排列節點"""
        if not self.canvas_nodes:
            return
        
        # 垂直排列
        x = 400
        y = 100
        
        for i, node in enumerate(self.canvas_nodes):
            dx = x - node["x"]
            dy = y - node["y"]
            
            # 移動節點
            self.canvas.move(f"node_{i}", dx, dy)
            
            # 更新節點資料
            node["x"] = x
            node["y"] = y
            
            y += 80
        
        # 更新所有連接線
        for i in range(len(self.canvas_nodes)):
            self._update_connections(i)
    
    def _canvas_to_text(self):
        """將畫布節點轉換為文字指令"""
        if not self.canvas_nodes:
            messagebox.showinfo("提示", "畫布上沒有節點")
            return
        
        # 清空文字編輯器
        self.text_editor.delete("1.0", tk.END)
        
        # 轉換節點為文字
        for node in self.canvas_nodes:
            command = node["command"]
            self.text_editor.insert(tk.END, command + "\n")
        
        # 切換到文字模式
        self._toggle_editor_mode()
        
        messagebox.showinfo("成功", "已轉換為文字模式")
    
    def _toggle_editor_mode(self):
        """切換編輯器模式"""
        if self.canvas_mode:
            # 切換到文字模式
            self.canvas.pack_forget()
            # 不再使用浮動工具箱
            # self.toolbox.place_forget()
            self.text_editor_frame.pack(fill="both", expand=True)
            self.canvas_mode = False
        else:
            # 切換到畫布模式
            self.text_editor_frame.pack_forget()
            self.canvas.pack(fill="both", expand=True)
            # 不再使用浮動工具箱
            # self.toolbox.place(x=20, y=60, width=200, height=350)
            self.canvas_mode = True
    
    # ==================== 核心功能方法 ====================
    
    def _refresh_script_list(self):
        """刷新腳本列表"""
        scripts_dir = os.path.join(os.getcwd(), "scripts")
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
        
        script_files = []
        for filename in os.listdir(scripts_dir):
            if filename.endswith('.json'):
                script_name = os.path.splitext(filename)[0]
                script_files.append(script_name)
        
        script_files.sort()
        self.script_combo['values'] = script_files
        
        if script_files and not self.script_var.get():
            self.script_var.set(script_files[0])
    
    def _on_script_selected(self, event=None):
        """腳本選擇事件"""
        self._load_script()
    
    def _load_script(self):
        """載入腳本"""
        script_name = self.script_var.get()
        if not script_name:
            messagebox.showwarning("警告", "請選擇一個腳本")
            return
        
        scripts_dir = os.path.join(os.getcwd(), "scripts")
        script_file = os.path.join(scripts_dir, f"{script_name}.json")
        
        if not os.path.exists(script_file):
            messagebox.showerror("錯誤", f"找不到腳本檔案: {script_file}")
            return
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新屬性
            self.original_settings = data
            self.prop_entries["回放速度 (%)"].delete(0, tk.END)
            self.prop_entries["回放速度 (%)"].insert(0, data.get("speed", "100"))
            
            self.prop_entries["重複次數"].delete(0, tk.END)
            self.prop_entries["重複次數"].insert(0, data.get("repeat", "1"))
            
            self.prop_entries["重複時間"].delete(0, tk.END)
            self.prop_entries["重複時間"].insert(0, data.get("repeat_time", "00:00:00"))
            
            self.prop_entries["重複間隔"].delete(0, tk.END)
            self.prop_entries["重複間隔"].insert(0, data.get("repeat_interval", "00:00:00"))
            
            # 轉換JSON為文字指令
            actions = data.get("script_actions", [])
            text_commands = self._convert_json_to_text(actions)
            
            # 更新文字編輯器
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", text_commands)
            
            # 如果在畫布模式，也在畫布上顯示
            if self.canvas_mode and actions:
                self._clear_canvas()
                self._load_actions_to_canvas(actions)
            
            # 套用語法高亮
            self._apply_syntax_highlighting()
            
            messagebox.showinfo("成功", f"已載入腳本: {script_name}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入腳本失敗:\n{str(e)}")
    
    def _load_actions_to_canvas(self, actions):
        """將動作載入到畫布"""
        color_map = {
            "mouse_move": "#569cd6",
            "mouse_click": "#42a5f5",
            "mouse_drag": "#1976d2",
            "mouse_scroll": "#1565c0",
            "key_press": "#66bb6a",
            "type_text": "#66bb6a",
            "key_combo": "#43a047",
            "key_hold": "#2e7d32",
            "delay": "#ffa726",
            "label": "#ff9800",
            "image_recognition": "#ab47bc",
            "ocr_recognition": "#9c27b0",
            "default": "#888888"
        }
        
        for action in actions:
            action_type = action.get("action", "")
            color = color_map.get(action_type, color_map["default"])
            
            # 生成簡短的顯示文字
            if action_type == "mouse_move":
                text = f"移動 {action.get('x', 0)}, {action.get('y', 0)}"
            elif action_type == "mouse_click":
                text = f"點擊 {action.get('button', 'left')}"
            elif action_type == "key_press":
                text = f"按鍵 {action.get('key', '')}"
            elif action_type == "type_text":
                text = f"輸入 {action.get('text', '')[:15]}"
            elif action_type == "delay":
                text = f"等待 {action.get('duration', 0)}"
            elif action_type == "image_recognition":
                text = f"找圖 {action.get('image_name', '')}"
            elif action_type == "ocr_recognition":
                text = f"找字 {action.get('target_text', '')}"
            else:
                text = action_type
            
            self._create_canvas_node(text, color)
    
    def _save_script(self):
        """儲存腳本"""
        script_name = self.script_var.get()
        if not script_name:
            messagebox.showwarning("警告", "請選擇或輸入腳本名稱")
            return
        
        try:
            # 如果在畫布模式，先轉換為文字
            if self.canvas_mode:
                self._sync_canvas_to_text()
            
            # 取得文字指令
            text_commands = self.text_editor.get("1.0", tk.END)
            
            # 轉換文字指令為JSON
            actions = self._convert_text_to_json(text_commands)
            
            # 組合完整設定
            data = {
                "speed": self.prop_entries["回放速度 (%)"].get(),
                "repeat": self.prop_entries["重複次數"].get(),
                "repeat_time": self.prop_entries["重複時間"].get(),
                "repeat_interval": self.prop_entries["重複間隔"].get(),
                "random_interval": self.original_settings.get("random_interval", False),
                "script_hotkey": self.original_settings.get("script_hotkey", ""),
                "script_actions": actions,
                "window_info": self.original_settings.get("window_info")
            }
            
            # 儲存檔案
            scripts_dir = os.path.join(os.getcwd(), "scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            script_file = os.path.join(scripts_dir, f"{script_name}.json")
            
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"已儲存腳本: {script_name}\n共 {len(actions)} 個動作")
            self._refresh_script_list()
            
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存腳本失敗:\n{str(e)}")
    
    def _sync_canvas_to_text(self):
        """同步畫布內容到文字編輯器"""
        if not self.canvas_nodes:
            return
        
        # 清空文字編輯器
        self.text_editor.delete("1.0", tk.END)
        
        # 轉換節點為文字
        for node in self.canvas_nodes:
            command = node["command"]
            self.text_editor.insert(tk.END, command + "\n")
    
    def _convert_json_to_text(self, actions):
        """將JSON動作轉換為文字指令"""
        text_lines = []
        
        for action in actions:
            action_type = action.get("action")
            
            if action_type == "mouse_move":
                x, y = action.get("x", 0), action.get("y", 0)
                text_lines.append(f"移動 {x}, {y}")
            
            elif action_type == "mouse_click":
                button = action.get("button", "left")
                clicks = action.get("clicks", 1)
                if clicks > 1:
                    text_lines.append(f"點擊 {button}, {clicks}")
                else:
                    text_lines.append(f"點擊 {button}")
            
            elif action_type == "key_press":
                key = action.get("key", "")
                text_lines.append(f"按鍵 {key}")
            
            elif action_type == "key_combo":
                keys = action.get("keys", [])
                text_lines.append(f"組合 {', '.join(keys)}")
            
            elif action_type == "type_text":
                text = action.get("text", "")
                text_lines.append(f"輸入 {text}")
            
            elif action_type == "delay":
                duration = action.get("duration", 0)
                text_lines.append(f"等待 {duration}")
            
            elif action_type == "image_recognition":
                image_name = action.get("image_name", "")
                text_lines.append(f"找圖 {image_name}")
            
            elif action_type == "ocr_recognition":
                target_text = action.get("target_text", "")
                text_lines.append(f"找字 {target_text}")
            
            elif action_type == "label":
                label_name = action.get("label_name", "")
                text_lines.append(f"標籤:{label_name}")
            
            else:
                text_lines.append(f"# 未知動作: {action_type}")
        
        return "\n".join(text_lines)
    
    def _convert_text_to_json(self, text_commands):
        """將文字指令轉換為JSON動作"""
        actions = []
        lines = text_commands.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳過空行和註解
            if not line or line.startswith('#'):
                continue
            
            # 解析各種指令
            if line.startswith("移動"):
                match = re.match(r'移動\s+(\d+)\s*,\s*(\d+)', line)
                if match:
                    actions.append({
                        "action": "mouse_move",
                        "x": int(match.group(1)),
                        "y": int(match.group(2))
                    })
            
            elif line.startswith("點擊"):
                parts = line.split()
                button = parts[1] if len(parts) > 1 else "left"
                clicks = int(parts[2]) if len(parts) > 2 else 1
                actions.append({
                    "action": "mouse_click",
                    "button": button,
                    "clicks": clicks
                })
            
            elif line.startswith("按鍵"):
                key = line.split(maxsplit=1)[1] if ' ' in line else ""
                actions.append({
                    "action": "key_press",
                    "key": key
                })
            
            elif line.startswith("組合"):
                keys_str = line.split(maxsplit=1)[1] if ' ' in line else ""
                keys = [k.strip() for k in keys_str.split(',')]
                actions.append({
                    "action": "key_combo",
                    "keys": keys
                })
            
            elif line.startswith("輸入"):
                text = line.split(maxsplit=1)[1] if ' ' in line else ""
                actions.append({
                    "action": "type_text",
                    "text": text
                })
            
            elif line.startswith("等待"):
                duration_str = line.split()[1] if len(line.split()) > 1 else "0"
                actions.append({
                    "action": "delay",
                    "duration": float(duration_str)
                })
            
            elif line.startswith("找圖"):
                image_name = line.split(maxsplit=1)[1] if ' ' in line else ""
                actions.append({
                    "action": "image_recognition",
                    "image_name": image_name
                })
            
            elif line.startswith("找字"):
                target_text = line.split(maxsplit=1)[1] if ' ' in line else ""
                actions.append({
                    "action": "ocr_recognition",
                    "target_text": target_text
                })
            
            elif line.startswith("標籤:"):
                label_name = line.split(':', 1)[1].strip()
                actions.append({
                    "action": "label",
                    "label_name": label_name
                })
        
        return actions
    
    # ==================== 語法高亮 ====================
    
    def _on_text_modified(self, event=None):
        """文字修改事件"""
        if self.text_editor.edit_modified():
            self._apply_syntax_highlighting()
            self.text_editor.edit_modified(False)
    
    def _apply_syntax_highlighting(self):
        """套用語法高亮"""
        # 移除所有標籤
        for tag in self.text_editor.tag_names():
            if tag.startswith("syntax_"):
                self.text_editor.tag_remove(tag, "1.0", tk.END)
        
        content = self.text_editor.get("1.0", tk.END)
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            
            # 註解
            if line.strip().startswith('#'):
                self.text_editor.tag_add("syntax_comment", line_start, f"{i+1}.end")
                continue
            
            # 指令關鍵字高亮
            if line.startswith("移動") or line.startswith("點擊"):
                self.text_editor.tag_add("syntax_mouse", line_start, f"{line_start}+4c")
            elif line.startswith("按鍵") or line.startswith("輸入") or line.startswith("組合"):
                self.text_editor.tag_add("syntax_keyboard", line_start, f"{line_start}+4c")
            elif line.startswith("等待"):
                self.text_editor.tag_add("syntax_delay", line_start, f"{line_start}+4c")
            elif line.startswith("找圖") or line.startswith("找字"):
                self.text_editor.tag_add("syntax_image", line_start, f"{line_start}+4c")
            elif line.startswith("標籤:"):
                self.text_editor.tag_add("syntax_label", line_start, f"{i+1}.end")
    
    def _toggle_trajectory_display(self):
        """切換軌跡顯示"""
        # 簡化版本
        pass
    
    def _on_editor_click(self, event):
        """編輯器點擊事件"""
        pass
    
    def _show_context_menu(self, event):
        """顯示右鍵選單"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="剪下", command=lambda: self.text_editor.event_generate("<<Cut>>"))
        menu.add_command(label="複製", command=lambda: self.text_editor.event_generate("<<Copy>>"))
        menu.add_command(label="貼上", command=lambda: self.text_editor.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="全選", command=lambda: self.text_editor.tag_add("sel", "1.0", tk.END))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    # ==================== 模組管理 ====================
    
    def _refresh_module_list(self):
        """刷新模組列表"""
        self.module_listbox.delete(0, tk.END)
        
        if os.path.exists(self.modules_dir):
            for filename in sorted(os.listdir(self.modules_dir)):
                if filename.endswith('.txt'):
                    module_name = os.path.splitext(filename)[0]
                    self.module_listbox.insert(tk.END, module_name)
    
    def _save_new_module(self):
        """儲存新模組"""
        # 取得選取的文字
        try:
            selected_text = self.text_editor.get("sel.first", "sel.last")
        except:
            messagebox.showwarning("警告", "請先選取要儲存的指令")
            return
        
        if not selected_text.strip():
            messagebox.showwarning("警告", "選取的內容為空")
            return
        
        # 輸入模組名稱
        module_name = simpledialog.askstring("儲存模組", "請輸入模組名稱:")
        if not module_name:
            return
        
        # 儲存檔案
        module_file = os.path.join(self.modules_dir, f"{module_name}.txt")
        try:
            with open(module_file, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            messagebox.showinfo("成功", f"已儲存模組: {module_name}")
            self._refresh_module_list()
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存模組失敗:\n{str(e)}")
    
    def _insert_module(self):
        """插入模組"""
        selection = self.module_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇一個模組")
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_file = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_file, 'r', encoding='utf-8') as f:
                module_content = f.read()
            
            self.text_editor.insert("insert", module_content + "\n")
            self.text_editor.see("insert")
        except Exception as e:
            messagebox.showerror("錯誤", f"插入模組失敗:\n{str(e)}")
    
    def _delete_module(self):
        """刪除模組"""
        selection = self.module_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要刪除的模組")
            return
        
        module_name = self.module_listbox.get(selection[0])
        
        if messagebox.askyesno("確認", f"確定要刪除模組 '{module_name}' 嗎？"):
            module_file = os.path.join(self.modules_dir, f"{module_name}.txt")
            try:
                os.remove(module_file)
                self._refresh_module_list()
                messagebox.showinfo("成功", f"已刪除模組: {module_name}")
            except Exception as e:
                messagebox.showerror("錯誤", f"刪除模組失敗:\n{str(e)}")
    
    # ==================== 快速指令 ====================
    
    def _capture_mouse_position(self):
        """記錄滑鼠位置"""
        self.root.withdraw()
        self.root.after(100, self._do_capture_mouse)
    
    def _do_capture_mouse(self):
        messagebox.showinfo("提示", "請將滑鼠移到目標位置\n按下 Enter 記錄座標")
        
        def on_enter(event):
            try:
                import pyautogui
                x, y = pyautogui.position()
                self.text_editor.insert("insert", f"移動 {x}, {y}\n")
                self.root.deiconify()
            except:
                messagebox.showerror("錯誤", "無法取得滑鼠位置")
                self.root.deiconify()
        
        self.root.bind("<Return>", on_enter)
        self.root.deiconify()
    
    def _quick_type_text(self):
        """快速輸入文字"""
        text = simpledialog.askstring("輸入文字", "請輸入要自動輸入的文字:")
        if text:
            self.text_editor.insert("insert", f"輸入 {text}\n")
    
    def _insert_wait(self):
        """插入等待"""
        duration = simpledialog.askfloat("等待時間", "請輸入等待秒數:", initialvalue=1.0)
        if duration is not None:
            self.text_editor.insert("insert", f"等待 {duration}\n")
    
    def _capture_for_recognition(self):
        """截圖辨識"""
        self.root.withdraw()
        messagebox.showinfo("截圖", "請框選要辨識的區域\n完成後會自動儲存並插入指令")
        
        try:
            img = ImageGrab.grab()
            
            # 自動命名
            pic_name = f"pic{self._pic_counter:02d}"
            self._pic_counter += 1
            
            # 儲存圖片
            img_path = os.path.join(self.images_dir, f"{pic_name}.png")
            img.save(img_path)
            
            # 插入指令
            self.text_editor.insert("insert", f"找圖 {pic_name}\n")
            
            messagebox.showinfo("成功", f"已儲存圖片: {pic_name}")
        except Exception as e:
            messagebox.showerror("錯誤", f"截圖失敗:\n{str(e)}")
        finally:
            self.root.deiconify()
    
    def _insert_label(self):
        """新增標籤"""
        label_name = simpledialog.askstring("標籤名稱", "請輸入標籤名稱:")
        if label_name:
            self.text_editor.insert("insert", f"標籤:{label_name}\n")
    
    def _show_command_reference(self):
        """顯示指令說明"""
        help_text = """
═══════════════════════════════════════
        ChroLens 指令語法說明
═══════════════════════════════════════

【滑鼠操作】
  移動 x, y               - 移動滑鼠到指定座標
  點擊 左/右/中           - 點擊滑鼠按鍵
  點擊 左, 2              - 連續點擊2次
  拖曳 x1,y1 到 x2,y2     - 拖曳滑鼠
  滾輪 向上/向下, 次數     - 滾動滾輪

【鍵盤操作】
  按鍵 按鍵名稱           - 按下單一按鍵
  輸入 文字內容           - 輸入文字
  組合 ctrl, c            - 按下組合鍵
  按住 shift, 1.0         - 按住按鍵指定時間

【流程控制】
  等待 秒數               - 等待指定時間
  標籤:名稱               - 定義跳轉點
  跳到 標籤名             - 跳轉到標籤

【圖片辨識】
  找圖 圖片名             - 尋找並點擊圖片
  找字 文字內容           - OCR文字辨識
  截圖 x,y,w,h > 名稱     - 截圖並儲存

【註解】
  # 這是註解             - 不會執行的說明文字

═══════════════════════════════════════
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("指令說明")
        help_window.geometry("600x700")
        
        text = scrolledtext.ScrolledText(
            help_window,
            font=font_tuple(10, monospace=True),
            wrap="none",
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", help_text)
        text.config(state="disabled")
    
    def run(self):
        """執行主迴圈"""
        self.root.mainloop()


def main():
    """主程式入口"""
    editor = BlocklyScriptEditor()
    editor.run()


if __name__ == "__main__":
    main()
