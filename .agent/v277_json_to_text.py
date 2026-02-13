"""
ChroLens Mimic v2.7.7 - JSON 轉文字腳本函數（新格式）
可直接複製到 text_script_editor.py 中使用
"""

def _json_to_text_v277(events, settings):
    """
    將JSON事件轉換為文字指令（v2.7.7 新格式：間隔模式）
    
    新格式特點：
    1. 移除 T= 時間戳
    2. 使用 >間隔XXms 表示等待
    3. 簡化延遲語法 (,50ms)
    """
    lines = []
    
    # 添加設定區塊
    lines.append("# ========== 腳本設定 ==========\n")
    lines.append(f"# 重複次數: {settings.get('repeat', 1)}\n")
    lines.append(f"# 執行速度: {settings.get('speed', 100)}%\n")
    lines.append("# ================================\n\n")
    
    # v2.7.7: 追蹤上一個動作的結束時間（用於計算間隔）
    last_action_end_time = 0.0
    
    def add_action_with_interval(action_str, current_time, delay_ms):
        """添加動作指令，並在需要時插入間隔指令"""
        nonlocal last_action_end_time
        
        # 計算從上個動作結束到現在的間隔時間
        interval_ms = int((current_time - last_action_end_time) * 1000)
        
        # 總延遲 = 間隔時間 + 動作延遲
        total_delay_ms = interval_ms + delay_ms
        
        # 添加動作指令（包含總延遲）
        lines.append(f'{action_str},{total_delay_ms}ms\n')
        
        # 更新結束時間
        last_action_end_time = current_time + delay_ms / 1000.0
    
    # 處理每個事件
    for i, event in enumerate(events):
        event_type = event.get("type", "")
        current_time = event.get("time", 0.0)
        delay_ms = event.get("delay", 50)  # 預設延遲 50ms
        
        # 鍵盤事件
        if event_type == "keyboard":
            kb_event = event.get("event", "")
            key = event.get("key", "")
            
            if kb_event == "down":
                add_action_with_interval(f'>按下{key}', current_time, delay_ms)
            elif kb_event == "up":
                add_action_with_interval(f'>放開{key}', current_time, delay_ms)
            elif kb_event == "press":
                add_action_with_interval(f'>按鍵{key}', current_time, delay_ms)
        
        # 滑鼠移動事件
        elif event_type == "mouse" and event.get("event") == "move":
            x = event.get("x", 0)
            y = event.get("y", 0)
            add_action_with_interval(f'>移動至({x},{y})', current_time, delay_ms)
        
        # 滑鼠點擊事件
        elif event_type == "mouse":
            mouse_event = event.get("event", "")
            button = event.get("button", "left")
            x = event.get("x", 0)
            y = event.get("y", 0)
            
            if mouse_event == "down":
                add_action_with_interval(f'>{button}鍵按下({x},{y})', current_time, delay_ms)
            elif mouse_event == "up":
                add_action_with_interval(f'>{button}鍵放開({x},{y})', current_time, delay_ms)
            elif mouse_event == "click":
                add_action_with_interval(f'>{button}鍵點擊({x},{y})', current_time, delay_ms)
            elif mouse_event == "double_click":
                add_action_with_interval(f'>雙擊({x},{y})', current_time, delay_ms)
        
        # 滑鼠滾輪事件
        elif event_type == "scroll":
            x = event.get("x", 0)
            y = event.get("y", 0)
            delta = event.get("delta", 0)
            add_action_with_interval(f'>滾輪({x},{y},{delta})', current_time, delay_ms)
        
        # 延遲事件
        elif event_type == "delay":
            delay_time = event.get("duration", 1000)
            # 更新時間追蹤
            last_action_end_time = current_time + delay_time / 1000.0
        
        # 圖片辨識事件
        elif event_type == "image_recognition":
            template = event.get("template", "")
            action = event.get("action", "click")
            add_action_with_interval(f'>找圖[{template}]並{action}', current_time, delay_ms)
        
        # 文字辨識事件
        elif event_type == "ocr":
            text = event.get("text", "")
            action = event.get("action", "click")
            add_action_with_interval(f'>找字[{text}]並{action}', current_time, delay_ms)
        
        # 迴圈開始
        elif event_type == "loop_start":
            count = event.get("count", 1)
            lines.append(f'>迴圈開始,重複{count}次\n')
        
        # 迴圈結束
        elif event_type == "loop_end":
            lines.append(f'>迴圈結束\n')
        
        # 條件判斷
        elif event_type == "if":
            condition = event.get("condition", "")
            lines.append(f'>如果[{condition}]\n')
        
        # 其他事件類型
        # 可根據需要添加更多事件類型的處理
    
    return ''.join(lines)


# 測試代碼
if __name__ == "__main__":
    import json
    
    # 測試事件
    test_events = [
        {"type": "mouse", "event": "move", "x": 100, "y": 200, "time": 0.0, "delay": 50},
        {"type": "mouse", "event": "click", "button": "left", "x": 100, "y": 200, "time": 0.928, "delay": 50},
        {"type": "delay", "duration": 1000, "time": 1.040},
        {"type": "keyboard", "event": "press", "key": "a", "time": 2.040, "delay": 50},
    ]
    
    test_settings = {
        "repeat": 1,
        "speed": 100
    }
    
    print("="*60)
    print("測試 JSON 轉文字（v2.7.7 格式）")
    print("="*60)
    print("\n輸入事件:")
    print(json.dumps(test_events, indent=2, ensure_ascii=False))
    
    result = _json_to_text_v277(test_events, test_settings)
    
    print("\n輸出文字腳本:")
    print("="*60)
    print(result)
    print("="*60)
