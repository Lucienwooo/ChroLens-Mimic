"""
ChroLens_Mimic 更新管理器 - 方案3: 延遲更新機制
程式關閉時僅下載,下次啟動時進行檔案替換
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path


class PendingUpdateManager:
    """
    延遲更新管理器
    處理在程式啟動時檢查並執行待處理的更新
    """
    
    def __init__(self, app_dir=None):
        """
        初始化
        
        Args:
            app_dir: 應用程式目錄
        """
        if app_dir is None:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.app_dir = Path(app_dir)
        self.pending_file = self.app_dir / "pending_update.json"
        self.log_file = self.app_dir / "update_log_v3.txt"
    
    def log(self, message):
        """記錄日誌"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except:
            pass
    
    def mark_pending_update(self, source_dir, version):
        """
        標記待處理的更新
        
        Args:
            source_dir: 已下載的更新檔案目錄
            version: 版本號
            
        Returns:
            bool: 是否成功標記
        """
        try:
            pending_data = {
                "source_dir": str(source_dir),
                "version": version,
                "marked_time": time.time(),
                "status": "pending"
            }
            
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                json.dump(pending_data, f, indent=2, ensure_ascii=False)
            
            self.log(f"✓ 已標記待處理更新: {version}")
            self.log(f"  來源目錄: {source_dir}")
            self.log("  提示: 下次啟動程式時將自動完成更新")
            
            return True
            
        except Exception as e:
            self.log(f"✗ 標記更新失敗: {e}")
            return False
    
    def has_pending_update(self):
        """
        檢查是否有待處理的更新
        
        Returns:
            bool: 是否有待更新
        """
        return self.pending_file.exists()
    
    def get_pending_update_info(self):
        """
        獲取待處理更新的資訊
        
        Returns:
            dict or None: 更新資訊
        """
        if not self.has_pending_update():
            return None
        
        try:
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"讀取待更新資訊失敗: {e}")
            return None
    
    def apply_pending_update(self):
        """
        應用待處理的更新
        這個方法應該在程式啟動的最早階段調用
        
        Returns:
            bool: 更新是否成功
        """
        if not self.has_pending_update():
            return True  # 沒有待更新,視為成功
        
        self.log("=" * 60)
        self.log("方案 3: 延遲更新機制 - 啟動時更新")
        self.log("=" * 60)
        
        # 讀取待更新資訊
        update_info = self.get_pending_update_info()
        if not update_info:
            self.log("✗ 無法讀取更新資訊")
            return False
        
        source_dir = Path(update_info['source_dir'])
        version = update_info['version']
        
        self.log(f"發現待處理更新: {version}")
        self.log(f"來源目錄: {source_dir}")
        
        if not source_dir.exists():
            self.log("✗ 更新檔案目錄不存在")
            self._cleanup_pending()
            return False
        
        # 執行更新
        try:
            success = self._do_update(source_dir)
            
            if success:
                self.log("✓ 更新成功!")
                self._cleanup_pending()
                
                # 清理臨時目錄
                try:
                    # 確保不是測試目錄才清理
                    temp_parent = source_dir.parent
                    if "ChroLens_Update" in str(temp_parent) and "Test" not in str(temp_parent):
                        shutil.rmtree(temp_parent, ignore_errors=True)
                        self.log(f"✓ 已清理臨時目錄: {temp_parent}")
                    else:
                        self.log(f"  跳過清理 (測試模式): {temp_parent}")
                except:
                    pass
                
                return True
            else:
                self.log("✗ 更新失敗")
                return False
                
        except Exception as e:
            self.log(f"✗ 更新過程發生錯誤: {e}")
            return False
    
    def _do_update(self, source_dir):
        """
        執行實際的檔案更新
        
        Args:
            source_dir: 來源目錄
            
        Returns:
            bool: 是否成功
        """
        self.log("\n步驟 1: 清理舊備份...")
        for old_file in self.app_dir.glob("*.old"):
            try:
                old_file.unlink()
                self.log(f"  清理: {old_file.name}")
            except:
                pass
        
        # 步驟 2: 處理 exe (如果有)
        self.log("\n步驟 2: 更新主程式...")
        new_exe = source_dir / "ChroLens_Mimic.exe"
        old_exe = self.app_dir / "ChroLens_Mimic.exe"
        
        if new_exe.exists():
            # 這時程式剛啟動,不應該有檔案鎖,但還是做保護
            if old_exe.exists():
                try:
                    # 備份舊 exe
                    backup_exe = self.app_dir / "ChroLens_Mimic.exe.old"
                    shutil.copy2(old_exe, backup_exe)
                    self.log("  已備份舊版 exe")
                except Exception as e:
                    self.log(f"  備份失敗: {e}")
                
                try:
                    # 刪除舊 exe
                    old_exe.unlink()
                    self.log("  已刪除舊版 exe")
                except Exception as e:
                    self.log(f"  ✗ 無法刪除舊版 exe: {e}")
                    return False
            
            # 複製新 exe
            try:
                shutil.copy2(new_exe, old_exe)
                self.log(f"  ✓ 已更新 exe ({old_exe.stat().st_size:,} bytes)")
            except Exception as e:
                self.log(f"  ✗ 複製 exe 失敗: {e}")
                return False
        
        # 步驟 3: 更新其他檔案
        self.log("\n步驟 3: 更新其他檔案...")
        success_count = 0
        fail_count = 0
        
        for item in source_dir.rglob("*"):
            if not item.is_file():
                continue
            
            # 跳過 exe (已處理)
            if item.name == "ChroLens_Mimic.exe":
                continue
            
            # 計算相對路徑
            rel_path = item.relative_to(source_dir)
            dst_path = self.app_dir / rel_path
            
            # 確保目標目錄存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 複製檔案
            try:
                shutil.copy2(item, dst_path)
                success_count += 1
            except Exception as e:
                self.log(f"  ✗ 複製失敗: {rel_path} - {e}")
                fail_count += 1
        
        self.log(f"  完成: {success_count} 個成功, {fail_count} 個失敗")
        
        return fail_count == 0 or success_count > 0
    
    def _cleanup_pending(self):
        """清理待更新標記"""
        try:
            if self.pending_file.exists():
                self.pending_file.unlink()
                self.log("  已清理更新標記")
        except:
            pass
    
    def cancel_pending_update(self):
        """
        取消待處理的更新
        
        Returns:
            bool: 是否成功取消
        """
        update_info = self.get_pending_update_info()
        if update_info:
            # 清理下載的檔案
            source_dir = Path(update_info['source_dir'])
            if source_dir.exists():
                try:
                    shutil.rmtree(source_dir.parent, ignore_errors=True)
                    self.log(f"✓ 已清理下載檔案: {source_dir.parent}")
                except:
                    pass
        
        # 刪除標記
        self._cleanup_pending()
        self.log("✓ 已取消待處理的更新")
        return True


