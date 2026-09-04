import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import win32gui
import win32con
import win32api
import win32ui
import win32process
import sys
import os
import psutil
from PIL import Image, ImageTk
import ctypes

try:
    from utils.utils import get_icon_path, set_window_icon
except ImportError:
    def get_icon_path(): return "umi_奶茶.ico"
    def set_window_icon(w):
        try: w.iconbitmap(get_icon_path())
        except: pass

# --- Icon Cache ---
_ICON_CACHE = {}

def get_hicon_from_hwnd(hwnd):
    try:
        # 1. 嘗試從視窗訊息獲取小圖示 (設定 Timeout 避免卡死)
        result = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0, win32con.SMTO_ABORTIFHUNG, 50)
        hicon = result[1] if result else 0
        
        # 2. 如果沒有，嘗試獲取視窗類別圖示
        if not hicon:
            hicon = win32gui.GetClassLong(hwnd, win32con.GCL_HICONSM)
            
        # 3. 備案：追蹤 EXE 路徑並抽取
        if not hicon:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                exe_path = proc.exe()
                large, small = win32gui.ExtractIconEx(exe_path, 0)
                if small:
                    hicon = small[0]
                elif large:
                    hicon = large[0]
            except Exception:
                pass
        return hicon
    except Exception:
        return 0

def hicon_to_photoimage(hicon):
    if not hicon:
        return None
    try:
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        # 建立 32x32 的空間以容納可能比較大的圖示
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)
        
        # 使用 DrawIconEx 繪製並強制縮放到 32x32
        win32gui.DrawIconEx(hdc_mem.GetSafeHdc(), 0, 0, hicon, 32, 32, 0, 0, win32con.DI_NORMAL)
        
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (32, 32), bmpstr, 'raw', 'BGRA', 0, 1)
        
        # 將 32x32 的影像高品質縮放至 24x24，讓 Treeview 看起來剛好
        img = img.resize((24, 24), Image.Resampling.LANCZOS)
        
        # 清理
        win32gui.DestroyIcon(hicon)
        
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def get_cached_icon(hwnd):
    # 用 PID 作為快取鍵比較穩，因為同一個程式的圖示通常一樣
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if pid in _ICON_CACHE:
        return _ICON_CACHE[pid]
    
    hicon = get_hicon_from_hwnd(hwnd)
    img = hicon_to_photoimage(hicon)
    if img:
        _ICON_CACHE[pid] = img
    return img

def _enum_taskbar_titles():
    exclude_keywords = [
        "設定", "windows 輸入體驗", "windows input experience",
        "searchui", "cortana", "工作管理員", "start menu",
        "task manager", "lockapp", "shell experience host",
        "runtimebroker", "searchapp", "program manager"
    ]
    items = []
    
    # 使用 ctypes 的 EnumWindows 來避免 pywin32 長標題崩潰問題
    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    
    def foreach_window(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.strip()
                tl_low = title.lower()
                if not any(k in tl_low for k in exclude_keywords):
                    items.append((hwnd, title))
        return True
        
    cb = EnumWindowsProc(foreach_window)
    user32.EnumWindows(cb, 0)
    return items

class WindowSelectorDialog(tb.Toplevel):
    """
    附帶圖示的視窗選擇器
    on_select(hwnd, title)
    """
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.title("選擇目標視窗")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.on_select = on_select
        self.minsize(700, 450)
        self.minsize(600, 350)
        set_window_icon(self)

        try:
            from utils.utils import make_window_remember_position
            make_window_remember_position(self, 'window_selector_geometry', parent)
        except Exception as e:
            print('Window selector memory error:', e)

        frm = tb.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        # 左側 Treeview 區塊
        lb_frame = tb.Frame(frm)
        lb_frame.pack(fill="both", expand=True, side="left")

        # 設定 Treeview 樣式以適應更大的圖示
        style = tb.Style()
        style.configure("Treeview", rowheight=32)
        
        # 使用 Treeview 取代 Listbox，並隱藏表頭
        self.tree = tb.Treeview(lb_frame, columns=("title",), show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # 設定欄位寬度
        self.tree.column("#0", width=40, stretch=False) # 縮小圖示欄位
        self.tree.column("title", width=400)
        
        self.scroll = tb.Scrollbar(lb_frame, command=self.tree.yview)
        self.scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=self.scroll.set)
        self.tree.bind("<Double-Button-1>", lambda e: self._on_select())

        # 右側按鈕區塊
        btn_frame = tb.Frame(frm)
        btn_frame.pack(fill="y", side="right", padx=(10,0))

        self.select_btn = tb.Button(btn_frame, text="確認", bootstyle=SUCCESS, width=14, command=self._on_select)
        self.select_btn.pack(pady=(8,6), fill="x")

        self.refresh_btn = tb.Button(btn_frame, text="重新整理", bootstyle=SECONDARY, width=14, command=self.refresh)
        self.refresh_btn.pack(pady=6, fill="x")

        self.clear_btn = tb.Button(btn_frame, text="清除", bootstyle=WARNING, width=14, command=self._on_clear)
        self.clear_btn.pack(pady=6, fill="x")

        self.cancel_btn = tb.Button(btn_frame, text="取消", bootstyle=SECONDARY, width=14, command=self._on_cancel)
        self.cancel_btn.pack(pady=(12,6), fill="x")

        self._items = []
        self._tree_mapping = {} # iid -> (hwnd, title)
        
        # 讓視窗顯示後再非同步載入圖示，避免卡頓
        self.after(50, self.refresh)

    def refresh(self):
        # 清空 Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._tree_mapping.clear()
        
        self._items = _enum_taskbar_titles()
        
        for idx, (hwnd, title) in enumerate(self._items):
            img = get_cached_icon(hwnd)
            if img:
                iid = self.tree.insert("", "end", text="", image=img, values=(title,))
            else:
                iid = self.tree.insert("", "end", text="*", values=(title,))
            self._tree_mapping[iid] = (hwnd, title)
            
        if self._items:
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)

    def _on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        hwnd, title = self._tree_mapping[iid]
        try:
            self.on_select(hwnd, title)
        finally:
            self.destroy()

    def _on_clear(self):
        try:
            self.on_select(None, "")
        finally:
            self.destroy()

    def _on_cancel(self):
        self.destroy()