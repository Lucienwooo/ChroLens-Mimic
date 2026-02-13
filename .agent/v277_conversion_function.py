"""
ChroLens Mimic v2.7.7 - 舊格式轉換函數
可直接複製到 text_script_editor.py 中使用
"""

import re

def convert_old_format_to_new(text_script: str):
    """
    將舊格式腳本自動轉換為新格式（v2.7.7）
    
    舊格式: >按下7, 延遲50ms, T=0s000
           >延遲1000ms, T=0s050
    新格式: >按下7,1050ms  (包含動作延遲 + 間隔時間)
    
    :param text_script: 原始文字腳本
    :return: (轉換後的腳本, 是否進行了轉換)
    """
    # 檢查是否為舊格式（包含 T= 時間戳或 >間隔）
    if not re.search(r'T=\d+s\d+', text_script) and not re.search(r'>間隔\d+ms', text_script):
        return text_script, False
    
    lines = text_script.split('\n')
    new_lines = []
    last_timestamp = 0  # 上一個動作的時間戳（毫秒）
    pending_interval = 0  # 待處理的間隔時間（毫秒）
    
    for line in lines:
        stripped = line.strip()
        
        # 空行直接保留
        if not stripped:
            new_lines.append(line)
            continue
        
        # 匹配舊格式: >動作, 延遲XXms, T=Xs000
        old_format_match = re.match(
            r'^(>.*?),\s*延遲(\d+)ms,\s*T=(\d+)s(\d+)',
            stripped
        )
        
        if old_format_match:
            action = old_format_match.group(1)
            delay_ms = int(old_format_match.group(2))
            time_s = int(old_format_match.group(3))
            time_ms = int(old_format_match.group(4))
            
            # 計算間隔時間（毫秒）
            current_timestamp = time_s * 1000 + time_ms
            interval_ms = current_timestamp - last_timestamp
            
            # 總延遲 = 間隔 + 動作延遲
            total_delay = interval_ms + delay_ms
            
            # 更新時間戳
            last_timestamp = current_timestamp + delay_ms
            
            # 輸出新格式
            new_lines.append(f'{action},{total_delay}ms')
            continue
        
        # 匹配新格式的間隔指令: >間隔XXms
        elif re.match(r'^>間隔(\d+)ms', stripped):
            # 已經是新格式，直接保留
            interval_match = re.match(r'^>間隔(\d+)ms', stripped)
            pending_interval = int(interval_match.group(1))
            new_lines.append(line)
            continue
        
        # 匹配新格式的動作指令: >動作,XXms
        elif re.match(r'^>.*?,(\d+)ms', stripped):
            # 已經是新格式
            action_match = re.match(r'^(>.*?),(\d+)ms', stripped)
            if action_match:
                action = action_match.group(1)
                delay_ms = int(action_match.group(2))
                
                # 如果有待處理的間隔，合併進去
                if pending_interval > 0:
                    total_delay = pending_interval + delay_ms
                    new_lines.append(f'{action},{total_delay}ms')
                    pending_interval = 0
                else:
                    new_lines.append(line)
            continue
        
        # 其他行（註解、特殊指令等）直接保留
        new_lines.append(line)
    
    return '\n'.join(new_lines), True


# 測試代碼
if __name__ == "__main__":
    # 測試舊格式轉換
    old_script = """# 測試腳本
>按下7, 延遲50ms, T=0s000
>延遲1000ms, T=0s050
>左鍵點擊(100,200), 延遲50ms, T=1s050
>移動至(300,400), 延遲0ms, T=1s100
"""
    
    print("="*60)
    print("舊格式:")
    print("="*60)
    print(old_script)
    
    new_script, was_converted = convert_old_format_to_new(old_script)
    
    print("\n" + "="*60)
    print("新格式:")
    print("="*60)
    print(new_script)
    
    print("\n" + "="*60)
    print(f"是否轉換: {was_converted}")
    print("="*60)
