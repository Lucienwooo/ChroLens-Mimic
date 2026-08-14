import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/recorder.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def _execute_event(self, event):" in line:
        start_idx = i
        break

for i in range(start_idx, len(lines)):
    if "if event['type'] == 'keyboard':" in lines[i] and not lines[i].strip().startswith("elif"):
        insert_idx = i + 1
        break

new_code = """            # === [防護機制] 最上層視窗驗證 ===
            if self._target_hwnd and event.get('event') == 'down':
                try:
                    import win32gui
                    current_fg = win32gui.GetForegroundWindow()
                    if current_fg != self._target_hwnd:
                        self.logger(f"[防護] 目標視窗未置頂，略過按下 {event.get('name')}")
                        return
                except Exception as e:
                    pass
            # ==================================
"""
lines.insert(insert_idx, new_code)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.writelines(lines)
print('Precise patch applied successfully')
