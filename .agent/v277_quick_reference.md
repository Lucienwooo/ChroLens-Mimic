# ChroLens Mimic v2.7.7 時間戳記轉換 - 快速參考指南

## 📋 核心變更總結

### 格式對比

| 項目     | v2.7.6 (舊)   | v2.7.7 (新)   |
| :------- | :------------ | :------------ |
| 時間戳   | `T=0s000`     | ❌ 移除       |
| 延遲語法 | `, 延遲50ms`  | `,50ms`       |
| 間隔指令 | `>延遲1000ms` | `>間隔1000ms` |
| 空格     | `, 延遲`      | `,` (無空格)  |

### 範例對比

**舊格式 (v2.7.6):**

```
>按下7, 延遲50ms, T=0s000
>延遲1000ms, T=0s050
>左鍵點擊(100,200), 延遲50ms, T=1s050
```

**新格式 (v2.7.7):**

```
>按下7,50ms
>間隔1000ms
>左鍵點擊(100,200),1050ms
```

---

## 🔧 需要修改的檔案清單

### 1. text_script_editor.py

- [ ] 添加 `convert_old_format_to_new()` 函數
- [ ] 修改 `_json_to_text()` 函數
- [ ] 添加載入時自動轉換邏輯

### 2. 指令參考手冊.json

- [ ] 更新所有範例指令
- [ ] 添加新格式說明
- [ ] 更新注意事項

### 3. version_info.txt

- [ ] 更新版本號到 2.7.7

### 4. 打包.bat

- [ ] 更新版本號到 2.7.7

---

## 📁 提供的範本檔案

### .agent 資料夾中的檔案

1. **v277_timestamp_conversion_template.md**
   - 完整的轉換範本文檔
   - 包含所有修改細節
   - 使用說明和測試清單

2. **v277_conversion_function.py**
   - 舊格式轉新格式的轉換函數
   - 可直接複製使用
   - 包含測試代碼

3. **v277_json_to_text.py**
   - JSON 轉文字腳本函數（新格式）
   - 可直接替換現有函數
   - 包含測試代碼

4. **v2.7.7_summary.md**
   - 完整的實施總結
   - 已完成的修改列表
   - 測試指南

---

## 🚀 快速實施步驟

### 步驟 1：備份當前版本

```bash
# 備份整個專案
cp -r ChroLens-Mimic ChroLens-Mimic_backup
```

### 步驟 2：回退到 v2.7.6

```bash
# 刪除當前版本
rm -rf ChroLens-Mimic

# 從備份或 Git 恢復 v2.7.6
git checkout v2.7.6
```

### 步驟 3：應用時間戳記轉換

#### A. 複製轉換函數

從 `.agent/v277_conversion_function.py` 複製 `convert_old_format_to_new()` 函數到 `text_script_editor.py`

#### B. 複製 JSON 轉換函數

從 `.agent/v277_json_to_text.py` 複製 `_json_to_text_v277()` 函數，替換現有的 `_json_to_text()` 函數

#### C. 更新指令參考手冊

參考 `v277_timestamp_conversion_template.md` 中的 JSON 範例

#### D. 更新版本號

- version_info.txt → 2.7.7
- 打包.bat → 2.7.7

### 步驟 4：測試

```bash
# 啟動程式
python main/ChroLens_Mimic.py

# 測試項目：
# 1. 載入舊格式腳本 → 應自動轉換
# 2. 錄製新腳本 → 應生成新格式
# 3. 執行新格式腳本 → 應正常運行
```

---

## 📝 關鍵程式碼片段

### 1. 轉換函數（核心）

```python
def convert_old_format_to_new(text_script: str):
    """將舊格式轉換為新格式"""
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
```

### 2. JSON 轉文字（核心）

```python
def _json_to_text(self, events, settings):
    """v2.7.7 新格式"""
    lines = []
    last_action_end_time = 0.0

    def add_action_with_interval(action_str, current_time, delay_ms):
        nonlocal last_action_end_time
        interval_ms = int((current_time - last_action_end_time) * 1000)
        total_delay_ms = interval_ms + delay_ms
        lines.append(f'{action_str},{total_delay_ms}ms\n')
        last_action_end_time = current_time + delay_ms / 1000.0

    for event in events:
        event_type = event.get("type", "")
        current_time = event.get("time", 0.0)
        delay_ms = event.get("delay", 50)

        if event_type == "keyboard":
            key = event.get("key", "")
            add_action_with_interval(f'>按鍵{key}', current_time, delay_ms)
        # ... 其他事件類型

    return ''.join(lines)
```

---

## ⚠️ 注意事項

### 1. 備份重要

- 轉換前自動創建 `.bak` 備份
- 建議手動備份整個專案

### 2. 測試完整

- 測試所有指令類型
- 測試時間間隔準確性
- 測試邊界情況（0ms, 大數值等）

### 3. 向下相容

- 自動偵測舊格式
- 載入時自動轉換
- 使用者可選擇是否轉換

### 4. 文檔更新

- 更新使用手冊
- 更新範例腳本
- 更新版本說明

---

## 🎯 檢查清單

### 程式碼修改

- [ ] text_script_editor.py - 添加轉換函數
- [ ] text_script_editor.py - 修改 \_json_to_text
- [ ] 指令參考手冊.json - 更新範例
- [ ] version_info.txt - 更新版本號
- [ ] 打包.bat - 更新版本號

### 測試

- [ ] 載入舊格式腳本
- [ ] 自動轉換測試
- [ ] 錄製新腳本
- [ ] 執行新格式腳本
- [ ] 時間間隔準確性
- [ ] 編輯器功能

### 文檔

- [ ] 更新 README
- [ ] 更新 CHANGELOG
- [ ] 更新使用手冊

---

## 📞 支援

如有問題，參考以下文檔：

- `v277_timestamp_conversion_template.md` - 完整範本
- `v2.7.7_summary.md` - 實施總結
- `v2.7.7_testing_guide.md` - 測試指南

---

**所有時間戳記轉換相關的內容都已整理完成！**
