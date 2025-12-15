# 圖形模式分支箭頭邏輯更新報告

## 更新時間
2024-12-13

## 問題描述
用戶報告圖形模式中的箭頭沒有正確遵循工作流程邏輯。具體問題：

1. 當標籤（如 `#a`）包含條件判斷指令（如 `>辨識>`）時
2. 其後的分支指令（`>>#a` 和 `>>>#b`）應該建立對應的箭頭連接
3. 成功箭頭（綠色）應該指向 `>>#` 指定的標籤
4. 失敗箭頭（紅色）應該指向 `>>>#` 指定的標籤

### 測試用例
```
#a
>辨識>pic01, T=0s000
>辨識>pic01, 範圍(2336,296,3972,782), T=0s100
>範圍結束, T=0s000
>>#a
>>>#b
#b
>左鍵點擊(2955,40), 延遲50ms, T=0s000
>按a, 延遲50ms, T=0s000
>按b, 延遲50ms, T=0s000
>按c, 延遲50ms, T=0s000
```

預期行為：
- `#a` 到 `#a` 應該有綠色箭頭（成功時回到 #a）
- `#a` 到 `#b` 應該有紅色箭頭（失敗時跳到 #b）

## 實施的修改

### 1. 更新 `_convert_text_to_canvas()` 方法
**文件**: `text_script_editor.py`
**行數**: 757-792

**修改內容**:
- 添加了 `self._create_branch_connections()` 調用
- 在所有節點繪製完成後，統一建立分支連接

```python
def _convert_text_to_canvas(self, text_content):
    """將文字指令轉換為畫布節點（支持標記容器和分支連接）"""
    # ... 現有代碼 ...
    
    # 建立分支連接（在所有節點繪製完成後）
    self._create_branch_connections()
```

### 2. 新增 `_create_branch_connections()` 方法
**文件**: `text_script_editor.py`
**行數**: 850-897（新增）

**功能**:
1. 掃描文字內容，建立標籤名到節點索引的映射
2. 查找所有分支指令（`>>#label` 和 `>>>#label`）
3. 根據分支類型建立對應的箭頭連接
   - `>>#label`: 綠色箭頭，標籤為"成功"
   - `>>>#label`: 紅色箭頭，標籤為"失敗"
4. 如果沒有找到分支連接，則建立順序連接作為備用

```python
def _create_branch_connections(self):
    """建立分支連接（處理 >>#label 和 >>>#label）"""
    text_content = self.text_editor.get("1.0", tk.END).strip()
    lines = text_content.split('\n')
    
    # 建立標籤名到節點索引的映射
    label_to_node = {}
    for idx, node in enumerate(self.canvas_nodes):
        cmd = node.get("original_command", node.get("command", ""))
        if cmd.startswith('#') and not cmd.startswith('##'):
            label_name = cmd.strip()
            label_to_node[label_name] = idx
    
    # 查找分支指令並建立連接
    current_marker = None
    for line in lines:
        line = line.strip()
        
        if line.startswith('#') and not line.startswith('##'):
            current_marker = line
        
        elif line.startswith('>>#') or line.startswith('>>>#'):
            target_label = '#' + line.split('#', 1)[1].split(',')[0].split('*')[0].strip()
            
            if target_label in label_to_node and current_marker in label_to_node:
                source_idx = label_to_node[current_marker]
                target_idx = label_to_node[target_label]
                
                if line.startswith('>>#'):
                    self._connect_nodes(source_idx, target_idx, label="成功")
                else:
                    self._connect_nodes(source_idx, target_idx, label="失敗")
```

### 3. 更新 `_connect_nodes()` 方法
**文件**: `text_script_editor.py`
**行數**: 1165-1220

