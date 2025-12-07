@echo off
chcp 65001 >nul
title ChroLens_Mimic 打包工具 v2.7.3
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ChroLens_Mimic 自動打包工具 v2.7.3
echo    更新機制: 延遲更新 (方案3 - 啟動時自動安裝)
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 步驟 1: 環境檢查
REM ═══════════════════════════════════════════════════════════════════════════
echo [1/6] 檢查 Python 環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ❌ 錯誤：找不到 Python
    echo    請確認 Python 3.8+ 已安裝並加入系統 PATH
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo ✓ Python %PY_VER% 已就緒
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 步驟 2: 模組檢查
REM ═══════════════════════════════════════════════════════════════════════════
echo [2/6] 檢查必要模組...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ❌ 錯誤：PyInstaller 未安裝
    echo    請執行: pip install pyinstaller
    echo.
    pause
    exit /b 1
)
echo ✓ PyInstaller 已安裝
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 步驟 3: 專案檔案檢查
REM ═══════════════════════════════════════════════════════════════════════════
echo [3/6] 檢查專案檔案完整性...
set FILE_MISSING=0

if not exist "ChroLens_Mimic.py" (
    echo ❌ 主程式: ChroLens_Mimic.py
    set FILE_MISSING=1
) else (
    echo ✓ 主程式: ChroLens_Mimic.py
)

if not exist "update_manager.py" (
    echo ❌ 更新管理器: update_manager.py
    set FILE_MISSING=1
) else (
    echo ✓ 更新管理器: update_manager.py
)

if not exist "update_manager_v2_deferred.py" (
    echo ❌ 延遲更新模組: update_manager_v2_deferred.py
    set FILE_MISSING=1
) else (
    echo ✓ 延遲更新模組: update_manager_v2_deferred.py
)

if not exist "update_dialog.py" (
    echo ❌ 更新對話框: update_dialog.py
    set FILE_MISSING=1
) else (
    echo ✓ 更新對話框: update_dialog.py
)

if not exist "pack_safe.py" (
    echo ❌ 打包腳本: pack_safe.py
    set FILE_MISSING=1
) else (
    echo ✓ 打包腳本: pack_safe.py
)

if not exist "recorder.py" (
    echo ❌ 錄製模組: recorder.py
    set FILE_MISSING=1
) else (
    echo ✓ 錄製模組: recorder.py
)

if not exist "text_script_editor.py" (
    echo ❌ 編輯器模組: text_script_editor.py
    set FILE_MISSING=1
) else (
    echo ✓ 編輯器模組: text_script_editor.py
)

if %FILE_MISSING%==1 (
    color 0C
    echo.
    echo ❌ 檔案檢查失敗：有關鍵檔案遺失
    echo.
    pause
    exit /b 1
)
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 步驟 4: 清理舊產物
REM ═══════════════════════════════════════════════════════════════════════════
echo [4/6] 清理舊打包產物...
if exist "dist" (
    echo    正在刪除 dist 目錄...
    rmdir /s /q "dist" 2>nul
    if exist "dist" (
        echo    ⚠️  無法完全清理 dist 目錄（可能有檔案被佔用）
    ) else (
        echo    ✓ 已清理 dist 目錄
    )
) else (
    echo    ✓ dist 目錄不存在，無需清理
)

if exist "build" (
    echo    正在刪除 build 目錄...
    rmdir /s /q "build" 2>nul
    if exist "build" (
        echo    ⚠️  無法完全清理 build 目錄
    ) else (
        echo    ✓ 已清理 build 目錄
    )
) else (
    echo    ✓ build 目錄不存在，無需清理
)

if exist "*.spec" (
    echo    正在刪除舊的 .spec 檔案...
    del /q "*.spec" 2>nul
    echo    ✓ 已清理 .spec 檔案
)
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 步驟 5: 執行打包
REM ═══════════════════════════════════════════════════════════════════════════
echo [5/6] 開始執行 PyInstaller 打包...
echo ───────────────────────────────────────────────────────────────────────────
python pack_safe.py
set PACK_RESULT=%errorlevel%
echo ───────────────────────────────────────────────────────────────────────────

