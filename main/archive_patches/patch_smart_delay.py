import codecs
import re

# =======================
# 1. Patch ChroLens_Mimic.py
# =======================
file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/ChroLens_Mimic.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

old_ask_strategy_pattern = r'def ask_strategy\(\):.*?self\.after\(100, ask_strategy\)'
new_ask_strategy = """def ask_strategy():
                    popup = tb.Toplevel(self)
                    popup.title("視窗切換確認")
                    popup.geometry("400x260")
                    popup.attributes('-topmost', True)
                    popup.update_idletasks()
                    x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
                    y = self.winfo_y() + (self.winfo_height() // 2) - (260 // 2)
                    popup.geometry(f"+{x}+{y}")
                    
                    tb.Label(popup, text=f"已選定目標視窗:\\n{short}", font=("", 10, "bold"), justify="center").pack(pady=10)
                    tb.Label(popup, text="當前指定視窗非置頂時：").pack(pady=5)
                    
                    options = [
                        "1. Skip-忽略且繼續腳本",
                        "2. Pause-暫停腳本",
                        "3. Force-強制切換指定視窗且繼續腳本"
                    ]
                    
                    old_val = self.user_config.get("bg_protect_strategy", "3.")
                    if old_val == "skip" or old_val.startswith("1."): def_val = options[0]
                    elif old_val == "pause" or old_val.startswith("2."): def_val = options[1]
                    else: def_val = options[2]
                    
                    strategy_var = tb.StringVar(value=def_val)
                    cb = tb.Combobox(popup, textvariable=strategy_var, values=options, state="readonly", width=38)
                    cb.pack(pady=5)
                    
                    # 延遲輸入區塊 (含 Checkbox)
                    delay_frame = tb.Frame(popup)
                    delay_frame.pack(pady=5)
                    
                    force_wait_var = tb.BooleanVar(value=self.user_config.get("bg_protect_force_wait", False))
                    cb_wait = tb.Checkbutton(delay_frame, text="強迫等待", variable=force_wait_var, bootstyle="round-toggle")
                    cb_wait.pack(side="left", padx=5)
                    
                    delay_var = tb.StringVar(value=str(self.user_config.get("bg_protect_delay", "2")))
                    tb.Entry(delay_frame, textvariable=delay_var, width=4, justify="center").pack(side="left")
                    tb.Label(delay_frame, text="秒後繼續腳本").pack(side="left", padx=5)
                    
                    def on_confirm():
                        selected = strategy_var.get()
                        try: delay_val = float(delay_var.get())
                        except ValueError: delay_val = 2.0
                        force_wait_val = force_wait_var.get()
                            
                        self.user_config["bg_protect_strategy"] = selected
                        self.user_config["bg_protect_delay"] = delay_val
                        self.user_config["bg_protect_force_wait"] = force_wait_val
                        self.save_config()
                        
                        if hasattr(self.core_recorder, 'bg_protect_strategy'):
                            self.core_recorder.bg_protect_strategy = selected
                        if hasattr(self.core_recorder, 'bg_protect_delay'):
                            self.core_recorder.bg_protect_delay = delay_val
                        if hasattr(self.core_recorder, 'bg_protect_force_wait'):
                            self.core_recorder.bg_protect_force_wait = force_wait_val
                            
                        self.log(f"套用防護策略: {selected}, 強迫等待: {force_wait_val}, 延遲: {delay_val}s")
                        popup.destroy()
                        
                    tb.Button(popup, text="確認", bootstyle="primary", command=on_confirm).pack(pady=10)
                    
                self.after(100, ask_strategy)"""

new_content = re.sub(old_ask_strategy_pattern, new_ask_strategy, content, flags=re.DOTALL)
if new_content != content:
    with codecs.open(file_path, 'w', 'utf-8') as f:
        f.write(new_content)
    print("Patched ChroLens_Mimic.py successfully.")
else:
    print("Failed to patch ChroLens_Mimic.py")

# =======================
# 2. Patch recorder.py
# =======================
recorder_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/recorder.py'
with codecs.open(recorder_path, 'r', 'utf-8') as f:
    rec_content = f.read()

new_rec_block = """                        strategy = getattr(self, 'bg_protect_strategy', '3. Force')
                        delay = getattr(self, 'bg_protect_delay', 2.0)
                        force_wait = getattr(self, 'bg_protect_force_wait', False)
                        
                        if strategy.startswith('1.') or strategy == 'skip':
                            self.logger(f"[防護] 目標視窗未置頂，略過按下 {event.get('name')}")
                            return
                        elif strategy.startswith('2.') or strategy == 'pause':
                            self.logger(f"[防護] 目標視窗未置頂，自動暫停...")
                            while self.playing and not self.paused:
                                if win32gui.GetForegroundWindow() == self._target_hwnd:
                                    self.logger(f"[防護] 目標視窗已置頂，恢復。")
                                    break
                                time.sleep(0.5)
                        elif strategy.startswith('3.') or strategy == 'force':
                            self.logger(f"[防護] 目標視窗未置頂，強制切換並等待 {delay} 秒 (強迫:{force_wait})...")
                            try:
                                win32gui.SetForegroundWindow(self._target_hwnd)
                            except Exception:
                                pass
                            
                            if force_wait:
                                time.sleep(delay)
                            else:
                                elapsed = 0.0
                                while elapsed < delay and self.playing:
                                    if win32gui.GetForegroundWindow() == self._target_hwnd:
                                        time.sleep(0.2)
                                        break
                                    time.sleep(0.1)
                                    elapsed += 0.1"""

rec_pattern = r"strategy = getattr\(self, 'bg_protect_strategy', '3. Force'\).*?elapsed \+= 0\.1.*?# 如果超過延遲時間，還是會強制繼續執行"
new_rec_content = re.sub(rec_pattern, new_rec_block, rec_content, flags=re.DOTALL)

if new_rec_content != rec_content:
    with codecs.open(recorder_path, 'w', 'utf-8') as f:
        f.write(new_rec_content)
    print("Patched recorder.py successfully.")
else:
    print("Failed to patch recorder.py")
