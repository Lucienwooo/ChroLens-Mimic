# -*- coding: utf-8 -*-
"""
按鍵處理增強模組 - ChroLens_Mimic
解決 Alt 等修飾鍵的錄製和執行問題
"""

import keyboard
import time
from typing import Dict, Set, List, Optional


class KeyboardHandler:
    """增強的鍵盤處理器"""
    
    # 按鍵名稱標準化映射
    KEY_NORMALIZATION = {
        # Alt 鍵
        'alt_l': 'alt',
        'alt_r': 'alt',
        'left alt': 'alt',
        'right alt': 'alt',
        'alt gr': 'alt',
        
        # Ctrl 鍵
        'ctrl_l': 'ctrl',
        'ctrl_r': 'ctrl',
        'left ctrl': 'ctrl',
        'right ctrl': 'ctrl',
        'control': 'ctrl',
        
        # Shift 鍵
        'shift_l': 'shift',
        'shift_r': 'shift',
        'left shift': 'shift',
        'right shift': 'shift',
        
        # Win 鍵
        'win_l': 'win',
        'win_r': 'win',
        'left windows': 'win',
        'right windows': 'win',
        'windows': 'win',
        'cmd': 'win',
        'command': 'win',
        
        # 特殊鍵
        'return': 'enter',
        'escape': 'esc',
        'delete': 'del',
        'insert': 'ins',
        'page up': 'page_up',
        'page down': 'page_down',
        'num lock': 'num_lock',
        'caps lock': 'caps_lock',
        'scroll lock': 'scroll_lock',
        'print screen': 'print_screen',
        
        # 方向鍵
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
    }
    
    # 修飾鍵列表
    MODIFIER_KEYS = {'alt', 'ctrl', 'shift', 'win'}
    
    # 功能鍵列表
    FUNCTION_KEYS = {f'f{i}' for i in range(1, 25)}
    
    def __init__(self, logger=None):
        """初始化"""
        self.logger = logger or print
        self._pressed_keys: Set[str] = set()  # 當前按下的按鍵
        self._key_press_times: Dict[str, float] = {}  # 按鍵按下時間
        self._recording = False
        
    def normalize_key_name(self, key_name: str) -> str:
        """
        標準化按鍵名稱
        
        Args:
            key_name: 原始按鍵名稱
            
        Returns:
            標準化後的按鍵名稱
        """
        if not key_name:
            return key_name
            
        # 轉小寫
        key_lower = key_name.lower().strip()
        
        # 查找映射表
        normalized = self.KEY_NORMALIZATION.get(key_lower, key_lower)
        
        # 記錄標準化過程（僅在有變化時）
        if normalized != key_lower and self.logger:
            self.logger(f"[按鍵標準化] '{key_name}' → '{normalized}'")
        
        return normalized
    
    def is_modifier_key(self, key_name: str) -> bool:
        """判斷是否為修飾鍵"""
        normalized = self.normalize_key_name(key_name)
        return normalized in self.MODIFIER_KEYS
    
    def record_key_press(self, key_name: str) -> Dict:
        """
        記錄按鍵按下事件
        
        Args:
            key_name: 按鍵名稱
            
        Returns:
            事件字典
        """
        normalized = self.normalize_key_name(key_name)
        current_time = time.time()
        
        # 記錄按下狀態
        self._pressed_keys.add(normalized)
        self._key_press_times[normalized] = current_time
        
        event = {
            'type': 'keyboard',
            'event': 'down',
            'name': normalized,
            'original_name': key_name,
            'time': current_time,
            'is_modifier': self.is_modifier_key(key_name),
            'pressed_keys': list(self._pressed_keys)  # 記錄當前所有按下的鍵
        }
        
        if self.logger:
            modifiers = [k for k in self._pressed_keys if k in self.MODIFIER_KEYS]
            if modifiers:
                self.logger(f"[按鍵按下] {normalized} (修飾鍵: {'+'.join(modifiers)})")
            else:
                self.logger(f"[按鍵按下] {normalized}")
        
        return event
    
    def record_key_release(self, key_name: str) -> Dict:
        """
        記錄按鍵釋放事件
        
        Args:
            key_name: 按鍵名稱
            
        Returns:
            事件字典
        """
        normalized = self.normalize_key_name(key_name)
        current_time = time.time()
        
        # 計算按鍵持續時間
        press_time = self._key_press_times.get(normalized, current_time)
        duration = current_time - press_time
        
        # 移除按下狀態
        self._pressed_keys.discard(normalized)
        self._key_press_times.pop(normalized, None)
        
        event = {
            'type': 'keyboard',
            'event': 'up',
            'name': normalized,
            'original_name': key_name,
            'time': current_time,
            'duration': duration,
            'is_modifier': self.is_modifier_key(key_name)
        }
        
        if self.logger:
            self.logger(f"[按鍵釋放] {normalized} (持續: {duration:.3f}s)")
        
        return event
    
    def execute_key_press(self, key_name: str, use_scan_code: bool = False):
        """
        執行按鍵按下
        
        Args:
            key_name: 按鍵名稱
            use_scan_code: 是否使用掃描碼（更底層，某些遊戲需要）
        """
        normalized = self.normalize_key_name(key_name)
        
        try:
            if use_scan_code:
                # 使用掃描碼模式（更底層）
                keyboard.press(normalized)
            else:
                # 標準模式
                keyboard.press(normalized)
            
            self._pressed_keys.add(normalized)
            
            if self.logger:
                self.logger(f"[執行] 按下 {normalized}")
                
        except Exception as e:
            if self.logger:
                self.logger(f"[錯誤] 按鍵按下失敗 '{normalized}': {e}")
            raise
    
    def execute_key_release(self, key_name: str, use_scan_code: bool = False):
        """
        執行按鍵釋放
        
        Args:
            key_name: 按鍵名稱
            use_scan_code: 是否使用掃描碼
        """
        normalized = self.normalize_key_name(key_name)
        
        try:
            if use_scan_code:
                keyboard.release(normalized)
            else:
                keyboard.release(normalized)
            
            self._pressed_keys.discard(normalized)
            
            if self.logger:
                self.logger(f"[執行] 釋放 {normalized}")
                
        except Exception as e:
            if self.logger:
                self.logger(f"[錯誤] 按鍵釋放失敗 '{normalized}': {e}")
            # 不拋出異常，繼續執行
    
    def execute_key_combination(self, keys: List[str], hold_duration: float = 0.05):
        """
        執行組合鍵
        
        Args:
            keys: 按鍵列表，例如 ['ctrl', 'c']
            hold_duration: 按鍵持續時間（秒）
        """
        if not keys:
            return
        
        normalized_keys = [self.normalize_key_name(k) for k in keys]
        
        try:
            # 按順序按下所有鍵
            for key in normalized_keys:
                self.execute_key_press(key)
                time.sleep(0.01)  # 短暫延遲確保按鍵順序
            
            # 持續一段時間
            time.sleep(hold_duration)
            
            # 按相反順序釋放所有鍵
            for key in reversed(normalized_keys):
                self.execute_key_release(key)
                time.sleep(0.01)
            
            if self.logger:
                self.logger(f"[執行] 組合鍵 {'+'.join(normalized_keys)}")
                
        except Exception as e:
            if self.logger:
                self.logger(f"[錯誤] 組合鍵執行失敗: {e}")
            # 確保所有按鍵都被釋放
            for key in normalized_keys:
                try:
                    self.execute_key_release(key)
                except:
                    pass
    
    def release_all_keys(self):
        """釋放所有當前按下的按鍵"""
        if not self._pressed_keys:
            return
        
        keys_to_release = list(self._pressed_keys)
        
        if self.logger:
            self.logger(f"[清理] 釋放所有按鍵: {', '.join(keys_to_release)}")
        
        for key in keys_to_release:
            try:
                keyboard.release(key)
            except Exception as e:
                if self.logger:
                    self.logger(f"[警告] 釋放按鍵 '{key}' 失敗: {e}")
        
        self._pressed_keys.clear()
        self._key_press_times.clear()
    
    def release_all_modifiers(self):
        """釋放所有修飾鍵"""
        modifiers_to_release = [k for k in self._pressed_keys if k in self.MODIFIER_KEYS]
        
        if not modifiers_to_release:
            return
        
        if self.logger:
            self.logger(f"[清理] 釋放修飾鍵: {', '.join(modifiers_to_release)}")
        
        for key in modifiers_to_release:
            try:
                keyboard.release(key)
                self._pressed_keys.discard(key)
                self._key_press_times.pop(key, None)
            except Exception as e:
                if self.logger:
                    self.logger(f"[警告] 釋放修飾鍵 '{key}' 失敗: {e}")
    
    def get_pressed_keys(self) -> Set[str]:
        """獲取當前按下的所有按鍵"""
        return self._pressed_keys.copy()
    
    def is_key_pressed(self, key_name: str) -> bool:
        """檢查指定按鍵是否被按下"""
        normalized = self.normalize_key_name(key_name)
        return normalized in self._pressed_keys
    
    def validate_key_sequence(self, events: List[Dict]) -> List[str]:
        """
        驗證按鍵序列的完整性
        
        Args:
            events: 按鍵事件列表
            
        Returns:
            問題列表（空列表表示沒有問題）
        """
        issues = []
        press_count = {}
        release_count = {}
        
        for event in events:
            if event.get('type') != 'keyboard':
                continue
            
            key = event.get('name', '')
            event_type = event.get('event', '')
            
            if event_type == 'down':
                press_count[key] = press_count.get(key, 0) + 1
            elif event_type == 'up':
                release_count[key] = release_count.get(key, 0) + 1
        
        # 檢查按下和釋放是否配對
        all_keys = set(press_count.keys()) | set(release_count.keys())
        for key in all_keys:
            presses = press_count.get(key, 0)
            releases = release_count.get(key, 0)
            
            if presses != releases:
                issues.append(
                    f"按鍵 '{key}' 不配對: {presses} 次按下, {releases} 次釋放"
                )
        
        return issues


# 全域實例（可選）
_global_handler: Optional[KeyboardHandler] = None


def get_keyboard_handler(logger=None) -> KeyboardHandler:
    """獲取全域鍵盤處理器實例"""
    global _global_handler
    if _global_handler is None:
        _global_handler = KeyboardHandler(logger)
    return _global_handler
