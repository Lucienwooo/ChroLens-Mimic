import tkinter as tk
from tkinter import ttk, simpledialog
from PIL import Image, ImageGrab, ImageTk
import json
import sys
import os

class CoordinateSelector(tk.Toplevel):
    """座標捕捉工具（用於左鍵/右鍵點擊/拖曳）"""
    
    def __init__(self, parent, button_type, callback):
        super().__init__(parent)
        set_window_icon(self)
        
        self.callback = callback
        self.button_type = button_type  # "left", "right" or "drag"
        self.result = None
        self.ready = False
        
        self.coords = []          # [(x_root, y_root), ...]
        self.canvas_points = []   # [(x, y), ...]
        self.click_times = []     # [time.time(), ...]
        self.drag_line_id = None
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.45)
        
        # 1. 畫布 (全螢幕，佔滿整個視窗)
        self.canvas = tk.Canvas(self, cursor="crosshair", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        if button_type == "drag":
            prompt_text = "請點擊左鍵設定起點，點擊右鍵設定中繼點/終點，最後點擊「儲存路徑」按鈕或按 Enter 儲存"
        else:
            button_name = "左鍵" if button_type == "left" else "右鍵"
            prompt_text = f"請在畫面上點擊{button_name}以捕捉座標點，或點擊右側按鈕取消"
            
        # 2. 說明文字 (使用 24 大小、置中黃色)
        self.text_id = self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            60,
            text=prompt_text,
            font=font_tuple(24, "bold"),
            fill="yellow",
            justify="center",
            width=self.winfo_screenwidth() - 600
        )
        
        # 3. 建立並嵌入實體按鈕
        # 取消按鈕
        self.cancel_btn = tk.Button(
            self.canvas, 
            text="取消 (ESC)", 
            command=self._cancel, 
            bg="#D32F2F", 
            fg="white", 
            activebackground="#B71C1C",
            activeforeground="white",
            font=font_tuple(11, "bold"),
            relief="flat",
            padx=15,
            pady=5
        )
        self.canvas.create_window(
            self.winfo_screenwidth() - 100, 
            60, 
            window=self.cancel_btn,
            anchor="center"
        )
        
        if button_type == "drag":
            # 儲存按鈕
            self.save_btn = tk.Button(
                self.canvas, 
                text="儲存路徑 (Enter)", 
                command=self._save_path, 
                bg="#388E3C", 
                fg="white", 
                activebackground="#1B5E20",
                activeforeground="white",
                font=font_tuple(11, "bold"),
                relief="flat",
                padx=15,
                pady=5
            )
            self.canvas.create_window(
                self.winfo_screenwidth() - 250, 
                60, 
                window=self.save_btn,
                anchor="center"
            )
            
        # 綁定事件
        if button_type == "left":
            self.canvas.bind("<ButtonPress-1>", self._on_click)
        elif button_type == "right":
            self.canvas.bind("<ButtonPress-3>", self._on_click)
        elif button_type == "drag":
            self.canvas.bind("<ButtonPress-1>", self._on_drag_left_click)
            self.canvas.bind("<ButtonPress-3>", self._on_drag_right_click)
            
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind("<Return>", lambda e: self._save_path())
        self.bind("<KP_Enter>", lambda e: self._save_path())
        
        self.focus_force()
        self.after(100, self._enable_capture)
    
    def _enable_capture(self):
        """啟用座標捕捉功能"""
        self.ready = True

    def _on_click(self, event):
        """左鍵/右鍵單點捕捉"""
        if not self.ready:
            return
        
        # 使用螢幕絕對座標
        x = event.x_root
        y = event.y_root
        
        # 繪製綠色圈圈標記
        r = 10
        self.canvas.create_oval(
            event.x - r, event.y - r, event.x + r, event.y + r, 
            fill="green", outline="white", width=2
        )
        
        self.result = (x, y)
        self.after(300, self._finish)

    def _on_drag_left_click(self, event):
        if not self.ready:
            return
        
        if len(self.coords) == 0:
            # 記錄起點
            self.coords.append((event.x_root, event.y_root))
            self.canvas_points.append((event.x, event.y))
            self.click_times.append(time.time())
            
            # 繪製起點紅色圈圈標記
            r = 10
            self.canvas.create_oval(
                event.x - r, event.y - r, event.x + r, event.y + r, 
                fill="red", outline="white", width=2, tags="anchor_marker"
            )
            
            # 綁定滑鼠移動
            self.canvas.bind("<Motion>", self._on_drag_mouse_move)
            self.canvas.itemconfig(
                self.text_id,
                text="起點已設定！請將滑鼠移到下一點並點擊右鍵以新增中繼點/終點"
            )
        else:
            # 再次點擊左鍵來取消最後生成的紅線顯示
            if self.drag_line_id:
                self.canvas.delete(self.drag_line_id)
                self.drag_line_id = None
            self.canvas.unbind("<Motion>")
            self.canvas.itemconfig(
                self.text_id,
                text="跟隨紅線已取消。點擊「儲存路徑」按鈕完成，或點擊右鍵繼續新增中繼點"
            )

    def _on_drag_mouse_move(self, event):
        if len(self.coords) == 0:
            return
        
        # 畫一條跟隨滑鼠的紅線
        last_x, last_y = self.canvas_points[-1]
        
        if self.drag_line_id:
            self.canvas.delete(self.drag_line_id)
        
        # 使用實心紅線，寬度 4
        self.drag_line_id = self.canvas.create_line(
            last_x, last_y, event.x, event.y, 
            fill="red", width=4
        )

    def _on_drag_right_click(self, event):
        if not self.ready or len(self.coords) == 0:
            return
            
        # 如果滑鼠移動事件被取消了（例如之前點了左鍵），點右鍵時要重新綁定
        self.canvas.bind("<Motion>", self._on_drag_mouse_move)
        
        # 記錄中繼點/終點
        self.coords.append((event.x_root, event.y_root))
        self.canvas_points.append((event.x, event.y))
        self.click_times.append(time.time())
        
        # 繪製紅色圈圈標記
        r = 10
        self.canvas.create_oval(
            event.x - r, event.y - r, event.x + r, event.y + r, 
            fill="red", outline="white", width=2, tags="anchor_marker"
        )
        
        # 繪製與前一個點的實心紅線，寬度 4
        prev_x, prev_y = self.canvas_points[-2]
        self.canvas.create_line(
            prev_x, prev_y, event.x, event.y, 
            fill="red", width=4, tags="path_line"
        )
        
        # 刪除並重置臨時跟隨紅線
        if self.drag_line_id:
            self.canvas.delete(self.drag_line_id)
            self.drag_line_id = None
            
        # 觸發一次 mouse move 來產生下一段跟隨紅線
        self._on_drag_mouse_move(event)
        
        self.canvas.itemconfig(
            self.text_id,
            text=f"已設定 {len(self.coords)-1} 個段落。點擊「儲存路徑」完成，或點擊右鍵繼續新增中繼點 (ESC取消)"
        )

    def _save_path(self):
        if len(self.coords) < 2:
            return
            
        # 計算每段時間差
        durations = []
        for idx in range(1, len(self.click_times)):
            durations.append(self.click_times[idx] - self.click_times[idx - 1])
            
        self.result = {
            "points": self.coords,
            "durations": durations
        }
        
        self.canvas.itemconfig(
            self.text_id,
            text=f"路徑儲存成功！共 {len(self.coords)} 個點，正在返回編輯器..."
        )
        
        self.after(500, self._finish)

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
        set_window_icon(self)
        
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

