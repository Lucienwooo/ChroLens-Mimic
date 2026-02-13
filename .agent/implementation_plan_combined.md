# ChroLens Mimic - 綜合實施計畫

## 📋 任務概述

### 任務 1：快捷鍵系統修復（高優先級）

- 使用 pynput 替代 keyboard 模組
- 解決 Windows 11 快捷鍵失效問題

### 任務 2：v2.7.7 時間語法測試

- 測試錄製功能
- 測試腳本執行
- 測試編輯器讀寫

---

## 🔧 任務 1：快捷鍵系統修復

### 步驟 1：安裝 pynput

```bash
pip install pynput
```

### 步驟 2：創建 pynput 快捷鍵管理器

創建新檔案：`main/hotkey_manager.py`

```python
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import threading

class HotkeyManager:
    """
    使用 pynput 實現的快捷鍵管理器
    解決 keyboard 模組在 Windows 11 上的相容性問題
    """

    def __init__(self):
        self.current_keys = set()
        self.hotkeys = {}
        self.listener = None
        self.callbacks = {}
        self.lock = threading.Lock()

    def register(self, hotkey_str, callback, name=""):
        """
        註冊快捷鍵

        Args:
            hotkey_str: 快捷鍵字串，例如 'f9', 'ctrl+alt+a', 'alt+f1'
            callback: 回調函數
            name: 快捷鍵名稱（用於日誌）

        Returns:
            bool: 註冊成功返回 True
        """
        try:
            keys = self._parse_hotkey(hotkey_str)
            key_set = frozenset(keys)

            with self.lock:
                self.hotkeys[key_set] = {
                    'callback': callback,
                    'name': name or hotkey_str,
                    'hotkey_str': hotkey_str
                }

            if not self.listener:
                self.start_listening()

            return True
        except Exception as e:
            print(f"註冊快捷鍵失敗 {hotkey_str}: {e}")
            return False

    def unregister(self, hotkey_str):
        """取消註冊快捷鍵"""
        try:
            keys = self._parse_hotkey(hotkey_str)
            key_set = frozenset(keys)

            with self.lock:
                if key_set in self.hotkeys:
                    del self.hotkeys[key_set]
                    return True
            return False
        except:
            return False

    def unregister_all(self):
        """取消所有快捷鍵"""
        with self.lock:
            self.hotkeys.clear()
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _parse_hotkey(self, hotkey_str):
        """
        解析快捷鍵字串

        支援格式：
        - 單鍵: 'f9', 'a', '1'
        - 組合鍵: 'ctrl+a', 'alt+f1', 'ctrl+alt+delete'
        """
        keys = []
        parts = hotkey_str.lower().replace(' ', '').split('+')

        for part in parts:
            if part in ['ctrl', 'control']:
                keys.append(Key.ctrl_l)
            elif part == 'alt':
                keys.append(Key.alt_l)
            elif part == 'shift':
                keys.append(Key.shift_l)
            elif part == 'win' or part == 'cmd':
                keys.append(Key.cmd)
            elif part.startswith('f') and len(part) <= 3:  # F1-F12
                try:
                    f_num = int(part[1:])
                    if 1 <= f_num <= 12:
                        keys.append(getattr(Key, f'f{f_num}'))
                except:
                    pass
            elif len(part) == 1:  # 單個字符
                keys.append(KeyCode.from_char(part))
            else:
                # 其他特殊鍵
                try:
                    keys.append(getattr(Key, part))
                except:
                    # 嘗試作為字符
                    if len(part) > 0:
                        keys.append(KeyCode.from_char(part[0]))

        return keys

    def start_listening(self):
        """開始監聽鍵盤事件"""
        if self.listener:
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def _on_press(self, key):
        """按鍵按下事件"""
        self.current_keys.add(key)
        self._check_hotkeys()

    def _on_release(self, key):
        """按鍵釋放事件"""
        if key in self.current_keys:
            self.current_keys.discard(key)

    def _check_hotkeys(self):
        """檢查是否觸發快捷鍵"""
        with self.lock:
            for key_set, info in self.hotkeys.items():
                if key_set.issubset(self.current_keys):
                    # 觸發快捷鍵
                    try:
                        info['callback']()
                    except Exception as e:
                        print(f"快捷鍵 {info['name']} 回調執行失敗: {e}")

    def get_registered_hotkeys(self):
        """獲取所有已註冊的快捷鍵"""
        with self.lock:
            return [info['hotkey_str'] for info in self.hotkeys.values()]
```

