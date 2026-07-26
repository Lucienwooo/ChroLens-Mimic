import re

editor_path = r'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/text_script_editor.py'

with open(editor_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace _json_to_text and _format_generic_event
json_to_text_start_marker = '    def _json_to_text(self, data: Dict) -> str:'
json_to_text_end_marker = '    def _format_time(self, seconds: float) -> str:'

start_idx = content.find(json_to_text_start_marker)
if start_idx == -1:
    raise Exception("Could not find _json_to_text start")

end_idx = content.find(json_to_text_end_marker)
if end_idx == -1:
    raise Exception("Could not find _format_time start")

new_json_to_text_section = """    def _json_to_text(self, data: Dict) -> str:
        \"\"\"將JSON事件轉換為文字指令 (v2.8 - 整合相對時間版本)\"\"\"
        events = data.get("events", [])
        lines = []
        
        if not events:
            lines.append("# 此腳本無事件\\n# 請先錄製操作或手動新增指令\\n")
            return "".join(lines)
            
        # 輔助函式：尋找下一個非跳過事件的時間戳記，用於計算相對延遲
        def get_next_active_time(start_idx):
            for j in range(start_idx + 1, len(events)):
                if not events[j].get("_skip_next"):
                    return events[j].get("time", 0.0)
            return None

        pressed_keys = {}
        
        for idx, event in enumerate(events):
            if event.get("_skip_next"): continue
            
            try:
                event_type = event.get("type")
                event_name = event.get("event")
                event_time = event.get("time", 0.0)
                
                # 尋找下一個有效事件的時間，計算當前動作後的相對延遲
                next_active_time = get_next_active_time(idx)
                if next_active_time is not None:
                    rel_delay = max(0.0, next_active_time - event_time)
                else:
                    rel_delay = event.get("_delay_after", 0.0) / 1000.0 if event.get("_delay_after") else 0.0
                
                # 對於延遲指令，其實際延遲時間已經透過 duration 執行了
                # 所以 T= 後面的相對延遲應該扣除該 delay 的 duration
                if event_type == "delay":
                    duration = event.get("duration", 0.0)
                    rel_delay = max(0.0, rel_delay - duration)
                
                time_suffix_val = self._format_time(rel_delay)
                time_suffix = f", T={time_suffix_val}"
                
                # 2. 處理當前事件指令
                if event_type == "label":
                    lines.append(f"#{event.get('name', '')}\\n")
                    continue

                if event_type == "comment":
                    lines.append(f"# {event.get('text', '')}\\n")
                    continue

                if event_type == "separator":
                    char = event.get("char", "=")
                    lines.append(f"{char * 30}\\n")
                    continue

                if event_type == "keyboard":
                    key_name = event.get("name", "")
                    is_press = event.get("_is_press", False)
                    is_release = event.get("_is_release", False)
                    auto_pair = event.get("_auto_pair", False)
                    
                    if event_name == "down":
                        if is_press:
                            lines.append(f">按下{key_name}, T={time_suffix_val}\\n")
                        elif auto_pair:
                            pressed_keys[key_name] = (event_time, rel_delay)
                        else:
                            pressed_keys[key_name] = (event_time, rel_delay)
                            lines.append(f">按下{key_name}, T={time_suffix_val}\\n")
                    elif event_name == "up":
                        if is_release:
                            lines.append(f">放開{key_name}, T={time_suffix_val}\\n")
                        elif key_name in pressed_keys:
                            press_time, p_delay = pressed_keys[key_name]
                            if next_active_time is not None:
                                key_click_rel_delay = max(0.0, next_active_time - press_time)
                            else:
                                key_click_rel_delay = 0.0
                            lines.append(f">按{key_name}, T={self._format_time(key_click_rel_delay)}\\n")
                            del pressed_keys[key_name]
                        else:
                            lines.append(f">放開{key_name}, T={time_suffix_val}\\n")
                    continue

                if event_type == "mouse":
                    x, y = event.get("x"), event.get("y")
                    
                    if event_name == "move":
                        duration = event.get("duration", 0)
                        lines.append(f">移動至({x},{y}), T={time_suffix_val}\\n")
                    elif event_name == "wheel":
                        lines.append(f">滾輪({event.get('delta', 1)}), T={time_suffix_val}\\n")
                    elif event_name == "down":
                        button = event.get("button", "left")
                        btn_name = "左鍵" if button == "left" else "右鍵" if button == "right" else "中鍵"
                        
                        next_event = events[idx + 1] if idx + 1 < len(events) else None
                        
                        # 檢查是否為「點擊」序列 (Down -> Up)
                        if (next_event and next_event.get("type") == "mouse" and 
                            next_event.get("event") == "up" and next_event.get("button") == button):
                            next_event["_skip_next"] = True
                            
                            next_active_time_after_up = None
                            for j in range(idx + 2, len(events)):
                                if not events[j].get("_skip_next"):
                                    next_active_time_after_up = events[j].get("time", 0.0)
                                    break
                            
                            if next_active_time_after_up is not None:
                                click_rel_delay = max(0.0, next_active_time_after_up - event_time)
                            else:
                                click_rel_delay = next_event.get("_delay_after", 0.0) / 1000.0 if next_event.get("_delay_after") else 0.0
                                
                            if x is not None and y is not None:
                                lines.append(f">{btn_name}點擊({x},{y}), T={self._format_time(click_rel_delay)}\\n")
                            else:
                                lines.append(f">{btn_name}點擊, T={self._format_time(click_rel_delay)}\\n")
                        else:
                            coord_str = f"({x},{y})" if x is not None else ""
                            lines.append(f">按下{btn_name}{coord_str}, T={time_suffix_val}\\n")
                    elif event_name == "up":
                        btn_name = "left" if event.get("button") == "left" else "right" if event.get("button") == "right" else "middle"
                        btn_name = "左鍵" if btn_name == "left" else "右鍵" if btn_name == "right" else "中鍵"
                        coord_str = f"({x},{y})" if x is not None else ""
                        lines.append(f">放開{btn_name}{coord_str}, T={time_suffix_val}\\n")
                    continue

                if event_type in ["click_image", "wait_image", "move_to_image", "recognize_image", "if_image_exists", "yolo_detect"]:
                    region_str = f", 範圍({event['region'][0]},{event['region'][1]},{event['region'][2]},{event['region'][3]})" if event.get("region") else ""
                    border_str = ", 邊框" if event.get("show_border") else ""
                    
                    if event_type == "click_image":
                        pic_name = event.get("image", "")
                        btn = "左鍵點擊" if event.get("button", "left") == "left" else "右鍵點擊"
                        lines.append(f">{btn}>{pic_name}{border_str}{region_str}{time_suffix}\\n")
                    elif event_type == "wait_image":
                        pic_name = event.get("image", "")
                        lines.append(f">等待圖片>{pic_name}{border_str}{region_str}{time_suffix}\\n")
                    elif event_type == "move_to_image":
                        pic_name = event.get("image", "")
                        lines.append(f">移動至>{pic_name}{border_str}{region_str}{time_suffix}\\n")
                    elif event_type == "recognize_image":
                        lines.append(f">辨識>{event.get('image', '')}{border_str}{region_str}{time_suffix}\\n")
                    elif event_type == "if_image_exists":
                        lines.append(f">if>{event.get('image', '')}{border_str}{region_str}{time_suffix}\\n")
                        if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                        if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    elif event_type == "yolo_detect":
                        cls_name = event.get('class_name', '')
                        conf = event.get('confidence', 0.5)
                        lines.append(f">辨識>AI:{cls_name}, 門檻({conf}){border_str}{region_str}{time_suffix}\\n")
                        if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                        if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    continue

                if event_type == "region_end":
                    lines.append(f">範圍結束, T={time_suffix_val}\\n")
                    continue

                if event_type == "set_variable":
                    lines.append(f">設定變數>{event.get('name', '')}, {event.get('value', 0)}, T={time_suffix_val}\\n")
                    continue

                if event_type == "variable_operation":
                    op = "加1" if event.get("operation") == "add" else "減1"
                    lines.append(f">變數{op}>{event.get('name', '')}, T={time_suffix_val}\\n")
                    continue

                if event_type == "if_variable":
                    lines.append(f">if變數>{event.get('name', '')}, {event.get('operator', '==')}, {event.get('value', 0)}, T={time_suffix_val}\\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    continue

                if event_type == "loop_start":
                    if event.get("loop_type") == "repeat":
                        max_cnt = event.get('max_count', 1)
                        cnt_str = "無限" if max_cnt == 999999 else f"{max_cnt}次"
                        lines.append(f">重複>{cnt_str}, T={time_suffix_val}\\n")
                    elif event.get("loop_type") == "while":
                        cond = event.get("condition", {})
                        if cond.get("type") == "image_exists":
                            lines.append(f">當圖片存在>{cond.get('image', '')}, T={time_suffix_val}\\n")
                        elif cond.get("type") == "image_missing":
                            lines.append(f">當圖片消失>{cond.get('image', '')}, T={time_suffix_val}\\n")
                    continue

                if event_type == "loop_end":
                    loop_name = ">重複結束" if event.get("loop_type") == "repeat" else ">迴圈結束"
                    lines.append(f"{loop_name}, T={time_suffix_val}\\n")
                    continue

                if event_type == "delay":
                    ms = int(event.get("duration", 0) * 1000)
                    if ms > 0: lines.append(f">延遲{ms}ms, T={time_suffix_val}\\n")
                    continue

                if event_type == "start_combat":
                    lines.append(f">啟動自動戰鬥, T={time_suffix_val}\\n")
                    continue

                if event_type == "ocr_auto_input":
                    lines.append(f">自動辨識輸入驗證碼, T={time_suffix_val}\\n")
                    continue

                if event_type == "ocr_input":
                    r = event.get("region", (0, 0, 0, 0))
                    x, y, w, h = r[0], r[1], r[2]-r[0], r[3]-r[1]
                    lines.append(f">OCR辨識輸入範圍({x},{y},{w},{h}), T={time_suffix_val}\\n")
                    continue

                if event_type == "ocr_relative_input":
                    anchor = event.get("anchor_text", "")
                    dx, dy, w, h = event.get("offset", (0, 0, 100, 30))
                    lines.append(f">相對OCR辨識輸入>{anchor}, 偏移({dx},{dy},{w},{h}), T={time_suffix_val}\\n")
                    continue

                if event_type == "click_text":
                    target = event.get("target_text", "")
                    off_x = event.get("offset_x", 0)
                    off_y = event.get("offset_y", 0)
                    suffix = f", 偏移({off_x},{off_y})" if (off_x != 0 or off_y != 0) else ""
                    lines.append(f">點擊文字>{target}{suffix}, T={time_suffix_val}\\n")
                    continue

                if event_type == "wait_text":
                    target = event.get("target_text", "")
                    timeout = event.get("timeout", 10.0)
                    lines.append(f">等待文字>{target}, 最長{timeout}s, T={time_suffix_val}\\n")
                    continue

                if event_type == "if_text_exists":
                    target = event.get("target_text", "")
                    lines.append(f">if文字>{target}, T={time_suffix_val}\\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    continue

                # 分支處理
                if event_type == "branch_success":
                    lines.append(f">>{self._format_branch_action(event)}\\n")
                    continue
                
                if event_type == "branch_failure":
                    lines.append(f">>>{self._format_branch_action(event)}\\n")
                    continue

                if event_type == "if_all_images_exist":
                    images_str = ",".join(event.get("images", []))
                    lines.append(f">if全部存在>{images_str}{time_suffix}\\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    continue

                if event_type == "if_any_image_exists":
                    images_str = ",".join(event.get("images", []))
                    lines.append(f">if任一存在>{images_str}{time_suffix}\\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    continue

                if event_type == "random_delay":
                    min_ms = event.get("min_ms", 0)
                    max_ms = event.get("max_ms", 0)
                    lines.append(f">隨機延遲>{self._format_time(min_ms/1000.0)},{self._format_time(max_ms/1000.0)}{time_suffix}\\n")
                    continue

                if event_type == "random_branch":
                    prob = event.get("probability", 50)
                    lines.append(f">隨機執行>{prob}%{time_suffix}\\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\\n")
                    continue

                if event_type == "random_jump":
                    labels_str = ",".join(["#" + l for l in event.get("labels", [])])
                    lines.append(f">隨機跳轉>{labels_str}{time_suffix}\\n")
                    continue

                if event_type == "counter_trigger":
                    action_id = event.get("action_id", "")
                    count = event.get("count", 0)
                    lines.append(f">計數器>{action_id}, {count}次後{time_suffix}\\n")
                    if event.get("on_trigger"): lines.append(f">>{self._format_branch_action(event['on_trigger'])}\\n")
                    continue

                if event_type == "timer_trigger":
                    action_id = event.get("action_id", "")
                    duration = event.get("duration", 0)
                    lines.append(f">計時器>{action_id}, {duration}秒後{time_suffix}\\n")
                    if event.get("on_trigger"): lines.append(f">>{self._format_branch_action(event['on_trigger'])}\\n")
                    continue

                if event_type == "reset_counter":
                    action_id = event.get("action_id", "")
                    lines.append(f">重置計數器>{action_id}{time_suffix}\\n")
                    continue

                if event_type == "reset_timer":
                    action_id = event.get("action_id", "")
                    lines.append(f">重置計時器>{action_id}{time_suffix}\\n")
                    continue

                if event_type == "delayed_start":
                    delay_seconds = event.get("delay_seconds", 0)
                    lines.append(f">開始>{delay_seconds}秒後{time_suffix}\\n")
                    continue

                if event_type == "delayed_end":
                    delay_seconds = event.get("delay_seconds", 0)
                    lines.append(f">結束>{delay_seconds}秒後{time_suffix}\\n")
                    continue

                if event_type == "set_bezier":
                    enabled = event.get("enabled", False)
                    state = "開啟" if enabled else "關閉"
                    lines.append(f">擬真滑鼠>{state}{time_suffix}\\n")
                    continue

                # 使用通用格式化
                line = self._format_generic_event(event, rel_delay)
                if line: lines.append(f">{line}\\n")

            except Exception as e:
                lines.append(f"# 轉換事件錯誤: {e}\\n")
                continue
        
        # 處理未放開的按鍵
        if pressed_keys:
            lines.append("\\n# 警告: 未放開按鍵\\n")
            for k in pressed_keys: lines.append(f"# >按下{k} (未放開)\\n")
            
        return "".join(lines)

    def _format_generic_event(self, event: dict, rel_delay: float = 0.0) -> str:
        \"\"\"
        通用格式化 (作為後備)
        用於處理未被顯式處理的事件類型
        \"\"\"
        event_type = event.get("type", "")
        time_suffix = f", T={self._format_time(rel_delay)}"
        
        if event_type == "mouse":
            evt = event.get("event")
            btn = "左鍵" if event.get("button") == "left" else "右鍵" if event.get("button") == "right" else "中鍵"
            x, y = event.get("x"), event.get("y")
            coord_str = f"({x},{y})" if x is not None else ""
            
            if evt == "down": return f"按下{btn}{coord_str}{time_suffix}"
            if evt == "up": return f"放開{btn}{coord_str}{time_suffix}"
            if evt == "move": return f"移動至{coord_str}{time_suffix}"
            if evt == "wheel": return f"滾輪({event.get('delta', 0)}){time_suffix}"
        
        elif event_type == "keyboard":
            evt = event.get("event")
            key = event.get("name", "")
            if evt == "down": return f"按下{key}{time_suffix}"
            if evt == "up": return f"放開{key}{time_suffix}"
            
        # 如果無法格式化，返回描述性字串
        return f"未知指令({event_type}){time_suffix}"

"""

content = content[:start_idx] + new_json_to_text_section + content[end_idx:]

# 2. Replace _text_to_json
text_to_json_start_marker = '    def _text_to_json(self, text: str) -> Dict:'
text_to_json_end_marker = '    def _parse_image_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:'

start_idx = content.find(text_to_json_start_marker)
if start_idx == -1:
    raise Exception("Could not find _text_to_json start")

end_idx = content.find(text_to_json_end_marker)
if end_idx == -1:
    raise Exception("Could not find _parse_image_command_to_json start")

new_text_to_json_section = """    def _text_to_json(self, text: str) -> Dict:
        \"\"\"將文字指令轉換回JSON格式 (相對時間版)\"\"\"
        # Alias System: Expand colloquial aliases first
        text = self._expand_alias_commands(text)

        import time
        lines = text.split("\\n")
        events = []
        labels = {}  # 標籤映射
        
        # 第一遍: 掃描標籤
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("#") and not line.startswith("# "):
                # 這是標籤定義
                label_name = line[1:].strip()
                labels[label_name] = i
        
        # 第二遍: 解析指令
        i = 0
        pending_label = None  # 暫存標籤,等待下一個事件的時間
        line_number = 0  # 記錄原始行號，用於保持順序
        running_time = 0.0  # 累積時間 (Running Clock)
        
        while i < len(lines):
            line = lines[i].strip()
            line_number = i  # 記錄當前行號
            
            # 處理備註（# 後有空格）
            if line.startswith("# "):
                comment_text = line[2:]  # 移除 "# " 前綴
                events.append({
                    "type": "comment",
                    "text": comment_text,
                    "time": running_time,  # 使用累積時間
                    "_line_number": line_number
                })
                i += 1
                continue
            
            # 處理分隔符號（=== 或 --- 等）- 儲存為特殊事件
            separator_match = re.match(r'^([=\\-_])\\1{2,}$', line)
            if separator_match:
                separator_char = separator_match.group(1)
                events.append({
                    "type": "separator",
                    "char": separator_char,
                    "time": running_time,  # 使用累積時間
                    "_line_number": line_number
                })
                i += 1
                continue
            
            # 跳過空行 and 僅包含空白字元的行
            if not line or line.isspace():
                i += 1
                continue
            
            # 標籤定義
            if line.startswith("#"):
                label_name = line[1:].strip()
                # 暫存標籤,使用下一個事件的時間
                pending_label = label_name
                i += 1
                continue
            
            # 解析指令
            if line.startswith(">"):
                # 處理分支指令（>> 和 >>>）
                if line.startswith(">>>"):
                    # 失敗分支
                    target_match = re.match(r'>>>#([a-zA-Z0-9_\\\\u4e00-\\\\u9fa5]+)', line)
                    if target_match:
                        target_label = target_match.group(1)
                        # 檢查是否緊接在條件判斷後
                        has_preceding_condition = False
                        for check_i in range(i-1, max(-1, i-10), -1):
                            if check_i < 0 or check_i >= len(lines):
                                break
                            prev_line = lines[check_i].strip()
                            if not prev_line or prev_line.startswith('>>'):
                                continue
                            if any(kw in prev_line for kw in ['>if>', '>辨識>', '>if文字>', '>if變數>', '>if全部存在>', '>if任一存在>', '>隨機執行>', '>計數器>', '>計時器>']):
                                has_preceding_condition = True
                                break
                            if prev_line.startswith('>') or prev_line.startswith('#'):
                                break
                        
                        if not has_preceding_condition:
                            repeat_count = 999999
                            repeat_match = re.search(r'\\\\*(\\\\d+)', line)
                            if repeat_match:
                                repeat_count = int(repeat_match.group(1))
                            
                            time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                            parsed_delay = self._parse_time(time_str)
                            
                            events.append({
                                "type": "branch_failure",
                                "target": target_label,
                                "repeat_count": repeat_count,
                                "time": running_time,
                                "_line_number": line_number,
                                "_standalone": True
                            })
                            running_time += parsed_delay
                    i += 1
                    continue
                    
                elif line.startswith(">>"):
                    # 成功分支
                    target_match = re.match(r'>>#([a-zA-Z0-9_\\\\u4e00-\\\\u9fa5]+)', line)
                    if target_match:
                        target_label = target_match.group(1)
                        has_preceding_condition = False
                        for check_i in range(i-1, max(-1, i-10), -1):
                            if check_i < 0 or check_i >= len(lines):
                                break
                            prev_line = lines[check_i].strip()
                            if not prev_line or prev_line.startswith('>>'):
                                continue
                            if any(kw in prev_line for kw in ['>if>', '>辨識>', '>if文字>', '>if變數>', '>if全部存在>', '>if任一存在>', '>隨機執行>', '>計數器>', '>計時器>']):
                                has_preceding_condition = True
                                break
                            if prev_line.startswith('>') or prev_line.startswith('#'):
                                break
                        
                        if not has_preceding_condition:
                            repeat_count = 999999
                            repeat_match = re.search(r'\\\\*(\\\\d+)', line)
                            if repeat_match:
                                repeat_count = int(repeat_match.group(1))
                            
                            time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                            parsed_delay = self._parse_time(time_str)
                            
                            events.append({
                                "type": "branch_success",
                                "target": target_label,
                                "repeat_count": repeat_count,
                                "time": running_time,
                                "_line_number": line_number,
                                "_standalone": True
                            })
                            running_time += parsed_delay
                    i += 1
                    continue
                
                # 處理 >範圍結束 指令
                if "範圍結束" in line:
                    time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                    parsed_delay = self._parse_time(time_str)
                    
                    events.append({
                        "type": "region_end",
                        "time": running_time,
                        "_line_number": line_number
                    })
                    running_time += parsed_delay
                    i += 1
                    continue
                
                try:
                    if any(keyword in line for keyword in ["啟動自動戰鬥", "尋找並攻擊", "迴圈攻擊", "智能戰鬥", "設定戰鬥區域", "暫停戰鬥", "恢復戰鬥", "停止戰鬥"]):
                        # 戰鬥指令
                        time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                        parsed_delay = self._parse_time(time_str)
                        
                        event = self._parse_combat_command_to_json(line, 0.0)
                        if event:
                            event["_line_number"] = line_number
                            event["time"] = running_time
                            
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": running_time,
                                    "_line_number": line_number - 1
                                })
                                pending_label = None
                            events.append(event)
                            running_time += parsed_delay
                        i += 1
                        continue

                    if any(keyword in line for keyword in [
                        "等待圖片", "點擊圖片", "如果存在", 
                        "辨識>", "移動至>", "左鍵點擊>", "右鍵點擊>", 
                        "如果存在>", "辨識任一>", "if>",
                        "if文字>", "等待文字>", "點擊文字>", "自動辨識輸入驗證碼",
                        "OCR辨識輸入範圍", "相對OCR辨識輸入"
                    ]):
                        line_delay_ms = 0
                        delay_match = re.search(r'(?:,\\\\s*)?延遲(\\\\d+)ms', line)
                        if delay_match:
                            line_delay_ms = int(delay_match.group(1))
                            line = line.replace(delay_match.group(0), "").strip()
                            
                        # 傳遞 0.0 作為 start_time，從而讓 returned event['time'] 剛好等於 time_suffix 中的延遲值
                        event = self._parse_image_command_to_json(line, lines[i+1:i+6], 0.0)
                        if event:
                            event["_delay_after"] = line_delay_ms
                            parsed_delay = event.get("time", 0.0)
                            event["time"] = running_time
                            event["_line_number"] = line_number
                            
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": running_time,
                                    "_line_number": line_number - 1
                                })
                                pending_label = None
                            events.append(event)
                            
                            running_time += (line_delay_ms / 1000.0) + parsed_delay
                            i += 1
                            continue
                    
                    if any(keyword in line for keyword in [
                        "設定變數>", "變數加1>", "變數減1>", "if變數>",
                        "重複>", "當圖片存在>", "當圖片消失>", "迴圈結束", "重複結束",
                        "if全部存在>", "if任一存在>",
                        "隨機延遲>", "隨機執行>",
                        "計數器>", "計時器>", "重置計數器>", "重置計時器>",
                        "開始>", "結束>",
                        "每隔>", "每隔結束",
                        "當偵測到>", "當偵測結束",
                        "優先偵測>", "優先偵測結束",
                        "並行開始", "並行結束",
                        "執行緒>", "執行緒結束",
                        "狀態機>", "狀態機結束",
                        "狀態>", "切換>"
                    ]):
                        event = self._parse_advanced_command_to_json(line, lines[i+1:], 0.0)
                        if event:
                            parsed_delay = event.get("time", 0.0)
                            event["time"] = running_time
                            event["_line_number"] = line_number
                            
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": running_time,
                                    "_line_number": line_number - 1
                                })
                                pending_label = None
                            events.append(event)
                            
                            running_time += parsed_delay
                            lines_consumed = event.get("lines_consumed", 0)
                            i += lines_consumed + 1
                            continue
                    
                    # 基本滑鼠鍵盤動作
                    line_content = line[1:]
                    protected = re.sub(r'\\\\(([^)]+)\\\\)', lambda m: f"({m.group(1).replace(',', '§')})", line_content)
                    parts_raw = protected.split(",")
                    parts = [p.replace('§', ',') for p in parts_raw]
                    
                    if len(parts) >= 1:
                        action = parts[0].strip()
                        if len(parts) == 2 and "T=" in parts[1]:
                            delay_str = "0ms"
                            time_str = parts[1].strip()
                        else:
                            delay_str = parts[1].strip() if len(parts) > 1 else "0ms"
                            time_str = parts[2].strip() if len(parts) > 2 else "T=0s000"
                        
                        parsed_delay = self._parse_time(time_str)
                        
                        if pending_label:
                            events.append({
                                "type": "label",
                                "name": pending_label,
                                "time": running_time,
                                "_line_number": line_number - 1
                            })
                            pending_label = None
                        
                        delay_ms = int(re.search(r'\\\\d+', delay_str).group()) if re.search(r'\\\\d+', delay_str) else 0
                        delay_s = delay_ms / 1000.0
                        
                        coords = re.search(r'\\\\((-?\\\\d+),(-?\\\\d+)\\\\)', action)
                        
                        # 攔截獨立等待指令
                        wait_match = re.match(r'^(?:等待|延遲)\\s*(\\\\d+)ms$', action)
                        if wait_match:
                            wait_ms = int(wait_match.group(1))
                            events.append({"type": "delay", "duration": wait_ms/1000.0, "time": running_time, "_line_number": line_number})
                            running_time += (wait_ms/1000.0) + parsed_delay
                            
                        elif ("左鍵點擊" in action or "右鍵點擊" in action or "中鍵點擊" in action) and not coords:
                            button = "right" if "右鍵" in action else "middle" if "中鍵" in action else "left"
                            events.append({"type": "mouse", "event": "down", "button": button, "x": None, "y": None, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number})
                            events.append({"type": "mouse", "event": "up", "button": button, "x": None, "y": None, "time": running_time + (delay_ms/1000.0), "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                            running_time += delay_s + parsed_delay
                        
                        elif coords:
                            x, y = int(coords.group(1)), int(coords.group(2))
                            if "移動至" in action:
                                events.append({
                                    "type": "mouse", 
                                    "event": "move", 
                                    "x": x, 
                                    "y": y, 
                                    "time": running_time, 
                                    "in_target": True, 
                                    "relative_to_window": True,
                                    "duration": delay_s,
                                    "_line_number": line_number,
                                    "_delay_after": delay_ms
                                })
                                running_time += delay_s + parsed_delay
                            elif "點擊" in action or "鍵" in action:
                                button = "right" if "右鍵" in action else "middle" if "中鍵" in action else "left"
                                if "點擊" in action:
                                    events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number})
                                    events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": running_time + (delay_ms/1000.0), "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                                elif "按下" in action:
                                    events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                                elif "放開" in action:
                                    events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                                running_time += delay_s + parsed_delay
                        
                        elif "滾輪" in action:
                            wheel_match = re.search(r'滾輪\\\\(([+-]?\\\\d+)\\\\)', action)
                            if wheel_match:
                                delta = int(wheel_match.group(1))
                                events.append({"type": "mouse", "event": "wheel", "delta": delta, "x": 0, "y": 0, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                                running_time += delay_s + parsed_delay
                        
                        elif "按下" in action:
                            key = action.replace("按下", "").strip()
                            if key in ["左鍵", "右鍵", "中鍵"]:
                                button = "left" if key == "左鍵" else "right" if key == "右鍵" else "middle"
                                events.append({"type": "mouse", "event": "down", "button": button, "x": None, "y": None, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                            else:
                                events.append({"type": "keyboard", "event": "down", "name": key, "time": running_time, "_line_number": line_number, "_is_press": True, "_press_delay": delay_ms, "_delay_after": delay_ms})
                            running_time += delay_s + parsed_delay
                        
                        elif "放開" in action:
                            key = action.replace("放開", "").strip()
                            if key in ["左鍵", "右鍵", "中鍵"]:
                                button = "left" if key == "左鍵" else "right" if key == "右鍵" else "middle"
                                events.append({"type": "mouse", "event": "up", "button": button, "x": None, "y": None, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                            else:
                                events.append({"type": "keyboard", "event": "up", "name": key, "time": running_time, "_line_number": line_number, "_is_release": True, "_delay_after": delay_ms})
                            running_time += delay_s + parsed_delay
                        
                        elif action.startswith("按") and "按下" not in action and "按鍵" not in action:
                            key = action.replace("按", "").strip()
                            events.append({"type": "keyboard", "event": "down", "name": key, "time": running_time, "_line_number": line_number, "_auto_pair": True})
                            events.append({"type": "keyboard", "event": "up", "name": key, "time": running_time + delay_s, "_line_number": line_number, "_auto_pair": True})
                            running_time += delay_s + parsed_delay
                            
                        elif action.startswith("鍵入"):
                            key = action.replace("鍵入", "").strip()
                            events.append({"type": "keyboard", "event": "down", "name": key, "time": running_time, "_line_number": line_number, "_auto_pair": True})
                            events.append({"type": "keyboard", "event": "up", "name": key, "time": running_time + delay_s, "_line_number": line_number, "_auto_pair": True})
                            running_time += delay_s + parsed_delay
                            
                        elif not any(k in action for k in ["左鍵", "右鍵", "中鍵", "滾輪", "按下", "放開"]):
                            key = action.strip()
                            if key:
                                events.append({"type": "keyboard", "event": "down", "name": key, "time": running_time, "_line_number": line_number, "_auto_pair": True})
                                events.append({"type": "keyboard", "event": "up", "name": key, "time": running_time + delay_s, "_line_number": line_number, "_auto_pair": True})
                                running_time += delay_s + parsed_delay
                
                except Exception as e:
                    print(f"解析行失敗: {line}\\n錯誤: {e}")
                    i += 1
                    continue
            
            i += 1
        
        # 按行號排序（保持原始順序），而不是按時間排序
        # 這樣可以確保標籤和條件判斷的順序不會被打亂
        events.sort(key=lambda x: x.get("_line_number", 999999))
        
        # 移除臨時的行號標記（清理）
        for event in events:
            if "_line_number" in event:
                del event["_line_number"]
        
        # 使用儲存的原始設定，而非硬編碼預設值（修復儲存時覆蓋設定的問題）
        settings = self.original_settings if self.original_settings else {
            "speed": "100",
            "repeat": "1",
            "repeat_time": "00:00:00",
            "repeat_interval": "00:00:00",
            "random_interval": False,
            "script_hotkey": "",
            "script_actions": [],
            "window_info": None
        }
        
        return {
            "events": events,
            "settings": settings
        }

"""

content = content[:start_idx] + new_text_to_json_section + content[end_idx:]

# 3. Replace _get_next_available_time
get_next_time_start_marker = '    def _get_next_available_time(self):'
get_next_time_end_marker = '    # ==================== 已棄用：舊的彈窗式自訂模組管理器 ===================='

start_idx = content.find(get_next_time_start_marker)
if start_idx == -1:
    raise Exception("Could not find _get_next_available_time start")

end_idx = content.find(get_next_time_end_marker)
if end_idx == -1:
    raise Exception("Could not find placeholder end after _get_next_available_time")

new_get_next_time_section = """    def _get_next_available_time(self):
        \"\"\"獲取下一個可用的時間戳記\"\"\"
        return "0s000"
    
"""

content = content[:start_idx] + new_get_next_time_section + content[end_idx:]

with open(editor_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Editor patching completed successfully!")
