import re
import os

filepath = r'c:\Users\Lucien\Documents\GitHub\ChroLens-Mimic\main\ChroLens_Mimic.py'

if not os.path.exists(filepath):
    print(f"File not found: {filepath}")
    exit(1)

with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix conflict markers
pattern = re.compile(r'<<<<<<< Updated upstream.*?>>>>>>> Stashed changes', re.DOTALL)
clean = pattern.sub('# [Resolved Conflict]\nVERSION = "2.7.6"\nGITHUB_REPO = "Lucienwooo/ChroLens-Mimic"', content)

# Fix Mojibake/Corrupted Chinese (heuristic)
# We'll replace specific patterns found in the view_file output
replacements = {
    '# qܡG:: (iW߳]mC)': '# 時間顯示：時:分:秒 (此區域動態更新)',
    '# 榸Ѿl]ϥ Frame ]qh Label {ܦ^': '# 播放剩餘時間（包含循環計數的標籤顯示）',
    '# `B@]ϥ Frame ]qh Label {ܦ^': '# 總共已播放時間',
    '# ====== row5 ϰ ======': '# ====== 第 5 列：分頁功能區 ======',
    '# sWG': '# 新增：',
    '# sWGפJ': '# 新增：匯入',
    '# sWGN': '# 新增：',
    '# ˬdO_H޲z': '# 檢查是否為管理員',
    '# LkפJ': '# 無法匯入',
    '# ? ϥΤrO}s边]wªϧΤƽs边^': '# 使用文字指令式腳本編輯器（已移除舊版圖形化編輯器）',
    '# ? wJrOs边': '# 已載入文字指令編輯器',
    '# ? LkפJs边:': '# 無法匯入編輯器:',
    '# եH`ΩRWפJAYѫh import module ˬd禡W١A̫ᴣ fallback @': '# 強化版函式匯入：嘗試匯入但若失敗則使用 module 屬性偵測，最後提供 fallback 函式',
    '# uխwRWפJ': '# 嘗試標準匯入',
    '# script_io Ҳկʤֹw禡': '# script_io 模組缺少必要函式',
    '# Ur:': '# 註冊字體失敗:',
    '# յU]|߿AѮɵ{i~^': '# 嘗試註冊（即使失敗也會繼續，避免程式中斷）',
    '# ^ (family, size)  (family, size, weight)  tupleA': '# 返回 (family, size) 或 (family, size, weight) 的 tuple，',
    '# u LINESeedTW]YiΡ^A_h^h Microsoft JhengHeiC': '# 優先選用 LINESeedTW（若已註冊），否則選用 Microsoft JhengHei。',
    '# monospace=True ɨϥ ConsolasC': '# monospace=True 時選用 Consolas。',
    '"""oϥɮ׸|]]M}oҳqΡ^"""': '"""獲取圖示路徑（包含打包後與開發環境的相容性）"""',
    '"""]wϥ"""': '"""設定視窗圖示"""',
    'print(f"]wϥܥ: {e}")': 'print(f"設定視窗圖示失敗: {e}")',
}

for old, new in replacements.items():
    clean = clean.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(clean)

print("Cleanup complete.")
