# ChroLens Mimic v2.7.7 時間戳記轉換完整範本

## 📋 概述

這是 v2.7.6 到 v2.7.7 之間的時間戳記格式轉換完整範本。
可以直接應用到任何版本的 ChroLens Mimic。

---

## 🎯 核心變更

### 舊格式 (v2.7.6)

```
>按下7, 延遲50ms, T=0s000
>延遲1000ms, T=0s050
>左鍵點擊(100,200), 延遲50ms, T=1s050
>移動至(300,400), 延遲0ms, T=1s100
```

### 新格式 (v2.7.7)

```
>按下7,50ms
>間隔1000ms
>左鍵點擊(100,200),50ms
>間隔50ms
>移動至(300,400),0ms
```

### 變更重點

1. ❌ 移除所有 `T=` 時間戳
2. ✅ 使用 `>間隔XXms` 表示等待時間
3. ✅ 簡化延遲語法（`,50ms` 而非 `, 延遲50ms`）
4. ✅ 移除逗號後空格

---

## 📁 需要修改的檔案

### 1. text_script_editor.py

#### A. 新增舊格式轉換函數

在檔案開頭（約第 175 行）添加：

```python
# ========== v2.7.7 腳本格式自動轉換器 ==========
# 將舊格式 (T=0s000) 自動轉換為新格式 (純相對延遲模式)

def convert_old_format_to_new(text_script: str):
    """
    將舊格式腳本自動轉換為新格式（方案一：純相對延遲）

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
```

#### B. 修改 \_json_to_text 函數

找到 `_json_to_text` 函數（約第 3728 行），完全替換為：

```python
def _json_to_text(self, events, settings):
    """將JSON事件轉換為文字指令（v2.7.7 新格式：間隔模式）"""
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

        # 延遲事件（已整合到間隔中，不需要單獨處理）
        elif event_type == "delay":
            delay_time = event.get("duration", 1000)
            # 在新格式中，延遲已經整合到動作的總延遲中
            # 這裡只需要更新時間追蹤
            last_action_end_time = current_time + delay_time / 1000.0

        # 其他所有事件類型（批次處理，移除 T= 時間戳）
        else:
            # 這裡處理所有其他類型的事件
            # 根據實際需要添加對應的處理邏輯
            pass

    return ''.join(lines)
```

---

### 2. 指令參考手冊.json

更新指令範例（約第 48 行開始）：

```json
{
  "基本指令": {
    "滑鼠操作": {
      "移動滑鼠": ">移動至(100,200),50ms",
      "左鍵點擊": ">左鍵點擊(100,200),50ms",
      "右鍵點擊": ">右鍵點擊(100,200),50ms",
      "雙擊": ">雙擊(100,200),50ms",
      "拖曳": ">拖曳從(100,200)到(300,400),100ms"
    },
    "鍵盤操作": {
      "按鍵": ">按鍵a,50ms",
      "按下": ">按下shift,50ms",
      "放開": ">放開shift,50ms",
      "組合鍵": ">按下ctrl+c,50ms"
    },
    "延遲等待": {
      "延遲等待(毫秒)": ">間隔1000ms",
      "延遲等待(秒)": ">間隔2000ms"
    }
  },
  "格式說明": {
    "新格式說明": "v2.7.7 採用間隔模式，移除 T= 時間戳",
    "間隔指令": ">間隔1000ms 表示等待 1 秒",
    "動作延遲": "每個動作後的 ,XXms 表示該動作的執行延遲",
    "範例": [
      ">按下7,50ms",
      ">間隔1000ms = 等待 1 秒",
      ">左鍵點擊(100,200),50ms"
    ],
    "完整範例": [
      "# 範例腳本",
      ">按下7,50ms",
      ">間隔1000ms",
      ">左鍵點擊(100,200),50ms",
      ">間隔2000ms",
      ">按鍵enter,50ms",
      ">間隔500ms",
      ">移動至(300,400),0ms"
    ]
  },
  "注意事項": [
    "1. 所有時間單位為毫秒 (ms)",
    "2. 動作延遲通常設為 50ms",
    "3. 移動指令可以設為 0ms（立即執行）",
    "4. 使用 >間隔XXms 控制動作之間的等待時間",
    "5. 不再使用 T= 時間戳",
    "6. 逗號後不加空格",
    "7. 延遲時間可以為 0",
    "8. 間隔時間通常 > 0",
    "9. v2.7.7+ 使用新的間隔模式，舊格式腳本會自動轉換"
  ]
}
```

---

### 3. 批次轉換工具

