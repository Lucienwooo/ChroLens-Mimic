import codecs
import re
import os

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. Fix Syntax Highlighting (ENG mode)
old_highlight = """            try:
                from modules.command_lang import COMMAND_MAP_EN
                eng_patterns = []
                for p, tag in patterns:
                    for zh, en in COMMAND_MAP_EN.items():
                        if zh in p:
                            eng_patterns.append((p.replace(zh, en), tag))
                patterns.extend(eng_patterns)
            except: pass"""

new_highlight = """            # English patterns
            eng_patterns = [
                (r'Delay\d+ms', 'syntax_delay'),
                (r'ifText>', 'syntax_ocr'),
                (r'WaitText>', 'syntax_ocr'),
                (r'ClickText>', 'syntax_ocr'),
                (r'KeyDown\w+', 'syntax_keyboard'),
                (r'KeyUp\w+', 'syntax_keyboard'),
                (r'Press(?![Down|Up])\S+', 'syntax_keyboard'),
                (r'InputText>', 'syntax_keyboard'),
                (r'MoveTo\(', 'syntax_mouse'),
                (r'LeftClick\(', 'syntax_mouse'),
                (r'RightClick\(', 'syntax_mouse'),
                (r'Scroll\(', 'syntax_mouse'),
                (r'Recognize>', 'syntax_image'),
                (r'MoveTo>', 'syntax_image'),
                (r'LeftClick>', 'syntax_image'),
                (r'RightClick>', 'syntax_image'),
            ]
            patterns.extend(eng_patterns)"""
if old_highlight in content:
    content = content.replace(old_highlight, new_highlight)

# 2. Fix Grid to Text syntax highlighting
old_save_grid = """        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", "".join(lines))"""
new_save_grid = """        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("1.0", "".join(lines))
        self._apply_syntax_highlighting_to_widget(self.text_editor)"""
if old_save_grid in content:
    content = content.replace(old_save_grid, new_save_grid)


