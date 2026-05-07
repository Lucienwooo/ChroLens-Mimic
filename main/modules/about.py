import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
import os

try:
    from utils import get_icon_path, set_window_icon
except ImportError:
    # fallback（極端情況：utils.py 遺失）
    def get_icon_path(): return "umi_奶茶色.ico"
    def set_window_icon(w):
        try: w.iconbitmap(get_icon_path())
        except: pass

def show_about(parent):
    about_win = tb.Toplevel(parent)
    about_win.title("關於Mimic")
    about_win.geometry("450x600")
    about_win.resizable(False, False)
    about_win.grab_set()
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - 175
    y = parent.winfo_y() + 80
    about_win.geometry(f"+{x}+{y}")
    # 設定視窗圖示
    set_window_icon(about_win)

    frm = tb.Frame(about_win, padding=20)
    frm.pack(fill="both", expand=True)

    # 文字使用簡單設定（視主程式字型設定而定）
    tb.Label(frm, text="可理解為按鍵精靈/操作錄製/掛機工具\n解決重複性高的表單填入等動作", font=("Microsoft JhengHei", 11)).pack(anchor="w", pady=(0, 6))
    link = tk.Label(frm, text="任何問題歡迎加入DC伺服器詢問(點我)", font=("Microsoft JhengHei", 10, "underline"), fg="#5865F2", cursor="hand2")
    link.pack(anchor="w")
    link.bind("<Button-1>", lambda e: os.startfile("https://discord.gg/72Kbs4WPPn"))

    tb.Label(frm, text="By Lucienwooo", font=("Microsoft JhengHei", 11)).pack(anchor="w", pady=(6, 0))
    tb.Label(frm, text="若不嫌棄請我喝飲料\n贊助QRcode(可使用line pay)", font=("Microsoft JhengHei", 11)).pack(anchor="w", pady=(6, 0))

    # 新增贊助 QR Code
    qr_frame = tb.Frame(frm)
    qr_frame.pack(fill="x", pady=(10, 0))
    
    qr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images", "qr_code.png")
    if os.path.exists(qr_path):
        try:
            # 儲存參考避免被 GC
            about_win.qr_img = tk.PhotoImage(file=qr_path)
            # 調整圖片大小（512x512 縮小為 256x256）
            about_win.qr_img = about_win.qr_img.subsample(2, 2) 
            
            qr_label = tk.Label(qr_frame, image=about_win.qr_img, bg="#ffffff")
            qr_label.pack(pady=5)
        except Exception as e:
            tb.Label(qr_frame, text=f"(圖片載入失敗: {e})", font=("Microsoft JhengHei", 9)).pack()
    else:
        tb.Label(qr_frame, text="(尚未放置贊助圖片 images/qr_code.png)", font=("Microsoft JhengHei", 9)).pack()

    tb.Button(frm, text="關閉", command=about_win.destroy, width=8, bootstyle=SECONDARY).pack(side="bottom", anchor="e", pady=(20, 0))