# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser

class VersionInfoDialog:
    def __init__(self, parent, version_manager, current_version, app_name="ChroLens App"):
        self.vm = version_manager
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"關於 {app_name}")
        self.dialog.geometry("400x300")
        ttk.Label(self.dialog, text=app_name, font=("", 16, "bold")).pack(pady=10)
        ttk.Label(self.dialog, text=f"版本: {current_version}").pack(pady=5)
        ttk.Button(self.dialog, text="檢查更新", command=self.check).pack(pady=10)
        ttk.Button(self.dialog, text="關閉", command=self.dialog.destroy).pack(pady=5)

    def check(self):
        def task():
            info = self.vm.check_for_updates()
            if info:
                if messagebox.askyesno("更新", f"發現新版本 {info['version']}\n是否更新?"):
                    path = self.vm.download_update(info['download_url'])
                    if path:
                        ext = self.vm.extract_update(path)
                        if ext: self.vm.apply_update(ext)
            else: messagebox.showinfo("更新", "已是最新版本")
        threading.Thread(target=task, daemon=True).start()
