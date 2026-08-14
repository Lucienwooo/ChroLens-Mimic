import os
import re

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
if 'from modules.visual_tracker_ui import VisualTrackerUI' not in content:
    content = content.replace('from modules.text_script_editor import TextScriptEditor', 'from modules.visual_tracker_ui import VisualTrackerUI\nfrom modules.text_script_editor import TextScriptEditor')

# 2. Add to menu 1
content = re.sub(r'(self\.page_menu\.insert\(2, lang_map\["3\.腳本編輯器beta"\]\))', r'\1\n        self.page_menu.insert(3, lang_map.get("4.智慧追蹤beta", "4.智慧追蹤beta"))', content)

# 3. Handle show_page
show_page_replacement = '''        elif idx == 2:
            self.open_visual_editor()
            self.page_menu.selection_clear(0, "end")
            self.page_menu.selection_set(0)
            self.show_page(0)
        elif idx == 3:
            if not hasattr(self, "visual_tracker_frame"):
                self.visual_tracker_frame = VisualTrackerUI(self.page_content_frame, self)
            self.visual_tracker_frame.place(relx=0, rely=0, relwidth=1, relheight=1)'''

content = re.sub(r'elif idx == 2:.*?elif idx == 3:.*?(?=def on_script_treeview_select)', show_page_replacement + '\n\n    ', content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
