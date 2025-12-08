@echo off
chcp 65001 >nul
title 驗證打包結果
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ChroLens_Mimic 打包結果驗證工具
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM 檢查 dist 目錄
echo [1/3] 檢查輸出目錄...
if not exist "dist\ChroLens_Mimic" (
    color 0C
    echo ❌ 找不到輸出目錄: dist\ChroLens_Mimic
    echo    請先執行 打包.bat
    pause
    exit /b 1
)
echo ✓ 輸出目錄存在
echo.

REM 檢查更新工具檔案
echo [2/3] 檢查更新工具檔案...
set FILES_OK=1

if exist "dist\ChroLens_Mimic\manual_update.bat" (
    echo ✓ manual_update.bat 存在
    for %%F in ("dist\ChroLens_Mimic\manual_update.bat") do echo    大小: %%~zF bytes
) else (
    echo ❌ manual_update.bat 不存在
    set FILES_OK=0
)

if exist "dist\ChroLens_Mimic\更新說明.txt" (
    echo ✓ 更新說明.txt 存在
    for %%F in ("dist\ChroLens_Mimic\更新說明.txt") do echo    大小: %%~zF bytes
) else (
    echo ❌ 更新說明.txt 不存在
    set FILES_OK=0
)
echo.

REM 檢查 ZIP 檔案
echo [3/3] 檢查 ZIP 壓縮檔...
set ZIP_FOUND=0
for %%F in (dist\ChroLens_Mimic_*.zip) do (
    set ZIP_FOUND=1
    echo ✓ 找到 ZIP: %%~nxF
    for %%S in ("%%F") do echo    大小: %%~zS bytes
    
    echo.
    echo 正在解壓縮驗證...
    if exist "temp_verify" rmdir /s /q "temp_verify"
    powershell -Command "Expand-Archive -Path '%%F' -DestinationPath 'temp_verify' -Force" >nul 2>&1
    
    if exist "temp_verify\ChroLens_Mimic\manual_update.bat" (
        echo ✓ ZIP 中包含: manual_update.bat
    ) else (
        echo ❌ ZIP 中缺少: manual_update.bat
        set FILES_OK=0
    )
    
    if exist "temp_verify\ChroLens_Mimic\更新說明.txt" (
        echo ✓ ZIP 中包含: 更新說明.txt
    ) else (
        echo ❌ ZIP 中缺少: 更新說明.txt
        set FILES_OK=0
    )
    
    if exist "temp_verify" rmdir /s /q "temp_verify"
)

if %ZIP_FOUND%==0 (
    echo ⚠️  找不到 ZIP 壓縮檔
)
echo.

REM 結果
echo ═══════════════════════════════════════════════════════════════════════════
if %FILES_OK%==1 (
    color 0A
    echo ✅ 驗證通過！所有檔案都正確打包
) else (
    color 0C
    echo ❌ 驗證失敗！有檔案缺失
    echo.
    echo 請嘗試：
    echo 1. 重新執行 打包.bat
    echo 2. 確認 manual_update.bat 和 更新說明.txt 存在於 main 目錄
)
echo ═══════════════════════════════════════════════════════════════════════════
echo.
pause
