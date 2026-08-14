import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/recorder.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "if event['type'] == 'keyboard':" in line:
        new_lines.append(line)
        new_lines.append("            # === [防護機制] 最上層視窗驗證 ===\n")
        new_lines.append("            if self._target_hwnd and event.get('event') == 'down':\n")
        new_lines.append("                try:\n")
        new_lines.append("                    import win32gui\n")
        new_lines.append("                    current_fg = win32gui.GetForegroundWindow()\n")
        new_lines.append("                    if current_fg != self._target_hwnd:\n")
        new_lines.append("                        self.logger(f\"[防護] 目標視窗未置頂，略過按下 {event.get('name')}\")\n")
        new_lines.append("                        return\n")
        new_lines.append("                except Exception as e:\n")
        new_lines.append("                    pass\n")
        new_lines.append("            # ==================================\n")
    else:
        new_lines.append(line)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.writelines(new_lines)
print('Patch applied successfully')