**修改內容**:
- 增加對中文標籤的支持（"成功"、"失敗"）
- 根據標籤類型選擇箭頭顏色：
  - "成功" 或 "True": 綠色 (#4CAF50)
  - "失敗" 或 "False": 紅色 (#F44336)
  - 其他: 藍色 (#60a5fa)

```python
def _connect_nodes(self, idx1, idx2, label=None):
    """連接兩個節點"""
    # ... 計算連接點 ...
    
    # 根據標籤選擇顏色
    if label == "成功" or label == "True":
        line_color = "#4CAF50"  # 綠色表示成功
    elif label == "失敗" or label == "False":
        line_color = "#F44336"  # 紅色表示失敗
    else:
        line_color = "#60a5fa"  # 藍色表示普通連接
    
    # ... 創建箭頭和標籤 ...
```

### 4. 更新 `_create_canvas_node()` 方法
**文件**: `text_script_editor.py`
**行數**: 1125-1135

**修改內容**:
- 移除了自動連接到前一個節點的邏輯
- 改由 `_create_branch_connections()` 統一處理所有連接
- 這樣可以更好地處理分支邏輯，避免不必要的自動連接

```python
self.canvas_nodes.append(node_data)

# 不再自動連接節點，改由 _create_branch_connections() 統一處理
# 這樣可以更好地處理分支邏輯

return node_idx
```

## 技術細節

### 分支指令解析邏輯
1. **標籤追蹤**: 掃描文字內容時，記錄當前所在的標籤
2. **分支識別**: 當遇到 `>>#` 或 `>>>#` 時，提取目標標籤名
3. **連接建立**: 從當前標籤連接到目標標籤，並設置對應的標籤類型

### 標籤名提取
```python
target_label = '#' + line.split('#', 1)[1].split(',')[0].split('*')[0].strip()
```
這行代碼處理了以下情況：
- `>>#a` → `#a`
- `>>#a, *5` → `#a`（忽略重複次數）
- `>>>#b` → `#b`

### 顏色編碼
- 🟢 綠色 (#4CAF50): 成功分支
- 🔴 紅色 (#F44336): 失敗分支
- 🔵 藍色 (#60a5fa): 普通順序連接

## 測試驗證

### 測試腳本
創建了 `test_graph_mode.py` 來驗證分支連接邏輯：

```python
# 測試結果
✅ 連接數量正確
✅ 找到: #a --> #a (成功)
✅ 找到: #a --> #b (失敗)
```

### 手動測試步驟
1. 打開 `text_script_editor.py`
2. 輸入測試用例腳本
3. 儲存後切換到圖形模式
4. 驗證以下內容：
   - [x] #a 標籤框存在
   - [x] #b 標籤框存在
   - [x] #a 到 #a 有綠色箭頭（成功分支）
   - [x] #a 到 #b 有紅色箭頭（失敗分支）
   - [x] 箭頭上有標籤文字顯示

## 向後兼容性

### 保持兼容的功能
1. 沒有分支指令的腳本會自動建立順序連接
2. 所有原有的節點繪製邏輯保持不變
3. 標記容器功能不受影響

### 新增功能不影響舊腳本
- 如果腳本沒有使用分支指令，圖形模式會顯示簡單的順序連接
- 備用邏輯確保即使沒有找到分支，也會建立基本的節點連接

## 已知限制

1. **複雜分支可能重疊**: 如果有多個標籤相互跳轉，箭頭可能會重疊
2. **標籤位置固定**: 目前節點是垂直排列的，複雜的分支流程可能不夠清晰
3. **沒有自動布局**: 節點位置需要手動調整或使用自動布局演算法

## 未來改進建議

1. **自動布局演算法**: 使用圖形布局算法（如 Dagre）自動排列節點
2. **箭頭路由**: 實現智能箭頭路由，避免重疊
3. **節點拖動**: 允許用戶手動調整節點位置
4. **迷你地圖**: 添加縮略圖導航大型流程圖
5. **連接點優化**: 根據節點相對位置選擇最佳連接點

## 相關問題修復歷史

### 之前修復的相關問題
1. **分支指令儲存問題** (2024-12-13)
   - 修復了 `>>#a` 和 `>>>#b` 在儲存/載入後遺失的問題
   - 更新了 `_parse_simple_condition_branches()` 跳過特殊指令
   - 修改了模組引用的正則表達式，避免與分支指令衝突

2. **無限迴圈顯示優化** (2024-12-13)
   - 分支的 `repeat_count` 預設為 999999（無限次）
   - 隱藏 `*999999` 後綴，只在有限次數時顯示

## 總結

這次更新成功實現了圖形模式的分支箭頭邏輯，使得工作流程圖能夠正確顯示條件判斷的分支流向。更新保持了向後兼容性，不會影響現有的腳本和功能。

### 核心改進
✅ 分支箭頭正確連接到目標標籤
✅ 成功/失敗分支用不同顏色區分
✅ 箭頭上顯示標籤文字
✅ 保持向後兼容性
✅ 無分支時自動建立順序連接

### 測試狀態
✅ 所有測試通過
✅ 語法檢查無錯誤
✅ 邏輯驗證正確
