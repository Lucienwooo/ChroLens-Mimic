@echo off
chcp 65001 >nul
title OpenCV-Python 快速安裝工具

echo ═══════════════════════════════════════════════════════════════
echo          OpenCV-Python 快速安裝工具（優化版）
echo ═══════════════════════════════════════════════════════════════
echo.

:: 方案 1: 使用預編譯的 wheel 檔（最快）
echo [方案 1] 嘗試使用預編譯 wheel 安裝...
echo.

:: 先升級 pip
python -m pip install --upgrade pip

:: 安裝預編譯的 numpy（避免編譯）
echo 正在安裝預編譯的 numpy...
pip install numpy --only-binary :all:

if %errorlevel% equ 0 (
    echo [✓] numpy 安裝成功
) else (
    echo [✗] numpy 安裝失敗，嘗試備用方案...
    :: 備用：使用較舊但穩定的版本
    pip install numpy==1.24.3
)

:: 安裝 opencv-python（使用預編譯版本）
echo.
echo 正在安裝 opencv-python...
pip install opencv-python --only-binary :all:

if %errorlevel% equ 0 (
    echo [✓] opencv-python 安裝成功
    goto verify
)

:: 方案 2: 使用 headless 版本（更小、更快）
echo.
echo [方案 2] 嘗試安裝 opencv-python-headless（無 GUI 版本）...
pip install opencv-python-headless --only-binary :all:

if %errorlevel% equ 0 (
    echo [✓] opencv-python-headless 安裝成功
    goto verify
)

:: 方案 3: 使用較舊但穩定的版本
echo.
echo [方案 3] 嘗試安裝穩定版本 opencv-python 4.8.1...
pip install opencv-python==4.8.1.78

if %errorlevel% equ 0 (
    echo [✓] opencv-python 4.8.1 安裝成功
    goto verify
)

:: 方案 4: 終極方案 - 使用 conda（如果有）
echo.
echo [方案 4] 檢查是否有 conda...
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo 發現 conda，使用 conda 安裝...
    conda install -c conda-forge opencv -y
    goto verify
)

echo.
echo [✗] 所有安裝方案都失敗了
echo.
echo 建議手動安裝：
echo 1. 下載預編譯 wheel: https://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv
echo 2. 執行: pip install 下載的檔案.whl
echo.
pause
exit /b 1

:verify
echo.
echo ═══════════════════════════════════════════════════════════════
echo                    驗證安裝
echo ═══════════════════════════════════════════════════════════════
echo.

python -c "import cv2; print('[✓] OpenCV 版本:', cv2.__version__)"
python -c "import numpy; print('[✓] NumPy 版本:', numpy.__version__)"

if %errorlevel% equ 0 (
    echo.
    echo ═══════════════════════════════════════════════════════════════
    echo                 安裝成功！
    echo ═══════════════════════════════════════════════════════════════
) else (
    echo.
    echo [✗] 驗證失敗，請檢查安裝
)

echo.
pause
