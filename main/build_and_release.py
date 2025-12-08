"""
ChroLens_Mimic 自動打包並發布到 GitHub
整合打包、壓縮、上傳到 GitHub Releases 的完整流程

使用方法:
1. 首次使用需要設定 GitHub Token (一次性設定)
2. 更新 ChroLens_Mimic.py 中的 VERSION
3. 執行此腳本會自動完成打包並上傳到 GitHub

需要安裝:
pip install PyGithub
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

try:
    from github import Github, GithubException
except ImportError:
    print("錯誤: 需要安裝 PyGithub")
    print("請執行: pip install PyGithub")
    sys.exit(1)


class MimicReleaseBuilder:
    """Mimic 打包與發布工具"""
    
    def __init__(self):
        # 專案目錄
        self.project_dir = Path(__file__).parent
        self.main_file = self.project_dir / "ChroLens_Mimic.py"
        self.icon_file = self.project_dir / "umi_奶茶色.ico"
        
        # 輸出目錄
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.output_dir = self.dist_dir / "ChroLens_Mimic"
        
        # GitHub 設定
        self.github_repo = "Lucienwooo/ChroLens-Mimic"
        self.token_file = self.project_dir / ".github_token"
        
        # 讀取版本號
        self.version = self._read_version()
        
        print(f"\n{'='*60}")
        print(f"ChroLens_Mimic 自動打包與發布工具")
        print(f"版本: {self.version}")
        print(f"{'='*60}\n")
    
    def _read_version(self) -> str:
        """從主程式讀取版本號"""
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('VERSION ='):
                        version = line.split('=')[1].strip().strip('"\'')
                        return version
        except Exception as e:
            print(f"警告: 無法讀取版本號: {e}")
            return "2.7.2"
    
    def _get_github_token(self) -> str:
        """獲取 GitHub Token"""
        # 檢查是否已存在 token
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    token = f.read().strip()
                    if token:
                        return token
            except:
                pass
        
        # 直接使用預設 token
        token = "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"
        
        # 保存 token
        try:
            with open(self.token_file, 'w') as f:
                f.write(token)
            # 設定檔案為只讀（安全性）
            os.chmod(self.token_file, 0o600)
        except:
            pass
        
        return token
    
    def _extract_changelog(self) -> str:
        """提取當前版本的更新說明"""
        # 嘗試從版本說明文件讀取
        version_files = [
            self.project_dir / "VERSION_UPDATE_REPORT.md",
            self.project_dir / "UPDATE.md",
            self.project_dir / "CHANGELOG.md"
        ]
        
        for file_path in version_files:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 簡單提取前幾段作為更新說明
                        lines = content.split('\n')
                        changelog = []
                        for line in lines[:30]:  # 只取前30行
                            if line.strip():
                                changelog.append(line)
                        if changelog:
                            return '\n'.join(changelog)
                except:
                    pass
        
        return f"ChroLens_Mimic v{self.version} 更新\n\n包含功能改進與錯誤修復。"
    
    def _format_release_notes(self, version_description: str) -> str:
        """格式化 Release Notes"""
        
        notes = ""
        notes += f"## 📝 更新內容\n\n"
        notes += f"{version_description}\n\n"
        
        notes += "## 📦 安裝方式\n\n"
        notes += "### 方式一：自動更新（推薦）\n"
        notes += "1. 開啟 ChroLens_Mimic\n"
        notes += "2. 點擊「版本資訊」按鈕\n"
        notes += "3. 點擊「立即更新」自動下載並安裝\n\n"
        
        notes += "### 方式二：手動安裝\n"
        notes += f"1. 下載 `ChroLens_Mimic_v{self.version}.zip`\n"
        notes += "2. 解壓縮到任意位置\n"
        notes += "3. 執行 `ChroLens_Mimic.exe`\n\n"
        
        notes += "---\n\n"
        notes += f"📅 發布時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        notes += f"💻 適用系統: Windows 10/11\n"
        notes += f"🔧 需要管理員權限執行\n"
        
        return notes
    
    def clean(self):
        """清理舊檔案"""
        print("\n[1/7] 清理舊檔案...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                print(f"  - 刪除 {dir_path.name}/")
                try:
                    shutil.rmtree(dir_path, ignore_errors=False)
                except Exception as e:
                    print(f"  ⚠ 警告: {e}")
        
        # 清理 .spec 檔案
        for spec_file in self.project_dir.glob("*.spec"):
            try:
                spec_file.unlink()
                print(f"  - 刪除 {spec_file.name}")
            except:
                pass
        
        print("  ✓ 清理完成\n")
    
    def check_dependencies(self):
        """檢查必要的依賴檔案"""
        print("\n[2/7] 檢查專案檔案...")
        
        required_files = [
            "ChroLens_Mimic.py",
            "recorder.py",
            "text_script_editor.py",
            "version_manager.py",
            "version_info_dialog.py",
            "pack_safe.py"
        ]
        
        all_exist = True
        for file_name in required_files:
            file_path = self.project_dir / file_name
            if file_path.exists():
                print(f"  ✓ {file_name}")
            else:
                print(f"  ✗ {file_name} (缺少)")
                all_exist = False
        
        if not all_exist:
            raise Exception("缺少必要檔案")
        
        print("  ✓ 檔案檢查完成\n")
    
    def build_main(self):
        """執行打包腳本"""
        print("\n[3/7] 執行打包...")
        
        pack_script = self.project_dir / "pack_safe.py"
        
        if not pack_script.exists():
            raise Exception("找不到 pack_safe.py")
        
        # 執行 pack_safe.py
        result = subprocess.run(
            [sys.executable, str(pack_script)],
            cwd=str(self.project_dir),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  錯誤輸出:\n{result.stderr}")
            raise Exception("打包失敗")
        
        print("  ✓ 打包完成\n")
    
    def copy_additional_files(self):
        """複製額外的更新工具檔案"""
        print("\n[4/7] 複製更新工具...")
        
        files_to_copy = [
            "更新說明.txt"
        ]
        
        for file_name in files_to_copy:
            src = self.project_dir / file_name
            dst = self.output_dir / file_name
            
            if src.exists():
                try:
                    shutil.copy2(src, dst)
                    print(f"  ✓ {file_name}")
                except Exception as e:
                    print(f"  ⚠ {file_name}: {e}")
            else:
                print(f"  - {file_name} (不存在，跳過)")
        
        print("  ✓ 複製完成\n")
    
    def create_version_file(self):
        """創建版本文件"""
        print("\n[5/7] 創建版本文件...")
        
        version_file = self.output_dir / f"version{self.version}.txt"
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(f"ChroLens_Mimic v{self.version}\n")
            f.write(f"打包時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"自動打包與發布工具\n")
        
        print(f"  ✓ version{self.version}.txt 已創建\n")
    
    def create_zip(self) -> Path:
        """創建 ZIP 壓縮包"""
        print("\n[6/7] 創建 ZIP 壓縮包...")
        
        zip_filename = f"ChroLens_Mimic_v{self.version}.zip"
        zip_path = self.dist_dir / zip_filename
        
        if zip_path.exists():
            zip_path.unlink()
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    # 壓縮時保留目錄結構（從 ChroLens_Mimic 開始）
                    arcname = file_path.relative_to(self.dist_dir)
                    zipf.write(file_path, arcname)
                    
        file_size = zip_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ {zip_filename} ({file_size:.2f} MB)\n")
        
        return zip_path
    
    def create_github_release(self, zip_path: Path):
        """創建 GitHub Release 並上傳檔案"""
        print("\n[7/7] 發布到 GitHub...")
        
        # 獲取 Token
        token = self._get_github_token()
        
        # 連接 GitHub
        try:
            g = Github(token)
            repo = g.get_repo(self.github_repo)
            print(f"  ✓ 已連接到 {self.github_repo}")
        except GithubException as e:
            print(f"  ✗ GitHub 認證失敗: {e}")
            print("  請檢查 Token 權限")
            return False
        
        # 檢查 Release 是否已存在
        tag_name = f"v{self.version}"
        try:
            existing_release = repo.get_release(tag_name)
            print(f"  ⚠ Release {tag_name} 已存在，自動刪除並重新創建...")
            existing_release.delete_release()
            print(f"  ✓ 已刪除舊的 Release")
        except GithubException:
            pass  # Release 不存在，繼續
        
        # 提取更新說明
        version_description = self._extract_changelog()
        release_notes = self._format_release_notes(version_description)
        
        # 創建 Release
        try:
            print(f"  正在創建 Release {tag_name}...")
            release = repo.create_git_release(
                tag=tag_name,
                name=f"ChroLens_Mimic v{self.version}",
                message=release_notes,
                draft=False,
                prerelease=False
            )
            print(f"  ✓ Release 已創建")
        except GithubException as e:
            print(f"  ✗ 創建 Release 失敗: {e}")
            return False
        
        # 上傳 ZIP 檔案
        try:
            print(f"  正在上傳 {zip_path.name}...")
            release.upload_asset(
                str(zip_path),
                label=zip_path.name,
                content_type='application/zip'
            )
            print(f"  ✓ 檔案已上傳")
        except GithubException as e:
            print(f"  ✗ 上傳失敗: {e}")
            return False
        
        print(f"\n  🎉 發布成功!")
        print(f"  🔗 查看 Release: https://github.com/{self.github_repo}/releases/tag/{tag_name}")
        
        return True
    
    def _validate_before_build(self):
        """打包前驗證"""
        print("\n[0/7] 打包前驗證...")
        
        # 檢查版本號格式
        import re
        if not re.match(r'^\d+\.\d+(\.\d+)?$', self.version):
            print(f"  ⚠ 警告: 版本號格式不正確: {self.version}")
            return False
        else:
            print(f"  ✓ 版本號格式正確: {self.version}")
        
        # 檢查主程式檔案
        if not self.main_file.exists():
            print(f"  ✗ 找不到主程式: {self.main_file}")
            return False
        else:
            print(f"  ✓ 主程式存在: {self.main_file.name}")
        
        print("  ✓ 驗證通過\n")
        return True
    
    def build_and_release(self):
        """執行完整流程"""
        try:
            # 驗證
            if not self._validate_before_build():
                print("\n驗證失敗，已取消打包")
                sys.exit(1)
            
            self.clean()
            self.check_dependencies()
            self.build_main()
            self.copy_additional_files()
            self.create_version_file()
            zip_path = self.create_zip()
            
            # 自動上傳到 GitHub
            print("\n" + "="*60)
            print("正在自動上傳到 GitHub Releases...")
            print("="*60)
            
            success = self.create_github_release(zip_path)
            
            if success:
                print("\n" + "="*60)
                print("✅ 打包與發布完成！")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("⚠ 打包完成，但發布失敗")
                print(f"ZIP 檔案: {zip_path}")
                print("請手動上傳到 GitHub")
                print("="*60)
            
            print()
            
        except Exception as e:
            print(f"\n✗ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    builder = MimicReleaseBuilder()
    builder.build_and_release()
    
    input("\n按 Enter 鍵退出...")
