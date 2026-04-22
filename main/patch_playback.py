import os, sys, re, json

with open('ChroLens_Mimic.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add _play_next_in_playlist method
play_next_method = '''
    def _play_next_in_playlist(self):
        """播放佇列中的下一個啟用的腳本"""
        start_idx = self._current_pl_index + 1
        found_idx = -1
        for i in range(start_idx, len(self.playlist_data)):
            if self.playlist_data[i].get('enabled', True):
                found_idx = i
                break
        
        if found_idx == -1:
            self.log(f"[{format_time(time.time())}] 群組播放佇列已全數執行完畢。")
            self._is_playlist_playing = False
            self.playing = False
            self._current_pl_index = -1
            self._update_playlist_ui()
            
            # 停止時的 UI 重置
            self.update_time_label(0)
            self.update_countdown_label(0)
            self.update_total_time_label(0)
            self._release_all_modifiers()
            return False
            
        self._current_pl_index = found_idx
        self._update_playlist_ui()
        
        path = self.playlist_data[found_idx]['path']
        try:
            from script_io import sio_load_script
            data = sio_load_script(path)
            self.events = data.get("events", [])
            self.log(f"[{format_time(time.time())}] 佇列執行: {os.path.basename(path)}")
            # 開始執行
            self._continue_play_record()
            return True
        except Exception as e:
            self.log(f"佇列腳本載入失敗: {e}，跳過此腳本。")
            return self._play_next_in_playlist()
'''

if 'def _play_next_in_playlist(self):' not in content:
    content = content.replace('def play_record(self):', play_next_method + '\n    def play_record(self):')

# 2. Patch play_record to handle playlist
play_record_patch = '''    def play_record(self):
        """開始執行"""
        if self.playing:
            return
            
        has_enabled_pl = any(item.get('enabled', True) for item in self.playlist_data)
        if has_enabled_pl:
            self.playing = True
            self._is_playlist_playing = True
            self._current_pl_index = -1
            self.log(f"[{format_time(time.time())}] 開始執行群組播放佇列。")
            
            if self.auto_mini_var.get() and not self.mini_mode_on:
                self.toggle_mini_mode()
                
            self.playback_offset_x = 0
            self.playback_offset_y = 0
            
            self._play_next_in_playlist()
            return
            
        if not self.events:
            self.log("沒有可執行的事件，請先錄製或載入腳本。")
            return'''

if 'has_enabled_pl = any(item.get' not in content:
    content = re.sub(
        r'    def play_record\(self\):\n\s*"""開始執行"""\n\s*if self\.playing:\n\s*return\n\s*if not self\.events:\n\s*self\.log\("沒有可執行的事件，請先錄製或載入腳本。"\)\n\s*return',
        play_record_patch,
        content,
        count=1
    )

# 3. Patch _update_play_time to call _play_next_in_playlist
update_play_time_patch = '''            # 檢查 core_recorder 是否仍在播放
            if not getattr(self.core_recorder, 'playing', False):
                # 執行已結束，同步狀態
                if self._is_playlist_playing:
                    self._play_next_in_playlist()
                    return
                else:
                    self.playing = False
                    self.log(f"[{format_time(time.time())}] 執行完成")
                    
                    # 釋放所有可能卡住的修飾鍵
                    self._release_all_modifiers()
                    
                    self.update_time_label(0)
                    self.update_countdown_label(0)
                    self.update_total_time_label(0)'''

if 'if self._is_playlist_playing:' not in content:
    content = re.sub(
        r'            # 檢查 core_recorder 是否仍在播放\n\s*if not getattr\(self\.core_recorder, \'playing\', False\):\n\s*# 執行已結束，同步狀態\n\s*self\.playing = False\n\s*self\.log\(f"\[\{format_time\(time\.time\(\)\)\}\] 執行完成"\)\n\s*# 釋放所有可能卡住的修飾鍵\n\s*self\._release_all_modifiers\(\)\n\s*self\.update_time_label\(0\)\n\s*self\.update_countdown_label\(0\)\n\s*self\.update_total_time_label\(0\)',
        update_play_time_patch,
        content,
        count=1
    )

# 4. Patch stop_all to handle playlist reset
stop_all_patch = '''    def stop_all(self):
        """停止所有動作（全新實作 - 更穩健的處理）"""
        self._is_playlist_playing = False
        self._current_pl_index = -1
        self._update_playlist_ui()
        
        stopped = False'''

if 'self._is_playlist_playing = False' not in content:
    content = content.replace(
        '''    def stop_all(self):
        """停止所有動作（全新實作 - 更穩健的處理）"""
        stopped = False''',
        stop_all_patch,
        1
    )

with open('ChroLens_Mimic.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied successfully.")
