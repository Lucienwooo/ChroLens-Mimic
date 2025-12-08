@echo off
chcp 65001 >nul
echo ========================================
echo ChroLens_Mimic 自動打包與發布工具
echo ========================================
echo.

REM 切換到腳本所在目錄
cd /d "%~dp0"

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤: 找不到 Python
    pause
    exit /b 1
)

REM 檢查並安裝必要套件
echo 檢查必要套件...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安裝 PyInstaller...
    pip install pyinstaller
)

python -c "import github" >nul 2>&1
if errorlevel 1 (
    echo 正在安裝 PyGithub...
    pip install PyGithub
)

REM 清理測試檔案
echo.
echo 清理測試檔案...
del /F /Q *_test.py >nul 2>&1
del /F /Q test_*.py >nul 2>&1
del /F /Q diagnose_*.py >nul 2>&1
del /F /Q TEST_*.md >nul 2>&1
del /F /Q REPAIR_*.md >nul 2>&1
del /F /Q *_NOTES.md >nul 2>&1
del /F /Q *_GUIDE.md >nul 2>&1
echo ✓ 測試檔案已清理

echo.
echo 開始打包與發布...
echo.

REM 執行打包腳本
python build_and_release.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo 執行失敗
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo 完成！
echo ========================================
pause
