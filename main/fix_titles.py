# -*- coding: utf-8 -*-
import codecs

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. Add ttkbootstrap import
if 'import ttkbootstrap as tb' not in content:
    content = content.replace('import tkinter as tk', 'import tkinter as tk\nimport ttkbootstrap as tb', 1)

# 2. Change gallery title
content = content.replace('self.title("圖庫瀏覽器")', 'self.title("圖庫")')
content = content.replace('self.title("圖片庫瀏覽器")', 'self.title("圖庫")')

# 3. Change editor title if wrong
content = content.replace('self.title("文字腳本編輯器")', 'self.title("指令編輯器")')
content = content.replace('self.title("ChroLens 指令式腳本編輯器")', 'self.title("指令編輯器")')

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print('Patched missing tb and titles successfully')
