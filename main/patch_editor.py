# -*- coding: utf-8 -*-
import codecs
import re

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. Add ttkbootstrap
if 'import ttkbootstrap as tb' not in content[:500]:
    content = content.replace('import tkinter as tk\nfrom tkinter import ttk', 'import tkinter as tk\nfrom tkinter import ttk\nimport ttkbootstrap as tb', 1)

# 2. TextCommandEditor geometry delay
old_editor_geom = '''        if not (hasattr(self.parent, "restore_window_position") and self.parent.restore_window_position("editor_geometry", self)):
            self.geometry("1405x1095")
        self.minsize(1405, 995)'''
new_editor_geom = '''        def _apply_geom():
            if not (hasattr(self.parent, "restore_window_position") and self.parent.restore_window_position("editor_geometry", self)):
                self.geometry("1405x1095")
        self.after(50, _apply_geom)
        self.minsize(1405, 995)'''
content = content.replace(old_editor_geom, new_editor_geom)

# 3. ImageGalleryViewer geometry and button
# Find ImageGalleryViewer layout
gallery_init_pattern = r'''(self\.auto_close_var = tk\.BooleanVar\(value=False\)\s+auto_close_cb = tb\.Checkbutton\(left_panel, text="[^"]+", variable=self\.auto_close_var, bootstyle="round-toggle"\)\s+auto_close_cb\.pack\(anchor="w", padx=10, pady=\(0, 10\)\))'''

button_code = r'''\1

        def _open_gallery_folder():
            import os
            if os.path.exists(self.images_root):
                os.startfile(self.images_root)
        
        open_folder_btn = tb.Button(left_panel, text="📁 圖庫資料夾", bootstyle="info", command=_open_gallery_folder)
        open_folder_btn.pack(fill="x", side="bottom", padx=10, pady=(0, 15))'''
content = re.sub(gallery_init_pattern, button_code, content)

# ImageGalleryViewer geometry delay
old_gal_geom = '''        if not (hasattr(self.editor.parent, "restore_window_position") and self.editor.parent.restore_window_position("gallery_geometry", self)): self.geometry(f"+{x}+{y}")
        self.minsize(800, 600)'''
new_gal_geom = '''        def _apply_gal_geom():
            if not (hasattr(self.editor.parent, "restore_window_position") and self.editor.parent.restore_window_position("gallery_geometry", self, "800x720")):
                self.geometry(f"800x720+{x}+{y}")
        self.after(50, _apply_gal_geom)
        self.minsize(800, 720)'''
content = content.replace(old_gal_geom, new_gal_geom)

# Images root
content = content.replace('self.images_root = os.path.join(base_dir, "images")', 'self.images_root = os.path.join(base_dir, "scripts", "images")')
content = content.replace('self.images_root = "images"', 'self.images_root = os.path.join("scripts", "images")')

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print('Done!')
