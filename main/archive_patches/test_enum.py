import ctypes
from ctypes import wintypes
import sys
print("Starting...")

user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

hwnds = []
def foreach_window(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            hwnds.append((hwnd, buf.value))
    return True

user32.EnumWindows(EnumWindowsProc(foreach_window), 0)
for h, t in hwnds[:5]:
    print(f'[{h}] {t[:30]}'.encode('utf-8', 'replace').decode('utf-8'))
