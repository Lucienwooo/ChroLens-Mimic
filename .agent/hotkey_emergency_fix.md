# ChroLens Mimic 快捷鍵問題 - 緊急修復方案

## 🚨 問題狀況

### 使用者回報

- **版本**: 2.7.6
- **問題**: 所有快捷鍵完全無法使用
- **環境**: Windows 11, 已使用管理員權限
- **影響**:
  - 錄製/暫停/停止快捷鍵無效
  - 腳本執行快捷鍵無效 (F12, ALT+F1, ALT+F2)
  - 自訂快捷鍵無效
  - 只能手動點擊按鈕

### 對比資訊

- **2.5版本**: 快捷鍵正常運作
- **2.7.6版本**: 快捷鍵完全失效

---

## 🔍 根本原因分析

### Python keyboard 模組的限制

#### 已知問題

1. **Windows 11 相容性問題**
   - Win11 的安全性更新可能阻擋低級別鍵盤鉤子
   - UAC 設定可能干擾快捷鍵註冊

2. **權限問題**
   - 即使以管理員執行，某些情況下仍然無效
   - 防毒軟體可能阻擋鍵盤鉤子

3. **模組本身的 Bug**
   - keyboard 模組在某些環境下不穩定
   - 長時間運行後快捷鍵可能失效

---

## ✅ 解決方案

### 方案 1：使用 pynput 替代 keyboard（推薦）

#### 優點

- ✅ **不需要管理員權限**
- ✅ **更穩定可靠**
- ✅ **跨平台支援**
- ✅ **活躍維護**
- ✅ **Win11 相容性好**

#### 實施步驟

##### 1. 安裝 pynput

```bash
pip install pynput
```

##### 2. 創建新的快捷鍵管理器

```python
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

class PynputHotkeyManager:
    def __init__(self):
        self.current_keys = set()
        self.hotkeys = {}
        self.listener = None

    def register(self, hotkey_combo, callback):
        """
        註冊快捷鍵
        hotkey_combo: 例如 'ctrl+alt+a' 或 'f12'
        """
        keys = self._parse_hotkey(hotkey_combo)
        self.hotkeys[frozenset(keys)] = callback

        if not self.listener:
            self.start_listening()

    def _parse_hotkey(self, combo):
        """解析快捷鍵字串"""
        keys = []
        parts = combo.lower().split('+')

        for part in parts:
            part = part.strip()
            if part == 'ctrl':
                keys.append(Key.ctrl_l)
            elif part == 'alt':
                keys.append(Key.alt_l)
            elif part == 'shift':
                keys.append(Key.shift_l)
            elif len(part) == 1:
                keys.append(KeyCode.from_char(part))
            else:
                # F1-F12 等功能鍵
                key_name = f'f{part[1:]}' if part.startswith('f') else part
                keys.append(getattr(Key, key_name, KeyCode.from_char(part)))

        return keys

    def start_listening(self):
        """開始監聽鍵盤事件"""
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def _on_press(self, key):
        """按鍵按下"""
        self.current_keys.add(key)
        self._check_hotkeys()

    def _on_release(self, key):
        """按鍵釋放"""
        if key in self.current_keys:
            self.current_keys.remove(key)

    def _check_hotkeys(self):
        """檢查是否觸發快捷鍵"""
        for hotkey_set, callback in self.hotkeys.items():
            if hotkey_set.issubset(self.current_keys):
                callback()

    def unregister_all(self):
        """取消所有快捷鍵"""
        if self.listener:
            self.listener.stop()
        self.hotkeys.clear()
        self.current_keys.clear()
```

##### 3. 整合到主程式

```python
# 在 ChroLens_Mimic.py 中
from pynput_hotkey import PynputHotkeyManager

class ChroLensMimic:
    def __init__(self):
        # 使用 pynput 替代 keyboard
        self.hotkey_manager = PynputHotkeyManager()

    def register_hotkeys(self):
        """註冊所有快捷鍵"""
        # 錄製快捷鍵
        self.hotkey_manager.register('f9', self.start_recording)

        # 暫停快捷鍵
        self.hotkey_manager.register('f10', self.pause_recording)

        # 停止快捷鍵
        self.hotkey_manager.register('f11', self.stop_recording)

        # 腳本執行快捷鍵
        for script_name, hotkey in self.script_hotkeys.items():
            self.hotkey_manager.register(
                hotkey,
                lambda s=script_name: self.execute_script(s)
            )
```

---

### 方案 2：改進現有 keyboard 模組使用（臨時方案）

如果暫時無法遷移到 pynput，可以嘗試：

#### 1. 延遲註冊

```python
def delayed_register_hotkeys(self):
    """延遲註冊快捷鍵"""
    import threading

    def register_after_delay():
        time.sleep(2)  # 等待2秒
        self.register_all_hotkeys()

    threading.Thread(target=register_after_delay, daemon=True).start()
```

#### 2. 定期重新註冊

```python
def periodic_hotkey_check(self):
    """定期檢查並重新註冊快捷鍵"""
    def check_loop():
        while self.running:
            time.sleep(60)  # 每分鐘檢查一次
            self.re_register_hotkeys()

    threading.Thread(target=check_loop, daemon=True).start()
```

#### 3. 使用 suppress=True

```python
keyboard.add_hotkey(
    hotkey,
    callback,
    suppress=True,  # 阻止快捷鍵傳遞
    trigger_on_release=False
)
```

---

## 🛠️ 診斷工具

已創建 `快捷鍵診斷.py` 工具：

```bash
python 快捷鍵診斷.py
```

### 診斷項目

1. ✅ 系統資訊
2. ✅ 管理員權限
3. ✅ keyboard 模組狀態
4. ✅ pynput 可用性

---

## 📋 實施計畫

### 階段 1：立即診斷（今天）

- [x] 創建診斷工具
- [ ] 使用者執行診斷
- [ ] 收集診斷報告

### 階段 2：快速修復（1-2天）

- [ ] 實施 pynput 方案
- [ ] 測試所有快捷鍵功能
- [ ] 向下相容性測試

### 階段 3：發布更新（3-5天）

- [ ] 打包新版本
- [ ] 更新文檔
- [ ] 發布 v2.7.8

---

## 🎯 推薦行動

### 立即執行

1. **執行診斷工具**

   ```bash
   cd ChroLens-Mimic
   python 快捷鍵診斷.py
   ```

2. **安裝 pynput**

   ```bash
   pip install pynput
   ```

3. **測試 pynput**
   - 創建簡單測試腳本
   - 驗證快捷鍵功能

### 後續步驟

1. 實施 pynput 方案
2. 全面測試
3. 發布更新版本

---

## 📊 風險評估

| 方案          | 成功率 | 實施時間 | 風險                |
| :------------ | :----: | :------: | :------------------ |
| pynput        |  95%   |  2-3天   | 低 - 需要測試相容性 |
| 改進 keyboard |  50%   |   1天    | 高 - 可能仍然失效   |
| 混合方案      |  90%   |  3-5天   | 中 - 複雜度增加     |

---

## 💡 建議

**強烈建議採用 pynput 方案：**

1. ✅ 徹底解決問題
2. ✅ 不需要管理員權限
3. ✅ 更好的跨平台支援
4. ✅ 長期穩定性

**實施優先級：**

1. 🔴 高優先級：執行診斷工具
2. 🔴 高優先級：安裝並測試 pynput
3. 🟡 中優先級：實施新快捷鍵管理器
4. 🟢 低優先級：向下相容性處理

---

**建議立即開始實施 pynput 方案！**
