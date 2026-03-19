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

REM ===================================================================
REM Step 1: Check Python and PyInstaller
REM ===================================================================
echo [1/6] Checking Python and PyInstaller...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: PyInstaller not installed. Please run: pip install pyinstaller
    pause
    exit /b 1
)
echo OK: Python and PyInstaller are ready.
echo.

REM ===================================================================
REM Step 2: Check Required Files
REM ===================================================================
echo [2/6] Checking required files...
set FILE_MISSING=0
for %%f in (ChroLens_Mimic.py modules\recorder.py modules\text_script_editor.py modules\lang.py) do (
    if not exist "%%f" (
        echo MISSING: %%f
        set FILE_MISSING=1
    ) else (
        echo OK: %%f
    )
)

if not exist "..\umi_奶茶色.ico" (
    echo WARNING: Icon file not found at ..\umi_奶茶色.ico
    set ICON_PARAM=
) else (
    echo OK: Icon file found
    set ICON_PARAM=--icon "..\umi_奶茶色.ico" --add-data "..\umi_奶茶色.ico;."
)

if "%FILE_MISSING%"=="1" (
    color 0C
    echo ERROR: Missing required files
    pause
    exit /b 1
)
echo.

REM ===================================================================
REM Step 3: Clean old build files
REM ===================================================================
echo [3/6] Cleaning old build files...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item -Path 'build' -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path 'dist' -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path '*.spec' -Force -ErrorAction SilentlyContinue"
echo OK: Cleanup finished.
echo.

REM ===================================================================
REM Step 4: Run PyInstaller
REM ===================================================================
echo [4/6] Running PyInstaller...
echo -------------------------------------------------------------------
set PYINSTALLER_CMD=pyinstaller --onedir --windowed --name "ChroLens_Mimic" --add-data "images;images" --add-data "TTF;TTF" --add-data "models;models" --add-data "data;data" --hidden-import "ttkbootstrap" --hidden-import "keyboard" --hidden-import "mouse" --hidden-import "mss" --hidden-import "PIL" --hidden-import "cv2" --hidden-import "numpy" --hidden-import "pystray" --hidden-import "bezier_mouse" --hidden-import "yolo_detector" --hidden-import "recorder" --hidden-import "text_script_editor" --hidden-import "lang" --hidden-import "script_io" --hidden-import "about" --hidden-import "mini" --hidden-import "pynput_hotkey" --hidden-import "window_selector" --hidden-import "version_manager" --hidden-import "version_info_dialog" --collect-all "ttkbootstrap" --collect-all "ultralytics" --noconfirm %ICON_PARAM% "ChroLens_Mimic.py"

%PYINSTALLER_CMD%

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERROR: Package failed (code: %errorlevel%)
    pause
    exit /b %errorlevel%
)
echo -------------------------------------------------------------------
echo.

REM ===================================================================
REM Step 5: Smoke Test
REM ===================================================================
echo [5/6] Running Smoke Test...
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
    pause
    exit /b 1
)

REM ===================================================================
REM Step 6: Finalizing Package (Zip and Cleanup)
REM ===================================================================
echo.
echo.
echo [6/6] Finalizing Package (Zip and Cleanup)...
echo -------------------------------------------------------------------
echo 1. 建立 ZIP 壓縮檔...

REM 使用獨立 PowerShell 腳本避免 CMD 變數衝突
set PS_TEMP=%TEMP%\pack_zip_%RANDOM%.ps1
echo $ErrorActionPreference = 'Stop' > "%PS_TEMP%"
echo $content = Get-Content '.\ChroLens_Mimic.py' -Raw >> "%PS_TEMP%"
echo if ($content -match 'VERSION\s*=\s*"([^"]+)"') { $ver = $Matches[1] } else { $ver = 'Unknown' } >> "%PS_TEMP%"
echo $zipName = 'ChroLens_Mimic_v' + $ver + '.zip' >> "%PS_TEMP%"
echo Write-Host ('打包版本: v' + $ver) -ForegroundColor Cyan >> "%PS_TEMP%"
echo $currentDir = Get-Location >> "%PS_TEMP%"
echo $src = Join-Path $currentDir 'dist\ChroLens_Mimic' >> "%PS_TEMP%"
echo $dst = Join-Path $currentDir ('dist\' + $zipName) >> "%PS_TEMP%"
echo if (Test-Path $dst) { Remove-Item $dst -Force } >> "%PS_TEMP%"
echo Write-Host ('正在壓縮 ' + $src + ' 到 ' + $dst + ' ...') >> "%PS_TEMP%"
echo Compress-Archive -Path ($src + '\*') -DestinationPath $dst -Force >> "%PS_TEMP%"
echo if (Test-Path $dst) { Write-Host ('OK: ZIP created at dist\' + $zipName) -ForegroundColor Green } else { Write-Error 'ZIP creation failed' } >> "%PS_TEMP%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_TEMP%"
del "%PS_TEMP%" 2>nul

echo 2. 清除 build 資料夾與 spec 檔案...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item -Path 'build' -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path '*.spec' -Force -ErrorAction SilentlyContinue"
if exist "build" (
    echo WARNING: build folder still exists after final cleanup!
) else (
    echo OK: No build artifacts remaining
)

color 0A
echo.
echo ===================================================================
echo    Package Complete! 🚀
echo ===================================================================
echo.
echo Output Directory: dist\
echo [Files in dist]
dir /b "dist"
echo.
echo ===================================================================
echo.
pause
