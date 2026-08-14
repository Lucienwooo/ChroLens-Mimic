import codecs
import re

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. Add "查看圖庫" button
old_buttons = """        # 操作按鈕群（載入、儲存）
        buttons = [
            ("載入", self._load_script, "#2196F3"),
            ("儲存", self._save_script, "#4CAF50")
        ]"""
new_buttons = """        # 操作按鈕群（載入、儲存、查看圖庫）
        buttons = [
            ("載入", self._load_script, "#2196F3"),
            ("儲存", self._save_script, "#4CAF50"),
            ("查看圖庫", self._open_image_gallery, "#9C27B0")
        ]"""
if old_buttons in content:
    content = content.replace(old_buttons, new_buttons)

# 2. Add ImageGalleryViewer class and _open_image_gallery method
gallery_code = """
class ImageGalleryViewer(tk.Toplevel):
    def __init__(self, parent, editor):
        super().__init__(parent)
        self.editor = editor
        self.title("圖庫查看器")
        
        # 設置視窗大小為編輯器的 2/3
        w = int(parent.winfo_width() * 0.66)
        h = int(parent.winfo_height() * 0.66)
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(bg="#1e1e1e")
        self.transient(parent)
        
        # 主框架
        main_frame = tk.Frame(self, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 建立 Canvas 來實現隱藏卷軸的網格
        self.canvas = tk.Canvas(main_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # 綁定滾輪
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind("<Destroy>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        self.grid_frame = tk.Frame(self.canvas, bg="#1e1e1e")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self._load_images()
        
    def _on_mousewheel(self, event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def _load_images(self):
        images_dir = "images"
        if not os.path.exists(images_dir):
            tk.Label(self.grid_frame, text="圖庫中沒有任何圖片", bg="#1e1e1e", fg="#ffffff", font=font_tuple(12)).pack(pady=20)
            return
            
        files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            tk.Label(self.grid_frame, text="圖庫中沒有任何圖片", bg="#1e1e1e", fg="#ffffff", font=font_tuple(12)).pack(pady=20)
            return
            
        # 繪製網格
        col = 0
        row = 0
        max_cols = 4 # 預設每行4張圖
        
        self.thumbnails = [] # 防止垃圾回收
        for f in files:
            try:
                img_path = os.path.join(images_dir, f)
                img = Image.open(img_path)
                img.thumbnail((120, 120))
                photo = ImageTk.PhotoImage(img)
                self.thumbnails.append(photo)
                
                frame = tk.Frame(self.grid_frame, bg="#2d2d2d", padx=5, pady=5, bd=1, relief="solid")
                frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                
                img_lbl = tk.Label(frame, image=photo, bg="#2d2d2d", cursor="hand2")
                img_lbl.pack()
                
                name_lbl = tk.Label(frame, text=os.path.splitext(f)[0], bg="#2d2d2d", fg="#ffffff", font=font_tuple(9), cursor="hand2")
                name_lbl.pack(pady=5)
                
                # 點擊事件
                def on_click(event, fname=os.path.splitext(f)[0]):
                    cmd = f">辨識>{fname}, T=0s000"
                    self.clipboard_clear()
                    self.clipboard_append(cmd)
                    self.editor._show_message("成功", f"已複製指令：\\n{cmd}", "success")
                
                img_lbl.bind("<Button-1>", on_click)
                name_lbl.bind("<Button-1>", on_click)
                frame.bind("<Button-1>", on_click)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            except Exception as e:
                pass
                
        # 讓每行自動擴展
        for i in range(max_cols):
            self.grid_frame.grid_columnconfigure(i, weight=1)
"""

if "class ImageGalleryViewer" not in content:
    # 插入在檔案最後
    content += "\n" + gallery_code
    
    # 插入 method 在 TextScriptEditor 內 (隨便找個 method 附加)
    method_code = """
    def _open_image_gallery(self):
        gallery = ImageGalleryViewer(self, self)
"""
    # 附加在 __init__ 後面或找一個合適的地方
    content = content.replace("    def _show_command_reference(self):", method_code + "\n    def _show_command_reference(self):")

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print("text_script_editor.py Image Gallery patched successfully!")
