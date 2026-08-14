import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/visual_tracker_ui.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def setup_tab_basic(self):" in line:
        insert_idx = i
        break

for i in range(insert_idx, len(lines)):
    if "def setup_tab_combat(self):" in lines[i]:
        insert_idx = i
        break

new_code = """
        # === [防護機制] 失焦防護策略 ===
        protect_frame = ttk.LabelFrame(self.tab_basic, text="失焦防護策略 (Background Strategy)")
        protect_frame.pack(fill="x", pady=5)
        
        self.protect_var = tk.StringVar(value=self.main_app.user_config.get("bg_protect_strategy", "skip"))
        
        protect_cb = ttk.Combobox(protect_frame, textvariable=self.protect_var, values=["skip", "pause", "force"], state="readonly", width=15)
        protect_cb.pack(side="left", padx=10, pady=5)
        
        # 綁定變更事件，儲存至設定檔
        def on_protect_change(event):
            self.main_app.user_config["bg_protect_strategy"] = self.protect_var.get()
            self.main_app.save_config()
            self.log(f"已切換防護策略: {self.protect_var.get()}")
            
        protect_cb.bind("<<ComboboxSelected>>", on_protect_change)
        
        ttk.Label(protect_frame, text="skip: 安全略過 | pause: 自動暫停等待 | force: 強制搶奪焦點").pack(side="left", padx=5)
        # ==================================
"""

lines.insert(insert_idx, new_code)

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.writelines(lines)
print('UI patch applied successfully')
