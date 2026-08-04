@echo off
REM ===================================================================
REM ChroLens_Mimic Auto Package Tool (極速版)
REM ===================================================================
chcp 65001 >nul
title ChroLens_Mimic Package Tool
color 0A

echo.
echo ===================================================================
echo    ChroLens_Mimic Auto Package Tool (極速直通版)
echo ===================================================================
echo.

REM [Step 1] 快速檢查環境
echo [1/4] Checking Python Environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Python not found!
    pause
    exit /b 1
)

REM 判斷 Icon
set ICON_PARAM=
if exist "..\umi_奶茶色.ico" (
    set ICON_PARAM=--icon "..\umi_奶茶色.ico" --add-data "..\umi_奶茶色.ico;."
)

REM [Step 2] 快速清理舊檔
echo [2/4] Cleaning old build files...
if exist "dist" rd /s /q "dist"
if exist "*.spec" del /q "*.spec"
echo OK: Cleanup finished.
echo.

REM [Step 3] 執行 PyInstaller 打包
echo [3/4] Running PyInstaller...
echo -------------------------------------------------------------------

set PYST_OPTS=--onedir --windowed --name "ChroLens_Mimic"
set DATA_OPTS=--add-data "images;images" --add-data "TTF;TTF" --add-data "models;models" --add-data "data;data"
set PATH_OPTS=--paths "." --paths "modules"

REM 只保留真正必要的隱藏模組 (外部動態加載的函式庫)
set HIDDEN_LIBS=--hidden-import "ttkbootstrap" --hidden-import "keyboard" --hidden-import "mouse" --hidden-import "mss" --hidden-import "PIL" --hidden-import "cv2" --hidden-import "numpy" --hidden-import "pystray" --hidden-import "pynput" --hidden-import "pynput.keyboard._win32" --hidden-import "pynput.mouse._win32"
REM 保留巨大 AI 模組的 collect-all 以保證運作正常
set COLLECT_OPTS=--collect-all "ttkbootstrap" --collect-all "ultralytics" --collect-all "ddddocr" --collect-all "cnocr" --collect-all "onnxruntime" --collect-submodules "pynput"

pyinstaller %PYST_OPTS% %DATA_OPTS% %PATH_OPTS% %HIDDEN_LIBS% %COLLECT_OPTS% --noconfirm %ICON_PARAM% --version-file "version_info.txt" "ChroLens_Mimic.py"

if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Package failed!
    pause
    exit /b %errorlevel%
)
echo -------------------------------------------------------------------
echo OK: PyInstaller build completed.
echo.

REM [Step 4] 極速 ZIP 壓縮
echo [4/4] Creating ZIP Archive...
echo -------------------------------------------------------------------

REM 透過 PowerShell 的 .NET 原生函式庫 (System.IO.Compression) 進行極速壓縮
set ZIP_NAME=ChroLens_Mimic.zip
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; $src = Join-Path (Get-Location).Path 'dist\ChroLens_Mimic'; $dst = Join-Path (Get-Location).Path 'dist\%ZIP_NAME%'; if (Test-Path $dst) { Remove-Item $dst -Force }; [System.IO.Compression.ZipFile]::CreateFromDirectory($src, $dst, [System.IO.Compression.CompressionLevel]::Fastest, $false); Write-Host 'ZIP created successfully at dist\%ZIP_NAME%' -ForegroundColor Green"

REM 順手清一下多餘的 spec
if exist "*.spec" del /q "*.spec"

color 0A
echo.
echo ===================================================================
echo    Package Complete! 🚀
echo ===================================================================
echo Output Directory: dist\
echo.
pause
