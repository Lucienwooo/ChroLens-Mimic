# -*- coding: utf-8 -*-
import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import tempfile
import subprocess
import time
from typing import Optional, Dict, Callable
from packaging import version as pkg_version

class VersionManager:
    def __init__(self, github_repo: str, current_version: str, logger: Optional[Callable] = None):
        self.github_repo = github_repo
        self.current_version = current_version
        self._logger = logger or (lambda msg: print(f"[VersionManager] {msg}"))
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
            if os.path.basename(self.app_dir) in ['main', 'src']:
                self.app_dir = os.path.dirname(self.app_dir)

    def log(self, msg: str):
        self._logger(msg)

    def check_for_updates(self) -> Optional[Dict]:
        try:
            self.log(f"正在檢查 {self.github_repo} 的更新...")
            req = urllib.request.Request(self.api_url, headers={'User-Agent': 'ChroLens-App'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            latest_version = data['tag_name'].lstrip('v')
            if pkg_version.parse(latest_version) > pkg_version.parse(self.current_version):
                download_url = None
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.zip'):
                        download_url = asset['browser_download_url']
                        break
                if not download_url and data.get('assets'):
                    download_url = data['assets'][0]['browser_download_url']
                return {
                    'version': latest_version,
                    'download_url': download_url,
                    'release_notes': data.get('body', '無更新說明')
                }
            return None
        except Exception as e:
            self.log(f"檢查更新失敗: {e}")
            return None

    def download_update(self, download_url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        try:
            temp_dir = tempfile.mkdtemp(prefix='chrolens_update_')
            zip_path = os.path.join(temp_dir, 'update.zip')
            urllib.request.urlretrieve(download_url, zip_path, 
                                        lambda b, s, t: progress_callback(b*s, t) if progress_callback else None)
            return zip_path
        except Exception as e:
            self.log(f"下載失敗: {e}"); return None

    def extract_update(self, zip_path: str) -> Optional[str]:
        try:
            extract_dir = os.path.join(os.path.dirname(zip_path), 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(extract_dir)
            return extract_dir
        except Exception as e:
            self.log(f"解壓失敗: {e}"); return None

    def apply_update(self, extract_dir: str, restart_after: bool = True) -> bool:
        try:
            src_dir = extract_dir
            files = os.listdir(extract_dir)
            if len(files) == 1 and os.path.isdir(os.path.join(extract_dir, files[0])):
                src_dir = os.path.join(extract_dir, files[0])
            bat = os.path.join(self.app_dir, 'update_temp.bat')
            exe = os.path.basename(sys.executable)
            content = f'''@echo off
timeout /t 2 /nobreak >nul
taskkill /F /IM "{exe}" >nul 2>&1
robocopy "{src_dir}" "{self.app_dir}" /E /IS /IT /R:3 /W:1
start "" "{sys.executable if getattr(sys, "frozen", False) else "python"}" {"" if getattr(sys, "frozen", False) else sys.argv[0]}
del "%~f0"
'''
            with open(bat, 'w', encoding='utf-8') as f: f.write(content)
            subprocess.Popen(['cmd', '/c', 'start', '', '/min', bat], shell=True)
            return True
        except Exception as e:
            self.log(f"更新失敗: {e}"); return False
