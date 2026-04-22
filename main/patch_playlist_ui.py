import os, re

with open('ChroLens_Mimic.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update refresh_script_list
refresh_patch = '''    def refresh_script_list(self):
        """重新整理腳本下拉選單內容（去除副檔名顯示）"""
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        # 顯示時去除副檔名，但實際儲存時仍使用完整檔名
        display_scripts = ["[ 群組播放佇列 ]"] + [os.path.splitext(f)[0] for f in scripts]
        self.script_combo['values'] = display_scripts
        
        # 若目前選擇的腳本不存在，則清空
        current = self.script_var.get()
        if current == "[ 群組播放佇列 ]":
            return
        if current.endswith('.json'):
            current_display = os.path.splitext(current)[0]
        else:
            current_display = current
        
        if current_display not in display_scripts:
            self.script_var.set('')
        else:
            self.script_var.set(current_display)'''

content = re.sub(
    r'    def refresh_script_list\(self\):.*?self\.script_var\.set\(current_display\)',
    refresh_patch,
    content,
    flags=re.DOTALL
)

# 2. Update on_script_selected
on_script_patch = '''    def on_script_selected(self, event=None):
        """載入選中的腳本及其設定"""
        script = self.script_var.get()
        if not script or not script.strip():
            return
            
        if script == "[ 群組播放佇列 ]":
            self.show_page(0)
            return
        
        # 如果沒有副檔名，加上 .json'''

content = re.sub(
    r'    def on_script_selected\(self, event=None\):.*?# 如果沒有副檔名，加上 \.json',
    on_script_patch,
    content,
    flags=re.DOTALL
)

# Insert logic for is_group inside on_script_selected
is_group_patch = '''            # 載入腳本資料
            data = sio_load_script(path)
            
            if data.get("is_group", False):
                self.log(f"[{format_time(time.time())}] 載入群組播放佇列：{script_file}")
                self.playlist_data = data.get("playlist", [])
                self._update_playlist_ui()
                self.events = []
                self.show_page(0)
                return
                
            #  檢查資料完整性'''

content = re.sub(
    r'            # 載入腳本資料\s*data = sio_load_script\(path\)\s*#  檢查資料完整性',
    is_group_patch,
    content
)

# 3. Rewrite _update_playlist_ui, pl_load_scripts, pl_save
playlist_methods_patch = '''    def _update_playlist_ui(self):
        self.playlist_listbox.delete(0, "end")
        for idx, item in enumerate(self.playlist_data):
            prefix = "" if item.get('enabled', True) else "[已停用] "
            pointer = "▶ " if self._is_playlist_playing and idx == self._current_pl_index else "  "
            # Format: 1 01-公會.json
            display_text = f"{pointer}{idx+1:2d} {prefix}{item['name']}"
            self.playlist_listbox.insert("end", display_text)
            
            if not item.get('enabled', True):
                self.playlist_listbox.itemconfig(idx, {'fg': '#555555'})
            elif self._is_playlist_playing and idx == self._current_pl_index:
                self.playlist_listbox.itemconfig(idx, {'fg': '#00ff00', 'bg': '#2a4d2a'})
        
        if len(self.playlist_data) > 0:
            self.pl_mode_label.config(text="狀態: 群組播放待命", foreground="#00ff00")
        else:
            self.pl_mode_label.config(text="模式: 單一載入", foreground="#888888")

    def pl_load_scripts(self):
        # 開啟自訂的加入群組播放清單視窗
        dialog = tk.Toplevel(self)
        dialog.title("加入群組播放清單")
        dialog.geometry("400x500")
        dialog.grab_set()
        dialog.transient(self)
        
        # 居中顯示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tb.Frame(dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # 搜尋框
        search_frame = tb.Frame(main_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        tb.Label(search_frame, text="搜尋：", font=("Microsoft JhengHei", 12)).pack(side="left")
        search_var = tk.StringVar()
        search_entry = tb.Entry(search_frame, textvariable=search_var, font=("Microsoft JhengHei", 12))
        search_entry.pack(side="left", fill="x", expand=True)
        
        # 列表框
        list_frame = tb.LabelFrame(main_frame, text="可用腳本名稱", padding=5)
        list_frame.pack(fill="both", expand=True)
        
        listbox = tk.Listbox(list_frame, font=("Microsoft JhengHei", 12), selectmode="extended", bg="#2b2b2b", fg="#e0e0e0")
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tb.Scrollbar(list_frame, command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)
        
        # 載入腳本列表
        scripts = sorted([f for f in os.listdir(self.script_dir) if f.endswith('.json') and not f.startswith('群組-')])
        
        def update_list(*args):
            search_term = search_var.get().lower()
            listbox.delete(0, "end")
            for s in scripts:
                if search_term in s.lower():
                    listbox.insert("end", s)
        
        search_var.trace("w", update_list)
        update_list()
        
        # 按鈕區
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        def on_confirm():
            selections = listbox.curselection()
            for idx in selections:
                script_name = listbox.get(idx)
                path = os.path.join(self.script_dir, script_name)
                self.playlist_data.append({
                    'path': path,
                    'name': script_name,
                    'enabled': True
                })
            self._update_playlist_ui()
            dialog.destroy()
            
        tb.Button(btn_frame, text="確認新增", bootstyle="success", command=on_confirm).pack(side="right", padx=(5, 0))
        tb.Button(btn_frame, text="取消", bootstyle="secondary", command=dialog.destroy).pack(side="right")

    def pl_save(self):
        if not self.playlist_data:
            self.log("播放佇列為空，無法儲存。")
            return
        # 使用自訂對話框輸入名稱
        import tkinter.simpledialog as simpledialog
        name = simpledialog.askstring("儲存群組", "請輸入群組名稱（將自動加上 '群組-' 前綴）：", parent=self)
        if not name or not name.strip():
            return
            
        if not name.startswith("群組-"):
            name = f"群組-{name}"
        if not name.endswith(".json"):
            name += ".json"
            
        path = os.path.join(self.script_dir, name)
        
        import json
        try:
            # 儲存為一個特殊的群組格式
            group_data = {
                "is_group": True,
                "playlist": self.playlist_data
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(group_data, f, ensure_ascii=False, indent=2)
            self.log(f"群組播放佇列已儲存: {name}")
            self.refresh_script_list()
        except Exception as e:
            self.log(f"儲存失敗: {e}")'''

content = re.sub(
    r'    def _update_playlist_ui\(self\):.*?except Exception as e:\n\s*self\.log\(f"儲存失敗: \{e\}"\)',
    playlist_methods_patch,
    content,
    flags=re.DOTALL
)

with open('ChroLens_Mimic.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied successfully.")
