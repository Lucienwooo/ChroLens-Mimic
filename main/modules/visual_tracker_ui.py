import tkinter as tk
import ttkbootstrap as ttk
from tkinter import filedialog
import cv2
import numpy as np
import mss
import threading
import time
from pynput.keyboard import Controller, Key
from pynput.mouse import Controller as MouseController, Button
from modules.utils import set_window_icon

class VisualTrackerUI(tk.Toplevel):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.keyboard = Controller()
        self.mouse = MouseController()
        self.tracking = False
        self.target_img = None
        self.target_path = None
        
        self.title("智慧追蹤beta")
        
        # 讀取視窗位置與大小
        geom = self.main_app.user_config.get("visual_tracker_geometry", "900x700")
        if '+' in geom:
            # Extract just the position +x+y
            pos = geom[geom.find('+'):]
            self.geometry(pos)
        self.minsize(900, 700)
        
        # 綁定關閉事件以儲存視窗位置
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        set_window_icon(self)

        self.setup_ui()

    def on_close(self):
        # 停止追蹤如果還在運行
        self.tracking = False
        # 儲存視窗狀態
        self.main_app.user_config["visual_tracker_geometry"] = self.geometry()
        self.main_app.save_config()
        self.destroy()

    def setup_ui(self):
        # 使用 ttk 元件，不再強制指定白底
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        header = ttk.Label(header_frame, text="智慧追蹤beta", font=("Microsoft JhengHei", 16, "bold"))
        header.pack(anchor="w")
        
        desc = ttk.Label(header_frame, text="此介面整合了未來的 YOLO 視覺辨識、小地圖導航、符文解鎖與自動輔助等全自動化模組。\n目前提供基礎介面框架與傳統影像追蹤功能做為核心雛形。", 
                       font=("Microsoft JhengHei", 10), justify="left")
        desc.pack(anchor="w", pady=(5, 0))
        
        # Notebook 分頁
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ===== 分頁 1: 基本設定 =====
        self.tab_basic = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_basic, text="基本設定與追蹤")
        self.setup_tab_basic()
        
        # ===== 分頁 2: 移動與戰鬥 =====
        self.tab_combat = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_combat, text="移動與戰鬥")
        self.setup_tab_combat()
        
        # ===== 分頁 3: 狀態與輔助 =====
        self.tab_buffs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_buffs, text="狀態與輔助")
        self.setup_tab_buffs()
        
        # ===== 分頁 4: 進階視覺 =====
        self.tab_adv = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_adv, text="進階視覺導航")
        self.setup_tab_advanced()

        # Control Buttons
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(pady=10)
        self.start_btn = ttk.Button(ctrl_frame, text="開始自動化", bootstyle="success", command=self.toggle_tracking, width=20)
        self.start_btn.pack(pady=5)
        
        # Log View
        self.log_text = tk.Text(self, height=8, font=("Consolas", 10))
        self.log_text.pack(fill="both", padx=20, pady=(0, 20))
        self.log("智慧追蹤模組已載入。介面已全面升級。")

    def setup_tab_basic(self):
        # Mode selection
        mode_frame = ttk.LabelFrame(self.tab_basic, text="偵測引擎")
        mode_frame.pack(fill="x", pady=5)
        self.engine_var = tk.StringVar(value="template")
        ttk.Radiobutton(mode_frame, text="傳統圖片比對 (Template Matching)", variable=self.engine_var, value="template").pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="YOLO AI 模型偵測 (需載入 .pt)", variable=self.engine_var, value="yolo").pack(side="left", padx=10)
        
        # Target Selection
        target_frame = ttk.LabelFrame(self.tab_basic, text="追蹤目標")
        target_frame.pack(fill="x", pady=5)
        ttk.Label(target_frame, text="目標檔案:").pack(side="left")
        self.img_path_var = tk.StringVar()
        ttk.Entry(target_frame, textvariable=self.img_path_var, width=20, state="readonly").pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(target_frame, text="瀏覽...", bootstyle="secondary", command=self.select_image).pack(side="left")
        ttk.Button(target_frame, text="資料夾", bootstyle="info", command=self.open_image_folder).pack(side="left", padx=(5,0))
        
        # Threshold
        thresh_frame = ttk.LabelFrame(self.tab_basic, text="執行參數")
        thresh_frame.pack(fill="x", pady=5)
        ttk.Label(thresh_frame, text="辨識相似度/信心度:").pack(side="left")
        self.thresh_var = tk.DoubleVar(value=0.8)
        ttk.Scale(thresh_frame, from_=0.5, to=0.99, orient="horizontal", variable=self.thresh_var).pack(side="left", padx=10)
        ttk.Label(thresh_frame, text="循環間隔(秒):").pack(side="left", padx=(20,0))
        self.interval = tk.DoubleVar(value=0.5)
        ttk.Entry(thresh_frame, textvariable=self.interval, width=10).pack(side="left", padx=5)


        # === [防護機制] 失焦防護策略 ===
        protect_frame = ttk.LabelFrame(self.tab_basic, text="失焦防護策略 (Background Strategy)")
        protect_frame.pack(fill="x", pady=5)
        
        self.protect_var = tk.StringVar(value=self.main_app.user_config.get("bg_protect_strategy", "skip"))
        
        protect_cb = ttk.Combobox(protect_frame, textvariable=self.protect_var, values=["skip", "pause", "force"], state="readonly", width=15)
        protect_cb.pack(side="left", padx=10, pady=5)
        
        # 綁定變更事件，儲存至設定檔
        def on_protect_change(event):
            self.main_app.user_config["bg_protect_strategy"] = self.protect_var.get()
            self.main_app.save_config()
            self.log(f"已切換防護策略: {self.protect_var.get()}")
            
        protect_cb.bind("<<ComboboxSelected>>", on_protect_change)
        
        ttk.Label(protect_frame, text="skip: 安全略過 | pause: 自動暫停等待 | force: 強制搶奪焦點").pack(side="left", padx=5)
        # ==================================
    def setup_tab_combat(self):
        keys_frame = ttk.LabelFrame(self.tab_combat, text="操作按鍵綁定")
        keys_frame.pack(fill="both", expand=True, pady=5)
        
        # Grid layout
        ttk.Label(keys_frame, text="向左移動:").grid(row=0, column=0, pady=10, padx=5, sticky="e")
        self.key_left = tk.StringVar(value="a")
        ttk.Entry(keys_frame, textvariable=self.key_left, width=15).grid(row=0, column=1, pady=10)
        
        ttk.Label(keys_frame, text="向右移動:").grid(row=0, column=2, pady=10, padx=(30,5), sticky="e")
        self.key_right = tk.StringVar(value="d")
        ttk.Entry(keys_frame, textvariable=self.key_right, width=15).grid(row=0, column=3, pady=10)
        
        ttk.Label(keys_frame, text="向上移動:").grid(row=1, column=0, pady=10, padx=5, sticky="e")
        self.key_up = tk.StringVar(value="w")
        ttk.Entry(keys_frame, textvariable=self.key_up, width=15).grid(row=1, column=1, pady=10)
        
        ttk.Label(keys_frame, text="向下移動:").grid(row=1, column=2, pady=10, padx=(30,5), sticky="e")
        self.key_down = tk.StringVar(value="s")
        ttk.Entry(keys_frame, textvariable=self.key_down, width=15).grid(row=1, column=3, pady=10)
        
        ttk.Separator(keys_frame, orient="horizontal").grid(row=2, column=0, columnspan=4, pady=15, sticky="ew")
        
        ttk.Label(keys_frame, text="主要攻擊:").grid(row=3, column=0, pady=10, padx=5, sticky="e")
        self.key_attack = tk.StringVar(value="ctrl")
        ttk.Entry(keys_frame, textvariable=self.key_attack, width=15).grid(row=3, column=1, pady=10)        
        self.mouse_strike_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(keys_frame, text="啟用滑鼠精準點擊 (打靶/網頁模式)", variable=self.mouse_strike_var).grid(row=4, column=0, columnspan=4, pady=10)
        
        ttk.Label(keys_frame, text="跳躍按鍵:").grid(row=3, column=2, pady=10, padx=(30,5), sticky="e")
        self.key_jump = tk.StringVar(value="alt")
        ttk.Entry(keys_frame, textvariable=self.key_jump, width=15).grid(row=3, column=3, pady=10)

    def setup_tab_buffs(self):
        hp_frame = ttk.LabelFrame(self.tab_buffs, text="自動喝水與防護 (概念展示)")
        hp_frame.pack(fill="x", pady=5)
        
        self.enable_hp = tk.BooleanVar(value=False)
        ttk.Checkbutton(hp_frame, text="啟用自動喝水", variable=self.enable_hp).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ttk.Label(hp_frame, text="HP 低於 (%) 觸發:").grid(row=1, column=0, sticky="e", padx=5)
        ttk.Entry(hp_frame, width=10).grid(row=1, column=1, pady=5)
        ttk.Label(hp_frame, text="按鍵:").grid(row=1, column=2, sticky="e", padx=(20,5))
        ttk.Entry(hp_frame, width=10).grid(row=1, column=3, pady=5)
        
        ttk.Label(hp_frame, text="MP 低於 (%) 觸發:").grid(row=2, column=0, sticky="e", padx=5)
        ttk.Entry(hp_frame, width=10).grid(row=2, column=1, pady=5)
        ttk.Label(hp_frame, text="按鍵:").grid(row=2, column=2, sticky="e", padx=(20,5))
        ttk.Entry(hp_frame, width=10).grid(row=2, column=3, pady=5)
        
        buff_frame = ttk.LabelFrame(self.tab_buffs, text="定時 Buff (概念展示)")
        buff_frame.pack(fill="x", pady=15)
        
        ttk.Label(buff_frame, text="Buff 1 按鍵:").grid(row=0, column=0, sticky="e", padx=5)
        ttk.Entry(buff_frame, width=10).grid(row=0, column=1, pady=5)
        ttk.Label(buff_frame, text="間隔(秒):").grid(row=0, column=2, sticky="e", padx=(20,5))
        ttk.Entry(buff_frame, width=10).grid(row=0, column=3, pady=5)

    def setup_tab_advanced(self):
        nav_frame = ttk.LabelFrame(self.tab_adv, text="進階小地圖導航 (概念展示)")
        nav_frame.pack(fill="x", pady=5)
        
        self.enable_minimap = tk.BooleanVar(value=False)
        ttk.Checkbutton(nav_frame, text="啟用小地圖尋路引擎", variable=self.enable_minimap).grid(row=0, column=0, sticky="w", pady=(0, 10))
        ttk.Button(nav_frame, text="框選小地圖區域", bootstyle="outline-primary").grid(row=0, column=1, sticky="w", padx=20, pady=(0, 10))
        
        rune_frame = ttk.LabelFrame(self.tab_adv, text="自動解符文與測謊 (概念展示)")
        rune_frame.pack(fill="x", pady=15)
        
        self.enable_rune = tk.BooleanVar(value=False)
        ttk.Checkbutton(rune_frame, text="啟用自動解符文 (YOLO 方向鍵辨識)", variable=self.enable_rune).grid(row=0, column=0, sticky="w", pady=5)
        
        self.enable_lie = tk.BooleanVar(value=False)
        ttk.Checkbutton(rune_frame, text="啟用測謊/異常中斷 (偵測紫框或特定圖示)", variable=self.enable_lie).grid(row=1, column=0, sticky="w", pady=5)

    def log(self, msg):
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")

    def open_image_folder(self):
        import os
        img_dir = os.path.join(self.main_app.script_dir, 'images')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir, exist_ok=True)
        try:
            os.startfile(img_dir)
        except Exception as e:
            pass

    def select_image(self):
        path = filedialog.askopenfilename(title="選擇目標檔案", filetypes=[("Image/Model Files", "*.png *.jpg *.jpeg *.bmp *.pt")])
        if path:
            self.img_path_var.set(path)
            self.target_path = path
            
            if path.endswith('.pt'):
                self.engine_var.set('yolo')
                self.log(f"已選取 YOLO 模型: {path}")
            else:
                self.engine_var.set('template')
                img_data = np.fromfile(path, dtype=np.uint8)
                img_bgra = cv2.imdecode(img_data, cv2.IMREAD_UNCHANGED)
                if img_bgra is not None:
                    if len(img_bgra.shape) == 3 and img_bgra.shape[2] == 4:
                        # Has Alpha channel
                        self.target_mask = img_bgra[:, :, 3]
                        self.target_img = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2GRAY)
                    else:
                        self.target_mask = None
                        if len(img_bgra.shape) == 3:
                            self.target_img = cv2.cvtColor(img_bgra, cv2.COLOR_BGR2GRAY)
                        else:
                            self.target_img = img_bgra
                self.log(f"已載入目標圖片: {path}")

    def toggle_tracking(self):
        if not self.tracking:
            if self.engine_var.get() == 'template' and self.target_img is None:
                self.log("錯誤: 請先選擇目標圖片!")
                return
            elif self.engine_var.get() == 'yolo' and (self.target_path is None or not self.target_path.endswith('.pt')):
                self.log("錯誤: 若使用 YOLO，請選擇 .pt 模型檔!")
                return
                
            self.tracking = True
            self.start_btn.config(text="停止自動化", bootstyle="danger")
            self.log("--- 開始自動化執行 ---")
            threading.Thread(target=self.tracking_loop, daemon=True).start()
        else:
            self.tracking = False
            self.start_btn.config(text="開始自動化", bootstyle="success")
            self.log("--- 自動化已停止 ---")

    def map_key(self, key_str):
        key_str = key_str.lower()
        mapping = {
            "ctrl": Key.ctrl_l,
            "shift": Key.shift,
            "alt": Key.alt,
            "enter": Key.enter,
            "space": Key.space,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right
        }
        return mapping.get(key_str, key_str)

    def press_key(self, key_str):
        if not key_str:
            return
        try:
            k = self.map_key(key_str)
            self.keyboard.press(k)
            time.sleep(0.05)
            self.keyboard.release(k)
        except Exception as e:
            self.log(f"按鍵錯誤: {e}")

    def tracking_loop(self):
        with mss.mss() as sct:
            while self.tracking:
                start_time = time.time()
                
                # capture screen
                monitor = sct.monitors[0]
                img = np.array(sct.grab(monitor))
                gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                
                # match template
                if hasattr(self, 'target_mask') and self.target_mask is not None:
                    res = cv2.matchTemplate(gray, self.target_img, cv2.TM_CCORR_NORMED, mask=self.target_mask)
                else:
                    res = cv2.matchTemplate(gray, self.target_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= self.thresh_var.get():
                    h, w = self.target_img.shape
                    # Target center
                    tx = max_loc[0] + w // 2
                    ty = max_loc[1] + h // 2
                    
                    # Draw Highlight Box
                    abs_x = monitor["left"] + max_loc[0]
                    abs_y = monitor["top"] + max_loc[1]
                    if hasattr(self.main_app, 'highlight'):
                        self.main_app.highlight(abs_x, abs_y, w, h, duration=0.1)

                    # Screen center
                    cx = monitor["width"] // 2
                    cy = monitor["height"] // 2
                    
                    # 簡易邏輯: 判斷目標在畫面中心的哪一側 (容許誤差 100 px)
                    
                    if hasattr(self, 'mouse_strike_var') and self.mouse_strike_var.get():
                        abs_tx = monitor["left"] + tx
                        abs_ty = monitor["top"] + ty
                        self.mouse.position = (abs_tx, abs_ty)
                        time.sleep(0.01)
                        self.mouse.click(Button.left)
                        action_msg = "滑鼠已精準點擊!"
                        self.log(f"{action_msg} (信心度: {max_val:.2f})")
                        # 避免過快連點
                        time.sleep(0.05)
                        continue
                    
                    # 鍵盤模擬模式
                    deadzone = 100
                    dx = tx - cx
                    dy = ty - cy
                    
                    action_msg = "找到目標!"
                    moved = False
                    
                    if dx > deadzone:
                        self.press_key(self.key_right.get())
                        action_msg += " 向右"
                        moved = True
                    elif dx < -deadzone:
                        self.press_key(self.key_left.get())
                        action_msg += " 向左"
                        moved = True
                        
                    if dy > deadzone:
                        self.press_key(self.key_down.get())
                        action_msg += " 向下"
                        moved = True
                    elif dy < -deadzone:
                        self.press_key(self.key_up.get())
                        action_msg += " 向上"
                        moved = True
                        
                    # 如果都在 deadzone 內 (代表夠靠近了)，則攻擊
                    if not moved:
                        self.press_key(self.key_attack.get())
                        action_msg += " 攻擊!"
                        
                    self.log(f"{action_msg} (信心度: {max_val:.2f})")
                else:
                    self.log("尋找目標中...")
                    
                # sleep
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval.get() - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