### 步驟 3：整合到主程式

在 `ChroLens_Mimic.py` 中：

1. **導入新模組**

```python
# 在檔案開頭添加
try:
    from hotkey_manager import HotkeyManager
    USE_PYNPUT_HOTKEY = True
except:
    USE_PYNPUT_HOTKEY = False
    print("[警告] 無法載入 pynput 快捷鍵管理器，將使用舊版 keyboard 模組")
```

2. **初始化快捷鍵管理器**

```python
# 在 __init__ 中
if USE_PYNPUT_HOTKEY:
    self.hotkey_manager = HotkeyManager()
else:
    self.hotkey_manager = None
```

3. **替換快捷鍵註冊邏輯**

```python
def register_system_hotkeys(self):
    """註冊系統快捷鍵"""
    if USE_PYNPUT_HOTKEY:
        # 使用 pynput
        self.hotkey_manager.register('f9', self.start_recording, "開始錄製")
        self.hotkey_manager.register('f10', self.pause_recording, "暫停錄製")
        self.hotkey_manager.register('f11', self.stop_recording, "停止錄製")
    else:
        # 使用舊版 keyboard
        keyboard.add_hotkey('f9', self.start_recording)
        keyboard.add_hotkey('f10', self.pause_recording)
        keyboard.add_hotkey('f11', self.stop_recording)
```

---

## 🧪 任務 2：v2.7.7 時間語法測試

### 測試 1：錄製功能

**測試步驟：**

1. 啟動 ChroLens Mimic
2. 點擊「開始錄製」
3. 執行以下操作：
   - 按下鍵盤按鍵 '7'
   - 等待 1 秒
   - 滑鼠點擊
   - 等待 0.5 秒
   - 移動滑鼠
4. 停止錄製
5. 查看生成的文字腳本

**預期結果：**

```
>按下7,50ms
>間隔1000ms
>左鍵點擊(100,200),50ms
>間隔500ms
>移動至(300,400),0ms
```

### 測試 2：腳本執行

**測試步驟：**

1. 創建測試腳本：

```
>按下7,50ms
>間隔1000ms
>按下8,50ms
```

2. 執行腳本
3. 觀察時間間隔是否正確

**預期結果：**

- 按下 7
- 等待 1 秒
- 按下 8

### 測試 3：編輯器讀寫

**測試步驟：**

1. 開啟文字編輯器
2. 輸入新格式指令
3. 儲存腳本
4. 重新載入腳本
5. 檢查格式是否保持

**預期結果：**

- 格式正確保存
- 重新載入後格式不變

### 測試 4：舊格式轉換

**測試步驟：**

1. 載入舊格式腳本（包含 T= 時間戳）
2. 檢查是否自動轉換
3. 查看轉換後的格式

**預期結果：**

- 自動偵測舊格式
- 顯示轉換通知
- 正確轉換為新格式

---

## 📊 實施時程

### 第 1 天（今天）

- [x] 創建實施計畫
- [ ] 安裝 pynput
- [ ] 創建 hotkey_manager.py
- [ ] 基本整合測試

### 第 2 天

- [ ] 完整整合快捷鍵管理器
- [ ] 測試所有快捷鍵功能
- [ ] v2.7.7 時間語法測試

### 第 3 天

- [ ] 修復發現的問題
- [ ] 完整測試
- [ ] 準備發布 v2.7.8

---

## 🎯 成功標準

### 快捷鍵系統

- ✅ 所有系統快捷鍵正常工作
- ✅ 腳本快捷鍵正常工作
- ✅ 不需要管理員權限
- ✅ Windows 11 相容

### 時間語法

- ✅ 錄製生成新格式
- ✅ 新格式腳本正確執行
- ✅ 時間間隔準確
- ✅ 舊格式自動轉換

---

**準備開始實施！**
