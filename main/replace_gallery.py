# -*- coding: utf-8 -*-
import codecs
import re

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

new_gallery_code = '''class ImageGalleryViewer(tk.Toplevel):
    def __init__(self, parent, editor):
        super().__init__(parent)
        self.editor = editor
        self.title("圖庫瀏覽器")
        
        # 設定大小為編輯器的 2/3，預設高度加到 720
        w = int(parent.winfo_width() * 0.8) if parent.winfo_width() > 1000 else 800
        h = 720
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        
        def _apply_gal_geom():
            if not (hasattr(self.editor.parent, "restore_window_position") and self.editor.parent.restore_window_position("gallery_geometry", self, "800x720")):
                self.geometry(f"800x720+{x}+{y}")
        self.after(50, _apply_gal_geom)
        
        self.minsize(800, 720)
        self.configure(bg="#1e1e1e")
        self.transient(parent)
        set_window_icon(self)
        self.protocol("WM_DELETE_WINDOW", self._on_gallery_closing)
        
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.images_root = os.path.join(base_dir, "scripts", "images")
        except:
            self.images_root = os.path.join("scripts", "images")
            
        if not os.path.exists(self.images_root):
            os.makedirs(self.images_root, exist_ok=True)
            
        self.current_folder = ""
        self.selected_image_path = None
        self.thumbnails = [] 
        
        # 主框架
        main_frame = tk.Frame(self, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 建立 Grid 版面的 20% / 80% 左右分割
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=8)
        main_frame.rowconfigure(0, weight=1)
        
        # 左側面板
        left_panel = tk.Frame(main_frame, bg="#252526")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 搜尋圖片
        tk.Label(left_panel, text="搜尋圖片:", bg="#252526", fg="#ffffff", font=font_tuple(10)).pack(anchor="w", padx=10, pady=(10, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._load_images())
        search_entry = tk.Entry(left_panel, textvariable=self.search_var, bg="#3c3c3c", fg="#ffffff", insertbackground="white")
        search_entry.pack(fill="x", padx=10, pady=(0, 15))
        
        # 分類資料夾
        folder_header = tk.Frame(left_panel, bg="#252526")
        folder_header.pack(fill="x", padx=10, pady=(0, 5))
        tk.Label(folder_header, text="分類資料夾:", bg="#252526", fg="#ffffff", font=font_tuple(10)).pack(side="left")
        
        add_folder_btn = tb.Button(folder_header, text="＋", bootstyle="success", command=self._create_folder, padding=(2,0))
        add_folder_btn.pack(side="right")
        
        self.folder_listbox = tk.Listbox(left_panel, bg="#3c3c3c", fg="#ffffff", selectbackground="#094771", highlightthickness=0, borderwidth=1, height=10)
        self.folder_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        self.folder_listbox.bind("<<ListboxSelect>>", self._on_folder_select)
        
        # 重新命名
        tk.Label(left_panel, text="重新命名 (選取圖片):", bg="#252526", fg="#ffffff", font=font_tuple(10)).pack(anchor="w", padx=10, pady=(0, 5))
        self.selected_img_name_var = tk.StringVar(value="未選擇")
        tk.Label(left_panel, textvariable=self.selected_img_name_var, bg="#252526", fg="#aaaaaa", font=font_tuple(9)).pack(anchor="w", padx=10, pady=(0, 5))
        
        self.rename_var = tk.StringVar()
        rename_entry = tk.Entry(left_panel, textvariable=self.rename_var, bg="#3c3c3c", fg="#ffffff", insertbackground="white")
        rename_entry.pack(fill="x", padx=10, pady=(0, 5))
        
        rename_btn = tb.Button(left_panel, text="確認修改", bootstyle="warning", command=self._rename_image)
        rename_btn.pack(fill="x", padx=10, pady=(0, 15))
        
        self.auto_close_var = tk.BooleanVar(value=False)
        auto_close_cb = tb.Checkbutton(left_panel, text="點擊自動關閉", variable=self.auto_close_var, bootstyle="round-toggle")
        auto_close_cb.pack(anchor="w", padx=10, pady=(0, 10))
        
        def _open_gallery_folder():
            import os
            if os.path.exists(self.images_root):
                os.startfile(self.images_root)
        
        open_folder_btn = tb.Button(left_panel, text="📁 圖庫資料夾", bootstyle="info", command=_open_gallery_folder)
        open_folder_btn.pack(fill="x", side="bottom", padx=10, pady=(0, 15))
        
        # 右側面板
        right_panel = tk.Frame(main_frame, bg="#1e1e1e")
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        self.status_var = tk.StringVar(value="等待指示 | 左鍵點擊複製指令")
        status_label = tk.Label(right_panel, textvariable=self.status_var, bg="#1e1e1e", fg="#4CAF50", font=font_tuple(10))
        status_label.pack(side="bottom", fill="x", pady=(5, 0))
        
        self.canvas = tk.Canvas(right_panel, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind("<Destroy>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        self.grid_frame = tk.Frame(self.canvas, bg="#1e1e1e")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self._load_directories()
        self._load_images()
        
    def _on_gallery_closing(self):
        try:
            if hasattr(self.editor.parent, "save_window_position"):
                self.editor.parent.save_window_position("gallery_geometry", self)
        except:
            pass
        self.destroy()

    def _on_mousewheel(self, event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def _create_folder(self):
        import tkinter.simpledialog as sd
        folder_name = sd.askstring("新增資料夾", "請輸入新資料夾名稱:", parent=self)
        if folder_name:
            new_path = os.path.join(self.images_root, folder_name)
            if not os.path.exists(new_path):
                os.makedirs(new_path)
                self._load_directories()
                
    def _on_folder_select(self, event):
        selection = self.folder_listbox.curselection()
        if selection:
            item = self.folder_listbox.get(selection[0])
            if item == "全部圖片":
                self.current_folder = ""
            else:
                self.current_folder = item
            self._load_images()
            
    def _rename_image(self):
        new_name = self.rename_var.get().strip()
        if not new_name or not self.selected_image_path:
            return
        old_path = self.selected_image_path
        ext = os.path.splitext(old_path)[1]
        new_path = os.path.join(os.path.dirname(old_path), new_name + ext)
        try:
            os.rename(old_path, new_path)
            self._load_images()
            self.status_var.set(f"已重新命名為 {new_name}{ext}")
            self.selected_img_name_var.set("未選擇")
            self.rename_var.set("")
            self.selected_image_path = None
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("錯誤", f"無法重新命名: {e}")
            
    def _load_directories(self):
        self.folder_listbox.delete(0, tk.END)
        self.folder_listbox.insert(tk.END, "全部圖片")
        if os.path.exists(self.images_root):
            for item in os.listdir(self.images_root):
                item_path = os.path.join(self.images_root, item)
                if os.path.isdir(item_path):
                    self.folder_listbox.insert(tk.END, item)
                    
    def _load_images(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        target_dir = self.images_root
        if self.current_folder:
            target_dir = os.path.join(self.images_root, self.current_folder)
            
        if not os.path.exists(target_dir):
            return
            
        search_query = self.search_var.get().lower()
        files = []
        
        if self.current_folder:
            files = [os.path.join(self.current_folder, f) for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        else:
            for root, dirs, filenames in os.walk(self.images_root):
                for f in filenames:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        rel_dir = os.path.relpath(root, self.images_root)
                        if rel_dir == '.':
                            files.append(f)
                        else:
                            files.append(os.path.join(rel_dir, f))
                            
        if search_query:
            files = [f for f in files if search_query in os.path.basename(f).lower()]
            
        if not files:
            tk.Label(self.grid_frame, text="圖庫無圖片", bg="#1e1e1e", fg="#ffffff", font=font_tuple(12)).pack(pady=20)
            return
            
        col = 0
        row = 0
        max_cols = 4
        self.thumbnails = []
        
        for f in files:
            try:
                img_path = os.path.join(self.images_root, f)
                img = Image.open(img_path)
                img.thumbnail((120, 120))
                photo = ImageTk.PhotoImage(img)
                self.thumbnails.append(photo)
                
                frame = tk.Frame(self.grid_frame, bg="#2d2d2d", padx=5, pady=5, bd=1, relief="solid")
                frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                
                img_lbl = tk.Label(frame, image=photo, bg="#2d2d2d", cursor="hand2")
                img_lbl.pack()
                
                name_lbl = tk.Label(frame, text=os.path.basename(f), bg="#2d2d2d", fg="#ffffff", font=font_tuple(9), cursor="hand2")
                name_lbl.pack(pady=5)
                
                def on_click(event, fname=os.path.basename(f), fpath=img_path):
                    cmd = f">圖>{os.path.splitext(fname)[0]}, T=0s000\\n>點>{os.path.splitext(fname)[0]}, T=1s500"
                    self.clipboard_clear()
                    self.clipboard_append(cmd)
                    self.status_var.set(f"已複製: >圖>{os.path.splitext(fname)[0]}... (共2行)")
                    self.selected_img_name_var.set(fname)
                    self.selected_image_path = fpath
                    if self.auto_close_var.get():
                        self._on_gallery_closing()
                    else:
                        self.after(3000, lambda: self.status_var.set("等待指示 | 左鍵點擊複製指令"))
                
                img_lbl.bind("<Button-1>", on_click)
                name_lbl.bind("<Button-1>", on_click)
                frame.bind("<Button-1>", on_click)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            except Exception as e:
                pass
                
        for i in range(max_cols):
            self.grid_frame.grid_columnconfigure(i, weight=1)'''

# Find bounds of old ImageGalleryViewer
lines = content.split('\n')
start = -1
end = -1
for i, l in enumerate(lines):
    if 'class ImageGalleryViewer(tk.Toplevel):' in l:
        start = i
    if start != -1 and 'class ' in l and i > start:
        end = i
        break
if end == -1:
    end = len(lines)

if start != -1:
    new_content = '\n'.join(lines[:start]) + '\n' + new_gallery_code + '\n' + '\n'.join(lines[end:])
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(new_content)
    print('Fully replaced ImageGalleryViewer with 20/80 layout, folder button, and search capabilities.')
else:
    print('Could not find ImageGalleryViewer class in file')
