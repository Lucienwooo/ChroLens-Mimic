# ============================================================
# ChroLens Mimic Web - 一鍵啟動腳本 (PowerShell)
# ============================================================

$ErrorActionPreference = "Stop"
$WebDir = Join-Path $PSScriptRoot "web"
$NodeDir = Join-Path $env:TEMP "node_temp"

function Write-Header {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ChroLens Mimic Web - 一鍵啟動腳本" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Find-NodeExe {
    # 先從 PATH 找
    $nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
    if ($nodeCmd) { return $nodeCmd.Source }

    # 常見安裝路徑
    $candidates = @(
        "C:\Program Files\nodejs\node.exe",
        "C:\Program Files (x86)\nodejs\node.exe",
        "$env:LOCALAPPDATA\Programs\nodejs\node.exe",
        (Join-Path $NodeDir "node.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

function Install-Node {
    Write-Host "[提示] 找不到 Node.js，正在自動下載免安裝版本..." -ForegroundColor Yellow
    Write-Host "       (Node.js v18 LTS, 約 34MB)" -ForegroundColor Gray
    Write-Host ""

    $zipUrl  = "https://nodejs.org/dist/v18.20.8/node-v18.20.8-win-x64.zip"
    $zipPath = Join-Path $env:TEMP "node18_lts.zip"
    $unzipDir = Join-Path $env:TEMP "node18_unzip"

    # 下載
    Write-Host "  正在下載..." -NoNewline
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Write-Host " 完成" -ForegroundColor Green

    # 解壓縮
    Write-Host "  正在解壓縮..." -NoNewline
    if (Test-Path $unzipDir) { Remove-Item $unzipDir -Recurse -Force }
    Expand-Archive -Path $zipPath -DestinationPath $unzipDir -Force
    $innerDir = Get-ChildItem $unzipDir -Directory | Select-Object -First 1

    if (Test-Path $NodeDir) { Remove-Item $NodeDir -Recurse -Force }
    Move-Item $innerDir.FullName $NodeDir
    Remove-Item $zipPath -Force
    Write-Host " 完成" -ForegroundColor Green
    Write-Host ""
}

# ── Main ──
Write-Header

$nodeExe = Find-NodeExe
if (-not $nodeExe) {
    Install-Node
    $nodeExe = Join-Path $NodeDir "node.exe"
}

if (-not (Test-Path $nodeExe)) {
    Write-Host "[錯誤] Node.js 安裝失敗，請手動安裝: https://nodejs.org" -ForegroundColor Red
    exit 1
}

# 確保 npm 和 node 在 PATH 中
$npmDir = Split-Path $nodeExe -Parent
if ($env:PATH -notlike "*$npmDir*") {
    $env:PATH = "$npmDir;$env:PATH"
}

$nodeVer = & $nodeExe --version 2>&1
Write-Host "[OK] Node.js $nodeVer" -ForegroundColor Green

# ── 安裝套件 ──
Set-Location $WebDir

$npmCmd = Join-Path $npmDir "npm.cmd"
if (-not (Test-Path $npmCmd)) { $npmCmd = "npm" }

if (-not (Test-Path "node_modules")) {
    Write-Host ""
    Write-Host "[1/2] 首次執行，安裝相依套件中 (可能需要 1-2 分鐘)..." -ForegroundColor Yellow
    & $npmCmd install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[錯誤] npm install 失敗" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] 套件安裝完成" -ForegroundColor Green
} else {
    Write-Host "[1/2] 套件已安裝，跳過。" -ForegroundColor Gray
}

# ── 啟動開發伺服器 ──
Write-Host ""
Write-Host "[2/2] 啟動開發伺服器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  網址: http://localhost:3000           " -ForegroundColor White
Write-Host "  按 Ctrl+C 可停止伺服器               " -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 延遲 3 秒後自動開啟瀏覽器
$job = Start-Job {
    Start-Sleep 4
    Start-Process "http://localhost:3000"
}

# 啟動 dev server (foreground)
& $npmCmd run dev
