"""
ChroLens Mimic - Pynput 快捷鍵替代方案
解決 keyboard 模組需要長按才能觸發的問題
"""

from pynput import keyboard as pynput_kb
import threading
import time

class PynputHotkeyManager:
    """
    使用 pynput 實現的快捷鍵管理器
    按下立即觸發，不需要長按
    """
    
    def __init__(self):
        self.hotkeys = {}  # {hotkey_str: callback}
        self.pressed_keys = set()  # 當前按下的鍵
        self.listener = None
        self.last_trigger_time = {}  # 防止重複觸發
        self.cooldown = 0.3  # 冷卻時間（秒）
        
    def _normalize_key(self, key):
        """標準化按鍵名稱"""
        try:
            # 功能鍵
            if hasattr(key, 'name'):
                return key.name.lower()
            # 字符鍵
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            # 其他
            return str(key).lower().replace('key.', '')
        except:
            return str(key).lower()
    
    def _parse_hotkey(self, hotkey_str):
        """
        解析快捷鍵字串
        例如: 'ctrl+shift+f9' -> ['ctrl', 'shift', 'f9']
        """
        parts = hotkey_str.lower().replace(' ', '').split('+')
        normalized = []
        for part in parts:
            # 標準化修飾鍵名稱
            if part in ['control', 'ctrl']:
                normalized.append('ctrl')
            elif part in ['alt', 'menu']:
                normalized.append('alt')
            elif part in ['shift']:
                normalized.append('shift')
            elif part in ['win', 'cmd', 'super']:
                normalized.append('cmd')
            else:
                normalized.append(part)
        return normalized
    
    def _is_hotkey_pressed(self, hotkey_parts):
        """檢查快捷鍵是否被按下"""
        # 獲取當前按下的鍵的標準化名稱
        current_keys = set(self._normalize_key(k) for k in self.pressed_keys)
        
        # 檢查所有部分是否都被按下
        for part in hotkey_parts:
            if part not in current_keys:
                return False
        return True
    
    def add_hotkey(self, hotkey_str, callback, suppress=False, trigger_on_release=False):
        """
        添加快捷鍵
        
        Args:
            hotkey_str: 快捷鍵字串，例如 'f9', 'ctrl+shift+f9'
            callback: 回調函數
            suppress: 是否抑制原始按鍵（pynput 不支持，保留參數以兼容）
            trigger_on_release: 是否在釋放時觸發（預設 False，按下時觸發）
        """
        hotkey_parts = self._parse_hotkey(hotkey_str)
        self.hotkeys[hotkey_str] = {
            'parts': hotkey_parts,
            'callback': callback,
            'trigger_on_release': trigger_on_release
        }
        
        # 如果監聽器還沒啟動，啟動它
        if self.listener is None or not self.listener.running:
            self.start_listener()
    
    def start_listener(self):
        """啟動鍵盤監聽器"""
        if self.listener and self.listener.running:
            return
        
        self.listener = pynput_kb.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
    
    def _on_press(self, key):
        """按鍵按下事件"""
        # 安全機制：如果同時按下的鍵過多（可能是卡鍵或漏掉 release 事件），強制重置
        if len(self.pressed_keys) > 10:
            self.pressed_keys.clear()
            
        self.pressed_keys.add(key)
        
        # 檢查所有快捷鍵
        for hotkey_str, hotkey_info in self.hotkeys.items():
            # 如果設定為釋放時觸發，跳過
            if hotkey_info['trigger_on_release']:
                continue
            
            # 檢查快捷鍵是否匹配
            if self._is_hotkey_pressed(hotkey_info['parts']):
                # 檢查冷卻時間
                current_time = time.time()
                last_time = self.last_trigger_time.get(hotkey_str, 0)
                
                if current_time - last_time > self.cooldown:
                    self.last_trigger_time[hotkey_str] = current_time
                    
                    # 在新線程中執行回調，避免阻塞監聽器
                    threading.Thread(
                        target=hotkey_info['callback'],
                        daemon=True
                    ).start()
    
    def _on_release(self, key):
        """按鍵釋放事件"""
        # 檢查釋放時觸發的快捷鍵
        for hotkey_str, hotkey_info in self.hotkeys.items():
            if not hotkey_info['trigger_on_release']:
                continue
            
            if self._is_hotkey_pressed(hotkey_info['parts']):
                current_time = time.time()
                last_time = self.last_trigger_time.get(hotkey_str, 0)
                
                if current_time - last_time > self.cooldown:
                    self.last_trigger_time[hotkey_str] = current_time
                    
                    threading.Thread(
                        target=hotkey_info['callback'],
                        daemon=True
                    ).start()
        
        # 移除釋放的鍵
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
    
    def remove_hotkey(self, hotkey_str):
        """移除快捷鍵"""
        if hotkey_str in self.hotkeys:
            del self.hotkeys[hotkey_str]
    
    def stop(self):
        """停止監聽器"""
        if self.listener:
            self.listener.stop()
            self.listener = None


# 全域實例
_pynput_manager = None

def get_pynput_manager():
    """獲取全域 pynput 管理器實例"""
    global _pynput_manager
    if _pynput_manager is None:
        _pynput_manager = PynputHotkeyManager()
    return _pynput_manager


# 兼容 keyboard 模組的 API
def add_hotkey(hotkey, callback, suppress=False, trigger_on_release=False):
    """
    兼容 keyboard.add_hotkey 的 API
    使用 pynput 實現，按下立即觸發
    """
    manager = get_pynput_manager()
    manager.add_hotkey(hotkey, callback, suppress, trigger_on_release)
    return hotkey  # 返回 hotkey 字串作為 handler


def remove_hotkey(hotkey_or_handler):
    """兼容 keyboard.remove_hotkey 的 API"""
    manager = get_pynput_manager()
    manager.remove_hotkey(hotkey_or_handler)


# 測試代碼
if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("Pynput 快捷鍵管理器測試")
    print("="*70)
    print()
    
    def test_f9():
        print(f"[{time.strftime('%H:%M:%S')}] ✓ F9 觸發！（應該按下立即觸發）")
    
    def test_f10():
        print(f"[{time.strftime('%H:%M:%S')}] ✓ F10 觸發！")
    
    def test_f11():
        print(f"[{time.strftime('%H:%M:%S')}] ✓ F11 觸發！")
    
    def test_ctrl_f1():
        print(f"[{time.strftime('%H:%M:%S')}] ✓ Ctrl+F1 觸發！")
    
    # 註冊快捷鍵
    add_hotkey('f9', test_f9, trigger_on_release=False)
    add_hotkey('f10', test_f10, trigger_on_release=False)
    add_hotkey('f11', test_f11, trigger_on_release=False)
    add_hotkey('ctrl+f1', test_ctrl_f1, trigger_on_release=False)
    
    print("已註冊快捷鍵：")
    print("  F9  - 測試 F9")
    print("  F10 - 測試 F10")
    print("  F11 - 測試 F11")
    print("  Ctrl+F1 - 測試組合鍵")
    print()
    print("請快速按下快捷鍵測試（不要長按）")
    print("按 Ctrl+C 結束測試")
    print("="*70)
    print()
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n測試結束")
        manager = get_pynput_manager()
        manager.stop()
