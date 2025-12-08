# -*- coding: utf-8 -*-
"""
版本資訊對話框 - ChroLens_Mimic
顯示當前版本、更新日誌和檢查更新

作者: Lucien
日期: 2025/12/08
"""

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, scrolledtext
import threading
import os
import sys


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


class VersionInfoDialog(tb.Toplevel):
    """版本資訊與更新對話框（合併版）"""
    
    def __init__(self, parent, version_manager, current_version, on_update_callback=None):
        """
        初始化版本資訊對話框
        
        Args:
            parent: 父視窗
            version_manager: 版本管理器實例
            current_version: 當前版本號
            on_update_callback: 更新完成後的回調函數
        """
        super().__init__(parent)
        
        self.parent = parent
        self.version_manager = version_manager
        self.current_version = current_version
        self.on_update_callback = on_update_callback
        
        self.title("版本資訊 - ChroLens_Mimic")
        self.geometry("600x680")
        self.resizable(True, True)
        self.minsize(550, 650)
        
        # 設定圖示
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # 置中顯示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # 設定為模態對話框
        self.transient(parent)
        self.grab_set()
        
        # 創建 UI
        self._create_ui()
        
        # 自動開始載入更新日誌和檢查更新
        self.after(100, self._load_content)
    
    def _create_ui(self):
        """創建 UI 元件"""
        # 主框架（減少內邊距）
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # ========== 標題區域 ==========
        title_frame = tb.Frame(main_frame)
        title_frame.pack(fill=X, pady=(0, 15))
        
        title_label = tb.Label(
            title_frame,
            text="ChroLens_Mimic",
            font=("Microsoft JhengHei", 18, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # ========== 版本資訊區域 ==========
        info_frame = tb.Labelframe(
            main_frame,
            text="版本資訊",
            padding=15,
            bootstyle="info"
        )
        info_frame.pack(fill=X, pady=(0, 15))
        
        # 當前版本
        current_version_frame = tb.Frame(info_frame)
        current_version_frame.pack(fill=X, pady=5)
        
        tb.Label(
            current_version_frame,
            text="目前版本：",
            font=("Microsoft JhengHei", 11),
            width=12,
            anchor=W
        ).pack(side=LEFT)
        
        tb.Label(
            current_version_frame,
            text=f"v{self.current_version}",
            font=("Microsoft JhengHei", 11, "bold"),
            bootstyle="info"
        ).pack(side=LEFT)
        
        # 最新版本（稍後更新）
        latest_version_frame = tb.Frame(info_frame)
        latest_version_frame.pack(fill=X, pady=5)
        
        tb.Label(
            latest_version_frame,
            text="最新版本：",
            font=("Microsoft JhengHei", 11),
            width=12,
            anchor=W
        ).pack(side=LEFT)
        
        self.latest_version_label = tb.Label(
            latest_version_frame,
            text="檢查中...",
            font=("Microsoft JhengHei", 11),
            bootstyle="secondary"
        )
        self.latest_version_label.pack(side=LEFT)
        
        # 更新狀態
        status_frame = tb.Frame(info_frame)
        status_frame.pack(fill=X, pady=5)
        
        tb.Label(
            status_frame,
            text="更新狀態：",
            font=("Microsoft JhengHei", 11),
            width=12,
            anchor=W
        ).pack(side=LEFT)
        
        self.update_status_label = tb.Label(
            status_frame,
            text="正在檢查更新...",
            font=("Microsoft JhengHei", 11),
            bootstyle="secondary"
        )
        self.update_status_label.pack(side=LEFT)
        
        # ========== 更新說明區域 ==========
        update_notes_frame = tb.Labelframe(
            main_frame,
            text="更新說明",
            padding=15,
            bootstyle="success"
        )
        update_notes_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        # 更新說明文字框
        self.update_notes_text = scrolledtext.ScrolledText(
            update_notes_frame,
            wrap=tk.WORD,
            font=("Microsoft JhengHei", 9),
            height=8
        )
        self.update_notes_text.pack(fill=BOTH, expand=YES)
        self.update_notes_text.insert("1.0", "檢查中...")
        self.update_notes_text.config(state=tk.DISABLED)
        
        # ========== 進度區域（初始隱藏）==========
        self.progress_frame = tb.Labelframe(
            main_frame,
            text="更新進度",
            padding=10,
            bootstyle="info"
        )
        # 不要立即 pack，等需要時再顯示
        
        self.progress_label = tb.Label(
            self.progress_frame,
            text="準備下載...",
            font=("Microsoft JhengHei", 10)
        )
        self.progress_label.pack(pady=(0, 5))
        
        self.progress_bar = tb.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=500,
            bootstyle="success"
        )
        self.progress_bar.pack(pady=(0, 5))
        
        self.progress_detail_label = tb.Label(
            self.progress_frame,
            text="",
            font=("Microsoft JhengHei", 9),
            bootstyle="secondary"
        )
        self.progress_detail_label.pack()
        
        # ========== 按鈕區域 ==========
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        # 更新按鈕（初始禁用）
        self.update_btn = tb.Button(
            button_frame,
            text="立即更新",
            bootstyle="success",
            width=15,
            command=self._start_update,
            state=DISABLED
        )
        self.update_btn.pack(side=LEFT, padx=5)
        
        # 關閉按鈕
        close_btn = tb.Button(
            button_frame,
            text="關閉",
            bootstyle="secondary",
            width=15,
            command=self.destroy
        )
        close_btn.pack(side=RIGHT, padx=5)
    
    def _load_content(self):
        """載入內容（在背景執行緒中）"""
        threading.Thread(target=self._fetch_data, daemon=True).start()
    
    def _perform_update(self):
        """執行更新流程"""
        try:
            # 1. 下載更新 (0-40%)
            self.after(0, lambda: self.progress_label.config(text="階段 1/3: 下載更新檔案"))
            self.after(0, lambda: self.progress_detail_label.config(text="正在連接伺服器..."))
            
            def progress_callback(downloaded, total):
                if total > 0:
                    # 下載佔總進度的 40%
                    download_percent = (downloaded / total) * 40
                    self.after(0, lambda p=download_percent: self.progress_bar.config(value=p))
                    
                    # 格式化檔案大小
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    
                    self.after(0, lambda d=downloaded_mb, t=total_mb: 
                              self.progress_detail_label.config(
                                  text=f"已下載: {d:.2f}MB / {t:.2f}MB ({(d/t)*100:.1f}%)"
                              ))
            
            zip_path = self.version_manager.download_update(
                self.update_info['download_url'],
                progress_callback
            )
            
            if not zip_path:
                raise Exception("下載失敗")
            
            # 2. 解壓縮 (40-70%)
            self.after(0, lambda: self.progress_bar.config(value=40))
            self.after(0, lambda: self.progress_label.config(text="階段 2/3: 解壓縮檔案"))
            self.after(0, lambda: self.progress_detail_label.config(text="正在解壓縮更新檔案..."))
            
            # 模擬解壓縮進度
            for i in range(40, 70, 5):
                self.after(0, lambda p=i: self.progress_bar.config(value=p))
                import time
                time.sleep(0.1)
            
            extract_dir = self.version_manager.extract_update(zip_path)
            
            if not extract_dir:
                raise Exception("解壓縮失敗")
            
            self.after(0, lambda: self.progress_bar.config(value=70))
            
            # 3. 應用更新 (70-100%)
            self.after(0, lambda: self.progress_label.config(text="階段 3/3: 安裝更新"))
            self.after(0, lambda: self.progress_detail_label.config(text="正在準備更新檔案..."))
            self.after(0, lambda: self.progress_bar.config(value=80))
            
            success = self.version_manager.apply_update(extract_dir, restart_after=True)
            
            if success:
                self.after(0, lambda: self.progress_bar.config(value=100))
                self.after(0, lambda: self.progress_detail_label.config(text="更新完成!"))
                self.after(0, self._show_success)
            else:
                raise Exception("應用更新失敗")
                
        except Exception as e:
            self.after(0, lambda err=str(e): self._show_error(err))
    
    def _show_success(self):
        """顯示更新成功"""
        # 確保進度條顯示 100%
        self.progress_bar.config(value=100)
        self.progress_label.config(text="✓ 更新完成!")
        self.progress_detail_label.config(text="所有檔案已準備就緒")
        
        # 詢問是否立即重啟
        result = messagebox.askyesno(
            "更新完成",
            "更新已成功下載並準備完成！\n\n是否立即重新啟動程式以應用更新？\n\n" +
            "(選擇'否'將在下次啟動時自動更新)",
            parent=self
        )
        
        if result:
            # 立即重啟
            if self.on_update_callback:
                self.on_update_callback()
            # 關閉視窗
            self.destroy()
        else:
            # 稍後重啟
            messagebox.showinfo(
                "提示",
                "更新將在下次啟動程式時自動應用。",
                parent=self
            )
            self.destroy()
    
    def _show_error(self, error_msg: str):
        """顯示更新失敗"""
        # 停止進度條動畫（如果在運行）
        try:
            self.progress_bar.stop()
        except:
            pass
        
        # 重置進度條為紅色
        self.progress_bar.config(bootstyle="danger")
        self.progress_label.config(text="✗ 更新失敗")
        self.progress_detail_label.config(text=f"錯誤: {error_msg}")
        
        # 重新啟用更新按鈕
        self.update_btn.config(state=NORMAL)
        
        # 顯示錯誤訊息
        messagebox.showerror(
            "更新失敗",
            f"更新過程中發生錯誤：\n\n{error_msg}\n\n請稍後再試或手動下載更新。",
            parent=self
        )
    
    def _fetch_data(self):
        """獲取更新資訊和檢查更新（背景執行緒）"""
        # 檢查更新
        update_info = self.version_manager.check_for_updates()
        self.after(0, lambda: self._update_version_status(update_info))
    
    def _update_version_status(self, update_info):
        """更新版本狀態和更新說明"""
        if update_info:
            # 有新版本
            latest_version = update_info['version']
            self.latest_version_label.config(text=f"v{latest_version}", bootstyle="success")
            self.update_status_label.config(text="有新版本可用！", bootstyle="success")
            self.update_btn.config(state=NORMAL)
            self.update_info = update_info
            
            # 顯示更新說明
            release_notes = update_info.get('release_notes', '無更新說明')
            self.update_notes_text.config(state=tk.NORMAL)
            self.update_notes_text.delete("1.0", tk.END)
            self.update_notes_text.insert("1.0", release_notes)
            self.update_notes_text.config(state=tk.DISABLED)
        else:
            # 已是最新版本
            self.latest_version_label.config(text=f"v{self.current_version}", bootstyle="info")
            self.update_status_label.config(text="目前已是最新版本", bootstyle="info")
            self.update_btn.config(state=DISABLED)
            self.update_info = None
            
            # 顯示當前版本資訊
            self.update_notes_text.config(state=tk.NORMAL)
            self.update_notes_text.delete("1.0", tk.END)
            self.update_notes_text.insert("1.0", "您目前使用的是最新版本，無需更新。")
            self.update_notes_text.config(state=tk.DISABLED)
    
    def _start_update(self):
        """開始更新流程（直接在此視窗執行）"""
        if not hasattr(self, 'update_info') or not self.update_info:
            return
        
        # 確認更新
        result = messagebox.askyesno(
            "確認更新",
            f"即將更新到 v{self.update_info['version']}\n\n更新完成後程式將自動重啟。\n\n確定要更新嗎？",
            parent=self
        )
        
        if not result:
            return
        
        # 禁用更新按鈕和關閉按鈕
        self.update_btn.config(state=DISABLED)
        
        # 顯示進度框（插入到按鈕區域之前）
        # 獲取 main_frame 的子元件
        main_frame = self.winfo_children()[0]
        button_frame = None
        for child in main_frame.winfo_children():
            if isinstance(child, tb.Frame) and not isinstance(child, tb.Labelframe):
                # 找到最後一個 Frame（應該是 button_frame）
                button_frame = child
        
        if button_frame:
            # 在按鈕框架之前插入進度框
            self.progress_frame.pack(fill=X, pady=(0, 10), before=button_frame)
        else:
            # 如果找不到,就直接pack
            self.progress_frame.pack(fill=X, pady=(0, 10))
        
        # 重置進度條
        self.progress_bar.config(value=0, mode='determinate')
        self.progress_label.config(text="準備下載...")
        self.progress_detail_label.config(text="")
        
        # 在背景執行緒中執行更新
        threading.Thread(target=self._perform_update, daemon=True).start()

