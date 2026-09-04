class KeyCaptureDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        try:
            from utils.utils import set_window_icon
            set_window_icon(self)
        except:
            pass


            
        self.title("捕捉按鍵")
        self.callback = callback
        self.captured_key = ""
        self._pressed_keys = set()
        
        self.geometry("380x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        bg_color = self.cget("bg")
        if not bg_color or bg_color == "SystemButtonFace":
            bg_color = "#2d2d30"
        self.configure(bg=bg_color)
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        try:
            ft_label = font_tuple(12)
            self.ft_display = font_tuple(18, "bold", monospace=True)
        except:
            ft_label = ("Arial", 12)
            self.ft_display = ("Consolas", 18, "bold")
            
        tk.Label(self, text="請按下欲捕捉的按鍵...", bg=bg_color, fg="white", font=ft_label).pack(pady=(15, 5))
        
        self.display_container = tk.Frame(self, bg=bg_color, relief="flat", borderwidth=0, width=380, height=40)
        self.display_container.pack_propagate(False)
        self.display_container.pack(pady=5)
        
        self.canvas = tk.Canvas(self.display_container, bg=bg_color, highlightthickness=0, width=380, height=40)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        
        btn_frame = tk.Frame(self, bg=bg_color)
        btn_frame.pack(pady=10)
        
        btn_reset = tk.Button(btn_frame, text="重設 (Reset)", command=self._reset, bg=bg_color, fg="white", bd=1, relief="solid", activebackground="#3d3d3d", activeforeground="white", padx=15, pady=2)
        btn_reset.pack(side="left", padx=10)
        btn_confirm = tk.Button(btn_frame, text="確認 (Confirm)", command=self._confirm, bg=bg_color, fg="white", bd=1, relief="solid", activebackground="#3d3d3d", activeforeground="white", padx=15, pady=2)
        btn_confirm.pack(side="left", padx=10)
        
        import keyboard
        self.keyboard_hook = keyboard.hook(self._on_keyboard_event, suppress=True)
        self.focus_force()

    def _on_keyboard_event(self, event):
        if event.event_type == 'down':
            key = event.name.lower()
            key_map = {
                'left ctrl': 'ctrl', 'right ctrl': 'ctrl',
                'left alt': 'alt', 'right alt': 'alt',
                'left shift': 'shift', 'right shift': 'shift',
                'left windows': 'win', 'right windows': 'win',
                'enter': 'enter', 'esc': 'esc', 'space': 'space',
                'backspace': 'backspace', 'delete': 'delete', 'tab': 'tab'
            }
            key = key_map.get(key, key)
            
            if key not in self._pressed_keys and len(self._pressed_keys) < 4:
                self._pressed_keys.add(key)
                self.after(0, self._update_captured_key)
        
        return False

    def _update_captured_key(self):
        modifiers = [k for k in ['ctrl', 'alt', 'shift', 'win'] if k in self._pressed_keys]
        normals = [k for k in self._pressed_keys if k not in modifiers]
        self.captured_key = "+".join(modifiers + normals)
        self._render_keys()

    def _render_keys(self):
        self.canvas.delete("all")
        if not self.captured_key:
            return
            
        parts = self.captured_key.split('+')
        
        import tkinter.font as tkfont
        font_obj = tkfont.Font(font=self.ft_display)
        
        total_width = 0
        elements = []
        for i, part in enumerate(parts):
            color = "#c586c0"
            if part == "ctrl": color = "#569cd6"
            elif part == "alt": color = "#dcdcaa"
            elif part == "shift": color = "#4ec9b0"
            elif part == "win": color = "#9cdcfe"
            elif part == "+": color = "#d4d4d4"
            
            w = font_obj.measure(part)
            elements.append((part, color, w))
            total_width += w
            
            if i < len(parts) - 1:
                pw = font_obj.measure("+")
                elements.append(("+", "#d4d4d4", pw))
                total_width += pw
                
        start_x = (380 - total_width) // 2
        y = 20
        
        current_x = start_x
        for text, color, w in elements:
            self.canvas.create_text(current_x, y, text=text, fill=color, font=self.ft_display, anchor="w")
            current_x += w

    def _reset(self):
        self.captured_key = ""
        self._pressed_keys.clear()
        self._render_keys()
        self.focus_force()
        
    def _cleanup_hook(self):
        if hasattr(self, 'keyboard_hook') and self.keyboard_hook:
            import keyboard
            keyboard.unhook(self.keyboard_hook)
            self.keyboard_hook = None

    def _on_close(self):
        self._cleanup_hook()
        self.destroy()

    def _confirm(self):
        self._cleanup_hook()
        self.destroy()
        if self.callback and self.captured_key:
            self.callback(self.captured_key)
