# ChroLens Mimic 專案功能與架構總覽 (2026 2.8.7版)

這份文件詳細記錄了目前「服役中」的系統架構，以及圖形化介面上各個按鈕的功能對應，協助您在未來進行開發或維護時，能夠快速掌握整個專案的全貌，避免不小心覆蓋到正常運作的核心模組。

---

## 📂 第一部分：現役核心程式碼架構解析

經過全域掃描，並清理了無用的備份與舊版路由後，目前的系統架構非常清晰且職責分明。**這些檔案沒有重複或冗餘，全部都在協同運作中**。

### 1. 核心啟動與控制器 (Root)

- **`ChroLens_Mimic.py`**：整個程式的主入口。負責初始化介面、設定全域熱鍵、加載各項 AI 視覺庫，並擔任各種模組（排程、圖庫、編輯器）的中樞神經。

### 2. 巨集與任務排程 (core)

- **`core/recorder.py`**：負責錄製使用者的滑鼠點擊與鍵盤輸入。這裡面使用的是 `pynput.keyboard.Listener` 來「捕捉所有的按鍵動作」以產生腳本。
- **`core/scheduler.py`**：處理任務的定時、重複執行邏輯 (ScheduleManager)。

### 3. 文字指令解析器 (parser)

- **`parser/command_lang.py`**：核心語法編譯器。負責將 `>等待圖片>pic`、`>點擊>x,y` 這種人類可讀的腳本，翻譯成 Python 實際可以執行的動作陣列。
- **`parser/editor_parser.py`**：文字編輯器專用的擴充模組，用來解析使用者在編輯器中輸入的即時內容，提供語法高亮、行號對齊等功能。

### 4. 使用者介面 (ui)

- **`ui/text_script_editor.py`**：最龐大的 UI 模組。包含了「文字指令編輯器」以及附屬的「圖片圖庫 (ImageGallery)」的全部視覺佈局與事件綁定。
- **`ui/editor_flowchart.py`**：流程圖生成工具。是編輯器用來繪製視覺化流程圖的擴充模組。
- **`ui/key_dialog.py`**：彈出的小視窗，專門用來讓使用者按下鍵盤並「捕捉單一按鍵」（例如用來設定快捷鍵）。這與 `recorder` 或 `pynput_hotkey` 完全不衝突，職責僅限於 UI 輸入。
- **`ui/window_selector.py`**：提供使用者選擇系統視窗的介面。
- **`ui/about.py`, `version_info_dialog.py`**：關於我們、版本資訊的簡單展示視窗。

### 5. 工具與底層邏輯 (utils)

- **`utils/pynput_hotkey.py`**：全域熱鍵管理器。負責監聽像是 `F9` 啟動、`F10` 停止等全域指令。
- **`utils/bezier_mouse.py`**：模擬真人滑鼠移動軌跡的演算法（貝茲曲線）。
- **`utils/db_manager.py`**：SQLite 資料庫管理器，專門用來替圖庫的圖片建立索引與快速搜尋。
- **`utils/script_io.py`**：處理腳本檔案的存檔與讀取。
- **`utils/lang.py`, `utils.py`, `version_manager.py`**：多國語言包、通用工具（如視窗置中、載入圖示）、版本檢查。

### 6. 視覺與 AI 引擎 (vision)

- **`vision/image_matcher.py`**：OpenCV 基礎的傳統圖片比對引擎（SSIM 等），用於尋找畫面中的特定圖片。
- **`vision/ocr_trigger.py`**：負責 PaddleOCR / ddddocr 的文字辨識與驗證碼破解。
- **`vision/yolo_detector.py`**：基於 YOLO 模型的進階物件偵測。

---

## 🖥️ 第二部分：文字編輯器與圖庫 UI 功能對應清單

以下列出 `text_script_editor.py` 中所有的重要按鈕，以及它們按下去後會觸發什麼底層邏輯。未來要調整功能時，請參考這個對應表。

### 【主編輯器區域】

| UI 按鈕 / 功能                     | 觸發的函式 (Function) | 功能說明                                                    |
| :--------------------------------- | :-------------------- | :---------------------------------------------------------- |
| **讀取 (Load)**                    | `_load_script`        | 呼叫 `script_io.py` 從硬碟讀取腳本內容到文字框。            |
| **儲存 (Save)**                    | `_save_script`        | 將目前文字框的內容存回 `.txt`。                             |
| **另存 (Save As)**                 | `_save_as_script`     | 跳出對話框讓使用者選擇新路徑儲存。                          |
| **全螢幕切換**                     | `_toggle_fullscreen`  | 移除/恢復視窗邊框，最大化編輯器。                           |
| **清空 (Clear)**                   | `_clear_text`         | 清空文字編輯區。                                            |
| **圖庫 (Gallery)**                 | `_open_image_gallery` | 呼叫並顯示 `ImageGalleryViewer` (圖庫對話視窗)。            |
| **鍵盤/滑鼠/流程等快捷輸入列**     | `_add_action_*`       | 將對應的巨集語法（如 `>左鍵點擊, T=1s000`）插入到游標位置。 |
| **文字高亮 (Syntax Highlighting)** | `_on_text_modified`   | 每次輸入時自動解析正規表達式，將特殊字詞上色。              |

### 【圖庫區域 (ImageGalleryViewer)】

| UI 按鈕 / 功能              | 觸發的函式 (Function)  | 功能說明                                                                          |
| :-------------------------- | :--------------------- | :-------------------------------------------------------------------------------- |
| **左側資料夾清單**          | `_on_folder_select`    | 點擊時設定 `current_folder`，然後觸發圖片重新載入。                               |
| **＋ (新增資料夾)**         | `_create_folder`       | 建立新的目錄，並同步更新資料庫。                                                  |
| **確認修改 (重新命名)**     | `_rename_image`        | 透過 `os.rename` 更改實體檔案名稱與資料庫。                                       |
| **點擊自動關閉 (Checkbox)** | 無特定觸發             | 勾選時設定 `auto_close_var` 為 True。複製指令時會連帶呼叫 `_on_gallery_closing`。 |
| **圖庫資料夾**              | `_open_gallery_folder` | 使用 `os.startfile` 打開實體資料夾的檔案總管。                                    |
| **時間順序 / 命名 (排序)**  | `_toggle_sort`         | 切換 `sort_by` 與 `sort_asc` 狀態，然後重新渲染圖片清單。                         |
| **批次移動**                | `_toggle_batch_mode`   | 開啟多選模式，關閉單點自動複製指令的功能，將點擊改為「選取狀態切換」。            |
| **確認移動**                | `_confirm_batch_move`  | 呼叫 `shutil.move` 將選取的圖片移動至左側清單選擇的目標資料夾。                   |
| **右側圖片 (點擊)**         | `on_click`             | 若非批次模式：清除剪貼簿並複製 `>圖>檔名` 指令，依設定決定是否關閉圖庫。          |
| **滾輪滑動**                | `_on_mousewheel`       | 連動 `canvas.yview_scroll` 來移動圖片視圖。                                       |

---

> 💡 **安心提示**
> 經過詳細檢查，目前現役系統中**並沒有**互相衝突的熱鍵捕捉功能。
> `recorder.py` (用來錄製滑鼠軌跡)、`pynput_hotkey.py` (用來監聽快捷鍵如 F9 啟動) 以及 `key_dialog.py` (UI 小視窗捕捉) 雖然都涉及按鍵輸入，但它們所處的執行環境與目的都完全切開，不會再發生覆蓋問題，您可以高枕無憂。