# 3. Add _parse_line_to_data
parse_method = """    def _parse_line_to_data(self, line: str) -> dict:
        data = {"category": "空白", "sub_action": "", "target": "", "delay": 0, "timestamp": "0s000"}
        line = line.strip()
        if not line: return data
        
        if ", T=" in line:
            parts = line.split(", T=")
            line = parts[0].strip()
            data["timestamp"] = parts[1].strip()
            
        if line.startswith("#"):
            data["category"] = "註解"
            data["target"] = line[1:].strip()
            return data
            
        try:
            from modules.command_lang import translate_script_line_to_canonical
            line = translate_script_line_to_canonical(line)
        except:
            pass
            
        if line.startswith(">辨識>") or line.startswith(">圖片辨識>"):
            data["category"] = "影像辨識"
            data["sub_action"] = "圖片辨識"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">等待圖片>"):
            data["category"] = "影像辨識"
            data["sub_action"] = "等待圖片"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">點擊圖片>"):
            data["category"] = "影像辨識"
            data["sub_action"] = "點擊圖片"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">如果存在>"):
            data["category"] = "影像辨識"
            data["sub_action"] = "如果存在"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">辨識任一>"):
            data["category"] = "影像辨識"
            data["sub_action"] = "辨識任一"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">左鍵點擊") or line.startswith(">右鍵點擊") or line.startswith(">滑鼠移動") or line.startswith(">雙擊"):
            data["category"] = "滑鼠鍵盤"
            if "點擊" in line:
                data["sub_action"] = "左鍵點擊" if "左" in line else "右鍵點擊"
            elif "雙擊" in line:
                data["sub_action"] = "雙擊"
            else:
                data["sub_action"] = "滑鼠移動"
            if "(" in line:
                data["target"] = line.split("(")[1].replace(")", "")
            elif ">" in line:
                data["target"] = line.split(">")[-1]
        elif line.startswith(">按下"):
            data["category"] = "滑鼠鍵盤"
            data["sub_action"] = "按鍵按下"
            data["target"] = line.replace(">按下", "")
        elif line.startswith(">放開"):
            data["category"] = "滑鼠鍵盤"
            data["sub_action"] = "按鍵放開"
            data["target"] = line.replace(">放開", "")
        elif line.startswith(">鍵入"):
            data["category"] = "滑鼠鍵盤"
            data["sub_action"] = "鍵入"
            data["target"] = line.replace(">鍵入", "")
        elif line.startswith(">等待 "):
            data["category"] = "流程控制"
            data["sub_action"] = "延遲等待"
            ms_part = line.replace(">等待 ", "").replace("ms", "").strip()
            if ms_part.isdigit():
                data["target"] = ms_part
                data["delay"] = int(ms_part)
        elif line.startswith(">重複>"):
            data["category"] = "流程控制"
            data["sub_action"] = "重複N次"
            data["target"] = line.split(">")[-1]
        elif line == ">重複結束":
            data["category"] = "流程控制"
            data["sub_action"] = "迴圈結束"
        elif line.startswith(">新增迴圈標籤>"):
            data["category"] = "流程控制"
            data["sub_action"] = "新增迴圈標籤"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">跳轉迴圈標籤>"):
            data["category"] = "流程控制"
            data["sub_action"] = "跳轉迴圈標籤"
            data["target"] = line.split(">")[-1]
        elif line.startswith(">條件失敗跳轉>"):
            data["category"] = "流程控制"
            data["sub_action"] = "條件失敗跳轉"
            data["target"] = line.split(">")[-1]
        else:
            data["category"] = "其他指令"
            data["sub_action"] = "未分類指令"
            data["target"] = line
        return data

"""
if "def _parse_line_to_data" not in content:
    # Insert it right before _load_text_to_grid
    content = content.replace("    def _load_text_to_grid(self):", parse_method + "    def _load_text_to_grid(self):")
    
# 4. Handle "其他指令" in _save_grid_to_text
old_custom = """            elif cat == "變數系統":
                action_line = f">{sub}>{target}"
                
            if action_line:"""
new_custom = """            elif cat == "變數系統":
                action_line = f">{sub}>{target}"
            elif cat == "其他指令":
                action_line = target
                
            if action_line:"""
if old_custom in content:
    content = content.replace(old_custom, new_custom)


# 5. Fix Combobox scrolling
old_mousewheel = """    def _on_grid_mousewheel(self, event):
        # 滑鼠滾輪控制滾動
        if hasattr(self, 'grid_mode') and self.grid_mode and hasattr(self, 'grid_canvas') and self.grid_canvas.winfo_exists():
            self.grid_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")"""

new_mousewheel = """    def _on_grid_mousewheel(self, event):
        focused = self.focus_get()
        if focused and "combobox" in str(focused.winfo_class()).lower():
            return
        if hasattr(self, 'grid_mode') and self.grid_mode and hasattr(self, 'grid_canvas') and self.grid_canvas.winfo_exists():
            self.grid_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")"""

if old_mousewheel in content:
    content = content.replace(old_mousewheel, new_mousewheel)


# 6. Auto-increment image name in ScreenCaptureSelector
old_save_path = """        initial_file = "pic01.png\""""
new_save_path = """        base_name = "pic01"
        try:
            if os.path.exists("images"):
                existing = [f for f in os.listdir("images") if f.startswith("pic") and f.endswith(".png")]
                max_num = 0
                for f in existing:
                    num_str = f[3:-4]
                    if num_str.isdigit():
                        max_num = max(max_num, int(num_str))
                base_name = f"pic{max_num + 1:02d}"
        except: pass
        initial_file = f"{base_name}.png\""""
if old_save_path in content:
    content = content.replace(old_save_path, new_save_path)


# Write back
with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)

print("text_script_editor.py patched successfully!")
