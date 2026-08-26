import json
import re
import math
from typing import Dict, Any, List
import os

class EditorParserMixin:
    def _text_to_json(self, text: str) -> Dict:
        try:
            from modules.command_lang import translate_script_line_to_canonical
            text = "\n".join([translate_script_line_to_canonical(line) for line in text.splitlines()])
        except Exception:
            pass
        """將文字指令轉換回JSON格式 (相對時間版)"""
        # Alias System: Expand colloquial aliases first
        text = self._expand_alias_commands(text)

        import time
        lines = text.split("\n")
        events = []
        labels = {}  # 標籤映射
        
        # 第一遍: 掃描標籤
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("#") and not line.startswith("# ") and not line.startswith("#>"):
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
            
            # 處理備註（# 後有空格 或 #> 註解掉的指令）
            if line.startswith("# ") or line.startswith("#>"):
                if line.startswith("#>"):
                    comment_text = line[1:]  # 保留 >, 變成 >辨識...
                else:
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
            separator_match = re.match(r'^([=\-_])\1{2,}$', line)
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
                    target_match = re.match(r'>>>#([a-zA-Z0-9_\u4e00-\u9fa5]+)', line)
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
                            repeat_match = re.search(r'\*(\d+)', line)
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
                    target_match = re.match(r'>>#([a-zA-Z0-9_\u4e00-\u9fa5]+)', line)
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
                            repeat_match = re.search(r'\*(\d+)', line)
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
                    
                    if any(keyword in line for keyword in ["執行腳本>"]):
                        time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                        parsed_delay = self._parse_time(time_str)
                        target = line.split("執行腳本>")[1].split(",")[0].strip()
                        
                        event = {
                            "type": "RunScript",
                            "script_name": target,
                            "time": running_time,
                            "_line_number": line_number,
                            "params_list": []
                        }
                        
                        # Read ahead for >> parameters
                        j = i + 1
                        while j < len(lines):
                            next_line = lines[j].strip()
                            if next_line.startswith(">>") and not next_line.startswith(">>>") and not next_line.startswith(">>#"):
                                param_str = next_line[2:].strip()
                                if "," in param_str and "T=" in param_str:
                                    p_parts = param_str.split(", T=")
                                    param_str = p_parts[0].strip()
                                event["params_list"].append(param_str)
                                j += 1
                            else:
                                break
                        
                        i = j - 1
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
                        delay_match = re.search(r'(?:,\s*)?延遲(\d+)ms', line)
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
                    protected = re.sub(r'\(([^)]+)\)', lambda m: f"({m.group(1).replace(',', '§')})", line_content)
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
                        
                        delay_ms = int(re.search(r'\d+', delay_str).group()) if re.search(r'\d+', delay_str) else 0
                        
                        # Default click/press hold time to 50ms if not specified (or 0ms is specified)
                        # but only for compound click/press actions, not separate down/up actions.
                        is_compound_click = False
                        if "點擊" in action or (action.startswith("按") and "按下" not in action and "按鍵" not in action) or action.startswith("鍵入"):
                            is_compound_click = True
                        elif not any(k in action for k in ["左鍵", "右鍵", "中鍵", "滾輪", "按下", "放開", "移動至"]) and action.strip():
                            is_compound_click = True
                            
                        if is_compound_click and delay_ms == 0:
                            delay_ms = 50
                            
                        delay_s = delay_ms / 1000.0
                        
                        coords = re.search(r'\((-?\d+),(-?\d+)\)', action)
                        
                        # 攔截獨立等待指令
                        wait_match = re.match(r'^(?:等待|延遲)\s*(\d+)ms$', action)
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
                                # If delay_s is 0, use parsed_delay as move duration to unify formatting!
                                move_duration = delay_s if delay_s > 0 else parsed_delay
                                # If move_duration is used as duration, the extra delay after it is parsed_delay - move_duration
                                extra_delay = parsed_delay - move_duration if delay_s > 0 else 0.0
                                events.append({
                                    "type": "mouse", 
                                    "event": "move", 
                                    "x": x, 
                                    "y": y, 
                                    "time": running_time, 
                                    "in_target": True, 
                                    "relative_to_window": True,
                                    "duration": move_duration,
                                    "_line_number": line_number,
                                    "_delay_after": int(move_duration * 1000)
                                })
                                running_time += move_duration + extra_delay
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
                            wheel_match = re.search(r'滾輪\(([+-]?\d+)\)', action)
                            if wheel_match:
                                delta = int(wheel_match.group(1))
                                events.append({"type": "mouse", "event": "wheel", "delta": delta, "x": 0, "y": 0, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                                running_time += delay_s + parsed_delay
                        
                        elif "按下" in action:
                            key = action.replace("按下", "").strip()
                            if key in ["left", "right", "middle", "左鍵", "右鍵", "中鍵"]:
                                button = "left" if key in ["left", "左鍵"] else "right" if key in ["right", "右鍵"] else "middle"
                                events.append({"type": "mouse", "event": "down", "button": button, "x": None, "y": None, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                            else:
                                sub_keys = [k.strip() for k in key.split("+")] if "+" in key else [key]
                                _mods = ['ctrl', 'alt', 'shift', 'win', 'cmd']
                                sorted_keys = sorted(sub_keys, key=lambda x: not any(m in x.lower() for m in _mods))
                                for idx, sub_key in enumerate(sorted_keys):
                                    events.append({"type": "keyboard", "event": "down", "name": sub_key, "time": running_time, "_line_number": line_number, "_is_press": True, "_press_delay": delay_ms if idx==0 else 0, "_delay_after": delay_ms if idx==len(sorted_keys)-1 else 0, "_original_group": key if sub_key == sub_keys[0] else ""})
                            running_time += delay_s + parsed_delay
                        
                        elif "放開" in action:
                            key = action.replace("放開", "").strip()
                            if key in ["left", "right", "middle", "左鍵", "右鍵", "中鍵"]:
                                button = "left" if key in ["left", "左鍵"] else "right" if key in ["right", "右鍵"] else "middle"
                                events.append({"type": "mouse", "event": "up", "button": button, "x": None, "y": None, "time": running_time, "in_target": True, "relative_to_window": True, "_line_number": line_number, "_delay_after": delay_ms})
                            else:
                                sub_keys = [k.strip() for k in key.split("+")] if "+" in key else [key]
                                _mods = ['ctrl', 'alt', 'shift', 'win', 'cmd']
                                sorted_keys = sorted(sub_keys, key=lambda x: any(m in x.lower() for m in _mods))
                                for idx, sub_key in enumerate(sorted_keys):
                                    events.append({"type": "keyboard", "event": "up", "name": sub_key, "time": running_time, "_line_number": line_number, "_is_release": True, "_delay_after": delay_ms if idx==len(sorted_keys)-1 else 0, "_original_group": key if sub_key == sub_keys[0] else ""})
                            running_time += delay_s + parsed_delay
                        
                        elif action.startswith("按") and "按下" not in action and "按鍵" not in action:
                            key = action.replace("按", "").strip()
                            sub_keys = [k.strip() for k in key.split("+")] if "+" in key else [key]
                            _mods = ['ctrl', 'alt', 'shift', 'win', 'cmd']
                            down_keys = sorted(sub_keys, key=lambda x: not any(m in x.lower() for m in _mods))
                            up_keys = sorted(sub_keys, key=lambda x: any(m in x.lower() for m in _mods))
                            for idx, sub_key in enumerate(down_keys):
                                events.append({"type": "keyboard", "event": "down", "name": sub_key, "time": running_time, "_line_number": line_number, "_auto_pair": True, "_original_group": key if sub_key == sub_keys[0] else ""})
                            for idx, sub_key in enumerate(up_keys):
                                events.append({"type": "keyboard", "event": "up", "name": sub_key, "time": running_time + delay_s, "_line_number": line_number, "_auto_pair": True, "_original_group": key if sub_key == sub_keys[0] else ""})
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
                    print(f"解析行失敗: {line}\n錯誤: {e}")
                    i += 1
                    continue
            
            i += 1
        
        # 按行號排序（保持原始順序），而不是按時間排序
        # 這樣可以確保標籤 and 條件判斷的順序不會被打亂
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


    def _parse_line_to_data(self, line):
        import re
        line = line.strip()
        if not line:
            return {"category": "空白", "sub_action": "", "target": "", "delay": 0, "timestamp": "0s000"}
        if line.startswith("#"):
            return {"category": "註解", "sub_action": "", "target": line[1:].strip(), "delay": 0, "timestamp": ""}
        
        # 移除 T=... 後置並解析
        timestamp = "0s000"
        if "T=" in line:
            parts = line.split("T=")
            timestamp = parts[-1].strip()
            line = parts[0].strip()
            if line.endswith(","):
                line = line[:-1].strip()
                
        # 優先判斷是否為獨立的延遲指令，防止被通用延遲後置移除 (Bug 修復)
        standalone_delay_match = re.match(r'^>?(?:延遲|等待)\s*(\d+)ms$', line)
        if standalone_delay_match:
            delay_ms = int(standalone_delay_match.group(1))
            return {
                "category": "流程控制",
                "sub_action": "延遲等待",
                "target": str(delay_ms),
                "delay": delay_ms,
                "timestamp": timestamp
            }

        # 移除 延遲Xms 後置並解析
        delay_ms = 0
        delay_match = re.search(r'(?:,\s*)?延遲(\d+)ms', line)
        if delay_match:
            delay_ms = int(delay_match.group(1))
            line = line.replace(delay_match.group(0), "").strip()
            if line.endswith(","):
                line = line[:-1].strip()
                
        # 去除首個 > 符號
        if line.startswith(">"):
            line = line[1:].strip()
            
        # 現在解析指令動作與目標
        category = "滑鼠鍵盤"
        sub_action = ""
        target = ""
        
        # 同義詞歸一化，確保 100% 相容各式語法
        if line.startswith("移動至"):
            line = line.replace("移動至", "滑鼠移動", 1)
        elif line.startswith("點擊圖片") or line.startswith("左鍵點擊>"):
            # 如果左鍵點擊後面直接是圖片名稱，將其分類為影像辨識
            parts = line.split(">")
            if len(parts) > 1 and not ("," in parts[1] and all(p.strip().isdigit() for p in parts[1].split(","))):
                category = "影像辨識"
                sub_action = "點擊圖片"
                target = parts[1].strip()
        elif line.startswith("辨識>"):
            category = "影像辨識"
            sub_action = "圖片辨識"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("if全部存在") or line.startswith("如果全部存在"):
            category = "影像辨識"
            sub_action = "辨識任一" # 或對應多圖
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("if任一存在") or line.startswith("如果任一存在"):
            category = "影像辨識"
            sub_action = "辨識任一"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("if") or line.startswith("當圖片存在"):
            category = "影像辨識"
            sub_action = "如果存在"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("按键") or line.startswith("按鍵") or line.startswith("按"):
            # 支援 >按enter, >按鍵k 等等
            category = "滑鼠鍵盤"
            sub_action = "鍵盤按鍵"
            if ">" in line:
                target = line.split(">")[1].strip()
            else:
                for prefix in ["按鍵按键", "按鍵", "按键", "按"]:
                    if line.startswith(prefix):
                        target = line[len(prefix):].strip()
                        break

        # 流程控制
        elif line.startswith("延遲") and line.endswith("ms") and line[2:-2].isdigit():
            category = "流程控制"
            sub_action = "延遲等待"
            target = line[2:-2]
        elif line.startswith("重複結束") or line.startswith("迴圈結束"):
            category = "流程控制"
            sub_action = "迴圈結束"
        elif line.startswith("重複"):
            category = "流程控制"
            sub_action = "重複N次"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("新增迴圈標籤"):
            category = "流程控制"
            sub_action = "新增迴圈標籤"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("跳轉迴圈標籤"):
            category = "流程控制"
            sub_action = "跳轉迴圈標籤"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("條件失敗跳轉"):
            category = "流程控制"
            sub_action = "條件失敗跳轉"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
            
        # 變數系統
        elif line.startswith("設定變數"):
            category = "變數系統"
            sub_action = "設定變數"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("變數加1"):
            category = "變數系統"
            sub_action = "變數加1"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("變數減1"):
            category = "變數系統"
            sub_action = "變數減1"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif line.startswith("if變數"):
            category = "變數系統"
            sub_action = "if變數"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
            
        # 影像辨識
        elif "等待圖片" in line:
            category = "影像辨識"
            sub_action = "等待圖片"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif "點擊圖片" in line:
            category = "影像辨識"
            sub_action = "點擊圖片"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif "如果存在" in line:
            category = "影像辨識"
            sub_action = "如果存在"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif "辨識任一" in line:
            category = "影像辨識"
            sub_action = "辨識任一"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
        elif "自動辨識輸入驗證碼" in line:
            category = "影像辨識"
            sub_action = "自動辨識輸入驗證碼"
        elif "OCR辨識輸入範圍" in line:
            category = "影像辨識"
            sub_action = "OCR辨識輸入範圍"
            match = re.search(r'\((.+?)\)', line)
            target = match.group(1).strip() if match else ""
        elif "相對OCR辨識輸入" in line:
            category = "影像辨識"
            sub_action = "相對OCR辨識輸入"
            parts = line.split(">")
            target = parts[1].strip() if len(parts) > 1 else ""
            
        # 滑鼠鍵盤 (預設)
        else:
            category = "滑鼠鍵盤"
            for kw in ["左鍵點擊", "右鍵點擊", "滑鼠移動", "按下", "放開", "鍵入", "連點", "雙擊"]:
                if line.startswith(kw):
                    sub_action = kw
                    if "(" in line:
                        match = re.search(r'\((.+?)\)', line)
                        target = match.group(1).strip() if match else ""
                    elif ">" in line:
                        target = line.split(">")[1].strip()
                    else:
                        target = line[len(kw):].strip()
                    break
            if not sub_action:
                sub_action = "鍵入"
                target = line
            
            # 正規化按鍵子動作名稱，對接 Combobox 與儲存白名單
            if sub_action == "按下":
                sub_action = "按鍵按下"
            elif sub_action == "放開":
                sub_action = "按鍵放開"
            elif sub_action in ["鍵入", ""]:
                sub_action = "按鍵鍵入"
                
        return {
            "category": category,
            "sub_action": sub_action,
            "target": target,
            "delay": delay_ms,
            "timestamp": timestamp
        }

    # === 拖曳排序實作方法 ===

    def _parse_advanced_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:
        """
        解析進階指令（v2.7.1+ 新增）
        支援：變數、迴圈、多條件、隨機、計數器、計時器
        """
        # ==================== 變數系統 ====================
        
        # 設定變數：>設定變數>count, 0, T=0s000
        pattern = r'>設定變數>(.+?),\s*(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            value = match.group(2).strip()
            seconds = int(match.group(3)) if match.group(3) else 0
            millis = int(match.group(4)) if match.group(4) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 嘗試轉換為數字
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # 保持字串
            
            return {
                "type": "set_variable",
                "name": name,
                "value": value,
                "time": abs_time
            }
        
        # 變數加1：>變數加1>count, T=0s000
        pattern = r'>變數加1>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "variable_operation",
                "name": name,
                "operation": "add",
                "value": 1,
                "time": abs_time
            }
        
        # 變數減1：>變數減1>count, T=0s000
        pattern = r'>變數減1>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "variable_operation",
                "name": name,
                "operation": "subtract",
                "value": 1,
                "time": abs_time
            }
        
        # 變數條件：>if變數>count, >=, 10, T=0s000
        pattern = r'>if變數>(.+?),\s*(==|!=|>|>=|<|<=),\s*(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            name = match.group(1).strip()
            operator = match.group(2).strip()
            value = match.group(3).strip()
            seconds = int(match.group(4)) if match.group(4) else 0
            millis = int(match.group(5)) if match.group(5) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 嘗試轉換為數字
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_variable",
                "name": name,
                "operator": operator,
                "value": value,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== 迴圈控制 ====================
        
        # 重複N次：>重複>10次, T=0s000
        pattern = r'>重複>\s*(\d+)次(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            count = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "loop_start",
                "loop_type": "repeat",
                "max_count": count,
                "time": abs_time
            }
        
        # 條件迴圈（當圖片存在）：>當圖片存在>loading, T=0s000
        pattern = r'>當圖片存在>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            image = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "loop_start",
                "loop_type": "while",
                "condition": {
                    "type": "image_exists",
                    "image": image
                },
                "time": abs_time
            }
        
        # 迴圈結束：>迴圈結束, T=0s000 或 >重複結束, T=0s000
        if "迴圈結束" in command_line or "重複結束" in command_line:
            pattern = r'(?:,\s*T=(\d+)s(\d+))'
            match = re.search(pattern, command_line)
            if match:
                seconds = int(match.group(1)) if match.group(1) else 0
                millis = int(match.group(2)) if match.group(2) else 0
                abs_time = start_time + seconds + millis / 1000.0
            else:
                abs_time = start_time
            
            return {
                "type": "loop_end",
                "time": abs_time
            }
        
        # ==================== 多條件判斷 ====================
        
        # 全部圖片存在（AND）：>if全部存在>pic01,pic02,pic03, T=0s000
        pattern = r'>if全部存在>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            images_str = match.group(1).strip()
            images = [img.strip() for img in images_str.split(',')]
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_all_images_exist",
                "images": images,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 任一圖片存在（OR）：>if任一存在>pic01,pic02,pic03, T=0s000
        pattern = r'>if任一存在>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            images_str = match.group(1).strip()
            images = [img.strip() for img in images_str.split(',')]
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_any_image_exists",
                "images": images,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== 隨機功能 ====================
        
        # 隨機延遲：>隨機延遲>100ms, 500ms, T=0s000
        pattern = r'>隨機延遲>(\d+)ms,\s*(\d+)ms(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            min_ms = int(match.group(1))
            max_ms = int(match.group(2))
            seconds = int(match.group(3)) if match.group(3) else 0
            millis = int(match.group(4)) if match.group(4) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "random_delay",
                "min_ms": min_ms,
                "max_ms": max_ms,
                "time": abs_time
            }
        
        # 隨機分支：>隨機執行>30%, T=0s000
        pattern = r'>隨機執行>(\d+)%(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            probability = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "random_branch",
                "probability": probability,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 隨機跳轉：>隨機跳轉>#標籤1, #標籤2, #標籤3, T=0s000
        pattern = r'>隨機跳轉>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            labels_str = match.group(1).strip()
            # 支援帶 # 或不帶 # 的標籤名，自動過濾掉 #
            labels = [l.strip().replace('#', '') for l in labels_str.split(',')]
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "random_jump",
                "labels": labels,
                "time": abs_time
            }
        
        # YOLO 偵測：>YOLO偵測>enemy, 門檻(0.6), 範圍(0,0,100,100), T=0s000
        pattern = r'>YOLO偵測>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(pattern, command_line)
        if match:
            content = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析門檻（信心度）
            confidence = 0.5
            conf_match = re.search(r'門檻\(([\d.]+)\)', content)
            if conf_match:
                confidence = float(conf_match.group(1))
            
            # 解析範圍
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 提取物件名稱
            class_name = content
            if conf_match:
                class_name = class_name.replace(conf_match.group(0), '').strip()
            if region_match:
                class_name = class_name.replace(region_match.group(0), '').strip()
            class_name = class_name.split(',')[0].strip()
            
            # 解析成功/失敗分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            return {
                "type": "yolo_detect",
                "class_name": class_name,
                "confidence": confidence,
                "region": region,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 擬真滑鼠開關：>擬真滑鼠>開啟 
        if '>擬真滑鼠>' in command_line:
            enabled = '開啟' in command_line
            # 解析時間
            time_str = command_line.split(",")[-1].strip() if "," in command_line and "T=" in command_line else "T=0s000"
            abs_time = start_time + self._parse_time(time_str)
            
            return {
                "type": "set_bezier",
                "enabled": enabled,
                "time": abs_time
            }
        
        # 貝茲曲線移動：>貝茲移動... (如果有其他語法)
        
        # ==================== 計數器與計時器 ====================
        
        # 計數器觸發：>計數器>找圖失敗, 3次後, T=0s000
        pattern = r'>計數器>(.+?),\s*(\d+)次後(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            count = int(match.group(2))
            seconds = int(match.group(3)) if match.group(3) else 0
            millis = int(match.group(4)) if match.group(4) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            on_trigger = branches.get('success', {"action": "continue"})
            
            return {
                "type": "counter_trigger",
                "action_id": action_id,
                "count": count,
                "on_trigger": on_trigger,
                "reset_on_trigger": True,
                "time": abs_time
            }
        
        # 計時器觸發：>計時器>等待載入, 60秒後, T=0s000
        pattern = r'>計時器>(.+?),\s*(\d+)秒後(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            duration = int(match.group(2))
            seconds = int(match.group(3)) if match.group(3) else 0
            millis = int(match.group(4)) if match.group(4) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            branches = self._parse_simple_condition_branches(next_lines)
            on_trigger = branches.get('success', {"action": "continue"})
            
            return {
                "type": "timer_trigger",
                "action_id": action_id,
                "duration": duration,
                "on_trigger": on_trigger,
                "reset_on_trigger": True,
                "time": abs_time
            }
        
        # 重置計數器：>重置計數器>找圖失敗, T=0s000
        pattern = r'>重置計數器>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "reset_counter",
                "action_id": action_id,
                "time": abs_time
            }
        
        # 重置計時器：>重置計時器>等待載入, T=0s000
        pattern = r'>重置計時器>(.+?)(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            action_id = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "reset_timer",
                "action_id": action_id,
                "time": abs_time
            }
        
        # 開始：>開始>10秒後, T=0s000
        pattern = r'>開始>(\d+)秒後(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            delay_seconds = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delayed_start",
                "delay_seconds": delay_seconds,
                "time": abs_time
            }
        
        # 結束：>結束>60秒後, T=0s000
        pattern = r'>結束>(\d+)秒後(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(pattern, command_line)
        if match:
            delay_seconds = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delayed_end",
                "delay_seconds": delay_seconds,
                "time": abs_time
            }
        
        # ==================== 觸發器系統 (Trigger System) ====================
        
        # 定時觸發器開始：>每隔>30秒 或 >定時觸發>30秒
        pattern = r'>(?:每隔|定時觸發)>(\d+)(秒|分鐘|ms)'
        match = re.match(pattern, command_line)
        if match:
            interval_value = int(match.group(1))
            interval_unit = match.group(2)
            
            # 轉換為毫秒
            if interval_unit == '秒':
                interval_ms = interval_value * 1000
            elif interval_unit == '分鐘':
                interval_ms = interval_value * 60 * 1000
            else:  # ms
                interval_ms = interval_value
            
            # 收集觸發器內的動作（直到 >每隔結束 或 >定時結束）
            trigger_actions = []
            lines_consumed = 0
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                if stripped == '>每隔結束' or stripped == '>定時結束':
                    break
                if stripped and not stripped.startswith('#'):
                    trigger_actions.append(stripped)
            
            return {
                "type": "interval_trigger",
                "interval_ms": interval_ms,
                "actions": trigger_actions,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # 條件觸發器：>當偵測到>圖片名稱 或 >條件觸發>圖片名稱, 冷卻N秒
        pattern = r'>(?:當偵測到|條件觸發)>(.+?)(?:,\s*冷卻(\d+)(秒|ms))?$'
        match = re.match(pattern, command_line)
        if match:
            target = match.group(1).strip()
            cooldown_value = int(match.group(2)) if match.group(2) else 5
            cooldown_unit = match.group(3) if match.group(3) else '秒'
            
            # 轉換為毫秒
            if cooldown_unit == '秒':
                cooldown_ms = cooldown_value * 1000
            else:
                cooldown_ms = cooldown_value
            
            # 收集觸發器內的動作（直到 >當偵測結束 或 >條件結束）
            trigger_actions = []
            lines_consumed = 0
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                if stripped == '>當偵測結束' or stripped == '>條件結束':
                    break
                if stripped and not stripped.startswith('#'):
                    trigger_actions.append(stripped)
            
            return {
                "type": "condition_trigger",
                "target": target,
                "cooldown_ms": cooldown_ms,
                "actions": trigger_actions,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # 優先觸發器：>優先偵測>圖片名稱
        pattern = r'>優先偵測>(.+?)$'
        match = re.match(pattern, command_line)
        if match:
            target = match.group(1).strip()
            
            # 收集觸發器內的動作（直到 >優先偵測結束）
            trigger_actions = []
            lines_consumed = 0
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                if stripped == '>優先偵測結束':
                    break
                if stripped and not stripped.startswith('#'):
                    trigger_actions.append(stripped)
            
            return {
                "type": "priority_trigger",
                "target": target,
                "actions": trigger_actions,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # ==================== 並行區塊 (Parallel Blocks) ====================
        
        # 並行開始：>並行開始
        if command_line == '>並行開始':
            # 收集所有執行緒（直到 >並行結束）
            threads = []
            current_thread = None
            lines_consumed = 0
            
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                
                if stripped == '>並行結束':
                    # 儲存最後一個執行緒
                    if current_thread:
                        threads.append(current_thread)
                    break
                elif stripped.startswith('>執行緒>'):
                    # 儲存前一個執行緒
                    if current_thread:
                        threads.append(current_thread)
                    # 開始新執行緒
                    thread_name = stripped[4:].strip()
                    current_thread = {
                        "name": thread_name,
                        "actions": []
                    }
                elif stripped == '>執行緒結束':
                    # 儲存當前執行緒
                    if current_thread:
                        threads.append(current_thread)
                        current_thread = None
                elif stripped and current_thread is not None:
                    # 添加動作到當前執行緒
                    current_thread["actions"].append(stripped)
            
            return {
                "type": "parallel_block",
                "threads": threads,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        # ==================== 狀態機模式 (State Machine) ====================
        
        # 狀態機開始：>狀態機>戰鬥AI
        if command_line.startswith('>狀態機>'):
            machine_name = command_line[5:].strip()
            
            # 收集所有狀態（直到 >狀態機結束）
            states = {}
            current_state = None
            initial_state = None
            lines_consumed = 0
            
            for next_line in next_lines:
                stripped = next_line.strip()
                lines_consumed += 1
                
                if stripped == '>狀態機結束':
                    # 儲存最後一個狀態
                    if current_state:
                        states[current_state["name"]] = current_state
                    break
                elif stripped.startswith('>狀態>'):
                    # 儲存前一個狀態
                    if current_state:
                        states[current_state["name"]] = current_state
                    
                    # 解析狀態名稱和屬性
                    state_def = stripped[4:].strip()
                    is_initial = False
                    
                    # 檢查是否為初始狀態
                    if ', 初始' in state_def or ',初始' in state_def:
                        is_initial = True
                        state_def = state_def.replace(', 初始', '').replace(',初始', '').strip()
                    
                    state_name = state_def
                    current_state = {
                        "name": state_name,
                        "actions": [],
                        "transitions": {}
                    }
                    
                    if is_initial:
                        initial_state = state_name
                        
                elif stripped.startswith('>切換>') and current_state:
                    # 狀態切換指令
                    target_state = stripped[4:].strip()
                    current_state["transitions"]["default"] = target_state
                    current_state["actions"].append(stripped)
                elif stripped.startswith('>>切換>') and current_state:
                    # 成功時切換
                    target_state = stripped[5:].strip()
                    current_state["transitions"]["success"] = target_state
                    current_state["actions"].append(stripped)
                elif stripped.startswith('>>>切換>') and current_state:
                    # 失敗時切換
                    target_state = stripped[6:].strip()
                    current_state["transitions"]["failure"] = target_state
                    current_state["actions"].append(stripped)
                elif stripped and current_state is not None:
                    # 添加動作到當前狀態
                    current_state["actions"].append(stripped)
            
            # 如果沒有指定初始狀態，使用第一個定義的狀態
            if not initial_state and states:
                initial_state = list(states.keys())[0]
            
            return {
                "type": "state_machine",
                "name": machine_name,
                "states": states,
                "initial_state": initial_state,
                "lines_consumed": lines_consumed,
                "time": start_time
            }
        
        return None
    

    def _parse_image_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:
        """
        解析圖片指令並轉換為JSON格式
        :param command_line: 圖片指令行
        :param next_lines: 後續行 (用於讀取分支)
        :param start_time: 起始時間戳
        :return: JSON事件字典
        """
        # 自動搜尋驗證碼指令 (v2.8.7+)
        # 格式: >自動辨識輸入驗證碼, T=0s000
        auto_ocr_pattern = r'>自動辨識輸入驗證碼(?:,\s*T=([\w\d]+))?$$'
        match = re.match(auto_ocr_pattern, command_line)
        if match:
            time_str = match.group(1) if match.group(1) else "0s000"
            abs_time = start_time + self._parse_time(time_str)
            return {
                "type": "ocr_auto_input",
                "time": abs_time
            }

        # OCR 辨識輸入指令 (v2.8.5+)
        # 格式: >OCR辨識輸入範圍(x,y,w,h), T=0s000
        # OCR 辨識輸入指令 (v2.8.5+)
        # 格式: >OCR辨識輸入範圍(x,y,w,h), T=0s000
        ocr_input_pattern = r'>OCR辨識輸入範圍\((\d+),(\d+),(\d+),(\d+)\)(?:,\s*(\d+)秒後輸入)?(?:,\s*T=([\w\d]+))?$$'
        match = re.match(ocr_input_pattern, command_line)
        if match:
            x, y, w, h = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
            input_delay = int(match.group(5)) if match.group(5) else 0
            time_str = match.group(6) if match.group(6) else "0s000"
            abs_time = start_time + self._parse_time(time_str)

            return {
                "type": "ocr_input",
                "region": (x, y, x + w, y + h),
                "input_delay": input_delay,
                "time": abs_time
            }

        # 相對 OCR 指令 (v2.8.6+)
        # 格式: >相對OCR辨識輸入>錨點, 偏移(dx,dy,w,h), T=0s000
        # 相對 OCR 指令 (v2.8.6+)
        # 格式: >相對OCR辨識輸入>錨點, 偏移(dx,dy,w,h), T=0s000
        rel_ocr_pattern = r'>相對OCR辨識輸入>(.+?),\s*偏移\((\d+),(\d+),(\d+),(\d+)\)(?:,\s*T=([\w\d]+))?$$'
        match = re.match(rel_ocr_pattern, command_line)
        if match:
            anchor = match.group(1).strip()
            is_image = anchor.startswith('圖片:')
            if is_image: anchor = anchor[3:].strip()
            
            dx, dy, w, h = int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))
            time_str = match.group(6) if match.group(6) else "0s000"
            abs_time = start_time + self._parse_time(time_str)
            
            return {
                "type": "ocr_relative_input",
                "anchor_text": anchor,
                "is_image_anchor": is_image,
                "offset": (dx, dy, w, h),
                "time": abs_time
            }

        # 辨識圖片指令（新格式：>辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s100）
        # 圖片辨識指令（>辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s000）
        recognize_pattern = r'>辨識>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(recognize_pattern, command_line)
        if match:
            # 分離圖片名稱和選項
            content = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項（邊框、範圍）
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            # 強降：只取第一個逗點前的部分作為圖片名稱
            pic_name = pic_name.split(',')[0].strip()
            # 強力清理：移除多餘空白
            pic_name = re.sub(r'\s+', '', pic_name).strip()
            
            #  v2.8.3+: 支援 AI 標註 (AI:name)
            is_ai = pic_name.startswith('AI:')
            if is_ai:
                class_name = pic_name[3:]
                # 解析門檻 (從 content 中找，如果沒有則用預設 0.5)
                confidence = 0.5
                conf_match = re.search(r'門檻\(([\d.]+)\)', content)
                if conf_match:
                    confidence = float(conf_match.group(1))
                
                # 解析成功/失敗分支
                branches = self._parse_simple_condition_branches(next_lines)
                
                return {
                    "type": "yolo_detect",
                    "class_name": class_name,
                    "confidence": confidence,
                    "region": region,
                    "on_success": branches.get('success'),
                    "on_failure": branches.get('failure'),
                    "time": abs_time
                }
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 檢查後續行是否有分支（>> 或 >>>）
            branches = self._parse_simple_condition_branches(next_lines)
            
            # 如果有分支，則視為條件判斷
            if branches.get('success') or branches.get('failure'):
                result = {
                    "type": "if_image_exists",
                    "image": pic_name,
                    "image_file": image_file,
                    "confidence": 0.7,
                    "on_success": branches.get('success'),
                    "on_failure": branches.get('failure'),
                    "time": abs_time,
                    "is_pure_recognize": False  #  標記不是純辨識
                }
                if show_border:
                    result["show_border"] = True
                if region:
                    result["region"] = region
                return result
            
            # 否則視為普通辨識指令
            result = {
                "type": "recognize_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "time": abs_time,
                "is_pure_recognize": True  #  標記為純辨識，不是條件判斷
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result

        # 移動至圖片指令（>移動至>pic01, 邊框, 範圍(x1,y1,x2,y2), T=1s000）
        move_pattern = r'>移動至>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(move_pattern, command_line)
        if match:
            content = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            # 強降：取第一個逗點前的內容，確保檔名乾淨
            pic_name = pic_name.split(',')[0].strip()
            pic_name = pic_name.rstrip(',').strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            result = {
                "type": "move_to_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result
        
        # 點擊圖片指令（>左鍵點擊>pic01 或 >點擊圖片>pic01）
        click_pattern = r'>(?:(左鍵|右鍵)點擊|點擊圖片)>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(click_pattern, command_line)
        if match:
            button = "right" if match.group(1) == "右鍵" else "left"
            content = match.group(2).strip()
            seconds = int(match.group(3)) if match.group(3) else 0
            millis = int(match.group(4)) if match.group(4) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            #  新增：解析點擊半徑和模式
            click_radius = 0
            click_offset_mode = 'center'
            radius_match = re.search(r'半徑\((\d+)\)', content)
            if radius_match:
                click_radius = int(radius_match.group(1))
            if '隨機' in content:
                click_offset_mode = 'random'
            elif '追蹤' in content:
                click_offset_mode = 'tracking'
            
            #  新增：解析返回原位選項
            return_to_origin = '返回' in content
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            if radius_match:
                pic_name = pic_name.replace(radius_match.group(0), '').strip()
            if '隨機' in pic_name:
                pic_name = pic_name.replace('隨機', '').strip()
            if '追蹤' in pic_name:
                pic_name = pic_name.replace('追蹤', '').strip()
            if '返回' in pic_name:
                pic_name = pic_name.replace('返回', '').strip()
            #  新增：先取第一個逗點前的部分作為圖片名稱，防範延遲參數被黏入 (Bug 修復)
            pic_name = pic_name.split(',')[0].strip()
            
            #  強力清理：移除所有逗點和多餘空白
            pic_name = re.sub(r'[,\s]+', '', pic_name).strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            result = {
                "type": "click_image",
                "button": button,
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "return_to_origin": return_to_origin,  #  使用解析的值
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            #  新增：點擊半徑和模式
            if click_radius > 0:
                result["click_radius"] = click_radius
                result["click_offset_mode"] = click_offset_mode
            return result        # 等待圖片指令（>等待圖片>pic01, 逾時(10s), 步長(500ms), T=1s500）
        wait_pic_pattern = r'>等待圖片>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(wait_pic_pattern, command_line)
        if match:
            content = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            #  新增：限制僅取第一個逗點前的內容 (Bug 修復)
            pic_name = pic_name.split(',')[0].strip()
            pic_name = pic_name.rstrip(',').strip()

            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)

            # 解析逾時和步長
            timeout = 10.0 # 預設10秒
            step = 0.5 # 預設0.5秒
            wait_t_match = re.search(r'等待T=(\d+)s(\d+)', content)
            if wait_t_match:
                sec = int(wait_t_match.group(1))
                ms = int(wait_t_match.group(2))
                timeout = 999999.0 if (sec == 0 and ms == 0) else float(sec) + float(ms) / 1000.0
            elif '直到出現' in content or '無限等待' in content:
                timeout = 999999.0
            else:
                timeout_match = re.search(r'逾時\((\d+(?:\.\d+)?)[sS]\)', content) or re.search(r'最長(\d+(?:\.\d+)?)[sS]', content)
                if timeout_match:
                    timeout = float(timeout_match.group(1))
            step_match = re.search(r'步長\((\d+)ms\)', content)
            if step_match:
                step = int(step_match.group(1)) / 1000.0

            result = {
                "type": "wait_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "timeout": timeout,
                "step": step,
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result

        # 新格式條件判斷：>if>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s100
        if_simple_pattern = r'>if>(?:辨識>)?(.+?)(?:,\s*T=(\d+)s(\d+))?$' # Made T optional
        match = re.match(if_simple_pattern, command_line)
        if match:
            content = match.group(1).strip()
            seconds = int(match.group(2)) if match.group(2) else 0 # Added check
            millis = int(match.group(3)) if match.group(3) else 0 # Added check
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in content
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', content)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 移除選項後取得圖片名稱
            pic_name = content
            if '邊框' in pic_name:
                pic_name = pic_name.replace('邊框', '').strip()
            if region_match:
                pic_name = pic_name.replace(region_match.group(0), '').strip()
            #  新增：限制僅取第一個逗點前的內容 (Bug 修復)
            pic_name = pic_name.split(',')[0].strip()
            pic_name = pic_name.rstrip(',').strip()
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 解析後續行的 >> 和 >>> 分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            # >if> 指令預期有分支，如果沒有則添加預設值
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            result = {
                "type": "if_image_exists",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result
        
        # 新增：如果存在圖片（條件判斷）>如果存在>pic01, T=0s100
        if_exists_pattern = r'>如果存在>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(if_exists_pattern, command_line)
        if match:
            pic_name = match.group(1).strip().rstrip(',').strip()
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 解析後續行的成功/失敗分支
            branches = self._parse_condition_branches(next_lines)
            
            return {
                "type": "if_image_exists",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== OCR 文字辨識指令 ====================
        
        # OCR 條件判斷：>if文字>確認, T=0s000
        ocr_if_pattern = r'>if文字>(.+?)(?:,\s*T=([\w\d]+))?$$'
        match = re.match(ocr_if_pattern, command_line)
        if match:
            target_text = match.group(1).strip()
            time_str = match.group(2) if match.group(2) else "0s000"
            abs_time = start_time + self._parse_time(time_str)
            
            # 解析後續行的 >> 和 >>> 分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            # 預設分支
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_text_exists",
                "target_text": target_text,
                "timeout": 10.0,  # 預設等待10秒
                "match_mode": "contains",  # contains/exact/regex
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 等待文字出現：>等待文字>確認, 最長10s, T=0s000
        ocr_wait_pattern = r'>等待文字>(.+?)(?:,\s*最長(\d+(?:\.\d+)?)[sS])?(?:,\s*T=([\w\d]+))?$$'
        match = re.match(ocr_wait_pattern, command_line)
        if match:
            target_text = match.group(1).strip()
            timeout = float(match.group(2)) if match.group(2) else 10.0
            time_str = match.group(3) if match.group(3) else "0s000"
            abs_time = start_time + self._parse_time(time_str)
            
            return {
                "type": "wait_text",
                "target_text": target_text,
                "timeout": timeout,
                "match_mode": "contains",
                "time": abs_time
            }
        
        # 點擊文字位置：>點擊文字>登入, 偏移(x,y), T=0s000
        ocr_click_pattern = r'>點擊文字>(.+?)(?:,\s*偏移\((\d+),(\d+)\))?(?:,\s*T=([\w\d]+))?$$'
        match = re.match(ocr_click_pattern, command_line)
        if match:
            target = match.group(1).strip()
            is_image = target.startswith('圖片:')
            if is_image: target = target[3:].strip()
            
            off_x = int(match.group(2)) if match.group(2) else 0
            off_y = int(match.group(3)) if match.group(3) else 0
            time_str = match.group(4) if match.group(4) else "0s000"
            abs_time = start_time + self._parse_time(time_str)
            
            return {
                "type": "click_image_anchor" if is_image else "click_text",
                "target_text": target,
                "image": target if is_image else None,
                "offset_x": off_x,
                "offset_y": off_y,
                "timeout": 5.0,
                "time": abs_time
            }
        
        # 延遲指令：>延遲1000ms, T=0s000
        delay_pattern = r'>延遲(\d+)ms(?:,\s*T=(\d+)s(\d+))?$'
        match = re.match(delay_pattern, command_line)
        if match:
            delay_ms = int(match.group(1))
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delay",
                "duration": delay_ms / 1000.0,  # 轉為秒
                "time": abs_time
            }
        
        # 新增：辨識任一圖片（多圖同時辨識）>辨識任一>pic01|pic02|pic03, T=0s100
        recognize_any_pattern = r'>辨識任一>(.+?)(?:,\s*T=(\d+)s(\d+))?$$'
        match = re.match(recognize_any_pattern, command_line)
        if match:
            pic_names = match.group(1).strip().split('|')
            seconds = int(match.group(2)) if match.group(2) else 0
            millis = int(match.group(3)) if match.group(3) else 0
            abs_time = start_time + seconds + millis / 1000.0
            
            # 為每張圖片建立配置
            images = []
            for pic_name in pic_names:
                pic_name = pic_name.strip()
                images.append({
                    'name': pic_name,
                    'action': 'click',  # 預設點擊
                    'button': 'left',
                    'return_to_origin': True
                })
            
            return {
                "type": "recognize_any",
                "images": images,
                "confidence": 0.75,
                "timeout": 10,  # 預設10秒逾時
                "time": abs_time
            }
        
        event = {"time": start_time}
        
        # 等待圖片
        wait_pattern = r'>等待圖片\[([^\]]+)\],?\s*逾時(\d+(?:\.\d+)?)[sS]?'
        match = re.match(wait_pattern, command_line)
        if match:
            event["type"] = "wait_image"
            event["image"] = match.group(1)
            event["timeout"] = float(match.group(2))
            event["confidence"] = 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 點擊圖片
        click_pattern = r'>點擊圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(click_pattern, command_line)
        if match:
            event["type"] = "click_image"
            event["image"] = match.group(1)
            event["confidence"] = float(match.group(2)) if match.group(2) else 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 移動到圖片（新增）
        move_pattern = r'>移動到圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(move_pattern, command_line)
        if match:
            event["type"] = "move_to_image"
            event["image"] = match.group(1)
            event["confidence"] = float(match.group(2)) if match.group(2) else 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 條件判斷
        exists_pattern = r'>如果存在\[([^\]]+)\]'
        match = re.match(exists_pattern, command_line)
        if match:
            event["type"] = "if_exists"
            event["image"] = match.group(1)
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 如果所有模式都不匹配,返回 None
        return None
    

    def _json_to_text(self, data: Dict) -> str:
        """將JSON事件轉換為文字指令 (v2.8 - 整合相對時間版本)"""
        events = data.get("events", [])
        lines = []
        
        if not events:
            lines.append("# 此腳本無事件\n# 請先錄製操作或手動新增指令\n")
            return "".join(lines)
            
        # 輔助函式：尋找下一個非跳過事件的時間戳記，用於計算相對延遲
        def get_next_active_time(start_idx):
            start_event = events[start_idx]
            for j in range(start_idx + 1, len(events)):
                if not events[j].get("_skip_next"):
                    # 避免同一個組合鍵的子按鍵互相計算時間導致 T=0
                    if (events[j].get("type") == "keyboard" and 
                        start_event.get("type") == "keyboard" and 
                        events[j].get("time") == start_event.get("time")):
                        continue
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
                    rel_delay = 0.0
                
                # 對於延遲指令，其實際延遲時間已經透過 duration 執行了
                # 所以 T= 後面的相對延遲應該扣除該 delay 的 duration
                if event_type == "delay":
                    duration = event.get("duration", 0.0)
                    rel_delay = max(0.0, rel_delay - duration)
                
                time_suffix_val = self._format_time(rel_delay)
                time_suffix = f", T={time_suffix_val}"
                
                # 2. 處理當前事件指令
                if event_type == "label":
                    lines.append(f"#{event.get('name', '')}\n")
                    continue

                if event_type == "comment":
                    lines.append(f"# {event.get('text', '')}\n")
                    continue

                if event_type == "separator":
                    char = event.get("char", "=")
                    lines.append(f"{char * 30}\n")
                    continue

                if event_type == "keyboard":
                    key_name = event.get("name", "")
                    is_press = event.get("_is_press", False)
                    is_release = event.get("_is_release", False)
                    auto_pair = event.get("_auto_pair", False)
                    
                    orig_group = event.get("_original_group")
                    if orig_group is not None:
                        if orig_group == "":
                            if auto_pair and event_name == "down":
                                pressed_keys[key_name] = (event_time, rel_delay)
                            elif auto_pair and event_name == "up" and key_name in pressed_keys:
                                del pressed_keys[key_name]
                            continue
                        else:
                            key_name = orig_group
                    
                    if event_name == "down":
                        if is_press:
                            press_delay_ms = event.get("_press_delay", 0)
                            if press_delay_ms > 0:
                                lines.append(f">按下{key_name}, 延遲{press_delay_ms}ms, T={time_suffix_val}\n")
                            else:
                                lines.append(f">按下{key_name}, T={time_suffix_val}\n")
                        elif auto_pair:
                            pressed_keys[key_name] = (event_time, rel_delay)
                        else:
                            pressed_keys[key_name] = (event_time, rel_delay)
                            lines.append(f">按下{key_name}, T={time_suffix_val}\n")
                    elif event_name == "up":
                        if is_release:
                            lines.append(f">放開{key_name}, T={time_suffix_val}\n")
                        elif key_name in pressed_keys:
                            press_time, p_delay = pressed_keys[key_name]
                            key_duration = max(0.0, event_time - press_time)
                            key_duration_ms = round(key_duration * 1000)
                            
                            if next_active_time is not None:
                                key_click_rel_delay = max(0.0, next_active_time - press_time - key_duration)
                            else:
                                key_click_rel_delay = 0.0
                                
                            if key_duration_ms != 50:
                                delay_part = f", 延遲{key_duration_ms}ms"
                            else:
                                delay_part = ""
                                
                            lines.append(f">按{key_name}{delay_part}, T={self._format_time(key_click_rel_delay)}\n")
                            del pressed_keys[key_name]
                        else:
                            lines.append(f">放開{key_name}, T={time_suffix_val}\n")
                    continue

                if event_type == "mouse":
                    x, y = event.get("x"), event.get("y")
                    
                    if event_name == "move":
                        duration = event.get("duration", 0)
                        duration_ms = round(duration * 1000)
                        move_rel_delay = max(0.0, rel_delay - duration)
                        if duration_ms > 0 and move_rel_delay > 0:
                            lines.append(f">移動至({x},{y}), 延遲{duration_ms}ms, T={self._format_time(move_rel_delay)}\n")
                        else:
                            lines.append(f">移動至({x},{y}), T={self._format_time(rel_delay)}\n")
                    elif event_name == "wheel":
                        lines.append(f">滾輪({event.get('delta', 1)}), T={time_suffix_val}\n")
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
                            
                            click_duration = max(0.0, next_event.get("time", 0.0) - event_time)
                            click_duration_ms = round(click_duration * 1000)
                            
                            if next_active_time_after_up is not None:
                                click_rel_delay = max(0.0, next_active_time_after_up - event_time - click_duration)
                            else:
                                click_rel_delay = 0.0
                                
                            if click_duration_ms != 50:
                                delay_part = f", 延遲{click_duration_ms}ms"
                            else:
                                delay_part = ""
                                
                            if x is not None and y is not None:
                                lines.append(f">{btn_name}點擊({x},{y}){delay_part}, T={self._format_time(click_rel_delay)}\n")
                            else:
                                lines.append(f">{btn_name}點擊{delay_part}, T={self._format_time(click_rel_delay)}\n")
                        else:
                            coord_str = f"({x},{y})" if x is not None else ""
                            lines.append(f">按下{btn_name}{coord_str}, T={time_suffix_val}\n")
                    elif event_name == "up":
                        btn_name = "left" if event.get("button") == "left" else "right" if event.get("button") == "right" else "middle"
                        btn_name = "左鍵" if btn_name == "left" else "右鍵" if btn_name == "right" else "中鍵"
                        coord_str = f"({x},{y})" if x is not None else ""
                        lines.append(f">放開{btn_name}{coord_str}, T={time_suffix_val}\n")
                    continue

                if event_type in ["click_image", "wait_image", "move_to_image", "recognize_image", "if_image_exists", "yolo_detect"]:
                    region_str = f", 範圍({event['region'][0]},{event['region'][1]},{event['region'][2]},{event['region'][3]})" if event.get("region") else ""
                    border_str = ", 邊框" if event.get("show_border") else ""
                    
                    if event_type == "click_image":
                        pic_name = event.get("image", "")
                        btn = "左鍵點擊" if event.get("button", "left") == "left" else "右鍵點擊"
                        lines.append(f">{btn}>{pic_name}{border_str}{region_str}{time_suffix}\n")
                    elif event_type == "wait_image":
                        pic_name = event.get("image", "")
                        timeout = event.get("timeout", 10.0)
                        timeout_str = ", 等待T=0s000" if timeout >= 999999.0 else (f", 等待T={int(timeout)}s{int((timeout-int(timeout))*1000):03d}" if timeout != 10.0 else "")
                        lines.append(f">等待圖片>{pic_name}{border_str}{region_str}{timeout_str}{time_suffix}\n")
                    elif event_type == "move_to_image":
                        pic_name = event.get("image", "")
                        lines.append(f">移動至>{pic_name}{border_str}{region_str}{time_suffix}\n")
                    elif event_type == "recognize_image":
                        lines.append(f">辨識>{event.get('image', '')}{border_str}{region_str}{time_suffix}\n")
                    elif event_type == "if_image_exists":
                        lines.append(f">if>辨識>{event.get('image', '')}{border_str}{region_str}{time_suffix}\n")
                        if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                        if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    elif event_type == "yolo_detect":
                        cls_name = event.get('class_name', '')
                        conf = event.get('confidence', 0.5)
                        lines.append(f">辨識>AI:{cls_name}, 門檻({conf}){border_str}{region_str}{time_suffix}\n")
                        if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                        if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    continue

                if event_type == "region_end":
                    lines.append(f">範圍結束, T={time_suffix_val}\n")
                    continue

                if event_type == "set_variable":
                    lines.append(f">設定變數>{event.get('name', '')}, {event.get('value', 0)}, T={time_suffix_val}\n")
                    continue

                if event_type == "variable_operation":
                    op = "加1" if event.get("operation") == "add" else "減1"
                    lines.append(f">變數{op}>{event.get('name', '')}, T={time_suffix_val}\n")
                    continue

                if event_type == "if_variable":
                    lines.append(f">if變數>{event.get('name', '')}, {event.get('operator', '==')}, {event.get('value', 0)}, T={time_suffix_val}\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    continue

                if event_type == "loop_start":
                    if event.get("loop_type") == "repeat":
                        max_cnt = event.get('max_count', 1)
                        cnt_str = "無限" if max_cnt == 999999 else f"{max_cnt}次"
                        lines.append(f">重複>{cnt_str}, T={time_suffix_val}\n")
                    elif event.get("loop_type") == "while":
                        cond = event.get("condition", {})
                        if cond.get("type") == "image_exists":
                            lines.append(f">當圖片存在>{cond.get('image', '')}, T={time_suffix_val}\n")
                        elif cond.get("type") == "image_missing":
                            lines.append(f">當圖片消失>{cond.get('image', '')}, T={time_suffix_val}\n")
                    continue

                if event_type == "loop_end":
                    loop_name = ">重複結束" if event.get("loop_type") == "repeat" else ">迴圈結束"
                    lines.append(f"{loop_name}, T={time_suffix_val}\n")
                    continue

                if event_type == "delay":
                    ms = int(event.get("duration", 0) * 1000)
                    if ms > 0: lines.append(f">延遲{ms}ms, T={time_suffix_val}\n")
                    continue

                if event_type == "start_combat":
                    lines.append(f">啟動自動戰鬥, T={time_suffix_val}\n")
                    continue

                if event_type == "ocr_auto_input":
                    lines.append(f">自動辨識輸入驗證碼, T={time_suffix_val}\n")
                    continue

                if event_type == "ocr_input":
                    r = event.get("region", (0, 0, 0, 0))
                    x, y, w, h = r[0], r[1], r[2]-r[0], r[3]-r[1]
                    input_delay = event.get("input_delay", 0)
                    delay_str = f", {input_delay}秒後輸入" if input_delay > 0 else ""
                    lines.append(f">OCR辨識輸入範圍({x},{y},{w},{h}){delay_str}, T={time_suffix_val}\n")
                    continue
                    lines.append(f">OCR辨識輸入範圍({x},{y},{w},{h}){delay_str}, T={time_suffix_val}\n")
                    continue

                if event_type == "ocr_relative_input":
                    anchor = event.get("anchor_text", "")
                    dx, dy, w, h = event.get("offset", (0, 0, 100, 30))
                    lines.append(f">相對OCR辨識輸入>{anchor}, 偏移({dx},{dy},{w},{h}), T={time_suffix_val}\n")
                    continue

                if event_type == "click_text":
                    target = event.get("target_text", "")
                    off_x = event.get("offset_x", 0)
                    off_y = event.get("offset_y", 0)
                    suffix = f", 偏移({off_x},{off_y})" if (off_x != 0 or off_y != 0) else ""
                    lines.append(f">點擊文字>{target}{suffix}, T={time_suffix_val}\n")
                    continue

                if event_type == "wait_text":
                    target = event.get("target_text", "")
                    timeout = event.get("timeout", 10.0)
                    lines.append(f">等待文字>{target}, 最長{timeout}s, T={time_suffix_val}\n")
                    continue

                if event_type == "if_text_exists":
                    target = event.get("target_text", "")
                    lines.append(f">if文字>{target}, T={time_suffix_val}\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    continue

                # 分支處理
                if event_type == "branch_success":
                    lines.append(f">>{self._format_branch_action(event)}\n")
                    continue
                
                if event_type == "branch_failure":
                    lines.append(f">>>{self._format_branch_action(event)}\n")
                    continue

                if event_type == "if_all_images_exist":
                    images_str = ",".join(event.get("images", []))
                    lines.append(f">if全部存在>{images_str}{time_suffix}\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    continue

                if event_type == "if_any_image_exists":
                    images_str = ",".join(event.get("images", []))
                    lines.append(f">if任一存在>{images_str}{time_suffix}\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    continue

                if event_type == "random_delay":
                    min_ms = event.get("min_ms", 0)
                    max_ms = event.get("max_ms", 0)
                    lines.append(f">隨機延遲>{int(min_ms)}ms,{int(max_ms)}ms{time_suffix}\n")
                    continue

                if event_type == "random_branch":
                    prob = event.get("probability", 50)
                    lines.append(f">隨機執行>{prob}%{time_suffix}\n")
                    if event.get("on_success"): lines.append(f">>{self._format_branch_action(event['on_success'])}\n")
                    if event.get("on_failure"): lines.append(f">>>{self._format_branch_action(event['on_failure'])}\n")
                    continue

                if event_type == "random_jump":
                    labels_str = ",".join(["#" + l for l in event.get("labels", [])])
                    lines.append(f">隨機跳轉>{labels_str}{time_suffix}\n")
                    continue

                if event_type == "counter_trigger":
                    action_id = event.get("action_id", "")
                    count = event.get("count", 0)
                    lines.append(f">計數器>{action_id}, {count}次後{time_suffix}\n")
                    if event.get("on_trigger"): lines.append(f">>{self._format_branch_action(event['on_trigger'])}\n")
                    continue

                if event_type == "timer_trigger":
                    action_id = event.get("action_id", "")
                    duration = event.get("duration", 0)
                    lines.append(f">計時器>{action_id}, {duration}秒後{time_suffix}\n")
                    if event.get("on_trigger"): lines.append(f">>{self._format_branch_action(event['on_trigger'])}\n")
                    continue

                if event_type == "reset_counter":
                    action_id = event.get("action_id", "")
                    lines.append(f">重置計數器>{action_id}{time_suffix}\n")
                    continue

                if event_type == "reset_timer":
                    action_id = event.get("action_id", "")
                    lines.append(f">重置計時器>{action_id}{time_suffix}\n")
                    continue

                if event_type == "delayed_start":
                    delay_seconds = event.get("delay_seconds", 0)
                    lines.append(f">開始>{delay_seconds}秒後{time_suffix}\n")
                    continue

                if event_type == "delayed_end":
                    delay_seconds = event.get("delay_seconds", 0)
                    lines.append(f">結束>{delay_seconds}秒後{time_suffix}\n")
                    continue

                if event_type == "set_bezier":
                    enabled = event.get("enabled", False)
                    state = "開啟" if enabled else "關閉"
                    lines.append(f">擬真滑鼠>{state}{time_suffix}\n")
                    continue

                # 使用通用格式化
                line = self._format_generic_event(event, rel_delay)
                if line: lines.append(f">{line}\n")

            except Exception as e:
                lines.append(f"# 轉換事件錯誤: {e}\n")
                continue
        
        # 處理未放開的按鍵
        if pressed_keys:
            lines.append("\n# 警告: 未放開按鍵\n")
            for k in pressed_keys: lines.append(f"# >按下{k} (未放開)\n")
            
        return "".join(lines)


    def _format_time(self, seconds: float) -> str:
        """格式化時間為易讀格式"""
        total_ms = round(seconds * 1000)  #  使用 round 四捨五入避免浮點數精度問題
        s = total_ms // 1000
        ms = total_ms % 1000
        
        if s >= 60:
            m = s // 60
            s = s % 60
            return f"{m}m{s:02d}s{ms:03d}"
        else:
            return f"{s}s{ms:03d}"
    

    def _expand_alias_commands(self, text_content):
        """
        展開口語化指令與拖曳指令 (Alias System v1.0)
        讓腳本語法更貼近自然語言
        """
        if not text_content:
            return ""
            
        lines = text_content.split('\n')
        expanded_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # 保留註解與空行
            if not stripped or stripped.startswith('#'):
                expanded_lines.append(line)
                continue

            # 1. 拖曳指令: 
            # 格式 A: >從(x1,y1)拖曳至(x2,y2), 延遲1000ms, T=0s000
            # 格式 B: >拖曳至(x2,y2), 延遲1000ms, T=0s000 (從目前位置開始)
            if '拖曳' in stripped and stripped.startswith('>'):
                # 嘗試匹配格式 A (起點 -> 終點)
                drag_from_to = re.search(r'>從\((-?\d+),(-?\d+)\)拖曳至\((-?\d+),(-?\d+)\)', stripped)
                # 嘗試匹配格式 B (目前 -> 終點)
                drag_to = re.search(r'>拖曳至\((-?\d+),(-?\d+)\)', stripped)
                
                if drag_from_to or drag_to:
                    # 提取目標座標
                    if drag_from_to:
                        x1, y1 = drag_from_to.group(1), drag_from_to.group(2)
                        x2, y2 = drag_from_to.group(3), drag_from_to.group(4)
                        has_start = True
                    else:
                        x2, y2 = drag_to.group(1), drag_to.group(2)
                        has_start = False
                    
                    # 提取延遲 (耗時)
                    duration_match = re.search(r'延遲(\d+)ms', stripped)
                    duration = int(duration_match.group(1)) if duration_match else 1500
                    
                    # 提取時間 T=
                    time_match = re.search(r'T=([\w\d]+)', stripped)
                    first_time_str = f", T={time_match.group(1)}" if time_match else ", T=0s000"
                    
                    # 展開為複合指令
                    if has_start:
                        # 1. 先移動到起點
                        expanded_lines.append(f">移動至({x1},{y1}), 延遲0ms{first_time_str}")
                        expanded_lines.append(f"  # --- 拖曳開始 ---")
                        # 如果已有起點移動，後續動作不帶 T= 以便時間累積
                        start_time_for_press = ""
                    else:
                        start_time_for_press = first_time_str
                    
                    # 2. 按下
                    expanded_lines.append(f">按下左鍵, 延遲50ms{start_time_for_press}")
                    # 3. 移動到終點 (帶耗時)，移除 T= 防止時間重設為 0
                    expanded_lines.append(f">移動至({x2},{y2}), 延遲{duration}ms, T=0s000")
                    # 4. 放開
                    expanded_lines.append(f">放開左鍵, 延遲50ms, T=0s000")
                    
                    if has_start:
                        expanded_lines.append(f"  # --- 拖曳結束 ---")
                    continue


            # 2. 口語化別名轉換
            
            # >如果看見[pic01] -> >if>pic01
            if stripped.startswith('>如果看見['):
                match = re.search(r'\[(.*?)\]', stripped)
                if match:
                    content = match.group(1)
                    # 保留後續參數 (T=...)
                    rest_match = re.search(r'(,\s*T=[\w\d]+)', stripped)
                    rest = rest_match.group(1) if rest_match else ", T=0s000"
                    expanded_lines.append(f">if>{content}{rest}")
                    continue

            # >成功時前往[標籤] -> >>#標籤
            if stripped.startswith('>成功時前往['):
                match = re.search(r'\[(.*?)\]', stripped)
                if match:
                    label = match.group(1)
                    expanded_lines.append(f">>#{label}")
                    continue

            # >失敗時前往[標籤] -> >>>#標籤
            if stripped.startswith('>失敗時前往['):
                match = re.search(r'\[(.*?)\]', stripped)
                if match:
                    label = match.group(1)
                    expanded_lines.append(f">>>#{label}")
                    continue
            
            # >當圖片消失[pic01] -> >if遺失>pic01 (目前核心未支援，暫不轉換或轉為備註)
            if stripped.startswith('>當圖片消失['):
                expanded_lines.append(f"# 核心暫未支援: {line}")
                continue

            # 3. 使用者要求的格式: >按下左鍵, 拖曳至(x2,y2), 延遲1000ms
            if '>按下左鍵' in stripped and '拖曳至' in stripped:
                match = re.search(r'>按下左鍵,\s*拖曳至\s*\((-?\d+),\s*(-?\d+)\)', stripped)
                if match:
                    x2, y2 = match.group(1), match.group(2)
                    duration_match = re.search(r'延遲(\d+)ms', stripped)
                    duration = int(duration_match.group(1)) if duration_match else 1500
                    time_match = re.search(r'T=([\w\d]+)', stripped)
                    t_str = f", T={time_match.group(1)}" if time_match else ", T=0s000"
                    
                    expanded_lines.append(f">按下左鍵, 延遲50ms{t_str}")
                    expanded_lines.append(f">移動至({x2},{y2}), 延遲{duration}ms, T=0s000")
                    expanded_lines.append(f">放開左鍵, 延遲50ms, T=0s000")
                    continue

            # 沒匹配到別名，保留原行
            expanded_lines.append(line)
            
        return '\n'.join(expanded_lines)


    def _parse_image_command(self, line: str) -> Dict[str, Any]:
        """解析圖片辨識相關指令
        
        支援格式：
        >辨識>pic01, T=時間（新格式）
        >辨識>pic01, 邊框, T=時間（顯示邊框）
        >辨識>pic01, 範圍(x1,y1,x2,y2), T=時間（範圍辨識）
        >辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=時間（邊框+範圍）
        >辨識>pic01>img_001.png, T=時間（舊格式，相容性）
        >移動至>pic01, T=時間
        >左鍵點擊>pic01, T=時間
        >右鍵點擊>pic02, T=時間
        """
        # 辨識指令（新格式，支援邊框和範圍）
        # 格式: >辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s000
        match = re.match(r'>辨識>([^>,]+)(?:,\s*([^,T]+))*,\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            options_str = match.group(2) if match.group(2) else ""
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            # 解析選項
            show_border = False
            region = None
            
            if options_str:
                # 檢查是否有"邊框"
                if '邊框' in options_str:
                    show_border = True
                
                # 檢查是否有"範圍"
                region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
                if region_match:
                    region = (
                        int(region_match.group(1)),
                        int(region_match.group(2)),
                        int(region_match.group(3)),
                        int(region_match.group(4))
                    )
            
            # 自動查找pic對應的圖片檔案
            image_file = self._find_pic_image_file(display_name)
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
                "show_border": show_border,
                "region": region,
                "time": seconds * 1000 + millis
            }
        
        # 辨識指令（舊格式，相容性）
        match = re.match(r'>辨識>([^>]+)>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            image_file = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
                "time": seconds * 1000 + millis
            }
        
        # 移動至圖片
        match = re.match(r'>移動至>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            target = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            
            return {
                "type": "move_to_image",
                "target": target,
                "time": seconds * 1000 + millis
            }
        
        # 點擊圖片
        match = re.match(r'>(左鍵|右鍵)點擊>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            button = "left" if match.group(1) == "左鍵" else "right"
            target = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            return {
                "type": "click_image",
                "button": button,
                "target": target,
                "time": seconds * 1000 + millis
            }
        
        return None
    

