import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "self.core_recorder.events =" in line:
        insert_idx = i + 1
        break

new_code = """        # 傳遞失焦防護策略
        bg_strategy = self.user_config.get("bg_protect_strategy", "skip")
        self.core_recorder.bg_protect_strategy = bg_strategy
"""

lines.insert(insert_idx, new_code)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.writelines(lines)
print('Config patch applied successfully')
