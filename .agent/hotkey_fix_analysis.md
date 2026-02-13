# ChroLens Mimic 快捷鍵問題分析與修復方案

## 📋 問題報告

### 使用者回報（2.7.6版本）

```
問題：快捷鍵無法使用
- 使用管理員權限開啟
- 執行錄製、暫停、停止等快捷鍵都不能按
- 自己更改的快捷鍵也不能按
- 設定腳本快捷鍵（F12, ALT+F1, ALT+F2）都不能用
- 只能手動執行
- 停止設定 8 執行 7 錄製原始的
- 腳本切換原本設定F1 F2 ALT+F1 ALT+F2 都不能
```

### 對比資訊

- **2.5版本**：快捷鍵正常，但錄製後動作沒有出來
- **2.7.6版本**：快捷鍵完全無法使用

---

## 🔍 問題分析

### 可能原因

#### 1. keyboard 模組的已知問題

Python `keyboard` 模組在某些情況下會失效：

- Windows 11 的安全性更新可能阻擋低級別鍵盤鉤子
- 某些防毒軟體會阻擋 keyboard 模組
- UAC (使用者帳戶控制) 可能干擾快捷鍵註冊
- 快捷鍵衝突（與其他程式或系統快捷鍵）

#### 2. 版本差異

從 2.5 到 2.7.6 的變更可能引入了問題：

- 快捷鍵註冊邏輯的改變
- 事件處理機制的修改
- 新增功能導致的衝突

#### 3. 快捷鍵註冊時機

- 註冊時機不當（太早或太晚）
- 註冊後被意外清除
- 多次註冊導致衝突

---

## 🔧 解決方案

### 方案 A：使用 pynput 替代 keyboard（推薦）

`pynput` 是一個更穩定的替代方案，不需要管理員權限：

```python
from pynput import keyboard as pynput_keyboard

class HotkeyManager:
    def __init__(self):
        self.hotkeys = {}
        self.listener = None

    def register_hotkey(self, hotkey_combo, callback):
        """
        註冊快捷鍵
        hotkey_combo: 例如 '<ctrl>+<alt>+a'
        """
        try:
            # 解析快捷鍵組合
            keys = self._parse_hotkey(hotkey_combo)
            self.hotkeys[frozenset(keys)] = callback

            if not self.listener:
                self.listener = pynput_keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release
                )
                self.listener.start()

            return True
        except Exception as e:
            print(f"註冊快捷鍵失敗: {e}")
            return False

    def _parse_hotkey(self, hotkey_str):
        """解析快捷鍵字串"""
        # 實現解析邏輯
        pass

    def _on_press(self, key):
        """按鍵按下事件"""
        # 檢查是否匹配已註冊的快捷鍵
        pass

    def _on_release(self, key):
        """按鍵釋放事件"""
        pass
```

### 方案 B：改進 keyboard 模組使用方式

如果繼續使用 `keyboard` 模組，需要：

#### 1. 確保管理員權限

```python
import ctypes
import sys

def ensure_admin():
    """確保以管理員權限運行"""
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # 重新以管理員權限啟動
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
```

#### 2. 延遲註冊快捷鍵

```python
def delayed_hotkey_registration():
    """延遲註冊快捷鍵，確保系統準備就緒"""
    time.sleep(1)  # 等待1秒
    register_all_hotkeys()
```

#### 3. 添加健康檢查

```python
def check_hotkey_health():
    """定期檢查快捷鍵是否仍然有效"""
    for hotkey_name, handler in self._hotkey_handlers.items():
        if not keyboard.is_pressed(hotkey_name):
            # 重新註冊
            self.re_register_hotkey(hotkey_name)
```

#### 4. 使用 suppress=True

```python
keyboard.add_hotkey(
    hotkey,
    callback,
    suppress=True,  # 阻止快捷鍵傳遞給其他程式
    trigger_on_release=False
)
```

### 方案 C：混合方案（最穩定）

結合多種方法確保快捷鍵可用：

```python
class RobustHotkeyManager:
    def __init__(self):
        self.method = self._detect_best_method()
        self.fallback_methods = []

    def _detect_best_method(self):
        """檢測最佳快捷鍵方法"""
        # 1. 嘗試 pynput
        try:
            from pynput import keyboard
            return 'pynput'
        except:
            pass

        # 2. 嘗試 keyboard (需要管理員)
        try:
            import keyboard
            if self._test_keyboard():
                return 'keyboard'
        except:
            pass

        # 3. 使用 tkinter 快捷鍵（最後手段）
        return 'tkinter'

    def register_hotkey(self, hotkey, callback):
        """使用最佳方法註冊快捷鍵"""
        if self.method == 'pynput':
            return self._register_pynput(hotkey, callback)
        elif self.method == 'keyboard':
            return self._register_keyboard(hotkey, callback)
        else:
            return self._register_tkinter(hotkey, callback)
```

---

## 📝 實施步驟

### 步驟 1：診斷當前問題

創建診斷工具：

```python
def diagnose_hotkey_system():
    """診斷快捷鍵系統"""
    report = []

    # 1. 檢查管理員權限
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    report.append(f"管理員權限: {'是' if is_admin else '否'}")

    # 2. 檢查 keyboard 模組
    try:
        import keyboard
        keyboard.add_hotkey('f12', lambda: None)
        keyboard.remove_hotkey('f12')
        report.append("keyboard 模組: 正常")
    except Exception as e:
        report.append(f"keyboard 模組: 異常 - {e}")

    # 3. 檢查 pynput 可用性
    try:
        from pynput import keyboard as pk
        report.append("pynput 模組: 可用")
    except:
        report.append("pynput 模組: 不可用")

    # 4. 檢查快捷鍵衝突
    # ...

    return "\n".join(report)
```

### 步驟 2：實施修復

1. 安裝 pynput：`pip install pynput`
2. 創建新的快捷鍵管理器
3. 遷移現有快捷鍵到新系統
4. 添加降級方案

### 步驟 3：測試

1. 在不同環境測試（Win10, Win11）
2. 測試有無管理員權限
3. 測試快捷鍵衝突情況
4. 長時間運行測試

---

## 🎯 推薦方案

### 立即實施：方案 A (pynput)

**優點：**

- ✅ 不需要管理員權限
- ✅ 更穩定可靠
- ✅ 跨平台支援
- ✅ 活躍維護

**缺點：**

- ⚠️ 需要重寫快捷鍵邏輯
- ⚠️ 新增依賴

**實施難度：** 中等

**預期效果：** 完全解決快捷鍵問題

---

## 📊 對比表

| 方案          |   穩定性   | 需要管理員 | 實施難度 |   推薦度   |
| :------------ | :--------: | :--------: | :------: | :--------: |
| pynput        | ⭐⭐⭐⭐⭐ |     ❌     |    中    | ⭐⭐⭐⭐⭐ |
| 改進 keyboard |   ⭐⭐⭐   |     ✅     |    低    |   ⭐⭐⭐   |
| 混合方案      |  ⭐⭐⭐⭐  |    部分    |    高    |  ⭐⭐⭐⭐  |
| tkinter       |    ⭐⭐    |     ❌     |    低    |    ⭐⭐    |

---

## 🚀 下一步

1. **創建診斷工具** - 幫助使用者診斷問題
2. **實施 pynput 方案** - 作為主要解決方案
3. **保留 keyboard 作為備用** - 向下相容
4. **添加快捷鍵測試工具** - 方便使用者測試
5. **更新文檔** - 說明快捷鍵使用方式

---

**建議立即實施 pynput 方案以徹底解決快捷鍵問題！**
