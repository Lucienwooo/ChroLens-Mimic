@echo off
chcp 65001 >nul
title ChroLens_Mimic 打包工具 v2.7.3
color 0A

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ChroLens_Mimic 自動打包工具 v2.7.3
echo    更新機制: GitHub Releases + 批次腳本更新
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

if not exist "version_manager.py" (
    echo ❌ 版本管理器: version_manager.py
    set FILE_MISSING=1
) else (
    echo ✓ 版本管理器: version_manager.py
)

if not exist "version_info_dialog.py" (
    echo ❌ 版本資訊對話框: version_info_dialog.py
    set FILE_MISSING=1
) else (
    echo ✓ 版本資訊對話框: version_info_dialog.py
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
REM 步驟 5.5: 複製更新工具（給舊版用戶使用）
REM ═══════════════════════════════════════════════════════════════════════════
echo [5.5/6] 複製更新工具到輸出目錄...

if exist "manual_update.bat" (
    copy /Y "manual_update.bat" "dist\ChroLens_Mimic\manual_update.bat" >nul
    echo ✓ 已複製: manual_update.bat
) else (
    echo ⚠️  找不到: manual_update.bat
)

if exist "更新說明.txt" (
    copy /Y "更新說明.txt" "dist\ChroLens_Mimic\更新說明.txt" >nul
    echo ✓ 已複製: 更新說明.txt
) else (
    echo ⚠️  找不到: 更新說明.txt
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

REM 檢查版本管理模組
if not exist "dist\ChroLens_Mimic\version_manager.pyc" (
    if not exist "dist\ChroLens_Mimic\_internal\version_manager.pyc" (
        color 0E
        echo ⚠️  警告: 找不到版本管理模組 (.pyc 檔案)
        echo    版本更新功能可能無法正常運作
    ) else (
        echo ✓ 版本管理模組: version_manager.pyc (在 _internal)
    )
) else (
    echo ✓ 版本管理模組: version_manager.pyc
)

REM 檢查版本資訊對話框
if not exist "dist\ChroLens_Mimic\version_info_dialog.pyc" (
    if not exist "dist\ChroLens_Mimic\_internal\version_info_dialog.pyc" (
        color 0E
        echo ⚠️  警告: 找不到版本資訊對話框模組
    ) else (
        echo ✓ 版本資訊對話框: version_info_dialog.pyc (在 _internal)
    )
) else (
    echo ✓ 版本資訊對話框: version_info_dialog.pyc
)

REM 檢查更新工具檔案
if exist "dist\ChroLens_Mimic\manual_update.bat" (
    echo ✓ 更新工具: manual_update.bat
) else (
    color 0E
    echo ⚠️  警告: 找不到更新工具: manual_update.bat
    echo    舊版用戶將無法使用自動更新工具
)

if exist "dist\ChroLens_Mimic\更新說明.txt" (
    echo ✓ 更新說明: 更新說明.txt
) else (
    color 0E
    echo ⚠️  警告: 找不到更新說明: 更新說明.txt
)
    echo ✓ 版本資訊對話框: version_info_dialog.pyc
)f defined ZIP_FILE (
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
echo 📌 更新機制說明 (GitHub Releases + 批次腳本):
echo    ┌────────────────────────────────────────────────────────────────────┐
echo    │ 【使用者操作流程】                                                 │
echo    │ 1. 點擊「版本資訊」按鈕 → 自動檢查 GitHub Releases                │
echo    │ 2. 發現新版本 → 點擊「立即更新」                                  │
echo    │ 3. 下載 .zip 檔案（顯示進度條）                                   │
echo    │ 4. 解壓縮並創建批次更新腳本                                       │
echo    │ 5. 程式自動關閉 → 批次腳本執行更新                                │
echo    │ 6. 更新完成後自動重啟新版本                                       │
echo    │                                                                    │
echo    │ 【技術實作】                                                       │
echo    │ • API: https://api.github.com/repos/Lucienwooo/                   │
echo    │        ChroLens-Mimic/releases/latest                              │
echo    │ • 版本比較: packaging 庫 (PEP 440)                                │
echo    │ • 更新方式: 批次腳本 (避免檔案鎖定)                               │
echo    │ • 自動備份: backup\ 目錄                                          │
echo    └────────────────────────────────────────────────────────────────────┘
echo.
echo 🧪 測試建議:
echo    1. 執行 dist\ChroLens_Mimic\ChroLens_Mimic.exe 確認正常啟動
echo    2. 測試基本功能（錄製、播放、編輯器、OCR）
echo    3. 點擊「版本資訊」檢查是否能連接 GitHub API
echo    4. 測試完整更新流程（需先發布 GitHub Release）
echo.
echo 🚀 發布新版本流程:
echo    【步驟 1】本地準備
echo       a) 更新 ChroLens_Mimic.py 中的 VERSION = "2.7.x"
echo       b) 執行本打包腳本 (打包.bat)
echo       c) 測試 dist\ChroLens_Mimic\ChroLens_Mimic.exe 所有功能
echo.
echo    【步驟 2】GitHub 發布
echo       a) 提交程式碼: git add . ^&^& git commit -m "v2.7.x"
echo       b) 推送到 GitHub: git push origin main
echo       c) 前往 GitHub → Releases → Create a new release
echo          • Tag version: v2.7.x
echo          • Release title: ChroLens_Mimic v2.7.x
echo          • Description: 詳細更新說明
echo          • 上傳 dist\ChroLens_Mimic_v2.7.x.zip
echo       d) 點擊「Publish release」
echo.
echo    【步驟 3】ZIP 檔案結構
echo       ChroLens_Mimic_v2.7.x.zip
echo       └── (打包 dist\ChroLens_Mimic\ 整個目錄)
echo           ├── ChroLens_Mimic.exe
echo           ├── _internal\       (所有依賴檔案)
echo           ├── images\
echo           ├── TTF\
echo           └── 其他資源檔案
echo.
echo    【步驟 4】更新官網 (可選)
echo       • 更新 docs/index.html 的更新日誌區塊
echo       • 或直接使用 GitHub Releases 的發布說明─────────────────────────────────────────────────────────┘
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
