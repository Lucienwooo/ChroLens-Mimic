import os
import re

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

print('Encoding used:', enc)

# Find the place where page_menu index 2 is inserted. It happens twice in the file.
content = re.sub(
    r'(self\.page_menu\.insert\(2,.*?\))(\n\s*#.*?)?\n', 
    r'\1\n        self.page_menu.insert(3, lang_map.get("4.智慧追蹤beta", "4.智慧追蹤beta"))\n', 
    content
)

with open(file_path, 'w', encoding=enc) as f:
    f.write(content)

print('Done applying regex using encoding:', enc)
