# 創建真正的 2.7.3 測試版本（修改版本號）

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   創建真正的 ChroLens_Mimic v2.7.3 測試版本" -ForegroundColor Cyan
Write-Host "   (修改版本號，可用於 GitHub Release 測試)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "此腳本會：" -ForegroundColor Yellow
Write-Host "1. 備份原始 ChroLens_Mimic.py" -ForegroundColor White
Write-Host "2. 將版本號從 2.7.2 改為 2.7.3" -ForegroundColor White
Write-Host "3. 執行打包" -ForegroundColor White
Write-Host "4. 還原原始檔案" -ForegroundColor White
Write-Host "5. 創建可發布到 GitHub Release 的 ZIP" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "是否繼續？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[1/6] 備份原始檔案..." -ForegroundColor Yellow
Copy-Item "ChroLens_Mimic.py" -Destination "ChroLens_Mimic.py.bak_2.7.2" -Force
Write-Host "✓ 已備份到 ChroLens_Mimic.py.bak_2.7.2" -ForegroundColor Green

Write-Host ""
Write-Host "[2/6] 修改版本號為 2.7.3..." -ForegroundColor Yellow
$content = Get-Content "ChroLens_Mimic.py" -Encoding UTF8
$newContent = $content -replace 'VERSION = "2.7.2"', 'VERSION = "2.7.3"'
$newContent | Out-File "ChroLens_Mimic.py" -Encoding UTF8
Write-Host "✓ 版本號已更新" -ForegroundColor Green

Write-Host ""
Write-Host "[3/6] 清理舊打包產物..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
Write-Host "✓ 清理完成" -ForegroundColor Green

Write-Host ""
Write-Host "[4/6] 執行打包 (這需要幾分鐘)..." -ForegroundColor Yellow
python pack_safe.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 打包失敗" -ForegroundColor Red
    Write-Host "正在還原原始檔案..." -ForegroundColor Yellow
    Copy-Item "ChroLens_Mimic.py.bak_2.7.2" -Destination "ChroLens_Mimic.py" -Force
    exit 1
}
Write-Host "✓ 打包完成" -ForegroundColor Green

Write-Host ""
Write-Host "[5/6] 還原原始檔案..." -ForegroundColor Yellow
Copy-Item "ChroLens_Mimic.py.bak_2.7.2" -Destination "ChroLens_Mimic.py" -Force
Remove-Item "ChroLens_Mimic.py.bak_2.7.2" -Force
Write-Host "✓ 已還原到 2.7.2" -ForegroundColor Green

Write-Host ""
Write-Host "[6/6] 驗證並重新命名 ZIP..." -ForegroundColor Yellow
if (Test-Path "dist\ChroLens_Mimic_2.7.3.zip") {
    $zipSize = [math]::Round((Get-Item "dist\ChroLens_Mimic_2.7.3.zip").Length / 1MB, 2)
    Write-Host "✓ 找到 ZIP: dist\ChroLens_Mimic_2.7.3.zip ($zipSize MB)" -ForegroundColor Green
    
    # 複製到根目錄方便上傳
    Copy-Item "dist\ChroLens_Mimic_2.7.3.zip" -Destination "ChroLens_Mimic_v2.7.3_RELEASE.zip" -Force
    Write-Host "✓ 已複製到: ChroLens_Mimic_v2.7.3_RELEASE.zip" -ForegroundColor Green
} else {
    Write-Host "❌ 找不到 ZIP 檔案" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   ✅ 真正的 2.7.3 測試版本創建完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📦 發布檔案：ChroLens_Mimic_v2.7.3_RELEASE.zip" -ForegroundColor Cyan
Write-Host "📏 大小：$zipSize MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 GitHub Release 發布步驟：" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 前往 GitHub Repository" -ForegroundColor White
Write-Host "   https://github.com/Lucienwooo/ChroLens-Mimic/releases/new" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 填寫 Release 資訊：" -ForegroundColor White
Write-Host "   Tag: v2.7.3" -ForegroundColor Gray
Write-Host "   Title: ChroLens_Mimic v2.7.3 (測試版本)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Description 範例：" -ForegroundColor White
Write-Host "   ## ⚠️ 這是測試版本" -ForegroundColor Gray
Write-Host "   " -ForegroundColor Gray
Write-Host "   此版本用於測試自動更新功能。" -ForegroundColor Gray
Write-Host "   " -ForegroundColor Gray
Write-Host "   ### 測試步驟" -ForegroundColor Gray
Write-Host "   1. 使用 2.7.2 版本" -ForegroundColor Gray
Write-Host "   2. 點擊「整體設定」→「版本資訊」" -ForegroundColor Gray
Write-Host "   3. 應該會偵測到 2.7.3 更新" -ForegroundColor Gray
Write-Host "   4. 點擊「立即更新」測試自動更新流程" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 上傳檔案：" -ForegroundColor White
Write-Host "   ChroLens_Mimic_v2.7.3_RELEASE.zip" -ForegroundColor Gray
Write-Host ""
Write-Host "5. 勾選「This is a pre-release」(這是預發布版本)" -ForegroundColor White
Write-Host ""
Write-Host "6. 點擊「Publish release」" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "💡 提示：" -ForegroundColor Cyan
Write-Host "- 原始 2.7.2 版本已保持不變" -ForegroundColor White
Write-Host "- 只有打包產物是 2.7.3" -ForegroundColor White
Write-Host "- 可以安全發布到 GitHub 進行測試" -ForegroundColor White
Write-Host ""

$open = Read-Host "是否開啟 GitHub Releases 頁面？(Y/N)"
if ($open -eq "Y" -or $open -eq "y") {
    Start-Process "https://github.com/Lucienwooo/ChroLens-Mimic/releases/new"
}

Write-Host ""
Write-Host "準備就緒！按任意鍵退出..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
