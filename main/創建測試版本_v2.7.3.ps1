# 創建 ChroLens_Mimic v2.7.3 測試版本
# 用於測試自動更新功能

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   創建 ChroLens_Mimic v2.7.3 測試版本" -ForegroundColor Cyan
Write-Host "   用於測試自動更新功能" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 創建測試目錄
Write-Host "[1/5] 創建測試目錄..." -ForegroundColor Yellow
if (Test-Path "test_v2.7.3") {
    Remove-Item "test_v2.7.3" -Recurse -Force
}
New-Item -ItemType Directory -Path "test_v2.7.3\ChroLens_Mimic" -Force | Out-Null
Write-Host "✓ 測試目錄已創建" -ForegroundColor Green
Write-Host ""

# 步驟 2: 複製檔案
Write-Host "[2/5] 複製檔案..." -ForegroundColor Yellow
Copy-Item "dist\ChroLens_Mimic\*" -Destination "test_v2.7.3\ChroLens_Mimic\" -Recurse -Force
Write-Host "✓ 檔案複製完成" -ForegroundColor Green
Write-Host ""

# 步驟 3: 創建版本標記檔案
Write-Host "[3/5] 創建版本標記..." -ForegroundColor Yellow
$testFileContent = @"
════════════════════════════════════════════════════════
  ChroLens_Mimic v2.7.3 測試版本
════════════════════════════════════════════════════════

此版本僅用於測試自動更新功能

【測試步驟】
1. 執行 2.7.2 版本的 ChroLens_Mimic.exe
2. 點擊「整體設定」→「版本資訊」
3. 手動指定此 ZIP 檔案進行更新測試
4. 更新完成後，檢查是否出現此檔案

【預期結果】
- 程式自動關閉
- 批次腳本執行更新
- 備份舊版本到 backup\ 目錄
- 複製新檔案覆蓋舊檔案
- 自動重新啟動程式
- 在程式目錄看到此檔案

【注意事項】
- 這不是真正的 2.7.3 版本
- 僅用於測試更新機制
- 程式功能與 2.7.2 相同

創建時間：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
════════════════════════════════════════════════════════
"@

$testFileContent | Out-File -FilePath "test_v2.7.3\ChroLens_Mimic\這是測試版本_v2.7.3.txt" -Encoding UTF8
Write-Host "✓ 版本標記已創建" -ForegroundColor Green
Write-Host ""

# 步驟 4: 創建 Release Notes
Write-Host "[4/5] 創建 Release Notes..." -ForegroundColor Yellow
$releaseNotes = @"
## ChroLens_Mimic v2.7.3 測試版本

### ⚠️ 這是測試版本

此版本僅用於測試自動更新功能，不包含實際的新功能。

### 測試內容
- 版本號顯示為 v2.7.3
- 包含測試用標記檔案
- 驗證自動更新流程
- 驗證批次腳本執行
- 驗證檔案備份功能
- 驗證自動重啟功能

### 測試步驟
1. 確保當前使用 v2.7.2
2. 開啟程式，點擊「整體設定」→「版本資訊」
3. 手動測試更新功能（使用本地 ZIP 檔案）
4. 觀察更新流程是否正確執行
5. 更新完成後檢查「這是測試版本_v2.7.3.txt」是否出現

### 如何使用此測試包

#### 方法 1: 模擬下載更新
``````
# 在 2.7.2 版本中，手動觸發下載這個 ZIP
# 然後觀察自動更新流程
``````

#### 方法 2: 使用 manual_update.bat
``````
1. 解壓 ChroLens_Mimic_v2.7.3_TEST.zip
2. 執行 manual_update.bat
3. 指定 2.7.2 版本的安裝路徑
``````
"@

$releaseNotes | Out-File -FilePath "test_v2.7.3\RELEASE_NOTES.md" -Encoding UTF8
Write-Host "✓ Release Notes 已創建" -ForegroundColor Green
Write-Host ""

# 步驟 5: 打包成 ZIP
Write-Host "[5/5] 打包成 ZIP..." -ForegroundColor Yellow
Start-Sleep -Seconds 1  # 等待檔案系統

if (Test-Path "ChroLens_Mimic_v2.7.3_TEST.zip") {
    Remove-Item "ChroLens_Mimic_v2.7.3_TEST.zip" -Force
}

try {
    Compress-Archive -Path "test_v2.7.3\ChroLens_Mimic\*" -DestinationPath "ChroLens_Mimic_v2.7.3_TEST.zip" -Force -CompressionLevel Optimal
    
    if (Test-Path "ChroLens_Mimic_v2.7.3_TEST.zip") {
        $zipSize = (Get-Item "ChroLens_Mimic_v2.7.3_TEST.zip").Length
        $zipSizeMB = [math]::Round($zipSize / 1MB, 2)
        Write-Host "✓ ZIP 創建完成" -ForegroundColor Green
        Write-Host ""
    } else {
        throw "ZIP 檔案未創建"
    }
} catch {
    Write-Host "❌ ZIP 創建失敗: $_" -ForegroundColor Red
    exit 1
}

# 完成
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   ✅ 測試版本創建完成！" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "📦 測試檔案位置:" -ForegroundColor Cyan
Write-Host "   ChroLens_Mimic_v2.7.3_TEST.zip"
Write-Host "   大小: $zipSizeMB MB"
Write-Host ""
Write-Host "📋 如何測試:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   【方法 1: 手動測試更新流程】" -ForegroundColor Yellow
Write-Host "   1. 將此 ZIP 放到容易存取的位置"
Write-Host "   2. 執行 2.7.2 版本的程式"
Write-Host "   3. 修改 version_manager.py 暫時指向本地檔案"
Write-Host "   4. 測試完整更新流程"
Write-Host ""
Write-Host "   【方法 2: 解壓後直接覆蓋測試】" -ForegroundColor Yellow
Write-Host "   1. 備份當前 2.7.2 版本"
Write-Host "   2. 解壓測試版本到新資料夾"
Write-Host "   3. 執行並確認「這是測試版本_v2.7.3.txt」存在"
Write-Host ""
Write-Host "📝 驗證要點:" -ForegroundColor Cyan
Write-Host "   ✓ 看到「這是測試版本_v2.7.3.txt」檔案"
Write-Host "   ✓ backup\ 目錄包含備份"
Write-Host "   ✓ 程式能正常啟動"
Write-Host "   ✓ 所有功能正常運作"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# 詢問是否清理
$cleanup = Read-Host "是否清理臨時測試目錄？(Y/N)"
if ($cleanup -eq "Y" -or $cleanup -eq "y") {
    Write-Host ""
    Write-Host "正在清理..." -ForegroundColor Yellow
    Remove-Item "test_v2.7.3" -Recurse -Force
    Write-Host "✓ 已清理測試目錄" -ForegroundColor Green
}

Write-Host ""
Write-Host "測試版本已就緒！按任意鍵退出..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
