@echo off
REM ===================================================================
REM ChroLens_Mimic Auto Package Tool
REM ===================================================================
chcp 65001 >nul
title ChroLens_Mimic Package Tool
color 0A

echo.
echo ===================================================================
echo    ChroLens_Mimic Auto Package Tool
echo ===================================================================
echo.

REM [Step 1]
echo [1/4] Checking Python Environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Python not found!
    pause
    exit /b 1
)

set ICON_PARAM=
if exist "..\umi_貓.ico" (
    set ICON_PARAM=--icon "..\umi_貓.ico"
)

REM [Step 2]
echo [2/4] Checking cache...
if exist "dist\ChroLens_Mimic" rd /s /q "dist\ChroLens_Mimic"
echo OK: Cleaned old output.

REM [Step 3]
echo [3/4] Running PyInstaller...
echo -------------------------------------------------------------------

if exist "ChroLens_Mimic.spec" goto USE_CACHE
goto FULL_BUILD

:USE_CACHE
echo [INFO] Found spec file, fast mode enabled!
pyinstaller --noconfirm ChroLens_Mimic.spec
goto CHECK_RESULT

:FULL_BUILD
echo [INFO] Full build mode...
set PYST_OPTS=--onedir --windowed --name "ChroLens_Mimic"
set DATA_OPTS=--add-data "images;images" --add-data "TTF;TTF" --add-data "models;models" --add-data "data;data"
if defined ICON_PARAM (
    set DATA_OPTS=%DATA_OPTS% --add-data "..\umi_貓.ico;."
)
set PATH_OPTS=--paths "." --paths "modules"
set HIDDEN_LIBS=--hidden-import "ttkbootstrap" --hidden-import "keyboard" --hidden-import "mouse" --hidden-import "mss" --hidden-import "PIL" --hidden-import "cv2" --hidden-import "numpy" --hidden-import "pystray" --hidden-import "pynput" --hidden-import "pynput.keyboard._win32" --hidden-import "pynput.mouse._win32"
set COLLECT_OPTS=--collect-all "ttkbootstrap" --collect-all "ultralytics" --collect-all "ddddocr" --collect-all "cnocr" --collect-all "onnxruntime" --collect-submodules "pynput"

pyinstaller %PYST_OPTS% %DATA_OPTS% %PATH_OPTS% %HIDDEN_LIBS% %COLLECT_OPTS% --noconfirm %ICON_PARAM% --version-file "version_info.txt" "ChroLens_Mimic.py"

:CHECK_RESULT
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Package failed!
    pause
    exit /b %errorlevel%
)
echo -------------------------------------------------------------------
echo OK: PyInstaller build completed.
echo.

REM [Step 4]
echo [4/4] Starting background ZIP Archive process...
echo -------------------------------------------------------------------
start cmd /c "壓縮.bat"

color 0A
echo.
echo ===================================================================
echo    Package Complete! 
echo ===================================================================
echo Output Directory: dist\
echo.
pause
