import codecs
import re

file_path = 'c:/Users/Lucien/Documents/GitHub/ChroLens-Mimic/main/modules/window_selector.py'
with codecs.open(file_path, 'r', 'utf-8') as f:
    content = f.read()

# 1. 替換 hicon_to_photoimage
old_hicon_func = """def hicon_to_photoimage(hicon):
    if not hicon:
        return None
    try:
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 16, 16)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)
        
        # 繪製 Icon 到 Bitmap
        hdc_mem.DrawIcon((0, 0), hicon)
        
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (16, 16), bmpstr, 'raw', 'BGRA', 0, 1)
        
        # 清理
        win32gui.DestroyIcon(hicon)
        
        return ImageTk.PhotoImage(img)
    except Exception:
        return None"""

new_hicon_func = """def hicon_to_photoimage(hicon):
    if not hicon:
        return None
    try:
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        # 建立 32x32 的空間以容納可能比較大的圖示
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)
        
        # 使用 DrawIconEx 繪製並強制縮放到 32x32
        win32gui.DrawIconEx(hdc_mem.GetSafeHdc(), 0, 0, hicon, 32, 32, 0, 0, win32con.DI_NORMAL)
        
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (32, 32), bmpstr, 'raw', 'BGRA', 0, 1)
        
        # 將 32x32 的影像高品質縮放至 24x24，讓 Treeview 看起來剛好
        img = img.resize((24, 24), Image.Resampling.LANCZOS)
        
        # 清理
        win32gui.DestroyIcon(hicon)
        
        return ImageTk.PhotoImage(img)
    except Exception:
        return None"""

if old_hicon_func in content:
    content = content.replace(old_hicon_func, new_hicon_func)
else:
    print("Could not find hicon_to_photoimage function!")

# 2. 修改 Treeview 樣式，增加 rowheight
tree_style_code = """        # 使用 Treeview 取代 Listbox，並隱藏表頭
        self.tree = tb.Treeview(lb_frame, columns=("title",), show="tree", selectmode="browse")"""

new_tree_style_code = """        # 設定 Treeview 樣式以適應更大的圖示
        style = tb.Style()
        style.configure("Treeview", rowheight=32)
        
        # 使用 Treeview 取代 Listbox，並隱藏表頭
        self.tree = tb.Treeview(lb_frame, columns=("title",), show="tree", selectmode="browse")"""

if tree_style_code in content:
    content = content.replace(tree_style_code, new_tree_style_code)
else:
    print("Could not find tree style code!")

with codecs.open(file_path, 'w', 'utf-8') as f:
    f.write(content)
print("Patched window_selector.py successfully!")
