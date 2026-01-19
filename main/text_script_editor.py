# -*- coding: utf-8 -*-
"""
ChroLens 文字指令式腳本編輯器
將JSON事件轉換為簡單的文字指令格式

強化功能：
- 正確處理空白行和僅包含空白字符的行，不影響腳本轉換
- 支援使用者在指令之間添加空行以提高可讀性
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
from tkinter import font as tkfont
import json
import os
import re
import sys
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageGrab, ImageTk

# 🔥 優化：引入更快的螢幕截圖庫
try:
    import mss
    import numpy as np
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

# 🔧 載入 LINE Seed 字體
LINE_SEED_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TTF", "LINESeedTW_TTF_Rg.ttf")
try:
    import pyglet
    if os.path.exists(LINE_SEED_FONT_PATH):
        pyglet.font.add_file(LINE_SEED_FONT_PATH)
        LINE_SEED_FONT_LOADED = True
    else:
        LINE_SEED_FONT_LOADED = False
except:
    LINE_SEED_FONT_LOADED = False

# 🔧 字體系統（獨立定義，避免循環匯入）
def font_tuple(size, weight=None, monospace=False):
    """
    回傳字體元組
    :param size: 字體大小
    :param weight: 字體粗細 (可選)
    :param monospace: 是否使用等寬字體
    :return: 字體元組
    """
    # 優先使用 LINE Seed 字體
    if LINE_SEED_FONT_LOADED:
        fam = "LINE Seed TW"
    else:
        fam = "Consolas" if monospace else "Microsoft JhengHei"
    if weight:
        return (fam, size, weight)
    return (fam, size)


# ========== PCB 風格布線器 (v11 - GitHub Actions 風格) ==========
# 用於圖形模式的線路碰撞偵測和路徑計算

PCB_COLORS = {
    "main": "#30363d",      # GitHub Actions 風格 - 主連線灰色
    "inactive": "#484f58",  # 無作用節點的連線用深灰色
    "success": "#3fb950",   # 成功 - 綠色
    "failure": "#f85149",   # 失敗 - 紅色
    "loop": "#58a6ff",      # 迴圈 - 藍色
    "fork": "#56d364",      # 並行分叉 - 亮綠色
    "parallel": "#a371f7",  # 並行線程 - 紫色
    "background": "#0d1117", # GitHub 深色背景
    "card": "#161b22",      # 卡片背景
    "text": "#c9d1d9",       # 文字顏色
    "border": "#30363d",    # 邊框顏色
}

PCB_LINE_WIDTH = 3
PCB_GRID_SIZE = 10
PCB_GRAY_COLOR = "#30363d"
PCB_CORNER_RADIUS = 12  # 圓角半徑


def create_rounded_rect(canvas, x1, y1, x2, y2, radius=12, **kwargs):
    """
    在 Canvas 上繪製圓角矩形
    
    使用 Bézier 曲線近似圓角
    """
    points = [
        x1 + radius, y1,           # 上邊起點
        x2 - radius, y1,           # 上邊終點
        x2, y1,                    # 右上角控制點
        x2, y1 + radius,           # 右邊起點
        x2, y2 - radius,           # 右邊終點
        x2, y2,                    # 右下角控制點
        x2 - radius, y2,           # 下邊起點
        x1 + radius, y2,           # 下邊終點
        x1, y2,                    # 左下角控制點
        x1, y2 - radius,           # 左邊起點
        x1, y1 + radius,           # 左邊終點
        x1, y1,                    # 左上角控制點
        x1 + radius, y1,           # 回到起點
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)



class GlobalRouter:
    """全域碰撞偵測布線器 - PCB 風格 (v2.8.2: 支援視覺縮放)"""
    
    def __init__(self, nodes, scale=1.0):
        self.nodes = nodes
        self.scale = scale
        # ✅ 基於縮放比例動態調整網格
        self.grid_size = max(2, int(PCB_GRID_SIZE * scale))
        self.h_segments = {}
        self.v_segments = {}
        self.label_rects = []
        self.node_rects = []
        self.line_count = 0
        self._mark_nodes_as_blocked()
    
    def _mark_nodes_as_blocked(self):
        self.node_rects = []
        # ✅ Padding 隨比例縮放
        padding = 4 * self.scale
        for node in self.nodes:
            # 使用 .get 以防寬高度缺失
            w = node.get("width", 150)
            h = node.get("height", 36)
            self.node_rects.append({
                "x1": node["x"] - padding,
                "y1": node["y"] - padding,
                "x2": node["x"] + w + padding,
                "y2": node["y"] + h + padding,
            })
    
    def _snap(self, val):
        return round(val / self.grid_size) * self.grid_size
    
    def _is_h_free(self, y, x1, x2, check_nodes=True, from_node_idx=None, to_node_idx=None):
        y_key = self._snap(y)
        x1, x2 = min(x1, x2), max(x1, x2)
        safe_dist = 5 * self.scale
        
        if y_key in self.h_segments:
            for sx1, sx2, _ in self.h_segments[y_key]:
                if not (x2 <= sx1 - safe_dist or x1 >= sx2 + safe_dist):
                    return False
        
        if check_nodes:
            for i, rect in enumerate(self.node_rects):
                if from_node_idx is not None and i == from_node_idx: continue
                if to_node_idx is not None and i == to_node_idx: continue
                if rect["y1"] <= y <= rect["y2"]:
                    if not (x2 <= rect["x1"] or x1 >= rect["x2"]):
                        return False
        return True
    
    def _is_v_free(self, x, y1, y2, check_nodes=True, from_node_idx=None, to_node_idx=None):
        x_key = self._snap(x)
        y1, y2 = min(y1, y2), max(y1, y2)
        safe_dist = 5 * self.scale
        
        if x_key in self.v_segments:
            for sy1, sy2, _ in self.v_segments[x_key]:
                if not (y2 <= sy1 - safe_dist or y1 >= sy2 + safe_dist):
                    return False
        
        if check_nodes:
            for i, rect in enumerate(self.node_rects):
                if from_node_idx is not None and i == from_node_idx: continue
                if to_node_idx is not None and i == to_node_idx: continue
                if rect["x1"] <= x <= rect["x2"]:
                    if not (y2 <= rect["y1"] or y1 >= rect["y2"]):
                        return False
        return True
    
    def _can_direct_connect(self, x1, y1, x2, y2, from_idx, to_idx):
        min_x, max_x = min(x1, x2), max(x1, x2)
        for i, rect in enumerate(self.node_rects):
            if i == from_idx or i == to_idx: continue
            if rect["x1"] < max_x and rect["x2"] > min_x:
                if rect["y1"] <= y1 <= rect["y2"]:
                    return False
        return True
    
    def _is_label_pos_free(self, x, y, w=30, h=16):
        w, h = w * self.scale, h * self.scale
        for rect in self.label_rects:
            if not (x + w < rect["x1"] or x - w > rect["x2"] or
                    y + h < rect["y1"] or y - h > rect["y2"]):
                return False
        for rect in self.node_rects:
            if not (x + w < rect["x1"] or x - w > rect["x2"] or
                    y + h < rect["y1"] or y - h > rect["y2"]):
                return False
        return True
    
    def find_label_position(self, path):
        scale_off20 = 20 * self.scale
        scale_off10 = 10 * self.scale
        
        for i in range(len(path)):
            x, y = path[i]
            for offset_y in [0, -scale_off20, scale_off20]:
                test_y = y + offset_y
                if self._is_label_pos_free(x, test_y):
                    self.label_rects.append({"x1": x - scale_off20, "y1": test_y - scale_off10, "x2": x + scale_off20, "y2": test_y + scale_off10})
                    return (x, test_y)
        mid = len(path) // 2
        return path[mid] if path else (0, 0)
    
    def _mark_used(self, path, line_id):
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            if abs(y2 - y1) < 2:
                y_key = self._snap(y1)
                if y_key not in self.h_segments: self.h_segments[y_key] = []
                self.h_segments[y_key].append((min(x1, x2), max(x1, x2), line_id))
            elif abs(x2 - x1) < 2:
                x_key = self._snap(x1)
                if x_key not in self.v_segments: self.v_segments[x_key] = []
                self.v_segments[x_key].append((min(y1, y2), max(y1, y2), line_id))
    
    def _find_h_channel(self, base_y, x1, x2, direction=1):
        for offset in range(0, int(400 * self.scale), self.grid_size):
            test_y = base_y + offset * direction
            if self._is_h_free(test_y, x1, x2):
                return test_y
        return base_y + (250 * self.scale) * direction
    
    def _find_v_channel(self, base_x, y1, y2, direction=1):
        for offset in range(0, int(400 * self.scale), self.grid_size):
            test_x = base_x + offset * direction
            if self._is_v_free(test_x, y1, y2):
                return test_x
        return base_x + (250 * self.scale) * direction
    
    def route(self, from_node, to_node, path_type, from_idx=None, to_idx=None):
        self.line_count += 1
        
        # ✅ 使用實時縮放後的寬高 (使用 .get 確保安全)
        fw = from_node.get("width", 150)
        fh = from_node.get("height", 36)
        tw = to_node.get("width", 150)
        th = to_node.get("height", 36)
        
        x1 = from_node["x"] + fw
        y1 = from_node["y"] + fh // 2
        x2 = to_node["x"]
        y2 = to_node["y"] + th // 2
        
        path = [(x1, y1)]
        dx = x2 - x1
        off15 = 15 * self.scale
        off20 = 20 * self.scale
        
        # 1. 向右發展的情形
        if dx > 0:
            # 如果在同一行，嘗試直線連接
            if from_node.get("row") == to_node.get("row") and self._can_direct_connect(x1, y1, x2, y2, from_idx, to_idx):
                path.append((x2, y1))
            else:
                # 不同行或有障礙，使用三段式佈線 (H-V-H)
                # 分叉 (fork) 類型通常需要更早的轉折，讓視覺更像分支
                split_ratio = 0.3 if path_type == "fork" else 0.5
                mid_x = x1 + dx * split_ratio
                
                path.append((mid_x, y1))
                path.append((mid_x, y2))
                path.append((x2, y2))
        
        # 2. 向左發展的情形 (重試或跳轉)
        elif dx <= 0:
            off30 = 30 * self.scale
            off40 = 40 * self.scale
            off50 = 50 * self.scale
            
            if path_type == "loop":
                top_y = min(n["y"] for n in self.nodes) - off50
                channel_y = self._find_h_channel(top_y, min(x1, x2) - off30, max(x1, x2) + off30, -1)
            elif path_type == "failure":
                bottom_y = max(n["y"] + n.get("height", 36) for n in self.nodes) + off50
                channel_y = self._find_h_channel(bottom_y, min(x1, x2) - off30, max(x1, x2) + off30, 1)
            else:
                channel_y = self._find_h_channel(min(n["y"] for n in self.nodes) - off40, min(x1, x2) - off30, max(x1, x2) + off30, -1)
            
            exit_x = x1 + off20
            entry_x = x2 - off20
            path.append((exit_x, y1))
            path.append((exit_x, channel_y))
            path.append((entry_x, channel_y))
            path.append((entry_x, y2))
            path.append((x2, y2))
        
        # 3. 垂直發展的情形 (罕見)
        else:
            path.append((x2, y2))
            
        return path


class TextCommandEditor(tk.Toplevel):
    """文字指令式腳本編輯器"""
    
    def __init__(self, parent=None, script_path=None):
        super().__init__(parent)
        
        self.parent = parent
        self.script_path = script_path
        self.title("文字指令編輯器")
        self.geometry("1405x1095")  # 寬度+50，高度+100
        
        # 設定最小視窗尺寸，確保按鈕群不被遮住
        self.minsize(1405, 995)
        
        # 設定視窗圖標(與主程式相同)
        try:
            # 避免循環匯入 - 直接定義 get_icon_path 函數
            def get_icon_path():
                """取得圖示檔案路徑（打包後和開發環境通用）"""
                try:
                    if getattr(sys, 'frozen', False):
                        return os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
                    else:
                        if os.path.exists("umi_奶茶色.ico"):
                            return "umi_奶茶色.ico"
                        elif os.path.exists("../pic/umi_奶茶色.ico"):
                            return "../pic/umi_奶茶色.ico"
                        elif os.path.exists("../umi_奶茶色.ico"):
                            return "../umi_奶茶色.ico"
                        else:
                            return "umi_奶茶色.ico"
                except:
                    return "umi_奶茶色.ico"
            
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            pass  # 圖標設定失敗不影響功能
        
        # 預設按鍵持續時間 (毫秒)
        self.default_key_duration = 50
        
        # 初始化 original_settings（防止儲存時找不到屬性）
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
        
        # 圖片辨識相關資料夾
        self.images_dir = self._get_images_dir()
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 自訂模組資料夾
        self.modules_dir = self._get_modules_dir()
        os.makedirs(self.modules_dir, exist_ok=True)
        
        # 圖片編號計數器（自動命名 pic01, pic02...）
        self._pic_counter = self._get_next_pic_number()
        
        self._create_ui()
        
        # 刷新腳本列表
        self._refresh_script_list()
        
        # 如果有指定腳本路徑，載入它
        if self.script_path:
            script_name = os.path.splitext(os.path.basename(self.script_path))[0]
            self.script_var.set(script_name)
            self._load_script()
        
        # 確保編輯器視窗顯示並獲得焦點（但不強制置頂避免覆蓋問題）
        self.focus_set()
    
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
        """獲取下一個可用的圖片編號（pic01, pic02...）
        
        注意：這個函數只用於自動生成純數字編號的圖片名稱
        使用者可以自由命名圖片（pic王01、pic小怪等），不受此限制
        """
        if not os.path.exists(self.images_dir):
            return 1
        
        # 掃描現有圖片檔案，找出最大編號
        max_num = 0
        try:
            # 支援的圖片副檔名
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            
            for filename in os.listdir(self.images_dir):
                # 取得副檔名
                ext = os.path.splitext(filename)[1].lower()
                
                # 只處理圖片檔案且以 "pic" 開頭、後面直接接數字的檔案
                if ext in image_extensions and filename.startswith("pic"):
                    # 提取 "pic" 後面的部分
                    try:
                        # 例如 pic01.png -> 01, pic999.jpg -> 999
                        name_without_ext = os.path.splitext(filename)[0]
                        num_str = name_without_ext[3:]  # 移除 "pic" 前綴
                        
                        # 只處理純數字的情況（排除 pic王01、pic小怪 等）
                        if num_str.isdigit():
                            num = int(num_str)
                            max_num = max(max_num, num)
                    except:
                        continue
        except:
            pass
        
        return max_num + 1
    
    def _create_ui(self):
        """創建UI"""
        # 配置 ttk.Combobox 現代化樣式（不改變全局主題，避免影響主程式）
        self.editor_style = ttk.Style(self)
        # 不使用 theme_use，直接配置樣式以避免影響主程式
        self.editor_style.configure('Editor.TCombobox',
                       fieldbackground='#ffffff',
                       background='#f0f0f0',
                       foreground='#333333',
                       borderwidth=1,
                       relief='flat',
                       arrowsize=15,
                       padding=5)
        self.editor_style.map('Editor.TCombobox',
                       fieldbackground=[('readonly', '#ffffff')],
                       selectbackground=[('readonly', '#0078d7')],
                       selectforeground=[('readonly', '#ffffff')])
        
        # 頂部工具列
        toolbar = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # 腳本選單區域（不顯示"腳本:"文字）
        # 下拉選單
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.script_var, 
            width=25, 
            height=10,
            state="readonly", 
            font=font_tuple(9),
            style='Editor.TCombobox'
        )
        self.script_combo.pack(side="left", padx=5, pady=2)
        self.script_combo.bind("<<ComboboxSelected>>", self._on_script_selected)
        self.script_combo.bind("<Button-1>", self._on_combo_click)
        
        # 操作按鈕（移除圖片辨識，移到底部指令區）
        buttons = [
            ("重新載入", self._load_script, "#2196F3"),
            ("儲存", self._save_script, "#4CAF50")
        ]
        for text, cmd, color in buttons:
            tk.Button(toolbar, text=text, command=cmd, bg=color, fg="white", font=font_tuple(9), padx=15, pady=5).pack(side="left", padx=5)
        
        # ✅ 新增：指令說明按鈕（靠右對齊）
        tk.Button(
            toolbar, 
            text="指令說明", 
            command=self._show_command_reference, 
            bg="#FF9800", 
            fg="white", 
            font=font_tuple(9), 
            padx=15, 
            pady=5
        ).pack(side="right", padx=5)
        
        # 主編輯區 - 使用左右兩欄佈局
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左側大區: 按鈕區 + 模組預覽（對調後）
        left_big_frame = tk.Frame(main_frame, width=450)
        left_big_frame.pack(side="left", fill="both", expand=False)
        left_big_frame.pack_propagate(False)
        
        # 左上: 快速指令按鈕區（移到左側）
        left_frame = tk.Frame(left_big_frame)
        left_frame.pack(fill="both", expand=True)
        
        # 快速指令按鈕區
        self._create_command_buttons_in_frame(left_frame)
        
        # 左下: 自訂模組管理（移到左側下方）
        left_bottom_frame = tk.Frame(left_big_frame, bg="#f5f5f5", relief="groove", bd=2, height=380)
        left_bottom_frame.pack(fill="both", expand=False, pady=(5, 0))
        left_bottom_frame.pack_propagate(False)
        
        tk.Label(
            left_bottom_frame,
            text="自訂模組",
            font=font_tuple(10),
            bg="#f5f5f5"
        ).pack(anchor="w", padx=10, pady=5)
        
        # 按鈕列
        module_btn_frame = tk.Frame(left_bottom_frame, bg="#f5f5f5")
        module_btn_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            module_btn_frame,
            text="儲存新模組",
            command=self._save_new_module_inline,
            bg="#4CAF50",
            fg="white",
            font=font_tuple(9),
            padx=10,
            pady=3
        ).pack(side="left", padx=2)
        
        tk.Button(
            module_btn_frame,
            text="插入模組",
            command=self._insert_module_inline,
            bg="#2196F3",
            fg="white",
            font=font_tuple(9),
            padx=10,
            pady=3
        ).pack(side="left", padx=2)
        
        tk.Button(
            module_btn_frame,
            text="刪除",
            command=self._delete_module_inline,
            bg="#F44336",
            fg="white",
            font=font_tuple(9),
            padx=10,
            pady=3
        ).pack(side="left", padx=2)
        
        # 模組列表
        module_list_frame = tk.Frame(left_bottom_frame, bg="#f5f5f5")
        module_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        tk.Label(
            module_list_frame,
            text="已儲存的模組 (雙擊插入):",
            font=font_tuple(9),
            bg="#f5f5f5"
        ).pack(anchor="w", pady=(0, 5))
        
        list_container = tk.Frame(module_list_frame)
        list_container.pack(fill="both", expand=True)
        
        list_scrollbar = tk.Scrollbar(list_container, bg="#2d2d30", troughcolor="#1e1e1e", width=12)
        list_scrollbar.pack(side="right", fill="y")
        
        self.module_listbox = tk.Listbox(
            list_container,
            font=font_tuple(10),
            yscrollcommand=list_scrollbar.set,
            width=35
        )
        self.module_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar.config(command=self.module_listbox.yview)
        
        self.module_listbox.bind("<Double-Button-1>", lambda e: self._insert_module_inline())
        self.module_listbox.bind("<<ListboxSelect>>", self._on_module_selected_inline)
        
        # 載入模組列表
        self._load_modules_inline()
        
        # 右側大區: 編輯器 + 模組管理（對調後）
        right_big_frame = tk.Frame(main_frame)
        right_big_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # 右上: 文字編輯器（移到右側）
        right_frame = tk.Frame(right_big_frame)
        right_frame.pack(fill="both", expand=True)
        
        # 新增：摺疊軌跡顯示勾選框和圖形模式開關
        trajectory_control = tk.Frame(right_frame)
        trajectory_control.pack(fill="x", pady=(0, 5))
        
        self.simplify_display_var = tk.BooleanVar(value=True)
        simplify_check = tk.Checkbutton(
            trajectory_control,
            text="摺疊軌跡顯示",
            variable=self.simplify_display_var,
            command=self._toggle_trajectory_display,
            font=font_tuple(9)
        )
        simplify_check.pack(side="left", padx=5)
        
        # 圖形模式開關 (新的 Workflow 流程圖)
        self.workflow_mode_var = tk.BooleanVar(value=False)
        workflow_mode_check = tk.Checkbutton(
            trajectory_control,
            text="圖形模式",
            variable=self.workflow_mode_var,
            command=self._toggle_workflow_mode,
            font=font_tuple(9)
        )
        workflow_mode_check.pack(side="left", padx=15)
        
        # 使用 LINE Seed 字體
        editor_font = ("LINE Seed TW", 10) if LINE_SEED_FONT_LOADED else font_tuple(10, monospace=True)
        
        # 創建編輯器容器（用於切換文字/畫布模式）
        self.editor_container = tk.Frame(right_frame)
        self.editor_container.pack(fill="both", expand=True)
        
        # 文字編輯器
        self.text_editor = scrolledtext.ScrolledText(
            self.editor_container,
            font=editor_font,
            wrap="none",
            bg="#1e1e1e",           # ✅ VS Code 深色背景
            fg="#d4d4d4",           # ✅ VS Code 淺灰色（非指令文字）
            insertbackground="white",
            selectbackground="#264f78",  # ✅ VS Code 選取背景色
            selectforeground="white",
            undo=True,
            maxundo=-1
        )
        self.text_editor.pack(fill="both", expand=True)
        
        # 綁定 Ctrl+A 全選功能
        self.text_editor.bind("<Control-a>", self._select_all_text)
        self.text_editor.bind("<Control-A>", self._select_all_text)
        
        # 畫布編輯器（初始隱藏）
        self.canvas_frame = tk.Frame(self.editor_container, bg="#252526")
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="#252526",
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # 畫布資料結構
        self.canvas_nodes = []  # 儲存所有節點
        self.canvas_connections = []  # 儲存所有連接線
        self.selected_node = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.canvas_mode = False  # 當前是否為畫布模式
        
        # 畫布縮放相關
        self.canvas_scale = 1.0  # 當前縮放比例
        self.canvas_offset_x = 0  # X軸偏移
        self.canvas_offset_y = 0  # Y軸偏移
        self.pan_data = {"x": 0, "y": 0, "active": False}  # 平移資料
        
        # 畫布事件綁定
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._show_canvas_context_menu)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_canvas_zoom)  # 滾輪縮放
        self.canvas.bind("<Button-2>", self._on_canvas_pan_start)  # 中鍵平移開始
        self.canvas.bind("<B2-Motion>", self._on_canvas_pan_move)  # 中鍵平移中
        self.canvas.bind("<ButtonRelease-2>", self._on_canvas_pan_end)  # 中鍵平移結束
        
        # === 新增 Workflow 流程圖畫布 ===
        self.workflow_frame = tk.Frame(self.editor_container, bg="#1e1e1e")
        self.workflow_canvas = tk.Canvas(
            self.workflow_frame,
            bg="#1e1e1e",
            highlightthickness=0
        )
        
        # 添加滾動條
        workflow_v_scroll = tk.Scrollbar(self.workflow_frame, orient="vertical", command=self.workflow_canvas.yview)
        workflow_h_scroll = tk.Scrollbar(self.workflow_frame, orient="horizontal", command=self.workflow_canvas.xview)
        self.workflow_canvas.configure(yscrollcommand=workflow_v_scroll.set, xscrollcommand=workflow_h_scroll.set)
        
        workflow_v_scroll.pack(side="right", fill="y")
        workflow_h_scroll.pack(side="bottom", fill="x")
        self.workflow_canvas.pack(side="left", fill="both", expand=True)
        
        # Workflow 資料結構
        self.workflow_nodes = {}  # {label_name: node_data}
        self.workflow_connections = []  # [(from_label, to_label, connection_type)]
        self.workflow_mode = False
        self.workflow_scale = 1.0
        self.workflow_dragging_node = None  # 正在拖移的節點
        self.workflow_drag_start_x = 0
        self.workflow_drag_start_y = 0
        self.workflow_pan_start_x = 0  # 畫布拖移起點
        self.workflow_pan_start_y = 0
        self.workflow_is_panning = False
        self.workflow_tooltip = None  # 💬 浮動提示框
        
        # 畫布事件綁定
        # 👆 啟用畫布拖移，但只能拖移畫布
        self.workflow_canvas.bind("<Button-1>", self._on_workflow_canvas_click)
        self.workflow_canvas.bind("<B1-Motion>", self._on_workflow_canvas_drag)
        self.workflow_canvas.bind("<ButtonRelease-1>", self._on_workflow_canvas_release)
        self.workflow_canvas.bind("<Button-3>", self._show_workflow_context_menu)
        self.workflow_canvas.bind("<MouseWheel>", self._on_workflow_zoom)
        
        # ✅ 設定語法高亮標籤 (VS Code Dark+ 配色方案)
        self.text_editor.tag_config("syntax_symbol", foreground="#d4d4d4")      # 淺灰色 - 符號（,、>等）
        self.text_editor.tag_config("syntax_time", foreground="#ce9178")        # 橘色 - 時間參數
        self.text_editor.tag_config("syntax_label", foreground="#4ec9b0")       # 青綠色 - 標籤
        self.text_editor.tag_config("syntax_keyboard", foreground="#9cdcfe")    # 淺藍色 - 鍵盤操作
        self.text_editor.tag_config("syntax_mouse", foreground="#569cd6")       # 藍色 - 滑鼠座標
        self.text_editor.tag_config("syntax_image", foreground="#4ec9b0")       # 青綠色 - 圖片辨識
        self.text_editor.tag_config("syntax_condition", foreground="#c586c0")   # 紫色 - 條件判斷
        self.text_editor.tag_config("syntax_ocr", foreground="#4ec9b0")         # 青綠色 - OCR 文字
        self.text_editor.tag_config("syntax_delay", foreground="#dcdcaa")       # 淺黃色 - 延遲控制
        self.text_editor.tag_config("syntax_flow", foreground="#c586c0")        # 紫色 - 流程控制
        self.text_editor.tag_config("syntax_picname", foreground="#ce9178")     # 橘色 - 圖片名稱
        self.text_editor.tag_config("syntax_comment", foreground="#6a9955")     # 綠色 - 註解
        self.text_editor.tag_config("syntax_module_ref", foreground="#ffd700", font=font_tuple(10, "bold"))  # 金色 - 模組引用
        
        # ✨ 新增：軌跡摺疊相關標籤和配置
        self.text_editor.tag_config("trajectory_summary", foreground="#00BFFF", font=font_tuple(10, "bold"))
        self.text_editor.tag_config("trajectory_hidden", elide=True)  # elide=True 會隱藏文字
        self.text_editor.tag_config("trajectory_clickable", foreground="#00BFFF", underline=1)
        
        # ✨ 新增：標籤範圍摺疊相關標籤和配置
        self.text_editor.tag_config("label_foldable", foreground="#4ec9b0", font=font_tuple(10, "bold"), underline=1)
        self.text_editor.tag_config("label_end", foreground="#6a9955", font=font_tuple(9))  # 標籤結束標記
        self.text_editor.tag_config("label_content_hidden", elide=True)  # 隱藏標籤內容
        
        # 追蹤摺疊狀態 {行號: 是否已摺疊}
        self.trajectory_fold_state = {}
        self.label_fold_state = {}  # 標籤摺疊狀態 {標籤名: 是否已摺疊}
        
        # 綁定內容變更事件以觸發語法高亮
        self.text_editor.bind("<<Modified>>", self._on_text_modified)
        
        # 綁定滑鼠點擊事件以處理摺疊/展開
        self.text_editor.bind("<Button-1>", self._on_editor_click)
        
        # 綁定右鍵選單
        self.text_editor.bind("<Button-3>", self._show_context_menu)
        
        # 右下: 模組內容預覽（移到右側下方）
        module_frame = tk.Frame(right_big_frame, bg="#f5f5f5", height=380)
        module_frame.pack(fill="both", expand=False, pady=(5, 0))
        module_frame.pack_propagate(False)
        
        tk.Label(
            module_frame,
            text="模組內容預覽",
            font=font_tuple(10),
            bg="#f5f5f5"
        ).pack(anchor="w", padx=5, pady=5)
        
        self.module_preview = scrolledtext.ScrolledText(
            module_frame,
            font=font_tuple(10, monospace=True),
            wrap="none",
            state="disabled",
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.module_preview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 為模組預覽框配置語法高亮標籤
        self.module_preview.tag_config("syntax_symbol", foreground="#d4d4d4")
        self.module_preview.tag_config("syntax_time", foreground="#ce9178")
        self.module_preview.tag_config("syntax_label", foreground="#4ec9b0")
        self.module_preview.tag_config("syntax_keyboard", foreground="#9cdcfe")
        self.module_preview.tag_config("syntax_mouse", foreground="#569cd6")
        self.module_preview.tag_config("syntax_image", foreground="#4ec9b0")
        self.module_preview.tag_config("syntax_condition", foreground="#c586c0")
        self.module_preview.tag_config("syntax_ocr", foreground="#4ec9b0")
        self.module_preview.tag_config("syntax_delay", foreground="#dcdcaa")
        self.module_preview.tag_config("syntax_flow", foreground="#c586c0")
        self.module_preview.tag_config("syntax_picname", foreground="#ce9178")
        self.module_preview.tag_config("syntax_comment", foreground="#6a9955")
        
        # 底部狀態列
        self.status_label = tk.Label(
            self,
            text="就緒",
            font=font_tuple(9),
            bg="#e8f5e9",
            fg="#2e7d32",
            anchor="w",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill="x", side="bottom")
    
    def _show_message(self, title, message, msg_type="info"):
        """顯示自訂訊息對話框，不會改變父視窗位置"""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)  # 設定為編輯器的子視窗
        dialog.grab_set()  # 模態對話框
        
        # 警告/錯誤/資訊對應的文字符號
        icon_map = {"info": "[資訊]", "warning": "[警告]", "error": "[錯誤]"}
        color_map = {"info": "#1976d2", "warning": "#f57c00", "error": "#d32f2f"}
        
        icon = icon_map.get(msg_type, "[資訊]")
        color = color_map.get(msg_type, "#1976d2")
        
        # 主框架
        frame = tk.Frame(dialog, bg="white", padx=20, pady=15)
        frame.pack(fill="both", expand=True)
        
        # 標題列（圖示+訊息）
        msg_frame = tk.Frame(frame, bg="white")
        msg_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        icon_label = tk.Label(msg_frame, text=icon, font=font_tuple(20), bg="white", fg=color)
        icon_label.pack(side="left", padx=(0, 10))
        
        msg_label = tk.Label(msg_frame, text=message, font=font_tuple(10), bg="white", fg="#333", justify="left", wraplength=300)
        msg_label.pack(side="left", fill="both", expand=True)
        
        # 確認按鈕
        btn = tk.Button(frame, text="確定", font=font_tuple(10), bg=color, fg="white", 
                       command=dialog.destroy, relief="flat", padx=20, pady=5, cursor="hand2")
        btn.pack()
        
        # 置中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
    
    def _show_confirm(self, title, message):
        """顯示確認對話框（是/否）"""
        result = [False]  # 使用列表來儲存結果（可變對象）
        
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.grab_set()
        
        # 主框架
        frame = tk.Frame(dialog, bg="white", padx=20, pady=15)
        frame.pack(fill="both", expand=True)
        
        # 訊息
        msg_frame = tk.Frame(frame, bg="white")
        msg_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        icon_label = tk.Label(msg_frame, text="[確認]", font=font_tuple(14, "bold"), bg="white", fg="#f57c00")
        icon_label.pack(side="left", padx=(0, 10))
        
        msg_label = tk.Label(msg_frame, text=message, font=font_tuple(10), bg="white", fg="#333", justify="left", wraplength=300)
        msg_label.pack(side="left", fill="both", expand=True)
        
        # 按鈕列
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack()
        
        def on_yes():
            result[0] = True
            dialog.destroy()
        
        def on_no():
            result[0] = False
            dialog.destroy()
        
        yes_btn = tk.Button(btn_frame, text="是", font=font_tuple(10), bg="#4caf50", fg="white",
                           command=on_yes, relief="flat", padx=20, pady=5, cursor="hand2")
        yes_btn.pack(side="left", padx=5)
        
        no_btn = tk.Button(btn_frame, text="否", font=font_tuple(10), bg="#757575", fg="white",
                          command=on_no, relief="flat", padx=20, pady=5, cursor="hand2")
        no_btn.pack(side="left", padx=5)
        
        # 置中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
        return result[0]
    
    def _on_editor_click(self, event):
        """處理編輯器點擊事件（用於軌跡和標籤展開/收合）"""
        try:
            # 獲取點擊位置的索引
            index = self.text_editor.index(f"@{event.x},{event.y}")
            line_start = self.text_editor.index(f"{index} linestart")
            line_end = self.text_editor.index(f"{index} lineend")
            line_text = self.text_editor.get(line_start, line_end)
            
            # 檢查是否點擊了軌跡摘要行
            if line_text.startswith("# [軌跡]"):
                line_num = int(index.split('.')[0])
                self._toggle_trajectory_fold(line_num)
                return "break"  # 阻止預設行為
            
            # 檢查是否點擊了標籤範圍
            if line_text.startswith("#b"):
                label_name = line_text[2:].strip()
                self._toggle_label_fold(label_name)
                return "break"
        except Exception as e:
            pass  # 忽略錯誤，不影響正常編輯
    
    def _select_all_text(self, event):
        """全選文字內容 (Ctrl+A)"""
        self.text_editor.tag_remove("sel", "1.0", "end")
        self.text_editor.tag_add("sel", "1.0", "end")
        return "break"  # 阻止 ttkbootstrap 的預設處理
    
    def _toggle_trajectory_fold(self, summary_line):
        """切換指定軌跡的摺疊狀態"""
        try:
            # 找到對應的軌跡區塊
            start_line = summary_line + 1
            end_line = None
            
            # 搜尋軌跡結束標記
            total_lines = int(self.text_editor.index('end-1c').split('.')[0])
            for i in range(start_line, total_lines + 1):
                line_text = self.text_editor.get(f"{i}.0", f"{i}.0 lineend")
                if line_text.strip() == "# [軌跡結束]":
                    end_line = i
                    break
            
            if not end_line:
                return  # 找不到結束標記
            
            # 切換摺疊狀態
            is_folded = self.trajectory_fold_state.get(summary_line, False)
            
            if is_folded:
                # 展開：移除 elide 標籤
                self.text_editor.tag_remove("trajectory_hidden", f"{start_line}.0", f"{end_line + 1}.0")
                # 更新摘要文字為 [收合]
                self._update_trajectory_summary_text(summary_line, "[收合]")
                self.trajectory_fold_state[summary_line] = False
                # ✅ 展開後重新套用語法高亮
                self._apply_syntax_highlighting()
            else:
                # 收合：添加 elide 標籤
                self.text_editor.tag_add("trajectory_hidden", f"{start_line}.0", f"{end_line + 1}.0")
                # 更新摘要文字為 [展開]
                self._update_trajectory_summary_text(summary_line, "[展開]")
                self.trajectory_fold_state[summary_line] = True
                
        except Exception as e:
            print(f"切換軌跡摺疊失敗: {e}")
    
    def _update_trajectory_summary_text(self, line_num, action_text):
        """更新軌跡摘要行的展開/收合文字"""
        try:
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.0 lineend"
            line_text = self.text_editor.get(line_start, line_end)
            
            # 替換 [展開] 或 [收合]
            import re
            new_text = re.sub(r'\[(展開|收合)\]', f'[{action_text}]', line_text)
            
            # ✅ 先移除舊標籤，避免標籤累積
            self.text_editor.tag_remove("trajectory_clickable", line_start, line_end)
            
            # 更新文字
            self.text_editor.delete(line_start, line_end)
            self.text_editor.insert(line_start, new_text)
            
            # 重新套用樣式
            self.text_editor.tag_add("trajectory_clickable", line_start, line_end)
        except Exception as e:
            print(f"更新摘要文字失敗: {e}")
    
    def _toggle_label_fold(self, label_name):
        """切換標籤範圍的摺疊狀態"""
        try:
            # 找到標籤起始和結束行
            start_line = None
            end_line = None
            
            total_lines = int(self.text_editor.index('end-1c').split('.')[0])
            
            # 搜尋標籤範圍
            for i in range(1, total_lines + 1):
                line_text = self.text_editor.get(f"{i}.0", f"{i}.0 lineend").strip()
                
                if line_text == f"#b{label_name}":
                    start_line = i
                elif line_text == f"#/{label_name}" and start_line:
                    end_line = i
                    break
            
            if not start_line or not end_line:
                return  # 找不到完整的標籤範圍
            
            # 切換摺疊狀態
            is_folded = self.label_fold_state.get(label_name, False)
            
            if is_folded:
                # 展開：移除 elide 標籤
                self.text_editor.tag_remove("label_content_hidden", f"{start_line + 1}.0", f"{end_line}.0")
                self.label_fold_state[label_name] = False
                # ✅ 展開後重新套用語法高亮
                self._apply_syntax_highlighting()
            else:
                # 收合：添加 elide 標籤
                self.text_editor.tag_add("label_content_hidden", f"{start_line + 1}.0", f"{end_line}.0")
                self.label_fold_state[label_name] = True
                
        except Exception as e:
            print(f"切換標籤摺疊失敗: {e}")
    
    def _update_status(self, text, status_type="info"):
        """更新狀態列，支持不同類型的狀態顯示"""
        status_colors = {
            "info": {"bg": "#e3f2fd", "fg": "#1976d2"},
            "success": {"bg": "#e8f5e9", "fg": "#2e7d32"},
            "warning": {"bg": "#fff3e0", "fg": "#e65100"},
            "error": {"bg": "#ffebee", "fg": "#c62828"}
        }
        
        colors = status_colors.get(status_type, status_colors["info"])
        self.status_label.config(text=text, bg=colors["bg"], fg=colors["fg"])
    
    def _toggle_trajectory_display(self):
        """切換軌跡顯示模式（簡化/完整）"""
        # 清空摺疊狀態
        self.trajectory_fold_state = {}
        # 重新載入腳本以套用新的顯示模式
        self._load_script()
    
    def _toggle_workflow_mode(self):
        """切換文字/Workflow流程圖模式"""
        if self.workflow_mode_var.get():
            # 切換到 Workflow 模式
            self._switch_to_workflow_mode()
        else:
            # 切換回文字模式
            self._switch_to_text_mode_from_workflow()
    
    def _switch_to_workflow_mode(self):
        """切換到 Workflow 流程圖模式"""
        try:
            # 獲取文字內容
            text_content = self.text_editor.get("1.0", tk.END).strip()
            if not text_content:
                self._update_status("沒有內容可以轉換", "warning")
                self.workflow_mode_var.set(False)
                return
            
            # 解析文字指令生成流程圖
            self._parse_and_draw_workflow(text_content)
            
            # 隱藏文字編輯器，顯示 Workflow 畫布
            self.text_editor.pack_forget()
            self.workflow_frame.pack(fill="both", expand=True)
            
            self.workflow_mode = True
            self._update_status("已切換到圖形模式", "success")
            
        except Exception as e:
            self._update_status(f"切換失敗: {str(e)}", "error")
            self.workflow_mode_var.set(False)
    
    def _switch_to_text_mode_from_workflow(self):
        """從 Workflow 模式切換回文字模式"""
        # 隱藏 Workflow 畫布，顯示文字編輯器
        self.workflow_frame.pack_forget()
        self.text_editor.pack(fill="both", expand=True)
        
        self.workflow_mode = False
        self._update_status("已切換回文字模式", "success")
    
    def _toggle_canvas_mode(self):
        """切換文字/畫布模式"""
        if self.canvas_mode_var.get():
            # 切換到畫布模式
            self._switch_to_canvas_mode()
        else:
            # 切換到文字模式
            self._switch_to_text_mode()
    
    def _switch_to_canvas_mode(self):
        """切換到畫布模式"""
        # 轉換文字指令為畫布節點
        text_content = self.text_editor.get("1.0", tk.END).strip()
        if text_content:
            self._convert_text_to_canvas(text_content)
        
        # 隱藏文字編輯器，顯示畫布
        self.text_editor.pack_forget()
        self.canvas_frame.pack(fill="both", expand=True)
        
        # 繪製網格
        self._draw_grid()
        
        self.canvas_mode = True
        self._update_status("已切換到圖形模式", "success")
    
    def _switch_to_text_mode(self):
        """切換到文字模式"""
        # 轉換畫布節點為文字指令
        if self.canvas_nodes:
            self._convert_canvas_to_text()
        
        # 隱藏畫布，顯示文字編輯器
        self.canvas_frame.pack_forget()
        self.text_editor.pack(fill="both", expand=True)
        
        self.canvas_mode = False
        self._update_status("已切換到文字模式", "success")
    
    def _draw_grid(self):
        """繪製畫布網格（已取消格線，保持深色背景）"""
        # 清除現有網格
        self.canvas.delete("grid")
        # 不再繪製格線，僅保持深色背景
    
    def _on_canvas_configure(self, event):
        """畫布大小改變事件"""
        self._draw_grid()
    
    def _convert_text_to_canvas(self, text_content):
        """將文字指令轉換為畫布節點（n8n 風格左到右布局）"""
        # 清空現有節點
        self.canvas.delete("all")
        self.canvas_nodes = []
        self.canvas_connections = []
        
        lines = text_content.split('\n')
        
        # 解析層級結構
        parsed_structure = self._parse_marker_structure(lines)
        
        # === n8n 風格左到右布局 ===
        # 節點尺寸
        node_width = 200
        node_height = 70
        
        # 間距設定
        horizontal_gap = 80   # 節點之間的水平間距
        vertical_gap = 100    # 分支之間的垂直間距
        start_x = 80          # 起始 X 位置
        start_y = 120         # 起始 Y 位置（為分支留出空間）
        
        # 追蹤當前位置
        current_x = start_x
        current_y = start_y
        
        # 追蹤分支結構
        branch_stack = []  # 用於追蹤分支點
        max_y = start_y    # 追蹤最大 Y 值，用於新分支
        
        # 解析並繪製節點
        for item in parsed_structure:
            if item['type'] == 'marker':
                # 標記容器 - 作為一個大節點處理
                marker_name = item['name']
                children = item['children']
                
                # 繪製標記容器
                container_height = self._draw_marker_container(item, current_x, current_y)
                
                # 更新位置（向右移動）
                current_x += node_width + horizontal_gap + 50
                max_y = max(max_y, current_y + container_height)
                
            else:
                # 單獨的指令
                line = item['line'].strip()
                if not line:
                    continue
                
                # 跳過分支跳轉指令（>>#label 或 >>>#label），它們只用於連線
                if line.startswith('>>'):
                    continue
                
                color = self._get_command_color(line)
                display_text = self._get_command_display_text(line)
                
                # 創建節點
                self._create_canvas_node(display_text, color, current_x, current_y, original_command=line)
                
                # 更新位置（向右移動）
                current_x += node_width + horizontal_gap
                
                # 如果超過某個寬度，換行（防止無限寬）
                if current_x > 1200:
                    current_x = start_x
                    current_y = max_y + vertical_gap
                    max_y = current_y
        
        # 建立分支連接（在所有節點繪製完成後）
        self._create_branch_connections()
        
        # 調整畫布滾動區域
        bbox = self.canvas.bbox("all")
        if bbox:
            # 增加一些邊距
            padding = 100
            self.canvas.configure(scrollregion=(
                bbox[0] - padding,
                bbox[1] - padding,
                bbox[2] + padding,
                bbox[3] + padding
            ))
    
    def _parse_marker_structure(self, lines):
        """解析標記層級結構
        返回: [{'type': 'marker', 'name': '#mm', 'children': [...]}, 
               {'type': 'command', 'line': '...'}]
        """
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 跳過空行和軌跡標記
            if not stripped or stripped.startswith('# [軌跡]') or stripped.startswith('# [軌跡結束]'):
                i += 1
                continue
            
            # 檢查是否是標記（#開頭，且只有一個>）
            if stripped.startswith('#') and not stripped.startswith('##'):
                # 這是一個標記
                marker_name = stripped
                children = []
                i += 1
                
                # 收集標記內的所有子元素（以>開頭，且縮排比標記多）
                while i < len(lines):
                    child_line = lines[i]
                    child_stripped = child_line.strip()
                    
                    # 空行跳過
                    if not child_stripped:
                        i += 1
                        continue
                    
                    # 檢查是否是標記的子元素（>開頭且只有一個>）
                    if child_stripped.startswith('>') and not child_stripped.startswith('>>'):
                        children.append(child_stripped)
                        i += 1
                    else:
                        # 遇到非子元素，退出
                        break
                
                result.append({
                    'type': 'marker',
                    'name': marker_name,
                    'children': children
                })
            else:
                # 普通指令
                result.append({
                    'type': 'command',
                    'line': line
                })
                i += 1
        
        return result
    
    def _create_branch_connections(self):
        """建立分支連接（處理 >>#label 和 >>>#label）"""
        # 解析當前的文字內容以找到分支關係
        text_content = self.text_editor.get("1.0", tk.END).strip()
        lines = text_content.split('\n')
        
        # 建立標籤名到節點索引的映射
        label_to_node = {}
        for idx, node in enumerate(self.canvas_nodes):
            cmd = node.get("original_command", node.get("command", ""))
            if cmd.startswith('#') and not cmd.startswith('##'):
                # 這是一個標籤，提取標籤名
                label_name = cmd.strip()
                label_to_node[label_name] = idx
        
        # 查找分支指令並建立連接
        i = 0
        current_marker = None
        current_marker_has_condition = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 追蹤當前標籤
            if line.startswith('#') and not line.startswith('##'):
                current_marker = line
                current_marker_has_condition = False
                
            # 檢查標籤內是否有條件判斷指令
            elif current_marker and line.startswith('>'):
                # 檢查是否是條件判斷類型的指令
                if any(keyword in line for keyword in ['>辨識>', '>if>', '>if文字>', '>if變數>', '>if全部存在>', '>if任一存在>', '>隨機執行>']):
                    current_marker_has_condition = True
            
            # 檢查是否是分支指令
            elif line.startswith('>>#') or line.startswith('>>>#'):
                # 解析目標標籤
                target_label = '#' + line.split('#', 1)[1].split(',')[0].split('*')[0].strip()
                
                # 找到目標節點
                if target_label in label_to_node:
                    target_idx = label_to_node[target_label]
                    
                    # 找到當前標籤的節點
                    if current_marker and current_marker in label_to_node:
                        source_idx = label_to_node[current_marker]
                        
                        # 判斷是成功分支還是失敗分支
                        if line.startswith('>>#'):
                            self._connect_nodes(source_idx, target_idx, label="成功")
                        else:  # >>>#
                            self._connect_nodes(source_idx, target_idx, label="失敗")
            
            i += 1
        
        # 如果沒有找到任何分支連接，建立順序連接作為備用
        if not self.canvas_connections and len(self.canvas_nodes) > 1:
            for i in range(len(self.canvas_nodes) - 1):
                self._connect_nodes(i, i + 1)
    
    def _draw_marker_container(self, marker_item, x, y):
        """繪製標記容器（n8n 風格）
        包含標記名和子元素，支援左到右布局
        返回: 容器高度
        """
        marker_name = marker_item['name']
        children = marker_item['children']
        
        # n8n 風格尺寸
        header_height = 35  # 標記名標題高度
        child_height = 40   # 每個子元素高度
        padding = 10        # 內邊距
        spacing = 5         # 子元素間距
        icon_size = 28      # 圖示大小
        port_radius = 6     # 連接點半徑
        
        # 計算容器尺寸
        total_child_height = len(children) * (child_height + spacing) if children else 20
        container_height = header_height + total_child_height + padding * 2
        container_width = 200
        
        # 繪製陰影
        shadow = self.canvas.create_rectangle(
            x + 3, y + 3,
            x + container_width + 3, y + container_height + 3,
            fill="#0a0a0a",
            outline="",
            tags=("shadow", "marker_shadow")
        )
        
        # 繪製容器外框（圓角矩形）
        container_rect = self._create_rounded_rectangle(
            x, y,
            x + container_width, y + container_height,
            radius=8,
            fill="#2d2d30",
            outline="#00bcd4",  # 青色邊框
            width=2,
            tags=("marker_container",)
        )
        
        # 繪製標題區域背景
        header_bg = self.canvas.create_rectangle(
            x + 2, y + 2,
            x + container_width - 2, y + header_height,
            fill="#1e1e1e",
            outline="",
            tags=("marker_header",)
        )
        
        # 繪製圖示圓形
        icon_x = x + padding + icon_size // 2
        icon_y = y + header_height // 2
        
        icon_bg = self.canvas.create_oval(
            icon_x - icon_size // 2, icon_y - icon_size // 2,
            icon_x + icon_size // 2, icon_y + icon_size // 2,
            fill="#4ec9b0",  # 青綠色
            outline="",
            tags=("marker_icon",)
        )
        
        # 繪製圖示符號
        icon_text = self.canvas.create_text(
            icon_x, icon_y,
            text="#",
            fill="white",
            font=font_tuple(12, "bold"),
            tags=("marker_icon_text",)
        )
        
        # 繪製標記名（在圖示右側）
        marker_text = self.canvas.create_text(
            x + padding + icon_size + 10,
            y + header_height // 2,
            text=marker_name,
            fill="#4ec9b0",
            font=font_tuple(10, "bold"),
            anchor="w",
            tags=("marker_name",)
        )
        
        # 繪製輸入連接點（左側）
        input_port_y = y + container_height // 2
        input_port = self.canvas.create_oval(
            x - port_radius, input_port_y - port_radius,
            x + port_radius, input_port_y + port_radius,
            fill="#1e1e1e",
            outline="#00bcd4",
            width=2,
            tags=("marker_input_port",)
        )
        
        # 繪製輸出連接點（右側）
        output_port = self.canvas.create_oval(
            x + container_width - port_radius, input_port_y - port_radius,
            x + container_width + port_radius, input_port_y + port_radius,
            fill="#1e1e1e",
            outline="#00bcd4",
            width=2,
            tags=("marker_output_port",)
        )
        
        # 保存標記容器作為一個特殊節點
        marker_node = {
            "rect": container_rect,
            "text": marker_text,
            "shadow": shadow,
            "container_rect": container_rect,
            "header_bg": header_bg,
            "icon_bg": icon_bg,
            "icon_text": icon_text,
            "marker_text": marker_text,
            "input_port": input_port,
            "output_port": output_port,
            "command": marker_name,
            "original_command": marker_name,
            "color": "#4ec9b0",
            "x": x,
            "y": y,
            "width": container_width,
            "height": container_height,
            "is_marker": True,
            "marker_children": [],
            "child_elements": []
        }
        
        # 繪製子元素
        child_y = y + header_height + padding
        for i, child in enumerate(children):
            color = self._get_command_color(child)
            display_text = self._get_command_display_text(child)
            
            # 子元素框
            child_x = x + padding
            child_width = container_width - padding * 2
            
            child_rect = self.canvas.create_rectangle(
                child_x, child_y,
                child_x + child_width, child_y + child_height,
                fill=color,
                outline="#555555",
                width=1,
                tags=("marker_child",)
            )
            
            child_text_elem = self.canvas.create_text(
                child_x + 8,
                child_y + child_height // 2,
                text=display_text[:25] + "..." if len(display_text) > 25 else display_text,
                fill="white",
                font=font_tuple(8),
                anchor="w",
                tags=("marker_child_text",)
            )
            
            # 保存到標記節點的子元素列表
            marker_node["marker_children"].append(child)
            marker_node["child_elements"].append({
                "rect": child_rect,
                "text": child_text_elem,
                "x": child_x,
                "y": child_y
            })
            
            child_y += child_height + spacing
        
        # 將標記節點加入節點列表
        self.canvas_nodes.append(marker_node)
        
        return container_height
    
    def _get_command_color(self, command):
        """根據指令類型返回對應的顏色（與VS Code語法高亮一致）"""
        # 註解
        if command.startswith('#'):
            return "#6a9955"
        
        # 滑鼠操作（藍色系）
        if command.startswith('>'):
            if '移動至' in command:
                return "#569cd6"  # syntax_mouse
            elif '點擊' in command:
                return "#569cd6"  # syntax_mouse
            elif '拖曳' in command:
                return "#569cd6"  # syntax_mouse
            elif '滾輪' in command:
                return "#569cd6"  # syntax_mouse
            return "#569cd6"
        
        # 鍵盤操作（淺藍色）
        if command.startswith('@'):
            return "#9cdcfe"  # syntax_keyboard
        
        # 等待延遲（淺黃色）
        if command.startswith('等待'):
            return "#dcdcaa"  # syntax_delay
        
        # 標籤（青綠色）
        if command.startswith('標籤:'):
            return "#4ec9b0"  # syntax_label
        
        # 圖片辨識（青綠色）
        if command.startswith('找圖'):
            return "#4ec9b0"  # syntax_image
        
        # OCR文字（青綠色）
        if command.startswith('找字'):
            return "#4ec9b0"  # syntax_ocr
        
        # 流程控制（紫色）
        if '條件判斷' in command or '迴圈' in command or '如果' in command or '否則' in command:
            return "#c586c0"  # syntax_flow/syntax_condition
        
        # 時間格式（橘色）
        if 'T=' in command:
            return "#ce9178"  # syntax_time
        
        return "#d4d4d4"  # 預設 - 淺灰色
    
    def _get_command_display_text(self, command):
        """獲取指令的顯示文字（簡化版）"""
        # 限制顯示長度
        if len(command) > 30:
            return command[:27] + "..."
        return command
    
    def _create_canvas_node(self, text, color, x, y, original_command=None):
        """在畫布上創建節點（n8n 工作流程圖風格）
        
        n8n 風格特點：
        - 左側圓形圖示區域
        - 右側卡片顯示標題和描述
        - 左側輸入連接點
        - 右側輸出連接點
        - 深色背景配淺色文字
        """
        node_idx = len(self.canvas_nodes)
        node_tag = f"node_{node_idx}"
        
        # === n8n 風格節點尺寸 ===
        node_width = 200
        node_height = 70
        icon_size = 40  # 圖示圓形直徑
        icon_margin = 10  # 圖示左邊距
        border_radius = 8
        
        # 判斷節點類型
        is_condition = '條件判斷' in text or '如果' in text or '辨識' in text or 'if' in text.lower()
        is_label = text.startswith('標籤:') or text.startswith('#')
        is_mouse = '移動' in text or '點擊' in text or '拖曳' in text or '滾輪' in text
        is_keyboard = text.startswith('@') or '按鍵' in text
        is_wait = '等待' in text or '延遲' in text
        is_loop = '迴圈' in text or '重複' in text
        
        # 根據類型選擇圖示顏色和符號
        if is_condition:
            icon_color = "#c586c0"  # 紫色 - 條件判斷
            icon_symbol = "?"
            border_color = "#9c27b0"
        elif is_label:
            icon_color = "#4ec9b0"  # 青綠色 - 標籤
            icon_symbol = "#"
            border_color = "#00bcd4"
        elif is_mouse:
            icon_color = "#569cd6"  # 藍色 - 滑鼠
            icon_symbol = "🖱"
            border_color = "#2196f3"
        elif is_keyboard:
            icon_color = "#9cdcfe"  # 淺藍色 - 鍵盤
            icon_symbol = "⌨"
            border_color = "#03a9f4"
        elif is_wait:
            icon_color = "#dcdcaa"  # 黃色 - 等待
            icon_symbol = "⏱"
            border_color = "#ffc107"
        elif is_loop:
            icon_color = "#ce9178"  # 橘色 - 迴圈
            icon_symbol = "↻"
            border_color = "#ff9800"
        else:
            icon_color = color
            icon_symbol = "▶"
            border_color = "#666666"
        
        # === 創建節點元素 ===
        
        # 1. 陰影效果（輕微偏移）
        shadow = self.canvas.create_rectangle(
            x + 3, y + 3,
            x + node_width + 3, y + node_height + 3,
            fill="#0a0a0a",
            outline="",
            tags=("shadow", node_tag)
        )
        
        # 2. 主卡片背景（深灰色圓角矩形）
        card_bg = self._create_rounded_rectangle(
            x, y,
            x + node_width, y + node_height,
            radius=border_radius,
            fill="#2d2d30",
            outline=border_color,
            width=2,
            tags=("node", "card_bg", node_tag)
        )
        
        # 3. 左側圖示背景圓形
        icon_x = x + icon_margin + icon_size // 2
        icon_y = y + node_height // 2
        
        icon_bg = self.canvas.create_oval(
            icon_x - icon_size // 2, icon_y - icon_size // 2,
            icon_x + icon_size // 2, icon_y + icon_size // 2,
            fill=icon_color,
            outline="",
            tags=("node", "icon_bg", node_tag)
        )
        
        # 4. 圖示符號
        icon_text = self.canvas.create_text(
            icon_x, icon_y,
            text=icon_symbol,
            fill="white",
            font=font_tuple(14, "bold"),
            tags=("node", "icon_text", node_tag)
        )
        
        # 5. 標題文字（在圖示右側）
        text_x = x + icon_margin + icon_size + 12
        text_y = y + node_height // 2 - 8
        
        # 標題（主要顯示文字，限制長度）
        display_title = text[:20] + "..." if len(text) > 20 else text
        
        title_text = self.canvas.create_text(
            text_x, text_y,
            text=display_title,
            fill="white",
            font=font_tuple(10, "bold"),
            anchor="w",  # 左對齊
            tags=("node", "title_text", node_tag)
        )
        
        # 6. 副標題/描述（較小的灰色文字）
        subtitle_y = y + node_height // 2 + 10
        
        # 從原始指令提取類型描述
        if is_condition:
            subtitle = "條件判斷"
        elif is_label:
            subtitle = "標籤節點"
        elif is_mouse:
            subtitle = "滑鼠動作"
        elif is_keyboard:
            subtitle = "鍵盤輸入"
        elif is_wait:
            subtitle = "等待延遲"
        elif is_loop:
            subtitle = "迴圈控制"
        else:
            subtitle = "動作指令"
        
        subtitle_text = self.canvas.create_text(
            text_x, subtitle_y,
            text=subtitle,
            fill="#888888",
            font=font_tuple(8),
            anchor="w",
            tags=("node", "subtitle_text", node_tag)
        )
        
        # 7. 輸入連接點（左側小圓形）
        port_radius = 6
        input_port = self.canvas.create_oval(
            x - port_radius, icon_y - port_radius,
            x + port_radius, icon_y + port_radius,
            fill="#1e1e1e",
            outline=border_color,
            width=2,
            tags=("node", "input_port", node_tag)
        )
        
        # 8. 輸出連接點（右側小圓形）
        output_port = self.canvas.create_oval(
            x + node_width - port_radius, icon_y - port_radius,
            x + node_width + port_radius, icon_y + port_radius,
            fill="#1e1e1e",
            outline=border_color,
            width=2,
            tags=("node", "output_port", node_tag)
        )
        
        # 如果是條件判斷，添加第二個輸出連接點（用於失敗分支）
        output_port_2 = None
        if is_condition:
            output_port_2 = self.canvas.create_oval(
                x + node_width - port_radius, icon_y + 15 - port_radius,
                x + node_width + port_radius, icon_y + 15 + port_radius,
                fill="#1e1e1e",
                outline="#F44336",  # 紅色表示失敗分支
                width=2,
                tags=("node", "output_port_2", node_tag)
            )
        
        # 儲存節點資料
        node_data = {
            "rect": card_bg,
            "text": title_text,
            "shadow": shadow,
            "icon_bg": icon_bg,
            "icon_text": icon_text,
            "subtitle_text": subtitle_text,
            "input_port": input_port,
            "output_port": output_port,
            "output_port_2": output_port_2,
            "command": text,
            "original_command": original_command if original_command else text,
            "color": color,
            "icon_color": icon_color,
            "border_color": border_color,
            "x": x,
            "y": y,
            "width": node_width,
            "height": node_height,
            "is_condition": is_condition,
            "is_label": is_label
        }
        self.canvas_nodes.append(node_data)
        
        return node_idx
    
    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        """創建圓角矩形（模擬Workflow風格）"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)
    
    def _connect_nodes(self, idx1, idx2, label=None):
        """連接兩個節點 - 使用 n8n 風格的 Bezier 曲線（左到右流向）"""
        if idx1 < 0 or idx1 >= len(self.canvas_nodes) or idx2 < 0 or idx2 >= len(self.canvas_nodes):
            return
        
        node1 = self.canvas_nodes[idx1]
        node2 = self.canvas_nodes[idx2]
        
        # 獲取節點尺寸（n8n 風格節點）
        node_width = node1.get("width", 200)
        node_height = node1.get("height", 70)
        
        # 計算起點（從節點右側中心）和終點（到節點左側中心）
        # n8n 風格是左到右流向
        x1 = node1["x"] + node_width  # 節點右側
        y1 = node1["y"] + node_height // 2  # 節點中心高度
        x2 = node2["x"]  # 節點左側
        y2 = node2["y"] + node2.get("height", 70) // 2  # 節點中心高度
        
        # 根據標籤選擇顏色
        if label == "成功" or label == "True":
            line_color = "#4CAF50"  # 綠色表示成功
            glow_color = "#81C784"
        elif label == "失敗" or label == "False":
            line_color = "#F44336"  # 紅色表示失敗
            glow_color = "#E57373"
        else:
            line_color = "#8B8B8B"  # 灰色表示普通連接（更接近 n8n 風格）
            glow_color = "#666666"
        
        # 計算連線索引（用於多輸出時的垂直偏移）
        existing_connections = [c for c in self.canvas_connections if c["from"] == idx1]
        connection_index = len(existing_connections)
        
        # 計算來自同一目標節點的連線數（用於輸入端偏移）
        incoming_connections = [c for c in self.canvas_connections if c["to"] == idx2]
        incoming_index = len(incoming_connections)
        
        # 輸出端垂直偏移（每條線間隔 15 像素）
        output_offset = (connection_index - 0.5) * 15 if connection_index > 0 else 0
        y1 += output_offset
        
        # 輸入端垂直偏移
        input_offset = (incoming_index - 0.5) * 15 if incoming_index > 0 else 0
        y2 += input_offset
        
        # === Bezier 曲線計算 ===
        # 計算水平距離和控制點偏移
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # 控制點偏移量（根據距離動態調整，創建平滑曲線）
        # 較長的距離需要更大的控制點偏移
        control_offset = max(50, min(dx * 0.4, 150))
        
        # 處理特殊情況：目標在左邊（需要繞回）
        if x2 < x1:
            # 需要先向右再繞回左邊
            control_offset = max(80, dy * 0.5 + 50)
            
            # 使用更複雜的路徑：右出 -> 下/上繞 -> 左入
            mid_y = (y1 + y2) / 2
            
            # 創建 S 形曲線的控制點
            cp1_x = x1 + control_offset
            cp1_y = y1
            cp2_x = x2 - control_offset
            cp2_y = y2
            
            # 如果垂直差距大，調整控制點
            if dy > 100:
                cp1_y = y1 + (y2 - y1) * 0.3
                cp2_y = y2 - (y2 - y1) * 0.3
        else:
            # 正常左到右流向
            cp1_x = x1 + control_offset
            cp1_y = y1
            cp2_x = x2 - control_offset
            cp2_y = y2
        
        # 使用多點近似 Bezier 曲線（tkinter 的 smooth=True 會自動平滑）
        # 計算貝塞爾曲線上的多個點
        bezier_points = []
        num_segments = 20  # 分段數量，越多越平滑
        
        for i in range(num_segments + 1):
            t = i / num_segments
            # 三次貝塞爾曲線公式
            # B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt
            
            px = mt3 * x1 + 3 * mt2 * t * cp1_x + 3 * mt * t2 * cp2_x + t3 * x2
            py = mt3 * y1 + 3 * mt2 * t * cp1_y + 3 * mt * t2 * cp2_y + t3 * y2
            
            bezier_points.extend([px, py])
        
        # 繪製發光效果（外層粗線）
        glow_line = self.canvas.create_line(
            *bezier_points,
            fill=glow_color,
            width=5,
            smooth=True,
            splinesteps=36,
            tags="connection_glow"
        )
        
        # 繪製主連接線
        line = self.canvas.create_line(
            *bezier_points,
            fill=line_color,
            width=2,
            smooth=True,
            splinesteps=36,
            tags="connection"
        )
        
        # 繪製終點箭頭（小圓形端點，n8n 風格）
        arrow_radius = 4
        arrow_end = self.canvas.create_oval(
            x2 - arrow_radius, y2 - arrow_radius,
            x2 + arrow_radius, y2 + arrow_radius,
            fill=line_color,
            outline="",
            tags="connection_arrow"
        )
        
        # 繪製起點連接點（小圓形）
        start_dot = self.canvas.create_oval(
            x1 - 3, y1 - 3,
            x1 + 3, y1 + 3,
            fill=line_color,
            outline="",
            tags="connection_start"
        )
        
        # 如果有標籤，添加帶背景的文字
        label_text = None
        label_bg = None
        if label:
            # 將標籤放在曲線中間位置
            label_x = (x1 + x2) / 2
            label_y = (y1 + y2) / 2 - 15  # 稍微往上偏移避免與線重疊
            
            # 創建標籤背景（圓角矩形效果）
            label_bg = self.canvas.create_rectangle(
                label_x - 25, label_y - 10,
                label_x + 25, label_y + 10,
                fill="#1e1e1e",
                outline=line_color,
                width=1,
                tags="connection_label_bg"
            )
            
            # 創建標籤文字
            label_text = self.canvas.create_text(
                label_x, label_y,
                text=label,
                fill=line_color,
                font=font_tuple(8, "bold"),
                tags="connection_label"
            )
        
        self.canvas_connections.append({
            "line": line,
            "glow_line": glow_line,
            "arrow_end": arrow_end,
            "start_dot": start_dot,
            "label_text": label_text,
            "label_bg": label_bg,
            "from": idx1,
            "to": idx2,
            "connection_index": connection_index,
            "bezier_points": bezier_points,
            "control_points": (cp1_x, cp1_y, cp2_x, cp2_y)
        })
        
        # 將連接線移到節點下層
        self.canvas.tag_lower("connection_label_bg")
        self.canvas.tag_lower("connection_label")
        self.canvas.tag_lower("connection_arrow")
        self.canvas.tag_lower("connection_start")
        self.canvas.tag_lower("connection")
        self.canvas.tag_lower("connection_glow")
        self.canvas.tag_lower("grid")
    
    def _convert_canvas_to_text(self):
        """將畫布節點轉換為文字指令（支持標記容器）"""
        if not self.canvas_nodes:
            return
        
        # 清空文字編輯器
        self.text_editor.delete("1.0", tk.END)
        
        # 轉換節點為文字（使用原始指令）
        for node in self.canvas_nodes:
            # 檢查是否是標記容器
            if node.get("is_marker", False):
                # 標記容器：先寫標記名，再寫所有子元素
                marker_name = node.get("original_command", node["command"])
                self.text_editor.insert(tk.END, marker_name + "\n")
                
                # 寫入所有子元素
                for child_cmd in node.get("marker_children", []):
                    self.text_editor.insert(tk.END, child_cmd + "\n")
            else:
                # 普通節點
                original_command = node.get("original_command", node["command"])
                self.text_editor.insert(tk.END, original_command + "\n")
    
    def _on_canvas_click(self, event):
        """畫布點擊事件（支援節點拖動和畫布平移）"""
        # 檢查是否點擊到節點
        items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        
        for item in items:
            tags = self.canvas.gettags(item)
            # 檢查標記容器和普通節點
            if "node" in tags or "marker_container" in tags or "marker_name" in tags or "marker_child" in tags:
                # 查找對應的節點索引
                for idx, node in enumerate(self.canvas_nodes):
                    # 檢查是否點擊到該節點的任何元素
                    if node.get("is_marker", False):
                        # 標記容器：檢查容器、標記名或子元素
                        if (item == node.get("container_rect") or 
                            item == node.get("marker_text") or
                            item == node.get("separator")):
                            self.selected_node = idx
                            self.drag_data["item"] = item
                            self.drag_data["x"] = event.x
                            self.drag_data["y"] = event.y
                            return
                        # 檢查子元素
                        for child_elem in node.get("child_elements", []):
                            if item == child_elem["rect"] or item == child_elem["text"]:
                                self.selected_node = idx
                                self.drag_data["item"] = item
                                self.drag_data["x"] = event.x
                                self.drag_data["y"] = event.y
                                return
                    else:
                        # 普通節點
                        if item == node.get("rect") or item == node.get("text") or item == node.get("shadow"):
                            self.selected_node = idx
                            self.drag_data["item"] = item
                            self.drag_data["x"] = event.x
                            self.drag_data["y"] = event.y
                            return
        
        # 如果沒有點擊到節點，啟動畫布拖移模式
        self.pan_data["active"] = True
        self.pan_data["x"] = event.x
        self.pan_data["y"] = event.y
        self.canvas.config(cursor="fleur")
    
    def _on_canvas_drag(self, event):
        """畫布拖曳事件（節點拖動或畫布平移）"""
        if self.drag_data["item"] and self.selected_node is not None:
            # 拖動節點
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            
            node = self.canvas_nodes[self.selected_node]
            
            # 檢查是否是標記容器
            if node.get("is_marker", False):
                # 移動整個標記容器
                self.canvas.move(node["container_rect"], dx, dy)
                self.canvas.move(node["marker_text"], dx, dy)
                self.canvas.move(node["separator"], dx, dy)
                
                # 移動所有子元素
                for child_elem in node.get("child_elements", []):
                    self.canvas.move(child_elem["rect"], dx, dy)
                    self.canvas.move(child_elem["text"], dx, dy)
                    child_elem["x"] += dx
                    child_elem["y"] += dy
            else:
                # 移動普通節點（n8n 風格，包含多個元素）
                # 陰影
                if "shadow" in node:
                    self.canvas.move(node["shadow"], dx, dy)
                # 主卡片
                self.canvas.move(node["rect"], dx, dy)
                # 標題文字
                self.canvas.move(node["text"], dx, dy)
                # 圖示背景
                if "icon_bg" in node:
                    self.canvas.move(node["icon_bg"], dx, dy)
                # 圖示文字
                if "icon_text" in node:
                    self.canvas.move(node["icon_text"], dx, dy)
                # 副標題
                if "subtitle_text" in node:
                    self.canvas.move(node["subtitle_text"], dx, dy)
                # 輸入連接點
                if "input_port" in node:
                    self.canvas.move(node["input_port"], dx, dy)
                # 輸出連接點
                if "output_port" in node:
                    self.canvas.move(node["output_port"], dx, dy)
                # 第二輸出連接點（條件判斷）
                if node.get("output_port_2"):
                    self.canvas.move(node["output_port_2"], dx, dy)
            
            # 更新節點位置
            node["x"] += dx
            node["y"] += dy
            
            # 更新連接線
            self._update_node_connections(self.selected_node)
            
            # 更新拖曳資料
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
        elif self.pan_data["active"]:
            # 拖移畫布
            dx = event.x - self.pan_data["x"]
            dy = event.y - self.pan_data["y"]
            
            # 移動所有元素
            self.canvas.move("all", dx, dy)
            
            # 更新節點位置記錄
            for node in self.canvas_nodes:
                node["x"] += dx
                node["y"] += dy
            
            self.pan_data["x"] = event.x
            self.pan_data["y"] = event.y
    
    def _on_canvas_release(self, event):
        """畫布釋放事件（結束節點拖動或畫布平移）"""
        self.drag_data["item"] = None
        self.selected_node = None
        if self.pan_data["active"]:
            self.pan_data["active"] = False
            self.canvas.config(cursor="crosshair")
    
    def _update_node_connections(self, node_idx):
        """更新與指定節點相關的所有連接線 - 使用 Bezier 曲線"""
        for conn in self.canvas_connections:
            if conn["from"] == node_idx or conn["to"] == node_idx:
                from_node = self.canvas_nodes[conn["from"]]
                to_node = self.canvas_nodes[conn["to"]]
                
                # 獲取節點尺寸
                node_width = from_node.get("width", 200)
                node_height = from_node.get("height", 70)
                
                # 計算起點（從節點右側）和終點（到節點左側）
                x1 = from_node["x"] + node_width
                y1 = from_node["y"] + node_height // 2
                x2 = to_node["x"]
                y2 = to_node["y"] + to_node.get("height", 70) // 2
                
                # 獲取連線索引
                connection_index = conn.get("connection_index", 0)
                
                # 計算偏移
                output_offset = (connection_index - 0.5) * 15 if connection_index > 0 else 0
                y1 += output_offset
                
                # 計算控制點
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                control_offset = max(50, min(dx * 0.4, 150))
                
                if x2 < x1:
                    control_offset = max(80, dy * 0.5 + 50)
                    cp1_x = x1 + control_offset
                    cp1_y = y1
                    cp2_x = x2 - control_offset
                    cp2_y = y2
                    if dy > 100:
                        cp1_y = y1 + (y2 - y1) * 0.3
                        cp2_y = y2 - (y2 - y1) * 0.3
                else:
                    cp1_x = x1 + control_offset
                    cp1_y = y1
                    cp2_x = x2 - control_offset
                    cp2_y = y2
                
                # 計算 Bezier 曲線點
                bezier_points = []
                num_segments = 20
                
                for i in range(num_segments + 1):
                    t = i / num_segments
                    t2 = t * t
                    t3 = t2 * t
                    mt = 1 - t
                    mt2 = mt * mt
                    mt3 = mt2 * mt
                    
                    px = mt3 * x1 + 3 * mt2 * t * cp1_x + 3 * mt * t2 * cp2_x + t3 * x2
                    py = mt3 * y1 + 3 * mt2 * t * cp1_y + 3 * mt * t2 * cp2_y + t3 * y2
                    
                    bezier_points.extend([px, py])
                
                # 更新連線座標
                self.canvas.coords(conn["line"], *bezier_points)
                if conn.get("glow_line"):
                    self.canvas.coords(conn["glow_line"], *bezier_points)
                
                # 更新箭頭和起點圓形位置
                arrow_radius = 4
                if conn.get("arrow_end"):
                    self.canvas.coords(conn["arrow_end"],
                                       x2 - arrow_radius, y2 - arrow_radius,
                                       x2 + arrow_radius, y2 + arrow_radius)
                if conn.get("start_dot"):
                    self.canvas.coords(conn["start_dot"],
                                       x1 - 3, y1 - 3,
                                       x1 + 3, y1 + 3)
                
                # 更新標籤位置
                if conn.get("label_text"):
                    label_x = (x1 + x2) / 2
                    label_y = (y1 + y2) / 2 - 15
                    
                    self.canvas.coords(conn["label_text"], label_x, label_y)
                    if conn.get("label_bg"):
                        self.canvas.coords(conn["label_bg"],
                                         label_x - 25, label_y - 10,
                                         label_x + 25, label_y + 10)
    
    def _on_canvas_zoom(self, event):
        """畫布縮放事件（滾輪）- 同步縮放文字和圖形"""
        # 獲取滾輪方向
        if event.delta > 0:
            scale_factor = 1.1
        else:
            scale_factor = 0.9
        
        # 限制縮放範圍
        new_scale = self.canvas_scale * scale_factor
        if new_scale < 0.3 or new_scale > 3.0:
            return
        
        self.canvas_scale = new_scale
        
        # 縮放所有元素（圖形部分）
        self.canvas.scale("all", event.x, event.y, scale_factor, scale_factor)
        
        # 更新節點位置和文字大小
        for node in self.canvas_nodes:
            # 更新節點位置記錄
            dx = node["x"] - event.x
            dy = node["y"] - event.y
            node["x"] = event.x + dx * scale_factor
            node["y"] = event.y + dy * scale_factor
            
            # 同步更新文字大小（確保文字跟圖形框同步）
            new_font_size = max(6, int(9 * self.canvas_scale))
            self.canvas.itemconfig(node["text"], font=font_tuple(new_font_size, "bold"))
        
        # 顯示縮放比例
        self._update_status(f"縮放: {int(self.canvas_scale * 100)}%", "info")
    
    def _on_canvas_pan_start(self, event):
        """開始平移畫布（中鍵）"""
        self.pan_data["active"] = True
        self.pan_data["x"] = event.x
        self.pan_data["y"] = event.y
        self.canvas.config(cursor="fleur")
    
    def _on_canvas_pan_move(self, event):
        """平移畫布中"""
        if self.pan_data["active"]:
            dx = event.x - self.pan_data["x"]
            dy = event.y - self.pan_data["y"]
            
            # 移動所有元素
            self.canvas.move("all", dx, dy)
            
            # 更新節點位置記錄
            for node in self.canvas_nodes:
                node["x"] += dx
                node["y"] += dy
            
            self.pan_data["x"] = event.x
            self.pan_data["y"] = event.y
    
    def _on_canvas_pan_end(self, event):
        """結束平移畫布"""
        self.pan_data["active"] = False
        self.canvas.config(cursor="crosshair")
    
    def _show_canvas_context_menu(self, event):
        """顯示畫布右鍵選單（簡化版）"""
        menu = tk.Menu(self, tearoff=0)
        
        # 只保留自動排列功能
        menu.add_command(label="🔄 自動排列", command=self._auto_arrange_nodes)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _clear_canvas(self):
        """清空畫布"""
        if messagebox.askyesno("確認", "確定要清空畫布嗎？"):
            self.canvas.delete("all")
            self.canvas_nodes = []
            self.canvas_connections = []
            self._draw_grid()
            self._update_status("已清空畫布", "success")
    
    def _add_command_node(self, x, y):
        """在指定位置添加指令節點"""
        # 彈出對話框輸入指令
        command = simpledialog.askstring("添加指令", "請輸入指令內容：\n(例如：>移動至(100,100), 延遲0ms, T=0s000)")
        if command:
            color = self._get_command_color(command)
            display_text = self._get_command_display_text(command)
            self._create_canvas_node(display_text, color, x, y, original_command=command)
            self._update_status("已添加指令節點", "success")
    
    def _add_marker_node(self, x, y):
        """在指定位置添加標記節點"""
        # 彈出對話框輸入標記名
        marker_name = simpledialog.askstring("添加標記", "請輸入標記名稱：\n(例如：#start、#loop等)")
        if marker_name:
            if not marker_name.startswith('#'):
                marker_name = '#' + marker_name
            
            # 創建標記容器（暫無子元素）
            marker_item = {
                'type': 'marker',
                'name': marker_name,
                'children': []
            }
            self._draw_marker_container(marker_item, x, y)
            self._update_status("已添加標記節點", "success")
    
    def _edit_node(self, node_idx):
        """編輯節點內容"""
        if node_idx < 0 or node_idx >= len(self.canvas_nodes):
            return
        
        node = self.canvas_nodes[node_idx]
        current_command = node.get("original_command", node["command"])
        
        if node.get("is_marker"):
            # 編輯標記名
            new_name = simpledialog.askstring("編輯標記", f"當前標記：{current_command}\n請輸入新的標記名稱：", 
                                              initialvalue=current_command)
            if new_name and new_name != current_command:
                if not new_name.startswith('#'):
                    new_name = '#' + new_name
                node["original_command"] = new_name
                node["command"] = new_name
                # 更新顯示
                self.canvas.itemconfig(node["marker_text"], text=new_name)
                self._update_status("已更新標記名稱", "success")
        else:
            # 編輯普通指令
            new_command = simpledialog.askstring("編輯指令", f"當前指令：{current_command}\n請輸入新的指令：",
                                                 initialvalue=current_command)
            if new_command and new_command != current_command:
                node["original_command"] = new_command
                node["command"] = self._get_command_display_text(new_command)
                node["color"] = self._get_command_color(new_command)
                # 更新顯示
                self.canvas.itemconfig(node["text"], text=node["command"])
                self.canvas.itemconfig(node["rect"], fill=node["color"])
                self._update_status("已更新指令內容", "success")
    
    def _delete_node(self, node_idx):
        """刪除節點"""
        if node_idx < 0 or node_idx >= len(self.canvas_nodes):
            return
        
        if not messagebox.askyesno("確認", "確定要刪除此節點嗎？"):
            return
        
        node = self.canvas_nodes[node_idx]
        
        # 刪除canvas元素
        if node.get("is_marker"):
            # 刪除標記容器及所有子元素
            self.canvas.delete(node["container_rect"])
            self.canvas.delete(node["marker_text"])
            self.canvas.delete(node["separator"])
            for child_elem in node.get("child_elements", []):
                self.canvas.delete(child_elem["rect"])
                self.canvas.delete(child_elem["text"])
        else:
            # 刪除普通節點
            if "shadow" in node:
                self.canvas.delete(node["shadow"])
            self.canvas.delete(node["rect"])
            self.canvas.delete(node["text"])
        
        # 從列表中移除
        self.canvas_nodes.pop(node_idx)
        
        # 刪除相關連接線
        self.canvas_connections = [conn for conn in self.canvas_connections 
                                   if conn["from"] != node_idx and conn["to"] != node_idx]
        
        self._update_status("已刪除節點", "success")
    
    def _add_action_to_marker(self, marker_idx):
        """向標記添加子動作"""
        if marker_idx < 0 or marker_idx >= len(self.canvas_nodes):
            return
        
        node = self.canvas_nodes[marker_idx]
        if not node.get("is_marker"):
            return
        
        # 輸入新動作
        action = simpledialog.askstring("添加動作", "請輸入要添加的動作：\n(例如：>按下a, 延遲50ms, T=0s000)")
        if action:
            # 添加到標記的子元素列表
            node["marker_children"].append(action)
            
            # 重新繪製整個標記容器
            # 先刪除舊的
            self.canvas.delete(node["container_rect"])
            self.canvas.delete(node["marker_text"])
            self.canvas.delete(node["separator"])
            for child_elem in node.get("child_elements", []):
                self.canvas.delete(child_elem["rect"])
                self.canvas.delete(child_elem["text"])
            
            # 重新創建
            marker_item = {
                'type': 'marker',
                'name': node["original_command"],
                'children': node["marker_children"]
            }
            
            x, y = node["x"], node["y"]
            # 移除舊節點
            self.canvas_nodes.pop(marker_idx)
            # 插入新節點到相同位置
            self._draw_marker_container(marker_item, x, y)
            # 將新節點移動到正確的索引位置
            new_node = self.canvas_nodes.pop()
            self.canvas_nodes.insert(marker_idx, new_node)
            
            self._update_status("已添加動作到標記", "success")
    
    def _reset_canvas_zoom(self):
        """重置畫布縮放到100%"""
        if self.canvas_scale == 1.0:
            self._update_status("已是100%縮放", "info")
            return
        
        # 計算需要的縮放因子
        reset_factor = 1.0 / self.canvas_scale
        
        # 獲取畫布中心點
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width / 2
        center_y = height / 2
        
        # 以中心點為基準縮放
        self.canvas.scale("all", center_x, center_y, reset_factor, reset_factor)
        
        # 更新節點位置記錄
        for node in self.canvas_nodes:
            dx = node["x"] - center_x
            dy = node["y"] - center_y
            node["x"] = center_x + dx * reset_factor
            node["y"] = center_y + dy * reset_factor
        
        # 重置縮放比例
        self.canvas_scale = 1.0
        self._update_status("已重置縮放到100%", "success")
    
    def _auto_arrange_nodes(self):
        """智能自動排列節點（符合指令判斷邏輯）"""
        if not self.canvas_nodes:
            return
        
        # 建立標籤到節點索引的映射
        label_to_idx = {}
        for idx, node in enumerate(self.canvas_nodes):
            cmd = node.get("original_command", node.get("command", ""))
            if cmd.startswith('#') and not cmd.startswith('##'):
                label_to_idx[cmd.strip()] = idx
        
        # 建立節點層級和位置映射
        node_levels = {}  # {idx: level}
        node_columns = {}  # {idx: column}
        visited = set()
        
        def calculate_layout(idx, level=0, column=0):
            """遞歸計算節點的層級和列位置"""
            if idx in visited or idx >= len(self.canvas_nodes):
                return
            
            visited.add(idx)
            node_levels[idx] = level
            node_columns[idx] = column
            
            # 查找此節點的分支目標
            node = self.canvas_nodes[idx]
            cmd = node.get("original_command", node.get("command", ""))
            
            # 查找文字內容中的分支指令
            text_content = self.text_editor.get("1.0", tk.END)
            lines = text_content.split('\n')
            
            # 找到當前標籤後的分支指令
            in_current_label = False
            for line in lines:
                line = line.strip()
                if line == cmd:
                    in_current_label = True
                    continue
                
                if in_current_label:
                    # 檢查是否到下一個標籤
                    if line.startswith('#') and not line.startswith('##'):
                        break
                    
                    # 檢查分支指令
                    if line.startswith('>>#') or line.startswith('>>>#'):
                        target_label = '#' + line.split('#', 1)[1].split(',')[0].strip()
                        if target_label in label_to_idx:
                            target_idx = label_to_idx[target_label]
                            # 成功分支往右，失敗分支往更右
                            branch_column = column + 1 if line.startswith('>>#') else column + 2
                            calculate_layout(target_idx, level + 1, branch_column)
        
        # 從第一個節點開始計算
        if self.canvas_nodes:
            calculate_layout(0, 0, 0)
        
        # 根據層級和列進行排列
        x_spacing = 300
        y_spacing = 120
        start_x = 150
        start_y = 100
        
        for idx, node in enumerate(self.canvas_nodes):
            if idx not in node_levels:
                # 未訪問的節點按順序排列
                level = len([i for i in range(idx) if i in node_levels])
                column = 0
            else:
                level = node_levels[idx]
                column = node_columns[idx]
            
            new_x = start_x + column * x_spacing
            new_y = start_y + level * y_spacing
            
            # 計算位移
            dx = new_x - node["x"]
            dy = new_y - node["y"]
            
            # 移動節點
            if node.get("is_marker", False):
                # 移動標記容器
                self.canvas.move(node["container_rect"], dx, dy)
                self.canvas.move(node["marker_text"], dx, dy)
                self.canvas.move(node["separator"], dx, dy)
                for child_elem in node.get("child_elements", []):
                    self.canvas.move(child_elem["rect"], dx, dy)
                    self.canvas.move(child_elem["text"], dx, dy)
                    child_elem["x"] += dx
                    child_elem["y"] += dy
            else:
                # 移動普通節點
                if "shadow" in node:
                    self.canvas.move(node["shadow"], dx, dy)
                self.canvas.move(node["rect"], dx, dy)
                self.canvas.move(node["text"], dx, dy)
            
            # 更新節點位置
            node["x"] = new_x
            node["y"] = new_y
        
        # 更新所有連接線
        for i in range(len(self.canvas_nodes)):
            self._update_node_connections(i)
        
        # 調整畫布滾動區域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        self._update_status("已智能排列節點", "success")
    
    def _auto_fold_all_trajectories(self):
        """自動摺疊所有軌跡區塊"""
        try:
            content = self.text_editor.get("1.0", "end")
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                if line.startswith("# [軌跡]") and "[展開]" in line:
                    # 找到軌跡摘要行，觸發摺疊
                    self._toggle_trajectory_fold(i)
        except Exception as e:
            print(f"自動摺疊失敗: {e}")
    
    def _simplify_trajectory_display(self, lines: list) -> list:
        """摺疊軌跡顯示：將連續的移動指令折疊為可展開的摘要行
        
        Args:
            lines: 原始文字指令列表
            
        Returns:
            簡化後的文字指令列表（預設摺疊）
        """
        if not self.simplify_display_var.get():
            return lines  # 不簡化，返回原始內容
        
        simplified = []
        trajectory_buffer = []
        trajectory_start_time = None
        
        for line in lines:
            # 檢測移動指令
            if line.startswith(">移動至(") and ", T=" in line:
                if not trajectory_buffer:
                    # 記錄軌跡開始
                    match = re.search(r'T=(\d+s\d+)', line)
                    if match:
                        trajectory_start_time = match.group(1)
                trajectory_buffer.append(line)
            else:
                # 非移動指令，處理累積的軌跡
                if len(trajectory_buffer) > 3:  # 只簡化超過3個點的軌跡
                    # 提取起點和終點座標（支援負數）
                    start_match = re.search(r'>移動至\((-?\d+),(-?\d+)\)', trajectory_buffer[0])
                    end_match = re.search(r'>移動至\((-?\d+),(-?\d+)\)', trajectory_buffer[-1])
                    end_time_match = re.search(r'T=(\d+s\d+)', trajectory_buffer[-1])
                    
                    if start_match and end_match and end_time_match:
                        start_pos = f"({start_match.group(1)},{start_match.group(2)})"
                        end_pos = f"({end_match.group(1)},{end_match.group(2)})"
                        end_time = end_time_match.group(1)
                        point_count = len(trajectory_buffer)
                        
                        # 計算持續時間
                        start_seconds = self._parse_time(trajectory_start_time)
                        end_seconds = self._parse_time(end_time)
                        duration = end_seconds - start_seconds
                        
                        # 生成摘要行（可點擊展開）
                        summary = f"# [軌跡] {start_pos}→{end_pos} 共{point_count}點 {duration:.1f}秒 [展開]\n"
                        simplified.append(summary)
                        
                        # 存儲軌跡詳細內容（預設隱藏）
                        simplified.append(f"# [軌跡開始]\n")
                        for traj_line in trajectory_buffer:
                            simplified.append(traj_line)  # 不加 # 前綴，保持原始指令
                        simplified.append(f"# [軌跡結束]\n")
                else:
                    # 軌跡太短，保留原樣
                    simplified.extend(trajectory_buffer)
                
                trajectory_buffer = []
                trajectory_start_time = None
                simplified.append(line)
        
        # 處理結尾的軌跡
        if len(trajectory_buffer) > 3:
            start_match = re.search(r'>移動至\((-?\d+),(-?\d+)\)', trajectory_buffer[0])
            end_match = re.search(r'>移動至\((-?\d+),(-?\d+)\)', trajectory_buffer[-1])
            end_time_match = re.search(r'T=(\d+s\d+)', trajectory_buffer[-1])
            
            if start_match and end_match and end_time_match:
                start_pos = f"({start_match.group(1)},{start_match.group(2)})"
                end_pos = f"({end_match.group(1)},{end_match.group(2)})"
                end_time = end_time_match.group(1)
                point_count = len(trajectory_buffer)
                
                start_seconds = self._parse_time(trajectory_start_time)
                end_seconds = self._parse_time(end_time)
                duration = end_seconds - start_seconds
                
                summary = f"# [軌跡] {start_pos}→{end_pos} 共{point_count}點 {duration:.1f}秒 [展開]\n"
                simplified.append(summary)
                
                simplified.append(f"# [軌跡開始]\n")
                for traj_line in trajectory_buffer:
                    simplified.append(traj_line)  # 不加 # 前綴，保持原始指令
                simplified.append(f"# [軌跡結束]\n")
        else:
            simplified.extend(trajectory_buffer)
        
        return simplified
    
    def _create_command_buttons_in_frame(self, parent_frame):
        """在指定的父框架中創建快速指令按鈕區（分類選單切換）"""
        # 主容器框架
        cmd_frame = tk.Frame(parent_frame, bg="#2b2b2b")
        cmd_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.button_categories = {
            "⭐ 快速範例": [
                ("無限找圖循環", "#E91E63", None, "# 🔄 無限找圖(直到找到為止)\n#開始找圖\n>if>需替換圖片, T=0s000\n  >>#找到圖片\n  >>>#開始找圖\n#找到圖片\n# 在此處添加找到後的動作"),
                ("等待圖片消失", "#9C27B0", None, "# ⏳ 等待圖片消失(如Loading)\n#檢查消失\n>if>需替換圖片, T=0s000\n  >>#檢查消失\n  >>>#已消失\n#已消失\n# 圖片已不見,繼續後續動作"),
                ("隨機三選一", "#3F51B5", None, "# 🎲 隨機執行三選一\n>隨機執行>33%, T=0s000\n  >>#動作1\n  >>>#檢查二\n#檢查二\n>隨機執行>50%, T=0s000\n  >>#動作2\n  >>>#動作3\n#動作1\n移動至(100,100), T=0s000\n>>#結束\n#動作2\n移動至(200,200), T=0s000\n>>#結束\n#動作3\n移動至(300,300), T=0s000\n#結束"),
                ("定時文字監控", "#009688", None, "# 👁️ 定時偵測畫面文字\n#開始監控\n>等待文字>目標文字, 最長5s, T=0s000\n>點擊文字>目標文字, T=0s000\n>延遲1000ms, T=0s000\n>>#開始監控"),
                ("連技按鍵序列", "#FF9800", None, "# ⌨️ 連續按鍵序列(循環10次)\n>重複>10次, T=0s000\n  按a, 延遲100ms, T=0s000\n  按b, 延遲100ms, T=0s000\n  按c, 延遲500ms, T=0s000\n>重複結束, T=0s000"),
            ],
            "圖片辨識": [
                ("圖片辨識", "#9C27B0", self._capture_and_recognize, None),
                ("範圍辨識", "#7B1FA2", self._capture_region_for_recognition, None),
                ("移動至圖片", "#673AB7", None, ">移動至>pic01, T=0s000"),
                ("點擊圖片", "#3F51B5", None, ">左鍵點擊>pic01, T=0s000"),
                ("條件判斷", "#2196F3", None, ">if>pic01, T=0s000\n>>#標籤\n>>>#標籤"),
            ],
            "滑鼠鍵盤": [
                ("左鍵點擊", "#03A9F4", self._capture_left_click_coordinate, None),
                ("右鍵點擊", "#00BCD4", self._capture_right_click_coordinate, None),
                ("滑鼠移動", "#009688", None, ">移動至(0,0), 延遲0ms, T=0s000"),
                ("滑鼠滾輪", "#4CAF50", None, ">滾輪(1), 延遲0ms, T=0s000"),
                ("按下按鍵", "#8BC34A", None, ">按下a, 延遲50ms, T=0s000"),
                ("放開按鍵", "#CDDC39", None, ">放開a, 延遲0ms, T=0s000"),
            ],
            "流程控制": [
                ("新增標籤", "#FFC107", None, "#標籤名稱"),
                ("跳轉標籤", "#FF9800", None, ">>#標籤名稱"),
                ("條件失敗跳轉", "#FF5722", None, ">>>#標籤名稱"),
                ("OCR文字判斷", "#00BCD4", None, ">if文字>更改為需判斷文字, T=0s000\n>>#找到\n>>>#沒找到"),
                ("OCR等待文字", "#009688", None, ">等待文字>更改為需等待文字, 最長10s, T=0s000"),
                ("OCR點擊文字", "#4CAF50", None, ">點擊文字>更改為需點擊文字, T=0s000"),
                ("延遲等待", "#795548", None, ">延遲1000ms, T=0s000"),
            ],
            "變數系統": [
                ("設定變數", "#6A1B9A", None, ">設定變數>count, 0, T=0s000"),
                ("變數加1", "#7B1FA2", None, ">變數加1>count, T=0s000"),
                ("變數減1", "#8E24AA", None, ">變數減1>count, T=0s000"),
                ("變數條件", "#9C27B0", None, ">if變數>count, >=, 10, T=0s000\n>>#成功\n>>>#失敗"),
            ],
            "循環控制": [
                ("重複N次", "#1565C0", None, ">重複>10次, T=0s000\n  # 在此處添加要重複的指令\n>重複結束, T=0s000"),
                ("條件循環", "#1976D2", None, ">當圖片存在>loading, T=0s000\n  # 在此處添加循環內的指令\n>循環結束, T=0s000"),
            ],
            "多條件與隨機": [
                ("全部圖片存在", "#00695C", None, ">if全部存在>pic01,pic02,pic03, T=0s000\n>>#全部找到\n>>>#缺少某個"),
                ("任一圖片存在", "#00796B", None, ">if任一存在>pic01,pic02,pic03, T=0s000\n>>#找到其中一個\n>>>#全部都沒有"),
                ("隨機延遲", "#388E3C", None, ">隨機延遲>100ms,500ms, T=0s000"),
                ("隨機分支", "#4CAF50", None, ">隨機執行>30%, T=0s000\n>>#執行A\n>>>#執行B"),
            ],
            "計時系統": [
                ("計數器觸發", "#E65100", None, ">計數器>找圖失敗, 3次後, T=0s000\n>>#下一步"),
                ("計時器觸發", "#F57C00", None, ">計時器>等待載入, 60秒後, T=0s000\n>>#超時處理"),
                ("重置計數器", "#FF6F00", None, ">重置計數器>找圖失敗, T=0s000"),
                ("重置計時器", "#FF9800", None, ">重置計時器>等待載入, T=0s000"),
                ("開始", "#4CAF50", None, ">開始>10秒後, T=0s000"),
                ("結束", "#F44336", None, ">結束>60秒後, T=0s000"),
            ]
        }
        
        # 創建分類選單按鈕區（上方）
        category_btn_frame = tk.Frame(cmd_frame, bg="#2b2b2b")
        category_btn_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # 創建分類按鈕
        self.category_buttons = {}
        self.current_category = "圖片辨識"  # 預設選中
        
        for idx, category_name in enumerate(self.button_categories.keys()):
            # 根據是否為當前分類設置初始顏色
            initial_bg = "#4A90E2" if category_name == self.current_category else "#3a3a3a"
            
            btn = tk.Button(
                category_btn_frame,
                text=category_name,
                bg=initial_bg,
                fg="white",
                font=font_tuple(9, "bold"),
                padx=10,
                pady=5,
                relief="raised",
                bd=2,
                cursor="hand2",
                command=lambda cat=category_name: self._switch_category(cat)
            )
            btn.grid(row=idx // 3, column=idx % 3, padx=2, pady=2, sticky="ew")
            self.category_buttons[category_name] = btn
            
            # 配置列權重使按鈕平均分配寬度
            category_btn_frame.grid_columnconfigure(idx % 3, weight=1)
        
        # 創建按鈕區外框
        button_area_frame = tk.Frame(cmd_frame, bg="#2b2b2b", relief="groove", bd=1, highlightbackground="#555555", highlightthickness=1)
        button_area_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # 創建 Canvas 和 Scrollbar 以支援捲動（顯示當前分類的按鈕）
        canvas = tk.Canvas(button_area_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = tk.Scrollbar(button_area_frame, orient="vertical", command=canvas.yview)
        
        # 可捲動的按鈕容器
        self.button_container = tk.Frame(canvas, bg="#2b2b2b")
        
        # 配置 Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 放置 Canvas 和 Scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # 在 Canvas 上創建窗口
        canvas_window = canvas.create_window((0, 0), window=self.button_container, anchor="nw")
        
        # 綁定事件以更新捲動區域
        def _on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def _on_canvas_configure(event):
            # 更新 canvas_window 的寬度以匹配 canvas
            canvas.itemconfig(canvas_window, width=event.width)
        
        self.button_container.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # 滑鼠滾輪支援
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 保存 canvas 引用
        self.cmd_canvas = canvas
        
        # 顯示預設分類的按鈕
        self._show_category_buttons(self.current_category)
    
    def _switch_category(self, category_name):
        """切換分類並更新按鈕顯示"""
        # 更新當前分類
        self.current_category = category_name
        
        # 更新分類按鈕的顏色
        for cat_name, btn in self.category_buttons.items():
            if cat_name == category_name:
                btn.config(bg="#4A90E2")  # 選中的顏色
            else:
                btn.config(bg="#3a3a3a")  # 未選中的顏色
        
        # 顯示該分類的按鈕
        self._show_category_buttons(category_name)
    
    def _show_category_buttons(self, category_name):
        """顯示指定分類的按鈕"""
        # 清空容器中的所有按鈕
        for widget in self.button_container.winfo_children():
            widget.destroy()
        
        # 獲取該分類的按鈕列表
        buttons = self.button_categories.get(category_name, [])
        
        # 創建按鈕（每行3個）
        for idx, (text, color, command, template) in enumerate(buttons):
            row = idx // 3
            col = idx % 3
            
            if command:
                # 特殊功能按鈕（如圖片辨識）
                btn = tk.Button(
                    self.button_container,
                    text=text,
                    bg=color,
                    fg="white",
                    font=font_tuple(9, "bold"),
                    padx=8,
                    pady=6,
                    height=2,
                    relief="raised",
                    bd=2,
                    cursor="hand2",
                    command=command,
                    wraplength=100  # 文字換行
                )
            else:
                # 插入模板的按鈕
                btn = tk.Button(
                    self.button_container,
                    text=text,
                    bg=color,
                    fg="white",
                    font=font_tuple(9, "bold"),
                    padx=8,
                    pady=6,
                    height=2,
                    relief="raised",
                    bd=2,
                    cursor="hand2",
                    command=lambda t=template: self._insert_command_template(t),
                    wraplength=100  # 文字換行
                )
            
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            
            # 配置列權重使按鈕平均分配寬度
            self.button_container.grid_columnconfigure(col, weight=1)

    def _insert_command_template(self, template):
        """插入指令模板到編輯器"""
        if not template:
            return
        
        # 獲取當前游標位置
        try:
            cursor_pos = self.text_editor.index(tk.INSERT)
        except:
            cursor_pos = "end"
        
        # 在游標位置插入模板
        self.text_editor.insert(cursor_pos, template + "\n")
        
        # 更新狀態
        self._update_status(f"已插入指令模板", "success")
        
        # 聚焦到編輯器
        self.text_editor.focus_set()
    
    def _insert_module_reference(self):
        """插入模組引用"""
        # 獲取所有可用模組
        modules = []
        if os.path.exists(self.modules_dir):
            for filename in os.listdir(self.modules_dir):
                if filename.endswith('.txt'):
                    module_name = filename[:-4]
                    modules.append(module_name)
        
        if not modules:
            self._show_message("提示", "沒有可用的模組\n\n請先保存模組（選擇指令後點擊「儲存新模組」）", "info")
            return
        
        # 創建對話框選擇模組
        dialog = tk.Toplevel(self)
        dialog.title("選擇模組")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="選擇要引用的模組：", font=font_tuple(10)).pack(pady=10)
        
        # 模組列表
        listbox = tk.Listbox(dialog, font=font_tuple(10), height=10)
        listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        for module in modules:
            listbox.insert(tk.END, module)
        
        # 選擇層級
        level_frame = tk.Frame(dialog)
        level_frame.pack(pady=5)
        
        tk.Label(level_frame, text="引用層級：", font=font_tuple(9)).pack(side="left", padx=5)
        level_var = tk.StringVar(value=">>")
        
        tk.Radiobutton(level_frame, text=">>  (條件成功)", variable=level_var, value=">>", font=font_tuple(9)).pack(side="left")
        tk.Radiobutton(level_frame, text=">>> (條件失敗)", variable=level_var, value=">>>", font=font_tuple(9)).pack(side="left")
        
        def insert():
            selection = listbox.curselection()
            if not selection:
                return
            
            module_name = listbox.get(selection[0])
            level = level_var.get()
            reference = f"{level}#{module_name}"
            
            # 插入到編輯器
            self.text_editor.insert(tk.INSERT, reference + "\n")
            self._update_status(f"已插入模組引用：{reference}", "success")
            dialog.destroy()
        
        # 按鈕
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="插入", command=insert, bg="#4CAF50", fg="white", 
                 font=font_tuple(10), padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, bg="#757575", fg="white",
                 font=font_tuple(10), padx=20, pady=5).pack(side="left", padx=5)
        
        # 雙擊也可以插入
        listbox.bind("<Double-Button-1>", lambda e: insert())
    
    def _show_command_reference(self):
        """顯示指令說明視窗（使用 grid 佈局的表格）"""
        # 創建獨立的說明視窗
        ref_window = tk.Toplevel(self)
        ref_window.title("ChroLens Mimic - 指令說明")
        ref_window.geometry("1200x850")  # 增加高度以容納新手入門區
        ref_window.configure(bg="#1e1e1e")
        
        # 創建帶滾動條的 Canvas 容器
        container = tk.Frame(ref_window, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 創建 Canvas 和滾動條（深色樣式）
        canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview, bg="#2d2d30", troughcolor="#1e1e1e", width=12)
        scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ✅ 新增：新手快速入門區（更親民的說明）
        self._insert_beginner_guide(scrollable_frame)
        
        # 插入指令表格（使用 grid）
        self._insert_command_grid_table(scrollable_frame)
        
        # 底部提示文字（更清楚的說明）
        info_frame = tk.Frame(ref_window, bg="#1e1e1e")
        info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # 更實用的提示文字
        tips = [
            "💡 快速上手: 按「錄製」→ 做你想自動化的動作 → 按「停止」→ 按「播放」測試",
            "💡 時間格式: T=1s500 = 1.5秒 (1秒 + 500毫秒),不懂就用錄製功能自動產生!",
            "💡 找不到指令? 按「指令說明」鈕,裡面有所有指令的範例",
            "💡 圖片辨識: 按「圖片辨識」鈕 → 框選要找的圖 → 自動產生指令,超簡單!"
        ]
        for tip in tips:
            tk.Label(
                info_frame,
                text=tip,
                font=font_tuple(9),
                bg="#1e1e1e",
                fg="#6a9955",
                anchor="w"
            ).pack(anchor="w", pady=1)
        
        # 綁定滑鼠滾輪
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Canvas 已銷毀，忽略
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 窗口關閉時解綁事件
        def _on_close():
            try:
                canvas.unbind_all("<MouseWheel>")
            except:
                pass
            ref_window.destroy()
        
        ref_window.protocol("WM_DELETE_WINDOW", _on_close)
        
        # 確保視窗在編輯器之上
        ref_window.transient(self)
        ref_window.lift()
        ref_window.focus_force()
    
    def _insert_beginner_guide(self, parent_frame):
        """新增新手快速入門區塊（白話說明）- 可摺疊版本"""
        # 主容器
        container = tk.Frame(parent_frame, bg="#1e1e1e")
        container.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15), padx=5)
        
        # 摺疊狀態
        is_expanded = [True]  # 使用列表以便在閉包中修改
        
        # 快速入門標題（可點擊切換展開/收合）
        title_frame = tk.Frame(container, bg="#2d5a2d", cursor="hand2")
        title_frame.pack(fill="x")
        
        # 展開/收合圖示
        toggle_label = tk.Label(
            title_frame,
            text="▼",
            font=font_tuple(10),
            bg="#2d5a2d",
            fg="#ffffff"
        )
        toggle_label.pack(side="left", padx=10, pady=8)
        
        title_label = tk.Label(
            title_frame,
            text="🌟 5分鐘學會寫腳本 - 這些指令超簡單! (點擊收合/展開)",
            font=font_tuple(11, "bold"),
            bg="#2d5a2d",
            fg="#ffffff",
            cursor="hand2"
        )
        title_label.pack(side="left", pady=8)
        
        # 簡易說明內容區
        guide_frame = tk.Frame(container, bg="#1e1e1e", relief="groove", bd=1)
        guide_frame.pack(fill="x", pady=(5, 0))
        
        guide_items = [
            ("🖱️ 滑鼠操作", 
             "讓電腦幫你點滑鼠\n"
             "• 左鍵點擊(100,200) → 在座標 (100,200) 點一下\n"
             "• 不知道座標? 按「錄製」鈕,程式會自動記錄!"),
            
            ("⌨️ 鍵盤操作", 
             "讓電腦幫你打字或按按鍵\n"
             "• 按a → 按一下鍵盤的 A 鍵\n"
             "• 按ctrl+c → 按複製快捷鍵"),
            
            ("📷 圖片辨識", 
             "讓電腦「看」螢幕找圖片,找到後自動點擊\n"
             "• >左鍵點擊>登入按鈕 → 找到「登入按鈕」圖片並點擊\n"
             "• 按「圖片辨識」鈕可以自動截圖!"),
            
            ("📝 文字辨識", 
             "讓電腦「讀」螢幕上的文字\n"
             "• >OCR>歡迎 → 找到螢幕上的「歡迎」字樣\n"
             "• 可以用來判斷遊戲狀態或網頁內容"),
            
            ("🏷️ 標籤跳轉", 
             "標籤就像書籤,讓程式可以跳回去重複執行\n"
             "• #開始 → 設定一個叫「開始」的標籤\n"
             "• >>#開始 → 跳回「開始」標籤繼續執行"),
            
            ("⏱️ 延遲等待", 
             "讓程式暫停一下再繼續\n"
             "• >延遲>1s → 等待 1 秒\n"
             "• >延遲>500ms → 等待 0.5 秒 (1000ms = 1秒)"),
            
            ("🔀 條件判斷", 
             "根據情況決定下一步做什麼\n"
             "• >if>登入按鈕 → 如果找到「登入按鈕」就執行下面的指令\n"
             "• 找不到就跳過,繼續往下執行"),
            
            ("🔄 迴圈重複", 
             "讓一段指令重複執行多次\n"
             "• >迴圈>10 → 重複執行 10 次\n"
             "• >迴圈>無限 → 一直重複到按停止"),
        ]
        
        for i, (title, desc) in enumerate(guide_items):
            row_frame = tk.Frame(guide_frame, bg="#252526" if i % 2 == 0 else "#1e1e1e")
            row_frame.pack(fill="x", padx=5, pady=3)
            
            # 標題
            tk.Label(
                row_frame,
                text=title,
                font=font_tuple(10, "bold"),
                bg=row_frame["bg"],
                fg="#4ec9b0",
                width=12,
                anchor="nw"  # 改為左上對齊
            ).pack(side="left", padx=10, pady=8)
            
            # 說明 (支援多行)
            tk.Label(
                row_frame,
                text=desc,
                font=font_tuple(9),
                bg=row_frame["bg"],
                fg="#d4d4d4",
                anchor="w",
                wraplength=850,
                justify="left"
            ).pack(side="left", fill="both", expand=True, padx=5, pady=8)
        
        # 摺疊/展開功能
        def toggle_guide():
            if is_expanded[0]:
                guide_frame.pack_forget()
                toggle_label.config(text="▶")
                is_expanded[0] = False
            else:
                guide_frame.pack(fill="x", pady=(5, 0))
                toggle_label.config(text="▼")
                is_expanded[0] = True
        
        # 綁定點擊事件
        title_frame.bind("<Button-1>", lambda e: toggle_guide())
        title_label.bind("<Button-1>", lambda e: toggle_guide())
        toggle_label.bind("<Button-1>", lambda e: toggle_guide())
    
    def _configure_reference_tags(self, text_widget):
        """配置指令說明的文字標籤樣式（與編輯器一致）"""
        # 表格標題樣式
        text_widget.tag_config("header", foreground="#46DDC3", font=font_tuple(10, "bold"))
        
        # 表格框線樣式
        text_widget.tag_config("table_border", foreground="#569cd6")
        
        # 指令按鈕名稱
        text_widget.tag_config("button_name", foreground="#569cd6", font=font_tuple(10, "bold"))
        
        # ✅ 指令內容（與編輯器語法高亮完全相同）
        text_widget.tag_config("syntax_symbol", foreground="#d4d4d4")      # 淺灰色 - 符號
        text_widget.tag_config("syntax_time", foreground="#ce9178")        # 橘色 - 時間參數
        text_widget.tag_config("syntax_label", foreground="#4ec9b0")       # 青綠色 - 標籤
        text_widget.tag_config("syntax_keyboard", foreground="#9cdcfe")    # 淺藍色 - 鍵盤操作
        text_widget.tag_config("syntax_mouse", foreground="#569cd6")       # 藍色 - 滑鼠座標
        text_widget.tag_config("syntax_image", foreground="#4ec9b0")       # 青綠色 - 圖片辨識
        text_widget.tag_config("syntax_condition", foreground="#c586c0")   # 紫色 - 條件判斷
        text_widget.tag_config("syntax_ocr", foreground="#4ec9b0")         # 青綠色 - OCR 文字
        text_widget.tag_config("syntax_delay", foreground="#dcdcaa")       # 淺黃色 - 延遲控制
        text_widget.tag_config("syntax_flow", foreground="#c586c0")        # 紫色 - 流程控制
        text_widget.tag_config("syntax_picname", foreground="#ce9178")     # 橘色 - 圖片名稱
        text_widget.tag_config("syntax_comment", foreground="#6a9955")     # 綠色 - 註解
        text_widget.tag_config("syntax_operator", foreground="#d4d4d4")    # 淺灰色 - 操作符
        
        # 說明文字
        text_widget.tag_config("description", foreground="#b8c5d6")
    
    def _insert_command_reference_content(self, text_widget):
        """插入指令說明的內容"""
        # 定義所有指令的說明資料
        commands = [
            # 圖片相關指令
            ("圖片辨識", ">辨識>pic01, T=0s000", "截圖並儲存為pic01，用於圖片辨識"),
            ("範圍辨識", ">辨識>pic01, 範圍(100,100,500,500), T=0s000", "在指定螢幕範圍內辨識圖片"),
            ("移動至圖片", ">移動至>pic01, T=0s000", "移動滑鼠到圖片中心位置"),
            ("點擊圖片", ">左鍵點擊>pic01, T=0s000", "左鍵點擊圖片中心位置"),
            ("條件判斷", ">if>pic01, T=0s000\n>>#成功\n>>>#失敗", "判斷圖片是否存在，執行對應分支"),
            
            # 滑鼠操作
            ("左鍵點擊", ">左鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊左鍵"),
            ("右鍵點擊", ">右鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊右鍵"),
            ("左鍵點擊(無座標)", ">左鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊左鍵"),
            ("右鍵點擊(無座標)", ">右鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊右鍵"),
            ("滑鼠移動", ">移動至(100,200), 延遲0ms, T=0s000", "移動滑鼠到指定座標"),
            ("滑鼠滾輪", ">滾輪(1), 延遲0ms, T=0s000", "滾動滑鼠滾輪（正數向上，負數向下）"),
            
            # 鍵盤操作
            ("按下按鍵", ">按a, 延遲50ms, T=0s000", "按下並放開a鍵（含延遲時間）"),
            ("按下組合鍵", ">按下Ctrl,Shift,A, 延遲0ms, T=0s000", "同時按下多個按鍵（組合鍵）"),
            ("放開按鍵", ">放開a, 延遲0ms, T=0s000", "放開指定按鍵"),
            
            # 流程控制
            ("新增標籤", "#標籤名稱", "定義一個跳轉標籤"),
            ("跳轉標籤", ">>#標籤名稱", "跳轉到指定標籤（成功分支）"),
            ("條件失敗跳轉", ">>>#標籤名稱", "條件失敗時跳轉到指定標籤"),
            
            # OCR文字辨識
            ("OCR文字判斷", ">if文字>登入, T=0s000\n>>#找到\n>>>#沒找到", "判斷螢幕上是否有指定文字"),
            ("OCR等待文字", ">等待文字>完成, 最長10s, T=0s000", "等待指定文字出現（最長等待時間）"),
            ("OCR點擊文字", ">點擊文字>確認, T=0s000", "自動定位並點擊螢幕上的文字"),
            
            # 延遲控制
            ("延遲等待", ">延遲1000ms, T=0s000", "等待指定時間（毫秒）"),
            
            # 變數系統
            ("設定變數", ">設定變數>count, 0, T=0s000", "設定變數count的值為0"),
            ("變數加1", ">變數加1>count, T=0s000", "將變數count的值加1"),
            ("變數減1", ">變數減1>count, T=0s000", "將變數count的值減1"),
            ("變數條件", ">if變數>count, >=, 10, T=0s000\n>>#成功\n>>>#失敗", "判斷變數值，執行對應分支"),
            
            # 循環控制
            ("重複N次", ">重複>10次, T=0s000\n  # 在此處添加要重複的指令\n>重複結束, T=0s000", "重複執行指定次數"),
            ("條件循環", ">當圖片存在>loading, T=0s000\n  # 在此處添加循環內的指令\n>循環結束, T=0s000", "當條件滿足時持續循環"),
            
            # 多條件判斷
            ("全部圖片存在", ">if全部存在>pic01,pic02,pic03, T=0s000\n>>#全部找到\n>>>#缺少某個", "判斷所有圖片都存在"),
            ("任一圖片存在", ">if任一存在>pic01,pic02,pic03, T=0s000\n>>#找到其中一個\n>>>#全部都沒有", "判斷任一圖片存在"),
            
            # 隨機功能
            ("隨機延遲", ">隨機延遲>100ms,500ms, T=0s000", "在指定範圍內隨機延遲"),
            ("隨機分支", ">隨機執行>30%, T=0s000\n>>#執行A\n>>>#執行B", "按機率執行不同分支"),
            
            # 計數器與計時器
            ("計數器觸發", ">計數器>找圖失敗, 3次後, T=0s000\n>>#下一步", "計數達到指定次數後觸發"),
            ("計時器觸發", ">計時器>等待載入, 60秒後, T=0s000\n>>#超時處理", "時間達到後觸發"),
            ("重置計數器", ">重置計數器>找圖失敗, T=0s000", "重置指定計數器"),
            ("重置計時器", ">重置計時器>等待載入, T=0s000", "重置指定計時器"),
        ]
        
        # ✅ 定義欄位寬度（使用等寬字體確保對齊）
        col1_width = 22  # 指令按鈕
        col2_width = 50  # 指令內容
        col3_width = 40  # 說明
        
        # 輔助函數：計算顯示寬度（中文=2，英數=1）
        def display_width(text):
            return sum(2 if ord(c) > 127 else 1 for c in text)
        
        # 輔助函數：填充空格以達到指定寬度
        def pad_text(text, width):
            current_width = display_width(text)
            padding = ' ' * (width - current_width)
            return text + padding
        
        # 插入表格標題（固定在最上方）- 使用框線
        text_widget.insert("end", "┌" + "─" * (col1_width-2) + "┬" + "─" * (col2_width-2) + "┬" + "─" * (col3_width-2) + "┐\n", "table_border")
        text_widget.insert("end", "│ ", "table_border")
        text_widget.insert("end", pad_text('指令按鈕', col1_width-4), "header")
        text_widget.insert("end", " │ ", "table_border")
        text_widget.insert("end", pad_text('指令內容', col2_width-4), "header")
        text_widget.insert("end", " │ ", "table_border")
        text_widget.insert("end", pad_text('說明', col3_width-4), "header")
        text_widget.insert("end", " │\n", "table_border")
        text_widget.insert("end", "├" + "─" * (col1_width-2) + "┼" + "─" * (col2_width-2) + "┼" + "─" * (col3_width-2) + "┤\n", "table_border")
        
        # 插入每個指令
        for button_name, command, description in commands:
            # 左框線
            text_widget.insert("end", "│ ", "table_border")
            
            # 按鈕名稱（固定寬度，左對齊）
            text_widget.insert("end", pad_text(button_name, col1_width-4), "button_name")
            
            # 中框線
            text_widget.insert("end", " │ ", "table_border")
            
            # 指令內容（套用語法高亮，固定寬度）
            self._insert_highlighted_command(text_widget, command, col2_width-4)
            
            # 右框線
            text_widget.insert("end", " │ ", "table_border")
            
            # 說明（固定寬度，左對齊）
            text_widget.insert("end", pad_text(description, col3_width-4), "description")
            
            # 右框線和換行
            text_widget.insert("end", " │\n", "table_border")
        
        # 表格底部框線
        text_widget.insert("end", "└" + "─" * (col1_width-2) + "┴" + "─" * (col2_width-2) + "┴" + "─" * (col3_width-2) + "┘\n", "table_border")
        
        text_widget.insert("end", "\n")
        text_widget.insert("end", "提示：指令中的 T= 參數表示執行時間（格式：秒s毫秒，例如 T=1s500 表示 1.5 秒）\n", "description")
        text_widget.insert("end", "提示：所有座標和時間都可以根據需要調整\n", "description")
    
    def _insert_highlighted_command(self, text_widget, command, max_width):
        """插入帶語法高亮的指令內容（固定寬度，左對齊）"""
        # 將多行指令合併為單行顯示（用 | 分隔）
        lines = command.split('\n')
        display_text = ' | '.join(lines)
        
        # 計算實際顯示長度（考慮中文字符）
        actual_length = sum(2 if ord(c) > 127 else 1 for c in display_text)
        
        # 截斷過長的文字
        if actual_length > max_width:
            truncated = ""
            current_len = 0
            for c in display_text:
                char_width = 2 if ord(c) > 127 else 1
                if current_len + char_width > max_width - 3:
                    break
                truncated += c
                current_len += char_width
            display_text = truncated + "..."
            actual_length = current_len + 3
        
        # 套用語法高亮
        pos = 0
        while pos < len(display_text):
            # 操作符號 >
            if display_text[pos] == '>':
                text_widget.insert("end", display_text[pos], "syntax_operator")
                pos += 1
            # 註解 #
            elif display_text[pos] == '#':
                # 找到行尾或分隔符
                end = display_text.find('|', pos)
                if end == -1:
                    end = len(display_text)
                text_widget.insert("end", display_text[pos:end], "syntax_comment")
                pos = end
            # 時間標記 T=
            elif display_text[pos:pos+2] == 'T=':
                end = pos + 2
                while end < len(display_text) and display_text[end] not in ' ,|\n':
                    end += 1
                text_widget.insert("end", display_text[pos:end], "syntax_time")
                pos = end
            # 圖片名稱 pic
            elif display_text[pos:pos+3] == 'pic':
                end = pos + 3
                while end < len(display_text) and display_text[end] not in ' ,|\n>':
                    end += 1
                text_widget.insert("end", display_text[pos:end], "syntax_image")
                pos = end
            # 關鍵字
            elif display_text[pos:pos+2] in ['if', '辨識', '移動', '點擊', '按', '延遲', '設定', '重複', '當', '等待']:
                end = pos
                while end < len(display_text) and display_text[end] not in ' ,|\n>':
                    end += 1
                text_widget.insert("end", display_text[pos:end], "syntax_keyword")
                pos = end
            # 滑鼠操作
            elif any(keyword in display_text[pos:pos+10] for keyword in ['左鍵', '右鍵', '滾輪', '移動至']):
                end = pos
                while end < len(display_text) and display_text[end] not in ' ,|\n>(':
                    end += 1
                text_widget.insert("end", display_text[pos:end], "syntax_mouse")
                pos = end
            else:
                text_widget.insert("end", display_text[pos], "description")
                pos += 1
        
        # ✅ 補齊寬度（使用空格填充到固定寬度）
        padding = " " * (max_width - actual_length)
        text_widget.insert("end", padding)
    
    def _insert_treeview_commands(self, tree):
        """插入指令到 Treeview 表格（完美對齊）"""
        # 定義所有指令的說明資料
        commands = [
            # 圖片相關指令
            ("圖片辨識", ">辨識>pic01, T=0s000", "截圖並儲存為pic01，用於圖片辨識"),
            ("範圍辨識", ">辨識>pic01, 範圍(100,100,500,500), T=0s000", "在指定螢幕範圍內辨識圖片"),
            ("移動至圖片", ">移動至>pic01, T=0s000", "移動滑鼠到圖片中心位置"),
            ("點擊圖片", ">左鍵點擊>pic01, T=0s000", "左鍵點擊圖片中心位置"),
            ("條件判斷", ">if>pic01, T=0s000 | >>#成功 | >>>#失敗", "判斷圖片是否存在，執行對應分支"),
            
            # 滑鼠操作
            ("左鍵點擊", ">左鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊左鍵"),
            ("右鍵點擊", ">右鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊右鍵"),
            ("左鍵點擊(無座標)", ">左鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊左鍵"),
            ("右鍵點擊(無座標)", ">右鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊右鍵"),
            ("滑鼠移動", ">移動至(100,200), 延遲0ms, T=0s000", "移動滑鼠到指定座標"),
            ("滑鼠滾輪", ">滾輪(1), 延遲0ms, T=0s000", "滾動滑鼠滾輪（正數向上，負數向下）"),
            
            # 鍵盤操作
            ("按下按鍵", ">按a, 延遲50ms, T=0s000", "按下並放開a鍵（含延遲時間）"),
            ("按下組合鍵", ">按下Ctrl,Shift,A, 延遲0ms, T=0s000", "同時按下多個按鍵（組合鍵）"),
            ("放開按鍵", ">放開a, 延遲0ms, T=0s000", "放開指定按鍵"),
            
            # 流程控制
            ("新增標籤", "#標籤名稱", "定義一個跳轉標籤"),
            ("跳轉標籤", ">>#標籤名稱", "跳轉到指定標籤（成功分支）"),
            ("條件失敗跳轉", ">>>#標籤名稱", "條件失敗時跳轉到指定標籤"),
            
            # OCR文字辨識
            ("OCR文字判斷", ">if文字>登入, T=0s000 | >>#找到 | >>>#沒找到", "判斷螢幕上是否有指定文字"),
            ("OCR等待文字", ">等待文字>完成, 最長10s, T=0s000", "等待指定文字出現（最長等待時間）"),
            ("OCR點擊文字", ">點擊文字>確認, T=0s000", "自動定位並點擊螢幕上的文字"),
            
            # 延遲控制
            ("延遲等待", ">延遲1000ms, T=0s000", "等待指定時間（毫秒）"),
            
            # 變數系統
            ("設定變數", ">設定變數>count, 0, T=0s000", "設定變數count的值為0"),
            ("變數加1", ">變數加1>count, T=0s000", "將變數count的值加1"),
            ("變數減1", ">變數減1>count, T=0s000", "將變數count的值減1"),
            ("變數條件", ">if變數>count, >=, 10, T=0s000 | >>#成功 | >>>#失敗", "判斷變數值，執行對應分支"),
            
            # 循環控制
            ("重複N次", ">重複>10次, T=0s000 | >重複結束, T=0s000", "重複執行指定次數"),
            ("條件循環", ">當圖片存在>loading, T=0s000 | >循環結束, T=0s000", "當條件滿足時持續循環"),
            
            # 多條件判斷
            ("全部圖片存在", ">if全部存在>pic01,pic02,pic03, T=0s000 | >>#全部找到 | >>>#缺少某個", "判斷所有圖片都存在"),
            ("任一圖片存在", ">if任一存在>pic01,pic02,pic03, T=0s000 | >>#找到其中一個 | >>>#全部都沒有", "判斷任一圖片存在"),
            
            # 隨機功能
            ("隨機延遲", ">隨機延遲>100ms,500ms, T=0s000", "在指定範圍內隨機延遲"),
            ("隨機分支", ">隨機執行>30%, T=0s000 | >>#執行A | >>>#執行B", "按機率執行不同分支"),
            
            # 計數器與計時器
            ("計數器觸發", ">計數器>找圖失敗, 3次後, T=0s000 | >>#下一步", "計數達到指定次數後觸發"),
            ("計時器觸發", ">計時器>等待載入, 60秒後, T=0s000 | >>#超時處理", "時間達到後觸發"),
            ("重置計數器", ">重置計數器>找圖失敗, T=0s000", "重置指定計數器"),
            ("重置計時器", ">重置計時器>等待載入, T=0s000", "重置指定計時器"),
        ]
        
        # 插入每個指令到表格
        for button_name, command, description in commands:
            tree.insert("", "end", values=(button_name, command, description))
    
    def _insert_command_grid_table(self, parent_frame):
        """使用 grid 佈局插入指令表格"""
        # 定義所有指令的說明資料
        commands = [
            # 圖片相關指令
            ("圖片辨識", ">辨識>pic01, T=0s000", "截圖並儲存為pic01，用於圖片辨識"),
            ("範圍辨識", ">辨識>pic01, 範圍(100,100,500,500), T=0s000", "在指定螢幕範圍內辨識圖片"),
            ("移動至圖片", ">移動至>pic01, T=0s000", "移動滑鼠到圖片中心位置"),
            ("點擊圖片", ">左鍵點擊>pic01, T=0s000", "左鍵點擊圖片中心位置"),
            ("條件判斷", ">if>pic01, T=0s000 | >>#成功 | >>>#失敗", "判斷圖片是否存在，執行對應分支"),
            
            # 滑鼠操作
            ("左鍵點擊", ">左鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊左鍵"),
            ("右鍵點擊", ">右鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊右鍵"),
            ("左鍵點擊(無座標)", ">左鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊左鍵"),
            ("右鍵點擊(無座標)", ">右鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊右鍵"),
            ("滑鼠移動", ">移動至(100,200), 延遲0ms, T=0s000", "移動滑鼠到指定座標"),
            ("滑鼠滾輪", ">滾輪(1), 延遲0ms, T=0s000", "滾動滑鼠滾輪（正數向上，負數向下）"),
            
            # 鍵盤操作
            ("按下按鍵", ">按a, 延遲50ms, T=0s000", "按下並放開a鍵（含延遲時間）"),
            ("按下組合鍵", ">按下Ctrl,Shift,A, 延遲0ms, T=0s000", "同時按下多個按鍵（組合鍵）"),
            ("放開按鍵", ">放開a, 延遲0ms, T=0s000", "放開指定按鍵"),
            
            # 流程控制
            ("新增標籤", "#標籤名稱", "定義一個跳轉標籤"),
            ("跳轉標籤", ">>#標籤名稱", "跳轉到指定標籤（成功分支）"),
            ("條件失敗跳轉", ">>>#標籤名稱", "條件失敗時跳轉到指定標籤"),
            
            # OCR文字辨識
            ("OCR文字判斷", ">if文字>登入, T=0s000 | >>#找到 | >>>#沒找到", "判斷螢幕上是否有指定文字"),
            ("OCR等待文字", ">等待文字>完成, 最長10s, T=0s000", "等待指定文字出現（最長等待時間）"),
            ("OCR點擊文字", ">點擊文字>確認, T=0s000", "自動定位並點擊螢幕上的文字"),
            
            # 延遲控制
            ("延遲等待", ">延遲1000ms, T=0s000", "等待指定時間（毫秒）"),
            
            # 變數系統
            ("設定變數", ">設定變數>count, 0, T=0s000", "設定變數count的值為0"),
            ("變數加1", ">變數加1>count, T=0s000", "將變數count的值加1"),
            ("變數減1", ">變數減1>count, T=0s000", "將變數count的值減1"),
            ("變數條件", ">if變數>count, >=, 10, T=0s000 | >>#成功 | >>>#失敗", "判斷變數值，執行對應分支"),
            
            # 循環控制
            ("重複N次", ">重複>10次, T=0s000 | >重複結束, T=0s000", "重複執行指定次數"),
            ("條件循環", ">當圖片存在>loading, T=0s000 | >循環結束, T=0s000", "當條件滿足時持續循環"),
            
            # 多條件判斷
            ("全部圖片存在", ">if全部存在>pic01,pic02,pic03, T=0s000 | >>#全部找到 | >>>#缺少某個", "判斷所有圖片都存在"),
            ("任一圖片存在", ">if任一存在>pic01,pic02,pic03, T=0s000 | >>#找到其中一個 | >>>#全部都沒有", "判斷任一圖片存在"),
            
            # 隨機功能
            ("隨機延遲", ">隨機延遲>100ms,500ms, T=0s000", "在指定範圍內隨機延遲"),
            ("隨機分支", ">隨機執行>30%, T=0s000 | >>#執行A | >>>#執行B", "按機率執行不同分支"),
            
            # 計數器與計時器
            ("計數器觸發", ">計數器>找圖失敗, 3次後, T=0s000 | >>#下一步", "計數達到指定次數後觸發"),
            ("計時器觸發", ">計時器>等待載入, 60秒後, T=0s000 | >>#超時處理", "時間達到後觸發"),
            ("重置計數器", ">重置計數器>找圖失敗, T=0s000", "重置指定計數器"),
            ("重置計時器", ">重置計時器>等待載入, T=0s000", "重置指定計時器"),
        ]
        
        # 設定統一的欄位寬度（像素）
        col_widths = [150, 480, 320]  # 指令按鈕、指令內容、說明
        
        # 表頭（使用與資料列相同的結構確保對齊）
        base_row = 1  # 從 row=1 開始，row=0 被新手入門區塊使用
        header_frame = tk.Frame(parent_frame, bg="#2d2d30")
        header_frame.grid(row=base_row, column=0, columnspan=3, sticky="ew", padx=5)
        
        headers = ["指令按鈕", "指令內容", "說明"]
        for col, (header, width) in enumerate(zip(headers, col_widths)):
            label = tk.Label(
                header_frame,
                text=header,
                font=font_tuple(10, "bold"),
                bg="#2d2d30",
                fg="#ffffff",
                width=width // 8,  # 大約轉換為字元寬度
                padx=10,
                pady=8,
                anchor="w",
                relief="solid",
                borderwidth=1
            )
            label.pack(side="left", fill="x", expand=(col == 1))  # 中間欄位可伸縮
        
        # 插入指令資料（從 base_row + 1 開始）
        for row, (button_name, command, description) in enumerate(commands, start=base_row + 1):
            # 創建整行的框架
            row_frame = tk.Frame(parent_frame, bg="#1e1e1e", highlightthickness=2)
            row_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5)
            row_frame.config(highlightbackground="#1e1e1e", highlightcolor="#1e1e1e")
            
            # 按鈕名稱
            btn_label = tk.Label(
                row_frame,
                text=button_name,
                font=font_tuple(9),
                bg="#1e1e1e",
                fg="#569cd6",
                width=col_widths[0] // 8,
                padx=10,
                pady=5,
                anchor="w",
                relief="solid",
                borderwidth=1
            )
            btn_label.pack(side="left", fill="y")
            
            # 指令內容（帶語法高亮）
            cmd_frame = tk.Frame(row_frame, bg="#1e1e1e", relief="solid", borderwidth=1)
            cmd_frame.pack(side="left", fill="both", expand=True)
            
            cmd_text = tk.Text(
                cmd_frame,
                font=font_tuple(9, monospace=True),
                bg="#1e1e1e",
                fg="#d4d4d4",
                height=1,
                wrap="none",
                padx=10,
                pady=5,
                relief="flat",
                borderwidth=0
            )
            cmd_text.pack(fill="both", expand=True)
            
            # 配置語法高亮標籤
            self._configure_reference_tags(cmd_text)
            
            # 插入指令並套用高亮
            self._insert_command_with_syntax_highlight(cmd_text, command)
            cmd_text.config(state="disabled")
            
            # 說明
            desc_label = tk.Label(
                row_frame,
                text=description,
                font=font_tuple(9),
                bg="#1e1e1e",
                fg="#b8c5d6",
                width=col_widths[2] // 8,
                padx=10,
                pady=5,
                anchor="w",
                relief="solid",
                borderwidth=1,
                wraplength=col_widths[2] - 20
            )
            desc_label.pack(side="left", fill="y")
            
            # 為整行添加點擊事件，顯示選取框
            def make_click_handler(frame, labels):
                def on_click(event=None):
                    # 移除所有選取（改變邊框顏色而不是寬度,避免浮動）
                    for child in parent_frame.winfo_children():
                        if isinstance(child, tk.Frame) and child != parent_frame:
                            child.config(borderwidth=2, bg="#1e1e1e", highlightbackground="#1e1e1e", highlightcolor="#1e1e1e")
                            for widget in child.winfo_children():
                                if isinstance(widget, tk.Label):
                                    widget.config(bg="#1e1e1e")
                                elif isinstance(widget, tk.Frame):
                                    widget.config(bg="#1e1e1e")
                                    for sub in widget.winfo_children():
                                        if isinstance(sub, tk.Text):
                                            sub.config(bg="#1e1e1e")
                    
                    # 顯示當前選取（使用邊框顏色高亮,保持寬度不變）
                    frame.config(borderwidth=2, bg="#264f78", highlightbackground="#569cd6", highlightcolor="#569cd6")
                    for widget in labels:
                        if isinstance(widget, tk.Label):
                            widget.config(bg="#264f78")
                        elif isinstance(widget, tk.Frame):
                            widget.config(bg="#264f78")
                            for sub in widget.winfo_children():
                                if isinstance(sub, tk.Text):
                                    sub.config(bg="#264f78")
                return on_click
            
            widgets = [btn_label, cmd_frame, desc_label]
            click_handler = make_click_handler(row_frame, widgets)
            
            # 綁定點擊事件
            row_frame.bind("<Button-1>", click_handler)
            btn_label.bind("<Button-1>", click_handler)
            cmd_frame.bind("<Button-1>", click_handler)
            cmd_text.bind("<Button-1>", click_handler)
            desc_label.bind("<Button-1>", click_handler)
    
    def _insert_command_reference_with_highlight(self, text_widget):
        """插入帶語法高亮的指令說明（使用固定寬度對齊）"""
        # 定義所有指令的說明資料
        commands = [
            # 圖片相關指令
            ("圖片辨識", ">辨識>pic01, T=0s000", "截圖並儲存為pic01，用於圖片辨識"),
            ("範圍辨識", ">辨識>pic01, 範圍(100,100,500,500), T=0s000", "在指定螢幕範圍內辨識圖片"),
            ("移動至圖片", ">移動至>pic01, T=0s000", "移動滑鼠到圖片中心位置"),
            ("點擊圖片", ">左鍵點擊>pic01, T=0s000", "左鍵點擊圖片中心位置"),
            ("條件判斷", ">if>pic01, T=0s000 | >>#成功 | >>>#失敗", "判斷圖片是否存在，執行對應分支"),
            
            # 滑鼠操作
            ("左鍵點擊", ">左鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊左鍵"),
            ("右鍵點擊", ">右鍵點擊(100,200), 延遲50ms, T=0s000", "在指定座標點擊右鍵"),
            ("左鍵點擊(無座標)", ">左鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊左鍵"),
            ("右鍵點擊(無座標)", ">右鍵點擊, 延遲50ms, T=0s000", "在當前滑鼠位置點擊右鍵"),
            ("滑鼠移動", ">移動至(100,200), 延遲0ms, T=0s000", "移動滑鼠到指定座標"),
            ("滑鼠滾輪", ">滾輪(1), 延遲0ms, T=0s000", "滾動滑鼠滾輪（正數向上，負數向下）"),
            
            # 鍵盤操作
            ("按下按鍵", ">按a, 延遲50ms, T=0s000", "按下並放開a鍵（含延遲時間）"),
            ("按下組合鍵", ">按下Ctrl,Shift,A, 延遲0ms, T=0s000", "同時按下多個按鍵（組合鍵）"),
            ("放開按鍵", ">放開a, 延遲0ms, T=0s000", "放開指定按鍵"),
            
            # 流程控制
            ("新增標籤", "#標籤名稱", "定義一個跳轉標籤"),
            ("跳轉標籤", ">>#標籤名稱", "跳轉到指定標籤（成功分支）"),
            ("條件失敗跳轉", ">>>#標籤名稱", "條件失敗時跳轉到指定標籤"),
            
            # OCR文字辨識
            ("OCR文字判斷", ">if文字>登入, T=0s000 | >>#找到 | >>>#沒找到", "判斷螢幕上是否有指定文字"),
            ("OCR等待文字", ">等待文字>完成, 最長10s, T=0s000", "等待指定文字出現（最長等待時間）"),
            ("OCR點擊文字", ">點擊文字>確認, T=0s000", "自動定位並點擊螢幕上的文字"),
            
            # 延遲控制
            ("延遲等待", ">延遲1000ms, T=0s000", "等待指定時間（毫秒）"),
            
            # 變數系統
            ("設定變數", ">設定變數>count, 0, T=0s000", "設定變數count的值為0"),
            ("變數加1", ">變數加1>count, T=0s000", "將變數count的值加1"),
            ("變數減1", ">變數減1>count, T=0s000", "將變數count的值減1"),
            ("變數條件", ">if變數>count, >=, 10, T=0s000 | >>#成功 | >>>#失敗", "判斷變數值，執行對應分支"),
            
            # 循環控制
            ("重複N次", ">重複>10次, T=0s000 | >重複結束, T=0s000", "重複執行指定次數"),
            ("條件循環", ">當圖片存在>loading, T=0s000 | >循環結束, T=0s000", "當條件滿足時持續循環"),
            
            # 多條件判斷
            ("全部圖片存在", ">if全部存在>pic01,pic02,pic03, T=0s000 | >>#全部找到 | >>>#缺少某個", "判斷所有圖片都存在"),
            ("任一圖片存在", ">if任一存在>pic01,pic02,pic03, T=0s000 | >>#找到其中一個 | >>>#全部都沒有", "判斷任一圖片存在"),
            
            # 隨機功能
            ("隨機延遲", ">隨機延遲>100ms,500ms, T=0s000", "在指定範圍內隨機延遲"),
            ("隨機分支", ">隨機執行>30%, T=0s000 | >>#執行A | >>>#執行B", "按機率執行不同分支"),
            
            # 計數器與計時器
            ("計數器觸發", ">計數器>找圖失敗, 3次後, T=0s000 | >>#下一步", "計數達到指定次數後觸發"),
            ("計時器觸發", ">計時器>等待載入, 60秒後, T=0s000 | >>#超時處理", "時間達到後觸發"),
            ("重置計數器", ">重置計數器>找圖失敗, T=0s000", "重置指定計數器"),
            ("重置計時器", ">重置計時器>等待載入, T=0s000", "重置指定計時器"),
        ]
        
        # 計算顯示寬度的輔助函數（中文=2，英文=1）
        def display_width(text):
            return sum(2 if ord(c) > 127 else 1 for c in text)
        
        # 填充到指定寬度的輔助函數
        def pad_to_width(text, target_width):
            current = display_width(text)
            if current < target_width:
                return text + ' ' * (target_width - current)
            return text
        
        # 欄位寬度定義
        col1_width = 20  # 指令按鈕
        col2_width = 55  # 指令內容
        col3_width = 35  # 說明
        
        # 插入表頭
        text_widget.insert("end", "┌" + "─" * col1_width + "┬" + "─" * col2_width + "┬" + "─" * col3_width + "┐\n", "header")
        text_widget.insert("end", "│ ", "header")
        text_widget.insert("end", pad_to_width("指令按鈕", col1_width-1), "header")
        text_widget.insert("end", "│ ", "header")
        text_widget.insert("end", pad_to_width("指令內容", col2_width-1), "header")
        text_widget.insert("end", "│ ", "header")
        text_widget.insert("end", pad_to_width("說明", col3_width-1), "header")
        text_widget.insert("end", "│\n", "header")
        text_widget.insert("end", "├" + "─" * col1_width + "┼" + "─" * col2_width + "┼" + "─" * col3_width + "┤\n", "header")
        
        # 插入每個指令
        for button_name, command, description in commands:
            text_widget.insert("end", "│ ", "description")
            
            # 插入按鈕名稱（固定寬度）
            text_widget.insert("end", pad_to_width(button_name, col1_width-1), "button_name")
            text_widget.insert("end", "│ ", "description")
            
            # 插入指令內容（帶語法高亮，固定寬度）
            cmd_start = text_widget.index("end-1c")
            self._insert_command_with_syntax_highlight(text_widget, command)
            cmd_text = text_widget.get(cmd_start, "end-1c")
            cmd_width = display_width(cmd_text)
            if cmd_width < col2_width - 1:
                text_widget.insert("end", ' ' * (col2_width - 1 - cmd_width))
            
            text_widget.insert("end", "│ ", "description")
            
            # 插入說明（固定寬度）
            text_widget.insert("end", pad_to_width(description, col3_width-1), "description")
            text_widget.insert("end", "│\n", "description")
        
        # 表格底部
        text_widget.insert("end", "└" + "─" * col1_width + "┴" + "─" * col2_width + "┴" + "─" * col3_width + "┘\n", "header")
    
    def _insert_command_with_syntax_highlight(self, text_widget, command):
        """插入單一指令並套用語法高亮（與編輯器相同配色）"""
        lines = command.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                text_widget.insert("end", " ")  # 多行用空格分隔
            
            pos = 0
            while pos < len(line):
                # 操作符號 >
                if line[pos] == '>':
                    text_widget.insert("end", line[pos], "syntax_symbol")
                    pos += 1
                # 註解 #
                elif line[pos] == '#':
                    text_widget.insert("end", line[pos:], "syntax_comment")
                    break
                # 時間標記 T=
                elif line[pos:pos+2] == 'T=':
                    end = pos + 2
                    while end < len(line) and line[end] not in ' ,\n':
                        end += 1
                    text_widget.insert("end", line[pos:end], "syntax_time")
                    pos = end
                # 圖片名稱 pic
                elif line[pos:pos+3] == 'pic':
                    end = pos + 3
                    while end < len(line) and line[end] not in ' ,\n>':
                        end += 1
                    text_widget.insert("end", line[pos:end], "syntax_image")
                    pos = end
                # 標籤相關
                elif line[pos:pos+2] in ['if', '辨識', '移動', '點擊', '等待', '設定', '重複', '當', '延遲']:
                    end = pos
                    while end < len(line) and line[end] not in ' ,>\n':
                        end += 1
                    keyword = line[pos:end]
                    
                    # 根據關鍵字類型選擇標籤
                    if keyword in ['if', 'if文字', 'if變數', 'if全部存在', 'if任一存在']:
                        tag = "syntax_condition"
                    elif keyword in ['辨識', '移動至', '點擊圖片']:
                        tag = "syntax_image"
                    elif keyword in ['點擊文字', '等待文字']:
                        tag = "syntax_ocr"
                    elif keyword in ['延遲', '隨機延遲']:
                        tag = "syntax_delay"
                    elif keyword in ['重複', '重複結束', '當', '循環結束', '隨機執行']:
                        tag = "syntax_flow"
                    else:
                        tag = "syntax_label"
                    
                    text_widget.insert("end", keyword, tag)
                    pos = end
                # 滑鼠操作
                elif any(keyword in line[pos:pos+10] for keyword in ['左鍵', '右鍵', '滾輪', '移動至', '按', '按下', '放開']):
                    end = pos
                    while end < len(line) and line[end] not in ' ,\n>(':
                        end += 1
                    keyword = line[pos:end]
                    
                    if keyword in ['左鍵', '右鍵', '滾輪', '左鍵點擊', '右鍵點擊', '移動至']:
                        tag = "syntax_mouse"
                    else:
                        tag = "syntax_keyboard"
                    
                    text_widget.insert("end", keyword, tag)
                    pos = end
                # 變數操作
                elif line[pos:pos+4] in ['設定變數', '變數加1', '變數減1']:
                    end = pos + 4
                    text_widget.insert("end", line[pos:end], "syntax_flow")
                    pos = end
                # 計數器/計時器
                elif line[pos:pos+3] in ['計數器', '計時器'] or line[pos:pos+5] in ['重置計數器', '重置計時器']:
                    end = pos
                    while end < len(line) and line[end] not in ' ,>\n':
                        end += 1
                    text_widget.insert("end", line[pos:end], "syntax_flow")
                    pos = end
                else:
                    text_widget.insert("end", line[pos], "description")
                    pos += 1
    
    def _on_combo_click(self, event):
        """點擊下拉選單時刷新列表"""
        self._refresh_script_list()
    
    def _refresh_script_list(self):
        """刷新腳本下拉選單內容"""
        script_dir = os.path.join(os.getcwd(), "scripts")
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        
        # 獲取所有腳本（去除副檔名）
        scripts = [f for f in os.listdir(script_dir) if f.endswith('.json')]
        display_scripts = [os.path.splitext(f)[0] for f in scripts]
        
        # 第一個選項固定為"新增腳本"
        all_options = ["新增腳本"] + sorted(display_scripts)
        self.script_combo['values'] = all_options
    
    def _on_script_selected(self, event):
        """處理腳本選擇事件"""
        selected = self.script_var.get()
        
        if selected == "新增腳本":
            # 彈出簡單命名對話框
            self._show_create_script_dialog()
        else:
            # 載入選中的腳本
            script_dir = os.path.join(os.getcwd(), "scripts")
            self.script_path = os.path.join(script_dir, selected + ".json")
            
            # 載入前檢查檔案是否存在且有效
            if os.path.exists(self.script_path):
                try:
                    with open(self.script_path, 'r', encoding='utf-8') as f:
                        test_data = json.load(f)
                    # 檢查是否為有效的腳本格式
                    if isinstance(test_data, dict) and ("events" in test_data or "settings" in test_data):
                        self._load_script()
                    else:
                        self._show_message("錯誤", f"腳本格式不正確：{selected}", "error")
                except Exception as e:
                    self._show_message("錯誤", f"無法讀取腳本：{e}", "error")
            else:
                self._show_message("警告", f"腳本檔案不存在：{selected}", "warning")
    
    def _show_create_script_dialog(self):
        """顯示新增腳本命名對話框"""
        dialog = tk.Toplevel(self)
        dialog.title("")
        dialog.geometry("300x100")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # 文字輸入框
        entry_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=entry_var, font=font_tuple(11), width=25)
        entry.pack(padx=20, pady=20)
        entry.focus()
        
        # 確定按鈕
        def on_confirm():
            name = entry_var.get().strip()
            if name:
                dialog.result = name
                dialog.destroy()
        
        btn = tk.Button(dialog, text="確定", command=on_confirm, 
                       font=font_tuple(10), bg="#4CAF50", fg="white",
                       padx=30, pady=5)
        btn.pack(pady=5)
        
        # 綁定 Enter 鍵
        entry.bind('<Return>', lambda e: on_confirm())
        
        # 置中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.result = None
        dialog.wait_window()
        
        # 如果有輸入名稱，創建腳本
        if dialog.result:
            self._create_custom_script(dialog.result)
    
    def _create_custom_script(self, custom_name):
        """建立自訂腳本"""
        custom_name = custom_name.strip()
        
        # 檢查檔名是否合法
        if any(char in custom_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            self._show_message("錯誤", "檔名包含非法字元", "error")
            return
        
        script_dir = os.path.join(os.getcwd(), "scripts")
        script_path = os.path.join(script_dir, custom_name + ".json")
        
        # 檢查檔案是否已存在
        if os.path.exists(script_path):
            self._show_message("提示", f"腳本「{custom_name}」已存在", "warning")
            return
        
        # 建立空白腳本
        try:
            empty_script = {
                "events": [],
                "settings": {
                    "speed": "100",
                    "repeat": "1",
                    "repeat_time": "00:00:00",
                    "repeat_interval": "00:00:00"
                }
            }
            
            with open(script_path, 'w', encoding='utf-8') as f:
                json.dump(empty_script, f, ensure_ascii=False, indent=2)
            
            # 設定為當前腳本
            self.script_path = script_path
            
            # 載入空白腳本
            self.text_editor.delete("1.0", "end")
            # 不再顯示標題文字，直接空白
            
            # 刷新列表並選中新腳本
            self._refresh_script_list()
            self.script_var.set(custom_name)
            
            self.status_label.config(
                text=f"已建立新腳本: {custom_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
            
        except Exception as e:
            self._show_message("錯誤", f"建立腳本失敗:\n{e}", "error")
    
    def _load_script(self):
        """載入腳本並轉換為文字指令"""
        if not self.script_path or not os.path.exists(self.script_path):
            self.text_editor.delete("1.0", "end")
            # 不再顯示標題文字，直接空白
            return
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 保存原始設定（防止儲存時被預設值覆蓋）
            if isinstance(data, dict) and "settings" in data:
                self.original_settings = data["settings"].copy()
            elif isinstance(data, dict) and "events" in data:
                # 舊格式：沒有 settings 區塊，使用預設值
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
            else:
                # 純 events 陣列格式
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
            
            # 轉換為文字指令（增加錯誤處理）
            try:
                text_commands = self._json_to_text(data)
                
                # 檢查轉換結果是否有效（避免載入空內容）
                if not text_commands or text_commands.strip() == "":
                    raise ValueError("轉換結果為空")
                
                # 只有轉換成功且有內容才更新編輯器
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", text_commands)
                
                # 載入後套用語法高亮
                self._apply_syntax_highlighting()
                
                # ✨ 自動摺疊所有軌跡（如果啟用簡化顯示）
                if self.simplify_display_var.get():
                    self.after(100, self._auto_fold_all_trajectories)
                
                self._update_status(
                    f"已載入: {os.path.basename(self.script_path)} ({len(data.get('events', []))}筆事件)",
                    "success"
                )
            except Exception as convert_error:
                # 轉換失敗不清空編輯器，顯示錯誤訊息
                import traceback
                error_detail = traceback.format_exc()
                
                error_msg = f"# 轉換失敗：{convert_error}\n\n"
                error_msg += f"# 錯誤詳情：\n# {error_detail.replace(chr(10), chr(10) + '# ')}\n\n"
                error_msg += "# 原始 JSON 資料：\n"
                error_msg += json.dumps(data, ensure_ascii=False, indent=2)
                
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", error_msg)
                
                self._update_status(f"警告: 轉換失敗: {convert_error}", "warning")
                
                self._show_message(
                    "警告", 
                    f"腳本轉換失敗，可能包含異常資料：\n\n{convert_error}\n\n"
                    f"已顯示原始 JSON 資料，請查看日誌或手動修復。",
                    "warning"
                )
            
        except Exception as e:
            self._show_message("錯誤", f"載入腳本失敗:\n{e}", "error")
            self._update_status(f"錯誤: 載入失敗: {e}", "error")
    
    def _json_to_text(self, data: Dict) -> str:
        """將JSON事件轉換為文字指令"""
        events = data.get("events", [])
        lines = []  # 不再添加標題文字
        
        # 空腳本處理
        if not events:
            lines.append("# 此腳本無事件\n")
            lines.append("# 請先錄製操作或手動新增指令\n")
            return "".join(lines)
        
        # 記錄按下但未放開的按鍵
        pressed_keys = {}
        start_time = events[0]["time"] if events else 0
        
        # 逐迴所有事件，增加異常處理
        for idx, event in enumerate(events):
            try:
                event_type = event.get("type")
                event_name = event.get("event")
                time_offset = event.get("time", 0) - start_time
                
                # 格式化時間
                time_str = self._format_time(time_offset)
                
                # 標籤事件 (跳轉目標)
                if event_type == "label":
                    label_name = event.get("name", "")
                    lines.append(f"#{label_name}\n")
                
                # 備註事件
                elif event_type == "comment":
                    comment_text = event.get("text", "")
                    lines.append(f"# {comment_text}\n")
                
                # 分隔符事件
                elif event_type == "separator":
                    separator_char = event.get("char", "=")
                    lines.append(f"{separator_char * 3}\n")
                
                elif event_type == "keyboard":
                    key_name = event.get("name", "")
                    
                    # 🔧 檢查特殊標記
                    is_press = event.get("_is_press", False)
                    is_release = event.get("_is_release", False)
                    auto_pair = event.get("_auto_pair", False)
                    
                    if event_name == "down":
                        if is_press:
                            # 獨立的按下指令
                            press_delay = event.get("_press_delay", 0)  # 讀取保存的延遲
                            lines.append(f">按下{key_name}, 延遲{press_delay}ms, T={time_str}\n")
                        elif auto_pair:
                            # 自動配對的按下，記錄但不輸出
                            pressed_keys[key_name] = time_offset
                        else:
                            # 記錄按下時間（等待配對）
                            pressed_keys[key_name] = time_offset
                        
                    elif event_name == "up":
                        if is_release:
                            # 獨立的放開指令
                            lines.append(f">放開{key_name}, 延遲0ms, T={time_str}\n")
                        elif auto_pair and key_name in pressed_keys:
                            # 自動配對的放開，輸出完整的按鍵指令
                            press_time = pressed_keys[key_name]
                            duration = round((time_offset - press_time) * 1000)
                            press_time_str = self._format_time(press_time)
                            lines.append(f">按{key_name}, 延遲{duration}ms, T={press_time_str}\n")
                            del pressed_keys[key_name]
                        elif key_name in pressed_keys:
                            # 普通配對
                            press_time = pressed_keys[key_name]
                            duration = round((time_offset - press_time) * 1000)
                            press_time_str = self._format_time(press_time)
                            lines.append(f">按{key_name}, 延遲{duration}ms, T={press_time_str}\n")
                            del pressed_keys[key_name]
                
                elif event_type == "mouse":
                    x = event.get("x", 0)
                    y = event.get("y", 0)
                    
                    if event_name == "move":
                        lines.append(f">移動至({x},{y}), 延遲0ms, T={time_str}\n")
                    
                    elif event_name == "down":
                        button = event.get("button", "left")
                        # 檢查下一個事件是否為同一按鈕的 up（為了簡化指令）
                        next_event = events[idx + 1] if idx + 1 < len(events) else None
                        if (next_event and 
                            next_event.get("type") == "mouse" and 
                            next_event.get("event") == "up" and 
                            next_event.get("button") == button and
                            next_event.get("x") == x and 
                            next_event.get("y") == y):
                            # 這是一個完整的點擊動作，轉為點擊指令
                            next_time = next_event.get("time", 0)
                            duration_ms = round((next_time - event.get("time", 0)) * 1000)  # 🔥 使用 round 四捨五入
                            button_name = "左鍵" if button == "left" else "右鍵" if button == "right" else "中鍵"
                            lines.append(f">{button_name}點擊({x},{y}), 延遲{duration_ms}ms, T={time_str}\n")
                            # 標記下一個事件已處理（跳過）
                            event["_skip_next"] = True
                        else:
                            # 僅按下，沒有對應的放開
                            lines.append(f">按下{button}鍵({x},{y}), 延遲0ms, T={time_str}\n")
                    
                    elif event_name == "up":
                        # 檢查前一個事件是否已處理過這個 up
                        prev_event = events[idx - 1] if idx > 0 else None
                        if prev_event and prev_event.get("_skip_next"):
                            # 這個 up 已經被合併到 down 中，跳過
                            continue
                        else:
                            # 獨立的放開動作
                            button = event.get("button", "left")
                            lines.append(f">放開{button}鍵({x},{y}), 延遲0ms, T={time_str}\n")
                    
                    elif event_name == "wheel":
                        # 滾輪事件
                        delta = event.get("delta", 1)
                        lines.append(f">滾輪({delta}), 延遲0ms, T={time_str}\n")
                
                # 範圍結束
                elif event_type == "region_end":
                    lines.append(f">範圍結束, T={time_str}\n")
                
                # 獨立的分支指令
                elif event_type == "branch_success":
                    if event.get("_standalone", False):
                        target = event.get("target", "")
                        repeat_count = event.get("repeat_count", 999999)
                        if repeat_count == 999999:
                            lines.append(f">>#{ target}\n")
                        else:
                            lines.append(f">>#{ target}, *{repeat_count}\n")
                
                elif event_type == "branch_failure":
                    if event.get("_standalone", False):
                        target = event.get("target", "")
                        repeat_count = event.get("repeat_count", 999999)
                        if repeat_count == 999999:
                            lines.append(f">>>#{ target}\n")
                        else:
                            lines.append(f">>>#{ target}, *{repeat_count}\n")
                
                # 圖片辨識指令
                elif event_type == "recognize_image":
                    pic_name = event.get("image", "")
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    
                    # 建立選項列表
                    options = []
                    if show_border:
                        options.append("邊框")
                    if region:
                        options.append(f"範圍({region[0]},{region[1]},{region[2]},{region[3]})")
                    
                    # 組合指令
                    cmd = f">辨識>{pic_name}"
                    if options:
                        cmd += ", " + ", ".join(options)
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                
                elif event_type == "move_to_image":
                    pic_name = event.get("image", "")
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    
                    # 建立選項列表
                    options = []
                    if show_border:
                        options.append("邊框")
                    if region:
                        options.append(f"範圍({region[0]},{region[1]},{region[2]},{region[3]})")
                    
                    # 組合指令
                    cmd = f">移動至>{pic_name}"
                    if options:
                        cmd += ", " + ", ".join(options)
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                
                # ==================== OCR 文字辨識事件格式化 ====================
                elif event_type == "if_text_exists":
                    target_text = event.get("target_text", "")
                    lines.append(f">if文字>{target_text}, T={time_str}\n")
                    
                    # 成功分支
                    on_success = event.get("on_success", {})
                    if on_success:
                        branch_text = self._format_branch_action(on_success)
                        lines.append(f">>{branch_text}\n")
                    
                    # 失敗分支
                    on_failure = event.get("on_failure", {})
                    if on_failure:
                        branch_text = self._format_branch_action(on_failure)
                        lines.append(f">>>{branch_text}\n")
                
                elif event_type == "wait_text":
                    target_text = event.get("target_text", "")
                    timeout = event.get("timeout", 10.0)
                    lines.append(f">等待文字>{target_text}, 最長{timeout}s, T={time_str}\n")
                
                elif event_type == "click_text":
                    target_text = event.get("target_text", "")
                    lines.append(f">點擊文字>{target_text}, T={time_str}\n")
                
                elif event_type == "click_image":
                    pic_name = event.get("image", "")
                    button = event.get("button", "left")
                    button_name = "左鍵" if button == "left" else "右鍵"
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    click_radius = event.get("click_radius", 0)
                    click_offset_mode = event.get("click_offset_mode", "center")
                    
                    # 建立選項列表
                    options = []
                    if event.get("return_to_origin", False):
                        options.append("返回")
                    if show_border:
                        options.append("邊框")
                    if region:
                        options.append(f"範圍({region[0]},{region[1]},{region[2]},{region[3]})")
                    if click_radius > 0:
                        options.append(f"半徑({click_radius})")
                        if click_offset_mode == 'random':
                            options.append("隨機")
                        elif click_offset_mode == 'tracking':
                            options.append("追蹤")
                    
                    # 組合指令
                    cmd = f">{button_name}點擊>{pic_name}"
                    if options:
                        cmd += ", " + ", ".join(options)
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                
                elif event_type == "if_image_exists":
                    pic_name = event.get("image", "")
                    on_success = event.get("on_success", {})
                    on_failure = event.get("on_failure", {})
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    is_pure_recognize = event.get("is_pure_recognize", False)
                    
                    # ✨ 如果是純辨識（從>>辨識>轉換來的），輸出為辨識格式
                    if is_pure_recognize:
                        cmd = f">辨識>{pic_name}"
                    else:
                        # 使用新的簡化格式：>if>pic01, T=xxx
                        cmd = f">if>{pic_name}"
                    
                    if show_border:
                        cmd += ", 邊框"
                    if region:
                        cmd += f", 範圍({region[0]},{region[1]},{region[2]},{region[3]})"
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                    
                    # 格式化分支動作（使用 >> 和 >>> 格式）
                    if on_success:
                        success_action = self._format_branch_action(on_success)
                        # 只在有實際內容時才添加分支行
                        if success_action or on_success.get("action") != "continue":
                            lines.append(f">>{success_action}\n")
                    
                    if on_failure:
                        failure_action = self._format_branch_action(on_failure)
                        # 只在有實際內容時才添加分支行
                        if failure_action or on_failure.get("action") != "continue":
                            lines.append(f">>>{failure_action}\n")
                
                elif event_type == "recognize_any":
                    images = event.get("images", [])
                    pic_names = [img.get("name", "") for img in images]
                    pic_list = "|".join(pic_names)
                    lines.append(f">辨識任一>{pic_list}, T={time_str}\n")
                
                # 延遲事件
                elif event_type == "delay":
                    duration_ms = int(event.get("duration", 0) * 1000)
                    lines.append(f">延遲{duration_ms}ms, T={time_str}\n")
                
                # 戰鬥指令
                elif event_type in ["start_combat", "find_and_attack", "loop_attack", "smart_combat", "set_combat_region", "pause_combat", "resume_combat", "stop_combat"]:
                    combat_line = self._format_combat_event(event)
                    if combat_line:
                        lines.append(f">{combat_line}, T={time_str}\n")
                
                # ==================== v2.7.1+ 新增事件類型格式化 ====================
                
                # 變數設定
                elif event_type == "set_variable":
                    name = event.get("name", "")
                    value = event.get("value", 0)
                    lines.append(f">設定變數>{name}, {value}, T={time_str}\n")
                
                # 變數運算
                elif event_type == "variable_operation":
                    name = event.get("name", "")
                    operation = event.get("operation", "add")
                    if operation == "add":
                        lines.append(f">變數加1>{name}, T={time_str}\n")
                    elif operation == "subtract":
                        lines.append(f">變數減1>{name}, T={time_str}\n")
                
                # 變數條件判斷
                elif event_type == "if_variable":
                    name = event.get("name", "")
                    operator = event.get("operator", "==")
                    value = event.get("value", 0)
                    on_success = event.get("on_success", {})
                    on_failure = event.get("on_failure", {})
                    
                    lines.append(f">if變數>{name}, {operator}, {value}, T={time_str}\n")
                    
                    if on_success:
                        success_action = self._format_branch_action(on_success)
                        if success_action or on_success.get("action") != "continue":
                            lines.append(f">>{success_action}\n")
                    
                    if on_failure:
                        failure_action = self._format_branch_action(on_failure)
                        if failure_action or on_failure.get("action") != "continue":
                            lines.append(f">>>{failure_action}\n")
                
                # 循環開始
                elif event_type == "loop_start":
                    loop_type = event.get("loop_type", "repeat")
                    if loop_type == "repeat":
                        max_count = event.get("max_count", 1)
                        lines.append(f">重複>{max_count}次, T={time_str}\n")
                    elif loop_type == "while":
                        condition = event.get("condition", {})
                        if condition.get("type") == "image_exists":
                            image = condition.get("image", "")
                            lines.append(f">當圖片存在>{image}, T={time_str}\n")
                
                # 循環結束
                elif event_type == "loop_end":
                    lines.append(f">循環結束, T={time_str}\n")
                
                # 多條件判斷（AND）
                elif event_type == "if_all_images_exist":
                    images = event.get("images", [])
                    images_str = ",".join(images)
                    on_success = event.get("on_success", {})
                    on_failure = event.get("on_failure", {})
                    
                    lines.append(f">if全部存在>{images_str}, T={time_str}\n")
                    
                    if on_success:
                        success_action = self._format_branch_action(on_success)
                        if success_action or on_success.get("action") != "continue":
                            lines.append(f">>{success_action}\n")
                    
                    if on_failure:
                        failure_action = self._format_branch_action(on_failure)
                        if failure_action or on_failure.get("action") != "continue":
                            lines.append(f">>>{failure_action}\n")
                
                # 多條件判斷（OR）
                elif event_type == "if_any_image_exists":
                    images = event.get("images", [])
                    images_str = ",".join(images)
                    on_success = event.get("on_success", {})
                    on_failure = event.get("on_failure", {})
                    
                    lines.append(f">if任一存在>{images_str}, T={time_str}\n")
                    
                    if on_success:
                        success_action = self._format_branch_action(on_success)
                        if success_action or on_success.get("action") != "continue":
                            lines.append(f">>{success_action}\n")
                    
                    if on_failure:
                        failure_action = self._format_branch_action(on_failure)
                        if failure_action or on_failure.get("action") != "continue":
                            lines.append(f">>>{failure_action}\n")
                
                # 隨機延遲
                elif event_type == "random_delay":
                    min_ms = event.get("min_ms", 100)
                    max_ms = event.get("max_ms", 500)
                    lines.append(f">隨機延遲>{min_ms}ms,{max_ms}ms, T={time_str}\n")
                
                # 隨機分支
                elif event_type == "random_branch":
                    probability = event.get("probability", 50)
                    on_success = event.get("on_success", {})
                    on_failure = event.get("on_failure", {})
                    
                    lines.append(f">隨機執行>{probability}%, T={time_str}\n")
                    
                    if on_success:
                        success_action = self._format_branch_action(on_success)
                        if success_action or on_success.get("action") != "continue":
                            lines.append(f">>{success_action}\n")
                    
                    if on_failure:
                        failure_action = self._format_branch_action(on_failure)
                        if failure_action or on_failure.get("action") != "continue":
                            lines.append(f">>>{failure_action}\n")
                
                # 計數器觸發
                elif event_type == "counter_trigger":
                    action_id = event.get("action_id", "")
                    count = event.get("count", 3)
                    on_trigger = event.get("on_trigger", {})
                    
                    lines.append(f">計數器>{action_id}, {count}次後, T={time_str}\n")
                    
                    if on_trigger:
                        trigger_action = self._format_branch_action(on_trigger)
                        if trigger_action or on_trigger.get("action") != "continue":
                            lines.append(f">>{trigger_action}\n")
                
                # 計時器觸發
                elif event_type == "timer_trigger":
                    action_id = event.get("action_id", "")
                    duration = event.get("duration", 60)
                    on_trigger = event.get("on_trigger", {})
                    
                    lines.append(f">計時器>{action_id}, {duration}秒後, T={time_str}\n")
                    
                    if on_trigger:
                        trigger_action = self._format_branch_action(on_trigger)
                        if trigger_action or on_trigger.get("action") != "continue":
                            lines.append(f">>{trigger_action}\n")
                
                # 重置計數器
                elif event_type == "reset_counter":
                    action_id = event.get("action_id", "")
                    lines.append(f">重置計數器>{action_id}, T={time_str}\n")
                
                # 重置計時器
                elif event_type == "reset_timer":
                    action_id = event.get("action_id", "")
                    lines.append(f">重置計時器>{action_id}, T={time_str}\n")
                
                # 開始（延遲開始）
                elif event_type == "delayed_start":
                    delay_seconds = event.get("delay_seconds", 10)
                    lines.append(f">開始>{delay_seconds}秒後, T={time_str}\n")
                
                # 結束（延遲結束）
                elif event_type == "delayed_end":
                    delay_seconds = event.get("delay_seconds", 60)
                    lines.append(f">結束>{delay_seconds}秒後, T={time_str}\n")
                
                # ==================== 觸發器系統輸出 ====================
                
                # 定時觸發器
                elif event_type == "interval_trigger":
                    interval_ms = event.get("interval_ms", 30000)
                    actions = event.get("actions", [])
                    
                    # 轉換為最佳單位
                    if interval_ms >= 60000 and interval_ms % 60000 == 0:
                        lines.append(f">每隔>{interval_ms // 60000}分鐘\n")
                    elif interval_ms >= 1000 and interval_ms % 1000 == 0:
                        lines.append(f">每隔>{interval_ms // 1000}秒\n")
                    else:
                        lines.append(f">每隔>{interval_ms}ms\n")
                    
                    for action in actions:
                        lines.append(f"{action}\n")
                    lines.append(">每隔結束\n")
                
                # 條件觸發器
                elif event_type == "condition_trigger":
                    target = event.get("target", "")
                    cooldown_ms = event.get("cooldown_ms", 5000)
                    actions = event.get("actions", [])
                    
                    cooldown_str = f"{cooldown_ms // 1000}秒" if cooldown_ms >= 1000 else f"{cooldown_ms}ms"
                    lines.append(f">當偵測到>{target}, 冷卻{cooldown_str}\n")
                    
                    for action in actions:
                        lines.append(f"{action}\n")
                    lines.append(">當偵測結束\n")
                
                # 優先觸發器
                elif event_type == "priority_trigger":
                    target = event.get("target", "")
                    actions = event.get("actions", [])
                    
                    lines.append(f">優先偵測>{target}\n")
                    
                    for action in actions:
                        lines.append(f"{action}\n")
                    lines.append(">優先偵測結束\n")
                
                # 並行區塊
                elif event_type == "parallel_block":
                    threads = event.get("threads", [])
                    
                    lines.append(">並行開始\n")
                    
                    for thread in threads:
                        thread_name = thread.get("name", "")
                        actions = thread.get("actions", [])
                        lines.append(f">線程>{thread_name}\n")
                        for action in actions:
                            lines.append(f"  {action}\n")
                        lines.append(">線程結束\n")
                    
                    lines.append(">並行結束\n")
                
                # 狀態機
                elif event_type == "state_machine":
                    machine_name = event.get("name", "")
                    states = event.get("states", {})
                    initial_state = event.get("initial_state", "")
                    
                    lines.append(f">狀態機>{machine_name}\n")
                    
                    for state_name, state_data in states.items():
                        is_initial = (state_name == initial_state)
                        initial_flag = ", 初始" if is_initial else ""
                        lines.append(f">狀態>{state_name}{initial_flag}\n")
                        
                        for action in state_data.get("actions", []):
                            lines.append(f"  {action}\n")
                    
                    lines.append(">狀態機結束\n")
            
            except Exception as event_error:
                # 異常事件跳過，記錄錯誤
                lines.append(f"# 事件{idx}轉換失敗: {event_error}\n")
                lines.append(f"# 異常事件: {event}\n\n")
                continue
        
        # 處理未放開的按鍵
        if pressed_keys:
            lines.append("\n# 警告: 以下按鍵被按下但未放開\n")
            for key, time in pressed_keys.items():
                time_str = self._format_time(time)
                lines.append(f"# >按下{key}, T={time_str} (未放開)\n")
        
        # 應用軌跡簡化
        lines = self._simplify_trajectory_display(lines)
        
        return "".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間為易讀格式"""
        total_ms = round(seconds * 1000)  # 🔥 使用 round 四捨五入避免浮點數精度問題
        s = total_ms // 1000
        ms = total_ms % 1000
        
        if s >= 60:
            m = s // 60
            s = s % 60
            return f"{m}m{s:02d}s{ms:03d}"
        else:
            return f"{s}s{ms:03d}"
    
    def _parse_time(self, time_str: str) -> float:
        """解析時間字串為秒數"""
        # T=17s500 或 T=1m30s500
        time_str = time_str.replace("T=", "").strip()
        
        total_seconds = 0.0
        
        # 解析分鐘
        if "m" in time_str:
            parts = time_str.split("m")
            total_seconds += float(parts[0]) * 60
            time_str = parts[1]
        
        # 解析秒和毫秒
        if "s" in time_str:
            parts = time_str.split("s")
            total_seconds += float(parts[0])
            if len(parts) > 1 and parts[1]:
                total_seconds += float(parts[1]) / 1000
        
        return total_seconds
    
    def _text_to_json(self, text: str) -> Dict:
        """將文字指令轉換回JSON格式 (支援圖片指令)"""
        import time
        lines = text.split("\n")
        events = []
        labels = {}  # 標籤映射
        start_time = time.time()  # 使用當前時間戳
        
        # 第一遍: 掃描標籤
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("#") and not line.startswith("# "):
                # 這是標籤定義
                label_name = line[1:].strip()
                labels[label_name] = i
        
        # 第二遍: 解析指令
        i = 0
        pending_label = None  # 暫存標籤,等待下一個事件的時間
        line_number = 0  # 記錄原始行號，用於保持順序
        while i < len(lines):
            line = lines[i].strip()
            line_number = i  # 記錄當前行號
            
            # 處理備註（# 後有空格）
            if line.startswith("# "):
                # 保存備註為特殊事件
                comment_text = line[2:]  # 移除 "# " 前綴
                events.append({
                    "type": "comment",
                    "text": comment_text,
                    "time": start_time,
                    "_line_number": line_number
                })
                i += 1
                continue
            
            # 處理分隔符號（=== 或 --- 等）- 保存為特殊事件
            separator_match = re.match(r'^([=\-_])\1{2,}$', line)
            if separator_match:
                separator_char = separator_match.group(1)
                events.append({
                    "type": "separator",
                    "char": separator_char,
                    "time": start_time,
                    "_line_number": line_number
                })
                i += 1
                continue
            
            # 跳過空行和僅包含空白字符的行（但記錄行號以保持順序）
            # 強化：使用更嚴格的空白檢查，確保各種空白字符都能被正確處理
            if not line or line.isspace():
                i += 1
                continue
            
            # 標籤定義
            if line.startswith("#"):
                label_name = line[1:].strip()
                # 暫存標籤,使用下一個事件的時間
                pending_label = label_name
                i += 1
                continue
            
            # 解析指令
            if line.startswith(">"):
                # 🔧 處理分支指令（>> 和 >>>）
                # 檢查這些分支是否緊接在條件判斷後面（中間只能有空行或分支）
                if line.startswith(">>>"):
                    # 失敗分支
                    target_match = re.match(r'>>>#([a-zA-Z0-9_\u4e00-\u9fa5]+)', line)
                    if target_match:
                        target_label = target_match.group(1)
                        # 🔧 檢查是否緊接在條件判斷後（向上找，遇到非分支的>指令就停止）
                        has_preceding_condition = False
                        for check_i in range(i-1, max(-1, i-10), -1):
                            if check_i < 0 or check_i >= len(lines):
                                break
                            prev_line = lines[check_i].strip()
                            
                            # 跳過空行和分支指令
                            if not prev_line or prev_line.startswith('>>'):
                                continue
                            
                            # 遇到條件判斷指令
                            if any(kw in prev_line for kw in ['>if>', '>辨識>', '>if文字>', '>if變數>', '>if全部存在>', '>if任一存在>', '>隨機執行>', '>計數器>', '>計時器>']):
                                has_preceding_condition = True
                                break
                            
                            # 遇到其他>指令（如>範圍結束），停止搜索
                            if prev_line.startswith('>'):
                                break
                            
                            # 遇到標籤定義，停止
                            if prev_line.startswith('#'):
                                break
                        
                        if not has_preceding_condition:
                            # 這是一個獨立的分支指令，需要保存
                            repeat_count = 999999
                            repeat_match = re.search(r'\*(\d+)', line)
                            if repeat_match:
                                repeat_count = int(repeat_match.group(1))
                            
                            time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                            abs_time = start_time + self._parse_time(time_str)
                            
                            events.append({
                                "type": "branch_failure",
                                "target": target_label,
                                "repeat_count": repeat_count,
                                "time": abs_time,
                                "_line_number": line_number,
                                "_standalone": True  # 標記為獨立分支
                            })
                    i += 1
                    continue
                    
                elif line.startswith(">>"):
                    # 成功分支
                    target_match = re.match(r'>>#([a-zA-Z0-9_\u4e00-\u9fa5]+)', line)
                    if target_match:
                        target_label = target_match.group(1)
                        # 🔧 檢查是否緊接在條件判斷後（向上找，遇到非分支的>指令就停止）
                        has_preceding_condition = False
                        for check_i in range(i-1, max(-1, i-10), -1):
                            if check_i < 0 or check_i >= len(lines):
                                break
                            prev_line = lines[check_i].strip()
                            
                            # 跳過空行和分支指令
                            if not prev_line or prev_line.startswith('>>'):
                                continue
                            
                            # 遇到條件判斷指令
                            if any(kw in prev_line for kw in ['>if>', '>辨識>', '>if文字>', '>if變數>', '>if全部存在>', '>if任一存在>', '>隨機執行>', '>計數器>', '>計時器>']):
                                has_preceding_condition = True
                                break
                            
                            # 遇到其他>指令（如>範圍結束），停止搜索
                            if prev_line.startswith('>'):
                                break
                            
                            # 遇到標籤定義，停止
                            if prev_line.startswith('#'):
                                break
                        
                        if not has_preceding_condition:
                            # 這是一個獨立的分支指令，需要保存
                            repeat_count = 999999
                            repeat_match = re.search(r'\*(\d+)', line)
                            if repeat_match:
                                repeat_count = int(repeat_match.group(1))
                            
                            time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                            abs_time = start_time + self._parse_time(time_str)
                            
                            events.append({
                                "type": "branch_success",
                                "target": target_label,
                                "repeat_count": repeat_count,
                                "time": abs_time,
                                "_line_number": line_number,
                                "_standalone": True  # 標記為獨立分支
                            })
                    i += 1
                    continue
                
                # 處理 >範圍結束 指令
                if "範圍結束" in line:
                    # 解析時間
                    time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                    abs_time = start_time + self._parse_time(time_str)
                    
                    events.append({
                        "type": "region_end",
                        "time": abs_time,
                        "_line_number": line_number  # 保留行號
                    })
                    i += 1
                    continue
                
                try:
                    # 檢查是否為戰鬥指令
                    if any(keyword in line for keyword in ["啟動自動戰鬥", "尋找並攻擊", "循環攻擊", "智能戰鬥", "設定戰鬥區域", "暫停戰鬥", "恢復戰鬥", "停止戰鬥"]):
                        # 戰鬥指令處理
                        event = self._parse_combat_command_to_json(line, start_time)
                        if event:
                            event["_line_number"] = line_number  # 保留行號
                            # 如果有待處理的標籤,先加入標籤事件
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": event.get("time", start_time),
                                    "_line_number": line_number - 1  # 標籤在前一行
                                })
                                pending_label = None
                            events.append(event)
                        i += 1
                        continue
                    
                    # 檢查是否為圖片指令或OCR指令（支援舊格式和新格式）
                    # 重要：OCR指令（if文字>、等待文字>、點擊文字>）也要在這裡處理
                    if any(keyword in line for keyword in [
                        "等待圖片", "點擊圖片", "如果存在", 
                        "辨識>", "移動至>", "左鍵點擊>", "右鍵點擊>", 
                        "如果存在>", "辨識任一>", "if>",
                        "if文字>", "等待文字>", "點擊文字>",  # OCR指令
                        "延遲"  # 延遲指令
                    ]):
                        # 圖片指令和OCR指令處理
                        event = self._parse_image_command_to_json(line, lines[i+1:i+6], start_time)
                        if event:
                            event["_line_number"] = line_number  # 保留行號
                            # 如果有待處理的標籤,先加入標籤事件
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": event.get("time", start_time),
                                    "_line_number": line_number - 1  # 標籤在前一行
                                })
                                pending_label = None
                            events.append(event)
                            # ✅ 修正：只有成功解析時才跳過後續邏輯
                            i += 1
                            continue
                        # ✅ 修正：如果解析失敗（event為None），不跳過，繼續執行下方的標準解析邏輯
                    
                    # ✅ v2.7.1+ 新增：進階指令解析
                    # ✅ v2.8.0+ 新增：觸發器、並行區塊、狀態機
                    if any(keyword in line for keyword in [
                        "設定變數>", "變數加1>", "變數減1>", "if變數>",
                        "重複>", "當圖片存在>", "循環結束", "重複結束",
                        "if全部存在>", "if任一存在>",
                        "隨機延遲>", "隨機執行>",
                        "計數器>", "計時器>", "重置計數器>", "重置計時器>",
                        "開始>", "結束>",
                        # v2.8.0 觸發器
                        "每隔>", "每隔結束",
                        "當偵測到>", "當偵測結束",
                        "優先偵測>", "優先偵測結束",
                        # v2.8.0 並行區塊
                        "並行開始", "並行結束",
                        "線程>", "線程結束",
                        # v2.8.0 狀態機
                        "狀態機>", "狀態機結束",
                        "狀態>", "切換>"
                    ]):
                        # 進階指令處理（傳遞所有剩餘行，支援區塊指令）
                        event = self._parse_advanced_command_to_json(line, lines[i+1:], start_time)
                        if event:
                            event["_line_number"] = line_number
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": event.get("time", start_time),
                                    "_line_number": line_number - 1
                                })
                                pending_label = None
                            events.append(event)
                            # ✅ v2.8.0 修復：區塊指令需要跳過多行
                            lines_consumed = event.get("lines_consumed", 0)
                            if lines_consumed > 0:
                                i += lines_consumed + 1  # +1 是當前行
                            else:
                                i += 1
                            continue
                    
                    # 移除 ">" 並智能分割（保護括號內的逗號）
                    line_content = line[1:]
                    
                    # 先保護括號內的內容
                    protected = re.sub(r'\(([^)]+)\)', lambda m: f"({m.group(1).replace(',', '§')})", line_content)
                    parts_raw = protected.split(",")
                    # 還原括號內的逗號
                    parts = [p.replace('§', ',') for p in parts_raw]
                    
                    # 修復：更寬鬆的格式處理，允許只有動作和時間（缺少延遲）
                    if len(parts) >= 2:
                        action = parts[0].strip()
                        
                        # 智能判斷：如果第二部分包含 T=，則視為時間（缺少延遲欄位）
                        if len(parts) == 2 and "T=" in parts[1]:
                            delay_str = "0ms"
                            time_str = parts[1].strip()
                        else:
                            delay_str = parts[1].strip() if len(parts) > 1 else "0ms"
                            time_str = parts[2].strip() if len(parts) > 2 else "T=0s000"
                        
                        # 解析時間
                        abs_time = start_time + self._parse_time(time_str)
                        
                        # 如果有待處理的標籤,先加入標籤事件
                        if pending_label:
                            events.append({
                                "type": "label",
                                "name": pending_label,
                                "time": abs_time,
                                "_line_number": line_number - 1  # 標籤在前一行
                            })
                            pending_label = None
                        
                        # 解析延遲
                        delay_ms = int(re.search(r'\d+', delay_str).group()) if re.search(r'\d+', delay_str) else 0
                        delay_s = delay_ms / 1000.0
                        
                        # 解析動作類型
                        # 優先檢查滑鼠操作（避免誤判為鍵盤操作）
                        # 修復：先嘗試提取座標，支援負數座標
                        coords = re.search(r'\((-?\d+),(-?\d+)\)', action)
                        
                        # 檢查是否為點擊指令（左鍵點擊/右鍵點擊），即使沒有座標
                        if ("左鍵點擊" in action or "右鍵點擊" in action or "中鍵點擊" in action) and not coords:
                            # 沒有座標的點擊指令，使用 (None, None) 表示當前滑鼠位置
                            button = "right" if "右鍵" in action else "middle" if "中鍵" in action else "left"
                            
                            # 點擊 = 按下 + 放開（使用 delay_s 作為按鍵持續時間）
                            events.append({"type": "mouse", "event": "down", "button": button, "x": None, "y": None, "time": abs_time, "in_target": True, "_line_number": line_number})
                            events.append({"type": "mouse", "event": "up", "button": button, "x": None, "y": None, "time": abs_time + delay_s, "in_target": True, "_line_number": line_number})
                        
                        elif coords:
                            # 確定是滑鼠操作（有座標）
                            x, y = int(coords.group(1)), int(coords.group(2))
                            
                            if "移動至" in action:
                                events.append({"type": "mouse", "event": "move", "x": x, "y": y, "time": abs_time, "in_target": True, "_line_number": line_number})
                            elif "點擊" in action or "鍵" in action:
                                # 解析按鍵類型
                                button = "right" if "右鍵" in action else "middle" if "中鍵" in action else "left"
                                
                                # 判斷是點擊還是按下/放開
                                if "點擊" in action:
                                    # 點擊 = 按下 + 放開（使用 delay_s 作為按鍵持續時間）
                                    events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True, "_line_number": line_number})
                                    events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": abs_time + delay_s, "in_target": True, "_line_number": line_number})
                                elif "按下" in action:
                                    events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True, "_line_number": line_number})
                                elif "放開" in action:
                                    events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True, "_line_number": line_number})
                        
                        elif "滾輪" in action:
                            # 滑鼠滾輪指令：>滾輪(1), 延遲0ms, T=0s000
                            # 提取滾輪方向/數值
                            wheel_match = re.search(r'滾輪\(([+-]?\d+)\)', action)
                            if wheel_match:
                                delta = int(wheel_match.group(1))
                                # 獲取當前滑鼠位置（使用 0,0 作為預設）
                                events.append({
                                    "type": "mouse",
                                    "event": "wheel",
                                    "delta": delta,
                                    "x": 0,
                                    "y": 0,
                                    "time": abs_time,
                                    "in_target": True,
                                    "_line_number": line_number
                                })
                        
                        elif "按下" in action:
                            # 🔧 按下按鍵（不自動加放開）
                            key = action.replace("按下", "").strip()
                            events.append({
                                "type": "keyboard",
                                "event": "down",
                                "name": key,
                                "time": abs_time,
                                "_line_number": line_number,
                                "_is_press": True,  # 標記為按下指令
                                "_press_delay": delay_ms  # 保存延遲時間
                            })
                        
                        elif "放開" in action:
                            # 🔧 單純放開按鍵
                            key = action.replace("放開", "").strip()
                            events.append({
                                "type": "keyboard",
                                "event": "up",
                                "name": key,
                                "time": abs_time,
                                "_line_number": line_number,
                                "_is_release": True  # 標記為放開指令
                            })
                        
                        elif action.startswith("按") and "按下" not in action and "按鍵" not in action:
                            # 🔧 鍵盤操作（按 = 按下 + 放開，自動配對）
                            key = action.replace("按", "").strip()
                            
                            # 按下事件
                            events.append({
                                "type": "keyboard",
                                "event": "down",
                                "name": key,
                                "time": abs_time,
                                "_line_number": line_number,
                                "_auto_pair": True  # 標記為自動配對
                            })
                            
                            # 放開事件
                            events.append({
                                "type": "keyboard",
                                "event": "up",
                                "name": key,
                                "time": abs_time + delay_s,
                                "_line_number": line_number,
                                "_auto_pair": True  # 標記為自動配對
                            })
                
                except Exception as e:
                    print(f"解析行失敗: {line}\n錯誤: {e}")
                    i += 1
                    continue
            
            i += 1
        
        # 按行號排序（保持原始順序），而不是按時間排序
        # 這樣可以確保標籤和條件判斷的順序不會被打亂
        events.sort(key=lambda x: x.get("_line_number", 999999))
        
        # 移除臨時的行號標記（清理）
        for event in events:
            if "_line_number" in event:
                del event["_line_number"]
        
        # 使用保存的原始設定，而非硬編碼預設值（修復儲存時覆蓋設定的問題）
        settings = self.original_settings if self.original_settings else {
            "speed": "100",
            "repeat": "1",
            "repeat_time": "00:00:00",
            "repeat_interval": "00:00:00",
            "random_interval": False,
            "script_hotkey": "",
            "script_actions": [],
            "window_info": None
        }
        
        return {
            "events": events,
            "settings": settings
        }
    
    def _parse_image_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:
        """
        解析圖片指令並轉換為JSON格式
        :param command_line: 圖片指令行
        :param next_lines: 後續行 (用於讀取分支)
        :param start_time: 起始時間戳
        :return: JSON事件字典
        """
        # 辨識圖片指令（新格式：>辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s100）
        recognize_pattern = r'>辨識>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(recognize_pattern, command_line)
        if match:
            # 分離圖片名稱和選項
            content = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項（邊框、範圍）
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            # 🔥 強力清理：移除所有逗點和多餘空白
            pic_name = re.sub(r'[,\s]+', '', pic_name).strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 檢查後續行是否有分支（>> 或 >>>）
            branches = self._parse_simple_condition_branches(next_lines)
            
            # 如果有分支，則視為條件判斷
            if branches.get('success') or branches.get('failure'):
                result = {
                    "type": "if_image_exists",
                    "image": pic_name,
                    "image_file": image_file,
                    "confidence": 0.7,
                    "on_success": branches.get('success'),
                    "on_failure": branches.get('failure'),
                    "time": abs_time,
                    "is_pure_recognize": False  # ✨ 標記不是純辨識
                }
                if show_border:
                    result["show_border"] = True
                if region:
                    result["region"] = region
                return result
            
            # 否則視為普通辨識指令
            result = {
                "type": "recognize_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "time": abs_time,
                "is_pure_recognize": True  # ✨ 標記為純辨識，不是條件判斷
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result        # 移動至圖片指令（>移動至>pic01, 邊框, 範圍(x1,y1,x2,y2), T=1s000）
        move_pattern = r'>移動至>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(move_pattern, command_line)
        if match:
            content = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            pic_name = pic_name.rstrip(',').strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            result = {
                "type": "move_to_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result
        
        # 點擊圖片指令（>左鍵點擊>pic01, 邊框, 範圍(x1,y1,x2,y2), 半徑(60), 隨機, T=1s200）
        click_pattern = r'>(左鍵|右鍵)點擊>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(click_pattern, command_line)
        if match:
            button = "left" if match.group(1) == "左鍵" else "right"
            content = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 🔥 新增：解析點擊半徑和模式
            click_radius = 0
            click_offset_mode = 'center'
            radius_match = re.search(r'半徑\((\d+)\)', content)
            if radius_match:
                click_radius = int(radius_match.group(1))
            if '隨機' in content:
                click_offset_mode = 'random'
            elif '追蹤' in content:
                click_offset_mode = 'tracking'
            
            # 🔥 新增：解析返回原位選項
            return_to_origin = '返回' in content
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            if radius_match:
                pic_name = pic_name.replace(radius_match.group(0), '').strip()
            if '隨機' in pic_name:
                pic_name = pic_name.replace('隨機', '').strip()
            if '追蹤' in pic_name:
                pic_name = pic_name.replace('追蹤', '').strip()
            if '返回' in pic_name:
                pic_name = pic_name.replace('返回', '').strip()
            # 🔥 強力清理：移除所有逗點和多餘空白
            pic_name = re.sub(r'[,\s]+', '', pic_name).strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            result = {
                "type": "click_image",
                "button": button,
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "return_to_origin": return_to_origin,  # 🔥 使用解析的值
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            # 🔥 新增：點擊半徑和模式
            if click_radius > 0:
                result["click_radius"] = click_radius
                result["click_offset_mode"] = click_offset_mode
            return result        # 新格式條件判斷：>if>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s100
        if_simple_pattern = r'>if>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(if_simple_pattern, command_line)
        if match:
            content = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            pic_name = pic_name.rstrip(',').strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 解析後續行的 >> 和 >>> 分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            # >if> 指令預期有分支，如果沒有則添加預設值
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            result = {
                "type": "if_image_exists",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result
        
        # 新增：如果存在圖片（條件判斷）>如果存在>pic01, T=0s100
        if_exists_pattern = r'>如果存在>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(if_exists_pattern, command_line)
        if match:
            pic_name = match.group(1).strip().rstrip(',').strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 解析後續行的成功/失敗分支
            branches = self._parse_condition_branches(next_lines)
            
            return {
                "type": "if_image_exists",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== OCR 文字辨識指令 ====================
        
        # OCR 條件判斷：>if文字>確認, T=0s000
        ocr_if_pattern = r'>if文字>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(ocr_if_pattern, command_line)
        if match:
            target_text = match.group(1).strip().rstrip(',').strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析後續行的 >> 和 >>> 分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            # 預設分支
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_text_exists",
                "target_text": target_text,
                "timeout": 10.0,  # 預設等待10秒
                "match_mode": "contains",  # contains/exact/regex
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 等待文字出現：>等待文字>確認, 最長10s, T=0s000
        ocr_wait_pattern = r'>等待文字>(.+?),\s*最長(\d+(?:\.\d+)?)[sS],\s*T=(\d+)s(\d+)'
        match = re.match(ocr_wait_pattern, command_line)
        if match:
            target_text = match.group(1).strip()
            timeout = float(match.group(2))
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "wait_text",
                "target_text": target_text,
                "timeout": timeout,
                "match_mode": "contains",
                "time": abs_time
            }
        
        # 點擊文字位置：>點擊文字>登入, T=0s000
        ocr_click_pattern = r'>點擊文字>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(ocr_click_pattern, command_line)
        if match:
            target_text = match.group(1).strip().rstrip(',').strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "click_text",
                "target_text": target_text,
                "timeout": 5.0,
                "time": abs_time
            }
        
        # 延遲指令：>延遲1000ms, T=0s000
        delay_pattern = r'>延遲(\d+)ms,\s*T=(\d+)s(\d+)'
        match = re.match(delay_pattern, command_line)
        if match:
            delay_ms = int(match.group(1))
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delay",
                "duration": delay_ms / 1000.0,  # 轉為秒
                "time": abs_time
            }
        
        # 新增：辨識任一圖片（多圖同時辨識）>辨識任一>pic01|pic02|pic03, T=0s100
        recognize_any_pattern = r'>辨識任一>([^,]+),\s*T=(\d+)s(\d+)'
        match = re.match(recognize_any_pattern, command_line)
        if match:
            pic_names = match.group(1).strip().split('|')
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 為每張圖片建立配置
            images = []
            for pic_name in pic_names:
                pic_name = pic_name.strip()
                images.append({
                    'name': pic_name,
                    'action': 'click',  # 預設點擊
                    'button': 'left',
                    'return_to_origin': True
                })
            
            return {
                "type": "recognize_any",
                "images": images,
                "confidence": 0.75,
                "timeout": 10,  # 預設10秒逾時
                "time": abs_time
            }
        
        event = {"time": start_time}
        
        # 等待圖片
        wait_pattern = r'>等待圖片\[([^\]]+)\],?\s*超時(\d+(?:\.\d+)?)[sS]?'
        match = re.match(wait_pattern, command_line)
        if match:
            event["type"] = "wait_image"
            event["image"] = match.group(1)
            event["timeout"] = float(match.group(2))
            event["confidence"] = 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 點擊圖片
        click_pattern = r'>點擊圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(click_pattern, command_line)
        if match:
            event["type"] = "click_image"
            event["image"] = match.group(1)
            event["confidence"] = float(match.group(2)) if match.group(2) else 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 移動到圖片（新增）
        move_pattern = r'>移動到圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(move_pattern, command_line)
        if match:
            event["type"] = "move_to_image"
            event["image"] = match.group(1)
            event["confidence"] = float(match.group(2)) if match.group(2) else 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 條件判斷
        exists_pattern = r'>如果存在\[([^\]]+)\]'
        match = re.match(exists_pattern, command_line)
        if match:
            event["type"] = "if_exists"
            event["image"] = match.group(1)
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 如果所有模式都不匹配,返回 None
        return None
    
    def _parse_branches(self, next_lines):
        """
        解析分支指令
        :param next_lines: 後續行列表
        :return: 分支字典
        """
        branches = {}
        
        for line in next_lines[:5]:  # 只看接下來5行
            line = line.strip()
            # 強化：處理空行和僅包含空白字元的行
            if not line or line.isspace():
                continue
            # 遇到新指令或標籤就停止
            if line.startswith(">") or line.startswith("#"):
                break
            
            # 成功分支
            success_pattern = r'\s*成功→(.+)'
            match = re.match(success_pattern, line)
            if match:
                branches["success"] = self._parse_branch_action(match.group(1).strip())
                continue
            
            # 失敗分支
            failure_pattern = r'\s*失敗→(.+)'
            match = re.match(failure_pattern, line)
            if match:
                branches["failure"] = self._parse_branch_action(match.group(1).strip())
                continue
            
            # 執行分支
            execute_pattern = r'\s*執行→(.+)'
            match = re.match(execute_pattern, line)
            if match:
                branches["execute"] = self._parse_branch_action(match.group(1).strip())
                continue
        
        return branches
    
    def _parse_condition_branches(self, next_lines: list) -> dict:
        """
        解析條件判斷的分支(成功/失敗)
        :param next_lines: 後續行列表
        :return: 分支字典 {'success': {...}, 'failure': {...}}
        """
        branches = {}
        
        for line in next_lines[:5]:  # 只看接下來5行
            line = line.strip()
            # 強化：處理空行和僅包含空白字元的行
            if not line or line.isspace():
                continue
            # 遇到新指令或標籤就停止
            if line.startswith(">") or line.startswith("#"):
                break
            
            # 成功分支：成功→繼續 / 成功→停止 / 成功→跳到#標籤
            success_pattern = r'成功→(.+)'
            match = re.match(success_pattern, line)
            if match:
                action_str = match.group(1).strip()
                if action_str == "繼續":
                    branches["success"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["success"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    label = action_str.replace("跳到#", "").strip()
                    branches["success"] = {"action": "jump", "target": label}
                continue
            
            # 失敗分支：失敗→繼續 / 失敗→停止 / 失敗→跳到#標籤
            failure_pattern = r'失敗→(.+)'
            match = re.match(failure_pattern, line)
            if match:
                action_str = match.group(1).strip()
                if action_str == "繼續":
                    branches["failure"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["failure"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    label = action_str.replace("跳到#", "").strip()
                    branches["failure"] = {"action": "jump", "target": label}
                continue
        
        return branches
    
    def _parse_simple_condition_branches(self, next_lines: list) -> dict:
        """
        解析簡化條件判斷的分支(>> 成功, >>> 失敗)
        :param next_lines: 後續行列表
        :return: 分支字典 {'success': {...}, 'failure': {...}}
        
        🔧 修正：只搜索緊接著的分支指令，不跳過其他指令
        """
        branches = {}
        
        for line in next_lines[:5]:  # 只看接下來5行
            line_stripped = line.strip()
            
            # 空行跳過
            if not line_stripped or line_stripped.isspace():
                continue
            
            # 🔧 關鍵修正：遇到任何非分支的 > 指令就停止搜索
            # 這確保分支指令必須緊接在條件判斷後面
            if line_stripped.startswith(">") and not line_stripped.startswith(">>"):
                # 不是分支指令，停止搜索
                break
            
            # 遇到標籤定義時停止（不是##開頭的標籤引用）
            if line_stripped.startswith("#") and not line_stripped.startswith("##"):
                break
            
            # 失敗分支（三個>）
            if line_stripped.startswith(">>>"):
                action_str = line_stripped[3:].strip()
                
                if not action_str or action_str == "繼續":
                    branches["failure"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["failure"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    # 跳轉到標籤（完整格式：'跳到#標籤'）
                    label = action_str[3:].strip()
                    branches["failure"] = {"action": "jump", "target": label}
                elif action_str.startswith("#"):
                    # 簡化格式：直接寫 '>>>#標籤' 或 '>>>#標籤*N' 表示跳轉到該標籤並執行N次
                    # 🔧 修復：沒有指定次數時，預設為無限循環（999999次）
                    label_with_count = action_str[1:].strip()
                    if "*" in label_with_count:
                        label, count_str = label_with_count.split("*", 1)
                        try:
                            count = int(count_str.strip())
                            branches["failure"] = {"action": "jump", "target": label.strip(), "repeat_count": count}
                        except ValueError:
                            branches["failure"] = {"action": "jump", "target": label_with_count, "repeat_count": 999999}
                    else:
                        # 沒有指定次數，預設無限循環
                        branches["failure"] = {"action": "jump", "target": label_with_count, "repeat_count": 999999}
                else:
                    # 其他文字視為註解，保存下來（保留用戶的註解內容）
                    branches["failure"] = {"action": "continue", "comment": action_str}
                continue
            
            # 成功分支（兩個>）
            elif line_stripped.startswith(">>"):
                action_str = line_stripped[2:].strip()
                
                if not action_str or action_str == "繼續":
                    branches["success"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["success"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    # 跳轉到標籤（完整格式：'跳到#標籤'）
                    label = action_str[3:].strip()
                    branches["success"] = {"action": "jump", "target": label}
                elif action_str.startswith("#"):
                    # 簡化格式：直接寫 '>>#標籤' 或 '>>#標籤*N' 表示跳轉到該標籤並執行N次
                    # 🔧 修復：沒有指定次數時，預設為無限循環（999999次）
                    label_with_count = action_str[1:].strip()
                    if "*" in label_with_count:
                        label, count_str = label_with_count.split("*", 1)
                        try:
                            count = int(count_str.strip())
                            branches["success"] = {"action": "jump", "target": label.strip(), "repeat_count": count}
                        except ValueError:
                            branches["success"] = {"action": "jump", "target": label_with_count, "repeat_count": 999999}
                    else:
                        # 沒有指定次數，預設無限循環
                        branches["success"] = {"action": "jump", "target": label_with_count, "repeat_count": 999999}
                else:
                    # 其他文字視為註解，保存下來（保留用戶的註解內容）
                    branches["success"] = {"action": "continue", "comment": action_str}
                continue
        
        # 不設定預設值，讓呼叫者決定是否需要預設行為
        return branches
    
    def _parse_branch_action(self, action: str) -> dict:
        """
        解析分支動作
        :param action: 動作字串
        :return: 動作字典
        """
        # 跳到標籤
        jump_pattern = r'跳到\s*#(.+)'
        match = re.match(jump_pattern, action)
        if match:
            return {"action": "jump", "label": match.group(1).strip()}
        
        # 重試
        retry_pattern = r'重試(\d+)次(?:,?\s*間隔([\d.]+)[sS])?'
        match = re.match(retry_pattern, action)
        if match:
            return {
                "action": "retry",
                "count": int(match.group(1)),
                "interval": float(match.group(2)) if match.group(2) else 1.0
            }
        
        # 繼續
        if action == "繼續":
            return {"action": "continue"}
    
    def _parse_advanced_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:
        """
        解析進階指令（v2.7.1+ 新增）
        支援：變數、循環、多條件、隨機、計數器、計時器
        """
        # ==================== 變數系統 ====================
        
        # 設定變數：>設定變數>count, 0, T=0s000
        pattern = r'>設定變數>(.+?),\s*(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            value = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 嘗試轉換為數字
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # 保持字串
            
            return {
                "type": "set_variable",
                "name": name,
                "value": value,
                "time": abs_time
            }
        
        # 變數加1：>變數加1>count, T=0s000
        pattern = r'>變數加1>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "variable_operation",
                "name": name,
                "operation": "add",
                "value": 1,
                "time": abs_time
            }
        
        # 變數減1：>變數減1>count, T=0s000
        pattern = r'>變數減1>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "variable_operation",
                "name": name,
                "operation": "subtract",
                "value": 1,
                "time": abs_time
            }
        
        # 變數條件：>if變數>count, >=, 10, T=0s000
        pattern = r'>if變數>(.+?),\s*(==|!=|>|>=|<|<=),\s*(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            operator = match.group(2).strip()
            value = match.group(3).strip()
            seconds = int(match.group(4))
            millis = int(match.group(5))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 嘗試轉換為數字
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_variable",
                "name": name,
                "operator": operator,
                "value": value,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== 循環控制 ====================
        
        # 重複N次：>重複>10次, T=0s000
        pattern = r'>重複>(\d+)次(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            count = int(match.group(1))
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "loop_start",
                "loop_type": "repeat",
                "max_count": count,
                "time": abs_time
            }
        
        # 條件循環（當圖片存在）：>當圖片存在>loading, T=0s000
        pattern = r'>當圖片存在>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            image = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "loop_start",
                "loop_type": "while",
                "condition": {
                    "type": "image_exists",
                    "image": image
                },
                "time": abs_time
            }
        
        # 循環結束：>循環結束, T=0s000 或 >重複結束, T=0s000
        if "循環結束" in command_line or "重複結束" in command_line:
            pattern = r'(?:,\s*T=(\d+)s(\d+))'
            match = re.search(pattern, command_line)
            if match:
                seconds = int(match.group(1))
                millis = int(match.group(2))
                abs_time = start_time + seconds + millis / 1000.0
            else:
                abs_time = start_time
            
            return {
                "type": "loop_end",
                "time": abs_time
            }
        
        # ==================== 多條件判斷 ====================
        
        # 全部圖片存在（AND）：>if全部存在>pic01,pic02,pic03, T=0s000
        pattern = r'>if全部存在>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            images_str = match.group(1).strip()
            images = [img.strip() for img in images_str.split(',')]
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_all_images_exist",
                "images": images,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 任一圖片存在（OR）：>if任一存在>pic01,pic02,pic03, T=0s000
        pattern = r'>if任一存在>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            images_str = match.group(1).strip()
            images = [img.strip() for img in images_str.split(',')]
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_any_image_exists",
                "images": images,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== 隨機功能 ====================
        
        # 隨機延遲：>隨機延遲>100ms,500ms, T=0s000
        pattern = r'>隨機延遲>(\d+)ms,(\d+)ms(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            min_ms = int(match.group(1))
            max_ms = int(match.group(2))
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "random_delay",
                "min_ms": min_ms,
                "max_ms": max_ms,
                "time": abs_time
            }
        
        # 隨機分支：>隨機執行>30%, T=0s000
        pattern = r'>隨機執行>(\d+)%(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            probability = int(match.group(1))
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "random_branch",
                "probability": probability,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== 計數器與計時器 ====================
        
        # 計數器觸發：>計數器>找圖失敗, 3次後, T=0s000
        pattern = r'>計數器>(.+?),\s*(\d+)次後(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            count = int(match.group(2))
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            on_trigger = branches.get('success', {"action": "continue"})
            
            return {
                "type": "counter_trigger",
                "action_id": action_id,
                "count": count,
                "on_trigger": on_trigger,
                "reset_on_trigger": True,
                "time": abs_time
            }
        
        # 計時器觸發：>計時器>等待載入, 60秒後, T=0s000
        pattern = r'>計時器>(.+?),\s*(\d+)秒後(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            duration = int(match.group(2))
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            on_trigger = branches.get('success', {"action": "continue"})
            
            return {
                "type": "timer_trigger",
                "action_id": action_id,
                "duration": duration,
                "on_trigger": on_trigger,
                "reset_on_trigger": True,
                "time": abs_time
            }
        
        # 重置計數器：>重置計數器>找圖失敗, T=0s000
        pattern = r'>重置計數器>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "reset_counter",
                "action_id": action_id,
                "time": abs_time
            }
        
        # 重置計時器：>重置計時器>等待載入, T=0s000
        pattern = r'>重置計時器>(.+?)(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "reset_timer",
                "action_id": action_id,
                "time": abs_time
            }
        
        # 開始：>開始>10秒後, T=0s000
        pattern = r'>開始>(\d+)秒後(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            delay_seconds = int(match.group(1))
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delayed_start",
                "delay_seconds": delay_seconds,
                "time": abs_time
            }
        
        # 結束：>結束>60秒後, T=0s000
        pattern = r'>結束>(\d+)秒後(?:,\s*T=(\d+)s(\d+))'
        match = re.match(pattern, command_line)
        if match:
            delay_seconds = int(match.group(1))
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delayed_end",
                "delay_seconds": delay_seconds,
                "time": abs_time
            }
        
        # ==================== 觸發器系統 (Trigger System) ====================
        
        # 定時觸發器開始：>每隔>30秒
        pattern = r'>每隔>(\d+)(秒|分鐘|ms)'
        match = re.match(pattern, command_line)
        if match:
            interval_value = int(match.group(1))
            interval_unit = match.group(2)
            
            # 轉換為毫秒
            if interval_unit == '秒':
                interval_ms = interval_value * 1000
            elif interval_unit == '分鐘':
                interval_ms = interval_value * 60 * 1000
            else:  # ms
                interval_ms = interval_value
            
            # 收集觸發器內的動作（直到 >每隔結束）
            trigger_actions = []
            lines_consumed = 0
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                if stripped == '>每隔結束':
                    break
                if stripped and not stripped.startswith('#'):
                    trigger_actions.append(stripped)
            
            return {
                "type": "interval_trigger",
                "interval_ms": interval_ms,
                "actions": trigger_actions,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # 條件觸發器：>當偵測到>圖片名稱, 冷卻N秒
        pattern = r'>當偵測到>(.+?)(?:,\s*冷卻(\d+)(秒|ms))?$'
        match = re.match(pattern, command_line)
        if match:
            target = match.group(1).strip()
            cooldown_value = int(match.group(2)) if match.group(2) else 5
            cooldown_unit = match.group(3) if match.group(3) else '秒'
            
            # 轉換為毫秒
            if cooldown_unit == '秒':
                cooldown_ms = cooldown_value * 1000
            else:
                cooldown_ms = cooldown_value
            
            # 收集觸發器內的動作（直到 >當偵測結束）
            trigger_actions = []
            lines_consumed = 0
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                if stripped == '>當偵測結束':
                    break
                if stripped and not stripped.startswith('#'):
                    trigger_actions.append(stripped)
            
            return {
                "type": "condition_trigger",
                "target": target,
                "cooldown_ms": cooldown_ms,
                "actions": trigger_actions,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # 優先觸發器：>優先偵測>圖片名稱
        pattern = r'>優先偵測>(.+?)$'
        match = re.match(pattern, command_line)
        if match:
            target = match.group(1).strip()
            
            # 收集觸發器內的動作（直到 >優先偵測結束）
            trigger_actions = []
            lines_consumed = 0
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                if stripped == '>優先偵測結束':
                    break
                if stripped and not stripped.startswith('#'):
                    trigger_actions.append(stripped)
            
            return {
                "type": "priority_trigger",
                "target": target,
                "actions": trigger_actions,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # ==================== 並行區塊 (Parallel Blocks) ====================
        
        # 並行開始：>並行開始
        if command_line == '>並行開始':
            # 收集所有線程（直到 >並行結束）
            threads = []
            current_thread = None
            lines_consumed = 0
            
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                
                if stripped == '>並行結束':
                    # 儲存最後一個線程
                    if current_thread:
                        threads.append(current_thread)
                    break
                elif stripped.startswith('>線程>'):
                    # 儲存前一個線程
                    if current_thread:
                        threads.append(current_thread)
                    # 開始新線程
                    thread_name = stripped[4:].strip()
                    current_thread = {
                        "name": thread_name,
                        "actions": []
                    }
                elif stripped == '>線程結束':
                    # 儲存當前線程
                    if current_thread:
                        threads.append(current_thread)
                        current_thread = None
                elif stripped and current_thread is not None:
                    # 添加動作到當前線程
                    current_thread["actions"].append(stripped)
            
            return {
                "type": "parallel_block",
                "threads": threads,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # ==================== 狀態機模式 (State Machine) ====================
        
        # 狀態機開始：>狀態機>戰鬥AI
        if command_line.startswith('>狀態機>'):
            machine_name = command_line[5:].strip()
            
            # 收集所有狀態（直到 >狀態機結束）
            states = {}
            current_state = None
            initial_state = None
            lines_consumed = 0
            
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                
                if stripped == '>狀態機結束':
                    # 儲存最後一個狀態
                    if current_state:
                        states[current_state["name"]] = current_state
                    break
                elif stripped.startswith('>狀態>'):
                    # 儲存前一個狀態
                    if current_state:
                        states[current_state["name"]] = current_state
                    
                    # 解析狀態名稱和屬性
                    state_def = stripped[4:].strip()
                    is_initial = False
                    
                    # 檢查是否為初始狀態
                    if ', 初始' in state_def or ',初始' in state_def:
                        is_initial = True
                        state_def = state_def.replace(', 初始', '').replace(',初始', '').strip()
                    
                    state_name = state_def
                    current_state = {
                        "name": state_name,
                        "actions": [],
                        "transitions": {}
                    }
                    
                    if is_initial:
                        initial_state = state_name
                        
                elif stripped.startswith('>切換>') and current_state:
                    # 狀態切換指令
                    target_state = stripped[4:].strip()
                    current_state["transitions"]["default"] = target_state
                    current_state["actions"].append(stripped)
                elif stripped.startswith('>>切換>') and current_state:
                    # 成功時切換
                    target_state = stripped[5:].strip()
                    current_state["transitions"]["success"] = target_state
                    current_state["actions"].append(stripped)
                elif stripped.startswith('>>>切換>') and current_state:
                    # 失敗時切換
                    target_state = stripped[6:].strip()
                    current_state["transitions"]["failure"] = target_state
                    current_state["actions"].append(stripped)
                elif stripped and current_state is not None:
                    # 添加動作到當前狀態
                    current_state["actions"].append(stripped)
            
            # 如果沒有指定初始狀態，使用第一個定義的狀態
            if not initial_state and states:
                initial_state = list(states.keys())[0]
            
            return {
                "type": "state_machine",
                "name": machine_name,
                "states": states,
                "initial_state": initial_state,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        return None
    
    def _parse_combat_command_to_json(self, command_line: str, start_time: float) -> dict:
        """
        解析戰鬥指令並轉換為JSON格式
        :param command_line: 戰鬥指令行
        :param start_time: 起始時間戳
        :return: JSON事件字典
        """
        from combat_command_parser import CombatCommandParser
        
        parser = CombatCommandParser()
        result = parser.parse_combat_command(command_line)
        
        if result:
            # 添加時間戳
            result["time"] = start_time
            return result
        
        return None
    
    def _format_combat_event(self, event: dict) -> str:
        """
        將戰鬥事件轉換為文字指令格式
        :param event: 戰鬥事件字典
        :return: 文字指令字串
        """
        event_type = event.get("type")
        
        # 啟動自動戰鬥
        if event_type == "start_combat":
            enemies = event.get("enemies", [])
            attack_key = event.get("attack_key", "1")
            skills = event.get("skills", [])
            
            parts = ["啟動自動戰鬥"]
            if enemies:
                parts.append(f"敵人[{', '.join(enemies)}]")
            parts.append(f"攻擊鍵{attack_key}")
            if skills:
                parts.append(f"技能[{','.join(skills)}]")
            
            return ", ".join(parts)
        
        # 尋找並攻擊
        elif event_type == "find_and_attack":
            template = event.get("template", "")
            move_duration = event.get("move_duration", 0.3)
            
            return f"尋找並攻擊[{template}], 移動時間{move_duration}s"
        
        # 循環攻擊
        elif event_type == "loop_attack":
            templates = event.get("templates", [])
            attack_key = event.get("attack_key", "1")
            interval = event.get("interval", 1.0)
            
            return f"循環攻擊[{', '.join(templates)}], 攻擊鍵{attack_key}, 間隔{interval}s"
        
        # 智能戰鬥
        elif event_type == "smart_combat":
            priority = event.get("priority", [])
            attack_key = event.get("attack_key", "1")
            skills = event.get("skills", [])
            
            parts = ["智能戰鬥"]
            if priority:
                parts.append(f"優先順序[{' > '.join(priority)}]")
            parts.append(f"攻擊鍵{attack_key}")
            if skills:
                parts.append(f"技能[{','.join(skills)}]")
            
            return ", ".join(parts)
        
        # 設定戰鬥區域
        elif event_type == "set_combat_region":
            region = event.get("region", {})
            x = region.get("x", 0)
            y = region.get("y", 0)
            w = region.get("width", 0)
            h = region.get("height", 0)
            
            return f"設定戰鬥區域[X={x}, Y={y}, W={w}, H={h}]"
        
        # 暫停/恢復/停止
        elif event_type == "pause_combat":
            return "暫停戰鬥"
        elif event_type == "resume_combat":
            return "恢復戰鬥"
        elif event_type == "stop_combat":
            return "停止戰鬥"
        
        return ""
    
    def _format_branch_action(self, branch: dict) -> str:
        """
        將分支動作字典轉換為文字格式(簡化版, 不帶→符號)
        :param branch: 分支字典 {"action": "continue"/"stop"/"jump", "target": "label"}
        :return: 文字格式的分支動作
        """
        action = branch.get("action", "continue")
        
        if action == "continue":
            # 如果有註解內容，輸出註解；否則不輸出
            comment = branch.get("comment", "")
            return comment if comment else ""
        elif action == "stop":
            return "停止"
        elif action == "jump":
            target = branch.get("target", "")
            repeat_count = branch.get("repeat_count", 1)
            # 🔧 優化顯示：999999視為無限循環，不顯示次數；其他次數才顯示
            if repeat_count == 999999:
                # 無限循環，不顯示次數
                return f"#{target}"
            elif repeat_count > 1:
                # 有限次數循環
                return f"#{target}*{repeat_count}"
            else:
                # 只跳轉1次
                return f"#{target}"
        
        return ""  # 預設值
    
    def _save_script(self):
        """儲存文字指令回JSON格式（支持模組引用展開）"""
        if not self.script_path:
            self._show_message("警告", "沒有指定要儲存的腳本檔案", "warning")
            return
        
        try:
            # 獲取編輯器內容
            text_content = self.text_editor.get("1.0", "end-1c")
            
            # ✨ 展開模組引用（將 >>#a 替換為模組內容）
            expanded_content = self._expand_module_references(text_content)
            
            # 檢查是否只有註解和空行（避免保存空腳本）
            has_commands = False
            for line in expanded_content.split("\n"):
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith("#"):
                    has_commands = True
                    break
            
            if not has_commands:
                self._show_message(
                    "警告", 
                    "腳本沒有任何指令，無法儲存！\n\n請先添加指令（以 > 或 # 開頭的行）",
                    "warning"
                )
                self._update_status("警告: 無法儲存：腳本無指令", "warning")
                return
            
            # 轉換為JSON（使用展開後的內容）
            json_data = self._text_to_json(expanded_content)
            
            # 二次檢查：確保轉換後的events不為空
            if not json_data.get("events") or len(json_data.get("events", [])) == 0:
                self._show_message(
                    "錯誤", 
                    "指令解析失敗，無法產生有效的事件！\n\n可能原因：\n"
                    "• 指令格式不正確\n"
                    "• 缺少必要欄位（如時間T=）\n"
                    "• 座標或按鍵名稱解析失敗\n\n"
                    "請檢查編輯器中的指令格式。",
                    "error"
                )
                self._update_status("錯誤: 解析失敗：events為空", "error")
                return
            
            # ✅ 雙向驗證：將JSON轉回文字，確保可以正確還原
            try:
                verification_text = self._json_to_text(json_data)
                # 簡單檢查：確保轉換後有內容
                if not verification_text or len(verification_text.strip()) < 10:
                    raise ValueError("JSON轉文字驗證失敗：內容過短")
            except Exception as verify_error:
                self._show_message(
                    "錯誤",
                    f"雙向驗證失敗！\n\n儲存的JSON無法正確轉回文字格式。\n\n錯誤：{verify_error}\n\n請檢查指令格式。",
                    "error"
                )
                self._update_status("錯誤: 雙向驗證失敗", "error")
                return
            
            # 備份原檔案
            backup_path = self.script_path + ".backup"
            if os.path.exists(self.script_path):
                try:
                    with open(self.script_path, 'r', encoding='utf-8') as f:
                        with open(backup_path, 'w', encoding='utf-8') as bf:
                            bf.write(f.read())
                except:
                    pass  # 備份失敗不影響儲存流程
            
            # 使用臨時檔案儲存（防止寫入失敗損毀原檔案）
            temp_path = self.script_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # 驗證臨時檔案內容
            with open(temp_path, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
                if not verify_data.get("events") or len(verify_data.get("events", [])) == 0:
                    raise ValueError("儲存後驗證失敗：events為空")
                
                # ✅ 再次雙向驗證：確保儲存的檔案可以正確讀取
                verify_text_2 = self._json_to_text(verify_data)
                if not verify_text_2 or len(verify_text_2.strip()) < 10:
                    raise ValueError("儲存檔案二次驗證失敗")
            
            # 驗證成功後才替換原檔案
            if os.path.exists(self.script_path):
                os.remove(self.script_path)
            os.rename(temp_path, self.script_path)
            
            event_count = len(json_data.get("events", []))
            self._update_status(
                f"已儲存: {os.path.basename(self.script_path)} ({event_count}筆事件)",
                "success"
            )
            
        except ValueError as ve:
            # 解析/驗證錯誤
            self._show_message("錯誤", f"儲存驗證失敗:\n{ve}", "error")
            self._update_status(f"錯誤: 驗證失敗: {ve}", "error")
            # 清理臨時檔案
            temp_path = self.script_path + ".tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
        except Exception as e:
            # 其他錯誤
            self._show_message("錯誤", f"儲存腳本失敗:\n{e}", "error")
            self._update_status(f"錯誤: 儲存失敗: {e}", "error")
            # 清理臨時檔案
            temp_path = self.script_path + ".tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    # ==================== 內嵌自訂模組功能 ====================
    
    def _load_modules_inline(self):
        """載入模組列表"""
        self.module_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.modules_dir):
            os.makedirs(self.modules_dir, exist_ok=True)
            return
        
        modules = [f for f in os.listdir(self.modules_dir) if f.endswith('.txt')]
        for module in sorted(modules):
            display_name = os.path.splitext(module)[0]
            self.module_listbox.insert(tk.END, display_name)
    
    def _on_module_selected_inline(self, event):
        """模組選取事件"""
        selection = self.module_listbox.curselection()
        if not selection:
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.module_preview.config(state="normal")
            self.module_preview.delete("1.0", tk.END)
            self.module_preview.insert("1.0", content)
            
            # ✅ 為模組預覽套用語法高亮
            self._apply_syntax_highlighting_to_widget(self.module_preview)
            
            self.module_preview.config(state="disabled")
        except Exception as e:
            self.module_preview.config(state="normal")
            self.module_preview.delete("1.0", tk.END)
            self.module_preview.insert("1.0", f"讀取失敗: {e}")
            self.module_preview.config(state="disabled")
    
    def _save_new_module_inline(self):
        """儲存新模組（內嵌版，支持標記引用）"""
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            self._show_message("提示", "請先在編輯器中選取（反白）要儲存的指令", "warning")
            return
        
        if not selected_text.strip():
            self._show_message("提示", "選取的內容為空", "warning")
            return
        
        # 自動檢測模組名稱（如果選取內容以#開頭，提取標記名）
        lines = selected_text.strip().split('\n')
        suggested_name = ""
        
        if lines[0].startswith('#') and not lines[0].startswith('##'):
            # 第一行是標記，使用標記名作為預設模組名
            suggested_name = lines[0].strip()[1:]  # 移除#
        
        # 詢問模組名稱
        module_name = simpledialog.askstring(
            "模組名稱",
            "請輸入自訂模組的名稱：\n\n提示：如果儲存標記（例如#a），可以直接用'a'作為模組名",
            parent=self,
            initialvalue=suggested_name
        )
        
        if not module_name:
            return
        
        # 儲存模組（檔案名為 mod_模組名.txt）
        module_path = os.path.join(self.modules_dir, f"mod_{module_name}.txt")
        
        try:
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            # 重新載入列表
            self._load_modules_inline()
            
            # 選中新建的模組
            for i in range(self.module_listbox.size()):
                if self.module_listbox.get(i) == module_name:
                    self.module_listbox.selection_clear(0, tk.END)
                    self.module_listbox.selection_set(i)
                    self.module_listbox.see(i)
                    self._on_module_selected_inline(None)
                    break
            
            self.status_label.config(
                text=f"模組已儲存：mod_{module_name}.txt (可使用 >#mod_{module_name} 引用)",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"儲存模組失敗：{e}", "error")
    
    def _insert_module_inline(self):
        """插入選取的模組（內嵌版）"""
        selection = self.module_listbox.curselection()
        if not selection:
            self._show_message("提示", "請先選擇要插入的模組", "warning")
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, content + "\n")
            
            self.status_label.config(
                text=f"已插入模組：{module_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"插入模組失敗：{e}", "error")
    
    def _delete_module_inline(self):
        """刪除選取的模組（內嵌版）"""
        selection = self.module_listbox.curselection()
        if not selection:
            self._show_message("提示", "請先選擇要刪除的模組", "warning")
            return
        
        module_name = self.module_listbox.get(selection[0])
        
        # 確認刪除
        if not self._show_confirm("確認刪除", f"確定要刪除模組「{module_name}」嗎？"):
            return
        
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            os.remove(module_path)
            
            # 清空預覽
            self.module_preview.config(state="normal")
            self.module_preview.delete("1.0", tk.END)
            self.module_preview.config(state="disabled")
            
            # 重新載入列表
            self._load_modules_inline()
            
            self.status_label.config(
                text=f"已刪除模組：{module_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"刪除模組失敗：{e}", "error")
    
    def _expand_module_references(self, text_content):
        """展開模組引用：將 >#mod_a 替換為模組內容
        
        用於在保存或執行時，將標記引用替換為實際的模組內容
        
        🔧 新格式規則：
        1. 模組引用格式：>#mod_模組名 (例如：>#mod_a, >#mod_click01)
        2. 模組名只包含英文字母、數字和底線，長度1-30個字符
        3. 模組檔案儲存為 mod_模組名.txt (例如：mod_a.txt, mod_click01.txt)
        4. 分支指令（>>、>>>）永遠不會被當作模組引用
        """
        lines = text_content.split('\n')
        expanded_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # 🔧 新格式：匹配 >#mod_模組名
            # 正則表達式：^>#mod_([a-zA-Z0-9_]{1,30})$
            # 例如：>#mod_a, >#mod_click01, >#mod_戰鬥循環
            if re.match(r'^>#mod_([a-zA-Z0-9_\u4e00-\u9fa5]{1,30})$', stripped):
                match = re.match(r'^>#mod_([a-zA-Z0-9_\u4e00-\u9fa5]{1,30})$', stripped)
                module_ref = match.group(1)  # 獲取模組名（a、click01等）
                
                # 嘗試加載對應的模組（檔案名為 mod_模組名.txt）
                module_path = os.path.join(self.modules_dir, f"mod_{module_ref}.txt")
                
                if os.path.exists(module_path):
                    try:
                        with open(module_path, 'r', encoding='utf-8') as f:
                            module_content = f.read()
                        
                        # 處理模組內容，直接添加
                        module_lines = module_content.strip().split('\n')
                        for module_line in module_lines:
                            expanded_lines.append(module_line)
                    except Exception as e:
                        # 加載失敗，保留原始引用並添加註釋
                        expanded_lines.append(f"{line}  # 模組加載失敗: {e}")
                else:
                    # 模組不存在，保留原始引用並添加註釋
                    expanded_lines.append(f"{line}  # 模組不存在: mod_{module_ref}.txt")
            else:
                # 非模組引用，直接保留（包括分支指令 >>、>>> 等）
                expanded_lines.append(line)
        
        return '\n'.join(expanded_lines)
    
    def _get_module_content(self, module_name):
        """獲取模組內容（用於預覽和引用）"""
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        if os.path.exists(module_path):
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None
        return None
    
    # ==================== 右鍵選單功能 ====================
    
    
    def _on_text_modified(self, event=None):
        """文字內容修改時觸發語法高亮（優化版：防抖動處理）"""
        # 重置 modified 標誌
        self.text_editor.edit_modified(False)
        
        # ✨ 使用防抖動機制：取消之前的延遲任務
        if hasattr(self, '_highlight_after_id'):
            self.after_cancel(self._highlight_after_id)
        
        # 延遲執行語法高亮以提高效能（延長至150ms避免卡頓）
        self._highlight_after_id = self.after(150, self._apply_syntax_highlighting)
    
    def _apply_syntax_highlighting_to_widget(self, text_widget):
        """為指定的Text小工具套用語法高亮"""
        try:
            content = text_widget.get("1.0", "end-1c")
            
            # 定義需要高亮的模式 (VS Code Dark+ 配色方案)
            patterns = [
                (r'跳到#\S+', 'syntax_flow'),
                (r'停止', 'syntax_flow'),
                (r'if>', 'syntax_condition'),
                (r'如果存在>', 'syntax_condition'),
                (r'延遲\d+ms', 'syntax_delay'),
                (r'if文字>', 'syntax_ocr'),
                (r'等待文字>', 'syntax_ocr'),
                (r'點擊文字>', 'syntax_ocr'),
                (r'按下\w+', 'syntax_keyboard'),
                (r'放開\w+', 'syntax_keyboard'),
                (r'按(?![下放])\S+', 'syntax_keyboard'),
                (r'移動至\(', 'syntax_mouse'),
                (r'左鍵點擊\(', 'syntax_mouse'),
                (r'右鍵點擊\(', 'syntax_mouse'),
                (r'滾輪\(', 'syntax_mouse'),
                (r'辨識>', 'syntax_image'),
                (r'移動至>', 'syntax_image'),
                (r'左鍵點擊>', 'syntax_image'),
                (r'右鍵點擊>', 'syntax_image'),
                (r'pic\w+', 'syntax_picname'),
                (r'T=\d+[smh]\d*', 'syntax_time'),
                (r'^#\S+', 'syntax_label'),
                (r'>>#\S+', 'syntax_label'),
                (r'>>>#\S+', 'syntax_label'),
                (r'^# .*', 'syntax_comment'),
                (r'^>>>', 'syntax_symbol'),
                (r'^>>', 'syntax_symbol'),
                (r'^>', 'syntax_symbol'),
                (r',', 'syntax_symbol'),
            ]
            
            # 逐行處理
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern, tag in patterns:
                    for match in re.finditer(pattern, line):
                        start_idx = f"{line_num}.{match.start()}"
                        end_idx = f"{line_num}.{match.end()}"
                        text_widget.tag_add(tag, start_idx, end_idx)
        except:
            pass
    
    def _apply_syntax_highlighting(self):
        """套用語法高亮 (VS Code Dark+ 配色) - 優化版"""
        try:
            # ✨ 修正：處理所有行而非僅可見區域，確保長腳本完整著色
            # 取得整份檔案的總行數
            total_lines = int(self.text_editor.index("end-1c").split('.')[0])
            
            # 處理整份檔案
            start_line = 1
            end_line = total_lines
            
            # 移除舊標籤（全域）
            for tag in ["syntax_symbol", "syntax_time", "syntax_label", "syntax_keyboard",
                       "syntax_mouse", "syntax_image", "syntax_condition", "syntax_ocr",
                       "syntax_delay", "syntax_flow", "syntax_picname", "syntax_comment",
                       "syntax_module_ref", "label_foldable", "label_end"]:
                self.text_editor.tag_remove(tag, "1.0", "end")
            
            # 獲取全部文字內容
            content = self.text_editor.get(f"{start_line}.0", f"{end_line}.end")
            
            # 定義需要高亮的模式 (Dracula 配色方案)
            
            # 觸發器系統 (紫色) - 優先順序最高
            patterns_trigger = [
                (r'>每隔>\d+(秒|分鐘|ms)', 'syntax_condition'),
                (r'>每隔結束', 'syntax_condition'),
                (r'>當偵測到>.+', 'syntax_condition'),
                (r'>當偵測結束', 'syntax_condition'),
                (r'>優先偵測>.+', 'syntax_flow'),
                (r'>優先偵測結束', 'syntax_flow'),
                # 並行區塊
                (r'>並行開始', 'syntax_flow'),
                (r'>線程>.+', 'syntax_flow'),
                (r'>線程結束', 'syntax_flow'),
                (r'>並行結束', 'syntax_flow'),
                # 狀態機
                (r'>狀態機>.+', 'syntax_flow'),
                (r'>狀態>.+', 'syntax_flow'),
                (r'>切換>.+', 'syntax_flow'),
                (r'>>切換>.+', 'syntax_flow'),
                (r'>>>切換>.+', 'syntax_flow'),
                (r'>狀態機結束', 'syntax_flow'),
            ]
            
            # 流程控制 (紅色) - 優先順序最高
            patterns_flow = [
                (r'跳到#\S+', 'syntax_flow'),
                (r'停止', 'syntax_flow'),
            ]
            
            # 條件判斷 (橘色)
            patterns_condition = [
                (r'if>', 'syntax_condition'),
                (r'如果存在>', 'syntax_condition'),
            ]
            
            # 延遲控制 (橘色)
            patterns_delay = [
                (r'延遲\d+ms', 'syntax_delay'),
                (r'延遲時間', 'syntax_delay'),
            ]
            
            # OCR 文字辨識 (青色)
            patterns_ocr = [
                (r'if文字>', 'syntax_ocr'),
                (r'等待文字>', 'syntax_ocr'),
                (r'點擊文字>', 'syntax_ocr'),
            ]
            
            # 鍵盤操作 (淡紫色)
            patterns_keyboard = [
                (r'按下\w+', 'syntax_keyboard'),
                (r'放開\w+', 'syntax_keyboard'),
                (r'按(?![下放])\S+', 'syntax_keyboard'),  # 按但不是按下/按放
            ]
            
            # 滑鼠座標操作 (藍色)
            patterns_mouse = [
                (r'移動至\(', 'syntax_mouse'),
                (r'左鍵點擊\(', 'syntax_mouse'),
                (r'右鍵點擊\(', 'syntax_mouse'),
                (r'中鍵點擊\(', 'syntax_mouse'),
                (r'雙擊\(', 'syntax_mouse'),
                (r'按下left鍵\(', 'syntax_mouse'),
                (r'放開left鍵\(', 'syntax_mouse'),
                (r'滾輪\(', 'syntax_mouse'),
            ]
            
            # 圖片辨識 (綠色)
            patterns_image = [
                (r'辨識>', 'syntax_image'),
                (r'移動至>', 'syntax_image'),
                (r'左鍵點擊>', 'syntax_image'),
                (r'右鍵點擊>', 'syntax_image'),
                (r'辨識任一>', 'syntax_image'),
            ]
            
            # 圖片名稱 (黃色) - pic + 數字
            patterns_picname = [
                (r'pic\d+', 'syntax_picname'),
            ]
            
            # 時間參數 (粉紅色)
            patterns_time = [
                (r'T=\d+[smh]\d*', 'syntax_time'),
            ]
            
            # 備註 (灰色) - 優先處理
            patterns_comment = [
                (r'^# .+', 'syntax_comment'),         # 行首的 # 後接空格的備註
            ]
            
            # 標籤 (青色)
            patterns_label = [
                (r'^#b\S+', 'label_foldable'),        # 行首的 #b 標籤 (可摺疊)
                (r'^#/\S+', 'label_end'),             # 行首的 #/ 標籤 (結束標記)
                (r'^#\S+', 'syntax_label'),           # 行首的其他 # 標籤
            ]
            
            # 模組引用 (金色 - 特殊標記)
            patterns_module_ref = [
                (r'>#mod_[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),  # >#mod_a 模組引用
                (r'>>#[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),     # >>#標籤 分支跳轉
                (r'>>>#[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),    # >>>#標籤 分支跳轉
            ]
            
            # 符號 (淡紫色) - 最後處理
            patterns_symbol = [
                (r'^>>>', 'syntax_symbol'),           # 行首的 >>>
                (r'^>>', 'syntax_symbol'),            # 行首的 >>
                (r'^>', 'syntax_symbol'),             # 行首的 >
                (r',', 'syntax_symbol'),              # 逗號
            ]
            
            # 按順序合併所有模式 (優先順序從高到低)
            all_patterns = (patterns_trigger + patterns_comment + patterns_flow + patterns_condition + patterns_delay + 
                          patterns_ocr + patterns_keyboard + patterns_mouse + 
                          patterns_image + patterns_picname + patterns_time + 
                          patterns_module_ref + patterns_label + patterns_symbol)
            
            # 逐行處理（調整行號以配合範圍）
            lines = content.split('\n')
            for offset, line in enumerate(lines):
                line_num = start_line + offset
                for pattern, tag in all_patterns:
                    for match in re.finditer(pattern, line):
                        start_idx = f"{line_num}.{match.start()}"
                        end_idx = f"{line_num}.{match.end()}"
                        self.text_editor.tag_add(tag, start_idx, end_idx)
        
        except Exception as e:
            # 靜默處理錯誤，避免影響編輯器使用
            pass
    
    def _show_context_menu(self, event):
        """顯示右鍵選單"""
        # 檢查是否有選取文字
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            has_selection = bool(selected_text.strip())
        except:
            has_selection = False
        
        # 創建右鍵選單
        context_menu = tk.Menu(self, tearoff=0)
        
        if has_selection:
            context_menu.add_command(
                label="儲存為自訂模組",
                command=self._save_selection_as_module
            )
            context_menu.add_separator()
        
        # 載入已存在的模組子選單
        modules_menu = tk.Menu(context_menu, tearoff=0)
        
        # 取得所有模組
        module_files = []
        if os.path.exists(self.modules_dir):
            module_files = [f for f in os.listdir(self.modules_dir) if f.endswith('.txt')]
        
        if module_files:
            for module_file in sorted(module_files):
                module_name = os.path.splitext(module_file)[0]
                modules_menu.add_command(
                    label=module_name,
                    command=lambda name=module_name: self._insert_module_from_menu(name)
                )
            context_menu.add_cascade(label="插入自訂模組", menu=modules_menu)
        else:
            context_menu.add_command(
                label="插入自訂模組 (無可用模組)",
                state="disabled"
            )
        
        # 顯示選單
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _save_selection_as_module(self):
        """將選取的文字儲存為自訂模組"""
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            self._show_message("提示", "請先選取（反白）要儲存的指令", "warning")
            return
        
        if not selected_text.strip():
            self._show_message("提示", "選取的內容為空", "warning")
            return
        
        # 詢問模組名稱
        module_name = simpledialog.askstring(
            "自訂模組名稱",
            "請輸入模組名稱：",
            parent=self
        )
        
        if not module_name:
            return
        
        # 儲存模組（檔案名為 mod_模組名.txt）
        module_path = os.path.join(self.modules_dir, f"mod_{module_name}.txt")
        
        try:
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            # 重新載入右側模組列表
            self._load_modules_inline()
            
            # 選中新建的模組
            for i in range(self.module_listbox.size()):
                if self.module_listbox.get(i) == module_name:
                    self.module_listbox.selection_clear(0, tk.END)
                    self.module_listbox.selection_set(i)
                    self.module_listbox.see(i)
                    self._on_module_selected_inline(None)
                    break
            
            self.status_label.config(
                text=f"模組已儲存：mod_{module_name}.txt (可使用 >#mod_{module_name} 引用)",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"儲存失敗：{e}", "error")
    
    def _insert_module_from_menu(self, module_name):
        """從右鍵選單插入模組"""
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, content + "\n")
        except Exception as e:
            self._show_message("錯誤", f"讀取模組失敗：{e}", "error")
    
    # ==================== 執行功能 ====================
    
    def _execute_script(self):
        """執行當前文字指令（先儲存再執行）"""
        if not self.parent:
            self.status_label.config(text="錯誤: 無法執行：找不到主程式")
            return
        
        # 1. 先儲存腳本
        if not self.script_path:
            self._show_message("提示", "請先建立或選擇一個腳本", "warning")
            return
        
        # 儲存當前內容
        self._save_script()
        
        # 2. 確認儲存成功後再執行
        if not os.path.exists(self.script_path):
            self.status_label.config(text="錯誤: 執行失敗：腳本未儲存")
            return
        
        try:
            # 3. 讀取儲存後的腳本
            with open(self.script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 4. 載入到主程式
            if hasattr(self.parent, 'events'):
                self.parent.events = data.get("events", [])
            else:
                self.status_label.config(text="錯誤: 主程式缺少events屬性")
                return
            
            if hasattr(self.parent, 'metadata'):
                self.parent.metadata = data.get("settings", {})
            
            # 載入到 core_recorder（關鍵：確保錄製器有事件）
            if hasattr(self.parent, 'core_recorder'):
                self.parent.core_recorder.events = data.get("events", [])
                # 同時確保 core_recorder 的 images_dir 已設定
                if hasattr(self.parent.core_recorder, 'set_images_dir'):
                    images_dir = os.path.join(os.path.dirname(self.script_path), "images")
                    if os.path.exists(images_dir):
                        self.parent.core_recorder.set_images_dir(images_dir)
            
            # 5. 更新主程式設定
            settings = data.get("settings", {})
            if hasattr(self.parent, 'speed_var'):
                self.parent.speed_var.set(settings.get("speed", "100"))
            if hasattr(self.parent, 'repeat_var'):
                self.parent.repeat_var.set(settings.get("repeat", "1"))
            if hasattr(self.parent, 'repeat_time_var'):
                self.parent.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
            if hasattr(self.parent, 'repeat_interval_var'):
                self.parent.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
            
            # 同步更新主程式的腳本選擇（避免選擇不一致）
            if hasattr(self.parent, 'script_var'):
                script_name = os.path.splitext(os.path.basename(self.script_path))[0]
                self.parent.script_var.set(script_name)
            
            # 6. 記錄視窗資訊（避免執行時彈窗）
            if hasattr(self.parent, 'target_hwnd') and self.parent.target_hwnd:
                from utils import get_window_info
                current_info = get_window_info(self.parent.target_hwnd)
                if current_info:
                    self.parent.recorded_window_info = current_info
            
            # 7. 確認狀態並執行腳本
            event_count = len(data.get("events", []))
            if event_count == 0:
                self.status_label.config(text="錯誤: 腳本無事件")
                if hasattr(self.parent, 'log'):
                    self.parent.log("錯誤: 腳本無事件，無法執行")
                return
            
            # 確保不在錄製或播放狀態
            if hasattr(self.parent, 'recording') and self.parent.recording:
                self.status_label.config(text="錯誤: 請先停止錄製")
                return
            if hasattr(self.parent, 'playing') and self.parent.playing:
                self.status_label.config(text="錯誤: 已在播放中")
                return
            
            self.status_label.config(text=f"執行中... ({event_count}筆事件)")
            
            # 記錄日誌
            if hasattr(self.parent, 'log'):
                script_name = os.path.splitext(os.path.basename(self.script_path))[0]
                self.parent.log(f"從編輯器執行腳本：{script_name}（{event_count}筆事件）")
            
            # 調用 play_record（直接播放）
            if hasattr(self.parent, 'play_record'):
                self.parent.play_record()
            else:
                self.status_label.config(text="錯誤: 主程式缺少play_record方法")
                
        except Exception as e:
            self.status_label.config(text=f"錯誤: 執行失敗：{e}")
            if hasattr(self.parent, 'log'):
                self.parent.log(f"錯誤: 編輯器執行失敗：{e}")
    
    # ==================== 圖片辨識功能 ====================
    
    def _show_image_help(self):
        """顯示圖片使用說明"""
        help_text = """
📷 圖片辨識使用說明

【方法1: 使用截圖功能（推薦新手）】
1. 點擊「圖片辨識」按鈕
2. 框選螢幕上要辨識的目標區域
3. 系統自動命名為 pic01, pic02... 並插入指令
4. 您可以手動將圖片重新命名為有意義的名稱

【方法2: 自行放入圖片（進階用戶）】
1. 準備圖片檔案（建議使用去背景或純淨的圖片）
   - 支援格式: .png, .jpg, .jpeg, .bmp, .gif
   - 建議大小: 50x50 ~ 200x200 px
   - 圖片越純淨,辨識越準確

2. 圖片命名規則（任何以 pic 開頭的命名都可以）:
   ✓ 純數字: pic01, pic02, pic999
   ✓ 中文描述: pic血條, pic怪物, pic確定按鈕
   ✓ 中文+數字: pic王01, pic王02, pic小怪03
   ✓ 英文描述: pic右上角, pic_button, pic_monster
   
   注意: 必須以 "pic" 開頭才能被辨識

3. 放入圖片資料夾:
   📁 {images_path}

4. 在編輯器中輸入指令（無需寫副檔名）:
   >辨識>pic01, T=0s000
   >移動至>pic血條, T=0s000
   >左鍵點擊>pic怪物, T=0s000
   >if>pic王01, T=0s000

【注意事項】
✓ 圖片名稱必須以 "pic" 開頭才能被辨識
✓ 編輯器會自動搜尋對應的圖片檔案（任何副檔名）
✓ 指令中不需要寫副檔名（例如寫 pic血條 即可，不用寫 pic血條.png）
✓ 使用去背景或高對比圖片可提升辨識準確度
✓ 避免過小的圖片（建議 > 30x30 px）

【範例】
假設你放入了 pic登入按鈕.png
在編輯器中輸入:
  >辨識>pic登入按鈕, T=0s000
  >>=點擊
  >>>=找不到

系統會自動找到並使用 pic登入按鈕.png 進行辨識
"""
        
        help_text = help_text.replace("{images_path}", self.images_dir)
        
        # 創建說明視窗
        help_win = tk.Toplevel(self)
        help_win.title("圖片辨識使用說明")
        help_win.geometry("600x550")
        help_win.resizable(False, False)
        
        # 文字區域
        text_area = tk.Text(
            help_win,
            wrap="word",
            font=font_tuple(9),
            bg="#f5f5f5",
            fg="#333333",
            padx=15,
            pady=15,
            relief="flat"
        )
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        text_area.insert("1.0", help_text)
        text_area.config(state="disabled")
        
        # 關閉按鈕
        close_btn = tk.Button(
            help_win,
            text="知道了",
            font=font_tuple(10, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=30,
            pady=8,
            cursor="hand2",
            command=help_win.destroy
        )
        close_btn.pack(pady=10)
        
        # 居中顯示
        help_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - help_win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - help_win.winfo_height()) // 2
        help_win.geometry(f"+{x}+{y}")
    
    def _capture_and_recognize(self):
        """截圖並儲存，插入辨識指令"""
        try:
            # 儲存當前視窗尺寸和位置
            self.saved_geometry = self.geometry()
            if self.parent:
                self.saved_parent_geometry = self.parent.geometry()
            
            # 獲取螢幕尺寸
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # 步驟1: 先最小化到工作列（讓 Windows 移除視窗的視覺效果）
            self.state('iconic')
            if self.parent:
                self.parent.state('iconic')
            
            self.update_idletasks()
            if self.parent:
                self.parent.update_idletasks()
            
            # ✅ 優化後的延遲：200ms 足以完成視窗最小化
            self.after(200)
            self.update()
            if self.parent:
                self.parent.update()
            
            # 步驟2: 完全隱藏視窗（withdraw）
            self.withdraw()
            if self.parent:
                self.parent.withdraw()
            
            self.update_idletasks()
            if self.parent:
                self.parent.update_idletasks()
            
            # 步驟3: 移到螢幕外（三重保險）
            self.geometry(f"1x1+{screen_width + 2000}+{screen_height + 2000}")
            if self.parent:
                self.parent.geometry(f"1x1+{screen_width + 3000}+{screen_height + 3000}")
            
            self.update_idletasks()
            if self.parent:
                self.parent.update_idletasks()
            
            # 步驟4: 強制更新並等待 Windows DWM 完成重繪
            self.update()
            if self.parent:
                self.parent.update()
            
            # 步驟5: 使用 Windows API 強制重繪桌面（確保視窗消失）
            try:
                import ctypes
                # InvalidateRect: 強制重繪整個桌面
                ctypes.windll.user32.InvalidateRect(0, None, True)
                # UpdateWindow: 立即更新桌面
                ctypes.windll.user32.UpdateWindow(0)
                # RedrawWindow: 強制重繪所有視窗
                RDW_INVALIDATE = 0x0001
                RDW_ALLCHILDREN = 0x0080
                RDW_UPDATENOW = 0x0100
                ctypes.windll.user32.RedrawWindow(0, None, None, RDW_INVALIDATE | RDW_ALLCHILDREN | RDW_UPDATENOW)
            except:
                pass  # API 調用失敗不影響主流程
            
            # ✅ 優化後的總延遲：800ms 內完成截圖（200ms + 600ms = 800ms < 1秒）
            self.after(600, self._do_capture)
            
        except Exception as e:
            print(f"隱藏視窗失敗: {e}")
            self._restore_windows()
    
    def _do_capture(self):
        """執行截圖"""
        try:
            # 創建截圖選取視窗
            capture_win = ScreenCaptureSelector(self, self._on_capture_complete)
            capture_win.wait_window()
        except Exception as e:
            self._show_message("錯誤", f"截圖失敗：{e}", "error")
            self._restore_windows()
    
    def _restore_windows(self):
        """恢復視窗顯示"""
        try:
            # 步驟1: 從 withdraw 狀態恢復
            self.deiconify()
            if self.parent:
                self.parent.deiconify()
            
            # 步驟2: 恢復正常狀態
            self.state('normal')
            if self.parent:
                self.parent.state('normal')
            
            # 步驟3: 恢復視窗尺寸和位置
            if hasattr(self, 'saved_geometry'):
                self.geometry(self.saved_geometry)
            if self.parent and hasattr(self, 'saved_parent_geometry'):
                self.parent.geometry(self.saved_parent_geometry)
            
            # 強制更新
            self.update()
            if self.parent:
                self.parent.update()
            
            # ✅ 修復：確保編輯器視窗在父視窗之上
            # 先提升父視窗（主程式）
            if self.parent:
                self.parent.lift()
                self.parent.update()
            
            # 再提升編輯器視窗到最上層
            self.lift()
            self.focus_force()
            
            # 短暫延遲後再次確保編輯器在最上層（防止主程式蓋過編輯器）
            self.after(10, self._ensure_on_top)
        except Exception as e:
            print(f"恢復視窗失敗: {e}")
    
    def _ensure_on_top(self):
        """確保編輯器視窗在最上層"""
        try:
            self.lift()
            self.focus_force()
        except:
            pass
    
    def _on_capture_complete(self, image_region):
        """截圖完成回調"""
        # ✅ 修正：先檢查是否取消，如果取消才立即恢復視窗
        if image_region is None:
            self._restore_windows()
            return
        
        try:
            x1, y1, x2, y2 = image_region
            
            # ✅ 修正：在視窗仍然隱藏的狀態下截圖（🔥 優化：使用 mss）
            if MSS_AVAILABLE:
                try:
                    with mss.mss() as sct:
                        monitor = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
                        screenshot_mss = sct.grab(monitor)
                        screenshot = Image.frombytes('RGB', screenshot_mss.size, screenshot_mss.bgra, 'raw', 'BGRX')
                except Exception:
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            else:
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # ✅ 修正：截圖完成後才恢復視窗
            self._restore_windows()
            
            # 顯示合併的命名+預覽對話框
            self._show_name_and_preview_dialog(screenshot)
            
        except Exception as e:
            # ✅ 確保即使發生錯誤也要恢復視窗
            self._restore_windows()
            self._show_message("錯誤", f"儲存圖片失敗：{e}", "error")
    
    def _show_name_and_preview_dialog(self, screenshot):
        """顯示圖片預覽和命名的合併對話框"""
        dialog = tk.Toplevel(self)
        dialog.title("圖片辨識 - 命名與預覽")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.transient(self)
        dialog.grab_set()
        
        result = {"confirmed": False, "name": None}
        
        # 主框架
        main_frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # ========== 命名區域 ==========
        name_frame = tk.Frame(main_frame, bg="white")
        name_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            name_frame,
            text="請輸入圖片名稱",
            font=font_tuple(11, "bold"),
            bg="white",
            fg="#1976d2"
        ).pack(anchor="w", pady=(0, 10))
        
        # 輸入框
        input_frame = tk.Frame(name_frame, bg="white")
        input_frame.pack(anchor="w")
        
        tk.Label(input_frame, text="pic", font=font_tuple(10, "bold"), bg="white").pack(side="left")
        
        name_entry = tk.Entry(input_frame, width=25, font=font_tuple(10))
        name_entry.pack(side="left", padx=5)
        name_entry.insert(0, f"{self._pic_counter:02d}")
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        # ========== 分隔線 ==========
        tk.Frame(main_frame, height=1, bg="#e0e0e0").pack(fill="x", pady=10)
        
        # ========== 預覽區域 ==========
        preview_frame = tk.Frame(main_frame, bg="white")
        preview_frame.pack(fill="both", expand=True)
        
        tk.Label(
            preview_frame,
            text="圖片預覽",
            font=font_tuple(11, "bold"),
            bg="white",
            fg="#1976d2"
        ).pack(anchor="w", pady=(0, 10))
        
        # 圖片預覽（調整大小以適應對話框）
        max_width, max_height = 500, 350
        img_width, img_height = screenshot.size
        
        scale = min(max_width / img_width, max_height / img_height, 1.0)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized_img = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_img)
        
        img_label = tk.Label(preview_frame, image=photo, bg="white", relief="solid", borderwidth=1)
        img_label.image = photo  # 保持引用
        img_label.pack(pady=(0, 15))
        
        # ========== 按鈕區域 ==========
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill="x")
        
        def on_confirm():
            custom_name = name_entry.get().strip()
            if not custom_name:
                custom_name = f"{self._pic_counter:02d}"
            result["name"] = f"pic{custom_name}"
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        tk.Button(
            btn_frame,
            text="儲存",
            command=on_confirm,
            bg="#4caf50",
            fg="white",
            font=font_tuple(10, "bold"),
            relief="flat",
            padx=30,
            pady=8,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="取消",
            command=on_cancel,
            bg="#757575",
            fg="white",
            font=font_tuple(10),
            relief="flat",
            padx=30,
            pady=8,
            cursor="hand2"
        ).pack(side="left")
        
        # 快捷鍵
        name_entry.bind('<Return>', lambda e: on_confirm())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        # 置中顯示
        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - dialog_width) // 2
        y = (dialog.winfo_screenheight() - dialog_height) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 等待對話框關閉
        dialog.wait_window()
        
        # 如果確認，儲存圖片並插入指令
        if result["confirmed"] and result["name"]:
            self._save_and_insert_commands(screenshot, result["name"])
    
    def _save_and_insert_commands(self, screenshot, display_name):
        """儲存圖片並自動插入指令"""
        try:
            # 檔案名稱使用完整的 display_name
            image_filename = f"{display_name}.png"
            image_path = os.path.join(self.images_dir, image_filename)
            
            # 儲存圖片
            screenshot.save(image_path)
            
            # 更新計數器
            self._pic_counter += 1
            
            # 自動插入辨識指令（時間固定為 T=0s000）
            # 生成指令文字
            commands = f">辨識>{display_name}, T=0s000\n"
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, commands)
            
            # 更新狀態列
            self._update_status(f"圖片已儲存並插入指令：{display_name}", "success")
            
        except Exception as e:
            self._show_message("錯誤", f"儲存圖片失敗：{e}", "error")
    
    def _capture_left_click_coordinate(self):
        """捕捉左鍵點擊座標"""
        self._capture_click_coordinate("left")
    
    def _capture_right_click_coordinate(self):
        """捕捉右鍵點擊座標"""
        self._capture_click_coordinate("right")
    
    def _capture_click_coordinate(self, button_type):
        """捕捉滑鼠點擊座標的通用函數"""
        try:
            # 儲存當前視窗尺寸和位置
            self.saved_geometry = self.geometry()
            if self.parent:
                self.saved_parent_geometry = self.parent.geometry()
            
            # 獲取螢幕尺寸
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # 步驟1: 先最小化到工作列
            self.state('iconic')
            if self.parent:
                self.parent.state('iconic')
            
            self.update_idletasks()
            if self.parent:
                self.parent.update_idletasks()
            
            self.after(200)
            self.update()
            if self.parent:
                self.parent.update()
            
            # 步驟2: 完全隱藏視窗
            self.withdraw()
            if self.parent:
                self.parent.withdraw()
            
            self.update_idletasks()
            if self.parent:
                self.parent.update_idletasks()
            
            # 步驟3: 移到螢幕外
            self.geometry(f"1x1+{screen_width + 2000}+{screen_height + 2000}")
            if self.parent:
                self.parent.geometry(f"1x1+{screen_width + 3000}+{screen_height + 3000}")
            
            self.update_idletasks()
            if self.parent:
                self.parent.update_idletasks()
            
            self.update()
            if self.parent:
                self.parent.update()
            
            # 延遲後執行座標捕捉
            self.after(600, lambda: self._do_coordinate_capture(button_type))
            
        except Exception as e:
            print(f"隱藏視窗失敗: {e}")
            self._restore_windows()
    
    def _do_coordinate_capture(self, button_type):
        """執行座標捕捉"""
        try:
            # 創建座標選擇視窗
            capture_win = CoordinateSelector(self, button_type, lambda coord: self._on_coordinate_captured(coord, button_type))
            capture_win.wait_window()
        except Exception as e:
            self._show_message("錯誤", f"座標捕捉失敗：{e}", "error")
            self._restore_windows()
    
    def _on_coordinate_captured(self, coordinate, button_type):
        """座標捕捉完成回調"""
        # 恢復視窗
        self._restore_windows()
        
        if coordinate is None:
            return
        
        try:
            x, y = coordinate
            
            # 生成點擊指令
            if button_type == "left":
                command = f">左鍵點擊({x},{y}), 延遲50ms, T=0s000\n"
            else:  # right
                command = f">右鍵點擊({x},{y}), 延遲50ms, T=0s000\n"
            
            # ✅ 確保編輯器在最上層再插入文字
            self.lift()
            self.focus_force()
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, command)
            self.text_editor.focus_set()
            
            # 更新狀態列
            button_name = "左鍵" if button_type == "left" else "右鍵"
            self._update_status(f"{button_name}點擊座標已插入：({x}, {y})", "success")
            
        except Exception as e:
            self._show_message("錯誤", f"插入點擊指令失敗：{e}", "error")
    
    def _capture_region_for_recognition(self):
        """選擇範圍用於圖片辨識"""
        # 儲存視窗狀態
        self.editor_geometry = self.geometry()
        if self.parent:
            self.parent_geometry = self.parent.geometry()
        
        # 隱藏視窗
        self.lower()
        if self.parent:
            self.parent.lower()
        
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        self.withdraw()
        if self.parent:
            self.parent.withdraw()
        
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        # 延遲後選擇範圍
        self.after(300, self._do_region_selection)
    
    def _do_region_selection(self):
        """執行範圍選擇"""
        try:
            # 創建範圍選擇視窗
            region_selector = RegionSelector(self, self._on_region_selected)
            region_selector.wait_window()
        except Exception as e:
            self._show_message("錯誤", f"範圍選擇失敗：{e}", "error")
            self._restore_windows()
    
    def _on_region_selected(self, region):
        """範圍選擇完成回調"""
        # 恢復視窗
        self._restore_windows()
        
        if region is None:
            return
        
        # ✅ 確保編輯器在最上層
        self.lift()
        self.focus_force()
        
        try:
            x1, y1, x2, y2 = region
            
            # 在游標位置插入範圍辨識指令
            # 格式: >辨識>pic01, 範圍(x1,y1,x2,y2), T=0s000
            current_time = self._get_next_available_time()
            
            # 插入範圍辨識指令和範圍結束標記
            command = f">辨識>pic01, 範圍({x1},{y1},{x2},{y2}), T={current_time}\n>範圍結束\n"
            
            self.text_editor.insert(tk.INSERT, command)
            
            # 更新狀態列
            self._update_status(f"已插入範圍辨識指令：({x1},{y1},{x2},{y2})", "success")
            
        except Exception as e:
            self._show_message("錯誤", f"插入指令失敗：{e}", "error")
    
    def _capture_and_ocr(self):
        """截圖並進行文字辨識（OCR），顯示結果並可插入指令"""
        # 儲存視窗狀態
        self.editor_geometry = self.geometry()
        if self.parent:
            self.parent_geometry = self.parent.geometry()
        
        # 隱藏視窗
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        self.geometry(f"+{screen_width + 100}+{screen_height + 100}")
        if self.parent:
            self.parent.geometry(f"+{screen_width + 200}+{screen_height + 200}")
        
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        self.withdraw()
        if self.parent:
            self.parent.withdraw()
        
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        # 延遲後執行截圖
        self.after(400, self._do_ocr_capture)
    
    def _do_ocr_capture(self):
        """執行 OCR 截圖"""
        try:
            capture_win = ScreenCaptureSelector(self, self._on_ocr_capture_complete)
            capture_win.wait_window()
        except Exception as e:
            self._show_message("錯誤", f"截圖失敗：{e}", "error")
            self._restore_windows()
    
    def _on_ocr_capture_complete(self, image_region):
        """OCR 截圖完成回調"""
        self._restore_windows()
        
        if image_region is None:
            return
        
        try:
            x1, y1, x2, y2 = image_region
            # 🔥 優化：使用 mss 截圖
            if MSS_AVAILABLE:
                try:
                    with mss.mss() as sct:
                        monitor = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
                        screenshot_mss = sct.grab(monitor)
                        screenshot = Image.frombytes('RGB', screenshot_mss.size, screenshot_mss.bgra, 'raw', 'BGRX')
                except Exception:
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            else:
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # 執行 OCR 辨識
            self._perform_ocr_and_show_result(screenshot)
            
        except Exception as e:
            self._show_message("錯誤", f"OCR 辨識失敗：{e}", "error")
    
    def _perform_ocr_and_show_result(self, screenshot):
        """執行 OCR 並顯示結果對話框"""
        try:
            import pytesseract
            
            # 創建結果對話框
            dialog = tk.Toplevel(self)
            dialog.title("文字辨識結果 (OCR)")
            dialog.geometry("600x700")
            dialog.resizable(True, True)
            dialog.attributes('-topmost', True)
            dialog.transient(self)
            dialog.grab_set()
            
            # 主框架
            main_frame = tk.Frame(dialog, bg="white", padx=15, pady=15)
            main_frame.pack(fill="both", expand=True)
            
            # 標題
            title_label = tk.Label(
                main_frame,
                text="📝 文字辨識結果",
                font=font_tuple(14, "bold"),
                bg="white",
                fg="#333333"
            )
            title_label.pack(pady=(0, 10))
            
            # 圖片預覽區
            preview_frame = tk.LabelFrame(
                main_frame,
                text="截圖預覽",
                font=font_tuple(9, "bold"),
                bg="white",
                fg="#555555"
            )
            preview_frame.pack(fill="x", pady=(0, 10))
            
            # 縮放圖片以適應預覽
            max_width, max_height = 550, 200
            img_width, img_height = screenshot.size
            ratio = min(max_width / img_width, max_height / img_height, 1.0)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            preview_img = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview_img)
            
            preview_label = tk.Label(preview_frame, image=photo, bg="white")
            preview_label.image = photo  # 保持引用
            preview_label.pack(padx=5, pady=5)
            
            # 辨識結果區
            result_frame = tk.LabelFrame(
                main_frame,
                text="辨識結果",
                font=font_tuple(9, "bold"),
                bg="white",
                fg="#555555"
            )
            result_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            # 辨識進度提示
            progress_label = tk.Label(
                result_frame,
                text="正在辨識中，請稍候...",
                font=font_tuple(10),
                bg="white",
                fg="#666666"
            )
            progress_label.pack(pady=20)
            
            # 結果文字框（初始隱藏）
            result_text = scrolledtext.ScrolledText(
                result_frame,
                font=font_tuple(11, monospace=True),
                wrap="word",
                height=8,
                bg="#f5f5f5",
                fg="#333333"
            )
            
            # 按鈕區
            button_frame = tk.Frame(main_frame, bg="white")
            button_frame.pack(fill="x", pady=(10, 0))
            
            result_data = {"text": ""}
            
            def insert_if_text():
                """插入 if文字 指令"""
                text = result_data["text"].strip()
                if text:
                    current_time = self._get_next_available_time()
                    command = f">if文字>{text}, T={current_time}\n>>#找到\n>>>#沒找到\n"
                    self.text_editor.insert(tk.INSERT, command)
                    self._update_status(f"已插入 OCR 條件判斷：{text}", "success")
                    dialog.destroy()
            
            def insert_wait_text():
                """插入 等待文字 指令"""
                text = result_data["text"].strip()
                if text:
                    current_time = self._get_next_available_time()
                    command = f">等待文字>{text}, 最長10s, T={current_time}\n"
                    self.text_editor.insert(tk.INSERT, command)
                    self._update_status(f"已插入 OCR 等待文字：{text}", "success")
                    dialog.destroy()
            
            def insert_click_text():
                """插入 點擊文字 指令"""
                text = result_data["text"].strip()
                if text:
                    current_time = self._get_next_available_time()
                    command = f">點擊文字>{text}, T={current_time}\n"
                    self.text_editor.insert(tk.INSERT, command)
                    self._update_status(f"已插入 OCR 點擊文字：{text}", "success")
                    dialog.destroy()
            
            def copy_to_clipboard():
                """複製到剪貼簿"""
                text = result_data["text"].strip()
                if text:
                    dialog.clipboard_clear()
                    dialog.clipboard_append(text)
                    self._update_status("已複製到剪貼簿", "success")
            
            # 按鈕（初始禁用，等待辨識完成）
            btn_if = tk.Button(
                button_frame,
                text="插入條件判斷",
                font=font_tuple(9, "bold"),
                bg="#00BCD4",
                fg="white",
                padx=10,
                pady=5,
                cursor="hand2",
                state="disabled",
                command=insert_if_text
            )
            btn_if.pack(side="left", padx=3)
            
            btn_wait = tk.Button(
                button_frame,
                text="插入等待文字",
                font=font_tuple(9, "bold"),
                bg="#009688",
                fg="white",
                padx=10,
                pady=5,
                cursor="hand2",
                state="disabled",
                command=insert_wait_text
            )
            btn_wait.pack(side="left", padx=3)
            
            btn_click = tk.Button(
                button_frame,
                text="插入點擊文字",
                font=font_tuple(9, "bold"),
                bg="#4CAF50",
                fg="white",
                padx=10,
                pady=5,
                cursor="hand2",
                state="disabled",
                command=insert_click_text
            )
            btn_click.pack(side="left", padx=3)
            
            btn_copy = tk.Button(
                button_frame,
                text="複製文字",
                font=font_tuple(9, "bold"),
                bg="#FF9800",
                fg="white",
                padx=10,
                pady=5,
                cursor="hand2",
                state="disabled",
                command=copy_to_clipboard
            )
            btn_copy.pack(side="left", padx=3)
            
            btn_close = tk.Button(
                button_frame,
                text="關閉",
                font=font_tuple(9),
                bg="#9E9E9E",
                fg="white",
                padx=15,
                pady=5,
                cursor="hand2",
                command=dialog.destroy
            )
            btn_close.pack(side="right", padx=3)
            
            # 在背景執行 OCR
            def do_ocr():
                try:
                    # 嘗試多種 OCR 配置
                    configs = [
                        ('基本辨識', ''),
                        ('單行模式', '--psm 7'),
                        ('單字模式', '--psm 8'),
                        ('限定字符', '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'),
                    ]
                    
                    results = []
                    for name, config in configs:
                        try:
                            text = pytesseract.image_to_string(screenshot, lang='eng', config=config).strip()
                            if text:
                                results.append(f"【{name}】\n{text}\n")
                        except:
                            pass
                    
                    if results:
                        final_text = "\n".join(results)
                        # 取第一個結果作為主要結果
                        main_result = pytesseract.image_to_string(screenshot, lang='eng', config='--psm 7').strip()
                        result_data["text"] = main_result
                    else:
                        final_text = "無法辨識文字"
                        result_data["text"] = ""
                    
                    # 更新 UI（在主線程）
                    dialog.after(0, lambda: update_ui(final_text))
                    
                except Exception as e:
                    dialog.after(0, lambda: update_ui(f"辨識失敗：{e}"))
            
            def update_ui(text):
                """更新 UI 顯示辨識結果"""
                progress_label.pack_forget()
                result_text.pack(fill="both", expand=True, padx=5, pady=5)
                result_text.insert("1.0", text)
                result_text.config(state="disabled")
                
                # 啟用按鈕
                if result_data["text"]:
                    btn_if.config(state="normal")
                    btn_wait.config(state="normal")
                    btn_click.config(state="normal")
                    btn_copy.config(state="normal")
            
            # 啟動 OCR 線程
            import threading
            ocr_thread = threading.Thread(target=do_ocr, daemon=True)
            ocr_thread.start()
            
            # 置中顯示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
            y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
        except ImportError:
            self._show_message("錯誤", "未安裝 pytesseract\n請執行: pip install pytesseract", "error")
        except Exception as e:
            self._show_message("錯誤", f"OCR 處理失敗：{e}", "error")
    
    def _get_next_available_time(self):
        """獲取下一個可用的時間戳記"""
        content = self.text_editor.get("1.0", "end-1c")
        lines = content.split('\n')
        
        max_time = 0
        for line in lines:
            match = re.search(r'T=(\d+)s(\d+)', line)
            if match:
                seconds = int(match.group(1))
                millis = int(match.group(2))
                total_ms = seconds * 1000 + millis
                max_time = max(max_time, total_ms)
        
        # 下一個時間點（+100ms）
        next_time_ms = max_time + 100
        seconds = next_time_ms // 1000
        millis = next_time_ms % 1000
        return f"{seconds}s{millis}"
    
    # ==================== 已棄用：舊的彈窗式自訂模組管理器 ====================
    # 保留作為備份，但不再使用（已整合到右側面板）
    
    def _open_custom_module(self):
        """開啟自訂模組管理視窗（已棄用）"""
        # 此功能已整合到右側面板，不再需要彈窗
        pass
    
    # ==================== 圖片辨識指令解析 ====================
    
    def _parse_image_command(self, line: str) -> Dict[str, Any]:
        """解析圖片辨識相關指令
        
        支援格式：
        >辨識>pic01, T=時間（新格式）
        >辨識>pic01, 邊框, T=時間（顯示邊框）
        >辨識>pic01, 範圍(x1,y1,x2,y2), T=時間（範圍辨識）
        >辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=時間（邊框+範圍）
        >辨識>pic01>img_001.png, T=時間（舊格式，相容性）
        >移動至>pic01, T=時間
        >左鍵點擊>pic01, T=時間
        >右鍵點擊>pic02, T=時間
        """
        # 辨識指令（新格式，支援邊框和範圍）
        # 格式: >辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s000
        match = re.match(r'>辨識>([^>,]+)(?:,\s*([^,T]+))*,\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            options_str = match.group(2) if match.group(2) else ""
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            # 解析選項
            show_border = False
            region = None
            
            if options_str:
                # 檢查是否有"邊框"
                if '邊框' in options_str:
                    show_border = True
                
                # 檢查是否有"範圍"
                region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
                if region_match:
                    region = (
                        int(region_match.group(1)),
                        int(region_match.group(2)),
                        int(region_match.group(3)),
                        int(region_match.group(4))
                    )
            
            # 自動查找pic對應的圖片檔案
            image_file = self._find_pic_image_file(display_name)
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
                "show_border": show_border,
                "region": region,
                "time": seconds * 1000 + millis
            }
        
        # 辨識指令（舊格式，相容性）
        match = re.match(r'>辨識>([^>]+)>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            image_file = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
                "time": seconds * 1000 + millis
            }
        
        # 移動至圖片
        match = re.match(r'>移動至>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            target = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            
            return {
                "type": "move_to_image",
                "target": target,
                "time": seconds * 1000 + millis
            }
        
        # 點擊圖片
        match = re.match(r'>(左鍵|右鍵)點擊>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            button = "left" if match.group(1) == "左鍵" else "right"
            target = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            return {
                "type": "click_image",
                "button": button,
                "target": target,
                "time": seconds * 1000 + millis
            }
        
        return None
    
    def _find_pic_image_file(self, pic_name: str) -> str:
        """根據pic名稱查找對應的圖片檔案
        
        Args:
            pic_name: pic名稱（例如：pic01、pic王01、pic小怪、pic確定）
        
        Returns:
            圖片檔名（例如：pic01.png、pic王01.png），如果找不到則返回 pic_name.png
            
        支援格式：
            - pic01, pic02, pic999 (傳統數字編號)
            - pic王01, pic王02 (中文+數字)
            - pic小怪, pic確定, pic右上角 (純中文描述)
            - 任何以 pic 開頭的命名
        """
        if not os.path.exists(self.images_dir):
            return f"{pic_name}.png"
        
        # 查找該pic名稱對應的圖片檔案
        try:
            # 支援的圖片副檔名
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            
            for filename in os.listdir(self.images_dir):
                # 取得檔案名稱（不含副檔名）
                name_without_ext = os.path.splitext(filename)[0]
                ext = os.path.splitext(filename)[1].lower()
                
                # 檢查是否為圖片檔案且名稱匹配
                if ext in image_extensions and name_without_ext == pic_name:
                    return filename
        except:
            pass
        
        # 找不到時返回預設檔名（優先使用 .png）
        return f"{pic_name}.png"
    
    # ==================== Workflow 流程圖相關方法 ====================
    
    def _parse_and_draw_workflow(self, text_content):
        """解析文字指令並繪製 Workflow 流程圖（PCB v11 風格）"""
        # 清空畫布
        self.workflow_canvas.delete("all")
        self.workflow_nodes = {}
        self.workflow_connections = []
        
        # ★ 新增：PCB 風格資料結構 ★
        self.pcb_nodes = []  # [{x, y, width, height, name, row, col, type, tag}]
        self.pcb_connections = []  # [(from_idx, to_idx, path_type)]
        self.pcb_groups = []  # [{nodes: [...], color, name}]
        self.pcb_router = None
        
        # ✅ v2.8.2: 重設並行區塊追蹤
        self.parallel_threads = {}  # {parallel_label: [thread_labels]}
        
        # PCB 佈局參數
        start_x = 80
        start_y = 80
        h_gap = 180  # 水平間距
        v_gap = 80   # 垂直間距（縮小以配合分叉）
        node_width = 150
        node_height = 36
        
        # 解析標籤和指令
        lines = text_content.split('\n')
        current_label = None
        label_commands = {}  # {label: [commands]}
        label_order = []  # 保持標籤順序
        
        # ✅ v2.8.0: 追蹤區塊結構
        block_stack = []  # 追蹤區塊嵌套
        
        # ✅ v2.8.0: 追蹤背景任務（觸發器、並行區塊等）
        background_labels = []  # 背景線程的標籤
        main_labels = []  # 主線程的標籤
        
        # ✅ v2.8.1: 追蹤軌跡區塊和滑鼠動作
        in_trajectory = False  # 是否在軌跡區塊內
        pending_trajectory_info = ""  # 待處理的軌跡資訊
        action_counter = 0  # 動作計數器
        connection_labels = {}  # 連線標籤 {(from_label, to_label): label_text}
        last_action_label = None  # 上一個動作的標籤
        
        # ✅ 自動添加起點
        start_label = '#[起點]'
        label_commands[start_label] = []
        label_order.append(start_label)
        last_action_label = start_label
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('##'):
                continue
            
            # ✅ v2.8.1: 識別軌跡區塊
            if line.startswith('# [軌跡]'):
                # 提取軌跡摘要資訊
                pending_trajectory_info = "軌跡"
                in_trajectory = True
                continue
            elif line == '# [軌跡開始]':
                in_trajectory = True
                continue
            elif line == '# [軌跡結束]':
                in_trajectory = False
                continue
            elif in_trajectory and line.startswith('>移動至'):
                # 跳過軌跡內的移動指令
                continue
            
            # ✅ v2.8.1: 識別滑鼠點擊動作（在軌跡外）
            if (line.startswith('>左鍵點擊') or line.startswith('>右鍵點擊') or 
                line.startswith('>中鍵點擊') or line.startswith('>左鍵雙擊')):
                action_counter += 1
                # 提取點擊動作的簡化名稱
                if '>左鍵點擊' in line:
                    action_name = '左鍵點擊'
                elif '>右鍵點擊' in line:
                    action_name = '右鍵點擊'
                elif '>中鍵點擊' in line:
                    action_name = '中鍵點擊'
                elif '>左鍵雙擊' in line:
                    action_name = '左鍵雙擊'
                else:
                    action_name = '點擊'
                
                # 創建動作節點
                action_label = f'#[{action_name}_{action_counter}]'
                label_commands[action_label] = [line]
                label_order.append(action_label)
                
                # 記錄連線標籤（如果有待處理的軌跡）
                if last_action_label and pending_trajectory_info:
                    connection_labels[(last_action_label, action_label)] = pending_trajectory_info
                    pending_trajectory_info = ""  # 清除已使用的軌跡資訊
                
                last_action_label = action_label
                continue
            
            # ✅ v2.8.0: 識別新的區塊結構（視為特殊標籤）
            # 並行區塊
            if line == '>並行開始':
                # 創建唯一的並行區塊標籤
                parallel_count = sum(1 for l in label_order if '[並行區塊' in l)
                block_label = f'#[並行區塊{parallel_count + 1}]' if parallel_count > 0 else '#[並行區塊]'
                label_commands[block_label] = []
                label_order.append(block_label)
                current_label = block_label
                # 追蹤此並行區塊包含的線程
                if not hasattr(self, 'parallel_threads'):
                    self.parallel_threads = {}  # {parallel_label: [thread_labels]}
                self.parallel_threads[block_label] = []
                block_stack.append(('parallel', block_label))
                continue
            elif line == '>並行結束':
                if block_stack and block_stack[-1][0] == 'parallel':
                    block_stack.pop()
                current_label = None
                continue
            elif line.startswith('>線程>'):
                thread_name = line[4:].strip()
                thread_label = f'#[線程:{thread_name}]'
                label_commands[thread_label] = []
                label_order.append(thread_label)
                current_label = thread_label
                # 記錄此線程屬於哪個並行區塊
                if block_stack and block_stack[-1][0] == 'parallel':
                    parallel_label = block_stack[-1][1]
                    self.parallel_threads[parallel_label].append(thread_label)
                continue
            elif line == '>線程結束':
                current_label = None
                continue
            
            # 觸發器（視為背景線程）
            if line.startswith('>每隔>'):
                interval = line[4:].strip()
                trigger_label = f'#[定時:{interval}]'
                label_commands[trigger_label] = []
                label_order.append(trigger_label)
                background_labels.append(trigger_label)  # 標記為背景
                current_label = trigger_label
                continue
            elif line == '>每隔結束':
                current_label = None
                continue
            elif line.startswith('>當偵測到>'):
                target = line[6:].split(',')[0].strip()
                trigger_label = f'#[監聽:{target}]'
                label_commands[trigger_label] = []
                label_order.append(trigger_label)
                background_labels.append(trigger_label)  # 標記為背景
                current_label = trigger_label
                continue
            elif line == '>當偵測結束':
                current_label = None
                continue
            elif line.startswith('>優先偵測>'):
                target = line[6:].strip()
                trigger_label = f'#[優先:{target}]'
                label_commands[trigger_label] = []
                label_order.append(trigger_label)
                current_label = trigger_label
                continue
            elif line == '>優先偵測結束':
                current_label = None
                continue
            
            # 狀態機
            if line.startswith('>狀態機>'):
                machine_name = line[5:].strip()
                sm_label = f'#[狀態機:{machine_name}]'
                label_commands[sm_label] = []
                label_order.append(sm_label)
                current_label = sm_label
                block_stack.append('state_machine')
                continue
            elif line == '>狀態機結束':
                if block_stack and block_stack[-1] == 'state_machine':
                    block_stack.pop()
                current_label = None
                continue
            elif line.startswith('>狀態>'):
                state_def = line[4:].strip()
                state_name = state_def.replace(', 初始', '').replace(',初始', '').strip()
                is_initial = '初始' in state_def
                state_label = f'#[狀態:{state_name}]{"(初始)" if is_initial else ""}'
                label_commands[state_label] = []
                label_order.append(state_label)
                current_label = state_label
                continue
            
            # 識別一般標籤（視為主線程）
            # ✅ v2.8.2: 跳過 "# " 開頭的註解（如 "# 並行區塊範例"）
            if line.startswith('#') and not line.startswith('##') and not line.startswith('# [') and not line.startswith('# '):
                current_label = line
                label_commands[current_label] = []
                label_order.append(current_label)
                main_labels.append(current_label)  # 標記為主線程
            elif current_label:
                label_commands[current_label].append(line)
        
        # ✅ 自動添加終點
        end_label = '#[終點]'
        label_commands[end_label] = []
        label_order.append(end_label)
        
        if not label_order:
            return
        
        # 將標籤分配到行 (row) - 根據跳轉關係
        label_to_row = {}
        label_to_col = {}
        current_row = 0
        current_col = 0
        
        # 計算每個標籤的類型
        label_types = {}
        for label, commands in label_commands.items():
            # ✅ v2.8.0: 識別特殊區塊類型
            if '[起點]' in label:
                label_types[label] = "start"
            elif '[終點]' in label:
                label_types[label] = "end"
            elif '[並行區塊]' in label:
                label_types[label] = "parallel"
            elif '[線程:' in label:
                label_types[label] = "thread"
            elif '[定時:' in label or '[監聽:' in label or '[優先:' in label:
                label_types[label] = "trigger"
            elif '[狀態機:' in label:
                label_types[label] = "state_machine"
            elif '[狀態:' in label:
                label_types[label] = "state"
            # ✅ v2.8.1: 識別滑鼠動作節點
            elif '[左鍵點擊' in label or '[右鍵點擊' in label or '[中鍵點擊' in label or '[左鍵雙擊' in label:
                label_types[label] = "action"
            elif any(c.startswith('>>>') for c in commands):
                label_types[label] = "condition"
            else:
                label_types[label] = "label"
        
        # 簡單佈局：根據依賴關係排列
        # 簡單佈局：根據依賴關係與順序排列
        visited = set()
        
        def assign_position(label, row, col):
            if label in visited:
                return col
            visited.add(label)
            label_to_row[label] = row
            label_to_col[label] = col
            
            # 優先處理跳轉關係 (>># 或 >>>#)
            commands = label_commands.get(label, [])
            for cmd in commands:
                if cmd.startswith('>>#'):
                    target = '#' + cmd.split('#')[1].split(',')[0].strip()
                    if target in label_order and target not in visited:
                        assign_position(target, row, col + 1)
                elif cmd.startswith('>>>#'):
                    target = '#' + cmd.split('#')[1].split(',')[0].strip()
                    if target in label_order and target not in visited:
                        assign_position(target, row + 1, col)
            
            # ✅ v2.8.2: 處理自動順序流 - 如果下一個標籤在腳本中緊隨其後，則向右排列
            idx = label_order.index(label) if label in label_order else -1
            if idx != -1 and idx + 1 < len(label_order):
                next_label = label_order[idx + 1]
                # 排除特殊功能標籤，讓主流程橫向發展
                if next_label not in visited and not any(kw in next_label for kw in ['[定時:', '[監聽:', '[優先:', '[終點]']):
                    assign_position(next_label, row, col + 1)
            
            return col
        
        # 從起點開始繪製
        if label_order:
            assign_position(label_order[0], 0, 0)
        
        # 填充任何脫漏的標籤
        for label in label_order:
            if label not in label_to_row:
                max_r = max(label_to_row.values()) if label_to_row else 0
                assign_position(label, max_r + 1, 0)
        
        # 將終點放置在最右側
        if end_label in label_order:
            final_col = max(label_to_col.values()) if label_to_col else 0
            label_to_row[end_label] = label_to_row.get(start_label, 0)
            label_to_col[end_label] = final_col + 1
        
        
        # ✅ v2.8.2: 處理並行區塊的分叉佈局
        # 讓並行區塊的線程垂直分叉顯示
        if hasattr(self, 'parallel_threads') and self.parallel_threads:
            for parallel_label, thread_labels in self.parallel_threads.items():
                if parallel_label in label_to_row and len(thread_labels) > 0:
                    parallel_col = label_to_col.get(parallel_label, 0)
                    parallel_row = label_to_row.get(parallel_label, 0)
                    
                    # 計算線程的垂直分佈
                    # 線程從並行區塊的右側開始，垂直分叉
                    thread_start_col = parallel_col + 1
                    thread_count = len(thread_labels)
                    
                    for i, thread_label in enumerate(thread_labels):
                        if thread_label in label_to_row:
                            # ✅ v2.8.2: 增加垂直間距，讓分叉更清晰
                            # 將線程均勻分布在並行區塊的上下
                            # 例如 2 個線程：row -1 和 +1（間距 2）
                            # 例如 3 個線程：row -1.5, 0, +1.5（間距 1.5）
                            spacing = 1.5  # 線程間距係數
                            center_offset = (thread_count - 1) / 2.0
                            offset = (i - center_offset) * spacing
                            new_row = parallel_row + offset
                            
                            label_to_row[thread_label] = new_row
                            label_to_col[thread_label] = thread_start_col
        
        # 創建 PCB 節點
        label_to_idx = {}
        for label in label_order:
            row = label_to_row.get(label, 0)
            col = label_to_col.get(label, 0)
            
            x = start_x + col * h_gap
            y = start_y + row * v_gap
            
            idx = len(self.pcb_nodes)
            label_to_idx[label] = idx
            
            # 判斷節點類型
            node_type = label_types.get(label, "label")
            
            self.pcb_nodes.append({
                "x": x, "y": y,
                "width": node_width, "height": node_height,
                "name": label, "row": row, "col": col,
                "type": node_type, "tag": f"pcb_node_{idx}",
                "commands": label_commands.get(label, []),
            })
            
            # 同時建立舊格式 (兼容)
            self.workflow_nodes[label] = {
                'x': x, 'y': y, 'level': row, 'items': [],
                'connections': 0,
            }
        
        # 解析連線
        # ✅ v2.8.0: 首先從起點連接到所有背景任務和主線程第一個標籤
        start_idx = label_to_idx.get('#[起點]')
        if start_idx is not None:
            # 連接到所有背景任務
            for bg_label in background_labels:
                bg_idx = label_to_idx.get(bg_label)
                if bg_idx is not None:
                    self.pcb_connections.append((start_idx, bg_idx, "parallel"))
            
            # 連接到主線程第一個標籤
            if main_labels:
                first_main_idx = label_to_idx.get(main_labels[0])
                if first_main_idx is not None:
                    self.pcb_connections.append((start_idx, first_main_idx, "main"))
        
        # ✅ v2.8.2: 並行區塊連接到其所屬線程（分叉連線）
        if hasattr(self, 'parallel_threads') and self.parallel_threads:
            for parallel_label, thread_labels in self.parallel_threads.items():
                parallel_idx = label_to_idx.get(parallel_label)
                if parallel_idx is not None:
                    for thread_label in thread_labels:
                        thread_idx = label_to_idx.get(thread_label)
                        if thread_idx is not None:
                            self.pcb_connections.append((parallel_idx, thread_idx, "fork"))
        
        for label, commands in label_commands.items():
            from_idx = label_to_idx.get(label)
            if from_idx is None:
                continue
            
            success_target = None
            fail_target = None
            
            for cmd in commands:
                if cmd.startswith('>>#'):
                    success_target = '#' + cmd.split('#')[1].split(',')[0].strip()
                elif cmd.startswith('>>>#'):
                    fail_target = '#' + cmd.split('#')[1].split(',')[0].strip()
            
            # 找下一個順序標籤（main 連線）
            label_idx_in_order = label_order.index(label) if label in label_order else -1
            if label_idx_in_order >= 0 and label_idx_in_order < len(label_order) - 1:
                next_label = label_order[label_idx_in_order + 1]
                next_idx = label_to_idx.get(next_label)
                
                # ✅ v2.8.2: 跳過並行區塊到線程的連線（已經用 fork 處理）
                is_parallel_to_thread = False
                if hasattr(self, 'parallel_threads') and self.parallel_threads:
                    for parallel_label, thread_labels in self.parallel_threads.items():
                        if label == parallel_label and next_label in thread_labels:
                            is_parallel_to_thread = True
                            break
                        # 也跳過線程到下一個線程的連線
                        if label in thread_labels and next_label in thread_labels:
                            is_parallel_to_thread = True
                            break
                
                # 如果已經有 success/fail 跳轉，不添加 main
                if next_idx is not None and success_target != next_label and fail_target != next_label and not is_parallel_to_thread:
                    # 判斷是否為迴圈（向左回頭）
                    if self.pcb_nodes[next_idx]["col"] < self.pcb_nodes[from_idx]["col"]:
                        self.pcb_connections.append((from_idx, next_idx, "loop"))
                    else:
                        self.pcb_connections.append((from_idx, next_idx, "main"))
            
            # 添加 success 連線
            if success_target and success_target in label_to_idx:
                to_idx = label_to_idx[success_target]
                path_type = "loop" if self.pcb_nodes[to_idx]["col"] < self.pcb_nodes[from_idx]["col"] else "success"
                self.pcb_connections.append((from_idx, to_idx, path_type))
                self.workflow_connections.append((label, success_target, 'success'))
            
            # 添加 failure 連線
            if fail_target and fail_target in label_to_idx:
                to_idx = label_to_idx[fail_target]
                path_type = "loop" if self.pcb_nodes[to_idx]["col"] < self.pcb_nodes[from_idx]["col"] else "failure"
                self.pcb_connections.append((from_idx, to_idx, path_type))
                self.workflow_connections.append((label, fail_target, 'fail'))
        
        # 自動生成群組（根據類型分組）
        condition_nodes = [i for i, n in enumerate(self.pcb_nodes) if n["type"] == "condition"]
        if condition_nodes:
            self.pcb_groups.append({
                "nodes": condition_nodes,
                "color": "#8957e5",
                "name": "條件判斷區"
            })
        
        # ✅ v2.8.1: 儲存連線標籤（用於軌跡標籤顯示）
        self.pcb_connection_labels = {}
        for (from_label, to_label), label_text in connection_labels.items():
            from_idx = label_to_idx.get(from_label)
            to_idx = label_to_idx.get(to_label)
            if from_idx is not None and to_idx is not None:
                self.pcb_connection_labels[(from_idx, to_idx)] = label_text
        
        # 繪製
        self._draw_pcb_graph()
    
    def _draw_pcb_graph(self):
        """繪製 PCB 風格圖形"""
        self.workflow_canvas.configure(bg="#010409")
        
        # 1. 創建路由器 (v2.8.2: 傳入縮放比例)
        self.pcb_router = GlobalRouter(self.pcb_nodes, scale=getattr(self, "workflow_scale", 1.0))
        
        # 2. 繪製連線
        self._draw_pcb_connections()
        
        # 3. 繪製節點
        for idx, node in enumerate(self.pcb_nodes):
            self._draw_pcb_node(idx, node)
        
        # 4. 繪製群組框
        self._draw_pcb_groups()
        
        # 5. 調整層級
        self.workflow_canvas.tag_lower("pcb_connection")
        
        # 6. 更新滾動區域
        bbox = self.workflow_canvas.bbox("all")
        if bbox:
            padding = 100
            self.workflow_canvas.configure(scrollregion=(
                bbox[0] - padding,
                bbox[1] - padding,
                bbox[2] + padding,
                bbox[3] + padding
            ))
    
    def _draw_pcb_node(self, idx, node):
        """繪製單個 PCB 風格節點 - GitHub Actions 風格 (圓角矩形)"""
        x, y = node["x"], node["y"]
        w, h = node["width"], node["height"]
        name = node["name"]
        node_type = node.get("type", "label")
        tag = node["tag"]
        
        # 根據類型設定樣式
        style = self._get_pcb_node_style(name, node_type)
        
        # 陰影 (圓角)
        create_rounded_rect(
            self.workflow_canvas,
            x + 2, y + 2, x + w + 2, y + h + 2,
            radius=PCB_CORNER_RADIUS,
            fill="#010409", outline="",
            tags=(tag, "pcb_node")
        )
        
        # 卡片背景 (圓角矩形)
        create_rounded_rect(
            self.workflow_canvas,
            x, y, x + w, y + h,
            radius=PCB_CORNER_RADIUS,
            fill=PCB_COLORS["card"], outline=style["border"], width=2,
            tags=(tag, "pcb_node", "pcb_card")
        )
        
        # 左側圖示背景 (GitHub 風格 - 較小的圓形)
        icon_x, icon_y = x + 16, y + h // 2
        self.workflow_canvas.create_oval(
            icon_x - 8, icon_y - 8, icon_x + 8, icon_y + 8,
            fill=style["icon_color"], outline="",
            tags=(tag, "pcb_node")
        )
        
        # 圖示文字 (使用 ✓ 符號類似 GitHub Actions)
        icon_text = "✓" if style["icon"] == "▶" else style["icon"]
        self.workflow_canvas.create_text(
            icon_x, icon_y, text=icon_text,
            fill="white", font=("Segoe UI", 7, "bold"),
            tags=(tag, "pcb_node")
        )
        
        # 標題文字 (置左)
        display_name = name.replace("#", "")
        if len(display_name) > 12:
            display_name = display_name[:11] + ".."
        
        self.workflow_canvas.create_text(
            x + 30, y + h // 2, text=display_name,
            fill=PCB_COLORS["text"], font=("Segoe UI", 9),
            anchor="w", tags=(tag, "pcb_node", "pcb_text")
        )
        
        # 右側時間標籤 (GitHub Actions 風格)
        time_text = node.get("duration", "")
        if time_text:
            self.workflow_canvas.create_text(
                x + w - 10, y + h // 2, text=time_text,
                fill="#8b949e", font=("Segoe UI", 8),
                anchor="e", tags=(tag, "pcb_node", "pcb_time")
            )
        
        # 輸入連接埠
        self.workflow_canvas.create_oval(
            x - 4, icon_y - 4, x + 4, icon_y + 4,
            fill="#161b22", outline=style["border"], width=2,
            tags=(tag, "pcb_node", "pcb_port")
        )
        
        # 輸出連接埠
        self.workflow_canvas.create_oval(
            x + w - 4, icon_y - 4, x + w + 4, icon_y + 4,
            fill="#161b22", outline=style["border"], width=2,
            tags=(tag, "pcb_node", "pcb_port")
        )
        
        # 綁定事件
        self.workflow_canvas.tag_bind(tag, "<Enter>",
            lambda e, n=node: self._show_node_tooltip(e, n["name"], n.get("commands", [])))
        self.workflow_canvas.tag_bind(tag, "<Leave>",
            lambda e: self._hide_node_tooltip())
        
        # ✅ v2.8.0: 綁定拖曳事件
        self.workflow_canvas.tag_bind(tag, "<ButtonPress-1>",
            lambda e, t=tag, n=node: self._on_node_press(e, t, n))
        self.workflow_canvas.tag_bind(tag, "<B1-Motion>",
            lambda e, t=tag, n=node: self._on_node_drag(e, t, n))
        # ✅ v2.8.1: 綁定釋放事件以清理拖曳狀態
        self.workflow_canvas.tag_bind(tag, "<ButtonRelease-1>",
            lambda e: self._on_node_release(e))
    
    def _get_pcb_node_style(self, name, node_type):
        """取得節點樣式"""
        # ✅ v2.8.0: 新增特殊節點類型樣式
        if node_type == "start" or '[起點]' in name:
            return {"icon": "▶", "icon_color": "#3fb950", "border": "#3fb950"}
        elif node_type == "end" or '[終點]' in name:
            return {"icon": "■", "icon_color": "#6e7681", "border": "#6e7681"}  # 灰色，因為可能未連接
        elif node_type == "trigger" or '[監聽:' in name or '[定時:' in name or '[優先:' in name:
            return {"icon": "⚡", "icon_color": "#f0883e", "border": "#f0883e"}  # 橘色
        elif node_type == "parallel" or '[並行區塊]' in name:
            return {"icon": "⫛", "icon_color": "#a371f7", "border": "#a371f7"}  # 紫色
        elif node_type == "thread" or '[線程:' in name:
            return {"icon": "∥", "icon_color": "#a371f7", "border": "#a371f7"}  # 紫色
        elif node_type == "state_machine" or '[狀態機:' in name:
            return {"icon": "⊚", "icon_color": "#ec6547", "border": "#ec6547"}  # 紅橘色
        elif node_type == "state" or '[狀態:' in name:
            return {"icon": "◉", "icon_color": "#ec6547", "border": "#ec6547"}  # 紅橘色
        # ✅ v2.8.1: 滑鼠動作節點樣式
        elif node_type == "action" or '[左鍵點擊' in name or '[右鍵點擊' in name or '[中鍵點擊' in name or '[左鍵雙擊' in name:
            return {"icon": "🖱", "icon_color": "#58a6ff", "border": "#58a6ff"}  # 藍色滑鼠
        elif node_type == "condition" or "檢查" in name or "驗證" in name:
            return {"icon": "?", "icon_color": "#8957e5", "border": "#8957e5"}
        elif "成功" in name:
            return {"icon": "✓", "icon_color": "#3fb950", "border": "#3fb950"}
        elif "失敗" in name:
            return {"icon": "✗", "icon_color": "#f85149", "border": "#f85149"}
        elif name.startswith("#"):
            return {"icon": "#", "icon_color": "#58a6ff", "border": "#58a6ff"}
        return {"icon": "●", "icon_color": "#6e7681", "border": "#6e7681"}
    
    def _on_node_press(self, event, tag, node):
        """節點按下事件"""
        # ✅ v2.8.2: 使用畫布座標
        self._drag_data = {
            "tag": tag,
            "node": node,
            "x": self.workflow_canvas.canvasx(event.x),
            "y": self.workflow_canvas.canvasy(event.y)
        }
    
    def _on_node_drag(self, event, tag, node):
        """節點拖曳事件"""
        if not hasattr(self, '_drag_data') or self._drag_data is None:
            return
        
        # ✅ v2.8.2: 使用畫布座標而非視窗座標，修復縮放後拖曳錯位問題
        canvas_x = self.workflow_canvas.canvasx(event.x)
        canvas_y = self.workflow_canvas.canvasy(event.y)
        
        dx = canvas_x - self._drag_data["x"]
        dy = canvas_y - self._drag_data["y"]
        
        self.workflow_canvas.move(tag, dx, dy)
        
        # 更新節點座標
        node["x"] += dx
        node["y"] += dy
        
        self._drag_data["x"] = canvas_x
        self._drag_data["y"] = canvas_y
        
        # ✅ 重新繪製所有連線 (v2.8.2: 傳入縮放比例)
        self.workflow_canvas.delete("pcb_connection")
        self.pcb_router = GlobalRouter(self.pcb_nodes, scale=getattr(self, "workflow_scale", 1.0))
        self._draw_pcb_connections()
    
    def _on_node_release(self, event):
        """✅ v2.8.1: 節點釋放事件 - 清理拖曳狀態"""
        self._drag_data = None
    
    def _draw_pcb_connections(self):
        """繪製 PCB 風格連線 (v2.8.2: 支援視覺縮放)"""
        scale = getattr(self, "workflow_scale", 1.0)
        
        for from_idx, to_idx, path_type in self.pcb_connections:
            if from_idx >= len(self.pcb_nodes) or to_idx >= len(self.pcb_nodes):
                continue
            
            from_node = self.pcb_nodes[from_idx]
            to_node = self.pcb_nodes[to_idx]
            
            # 計算路徑
            path = self.pcb_router.route(from_node, to_node, path_type, from_idx, to_idx)
            
            # ✅ v2.8.1: 檢查目標節點是否無作用
            to_node_name = to_node.get("name", "")
            to_node_type = to_node.get("type", "")
            is_inactive_target = (to_node_type == "end" or '[終點]' in to_node_name)
            
            color = PCB_COLORS.get("inactive", "#6e7681") if (is_inactive_target and path_type == "main") else PCB_COLORS.get(path_type, PCB_COLORS["main"])
            
            if len(path) >= 2:
                points = []
                for px, py in path:
                    points.extend([px, py])
                
                # ✅ 縮放連線寬度
                self.workflow_canvas.create_line(
                    *points, fill=color, width=max(1, int(PCB_LINE_WIDTH * scale)),
                    capstyle="round", joinstyle="round",
                    tags=("pcb_connection",)
                )
            
            # 繪製標籤
            if path_type in ("success", "failure", "loop"):
                labels = {"success": "成功", "failure": "失敗", "loop": "重試"}
                lx, ly = self.pcb_router.find_label_position(path)
                
                # ✅ 縮放標籤尺寸與字體
                rw, rh = 16 * scale, 8 * scale
                f_size = max(5, int(7 * scale))
                
                self.workflow_canvas.create_rectangle(
                    lx - rw, ly - rh, lx + rw, ly + rh,
                    fill="#161b22", outline=color, width=max(1, int(1 * scale)),
                    tags=("pcb_connection", "pcb_label")
                )
                self.workflow_canvas.create_text(
                    lx, ly, text=labels.get(path_type, ""),
                    fill=color, font=("Microsoft JhengHei", f_size, "bold"),
                    tags=("pcb_connection", "pcb_label")
                )
            
            # ✅ v2.8.1: 繪製軌跡標籤
            if hasattr(self, 'pcb_connection_labels') and (from_idx, to_idx) in self.pcb_connection_labels:
                trajectory_label = self.pcb_connection_labels[(from_idx, to_idx)]
                lx, ly = self.pcb_router.find_label_position(path)
                rw, rh = 18 * scale, 8 * scale
                f_size = max(5, int(7 * scale))
                
                self.workflow_canvas.create_rectangle(
                    lx - rw, ly - rh, lx + rw, ly + rh,
                    fill="#161b22", outline="#f0883e", width=max(1, int(1 * scale)),
                    tags=("pcb_connection", "pcb_label")
                )
                self.workflow_canvas.create_text(
                    lx, ly, text=trajectory_label,
                    fill="#f0883e", font=("Microsoft JhengHei", f_size, "bold"),
                    tags=("pcb_connection", "pcb_label")
                )
    
    def _draw_pcb_groups(self):
        """繪製 PCB 風格群組框"""
        padding = 15
        for group in self.pcb_groups:
            if not group.get("nodes"):
                continue
            
            group_nodes = [self.pcb_nodes[i] for i in group["nodes"] if i < len(self.pcb_nodes)]
            if not group_nodes:
                continue
            
            min_x = min(n["x"] for n in group_nodes) - padding
            min_y = min(n["y"] for n in group_nodes) - padding
            max_x = max(n["x"] + n["width"] for n in group_nodes) + padding
            max_y = max(n["y"] + n["height"] for n in group_nodes) + padding
            
            self.workflow_canvas.create_rectangle(
                min_x, min_y, max_x, max_y,
                outline=group["color"], width=2, fill="", dash=(4, 2),
                tags=("pcb_group",)
            )
            self.workflow_canvas.create_text(
                min_x + 4, min_y - 8, text=group.get("name", ""),
                fill=group["color"], font=("Microsoft JhengHei", 8),
                anchor="w", tags=("pcb_group_label",)
            )
    
    def _calculate_workflow_layout(self, labels):
        """計算節點佈局位置"""
        if not labels:
            return
        
        # 簡單的層級佈局：從上到下排列
        start_x = 150
        start_y = 80
        x_spacing = 300
        y_spacing = 120
        
        # 統計每個節點的連接數量（入度+出度）
        connection_count = {label: 0 for label in labels}
        for from_label, to_label, conn_type in self.workflow_connections:
            if from_label in connection_count:
                connection_count[from_label] += 1
            if to_label in connection_count:
                connection_count[to_label] += 1
        
        # 建立標籤到層級的映射
        label_levels = {}
        visited = set()
        
        def get_level(label, level=0):
            if label in visited or label not in labels:
                return
            visited.add(label)
            label_levels[label] = max(label_levels.get(label, 0), level)
            
            # 查找此標籤的子節點
            for from_label, to_label, conn_type in self.workflow_connections:
                if from_label == label:
                    get_level(to_label, level + 1)
        
        # 從第一個標籤開始
        if labels:
            get_level(labels[0], 0)
        
        # 為未訪問的標籤分配層級
        for i, label in enumerate(labels):
            if label not in label_levels:
                label_levels[label] = i
        
        # 分配位置
        level_offsets = {}  # 記錄每層已使用的偏移
        for label in labels:
            level = label_levels[label]
            offset = level_offsets.get(level, 0)
            level_offsets[level] = offset + 1
            
            x = start_x + offset * x_spacing
            y = start_y + level * y_spacing
            
            self.workflow_nodes[label] = {
                'x': x,
                'y': y,
                'level': level,
                'connections': connection_count.get(label, 0),  # 連接數量
                'items': []  # 畫布元件 IDs
            }
    
    def _draw_workflow_node(self, label, commands):
        """繪製工作流節點（Mini Metro 風格 - 全部使用圓形）"""
        if label not in self.workflow_nodes:
            return
        
        node_data = self.workflow_nodes[label]
        x, y = node_data['x'], node_data['y']
        
        # 分析節點類型
        has_condition = any(c.startswith('>>>') for c in commands)
        is_start = label == list(self.workflow_nodes.keys())[0] if self.workflow_nodes else False
        is_end = not any(conn[0] == label for conn in self.workflow_connections)
        
        # 🎯 根據連接數量動態調整圓圈大小
        # 基礎半徑：45px（足夠容納4個中文字），每多一個連接增加3px
        connections = node_data.get('connections', 0)
        radius = 45 + min(connections * 3, 30)  # 基礎45px，最大75px
        node_data['radius'] = radius  # 保存半徑供路徑計算使用
        
        # 根據類型設定顏色（參考 Mini Metro 的配色）
        if is_start:
            # 開始節點：鮮綠色
            fill_color = "#00b300"
            outline_color = "#ffffff"
            text_color = "#ffffff"
            line_width = 4
        elif is_end:
            # 結束節點：深紅色
            fill_color = "#e63946"
            outline_color = "#ffffff"
            text_color = "#ffffff"
            line_width = 4
        elif has_condition:
            # 條件節點：橙色
            fill_color = "#f77f00"
            outline_color = "#ffffff"
            text_color = "#ffffff"
            line_width = 4
        else:
            # 一般處理節點：藍色
            fill_color = "#0077be"
            outline_color = "#ffffff"
            text_color = "#ffffff"
            line_width = 4
        
        # 繪製正圓形節點（Metro 站點風格）
        # 🎨 確保圓形足夠圓滑（Tkinter的oval已經是抗鋸齒的）
        shape_id = self.workflow_canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline=outline_color,
            width=line_width,
            tags="node_shape"
        )
        node_data['items'].append(shape_id)
        
        # 📝 繪製標籤文字（完整顯示，不縮短）
        label_text = label.replace('#', '')
        
        # 🎯 根據節點大小動態調整字體大小
        if radius < 55:
            font_size = 12
        elif radius < 65:
            font_size = 14
        else:
            font_size = 16
        
        text_id = self.workflow_canvas.create_text(
            x, y,
            text=label_text,
            fill=text_color,
            font=("LINE Seed TW", font_size, "bold") if LINE_SEED_FONT_LOADED else ("Arial", font_size, "bold"),
            tags="node_text",
            width=radius * 1.8  # 📝 限制文字寬度，讓長文字自動換行
        )
        node_data['items'].append(text_id)
        
        # 💬 綁定滑鼠停留事件（顯示浮動提示）
        for item_id in node_data['items']:
            self.workflow_canvas.tag_bind(item_id, "<Enter>", 
                lambda e, lbl=label, cmds=commands: self._show_node_tooltip(e, lbl, cmds))
            self.workflow_canvas.tag_bind(item_id, "<Leave>", 
                lambda e: self._hide_node_tooltip())
    
    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        """創建圓角矩形"""
        points = [
            x1+radius, y1,
            x1+radius, y1,
            x2-radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.workflow_canvas.create_polygon(points, **kwargs, smooth=True)
    
    def _draw_workflow_connections(self):
        """繪製工作流連接線（Mini Metro 風格：使用直線和45度角）
        
        Mini Metro 特點：
        1. 只使用水平線、垂直線、45度斜線
        2. 線路粗而明顯
        3. 顏色鮮艷，易於區分
        4. 避免重疊，使用偏移
        """
        # 通道管理
        channel_offset = 25  # Metro 風格需要更大的間距
        occupied_channels = {}
        
        # 預處理：分配通道
        connections_with_channels = []
        
        for idx, (from_label, to_label, conn_type) in enumerate(self.workflow_connections):
            if from_label not in self.workflow_nodes or to_label not in self.workflow_nodes:
                continue
            
            from_node = self.workflow_nodes[from_label]
            to_node = self.workflow_nodes[to_label]
            
            is_loop = to_node['level'] <= from_node['level']
            
            if is_loop:
                channel = self._allocate_channel(from_node, to_node, occupied_channels, positive=True)
            else:
                channel = self._allocate_channel(from_node, to_node, occupied_channels, positive=False)
            
            connections_with_channels.append((from_label, to_label, conn_type, channel, is_loop))
        
        # 🎨 多彩顏色系統（不限於紅綠）
        metro_colors = [
            "#00d084",  # 翠綠
            "#0077be",  # 寶藍
            "#f77f00",  # 橙色
            "#e63946",  # 紅色
            "#9d4edd",  # 紫色
            "#06ffa5",  # 青綠
            "#ffbe0b",  # 金黃
            "#fb5607",  # 橘紅
            "#8338ec",  # 深紫
            "#3a86ff",  # 亮藍
        ]
        
        # 繪製所有連接線
        for idx, (from_label, to_label, conn_type, channel, is_loop) in enumerate(connections_with_channels):
            from_node = self.workflow_nodes[from_label]
            to_node = self.workflow_nodes[to_label]
            
            # 🎨 使用多彩顏色，根據索引循環選擇
            color = metro_colors[idx % len(metro_colors)]
            width = 5
            
            # 🎯 使用節點的實際半徑
            from_radius = from_node.get('radius', 45)
            to_radius = to_node.get('radius', 45)
            
            # 🎯 智能計算最佳連接點（最短距離）
            start_x, start_y, end_x, end_y = self._calculate_optimal_connection_points(
                from_node['x'], from_node['y'], from_radius,
                to_node['x'], to_node['y'], to_radius
            )
            
            # 🎯 通道偏移 - 完全並行避免重疊
            offset = channel * 50  # 增加到50px確保完全分離
            
            # 使用 Metro 風格的路徑規劃（只用直線和45度角）
            points = self._calculate_metro_path(
                start_x, start_y, 
                end_x, end_y, 
                offset, is_loop
            )
            
            # 繪製線路（不使用 smooth，保持銳利的角度）
            self.workflow_canvas.create_line(
                *points,
                fill=color,
                width=width,
                capstyle=tk.ROUND,  # 圓形端點
                joinstyle=tk.ROUND,  # 圓形連接
                tags="connection"
            )
            
            # 在線路末端繪製箭頭（Metro 風格的小圓點）
            arrow_size = 6
            self.workflow_canvas.create_oval(
                end_x - arrow_size, end_y - arrow_size,
                end_x + arrow_size, end_y + arrow_size,
                fill=color,
                outline=color,
                tags="connection"
            )
    
    def _calculate_optimal_connection_points(self, x1, y1, r1, x2, y2, r2):
        """計算最佳連接點（最短距離原則）
        
        根據兩個節點的相對位置，選擇最佳的出發點和到達點。
        例如：如果目標在左上方，則從左上角出發
        
        Args:
            x1, y1: 起始節點中心
            r1: 起始節點半徑
            x2, y2: 目標節點中心
            r2: 目標節點半徑
        
        Returns:
            (start_x, start_y, end_x, end_y): 最佳連接點
        """
        import math
        
        # 計算方向角度
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 0.001:
            # 防止除零
            return (x1, y1 + r1, x2, y2 - r2)
        
        # 標準化方向向量
        nx = dx / distance
        ny = dy / distance
        
        # 起點：從圓心沿方向向量移動半徑距離
        start_x = x1 + nx * r1
        start_y = y1 + ny * r1
        
        # 終點：從圓心沿反方向移動半徑距離
        end_x = x2 - nx * r2
        end_y = y2 - ny * r2
        
        return (start_x, start_y, end_x, end_y)
    
    def _calculate_metro_path(self, x1, y1, x2, y2, offset, is_loop):
        """計算 Metro 風格路徑（支持斜線，完全並行）
        
        新特點：
        1. 支持45度斜線，更美觀清晰
        2. 完全並行，絕不重疊
        3. 每條線有獨立通道
        4. 智能選擇最佳路徑類型
        
        Returns:
            路徑點列表 [x1, y1, x2, y2, ...]
        """
        if is_loop:
            # 循環路徑：繞外側
            loop_offset = 150 + abs(offset)
            return [
                x1, y1,
                x1, y1 + 40,
                x1 + loop_offset, y1 + 40,
                x1 + loop_offset, y2 - 40,
                x2, y2 - 40,
                x2, y2
            ]
        
        dx = x2 - x1
        dy = y2 - y1
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        # 🎯 完全並行策略：每條線在獨立通道中運行
        
        if offset == 0:
            # 中心線路：使用最簡潔的路徑
            if abs_dx < 20:
                # 垂直
                return [x1, y1, x2, y2]
            elif abs_dy < 20:
                # 水平
                return [x1, y1, x2, y2]
            elif abs(abs_dx - abs_dy) < 30:
                # 🎨 接近45度：使用斜線！
                return [x1, y1, x2, y2]
            else:
                # 正交三段式
                mid_y = (y1 + y2) / 2
                return [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
        else:
            # 🎯 偏移線路：完全並行，永不重疊
            # 計算獨立通道位置
            channel_x = x1 + offset
            
            # 判斷路徑類型
            if abs_dy < 20:
                # 接近水平：使用上下偏移
                offset_y = offset * 0.5
                mid_y = (y1 + y2) / 2 + offset_y
                return [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
            elif abs_dx < 20:
                # 接近垂直：使用左右偏移
                return [x1, y1, channel_x, y1, channel_x, y2, x2, y2]
            elif abs(abs_dx - abs_dy) < 50:
                # 🎨 可以用斜線：創建平行斜線
                # 偏移方向垂直於主方向
                angle = abs(dy) / abs_dx if abs_dx > 0 else 1
                perp_offset_x = offset / (1 + angle)
                perp_offset_y = offset * angle / (1 + angle)
                
                # 起點偏移
                start_offset_x = perp_offset_x if dy * dx > 0 else -perp_offset_x
                start_offset_y = -perp_offset_y
                
                return [
                    x1, y1,
                    x1 + start_offset_x, y1 + start_offset_y,
                    x2 + start_offset_x, y2 + start_offset_y,
                    x2, y2
                ]
            else:
                # 一般情況：四段式完全並行
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
    
    def _allocate_channel(self, from_node, to_node, occupied, positive=False):
        """為連接線分配通道，智能避免重疊
        
        改進算法：
        1. 根據連接方向分配不同的通道組
        2. 優先使用中心通道（offset=0）
        3. 循環線路使用外側通道
        4. 考慮節點層級差異
        
        Args:
            from_node: 起始節點
            to_node: 目標節點
            occupied: 已占用的通道字典
            positive: True=使用正通道（外側），False=使用零或負通道（內側）
        
        Returns:
            分配的通道編號
        """
        key = (from_node['level'], to_node['level'])
        
        if key not in occupied:
            occupied[key] = set()
        
        # 尋找可用通道
        if positive:
            # 循環線路：從1開始往外找
            channel = 1
            while channel in occupied[key]:
                channel += 1
        else:
            # 正常線路：優先使用0，然後±1, ±2...
            channel = 0
            if channel in occupied[key]:
                for offset in range(1, 10):
                    if offset not in occupied[key]:
                        channel = offset
                        break
                    elif -offset not in occupied[key]:
                        channel = -offset
                        break
        
        occupied[key].add(channel)
        return channel
    
    # ❌ 已停用：點擊節點不再回到文字模式
    # def _on_workflow_node_click(self, label):
    #     """點擊節點時跳轉到對應的文字行 - 已停用"""
    #     pass
    
    def _on_workflow_canvas_click(self, event):
        """處理畫布點擊（支援節點拖曳和畫布平移）"""
        # ✅ v2.8.2: 使用畫布座標而非視窗座標
        canvas_x = self.workflow_canvas.canvasx(event.x)
        canvas_y = self.workflow_canvas.canvasy(event.y)
        
        # 檢查是否點擊到 PCB 節點
        clicked_items = self.workflow_canvas.find_overlapping(
            canvas_x - 5, canvas_y - 5,
            canvas_x + 5, canvas_y + 5
        )
        
        # 檢查是否點擊到 pcb_node
        for item in clicked_items:
            tags = self.workflow_canvas.gettags(item)
            if "pcb_node" in tags:
                # 點擊到節點，不啟動畫布平移（讓 tag_bind 處理）
                self.workflow_is_panning = False
                return
        
        # 沒有點擊到節點，啟動畫布拖移
        self.workflow_is_panning = True
        self.workflow_pan_start_x = event.x
        self.workflow_pan_start_y = event.y
        self.workflow_canvas.config(cursor="fleur")
    
    def _on_workflow_canvas_drag(self, event):
        """處理畫布拖移（同步更新節點座標資料）"""
        # ✅ v2.8.2: 如果正在拖曳節點（有 _drag_data），不執行畫布拖移
        if hasattr(self, '_drag_data') and self._drag_data is not None:
            return
        
        if hasattr(self, 'workflow_is_panning') and self.workflow_is_panning:
            # 拖移畫布
            dx = event.x - self.workflow_pan_start_x
            dy = event.y - self.workflow_pan_start_y
            
            # 移動所有視覺元素
            self.workflow_canvas.move("all", dx, dy)
            
            # ✅ v2.8.1: 同步更新 pcb_nodes 座標資料
            if hasattr(self, 'pcb_nodes'):
                for node in self.pcb_nodes:
                    node["x"] += dx
                    node["y"] += dy
            
            # ✅ v2.8.1: 同步更新 workflow_nodes 座標資料
            for label, node_data in self.workflow_nodes.items():
                node_data['x'] += dx
                node_data['y'] += dy
            
            self.workflow_pan_start_x = event.x
            self.workflow_pan_start_y = event.y
    
    def _on_workflow_canvas_release(self, event):
        """處理滑鼠釋放"""
        self.workflow_is_panning = False
        self.workflow_canvas.config(cursor="")
    
    def _show_node_tooltip(self, event, label, commands):
        """💬 顯示節點浮動提示（顯示對應的程式碼）"""
        # 移除舊的提示框
        self._hide_node_tooltip()
        
        # 組合程式碼
        code_lines = [f"{label}"]
        for cmd in commands:
            code_lines.append(f"  {cmd}")
        code_text = "\n".join(code_lines)
        
        # 限制最大長度
        if len(code_text) > 500:
            code_text = code_text[:500] + "..."
        
        # 創建浮動提示框
        tooltip = tk.Toplevel(self)
        tooltip.wm_overrideredirect(True)  # 無邊框
        tooltip.wm_geometry(f"+{event.x_root + 15}+{event.y_root + 15}")
        
        # 背景框
        frame = tk.Frame(tooltip, bg="#2d2d30", relief=tk.SOLID, borderwidth=1)
        frame.pack()
        
        # 文字
        label_widget = tk.Label(
            frame,
            text=code_text,
            bg="#2d2d30",
            fg="#d4d4d4",
            font=("LINE Seed TW", 10) if LINE_SEED_FONT_LOADED else ("Consolas", 10),
            justify=tk.LEFT,
            padx=10,
            pady=8
        )
        label_widget.pack()
        
        self.workflow_tooltip = tooltip
    
    def _hide_node_tooltip(self):
        """隱藏浮動提示"""
        if self.workflow_tooltip:
            self.workflow_tooltip.destroy()
            self.workflow_tooltip = None
    
    def _on_workflow_click(self, event):
        """處理畫布點擊事件"""
        # 檢查是否點擊到節點
        clicked_items = self.workflow_canvas.find_overlapping(
            event.x - 5, event.y - 5,
            event.x + 5, event.y + 5
        )
        
        # 尋找被點擊的節點
        clicked_node_label = None
        for label, node_data in self.workflow_nodes.items():
            for item_id in node_data.get('items', []):
                if item_id in clicked_items:
                    clicked_node_label = label
                    break
            if clicked_node_label:
                break
        
        if clicked_node_label:
            # 點擊到節點：準備拖移
            self.workflow_dragging_node = clicked_node_label
            self.workflow_drag_start_x = event.x
            self.workflow_drag_start_y = event.y
        else:
            # 點擊空白：準備拖移畫布
            self.workflow_is_panning = True
            self.workflow_pan_start_x = event.x
            self.workflow_pan_start_y = event.y
            self.workflow_canvas.config(cursor="fleur")
    
    def _on_workflow_drag(self, event):
        """處理拖移事件"""
        if self.workflow_dragging_node:
            # 拖移節點
            dx = event.x - self.workflow_drag_start_x
            dy = event.y - self.workflow_drag_start_y
            
            node_data = self.workflow_nodes[self.workflow_dragging_node]
            
            # 移動節點的所有元件
            for item_id in node_data.get('items', []):
                self.workflow_canvas.move(item_id, dx, dy)
            
            # 更新節點位置
            node_data['x'] += dx
            node_data['y'] += dy
            
            # 更新起點
            self.workflow_drag_start_x = event.x
            self.workflow_drag_start_y = event.y
            
            # 重繪連接線
            self.workflow_canvas.delete("connection")
            self._draw_workflow_connections()
            
        elif self.workflow_is_panning:
            # 拖移畫布
            dx = event.x - self.workflow_pan_start_x
            dy = event.y - self.workflow_pan_start_y
            
            self.workflow_canvas.move("all", dx, dy)
            
            self.workflow_pan_start_x = event.x
            self.workflow_pan_start_y = event.y
    
    def _on_workflow_release(self, event):
        """處理釋放事件"""
        self.workflow_dragging_node = None
        self.workflow_is_panning = False
        self.workflow_canvas.config(cursor="")
    
    def _on_workflow_zoom(self, event):
        """處理滾輪縮放"""
        if event.delta > 0:
            scale = 1.1
        else:
            scale = 0.9
        
        self.workflow_scale *= scale
        
        # ✅ v2.8.2: 縮放時同步更新 pcb_nodes 座標
        # 計算縮放中心點（畫布座標）
        cx = self.workflow_canvas.canvasx(event.x)
        cy = self.workflow_canvas.canvasy(event.y)
        
        # 更新所有節點座標與尺寸
        if hasattr(self, 'pcb_nodes'):
            for node in self.pcb_nodes:
                # 套用縮放公式：new_pos = center + (old_pos - center) * scale
                node["x"] = cx + (node["x"] - cx) * scale
                node["y"] = cy + (node["y"] - cy) * scale
                # ✅ 確保寬高也同步更新，讓路由器計算正確
                node["width"] = node.get("width", 150) * scale
                node["height"] = node.get("height", 36) * scale
        
        # 更新 workflow_nodes 座標
        if hasattr(self, 'workflow_nodes'):
            for label, node_data in self.workflow_nodes.items():
                node_data['x'] = cx + (node_data['x'] - cx) * scale
                node_data['y'] = cy + (node_data['y'] - cy) * scale
        
        self.workflow_canvas.scale("all", event.x, event.y, scale, scale)
    
    def _show_workflow_context_menu(self, event):
        """顯示右鍵選單"""
        menu = tk.Menu(self, tearoff=0, bg="#2d2d30", fg="white")
        menu.add_command(label="🏠 恢復原始大小 (100%)", command=self._reset_workflow_zoom)
        menu.add_command(label="🔄 自動排列", command=self._auto_arrange_workflow)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _reset_workflow_zoom(self):
        """🏠 恢復原始大小 (100%) - 最有效的補救措施"""
        if not hasattr(self, 'workflow_scale') or self.workflow_scale == 1.0:
            return
            
        # 計算還原倍率 (目前的倒數)
        ratio = 1.0 / self.workflow_scale
        
        # ✅ 還原邏輯座標資料 (以 0,0 為準還原，確保座標系統回歸標準)
        if hasattr(self, 'pcb_nodes'):
            for node in self.pcb_nodes:
                node["x"] *= ratio
                node["y"] *= ratio
                # 強制重設為原始預設尺寸
                node["width"] = 150
                node["height"] = 36
        
        # 還原主節點資料
        if hasattr(self, 'workflow_nodes'):
            for label, node_data in self.workflow_nodes.items():
                node_data['x'] *= ratio
                node_data['y'] *= ratio
        
        # 重設全域倍率
        self.workflow_scale = 1.0
        
        # ✅ 清除畫布並以 1.0 倍率重繪所有內容 (這會讓所有線條與字體回歸精準)
        self.workflow_canvas.delete("all")
        self._draw_pcb_graph()
        
    def _auto_arrange_workflow(self):
        """自動重新排列節點"""
        # 重新解析和繪製
        text_content = self.text_editor.get("1.0", tk.END).strip()
        if text_content:
            self._parse_and_draw_workflow(text_content)


class ScreenCaptureSelector(tk.Toplevel):
    """螢幕截圖選取工具"""
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.canvas_start_x = None
        self.canvas_start_y = None
        self.rect_id = None
        self.result = None
        self.ready = False  # 是否準備好截圖
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        self.text_id = self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text="正在準備截圖...",
            font=font_tuple(18, "bold"),
            fill="yellow"
        )
        
        # 綁定事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.focus_force()
        
        # 延遲100ms後才允許截圖(視窗已在螢幕外，不需要太長延遲)
        self.after(100, self._enable_capture)
    
    def _enable_capture(self):
        """啟用截圖功能"""
        self.ready = True
        self.canvas.itemconfig(self.text_id, text="拖曳滑鼠選取要辨識的區域 (ESC取消)")
    
    def _on_press(self, event):
        """滑鼠按下"""
        if not self.ready:  # 尚未準備好，忽略點擊
            return
        # 使用螢幕絕對座標
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        # 轉換為canvas相對座標用於繪製
        canvas_x = event.x
        canvas_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            canvas_x, canvas_y, canvas_x, canvas_y,
            outline="red", width=3
        )
        self.canvas_start_x = canvas_x
        self.canvas_start_y = canvas_y
    
    def _on_drag(self, event):
        """滑鼠拖曳"""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.canvas_start_x, self.canvas_start_y,
                event.x, event.y
            )
    
    def _on_release(self, event):
        """滑鼠放開"""
        # 使用螢幕絕對座標
        end_x = event.x_root
        end_y = event.y_root
        
        # 計算實際螢幕座標
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        if x2 - x1 > 10 and y2 - y1 > 10:  # 最小10x10像素
            self.result = (x1, y1, x2, y2)
        
        self._finish()
    
    def _cancel(self):
        """取消截圖"""
        self.result = None
        self._finish()
    
    def _finish(self):
        """完成截圖"""
        self.destroy()
        if self.callback:
            self.callback(self.result)


class CoordinateSelector(tk.Toplevel):
    """座標捕捉工具（用於左鍵/右鍵點擊）"""
    
    def __init__(self, parent, button_type, callback):
        super().__init__(parent)
        
        self.callback = callback
        self.button_type = button_type  # "left" or "right"
        self.result = None
        self.ready = False
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="crosshair", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        button_name = "左鍵" if button_type == "left" else "右鍵"
        self.text_id = self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text="正在準備捕捉座標...",
            font=font_tuple(18, "bold"),
            fill="yellow"
        )
        
        # 綁定事件 - 根據按鈕類型綁定不同的滑鼠事件
        if button_type == "left":
            self.canvas.bind("<ButtonPress-1>", self._on_click)
        else:  # right
            self.canvas.bind("<ButtonPress-3>", self._on_click)
        
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.focus_force()
        
        # 延遲100ms後才允許捕捉
        self.after(100, self._enable_capture)
    
    def _enable_capture(self):
        """啟用座標捕捉功能"""
        self.ready = True
        button_name = "左鍵" if self.button_type == "left" else "右鍵"
        self.canvas.itemconfig(self.text_id, text=f"請點擊{button_name}以捕捉座標 (ESC取消)")
    
    def _on_click(self, event):
        """滑鼠點擊"""
        if not self.ready:
            return
        
        # 使用螢幕絕對座標
        x = event.x_root
        y = event.y_root
        
        self.result = (x, y)
        self._finish()
    
    def _cancel(self):
        """取消捕捉"""
        self.result = None
        self._finish()
    
    def _finish(self):
        """完成捕捉"""
        self.destroy()
        if self.callback:
            self.callback(self.result)


class RegionSelector(tk.Toplevel):
    """區域選擇工具（用於範圍辨識）"""
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.canvas_start_x = None
        self.canvas_start_y = None
        self.rect_id = None
        self.result = None
        self.ready = False
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        self.text_id = self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text="正在準備選擇範圍...",
            font=font_tuple(18, "bold"),
            fill="yellow"
        )
        
        # 綁定事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.focus_force()
        
        # 延遲100ms後才允許選擇
        self.after(100, self._enable_selection)
    
    def _enable_selection(self):
        """啟用選擇功能"""
        self.ready = True
        self.canvas.itemconfig(self.text_id, text="拖曳滑鼠選取辨識範圍 (ESC取消)")
    
    def _on_press(self, event):
        """滑鼠按下"""
        if not self.ready:
            return
        
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        canvas_x = event.x
        canvas_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            canvas_x, canvas_y, canvas_x, canvas_y,
            outline="blue", width=3
        )
        self.canvas_start_x = canvas_x
        self.canvas_start_y = canvas_y
    
    def _on_drag(self, event):
        """滑鼠拖曳"""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.canvas_start_x, self.canvas_start_y,
                event.x, event.y
            )
    
    def _on_release(self, event):
        """滑鼠放開"""
        if not self.ready or not self.rect_id:
            return
        
        end_x = event.x_root
        end_y = event.y_root
        
        # 確保 x1 < x2, y1 < y2
        x1, x2 = min(self.start_x, end_x), max(self.start_x, end_x)
        y1, y2 = min(self.start_y, end_y), max(self.start_y, end_y)
        
        # 檢查範圍是否足夠大
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self.canvas.itemconfig(self.text_id, text="範圍太小，請重新選擇")
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            return
        
        # 返回範圍座標 (x1, y1, x2, y2)
        self.result = (x1, y1, x2, y2)
        self._finish()
    
    def _cancel(self):
        """取消選擇"""
        self.result = None
        self._finish()
    
    def _finish(self):
        """完成選擇"""
        self.destroy()
        if self.callback:
            self.callback(self.result)


# ==================== 舊版彈出式模組管理器（已廢棄） ====================
# 現已改用內嵌式模組管理（在編輯器右側面板）
# 此類別保留供參考，但不再使用

# ==================== 舊版彈出式模組管理器（已移除） ====================
# 現已改用內嵌式模組管理（在編輯器右側面板）


# 測試用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # 測試用腳本路徑
    test_script = r"c:\Users\Lucien\Documents\GitHub\scripts\2025_1117_1540_20.json"
    
    editor = TextCommandEditor(root, test_script)
    root.mainloop()

