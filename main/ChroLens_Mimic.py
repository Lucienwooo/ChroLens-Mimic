
# ChroLens Studio - Lucienwooo
# python "C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\ChroLens_Mimic.py"
#
<<<<<<< Updated upstream
# ---------------------------------------------------------------------------
# [ AI Agent 必讀 ]
# ---------------------------------------------------------------------------
# 在對本專案進行任何修改前，請先閱讀 AI_AGENT_NOTES.py
# 該檔案包含所有開發規範、流程說明、版本管理規則和重要備註
# ---------------------------------------------------------------------------

VERSION = "2.7.6"
=======
# 
# i?? AI Agent Ūj
# 
# b糧M׶iקeAХ\Ū AI_AGENT_NOTES.py
# ɮץ]tҦ}oWdBy{B޲zWhMnƵ
# 

GITHUB_REPO = "Lucienwooo/ChroLens-Mimic"
VERSION = "2.7.5"
>>>>>>> Stashed changes

import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import threading, time, json, os, datetime
import keyboard, mouse
import ctypes
import win32api
import win32gui
import win32con
import pywintypes
import random  # sW
import tkinter.font as tkfont
import sys

# 新增：系統托盤支援
try:
    import pystray
    from PIL import Image as PILImage
    PYSTRAY_AVAILABLE = True
except ImportError:
    print("pystray 或 Pillow 未安裝，將停用系統托盤功能")
    PYSTRAY_AVAILABLE = False




# 檢查是否為管理員
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 新增：匯入 Recorder / 語言 / 腳本 IO 函式（使用 fallback 機制）
try:
    from recorder import CoreRecorder
except Exception as e:
    print(f"無法匯入 CoreRecorder: {e}")

# 使用文字指令式腳本編輯器（已移除舊版圖形化編輯器）
try:
    from text_script_editor import TextCommandEditor as VisualScriptEditor
    print("[訊息] 已載入文字指令編輯器")
except Exception as e:
    print(f"[錯誤] 無法匯入編輯器: {e}")
    import traceback
    traceback.print_exc()
    VisualScriptEditor = None
try:
    from lang import LANG_MAP
except Exception as e:
    print(f"無法匯入 LANG_MAP: {e}")

# 強化版函式匯入：嘗試匯入但若失敗則使用 module 屬性偵測，最後提供 fallback 函式
try:
    # 嘗試標準匯入
    from script_io import sio_auto_save_script, sio_load_script, sio_save_script_settings
except Exception as _e:
    try:
        import script_io as _sio_mod
        sio_auto_save_script = getattr(_sio_mod, "sio_auto_save_script", getattr(_sio_mod, "auto_save_script", None))
        sio_load_script = getattr(_sio_mod, "sio_load_script", getattr(_sio_mod, "load_script", None))
        sio_save_script_settings = getattr(_sio_mod, "sio_save_script_settings", getattr(_sio_mod, "save_script_settings", None))
        if not (sio_auto_save_script and sio_load_script and sio_save_script_settings):
            raise ImportError("script_io 模組缺少必要函式")
    except Exception as e:
        print(f"無法匯入 script_io 函式: {e}")
        # ѳ̤p fallback @ATOD{B@]|^/gJ¦ JSON^
        def sio_auto_save_script(script_dir, events, settings):
            if not os.path.exists(script_dir):
                os.makedirs(script_dir)
            fname = f"autosave_{int(time.time())}.json"
            path = os.path.join(script_dir, fname)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"events": events, "settings": settings}, f, ensure_ascii=False, indent=2)
                return fname
            except Exception as ex:
                print(f"autosave failed: {ex}")
                return ""

        def sio_load_script(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {"events": data.get("events", []), "settings": data.get("settings", {})}
            except Exception as ex:
                print(f"sio_load_script fallback failed: {ex}")
                return {"events": [], "settings": {}}

        def sio_save_script_settings(path, settings):
            try:
                data = {}
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                data["settings"] = settings
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as ex:
                print(f"sio_save_script_settings fallback failed: {ex}")

# 新增：匯入 about 模組
try:
    import about
except Exception as e:
    print(f"無法匯入 about 模組: {e}")

# 新增：匯入 MiniMode 模組 mini.py
try:
    import mini
except Exception as e:
    print(f"無法匯入 mini 模組: {e}")

# 新增：匯入 window_selector 模組
try:
    from window_selector import WindowSelectorDialog
except Exception as e:
    print(f"無法匯入 window_selector 模組: {e}")
    WindowSelectorDialog = None

# 新增：註冊私有 TTF 字體（若存在），優先供 font_tuple() 呼叫
TTF_PATH = os.path.join(os.path.dirname(__file__), "TTF", "LINESeedTW_TTF_Rg.ttf")

def _register_private_ttf(ttf_path):
    try:
        if os.path.exists(ttf_path):
            FR_PRIVATE = 0x10
            ctypes.windll.gdi32.AddFontResourceExW(ttf_path, FR_PRIVATE, 0)
    except Exception as e:
        print(f"註冊字體失敗: {e}")

# 嘗試註冊（即使失敗也會繼續，避免程式中斷）
_register_private_ttf(TTF_PATH)

def font_tuple(size, weight=None, monospace=False):
    """
    返回 (family, size) 或 (family, size, weight) 的 tuple，
    優先選用 LINESeedTW（若已註冊），否則選用 Microsoft JhengHei。
    monospace=True 時選用 Consolas。
    """
    fam = "Consolas" if monospace else "LINESeedTW_TTF_Rg"
    try:
        # Y|إ tk rootAtkfont.families() i|ѡFH try @
        fams = set(f.lower() for f in tkfont.families())
        # էXH lineseed }Y family
        for f in tkfont.families():
            if f.lower().startswith("lineseed"):
                fam = f
                break
        else:
            # Y䤣 LINESEEDA^h Microsoft JhengHei]Ysb^
            if not monospace:
                for f in tkfont.families():
                    if f.lower().startswith("microsoft jhenghei") or f.lower().startswith("microsoft jhenghei ui"):
                        fam = f
                        break
    except Exception:
        # YLkd familiesAOdw] fam]̫ezȡ^
        pass
    if weight:
        return (fam, size, weight)
    return (fam, size)

def get_icon_path():
    """獲取圖示路徑（包含打包後與開發環境的相容性）"""
    try:
        import sys
        if getattr(sys, 'frozen', False):
            # 打包後的 exe
            return os.path.join(sys._MEIPASS, "umi_.ico")
        else:
            # 開發環境
            # 檢查是否在 main 資料夾
            if os.path.exists("umi_.ico"):
                return "umi_.ico"
            # 檢查上層 pic 資料夾
            elif os.path.exists("../pic/umi_.ico"):
                return "../pic/umi_.ico"
            # 檢查上層資料夾（相容舊版）
            elif os.path.exists("../umi_.ico"):
                return "../umi_.ico"
            else:
                return "umi_.ico"
    except:
        return "umi_.ico"

def set_window_icon(window):
    """設定視窗圖示"""
    try:
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"設定視窗圖示失敗: {e}")

def show_error_window(window_name):
    ctypes.windll.user32.MessageBoxW(
        0,
        f'䤣 "{window_name}" AЭ',
        '~',
        0x10  # MB_ICONERROR
    )

def client_to_screen(hwnd, rel_x, rel_y, window_name=""):
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        abs_x = left + rel_x
        abs_y = top + rel_y
        return abs_x, abs_y
    except pywintypes.error:
        ctypes.windll.user32.MessageBoxW(
            0,
            f'䤣 "{window_name}" AЭ',
            '~',
            0x10  # MB_ICONERROR
        )
        raise

# ====== ƹ禡bo ======
def move_mouse_abs(x, y):
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def mouse_event_win(event, x=0, y=0, button='left', delta=0):
    user32 = ctypes.windll.user32
    if not button:
        button = 'left'
    if event == 'down' or event == 'up':
        flags = {'left': (0x0002, 0x0004), 'right': (0x0008, 0x0010), 'middle': (0x0020, 0x0040)}
        flag = flags.get(button, (0x0002, 0x0004))[0 if event == 'down' else 1]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),
                        ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),
                        ("mi", MOUSEINPUT)]
        inp = INPUT()
        inp.type = 0
        inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    elif event == 'wheel':
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),
                        ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),
                        ("mi", MOUSEINPUT)]
        inp = INPUT()
        inp.type = 0
        inp.mi = MOUSEINPUT(0, 0, int(delta * 120), 0x0800, 0, None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


# ====== Ƶ{޲z ======
class ScheduleManager:
    """
    Ƶ{޲z - IˬdɶĲoƵ{}
    
    \G
    - D{}ۮɦ۰ˬdɶ
    - FƵ{ɶ۰ʰ}
    - ĬBzGY}椤AªBs
    """
    
    def __init__(self, app):
        self.app = app
        self.schedules = {}  # {schedule_id: config}
        self.running = True
        self.last_trigger = {}  # קKP@Ĳo {schedule_id: "HH:MM"}
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        print("? Ƶ{޲zwҰ")
    
    def add_schedule(self, schedule_id, config):
        """
        sWƵ{
        config = {
            'name': '}W',
            'type': 'daily',
            'time': 'HH:MM:SS',
            'script': 'script_file.json',
            'enabled': True,
            'callback': function
        }
        """
        self.schedules[schedule_id] = config
        print(f"? wsWƵ{: {schedule_id} @ {config.get('time', '')}")
    
    def remove_schedule(self, schedule_id):
        """Ƶ{"""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            print(f"? wƵ{: {schedule_id}")
    
    def get_all_schedules(self):
        """oҦƵ{"""
        return self.schedules.copy()
    
    def _check_loop(self):
        """I - C 5 ˬd@Ƶ{ɶ]TOǮĲo^"""
        while self.running:
            try:
                now = datetime.datetime.now()
                current_time = now.strftime("%H:%M")
                current_date = now.strftime("%Y-%m-%d")
                
                for sid, config in list(self.schedules.items()):
                    if not config.get('enabled', True):
                        continue
                    
                    # oƵ{ɶ (u HH:MM)
                    schedule_time = config.get('time', '')
                    if ':' in schedule_time:
                        schedule_time = schedule_time[:5]  # "15:30:00" -> "15:30"
                    
                    if schedule_time == current_time:
                        # ϥΤ+ɶ@ keyAקKP@Ĳo
                        trigger_key = f"{current_date}_{current_time}"
                        if self.last_trigger.get(sid) == trigger_key:
                            continue
                        self.last_trigger[sid] = trigger_key
                        
                        # bDĲo}
                        script_file = config.get('script')
                        callback = config.get('callback')
                        
                        if callback and script_file:
                            self.app.after(0, lambda s=script_file, c=callback: self._trigger_script(s, c))
                        
            except Exception as e:
                print(f"Ƶ{ˬd~: {e}")
            
            time.sleep(5)  # C 5 ˬd@]TO̦h 5 ^
    
    def _trigger_script(self, script_file, callback):
        """ĲoƵ{} - YĬhª"""
        try:
            # ˬdO_}b
            if hasattr(self.app, 'playing') and self.app.playing:
                print(f"?? ĬGثe椤}")
                self.app.log(f"?? Ƶ{ĬGثe}AsƵ{")
                self.app.stop_all()
                time.sleep(0.5)  # ݰ
            
            # Ƶ{}
            print(f"? ĲoƵ{: {script_file}")
            self.app.log(f"? Ƶ{Ĳo: {script_file}")
            callback(script_file)
            
        except Exception as e:
            print(f"ĲoƵ{: {e}")
            if hasattr(self.app, 'log'):
                self.app.log(f"? ĲoƵ{: {e}")
    
    def stop(self):
        """Ƶ{޲z"""
        self.running = False
        print("Ƶ{޲zw")


# ====== RecorderApp OPl{X ======
SCRIPTS_DIR = "scripts"
LAST_SCRIPT_FILE = "last_script.txt"
LAST_SKIN_FILE = "last_skin.txt"  # sWo
MOUSE_SAMPLE_INTERVAL = 0.01  # 10ms


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, background="#ffffe0",
            relief="solid", borderwidth=1,
            font=font_tuple(10)
        )
        label.pack(ipadx=6, ipady=2)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def get_dpi_scale():
    """ Windows tΪ DPI Y"""
    try:
        # ]w DPI Awareness
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except:
        pass
    
    try:
        # t DPI
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        scale = dpi / 96.0  # 96 DPI O 100% Y
        return scale
    except:
        return 1.0

def get_screen_resolution():
    """ùѪR"""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)   # SM_CXSCREEN
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        return (width, height)
    except:
        return (1920, 1080)  # w]

def get_window_info(hwnd):
    """T]]t DPIBѪR׵^"""
    try:
        # x
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        pos = (rect[0], rect[1])
        
        # tθT
        dpi_scale = get_dpi_scale()
        screen_res = get_screen_resolution()
        
        return {
            "size": (width, height),
            "position": pos,
            "dpi_scale": dpi_scale,
            "screen_resolution": screen_res,
            "client_size": (width, height)  # ڥiΰϰ
        }
    except Exception as e:
        return None

def screen_to_client(hwnd, x, y):
    # ùyy
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return x - left, y - top

def client_to_screen(hwnd, x, y):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left + x, top + y

class RecorderApp(tb.Window):
    def __init__(self):
        # ˬd޲zv
        if not is_admin():
            # ĵi~
            try:
                print("?? ĵiG{H޲zAs\iLk`u@I")
            except:
                print("[WARNING] Program not running as administrator, recording may not work properly!")
        
        # lưܼ
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []

        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        # Ū̫@y]wAw]c餤
        lang = self.user_config.get("language", "c餤")
        super().__init__(themename=skin)
        
        # pGO޲zAĵiܮ
        if not is_admin():
            self.after(1000, self._show_admin_warning)
        
        self.language_var = tk.StringVar(self, value=lang)
        self._hotkey_handlers = {}
        # Ψxs}ֱ䪺 handler id
        self._script_hotkey_handlers = {}
<<<<<<< Updated upstream
        # ✅ 快捷鍵健康檢查變數
        self._last_hotkey_register_time = 0
        self._hotkey_check_failures = 0
        # MiniMode 管理器（由 mini.py 提供）
=======
        # MiniMode ޲z] mini.py ѡ^
