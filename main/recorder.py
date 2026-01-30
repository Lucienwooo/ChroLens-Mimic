import keyboard
import mouse
import time
import threading
import ctypes
import ctypes.wintypes
from pynput.mouse import Controller, Listener
import pynput  # 加入這行
import win32gui  # 新增：用於視窗檢測
import win32api
import win32con
import os
import cv2
import numpy as np
from PIL import ImageGrab

#  優化：引入更快的螢幕截圖庫
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("[警告] mss 庫未安裝，將使用較慢的 PIL.ImageGrab。建議執行: pip install mss")

#  重構：匯入新模組
try:
    from bezier_mouse import BezierMouseMover
    BEZIER_AVAILABLE = True
except ImportError:
    BEZIER_AVAILABLE = False
    print("️ BezierMouseMover 未載入，將使用傳統直線移動")

#  v2.8.2: 匯入 YOLO 物件偵測模組
try:
    from yolo_detector import YOLODetector, get_detector, YOLO_AVAILABLE
except ImportError:
    YOLO_AVAILABLE = False
    YOLODetector = None
    get_detector = None
    print("️ YOLO 模組未載入，物件偵測功能不可用")


# ==================== 觸發器管理器 (v2.8.0+) ====================
class TriggerManager:
    """管理觸發器的並行執行
    
    支援三種觸發器類型：
    1. interval_trigger: 定時觸發（每 N 秒執行）
    2. condition_trigger: 條件觸發（偵測到目標時執行）
    3. priority_trigger: 優先觸發（中斷當前執行）
    """
    
    def __init__(self, recorder, logger=None):
        self.recorder = recorder
        self.logger = logger or (lambda s: None)
        self._triggers = []  # List of trigger configs
        self._threads = []  # Running trigger threads
        self._running = False
        self._lock = threading.Lock()
        self._last_trigger_time = {}  # Cooldown tracking
    
    def add_trigger(self, trigger_config):
        """添加觸發器配置"""
        self._triggers.append(trigger_config)
    
    def clear_triggers(self):
        """清空所有觸發器"""
        self._triggers.clear()
        self._last_trigger_time.clear()
    
    def start(self):
        """啟動所有觸發器"""
        if self._running:
            return
        self._running = True
        
        for trigger in self._triggers:
            trigger_type = trigger.get('type')
            if trigger_type == 'interval_trigger':
                t = threading.Thread(
                    target=self._run_interval_trigger,
                    args=(trigger,),
                    daemon=True
                )
                t.start()
                self._threads.append(t)
            elif trigger_type == 'condition_trigger':
                t = threading.Thread(
                    target=self._run_condition_trigger,
                    args=(trigger,),
                    daemon=True
                )
                t.start()
                self._threads.append(t)
            elif trigger_type == 'priority_trigger':
                t = threading.Thread(
                    target=self._run_priority_trigger,
                    args=(trigger,),
                    daemon=True
                )
                t.start()
                self._threads.append(t)
    
    def stop(self):
        """停止所有觸發器"""
        self._running = False
        # 等待所有線程結束
        for t in self._threads:
            t.join(timeout=1.0)
        self._threads.clear()
    
    def _run_interval_trigger(self, trigger):
        """執行定時觸發器"""
        interval_ms = trigger.get('interval_ms', 30000)
        actions = trigger.get('actions', [])
        interval_sec = interval_ms / 1000.0
        
        while self._running and self.recorder.playing:
            # 執行動作
            with self._lock:
                for action in actions:
                    if not self._running:
                        break
                    self._execute_action_text(action)
            
            # 等待間隔
            wait_start = time.time()
            while self._running and self.recorder.playing:
                if time.time() - wait_start >= interval_sec:
                    break
                time.sleep(0.1)
    
    def _run_condition_trigger(self, trigger):
        """執行條件觸發器"""
        target = trigger.get('target', '')
        cooldown_ms = trigger.get('cooldown_ms', 5000)
        actions = trigger.get('actions', [])
        cooldown_sec = cooldown_ms / 1000.0
        trigger_id = f"condition_{target}"
        
        while self._running and self.recorder.playing:
            # 檢查冷卻
            last_time = self._last_trigger_time.get(trigger_id, 0)
            if time.time() - last_time < cooldown_sec:
                time.sleep(0.1)
                continue
            
            # 檢查條件（圖片是否存在）
            if self.recorder._images_dir:
                found = self.recorder._find_image_on_screen(target)
                if found:
                    self._last_trigger_time[trigger_id] = time.time()
                    with self._lock:
                        for action in actions:
                            if not self._running:
                                break
                            self._execute_action_text(action)
            
            time.sleep(0.2)  # 偵測間隔
    
    def _run_priority_trigger(self, trigger):
        """執行優先觸發器（偵測到目標時中斷當前執行）"""
        target = trigger.get('target', '')
        actions = trigger.get('actions', [])
        trigger_id = f"priority_{target}"
        
        while self._running and self.recorder.playing:
            # 檢查冷卻（優先觸發器也需要冷卻避免頻繁觸發）
            last_time = self._last_trigger_time.get(trigger_id, 0)
            if time.time() - last_time < 2.0:  # 2秒冷卻
                time.sleep(0.1)
                continue
            
            # 檢查條件
            if self.recorder._images_dir:
                found = self.recorder._find_image_on_screen(target)
                if found:
                    self._last_trigger_time[trigger_id] = time.time()
                    self.logger(f"[優先觸發] 偵測到 {target}，中斷當前執行")
                    with self._lock:
                        for action in actions:
                            if not self._running:
                                break
                            self._execute_action_text(action)
            
            time.sleep(0.3)  # 優先觸發偵測間隔
    
    def _execute_action_text(self, action_text):
        """執行單行動作文字"""
        try:
            # 解析簡單動作
            if action_text.startswith('>按'):
                # 按鍵動作：>按F1, 延遲100ms
                import re
                match = re.match(r'>按(\w+)', action_text)
                if match:
                    key = match.group(1)
                    import keyboard
                    keyboard.press_and_release(key)
            elif action_text.startswith('>跳到#'):
                # 跳轉：目前在觸發器中的跳轉需要特殊處理
                label = action_text.replace('>跳到#', '').strip()
                self.recorder._pending_jump = label
            elif action_text.startswith('>延遲'):
                match = re.match(r'>延遲(\d+)(ms|秒)', action_text)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    delay = value / 1000.0 if unit == 'ms' else value
                    time.sleep(delay)
        except Exception as e:
            self.logger(f"[觸發器] 執行動作失敗: {e}")


# ==================== 並行執行器 (v2.8.0+) ====================
class ParallelExecutor:
    """管理並行區塊的多線程執行
    
    執行多個線程，每個線程內的動作按順序執行，
    但不同線程之間並行執行。
    """
    
    def __init__(self, recorder, logger=None):
        self.recorder = recorder
        self.logger = logger or (lambda s: None)
        self._threads = []
        self._running = False
        self._lock = threading.Lock()
    
    def execute_parallel_block(self, parallel_event):
        """執行並行區塊"""
        threads_config = parallel_event.get('threads', [])
        if not threads_config:
            return
        
        self._running = True
        self._threads.clear()
        
        # 為每個配置創建並啟動線程
        for thread_config in threads_config:
            thread_name = thread_config.get('name', 'unnamed')
            actions = thread_config.get('actions', [])
            
            t = threading.Thread(
                target=self._run_thread,
                args=(thread_name, actions),
                daemon=True,
                name=f"Parallel-{thread_name}"
            )
            self._threads.append(t)
            t.start()
            self.logger(f"[並行] 啟動線程: {thread_name}")
        
        # 等待所有線程完成
        for t in self._threads:
            t.join()
        
        self._running = False
        self.logger("[並行] 所有線程已完成")
    
    def _run_thread(self, thread_name, actions):
        """執行單個線程的動作"""
        for action in actions:
            if not self._running or not self.recorder.playing:
                break
            
            with self._lock:
                try:
                    self._execute_action_text(action)
                except Exception as e:
                    self.logger(f"[並行-{thread_name}] 動作執行失敗: {e}")
    
    def _execute_action_text(self, action_text):
        """執行單行動作文字（與 TriggerManager 共用邏輯）"""
        try:
            if action_text.startswith('>按'):
                import re
                match = re.match(r'>按(\w+)', action_text)
                if match:
                    key = match.group(1)
                    import keyboard
                    keyboard.press_and_release(key)
            elif action_text.startswith('>延遲'):
                import re
                match = re.match(r'>延遲(\d+)(ms|秒)', action_text)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    delay = value / 1000.0 if unit == 'ms' else value
                    time.sleep(delay)
            elif action_text.startswith('>左鍵點擊'):
                import re
                match = re.match(r'>左鍵點擊\((\d+),(\d+)\)', action_text)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                    import mouse
                    mouse.move(x, y)
                    mouse.click('left')
        except Exception as e:
            self.logger(f"[並行] 動作執行失敗: {e}")
    
    def stop(self):
        """停止所有線程"""
        self._running = False


# ==================== 狀態機執行器 (v2.8.0+) ====================
class StateMachine:
    """執行狀態機邏輯
    
    狀態機由多個狀態組成，每個狀態包含：
    - actions: 該狀態下執行的動作列表
    - transitions: 狀態切換規則 {condition: target_state}
    """
    
    def __init__(self, recorder, logger=None):
        self.recorder = recorder
        self.logger = logger or (lambda s: None)
        self._current_state = None
        self._states = {}
        self._running = False
        self._lock = threading.Lock()
    
    def load(self, state_machine_event):
        """載入狀態機配置"""
        self._states = state_machine_event.get('states', {})
        self._current_state = state_machine_event.get('initial_state', None)
        
        if not self._current_state and self._states:
            self._current_state = list(self._states.keys())[0]
        
        self.logger(f"[狀態機] 已載入，初始狀態: {self._current_state}")
    
    def run(self):
        """執行狀態機（循環執行直到停止）"""
        self._running = True
        
        while self._running and self.recorder.playing:
            if not self._current_state or self._current_state not in self._states:
                self.logger(f"[狀態機] 無效狀態: {self._current_state}，停止執行")
                break
            
            state_data = self._states[self._current_state]
            actions = state_data.get('actions', [])
            transitions = state_data.get('transitions', {})
            
            self.logger(f"[狀態機] 進入狀態: {self._current_state}")
            
            # 執行狀態內的動作
            last_result = None
            for action in actions:
                if not self._running:
                    break
                
                # 檢查是否為狀態切換指令
                if action.startswith('>切換>') or action.startswith('>>切換>') or action.startswith('>>>切換>'):
                    continue  # 切換指令在動作執行後處理
                
                with self._lock:
                    last_result = self._execute_action_text(action)
            
            if not self._running:
                break
            
            # 根據結果處理狀態切換
            next_state = None
            if last_result == 'success' and 'success' in transitions:
                next_state = transitions['success']
            elif last_result == 'failure' and 'failure' in transitions:
                next_state = transitions['failure']
            elif 'default' in transitions:
                next_state = transitions['default']
            
            if next_state and next_state in self._states:
                self._current_state = next_state
            elif next_state:
                self.logger(f"[狀態機] 目標狀態不存在: {next_state}")
                self._running = False
    
    def _execute_action_text(self, action_text):
        """執行單行動作，返回結果 ('success', 'failure', None)"""
        try:
            if action_text.startswith('>按'):
                import re
                match = re.match(r'>按(\w+)', action_text)
                if match:
                    key = match.group(1)
                    import keyboard
                    keyboard.press_and_release(key)
                return 'success'
            elif action_text.startswith('>延遲'):
                import re
                match = re.match(r'>延遲(\d+)(ms|秒)', action_text)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    delay = value / 1000.0 if unit == 'ms' else value
                    time.sleep(delay)
                return None
            elif action_text.startswith('>if>'):
                # 條件檢查：簡化版本
                target = action_text[4:].split(',')[0].strip()
                if self.recorder._images_dir:
                    found = self.recorder._find_image_on_screen(target)
                    return 'success' if found else 'failure'
                return 'failure'
        except Exception as e:
            self.logger(f"[狀態機] 動作執行失敗: {e}")
        return None
    
    def stop(self):
        """停止狀態機"""
        self._running = False


