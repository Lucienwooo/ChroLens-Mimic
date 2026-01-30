# -*- coding: utf-8 -*-
"""
版本管理器 - ChroLens_Mimic
負責檢查更新和版本資訊顯示

更新機制：基於 GitHub Releases + 獨立更新程式
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import tempfile
import shutil
import subprocess
import threading
import time
from typing import Optional, Dict, Callable
from packaging import version as pkg_version


class VersionManager:
    """版本管理器"""
    
    # GitHub 資訊
    GITHUB_REPO = "Lucienwooo/ChroLens-Mimic"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    CHANGELOG_URL = "https://lucienwooo.github.io/ChroLens_Mimic/"
    
    def __init__(self, current_version: str, logger: Optional[Callable] = None):
        """
        初始化版本管理器
        
        Args:
            current_version: 當前版本號（如 "2.7.2"）
            logger: 日誌函數
        """
        self.current_version = current_version
        self._logger = logger or (lambda msg: print(f"[VersionManager] {msg}"))
        
        # 取得應用程式目錄
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
    
    def log(self, msg: str):
        """記錄日誌"""
        self._logger(msg)
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        檢查是否有新版本
        
        Returns:
            如果有更新，返回更新資訊字典，否則返回 None
        """
        try:
            self.log("正在檢查更新...")
            
            # 發送請求到 GitHub API
            req = urllib.request.Request(
                self.API_URL,
                headers={'User-Agent': 'ChroLens-Mimic-App'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 解析版本資訊
            latest_version = data['tag_name'].lstrip('v')  # 移除 'v' 前綴
            
            # 比較版本
            if self._is_newer_version(latest_version, self.current_version):
                # 尋找下載連結（找 .zip 檔案）
                download_url = None
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.zip'):
                        download_url = asset['browser_download_url']
                        break
                
                if not download_url:
                    self.log("找不到下載連結")
                    return None
                
                update_info = {
                    'version': latest_version,
                    'download_url': download_url,
                    'release_notes': data.get('body', '無更新說明'),
                    'published_at': data.get('published_at', ''),
                    'html_url': data.get('html_url', '')
                }
                
                self.log(f"發現新版本: {latest_version}")
                return update_info
            else:
                self.log("目前已是最新版本")
                return None
                
        except urllib.error.HTTPError as e:
            self.log(f"HTTP 錯誤: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            self.log(f"網路錯誤: {e.reason}")
            return None
        except Exception as e:
            self.log(f"檢查更新失敗: {e}")
            return None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """比較版本號"""
        try:
            return pkg_version.parse(latest) > pkg_version.parse(current)
        except Exception:
            # 簡單的字串比較作為備援
            return latest > current
    
    def download_update(self, download_url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """下載更新檔案"""
        try:
            self.log(f"開始下載: {download_url}")
            
            # 創建臨時目錄
            temp_dir = tempfile.mkdtemp(prefix='chrolens_update_')
            zip_path = os.path.join(temp_dir, 'update.zip')
            
            # 下載檔案
            def reporthook(block_num, block_size, total_size):
                if progress_callback:
                    downloaded = block_num * block_size
                    progress_callback(downloaded, total_size)
            
            urllib.request.urlretrieve(download_url, zip_path, reporthook)
            
            self.log(f"下載完成: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.log(f"下載失敗: {e}")
            return None
    
    def extract_update(self, zip_path: str) -> Optional[str]:
        """解壓縮更新檔案"""
        try:
            self.log(f"正在解壓縮: {zip_path}")
            
            extract_dir = os.path.join(os.path.dirname(zip_path), 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            self.log(f"解壓縮完成: {extract_dir}")
            return extract_dir
            
        except Exception as e:
            self.log(f"解壓縮失敗: {e}")
            return None
    
    def apply_update(self, extract_dir: str, restart_after: bool = True) -> bool:
        """
        應用更新(使用簡單可靠的 BAT 批次腳本)
        
        Args:
            extract_dir: 解壓縮目錄
            restart_after: 是否在更新後重新啟動
            
        Returns:
            是否成功創建並啟動更新腳本
        """
        try:
            self.log("準備應用更新...")
            
            # 尋找解壓縮後的實際程式目錄
            actual_source_dir = self._find_update_source(extract_dir)
            if not actual_source_dir:
                self.log("錯誤: 找不到有效的更新來源目錄")
                return False
            
            self.log(f"找到更新來源: {actual_source_dir}")
            
            # 創建批次更新腳本
            bat_script = os.path.join(self.app_dir, 'update_now.bat')
            log_path = os.path.join(self.app_dir, 'update_log.txt')
            
            # 先創建初始日誌
            try:
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write("ChroLens_Mimic 更新程式\n")
                    f.write(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n")
                    f.write(f"來源: {actual_source_dir}\n")
                    f.write(f"目標: {self.app_dir}\n")
                    f.write(f"腳本: {bat_script}\n")
                    f.write("\n")
            except Exception as e:
                self.log(f"警告: 無法創建日誌檔案: {e}")
            
            exe_path = os.path.join(self.app_dir, "ChroLens_Mimic.exe")
            
            # BAT 批次腳本內容 (簡單可靠,使用 robocopy)
            script_content = f'''@echo off
chcp 65001 >nul
title ChroLens_Mimic 更新程式

set "LOG_FILE={log_path}"
set "SOURCE_DIR={actual_source_dir}"
set "TARGET_DIR={self.app_dir}"
set "EXE_PATH={exe_path}"

echo ======================================== >> "%LOG_FILE%"
echo 批次腳本開始執行 >> "%LOG_FILE%"
echo 時間: %DATE% %TIME% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo.
echo ========================================
echo ChroLens_Mimic 更新程式
echo ========================================
echo.

REM 等待主程式完全關閉
echo 等待主程式關閉...
echo 等待主程式關閉... >> "%LOG_FILE%"

timeout /t 3 /nobreak >nul

REM 強制終止所有相關程序
taskkill /F /IM ChroLens_Mimic.exe >nul 2>&1

REM 再等待一下確保資源釋放
timeout /t 2 /nobreak >nul

echo 主程式已關閉 >> "%LOG_FILE%"
echo.

REM 創建備份標記
echo 創建備份標記...
echo 創建備份標記... >> "%LOG_FILE%"
if not exist "%TARGET_DIR%\\backup" mkdir "%TARGET_DIR%\\backup"
echo {self.current_version} > "%TARGET_DIR%\\backup\\pre_update_version.txt"

echo.
echo 開始複製檔案...
echo 開始複製檔案... >> "%LOG_FILE%"
echo 使用 robocopy 複製... >> "%LOG_FILE%"

REM 使用 robocopy 複製檔案 (更可靠)
REM /E = 包含子目錄(含空目錄)
REM /IS = 包含相同檔案
REM /IT = 包含已調整的檔案  
REM /R:3 = 重試3次
REM /W:1 = 每次重試等待1秒
REM /NP = 不顯示進度百分比
REM /NFL = 不記錄檔案清單
REM /NDL = 不記錄目錄清單

robocopy "%SOURCE_DIR%" "%TARGET_DIR%" /E /IS /IT /R:3 /W:1 /NP /NFL /NDL >> "%LOG_FILE%" 2>&1

REM robocopy 的返回碼: 0-7 是成功, >7 是錯誤
if %ERRORLEVEL% LEQ 7 (
    echo 檔案複製成功 >> "%LOG_FILE%"
    echo.
    echo 更新完成!
    echo 更新完成! >> "%LOG_FILE%"
) else (
    echo 檔案複製失敗，錯誤碼: %ERRORLEVEL% >> "%LOG_FILE%"
    echo.
    echo 更新失敗! 錯誤碼: %ERRORLEVEL%
    echo 請查看日誌: %LOG_FILE%
    pause
    exit /b 1
)

REM 驗證主程式是否存在
if not exist "%EXE_PATH%" (
    echo 錯誤: 找不到執行檔 >> "%LOG_FILE%"
    echo.
    echo 錯誤: 找不到執行檔!
    echo 路徑: %EXE_PATH%
    pause
    exit /b 1
)

echo 執行檔驗證通過 >> "%LOG_FILE%"

REM 清理臨時檔案
echo 清理臨時檔案... >> "%LOG_FILE%"
rd /S /Q "{os.path.dirname(extract_dir)}" >nul 2>&1

'''

            if restart_after:
                script_content += f'''
REM 重新啟動程式
echo.
echo 正在啟動程式...
echo 正在啟動程式... >> "%LOG_FILE%"

timeout /t 2 /nobreak >nul

cd /d "%TARGET_DIR%"
start "" "%EXE_PATH%"

if %ERRORLEVEL% EQU 0 (
    echo 程式已啟動 >> "%LOG_FILE%"
    echo 程式已啟動!
) else (
    echo 啟動失敗，錯誤碼: %ERRORLEVEL% >> "%LOG_FILE%"
    echo 啟動失敗!
    echo 請手動執行: %EXE_PATH%
    pause
    exit /b 1
)
'''
            
            script_content += '''
REM 完成
echo. >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo 更新流程完成 >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

timeout /t 2 /nobreak >nul

REM 刪除自己
del "%~f0"
'''
            
            # 寫入批次腳本
            with open(bat_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.log(f"更新腳本已創建: {bat_script}")
            
            # 記錄到日誌
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"批次腳本已創建: {bat_script}\n")
                    f.write("準備啟動更新腳本並關閉主程式...\n\n")
            except:
                pass
            
            # 啟動批次腳本 (使用 cmd /c start 確保非同步執行)
            try:
                subprocess.Popen(
                    ['cmd', '/c', 'start', '', '/min', bat_script],
                    shell=True,
                    cwd=self.app_dir
                )
                self.log("✓ 更新腳本已啟動，主程式即將關閉")
                return True
            except Exception as e:
                self.log(f"啟動批次腳本失敗: {e}")
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(f"✗ 啟動批次腳本失敗: {e}\n")
                except:
                    pass
                return False
            
        except Exception as e:
            self.log(f"創建更新腳本失敗: {e}")
            import traceback
            self.log(f"詳細錯誤: {traceback.format_exc()}")
            return False
            
            # PowerShell 腳本內容(更可靠,不會卡在 xcopy)
            script_content = f'''# ChroLens_Mimic 更新腳本
$LogFile = "{log_path}"
$SourceDir = "{actual_source_dir}"
$TargetDir = "{self.app_dir}"
$ExePath = "{exe_path}"

# 開始記錄
"=" * 60 | Out-File -FilePath $LogFile -Encoding UTF8
"ChroLens_Mimic 更新程式" | Out-File -FilePath $LogFile -Append -Encoding UTF8
"時間: $(Get-Date)" | Out-File -FilePath $LogFile -Append -Encoding UTF8
"=" * 60 | Out-File -FilePath $LogFile -Append -Encoding UTF8
"來源: $SourceDir" | Out-File -FilePath $LogFile -Append -Encoding UTF8
"目標: $TargetDir" | Out-File -FilePath $LogFile -Append -Encoding UTF8
"" | Out-File -FilePath $LogFile -Append -Encoding UTF8

Write-Host "等待程式關閉..." -ForegroundColor Cyan

# 等待主程式關閉(最多10秒)
$count = 0
while ((Get-Process -Name "ChroLens_Mimic" -ErrorAction SilentlyContinue) -and ($count -lt 10)) {{
    Start-Sleep -Seconds 1
    $count++
}}

# 如果還在運行,強制關閉
if (Get-Process -Name "ChroLens_Mimic" -ErrorAction SilentlyContinue) {{
    "強制終止程式..." | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Stop-Process -Name "ChroLens_Mimic" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}}

"程式已關閉" | Out-File -FilePath $LogFile -Append -Encoding UTF8
Write-Host "程式已關閉" -ForegroundColor Green

# 額外等待
Start-Sleep -Seconds 2

Write-Host "開始複製檔案..." -ForegroundColor Cyan
"開始複製檔案..." | Out-File -FilePath $LogFile -Append -Encoding UTF8

# 創建備份標記
$BackupDir = Join-Path $TargetDir "backup"
if (-not (Test-Path $BackupDir)) {{
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}}

# 使用 Copy-Item 逐個複製檔案(比 xcopy 更可靠)
try {{
    $files = Get-ChildItem -Path $SourceDir -Recurse -File
    $total = $files.Count
    $copied = 0
    
    foreach ($file in $files) {{
        $relativePath = $file.FullName.Substring($SourceDir.Length + 1)
        $targetPath = Join-Path $TargetDir $relativePath
        $targetFolder = Split-Path $targetPath -Parent
        
        # 創建目標目錄
        if (-not (Test-Path $targetFolder)) {{
            New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
        }}
        
        # 複製檔案(重試3次)
        $retry = 0
        $success = $false
        while ((-not $success) -and ($retry -lt 3)) {{
            try {{
                Copy-Item -Path $file.FullName -Destination $targetPath -Force
                $success = $true
            }} catch {{
                $retry++
                if ($retry -lt 3) {{
                    Start-Sleep -Milliseconds 500
                }}
            }}
        }}
        
        if ($success) {{
            $copied++
            if ($copied % 50 -eq 0) {{
                $percent = [math]::Round(($copied / $total) * 100)
                Write-Host "進度: $percent% ($copied/$total)" -ForegroundColor Yellow
            }}
        }} else {{
            "警告: 複製失敗 - $relativePath" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        }}
    }}
    
    "✓ 已複製 $copied/$total 個檔案" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "✓ 更新完成! 已複製 $copied 個檔案" -ForegroundColor Green
    
}} catch {{
    "✗ 複製檔案時發生錯誤: $_" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "錯誤: $_" -ForegroundColor Red
    Read-Host "按 Enter 繼續"
    exit 1
}}

# 清理臨時檔案
"清理臨時檔案..." | Out-File -FilePath $LogFile -Append -Encoding UTF8
try {{
    Remove-Item -Path "{os.path.dirname(extract_dir)}" -Recurse -Force -ErrorAction SilentlyContinue
}} catch {{}}
'''

            if restart_after:
                script_content += f'''
# 重啟程式
if (Test-Path $ExePath) {{
    "啟動程式: $ExePath" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "啟動程式..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-Process -FilePath $ExePath -WorkingDirectory $TargetDir
    
    # 確認啟動
    Start-Sleep -Seconds 2
    if (Get-Process -Name "ChroLens_Mimic" -ErrorAction SilentlyContinue) {{
        "✓ 程式已啟動" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        Write-Host "✓ 程式已啟動" -ForegroundColor Green
    }}
}} else {{
    "✗ 找不到執行檔: $ExePath" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "錯誤: 找不到執行檔" -ForegroundColor Red
    Read-Host "按 Enter 繼續"
    exit 1
}}
'''

            script_content += '''
# 完成
"更新完成" | Out-File -FilePath $LogFile -Append -Encoding UTF8
Start-Sleep -Seconds 2

# 刪除腳本自己
Remove-Item -Path $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
'''
            
            # 寫入 PowerShell 腳本
            with open(ps_script, 'w', encoding='utf-8-sig') as f:  # 使用 UTF-8 BOM
                f.write(script_content)
            
            self.log(f"更新腳本已創建: {ps_script}")
            self.log(f"日誌位置: {log_path}")
            
            # 記錄腳本路徑到日誌
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"PowerShell 腳本已創建: {ps_script}\n")
                    f.write("準備啟動更新腳本...\n\n")
            except:
                pass
            
            # 執行 PowerShell 腳本 (使用 -NoProfile 加速)
            try:
                subprocess.Popen(
                    ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ps_script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log("✓ 更新程式已啟動")
                return True
            except Exception as e:
                self.log(f"啟動 PowerShell 失敗: {e}")
                # 記錄到日誌
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(f"✗ 啟動 PowerShell 失敗: {e}\n")
                except:
                    pass
                return False
            
        except Exception as e:
            self.log(f"創建更新腳本失敗: {e}")
            import traceback
            self.log(f"詳細錯誤: {traceback.format_exc()}")
            return False
    
    def _find_update_source(self, extract_dir: str) -> Optional[str]:
        """尋找更新檔案來源目錄"""
        # 檢查根目錄
        if self._is_valid_update_source(extract_dir):
            return extract_dir
        
        # 檢查子目錄（一層）
        for item in os.listdir(extract_dir):
            item_path = os.path.join(extract_dir, item)
            if os.path.isdir(item_path):
                if self._is_valid_update_source(item_path):
                    return item_path
        
        # 檢查子目錄的子目錄（兩層，處理 GitHub zip 結構）
        for item in os.listdir(extract_dir):
            item_path = os.path.join(extract_dir, item)
            if os.path.isdir(item_path):
                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isdir(subitem_path) and self._is_valid_update_source(subitem_path):
                        return subitem_path
        
        return None
    
    def _is_valid_update_source(self, path: str) -> bool:
        """檢查目錄是否包含有效的更新檔案"""
        try:
            if getattr(sys, 'frozen', False):
                # 打包後：檢查是否有 .exe
                return any(f.endswith('.exe') and 'ChroLens_Mimic' in f 
                          for f in os.listdir(path))
            else:
                # 開發環境：檢查是否有主要的 .py 檔案
                return os.path.exists(os.path.join(path, 'ChroLens_Mimic.py'))
        except:
            return False
    
    def fetch_changelog(self) -> str:
        """從官網獲取更新日誌"""
        try:
            self.log(f"正在獲取更新日誌: {self.CHANGELOG_URL}")
            
            req = urllib.request.Request(
                self.CHANGELOG_URL,
                headers={'User-Agent': 'ChroLens-Mimic-App'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read().decode('utf-8')
            
            # 簡單解析 HTML 提取更新日誌
            changelog = self._parse_changelog_from_html(html_content)
            
            return changelog
            
        except Exception as e:
            self.log(f"獲取更新日誌失敗: {e}")
            return "無法載入更新日誌，請訪問官網查看。"
    
    def _parse_changelog_from_html(self, html: str) -> str:
        """從 HTML 中提取更新日誌（簡單解析）"""
        try:
            # 尋找更新日誌區塊（根據實際網頁結構調整）
            import re
            
            # 嘗試找到版本資訊區塊
            pattern = r'<h[23].*?>(.*?v?\d+\.\d+\.\d+.*?)</h[23]>(.*?)(?=<h[23]|$)'
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            
            if matches:
                changelog = ""
                for title, content in matches[:10]:  # 最多取 10 個版本
                    # 清理 HTML 標籤
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_content = re.sub(r'<[^>]+>', '\n', content).strip()
                    clean_content = re.sub(r'\n+', '\n', clean_content)
                    
                    changelog += f"\n{'='*50}\n{clean_title}\n{'='*50}\n{clean_content}\n"
                
                return changelog if changelog else "更新日誌格式不符，請訪問官網查看。"
            else:
                return "無法解析更新日誌，請訪問官網查看。"
                
        except Exception as e:
            self.log(f"解析更新日誌失敗: {e}")
            return "解析失敗，請訪問官網查看。"
