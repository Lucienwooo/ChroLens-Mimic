# -*- coding: utf-8 -*-
"""
ChroLens Mimic — 共用工具函式庫 (utils.py)
==========================================
整合散落在各模組中重複定義的工具函式，統一在此維護：
  - get_icon_path()   : 取得圖示路徑（打包 / 開發環境通用）
  - set_window_icon() : 為 tk/tb 視窗設定圖示
  - center_window()   : 讓視窗在父視窗或螢幕正中央顯示

任何新的跨模組工具函式請一律加在這裡。
"""

import os
import sys


# ─── 圖示路徑 ────────────────────────────────────────────
ICON_NAME = "umi_奶茶色.ico"

def get_icon_path() -> str:
    """取得圖示檔案路徑（打包後和開發環境通用）"""
    try:
        # PyInstaller 打包後的環境
        if getattr(sys, "frozen", False):
            p = os.path.join(sys._MEIPASS, ICON_NAME)
            if os.path.exists(p):
                return p

        # 開發環境：依序嘗試常見位置
        this_dir = os.path.dirname(os.path.abspath(__file__))  # modules/
        main_dir = os.path.dirname(this_dir)                    # main/
        project_dir = os.path.dirname(main_dir)                 # ChroLens-Mimic/

        candidates = [
            os.path.join(main_dir, ICON_NAME),          # main/umi_奶茶色.ico  ← 最常見
            os.path.join(project_dir, ICON_NAME),        # ChroLens-Mimic/umi_奶茶色.ico
            os.path.join(project_dir, "pic", ICON_NAME), # ChroLens-Mimic/pic/umi_奶茶色.ico
            os.path.join(this_dir, ICON_NAME),           # modules/umi_奶茶色.ico
            ICON_NAME,                                    # 當前工作目錄
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
    except Exception:
        pass
    return ICON_NAME  # 最終回退


def set_window_icon(window) -> None:
    """為 tk / ttkbootstrap Toplevel 視窗設定圖示（靜默失敗）"""
    try:
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception:
        pass


def center_window(window, width: int, height: int, parent=None) -> None:
    """將視窗置中於父視窗或螢幕

    Args:
        window: tk / ttkbootstrap 視窗物件
        width:  視窗寬度 (px)
        height: 視窗高度 (px)
        parent: 父視窗（若為 None 則置中於螢幕）
    """
    try:
        window.update_idletasks()
        if parent:
            px = parent.winfo_x() + (parent.winfo_width() - width) // 2
            py = parent.winfo_y() + (parent.winfo_height() - height) // 2
        else:
            px = (window.winfo_screenwidth() - width) // 2
            py = (window.winfo_screenheight() - height) // 2
        window.geometry(f"{width}x{height}+{px}+{py}")
    except Exception:
        pass


import tkinter as tk
import ttkbootstrap as tb

class CustomAskStringDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, initialvalue="", win_name=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.win_name = win_name
        
        # Try to find the root app that holds user_config
        self.root_app = parent
        while self.root_app and not hasattr(self.root_app, 'user_config') and getattr(self.root_app, 'master', None):
            self.root_app = self.root_app.master
        if not self.root_app or not hasattr(self.root_app, 'user_config'):
            # Also check if parent has a 'parent' attribute (like GalleryBrowser)
            if hasattr(parent, 'parent') and hasattr(parent.parent, 'user_config'):
                self.root_app = parent.parent
            elif hasattr(parent, 'editor') and hasattr(parent.editor, 'parent') and hasattr(parent.editor.parent, 'user_config'):
                self.root_app = parent.editor.parent
        
        # Try to set icon
        try:
            set_window_icon(self)
        except Exception:
            pass
            
        # UI
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        lbl = tb.Label(main_frame, text=prompt)
        lbl.pack(anchor="w", pady=(0, 10))
        
        self.entry_var = tk.StringVar(value=initialvalue)
        self.entry = tb.Entry(main_frame, textvariable=self.entry_var, width=40)
        self.entry.pack(fill="x", pady=(0, 20))
        self.entry.select_range(0, tk.END)
        self.entry.focus_set()
        
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x")
        
        ok_btn = tb.Button(btn_frame, text="OK", command=self.on_ok, bootstyle="primary")
        ok_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        cancel_btn = tb.Button(btn_frame, text="Cancel", command=self.on_cancel, bootstyle="secondary")
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Restore position
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        self.update_idletasks()
        
        if self.win_name and self.root_app and hasattr(self.root_app, "user_config") and self.win_name in self.root_app.user_config:
            try:
                geom = self.root_app.user_config[self.win_name]
                if '+' in geom:
                    pos = geom[geom.find('+'):]
                    self.after(50, lambda p=pos: self.geometry(p))
                else:
                    self.after(50, lambda: self._center_window(parent))
            except:
                self.after(50, lambda: self._center_window(parent))
        else:
            self.after(50, lambda: self._center_window(parent))
            
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)
        
    def _center_window(self, parent):
        try:
            self.update_idletasks()
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            if parent and parent.winfo_viewable():
                px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
                py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
            else:
                px = (self.winfo_screenwidth() - w) // 2
                py = (self.winfo_screenheight() - h) // 2
            self.geometry(f"+{px}+{py}")
        except:
            pass
            
    def on_ok(self):
        self.result = self.entry_var.get()
        self.save_geometry()
        self.destroy()
        
    def on_cancel(self):
        self.result = None
        self.save_geometry()
        self.destroy()
        
    def save_geometry(self):
        if self.win_name and self.root_app and hasattr(self.root_app, "user_config"):
            self.root_app.user_config[self.win_name] = self.geometry()
            try:
                if hasattr(self.root_app, "save_config"):
                    self.root_app.save_config()
            except:
                pass

