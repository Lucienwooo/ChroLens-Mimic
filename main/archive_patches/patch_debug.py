import os

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

original = 'self.page_menu.grid(row=0, column=0, sticky="nsew")'
replaced = 'self.page_menu.grid(row=0, column=0, sticky="nsew")\n        print("PAGE MENU ITEMS 1:", self.page_menu.get(0, "end"))'
content = content.replace(original, replaced)

original_change_lang = 'self.page_menu.insert(3, lang_map.get("4.智慧追蹤beta", "4.智慧追蹤beta"))\n        if hasattr(self, \'playlist_frame\'):'
replaced_change_lang = 'self.page_menu.insert(3, lang_map.get("4.智慧追蹤beta", "4.智慧追蹤beta"))\n        print("PAGE MENU ITEMS 2:", self.page_menu.get(0, "end"))\n        if hasattr(self, \'playlist_frame\'):'
content = content.replace(original_change_lang, replaced_change_lang)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Debug print patched.")
