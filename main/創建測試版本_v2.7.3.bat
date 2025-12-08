@echo off
chcp 65001 >nul
title 創建 2.7.3 測試版本
color 0B

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    創建 ChroLens_Mimic v2.7.3 測試版本
echo    用於測試自動更新功能
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo 此腳本會創建一個僅用於測試的 2.7.3 版本
echo 內容：
echo   - 版本號改為 2.7.3
echo   - 新增測試用文字檔說明這是測試版本
echo   - 打包成 ZIP 供測試更新功能使用
echo.
pause

REM 創建測試目錄
echo.
echo [1/5] 創建測試目錄...
if exist "test_v2.7.3" rmdir /s /q "test_v2.7.3"
mkdir "test_v2.7.3"
mkdir "test_v2.7.3\ChroLens_Mimic"
echo ✓ 測試目錄已創建
echo.

REM 複製當前版本檔案
echo [2/5] 複製檔案...
xcopy /E /I /Y "dist\ChroLens_Mimic\*" "test_v2.7.3\ChroLens_Mimic\" >nul
echo ✓ 檔案複製完成
echo.

REM 創建版本標記檔案
echo [3/5] 創建版本標記...
echo ════════════════════════════════════════════════════════ > "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo   ChroLens_Mimic v2.7.3 測試版本 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo ════════════════════════════════════════════════════════ >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo. >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 此版本僅用於測試自動更新功能 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo. >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 【測試步驟】 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 1. 執行 2.7.2 版本的 ChroLens_Mimic.exe >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 2. 點擊「整體設定」→「版本資訊」 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 3. 手動指定此 ZIP 檔案進行更新測試 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 4. 更新完成後，檢查是否出現此檔案 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo. >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 【預期結果】 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 程式自動關閉 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 批次腳本執行更新 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 備份舊版本到 backup\ 目錄 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 複製新檔案覆蓋舊檔案 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 自動重新啟動程式 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 在程式目錄看到此檔案 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo. >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 【注意事項】 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 這不是真正的 2.7.3 版本 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 僅用於測試更新機制 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo - 程式功能與 2.7.2 相同 >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo. >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo 創建時間：%date% %time% >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"
echo ════════════════════════════════════════════════════════ >> "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt"

echo ✓ 版本標記已創建
echo.

REM 創建 Release Notes
echo [4/5] 創建 Release Notes...
echo ## ChroLens_Mimic v2.7.3 測試版本 > "test_v2.7.3\RELEASE_NOTES.txt"
echo. >> "test_v2.7.3\RELEASE_NOTES.txt"
echo ### ⚠️ 這是測試版本 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo. >> "test_v2.7.3\RELEASE_NOTES.txt"
echo 此版本僅用於測試自動更新功能，不包含實際的新功能。 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo. >> "test_v2.7.3\RELEASE_NOTES.txt"
echo ### 測試內容 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo - 版本號顯示為 v2.7.3 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo - 包含測試用標記檔案 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo - 驗證自動更新流程 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo - 驗證批次腳本執行 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo - 驗證檔案備份功能 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo - 驗證自動重啟功能 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo. >> "test_v2.7.3\RELEASE_NOTES.txt"
echo ### 測試步驟 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo 1. 確保當前使用 v2.7.2 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo 2. 開啟程式，點擊「整體設定」→「版本資訊」 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo 3. 手動測試更新功能（使用本地 ZIP 檔案） >> "test_v2.7.3\RELEASE_NOTES.txt"
echo 4. 觀察更新流程是否正確執行 >> "test_v2.7.3\RELEASE_NOTES.txt"
echo 5. 更新完成後檢查「這是測試版本_v2.7.3.txt」是否出現 >> "test_v2.7.3\RELEASE_NOTES.txt"

echo ✓ Release Notes 已創建
echo.

REM 打包成 ZIP
echo [5/5] 打包成 ZIP...
powershell -Command "Compress-Archive -Path 'test_v2.7.3\ChroLens_Mimic\*' -DestinationPath 'ChroLens_Mimic_v2.7.3_TEST.zip' -Force"

if exist "ChroLens_Mimic_v2.7.3_TEST.zip" (
    for %%F in ("ChroLens_Mimic_v2.7.3_TEST.zip") do set ZIP_SIZE=%%~zF
    echo ✓ ZIP 創建完成
    echo.
) else (
    color 0C
    echo ❌ ZIP 創建失敗
    pause
    exit /b 1
)

REM 完成
color 0A
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo    ✅ 測試版本創建完成！
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo 📦 測試檔案位置:
echo    ChroLens_Mimic_v2.7.3_TEST.zip
echo    大小: %ZIP_SIZE% bytes
echo.
echo 📋 如何測試:
echo.
echo    【方法 1: 手動測試更新功能】
echo    1. 執行現有的 2.7.2 版本
echo    2. 點擊「整體設定」→「版本資訊」
echo    3. 由於沒有真實的 GitHub Release，更新會失敗
echo    4. 但您可以手動測試批次更新腳本
echo.
echo    【方法 2: 測試批次腳本】
echo    1. 解壓 ChroLens_Mimic_v2.7.3_TEST.zip 到臨時目錄
echo    2. 手動執行 version_manager.py 的更新流程
echo    3. 或使用 manual_update.bat 指定測試版路徑
echo.
echo    【方法 3: 模擬完整流程】
echo    1. 在本地建立簡易 HTTP 伺服器
echo    2. 修改 version_manager.py 的 API_URL 指向本地
echo    3. 測試完整的自動更新流程
echo.
echo 📝 驗證要點:
echo    ✓ 更新後看到「這是測試版本_v2.7.3.txt」檔案
echo    ✓ backup\ 目錄包含 2.7.2 版本備份
echo    ✓ 程式能自動重啟
echo    ✓ 所有功能正常運作
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM 詢問是否清理測試目錄
set /p CLEANUP="是否清理臨時測試目錄？(Y/N): "
if /i "%CLEANUP%"=="Y" (
    echo.
    echo 正在清理...
    rmdir /s /q "test_v2.7.3"
    echo ✓ 已清理測試目錄
)

echo.
echo 測試版本已就緒！
pause
