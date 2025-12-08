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
    """版本資訊對話框"""
    
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
        self.geometry("600x500")
        self.resizable(True, True)
        self.minsize(550, 450)
        
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
        
        # ========== 更新日誌區域 ==========
        changelog_frame = tb.Labelframe(
            main_frame,
            text="更新日誌",
            padding=15,
            bootstyle="primary"
        )
        changelog_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        # 文字框（減少高度）
        self.changelog_text = scrolledtext.ScrolledText(
            changelog_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=10
        )
        self.changelog_text.pack(fill=BOTH, expand=YES)
        self.changelog_text.insert("1.0", "正在載入更新日誌...")
        self.changelog_text.config(state=tk.DISABLED)
        
        # ========== 按鈕區域 ==========
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X)
        
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
        
        # 訪問官網按鈕
        visit_btn = tb.Button(
            button_frame,
            text="訪問官網",
            bootstyle="info",
            width=15,
            command=self._open_website
        )
        visit_btn.pack(side=LEFT, padx=5)
        
        # 重新檢查按鈕
        recheck_btn = tb.Button(
            button_frame,
            text="重新檢查",
            bootstyle="secondary",
            width=15,
            command=self._reload_content
        )
        recheck_btn.pack(side=LEFT, padx=5)
        
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
    
    def _reload_content(self):
        """重新載入內容"""
        self.latest_version_label.config(text="檢查中...")
        self.update_status_label.config(text="正在檢查更新...", bootstyle="secondary")
        self.update_btn.config(state=DISABLED)
        
        self.changelog_text.config(state=tk.NORMAL)
        self.changelog_text.delete("1.0", tk.END)
        self.changelog_text.insert("1.0", "正在載入更新日誌...")
        self.changelog_text.config(state=tk.DISABLED)
        
        self._load_content()
    
    def _fetch_data(self):
        """獲取更新日誌和檢查更新（背景執行緒）"""
        # 1. 獲取更新日誌
        changelog = self.version_manager.fetch_changelog()
        self.after(0, lambda: self._update_changelog(changelog))
        
        # 2. 檢查更新
        update_info = self.version_manager.check_for_updates()
        self.after(0, lambda: self._update_version_status(update_info))
    
    def _update_changelog(self, changelog: str):
        """更新更新日誌文字框"""
        self.changelog_text.config(state=tk.NORMAL)
        self.changelog_text.delete("1.0", tk.END)
        self.changelog_text.insert("1.0", changelog)
        self.changelog_text.config(state=tk.DISABLED)
    
    def _update_version_status(self, update_info):
        """更新版本狀態"""
        if update_info:
            # 有新版本
            latest_version = update_info['version']
            self.latest_version_label.config(text=f"v{latest_version}", bootstyle="success")
            self.update_status_label.config(text="有新版本可用！", bootstyle="success")
            self.update_btn.config(state=NORMAL)
            self.update_info = update_info
        else:
            # 已是最新版本
            self.latest_version_label.config(text=f"v{self.current_version}", bootstyle="info")
            self.update_status_label.config(text="目前已是最新版本", bootstyle="info")
            self.update_btn.config(state=DISABLED)
            self.update_info = None
    
    def _start_update(self):
        """開始更新流程"""
        if not hasattr(self, 'update_info') or not self.update_info:
            return
        
        # 顯示更新確認對話框
        UpdateConfirmDialog(self, self.version_manager, self.update_info, self.on_update_callback)
    
    def _open_website(self):
        """開啟官網"""
        import webbrowser
        try:
            webbrowser.open(self.version_manager.CHANGELOG_URL)
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟網站：\n{e}")


