# ChroLens Mimic v2.7.7 時間戳記轉換 - 完整範本包

## 📦 範本包內容

### 📄 文檔檔案

1. **v277_timestamp_conversion_template.md** ⭐ 主要範本
   - 完整的轉換說明
   - 所有需要修改的檔案
   - 詳細的程式碼範例
   - 測試檢查清單

2. **v277_quick_reference.md** 🚀 快速參考
   - 核心變更總結
   - 快速實施步驟
   - 關鍵程式碼片段
   - 檢查清單

3. **v2.7.7_summary.md** 📊 實施總結
   - 已完成的修改
   - 技術實現細節
   - 已知問題與解決方案

4. **v2.7.7_testing_guide.md** 🧪 測試指南
   - 詳細測試步驟
   - 測試案例
   - 預期結果

---

### 💻 程式碼檔案

1. **v277_conversion_function.py** 🔄 轉換函數
   - `convert_old_format_to_new()` 函數
   - 舊格式 → 新格式轉換
   - 包含測試代碼
   - 可直接複製使用

2. **v277_json_to_text.py** 📝 JSON轉換
   - `_json_to_text_v277()` 函數
   - JSON事件 → 文字腳本（新格式）
   - 包含測試代碼
   - 可直接替換現有函數

---

## 🎯 使用方式

### 方案 A：完整閱讀（推薦）

1. **閱讀主要範本**

   ```
   v277_timestamp_conversion_template.md
   ```

   - 了解所有變更
   - 查看詳細說明
   - 理解實施邏輯

2. **參考快速指南**

   ```
   v277_quick_reference.md
   ```

   - 快速查找關鍵資訊
   - 檢查實施步驟
   - 使用檢查清單

3. **複製程式碼**

   ```python
   # 從 v277_conversion_function.py
   # 複製 convert_old_format_to_new() 函數

   # 從 v277_json_to_text.py
   # 複製 _json_to_text_v277() 函數
   ```

### 方案 B：快速實施

1. **直接使用程式碼檔案**
   - 複製 `v277_conversion_function.py` 中的函數
   - 複製 `v277_json_to_text.py` 中的函數
   - 貼到對應的位置

2. **參考快速指南**
   - 查看需要修改的檔案清單
   - 按照檢查清單執行

3. **測試**
   - 使用測試指南驗證

---

## 📋 核心變更摘要

### 格式變更

| 項目   | 舊格式        | 新格式        |
| :----- | :------------ | :------------ |
| 時間戳 | `T=0s000`     | ❌ 移除       |
| 延遲   | `, 延遲50ms`  | `,50ms`       |
| 間隔   | `>延遲1000ms` | `>間隔1000ms` |
| 空格   | 有空格        | 無空格        |

### 範例

**舊格式:**

```
>按下7, 延遲50ms, T=0s000
>延遲1000ms, T=0s050
>左鍵點擊(100,200), 延遲50ms, T=1s050
```

**新格式:**

```
>按下7,50ms
>間隔1000ms
>左鍵點擊(100,200),1050ms
```

---

## 🔧 需要修改的檔案

### 必須修改

1. ✅ **text_script_editor.py**
   - 添加 `convert_old_format_to_new()` 函數
   - 修改 `_json_to_text()` 函數

2. ✅ **指令參考手冊.json**
   - 更新所有範例指令
   - 添加新格式說明

3. ✅ **version_info.txt**
   - 更新版本號到 2.7.7

4. ✅ **打包.bat**
   - 更新版本號到 2.7.7

### 可選修改

- README.md - 更新說明
- CHANGELOG.md - 添加版本記錄
- 使用手冊 - 更新範例

---

## 🚀 快速實施流程

### 步驟 1：準備

```bash
# 備份當前版本
cp -r ChroLens-Mimic ChroLens-Mimic_backup

# 回退到 v2.7.6（如果需要）
git checkout v2.7.6
```

### 步驟 2：複製程式碼

**A. 轉換函數**

```python
# 從 v277_conversion_function.py 複製
# 貼到 text_script_editor.py 約第 175 行
def convert_old_format_to_new(text_script: str):
    # ... 完整函數內容
```

**B. JSON轉換函數**

```python
# 從 v277_json_to_text.py 複製
# 替換 text_script_editor.py 中的 _json_to_text() 函數
def _json_to_text(self, events, settings):
    # ... 完整函數內容
```

### 步驟 3：更新設定

**A. 指令參考手冊.json**

```json
{
  "基本指令": {
    "延遲等待": {
      "延遲等待(毫秒)": ">間隔1000ms"
    }
  }
}
```

**B. version_info.txt**

```
filevers=(2, 7, 7, 0),
prodvers=(2, 7, 7, 0),
```

### 步驟 4：測試

```bash
# 啟動程式
python main/ChroLens_Mimic.py

# 測試：
# 1. 載入舊格式腳本
# 2. 錄製新腳本
# 3. 執行腳本
```

---

## 📊 檔案位置

所有範本檔案位於：

```
ChroLens-Mimic/.agent/
├── v277_timestamp_conversion_template.md  # 主要範本
├── v277_quick_reference.md                # 快速參考
├── v277_conversion_function.py            # 轉換函數
├── v277_json_to_text.py                   # JSON轉換
├── v2.7.7_summary.md                      # 實施總結
└── v2.7.7_testing_guide.md                # 測試指南
```

---

## ✅ 檢查清單

### 實施前

- [ ] 備份當前版本
- [ ] 閱讀主要範本
- [ ] 準備測試環境

### 實施中

- [ ] 複製轉換函數
- [ ] 複製 JSON 轉換函數
- [ ] 更新指令參考手冊
- [ ] 更新版本號

### 實施後

- [ ] 測試舊格式轉換
- [ ] 測試新格式錄製
- [ ] 測試腳本執行
- [ ] 測試時間間隔
- [ ] 更新文檔

---

## 💡 重要提醒

### 1. 備份

- ✅ 轉換前自動創建 `.bak` 備份
- ✅ 建議手動備份整個專案

### 2. 測試

- ✅ 測試所有指令類型
- ✅ 測試時間間隔準確性
- ✅ 測試邊界情況

### 3. 相容性

- ✅ 自動偵測舊格式
- ✅ 載入時自動轉換
- ✅ 使用者可選擇

---

## 🎉 完成！

這個範本包包含了所有 v2.7.7 時間戳記轉換所需的內容：

- ✅ 完整的文檔說明
- ✅ 可直接使用的程式碼
- ✅ 詳細的實施步驟
- ✅ 完整的測試指南

**您可以安全地刪除當前的 ChroLens-Mimic 資料夾，這些範本檔案包含了所有需要保留的時間戳記轉換內容！**

---

## 📞 參考順序

建議的閱讀/使用順序：

1. **v277_quick_reference.md** - 快速了解
2. **v277_timestamp_conversion_template.md** - 詳細學習
3. **v277_conversion_function.py** - 複製程式碼
4. **v277_json_to_text.py** - 複製程式碼
5. **v2.7.7_testing_guide.md** - 測試驗證

**祝您實施順利！** 🚀
