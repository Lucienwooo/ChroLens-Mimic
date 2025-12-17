@echo off
chcp 65001 >nul
title ChroLens Mimic Japanese Language Pack Installer

echo ═══════════════════════════════════════════════════════════════
echo    ChroLens Mimic 日本語パック インストーラー
echo    Japanese Language Pack Installer v1.0
echo ═══════════════════════════════════════════════════════════════
echo.

REM 檢查是否在正確的位置執行
if not exist "..\ChroLens_Mimic.exe" (
    color 0C
    echo ❌ エラー: ChroLens_Mimic.exe が見つかりません
    echo    Error: ChroLens_Mimic.exe not found
    echo.
    echo    このバッチファイルは language_packs\japanese_pack\ 内で実行してください
    echo    Please run this from language_packs\japanese_pack\ directory
    echo.
    pause
    exit /b 1
)

echo [1/3] 日本語フォントをチェック中...
echo       Checking Japanese font...

if not exist "fonts\NotoSansJP-Regular.ttf" (
    color 0E
    echo ⚠️  警告: 日本語フォントが見つかりません
    echo     Warning: Japanese font not found
    echo.
    echo     フォントファイル fonts\NotoSansJP-Regular.ttf をダウンロードしてください
    echo     Please download fonts\NotoSansJP-Regular.ttf
    echo     Download: https://fonts.google.com/noto/specimen/Noto+Sans+JP
    echo.
    pause
    exit /b 1
)

echo ✓ 日本語フォント確認完了
echo.

echo [2/3] 言語設定をコピー中...
echo       Copying language settings...

if not exist "lang_ja_extended.json" (
    color 0E
    echo ⚠️  言語設定ファイルが見つかりません
    echo     Language settings file not found
    pause
    exit /b 1
)

REM 創建語言資料夾
if not exist "..\..\languages" mkdir "..\..\languages"
copy /Y "lang_ja_extended.json" "..\..\languages\" >nul

echo ✓ 言語設定コピー完了
echo.

echo [3/3] フォントを登録中...
echo       Registering font...

REM 複製字型到主程式目錄
if not exist "..\..\TTF" mkdir "..\..\TTF"
copy /Y "fonts\NotoSansJP-Regular.ttf" "..\..\TTF\" >nul

echo ✓ フォント登録完了
echo.

color 0A
echo ═══════════════════════════════════════════════════════════════
echo    ✓ インストール完了！
echo      Installation Complete!
echo ═══════════════════════════════════════════════════════════════
echo.
echo 次の手順:
echo Next steps:
echo   1. ChroLens_Mimic.exe を起動
echo      Launch ChroLens_Mimic.exe
echo   2. Language ドロップダウンから「日本語」を選択
echo      Select "日本語" from Language dropdown
echo   3. プログラムを再起動
echo      Restart the program
echo.
echo ═══════════════════════════════════════════════════════════════
pause
