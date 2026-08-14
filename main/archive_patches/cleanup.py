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

content = content.replace('print("PAGE MENU ITEMS 1:", self.page_menu.get(0, "end"))\n', '')
content = content.replace('print("PAGE MENU ITEMS 2:", self.page_menu.get(0, "end"))\n', '')
content = content.replace('        print("PAGE MENU ITEMS 1:", self.page_menu.get(0, "end"))\n', '')
content = content.replace('        print("PAGE MENU ITEMS 2:", self.page_menu.get(0, "end"))\n', '')

with open(file_path, 'w', encoding=enc) as f:
    f.write(content)
print('Removed debug prints.')
