import codecs

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# Replace _show_message to auto-close on success
old_close = """        def on_close():
            dialog.destroy()"""
new_close = """        def on_close():
            try: dialog.destroy()
            except: pass
        
        if msg_type in ["info", "success"]:
            dialog.after(1000, on_close)"""

if old_close in content:
    content = content.replace(old_close, new_close, 1)

# Ensure update_idletasks is called in save module methods
old_save_module = """            self._show_message("成功", f"模組 [{module_name}] 已儲存修改", "info")
            self._apply_syntax_highlighting_to_widget(self.module_preview)"""
new_save_module = """            self._show_message("成功", f"模組 [{module_name}] 已儲存修改", "info")
            self._apply_syntax_highlighting_to_widget(self.module_preview)
            self.update_idletasks()"""

content = content.replace(old_save_module, new_save_module)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print("text_script_editor.py UI tweaks applied!")