class ScreenCaptureSelector(tk.Toplevel):
    """螢幕截圖選取工具"""
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        set_window_icon(self)
        
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


class RelativeMoveDistanceTool(tk.Toplevel):
    """相對移動距離測量工具 (覆蓋全螢幕的透明 UI)"""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.parent = parent
        self.callback = callback
        
        self.title("相對移動距離測量")
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.configure(cursor="crosshair")
        
        # 截取螢幕並調暗
        self.screenshot = None
        try:
            if MSS_AVAILABLE:
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            else:
                img = ImageGrab.grab()
                
            dim_layer = Image.new('RGBA', img.size, (0, 0, 0, 128))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, dim_layer)
            self.screenshot = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"截圖失敗: {e}")
            
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        if self.screenshot:
            self.canvas.create_image(0, 0, image=self.screenshot, anchor="nw")
            
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        
        self.shift_pressed = False
        
        self.bind("<Button-1>", self.on_click)
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<KeyPress-Shift_L>", self.on_shift_press)
        self.bind("<KeyRelease-Shift_L>", self.on_shift_release)
        self.bind("<KeyPress-Shift_R>", self.on_shift_press)
        self.bind("<KeyRelease-Shift_R>", self.on_shift_release)
        self.bind("<Return>", self.on_enter)
        self.bind("<KP_Enter>", self.on_enter)
        self.bind("<Escape>", self.on_escape)
        
        self.canvas.bind("<Return>", self.on_enter)
        self.canvas.bind("<KP_Enter>", self.on_enter)
        
        self.update_instruction_text("請點擊左鍵設定起點 (按 Esc 取消)")
        
        self.focus_force()

    def update_instruction_text(self, text):
        self.canvas.delete("instruction")
        self.canvas.delete("instruction_shadow")
        w = self.winfo_screenwidth()
        
        # 陰影
        self.canvas.create_text(
            w // 2 + 2, 52,
            text=text,
            font=("Microsoft JhengHei", 24, "bold"),
            fill="black",
            tags="instruction_shadow"
        )
        # 主文字
        self.canvas.create_text(
            w // 2, 50,
            text=text,
            font=("Microsoft JhengHei", 24, "bold"),
            fill="white",
            tags="instruction"
        )
        
    def on_shift_press(self, event):
        self.shift_pressed = True
        self._update_line(event.x, event.y)
        
    def on_shift_release(self, event):
        self.shift_pressed = False
        self._update_line(event.x, event.y)
        
    def _apply_shift_constraint(self, cx, cy):
        if self.start_x is None or self.start_y is None:
            return cx, cy
            
        dx = cx - self.start_x
        dy = cy - self.start_y
        
        if abs(dx) > 2 * abs(dy):
            return cx, self.start_y
        elif abs(dy) > 2 * abs(dx):
            return self.start_x, cy
        else:
            import math
            dist = max(abs(dx), abs(dy))
            new_dx = math.copysign(dist, dx) if dx != 0 else dist
            new_dy = math.copysign(dist, dy) if dy != 0 else dist
            return self.start_x + int(new_dx), self.start_y + int(new_dy)

    def _update_line(self, x, y):
        if self.start_x is not None and self.end_x is None:
            cx, cy = x, y
            if self.shift_pressed:
                cx, cy = self._apply_shift_constraint(cx, cy)
                
            self.canvas.delete("temp_line")
            self.canvas.create_line(
                self.start_x, self.start_y, cx, cy,
                fill="#FF5722", width=3, arrow=tk.LAST, tags="temp_line"
            )
            
            self.canvas.delete("distance_text")
            self.canvas.delete("distance_text_shadow")
            
            dx = cx - self.start_x
            dy = cy - self.start_y
            dist_text = f"dx: {dx}, dy: {dy}"
            
            self.canvas.create_text(
                cx + 12, cy + 12,
                text=dist_text,
                font=("Consolas", 14, "bold"),
                fill="black",
                tags="distance_text_shadow",
                anchor="nw"
            )
            self.canvas.create_text(
                cx + 10, cy + 10,
                text=dist_text,
                font=("Consolas", 14, "bold"),
                fill="#FFEB3B",
                tags="distance_text",
                anchor="nw"
            )

    def on_mouse_move(self, event):
        self._update_line(event.x, event.y)
        
    def on_click(self, event):
        if self.start_x is None:
            self.start_x = event.x
            self.start_y = event.y
            self.canvas.create_oval(
                self.start_x - 6, self.start_y - 6,
                self.start_x + 6, self.start_y + 6,
                fill="#FF5722", outline="white", width=2, tags="start_dot"
            )
            self.update_instruction_text("請點擊左鍵設定終點 (按住 Shift 鎖定直線/45度角)")
        elif self.end_x is None:
            cx, cy = event.x, event.y
            if self.shift_pressed:
                cx, cy = self._apply_shift_constraint(cx, cy)
            
            self.end_x = cx
            self.end_y = cy
            
            self._update_line(cx, cy)
            
            self.canvas.create_oval(
                self.end_x - 6, self.end_y - 6,
                self.end_x + 6, self.end_y + 6,
                fill="#4CAF50", outline="white", width=2, tags="end_dot"
            )
            self.update_instruction_text("按下 Enter 鍵儲存路徑，或按 Esc 取消")

    def on_enter(self, event):
        if self.start_x is not None and self.end_x is not None:
            dx = self.end_x - self.start_x
            dy = self.end_y - self.start_y
            self.callback(dx, dy)
            self.destroy()

    def on_escape(self, event):
        self.destroy()