if %PACK_RESULT% neq 0 (
    color 0C
    echo.
    echo ❌ 打包過程失敗 (錯誤碼: %PACK_RESULT%)
    echo    請檢查上方輸出的錯誤訊息
    echo.
    pause
    exit /b %PACK_RESULT%
)
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 步驟 6: 驗證打包結果
REM ═══════════════════════════════════════════════════════════════════════════
echo [6/6] 驗證打包產物...

if not exist "dist\ChroLens_Mimic" (
    color 0C
    echo ❌ 找不到輸出目錄: dist\ChroLens_Mimic
    pause
    exit /b 1
)
echo ✓ 輸出目錄存在: dist\ChroLens_Mimic

if not exist "dist\ChroLens_Mimic\ChroLens_Mimic.exe" (
    color 0C
    echo ❌ 找不到主執行檔: ChroLens_Mimic.exe
    pause
    exit /b 1
)
echo ✓ 主執行檔存在: ChroLens_Mimic.exe

REM 檢查延遲更新模組
if not exist "dist\ChroLens_Mimic\update_manager_v2_deferred.pyc" (
    if not exist "dist\ChroLens_Mimic\_internal\update_manager_v2_deferred.pyc" (
        color 0E
        echo ⚠️  警告: 找不到延遲更新模組 (.pyc 檔案)
        echo    延遲更新功能可能無法正常運作
    ) else (
        echo ✓ 延遲更新模組: update_manager_v2_deferred.pyc (在 _internal)
    )
) else (
    echo ✓ 延遲更新模組: update_manager_v2_deferred.pyc
)

REM 檢查 ZIP 壓縮檔
for %%f in (dist\ChroLens_Mimic_*.zip) do (
    set ZIP_FILE=%%~nxf
    set ZIP_SIZE=%%~zf
)
if defined ZIP_FILE (
    echo ✓ ZIP 壓縮檔: %ZIP_FILE%
) else (
    color 0E
    echo ⚠️  警告: 找不到 ZIP 壓縮檔
    echo    您可能需要手動壓縮 dist\ChroLens_Mimic 目錄
)
echo.

REM ═══════════════════════════════════════════════════════════════════════════
REM 完成訊息
REM ═══════════════════════════════════════════════════════════════════════════
color 0A
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ✅ 打包完成！
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo 📁 輸出位置:
echo    主目錄: dist\ChroLens_Mimic\
echo    執行檔: dist\ChroLens_Mimic\ChroLens_Mimic.exe
if defined ZIP_FILE (
    echo    壓縮檔: dist\%ZIP_FILE%
)
echo.
echo 📌 更新機制說明 (方案3 - 延遲更新):
echo    ┌────────────────────────────────────────────────────────────────────┐
echo    │ 1. 程式檢測到新版本時，下載更新檔案                               │
echo    │ 2. 標記為「待處理更新」(pending_update.json)                       │
echo    │ 3. 提示用戶關閉程式                                                │
echo    │ 4. 下次啟動時，程式自動安裝更新（此時無檔案鎖）                   │
echo    │ 5. 更新完成後正常啟動程式                                          │
echo    └────────────────────────────────────────────────────────────────────┘
echo.
echo 🧪 測試建議:
echo    1. 執行 dist\ChroLens_Mimic\ChroLens_Mimic.exe 確認正常啟動
echo    2. 測試基本功能（錄製、播放、編輯器）
echo    3. 測試更新功能（需要 GitHub Release 配合）
echo.
echo 🚀 發布流程:
echo    1. 測試打包產物功能完整性
echo    2. 更新 CHANGELOG.md 和 docs/index.html
echo    3. 提交程式碼到 GitHub
echo    4. 建立新 Release 並上傳 ZIP 檔案
echo    5. 填寫版本說明並發布
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