>>>>>>> Stashed changes
        self.mini_window = None
        self.mini_mode_on = False
        self.target_hwnd = None
        self.target_title = None
        
        # Bлx]Ω󱱨O_ܧֱ䴣ܡ^
        self._is_first_run = self.user_config.get("first_run", True)
        if self._is_first_run:
            # аOwBL
            self.user_config["first_run"] = False
            save_user_config(self.user_config)

        # Ū hotkey_mapAYLhιw]
        default_hotkeys = {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "mini": "alt+`",
            "force_quit": "ctrl+alt+z"  # jw]ֱ
        }
        self.hotkey_map = self.user_config.get("hotkey_map", default_hotkeys)
        
        # TO force_quit sb]VUۮe°tm^
        if "force_quit" not in self.hotkey_map:
            self.hotkey_map["force_quit"] = "ctrl+alt+z"

        # ====== Τ@r style ======
        self.style.configure("My.TButton", font=font_tuple(9))
        self.style.configure("My.TLabel", font=font_tuple(9))
        self.style.configure("My.TEntry", font=font_tuple(9))
        self.style.configure("My.TCombobox", font=font_tuple(9))
        self.style.configure("My.TCheckbutton", font=font_tuple(9))
        self.style.configure("miniBold.TButton", font=font_tuple(9, "bold"))

        self.title(f"ChroLens_Mimic_{VERSION}")
        # ]wϥ
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                # ϥ wm_iconbitmap k (ۮe ttkbootstrap)
                self.wm_iconbitmap(icon_path)
        except Exception as e:
            print(f"]wϥܥ: {e}")
        # ɨϥαjMz禡
        try:
            self.protocol("WM_DELETE_WINDOW", self.force_quit)
        except Exception:
            pass

        # bWإߤ@Ӥplabel@iconϰ쪺aBĲoI
        self.icon_tip_label = tk.Label(self, width=2, height=1, bg=self.cget("background"))
        self.icon_tip_label.place(x=0, y=0)
        window_title = self.title()
        Tooltip(self.icon_tip_label, f"{window_title}_By_Lucien")

        # ]wTG (Responsive Layout / Adaptive Window)
        # ]w̤pؤoä\uʽվ
        self.minsize(1100, 600)  # W[̤peץHeǷs\
        self.geometry("1150x620")  # W[leשM
        self.resizable(True, True)  # \վjp
        
        # ҥΤe۰ʾA
        self.update_idletasks()  # sҦݳBz GUI ƥ
        
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self.speed = 1.0
        self._record_start_time = None
        self._play_start_time = None
        self._total_play_time = 0

        # ]w}Ƨ
        self.script_dir = self.user_config.get("script_dir", SCRIPTS_DIR)
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        
        # ====== sW޲z ======
        # hù޲z
        self.multi_monitor = None
        # Ƶ{޲z - lƭIˬdƵ{
        self.schedule_manager = ScheduleManager(self)
        # įuƾ
        self.performance_optimizer = None



        # ====== Wާ@ ======
        frm_top = tb.Frame(self, padding=(8, 10, 8, 5))
        frm_top.pack(fill="x")

        self.btn_start = tb.Button(frm_top, text=f"}ls ({self.hotkey_map['start']})", command=self.start_record, bootstyle=PRIMARY, width=14, style="My.TButton")
        self.btn_start.grid(row=0, column=0, padx=(0, 4))
        self.btn_pause = tb.Button(frm_top, text=f"Ȱ/~ ({self.hotkey_map['pause']})", command=self.toggle_pause, bootstyle=INFO, width=14, style="My.TButton")
        self.btn_pause.grid(row=0, column=1, padx=4)
        self.btn_stop = tb.Button(frm_top, text=f" ({self.hotkey_map['stop']})", command=self.stop_all, bootstyle=WARNING, width=14, style="My.TButton")
        self.btn_stop.grid(row=0, column=2, padx=4)
        self.btn_play = tb.Button(frm_top, text=f" ({self.hotkey_map['play']})", command=self.play_record, bootstyle=SUCCESS, width=10, style="My.TButton")
        self.btn_play.grid(row=0, column=3, padx=4)

        # ====== MiniMode s ======
        self.mini_mode_btn = tb.Button(
            frm_top, text="MiniMode", style="My.TButton",
            command=self.toggle_mini_mode, width=10
        )
        self.mini_mode_btn.grid(row=0, column=7, padx=4)

        # ====== Uާ@ ======
        frm_bottom = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_bottom.pack(fill="x")
        self.lbl_speed = tb.Label(frm_bottom, text="t:", style="My.TLabel")
        self.lbl_speed.grid(row=0, column=0, padx=(0, 6))
        self.speed_tooltip = Tooltip(self.lbl_speed, "`t1=100,d1~1000")
        self.update_speed_tooltip()
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "100"))
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=6)
        saved_lang = self.user_config.get("language", "c餤")
        self.language_var = tk.StringVar(self, value=saved_lang)

        # ====== ưѼƳ]w ======
        self.repeat_label = tb.Label(frm_bottom, text="Ʀ:", style="My.TLabel")
        self.repeat_label.grid(row=0, column=2, padx=(8, 2))
        self.repeat_var = tk.StringVar(value=self.user_config.get("repeat", "1"))
        entry_repeat = tb.Entry(frm_bottom, textvariable=self.repeat_var, width=6, style="My.TEntry")
        entry_repeat.grid(row=0, column=3, padx=2)
        # K[ƦƪaB
        self.repeat_tooltip = Tooltip(self.repeat_label, "]wư榸\nJ 0 ܵL\nkIJإiֳt]0")

        self.repeat_time_var = tk.StringVar(value="00:00:00")
        entry_repeat_time = tb.Entry(frm_bottom, textvariable=self.repeat_time_var, width=10, style="My.TEntry", justify="center")
        entry_repeat_time.grid(row=0, column=5, padx=(10, 2))
        self.repeat_time_label = tb.Label(frm_bottom, text="Ʈɶ", style="My.TLabel")
        self.repeat_time_label.grid(row=0, column=6, padx=(0, 2))
        self.repeat_time_tooltip = Tooltip(self.repeat_time_label, "]w`B@ɶA榡HH:MM:SS\nҦp: 01:30:00 ܫ1.5p\ndũ00:00:00h̭Ʀư")

        self.repeat_interval_var = tk.StringVar(value="00:00:00")
        repeat_interval_entry = tb.Entry(frm_bottom, textvariable=self.repeat_interval_var, width=10, style="My.TEntry", justify="center")
        repeat_interval_entry.grid(row=0, column=7, padx=(10, 2))
        self.repeat_interval_label = tb.Label(frm_bottom, text="ƶj", style="My.TLabel")
        self.repeat_interval_label.grid(row=0, column=8, padx=(0, 2))
        self.repeat_interval_tooltip = Tooltip(self.repeat_interval_label, "CƤݮɶ\n榡HH:MM:SSAҦp: 00:00:30\nܨC槹30A}lU@")

        self.random_interval_var = tk.BooleanVar(value=False)
        self.random_interval_check = tb.Checkbutton(
            frm_bottom, text="H", variable=self.random_interval_var, style="My.TCheckbutton"
        )
        self.random_interval_check.grid(row=0, column=9, padx=(8, 2))
        self.random_interval_tooltip = Tooltip(self.random_interval_check, "ĿAƶjNb0]wȤH\niקKQH欰")

        # ====== ۰ʤ MiniMode Ŀ ======
        self.auto_mini_var = tk.BooleanVar(value=self.user_config.get("auto_mini_mode", False))
        lang_map = LANG_MAP.get(saved_lang, LANG_MAP["c餤"])
        self.main_auto_mini_check = tb.Checkbutton(
            frm_top, text=lang_map["۰ʤ"], variable=self.auto_mini_var, style="My.TCheckbutton"
        )
        self.main_auto_mini_check.grid(row=0, column=8, padx=4)
        Tooltip(self.main_auto_mini_check, lang_map["ĿɡA{s/N۰ഫ"])
        
        # ====== ètΦLĿ ======
        self.hide_to_tray_var = tk.BooleanVar(value=self.user_config.get("hide_to_tray", False))
        self.hide_to_tray_check = tb.Checkbutton(
            frm_top, text=lang_map.get("", ""), variable=self.hide_to_tray_var, style="My.TCheckbutton"
        )
        self.hide_to_tray_check.grid(row=0, column=9, padx=4)
        Tooltip(self.hide_to_tray_check, lang_map.get("Ŀ̤pƱNæܨtΦL", "Ŀ̤pƱNæܨtΦL"))
        
        # tΦLϥܹ
        self.tray_icon = None
        
        # jw̤pƨƥ
        self.bind("<Unmap>", self._on_minimize)

        
        # ====== xss ======
        self.save_script_btn_text = tk.StringVar(value=LANG_MAP.get(saved_lang, LANG_MAP["c餤"])["xs"])
        self.save_script_btn = tb.Button(
            frm_bottom, textvariable=self.save_script_btn_text, width=8, bootstyle=SUCCESS, style="My.TButton",
            command=self.save_script_settings
        )
        self.save_script_btn.grid(row=0, column=10, padx=(8, 0))

        # ====== ɶJ ======
        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        vcmd = (self.register(validate_time_input), "%P")
        entry_repeat_time.config(validate="key", validatecommand=vcmd)
        repeat_interval_entry.config(validate="key", validatecommand=vcmd)

        entry_repeat.bind("<Button-3>", lambda e: self.repeat_var.set("0"))
        entry_repeat_time.bind("<Button-3>", lambda e: self.repeat_time_var.set("00:00:00"))
        repeat_interval_entry.bind("<Button-3>", lambda e: self.repeat_interval_var.set("00:00:00"))

        def on_repeat_time_change(*args):
            t = self.repeat_time_var.get()
            seconds = self._parse_time_to_seconds(t)
            if seconds > 0:
                self.update_total_time_label(seconds)
            else:
                self.update_total_time_label(0)
        self.repeat_time_var.trace_add("write", on_repeat_time_change)

        # ====== } ======
        frm_script = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_script.pack(fill="x")
        self.script_menu_label = tb.Label(frm_script, text="}:", style="My.TLabel")
        self.script_menu_label.grid(row=0, column=0, sticky="w", padx=(0, 2))
        self.script_var = tk.StringVar(value=self.user_config.get("last_script", ""))
        self.script_combo = tb.Combobox(frm_script, textvariable=self.script_var, width=20, state="readonly", style="My.TCombobox")
        self.script_combo.grid(row=0, column=1, sticky="w", padx=4)
        self.rename_var = tk.StringVar()
        self.rename_entry = tb.Entry(frm_script, textvariable=self.rename_var, width=20, style="My.TEntry")
        self.rename_entry.grid(row=0, column=2, padx=4)
        self.rename_btn = tb.Button(frm_script, text=lang_map["sRW"], command=self.rename_script, bootstyle=WARNING, width=12, style="My.TButton")
        self.rename_btn.grid(row=0, column=3, padx=4)

        self.select_target_btn = tb.Button(frm_script, text=lang_map["ܵ"], command=self.select_target_window, bootstyle=INFO, width=14, style="My.TButton")
        self.select_target_btn.grid(row=0, column=4, padx=4)

        # ====== ƹҦĿء]w]ġ^======
        self.mouse_mode_var = tk.BooleanVar(value=self.user_config.get("mouse_mode", True))  # אּ True
        self.mouse_mode_check = tb.Checkbutton(
            frm_script, text=lang_map["ƹҦ"], variable=self.mouse_mode_var, style="My.TCheckbutton"
        )
        self.mouse_mode_check.grid(row=0, column=5, padx=4)
        Tooltip(self.mouse_mode_check, lang_map["ĿɥHuƹҦ"])
        
        # K[ƹҦܧť - Ŀĵi
        def on_mouse_mode_change(*args):
            if not self.mouse_mode_var.get():
                # Ŀĵi
                current_lang = self.language_var.get()
                lang_m = LANG_MAP.get(current_lang, LANG_MAP["c餤"])
                warning_msg = lang_m.get("ƹҦĵi", "?? `NI\n\nĿƹҦNϥΫxާ@C\nCi|~AԷVϥΡAGۭtI")
                messagebox.showwarning("ĵi", warning_msg)
        self.mouse_mode_var.trace_add("write", on_mouse_mode_change)

        self.script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)
        # jwIƥAbi}UԿe۰ʨsC
        self.script_combo.bind("<Button-1>", self._on_script_combo_click)


        # ====== xܰ ======
        frm_log = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_log.pack(fill="both", expand=True)
        log_title_frame = tb.Frame(frm_log)
        log_title_frame.pack(fill="x")

        self.mouse_pos_label = tb.Label(
            log_title_frame, text="(X=0,Y=0)",
            font=("Consolas", 10),  # rYp@ӳ
            foreground="#668B9B"
        )
        self.mouse_pos_label.pack(side="left", padx=4)  # ֶZ

        # ܥثewؼе]򱵦bƹyХkAnd`B@^
        self.target_label = tb.Label(
            log_title_frame, text="",
            font=font_tuple(9),
            foreground="#FF9500",
            anchor="w",
            width=25,  # ̤je
            cursor="hand2"  # ƹaܤ⫬
        )
        self.target_label.pack(side="left", padx=(0, 4))
        # jwIƥӨsۦP
        self.target_label.bind("<Button-1>", self._refresh_target_window)
        # jwkIƥӨ
        self.target_label.bind("<Button-3>", self._clear_target_window)

        # sɶ]ϥ Frame ]qh Label {ܦ^
        time_frame = tb.Frame(log_title_frame)
        time_frame.pack(side="right", padx=0)
        self.time_label_prefix = tb.Label(time_frame, text="s: ", font=font_tuple(12, monospace=True), foreground="#15D3BD")
        self.time_label_prefix.pack(side="left", padx=0)
        # 時間顯示：時:分:秒 (此區域動態更新)
        self.time_label_h = tb.Label(time_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_h.pack(side="left", padx=0)
        tb.Label(time_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.time_label_m = tb.Label(time_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_m.pack(side="left", padx=0)
        tb.Label(time_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.time_label_s = tb.Label(time_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_s.pack(side="left", padx=0)

        # 播放剩餘時間（包含循環計數的標籤顯示）
        countdown_frame = tb.Frame(log_title_frame)
        countdown_frame.pack(side="right", padx=0)
        self.countdown_label_prefix = tb.Label(countdown_frame, text="榸: ", font=font_tuple(12, monospace=True), foreground="#DB0E59")
        self.countdown_label_prefix.pack(side="left", padx=0)
        self.countdown_label_h = tb.Label(countdown_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_h.pack(side="left", padx=0)
        tb.Label(countdown_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.countdown_label_m = tb.Label(countdown_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_m.pack(side="left", padx=0)
        tb.Label(countdown_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.countdown_label_s = tb.Label(countdown_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_s.pack(side="left", padx=0)

        # 總共已播放時間
        total_frame = tb.Frame(log_title_frame)
        total_frame.pack(side="right", padx=0)
        self.total_time_label_prefix = tb.Label(total_frame, text="`B@: ", font=font_tuple(12, monospace=True), foreground="#FF95CA")
        self.total_time_label_prefix.pack(side="left", padx=0)
        self.total_time_label_h = tb.Label(total_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_h.pack(side="left", padx=0)
        tb.Label(total_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.total_time_label_m = tb.Label(total_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_m.pack(side="left", padx=0)
        tb.Label(total_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.total_time_label_s = tb.Label(total_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_s.pack(side="left", padx=0)

        # ====== 第 5 列：分頁功能區 ======
        frm_page = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_page.pack(fill="both", expand=True)
        frm_page.grid_rowconfigure(0, weight=1)
        frm_page.grid_columnconfigure(0, weight=0)  # Twe
        frm_page.grid_columnconfigure(1, weight=1)  # keϼuXi

        # 
        lang_map = LANG_MAP.get(saved_lang, LANG_MAP["c餤"])
        self.page_menu = tk.Listbox(frm_page, width=18, font=("Microsoft JhengHei", 11), height=5)
        self.page_menu.insert(0, lang_map["1.x"])
        self.page_menu.insert(1, lang_map["2.}s边"])
        self.page_menu.insert(2, lang_map["3.}]w"])
        self.page_menu.insert(3, lang_map["4.]w"])
        self.page_menu.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=4)
        self.page_menu.bind("<<ListboxSelect>>", self.on_page_selected)

        # keϡ]Hjpվ^
        self.page_content_frame = tb.Frame(frm_page)
        self.page_content_frame.grid(row=0, column=1, sticky="nsew")
        self.page_content_frame.grid_rowconfigure(0, weight=1)
        self.page_content_frame.grid_columnconfigure(0, weight=1)

        # xܰϡ]uʽվ^
        self.log_text = tb.Text(self.page_content_frame, state="disabled", font=font_tuple(9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = tb.Scrollbar(self.page_content_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # }]wϡ]uʽվ^
        self.script_setting_frame = tb.Frame(self.page_content_frame)
        self.script_setting_frame.grid_rowconfigure(0, weight=1)
        self.script_setting_frame.grid_columnconfigure(0, weight=1)  # CϦ۾A
        self.script_setting_frame.grid_columnconfigure(1, weight=0)  # kTw

        # }Cϡ]ϥ Text ɦWMֱ^
        list_frame = tb.Frame(self.script_setting_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(8,0), pady=8)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # ϥ Treeview ܤT]}W | ֱ | wɡ^
        from tkinter import ttk
        self.script_treeview = ttk.Treeview(
            list_frame,
            columns=("name", "hotkey", "schedule"),
            show="headings",
            height=15,
            selectmode="extended"  # 䴩h]Ctrl+I  Shift+I^
        )
        self.script_treeview.heading("name", text="}W")
        self.script_treeview.heading("hotkey", text="ֱ")
        self.script_treeview.heading("schedule", text="w")
        self.script_treeview.column("name", width=250, anchor="w")
        self.script_treeview.column("hotkey", width=80, anchor="center")
        self.script_treeview.column("schedule", width=120, anchor="center")
        self.script_treeview.grid(row=0, column=0, sticky="nsew")
        
        # [Jb
        list_scroll = tb.Scrollbar(list_frame, command=self.script_treeview.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.script_treeview.config(yscrollcommand=list_scroll.set)
        
        # jwܨƥ
        self.script_treeview.bind("<<TreeviewSelect>>", self.on_script_treeview_select)
        
        # xse襤}
        self.selected_script_line = None

        # kϡ]ƦCA񺡳ѾlŶ^
        self.script_right_frame = tb.Frame(self.script_setting_frame, padding=6)
        self.script_right_frame.grid(row=0, column=1, sticky="nsew", padx=(6,8), pady=8)

        # ֱ䮷]iNβզX^
        self.hotkey_capture_var = tk.StringVar(value="")
        self.hotkey_capture_label = tb.Label(self.script_right_frame, text="ֱG", style="My.TLabel")
        self.hotkey_capture_label.pack(anchor="w", pady=(2,2))
        hotkey_entry = tb.Entry(self.script_right_frame, textvariable=self.hotkey_capture_var, font=font_tuple(10, monospace=True), width=16)
        hotkey_entry.pack(anchor="w", pady=(0,8))
        #  KeyPress ƥHTզX
        hotkey_entry.bind("<KeyPress>", self.on_hotkey_entry_key)
        hotkey_entry.bind("<FocusIn>", lambda e: self.hotkey_capture_var.set("J"))
        hotkey_entry.bind("<FocusOut>", lambda e: None)

        # a) ]wֱsGN쪺ֱgJw}õU
        self.set_hotkey_btn = tb.Button(self.script_right_frame, text="]wֱ", width=16, bootstyle=SUCCESS, command=self.set_script_hotkey)
        self.set_hotkey_btn.pack(anchor="w", pady=4)

        # b) }Ҹ}Ƨ]U\^
        self.open_dir_btn = tb.Button(self.script_right_frame, text="}ҸƧ", width=16, bootstyle=SECONDARY, command=self.open_scripts_dir)
        self.open_dir_btn.pack(anchor="w", pady=4)

        # c) RsGRɮרèUֱ]Y^
        self.del_script_btn = tb.Button(self.script_right_frame, text="R}", width=16, bootstyle=DANGER, command=self.delete_selected_script)
        self.del_script_btn.pack(anchor="w", pady=4)
        
        # d) Ƶ{sG]w}wɰ
        self.schedule_btn = tb.Button(self.script_right_frame, text="Ƶ{", width=16, bootstyle=INFO, command=self.open_schedule_settings)
        self.schedule_btn.pack(anchor="w", pady=4)
        
        # e) Xָ}sGNhӸ}X֬@
        self.merge_btn = tb.Button(self.script_right_frame, text=lang_map["Xָ}"], width=16, bootstyle=SUCCESS, command=self.merge_scripts)
        self.merge_btn.pack(anchor="w", pady=4)

        # lƲM
        self.refresh_script_listbox()

        # ====== ]w ======
        self.global_setting_frame = tb.Frame(self.page_content_frame)
        
        self.btn_hotkey = tb.Button(self.global_setting_frame, text="ֱ", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=15, style="My.TButton")
        self.btn_hotkey.pack(anchor="w", pady=4, padx=8)
        
        self.about_btn = tb.Button(self.global_setting_frame, text="", width=15, style="My.TButton", command=self.show_about_dialog, bootstyle=SECONDARY)
        self.about_btn.pack(anchor="w", pady=4, padx=8)
        
        # Ts
        self.version_info_btn = tb.Button(
            self.global_setting_frame,
            text="T",
            width=15,
            style="My.TButton",
            command=self.show_version_info,
            bootstyle=INFO
        )
        self.version_info_btn.pack(anchor="w", pady=4, padx=8)
        
        # xss
        self.website_btn = tb.Button(
            self.global_setting_frame, 
            text="Mimicx", 
            width=15, 
            style="My.TButton", 
            command=self.open_website, 
            bootstyle=SUCCESS
        )
        self.website_btn.pack(anchor="w", pady=4, padx=8)
        
        self.actual_language = saved_lang
        self.language_display_var = tk.StringVar(self, value="Language")
        
        lang_combo_global = tb.Combobox(
            self.global_setting_frame,
            textvariable=self.language_display_var,
            values=["c餤", "饻y", "English"],
            state="readonly",
            width=12,
            style="My.TCombobox"
        )
        lang_combo_global.pack(anchor="w", pady=4, padx=8)
        lang_combo_global.bind("<<ComboboxSelected>>", self.change_language)
        self.language_combo = lang_combo_global

        # ====== lƳ]w ======
        self.page_menu.selection_set(0)
        self.show_page(0)

        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()
        # self._init_language(saved_lang)  # ksbAw
        self.after(1500, self._delayed_init)

    def _show_admin_warning(self):
        """ܺ޲zvĵi"""
        try:
            import tkinter.messagebox as messagebox
            result = messagebox.askquestion(
                "޲zvĵi",
                "?? ˴{H޲zI\n\n"
                "s\ݭn޲zv~ॿ`u@C\n"
                "LMƹťi|ѡC\n\n"
                "O_nH޲zsҰʵ{H\n"
                "]ܡu_vN~As\iLkϥΡ^",
                icon='warning'
            )
            
            if result == 'yes':
                # sH޲zҰ
                self._restart_as_admin()
        except Exception as e:
            self.log(f"ܺ޲zĵiɵoͿ~: {e}")
    
    def _restart_as_admin(self):
        """H޲zsҰʵ{"""
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # ]᪺ exe
                script = sys.executable
            else:
                # }o
                script = os.path.abspath(sys.argv[0])
            
            params = ' '.join([script] + sys.argv[1:])
            
            # ϥ ShellExecute H޲z
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",  # H޲z
                sys.executable if getattr(sys, 'frozen', False) else sys.executable,
                f'"{script}"' if not getattr(sys, 'frozen', False) else None,
                None, 
                1
            )
            
            # e{
            self.quit()
            sys.exit(0)
        except Exception as e:
            self.log(f"sҰʬ޲zɵoͿ~: {e}")

    def _delayed_init(self):
        # l core_recorder]ݭnb self.log iΤ^
        self.core_recorder = CoreRecorder(logger=self.log)
        
        # jƵJIMֱUɧ
        self.after(50, self._force_focus)   # DoJI
        self.after(200, self._force_focus)  # AT{JI
        self.after(300, self._register_hotkeys)  # Uֱ
        self.after(400, self._register_script_hotkeys)
        # ✅ 新增：定期檢查快捷鍵健康狀態（每30秒）
        self.after(30000, self._check_hotkey_health)
        self.after(500, self.refresh_script_list)
        self.after(600, self.load_last_script)
        self.after(700, self.update_mouse_pos)
        self.after(800, self._init_background_mode)
        self.after(900, self._load_all_schedules)  # JҦƵ{

    def _force_focus(self):
        """DoJIATOL_l`u@"""
        try:
            # jƵJI]ϥtopmostקK\LL^
            self.lift()  # ɵ
            self.focus_force()  # joJI
            self.update()  # js
            
            # ? ?~Ĳo@LƥӿE_l
            self.event_generate('<KeyPress>', keysym='Shift_L')
            self.event_generate('<KeyRelease>', keysym='Shift_L')
        except Exception as e:
            pass  # RqBz~

    def _init_background_mode(self):
        """lƫxҦ]w]TwϥδҦ^"""
        mode = "smart"
        if hasattr(self.core_recorder, 'set_background_mode'):
            self.core_recorder.set_background_mode(mode)
        # Rq]wAܤx

    # ====== tΦLk ======
    def _on_minimize(self, event):
        """̤pƮĲo"""
        if not self.hide_to_tray_var.get():
            return  # SĿuávA
        
        # ˬdO_uO̤pơ]OéΨLƥ^
        if self.state() == "iconic":
            self._hide_to_tray()
    
    def _hide_to_tray(self):
        """õtΦL"""
        if not PYSTRAY_AVAILABLE:
            return
        
        # åD
        self.withdraw()
        
        # إߦLϥܡ]pG٨Sإߡ^
        if self.tray_icon is None:
            self._create_tray_icon()
    
    def _create_tray_icon(self):
        """إߨtΦLϥ"""
        if not PYSTRAY_AVAILABLE:
            return
        
        # Jϥ
        icon_path = get_icon_path()
        try:
            if os.path.exists(icon_path):
                image = PILImage.open(icon_path)
            else:
                # إ߹w]ϥܡ]Ŧ^
                image = PILImage.new('RGB', (64, 64), color=(66, 133, 244))
        except Exception:
            image = PILImage.new('RGB', (64, 64), color=(66, 133, 244))
        
        # oeyr
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
        show_text = lang_map.get("ܥD", "ܥD")
        exit_text = lang_map.get("hX", "hX")
        
        # إ߿
        menu = pystray.Menu(
            pystray.MenuItem(show_text, self._show_from_tray),
            pystray.MenuItem(exit_text, self._quit_from_tray)
        )
        
        # إߦLϥ
        self.tray_icon = pystray.Icon(
            "ChroLens_Mimic",
            image,
            f"ChroLens_Mimic {VERSION}",
            menu
        )
        
        # ]wIƥ]Iܵ^
        self.tray_icon.default = pystray.MenuItem(show_text, self._show_from_tray)
        
        # bI榫Lϥ
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
    
    def _show_from_tray(self, icon=None, item=None):
        """qtΦLܥD"""
        # Lϥ
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        
        # ϥ after TObD
        self.after(0, self._restore_window)
    
    def _restore_window(self):
        """٭]bD^"""
        self.deiconify()  # ܵ
        self.lift()       # ɨ̤Wh
        self.focus_force()  # oJI
    
    def _quit_from_tray(self, icon=None, item=None):
        """qtΦLhX{"""
        # Lϥ
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        
        # bDhX
        self.after(0, self.force_quit)


    def update_speed_tooltip(self):
        lang = self.language_var.get()
        tips = {
            "c餤": "`t1=100,d1~1000",
            "饻y": "зǳt1=100Bd?11000",
            "English": "Normal speed 1x=100, range 1~1000"
        }
        tip_text = tips.get(lang, tips["c餤"])
        if hasattr(self, "speed_tooltip") and self.speed_tooltip:
            self.speed_tooltip.text = tip_text

    def _parse_time_to_seconds(self, t):
        """N 00:00:00  00:00 榡rର"""
        if not t or not isinstance(t, str):
            return 0
        parts = t.strip().split(":")
        try:
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
            elif len(parts) == 1:
                return int(parts[0])
        except Exception:
            return 0
        return 0
    
    def _actions_to_events(self, actions):
        """Nıƽs边ʧ@CഫƥC
        
<<<<<<< Updated upstream
        增強穩定性:
        - 完整的資料驗證
        - 詳細的錯誤日誌
        - 自動修復異常資料
        - 跳過無效動作而非中斷
=======
        Wjíw:
        - 㪺ƾ
        - ԲӪ~x
        - ۰ʭ״_`ƾ
        - LLİʧ@ӫD_
>>>>>>> Stashed changes
        """
        events = []
        current_time = 0.0
        skipped_count = 0
        
<<<<<<< Updated upstream
        # 資料驗證
=======
        # ƾ
>>>>>>> Stashed changes
        if not isinstance(actions, list):
            self.log(f"[ഫ~] actions OC: {type(actions)}")
            return []
        
        if len(actions) == 0:
            self.log("[ഫĵi] ʧ@C")
            return []
        
        self.log(f"[ഫ}l] ǳഫ {len(actions)} Ӱʧ@ƥ")
        
        try:
            for idx, action in enumerate(actions):
                # Ұʧ@榡
                if not isinstance(action, dict):
                    self.log(f"[L]  {idx+1} Ӱʧ@Or")
                    skipped_count += 1
                    continue
                
                command = action.get("command", "")
                if not command:
                    self.log(f"[L]  {idx+1} Ӱʧ@ʤ֫O")
                    skipped_count += 1
                    continue
                
                params_str = action.get("params", "")
                
                # wѪR
                try:
                    delay = float(action.get("delay", 0)) / 1000.0  # @
                    if delay < 0:
                        delay = 0
                except (ValueError, TypeError) as e:
                    self.log(f"[ĵi]  {idx+1} Ӱʧ@ȵL: {e}")
                    delay = 0
                
                # [W
                current_time += delay
                
                # ھګOЫبƥ
                if command == "move_to" or command == "move_to_path":
                    # ѪRy
                    try:
                        if command == "move_to_path":
                            # move_to_path: params O JSON r榡yC
                            trajectory = None
                            
<<<<<<< Updated upstream
                            # 嘗試解析軌跡資料
=======
                            # ոѪRyƾ
>>>>>>> Stashed changes
                            try:
                                trajectory = json.loads(params_str)
                            except json.JSONDecodeError:
                                # pG json.loads , ast.literal_eval
                                try:
                                    import ast
                                    trajectory = ast.literal_eval(params_str)
                                except Exception as ast_err:
<<<<<<< Updated upstream
                                    self.log(f"[錯誤] 第 {idx+1} 個動作: 無法解析軌跡資料 - {ast_err}")
                                    skipped_count += 1
                                    continue
                            
                            # 驗證軌跡資料
                            if not isinstance(trajectory, list) or len(trajectory) == 0:
                                self.log(f"[跳過] 第 {idx+1} 個動作: 軌跡資料格式錯誤或為空")
=======
                                    self.log(f"[~]  {idx+1} Ӱʧ@: LkѪRyƾ - {ast_err}")
                                    skipped_count += 1
                                    continue
                            
                            # ҭyƾ
                            if not isinstance(trajectory, list) or len(trajectory) == 0:
                                self.log(f"[L]  {idx+1} Ӱʧ@: yƾڮ榡~ά")
>>>>>>> Stashed changes
                                skipped_count += 1
                                continue
                            
                            # ҭyI榡
                            valid_points = []
                            for pt_idx, point in enumerate(trajectory):
                                if isinstance(point, dict) and "x" in point and "y" in point:
                                    valid_points.append(point)
                                else:
                                    self.log(f"[ĵi] yI {pt_idx+1} 榡~,wL")
                            
                            if len(valid_points) == 0:
                                self.log(f"[L]  {idx+1} Ӱʧ@: LĭyI")
                                skipped_count += 1
                                continue
                            
                            # ̫@I@I
                            last_point = valid_points[-1]
                            x = int(last_point.get("x", 0))
                            y = int(last_point.get("y", 0))
                            
                            events.append({
                                "type": "mouse",
                                "event": "move",
                                "x": x,
                                "y": y,
                                "time": current_time,
                                "trajectory": valid_points
                            })
                            self.log(f"[ഫ] y񲾰: {len(valid_points)} I")
                        else:
                            # move_to: params O "x, y"  "x, y, trajectory"
                            if not params_str:
                                self.log(f"[L]  {idx+1} Ӱʧ@: move_to ʤְѼ")
                                skipped_count += 1
                                continue
                            
                            parts = [p.strip() for p in params_str.split(",", 2)]  # ̦hά3
                            
                            # ҨøѪRy
                            try:
                                x = int(parts[0]) if len(parts) > 0 and parts[0] else 0
                                y = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                            except (ValueError, IndexError) as e:
                                self.log(f"[L]  {idx+1} Ӱʧ@: yиѪR - {e}")
                                skipped_count += 1
                                continue
                            
<<<<<<< Updated upstream
                            # 檢查是否有軌跡資料
                            if len(parts) > 2 and parts[2]:
                                # 有軌跡資料,嘗試解析
=======
                            # ˬdO_yƾ
                            if len(parts) > 2 and parts[2]:
                                # yƾ,ոѪR
>>>>>>> Stashed changes
                                try:
                                    trajectory = json.loads(parts[2])
                                    events.append({
                                        "type": "mouse",
                                        "event": "move",
                                        "x": x,
                                        "y": y,
                                        "time": current_time,
                                        "trajectory": trajectory
                                    })
                                except:
                                    try:
                                        import ast
                                        trajectory = ast.literal_eval(parts[2])
                                        events.append({
                                            "type": "mouse",
                                            "event": "move",
                                            "x": x,
                                            "y": y,
                                            "time": current_time,
                                            "trajectory": trajectory
                                        })
                                    except Exception as traj_err:
                                        self.log(f"[ĵi]  {idx+1} Ӱʧ@: yѪR,ϥδq - {traj_err}")
                                        events.append({
                                            "type": "mouse",
                                            "event": "move",
                                            "x": x,
                                            "y": y,
                                            "time": current_time
                                        })
                            else:
                                # q
                                events.append({
                                    "type": "mouse",
                                    "event": "move",
                                    "x": x,
                                    "y": y,
                                    "time": current_time
                                })
                    except Exception as e:
                        self.log(f"[~]  {idx+1} Ӱʧ@({command}): Bz - {e}")
                        import traceback
                        self.log(f"Բ: {traceback.format_exc()}")
                        skipped_count += 1
                        continue
                
                elif command == "click":
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": "left",
                        "time": current_time
                    })
                    current_time += 0.05
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": "left",
                        "time": current_time
                    })
                
                elif command == "double_click":
                    for _ in range(2):
                        events.append({
                            "type": "mouse",
                            "event": "down",
                            "button": "left",
                            "time": current_time
                        })
                        current_time += 0.05
                        events.append({
                            "type": "mouse",
                            "event": "up",
                            "button": "left",
                            "time": current_time
                        })
                        current_time += 0.05
                
                elif command == "right_click":
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": "right",
                        "time": current_time
                    })
                    current_time += 0.05
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": "right",
                        "time": current_time
                    })
                
                elif command == "press_down":
                    button = params_str.strip() if params_str else "left"
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": button,
                        "time": current_time
                    })
                
                elif command == "release":
                    button = params_str.strip() if params_str else "left"
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": button,
                        "time": current_time
                    })
                
                elif command == "scroll":
                    # uu
                    try:
                        delta = int(params_str) if params_str and params_str.strip() else 1
                        events.append({
                            "type": "mouse",
                            "event": "wheel",
                            "delta": delta,
                            "time": current_time
                        })
                    except (ValueError, TypeError) as e:
                        self.log(f"[ĵi]  {idx+1} Ӱʧ@: scroll ѼƵL - {e}")
                        skipped_count += 1
                
                elif command == "type_text":
                    # Jr
                    text = params_str.strip() if params_str else ""
                    if not text:
                        self.log(f"[L]  {idx+1} Ӱʧ@: type_text ʤ֤re")
                        skipped_count += 1
                        continue
                    
                    for char in text:
                        events.append({
                            "type": "keyboard",
                            "event": "down",
                            "key": char,
                            "time": current_time
                        })
                        current_time += 0.05
                        events.append({
                            "type": "keyboard",
                            "event": "up",
                            "key": char,
                            "time": current_time
                        })
                        current_time += 0.05
                
                elif command == "press_key":
                    # U
                    key = params_str.strip() if params_str else ""
                    if not key:
                        self.log(f"[L]  {idx+1} Ӱʧ@: press_key ʤ֫W")
                        skipped_count += 1
                        continue
                    
                    events.append({
                        "type": "keyboard",
                        "event": "down",
                        "key": key,
                        "time": current_time
                    })
                    current_time += 0.05
                    events.append({
                        "type": "keyboard",
                        "event": "up",
                        "key": key,
                        "time": current_time
                    })
                
                elif command == "hotkey":
                    # ֱզX
                    if not params_str or not params_str.strip():
                        self.log(f"[L]  {idx+1} Ӱʧ@: hotkey ʤ֫զX")
                        skipped_count += 1
                        continue
                    
                    keys = [k.strip() for k in params_str.split("+") if k.strip()]
                    if len(keys) == 0:
                        self.log(f"[L]  {idx+1} Ӱʧ@: hotkey ѪRLī")
                        skipped_count += 1
                        continue
                    
                    # UҦ
                    for key in keys:
                        events.append({
                            "type": "keyboard",
                            "event": "down",
                            "key": key,
                            "time": current_time
                        })
                        current_time += 0.02
                    # Ҧ]ϦV^
                    for key in reversed(keys):
                        events.append({
                            "type": "keyboard",
                            "event": "up",
                            "key": key,
                            "time": current_time
                        })
                        current_time += 0.02
                
                elif command == "delay":
                    # 𵥫
                    try:
                        extra_delay = float(params_str) / 1000.0 if params_str and params_str.strip() else 0
                        if extra_delay > 0:
                            current_time += extra_delay
                    except (ValueError, TypeError) as e:
                        self.log(f"[ĵi]  {idx+1} Ӱʧ@: delay ѼƵL - {e}")
                        skipped_count += 1
                
                else:
                    # O
                    self.log(f"[L]  {idx+1} Ӱʧ@: O '{command}'")
                    skipped_count += 1
        
        except Exception as e:
            self.log(f"[ഫ~] `: {e}")
            import traceback
            self.log(f"Բ: {traceback.format_exc()}")
        
        # ഫέp
        success_count = len(events)
        total_count = len(actions)
        
        self.log(f"[ഫ] \: {success_count}/{total_count} Ӱʧ@")
        if skipped_count > 0:
            self.log(f"[ഫĵi] L: {skipped_count} ӵLİʧ@")
        
        if success_count == 0 and total_count > 0:
            self.log(f"[ഫ] Ҧʧ@ഫ,ˬdʧ@榡")
        
        return events

    def show_about_dialog(self):
        try:
            about.show_about(self)
        except Exception as e:
            print(f" about : {e}")
    
    def show_version_info(self):
        """ܪTܮ"""
        try:
            from version_manager import VersionManager
            from version_info_dialog import VersionInfoDialog
            
            # Ыت޲z
            vm = VersionManager(GITHUB_REPO, VERSION, logger=self.log)
            
            # ܪTܮ
            def on_update_complete():
                """sD{"""
                self.log("ǳ{His...")
                self.after(1000, self.force_quit)
            
            VersionInfoDialog(self, vm, VERSION, on_update_complete)
            
        except Exception as e:
            self.log(f"ܪT: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("~", f"LkܪTG\n{e}")
    
    def open_website(self):
        """} ChroLens Mimic x"""
        import webbrowser
        try:
            webbrowser.open("https://lucienwooo.github.io/ChroLens_Mimic/")
            self.log("w}ҩx")
        except Exception as e:
            self.log(f"}Һ: {e}")
            messagebox.showerror("~", f"Lk}ҺG\n{e}")
    

    def change_language(self, event=None):
        lang = self.language_display_var.get()
        if lang == "Language" or not lang:
            return
        
        # sڻyM
        self.actual_language = lang
        self.language_var.set(lang)
        
        # s᭫mܬ "Language"
        self.after(100, lambda: self.language_display_var.set("Language"))
        
        lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
        self.btn_start.config(text=lang_map["}ls"] + f" ({self.hotkey_map['start']})")
        self.btn_pause.config(text=lang_map["Ȱ/~"] + f" ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=lang_map[""] + f" ({self.hotkey_map['stop']})")
        self.btn_play.config(text=lang_map[""] + f" ({self.hotkey_map['play']})")
        self.mini_mode_btn.config(text=lang_map["MiniMode"])
        self.about_btn.config(text=lang_map[""])
        self.lbl_speed.config(text=lang_map["t:"])
        self.btn_hotkey.config(text=lang_map["ֱ"])
        self.total_time_label_prefix.config(text=lang_map["`B@"])
        self.countdown_label_prefix.config(text=lang_map["榸"])
        self.time_label_prefix.config(text=lang_map["s"])
        self.repeat_label.config(text=lang_map["Ʀ:"])
        self.repeat_time_label.config(text=lang_map["Ʈɶ"])
        self.repeat_interval_label.config(text=lang_map["ƶj"])
        self.script_menu_label.config(text=lang_map["Script:"])
        self.save_script_btn_text.set(lang_map["xs"])
        # }]wϫs
        if hasattr(self, 'rename_btn'):
            self.rename_btn.config(text=lang_map["sRW"])
        if hasattr(self, 'merge_btn'):
            self.merge_btn.config(text=lang_map["Xָ}"])
        if hasattr(self, 'select_target_btn'):
            self.select_target_btn.config(text=lang_map["ܵ"])
        if hasattr(self, 'mouse_mode_check'):
            self.mouse_mode_check.config(text=lang_map["ƹҦ"])
        if hasattr(self, 'hotkey_capture_label'):
            self.hotkey_capture_label.config(text=lang_map["ֱG"])
        if hasattr(self, 'set_hotkey_btn'):
            self.set_hotkey_btn.config(text=lang_map["]wֱ"])
        if hasattr(self, 'open_dir_btn'):
            self.open_dir_btn.config(text=lang_map["}ҸƧ"])
        if hasattr(self, 'del_script_btn'):
            self.del_script_btn.config(text=lang_map["R}"])
        if hasattr(self, 'edit_script_btn'):
            self.edit_script_btn.config(text=lang_map["}s边"])
        # Treeview D
        if hasattr(self, 'script_treeview'):
            self.script_treeview.heading("name", text=lang_map["}W"])
            self.script_treeview.heading("hotkey", text=lang_map["ֱ"])
            self.script_treeview.heading("schedule", text=lang_map.get("w", "w"))
        # Ŀ
        if hasattr(self, 'random_interval_check'):
            self.random_interval_check.config(text=lang_map["H"])
        if hasattr(self, 'main_auto_mini_check'):
            self.main_auto_mini_check.config(text=lang_map["۰ʤ"])
        # s
        if hasattr(self, 'page_menu'):
            self.page_menu.delete(0, tk.END)
            self.page_menu.insert(0, lang_map["1.x"])
            self.page_menu.insert(1, lang_map["2.}]w"])
            self.page_menu.insert(2, lang_map["3.]w"])
        self.user_config["language"] = lang
        self.save_config()
        self.update_idletasks()

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_time_label(self, seconds):
        """ssɶܡ]ʺACGDsƦr #FF95CA^"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        
        # ]wCGDsƦr #FF95CAAsܦǦ #888888
        h_color = "#FF95CA" if h > 0 else "#888888"
        m_color = "#FF95CA" if m > 0 or h > 0 else "#888888"  # pGp>0A]nG
        s_color = "#FF95CA" if s > 0 or m > 0 or h > 0 else "#888888"  # pG>0A]nG
        
        self.time_label_h.config(text=f"{h:02d}", foreground=h_color)
        self.time_label_m.config(text=f"{m:02d}", foreground=m_color)
        self.time_label_s.config(text=f"{s:02d}", foreground=s_color)

    def update_total_time_label(self, seconds):
        """s`B@ɶܡ]ʺACGDsƦr #FF95CA^"""
        # BzLƪp
        if seconds == float('inf') or (isinstance(seconds, float) and (seconds != seconds or seconds > 1e10)):
            # NaN εLjA 
            self.total_time_label_h.config(text="", foreground="#FF95CA")
            self.total_time_label_m.config(text="", foreground="#888888")
            self.total_time_label_s.config(text="", foreground="#888888")
            return
        
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        
        # ]wCGDsƦr #FF95CAAsܦǦ #888888
        h_color = "#FF95CA" if h > 0 else "#888888"
        m_color = "#FF95CA" if m > 0 or h > 0 else "#888888"
        s_color = "#FF95CA" if s > 0 or m > 0 or h > 0 else "#888888"
        
        self.total_time_label_h.config(text=f"{h:02d}", foreground=h_color)
        self.total_time_label_m.config(text=f"{m:02d}", foreground=m_color)
        self.total_time_label_s.config(text=f"{s:02d}", foreground=s_color)

    def update_countdown_label(self, seconds):
        """s榸Ѿlɶܡ]ʺACGDsƦr #FF95CA^"""
        # BzLƪp
        if seconds == float('inf') or (isinstance(seconds, float) and (seconds != seconds or seconds > 1e10)):
            # NaN εLjA 
            self.countdown_label_h.config(text="", foreground="#FF95CA")
            self.countdown_label_m.config(text="", foreground="#888888")
            self.countdown_label_s.config(text="", foreground="#888888")
            return
        
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        
        # ]wCGDsƦr #FF95CAAsܦǦ #888888
        h_color = "#FF95CA" if h > 0 else "#888888"
        m_color = "#FF95CA" if m > 0 or h > 0 else "#888888"
        s_color = "#FF95CA" if s > 0 or m > 0 or h > 0 else "#888888"
        
        self.countdown_label_h.config(text=f"{h:02d}", foreground=h_color)
        self.countdown_label_m.config(text=f"{m:02d}", foreground=m_color)
        self.countdown_label_s.config(text=f"{s:02d}", foreground=s_color)

    def _update_play_time(self):
        """sɶܡ]jƪ - ϥιڮɶTOǽT˼ơ^"""
        if self.playing:
            # ˬd core_recorder O_b
            if not getattr(self.core_recorder, 'playing', False):
                # wAPBA
                self.playing = False
                self.log(f"[{format_time(time.time())}] 槹")
                
                # Ҧid׹
                self._release_all_modifiers()
                
                self.update_time_label(0)
                self.update_countdown_label(0)
                self.update_total_time_label(0)
                # MiniMode˼ks
                if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                    if hasattr(self, "mini_countdown_label"):
                        try:
                            lang = self.language_var.get()
                            lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
                            self.mini_countdown_label.config(text=f"{lang_map['Ѿl']}: 00:00:00")
                        except Exception:
                            pass
                return
            
            # ? ״_GϥιڸgLɶӫDƥ
            # p}`ס]޿ɶ^
            if self.events and len(self.events) > 0:
                script_duration = self.events[-1]['time'] - self.events[0]['time']
            else:
                script_duration = 0
            
            # e`p
            current_repeat = getattr(self.core_recorder, '_current_repeat_count', 0)
            
            # ˴`ܤơ]}ls`^
            if not hasattr(self, '_last_repeat_count'):
                self._last_repeat_count = 0
            
            if current_repeat != self._last_repeat_count:
                # `ܤơAm`_lɶ
                self._current_cycle_start_time = time.time()
                self._last_repeat_count = current_repeat
            
            # 榸檺_lɶ
            if not hasattr(self, '_current_cycle_start_time') or self._current_cycle_start_time is None:
                # lƷe`_lɶ
                self._current_cycle_start_time = time.time()
            
            # pe`ڸgLɶ
            elapsed_real = time.time() - self._current_cycle_start_time
            
            # γt׫Yƨӭp޿ɶ
            speed = getattr(self, 'speed', 1.0)
            elapsed = elapsed_real * speed
            
            #  elapsed WL}`ס]榸^
            if script_duration > 0 and elapsed > script_duration:
                elapsed = script_duration
                    
            self.update_time_label(elapsed)
            
            # p榸Ѿlɶ]޿ɶ^
            remain = max(0, script_duration - elapsed)
            self.update_countdown_label(remain)
            
            # p`B@Ѿlɶ
            if hasattr(self, "_play_start_time") and self._play_start_time:
                elapsed_real = time.time() - self._play_start_time
                
                # BzLƪp
                if self._total_play_time == float('inf'):
                    total_remain = float('inf')
                elif self._repeat_time_limit:
                    # ϥήɶҦ
                    total_remain = max(0, self._repeat_time_limit - elapsed_real)
                else:
                    # ϥ`ɶҦ
                    total_remain = max(0, self._total_play_time - elapsed_real)
                    
                self.update_total_time_label(total_remain)
                
                # s MiniMode ˼
                if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                    if hasattr(self, "mini_countdown_label"):
                        try:
                            lang = self.language_var.get()
                            lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
                            
                            # BzL
                            if total_remain == float('inf'):
                                time_str = ""
                            else:
                                h = int(total_remain // 3600)
                                m = int((total_remain % 3600) // 60)
                                s = int(total_remain % 60)
                                time_str = f"{h:02d}:{m:02d}:{s:02d}"
                            
                            self.mini_countdown_label.config(text=f"{lang_map['Ѿl']}: {time_str}")
                        except Exception:
                            pass
            
            # s]100ms sv^
            self.after(100, self._update_play_time)
        else:
            # 氱ɭmҦɶ
            self.update_time_label(0)
            self.update_countdown_label(0)
            self.update_total_time_label(0)
            # MiniMode˼ks
            if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                if hasattr(self, "mini_countdown_label"):
                    try:
                        lang = self.language_var.get()
                        lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
                        self.mini_countdown_label.config(text=f"{lang_map['Ѿl']}: 00:00:00")
                    except Exception:
                        pass

    def start_record(self):
        """}ls (v2.6.5 - ²ƪAѦ2.5íw)"""
        if self.recording:
            return
        
        # ۰ʤ MiniMode]pGĿ^
        if self.auto_mini_var.get() and not self.mini_mode_on:
            self.toggle_mini_mode()
        
        # C}lsɡAmuixs}vѼƬw]
        try:
            self.reset_to_defaults()
        except Exception:
            pass
        
        # TO core_recorder Dؼе]w
        if hasattr(self, 'core_recorder') and hasattr(self.core_recorder, 'set_target_window'):
            self.core_recorder.set_target_window(self.target_hwnd)
        
        # OؼеT]]t DPIBѪR׵^
        self.recorded_window_info = None
        if self.target_hwnd:
            try:
                window_info = get_window_info(self.target_hwnd)
                if window_info:
                    self.recorded_window_info = window_info
                    self.log(f"OT:")
                    self.log(f"  jp: {window_info['size'][0]} x {window_info['size'][1]}")
                    self.log(f"  m: ({window_info['position'][0]}, {window_info['position'][1]})")
                    self.log(f"  DPI Y: {window_info['dpi_scale']:.2f}x ({int(window_info['dpi_scale'] * 100)}%)")
                    self.log(f"  ùѪR: {window_info['screen_resolution'][0]} x {window_info['screen_resolution'][1]}")
            except Exception as e:
                self.log(f"LkOT: {e}")
        
        # ? M events ó]wA
        self.events = []
        self.recording = True
        self.paused = False
        self.log(f"[{format_time(time.time())}] }ls...")
        
        # ? ץGե core_recorder.start_record() HTOl
        if hasattr(self, 'core_recorder'):
            self._record_start_time = self.core_recorder.start_record()
            if self._record_start_time is None:
                self._record_start_time = time.time()
            self._record_thread_handle = self.core_recorder._record_thread
        else:
            # Vۮe: ϥª threading 覡
            self._record_start_time = time.time()
            self._record_thread_handle = threading.Thread(target=self._record_thread, daemon=True)
            self._record_thread_handle.start()
        
        self.after(100, self._update_record_time)

    def _update_record_time(self):
        if self.recording:
            now = time.time()
            elapsed = now - self._record_start_time
            self.update_time_label(elapsed)
            self.after(100, self._update_record_time)
        else:
            self.update_time_label(0)

    def reset_to_defaults(self):
        """NiQxsѼƭmw]]sɨϥΡ^"""
        # UI w]
        try:
            self.speed_var.set("100")
        except Exception:
            pass
        try:
            self.repeat_var.set("1")
        except Exception:
            pass
        try:
            self.repeat_time_var.set("00:00:00")
        except Exception:
            pass
        try:
            self.repeat_interval_var.set("00:00:00")
        except Exception:
            pass
        try:
            self.random_interval_var.set(False)
        except Exception:
            pass
        # PB speed
        try:
            speed_val = int(self.speed_var.get())
            speed_val = min(1000, max(1, speed_val))
            self.speed = speed_val / 100.0
            self.speed_var.set(str(speed_val))
        except Exception:
            self.speed = 1.0
            self.speed_var.set("100")
        # sܡ]ȧs tooltipA lbl_speed^
        try:
            self.update_speed_tooltip()
            self.update_total_time_label(0)
            self.update_countdown_label(0)
            self.update_time_label(0)
        except Exception:
            pass

    def toggle_pause(self):
        """Ȱ/~]v2.6.5 - Ѧ2.5²޿^"""
        if self.recording or self.playing:
            # ? uϥ core_recorder Ȱ\
            if hasattr(self, 'core_recorder'):
                is_paused = self.core_recorder.toggle_pause()
                self.paused = is_paused
            else:
                # VۮeGA
                self.paused = not self.paused
            
            state = "Ȱ" if self.paused else "~"
            mode = "s" if self.recording else ""
            self.log(f"[{format_time(time.time())}] {mode}{state}C")
            
            # ? 2.5 GȰɰ keyboard sAȦsƥ
            if self.paused and self.recording:
                try:
                    import keyboard
                    if hasattr(self.core_recorder, "_keyboard_recording") and self.core_recorder._keyboard_recording:
                        k_events = keyboard.stop_recording()
                        if not hasattr(self.core_recorder, "_paused_k_events"):
                            self.core_recorder._paused_k_events = []
                        self.core_recorder._paused_k_events.extend(k_events)
                        self.core_recorder._keyboard_recording = False
                except Exception as e:
                    self.log(f"[ĵi] Ȱɰkeyboards: {e}")
            elif self.recording:
                # ~ɭs}l keyboard s
                try:
                    import keyboard
                    keyboard.start_recording()
                    if hasattr(self.core_recorder, "_keyboard_recording"):
                        self.core_recorder._keyboard_recording = True
                except Exception as e:
                    self.log(f"[ĵi] ~sɱҰkeyboard: {e}")

    def stop_record(self):
        """s]²ƪ - v2.1 ^"""
        if not self.recording:
            return
        
        # iD core_recorder s
        self.recording = False
        self.core_recorder.stop_record()
        self.log(f"[{format_time(time.time())}] s]ݼgJƥ...^C")
        
        #  core_recorder s
        self._wait_record_thread_finish()
        

    def play_record(self):
        """}l"""
        if self.playing:
            return
        if not self.events:
            self.log("Si檺ƥAХsθJ}C")
            return
        
        # ۰ʤ MiniMode]pGĿ^
        if self.auto_mini_var.get() and not self.mini_mode_on:
            self.toggle_mini_mode()
        
        # lƮyаq]Ω۹yа^
        self.playback_offset_x = 0
        self.playback_offset_y = 0
        
        # ˬdA]jpBmBDPIBѪRס^
        if self.target_hwnd:
            try:
                from tkinter import messagebox
                
                # eT
                current_info = get_window_info(self.target_hwnd)
                if not current_info:
                    self.log("LkT")
                    return
                
                # sɪT
                recorded_info = getattr(self, 'recorded_window_info', None)
                
                if recorded_info:
                    # ˬdUt
                    size_mismatch = (current_info['size'] != recorded_info['size'])
                    pos_mismatch = (current_info['position'] != recorded_info['position'])
                    dpi_mismatch = abs(current_info['dpi_scale'] - recorded_info['dpi_scale']) > 0.01
                    resolution_mismatch = (current_info['screen_resolution'] != recorded_info['screen_resolution'])
                    
                    if size_mismatch or pos_mismatch or dpi_mismatch or resolution_mismatch:
                        # ЫظԲӪܮ
                        dialog = tk.Toplevel(self)
<<<<<<< Updated upstream
                        dialog.title("視窗狀態檢測")
                        dialog.geometry("720x820")
                        dialog.resizable(True, True)
                        dialog.minsize(600, 650)  # 設定最小尺寸
=======
                        dialog.title("A˴")
                        dialog.geometry("650x550")
                        dialog.resizable(True, True)
                        dialog.minsize(550, 450)  # ]w̤pؤo
>>>>>>> Stashed changes
                        dialog.grab_set()
                        dialog.transient(self)
                        set_window_icon(dialog)
                        
                        # ~
                        dialog.update_idletasks()
                        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                        dialog.geometry(f"+{x}+{y}")
                        
<<<<<<< Updated upstream
                        # 主框架
                        outer_frame = tb.Frame(dialog)
                        outer_frame.pack(fill="both", expand=True, padx=20, pady=20)
                        
                        # 1. 標題區 (固定頂部)
                        title_label = tb.Label(outer_frame, 
                            text="⚠️ 偵測到視窗狀態不同！", 
                            font=("Microsoft JhengHei", 14, "bold"),
                            bootstyle=WARNING)
                        title_label.pack(pady=(0, 15))
                        
                        # 2. 訊息內容區 (自適應捲動)
                        scroll_container = tb.Frame(outer_frame)
                        scroll_container.pack(fill="both", expand=True)
                        
                        canvas = tk.Canvas(scroll_container, highlightthickness=0, bg=None)
                        scrollbar = tb.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
                        scroll_content = tb.Frame(canvas)
                        
                        def _on_canvas_configure(e):
                            canvas.itemconfig(canvas_window, width=e.width)
                            
                        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")
                        canvas.configure(yscrollcommand=scrollbar.set)
                        
                        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                        canvas.bind("<Configure>", _on_canvas_configure)
                        
                        scrollbar.pack(side="right", fill="y")
                        canvas.pack(side="left", fill="both", expand=True)
                        
                        # 訊息內容
                        msg = "📊 錄製時 vs 目前狀態比較：\n\n"
=======
                        # Dج[
                        main_frame = tb.Frame(dialog)
                        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                        
                        # D
                        title_label = tb.Label(main_frame, 
                            text="?? API", 
                            font=("Microsoft JhengHei", 12, "bold"))
                        title_label.pack(pady=(0, 15))
                        
                        # Te
                        msg_frame = tb.Frame(main_frame)
                        msg_frame.pack(fill="both", expand=True)
                        
                        msg = "?? s vs ثeAG\n\n"
>>>>>>> Stashed changes
                        
                        if size_mismatch:
                            msg += f"??? jpG\n"
                            msg += f"   s: {recorded_info['size'][0]} x {recorded_info['size'][1]}\n"
                            msg += f"   ثe: {current_info['size'][0]} x {current_info['size'][1]}\n\n"
                        
                        if pos_mismatch:
                            msg += f"?? mG\n"
                            msg += f"   s: ({recorded_info['position'][0]}, {recorded_info['position'][1]})\n"
                            msg += f"   ثe: ({current_info['position'][0]}, {current_info['position'][1]})\n\n"
                        
                        if dpi_mismatch:
                            msg += f"?? DPI YG\n"
                            msg += f"   s: {recorded_info['dpi_scale']:.2f}x ({int(recorded_info['dpi_scale'] * 100)}%)\n"
                            msg += f"   ثe: {current_info['dpi_scale']:.2f}x ({int(current_info['dpi_scale'] * 100)}%)\n\n"
                        
                        if resolution_mismatch:
                            msg += f"??? ùѪRסG\n"
                            msg += f"   s: {recorded_info['screen_resolution'][0]} x {recorded_info['screen_resolution'][1]}\n"
                            msg += f"   ثe: {current_info['screen_resolution'][0]} x {current_info['screen_resolution'][1]}\n\n"
                        
                        msg_label = tb.Label(scroll_content, text=msg, font=("Microsoft JhengHei", 10), justify="left")
                        msg_label.pack(anchor="w", padx=10, pady=5, fill="x")
                        
<<<<<<< Updated upstream
                        # 3. 按鈕區 (固定底部)
                        bottom_frame = tb.Frame(outer_frame)
                        bottom_frame.pack(fill="x", pady=(10, 0))
                        
                        tb.Separator(bottom_frame, orient="horizontal").pack(fill="x", pady=10)
                        
=======
                        # ju
                        separator = tb.Separator(main_frame, orient="horizontal")
                        separator.pack(fill="x", pady=10)
                        
                        # ϥΪ̿
>>>>>>> Stashed changes
                        user_choice = {"action": None}
                        
                        def on_force_adjust():
                            user_choice["action"] = "adjust"
                            dialog.destroy()
                        
                        def on_auto_scale():
                            user_choice["action"] = "auto_scale"
                            dialog.destroy()
                        
                        def on_cancel():
                            user_choice["action"] = "cancel"
                            dialog.destroy()
                        
                        tb.Button(bottom_frame, text="🔧 強制歸位（將目前視窗調整回錄製狀態）", bootstyle=PRIMARY, 
                                 command=on_force_adjust).pack(pady=5, fill="x")
                        
<<<<<<< Updated upstream
                        tb.Button(bottom_frame, text="✨ 智能適配（推薦：保留目前狀態並自動縮放）", bootstyle=SUCCESS, 
                                 command=on_auto_scale).pack(pady=5, fill="x")
                        
                        tb.Button(bottom_frame, text="❌ 取消執行", bootstyle=DANGER, 
                                 command=on_cancel).pack(pady=5, fill="x")
                        
                        # 添加說明
                        info_label = tb.Label(bottom_frame, 
                            text="💡 提示：「智能適配」會自動調整座標以適應當前環境，適用於不同解析度、DPI 縮放和視窗大小的跨設備跑本。", 
=======
                        tb.Button(btn_frame, text="?? jk]վ^", bootstyle=PRIMARY, 
                                 command=on_force_adjust, width=25).pack(pady=5, fill="x")
                        
                        tb.Button(btn_frame, text="? At]ˡ^", bootstyle=SUCCESS, 
                                 command=on_auto_scale, width=25).pack(pady=5, fill="x")
                        
                        tb.Button(btn_frame, text="? ", bootstyle=DANGER, 
                                 command=on_cancel, width=25).pack(pady=5, fill="x")
                        
                        # K[
                        info_label = tb.Label(main_frame, 
                            text="?? ܡGuAtv|۰ʽվyХHAe\n"
                                 "AΩ󤣦PѪRסBDPI YMjp", 
>>>>>>> Stashed changes
                            font=("Microsoft JhengHei", 9), 
                            foreground="#666",
                            wraplength=650)
                        info_label.pack(pady=(10, 0))
                        
                        dialog.wait_window()
                        
                        # BzϥΪ̿
                        if user_choice["action"] == "cancel":
                            self.log("w")
                            return
                        elif user_choice["action"] == "adjust":
                            # jk
                            try:
                                target_width, target_height = recorded_info['size']
                                target_x, target_y = recorded_info['position']
                                
                                win32gui.SetWindowPos(
                                    self.target_hwnd,
                                    0,  # HWND_TOP
                                    target_x, target_y,
                                    target_width, target_height,
                                    0x0240  # SWP_SHOWWINDOW | SWP_ASYNCWINDOWPOS
                                )
                                
                                self.log(f"wվܿsɪA")
                                self.log("Nb 2 }l...")
                                
                                #  2 ~
                                self.after(2000, self._continue_play_record)
                                return
                            except Exception as e:
                                self.log(f"Lkվ: {e}")
                        elif user_choice["action"] == "auto_scale":
                            # AtҦ
                            self.log(f"ϥδAtҦi")
                            self.log(f"N۰ʽվyХHAe")
                            # ]wYҡ]Ωyഫ^
                            self._scale_ratio = {
                                'x': current_info['size'][0] / recorded_info['size'][0] if recorded_info['size'][0] > 0 else 1.0,
                                'y': current_info['size'][1] / recorded_info['size'][1] if recorded_info['size'][1] > 0 else 1.0,
                                'dpi': current_info['dpi_scale'] / recorded_info['dpi_scale'] if recorded_info['dpi_scale'] > 0 else 1.0
                            }
                            self.log(f"Y - X: {self._scale_ratio['x']:.3f}, Y: {self._scale_ratio['y']:.3f}, DPI: {self._scale_ratio['dpi']:.3f}")
            except Exception as e:
                self.log(f"ˬdAɵoͿ~: {e}")
                import traceback
                self.log(f"~Ա: {traceback.format_exc()}")
        
        # }l
        self._continue_play_record()
    
    def play_script(self):
        """? sWGѽs边եΪkOW"""
        self.play_record()
    
    def _continue_play_record(self):
        """ڰ檺k]䴩Y^"""
        # ? ]wϤѥؿ
        images_dir = os.path.join(self.script_dir, "images")
        if os.path.exists(images_dir):
            self.core_recorder.set_images_directory(images_dir)
            self.log(f"[Ϥ] w]wϤؿ: {images_dir}")
        
        # em]pGؼе^
        current_window_x = 0
        current_window_y = 0
        if self.target_hwnd:
            try:
                import win32gui
                rect = win32gui.GetWindowRect(self.target_hwnd)
                current_window_x, current_window_y = rect[0], rect[1]
            except Exception as e:
                self.log(f"Lkm: {e}")
        
        # ˬdO_Yҳ]w]AtҦ^
        has_scale_ratio = hasattr(self, '_scale_ratio') and self._scale_ratio
        
        # ഫƥy
        adjusted_events = []
        scaled_count = 0  # OYƥƶq
        
        for event in self.events:
            event_copy = event.copy()
            
            # Bzƹƥ󪺮y
            if event.get('type') == 'mouse' and 'x' in event and 'y' in event:
                # ˬdO_۹y
                if event.get('relative_to_window', False):
                    # o۹y
                    rel_x = event['x']
                    rel_y = event['y']
                    
                    # pGYAY
                    if has_scale_ratio:
                        # εjpY
                        rel_x = int(rel_x * self._scale_ratio['x'])
                        rel_y = int(rel_y * self._scale_ratio['y'])
                        scaled_count += 1
                    
                    # ഫeùy
                    event_copy['x'] = rel_x + current_window_x
                    event_copy['y'] = rel_y + current_window_y
                else:
                    # ùyСAഫ
                    pass
            
            adjusted_events.append(event_copy)
        
        # YT]ܤ@^
        if has_scale_ratio and scaled_count > 0:
            self.log(f"[At] wY {scaled_count} ӮyШƥ")
            # MYҡ]קKvTU^
            del self._scale_ratio
        
        # ]w core_recorder ƥ
        self.core_recorder.events = adjusted_events
        
        # ]wƹҦ
        if hasattr(self.core_recorder, 'set_mouse_mode'):
            mouse_mode = self.mouse_mode_var.get()
            self.core_recorder.set_mouse_mode(mouse_mode)
            if mouse_mode:
                self.log("ҦGƹҦ]NuƹС^")
            else:
                self.log("ҦGxҦ]۰ʾA^")
        
        if self.target_hwnd and any(e.get('relative_to_window', False) for e in self.events):
            relative_count = sum(1 for e in self.events if e.get('relative_to_window', False))
            self.log(f"[yഫ] {relative_count} ӵ۹y  eùy")

        try:
            speed_val = int(self.speed_var.get())
            speed_val = min(1000, max(1, speed_val))
            self.speed_var.set(str(speed_val))
            self.speed = speed_val / 100.0
        except:
            self.speed = 1.0
            self.speed_var.set("100")

        repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
        repeat_interval_sec = self._parse_time_to_seconds(self.repeat_interval_var.get())
        self._repeat_time_limit = repeat_time_sec if repeat_time_sec > 0 else None

        try:
            repeat = int(self.repeat_var.get())
        except:
            repeat = 1
        
        # Ʀ = 0 ܵLơAǤJ -1  core_recorder
        if repeat == 0:
            repeat = -1  # L
            self.log(f"[{format_time(time.time())}] ]wLƼҦ")
        elif repeat < 0:
            repeat = 1  # tƵ1

        # p`B@ɶ
        single_time = (self.events[-1]['time'] - self.events[0]['time']) / self.speed if self.events else 0
        if repeat == -1:
            # LƼҦ
            total_time = float('inf') if not self._repeat_time_limit else self._repeat_time_limit
        elif self._repeat_time_limit and repeat > 0:
            total_time = self._repeat_time_limit
        else:
            total_time = single_time * repeat + repeat_interval_sec * max(0, repeat - 1)
        self._total_play_time = total_time

        self._play_start_time = time.time()
        self._current_cycle_start_time = time.time()  # ? lƷe`_lɶ
        self.update_total_time_label(self._total_play_time)
        self.playing = True
        self.paused = False

        # lƨƥޡ]Ω UI s^
        self._current_play_index = 0

        def on_event(event):
            """ƥ󪺦^ըơ]TOަPBs^"""
            # q core_recorder ̷s
            try:
                idx = getattr(self.core_recorder, "_current_play_index", 0)
                self._current_play_index = idx
            except:
                pass

        success = self.core_recorder.play(
            speed=self.speed,
            repeat=repeat,
            repeat_time_limit=self._repeat_time_limit,
            repeat_interval=repeat_interval_sec,
            on_event=on_event
        )

        if success:
            # ץxܡAn ratio r괡J lblAOdƭܻPv
            self.log(f"[{format_time(time.time())}] }lAt׭v: {self.speed:.2f} ({self.speed_var.get()})")
            self.after(100, self._update_play_time)
        else:
            self.log("Si檺ƥAХsθJ}C")

    def stop_all(self):
        """Ҧʧ@]s@ - íBz^"""
        stopped = False
        
        # ? ߧY]wA
        if self.recording:
            self.recording = False
            stopped = True
            self.log(f"[{format_time(time.time())}] sC")
            
            #  core_recorder
            if hasattr(self, 'core_recorder'):
                try:
                    if hasattr(self.core_recorder, 'recording'):
                        self.core_recorder.recording = False
                    if hasattr(self.core_recorder, 'stop_record'):
                        self.core_recorder.stop_record()
                    if hasattr(self.core_recorder, 'events'):
                        self.events = self.core_recorder.events
                except Exception as e:
                    self.log(f"[ĵi]  core_recorder ɵoͿ~: {e}")
                    # ? jmA
                    self.core_recorder.recording = False
            
            # ݿs
            try:
                self._wait_record_thread_finish()
            except Exception as e:
                self.log(f"[ĵi] ݿsɵoͿ~: {e}")
            
        
        if self.playing:
            self.playing = False
            stopped = True
            self.log(f"[{format_time(time.time())}] C")
            
            #  core_recorder 
            if hasattr(self, 'core_recorder') and hasattr(self.core_recorder, 'stop_play'):
                try:
                    self.core_recorder.stop_play()
                except Exception as e:
                    self.log(f"[ĵi] ɵoͿ~: {e}")
            
            # Ҧid׹
            try:
                self._release_all_modifiers()
            except Exception as e:
                self.log(f"[ĵi] ׹ɵoͿ~: {e}")
        
        if not stopped:
            self.log(f"[{format_time(time.time())}] Li椤ʧ@iC")
        
        # ? ߧYs
        self.update_time_label(0)
        self.update_countdown_label(0)
        self.update_total_time_label(0)
        
        # jsɶ
        try:
            self._update_play_time()
            self._update_record_time()
        except Exception:
            pass
    


    def force_quit(self):
        """
        jҦʧ@{]v2.6.5+ TMz^
        
        ? ciG
        - u{Uֱ
        - ϥ keyboard.unhook_all()
        - O@L{
        
        i涶ǡj
        1. ߧYҦsM
        2. ҦM hooks
        3. Mz{Uֱ]vTL{^
        4. jפ{
        """
        try:
            self.log("[t] ?? jGߧYפҦʧ@...")
        except:
            pass

        # ? BJ1GߧYҦʧ@
        try:
            self.recording = False
            self.playing = False
            self.paused = False
            
            #  core_recorder
            if hasattr(self, 'core_recorder'):
                try:
                    self.core_recorder.recording = False
                    self.core_recorder.playing = False
                    self.core_recorder.stop_record()
                    self.core_recorder.stop_play()
                except:
                    pass
        except Exception as e:
            try:
                self.log(f"[ĵi] ʧ@~: {e}")
            except:
                pass

        # ? BJ2GҦ]קKd^
        try:
            self._release_all_modifiers()
        except:
            pass

        # ? BJ3GTMz{ֱ]vTL{^
        try:
            import keyboard
            
            # tΧֱ
            for handler in self._hotkey_handlers.values():
                try:
                    keyboard.remove_hotkey(handler)
                except:
                    pass
            self._hotkey_handlers.clear()
            
            # }ֱ
            for handler in self._script_hotkey_handlers.values():
                try:
                    keyboard.remove_hotkey(handler)
                except:
                    pass
            self._script_hotkey_handlers.clear()
            
            # ? TGkeyboard.unhook_all() 
            # ]G|Ҧ{A]AϥΪ̪Lu
            
        except Exception:
            pass

        # PhX
        try:
            self.log("[t] YN{")
        except:
            pass
        try:
            # ϥ os._exit HTOߧYפ
            import os, sys
            try:
                self.quit()
            except:
                try:
                    self.destroy()
                except:
                    pass
            try:
                os._exit(0)
            except SystemExit:
                sys.exit(0)
        except Exception:
            try:
                import sys
                sys.exit(0)
            except:
                pass
    
    def _release_all_modifiers(self):
        """Ҧ׹Hd]v2.6.5 ״_ - ֱ^"""
        try:
            import keyboard
            # `׹P`ΫAɶqקKd
            keys_to_release = ['ctrl', 'shift', 'alt', 'win']
            # [J\PrƦr
            keys_to_release += [f'f{i}' for i in range(1, 13)]
            keys_to_release += [chr(c) for c in range(ord('a'), ord('z')+1)]
            keys_to_release += [str(d) for d in range(0, 10)]

            for k in keys_to_release:
                try:
                    keyboard.release(k)
                except:
                    pass

<<<<<<< Updated upstream
            # ✅ v2.7.6 強制透過 Windows API 釋放核心修飾鍵 (防止 keyboard 模組失效)
            try:
                import win32api, win32con
                vk_map = {
                    'ctrl': [win32con.VK_CONTROL, win32con.VK_LCONTROL, win32con.VK_RCONTROL],
                    'shift': [win32con.VK_SHIFT, win32con.VK_LSHIFT, win32con.VK_RSHIFT],
                    'alt': [win32con.VK_MENU, win32con.VK_LMENU, win32con.VK_RMENU],
                    'win': [win32con.VK_LWIN, win32con.VK_RWIN]
                }
                for name, vks in vk_map.items():
                    for vk in vks:
                        # 0x0002 是 KEYEVENTF_KEYUP
                        win32api.keybd_event(vk, 0, 0x0002, 0)
            except Exception as e:
                self.log(f"⚠️ WinAPI 釋放按鍵失敗: {e}")

            # 不再呼叫 unhook_all/unhook_all_hotkeys
            # 這些會移除系統快捷鍵 (F9/F10 等)，導致 3-5 次後失效
            # 只需釋放按鍵本身即可，快捷鍵保持註冊狀態
=======
            # AIs unhook_all/unhook_all_hotkeys
            # oǷ|tΧֱ (F9/F10 )AɭP 3-5 ᥢ
            # u䥻YiAֱOUA
>>>>>>> Stashed changes

            self.log("[t] w`")
        except Exception as e:
            self.log(f"[ĵi] ׹ɵoͿ~: {e}")

    def _wait_record_thread_finish(self):
        """ݿs core_recorder APB events  auto_save"""
        # uˬd core_recorder  thread
        t = getattr(self.core_recorder, "_record_thread", None)
        if t and getattr(t, "is_alive", lambda: False)():
            # ٨SA~򵥫
            self.after(100, self._wait_record_thread_finish)
            return

        # pG core_recorder wAq core_recorder ^ events æs
        try:
            self.events = getattr(self.core_recorder, "events", []) or []
            
            # YϥΪ̿wFؼеABz۹y
            if getattr(self, "target_hwnd", None):
                try:
                    rect = win32gui.GetWindowRect(self.target_hwnd)
                    l, t, r, b = rect
                    window_x, window_y = l, t
                    
                    # ഫ۹yШùLo~ƥ
                    converted_events = []
                    for e in self.events:
                        if not isinstance(e, dict):
                            continue
                        
                        # ˬdO_y
                        x = y = None
                        if 'x' in e and 'y' in e:
                            x, y = e.get('x'), e.get('y')
                        elif 'pos' in e and isinstance(e.get('pos'), (list, tuple)) and len(e.get('pos')) >= 2:
                            x, y = e.get('pos')[0], e.get('pos')[1]
                        
                        # Y䤣yЫhDƹƥAOd
                        if x is None or y is None:
                            converted_events.append(e)
                            continue
                        
                        # ˬdO_b
                        if (l <= int(x) <= r) and (t <= int(y) <= b):
                            # ഫ۹y
                            event_copy = e.copy()
                            event_copy['x'] = int(x) - window_x
                            event_copy['y'] = int(y) - window_y
                            # аOoO۹y
                            event_copy['relative_to_window'] = True
                            converted_events.append(event_copy)
                    
                    self.log(f"[{format_time(time.time())}] sAlƥơG{len(self.events)}Aഫ۹yСG{len(converted_events)}")
                    self.events = converted_events
                except Exception as ex:
                    self.log(f"[{format_time(time.time())}] ഫ۹yЮɵoͿ~: {ex}")
            else:
                self.log(f"[{format_time(time.time())}] swAoƥơG{len(self.events)}")
            
            # ATO|b|gJɩIs auto_save
            self.auto_save_script()
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] PBsƥoͿ~: {ex}")

    def get_events_json(self):
        return json.dumps(self.events, ensure_ascii=False, indent=2)

    def set_events_json(self, json_str):
        try:
            data = json.loads(json_str)
            
            # Bzخ榡G
            # 1. 榡: {"events": [...], "settings": {...}}
            # 2. ²Ʈ榡: [...] (OƥC)
            if isinstance(data, dict) and "events" in data:
                self.events = data["events"]
            elif isinstance(data, list):
                self.events = data
            else:
                raise ValueError("䴩 JSON 榡")
            
            self.log(f"[{format_time(time.time())}] wq JSON J {len(self.events)} ƥC")
        except Exception as e:
            self.log(f"[{format_time(time.time())}] JSON J: {e}")

    def save_config(self):
        # theme_var wQAϥηe theme
        current_theme = self.style.theme_use()
        self.user_config["skin"] = current_theme
        # TOxsɥ[WɦW
        script_name = self.script_var.get()
        if script_name and not script_name.endswith('.json'):
            script_name = script_name + '.json'
        self.user_config["last_script"] = script_name
        self.user_config["repeat"] = self.repeat_var.get()
        self.user_config["speed"] = self.speed_var.get()
        self.user_config["script_dir"] = self.script_dir
        self.user_config["language"] = self.language_var.get()
        self.user_config["repeat_time"] = self.repeat_time_var.get()
        self.user_config["hotkey_map"] = self.hotkey_map
        self.user_config["auto_mini_mode"] = self.auto_mini_var.get()  # xs۰ʤ]w
        self.user_config["mouse_mode"] = self.mouse_mode_var.get()  # xsƹҦ]w
        save_user_config(self.user_config)
        self.log("i]wwsj")  # sWGx

    def auto_save_script(self):
        try:
            # ϥ script_io  auto_save_script
            settings = {
                "speed": self.speed_var.get(),
                "repeat": self.repeat_var.get(),
                "repeat_time": self.repeat_time_var.get(),
                "repeat_interval": self.repeat_interval_var.get(),
                "random_interval": self.random_interval_var.get()
            }
            # xs㪺T]]t DPIBѪR׵^
            if hasattr(self, 'recorded_window_info') and self.recorded_window_info:
                settings["window_info"] = self.recorded_window_info
                self.log(f"[xs] Tw]tb}")
            
            filename = sio_auto_save_script(self.script_dir, self.events, settings)
            # h .json ɦWHܦb UI
            display_name = os.path.splitext(filename)[0] if filename.endswith('.json') else filename
            self.log(f"[{format_time(time.time())}] ۰ʦsɡG{filename}AƥơG{len(self.events)}")
            self.refresh_script_list()
            self.refresh_script_listbox()  # Pɧs}C
            self.script_var.set(display_name)  # ϥΥhɦWW
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)  # MxsɦWHŪ
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] sɥ: {ex}")

    # --- xs}]w ---
    def save_script_settings(self):
        """Nثe speed/repeat/repeat_time/repeat_interval/random_interval gJe}ɮ
        
<<<<<<< Updated upstream
        增強穩定性:
        - 完整的錯誤處理
        - 資料驗證
        - 清晰的用戶反饋
=======
        Wjíw:
        - 㪺~Bz
        - ƾ
        - MΤX
>>>>>>> Stashed changes
        """
        script = self.script_var.get()
        
        # ҬO_ܸ}
        if not script or not script.strip():
            self.log("xs: Хܤ@Ӹ}")
            messagebox.showwarning("ĵi", "Хb}椤ܤ@Ӹ}")
            return
        
        # TO}W٥]t .json ɦW
        if not script.endswith('.json'):
            script_file = script + '.json'
        else:
            script_file = script
        
        # إߧ|
        path = os.path.join(self.script_dir, script_file)
        
        # ˬdɮ׬O_sb
        if not os.path.exists(path):
            self.log(f"xs: 䤣}ɮ '{script_file}'")
            messagebox.showerror("~", f"䤣}ɮ:\n{script_file}\n\nнT{}O_sb")
            return
        
        try:
            # ]w][Jҡ^
            settings = {}
            
            # ҳt
            try:
                speed_val = self.speed_var.get().strip()
                speed_int = int(speed_val)
                if speed_int < 1 or speed_int > 1000:
                    raise ValueError(f"t׭ {speed_int} WXd (1-1000)")
                settings["speed"] = speed_val
            except Exception as e:
                self.log(f"ĵi: t׭ȵL,ϥιw] 100: {e}")
                settings["speed"] = "100"
            
            # ҭƦ
            try:
                repeat_val = self.repeat_var.get().strip()
                repeat_int = int(repeat_val)
                if repeat_int < 0:
                    raise ValueError(f"Ʀ {repeat_int} it")
                settings["repeat"] = repeat_val
            except Exception as e:
                self.log(f"ĵi: ƦƵL,ϥιw] 1: {e}")
                settings["repeat"] = "1"
            
            # Үɶ榡
            for time_var_name, var, default in [
                ("Ʈɶ", self.repeat_time_var, "00:00:00"),
                ("ƶj", self.repeat_interval_var, "00:00:00")
            ]:
                try:
                    time_val = var.get().strip()
                    # Үɶ榡
                    if time_val and not self._validate_time_format(time_val):
                        raise ValueError(f"ɶ榡T: {time_val}")
                    settings[time_var_name.replace("", "repeat_").replace("ɶ", "time").replace("j", "interval")] = time_val if time_val else default
                except Exception as e:
                    self.log(f"ĵi: {time_var_name}榡L,ϥιw] {default}: {e}")
                    settings[time_var_name.replace("", "repeat_").replace("ɶ", "time").replace("j", "interval")] = default
            
            # Hj
            try:
                settings["random_interval"] = bool(self.random_interval_var.get())
            except:
                settings["random_interval"] = False
            
            # ϥ script_io xs
            sio_save_script_settings(path, settings)
            
            # \^X
            self.log(f"]wwxs}: {script}")
            self.log(f"   t: {settings['speed']}, : {settings['repeat']}, " +
                    f"ɶ: {settings.get('repeat_time', '00:00:00')}, " +
                    f"j: {settings.get('repeat_interval', '00:00:00')}")
            self.log(": ϥΧֱɱNMγoǰѼ")
            
        except Exception as ex:
            # Բӿ~i
            error_msg = str(ex)
            self.log(f"xs}]w: {error_msg}")
            
            import traceback
            detailed_error = traceback.format_exc()
            self.log(f"~Ա:\n{detailed_error}")
            
            messagebox.showerror("xs", 
                               f"Lkxs}]w:\n\n{error_msg}\n\nЬdݤxԲӸT")
    
    def _validate_time_format(self, time_str):
        """Үɶ榡 HH:MM:SS"""
        import re
        pattern = r'^\d{1,2}:\d{2}:\d{2}$'
        return re.match(pattern, time_str) is not None

    # --- Ū}]w ---
    def on_script_selected(self, event=None):
        """J襤}Ψ]w
        
        Wjíw:
        - 㪺ɮ
        - ۰ʮ榡ഫ (ıƽs边  events)
        - ԲӪ~i
        - TBz
        """
        script = self.script_var.get()
        if not script or not script.strip():
            return
        
        # pGSɦWA[W .json
        if not script.endswith('.json'):
            script_file = script + '.json'
        else:
            script_file = script
        
        path = os.path.join(self.script_dir, script_file)
        
        # ? ˬdɮ׬O_sb
        if not os.path.exists(path):
            self.log(f"? J: }ɮפsb '{script_file}'")
            messagebox.showwarning("ĵi", f"䤣}ɮ:\n{script_file}")
            return
        
        # ? ˬdɮפjp (ɮ)
        try:
            file_size = os.path.getsize(path)
            if file_size == 0:
                self.log(f"J: }ɮ׬ '{script_file}'")
                messagebox.showerror("~", f"}ɮפwlaά:\n{script_file}")
                return
            elif file_size > 50 * 1024 * 1024:  # 50MB
                self.log(f"ĵi: }ɮ׹Lj ({file_size / 1024 / 1024:.1f} MB)")
                if not messagebox.askyesno("T{", f"}ɮ׸j ({file_size / 1024 / 1024:.1f} MB)\nTwnJ?"):
                    return
        except Exception as e:
            self.log(f"ĵi: ˬdɮ׮ɵoͿ~: {e}")
        
        try:
<<<<<<< Updated upstream
            # 載入腳本資料
            data = sio_load_script(path)
            
            # ✅ 檢查資料完整性
=======
            # J}ƾ
            data = sio_load_script(path)
            
            # ? ˬdƾڧ
>>>>>>> Stashed changes
            if not isinstance(data, dict):
                raise ValueError("}榡~: OĪ JSON ")
            
            events = data.get("events", [])
            settings = data.get("settings", {})
            
            # ? SBz: ıƽs边榡ഫ
            if not events or len(events) == 0:
                if "script_actions" in settings and settings["script_actions"]:
                    self.log("ıƽs边},}lഫ...")
                    try:
                        events = self._actions_to_events(settings["script_actions"])
                        if len(events) == 0:
                            raise ValueError("ഫLĨƥ")
                        self.log(f"ഫ: {len(events)} ƥ")
                    except Exception as convert_err:
                        self.log(f"ഫ: {convert_err}")
                        messagebox.showerror("ഫ", 
                                           f"Lkഫıƽs边}:\n\n{convert_err}")
                        return
                else:
                    self.log(f"ĵi: }LƥBLʧ@C")
                    if not messagebox.askyesno("T{", 
                                               "}S󤺮e\nO_~J?"):
                        return
            
            # ]wƥC
            self.events = events
            
            # _Ѽ (aw])
            self.speed_var.set(settings.get("speed", "100"))
            self.repeat_var.set(settings.get("repeat", "1"))
            self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
            self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
            
            try:
                self.random_interval_var.set(settings.get("random_interval", False))
            except:
                self.random_interval_var.set(False)
            
            # ? ŪT (s榡u,ݮe®榡)
            if "window_info" in settings and isinstance(settings["window_info"], dict):
                self.recorded_window_info = settings["window_info"]
                self.log(f"?? T:")
                self.log(f"   jp: {self.recorded_window_info.get('size', ('N/A', 'N/A'))[0]} x {self.recorded_window_info.get('size', ('N/A', 'N/A'))[1]}")
                self.log(f"   DPI: {self.recorded_window_info.get('dpi_scale', 1.0):.2f}x ({int(self.recorded_window_info.get('dpi_scale', 1.0) * 100)}%)")
                self.log(f"   ѪR: {self.recorded_window_info.get('screen_resolution', ('N/A', 'N/A'))[0]} x {self.recorded_window_info.get('screen_resolution', ('N/A', 'N/A'))[1]}")
            elif "window_size" in settings:
                # ݮe®榡
                self.recorded_window_info = {
                    "size": tuple(settings["window_size"]),
                    "position": (0, 0),
                    "dpi_scale": 1.0,
                    "screen_resolution": (1920, 1080),
                    "client_size": tuple(settings["window_size"])
                }
                self.log(f"®榡T (wഫ)")
            else:
                self.recorded_window_info = None
                self.log(f"LT (iରyи})")
            
            # ɦWɥhɦW
            display_name = os.path.splitext(script_file)[0]
            self.log(f"}wJ: {display_name} ({len(self.events)} ƥ)")
            self.log(f"   t: {self.speed_var.get()}, : {self.repeat_var.get()}")
            
            # xs]w
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(script_file)
            
            # ? pܹwɶ
            if self.events and len(self.events) > 0:
                try:
                    # 榸ɶ
                    single_time = self.events[-1]['time'] - self.events[0]['time']
                    self.update_countdown_label(single_time)
                    
                    # p`B@ɶ
                    speed_val = int(self.speed_var.get())
                    speed = speed_val / 100.0
                    repeat = int(self.repeat_var.get())
                    repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
                    repeat_interval_sec = self._parse_time_to_seconds(self.repeat_interval_var.get())
                    
                    single_adjusted = single_time / speed
                    
                    if repeat == 0:  # L
                        total_time = float('inf') if not repeat_time_sec else repeat_time_sec
                    elif repeat_time_sec > 0:
                        total_time = repeat_time_sec
                    else:
                        total_time = single_adjusted * repeat + repeat_interval_sec * max(0, repeat - 1)
                    
                    self.update_total_time_label(total_time)
                    
                    # ܮɶT
                    if total_time == float('inf'):
                        self.log(f"榸ɶ: {single_time:.1f}, `B@: L")
                    else:
                        self.log(f"榸ɶ: {single_time:.1f}, `B@: {total_time:.1f}")
                except Exception as time_err:
                    self.log(f"pɶɵoͿ~: {time_err}")
                    self.update_countdown_label(0)
                    self.update_total_time_label(0)
            else:
                self.update_countdown_label(0)
                self.update_total_time_label(0)
                
        except json.JSONDecodeError as e:
            self.log(f"J: JSON 榡~ - {e}")
            messagebox.showerror("榡~", 
                               f"}ɮ׮榡la:\n\n{e}\n\nШϥΤrs边ˬdɮפe")
        except Exception as ex:
            self.log(f"J}: {ex}")
            import traceback
            detailed_error = traceback.format_exc()
            self.log(f"~Ա:\n{detailed_error}")
            messagebox.showerror("J", 
                               f"LkJ}:\n\n{ex}\n\nЬdݤxԲӸT")
        
        # xs]w
        self.save_config()

    def load_script(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], initialdir=self.script_dir)
        if path:
            try:
                data = sio_load_script(path)
                self.events = data.get("events", [])
                settings = data.get("settings", {})
                self.speed_var.set(settings.get("speed", "100"))
                self.repeat_var.set(settings.get("repeat", "1"))
                self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(settings.get("random_interval", False))
                self.log(f"[{format_time(time.time())}] }wJG{os.path.basename(path)}A@ {len(self.events)} ƥC")
                self.refresh_script_list()
                self.script_var.set(os.path.basename(path))
                with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                    f.write(os.path.basename(path))
                self.save_config()
            except Exception as ex:
                self.log(f"J}: {ex}")

    def load_last_script(self):
        if os.path.exists(LAST_SCRIPT_FILE):
            with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                last_script = f.read().strip()
            if last_script:
                # TOɦW
                if not last_script.endswith('.json'):
                    last_script = last_script + '.json'
                
                script_path = os.path.join(self.script_dir, last_script)
                if os.path.exists(script_path):
                    try:
                        data = sio_load_script(script_path)
                        self.events = data.get("events", [])
                        settings = data.get("settings", {})
                        self.speed_var.set(settings.get("speed", "100"))
                        self.repeat_var.set(settings.get("repeat", "1"))
                        self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                        self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                        self.random_interval_var.set(settings.get("random_interval", False))
                        
                        # ŪT]s榡u^
                        if "window_info" in settings:
                            self.recorded_window_info = settings["window_info"]
                        elif "window_size" in settings:
                            # ݮe®榡
                            self.recorded_window_info = {
                                "size": tuple(settings["window_size"]),
                                "position": (0, 0),
                                "dpi_scale": 1.0,
                                "screen_resolution": (1920, 1080),
                                "client_size": tuple(settings["window_size"])
                            }
                        else:
                            self.recorded_window_info = None
                        
                        # ܮɥhɦW
                        display_name = os.path.splitext(last_script)[0]
                        self.script_var.set(display_name)
                        self.log(f"[{format_time(time.time())}] ۰ʸJ}G{display_name}A@ {len(self.events)} ƥC")
                    except Exception as ex:
                        self.log(f"JW}: {ex}")
                        self.random_interval_var.set(settings.get("random_interval", False))
                        self.script_var.set(last_script)
                        self.log(f"[{format_time(time.time())}] w۰ʸJW}G{last_script}A@ {len(self.events)} ƥC")
                    except Exception as ex:
                        self.log(f"JW}: {ex}")

    def update_mouse_pos(self):
        try:
            import mouse
            x, y = mouse.get_position()
            self.mouse_pos_label.config(text=f"(X={x},Y={y})")
        except Exception:
            self.mouse_pos_label.config(text="(X=?,Y=?)")
        self.after(100, self.update_mouse_pos)

    def rename_script(self):
        old_name = self.script_var.get()
        new_name = self.rename_var.get().strip()
        if not old_name or not new_name:
            self.log(f"[{format_time(time.time())}] пܸ}ÿJsW١C")
            return
        
        # TO old_name ɦW
        if not old_name.endswith('.json'):
            old_name += '.json'
        
        # TO new_name ɦW
        if not new_name.endswith('.json'):
            new_name += '.json'
        
        old_path = os.path.join(self.script_dir, old_name)
        new_path = os.path.join(self.script_dir, new_name)
        
        if not os.path.exists(old_path):
            self.log(f"[{format_time(time.time())}] 䤣l}ɮסC")
            return
        
        if os.path.exists(new_path):
            self.log(f"[{format_time(time.time())}] ɮפwsbAдӦW١C")
            return
        
        try:
            os.rename(old_path, new_path)
            # s last_script.txt
            new_display_name = os.path.splitext(new_name)[0]
            self.log(f"[{format_time(time.time())}] }wWG{new_display_name}")
            self.refresh_script_list()
            self.refresh_script_listbox()
            # sܡ]ܮɤtɦW^
            self.script_var.set(new_display_name)
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(new_name)
        except Exception as e:
            self.log(f"[{format_time(time.time())}] W: {e}")
        self.rename_var.set("")  # WMſJ

    def merge_scripts(self):
        """}Ҹ}XֹܮءA\NhӸ}ǦX֬@ӷs}"""
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
        
        # ЫئXֹܮ
        merge_win = tb.Toplevel(self)
        merge_win.title(lang_map.get("Xָ}", "Xָ}"))
        merge_win.geometry("850x550")
        merge_win.resizable(True, True)
        merge_win.minsize(750, 500)
        
<<<<<<< Updated upstream
        # 待合併腳本資料列表：儲存 {"name": str, "delay": float}
        self.merge_data_list = []
=======
        # ӧO}r]}W -> ơ^
        script_delays = {}
>>>>>>> Stashed changes
        
        # 
        info_frame = tb.Frame(merge_win, padding=10)
        info_frame.pack(fill="x")
        info_label = tb.Label(
            info_frame, 
<<<<<<< Updated upstream
            text="[合併] 選擇要合併的腳本，按順序執行（點兩下腳本設定延遲）",
            font=("微軟正黑體", 10),
=======
            text="?? ܭnX֪}Aǰ]IU}]w^",
            font=("Ln", 10),
>>>>>>> Stashed changes
            wraplength=800
        )
        info_label.pack()
        
        # Dne
        main_content = tb.Frame(merge_win)
        main_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # iθ}C]^
        left_frame = tb.LabelFrame(main_content, text=lang_map.get("ҦScript", "Ҧ}"), padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        available_list = tk.Listbox(left_frame, height=12, selectmode=tk.EXTENDED, font=("Ln", 10))
        available_list.pack(fill="both", expand=True)
        
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        for script in scripts:
            display_name = os.path.splitext(script)[0]
            available_list.insert(tk.END, display_name)
        
        # s
        middle_frame = tb.Frame(main_content, padding=5)
        middle_frame.pack(side="left", fill="y")
        
        def add_to_merge():
            selected_indices = available_list.curselection()
            for idx in selected_indices:
                script_name = available_list.get(idx)
<<<<<<< Updated upstream
                # 允許重複加入
                self.merge_data_list.append({"name": script_name, "delay": 0})
            update_merge_list_display()
=======
                if script_name not in merge_list.get(0, tk.END):
                    merge_list.insert(tk.END, script_name)
                    script_delays[script_name] = 0  # w] 0 
>>>>>>> Stashed changes
        
        def remove_from_merge():
            selected_indices = list(merge_list.curselection())
            if not selected_indices:
                return
            for idx in reversed(selected_indices):
                if 0 <= idx < len(self.merge_data_list):
                    self.merge_data_list.pop(idx)
            update_merge_list_display()
        
        def move_up():
            selected_indices = merge_list.curselection()
            if not selected_indices or selected_indices[0] == 0:
                return
            for idx in selected_indices:
                if idx > 0:
                    self.merge_data_list[idx], self.merge_data_list[idx-1] = self.merge_data_list[idx-1], self.merge_data_list[idx]
            update_merge_list_display()
            for idx in selected_indices:
                if idx > 0:
                    merge_list.selection_set(idx - 1)
        
        def move_down():
            selected_indices = merge_list.curselection()
            if not selected_indices or selected_indices[-1] == merge_list.size() - 1:
                return
            for idx in reversed(selected_indices):
                if idx < len(self.merge_data_list) - 1:
                    self.merge_data_list[idx], self.merge_data_list[idx+1] = self.merge_data_list[idx+1], self.merge_data_list[idx]
            update_merge_list_display()
            for idx in selected_indices:
                if idx < len(self.merge_data_list) - 1:
                    merge_list.selection_set(idx + 1)
        
        def on_double_click(event):
            """IU}]wɶ"""
            index = merge_list.nearest(event.y)
            if index < 0 or index >= len(self.merge_data_list):
                return
            item_data = self.merge_data_list[index]
            script_name = item_data["name"]
            
            # ЫؿJܮ
            delay_win = tb.Toplevel(merge_win)
            delay_win.title("]w")
            delay_win.geometry("300x150")
            delay_win.resizable(False, False)
            delay_win.transient(merge_win)
            delay_win.grab_set()
            
            # m
            delay_win.update_idletasks()
            x = merge_win.winfo_x() + (merge_win.winfo_width() - 300) // 2
            y = merge_win.winfo_y() + (merge_win.winfo_height() - 150) // 2
            delay_win.geometry(f"+{x}+{y}")
            
            frame = tb.Frame(delay_win, padding=20)
            frame.pack(fill="both", expand=True)
            
            tb.Label(frame, text=f"}G{script_name}", font=("Ln", 10, "bold")).pack(pady=(0, 10))
            tb.Label(frame, text="ơG", font=("Ln", 10)).pack()
            
            current_delay = item_data["delay"]
            delay_var = tk.StringVar(value=str(current_delay))
            delay_entry = tb.Entry(frame, textvariable=delay_var, width=15, font=("Ln", 11), justify="center")
            delay_entry.pack(pady=5)
            delay_entry.focus()
            delay_entry.select_range(0, tk.END)
            
            # u\ƦrA̦h 4 
            def validate_delay(P):
                if P == "":
                    return True
                try:
                    if len(P) > 4:
                        return False
                    val = int(P)
                    return 0 <= val <= 9999
                except:
                    return False
            
            vcmd = (delay_win.register(validate_delay), '%P')
            delay_entry.config(validate="key", validatecommand=vcmd)
            
            def save_delay():
                try:
                    delay_value = int(delay_var.get()) if delay_var.get() else 0
<<<<<<< Updated upstream
                    self.merge_data_list[index]["delay"] = delay_value
                    # 更新顯示
=======
                    script_delays[script_name] = delay_value
                    # s
>>>>>>> Stashed changes
                    update_merge_list_display()
                    delay_win.destroy()
                except:
                    messagebox.showerror("~", "пJĪƦr")
            
            btn_frame = tb.Frame(frame)
            btn_frame.pack(pady=10)
            tb.Button(btn_frame, text="Tw", command=save_delay, width=8, bootstyle=SUCCESS).pack(side="left", padx=5)
            tb.Button(btn_frame, text="", command=delay_win.destroy, width=8, bootstyle=SECONDARY).pack(side="left", padx=5)
            
            # Enter T{
            delay_entry.bind("<Return>", lambda e: save_delay())
        
        def update_merge_list_display():
<<<<<<< Updated upstream
            """更新合併列表顯示（顯示延遲時間）"""
=======
            """sX֦Cܡ]ܩɶ^"""
            current_items = list(merge_list.get(0, tk.END))
>>>>>>> Stashed changes
            merge_list.delete(0, tk.END)
            for item in self.merge_data_list:
                script_name = item["name"]
                delay = item["delay"]
                if delay > 0:
                    display_text = f"{script_name}  [ {delay}]"
                else:
                    display_text = script_name
                merge_list.insert(tk.END, display_text)
        
<<<<<<< Updated upstream
        add_btn = tb.Button(middle_frame, text="加 入", command=add_to_merge, width=10, bootstyle=SUCCESS)
        add_btn.pack(pady=5)
        
        remove_btn = tb.Button(middle_frame, text="移 除", command=remove_from_merge, width=10, bootstyle=DANGER)
=======
        add_btn = tb.Button(middle_frame, text="? " + lang_map.get("[J", "[J"), command=add_to_merge, width=10, bootstyle=SUCCESS)
        add_btn.pack(pady=5)
        
        remove_btn = tb.Button(middle_frame, text="? " + lang_map.get("", ""), command=remove_from_merge, width=10, bootstyle=DANGER)
>>>>>>> Stashed changes
        remove_btn.pack(pady=5)
        
        tb.Label(middle_frame, text="").pack(pady=10)
        
<<<<<<< Updated upstream
        up_btn = tb.Button(middle_frame, text="上 移", command=move_up, width=10, bootstyle=INFO)
        up_btn.pack(pady=5)
        
        down_btn = tb.Button(middle_frame, text="下 移", command=move_down, width=10, bootstyle=INFO)
=======
        up_btn = tb.Button(middle_frame, text="? W", command=move_up, width=10, bootstyle=INFO)
        up_btn.pack(pady=5)
        
        down_btn = tb.Button(middle_frame, text="? U", command=move_down, width=10, bootstyle=INFO)
>>>>>>> Stashed changes
        down_btn.pack(pady=5)
        
        # X֦C]k^
        right_frame = tb.LabelFrame(main_content, text="ݦXָ}]涶ǡ^", padding=10)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        merge_list = tk.Listbox(right_frame, height=12, selectmode=tk.EXTENDED, font=("Ln", 10))
        merge_list.pack(fill="both", expand=True)
        merge_list.bind("<Double-Button-1>", on_double_click)
        
        # ާ@
        bottom_frame = tb.Frame(merge_win, padding=15)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        tb.Label(bottom_frame, text="X֦W١G", 
                font=("Ln", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        
        new_name_var = tk.StringVar(value="merged_script")
        new_name_entry = tb.Entry(bottom_frame, textvariable=new_name_var, width=40, font=("Ln", 10))
        new_name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        button_frame = tb.Frame(bottom_frame)
        button_frame.grid(row=0, column=2, sticky="e", padx=(20, 0))
        
        bottom_frame.columnconfigure(1, weight=1)
        
        def do_merge():
<<<<<<< Updated upstream
            """執行腳本合併"""
            if len(self.merge_data_list) < 2:
                messagebox.showwarning("提示", "請至少選擇2個腳本進行合併")
=======
            """}X"""
            script_names_display = list(merge_list.get(0, tk.END))
            # u}W١]ܪаO^
            script_names = []
            for display_name in script_names_display:
                #  [ X] аO
                if "  [" in display_name:
                    real_name = display_name.split("  [")[0]
                else:
                    real_name = display_name
                script_names.append(real_name)
            
            if len(script_names) < 2:
                messagebox.showwarning("", "Цܤֿ2Ӹ}iX")
>>>>>>> Stashed changes
                return
            
            script_names = [item["name"] for item in self.merge_data_list]
            script_delays_list = [item["delay"] for item in self.merge_data_list]
            
            new_name = new_name_var.get().strip()
            if not new_name:
                messagebox.showwarning("", "пJX֦W")
                return
            
            if not new_name.endswith('.json'):
                new_name += '.json'
            
            new_path = os.path.join(self.script_dir, new_name)
            if os.path.exists(new_path):
                if not messagebox.askyesno("T{", f"} {new_name} wsbAO_л\H"):
                    return
            
            try:
                merged_events = []
                time_offset = 0.0
                first_script_settings = None
                
                for i, script_name in enumerate(script_names):
                    script_path = os.path.join(self.script_dir, script_name + '.json')
                    if not os.path.exists(script_path):
                        self.log(f"[ĵi] 䤣}G{script_name}")
                        continue
                    
                    data = sio_load_script(script_path)
                    events = data.get("events", [])
                    
                    if i == 0:
                        first_script_settings = data.get("settings", {}).copy()
<<<<<<< Updated upstream
                        self.log(f"[合併] 使用腳本A的參數設定：{script_name}")
=======
                        self.log(f"? ϥθ}AѼƳ]wG{script_name}")
>>>>>>> Stashed changes
                    
                    if not events:
                        continue
                    
                    script_base_time = events[0]['time'] if events else 0
                    
                    for event in events:
                        new_event = event.copy()
                        new_event['time'] = (event['time'] - script_base_time) + time_offset
                        merged_events.append(new_event)
                    
                    # sɶ][W}ɶ + ӧO^
                    if merged_events:
                        script_duration = events[-1]['time'] - script_base_time
                        individual_delay = script_delays_list[i]
                        time_offset = merged_events[-1]['time'] + individual_delay
                        if individual_delay > 0:
<<<<<<< Updated upstream
                            self.log(f"[合併] 腳本 {script_name} 設定延遲 {individual_delay} 秒")
=======
                            self.log(f"? } {script_name} ]w {individual_delay} ")
>>>>>>> Stashed changes
                
                # xsX᪺֫}
                merged_data = {
                    "events": merged_events,
                    "settings": first_script_settings or {}
                }
                
                with open(new_path, "w", encoding="utf-8") as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)
                
<<<<<<< Updated upstream
                self.log(f"[成功] 合併完成：{new_name}，共 {len(merged_events)} 筆事件")
                messagebox.showinfo("成功", f"已合併 {len(script_names)} 個腳本為\n{new_name}")
=======
                self.log(f"? X֧G{new_name}A@ {len(merged_events)} ƥ")
                messagebox.showinfo("\", f"wX {len(script_names)} Ӹ}\n{new_name}")
>>>>>>> Stashed changes
                
                self.refresh_script_list()
                self.script_var.set(os.path.splitext(new_name)[0])
                merge_win.destroy()
                
            except Exception as e:
                self.log(f"X֥: {e}")
                messagebox.showerror("~", f"X֥ѡG\n{e}")
                import traceback
                traceback.print_exc()
                
                # s}C
                self.refresh_script_list()
                self.refresh_script_listbox()
                
                # ܮ
                merge_win.destroy()
                
                # ߰ݬO_Js}
                if messagebox.askyesno("", "O_JsX֪}H"):
                    # Js}
                    self.events = merged_events
                    self.script_settings = first_script_settings
                    self.script_var.set(os.path.splitext(new_name)[0])
                    with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                        f.write(new_name)
                
            except Exception as e:
                messagebox.showerror("~", f"X֥ѡG{e}")
                import traceback
                self.log(f"Xֿ~Ա: {traceback.format_exc()}")
        
        merge_execute_btn = tb.Button(
            button_frame, 
            text=lang_map.get("X֨xs", "X֨xs"), 
            command=do_merge, 
            bootstyle=SUCCESS,
            width=15
        )
        merge_execute_btn.pack(side="left", padx=(0, 5))
        
        cancel_btn = tb.Button(
            button_frame, 
            text=lang_map.get("", ""), 
            command=merge_win.destroy, 
            bootstyle=SECONDARY,
            width=10
        )
        cancel_btn.pack(side="left")

    def open_scripts_dir(self):
        path = os.path.abspath(self.script_dir)  # ץ
        os.startfile(path)

    def open_hotkey_settings(self):
        win = tb.Toplevel(self)
        win.title("Hotkey")
        win.geometry("400x450")  # WjؤoHeǱj
        win.resizable(True, True)  # \վjp
        win.minsize(350, 400)  # ]m̤pؤo
        # ]wϥ
        set_window_icon(win)
        
        # ~
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")

        # إߥDج[
        main_frame = tb.Frame(win)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ̥ثeyo
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
        labels = {
            "start": lang_map["}ls"],
            "pause": lang_map["Ȱ/~"],
            "stop": lang_map[""],
            "play": lang_map[""],
            "mini": lang_map["MiniMode"],
            "force_quit": lang_map["j"]
        }
        vars = {}
        entries = {}
        row = 0

        def on_entry_key(event, key, var):
            """jƪֱ䮷 - v2.8.2 ״_
            
            ״_DGϥΪ̥u]w alt+ զX
            ѨMסGT׹䰻PDBz
            
            䴩G
            - WGz, F7, F12
            - զXGalt+z, ctrl+F3, shift+a
            - h׹Gctrl+alt+z, ctrl+shift+F5
            """
            # oDW
            key_name = event.keysym.lower()
            
            # ׹Mg]ΩLo^
            modifier_keysyms = {
                'shift_l', 'shift_r', 
                'control_l', 'control_r',
                'alt_l', 'alt_r', 'alt_gr',
                'win_l', 'win_r', 'super_l', 'super_r',
                'meta_l', 'meta_r'
            }
            
            # pGuF׹䥻A]w]ݥD^
            if key_name in modifier_keysyms:
                return "break"
            
            # ˴u׹]ư׹䥻 keysym^
            modifiers = []
            
            # Ctrl Gstate bit 2 (0x0004)
            if event.state & 0x0004:
                modifiers.append("ctrl")
            
            # Shift Gstate bit 0 (0x0001)
            if event.state & 0x0001:
                modifiers.append("shift")
            
            # Alt GWindows W Alt O state bit 17 (0x20000)A]iO bit 3 (0x0008)
            # `NGubD Alt ɤ~[J
            if event.state & 0x20000 or event.state & 0x0008:
                modifiers.append("alt")
            
            # Win Gstate bit 6 (0x0040)
            if event.state & 0x0040:
                modifiers.append("win")
            
            # SMg]N Tkinter keysym ର keyboard Ҳծ榡^
            special_keys = {
                'return': 'enter',
                'prior': 'page_up',
                'next': 'page_down',
                'backspace': 'backspace',
                'delete': 'delete',
                'insert': 'insert',
                'home': 'home',
                'end': 'end',
                'tab': 'tab',
                'escape': 'esc',
                'space': 'space',
                'caps_lock': 'caps_lock',
                'num_lock': 'num_lock',
                'scroll_lock': 'scroll_lock',
                'print': 'print_screen',
                'pause': 'pause',
                'grave': '`',
                'asciitilde': '`',
                'quoteleft': '`',
                'minus': '-',
                'equal': '=',
                'bracketleft': '[',
                'bracketright': ']',
                'backslash': '\\',
                'semicolon': ';',
                'quoteright': "'",
                'apostrophe': "'",
                'comma': ',',
                'period': '.',
                'slash': '/',
            }
            
            # BzD
            main_key = None
            
            # \ F1-F24
            if key_name.startswith('f') and len(key_name) >= 2 and key_name[1:].isdigit():
                main_key = key_name.upper()  # F1, F12 jg
            # V
            elif key_name in ('up', 'down', 'left', 'right'):
                main_key = key_name
            # S
            elif key_name in special_keys:
                main_key = special_keys[key_name]
            # ƦrL
            elif key_name.startswith('kp_'):
                main_key = key_name.replace('kp_', 'num_')
            # @]rBƦr^
            elif len(key_name) == 1 and key_name.isalnum():
                main_key = key_name
            # L
            elif key_name not in modifier_keysyms:
                main_key = key_name
            
            # զX̲׵G
            if main_key:
                # MJبݯdr
                entries[key].delete(0, tk.END)
                
                #  ctrl, alt, shift, win ǱƦC
                modifier_order = {'ctrl': 0, 'alt': 1, 'shift': 2, 'win': 3}
                modifiers.sort(key=lambda x: modifier_order.get(x, 99))
                
                # h
                seen = set()
                unique_modifiers = []
                for m in modifiers:
                    if m not in seen:
                        seen.add(m)
                        unique_modifiers.append(m)
                
                result_parts = unique_modifiers + [main_key]
                result = "+".join(result_parts)
                
                var.set(result)
            
            return "break"

        def on_entry_focus_in(event, var):
            var.set("J")

        def on_entry_focus_out(event, key, var):
            if var.get() == "J" or not var.get():
                var.set(self.hotkey_map.get(key, ""))

        for key, label in labels.items():
            entry_frame = tb.Frame(main_frame)
            entry_frame.pack(fill="x", pady=5)
            
            tb.Label(entry_frame, text=label, font=("Microsoft JhengHei", 11), width=12, anchor="w").pack(side="left", padx=5)
            # TO hotkey_map AקK KeyError
            hotkey_value = self.hotkey_map.get(key, "")
            var = tk.StringVar(value=hotkey_value)
            entry = tb.Entry(entry_frame, textvariable=var, font=("Consolas", 10), state="normal")
            entry.pack(side="left", fill="x", expand=True, padx=5)
            vars[key] = var
            entries[key] = entry
            # jƪGu KeyPress ƥ
            entry.bind("<KeyPress>", lambda e, k=key, v=var: on_entry_key(e, k, v))
            entry.bind("<FocusIn>", lambda e, v=var: on_entry_focus_in(e, v))
            entry.bind("<FocusOut>", lambda e, k=key, v=var: on_entry_focus_out(e, k, v))
            row += 1

        def save_and_apply():
            for key in self.hotkey_map:
                val = vars[key].get()
                if val and val != "J":
                    self.hotkey_map[key] = val.lower()
            #  HotkeyManager Τ@U]Ysb^A_hϥª _register_hotkeys
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                try:
                    self.hotkey_manager.register_all()
                except Exception:
                    self._register_hotkeys()
            else:
                self._register_hotkeys()
            self._update_hotkey_labels()
            self.save_config()  # sWo,TOxs
            self.log("ֱ]wwsC")
            win.destroy()

        # sج[
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        tb.Button(btn_frame, text="xs", command=save_and_apply, width=15, bootstyle=SUCCESS).pack(pady=5)


    def _register_hotkeys(self):
        """
        UtΧֱ
        
        - xsCӧֱ䪺 handle
        - Mzɥu{Uֱ
        - vTL{
        
        TGkeyboard.unhook_all() - |Ҧ]]AL{^
        """
        try:
            import keyboard
        except Exception as e:
            self.log(f"[~] keyboard ҲոJ: {e}")
            return
        
        method_map = {
            "start": "start_record",
            "pause": "toggle_pause",
            "stop": "stop_all",
            "play": "play_record",
            "mini": "toggle_mini_mode",
            "force_quit": "force_quit"
        }
        
        # ? M handler]u{U^
        for handler in self._hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(handler)
            except Exception:
                pass  # 
        self._hotkey_handlers.clear()
        
        # UҦֱ
        for key, hotkey in self.hotkey_map.items():
            method_name = method_map.get(key)
            if not method_name:
                continue
                
            callback = getattr(self, method_name, None)
            if not callable(callback):
                continue
            
            # ✅ 註冊並儲存 handle (加入重試機制)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    handler = keyboard.add_hotkey(
                        hotkey, 
                        callback,
                        suppress=False,
                        trigger_on_release=False
                    )
                    self._hotkey_handlers[key] = handler
                    
<<<<<<< Updated upstream
                    if self._is_first_run:
                        self.log(f"已註冊快捷鍵: {hotkey} → {key}")
                    break  # 成功則跳出重試迴圈
                except Exception as ex:
                    if attempt == max_retries - 1:  # 最後一次嘗試
                        self.log(f"快捷鍵 {hotkey} 註冊失敗 (已重試{max_retries}次): {ex}")
                    else:
                        time.sleep(0.1)  # 短暫延遲後重試
=======
                callback = getattr(self, method_name, None)
                if not callable(callback):
                    continue
                
                # ? Uxs handle
                handler = keyboard.add_hotkey(
                    hotkey, 
                    callback,
                    suppress=False,
                    trigger_on_release=False
                )
                self._hotkey_handlers[key] = handler
                
                if self._is_first_run:
                    self.log(f"wUֱ: {hotkey}  {key}")
            except Exception as ex:
                self.log(f"ֱ {hotkey} U: {ex}")
>>>>>>> Stashed changes
        
        # ܡGBᤣAܵUT
        if self._is_first_run:
<<<<<<< Updated upstream
            self.log("✅ 系統快捷鍵註冊完成（錄製時仍然有效）")
        
        # ✅ 記錄註冊時間（用於健康檢查）
        self._last_hotkey_register_time = time.time()
=======
            self.log("? tΧֱU]sɤMġ^")
>>>>>>> Stashed changes


    def _register_script_hotkeys(self):
        """
        UҦ}ֱ]ϥ keyboard Ҳա^
        
        iPyInstaller ݮeʼWjj
        - K[ keyboard ҲոJˬd
        - ԲӪ~BzMx
        """
        try:
            import keyboard
        except ImportError as e:
            self.log(f"[~] LkJ keyboard ҲեΩ}ֱ: {e}")
            return
        except Exception as e:
            self.log(f"[~] keyboard Ҳժlƥ: {e}")
            return
        
        # ª}ֱ
        for script, info in self._script_hotkey_handlers.items():
            try:
                if "handler" in info:
                    keyboard.remove_hotkey(info["handler"])
            except Exception as ex:
                # 
                pass
        self._script_hotkey_handlers.clear()

        # yҦ}õUֱ
        if not os.path.exists(self.script_dir):
            return
        
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        registered_scripts = 0
        failed_scripts = 0
        
        for script in scripts:
            path = os.path.join(self.script_dir, script)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # ձq settings ŪApGShqŪ]ݮe®榡^
                hotkey = ""
                if "settings" in data and "script_hotkey" in data["settings"]:
                    hotkey = data["settings"]["script_hotkey"]
                elif "script_hotkey" in data:
                    hotkey = data["script_hotkey"]
                
                if hotkey:
                    try:
                        # ϥ lambda e script 
                        handler = keyboard.add_hotkey(
                            hotkey,
                            lambda s=script: self._play_script_by_hotkey(s),
                            suppress=False,
                            trigger_on_release=False
                        )
                        
                        self._script_hotkey_handlers[script] = {
                            "script": script,
                            "hotkey": hotkey,
                            "handler": handler
                        }
                        registered_scripts += 1
                        self.log(f"wU}ֱ: {hotkey}  {script}")
                    except Exception as ex:
                        failed_scripts += 1
                        self.log(f"U}ֱ䥢 ({script}): {ex}")
            except Exception as ex:
                self.log(f"Ū}ɮץ ({script}): {ex}")
        
        # `UG
        if registered_scripts > 0 or failed_scripts > 0:
            self.log(f"[}ֱ] U: \ {registered_scripts},  {failed_scripts}")

    def _check_hotkey_health(self):
        """
        定期檢查快捷鍵健康狀態並自動修復
        
        功能：
        - 檢測快捷鍵是否仍然有效
        - 自動重新註冊失效的快捷鍵
        - 記錄失敗次數並提示用戶
        
        每30秒執行一次
        """
        try:
            import keyboard
            
            # 檢查是否需要重新註冊（如果上次註冊超過5分鐘且有失敗記錄）
            current_time = time.time()
            time_since_last_register = current_time - self._last_hotkey_register_time
            
            # 檢查快捷鍵是否仍然註冊
            hotkeys_ok = True
            
            # 簡單檢查：嘗試獲取已註冊的快捷鍵數量
            if len(self._hotkey_handlers) == 0 and len(self.hotkey_map) > 0:
                # 快捷鍵應該存在但實際上沒有 - 需要重新註冊
                hotkeys_ok = False
                self._hotkey_check_failures += 1
                self.log("⚠️ 檢測到快捷鍵失效，正在自動修復...")
            
            # 如果檢測到問題或距離上次註冊超過10分鐘，重新註冊
            if not hotkeys_ok or time_since_last_register > 600:
                try:
                    # 重新註冊系統快捷鍵
                    self._register_hotkeys()
                    # 重新註冊腳本快捷鍵
                    self._register_script_hotkeys()
                    
                    if not hotkeys_ok:
                        self.log("✅ 快捷鍵已自動修復")
                        self._hotkey_check_failures = 0  # 重置失敗計數
                except Exception as ex:
                    self.log(f"❌ 快捷鍵修復失敗: {ex}")
                    self._hotkey_check_failures += 1
            
            # 如果連續失敗3次，提示用戶
            if self._hotkey_check_failures >= 3:
                self.log("⚠️ 快捷鍵多次失效，建議重啟程式")
                self._hotkey_check_failures = 0  # 重置計數避免重複提示
            
        except Exception as e:
            # 靜默處理錯誤，避免影響主程式
            pass
        finally:
            # 繼續下一次檢查（每30秒）
            try:
                self.after(30000, self._check_hotkey_health)
            except:
                pass  # 如果視窗已關閉，忽略錯誤

    def _play_script_by_hotkey(self, script):
        """zLֱĲo}]ϥθ}xsѼơ^"""
        if self.playing or self.recording:
            self.log(f"ثebsΰ椤ALk}G{script}")
            return
        
        path = os.path.join(self.script_dir, script)
        if not os.path.exists(path):
            self.log(f"䤣}ɮסG{script}")
            return
        
        try:
            # J}Ψ]w
            data = sio_load_script(path)
            self.events = data.get("events", [])
            settings = data.get("settings", {})
            
            # Mθ}ѼƳ]w
            self.speed_var.set(settings.get("speed", "100"))
            self.repeat_var.set(settings.get("repeat", "1"))
            self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
            self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
            self.random_interval_var.set(settings.get("random_interval", False))
            
            # s}
            self.script_var.set(script)
            
            self.log(f"zLֱJ}G{script}")
            
            # }l
            self.play_record()
            
        except Exception as ex:
            self.log(f"Jð}ѡG{ex}")

    def _update_hotkey_labels(self):
        self.btn_start.config(text=f"}ls ({self.hotkey_map['start']})")
        self.btn_pause.config(text=f"Ȱ/~ ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=f" ({self.hotkey_map['stop']})")
        self.btn_play.config(text=f" ({self.hotkey_map['play']})")
        # MiniMode sPBs
        if hasattr(self, "mini_btns") and self.mini_btns:
            for btn, icon, key in self.mini_btns:
                btn.config(text=f"{icon} {self.hotkey_map[key]}")

    def toggle_mini_mode(self):
        #  MiniMode A]Ѧ ChroLens_Mimic2.5.py  TinyMode^
        if not hasattr(self, "mini_mode_on"):
            self.mini_mode_on = False
        if not hasattr(self, "mini_window"):
            self.mini_window = None
        
        self.mini_mode_on = not self.mini_mode_on
        
        if self.mini_mode_on:
            if self.mini_window is None or not self.mini_window.winfo_exists():
                self.mini_window = tb.Toplevel(self)
                self.mini_window.title("ChroLens_Mimic MiniMode")
                self.mini_window.geometry("810x40")
                self.mini_window.overrideredirect(True)
                self.mini_window.resizable(False, False)
                self.mini_window.attributes("-topmost", True)
                # ]wϥ
                set_window_icon(self.mini_window)
                
                self.mini_btns = []
                
                # sW˼Label]hyt^
                lang = self.language_var.get()
                lang_map = LANG_MAP.get(lang, LANG_MAP["c餤"])
                self.mini_countdown_label = tb.Label(
                    self.mini_window,
                    text=f"{lang_map['Ѿl']}: 00:00:00",
                    font=("Microsoft JhengHei", 12),
                    foreground="#FF95CA", width=13
                )
                self.mini_countdown_label.grid(row=0, column=0, padx=2, pady=5)
                
                # 즲\
                self.mini_window.bind("<ButtonPress-1>", self._start_move_mini)
                self.mini_window.bind("<B1-Motion>", self._move_mini)
                
                btn_defs = [
                    ("?", "start"),
                    ("?", "pause"),
                    ("?", "stop"),
                    ("??", "play"),
                    ("??", "mini")
                ]
                
                for i, (icon, key) in enumerate(btn_defs):
                    command_map = {
                        "start": "start_record",
                        "pause": "toggle_pause",
                        "stop": "stop_all",
                        "play": "play_record",
                        "mini": "toggle_mini_mode"
                    }
                    btn = tb.Button(
                        self.mini_window,
                        text=f"{icon} {self.hotkey_map[key]}",
                        width=7, style="My.TButton",
                        command=getattr(self, command_map[key])
                    )
                    btn.grid(row=0, column=i+1, padx=2, pady=5)
                    self.mini_btns.append((btn, icon, key))
                
                # K[۰ʤĿ
                self.mini_auto_check = tb.Checkbutton(
                    self.mini_window,
                    text=lang_map["۰ʤ"],
                    variable=self.auto_mini_var,
                    style="My.TCheckbutton"
                )
                self.mini_auto_check.grid(row=0, column=len(btn_defs)+1, padx=5, pady=5)
                
                # K[ Tooltip
                Tooltip(self.mini_auto_check, lang_map["ĿɡA{s/N۰ഫ"])
                
                self.mini_window.protocol("WM_DELETE_WINDOW", self._close_mini_mode)
                self.withdraw()
        else:
            self._close_mini_mode()
    
    def _close_mini_mode(self):
        """ MiniMode"""
        if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
        self.mini_window = None
        self.deiconify()
        self.mini_mode_on = False
    
    def _start_move_mini(self, event):
        """}l즲 MiniMode """
        self._mini_x = event.x
        self._mini_y = event.y
    
    def _move_mini(self, event):
        """즲 MiniMode """
        if hasattr(self, 'mini_window') and self.mini_window:
            x = self.mini_window.winfo_x() + event.x - self._mini_x
            y = self.mini_window.winfo_y() + event.y - self._mini_y
            self.mini_window.geometry(f"+{x}+{y}")

    def use_default_script_dir(self):
        self.script_dir = SCRIPTS_DIR
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        self.refresh_script_list()
        self.save_config()

        # }ҸƧ
        os.startfile(self.script_dir)
    
    def _on_script_combo_click(self, event=None):
        """I}UԿɡAYɨsC"""
        self.refresh_script_list()

    def refresh_script_list(self):
        """s}UԿ椺e]hɦWܡ^"""
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        # ܮɥhɦWAxsɤϥΧɦW
        display_scripts = [os.path.splitext(f)[0] for f in scripts]
        self.script_combo['values'] = display_scripts
        
        # Yثeܪ}sbAhM
        current = self.script_var.get()
        if current.endswith('.json'):
            current_display = os.path.splitext(current)[0]
        else:
            current_display = current
        
        if current_display not in display_scripts:
            self.script_var.set('')
        else:
            self.script_var.set(current_display)

    def refresh_script_listbox(self):
        """s}]wϥC]ɦWBֱMwɡ^"""
        try:
            # M Treeview
            for item in self.script_treeview.get_children():
                self.script_treeview.delete(item)
            
            if not os.path.exists(self.script_dir):
                os.makedirs(self.script_dir)
            
            scripts = sorted([f for f in os.listdir(self.script_dir) if f.endswith('.json')])
            
            # إܦC
            for script_file in scripts:
                # hɦW
                script_name = os.path.splitext(script_file)[0]
                
                # ŪֱMw
                hotkey = ""
                schedule_time = ""
                try:
                    path = os.path.join(self.script_dir, script_file)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "settings" in data:
                            if "script_hotkey" in data["settings"]:
                                hotkey = data["settings"]["script_hotkey"]
                            if "schedule_time" in data["settings"]:
                                schedule_time = data["settings"]["schedule_time"]
                except Exception:
                    pass
                
                # J Treeview]TGW١BֱBwɡ^
                self.script_treeview.insert("", "end", values=(
                    script_name, 
                    hotkey if hotkey else "", 
                    schedule_time if schedule_time else ""
                ))
                
        except Exception as ex:
            self.log(f"s}M楢: {ex}")

    def on_page_selected(self, event=None):
        idx = self.page_menu.curselection()
        if not idx:
            return
        self.show_page(idx[0])

    def show_page(self, idx):
        # MŤe
        for widget in self.page_content_frame.winfo_children():
            widget.grid_forget()
            widget.place_forget()
        if idx == 0:
            # x
            self.log_text.grid(row=0, column=0, sticky="nsew")
            for child in self.page_content_frame.winfo_children():
                if isinstance(child, tb.Scrollbar):
                    child.grid(row=0, column=1, sticky="ns")
        elif idx == 1:
            # }s边 - }ҽs边
            self.open_visual_editor()
            # ^xܭ
            self.page_menu.selection_clear(0, "end")
            self.page_menu.selection_set(0)
            self.show_page(0)
        elif idx == 2:
            # }]w
            self.script_setting_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.refresh_script_listbox()
        elif idx == 3:
            # ]w
            self.global_setting_frame.place(x=0, y=0, anchor="nw")

    def on_script_treeview_select(self, event=None):
        """Bz} Treeview ܨƥ"""
        try:
            selection = self.script_treeview.selection()
            if not selection:
                return
            
            # o襤ت
            item = selection[0]
            values = self.script_treeview.item(item, "values")
            if not values:
                return
            
            script_name = values[0]  # }W١]tɦW^
            
            # [^ .json ɦW
            script_file = script_name + ".json"
            
            # sUԿ
            self.script_var.set(script_name)  # UԿuܦW
            
            # J}T
            path = os.path.join(self.script_dir, script_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # ܧֱ
                if "settings" in data:
                    hotkey = data["settings"].get("script_hotkey", "")
                    self.hotkey_capture_var.set(hotkey)
                    
                    # JL]w
                    self.speed_var.set(data["settings"].get("speed", "100"))
                    self.repeat_var.set(data["settings"].get("repeat", "1"))
                    self.repeat_time_var.set(data["settings"].get("repeat_time", "00:00:00"))
                    self.repeat_interval_var.set(data["settings"].get("repeat_interval", "00:00:00"))
                    self.random_interval_var.set(data["settings"].get("random_interval", False))
                
                # Jƥ
                self.events = data.get("events", [])
                
            except Exception as ex:
                self.log(f"J}T: {ex}")
                self.hotkey_capture_var.set("")
        except Exception as ex:
            self.log(f"BzIƥ󥢱: {ex}")

    def on_script_listbox_select(self, event=None):
        """OdªܳBz]ݮeʡ^"""
        # kwQ on_script_listbox_click N
        pass

    def on_hotkey_entry_key(self, event):
        """jƪֱ䮷]Ω}ֱ^- v2.8.2 ״_
        
        ״_DGϥΪ̥u]w alt+ զX
        ѨMסGT׹䰻PDBz
        
        䴩G
        - WGz, F7, F12
        - զXGalt+z, ctrl+F3, shift+a
        - h׹Gctrl+alt+z, ctrl+shift+F5
        """
        # oDW
        key_name = event.keysym.lower()
        
        # ׹Mg]ΩLo^
        modifier_keysyms = {
            'shift_l', 'shift_r', 
            'control_l', 'control_r',
            'alt_l', 'alt_r', 'alt_gr',
            'win_l', 'win_r', 'super_l', 'super_r',
            'meta_l', 'meta_r'
        }
        
        # pGuF׹䥻A]w]ݥD^
        if key_name in modifier_keysyms:
            return "break"
        
        # ˴u׹
        modifiers = []
        
        # Ctrl Gstate bit 2 (0x0004)
        if event.state & 0x0004:
            modifiers.append("ctrl")
        
        # Shift Gstate bit 0 (0x0001)
        if event.state & 0x0001:
            modifiers.append("shift")
        
        # Alt GWindows W Alt O state bit 17 (0x20000)A]iO bit 3 (0x0008)
        if event.state & 0x20000 or event.state & 0x0008:
            modifiers.append("alt")
        
        # Win Gstate bit 6 (0x0040)
        if event.state & 0x0040:
            modifiers.append("win")
        
        # SMg]N Tkinter keysym ର keyboard Ҳծ榡^
        special_keys = {
            'return': 'enter',
            'prior': 'page_up',
            'next': 'page_down',
            'backspace': 'backspace',
            'delete': 'delete',
            'insert': 'insert',
            'home': 'home',
            'end': 'end',
            'tab': 'tab',
            'escape': 'esc',
            'space': 'space',
            'caps_lock': 'caps_lock',
            'num_lock': 'num_lock',
            'scroll_lock': 'scroll_lock',
            'print': 'print_screen',
            'pause': 'pause',
            'grave': '`',
            'asciitilde': '`',
            'quoteleft': '`',
            'minus': '-',
            'equal': '=',
            'bracketleft': '[',
            'bracketright': ']',
            'backslash': '\\',
            'semicolon': ';',
            'quoteright': "'",
            'apostrophe': "'",
            'comma': ',',
            'period': '.',
            'slash': '/',
        }
        
        # BzD
        main_key = None
        
        # \ F1-F24
        if key_name.startswith('f') and len(key_name) >= 2 and key_name[1:].isdigit():
            main_key = key_name.upper()  # F1, F12 jg
        # V
        elif key_name in ('up', 'down', 'left', 'right'):
            main_key = key_name
        # S
        elif key_name in special_keys:
            main_key = special_keys[key_name]
        # ƦrL
        elif key_name.startswith('kp_'):
            main_key = key_name.replace('kp_', 'num_')
        # @]rBƦr^
        elif len(key_name) == 1 and key_name.isalnum():
            main_key = key_name
        # L
        elif key_name not in modifier_keysyms:
            main_key = key_name
        
        # զX̲׵G
        if main_key:
            #  ctrl, alt, shift, win ǱƦC
            modifier_order = {'ctrl': 0, 'alt': 1, 'shift': 2, 'win': 3}
            modifiers.sort(key=lambda x: modifier_order.get(x, 99))
            
            # h
            seen = set()
            unique_modifiers = []
            for m in modifiers:
                if m not in seen:
                    seen.add(m)
                    unique_modifiers.append(m)
            
            result_parts = unique_modifiers + [main_key]
            result = "+".join(result_parts)
            
            self.hotkey_capture_var.set(result)
        
        return "break"

    def set_script_hotkey(self):
        """襤}]wֱõU"""
        script_name = self.script_var.get()
        hotkey = self.hotkey_capture_var.get().strip().lower()
        
        if not script_name or not hotkey or hotkey == "J":
            self.log("Хܸ}ÿJĪֱC")
            return
        
        # TO .json ɦW
        if not script_name.endswith('.json'):
            script_name = script_name + '.json'
        
        path = os.path.join(self.script_dir, script_name)
        
        if not os.path.exists(path):
            self.log(f"䤣}ɮסG{script_name}")
            return
        
        try:
            # Ū{
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # TO settings ϶
            if "settings" not in data:
                data["settings"] = {}
            
            # xsֱ} settings
            data["settings"]["script_hotkey"] = hotkey
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # sUҦ}ֱ
            self._register_script_hotkeys()
            
            # sC
            self.refresh_script_listbox()
            
            self.log(f"w]w} {script_name} ֱG{hotkey}")
            self.log("ܡGUֱNϥθ}xsѼƪ")
        except Exception as ex:
            self.log(f"]w}ֱ䥢: {ex}")
            import traceback
            self.log(f"~Ա: {traceback.format_exc()}")

    def delete_selected_script(self):
        """R襤}]䴩h^"""
        # q Treeview Ҧ襤
        selection = self.script_treeview.selection()
        
        if not selection:
            self.log("ХܭnR}C")
            return
        
        # nR}W
        scripts_to_delete = []
        for item in selection:
            values = self.script_treeview.item(item, "values")
            if values:
                script_name = values[0]  # }W١]tɦW^
                # TO .json ɦW
                if not script_name.endswith('.json'):
                    script_file = script_name + '.json'
                else:
                    script_file = script_name
                
                path = os.path.join(self.script_dir, script_file)
                if os.path.exists(path):
                    scripts_to_delete.append((script_name, script_file, path))
        
        if not scripts_to_delete:
            self.log("䤣iR}ɮסC")
            return
        
        # T{R
        import tkinter.messagebox as messagebox
        if len(scripts_to_delete) == 1:
            # Ӹ}R
            script_name = scripts_to_delete[0][0]
            message = f"TwnR}u{script_name}vܡH\nާ@Lk_I"
        else:
            # hӸ}R
            script_list = "\n".join([f"E {s[0]}" for s in scripts_to_delete])
            message = f"TwnRHU {len(scripts_to_delete)} Ӹ}ܡH\n\n{script_list}\n\nާ@Lk_I"
        
        result = messagebox.askyesno(
            "T{R",
            message,
            icon='warning'
        )
        
        if not result:
            return
        
        # R
        deleted_count = 0
        failed_count = 0
        
        for script_name, script_file, path in scripts_to_delete:
            try:
                os.remove(path)
                self.log(f"? wR}G{script_name}")
                deleted_count += 1
                
                # U}ֱ]pGܡ^
                if script_file in self._script_hotkey_handlers:
                    handler_info = self._script_hotkey_handlers[script_file]
                    try:
                        keyboard.remove_hotkey(handler_info.get('handler'))
                    except:
                        pass
                    del self._script_hotkey_handlers[script_file]
                    
            except Exception as ex:
                self.log(f"? R} [{script_name}]: {ex}")
                failed_count += 1
        
        # `
        if deleted_count > 0:
            self.log(f"[] \R {deleted_count} Ӹ}" + 
                    (f"A{failed_count} ӥ" if failed_count > 0 else ""))
        
        # szC
        self.refresh_script_listbox()
        self.refresh_script_list()
        
        # M UI
        self.script_var.set('')
        self.hotkey_capture_var.set('')
        if hasattr(self, 'selected_script_line'):
            self.selected_script_line = None


    def open_visual_editor(self):
        """}Ҹ}s边"""
        try:
            # ? ˬds边ҲլO_i
            if VisualScriptEditor is None:
                self.log("? s边ҲդiΡAˬd text_script_editor.py ɮ")
                messagebox.showerror("~", "LkJ}s边Ҳ")
                return
            
            # e襤}
            script_path = None
            current_script = self.script_var.get()
            if current_script:
                script_path = os.path.join(self.script_dir, f"{current_script}.json")
                if not os.path.exists(script_path):
                    self.log(f"[ĵi] 䤣}ɮ: {current_script}.json")
                    script_path = None
            
            # ˬdO_wgs边}
            if hasattr(self, 'visual_editor_window') and self.visual_editor_window and self.visual_editor_window.winfo_exists():
                # pGwsbANJIӵ
                self.visual_editor_window.focus_force()
                self.visual_editor_window.lift()
                self.log("[T] s边w},ܵ")
            else:
                # إ߷sxsޥ
                self.visual_editor_window = VisualScriptEditor(self, script_path)
                self.log("[T] w}Ҹ}s边")
                # ? TOs边b̤Wh]קKDBs边^
                self.after(100, self._ensure_editor_on_top)
        except Exception as e:
            self.log(f"[~] Lk}ҽs边G{e}")
            import traceback
            error_detail = traceback.format_exc()
            self.log(f"~Ա: {error_detail}")
            messagebox.showerror("~", f"Lk}Ҹ}s边G\n\n{e}\n\nЬdݤxԲӸT")

    def _ensure_editor_on_top(self):
        """TOs边b̤Wh"""
        if hasattr(self, 'visual_editor_window') and self.visual_editor_window:
            try:
                self.visual_editor_window.lift()
                self.visual_editor_window.focus_force()
            except:
                pass

    def open_schedule_settings(self):
        """}ұƵ{]w"""
        # ˬdO_襤}
        selection = self.script_treeview.selection()
        if not selection:
            self.log("Хܤ@Ӹ}")
            return
        
        item = selection[0]
        values = self.script_treeview.item(item, "values")
        script_name = values[0]
        script_file = f"{script_name}.json"
        script_path = os.path.join(self.script_dir, script_file)
        
        if not os.path.exists(script_path):
            self.log(f"}ɮפsbG{script_file}")
            return
        
        # Ū{Ƶ{
        current_schedule = ""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "settings" in data and "schedule_time" in data["settings"]:
                    current_schedule = data["settings"]["schedule_time"]
        except Exception as e:
            self.log(f"Ū}ѡG{e}")
            return
        
        # ЫرƵ{]w
        schedule_win = tk.Toplevel(self)
        schedule_win.title(f"]wƵ{ - {script_name}")
        schedule_win.geometry("500x350")  # W[ؤoקKsQB
        schedule_win.resizable(True, True)  # \վjp
        schedule_win.minsize(450, 320)  # ]w̤pؤo
        schedule_win.grab_set()
        schedule_win.transient(self)
        set_window_icon(schedule_win)  # ]wϥ
        
        # ~
        schedule_win.update_idletasks()
        x = (schedule_win.winfo_screenwidth() // 2) - (schedule_win.winfo_width() // 2)
        y = (schedule_win.winfo_screenheight() // 2) - (schedule_win.winfo_height() // 2)
        schedule_win.geometry(f"+{x}+{y}")
        
        # D
        title_frame = tb.Frame(schedule_win)
        title_frame.pack(fill="x", padx=20, pady=15)
        tb.Label(title_frame, text=f"}G{script_name}", 
                font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w")
        
        # ɶܮج[
        time_frame = tb.Frame(schedule_win)
        time_frame.pack(fill="x", padx=20, pady=10)
        
        tb.Label(time_frame, text="ɶG", 
                font=("Microsoft JhengHei", 11)).pack(side="left", padx=5)
        
        # pɤUԿ
        hour_var = tk.StringVar()
        hour_combo = tb.Combobox(time_frame, textvariable=hour_var, 
                                 values=[f"{i:02d}" for i in range(24)], 
                                 width=5, state="readonly")
        hour_combo.pack(side="left", padx=5)
        
        tb.Label(time_frame, text=":", font=("Microsoft JhengHei", 11)).pack(side="left")
        
        # UԿ
        minute_var = tk.StringVar()
        minute_combo = tb.Combobox(time_frame, textvariable=minute_var,
                                   values=[f"{i:02d}" for i in range(60)],
                                   width=5, state="readonly")
        minute_combo.pack(side="left", padx=5)
        
        # ]we
        if current_schedule:
            try:
                parts = current_schedule.split(":")
                if len(parts) == 2:
                    hour_var.set(parts[0])
                    minute_var.set(parts[1])
                else:
                    hour_var.set("09")
                    minute_var.set("00")
            except:
                hour_var.set("09")
                minute_var.set("00")
        else:
            hour_var.set("09")
            minute_var.set("00")
        
        # r
        info_frame = tb.Frame(schedule_win)
        info_frame.pack(fill="x", padx=20, pady=10)
        info_text = "]wA{NbCѫwɶ\n۰ʰ榹}"
        tb.Label(info_frame, text=info_text, 
                font=("Microsoft JhengHei", 9), 
                foreground="#666").pack(anchor="w")
        
        # sج[
        btn_frame = tb.Frame(schedule_win)
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        def save_schedule():
            hour = hour_var.get()
            minute = minute_var.get()
            
            if not hour or not minute:
                self.log("пܮɶ")
                return
            
            schedule_time = f"{hour}:{minute}"
            
            # xs}
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "settings" not in data:
                    data["settings"] = {}
                
                data["settings"]["schedule_time"] = schedule_time
                
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # sƵ{޲z
                if hasattr(self, 'schedule_manager') and self.schedule_manager:
                    schedule_id = f"script_{script_name}"
                    self.schedule_manager.add_schedule(schedule_id, {
                        'name': script_name,
                        'type': 'daily',
                        'time': f"{hour}:{minute}:00",
                        'script': script_file,
                        'enabled': True,
                        'callback': self._execute_scheduled_script
                    })
                    self.log(f"? w]wƵ{G{script_name} C {schedule_time}")
                
                # sC
                self.refresh_script_listbox()
                schedule_win.destroy()
                
            except Exception as e:
                self.log(f"xsƵ{ѡG{e}")
        
        def clear_schedule():
            # MƵ{
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "settings" in data and "schedule_time" in data["settings"]:
                    del data["settings"]["schedule_time"]
                
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Ƶ{޲zƵ{
                if hasattr(self, 'schedule_manager') and self.schedule_manager:
                    schedule_id = f"script_{script_name}"
                    self.schedule_manager.remove_schedule(schedule_id)
                    self.log(f"? wMƵ{G{script_name}")
                
                # sC
                self.refresh_script_listbox()
                schedule_win.destroy()
                
            except Exception as e:
                self.log(f"MƵ{ѡG{e}")
        
        tb.Button(btn_frame, text="Tw", width=10, bootstyle=SUCCESS,
                 command=save_schedule).pack(side="left", padx=5)
        tb.Button(btn_frame, text="MƵ{", width=10, bootstyle=WARNING,
                 command=clear_schedule).pack(side="left", padx=5)
        tb.Button(btn_frame, text="", width=10, bootstyle=SECONDARY,
                 command=schedule_win.destroy).pack(side="left", padx=5)

    def _load_all_schedules(self):
        """qҦ}JƵ{]w"""
        if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
            return
        
        try:
            if not os.path.exists(self.script_dir):
                return
            
            scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
            loaded_count = 0
            
            for script_file in scripts:
                script_path = os.path.join(self.script_dir, script_file)
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if "settings" in data and "schedule_time" in data["settings"]:
                        schedule_time = data["settings"]["schedule_time"]
                        script_name = os.path.splitext(script_file)[0]
                        schedule_id = f"script_{script_name}"
                        
                        self.schedule_manager.add_schedule(schedule_id, {
                            'name': script_name,
                            'type': 'daily',
                            'time': f"{schedule_time}:00",
                            'script': script_file,
                            'enabled': True,
                            'callback': self._execute_scheduled_script
                        })
                        loaded_count += 1
                        print(f"⏰ [系統啟動] 已載入排程: {script_name} @ {schedule_time}")
                except Exception as e:
                    self.log(f"JƵ{ ({script_file}): {e}")
            
            if loaded_count > 0:
<<<<<<< Updated upstream
                self.log(f"💡 [排程系統] 已成功載入 {loaded_count} 個腳本排程")
            else:
                print("ℹ️ [排程系統] 未發現任何設定排程的腳本")
=======
                self.log(f"? wJ {loaded_count} ӱƵ{")
>>>>>>> Stashed changes
        except Exception as e:
            self.log(f"JƵ{: {e}")
    
    def _execute_scheduled_script(self, script_file):
        """Ƶ{}^ը"""
        try:
            script_path = os.path.join(self.script_dir, script_file)
            if not os.path.exists(script_path):
                self.log(f"Ƶ{}sbG{script_file}")
                return
            
            # J}
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.events = data.get("events", [])
            self.script_settings = data.get("settings", {})
            
<<<<<<< Updated upstream
            # 更新 UI 設定（以便執行時使用正確參數）
            if "speed" in self.script_settings:
                self.speed_var.set(str(self.script_settings["speed"]))
=======
            # s]w
            if "loop_count" in self.script_settings:
                try:
                    self.loop_count_var.set(str(self.script_settings["loop_count"]))
                except:
                    pass
>>>>>>> Stashed changes
            
            if "repeat" in self.script_settings:
                # 支援舊版 loop_count 和新版 repeat
                repeat_val = self.script_settings.get("repeat", self.script_settings.get("loop_count", "1"))
                self.repeat_var.set(str(repeat_val))
            
<<<<<<< Updated upstream
            if "repeat_interval" in self.script_settings:
                # 支援舊版 interval 和新版 repeat_interval
                interval_val = self.script_settings.get("repeat_interval", self.script_settings.get("interval", "00:00:00"))
                self.repeat_interval_var.set(str(interval_val))

            if "repeat_time" in self.script_settings:
                self.repeat_time_var.set(str(self.script_settings["repeat_time"]))
            
            if "random_interval" in self.script_settings:
                self.random_interval_var.set(bool(self.script_settings["random_interval"]))
            
            if "mouse_mode" in self.script_settings:
                self.mouse_mode_var.set(bool(self.script_settings["mouse_mode"]))
            
            # 更新下拉選單顯示目前正在執行的腳本名稱
            display_name = os.path.splitext(script_file)[0]
            self.script_var.set(display_name)
            
            self.log(f"⏰ [排程執行] 腳本: {script_file}")
            self.log(f"📊 執行條件: 速度 {self.speed_var.get()}, 重複 {self.repeat_var.get()} 次")
            self.log(f"📂 載入 {len(self.events)} 筆事件")
=======
            self.log(f"? [Ƶ{] {script_file}")
            self.log(f"J {len(self.events)} ƥ")
>>>>>>> Stashed changes
            
            # ۰ʶ}l
            self.after(500, self.play_record)
            
        except Exception as e:
            self.log(f"Ƶ{}ѡG{e}")
            import traceback
            self.log(f"~Ա: {traceback.format_exc()}")

    def select_target_window(self):
        """}ҵܾAwusӵƹʧ@"""
        try:
            if WindowSelectorDialog is None:
                self.log("? ܾҲդiΡALkܵC")
                messagebox.showerror("~", "LkJܾҲ")
                return

            def on_selected(hwnd, title):
                # Me highlight
                try:
                    self.clear_window_highlight()
                except Exception:
                    pass
                if not hwnd:
                    # Mw
                    self._clear_target_window()
                    return
                #  hwnd O_
                try:
                    if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                        self.log("iΤsbC")
                        return
                except Exception:
                    pass
                self.target_hwnd = hwnd
                self.target_title = title
                # s UI ܡ]uܤrAܹϥܡ^
                short = title if len(title) <= 30 else title[:27] + "..."
                self.target_label.config(text=f"[ؼ] {short}")
                self.log(f"wwؼеG{title} (hwnd={hwnd})")
                self.log("?? ܡGkIW٥i")
                # ϥΪ̦beWeXخش
                try:
                    self.show_window_highlight(hwnd)
                except Exception:
                    pass
                # iD core_recorder]Y䴩^u hwnd
                if hasattr(self.core_recorder, 'set_target_window'):
                    self.core_recorder.set_target_window(hwnd)
                try:
                    setattr(self.core_recorder, "target_hwnd", hwnd)
                except Exception:
                    pass

            WindowSelectorDialog(self, on_selected)
        except Exception as e:
            self.log(f"[~] Lk}ҵܾG{e}")
            import traceback
            self.log(f"~Ա: {traceback.format_exc()}")
            messagebox.showerror("~", f"Lk}ҵܾG\n\n{e}")
    
    def _clear_target_window(self, event=None):
        """Mؼе]w]iѥkIĲo^"""
        self.target_hwnd = None
        self.target_title = None
        self.target_label.config(text="")
        # iD core_recorder w
        if hasattr(self.core_recorder, 'set_target_window'):
            self.core_recorder.set_target_window(None)
        self.log("wMؼе]w")

    def _refresh_target_window(self, event=None):
        """sؼе]iѥIĲo^- HۦPW٭sw"""
        if not self.target_title:
            self.log("Sؼеis")
            return
        
        original_title = self.target_title
        self.log(f"bjMG{original_title}")
        
        # jMҦiAŦXDĤ@
        found_hwnd = None
        
        def enum_callback(hwnd, _):
            nonlocal found_hwnd
            if found_hwnd:
                return True  # wgA~T|Bz
            
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                window_text = win32gui.GetWindowText(hwnd)
                if window_text and window_text == original_title:
                    found_hwnd = hwnd
                    return False  # FAT|
            except Exception:
                pass
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, None)
        except Exception as e:
            self.log(f"T|ɵoͿ~G{e}")
        
        if found_hwnd:
            # sX
            self.target_hwnd = found_hwnd
            self.target_title = original_title
            self.target_label.config(text=f"G{original_title}")
            
            # q core_recorder
            if hasattr(self.core_recorder, 'set_target_window'):
                self.core_recorder.set_target_window(found_hwnd)
            
            # ܰG
            self.show_window_highlight(found_hwnd)
            self.log(f"wswG{original_title}")
        else:
            self.log(f"䤣Wu{original_title}vAˬdO_wΧW")

    # sWGbeWH topmost Lصܿwش
    def show_window_highlight(self, hwnd):
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception:
            return
        l, t, r, b = rect
        w = max(2, r - l)
        h = max(2, b - t)
        # Mwsb
        self.clear_window_highlight()
        try:
            win = tk.Toplevel(self)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            # bzIAH frame eX border
            win.attributes("-alpha", 0.5)
            win.geometry(f"{w}x{h}+{l}+{t}")
            # ]wϥ
            set_window_icon(win)
            
            # ]w click-through]ƹƥz^
            hwnd_win = win.winfo_id()
            try:
                # WS_EX_TRANSPARENT = 0x00000020, WS_EX_LAYERED = 0x00080000
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x00080000
                WS_EX_TRANSPARENT = 0x00000020
                style = ctypes.windll.user32.GetWindowLongW(hwnd_win, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd_win, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            except Exception:
                pass
            
            # 
            frm = tk.Frame(win, bg="#00ff00", bd=4, relief="solid")
            frm.pack(fill="both", expand=True, padx=2, pady=2)
            
            # ܴܤr]ϥ Canvas HקKQjp^
            canvas = tk.Canvas(frm, bg="#000000", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            
            # pArjp]ھڵjp^
            font_size = max(12, min(24, min(w, h) // 20))
            
            # b Canvas Wøsr]jp^
            text = "? w]wؼе"
            canvas.create_text(
                w // 2, h // 2,
                text=text,
                font=("Microsoft JhengHei", font_size, "bold"),
                fill="#00ff00",
                anchor="center"
            )
            
            self._highlight_win = win
            
            # 2۰ʲMG
            self.after(2000, self.clear_window_highlight)
        except Exception as ex:
            self._highlight_win = None
            self.log(f"ܰGخɵoͿ~: {ex}")

    def clear_window_highlight(self):
        """MG"""
        w = getattr(self, "_highlight_win", None)
        if w:
            try:
                if w.winfo_exists():
                    w.destroy()
            except Exception:
                pass
            finally:
                self._highlight_win = None

# ====== ]wŪg ======
CONFIG_FILE = "user_config.json"

def load_user_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # }Ҥ~w]c餤
    return {

        "skin": "darkly",
        "last_script": "",
        "repeat": "1",
        "speed": "100",  # w]100
        "script_dir": SCRIPTS_DIR,
        "language": "c餤"
    }

def save_user_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def format_time(ts):
    """N timestamp ର HH:MM:SS r"""
    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

if __name__ == "__main__":
    # `ҰʥD{
    app = RecorderApp()
    app.mainloop()