def custom_askstring(title, prompt, initialvalue="", parent=None, win_name=None):
    if parent is None:
        import tkinter as tk
        try:
            parent = tk._default_root
        except:
            parent = None
    dlg = CustomAskStringDialog(parent, title, prompt, initialvalue, win_name)
    return dlg.result

def make_window_remember_position(window, win_name: str, parent=None):
    """
    讓指定的視窗具備：
    1. 貓貓圖示 (set_window_icon)
    2. 自動還原上次關閉的位置
    3. 自動在關閉時儲存位置 (透過覆寫 destroy)
    """
    try:
        set_window_icon(window)
    except Exception:
        pass

    # Find root app
    root_app = parent if parent else getattr(window, 'master', None)
    while root_app and not hasattr(root_app, 'user_config') and getattr(root_app, 'master', None):
        root_app = root_app.master
    if not root_app or not hasattr(root_app, 'user_config'):
        if hasattr(parent, 'parent') and hasattr(parent.parent, 'user_config'):
            root_app = parent.parent
        elif hasattr(parent, 'editor') and hasattr(parent.editor, 'parent') and hasattr(parent.editor.parent, 'user_config'):
            root_app = parent.editor.parent
        elif hasattr(window, 'parent') and hasattr(window.parent, 'user_config'):
            root_app = window.parent
        elif hasattr(window, 'master') and hasattr(window.master, 'user_config'):
            root_app = window.master

    # Restore position
    if root_app and hasattr(root_app, "user_config") and win_name in root_app.user_config:
        try:
            geom = root_app.user_config[win_name]
            if '+' in geom:
                pos = geom[geom.find('+'):]
                window.after(50, lambda p=pos: window.geometry(p))
        except:
            pass

    # Override destroy to save position
    orig_destroy = window.destroy
    def custom_destroy(*args, **kwargs):
        if root_app and hasattr(root_app, "user_config"):
            try:
                state = window.state()
                if state == 'normal' or state == 'withdrawn':
                    root_app.user_config[win_name] = window.geometry()
                    if hasattr(root_app, "save_config"):
                        root_app.save_config()
            except Exception:
                pass
        try:
            orig_destroy(*args, **kwargs)
        except:
            pass
        
    window.destroy = custom_destroy

    # Ensure clicking the X button triggers our custom destroy
    orig_protocol = window.protocol("WM_DELETE_WINDOW")
    def on_wm_delete():
        custom_destroy()
        if isinstance(orig_protocol, str) and orig_protocol:
            try:
                window.eval(orig_protocol)
            except:
                pass
    window.protocol("WM_DELETE_WINDOW", on_wm_delete)
