@echo off
title 啟動 ChroLens Mimic 網頁編輯器
echo ===================================================
echo   正在啟動 ChroLens Mimic 網頁伺服器...
echo ===================================================

:: 切換到 web 目錄
cd /d "%~dp0web"

:: 在新的命令提示字元視窗中啟動 npm run dev，讓伺服器持續在背景運作
start "Mimic Web Server" cmd /k "npm run dev"

echo.
echo 伺服器啟動中，請稍候...
:: 等待 4 秒確保伺服器已經準備就緒
timeout /t 4 /nobreak >nul

echo.
echo 正在開啟瀏覽器...
:: 使用預設瀏覽器開啟編輯器網址
start http://localhost:3000/builder

echo.
echo ===================================================
echo   啟動完成！您可以隨時關閉這個黑色視窗。
echo   (如果需要關閉伺服器，請關閉標題為 Mimic Web Server 的視窗)
echo ===================================================
timeout /t 3 >nul
