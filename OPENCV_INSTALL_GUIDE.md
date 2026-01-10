"""
OpenCV-Python 快速安裝指南

問題：opencv-python 安裝慢且容易失敗
原因：需要編譯 numpy，耗時且依賴 C++ 編譯器

解決方案（按優先級排序）：
"""

# ═══════════════════════════════════════════════════════════════
# 方案 1: 使用預編譯 wheel（推薦）⭐
# ═══════════════════════════════════════════════════════════════

"""
優點：
- 最快（無需編譯）
- 成功率高
- 檔案小

步驟：
1. 升級 pip
   pip install --upgrade pip

2. 安裝預編譯版本
   pip install numpy --only-binary :all:
   pip install opencv-python --only-binary :all:

3. 驗證
   python -c "import cv2; print(cv2.__version__)"
"""

# ═══════════════════════════════════════════════════════════════
# 方案 2: 使用 opencv-python-headless（更快）⭐⭐
# ═══════════════════════════════════════════════════════════════

"""
優點：
- 比完整版小 50%
- 安裝更快
- 功能完整（僅移除 GUI 相關）

適用場景：
- 不需要 cv2.imshow() 等 GUI 功能
- 僅用於圖片處理和 OCR
- ChroLens_Mimic 完全適用！

步驟：
pip install opencv-python-headless

注意：
- 與 opencv-python 二選一
- 功能幾乎相同，僅缺少視窗顯示
"""

# ═══════════════════════════════════════════════════════════════
# 方案 3: 使用舊版本（穩定）
# ═══════════════════════════════════════════════════════════════

"""
如果最新版失敗，使用經過驗證的舊版本：

pip install opencv-python==4.8.1.78
pip install numpy==1.24.3

優點：
- 穩定性高
- 相容性好
- 功能足夠
"""

# ═══════════════════════════════════════════════════════════════
# 方案 4: 手動下載 wheel 檔
# ═══════════════════════════════════════════════════════════════

"""
如果 pip 安裝失敗，手動下載預編譯檔案：

1. 前往：https://www.lfd.uci.edu/~gohlke/pythonlibs/
2. 搜尋 "opencv"
3. 下載對應版本：
   - Python 3.14 → cp314
   - Windows 64-bit → win_amd64
   例如：opencv_python-4.8.1-cp314-cp314-win_amd64.whl

4. 安裝：
   pip install 下載的檔案.whl
"""

# ═══════════════════════════════════════════════════════════════
# 方案 5: 使用 Conda（如果有）
# ═══════════════════════════════════════════════════════════════

"""
如果您使用 Anaconda/Miniconda：

conda install -c conda-forge opencv

優點：
- 自動處理依賴
- 預編譯版本
- 安裝快速
"""

# ═══════════════════════════════════════════════════════════════
# 推薦方案總結
# ═══════════════════════════════════════════════════════════════

"""
針對 ChroLens_Mimic 專案：

🥇 第一選擇：opencv-python-headless
   pip install opencv-python-headless --only-binary :all:
   
   理由：
   - 不需要 GUI 功能
   - 安裝快（約 30 秒）
   - 檔案小（約 30MB）
   - 功能完整

🥈 第二選擇：opencv-python（預編譯）
   pip install opencv-python --only-binary :all:
   
   理由：
   - 完整功能
   - 預編譯版本快

🥉 第三選擇：舊版本
   pip install opencv-python==4.8.1.78
   
   理由：
   - 穩定可靠
   - 相容性好

❌ 不推薦：從源碼編譯
   - 耗時長（10-30 分鐘）
   - 需要 C++ 編譯器
   - 容易失敗
"""

# ═══════════════════════════════════════════════════════════════
# 修改專案依賴
# ═══════════════════════════════════════════════════════════════

"""
建議修改 install_dependencies.bat 和 check_packages.py：

1. 優先嘗試 opencv-python-headless
2. 失敗後嘗試 opencv-python
3. 都失敗時提示手動安裝

範例代碼：
pip install opencv-python-headless --only-binary :all: || pip install opencv-python==4.8.1.78
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n執行 install_opencv.bat 開始安裝")
