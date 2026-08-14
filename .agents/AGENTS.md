
## 自適應視窗原則 (Adaptive Window Policy)
絕對禁止在任何 UI 元件中使用寫死的 \geometry("寬x高")\ 來固定視窗大小。所有的視窗 (Tk, Toplevel) 都必須利用 \pack()\, \grid()\ 等幾何管理器自動撐開視窗。若需限制最小尺寸以維持美觀，應使用 \minsize(寬, 高)\。若需指定視窗彈出位置，僅可使用 \geometry("+X+Y")\ 而不得綁定長寬。
