import codecs
import time

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/recorder.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

old_protect = """            # === [防護機制] 最上層視窗驗證 ===
            if self._target_hwnd and event.get('event') == 'down':
                try:
                    import win32gui
                    current_fg = win32gui.GetForegroundWindow()
                    if current_fg != self._target_hwnd:
                        self.logger(f"[防護] 目標視窗未置頂，略過按下 {event.get('name')}")
                        return
                except Exception as e:
                    pass
            # =================================="""

new_protect = """            # === [防護機制] 最上層視窗驗證 (三段開關) ===
            if self._target_hwnd and event.get('event') == 'down':
                try:
                    import win32gui
                    import time
                    current_fg = win32gui.GetForegroundWindow()
                    if current_fg != self._target_hwnd:
                        strategy = getattr(self, 'bg_protect_strategy', 'skip')
                        if strategy == 'skip':
                            self.logger(f"[防護] 目標視窗未置頂，略過按下 {event.get('name')}")
                            return
                        elif strategy == 'pause':
                            self.logger(f"[防護] 目標視窗未置頂，自動暫停等待...")
                            # 進入暫停迴圈，直到視窗回到最上層，或者播放被停止
                            while self.playing and not self.paused:
                                if win32gui.GetForegroundWindow() == self._target_hwnd:
                                    self.logger(f"[防護] 目標視窗已置頂，恢復執行。")
                                    break
                                time.sleep(0.5)
                        elif strategy == 'force':
                            self.logger(f"[防護] 目標視窗未置頂，強制搶奪焦點！")
                            win32gui.SetForegroundWindow(self._target_hwnd)
                            time.sleep(0.1) # 給予切換緩衝時間
                except Exception as e:
                    pass
            # =================================================="""

if old_protect in content:
    content = content.replace(old_protect, new_protect)
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(content)
    print("Protection strategy patch applied successfully")
else:
    print("Old protection string not found!")
