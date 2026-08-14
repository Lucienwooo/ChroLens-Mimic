import codecs
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = f.readlines()

insert_idx = -1
for i, line in enumerate(lines):
    if "setattr(self.core_recorder, \"target_hwnd\", hwnd)" in line:
        # Find the end of this try-except block
        for j in range(i, i+10):
            if "WindowSelectorDialog(self, on_selected)" in lines[j]:
                insert_idx = j
                break
        break

if insert_idx != -1:
    new_code = """
                # 彈出確認視窗，選擇防護策略
                def ask_strategy():
                    popup = tb.Toplevel(self)
                    popup.title("選擇防護策略")
                    popup.geometry("350x200")
                    popup.attributes('-topmost', True)
                    # 讓視窗居中
                    popup.update_idletasks()
                    x = self.winfo_x() + (self.winfo_width() // 2) - (350 // 2)
                    y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
                    popup.geometry(f"+{x}+{y}")
                    
                    tb.Label(popup, text=f"已選定目標視窗:\\n{short}", font=("", 10, "bold"), justify="center").pack(pady=10)
                    tb.Label(popup, text="請選擇失焦防護策略：").pack(pady=5)
                    
                    strategy_var = tb.StringVar(value=self.user_config.get("bg_protect_strategy", "skip"))
                    cb = tb.Combobox(popup, textvariable=strategy_var, values=["skip", "pause", "force"], state="readonly")
                    cb.pack(pady=5)
                    
                    def on_confirm():
                        selected = strategy_var.get()
                        self.user_config["bg_protect_strategy"] = selected
                        self.save_config()
                        if hasattr(self.core_recorder, 'bg_protect_strategy'):
                            self.core_recorder.bg_protect_strategy = selected
                        self.log(f"已套用防護策略: {selected}")
                        popup.destroy()
                        
                    tb.Button(popup, text="確認", bootstyle="primary", command=on_confirm).pack(pady=10)
                    
                # 延遲一點點時間彈出，避免與選擇視窗衝突
                self.after(100, ask_strategy)
"""
    lines.insert(insert_idx, new_code)
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.writelines(lines)
    print("Patch applied successfully.")
else:
    print("Could not find the insertion point.")
