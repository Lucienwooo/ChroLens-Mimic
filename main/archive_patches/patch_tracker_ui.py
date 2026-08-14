import sys
import codecs

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/visual_tracker_ui.py'

with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. Add import
if 'from utils import set_window_icon' not in content:
    content = content.replace('from pynput.keyboard import Controller, Key', 
                              'from pynput.keyboard import Controller, Key\nfrom utils import set_window_icon')

# 2. Add set_window_icon(self)
if 'set_window_icon(self)' not in content:
    content = content.replace('self.protocol("WM_DELETE_WINDOW", self.on_close)',
                              'self.protocol("WM_DELETE_WINDOW", self.on_close)\n        set_window_icon(self)')

# 3. Change title
content = content.replace('self.title("智慧追蹤 Beta - 全自動化控制中心")', 'self.title("智慧追蹤beta")')
content = content.replace('text="智慧追蹤 Beta (全自動化控制中心)"', 'text="智慧追蹤beta"')

# 4. Remove emojis
content = content.replace('text="▶ 基本設定與追蹤"', 'text="基本設定與追蹤"')
content = content.replace('text="⚔️ 移動與戰鬥"', 'text="移動與戰鬥"')
content = content.replace('text="💊 狀態與輔助"', 'text="狀態與輔助"')
content = content.replace('text="👁️ 進階視覺導航"', 'text="進階視覺導航"')
content = content.replace('text="▶ 開始自動化"', 'text="開始自動化"')
content = content.replace('text="⏹ 停止自動化"', 'text="停止自動化"')

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print("Patch applied successfully.")
