# 舊版升級到 2.7.2 指南

## 📋 問題分析

### 舊版本的更新機制

**2.7.2 之前的版本（如 2.7.1、2.6.x 等）：**
- ❌ 沒有「版本資訊」按鈕
- ❌ 沒有 `version_manager.py` 模組
- ❌ 使用舊的 `update_manager.py`、`update_dialog.py` 系統
- ❌ 無法自動檢測 2.7.2 版本

### 2.7.2 的新更新機制

- ✅ 基於 GitHub Releases API
- ✅ 使用批次腳本更新
- ✅ 新增「版本資訊」按鈕
- ✅ 新增 `version_manager.py` 和 `version_info_dialog.py`

---

## 🔄 升級方案

### 方案 1：手動下載完整版（推薦給一般使用者）⭐

**步驟：**
1. 前往 GitHub Releases：
   ```
   https://github.com/Lucienwooo/ChroLens-Mimic/releases/latest
   ```

2. 下載最新的 `ChroLens_Mimic_v2.7.2.zip`

3. 解壓縮到**新的資料夾**（建議不要直接覆蓋舊版）

4. 複製舊版的使用者資料（如有需要）：
   - 腳本檔案（`.json` 檔案）
   - 設定檔（如有）
   - 自訂範本（如有）

5. 執行新版的 `ChroLens_Mimic.exe`

6. 測試功能正常後，可刪除舊版資料夾

**優點：**
- ✅ 最安全、最可靠
- ✅ 保留舊版作為備份
- ✅ 避免檔案衝突

**缺點：**
- ⚠️ 需要手動複製使用者資料
- ⚠️ 需要更多磁碟空間

---

### 方案 2：使用批次腳本半自動更新（進階使用者）

我們已經增強了 `version_manager.py` 的批次腳本，使其能夠：

**自動處理的問題：**
1. ✅ 自動刪除舊版本的過時檔案：
   - `update_manager.pyc`
   - `update_manager_v2_deferred.pyc`
   - `update_dialog.pyc`

2. ✅ 自動備份舊版本到：
   ```
   backup\ChroLens_Mimic_backup_<舊版本號>\
   ```

3. ✅ 智能識別 ZIP 內的目錄結構
   - 處理有頂層目錄的 ZIP
   - 處理扁平結構的 ZIP

4. ✅ 覆蓋式更新所有檔案

**操作步驟：**

由於舊版本沒有「版本資訊」功能，需要手動執行以下步驟：

#### **步驟 1：下載更新包**
```
https://github.com/Lucienwooo/ChroLens-Mimic/releases/latest
下載 ChroLens_Mimic_v2.7.2.zip
```

#### **步驟 2：創建更新批次腳本**

在舊版 ChroLens_Mimic 的安裝目錄創建 `manual_update.bat`：

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo ChroLens_Mimic 手動更新工具
echo 從舊版本升級到 2.7.2
echo ========================================
echo.

REM 設定路徑
set "ZIP_FILE=%~dp0ChroLens_Mimic_v2.7.2.zip"
set "EXTRACT_DIR=%~dp0update_temp"
set "APP_DIR=%~dp0"

echo 檢查更新包...
if not exist "%ZIP_FILE%" (
    echo ❌ 找不到更新包: ChroLens_Mimic_v2.7.2.zip
    echo    請將更新包放在程式目錄中
    pause
    exit /b 1
)
echo ✓ 找到更新包

echo.
echo 請關閉 ChroLens_Mimic 程式後按任意鍵繼續...
pause >nul

echo.
echo 正在解壓縮更新包...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"
if %errorlevel% neq 0 (
    echo ❌ 解壓縮失敗
    pause
    exit /b 1
)
echo ✓ 解壓縮完成

echo.
echo 正在備份舊檔案...
if not exist "%APP_DIR%backup" mkdir "%APP_DIR%backup"
set "BACKUP_DIR=%APP_DIR%backup\backup_before_2.7.2_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_DIR=%BACKUP_DIR: =0%"
mkdir "%BACKUP_DIR%"
xcopy /E /I /Y "%APP_DIR%*" "%BACKUP_DIR%\" /EXCLUDE:%~f0 >nul 2>&1
echo ✓ 備份完成: %BACKUP_DIR%

echo.
echo 正在刪除舊版本檔案...
del /f /q "%APP_DIR%_internal\update_manager.pyc" 2>nul
del /f /q "%APP_DIR%_internal\update_manager_v2_deferred.pyc" 2>nul
del /f /q "%APP_DIR%_internal\update_dialog.pyc" 2>nul
del /f /q "%APP_DIR%update_manager.pyc" 2>nul
del /f /q "%APP_DIR%update_manager_v2_deferred.pyc" 2>nul
del /f /q "%APP_DIR%update_dialog.pyc" 2>nul
echo ✓ 清理完成

echo.
echo 正在更新檔案...
REM 找到解壓縮後的實際目錄
for /d %%D in ("%EXTRACT_DIR%\*") do (
    echo 正在從 %%D 複製檔案...
    xcopy /E /I /Y "%%D\*" "%APP_DIR%" >nul
    goto :copy_done
)
REM 如果沒有子目錄，直接從 EXTRACT_DIR 複製
xcopy /E /I /Y "%EXTRACT_DIR%\*" "%APP_DIR%" >nul
:copy_done
echo ✓ 更新完成

