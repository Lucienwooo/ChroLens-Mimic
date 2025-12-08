@echo off
chcp 65001 >nul
title ChroLens_Mimic 手動更新工具
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ChroLens_Mimic 手動更新工具
echo    適用於從舊版本（2.7.1 及以前）升級到 2.7.2
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo 【重要說明】
echo.
echo 此工具適用於以下情況：
echo   1. 您目前使用的是 ChroLens_Mimic 2.7.1 或更早版本
echo   2. 您想升級到 2.7.2 版本
echo   3. 您的舊版本沒有「版本資訊」自動更新功能
echo.
echo 【使用方式】
echo   1. 將整個 2.7.2 版本資料夾複製到您要更新的舊版本目錄旁邊
echo   2. 關閉舊版本的 ChroLens_Mimic 程式
echo   3. 執行此批次檔
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM 獲取使用者確認
:confirm
set /p CONFIRM="是否要繼續更新？(Y/N): "
if /i "%CONFIRM%"=="Y" goto :start_update
if /i "%CONFIRM%"=="N" goto :cancel
echo 請輸入 Y 或 N
goto :confirm

:cancel
echo.
echo 已取消更新
pause
exit /b 0

:start_update
echo.
echo ───────────────────────────────────────────────────────────────────────────
echo [步驟 1/6] 偵測環境
echo ───────────────────────────────────────────────────────────────────────────

REM 設定路徑
set "NEW_VERSION_DIR=%~dp0"
set "NEW_VERSION_DIR=%NEW_VERSION_DIR:~0,-1%"

echo 新版本位置: %NEW_VERSION_DIR%
echo.

REM 請使用者指定舊版本目錄
echo 請輸入舊版本 ChroLens_Mimic 的完整路徑
echo （例如: C:\Program Files\ChroLens_Mimic）
echo.
set /p OLD_VERSION_DIR="舊版本路徑: "

REM 移除結尾的反斜線
if "%OLD_VERSION_DIR:~-1%"=="\" set "OLD_VERSION_DIR=%OLD_VERSION_DIR:~0,-1%"

echo.
echo 舊版本位置: %OLD_VERSION_DIR%
echo.

REM 驗證路徑
if not exist "%OLD_VERSION_DIR%" (
    color 0C
    echo ❌ 錯誤: 找不到指定的舊版本目錄
    echo.
    pause
    exit /b 1
)

if not exist "%OLD_VERSION_DIR%\ChroLens_Mimic.exe" (
    color 0C
    echo ❌ 錯誤: 指定的目錄中找不到 ChroLens_Mimic.exe
    echo    請確認路徑是否正確
    echo.
    pause
    exit /b 1
)

echo ✓ 路徑驗證成功
echo.

REM 檢查程式是否還在執行
echo 正在檢查舊版本程式是否還在執行...
tasklist /FI "IMAGENAME eq ChroLens_Mimic.exe" 2>NUL | find /I /N "ChroLens_Mimic.exe">NUL
if "%ERRORLEVEL%"=="0" (
    color 0E
    echo.
    echo ⚠️  警告: 偵測到 ChroLens_Mimic.exe 正在執行
    echo.
    echo 請先關閉程式後再繼續
    echo 關閉程式後按任意鍵繼續...
    pause >nul
    
    REM 再次檢查
    tasklist /FI "IMAGENAME eq ChroLens_Mimic.exe" 2>NUL | find /I /N "ChroLens_Mimic.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        color 0C
        echo.
        echo ❌ 程式仍在執行中，無法繼續更新
        echo    請完全關閉 ChroLens_Mimic 後重新執行此批次檔
        echo.
        pause
        exit /b 1
    )
)
echo ✓ 程式未執行，可以安全更新
echo.

REM 最後確認
echo ───────────────────────────────────────────────────────────────────────────
echo [確認資訊]
echo ───────────────────────────────────────────────────────────────────────────
echo.
echo 新版本來源: %NEW_VERSION_DIR%
echo 舊版本目標: %OLD_VERSION_DIR%
echo.
echo ⚠️  此操作將會：
echo    1. 備份您的舊版本到 backup\ 目錄
echo    2. 刪除舊版本的過時檔案
echo    3. 將新版本檔案複製到舊版本目錄
echo    4. 保留您的使用者資料（腳本檔案等）
echo.
set /p FINAL_CONFIRM="確定要執行更新嗎？(Y/N): "
if /i not "%FINAL_CONFIRM%"=="Y" (
    echo.
    echo 已取消更新
    pause
    exit /b 0
)

echo.
echo ───────────────────────────────────────────────────────────────────────────
echo [步驟 2/6] 備份舊版本
echo ───────────────────────────────────────────────────────────────────────────

REM 創建備份目錄（使用時間戳）
set "BACKUP_DIR=%OLD_VERSION_DIR%\backup\backup_before_2.7.2_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_DIR=%BACKUP_DIR: =0%"

echo 正在創建備份目錄...
if not exist "%OLD_VERSION_DIR%\backup" mkdir "%OLD_VERSION_DIR%\backup"
mkdir "%BACKUP_DIR%"
echo ✓ 備份目錄已創建: %BACKUP_DIR%

echo.
echo 正在備份檔案...
echo （這可能需要一些時間，請耐心等待）
xcopy /E /I /Y /Q "%OLD_VERSION_DIR%\*" "%BACKUP_DIR%\" >nul 2>&1
echo ✓ 備份完成
echo.

echo ───────────────────────────────────────────────────────────────────────────
echo [步驟 3/6] 清理舊版本檔案
echo ───────────────────────────────────────────────────────────────────────────

echo 正在刪除舊版本的過時檔案...