class UpdateConfirmDialog(tb.Toplevel):
    """更新確認對話框"""
    
    def __init__(self, parent, version_manager, update_info, on_update_callback=None):
        super().__init__(parent)
        
        self.parent = parent
        self.version_manager = version_manager
        self.update_info = update_info
        self.on_update_callback = on_update_callback
        
        self.title("確認更新")
        self.geometry("480x450")
        self.resizable(False, False)
        
        # 設定圖示
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # 顯示在父視窗右側
        self.update_idletasks()
        if parent:
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            # 緊鄰父視窗右側
            x = parent_x + parent_width + 10
            y = parent_y
        else:
            # 如果沒有父視窗，則置中
            x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
            y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()
    
    def _create_ui(self):
        """創建 UI"""
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # 標題
        title_label = tb.Label(
            main_frame,
            text="發現新版本！",
            font=("Microsoft JhengHei", 16, "bold"),
            bootstyle="success"
        )
        title_label.pack(pady=(0, 15))
        
        # 版本資訊
        info_frame = tb.Frame(main_frame)
        info_frame.pack(fill=X, pady=(0, 15))
        
        version_text = f"新版本：v{self.update_info['version']}\n發布時間：{self.update_info['published_at'][:10]}"
        tb.Label(
            info_frame,
            text=version_text,
            font=("Microsoft JhengHei", 11),
            justify=LEFT
        ).pack(anchor=W)
        
        # 更新說明
        notes_frame = tb.Labelframe(main_frame, text="更新說明", padding=10)
        notes_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))
        
        notes_text = scrolledtext.ScrolledText(
            notes_frame,
            wrap=tk.WORD,
            font=("Microsoft JhengHei", 9),
            height=8
        )
        notes_text.pack(fill=BOTH, expand=YES)
        notes_text.insert("1.0", self.update_info['release_notes'])
        notes_text.config(state=tk.DISABLED)
        
        # 進度條
        self.progress_frame = tb.Labelframe(main_frame, text="下載進度", padding=10)
        self.progress_label = tb.Label(self.progress_frame, text="準備下載...")
        self.progress_label.pack()
        
        self.progress_bar = tb.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=5)
        
        # 按鈕
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(15, 0))
        
        self.confirm_btn = tb.Button(
            button_frame,
            text="開始更新",
            bootstyle="success",
            width=15,
            command=self._confirm_update
        )
        self.confirm_btn.pack(side=LEFT, padx=5)
        
        cancel_btn = tb.Button(
            button_frame,
            text="稍後再說",
            bootstyle="secondary",
            width=15,
            command=self.destroy
        )
        cancel_btn.pack(side=RIGHT, padx=5)
    
    def _confirm_update(self):
        """確認更新"""
        self.confirm_btn.config(state=DISABLED)
        self.progress_frame.pack(fill=X, pady=(0, 15), before=self.winfo_children()[3])
        
        # 在背景執行緒中執行更新
        threading.Thread(target=self._perform_update, daemon=True).start()
    
    def _perform_update(self):
        """執行更新流程"""
        try:
            # 1. 下載更新
            self.after(0, lambda: self.progress_label.config(text="正在下載更新..."))
            
            def progress_callback(downloaded, total):
                if total > 0:
                    percent = (downloaded / total) * 100
                    self.after(0, lambda p=percent: self.progress_bar.config(value=p))
                    self.after(0, lambda d=downloaded, t=total: 
                              self.progress_label.config(text=f"正在下載... {d//1024}KB / {t//1024}KB"))
            
            zip_path = self.version_manager.download_update(
                self.update_info['download_url'],
                progress_callback
            )
            
            if not zip_path:
                raise Exception("下載失敗")
            
            # 2. 解壓縮
            self.after(0, lambda: self.progress_label.config(text="正在解壓縮..."))
            self.after(0, lambda: self.progress_bar.config(mode='indeterminate'))
            self.after(0, lambda: self.progress_bar.start())
            
            extract_dir = self.version_manager.extract_update(zip_path)
            
            if not extract_dir:
                raise Exception("解壓縮失敗")
            
            # 3. 應用更新
            self.after(0, lambda: self.progress_label.config(text="準備應用更新..."))
            
            success = self.version_manager.apply_update(extract_dir, restart_after=True)
            
            if success:
                self.after(0, self._show_success)
            else:
                raise Exception("應用更新失敗")
                
        except Exception as e:
            self.after(0, lambda err=str(e): self._show_error(err))
    
    def _show_success(self):
        """顯示更新成功"""
        self.progress_bar.stop()
        messagebox.showinfo(
            "更新成功",
            "更新檔案已準備完成！\n\n程式將在關閉後自動更新並重新啟動。",
            parent=self
        )
        
        # 呼叫回調並關閉程式
        if self.on_update_callback:
            self.on_update_callback()
        
        # 關閉所有視窗
        self.destroy()
        if self.parent:
            self.parent.destroy()
    
    def _show_error(self, error_msg: str):
        """顯示更新失敗"""
        self.progress_bar.stop()
        self.confirm_btn.config(state=NORMAL)
        messagebox.showerror(
            "更新失敗",
            f"更新過程中發生錯誤：\n\n{error_msg}\n\n請稍後再試或手動下載更新。",
            parent=self
        )
