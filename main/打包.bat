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
echo [5/5] Running PyInstaller...
echo -------------------------------------------------------------------

REM Check if icon exists and build command accordingly
if defined ICON_PARAM (
    pyinstaller --onedir --windowed ^
        --name "ChroLens_Mimic" ^
        %ICON_PARAM% ^
        --add-data "..\umi_奶茶色.ico;." ^
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
        --collect-all "ttkbootstrap" ^
        --collect-all "ultralytics" ^
        --noconfirm ^
        "ChroLens_Mimic.py"
) else (
    pyinstaller --onedir --windowed ^
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
        --collect-all "ttkbootstrap" ^
        --collect-all "ultralytics" ^
        --noconfirm ^
        "ChroLens_Mimic.py"
)

set PACK_RESULT=%errorlevel%
echo -------------------------------------------------------------------

if %PACK_RESULT% neq 0 (
    color 0C
    echo.
    echo ERROR: Package failed (code: %PACK_RESULT%)
    echo Please check error messages above
    echo.
    pause
    exit /b %PACK_RESULT%
)
echo.

REM ===================================================================
REM Verify
REM ===================================================================
echo Verifying...

if not exist "dist\ChroLens_Mimic" (
    color 0C
    echo ERROR: Output directory not found
    pause
    exit /b 1
)
echo OK: Output directory exists

if not exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
    color 0C
    echo ERROR: Executable not found
    pause
    exit /b 1
)
echo OK: Executable exists
echo.

REM ===================================================================
REM Done
REM ===================================================================
color 0A
echo ===================================================================
echo    Package Complete!
echo ===================================================================
echo.
echo Output: dist\ChroLens_Mimic\
echo.
echo Test Steps:
echo    1. Run dist\ChroLens_Mimic\ChroLens_Mimic.exe
echo    2. Test recording and playback
echo    3. Test script merge feature
echo.
echo Release Steps:
echo    1. Test all features
echo    2. Compress dist\ChroLens_Mimic\ to ZIP
echo    3. Commit to GitHub
echo    4. Create new Release and upload ZIP
echo.
echo ===================================================================
echo.
pause
