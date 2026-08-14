import os

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'

def try_read(enc):
    try:
        with open(file_path, 'r', encoding=enc) as f:
            return f.read(), enc
    except Exception as e:
        return None, None

content, enc = try_read('utf-8')
if not content: content, enc = try_read('cp950')
if not content: content, enc = try_read('big5')

original = '        self.page_menu.insert(3, lang_map.get("4.智慧追蹤beta", "4.智慧追蹤beta"))\n        if hasattr(self, \'playlist_frame\'):'
replaced = '            self.page_menu.insert(3, lang_map.get("4.智慧追蹤beta", "4.智慧追蹤beta"))\n        if hasattr(self, \'playlist_frame\'):'

if original in content:
    content = content.replace(original, replaced)
    with open(file_path, 'w', encoding=enc) as f:
        f.write(content)
    print("Fixed indentation.")
else:
    print("Original not found.")
