@echo off
REM ===================================================================
REM ChroLens_Mimic Package Tool v2.7.6
REM ===================================================================
chcp 65001 >nul
title ChroLens_Mimic Package Tool
color 0A

echo.
echo ===================================================================
echo    ChroLens_Mimic Auto Package Tool v2.7.6
echo ===================================================================
echo.

REM ===================================================================
REM Step 1: Check Python
REM ===================================================================
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERROR: Python not found
    echo Please install Python 3.8+
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo OK: Python %PY_VER%
echo.

REM ===================================================================
REM Step 2: Check PyInstaller
REM ===================================================================
echo [2/5] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERROR: PyInstaller not installed
    echo Please run: pip install pyinstaller
    echo.
    pause
    exit /b 1
)
echo OK: PyInstaller installed
echo.

REM ===================================================================
REM Step 3: Check Files
REM ===================================================================
echo [3/5] Checking files...
set FILE_MISSING=0

if not exist "ChroLens_Mimic.py" (
    echo MISSING: ChroLens_Mimic.py
    set FILE_MISSING=1
) else (
    echo OK: ChroLens_Mimic.py
)

if not exist "recorder.py" (
    echo MISSING: recorder.py
    set FILE_MISSING=1
) else (
    echo OK: recorder.py
)

if not exist "text_script_editor.py" (
    echo MISSING: text_script_editor.py
    set FILE_MISSING=1
) else (
    echo OK: text_script_editor.py
)

if not exist "lang.py" (
    echo MISSING: lang.py
    set FILE_MISSING=1
) else (
    echo OK: lang.py
)

REM Check icon file
if not exist "..\umi_奶茶色.ico" (
    echo WARNING: Icon file not found at ..\umi_奶茶色.ico
    set ICON_PARAM=
) else (
    echo OK: Icon file found
    set ICON_PARAM=--icon "..\umi_奶茶色.ico"
)

if %FILE_MISSING%==1 (
    color 0C
    echo.
    echo ERROR: Missing required files
    echo.
    pause
    exit /b 1
)
echo.

REM ===================================================================
REM Step 4: Clean old build
REM ===================================================================
echo [4/5] Cleaning old build...
if exist "dist" (
    echo Removing dist...
    rmdir /s /q "dist" 2>nul
    if exist "dist" (
        echo WARNING: Cannot fully clean dist
    ) else (
        echo OK: dist cleaned
    )
) else (
    echo OK: dist not exist
)

if exist "build" (
    echo Removing build...
    rmdir /s /q "build" 2>nul
    if exist "build" (
        echo WARNING: Cannot fully clean build
    ) else (
        echo OK: build cleaned
    )
) else (
    echo OK: build not exist
)

if exist "*.spec" (
    echo Removing spec files...
    del /q "*.spec" 2>nul
    echo OK: spec files cleaned
)
echo.

REM ===================================================================
REM Step 5: Run PyInstaller
REM ===================================================================
echo [5/7] Running PyInstaller...
echo -------------------------------------------------------------------

set PYINSTALLER_CMD=pyinstaller --onedir --windowed ^
    --name "ChroLens_Mimic" ^
    --add-data "images;images" ^
    --add-data "TTF;TTF" ^
    --add-data "yolov8s.pt;." ^
    --hidden-import "ttkbootstrap" ^
    --hidden-import "keyboard" ^
    --hidden-import "mouse" ^
    --hidden-import "mss" ^
    --hidden-import "PIL" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "pystray" ^
    --hidden-import "bezier_mouse" ^
    --hidden-import "yolo_detector" ^
    --hidden-import "recorder" ^
    --hidden-import "text_script_editor" ^
    --hidden-import "lang" ^
    --hidden-import "script_io" ^
    --hidden-import "about" ^
    --hidden-import "mini" ^
    --hidden-import "window_selector" ^
    --hidden-import "version_manager" ^
    --hidden-import "version_info_dialog" ^
    --collect-all "ttkbootstrap" ^
    --collect-all "ultralytics" ^
    --noconfirm ^
    "ChroLens_Mimic.py"

if defined ICON_PARAM (
    %PYINSTALLER_CMD% --icon "..\umi_奶茶色.ico" --add-data "..\umi_奶茶色.ico;."
) else (
    %PYINSTALLER_CMD%
)

set PACK_RESULT=%errorlevel%
echo -------------------------------------------------------------------

if %PACK_RESULT% neq 0 (
    color 0C
    echo.
    echo ERROR: Package failed (code: %PACK_RESULT%)
    if exist "*.spec" del /f /q "*.spec"
    pause
    exit /b %PACK_RESULT%
)

REM ===================================================================
REM Step 6: Smoke Test
REM ===================================================================
echo.
echo [6/7] Running Smoke Test...
echo -------------------------------------------------------------------
echo 正在啟動程式進行測試...
start "" "dist\ChroLens_Mimic\ChroLens_Mimic.exe"
echo.
echo 請檢查程式是否正常啟動，並測試基本功能。
echo 確認沒問題後，請【關閉程式】。
echo.
set /p CONFIRM="所有功能運作正常嗎？ (Y/N): "
if /i "%CONFIRM%" neq "Y" (
    color 0E
    echo.
    echo 測試未通過或已取消。保留 build 資料夾以便除錯。
    if exist "*.spec" del /f /q "*.spec"
    pause
    exit /b 1
)

REM ===================================================================
REM Step 7: Packaging and Cleanup
REM ===================================================================
echo.
echo [7/7] Finalizing Package...
echo -------------------------------------------------------------------

echo 1. 清除 build 資料夾與 spec 檔案...
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /f /q "*.spec"

echo 2. 建立 ZIP 壓縮檔...
set ZIP_NAME=ChroLens_Mimic.zip
if exist "dist\%ZIP_NAME%" del /q "dist\%ZIP_NAME%"

powershell -Command "Compress-Archive -Path 'dist\ChroLens_Mimic' -DestinationPath 'dist\%ZIP_NAME%' -Force"

if %errorlevel% neq 0 (
    echo WARNING: ZIP compression failed!
) else (
    echo OK: ZIP created as dist\%ZIP_NAME%
)

REM ===================================================================
REM Done
REM ===================================================================
color 0A
echo.
echo ===================================================================
echo    Package Complete! 🚀
echo ===================================================================
echo.
echo Output Directory: dist\
echo.
echo [Files in dist]
dir /b "dist"
echo.
echo ===================================================================
echo.
pause
