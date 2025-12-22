# -*- coding: utf-8 -*-
"""
ChroLens 編輯器截圖與座標捕捉模組
提供螢幕截圖、座標選取和範圍選擇功能

v2.7.3 - 從 text_script_editor.py 拆分
"""

import tkinter as tk
from PIL import Image, ImageGrab

# 引入工具函式
from editor_utils import font_tuple

# 嘗試引入更快的螢幕截圖庫
try:
    import mss
    import numpy as np
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False


class ScreenCaptureSelector(tk.Toplevel):
    """螢幕截圖選取工具
    
    提供全螢幕半透明遮罩，讓使用者拖曳選取要截圖的區域。
    支援 ESC 取消操作。
    ✅ v2.7.5: 支援多螢幕環境
    """
    
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
        
        # ✅ 獲取虛擬桌面區域（包含所有螢幕）
        if MSS_AVAILABLE:
            try:
                with mss.mss() as sct:
                    # monitors[0] 是所有螢幕的合併區域
                    all_monitors = sct.monitors[0]
                    self.virtual_left = all_monitors["left"]
                    self.virtual_top = all_monitors["top"]
                    self.virtual_width = all_monitors["width"]
                    self.virtual_height = all_monitors["height"]
            except:
                # 回退到主螢幕
                self.virtual_left = 0
                self.virtual_top = 0
                self.virtual_width = self.winfo_screenwidth()
                self.virtual_height = self.winfo_screenheight()
        else:
            # 使用 Windows API 獲取虛擬桌面
            import ctypes
            user32 = ctypes.windll.user32
            self.virtual_left = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
            self.virtual_top = user32.GetSystemMetrics(77)    # SM_YVIRTUALSCREEN
            self.virtual_width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            self.virtual_height = user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
        
        # ✅ 覆蓋所有螢幕（取代 -fullscreen）
        self.overrideredirect(True)  # 無邊框
        self.geometry(f"{self.virtual_width}x{self.virtual_height}+{self.virtual_left}+{self.virtual_top}")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字（置中於視窗）
        self.text_id = self.canvas.create_text(
            self.virtual_width // 2,
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
        
        # 延遲100ms後才允許截圖
        self.after(100, self._enable_capture)
    
    def _enable_capture(self):
        """啟用截圖功能"""
        self.ready = True
        self.canvas.itemconfig(self.text_id, text="拖曳滑鼠選取要辨識的區域 (ESC取消)")
    
    def _on_press(self, event):
        """滑鼠按下"""
        if not self.ready:
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
    """座標捕捉工具（用於左鍵/右鍵點擊）
    
    提供全螢幕半透明遮罩，讓使用者點擊以捕捉座標。
    支援左鍵和右鍵兩種模式。
    ✅ v2.7.5: 支援多螢幕環境
    """
    
    def __init__(self, parent, button_type, callback):
        super().__init__(parent)
        
        self.callback = callback
        self.button_type = button_type  # "left" or "right"
        self.result = None
        self.ready = False
        
        # ✅ 獲取虛擬桌面區域（包含所有螢幕）
        if MSS_AVAILABLE:
            try:
                with mss.mss() as sct:
                    all_monitors = sct.monitors[0]
                    self.virtual_left = all_monitors["left"]
                    self.virtual_top = all_monitors["top"]
                    self.virtual_width = all_monitors["width"]
                    self.virtual_height = all_monitors["height"]
            except:
                self.virtual_left = 0
                self.virtual_top = 0
                self.virtual_width = self.winfo_screenwidth()
                self.virtual_height = self.winfo_screenheight()
        else:
            import ctypes
            user32 = ctypes.windll.user32
            self.virtual_left = user32.GetSystemMetrics(76)
            self.virtual_top = user32.GetSystemMetrics(77)
            self.virtual_width = user32.GetSystemMetrics(78)
            self.virtual_height = user32.GetSystemMetrics(79)
        
        # ✅ 覆蓋所有螢幕
        self.overrideredirect(True)
        self.geometry(f"{self.virtual_width}x{self.virtual_height}+{self.virtual_left}+{self.virtual_top}")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="crosshair", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        button_name = "左鍵" if button_type == "left" else "右鍵"
        self.text_id = self.canvas.create_text(
            self.virtual_width // 2,
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
    """區域選擇工具（用於範圍辨識）
    
    提供全螢幕半透明遮罩，讓使用者拖曳選取辨識範圍。
    返回範圍座標 (x1, y1, x2, y2)。
    ✅ v2.7.5: 支援多螢幕環境
    """
    
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
        
        # ✅ 獲取虛擬桌面區域（包含所有螢幕）
        if MSS_AVAILABLE:
            try:
                with mss.mss() as sct:
                    all_monitors = sct.monitors[0]
                    self.virtual_left = all_monitors["left"]
                    self.virtual_top = all_monitors["top"]
                    self.virtual_width = all_monitors["width"]
                    self.virtual_height = all_monitors["height"]
            except:
                self.virtual_left = 0
                self.virtual_top = 0
                self.virtual_width = self.winfo_screenwidth()
                self.virtual_height = self.winfo_screenheight()
        else:
            import ctypes
            user32 = ctypes.windll.user32
            self.virtual_left = user32.GetSystemMetrics(76)
            self.virtual_top = user32.GetSystemMetrics(77)
            self.virtual_width = user32.GetSystemMetrics(78)
            self.virtual_height = user32.GetSystemMetrics(79)
        
        # ✅ 覆蓋所有螢幕
        self.overrideredirect(True)
        self.geometry(f"{self.virtual_width}x{self.virtual_height}+{self.virtual_left}+{self.virtual_top}")
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        self.text_id = self.canvas.create_text(
            self.virtual_width // 2,
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


class CaptureMixin:
    """截圖與座標捕捉 Mixin 類別
    
    為 TextCommandEditor 提供截圖和座標捕捉功能。
    
    需要主類別提供:
    - self.text_editor: Text widget
    - self.images_dir: 圖片儲存目錄
    - self.withdraw() / self.deiconify(): 視窗隱藏/顯示方法
    """
    
    def _hide_windows_for_capture(self):
        """隱藏編輯器視窗以進行截圖"""
        # 儲存原始狀態
        self.editor_geometry = self.geometry()
        if self.parent:
            try:
                self.parent_geometry = self.parent.geometry()
            except:
                self.parent_geometry = None
        else:
            self.parent_geometry = None
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 步驟1: 縮小至 1x1 像素
        self.geometry("1x1")
        if self.parent and self.parent_geometry:
            try:
                self.parent.geometry("1x1")
            except:
                pass
        self.update_idletasks()
        
        # 步驟2: 移到螢幕外
        self.geometry(f"1x1+{screen_width + 100}+{screen_height + 100}")
        if self.parent and self.parent_geometry:
            try:
                self.parent.geometry(f"1x1+{screen_width + 200}+{screen_height + 200}")
            except:
                pass
        self.update_idletasks()
        
        # 步驟3: 隱藏視窗
        self.withdraw()
        if self.parent:
            try:
                self.parent.withdraw()
            except:
                pass
        self.update_idletasks()
    
    def _restore_windows(self):
        """恢復視窗顯示"""
        # 恢復顯示
        self.deiconify()
        if self.parent:
            try:
                self.parent.deiconify()
            except:
                pass
        
        # 恢復大小和位置
        if hasattr(self, 'editor_geometry') and self.editor_geometry:
            self.geometry(self.editor_geometry)
        if self.parent and hasattr(self, 'parent_geometry') and self.parent_geometry:
            try:
                self.parent.geometry(self.parent_geometry)
            except:
                pass
        
        self.update_idletasks()
        self.lift()
        self.focus_force()
    
    def _capture_and_recognize(self):
        """截圖並儲存，插入辨識指令"""
        self._hide_windows_for_capture()
        self.after(600, self._do_capture)
    
    def _do_capture(self):
        """執行截圖"""
        selector = ScreenCaptureSelector(self, self._on_capture_complete)
    
    def _on_capture_complete(self, region):
        """截圖完成回調"""
        self._restore_windows()
        
        if region:
            x1, y1, x2, y2 = region
            try:
                # 截取螢幕區域
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                self._show_name_and_preview_dialog(screenshot)
            except Exception as e:
                print(f"截圖失敗: {e}")
    
    def _capture_left_click_coordinate(self):
        """捕捉左鍵點擊座標"""
        self._capture_click_coordinate("left")
    
    def _capture_right_click_coordinate(self):
        """捕捉右鍵點擊座標"""
        self._capture_click_coordinate("right")
    
    def _capture_click_coordinate(self, button_type):
        """捕捉滑鼠點擊座標的通用函數"""
        self._hide_windows_for_capture()
        self.after(600, lambda: self._do_coordinate_capture(button_type))
    
    def _do_coordinate_capture(self, button_type):
        """執行座標捕捉"""
        selector = CoordinateSelector(self, button_type, 
                                      lambda coord: self._on_coordinate_captured(coord, button_type))
    
    def _on_coordinate_captured(self, coordinate, button_type):
        """座標捕捉完成回調"""
        self._restore_windows()
        
        if coordinate:
            x, y = coordinate
            if button_type == "left":
                command = f">左鍵點擊({x},{y}), 延遲50ms, T=0s000"
            else:
                command = f">右鍵點擊({x},{y}), 延遲50ms, T=0s000"
            
            # 插入指令
            self.text_editor.insert(tk.INSERT, command + "\n")
    
    def _capture_region_for_recognition(self):
        """選擇範圍用於圖片辨識"""
        self._hide_windows_for_capture()
        self.after(600, self._do_region_selection)
    
    def _do_region_selection(self):
        """執行範圍選擇"""
        selector = RegionSelector(self, self._on_region_selected)
    
    def _on_region_selected(self, region):
        """範圍選擇完成回調"""
        self._restore_windows()
        
        if region:
            x1, y1, x2, y2 = region
            # 插入帶範圍的辨識指令
            command = f">辨識>pic01, 範圍({x1},{y1},{x2},{y2}), T=0s000"
            self.text_editor.insert(tk.INSERT, command + "\n")