REM 刪除舊版本更新相關檔案
if exist "%OLD_VERSION_DIR%\_internal\update_manager.pyc" (
    del /f /q "%OLD_VERSION_DIR%\_internal\update_manager.pyc" >nul 2>&1
    echo ✓ 已刪除: _internal\update_manager.pyc
)
if exist "%OLD_VERSION_DIR%\_internal\update_manager_v2_deferred.pyc" (
    del /f /q "%OLD_VERSION_DIR%\_internal\update_manager_v2_deferred.pyc" >nul 2>&1
    echo ✓ 已刪除: _internal\update_manager_v2_deferred.pyc
)
if exist "%OLD_VERSION_DIR%\_internal\update_dialog.pyc" (
    del /f /q "%OLD_VERSION_DIR%\_internal\update_dialog.pyc" >nul 2>&1
    echo ✓ 已刪除: _internal\update_dialog.pyc
)
if exist "%OLD_VERSION_DIR%\update_manager.pyc" (
    del /f /q "%OLD_VERSION_DIR%\update_manager.pyc" >nul 2>&1
    echo ✓ 已刪除: update_manager.pyc
)
if exist "%OLD_VERSION_DIR%\update_manager_v2_deferred.pyc" (
    del /f /q "%OLD_VERSION_DIR%\update_manager_v2_deferred.pyc" >nul 2>&1
    echo ✓ 已刪除: update_manager_v2_deferred.pyc
)
if exist "%OLD_VERSION_DIR%\update_dialog.pyc" (
    del /f /q "%OLD_VERSION_DIR%\update_dialog.pyc" >nul 2>&1
    echo ✓ 已刪除: update_dialog.pyc
)

echo ✓ 清理完成
echo.

echo ───────────────────────────────────────────────────────────────────────────
echo [步驟 4/6] 複製新版本檔案
echo ───────────────────────────────────────────────────────────────────────────

echo 正在複製新版本檔案...
echo （這可能需要一些時間，請耐心等待）

REM 複製所有檔案（排除 backup 和此批次檔本身）
xcopy /E /I /Y /Q "%NEW_VERSION_DIR%\*" "%OLD_VERSION_DIR%\" /EXCLUDE:%~f0+nul >nul 2>&1

echo ✓ 檔案複製完成
echo.

echo ───────────────────────────────────────────────────────────────────────────
echo [步驟 5/6] 驗證更新結果
echo ───────────────────────────────────────────────────────────────────────────

echo 正在驗證關鍵檔案...

REM 驗證主程式
if exist "%OLD_VERSION_DIR%\ChroLens_Mimic.exe" (
    echo ✓ 主程式: ChroLens_Mimic.exe
) else (
    color 0C
    echo ❌ 主程式檔案遺失
)

REM 驗證新版本模組
set VERIFY_OK=1
if exist "%OLD_VERSION_DIR%\_internal\version_manager.pyc" (
    echo ✓ 版本管理器: version_manager.pyc
) else (
    if exist "%OLD_VERSION_DIR%\version_manager.pyc" (
        echo ✓ 版本管理器: version_manager.pyc
    ) else (
        echo ⚠️  找不到: version_manager.pyc
        set VERIFY_OK=0
    )
)

if exist "%OLD_VERSION_DIR%\_internal\version_info_dialog.pyc" (
    echo ✓ 版本資訊對話框: version_info_dialog.pyc
) else (
    if exist "%OLD_VERSION_DIR%\version_info_dialog.pyc" (
        echo ✓ 版本資訊對話框: version_info_dialog.pyc
    ) else (
        echo ⚠️  找不到: version_info_dialog.pyc
        set VERIFY_OK=0
    )
)

REM 確認舊檔案已被清除
set OLD_FILES_EXIST=0
if exist "%OLD_VERSION_DIR%\_internal\update_manager.pyc" set OLD_FILES_EXIST=1
if exist "%OLD_VERSION_DIR%\_internal\update_dialog.pyc" set OLD_FILES_EXIST=1

if %OLD_FILES_EXIST%==0 (
    echo ✓ 舊版本檔案已清理
) else (
    echo ⚠️  部分舊檔案可能未完全清理
)

echo.

if %VERIFY_OK%==0 (
    color 0E
    echo ⚠️  警告: 部分檔案驗證失敗
    echo    更新可能不完整，但可以嘗試執行程式
) else (
    echo ✓ 驗證完成，所有關鍵檔案正常
)

echo.

echo ───────────────────────────────────────────────────────────────────────────
echo [步驟 6/6] 完成
echo ───────────────────────────────────────────────────────────────────────────

color 0A
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ✅ 更新完成！
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo 📁 安裝位置: %OLD_VERSION_DIR%
echo 💾 備份位置: %BACKUP_DIR%
echo.
echo 📌 重要提醒:
echo    1. 您的舊版本已完整備份到 backup\ 目錄
echo    2. 如更新後有任何問題，可從備份還原
echo    3. 請啟動程式並測試以下功能：
echo       - 基本錄製/播放功能
echo       - 點擊「整體設定」→「版本資訊」按鈕
echo       - 確認版本號為 v2.7.2
echo.
echo 🎉 從 2.7.2 版本開始:
echo    未來所有版本更新都可透過「版本資訊」功能自動完成
echo    不再需要手動更新！
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM 詢問是否啟動程式
set /p START_APP="是否要立即啟動 ChroLens_Mimic？(Y/N): "
if /i "%START_APP%"=="Y" (
    echo.
    echo 正在啟動程式...
    start "" "%OLD_VERSION_DIR%\ChroLens_Mimic.exe"
    timeout /t 2 /nobreak >nul
    exit /b 0
)

echo.
echo 您可以隨時從以下位置啟動程式:
echo %OLD_VERSION_DIR%\ChroLens_Mimic.exe
echo.
pause
