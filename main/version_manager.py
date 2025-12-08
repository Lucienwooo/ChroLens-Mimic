# -*- coding: utf-8 -*-
"""
版本管理器 - ChroLens_Mimic
負責檢查更新和版本資訊顯示

更新機制：基於 GitHub Releases
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
            {
                'version': '2.7.3',
                'download_url': 'https://...',
                'release_notes': '更新內容...',
                'published_at': '2025-12-08T...'
            }
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
        """
        下載更新檔案
        
        Args:
            download_url: 下載連結
            progress_callback: 進度回調函數 callback(downloaded, total)
            
        Returns:
            下載檔案的路徑，失敗返回 None
        """
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
        """
        解壓縮更新檔案
        
        Args:
            zip_path: zip 檔案路徑
            
        Returns:
            解壓縮目錄路徑，失敗返回 None
        """
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
        應用更新（使用批次腳本在程式關閉後替換檔案）
        
        Args:
            extract_dir: 解壓縮目錄
            restart_after: 是否在更新後重新啟動
            
        Returns:
            是否成功創建更新腳本
        """
        try:
            self.log("準備應用更新...")
            
            # 創建批次更新腳本
            batch_script = os.path.join(tempfile.gettempdir(), 'chrolens_update.bat')
            
            # 尋找解壓縮後的實際程式目錄
            # 處理 ZIP 可能包含頂層目錄的情況
            actual_source_dir = extract_dir
            for item in os.listdir(extract_dir):
                item_path = os.path.join(extract_dir, item)
                if os.path.isdir(item_path) and 'ChroLens_Mimic' in item:
                    # 如果 ZIP 內有 ChroLens_Mimic 目錄，使用它
                    actual_source_dir = item_path
                    break
            
            # 批次腳本內容
            script_content = f"""@echo off
chcp 65001 >nul
echo ========================================
echo ChroLens_Mimic 更新程式
echo ========================================
echo.
echo 正在等待主程式關閉...
timeout /t 3 /nobreak >nul

echo.
echo 正在備份舊檔案...
if not exist "{self.app_dir}\\backup" mkdir "{self.app_dir}\\backup"
if exist "{self.app_dir}\\backup\\ChroLens_Mimic_backup_{self.current_version}" (
    rmdir /s /q "{self.app_dir}\\backup\\ChroLens_Mimic_backup_{self.current_version}"
)
mkdir "{self.app_dir}\\backup\\ChroLens_Mimic_backup_{self.current_version}"
xcopy /E /I /Y "{self.app_dir}\\*" "{self.app_dir}\\backup\\ChroLens_Mimic_backup_{self.current_version}\\" >nul 2>&1

echo.
echo 正在更新檔案...
echo 來源目錄: {actual_source_dir}
echo 目標目錄: {self.app_dir}

REM 先刪除舊版本特有的過時檔案（避免衝突）
if exist "{self.app_dir}\\_internal\\update_manager.pyc" del /f /q "{self.app_dir}\\_internal\\update_manager.pyc" >nul 2>&1
if exist "{self.app_dir}\\_internal\\update_manager_v2_deferred.pyc" del /f /q "{self.app_dir}\\_internal\\update_manager_v2_deferred.pyc" >nul 2>&1
if exist "{self.app_dir}\\_internal\\update_dialog.pyc" del /f /q "{self.app_dir}\\_internal\\update_dialog.pyc" >nul 2>&1
if exist "{self.app_dir}\\update_manager.pyc" del /f /q "{self.app_dir}\\update_manager.pyc" >nul 2>&1
if exist "{self.app_dir}\\update_manager_v2_deferred.pyc" del /f /q "{self.app_dir}\\update_manager_v2_deferred.pyc" >nul 2>&1
if exist "{self.app_dir}\\update_dialog.pyc" del /f /q "{self.app_dir}\\update_dialog.pyc" >nul 2>&1

REM 複製新檔案（覆蓋舊檔案）
xcopy /E /I /Y "{actual_source_dir}\\*" "{self.app_dir}\\" >nul

echo.
echo 更新完成！
"""
            
            if restart_after:
                # 尋找可執行檔
                exe_name = "ChroLens_Mimic.exe" if os.path.exists(os.path.join(self.app_dir, "ChroLens_Mimic.exe")) else "python.exe"
                script_content += f"""
echo 正在重新啟動程式...
timeout /t 1 /nobreak >nul
start "" "{os.path.join(self.app_dir, exe_name)}"
"""
            
            script_content += """
echo.
echo 按任意鍵關閉此視窗...
pause >nul
del "%~f0"
"""
            
            # 寫入批次檔
            with open(batch_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.log(f"更新腳本已創建: {batch_script}")
            
            # 執行批次檔（非同步）
            subprocess.Popen(['cmd', '/c', batch_script], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            return True
            
        except Exception as e:
            self.log(f"創建更新腳本失敗: {e}")
            return False
    
    def fetch_changelog(self) -> str:
        """
        從官網獲取更新日誌
        
        Returns:
            更新日誌文字
        """
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