def download_update_only(update_manager, download_url, target_dir):
    """
    僅下載更新,不立即安裝
    這個函數應該整合到原有的 UpdateManager 中
    
    Args:
        update_manager: UpdateManager 實例
        download_url: 下載網址
        target_dir: 目標目錄
        
    Returns:
        tuple: (success, extracted_dir)
    """
    import tempfile
    import zipfile
    import urllib.request
    
    temp_dir = Path(tempfile.gettempdir()) / f"ChroLens_Update_{update_manager._latest_version}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = temp_dir / "update.zip"
    
    try:
        # 下載
        print(f"下載更新檔案...")
        urllib.request.urlretrieve(download_url, zip_path)
        print(f"✓ 下載完成: {zip_path.stat().st_size:,} bytes")
        
        # 解壓縮
        print("解壓縮...")
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"✓ 解壓縮完成: {extract_dir}")
        
        # 清理 zip
        zip_path.unlink()
        
        return True, str(extract_dir)
        
    except Exception as e:
        print(f"✗ 下載失敗: {e}")
        return False, None


if __name__ == "__main__":
    """
    測試延遲更新機制
    
    用法:
        python update_manager_v2_deferred.py mark <source_dir> <version>  # 標記待更新
        python update_manager_v2_deferred.py check                         # 檢查待更新
        python update_manager_v2_deferred.py apply                         # 應用待更新
        python update_manager_v2_deferred.py cancel                        # 取消待更新
    """
    if len(sys.argv) < 2:
        print("用法:")
        print("  mark <source_dir> <version>  - 標記待處理更新")
        print("  check                        - 檢查待處理更新")
        print("  apply                        - 應用待處理更新")
        print("  cancel                       - 取消待處理更新")
        sys.exit(1)
    
    manager = PendingUpdateManager()
    command = sys.argv[1]
    
    if command == "mark":
        if len(sys.argv) < 4:
            print("用法: mark <source_dir> <version>")
            sys.exit(1)
        source_dir = sys.argv[2]
        version = sys.argv[3]
        manager.mark_pending_update(source_dir, version)
    
    elif command == "check":
        if manager.has_pending_update():
            info = manager.get_pending_update_info()
            print(f"有待處理更新:")
            print(f"  版本: {info['version']}")
            print(f"  來源: {info['source_dir']}")
            print(f"  標記時間: {time.ctime(info['marked_time'])}")
        else:
            print("沒有待處理更新")
    
    elif command == "apply":
        success = manager.apply_pending_update()
        sys.exit(0 if success else 1)
    
    elif command == "cancel":
        manager.cancel_pending_update()
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
