import os, sys, re, json

with open('ChroLens_Mimic.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add to __init__
if 'self.playlist_data = []' not in content:
    init_pattern = r'(self\.recording = False\s*self\.playing = False\s*self\.paused = False\s*self\.events = \[\]\s*self\.target_hwnd = None)'
    replacement = r'\1\n        self.playlist_data = []\n        self._current_pl_index = -1\n        self._is_playlist_playing = False\n        self._drag_start_index = None'
    content = re.sub(init_pattern, replacement, content)

# Add new methods at the end of RecorderApp
new_methods = '''

    # ==========================================
    # 群組播放佇列 (Playlist) 相關邏輯
    # ==========================================
    def _update_playlist_ui(self):
        self.playlist_listbox.delete(0, "end")
        for idx, item in enumerate(self.playlist_data):
            prefix = "" if item.get('enabled', True) else "[已停用] "
            pointer = "-> " if self._is_playlist_playing and idx == self._current_pl_index else "   "
            self.playlist_listbox.insert("end", f"{pointer}{prefix}{item['name']}")
            if not item.get('enabled', True):
                self.playlist_listbox.itemconfig(idx, {'fg': '#555555'})
            elif self._is_playlist_playing and idx == self._current_pl_index:
                self.playlist_listbox.itemconfig(idx, {'fg': '#00ff00', 'bg': '#2a4d2a'})
        
        if len(self.playlist_data) > 0:
            self.pl_mode_label.config(text="模式: 群組播放", foreground="#00ff00")
        else:
            self.pl_mode_label.config(text="模式: 單一載入", foreground="#888888")

    def pl_load_scripts(self):
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")], initialdir=self.script_dir)
        if paths:
            for p in paths:
                self.playlist_data.append({
                    'path': p,
                    'name': os.path.basename(p),
                    'enabled': True
                })
            self._update_playlist_ui()

    def pl_clear(self):
        self.playlist_data.clear()
        self._update_playlist_ui()

    def pl_toggle(self):
        selections = self.playlist_listbox.curselection()
        for idx in selections:
            self.playlist_data[idx]['enabled'] = not self.playlist_data[idx].get('enabled', True)
        self._update_playlist_ui()
        # 重新選取
        for idx in selections:
            self.playlist_listbox.selection_set(idx)

    def pl_save(self):
        if not self.playlist_data:
            self.log("播放佇列為空，無法儲存。")
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=self.script_dir, title="儲存群組播放佇列")
        if path:
            import json
            try:
                # 儲存為一個特殊的群組格式
                group_data = {
                    "is_group": True,
                    "playlist": self.playlist_data
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(group_data, f, ensure_ascii=False, indent=2)
                self.log(f"群組播放佇列已儲存: {os.path.basename(path)}")
                self.refresh_script_list()
            except Exception as e:
                self.log(f"儲存失敗: {e}")

    def pl_move_up(self):
        selections = self.playlist_listbox.curselection()
        if not selections or selections[0] == 0:
            return
        idx = selections[0]
        self.playlist_data[idx - 1], self.playlist_data[idx] = self.playlist_data[idx], self.playlist_data[idx - 1]
        self._update_playlist_ui()
        self.playlist_listbox.selection_set(idx - 1)

    def pl_move_down(self):
        selections = self.playlist_listbox.curselection()
        if not selections or selections[0] == len(self.playlist_data) - 1:
            return
        idx = selections[0]
        self.playlist_data[idx + 1], self.playlist_data[idx] = self.playlist_data[idx], self.playlist_data[idx + 1]
        self._update_playlist_ui()
        self.playlist_listbox.selection_set(idx + 1)

    def pl_drag_start(self, event):
        self._drag_start_index = self.playlist_listbox.nearest(event.y)

    def pl_drag_motion(self, event):
        if not hasattr(self, '_drag_start_index') or self._drag_start_index is None:
            return
        current_idx = self.playlist_listbox.nearest(event.y)
        if current_idx != self._drag_start_index and 0 <= current_idx < len(self.playlist_data):
            item = self.playlist_data.pop(self._drag_start_index)
            self.playlist_data.insert(current_idx, item)
            self._update_playlist_ui()
            self._drag_start_index = current_idx
            self.playlist_listbox.selection_clear(0, "end")
            self.playlist_listbox.selection_set(current_idx)

    def pl_drag_end(self, event):
        self._drag_start_index = None
'''

if 'def pl_load_scripts(self):' not in content:
    # Insert before the end of the file
    content += new_methods

with open('ChroLens_Mimic.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Methods added')
