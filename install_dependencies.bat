@echo off
chcp 65001 >nul
title ChroLens_Mimic 依賴安裝程式

echo ═══════════════════════════════════════════════════════════════
echo              ChroLens_Mimic 依賴模組一鍵安裝
echo ═══════════════════════════════════════════════════════════════
echo.

:: 檢查 Python 是否已安裝
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未偵測到 Python！
    echo.
    echo 請先安裝 Python：
    echo 1. 前往 https://www.python.org/downloads/
    echo 2. 下載並安裝 Python 3.10 或 3.11
    echo 3. 安裝時務必勾選 "Add Python to PATH"
    echo 4. 安裝完成後重新執行此腳本
    echo.
    pause
    exit /b 1
)

echo [✓] Python 已安裝
python --version
echo.

:: 升級 pip
echo [1/3] 升級 pip...
python -m pip install --upgrade pip
echo.

:: 安裝所有依賴模組
echo [2/3] 安裝依賴模組...
echo.

pip install ttkbootstrap
pip install keyboard
pip install mouse
pip install pynput
pip install pywin32
pip install pillow
pip install pystray
pip install opencv-python
pip install numpy
pip install mss
pip install pyglet
pip install packaging

:: pywin32 需要額外的後安裝步驟
echo.
echo [2.5/3] 執行 pywin32 後安裝設定...
python -m pywin32_postinstall -install 2>nul

echo.
echo [3/3] 驗證安裝...
echo.

python -c "import ttkbootstrap; print('[✓] ttkbootstrap')"
python -c "import keyboard; print('[✓] keyboard')"
python -c "import mouse; print('[✓] mouse')"
python -c "import pynput; print('[✓] pynput')"
python -c "import win32api; print('[✓] pywin32 (win32api)')"
python -c "import PIL; print('[✓] pillow (PIL)')"
python -c "import pystray; print('[✓] pystray')"
python -c "import cv2; print('[✓] opencv-python (cv2)')"
python -c "import numpy; print('[✓] numpy')"
python -c "import mss; print('[✓] mss')"
python -c "import pyglet; print('[✓] pyglet')"
python -c "import packaging; print('[✓] packaging')"

echo.
echo ═══════════════════════════════════════════════════════════════
echo                    安裝完成！
echo ═══════════════════════════════════════════════════════════════
echo.
echo 提示：建議以管理員身份執行程式以確保錄製功能正常
echo.

set /p run_now="是否立即啟動 ChroLens_Mimic？(Y/N): "
if /i "%run_now%"=="Y" (
    cd /d "%~dp0main"
    python ChroLens_Mimic.py
)

pause