echo.
echo 正在清理臨時檔案...
rmdir /s /q "%EXTRACT_DIR%" 2>nul
echo ✓ 清理完成

echo.
echo ========================================
echo ✅ 更新成功！
echo ========================================
echo.
echo 備份位置: %BACKUP_DIR%
echo 如更新後有問題，可從備份還原
echo.
echo 按任意鍵啟動 ChroLens_Mimic...
pause >nul
start "" "%APP_DIR%ChroLens_Mimic.exe"
```

#### **步驟 3：執行更新**
1. 將 `ChroLens_Mimic_v2.7.2.zip` 放在舊版程式目錄
2. 雙擊執行 `manual_update.bat`
3. 等待更新完成
4. 程式自動啟動新版本

---

### 方案 3：直接替換 exe 檔案（最簡單但不推薦）⚠️

**步驟：**
1. 關閉舊版程式
2. 下載並解壓縮 `ChroLens_Mimic_v2.7.2.zip`
3. 複製 `ChroLens_Mimic.exe` 和 `_internal\` 整個資料夾
4. 覆蓋到舊版目錄

**問題：**
- ⚠️ 可能殘留舊版本的過時檔案
- ⚠️ 可能導致模組衝突
- ⚠️ 沒有備份

---

## 🎯 升級後的驗證

### 確認版本號

1. 開啟程式後，點擊「整體設定」
2. 查看「關於」按鈕下方是否有「版本資訊」按鈕
3. 點擊「版本資訊」，確認版本為 `v2.7.2`

### 測試新功能

1. **版本資訊功能：**
   - ✅ 能正常顯示版本資訊對話框
   - ✅ 能檢查 GitHub 更新
   - ✅ 能顯示更新日誌

2. **基本功能：**
   - ✅ 錄製功能正常
   - ✅ 播放功能正常
   - ✅ 編輯器功能正常
   - ✅ OCR 功能正常（如有使用）

### 檢查檔案結構

新版本應該包含：
```
ChroLens_Mimic/
├── ChroLens_Mimic.exe
├── _internal/
│   ├── version_manager.pyc          # ✅ 新檔案
│   ├── version_info_dialog.pyc      # ✅ 新檔案
│   ├── (不應該有 update_manager.pyc)        # ❌ 舊檔案應該被刪除
│   ├── (不應該有 update_dialog.pyc)         # ❌ 舊檔案應該被刪除
│   └── ... (其他依賴)
├── images/
├── TTF/
└── backup/                           # ✅ 備份目錄
    └── ChroLens_Mimic_backup_<舊版本>/
```

---

## 🔧 常見問題排除

### 問題 1：更新後程式無法啟動

**可能原因：**
- 檔案不完整
- 權限問題
- 舊檔案衝突

**解決方案：**
1. 從 `backup\` 資料夾還原舊版本
2. 使用方案 1（手動下載完整版到新資料夾）
3. 確認以管理員身份執行

### 問題 2：更新後找不到「版本資訊」按鈕

**可能原因：**
- 更新不完整
- 快取問題

**解決方案：**
1. 完全關閉程式（檢查工作管理員）
2. 重新啟動程式
3. 如仍無效，重新使用方案 1 安裝

### 問題 3：舊版本的腳本檔案不見了

**預防措施：**
- 更新前手動備份 `.json` 腳本檔案
- 備份位置：`backup\ChroLens_Mimic_backup_<版本號>\`

**還原方法：**
```
從 backup\ChroLens_Mimic_backup_<舊版本>\ 複製 .json 檔案回主目錄
```

---

## 📝 給開發者的建議

### 未來版本的相容性策略

1. **版本遷移腳本：**
   - 為重大架構變更創建專用遷移腳本
   - 自動檢測並清理過時檔案

2. **發布說明：**
   - 在 GitHub Release 明確標註需要完整重新安裝的版本
   - 提供詳細的升級指南

3. **向後相容性：**
   - 保留舊版本的設定檔格式支援
   - 提供資料遷移工具

4. **自動檢測舊版本：**
   ```python
   # 未來可在程式啟動時加入
   def detect_old_version():
       old_modules = [
           '_internal/update_manager.pyc',
           '_internal/update_dialog.pyc'
       ]
       if any(os.path.exists(m) for m in old_modules):
           # 提示使用者這是從舊版升級
           # 提供清理工具
   ```

---

## ✅ 總結

### 推薦升級方式

| 使用者類型 | 推薦方案 | 原因 |
|-----------|---------|------|
| 一般使用者 | **方案 1** | 最安全、最可靠 |
| 進階使用者 | **方案 2** | 自動化程度高、有備份 |
| 測試用途 | 方案 3 | 快速但有風險 |

### 重要提醒

⚠️ **2.7.2 是架構變更版本**
- 從舊版（2.7.1 及以前）升級到 2.7.2 **建議使用方案 1**
- 這是一次性的升級成本
- 升級到 2.7.2 後，未來版本（2.7.3+）可使用內建的自動更新功能

✅ **從 2.7.2 開始**
- 所有後續版本都可透過「版本資訊」自動更新
- 無需再手動下載或執行批次腳本
- 更新流程全自動化

---

**製作日期：** 2025年12月8日  
**適用版本：** 從任何舊版本升級到 v2.7.2
