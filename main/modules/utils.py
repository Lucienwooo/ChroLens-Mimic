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
