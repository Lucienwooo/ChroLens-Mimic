import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "from ttkbootstrap.constants import *" in line:
        insert_idx = i + 1
        break

new_code = """
# === 注入客製化紫黑主題 (PalServer Theme) ===
from ttkbootstrap.themes.user import USER_THEMES
USER_THEMES['pal'] = {
    'type': 'dark',
    'colors': {
        'primary': '#7a5fcf',
        'secondary': '#2c2839',
        'success': '#67ae4e',
        'info': '#8b9fe6',
        'warning': '#ffbb44',
        'danger': '#ff5577',
        'light': '#f3f0fb',
        'dark': '#201c2c',
        'bg': '#201c2c',
        'fg': '#eceaf2',
        'selectbg': '#a594e8',
        'selectfg': '#0f0c17',
        'border': '#403c52',
        'inputfg': '#eceaf2',
        'inputbg': '#2c2839',
        'active': '#a594e8'
    }
}
# ========================================
"""

lines.insert(insert_idx, new_code)

# Replace the default theme
for i, line in enumerate(lines):
    if 'skin = self.user_config.get("skin",' in line:
        lines[i] = '        skin = self.user_config.get("skin", "pal")\n'
        break

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.writelines(lines)
print('Theme patch applied successfully')