class CoreRecorder:
    """錄製和執行的核心類別
    
     v2.6.5+ 重構改進：
    - 整合 BezierMouseMover（擬真滑鼠移動）
    - 支援標準化 logger（LoggerManager）
    - 預留 OCR 觸發介面
    """
    
    def __init__(self, logger=None):
        #  支援新舊兩種 logger 格式
        # 舊格式：lambda 函式 logger(msg)
        # 新格式：LoggerManager 實例 logger.info(msg)
        self.logger = logger or (lambda s: None)
        self._is_new_logger = hasattr(logger, 'info') if logger else False
        
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self._record_thread = None
        self._play_thread = None
        self._record_start_time = None
        self._mouse_events = []
        self._keyboard_recording = False
        self._recording_mouse = False
        self._paused_k_events = []
        self._current_play_index = 0
        self._target_hwnd = None  # 新增：目標視窗 handle
        self._background_mode = "smart"  # 後台模式：smart, fast_switch, postmessage, foreground
        self._mouse_mode = False  # 新增：滑鼠模式（是否控制真實滑鼠）
        self._mouse_listener = None
        self._pressed_keys = set()
        
        # 圖片辨識相關
        self._image_cache = {}  # 快取已載入的圖片 {display_name: (image_array, image_path)}
        self._images_dir = None  # 圖片目錄路徑
        self._border_window = None  # 邊框視窗
        self._current_region = None  # 當前辨識範圍（全域狀態，由 >範圍結束 清除）
        
        #  新增：圖片追蹤系統（用於追移動目標）
        self._last_found_positions = {}  # {image_name: (x, y, timestamp)}
        self._motion_history = {}  # {image_name: [(x, y, t), ...]}
        self._tracking_mode = {}  # {image_name: True/False} 是否啟用追蹤
        self._max_motion_history = 5  # 最多保留多少幀位置記錄
        
        #  優化：檢查 mss 是否可用
        if MSS_AVAILABLE:
            self._log("[優化] 已啟用 mss 快速截圖引擎", "info")
        else:
            self._log("[優化] mss 不可用，將使用 PIL", "info")
        
        # 貝茲曲線滑鼠移動器
        self._bezier_mover = BezierMouseMover() if BEZIER_AVAILABLE else None
        self._use_bezier = False  # 預設關閉（保持向下相容）
        
        #  v2.7.1+ 新增：變數系統和執行狀態
        self._variables = {}  # 變數儲存 {name: value}
        self._loop_stack = []  # 循環堆疊 [{type, start_index, counter, max_count}]
        self._retry_count = 0  # 重試計數器
        self._timeout_start = None  # 逾時計時開始時間
        self._timeout_duration = None  # 逾時時長（秒）
        self._action_retry_count = {}  # 動作重試計數 {action_id: count}
        self._action_start_time = {}  # 動作開始時間 {action_id: timestamp}
        self._current_try_action = None  # 當前嘗試的動作ID
        self._current_try_max = 0  # 當前嘗試的最大次數
        self._current_try_success = None  # 當前嘗試成功的分支
        self._current_try_failure = None  # 當前嘗試失敗的分支
        
        #  v2.8.0+ 新增：觸發器管理器
        self._trigger_manager = TriggerManager(self, logger)
        self._pending_jump = None  # 觸發器請求的跳轉目標
        
        #  v2.8.2+ 新增：YOLO 物件偵測器
        self._yolo_detector = None
        self._yolo_enabled = False
        if YOLO_AVAILABLE:
            self._yolo_detector = get_detector(logger=lambda m: self._log(m, "info"))
            self._log("[YOLO] YOLOv8s 偵測模組已就緒", "info")
    
    def _log(self, msg: str, level: str = "info"):
        """統一日誌輸出（相容新舊格式）
        
        Args:
            msg: 訊息內容
            level: 日誌等級（info/warning/error/debug）
        """
        if self._is_new_logger:
            # 新格式：LoggerManager
            if level == "info":
                self.logger.info(msg)
            elif level == "warning":
                self.logger.warning(msg)
            elif level == "error":
                self.logger.error(msg)
            elif level == "debug":
                self.logger.debug(msg)
        else:
            # 舊格式：lambda 函式
            self.logger(msg)
    
    def set_bezier_enabled(self, enabled: bool):
        """啟用/停用貝茲曲線滑鼠移動
        
        Args:
            enabled: True = 擬真移動, False = 直線移動（預設）
        """
        if not BEZIER_AVAILABLE:
            self._log("️ BezierMouseMover 未安裝，無法啟用擬真移動", "warning")
            return
        
        self._use_bezier = enabled
        if enabled:
            self._log(" 已啟用擬真滑鼠移動（貝茲曲線）", "info")
        else:
            self._log("️ 已停用擬真移動（直線移動）", "info")

    def set_target_window(self, hwnd):
        """設定目標視窗，只錄製/執行該視窗內的操作"""
        self._target_hwnd = hwnd
        if hwnd:
            self._log(f"已設定目標視窗：hwnd={hwnd}", "info")
        else:
            self._log("已取消目標視窗限定", "info")

    def set_background_mode(self, mode):
        """設定後台執行模式
        
        Args:
            mode: 執行模式
                - "smart": 智能模式（自動選擇最佳方法）
                - "fast_switch": 快速切換模式（高相容性）
                - "postmessage": 純後台模式（PostMessage）
                - "foreground": 前景模式（預設，移動真實滑鼠）
        """
        valid_modes = ["smart", "fast_switch", "postmessage", "foreground"]
        if mode in valid_modes:
            self._background_mode = mode
            # 靜默設定，不顯示日誌
        else:
            pass  # 無效模式也靜默處理
    
    def set_mouse_mode(self, enabled):
        """設定滑鼠模式
        
        Args:
            enabled: True = 控制真實滑鼠游標, False = 使用後台模式
        """
        self._mouse_mode = enabled
        if enabled:
            self.logger(f"滑鼠模式：已啟用（將控制真實滑鼠游標）")
        else:
            self.logger(f"滑鼠模式：已停用（使用後台模式）")

    def _screen_to_client(self, hwnd, screen_x, screen_y):
        """將螢幕座標轉換為視窗內座標"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            client_x = screen_x - left
            client_y = screen_y - top
            return client_x, client_y
        except Exception:
            return screen_x, screen_y

    def _name_to_vk(self, key_name):
        """將按鍵名稱轉換為虛擬鍵碼"""
        # 常用按鍵映射
        key_map = {
            'enter': win32con.VK_RETURN,
            'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB,
            'backspace': win32con.VK_BACK,
            'delete': win32con.VK_DELETE,
            'esc': win32con.VK_ESCAPE,
            'shift': win32con.VK_SHIFT,
            'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
        }
        
        # F1-F12
        for i in range(1, 13):
            key_map[f'f{i}'] = win32con.VK_F1 + i - 1
        
        # 字母和數字
        if len(key_name) == 1:
            if key_name.isalpha():
                return ord(key_name.upper())
            elif key_name.isdigit():
                return ord(key_name)
        
        return key_map.get(key_name.lower(), 0)

    def start_record(self):
        """開始錄製（v2.6.5 - 參考2.5簡化機制）"""
        if self.recording:
            return
        
        #  2.5 風格：不需要重置 keyboard 狀態
        # keyboard.add_hotkey 不受 keyboard.start_recording 影響
        
        self.recording = True
        self.paused = False
        self.events = []
        self._record_start_time = time.time()
        self.logger(f"[{time.ctime()}] 開始錄製")
        self._record_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._record_thread.start()
        return self._record_start_time

    def stop_record(self):
        """停止錄製（穩定增強版 - 添加清理鎖與重試機制）"""
        if not self.recording:
            return
        
        #  修復：先標記停止，讓錄製迴圈結束
        self.recording = False
        self.paused = False
        self._recording_mouse = False
        
        self.logger(f"[{time.ctime()}] 停止錄製（等待事件處理完成...）")
        
        #  智能軌跡壓縮：停止錄製時自動簡化滑鼠軌跡
        if hasattr(self, 'simplify_trajectory') and self.simplify_trajectory:
            self._compress_mouse_trajectories()
        
        #  穩定性增強：使用鎖保護 keyboard hook 清理，並添加重試機制
        try:
            # 只有在真正有啟動錄製時才嘗試停止
            if self._keyboard_recording:
                # 先重置狀態，避免重複呼叫
                self._keyboard_recording = False
                
                # 嘗試停止錄製（添加重試機制）
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        k_events = keyboard.stop_recording()
                        self.logger(f"[停止錄製] 已停止鍵盤錄製 (獲得 {len(k_events) if k_events else 0} 個事件)")
                        break
                    except Exception as retry_ex:
                        if attempt < max_retries - 1:
                            self.logger(f"[重試 {attempt + 1}/{max_retries}] 停止鍵盤錄製: {retry_ex}")
                            time.sleep(0.1)  # 短暫等待後重試
                        else:
                            raise retry_ex
        except Exception as e:
            self.logger(f"[警告] 停止鍵盤錄製時發生錯誤: {e}")
            #  強制重置狀態，確保下次可以重新開始
            self._keyboard_recording = False
        
        # 嘗試停止並 join mouse listener（若有）以釋放資源
        try:
            if getattr(self, '_mouse_listener', None):
                try:
                    self._mouse_listener.stop()
                    self.logger(f"[停止錄製] 已停止滑鼠監聽器")
                except Exception:
                    pass
                try:
                    self._mouse_listener.join(timeout=1.0)
                except Exception:
                    pass
                self._mouse_listener = None
        except Exception:
            pass
        
        # 釋放播放或錄製期間可能遺留的按鍵
        try:
            self._release_pressed_keys()
        except Exception:
            pass
        
        #  修復：等待錄製執行緒真正結束
        if hasattr(self, '_record_thread') and self._record_thread:
            try:
                self._record_thread.join(timeout=2.0)
                if self._record_thread.is_alive():
                    self.logger(f"[警告] 錄製執行緒未能在 2 秒內結束")
            except Exception:
                pass
        
        self.logger(f"[停止錄製] 錄製已完全停止，可以開始下一次錄製")

    def _reset_keyboard_state(self):
        """
        清理 keyboard 模組內部狀態，但保留既有的全局快捷鍵。
        v2.6.5 之後改為僅重置錄製相關旗標，避免 F9/F10 快捷鍵被移除。
        """
        # 重置錄製相關的內部變數，避免 keyboard 以為仍在錄製
        if hasattr(keyboard, '_recording'):
            keyboard._recording = None
        if hasattr(keyboard, '_recorded_events'):
            keyboard._recorded_events = []
        # 釋放被標記仍按下的鍵，避免影響下一輪錄製
        try:
            if hasattr(self, '_release_pressed_keys'):
                self._release_pressed_keys()
        except Exception:
            pass

    def toggle_pause(self):
        """切換暫停狀態（改善版）"""
        self.paused = not self.paused
        
        # 錄製時的暫停處理
        if self.recording and hasattr(self, '_keyboard_recording'):
            if self.paused:
                # 暫停時停止 keyboard 錄製，暫存事件
                if self._keyboard_recording:
                    try:
                        k_events = keyboard.stop_recording()
                        if not hasattr(self, "_paused_k_events"):
                            self._paused_k_events = []
                        self._paused_k_events.extend(k_events)
                        self._keyboard_recording = False
                        self.logger("[暫停] 鍵盤錄製已暫停")
                    except Exception as e:
                        self.logger(f"[警告] 暫停鍵盤錄製時發生錯誤: {e}")
            else:
                # 繼續時重新開始 keyboard 錄製
                try:
                    keyboard.start_recording()
                    self._keyboard_recording = True
                    self.logger("[繼續] 鍵盤錄製已繼續")
                except Exception as e:
                    self.logger(f"[警告] 繼續鍵盤錄製時發生錯誤: {e}")
                    self._keyboard_recording = False
        
        return self.paused

    def _is_point_in_target_window(self, x, y):
        """檢查座標是否在目標視窗內"""
        if not self._target_hwnd:
            return True  # 沒有設定目標視窗，全部接受
        try:
            # 取得滑鼠所在位置的視窗
            point = ctypes.wintypes.POINT(int(x), int(y))
            hwnd_at_point = ctypes.windll.user32.WindowFromPoint(point)
            
            # 檢查是否為目標視窗或其子視窗
            current_hwnd = hwnd_at_point
            while current_hwnd:
                if current_hwnd == self._target_hwnd:
                    return True
                try:
                    current_hwnd = win32gui.GetParent(current_hwnd)
                except:
                    break
            return False
        except:
            return True  # 發生錯誤時不過濾

    def _record_loop(self):
        """錄製主循環"""
        try:
            self._mouse_events = []
            self._recording_mouse = True
            self._record_start_time = time.time()
            self._paused_k_events = []
            
            # 追蹤滑鼠按鍵狀態（用於判斷是否為拖曳）
            self._mouse_pressed = False

            # 嘗試啟動 keyboard 錄製（可能在打包後失敗）
            try:
                keyboard.start_recording()
                self._keyboard_recording = True
                self.logger("[錄製] keyboard 模組已啟動")
            except Exception as e:
                self._keyboard_recording = False
                self.logger(f"[警告] keyboard 模組啟動失敗（可能需要管理員權限）: {e}")

            mouse_ctrl = Controller()
            last_pos = mouse_ctrl.position

            def on_click(x, y, button, pressed):
                if self._recording_mouse and not self.paused:
                    # 更新滑鼠按鍵狀態（用於拖曳判斷）
                    if str(button).replace('Button.', '') == 'left':
                        self._mouse_pressed = pressed
                    
                    # 記錄所有點擊事件，但標記是否在目標視窗內
                    in_target = self._is_point_in_target_window(x, y)
                    event = {
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x,
                        'y': y,
                        'time': time.time(),
                        'in_target': in_target  # 標記是否在目標視窗內
                    }
                    self._mouse_events.append(event)

            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.paused:
                    # 記錄所有滾輪事件，但標記是否在目標視窗內
                    in_target = self._is_point_in_target_window(x, y)
                    event = {
                        'type': 'mouse',
                        'event': 'wheel',
                        'delta': dy,
                        'x': x,
                        'y': y,
                        'time': time.time(),
                        'in_target': in_target  # 標記是否在目標視窗內
                    }
                    self._mouse_events.append(event)

            # 使用 pynput.mouse.Listener（添加錯誤處理）
            mouse_listener = None
            try:
                mouse_listener = pynput.mouse.Listener(
                    on_click=on_click,
                    on_scroll=on_scroll
                )
                mouse_listener.start()
                # 儲存 reference，以便外部能停止/join
                try:
                    self._mouse_listener = mouse_listener
                except Exception:
                    pass
                self.logger("[錄製] pynput.mouse.Listener 已啟動")
            except Exception as e:
                self.logger(f"[警告] pynput.mouse.Listener 啟動失敗（可能需要管理員權限）: {e}")
                # 如果 listener 失敗，仍然可以記錄移動

            # 記錄初始位置
            now = time.time()
            in_target = self._is_point_in_target_window(last_pos[0], last_pos[1])
            event = {
                'type': 'mouse',
                'event': 'move',
                'x': last_pos[0],
                'y': last_pos[1],
                'time': now,
                'in_target': in_target
            }
            self._mouse_events.append(event)

            # 持續記錄滑鼠移動
            while self.recording:
                if not self.paused:
                    now = time.time()
                    pos = mouse_ctrl.position
                    if pos != last_pos:
                        # 記錄所有移動，但標記是否在目標視窗內
                        in_target = self._is_point_in_target_window(pos[0], pos[1])
                        event = {
                            'type': 'mouse',
                            'event': 'move',
                            'x': pos[0],
                            'y': pos[1],
                            'time': now,
                            'in_target': in_target  # 標記是否在目標視窗內
                        }
                        self._mouse_events.append(event)
                        last_pos = pos
                time.sleep(0.01)  # 10ms sampling

            # 停止錄製
            self._recording_mouse = False
            if mouse_listener:
                try:
                    mouse_listener.stop()
                    self.logger("[錄製] pynput.mouse.Listener 已停止")
                except Exception as e:
                    self.logger(f"[警告] 停止 mouse listener 時發生錯誤: {e}")

            # 處理鍵盤事件（添加錯誤處理）
            if self._keyboard_recording:
                try:
                    k_events = keyboard.stop_recording()
                    self.logger("[錄製] keyboard 錄製已停止")
                except Exception as e:
                    self.logger(f"[警告] 停止 keyboard 錄製時發生錯誤: {e}")
                    k_events = []
            else:
                k_events = []

            # 合併暫停期間的事件
            all_k_events = []
            if hasattr(self, "_paused_k_events"):
                all_k_events.extend(self._paused_k_events)
            all_k_events.extend(k_events)

            # 過濾掉快捷鍵事件 (F9, F10, F11, F12)
            filtered_k_events = [
                e for e in all_k_events
                if not (e.name in ('f9', 'f10', 'f11', 'f12') and e.event_type in ('down', 'up'))
            ]

            # 合併所有事件並排序
            self.events = sorted(
                [{'type': 'keyboard', 'event': e.event_type, 'name': e.name, 'time': e.time} 
                 for e in filtered_k_events] +
                self._mouse_events,
                key=lambda e: e['time']
            )

            # 統計視窗內外的事件數量（如果有設定目標視窗）
            if self._target_hwnd:
                mouse_in_target = sum(1 for e in self._mouse_events if e.get('in_target', True))
                mouse_out_target = len(self._mouse_events) - mouse_in_target
                self.logger(f"錄製完成，共 {len(self.events)} 筆事件。")
                self.logger(f"  滑鼠事件：{len(self._mouse_events)} 筆（視窗內: {mouse_in_target}, 視窗外: {mouse_out_target}）")
                self.logger(f"  鍵盤事件：{len(filtered_k_events)} 筆")
            else:
                self.logger(f"錄製完成，共 {len(self.events)} 筆事件。")
            
            # 如果完全沒有事件，顯示警告
            if len(self.events) == 0:
                self.logger("️ 警告：沒有錄製到任何事件！")
                self.logger("可能原因：")
                self.logger("  1. 程式需要以管理員身份執行")
                self.logger("  2. 防毒軟體阻擋了鍵盤/滑鼠監聽")
                self.logger("  3. 系統安全設定阻止了 hook 功能")
                self.logger("建議：請以管理員身份執行此程式")

        except Exception as ex:
            self.logger(f"錄製執行緒發生錯誤: {ex}")
            import traceback
            self.logger(f"詳細錯誤: {traceback.format_exc()}")

    def play(self, speed=1.0, repeat=1, repeat_time_limit=None, repeat_interval=0, on_event=None):
        """開始執行錄製的事件
        
        Args:
            speed: 播放速度倍率
            repeat: 重複次數（-1 表示無限重複）
            repeat_time_limit: 總運作時間限制（秒），優先於 repeat
            repeat_interval: 每次重複之間的間隔（秒）
            on_event: 事件回調函數
        """
        if self.playing or not self.events:
            return False
        
        #  修復：確保所有錄製相關的監聽器都已關閉
        self._ensure_recording_stopped()
        
        #  修復：清空所有可能殘留的按鍵狀態
        self._pressed_keys.clear()
        
        self.playing = True
        self.paused = False
        self._play_thread = threading.Thread(
            target=self._play_loop,
            args=(speed, repeat, repeat_time_limit, repeat_interval, on_event),
            daemon=True
        )
        self._play_thread.start()
        return True

    def stop_play(self):
        """停止執行（強化版 - 確保狀態正確重置）"""
        was_playing = self.playing
        self.playing = False
        self.paused = False
        
        if was_playing:
            self.logger(f"[{time.ctime()}] 已停止執行")
            
            #  修復：釋放可能卡住的修飾鍵（強化版）
            try:
                import keyboard
                # 釋放常見修飾鍵
                modifiers = ['ctrl', 'shift', 'alt', 'win', 'left ctrl', 'right ctrl', 
                           'left shift', 'right shift', 'left alt', 'right alt']
                for mod in modifiers:
                    try:
                        keyboard.release(mod)
                    except:
                        pass
                
                #  修復：額外確保通過 Windows API 釋放修飾鍵
                try:
                    import ctypes
                    VK_CONTROL = 0x11
                    VK_SHIFT = 0x10
                    VK_MENU = 0x12  # Alt
                    VK_LWIN = 0x5B
                    VK_RWIN = 0x5C
                    
                    for vk in [VK_CONTROL, VK_SHIFT, VK_MENU, VK_LWIN, VK_RWIN]:
                        ctypes.windll.user32.keybd_event(vk, 0, 0x0002, 0)  # KEYEVENTF_KEYUP
                except:
                    pass
            except:
                pass
        
        # 釋放所有被按下但未 release 的鍵
        try:
            self._release_pressed_keys()
        except Exception:
            pass

    def _play_loop(self, speed, repeat, repeat_time_limit, repeat_interval, on_event):
        """執行主循環（強化版 - 支援時間限制優先，修復點擊其他視窗導致停止的問題）
        
        優先順序：重複時間 > 重複次數
        - 如果設定了 repeat_time_limit，則在時間內無限重複
        - 否則按照 repeat 次數執行
        """
        try:
            #  修復：再次確認沒有錄製在進行
            self._ensure_recording_stopped()
            
            # 初始化循環計數器和時間記錄
            self._current_repeat_count = 0
            play_start_time = time.time()
            
            #  核心修復：時間限制優先於次數限制
            if repeat_time_limit and repeat_time_limit > 0:
                # 時間限制模式：在時間內無限重複
                self.logger(f"[時間限制模式] 將在 {repeat_time_limit:.1f} 秒內重複執行")
                r = 0
                while self.playing:
                    # 檢查是否超過時間限制
                    elapsed = time.time() - play_start_time
                    if elapsed >= repeat_time_limit:
                        self.logger(f"[時間限制] 已達到設定時間 {repeat_time_limit:.1f} 秒，停止執行")
                        break
                    
                    if not self.playing:
                        break
                    
                    self._current_repeat_count = r
                    self._execute_single_round(speed, on_event)
                    r += 1
                    
                    # 執行間隔等待（同樣要檢查時間限制）
                    if repeat_interval > 0 and self.playing:
                        interval_start = time.time()
                        while time.time() - interval_start < repeat_interval:
                            if not self.playing:
                                break
                            # 再次檢查總時間限制
                            if time.time() - play_start_time >= repeat_time_limit:
                                self.logger(f"[時間限制] 間隔等待中達到時間限制，停止執行")
                                self.playing = False
                                break
                            time.sleep(0.1)
            elif repeat == -1:
                # 無限重複模式（無時間限制）
                self.logger("[無限重複模式] 將持續執行直到手動停止")
                r = 0
                while self.playing:
                    if not self.playing:
                        break
                    self._current_repeat_count = r
                    self._execute_single_round(speed, on_event)
                    r += 1
                    
                    # 執行間隔等待
                    if repeat_interval > 0 and self.playing:
                        interval_start = time.time()
                        while time.time() - interval_start < repeat_interval:
                            if not self.playing:
                                break
                            time.sleep(0.1)
            else:
                # 次數限制模式
                self.logger(f"[次數限制模式] 將執行 {repeat} 次")
                for r in range(max(1, repeat)):
                    if not self.playing:
                        break
                    self._current_repeat_count = r
                    self._execute_single_round(speed, on_event)
                    
                    # 執行間隔等待（最後一次不需要等待）
                    if repeat_interval > 0 and r < repeat - 1 and self.playing:
                        interval_start = time.time()
                        while time.time() - interval_start < repeat_interval:
                            if not self.playing:
                                break
                            time.sleep(0.1)
                    
        except Exception as ex:
            self.logger(f"執行循環錯誤: {ex}")
        finally:
            self.playing = False
            self._current_repeat_count = 0
            #  修復：執行結束後確保所有按鍵都被釋放
            try:
                self._release_pressed_keys()
                # 額外發送一次全局修飾鍵釋放
                import ctypes
                for vk in [0x10, 0x11, 0x12]: # Shift, Ctrl, Alt
                    ctypes.windll.user32.keybd_event(vk, 0, 0x0002, 0)
            except:
                pass
            
    def _execute_single_round(self, speed, on_event):
        """執行單次執行循環（支援標籤跳轉和重複執行）"""
        self._current_play_index = 0
        base_time = self.events[0]['time']
        play_start = time.time()
        pause_start_time = None  # 暫停開始時間
        total_pause_time = 0  # 累計暫停時間
        last_pause_state = False  # 上一次的暫停狀態
        
        #  核心修復：在一輪執行開始前，強制釋放所有修飾鍵，防止殘留
        try:
            import ctypes
            for vk in [0x10, 0x11, 0x12]: # Shift, Ctrl, Alt
                ctypes.windll.user32.keybd_event(vk, 0, 0x0002, 0)
            time.sleep(0.01)
        except:
            pass
        
        #  標籤與索引的映射
        label_map = {}  # {'label_name': index}
        for idx, event in enumerate(self.events):
            if event.get('type') == 'label':
                label_name = event.get('name', '')
                label_map[label_name] = idx
        
        #  標籤重複計數器 {'label_name': {'count': N, 'start_idx': idx}}
        label_repeat_tracker = {}

        while self._current_play_index < len(self.events):
            # 檢查 playing 狀態（不受外部事件影響）
            if not self.playing:
                break

            # 暫停處理：記錄暫停開始時間
            if self.paused:
                if not last_pause_state:
                    # 剛進入暫停狀態
                    pause_start_time = time.time()
                    last_pause_state = True
                    self.logger("[暫停] 執行已暫停")
                time.sleep(0.05)
                continue
            else:
                # 從暫停恢復：累計暫停時長
                if last_pause_state:
                    # 剛從暫停恢復
                    if pause_start_time is not None:
                        pause_duration = time.time() - pause_start_time
                        total_pause_time += pause_duration
                        self.logger(f"[繼續] 執行繼續（暫停了 {pause_duration:.2f} 秒）")
                        pause_start_time = None
                    last_pause_state = False

            event = self.events[self._current_play_index]
            event_offset = (event['time'] - base_time) / speed
            # 考慮暫停時間的目標時間
            target_time = play_start + event_offset + total_pause_time

            #  優化：檢查是否為圖片快速執行事件（跳過時間等待）
            is_fast_image_event = event.get('type') in [
                'recognize_image', 'move_to_image', 'click_image', 
                'if_image_exists', 'if_image_exists_move', 'if_image_exists_click'
            ] and event.get('time', 0) == 0  # T=0s000 的事件
            
            # 圖片快速事件只等待極短時間（0.001秒），否則按照時間戳等待
            if is_fast_image_event:
                # 極速模式：只等待1ms讓出CPU
                time.sleep(0.001)
            else:
                # 等待到目標時間（強化版 - 確保時間計算不受干擾）
                while time.time() < target_time:
                    if not self.playing:
                        break
                    if self.paused:
                        # 進入暫停狀態
                        if not last_pause_state:
                            pause_start_time = time.time()
                            last_pause_state = True
                            self.logger("[暫停] 執行已暫停")
                        break
                    # 使用極短的睡眠時間以保持時間計算精確
                    sleep_time = min(0.001, target_time - time.time())
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    else:
                        break  # 避免 busy-wait

            # 如果進入暫停，跳過事件執行
            if self.paused:
                continue

            if not self.playing:
                break

            # 執行事件（使用 try-except 確保單一事件錯誤不影響整體執行）
            try:
                # 檢查事件是否應該被執行
                should_execute = True
                if self._target_hwnd and event.get('type') == 'mouse':
                    # 如果事件標記為不在目標視窗內，跳過執行
                    if not event.get('in_target', True):
                        should_execute = False
                
                if should_execute:
                    # 根據後台模式選擇執行方法
                    result = self._execute_event_with_mode(event)
                    
                    #  處理分支跳轉
                    if result:
                        if result == 'stop':
                            break
                        elif isinstance(result, tuple) and result[0] == 'jump':
                            _, target_label, repeat_count = result
                            
                            # 檢查標籤是否存在
                            if target_label in label_map:
                                # 初始化計數器
                                if target_label not in label_repeat_tracker:
                                    label_repeat_tracker[target_label] = {
                                        'count': 0,
                                        'max_count': repeat_count,
                                        'start_idx': label_map[target_label]
                                    }
                                
                                tracker = label_repeat_tracker[target_label]
                                
                                # 檢查是否還需要重複
                                if tracker['count'] < tracker['max_count']:
                                    tracker['count'] += 1
                                    self.logger(f"[跳轉] 跳轉至 #{target_label} (第{tracker['count']}/{tracker['max_count']}次)")
                                    self._current_play_index = tracker['start_idx']
                                    continue
                                else:
                                    # 重複次數已完成，清除計數器，繼續下一個指令
                                    self.logger(f"[跳轉] #{target_label} 已完成{tracker['max_count']}次執行，繼續下一個")
                                    del label_repeat_tracker[target_label]
                            else:
                                self.logger(f"[錯誤] 標籤 '{target_label}' 不存在")
                
                # 通知事件已執行（即使有錯誤也要通知，保持進度）
                if on_event:
                    try:
                        on_event(event)
                    except:
                        pass  # 忽略回調錯誤
            except Exception as ex:
                self.logger(f"執行事件時發生錯誤: {ex}")
                # 繼續執行下一個事件，不中斷執行

            # 更新索引（確保一定會執行）
            self._current_play_index += 1

    def _execute_event_with_mode(self, event):
        """根據後台模式和滑鼠模式執行事件（強化版）
        
        Returns:
            執行結果，可能是 None, 'stop', 或 ('jump', label, count)
        """
        # 如果啟用滑鼠模式，直接使用前景模式（控制真實滑鼠）
        if self._mouse_mode:
            return self._execute_event(event)
        
        # 否則根據後台模式選擇執行方法
        mode = self._background_mode
        
        # 智能模式：自動選擇最佳方法（多層容錯 - 強化版）
        if mode == "smart":
            if self._target_hwnd:
                # 檢查視窗是否仍然存在
                try:
                    if not win32gui.IsWindow(self._target_hwnd):
                        self.logger("目標視窗已關閉，切換到前景模式")
                        return self._execute_event(event)
                except:
                    pass
                
                # 嘗試多種方式，確保執行成功
                # 1. 優先嘗試 SendMessage（比 PostMessage 更可靠）
                success = self._try_sendmessage_enhanced(event)
                if success:
                    return
                
                # 2. 嘗試 SetForegroundWindow + 直接執行（高相容性）
                try:
                    # 快速切換到前景執行（速度更快，相容性好）
                    current_hwnd = win32gui.GetForegroundWindow()
                    try:
                        win32gui.SetForegroundWindow(self._target_hwnd)
                        time.sleep(0.001)  # 極短延遲確保切換完成
                        result = self._execute_event(event)
                        # 立即切回
                        if current_hwnd and win32gui.IsWindow(current_hwnd):
                            win32gui.SetForegroundWindow(current_hwnd)
                        return result
                    except:
                        return self._execute_event(event)
                except Exception as e:
                    self.logger(f"智能模式執行失敗: {e}")
                
                # 3. 最後回退到前景模式
                return self._execute_event(event)
            else:
                # 沒有目標視窗，使用前景模式
                return self._execute_event(event)
        
        # 快速切換模式（增強穩定性）
        elif mode == "fast_switch":
            if self._target_hwnd:
                try:
                    return self._execute_fast_switch_enhanced(event)
                except Exception as e:
                    self.logger(f"快速切換失敗，回退到前景模式: {e}")
                    return self._execute_event(event)
            else:
                return self._execute_event(event)
        
        # 純後台模式（SendMessage 優先，增強版）
        elif mode == "postmessage":
            if self._target_hwnd:
                # 優先嘗試 SendMessage（同步，更可靠）
                success = self._try_sendmessage_enhanced(event)
                if not success:
                    # 回退到 PostMessage（異步）
                    success = self._try_postmessage(event)
                    if not success:
                        self.logger("後台模式執行失敗，嘗試前景模式")
                        return self._execute_event(event)
            else:
                return self._execute_event(event)
        
        # 前景模式（預設）
        else:
            return self._execute_event(event)

    def _try_sendmessage_enhanced(self, event):
        """增強版 SendMessage（更可靠的同步執行）"""
        if not self._target_hwnd:
            return False
        
        try:
            # 確保視窗存在且可見
            if not win32gui.IsWindow(self._target_hwnd):
                return False
            
            # 如果視窗最小化，嘗試恢復（但不切換焦點）
            if win32gui.IsIconic(self._target_hwnd):
                try:
                    win32gui.ShowWindow(self._target_hwnd, win32con.SW_RESTORE)
                    time.sleep(0.01)
                except:
                    pass
            
            if event['type'] == 'mouse':
                # 轉換為視窗內座標
                x, y = self._screen_to_client(self._target_hwnd, event['x'], event['y'])
                lParam = win32api.MAKELONG(x, y)
                
                if event['event'] == 'move':
                    # 移動事件使用 SendMessage（同步）
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                    # 額外發送 WM_SETCURSOR 確保游標更新
                    try:
                        win32api.SendMessage(self._target_hwnd, win32con.WM_SETCURSOR, self._target_hwnd, 
                                           win32api.MAKELONG(win32con.HTCLIENT, win32con.WM_MOUSEMOVE))
                    except:
                        pass
                    
                elif event['event'] == 'down':
                    button = event.get('button', 'left')
                    if button == 'left':
                        # 先發送 MOUSEMOVE 確保位置正確
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                        time.sleep(0.001)
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONDOWN, 
                                           win32con.MK_LBUTTON, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                        time.sleep(0.001)
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONDOWN, 
                                           win32con.MK_RBUTTON, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                        time.sleep(0.001)
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONDOWN, 
                                           win32con.MK_MBUTTON, lParam)
                        
                elif event['event'] == 'up':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                        
                elif event['event'] == 'wheel':
                    delta = event.get('delta', 0)
                    wParam = win32api.MAKELONG(0, int(delta * 120))
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
                    
                return True
            
            elif event['type'] == 'keyboard':
                vk_code = self._name_to_vk(event['name'])
                if vk_code:
                    if event['event'] == 'down':
                        # 使用 WM_KEYDOWN 發送按鍵
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                        # 對於字元鍵，額外發送 WM_CHAR
                        if 32 <= vk_code <= 126:  # 可顯示字元
                            try:
                                win32api.SendMessage(self._target_hwnd, win32con.WM_CHAR, vk_code, 0)
                            except:
                                pass
                    elif event['event'] == 'up':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYUP, vk_code, 0)
                    return True
            
            return False
            
        except Exception as ex:
            self.logger(f"SendMessage Enhanced 失敗: {ex}")
            return False

    def _execute_fast_switch_enhanced(self, event):
        """增強版快速切換（更穩定的前景切換）"""
        if not self._target_hwnd:
            self._execute_event(event)
            return
        
        try:
            # 檢查目標視窗是否還存在且可見
            if not win32gui.IsWindow(self._target_hwnd):
                self.logger("目標視窗已關閉")
                return
            
            # 如果視窗最小化，先恢復
            if win32gui.IsIconic(self._target_hwnd):
                try:
                    win32gui.ShowWindow(self._target_hwnd, win32con.SW_RESTORE)
                    time.sleep(0.02)
                except:
                    pass
            
            # 記住當前視窗
            current_hwnd = win32gui.GetForegroundWindow()
            
            # 切換到目標視窗（多種方法確保成功）
            switched = False
            try:
                # 方法1: 標準切換
                win32gui.SetForegroundWindow(self._target_hwnd)
                time.sleep(0.002)  # 2ms 極短延遲
                
                # 驗證是否成功切換
                if win32gui.GetForegroundWindow() == self._target_hwnd:
                    switched = True
                else:
                    # 方法2: 使用 BringWindowToTop
                    try:
                        win32gui.BringWindowToTop(self._target_hwnd)
                        win32gui.SetForegroundWindow(self._target_hwnd)
                        time.sleep(0.002)
                        switched = (win32gui.GetForegroundWindow() == self._target_hwnd)
                    except:
                        pass
                    
                    if not switched:
                        # 方法3: 使用 SwitchToThisWindow
                        try:
                            ctypes.windll.user32.SwitchToThisWindow(self._target_hwnd, True)
                            time.sleep(0.003)
                            switched = (win32gui.GetForegroundWindow() == self._target_hwnd)
                        except:
                            pass
                            
            except Exception as e:
                self.logger(f"切換視窗失敗: {e}")
            
            # 執行事件
            self._execute_event(event)
            
            # 極短延遲確保事件執行完成
            if event.get('type') == 'mouse':
                if event.get('event') in ('down', 'up', 'wheel'):
                    time.sleep(0.002)  # 2ms
            
            # 切回原視窗（如果需要且可能）
            if current_hwnd and win32gui.IsWindow(current_hwnd):
                try:
                    win32gui.SetForegroundWindow(current_hwnd)
                except Exception:
                    pass  # 切換失敗不影響執行
        
        except Exception as ex:
            self.logger(f"快速切換執行失敗: {ex}")
            # 失敗時直接執行
            self._execute_event(event)

    def _try_sendmessage(self, event):
        """嘗試使用 SendMessage 執行事件（同步，更可靠）"""
        if not self._target_hwnd:
            return False
        
        try:
            if event['type'] == 'mouse':
                # 轉換為視窗內座標
                x, y = self._screen_to_client(self._target_hwnd, event['x'], event['y'])
                lParam = win32api.MAKELONG(x, y)
                
                if event['event'] == 'move':
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                elif event['event'] == 'down':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONDOWN, 
                                           win32con.MK_LBUTTON, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONDOWN, 
                                           win32con.MK_RBUTTON, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONDOWN, 
                                           win32con.MK_MBUTTON, lParam)
                elif event['event'] == 'up':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    elif button == 'right':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    elif button == 'middle':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                elif event['event'] == 'wheel':
                    delta = event.get('delta', 0)
                    wParam = win32api.MAKELONG(0, int(delta * 120))
                    win32api.SendMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
                return True
            
            elif event['type'] == 'keyboard':
                vk_code = self._name_to_vk(event['name'])
                if vk_code:
                    if event['event'] == 'down':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                    elif event['event'] == 'up':
                        win32api.SendMessage(self._target_hwnd, win32con.WM_KEYUP, vk_code, 0)
                    return True
            
            return False
        except Exception as ex:
            self.logger(f"SendMessage 失敗: {ex}")
            return False

    def _try_postmessage(self, event):
        """嘗試使用 PostMessage 執行事件（純後台）"""
        if not self._target_hwnd:
            return False
        
        try:
            if event['type'] == 'mouse':
                # 轉換為視窗內座標
                x, y = self._screen_to_client(self._target_hwnd, event['x'], event['y'])
                lParam = win32api.MAKELONG(x, y)
                
                if event['event'] == 'move':
                    win32api.PostMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
                elif event['event'] == 'down':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_LBUTTONDOWN, 
                                           win32con.MK_LBUTTON, lParam)
                    elif button == 'right':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_RBUTTONDOWN, 
                                           win32con.MK_RBUTTON, lParam)
                    elif button == 'middle':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_MBUTTONDOWN, 
                                           win32con.MK_MBUTTON, lParam)
                elif event['event'] == 'up':
                    button = event.get('button', 'left')
                    if button == 'left':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                    elif button == 'right':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_RBUTTONUP, 0, lParam)
                    elif button == 'middle':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_MBUTTONUP, 0, lParam)
                elif event['event'] == 'wheel':
                    delta = event.get('delta', 0)
                    wParam = win32api.MAKELONG(0, int(delta * 120))
                    win32api.PostMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
                return True
            
            elif event['type'] == 'keyboard':
                vk_code = self._name_to_vk(event['name'])
                if vk_code:
                    if event['event'] == 'down':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                    elif event['event'] == 'up':
                        win32api.PostMessage(self._target_hwnd, win32con.WM_KEYUP, vk_code, 0)
                    return True
            
            return False
        except Exception as ex:
            self.logger(f"PostMessage 失敗: {ex}")
            return False

    def _execute_fast_switch(self, event):
        """快速切換到目標視窗執行事件（增強版）"""
        if not self._target_hwnd:
            self._execute_event(event)
            return
        
        try:
            # 檢查目標視窗是否還存在且可見
            if not win32gui.IsWindow(self._target_hwnd):
                self.logger("目標視窗已關閉")
                return
            
            if not win32gui.IsWindowVisible(self._target_hwnd):
                self.logger("目標視窗不可見，嘗試顯示")
                win32gui.ShowWindow(self._target_hwnd, win32con.SW_SHOW)
                time.sleep(0.05)
            
            # 記住當前視窗
            current_hwnd = win32gui.GetForegroundWindow()
            
            # 切換到目標視窗（增強切換邏輯）
            try:
                # 方法1: 標準切換
                win32gui.SetForegroundWindow(self._target_hwnd)
                time.sleep(0.01)  # 10ms 等待切換完成
                
                # 驗證是否成功切換
                if win32gui.GetForegroundWindow() != self._target_hwnd:
                    # 方法2: 強制切換（使用 SwitchToThisWindow）
                    try:
                        ctypes.windll.user32.SwitchToThisWindow(self._target_hwnd, True)
                        time.sleep(0.02)
                    except:
                        pass
                    
                    # 方法3: 使用 BringWindowToTop
                    try:
                        win32gui.BringWindowToTop(self._target_hwnd)
                        win32gui.SetForegroundWindow(self._target_hwnd)
                        time.sleep(0.02)
                    except:
                        pass
            except Exception as e:
                self.logger(f"切換視窗失敗: {e}")
            
            # 執行事件
            self._execute_event(event)
            
            # 延遲確保事件執行完成
            if event.get('type') == 'mouse':
                if event.get('event') in ('down', 'up', 'wheel'):
                    time.sleep(0.005)  # 5ms
            
            # 切回原視窗（增強切換回邏輯）
            if current_hwnd and win32gui.IsWindow(current_hwnd):
                try:
                    win32gui.SetForegroundWindow(current_hwnd)
                except Exception:
                    # 如果切換失敗，嘗試其他方法
                    try:
                        ctypes.windll.user32.SwitchToThisWindow(current_hwnd, True)
                    except:
                        pass
        
        except Exception as ex:
            self.logger(f"快速切換執行失敗: {ex}")
            # 失敗時直接執行
            self._execute_event(event)

    def _execute_event(self, event):
        """執行單一事件（滑鼠模式 - 強化版，添加即時日誌）"""
        # 處理範圍結束指令
        if event['type'] == 'region_end':
            self._current_region = None
            self.logger("[範圍結束] 已清除辨識範圍限制")
            return
        
        if event['type'] == 'keyboard':
            # 鍵盤事件執行
            try:
                if event['event'] == 'down':
                    keyboard.press(event['name'])
                    try:
                        self._pressed_keys.add(event['name'])
                    except Exception:
                        pass
                    #  2.5 風格：即時輸出鍵盤事件
                    self.logger(f"[鍵盤] {event['event']} {event['name']}")
                elif event['event'] == 'up':
                    keyboard.release(event['name'])
                    try:
                        if event['name'] in self._pressed_keys:
                            self._pressed_keys.discard(event['name'])
                    except Exception:
                        pass
                    #  2.5 風格：即時輸出鍵盤事件
                    self.logger(f"[鍵盤] {event['event']} {event['name']}")
                    #  核心修復：修飾鍵放開後加入微小延遲，確保 Windows 訊息隊列處理同步
                    if event['name'] in ['alt', 'ctrl', 'shift', 'windows', 'left alt', 'right alt', 'left ctrl', 'right ctrl', 'left shift', 'right shift']:
                        time.sleep(0.005)
            except Exception as e:
                self.logger(f"鍵盤事件執行失敗: {e}")
                
        elif event['type'] == 'mouse':
            # 解析座標，處理 None 的情況 (即目前位置點擊)
            x = event.get('x')
            y = event.get('y')
            
            if x is None or y is None:
                # 獲取當前游標位置
                point = ctypes.wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
                if x is None: x = point.x
                if y is None: y = point.y
            
            x, y = int(x), int(y)
            
            # 如果有設定目標視窗，先確保視窗在前景並將座標限制在視窗內
            if self._target_hwnd:
                try:
                    # 取得視窗矩形
                    left, top, right, bottom = win32gui.GetWindowRect(self._target_hwnd)
                    # 將座標限制在視窗範圍內
                    x = max(left, min(right - 1, x))
                    y = max(top, min(bottom - 1, y))
                except:
                    pass  # 視窗可能已關閉，使用原始座標
            
            try:
                #  修復：使用虛擬螢幕範圍（支援多螢幕）
                # GetSystemMetrics(0/1) 只返回主螢幕尺寸，不適用於多螢幕
                # 使用 SM_XVIRTUALSCREEN/SM_YVIRTUALSCREEN 獲取整個虛擬螢幕範圍
                SM_XVIRTUALSCREEN = 76  # 虛擬螢幕左上角 X 座標
                SM_YVIRTUALSCREEN = 77  # 虛擬螢幕左上角 Y 座標
                SM_CXVIRTUALSCREEN = 78  # 虛擬螢幕寬度
                SM_CYVIRTUALSCREEN = 79  # 虛擬螢幕高度
                
                virtual_left = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
                virtual_top = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
                virtual_width = ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
                virtual_height = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
                
                virtual_right = virtual_left + virtual_width
                virtual_bottom = virtual_top + virtual_height
                
                # 將座標限制在虛擬螢幕範圍內（支援負數座標）
                x = max(virtual_left, min(virtual_right - 1, int(x)))
                y = max(virtual_top, min(virtual_bottom - 1, int(y)))
                
                if event['event'] == 'move':
                    # 滑鼠移動
                    if self._use_bezier and self._bezier_mover:
                        self._bezier_mover.move_to(x, y, duration=0.2)
                    else:
                        ctypes.windll.user32.SetCursorPos(x, y)
                    # 移動事件太頻繁，不輸出日誌
                    
                elif event['event'] in ('down', 'up'):
                    # 點擊事件：先移動到正確位置
                    if self._use_bezier and self._bezier_mover:
                        self._bezier_mover.move_to(x, y, duration=0.2)
                    else:
                        ctypes.windll.user32.SetCursorPos(x, y)
                    
                    #  增加微小延遲確保系統更新位置狀態
                    time.sleep(0.01)
                    
                    button = event.get('button', 'left')
                    self._mouse_event_enhanced(event['event'], button=button)
                    #  2.5 風格：即時輸出滑鼠點擊事件
                    self.logger(f"[滑鼠] {event['event']} {button} at ({x}, {y})")
                    
                elif event['event'] == 'wheel':
                    # 滾輪事件：先移動到正確位置
                    ctypes.windll.user32.SetCursorPos(x, y)
                    time.sleep(0.001)
                    
                    delta = event.get('delta', 0)
                    self._mouse_event_enhanced('wheel', delta=delta)
                    #  2.5 風格：即時輸出滾輪事件
                    self.logger(f"[滑鼠] wheel {delta} at ({x}, {y})")
                    
            except Exception as e:
                self.logger(f"滑鼠事件執行失敗: {e}")
        
        # 處理圖片辨識相關事件
        elif event['type'] == 'recognize_image':
            # 辨識圖片（只是辨識，不做動作）
            try:
                image_name = event.get('image', '')
                confidence = event.get('confidence', 0.6)  #  優化：降低至0.6加快速度
                show_border = event.get('show_border', False)  # 是否顯示邊框
                region = event.get('region', None)  # 辨識範圍
                
                # 如果事件指定了範圍，更新全域範圍狀態
                if region is not None:
                    self._current_region = region
                # 如果事件沒有指定範圍，使用全域範圍狀態
                elif self._current_region is not None:
                    region = self._current_region
                
                self.logger(f"[圖片辨識] 開始辨識: {image_name}" + 
                          (f" (範圍: {region})" if region else ""))
                
                pos = self.find_image_on_screen(
                    image_name, 
                    threshold=confidence, 
                    fast_mode=True,
                    show_border=show_border,
                    region=region
                )
                
                if pos:
                    self.logger(f"[圖片辨識]  找到圖片於 ({pos[0]}, {pos[1]})")
                else:
                    self.logger(f"[圖片辨識]  未找到圖片")
            except Exception as e:
                self.logger(f"圖片辨識執行失敗: {e}")
        
        elif event['type'] == 'move_to_image':
            # 移動到圖片位置
            try:
                image_name = event.get('image', '')
                confidence = event.get('confidence', 0.6)  #  優化：降低至0.6加快速度
                show_border = event.get('show_border', False)
                region = event.get('region', None)
                
                # 如果事件指定了範圍，更新全域範圍狀態
                if region is not None:
                    self._current_region = region
                # 如果事件沒有指定範圍，使用全域範圍狀態
                elif self._current_region is not None:
                    region = self._current_region
                
                self.logger(f"[移動至圖片] 開始尋找: {image_name}" +
                          (f" (範圍: {region})" if region else ""))
                
                pos = self.find_image_on_screen(
                    image_name,
                    threshold=confidence,
                    fast_mode=True,
                    show_border=show_border,
                    region=region
                )
                
                if pos:
                    x, y = pos
                    ctypes.windll.user32.SetCursorPos(x, y)
                    self.logger(f"[移動至圖片]  已移動至 ({x}, {y})")
                else:
                    self.logger(f"[移動至圖片]  未找到圖片，無法移動")
            except Exception as e:
                self.logger(f"移動至圖片執行失敗: {e}")
        
        elif event['type'] == 'click_image':
            # 點擊圖片位置（ 新增：可選擇返回原位 +  彈性點擊範圍）
            try:
                image_name = event.get('image', '')
                confidence = event.get('confidence', 0.6)  #  優化：降低至0.6加快速度
                button = event.get('button', 'left')
                return_to_origin = event.get('return_to_origin', False)  # 預設不返回原位
                show_border = event.get('show_border', False)
                region = event.get('region', None)
                
                #  新增：彈性點擊範圍參數
                click_offset_mode = event.get('click_offset_mode', 'center')  #  預設中心模式（極速點擊）
                click_radius = event.get('click_radius', 0)  # 點擊半徑（0=使用預設45%範圍）
                
                #  如果未指定點擊半徑，計算圖片大小的45%作為預設範圍
                auto_radius = 0
                if click_radius == 0:
                    # 稍後在找到圖片後計算（需要圖片尺寸）
                    auto_radius = None  # 標記需要自動計算
                
                # 如果事件指定了範圍，更新全域範圍狀態
                if region is not None:
                    self._current_region = region
                # 如果事件沒有指定範圍，使用全域範圍狀態
                elif self._current_region is not None:
                    region = self._current_region
                
                self.logger(f"[點擊圖片] 開始尋找: {image_name}" +
                          (f" (範圍: {region})" if region else ""))
                
                #  記錄原始滑鼠位置
                if return_to_origin:
                    original_pos = win32api.GetCursorPos()
                
                pos = self.find_image_on_screen(
                    image_name,
                    threshold=confidence,
                    fast_mode=True,
                    show_border=show_border,
                    region=region
                )
                
                #  強化：必須找到圖片才執行點擊
                if pos is None:
                    self.logger(f"[點擊圖片]  未找到圖片 '{image_name}'，跳過點擊")
                    return  # 直接返回，不執行任何點擊動作
                
                if pos:
                    x, y = pos
                    
                    #  自動計算點擊半徑（圖片尺寸的80%）
                    if click_radius == 0 and auto_radius is None:
                        # 重新載入圖片取得尺寸（已有快取，速度很快）
                        template_gray, _ = self._load_image(image_name)
                        if template_gray is not None:
                            h, w = template_gray.shape
                            #  計算圖片尺寸的45%作為半徑（例如128x128→半徑28.8px）
                            import math
                            # 使用較短邊的45%作為半徑，更精準的點擊範圍
                            click_radius = int(min(w, h) * 0.45 / 2)  # 45%範圍 = 短邊的22.5%半徑
                            self.logger(f"[彈性點擊] 自動計算半徑: {click_radius}px (圖片尺寸{w}x{h}，45%範圍)")
                    
                    #  彈性點擊：根據模式計算偏移
                    if click_radius > 0:
                        if click_offset_mode == 'random':
                            # 隨機偏移：在半徑範圍內隨機點擊
                            import random
                            import math
                            angle = random.uniform(0, 2 * math.pi)
                            distance = random.uniform(0, click_radius)
                            offset_x = int(distance * math.cos(angle))
                            offset_y = int(distance * math.sin(angle))
                            x += offset_x
                            y += offset_y
                            self.logger(f"[彈性點擊] 隨機偏移 ({offset_x}, {offset_y})")
                        
                        elif click_offset_mode == 'tracking':
                            # 追蹤預測偏移：根據移動方向預測點擊位置
                            if image_name in self._motion_history and len(self._motion_history[image_name]) >= 2:
                                history = self._motion_history[image_name]
                                x2, y2, t2 = history[-1]
                                x1, y1, t1 = history[-2]
                                # 計算移動向量
                                vx = x2 - x1
                                vy = y2 - y1
                                # 預測下一個位置（限制在半徑範圍內）
                                import math
                                speed = math.sqrt(vx**2 + vy**2)
                                if speed > 0:
                                    scale = min(1.0, click_radius / speed)
                                    offset_x = int(vx * scale)
                                    offset_y = int(vy * scale)
                                    x += offset_x
                                    y += offset_y
                                    self.logger(f"[彈性點擊] 追蹤預測偏移 ({offset_x}, {offset_y})")
                        # center 模式不偏移，直接使用中心點
                    
                    #  修復點擊：增加擬真移動與合理延遲
                    if self._use_bezier and self._bezier_mover:
                        self._bezier_mover.move_to(x, y, duration=0.2)
                    else:
                        ctypes.windll.user32.SetCursorPos(x, y)
                    
                    # 增加微小延遲確保系統更新位置狀態
                    time.sleep(0.02)
                    
                    self._mouse_event_enhanced('down', button=button)
                    # 增加 Down 和 Up 之間的延遲，解決部分 App 不響應點擊的問題
                    time.sleep(0.05) 
                    self._mouse_event_enhanced('up', button=button)
                    
                    self.logger(f"[點擊圖片] 已點擊 {button} 於 ({x}, {y})")
                    
                    #  返回原位 (預設關閉,避免游標跳回原點)
                    if return_to_origin:
                        ctypes.windll.user32.SetCursorPos(original_pos[0], original_pos[1])
                        self.logger(f"[點擊圖片]  已返回原位 ({original_pos[0]}, {original_pos[1]})")
            except Exception as e:
                self.logger(f"點擊圖片執行失敗: {e}")
        
        #  新增：條件判斷 - 如果圖片存在
        elif event['type'] == 'if_image_exists':
            try:
                image_name = event.get('image', '')
                confidence = event.get('confidence', 0.65)  #  優化：降低預設閾值
                on_success = event.get('on_success')  # {'action': 'continue'/'stop'/'jump', 'target': 'label_name', 'repeat_count': N}
                on_failure = event.get('on_failure')
                show_border = event.get('show_border', False)
                region = event.get('region', None)
                
                # 如果事件指定了範圍，更新全域範圍狀態
                if region is not None:
                    self._current_region = region
                # 如果事件沒有指定範圍，使用全域範圍狀態
                elif self._current_region is not None:
                    region = self._current_region
                
                self.logger(f"[條件判斷] 檢查圖片是否存在: {image_name}" +
                          (f" (範圍: {region})" if region else ""))
                
                pos = self.find_image_on_screen(
                    image_name,
                    threshold=confidence,
                    fast_mode=True,
                    show_border=show_border,
                    region=region
                )
                
                if pos:
                    self.logger(f"[條件判斷] 找到圖片於 ({pos[0]}, {pos[1]})")
                    if on_success:
                        return self._handle_branch_action(on_success)
                else:
                    self.logger(f"[條件判斷]  未找到圖片")
                    if on_failure:
                        return self._handle_branch_action(on_failure)
            except Exception as e:
                self.logger(f"條件判斷執行失敗: {e}")
        
        # ==================== OCR 文字辨識事件 ====================
        
        # OCR 條件判斷：if_text_exists
        elif event['type'] == 'if_text_exists':
            try:
                from ocr_trigger import OCRTrigger
                
                target_text = event.get('target_text', '')
                timeout = event.get('timeout', 10.0)
                match_mode = event.get('match_mode', 'contains')
                on_success = event.get('on_success')
                on_failure = event.get('on_failure')
                
                self.logger(f"[OCR] 檢查文字是否存在: {target_text}（最長 {timeout}s）")
                
                # 初始化 OCR 引擎
                ocr = OCRTrigger(ocr_engine="auto")
                
                if not ocr.is_available():
                    self.logger("[OCR] ️ OCR 引擎未啟用，跳過此步驟")
                    if on_failure:
                        return self._handle_branch_action(on_failure)
                    return ('continue',)
                
                self.logger(f"[OCR] 使用引擎: {ocr.get_engine_name()}")
                
                # 等待文字出現
                found = ocr.wait_for_text(
                    target_text=target_text,
                    timeout=timeout,
                    match_mode=match_mode,
                    interval=0.5
                )
                
                if found:
                    self.logger(f"[OCR]  找到文字: {target_text}")
                    if on_success:
                        return self._handle_branch_action(on_success)
                else:
                    self.logger(f"[OCR]  未找到文字: {target_text}")
                    if on_failure:
                        return self._handle_branch_action(on_failure)
                        
            except ImportError:
                self.logger("[OCR]  ocr_trigger 模組未找到，請確認檔案存在")
            except Exception as e:
                self.logger(f"[OCR] 錯誤: {e}")
                if event.get('on_failure'):
                    return self._handle_branch_action(event.get('on_failure'))
        
        # OCR 等待文字：wait_text
        elif event['type'] == 'wait_text':
            try:
                from ocr_trigger import OCRTrigger
                
                target_text = event.get('target_text', '')
                timeout = event.get('timeout', 10.0)
                match_mode = event.get('match_mode', 'contains')
                
                self.logger(f"[OCR] 等待文字出現: {target_text}（最長 {timeout}s）")
                
                ocr = OCRTrigger(ocr_engine="auto")
                
                if not ocr.is_available():
                    self.logger("[OCR] ️ OCR 引擎未啟用")
                    return ('continue',)
                
                found = ocr.wait_for_text(
                    target_text=target_text,
                    timeout=timeout,
                    match_mode=match_mode
                )
                
                if found:
                    self.logger(f"[OCR]  文字已出現")
                else:
                    self.logger(f"[OCR] ️ 等待逾時")
                    
            except Exception as e:
                self.logger(f"[OCR] 錯誤: {e}")
        
        # OCR 點擊文字位置：click_text
        elif event['type'] == 'click_text':
            try:
                from ocr_trigger import OCRTrigger
                
                target_text = event.get('target_text', '')
                timeout = event.get('timeout', 5.0)
                
                self.logger(f"[OCR] 尋找並點擊文字: {target_text}")
                
                ocr = OCRTrigger(ocr_engine="auto")
                
                if not ocr.is_available():
                    self.logger("[OCR] ️ OCR 引擎未啟用")
                    return ('continue',)
                
                # 尋找文字位置
                pos = ocr.find_text_position(target_text)
                
                if pos:
                    x, y = pos
                    self.logger(f"[OCR]  找到文字於 ({x}, {y})，執行點擊")
                    
                    # 移動並點擊
                    win32api.SetCursorPos((x, y))
                    time.sleep(0.05)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                    time.sleep(0.05)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
                else:
                    self.logger(f"[OCR]  未找到文字")
                    
            except Exception as e:
                self.logger(f"[OCR] 錯誤: {e}")
        
        #  新增：多圖片同時辨識
        elif event['type'] == 'recognize_any':
            try:
                images = event.get('images', [])  # [{'name': 'pic01', 'action': 'click/move/log'}, ...]
                confidence = event.get('confidence', 0.7)  #  降低至0.7加快速度
                timeout = event.get('timeout', 0)  # 0 = 立即返回，>0 = 持續嘗試直到找到或逾時
                self.logger(f"[多圖辨識] 同時搜尋 {len(images)} 張圖片")
                
                start_time = time.time()
                found = False
                
                while True:
                    #  一次截圖，多次匹配（效能優化 - 使用 mss）
                    snapshot_gray = self._capture_screen_fast()
                    
                    # 準備圖片列表
                    template_list = [{'name': img.get('name', ''), 'threshold': confidence} for img in images]
                    
                    #  使用批次辨識方法
                    results = self.find_images_in_snapshot(snapshot, template_list, threshold=confidence, fast_mode=True)
                    
                    # 檢查是否有找到任何圖片
                    for img_config in images:
                        img_name = img_config.get('name', '')
                        action = img_config.get('action', 'log')
                        pos = results.get(img_name)
                        
                        if pos:
                            self.logger(f"[多圖辨識]  找到圖片: {img_name} 於 ({pos[0]}, {pos[1]})")
                            
                            # 執行對應動作
                            if action == 'click':
                                button = img_config.get('button', 'left')
                                return_to_origin = img_config.get('return_to_origin', False)  # 預設不返回原位,避免游標跳回
                                original_pos = win32api.GetCursorPos() if return_to_origin else None
                                
                                ctypes.windll.user32.SetCursorPos(pos[0], pos[1])
                                time.sleep(0.01)
                                self._mouse_event_enhanced('down', button=button)
                                time.sleep(0.05)
                                self._mouse_event_enhanced('up', button=button)
                                self.logger(f"[多圖辨識]  已點擊 {img_name}")
                                
                                if return_to_origin and original_pos:
                                    time.sleep(0.01)
                                    ctypes.windll.user32.SetCursorPos(original_pos[0], original_pos[1])
                                    self.logger(f"[多圖辨識]  已返回原位")
                            
                            elif action == 'move':
                                ctypes.windll.user32.SetCursorPos(pos[0], pos[1])
                                self.logger(f"[多圖辨識]  已移動至 {img_name}")
                            
                            found = True
                            break
                    
                    if found:
                        break
                    
                    # 檢查逾時
                    if timeout > 0 and (time.time() - start_time) >= timeout:
                        self.logger(f"[多圖辨識]  逾時 ({timeout}秒)，未找到任何圖片")
                        break
                    elif timeout == 0:
                        self.logger(f"[多圖辨識]  未找到任何圖片")
                        break
                    
                    time.sleep(0.1)  # 稍微延遲後再次嘗試
                    
            except Exception as e:
                self.logger(f"多圖辨識執行失敗: {e}")
        
        # ==================== v2.7.1+ 新增事件類型 ====================
        
        # 變數設定
        elif event['type'] == 'set_variable':
            name = event.get('name', '')
            value = event.get('value', 0)
            self._set_variable(name, value)
        
        # 變數運算
        elif event['type'] == 'variable_operation':
            name = event.get('name', '')
            operation = event.get('operation', 'add')  # add/subtract/multiply/divide
            value = event.get('value', 1)
            self._variable_operation(name, operation, value)
        
        # 變數條件判斷
        elif event['type'] == 'if_variable':
            name = event.get('name', '')
            operator = event.get('operator', '==')
            value = event.get('value', 0)
            on_success = event.get('on_success')
            on_failure = event.get('on_failure')
            
            result = self._check_variable_condition(name, operator, value)
            self.logger(f"[變數條件] {name} {operator} {value} = {result}")
            
            if result and on_success:
                return self._handle_branch_action(on_success)
            elif not result and on_failure:
                return self._handle_branch_action(on_failure)
        
        # 多條件判斷（AND）
        elif event['type'] == 'if_all_images_exist':
            try:
                images = event.get('images', [])
                confidence = event.get('confidence', 0.75)
                on_success = event.get('on_success')
                on_failure = event.get('on_failure')
                
                self.logger(f"[多條件AND] 檢查 {len(images)} 張圖片是否全部存在")
                
                all_found = True
                for img_name in images:
                    pos = self.find_image_on_screen(img_name, threshold=confidence, fast_mode=True)
                    if not pos:
                        self.logger(f"[多條件AND]  缺少: {img_name}")
                        all_found = False
                        break
                    else:
                        self.logger(f"[多條件AND]  找到: {img_name}")
                
                if all_found:
                    self.logger(f"[多條件AND]  全部找到")
                    if on_success:
                        return self._handle_branch_action(on_success)
                else:
                    if on_failure:
                        return self._handle_branch_action(on_failure)
                        
            except Exception as e:
                self.logger(f"多條件AND判斷失敗: {e}")
        
        # 多條件判斷（OR）
        elif event['type'] == 'if_any_image_exists':
            try:
                images = event.get('images', [])
                confidence = event.get('confidence', 0.75)
                on_success = event.get('on_success')
                on_failure = event.get('on_failure')
                found_image = event.get('found_image_var', '')  # 儲存找到的圖片名稱到變數
                
                self.logger(f"[多條件OR] 檢查 {len(images)} 張圖片是否有任一存在")
                
                found = None
                for img_name in images:
                    pos = self.find_image_on_screen(img_name, threshold=confidence, fast_mode=True)
                    if pos:
                        self.logger(f"[多條件OR]  找到: {img_name}")
                        found = img_name
                        if found_image:
                            self._set_variable(found_image, img_name)
                        break
                
                if found:
                    if on_success:
                        return self._handle_branch_action(on_success)
                else:
                    self.logger(f"[多條件OR]  全部未找到")
                    if on_failure:
                        return self._handle_branch_action(on_failure)
                        
            except Exception as e:
                self.logger(f"多條件OR判斷失敗: {e}")
        
        # 循環開始
        elif event['type'] == 'loop_start':
            loop_type = event.get('loop_type', 'repeat')  # repeat/while/for
            max_count = event.get('max_count', 1)
            condition = event.get('condition', {})  # for while loop
            
            self._loop_stack.append({
                'type': loop_type,
                'start_index': self._current_play_index,
                'counter': 0,
                'max_count': max_count,
                'condition': condition
            })
            self.logger(f"[循環開始] 類型={loop_type}, 次數={max_count}")
        
        # 循環結束
        elif event['type'] == 'loop_end':
            if self._loop_stack:
                loop_info = self._loop_stack[-1]
                loop_info['counter'] += 1
                
                should_continue = False
                
                if loop_info['type'] == 'repeat':
                    should_continue = loop_info['counter'] < loop_info['max_count']
                elif loop_info['type'] == 'while':
                    # 檢查條件
                    condition = loop_info['condition']
                    if condition.get('type') == 'image_exists':
                        img_name = condition.get('image', '')
                        pos = self.find_image_on_screen(img_name, threshold=0.75, fast_mode=True)
                        should_continue = bool(pos)
                
                if should_continue:
                    self.logger(f"[循環] 繼續循環 ({loop_info['counter']}/{loop_info['max_count']})")
                    self._current_play_index = loop_info['start_index']
                    return ('jump_index', loop_info['start_index'])
                else:
                    self.logger(f"[循環結束] 已完成 {loop_info['counter']} 次")
                    self._loop_stack.pop()
        
        # 隨機延遲
        elif event['type'] == 'random_delay':
            import random
            min_ms = event.get('min_ms', 100)
            max_ms = event.get('max_ms', 500)
            delay = random.randint(min_ms, max_ms) / 1000.0
            self.logger(f"[隨機延遲] {delay:.3f}s")
            time.sleep(delay)
        
        # 隨機分支
        elif event['type'] == 'random_branch':
            import random
            probability = event.get('probability', 50)  # 0-100
            on_success = event.get('on_success')
            on_failure = event.get('on_failure')
            
            roll = random.randint(1, 100)
            success = roll <= probability
            
            self.logger(f"[隨機分支] 概率={probability}%, 擲骰={roll}, 結果={'成功' if success else '失敗'}")
            
            if success and on_success:
                return self._handle_branch_action(on_success)
            elif not success and on_failure:
                return self._handle_branch_action(on_failure)
        
        # 嘗試執行（帶重試）
        elif event['type'] == 'try_action':
            action_id = event.get('action_id', 'default')
            max_retries = event.get('max_retries', 3)
            on_success = event.get('on_success')
            on_failure = event.get('on_failure')
            
            retry_count = self._get_action_retry_count(action_id)
            self.logger(f"[嘗試執行] {action_id} (第{retry_count + 1}次/最多{max_retries}次)")
            
            # 這裡需要配合下一個動作使用，標記為嘗試模式
            self._current_try_action = action_id
            self._current_try_max = max_retries
            self._current_try_success = on_success
            self._current_try_failure = on_failure
        
        # 計數器觸發
        elif event['type'] == 'counter_trigger':
            action_id = event.get('action_id', '')
            count = event.get('count', 3)
            on_trigger = event.get('on_trigger')
            reset_on_trigger = event.get('reset_on_trigger', True)
            
            current_count = self._increment_action_retry(action_id)
            self.logger(f"[計數器] {action_id}: {current_count}/{count}")
            
            if current_count >= count:
                self.logger(f"[計數器觸發] {action_id} 達到 {count} 次")
                if reset_on_trigger:
                    self._reset_action_retry(action_id)
                if on_trigger:
                    return self._handle_branch_action(on_trigger)
        
        # 計時器觸發
        elif event['type'] == 'timer_trigger':
            action_id = event.get('action_id', '')
            duration = event.get('duration', 60)  # 秒
            on_trigger = event.get('on_trigger')
            reset_on_trigger = event.get('reset_on_trigger', True)
            
            # 首次執行時開始計時
            if action_id not in self._action_start_time:
                self._start_action_timer(action_id)
                self.logger(f"[計時器] {action_id} 開始計時")
            
            elapsed = self._get_action_elapsed_time(action_id)
            self.logger(f"[計時器] {action_id}: {elapsed:.1f}s/{duration}s")
            
            if elapsed >= duration:
                self.logger(f"[計時器觸發] {action_id} 達到 {duration} 秒")
                if reset_on_trigger:
                    self._reset_action_timer(action_id)
                if on_trigger:
                    return self._handle_branch_action(on_trigger)
        
        # 重置計數器
        elif event['type'] == 'reset_counter':
            action_id = event.get('action_id', '')
            self._reset_action_retry(action_id)
            self.logger(f"[重置計數器] {action_id}")
        
        # 重置計時器
        elif event['type'] == 'reset_timer':
            action_id = event.get('action_id', '')
            self._reset_action_timer(action_id)
            self.logger(f"[重置計時器] {action_id}")
        
        #  新增：延遲開始
        elif event['type'] == 'delayed_start':
            delay_seconds = event.get('delay_seconds', 10)
            self.logger(f"[開始] 等待 {delay_seconds} 秒後開始...")
            
            # 顯示倒數計時
            for remaining in range(delay_seconds, 0, -1):
                if not self.playing:  # 檢查是否被停止
                    self.logger("[開始] 已取消")
                    return 'stop'
                self.logger(f"[開始] 倒數 {remaining} 秒")
                time.sleep(1)
            
            self.logger(f"[開始] 延遲完成，開始執行腳本")
        
        #  新增：延遲結束
        elif event['type'] == 'delayed_end':
            delay_seconds = event.get('delay_seconds', 60)
            self.logger(f"[結束] 將在 {delay_seconds} 秒後結束腳本")
            
            # 顯示倒數計時
            for remaining in range(delay_seconds, 0, -1):
                if not self.playing:  # 檢查是否被停止
                    self.logger("[結束] 已提前停止")
                    return 'stop'
                self.logger(f"[結束] 倒數 {remaining} 秒後結束")
                time.sleep(1)
            
            self.logger(f"[結束] 時間到，停止執行")
            self.playing = False
            return 'stop'

    def _handle_branch_action(self, action_config):
        """處理分支動作（繼續/停止/跳轉）
        
        Args:
            action_config: {'action': 'continue'/'stop'/'jump', 'target': 'label_name', 'repeat_count': N}
        
        Returns:
            'stop' 如果需要停止執行，否則 None
            ('jump', 'label_name', repeat_count) 如果需要跳轉
        """
        try:
            action = action_config.get('action', 'continue')
            
            if action == 'stop':
                self.logger("[分支] 執行停止動作")
                self.playing = False
                return 'stop'
            
            elif action == 'jump':
                target = action_config.get('target', '')
                repeat_count = action_config.get('repeat_count', 1)
                self.logger(f"[分支] 跳轉至標籤: {target}, 重複{repeat_count}次")
                return ('jump', target, repeat_count)
            
            else:  # continue
                self.logger("[分支] 繼續執行")
                return None
                
        except Exception as e:
            self.logger(f"分支動作處理失敗: {e}")
            return None
    
    # ==================== v2.7.1+ 變數系統 ====================
    
    def _set_variable(self, name, value):
        """設定變數"""
        try:
            # 嘗試轉換為數字
            if isinstance(value, str):
                if '.' in value:
                    value = float(value)
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        pass  # 保持字串
            self._variables[name] = value
            self.logger(f"[變數] {name} = {value}")
        except Exception as e:
            self.logger(f"設定變數失敗: {e}")
    
    def _get_variable(self, name, default=0):
        """取得變數值"""
        return self._variables.get(name, default)
    
    def _variable_operation(self, name, operation, value=1):
        """變數運算（加減乘除）"""
        try:
            current = self._get_variable(name, 0)
            if operation == 'add':
                self._variables[name] = current + value
            elif operation == 'subtract':
                self._variables[name] = current - value
            elif operation == 'multiply':
                self._variables[name] = current * value
            elif operation == 'divide':
                self._variables[name] = current / value if value != 0 else current
            self.logger(f"[變數] {name} {operation} {value} = {self._variables[name]}")
        except Exception as e:
            self.logger(f"變數運算失敗: {e}")
    
    def _check_variable_condition(self, name, operator, value):
        """檢查變數條件"""
        try:
            var_value = self._get_variable(name, 0)
            # 確保類型一致
            if isinstance(var_value, (int, float)) and isinstance(value, str):
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            
            if operator == '==':
                return var_value == value
            elif operator == '!=':
                return var_value != value
            elif operator == '>':
                return var_value > value
            elif operator == '>=':
                return var_value >= value
            elif operator == '<':
                return var_value < value
            elif operator == '<=':
                return var_value <= value
            else:
                self.logger(f"未知的運算符: {operator}")
                return False
        except Exception as e:
            self.logger(f"變數條件檢查失敗: {e}")
            return False
    
    def _increment_action_retry(self, action_id):
        """增加動作重試計數"""
        self._action_retry_count[action_id] = self._action_retry_count.get(action_id, 0) + 1
        return self._action_retry_count[action_id]
    
    def _reset_action_retry(self, action_id):
        """重置動作重試計數"""
        self._action_retry_count[action_id] = 0
    
    def _get_action_retry_count(self, action_id):
        """取得動作重試計數"""
        return self._action_retry_count.get(action_id, 0)
    
    def _start_action_timer(self, action_id):
        """開始動作計時"""
        self._action_start_time[action_id] = time.time()
    
    def _get_action_elapsed_time(self, action_id):
        """取得動作經過時間（秒）"""
        if action_id in self._action_start_time:
            return time.time() - self._action_start_time[action_id]
        return 0
    
    def _reset_action_timer(self, action_id):
        """重置動作計時"""
        if action_id in self._action_start_time:
            del self._action_start_time[action_id]
    
    # ==================== 滑鼠事件處理 ====================

    def _mouse_event_enhanced(self, event, button='left', delta=0):
        """增強版滑鼠事件執行（更精確穩定）"""
        user32 = ctypes.windll.user32
        
        # 定義 MOUSEINPUT 和 INPUT 結構
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]
            
        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_ulong),
                ("mi", MOUSEINPUT)
            ]
        
        try:
            if event == 'down' or event == 'up':
                # 按鈕事件標誌
                flags = {
                    'left': (0x0002, 0x0004),    # MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
                    'right': (0x0008, 0x0010),   # MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
                    'middle': (0x0020, 0x0040)   # MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
                }
                flag = flags.get(button, (0x0002, 0x0004))[0 if event == 'down' else 1]
                
                inp = INPUT()
                inp.type = 0  # INPUT_MOUSE
                inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, None)
                
                # 使用 SendInput 發送輸入（硬體級別）
                result = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
                
                if result == 0:
                    self.logger(f"SendInput 失敗: {ctypes.get_last_error()}")
                
            elif event == 'wheel':
                # 滾輪事件
                inp = INPUT()
                inp.type = 0  # INPUT_MOUSE
                inp.mi = MOUSEINPUT(0, 0, int(delta * 120), 0x0800, 0, None)  # MOUSEEVENTF_WHEEL
                
                result = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
                
                if result == 0:
                    self.logger(f"SendInput (wheel) 失敗: {ctypes.get_last_error()}")
                    
        except Exception as e:
            self.logger(f"滑鼠事件發送失敗: {e}")

    def _release_pressed_keys(self):
        """釋放在執行期間可能被 press 但未 release 的按鍵集合"""
        try:
            import keyboard
            for k in list(getattr(self, '_pressed_keys', [])):
                try:
                    keyboard.release(k)
                except Exception:
                    pass
            self._pressed_keys.clear()
            self.logger("[recorder] 已釋放遺留的按鍵")
        except Exception as ex:
            self.logger(f"[recorder] 釋放遺留按鍵失敗: {ex}")
    
    def _ensure_recording_stopped(self):
        """ 新增：確保所有錄製相關的監聽器都已完全停止"""
        try:
            # 停止鍵盤錄製
            if self._keyboard_recording:
                try:
                    keyboard.stop_recording()
                    self._keyboard_recording = False
                except:
                    pass
            
            # 停止滑鼠監聽器
            if self._mouse_listener is not None:
                try:
                    if hasattr(self._mouse_listener, 'stop'):
                        self._mouse_listener.stop()
                    self._mouse_listener = None
                    self._recording_mouse = False
                except:
                    pass
            
            # 清除錄製狀態
            self.recording = False
            
            self.logger("[recorder] 已確保所有錄製監聽器停止")
        except Exception as ex:
            self.logger(f"[recorder] 停止監聽器時發生錯誤: {ex}")

    def join_threads(self, timeout=1.0):
        """嘗試 join 內部的 record/play thread，回傳是否成功 join"""
        ok = True
        try:
            t = getattr(self, '_record_thread', None)
            if t and getattr(t, 'is_alive', lambda: False)():
                try:
                    t.join(timeout)
                except Exception:
                    ok = False
            p = getattr(self, '_play_thread', None)
            if p and getattr(p, 'is_alive', lambda: False)():
                try:
                    p.join(timeout)
                except Exception:
                    ok = False
        except Exception:
            ok = False
        return ok
    
    # ==================== 圖片辨識功能 ====================
    
    def set_images_directory(self, images_dir):
        """設定圖片目錄"""
        self._images_dir = images_dir
        self.logger(f"[圖片辨識] 圖片目錄：{images_dir}")
    
    def show_match_border(self, x, y, width, height, duration=1500):
        """顯示圖片辨識位置的邊框
        
        Args:
            x: 左上角 x 坐標
            y: 左上角 y 坐標
            width: 寬度
            height: 高度
            duration: 顯示時間(毫秒)
        """
        try:
            import tkinter as tk
            
            # 關閉舊的邊框視窗
            if self._border_window:
                try:
                    self._border_window.destroy()
                except:
                    pass
                self._border_window = None
            
            # 創建新的邊框視窗
            border = tk.Tk()
            border.overrideredirect(True)  # 無框視窗
            border.attributes('-topmost', True)  # 置頂
            border.attributes('-alpha', 0.6)  # 半透明
            border.geometry(f"{width}x{height}+{x}+{y}")
            
            # 綠色邊框
            canvas = tk.Canvas(border, bg='green', highlightthickness=3, highlightbackground='lime')
            canvas.pack(fill='both', expand=True)
            
            # 中央文字
            canvas.create_text(
                width//2, height//2,
                text=' 已辨識',
                font=('Microsoft JhengHei', 14, 'bold'),
                fill='white'
            )
            
            self._border_window = border
            
            # 定時關閉
            def close_border():
                try:
                    border.destroy()
                except:
                    pass
                self._border_window = None
            
            border.after(duration, close_border)
            
        except Exception as e:
            self._log(f"[邊框] 顯示失敗: {e}", "warning")
    
    def _capture_screen_fast(self, region=None):
        """ 優化：快速螢幕截圖（優先使用mss，回退到PIL）
        
        mss 的優勢：
        - 直接返回 BGRA 格式，轉灰度更快
        - 區域截圖時開銷更小
        - 適合高頻連續截圖（如圖片辨識循環）
        - 在圖片辨識場景中可提升 20-30% 整體性能
        
        Args:
            region: (x1, y1, x2, y2) 或 None（全螢幕）
            
        Returns:
            numpy.ndarray: 灰度圖 (GRAY)
        """
        try:
            if MSS_AVAILABLE:
                #  每次創建新的 mss 實例（避免多執行緒問題）
                with mss.mss() as sct:
                    # 使用 mss 快速截圖（速度提升 3-5倍）
                    if region:
                        monitor = {"left": region[0], "top": region[1], 
                                  "width": region[2] - region[0], 
                                  "height": region[3] - region[1]}
                    else:
                        monitor = sct.monitors[1]  # 主螢幕
                    
                    screenshot = sct.grab(monitor)
                    # 轉換為 numpy array 並轉灰度
                    img = np.array(screenshot)
                    # mss 輸出 BGRA，轉換為灰度
                    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                    return gray
            else:
                # 回退到 PIL.ImageGrab
                if region:
                    screenshot = ImageGrab.grab(bbox=region)
                else:
                    screenshot = ImageGrab.grab()
                
                screen_array = np.array(screenshot)
                gray = cv2.cvtColor(screen_array, cv2.COLOR_RGB2GRAY)
                return gray
                
        except Exception as e:
            self._log(f"[截圖] 快速截圖失敗: {e}", "warning")
            # 最終回退到 PIL
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()
            screen_array = np.array(screenshot)
            return cv2.cvtColor(screen_array, cv2.COLOR_RGB2GRAY)
    
    def _predict_search_region(self, image_name, full_screen_size):
        """ 預測式搜尋：根據歷史位置預測下一次搜尋範圍
        
        Args:
            image_name: 圖片名稱
            full_screen_size: 全螢幕尺寸 (width, height)
            
        Returns:
            預測的搜尋範圍 (x1, y1, x2, y2) 或 None（使用全螢幕）
        """
        import time
        
        if image_name not in self._last_found_positions:
            return None  # 第一次搜尋，使用全螢幕
        
        last_x, last_y, last_time = self._last_found_positions[image_name]
        current_time = time.time()
        time_diff = current_time - last_time
        
        # 如果距離上次發現超過3秒，視為目標可能已移動很遠，使用全螢幕
        if time_diff > 3.0:
            return None
        
        # 計算運動向量（如果有歷史記錄）
        velocity_x, velocity_y = 0, 0
        if image_name in self._motion_history and len(self._motion_history[image_name]) >= 2:
            history = self._motion_history[image_name]
            # 使用最近兩個位置計算速度
            x2, y2, t2 = history[-1]
            x1, y1, t1 = history[-2]
            dt = t2 - t1
            if dt > 0:
                velocity_x = (x2 - x1) / dt
                velocity_y = (y2 - y1) / dt
        
        # 預測當前位置
        predicted_x = last_x + velocity_x * time_diff
        predicted_y = last_y + velocity_y * time_diff
        
        # 設定搜尋範圍（預測位置±150像素）
        # 移動越快，範圍越大
        speed = (velocity_x**2 + velocity_y**2)**0.5
        search_radius = min(300, 150 + int(speed * time_diff))
        
        x1 = max(0, int(predicted_x - search_radius))
        y1 = max(0, int(predicted_y - search_radius))
        x2 = min(full_screen_size[0], int(predicted_x + search_radius))
        y2 = min(full_screen_size[1], int(predicted_y + search_radius))
        
        # 確保搜尋範圍至少300x300
        if x2 - x1 < 300 or y2 - y1 < 300:
            return None
        
        return (x1, y1, x2, y2)
    
    def _update_motion_history(self, image_name, x, y):
        """更新運動歷史記錄
        
        Args:
            image_name: 圖片名稱
            x, y: 發現的位置
        """
        import time
        current_time = time.time()
        
        # 更新最後發現位置
        self._last_found_positions[image_name] = (x, y, current_time)
        
        # 更新運動歷史
        if image_name not in self._motion_history:
            self._motion_history[image_name] = []
        
        self._motion_history[image_name].append((x, y, current_time))
        
        # 限制歷史記錄數量
        if len(self._motion_history[image_name]) > self._max_motion_history:
            self._motion_history[image_name].pop(0)
    
    def enable_tracking(self, image_name):
        """啟用圖片追蹤模式
        
        Args:
            image_name: 要追蹤的圖片名稱
        """
        self._tracking_mode[image_name] = True
        self.logger(f"[追蹤] 已啟用 {image_name} 的追蹤模式")
    
    def disable_tracking(self, image_name):
        """停用圖片追蹤模式
        
        Args:
            image_name: 要停止追蹤的圖片名稱
        """
        self._tracking_mode[image_name] = False
        if image_name in self._last_found_positions:
            del self._last_found_positions[image_name]
        if image_name in self._motion_history:
            del self._motion_history[image_name]
        self.logger(f"[追蹤] 已停用 {image_name} 的追蹤模式")
    
    def find_image_on_screen(self, image_name_or_path, threshold=0.9, region=None, multi_scale=True, fast_mode=False, use_features_fallback=True, show_border=False, enable_tracking=False, strict_mode=True):
        """在螢幕上尋找圖片（ 極速優化版 + 智能追蹤 + 精確比對）
        
        Args:
            image_name_or_path: 圖片顯示名稱或完整路徑
            threshold: 匹配閾值 (0-1)，預設0.8平衡速度與準確度 (v2.8.2 提高)
            region: 搜尋區域 (x1, y1, x2, y2)，None表示全螢幕
            multi_scale: 是否啟用多尺度搜尋（提高容錯性）
            fast_mode: 快速模式（跳過驗證步驟，大幅提升速度）
            use_features_fallback: 模板匹配失敗時，是否嘗試特徵點匹配
            show_border: 是否顯示邊框
            enable_tracking: 啟用追蹤模式（預測式搜尋，適合移動目標）
            strict_mode: 嚴格模式（v2.8.2 新增）- 使用更精確的比對避免相似圖片誤判
            
        Returns:
            (center_x, center_y) 如果找到，否則 None
        """
        try:
            #  載入目標圖片（已優化：返回灰度圖）
            template_gray, mask = self._load_image(image_name_or_path)
            if template_gray is None:
                self.logger(f"[圖片辨識] 無法載入圖片：{image_name_or_path}")
                return None
            
            #  智能追蹤：如果啟用追蹤模式且有歷史位置，使用預測式搜尋
            search_region = region
            if enable_tracking or self._tracking_mode.get(image_name_or_path, False):
                # 獲取螢幕尺寸
                import ctypes
                user32 = ctypes.windll.user32
                screen_size = (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
                
                predicted_region = self._predict_search_region(image_name_or_path, screen_size)
                if predicted_region:
                    search_region = predicted_region
                    self.logger(f"[追蹤] 預測搜尋範圍: {predicted_region}")
            
            #  使用快速截圖（優化：mss引擎 + 預轉灰度）
            screen_cv = self._capture_screen_fast(search_region)
            
            #  調試資訊：輸出截圖和模板尺寸
            if search_region:
                self.logger(f"[圖片辨識] 範圍截圖尺寸: {screen_cv.shape[1]}x{screen_cv.shape[0]} (範圍: {search_region})")
            self.logger(f"[圖片辨識] 模板圖片尺寸: {template_gray.shape[1]}x{template_gray.shape[0]}")
            
            # 檢查模板是否大於截圖
            if template_gray.shape[0] > screen_cv.shape[0] or template_gray.shape[1] > screen_cv.shape[1]:
                self.logger(f"[圖片辨識]  錯誤：模板圖片大於搜尋範圍！")
                return None
            
            best_match_val = 0
            best_match_loc = None
            best_template_size = None
            best_scale = 1.0
            
            #  極速模式：單一演算法、原始尺寸
            if fast_mode:
                # 使用最快的 TM_CCOEFF_NORMED 算法
                result = cv2.matchTemplate(screen_cv, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= threshold:
                    h, w = template_gray.shape
                    
                    #  v2.8.2 嚴格模式：驗證匹配區域是否真的與模板一致
                    if strict_mode:
                        verified = self._verify_match_strict(
                            screen_cv, template_gray, max_loc, 
                            threshold=0.92  # 嚴格驗證使用更高閾值
                        )
                        if not verified:
                            self.logger(f"[圖片辨識][嚴格模式] ️ 匹配位置驗證失敗，可能是相似但不同的圖片")
                            # 嘗試找下一個最佳匹配
                            alt_pos = self._find_strict_match(
                                screen_cv, template_gray, result, threshold, search_region
                            )
                            if alt_pos:
                                if search_region:
                                    alt_pos = (alt_pos[0] + search_region[0], alt_pos[1] + search_region[1])
                                self.logger(f"[圖片辨識][嚴格模式]  找到精確匹配於 ({alt_pos[0]}, {alt_pos[1]})")
                                return alt_pos
                            else:
                                self.logger(f"[圖片辨識][嚴格模式]  無法找到精確匹配")
                                return None
                    
                    pos = (max_loc[0] + w // 2, max_loc[1] + h // 2)
                    
                    # 如果有指定region，需要加上偏移
                    if search_region:
                        pos = (pos[0] + search_region[0], pos[1] + search_region[1])
                    
                    #  追蹤模式：更新位置歷史
                    if enable_tracking or self._tracking_mode.get(image_name_or_path, False):
                        self._update_motion_history(image_name_or_path, pos[0], pos[1])
                    
                    self.logger(f"[圖片辨識][極速]  找到圖片於 ({pos[0]}, {pos[1]}) 信心度:{max_val:.3f}")
                    
                    # 顯示邊框
                    if show_border:
                        x = max_loc[0] if not search_region else max_loc[0] + search_region[0]
                        y = max_loc[1] if not search_region else max_loc[1] + search_region[1]
                        self.show_match_border(x, y, w, h)
                    
                    return pos
                else:
                    #  追蹤模式失敗：如果使用了預測搜尋但失敗，嘗試全螢幕搜尋
                    if enable_tracking and search_region != region and region is None:
                        self.logger(f"[追蹤] 預測區域未找到，嘗試全螢幕搜尋")
                        screen_cv_full = self._capture_screen_fast(None)
                        result = cv2.matchTemplate(screen_cv_full, template_gray, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        
                        if max_val >= threshold:
                            h, w = template_gray.shape
                            pos = (max_loc[0] + w // 2, max_loc[1] + h // 2)
                            self._update_motion_history(image_name_or_path, pos[0], pos[1])
                            self.logger(f"[追蹤]  全螢幕找到於 ({pos[0]}, {pos[1]}) 信心度:{max_val:.3f}")
                            return pos
                    
                    #  增強日誌：顯示搜尋範圍資訊
                    if search_region:
                        region_info = f"，搜尋範圍: {search_region} (寬{search_region[2]-search_region[0]}x高{search_region[3]-search_region[1]})"
                    else:
                        region_info = "，搜尋範圍: 全螢幕"
                    self.logger(f"[圖片辨識][極速]  未找到圖片（最高信心度:{max_val:.3f}，閾值:{threshold:.3f}{region_info}）")
                    return None
            
            #  標準模式：多尺度模板匹配（主要方法，支援遮罩）
            if multi_scale:
                scales = [0.95, 1.0, 1.05]  #  優化：僅保留3個尺度，目標0.5秒內完成
                for scale in scales:
                    if scale != 1.0:
                        width = int(template.shape[1] * scale)
                        height = int(template.shape[0] * scale)
                        if width < 10 or height < 10 or width > screen_cv.shape[1] or height > screen_cv.shape[0]:
                            continue
                        scaled_template = cv2.resize(template, (width, height), interpolation=cv2.INTER_LINEAR)  #  使用INTER_LINEAR加快速度
                        scaled_mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST) if mask is not None else None
                    else:
                        scaled_template = template
                        scaled_mask = mask
                    
                    #  根據是否有遮罩選擇演算法
                    if scaled_mask is not None:
                        # 有透明遮罩：使用支援遮罩的演算法
                        self.logger(f"[圖片辨識] 使用透明遮罩進行匹配 (尺度:{scale:.2f})")
                        result = cv2.matchTemplate(screen_cv, scaled_template, cv2.TM_CCORR_NORMED, mask=scaled_mask)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        score = max_val
                        loc = max_loc
                    else:
                        # 無遮罩： 優化：只使用最快的相關係數法
                        result = cv2.matchTemplate(screen_cv, scaled_template, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        score = max_val
                        loc = max_loc
                    
                    # 記錄最佳匹配
                    if score > best_match_val:
                        best_match_val = score
                        best_match_loc = loc
                        best_template_size = (scaled_template.shape[1], scaled_template.shape[0])
                        best_scale = scale
            else:
                #  單一尺度匹配（支援遮罩）
                if mask is not None:
                    result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCORR_NORMED, mask=mask)
                else:
                    result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                best_match_val = max_val
                best_match_loc = max_loc
                best_template_size = (template.shape[1], template.shape[0])
            
            self.logger(f"[圖片辨識] 模板匹配度：{best_match_val:.3f} (尺度:{best_scale:.2f}, 閾值：{threshold})")
            
            #  如果模板匹配失敗但接近閾值，嘗試特徵點匹配
            if use_features_fallback and best_match_val < threshold and best_match_val >= threshold * 0.7:
                self.logger(f"[圖片辨識] 模板匹配未達閾值，嘗試特徵點匹配...")
                feature_x, feature_y, match_count = self.find_image_by_features(template, screen_cv)
                
                if feature_x is not None and match_count >= 15:  # 需要足夠的特徵點
                    if region:
                        feature_x += region[0]
                        feature_y += region[1]
                    self.logger(f"[圖片辨識]  特徵點匹配成功於 ({feature_x}, {feature_y})")
                    return (feature_x, feature_y)
            
            #  階段2: 進階驗證（當模板匹配度接近閾值時）
            if best_match_val >= threshold * 0.85:  # 降低初步門檻，進行更精確驗證
                w, h = best_template_size
                x1, y1 = best_match_loc
                x2, y2 = x1 + w, y1 + h
                
                # 確保範圍在螢幕內
                if x2 <= screen_cv.shape[1] and y2 <= screen_cv.shape[0]:
                    matched_region = screen_cv[y1:y2, x1:x2]
                    
                    # 調整模板大小以匹配找到的區域
                    if best_scale != 1.0:
                        template_resized = cv2.resize(template, (w, h), interpolation=cv2.INTER_LINEAR)  #  使用INTER_LINEAR加快速度
                    else:
                        template_resized = template
                    
                    verification_score = 0
                    verification_count = 0
                    
                    try:
                        #  優化：只使用快速的直方圖驗證（移除耗時的SSIM和邊緣檢測）
                        hist_template = cv2.calcHist([template_resized], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                        hist_matched = cv2.calcHist([matched_region], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                        
                        cv2.normalize(hist_template, hist_template)
                        cv2.normalize(hist_matched, hist_matched)
                        
                        hist_score = cv2.compareHist(hist_template, hist_matched, cv2.HISTCMP_CORREL)
                        verification_score += hist_score
                        verification_count += 1.0
                        self.logger(f"[圖片辨識] 直方圖驗證: {hist_score:.3f}")
                    except Exception as e:
                        self.logger(f"[圖片辨識] 直方圖驗證失敗: {e}")
                    
                    # 計算最終綜合分數
                    if verification_count > 0:
                        final_score = (best_match_val * 0.6 + (verification_score / verification_count) * 0.4)
                        self.logger(f"[圖片辨識] 綜合分數: {final_score:.3f} (模板:{best_match_val:.3f} + 驗證:{verification_score/verification_count:.3f})")
                    else:
                        final_score = best_match_val
                        self.logger(f"[圖片辨識] 最終分數: {final_score:.3f} (僅模板匹配)")
                    
                    # 使用綜合分數判斷
                    if final_score >= threshold:
                        # 計算中心點座標
                        center_x = best_match_loc[0] + w // 2
                        center_y = best_match_loc[1] + h // 2
                        
                        # 如果有指定region，需要加上偏移
                        if region:
                            center_x += region[0]
                            center_y += region[1]
                        
                        self.logger(f"[圖片辨識]  找到圖片於 ({center_x}, {center_y})")
                        
                        # 顯示邊框
                        if show_border:
                            x1 = best_match_loc[0] + (region[0] if region else 0)
                            y1 = best_match_loc[1] + (region[1] if region else 0)
                            self.show_match_border(x1, y1, w, h)
                        
                        return (center_x, center_y)
            
            self.logger(f"[圖片辨識]  未找到圖片（分數不足）")
            return None
                
        except Exception as e:
            self.logger(f"[圖片辨識] 錯誤：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_image(self, image_name_or_path):
        """載入圖片（ 優化：預先生成灰度圖快取）
        
        Args:
            image_name_or_path: 圖片顯示名稱或完整路徑
            
        Returns:
            tuple: (image_gray, mask) 或 (None, None)
                - image_gray: OpenCV 灰度格式的圖片（已優化）
                - mask: Alpha通道遮罩（如果有），否則為None
        """
        #  檢查快取（優先返回預先轉換好的灰度圖）
        if image_name_or_path in self._image_cache:
            cached = self._image_cache[image_name_or_path]
            # cached格式: (bgr, image_path, mask, gray)
            if len(cached) >= 4 and cached[3] is not None:
                return cached[3], cached[2]  # 灰度圖, 遮罩
            return cached[0], cached[2] if len(cached) > 2 else None
        
        # 判斷是否為完整路徑
        if os.path.isfile(image_name_or_path):
            image_path = image_name_or_path
        else:
            # 從圖片目錄中尋找
            if not self._images_dir or not os.path.exists(self._images_dir):
                self.logger(f"[圖片辨識] 圖片目錄不存在：{self._images_dir}")
                return None, None
            
            # 嘗試尋找匹配的檔案
            image_path = None
            for filename in os.listdir(self._images_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    # 檢查檔名或顯示名稱是否匹配
                    if image_name_or_path in filename or filename.startswith(image_name_or_path):
                        image_path = os.path.join(self._images_dir, filename)
                        break
            
            if not image_path:
                self.logger(f"[圖片辨識] 找不到圖片：{image_name_or_path}")
                return None, None
        
        # 載入圖片
        try:
            #  使用 cv2.imdecode 解決中文路徑問題
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image_rgba = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
            
            if image_rgba is None:
                self.logger(f"[圖片辨識] 無法讀取圖片：{image_path}")
                return None, None
            
            mask = None
            
            #  檢查是否有 Alpha 通道（透明遮罩）
            if len(image_rgba.shape) == 3 and image_rgba.shape[2] == 4:  # RGBA格式
                # 分離 RGB 和 Alpha
                bgr = cv2.cvtColor(image_rgba, cv2.COLOR_RGBA2BGR)
                mask = image_rgba[:, :, 3]  # Alpha通道作為遮罩
                
                # 檢查遮罩是否有效（是否真的有透明區域）
                if np.all(mask == 255):  # 完全不透明
                    mask = None
                    self.logger(f"[圖片辨識] 已載入圖片（無透明區域）：{os.path.basename(image_path)}")
                else:
                    self.logger(f"[圖片辨識] 已載入圖片（含透明遮罩）：{os.path.basename(image_path)}")
            else:  # RGB或灰階格式
                if len(image_rgba.shape) == 2:  # 灰階
                    bgr = cv2.cvtColor(image_rgba, cv2.COLOR_GRAY2BGR)
                else:  # RGB
                    bgr = image_rgba
                self.logger(f"[圖片辨識] 已載入圖片（不透明）：{os.path.basename(image_path)}")
            
            #  預先生成灰度圖（優化：避免重複轉換）
            if len(bgr.shape) == 3:
                gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            else:
                gray = bgr
            
            #  加入快取（包含遮罩和灰度圖）
            self._image_cache[image_name_or_path] = (bgr, image_path, mask, gray)
            
            return gray, mask
        except Exception as e:
            self.logger(f"[圖片辨識] 載入圖片失敗：{e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def _verify_match_strict(self, screen_cv, template_gray, match_loc, threshold=0.92):
        """ v2.8.2 嚴格驗證匹配區域
        
        用於區分相似但不同的按鈕（如 Accept vs Accept all）
        
        Args:
            screen_cv: 螢幕截圖（灰度）
            template_gray: 模板圖片（灰度）
            match_loc: 匹配位置 (x, y)
            threshold: 驗證閾值
            
        Returns:
            bool: 是否驗證通過
        """
        try:
            h, w = template_gray.shape
            x, y = match_loc
            
            # 確保範圍在螢幕內
            if y + h > screen_cv.shape[0] or x + w > screen_cv.shape[1]:
                return False
            
            # 提取匹配區域
            matched_region = screen_cv[y:y+h, x:x+w]
            
            # 1️⃣ 像素差異統計（核心驗證）
            diff = cv2.absdiff(matched_region, template_gray)
            mean_diff = np.mean(diff)
            max_diff = np.max(diff)
            
            # 如果平均差異太大，驗證失敗
            if mean_diff > 15:  # 平均像素差異超過15
                self.logger(f"[嚴格驗證] 像素差異過大: 平均={mean_diff:.2f}, 最大={max_diff}")
                return False
            
            # 2️⃣ 邊界像素驗證（檢查圖片邊緣是否一致）
            # 右邊緣（用於區分 Accept 和 Accept all）
            right_edge_template = template_gray[:, -5:]  # 右邊5像素
            right_edge_matched = matched_region[:, -5:]
            right_diff = np.mean(cv2.absdiff(right_edge_template, right_edge_matched))
            
            if right_diff > 20:  # 右邊緣差異太大
                self.logger(f"[嚴格驗證] 右邊緣差異過大: {right_diff:.2f}")
                return False
            
            # 3️⃣ 直方圖相似度驗證
            hist_template = cv2.calcHist([template_gray], [0], None, [256], [0, 256])
            hist_matched = cv2.calcHist([matched_region], [0], None, [256], [0, 256])
            
            cv2.normalize(hist_template, hist_template)
            cv2.normalize(hist_matched, hist_matched)
            
            hist_corr = cv2.compareHist(hist_template, hist_matched, cv2.HISTCMP_CORREL)
            
            if hist_corr < threshold:
                self.logger(f"[嚴格驗證] 直方圖相似度不足: {hist_corr:.3f} < {threshold}")
                return False
            
            # 4️⃣ 結構相似性（使用正規化互相關）
            result = cv2.matchTemplate(matched_region, template_gray, cv2.TM_CCOEFF_NORMED)
            ncc_score = result[0][0]
            
            if ncc_score < threshold:
                self.logger(f"[嚴格驗證] NCC分數不足: {ncc_score:.3f} < {threshold}")
                return False
            
            self.logger(f"[嚴格驗證]  通過 (像素差={mean_diff:.2f}, 邊緣差={right_diff:.2f}, 直方圖={hist_corr:.3f}, NCC={ncc_score:.3f})")
            return True
            
        except Exception as e:
            self.logger(f"[嚴格驗證] 錯誤: {e}")
            return True  # 錯誤時預設通過，避免中斷流程
    
    def _find_strict_match(self, screen_cv, template_gray, result_map, threshold, search_region):
        """ v2.8.2 尋找通過嚴格驗證的匹配位置
        
        當第一個最佳匹配驗證失敗時，嘗試找其他候選位置
        
        Args:
            screen_cv: 螢幕截圖（灰度）
            template_gray: 模板圖片（灰度）
            result_map: matchTemplate 的結果矩陣
            threshold: 匹配閾值
            search_region: 搜尋區域
            
        Returns:
            (center_x, center_y) 或 None
        """
        try:
            h, w = template_gray.shape
            
            # 複製結果矩陣以便操作
            result_copy = result_map.copy()
            
            # 最多嘗試5個候選位置
            for attempt in range(5):
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_copy)
                
                if max_val < threshold:
                    break  # 沒有更多高分候選
                
                # 驗證這個位置
                if self._verify_match_strict(screen_cv, template_gray, max_loc, threshold=0.92):
                    # 計算中心點
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    
                    self.logger(f"[嚴格匹配] 找到備選位置 (嘗試 #{attempt+1}): ({center_x}, {center_y}) 分數:{max_val:.3f}")
                    return (center_x, center_y)
                
                # 將這個位置標記為已檢查（抹除周圍區域）
                x, y = max_loc
                x1 = max(0, x - w // 2)
                y1 = max(0, y - h // 2)
                x2 = min(result_copy.shape[1], x + w // 2 + 1)
                y2 = min(result_copy.shape[0], y + h // 2 + 1)
                result_copy[y1:y2, x1:x2] = -1  # 標記為無效
                
                self.logger(f"[嚴格匹配] 候選 #{attempt+1} ({max_loc}) 驗證失敗，繼續搜尋...")
            
            return None
            
        except Exception as e:
            self.logger(f"[嚴格匹配] 錯誤: {e}")
            return None
    
    def clear_image_cache(self):
        """清除圖片快取"""
        self._image_cache.clear()
        self.logger("[圖片辨識] 已清除圖片快取")
    
    # ==================== YOLO 物件偵測 (v2.8.2+) ====================
    
    def load_yolo_model(self, model_path: str = None) -> bool:
        """載入 YOLO 模型
        
        Args:
            model_path: 模型路徑（可選），預設使用 yolov8s.pt
            
        Returns:
            bool: 是否成功載入
        """
        if not YOLO_AVAILABLE or self._yolo_detector is None:
            self._log("[YOLO]  YOLO 模組不可用，請安裝: pip install ultralytics", "warning")
            return False
        
        success = self._yolo_detector.load_model(model_path)
        if success:
            self._yolo_enabled = True
        return success
    
    def find_object_yolo(self, class_name: str, confidence: float = 0.5,
                        region=None) -> tuple:
        """使用 YOLO 在螢幕上尋找特定物件
        
        Args:
            class_name: 物件類別名稱（如 "person", "laptop", "cell phone"）
            confidence: 信心度閾值 (0-1)
            region: 搜尋區域 (x1, y1, x2, y2)，None 表示全螢幕
            
        Returns:
            (center_x, center_y) 如果找到，否則 None
        """
        if not self._yolo_enabled or self._yolo_detector is None:
            # 嘗試自動載入模型
            if not self.load_yolo_model():
                return None
        
        return self._yolo_detector.find_object(class_name, confidence, region)
    
    def detect_objects_yolo(self, confidence: float = 0.5, region=None) -> list:
        """使用 YOLO 偵測螢幕上的所有物件
        
        Args:
            confidence: 信心度閾值 (0-1)
            region: 搜尋區域
            
        Returns:
            List[Dict]: 偵測結果列表
        """
        if not self._yolo_enabled or self._yolo_detector is None:
            if not self.load_yolo_model():
                return []
        
        return self._yolo_detector.detect_screen(region, confidence)
    
    def get_yolo_classes(self) -> list:
        """取得 YOLO 可偵測的類別列表
        
        Returns:
            List[str]: COCO 類別名稱列表
        """
        if self._yolo_detector:
            return self._yolo_detector.get_available_classes()
        return []
    
    def is_yolo_available(self) -> bool:
        """檢查 YOLO 是否可用
        
        Returns:
            bool: True 如果 YOLO 模組已載入
        """
        return YOLO_AVAILABLE and self._yolo_detector is not None

    def find_image_by_features(self, template, screen_cv, threshold=0.7, min_match_count=10):
        """使用特徵點匹配尋找圖片（Template Matching 的備案方法）
        
        Args:
            template: 模板圖片 (BGR)
            screen_cv: 螢幕截圖 (BGR)
            threshold: Lowe's ratio test 閾值 (0-1)
            min_match_count: 最小匹配點數量
            
        Returns:
            (center_x, center_y, match_count) 如果找到，否則 (None, None, 0)
        """
        try:
            #  使用 ORB 特徵檢測器（快速且免費）
            orb = cv2.ORB_create(nfeatures=2000)  # 增加特徵點數量
            
            # 檢測關鍵點和描述符
            kp1, des1 = orb.detectAndCompute(template, None)
            kp2, des2 = orb.detectAndCompute(screen_cv, None)
            
            if des1 is None or des2 is None:
                self.logger("[特徵匹配] 無法提取特徵點")
                return None, None, 0
            
            #  使用 BFMatcher 進行特徵點匹配
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)
            
            #  Lowe's ratio test 篩選優質匹配
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < threshold * n.distance:
                        good_matches.append(m)
            
            match_count = len(good_matches)
            self.logger(f"[特徵匹配] 找到 {match_count} 個優質匹配點（最小需求：{min_match_count}）")
            
            if match_count >= min_match_count:
                #  使用 RANSAC 計算單應性矩陣
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None:
                    # 計算模板四個角點在螢幕上的位置
                    h, w = template.shape[:2]
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    # 計算中心點
                    center_x = int(np.mean(dst[:, 0, 0]))
                    center_y = int(np.mean(dst[:, 0, 1]))
                    
                    # 驗證中心點是否在合理範圍內
                    if 0 <= center_x < screen_cv.shape[1] and 0 <= center_y < screen_cv.shape[0]:
                        self.logger(f"[特徵匹配]  找到圖片於 ({center_x}, {center_y})，匹配點數：{match_count}")
                        return center_x, center_y, match_count
                    else:
                        self.logger(f"[特徵匹配]  中心點超出螢幕範圍")
                else:
                    self.logger(f"[特徵匹配]  無法計算單應性矩陣")
            
            return None, None, match_count
            
        except Exception as e:
            self.logger(f"[特徵匹配] 錯誤：{e}")
            import traceback
            traceback.print_exc()
            return None, None, 0
    
    def find_images_in_snapshot(self, snapshot, template_list, threshold=0.92, fast_mode=True):
        """在同一張螢幕截圖中批次搜尋多張圖片（一次截圖，多次匹配）
        
        Args:
            snapshot: 螢幕截圖 (PIL.Image 或 numpy array，支援灰度圖)
            template_list: 圖片名稱列表 [{'name': 'pic01', 'threshold': 0.9}, ...]
            threshold: 預設匹配閾值
            fast_mode: 是否使用快速模式
            
        Returns:
            dict: {'pic01': (x, y), 'pic02': None, ...}
        """
        results = {}
        
        try:
            # 轉換截圖為 OpenCV 格式（如果需要）
            if not isinstance(snapshot, np.ndarray):
                screen_cv = cv2.cvtColor(np.array(snapshot), cv2.COLOR_RGB2BGR)
            else:
                # 如果是灰度圖，轉換為BGR以便後續處理
                if len(snapshot.shape) == 2:
                    screen_cv = cv2.cvtColor(snapshot, cv2.COLOR_GRAY2BGR)
                else:
                    screen_cv = snapshot
            
            self.logger(f"[批次辨識] 開始在同一截圖中搜尋 {len(template_list)} 張圖片")
            
            #  批次處理每張圖片
            for template_info in template_list:
                if isinstance(template_info, dict):
                    img_name = template_info.get('name', '')
                    img_threshold = template_info.get('threshold', threshold)
                else:
                    img_name = template_info
                    img_threshold = threshold
                
                if not img_name:
                    continue
                
                # 載入模板圖片和遮罩
                template, mask = self._load_image(img_name)
                if template is None:
                    results[img_name] = None
                    continue
                
                #  在同一張截圖上進行匹配（不重複截圖）
                pos = self._match_template_on_screen(
                    screen_cv, template, mask, 
                    threshold=img_threshold, 
                    fast_mode=fast_mode
                )
                
                results[img_name] = pos
                
                if pos:
                    self.logger(f"[批次辨識]  {img_name} 於 ({pos[0]}, {pos[1]})")
                else:
                    self.logger(f"[批次辨識]  {img_name} 未找到")
            
            return results
            
        except Exception as e:
            self.logger(f"[批次辨識] 錯誤：{e}")
            import traceback
            traceback.print_exc()
            return results
    
    def _match_template_on_screen(self, screen_cv, template, mask, threshold=0.92, fast_mode=False, multi_scale=True):
        """在給定的螢幕截圖上進行模板匹配（支援透明遮罩）
        
        Args:
            screen_cv: 螢幕截圖 (BGR)
            template: 模板圖片 (BGR)
            mask: 透明遮罩（可選）
            threshold: 匹配閾值
            fast_mode: 快速模式
            multi_scale: 多尺度搜尋
            
        Returns:
            (center_x, center_y) 或 None
        """
        try:
            best_match_val = 0
            best_match_loc = None
            best_template_size = None
            best_scale = 1.0
            
            #  快速模式：只使用1.0尺度，跳過多尺度搜尋
            if fast_mode:
                scales = [1.0]  # 極速模式：只用原始尺寸
            else:
                scales = [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2] if multi_scale else [1.0]
            
            for scale in scales:
                if scale != 1.0:
                    width = int(template.shape[1] * scale)
                    height = int(template.shape[0] * scale)
                    if width < 10 or height < 10 or width > screen_cv.shape[1] or height > screen_cv.shape[0]:
                        continue
                    scaled_template = cv2.resize(template, (width, height), interpolation=cv2.INTER_LINEAR)  #  使用INTER_LINEAR加快速度
                    scaled_mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_NEAREST) if mask is not None else None
                else:
                    scaled_template = template
                    scaled_mask = mask
                
                #  使用遮罩進行匹配（如果有透明背景）
                if scaled_mask is not None:
                    # 支援遮罩的演算法：TM_CCORR_NORMED 或 TM_SQDIFF
                    result = cv2.matchTemplate(screen_cv, scaled_template, cv2.TM_CCORR_NORMED, mask=scaled_mask)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    score = max_val
                    loc = max_loc
                else:
                    # 無遮罩：使用標準演算法
                    result = cv2.matchTemplate(screen_cv, scaled_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    score = max_val
                    loc = max_loc
                
                if score > best_match_val:
                    best_match_val = score
                    best_match_loc = loc
                    best_template_size = (scaled_template.shape[1], scaled_template.shape[0])
                    best_scale = scale
            
            # 判斷是否達到閾值
            if best_match_val >= threshold:
                w, h = best_template_size
                center_x = best_match_loc[0] + w // 2
                center_y = best_match_loc[1] + h // 2
                return (center_x, center_y)
            else:
                return None
                
        except Exception as e:
            self.logger(f"[模板匹配] 錯誤：{e}")
            return None
    
    def find_image_by_features(self, template, screen_cv, threshold=0.7, min_match_count=10):
        """使用特徵點匹配尋找圖片（Template Matching 的備案方法）
        
        Args:
            template: 模板圖片 (BGR)
            screen_cv: 螢幕截圖 (BGR)
            threshold: Lowe's ratio test 閾值 (0-1)
            min_match_count: 最小匹配點數量
            
        Returns:
            (center_x, center_y, match_count) 如果找到，否則 (None, None, 0)
        """
        try:
            #  使用 ORB 特徵檢測器（快速且免費）
            orb = cv2.ORB_create(nfeatures=2000)  # 增加特徵點數量
            
            # 檢測關鍵點和描述符
            kp1, des1 = orb.detectAndCompute(template, None)
            kp2, des2 = orb.detectAndCompute(screen_cv, None)
            
            if des1 is None or des2 is None:
                self.logger("[特徵匹配] 無法提取特徵點")
                return None, None, 0
            
            #  使用 BFMatcher 進行特徵點匹配
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)
            
            #  Lowe's ratio test 篩選優質匹配
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < threshold * n.distance:
                        good_matches.append(m)
            
            match_count = len(good_matches)
            self.logger(f"[特徵匹配] 找到 {match_count} 個優質匹配點（最小需求：{min_match_count}）")
            
            if match_count >= min_match_count:
                #  使用 RANSAC 計算單應性矩陣
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if M is not None:
                    # 計算模板四個角點在螢幕上的位置
                    h, w = template.shape[:2]
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    # 計算中心點
                    center_x = int(np.mean(dst[:, 0, 0]))
                    center_y = int(np.mean(dst[:, 0, 1]))
                    
                    # 驗證中心點是否在合理範圍內
                    if 0 <= center_x < screen_cv.shape[1] and 0 <= center_y < screen_cv.shape[0]:
                        self.logger(f"[特徵匹配]  找到圖片於 ({center_x}, {center_y})，匹配點數：{match_count}")
                        return center_x, center_y, match_count
                    else:
                        self.logger(f"[特徵匹配]  中心點超出螢幕範圍")
                else:
                    self.logger(f"[特徵匹配]  無法計算單應性矩陣")
            
            return None, None, match_count
            
        except Exception as e:
            self.logger(f"[特徵匹配] 錯誤：{e}")
            import traceback
            traceback.print_exc()
            return None, None, 0
    
    def execute_image_action(self, action_type, target_name, button="left", **kwargs):
        """執行圖片辨識相關動作
        
        Args:
            action_type: 動作類型 ("move_to", "click", "wait_for")
            target_name: 目標圖片名稱
            button: 滑鼠按鍵 ("left", "right", "middle")
            **kwargs: 其他參數（threshold, region, timeout等）
            
        Returns:
            True 如果成功，False 如果失敗
        """
        threshold = kwargs.get('threshold', 0.8)
        region = kwargs.get('region', None)
        timeout = kwargs.get('timeout', 5.0)
        
        if action_type == "move_to":
            # 移動滑鼠到圖片位置
            pos = self.find_image_on_screen(target_name, threshold, region)
            if pos:
                mouse.move(pos[0], pos[1])
                self.logger(f"[圖片辨識] 已移動滑鼠至 {target_name}")
                return True
            else:
                self.logger(f"[圖片辨識] 移動失敗：找不到 {target_name}")
                return False
        
        elif action_type == "click":
            # 點擊圖片位置
            pos = self.find_image_on_screen(target_name, threshold, region)
            if pos:
                # 移動並點擊
                mouse.move(pos[0], pos[1])
                time.sleep(0.05)
                
                if button == "left":
                    mouse.click()
                elif button == "right":
                    mouse.right_click()
                elif button == "middle":
                    mouse.click(button='middle')
                
                self.logger(f"[圖片辨識] 已{button}鍵點擊 {target_name}")
                return True
            else:
                self.logger(f"[圖片辨識] 點擊失敗：找不到 {target_name}")
                return False
        
        elif action_type == "wait_for":
            # 等待圖片出現
            start_time = time.time()
            while time.time() - start_time < timeout:
                pos = self.find_image_on_screen(target_name, threshold, region)
                if pos:
                    self.logger(f"[圖片辨識] 已找到 {target_name}")
                    return True
                time.sleep(0.5)
            
            self.logger(f"[圖片辨識] 等待逾時：{target_name} 未出現")
            return False
        
        else:
            self.logger(f"[圖片辨識] 未知動作類型：{action_type}")
            return False
