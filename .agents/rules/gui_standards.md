# GUI 開發規範

## 視窗圖示 (Window Icons)
所有在 ChroLens-Mimic 專案中建立的視窗（`tk.Tk`, `tk.Toplevel`, `tb.Window`, `tb.Toplevel`），包含未來新增的任何主視窗或彈出視窗（如設定視窗、確認視窗、提示視窗等），**都必須強制套用 `umi_奶茶色.ico` 作為視窗圖示**。

### 實作方式：
1. 從 `modules.utils` 匯入 `set_window_icon`
2. 在視窗建立後（或 `__init__` 中），立刻呼叫 `set_window_icon(window_instance)`

```python
import tkinter as tk
from modules.utils import set_window_icon

def create_my_window(parent):
    win = tk.Toplevel(parent)
    win.title("My New Window")
    
    # 必須加上這行！
    set_window_icon(win)
```

**例外：**
浮動的 tooltip (提示框) 等無標題列且 `overrideredirect(True)` 的極小視窗不需要套用。
