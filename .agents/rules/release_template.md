# GitHub 釋出更新日誌 (Release Notes) 樣板

此文件定義了 ChroLens-Mimic 專案在發布新版本 (Release) 時，更新日誌的標準格式。未來的版本更新請務必依照此樣板來撰寫。

## 格式規範
1. 每個主功能區塊（例如「選擇視窗」、「指令編輯器」）作為獨立的段落。
2. 每個段落下，使用條列式（`-新增：`、`-修改：`、`-修復：` 等）列出變更細節。
3. 支援附上圖片預覽，並使用 HTML `<img>` 標籤調整寬高（若有需要展示 UI 變更）。
4. 各區塊之間使用分隔線 `──────────────────────────────────────` 隔開。
5. 最下方放置「已知Bug修復」或「其他系統優化」等雜項內容。

## 樣板範例

```markdown
選擇視窗：
-新增：icon捕捉、視窗強制切換選擇
-修改：字體放大
<img width="661" height="397" alt="image" src="https://github.com/user-attachments/assets/c1c535ac-cc7d-402e-9758-fd73447152e8" />
<img width="872" height="319" alt="image" src="https://github.com/user-attachments/assets/7c917494-f4e6-4615-9668-b5e38de0b3a5" />
──────────────────────────────────────
指令編輯器：
-新增：圖片辨識二值化(去除背景)功能
<img width="487" height="521" alt="image" src="https://github.com/user-attachments/assets/1562e42b-8129-4294-82ed-56ce39a1bfe7" />
<img width="487" height="521" alt="image" src="https://github.com/user-attachments/assets/4bc35dd8-79d5-4aa2-b2ec-ad4a54e20a03" />
──────────────────────────────────────
指令編輯器：
-新增：圖庫
<img width="1317" height="957" alt="image" src="https://github.com/user-attachments/assets/415593d1-f025-43e6-93bf-1e2882735126" />
e.g. 點擊先前辨識儲存過的"picb狩獵按鈕"圖示，會自動複製指令：
>辨識>picb狩獵按鈕, T=0s000
>左鍵點擊>picb狩獵按鈕, T=1s500
──────────────────────────────────────
已知Bug修復：主程式快捷鍵無法正常儲存
```