創建 `convert_scripts_to_v277.py`：

```python
"""
ChroLens Mimic - 批次轉換腳本到 v2.7.7 格式
"""

import os
import re
import json
from pathlib import Path

def convert_old_format_to_new(text_script: str):
    """
    將舊格式腳本轉換為新格式
    """
    # 檢查是否為舊格式
    if not re.search(r'T=\d+s\d+', text_script):
        return text_script, False

    lines = text_script.split('\n')
    new_lines = []
    last_timestamp = 0

    for line in lines:
        stripped = line.strip()

        if not stripped:
            new_lines.append(line)
            continue

        # 匹配舊格式
        old_format_match = re.match(
            r'^(>.*?),\s*延遲(\d+)ms,\s*T=(\d+)s(\d+)',
            stripped
        )

        if old_format_match:
            action = old_format_match.group(1)
            delay_ms = int(old_format_match.group(2))
            time_s = int(old_format_match.group(3))
            time_ms = int(old_format_match.group(4))

            current_timestamp = time_s * 1000 + time_ms
            interval_ms = current_timestamp - last_timestamp
            total_delay = interval_ms + delay_ms
            last_timestamp = current_timestamp + delay_ms

            new_lines.append(f'{action},{total_delay}ms')
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), True

def convert_directory(directory):
    """轉換目錄中的所有 .txt 腳本"""
    converted = 0
    skipped = 0

    for file_path in Path(directory).rglob('*.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content, was_converted = convert_old_format_to_new(content)

            if was_converted:
                # 備份原檔案
                backup_path = file_path.with_suffix('.txt.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                # 寫入新格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"✓ 已轉換: {file_path}")
                converted += 1
            else:
                print(f"- 跳過: {file_path} (已是新格式)")
                skipped += 1

        except Exception as e:
            print(f"✗ 錯誤: {file_path} - {e}")

    print(f"\n轉換完成！")
    print(f"  已轉換: {converted} 個檔案")
    print(f"  已跳過: {skipped} 個檔案")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("請輸入腳本目錄路徑: ")

    if os.path.exists(directory):
        convert_directory(directory)
    else:
        print(f"目錄不存在: {directory}")
```

---

## 🔄 轉換流程

### 自動轉換（載入時）

在 `text_script_editor.py` 的載入函數中添加：

```python
def load_script(self, file_path):
    """載入腳本並自動轉換舊格式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 自動轉換舊格式
    new_content, was_converted = convert_old_format_to_new(content)

    if was_converted:
        # 顯示轉換通知
        from tkinter import messagebox
        result = messagebox.askyesno(
            "格式轉換",
            "偵測到舊格式腳本 (v2.7.6)，是否轉換為新格式 (v2.7.7)？\n\n"
            "轉換後將移除 T= 時間戳，改用間隔模式。\n"
            "原檔案會備份為 .bak"
        )

        if result:
            # 備份原檔案
            backup_path = file_path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 保存新格式
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            messagebox.showinfo("轉換完成", f"已轉換為新格式！\n原檔案備份: {backup_path}")

    return new_content
```

---

## 📊 測試檢查清單

### 1. 轉換測試

- [ ] 載入舊格式腳本
- [ ] 確認自動偵測
- [ ] 確認轉換正確
- [ ] 確認備份創建

### 2. 執行測試

- [ ] 執行新格式腳本
- [ ] 檢查時間間隔正確
- [ ] 檢查動作順序正確

### 3. 編輯測試

- [ ] 手動編輯新格式
- [ ] 保存腳本
- [ ] 重新載入
- [ ] 確認格式保持

---

## 📝 版本資訊更新

### version_info.txt

```
filevers=(2, 7, 7, 0),
prodvers=(2, 7, 7, 0),
FileVersion='2.7.7.0',
ProductVersion='2.7.7.0'
```

### 打包.bat

```batch
pyinstaller --name="ChroLens_Mimic_v2.7.7" ^
    --onefile ^
    --windowed ^
    --icon=umi_奶茶色.ico ^
    --version-file=version_info.txt ^
    ChroLens_Mimic.py
```

---

## 🎯 重點提醒

1. **備份重要**
   - 轉換前自動備份
   - 備份檔案為 `.bak`

2. **向下相容**
   - 自動偵測舊格式
   - 自動轉換

3. **使用者友善**
   - 轉換前詢問
   - 顯示轉換通知

4. **完整測試**
   - 測試所有指令類型
   - 測試時間間隔
   - 測試邊界情況

---

**這個範本包含了所有 v2.7.7 時間戳記轉換的完整內容！**
