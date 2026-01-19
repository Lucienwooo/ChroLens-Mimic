# ChroLens Mimic

<div align="center">

![ChroLens_Mimic](./pic/clm2.6.png)

**🎯 強大的 Windows 自動化工具 | Powerful Windows Automation Tool**

[![GitHub release](https://img.shields.io/github/v/release/LucienWooo/ChroLens_Mimic?style=flat-square)](https://github.com/LucienWooo/ChroLens_Mimic/releases)
[![License](https://img.shields.io/github/license/LucienWooo/ChroLens_Mimic?style=flat-square)](./LICENSE)
[![Discord](https://img.shields.io/discord/YOUR_DISCORD_ID?style=flat-square&logo=discord)](https://discord.gg/72Kbs4WPPn)

[📖 完整文件](https://lucienwooo.github.io/ChroLens_Mimic/) | [🚀 快速開始](./QUICK_START.md) | [📦 範例模板](./templates/) | [💬 Discord 社群](https://discord.gg/72Kbs4WPPn)

</div>

---

## ✨ 特色功能

### 🎮 核心功能
- **🎬 錄製與播放** - 一鍵錄製滑鼠/鍵盤操作,自動生成腳本
- **🖼️ 圖片辨識** - 智能找圖並點擊,適應不同解析度
- **🤖 AI 物件偵測** - 整合 YOLO,更準確的目標識別
- **📝 OCR 文字辨識** - 辨識螢幕文字,實現智能判斷
- **🎨 圖形化編輯** - 類似 GitHub Actions 的流程圖顯示

### 🔥 進階功能
- **⚡ 觸發器系統** - 定時觸發、條件觸發、優先偵測
- **🔄 流程控制** - 循環、條件判斷、標籤跳轉
- **🔢 變數系統** - 記錄狀態、計數、動態判斷
- **🤖 狀態機** - 實現複雜的 AI 邏輯
- **⚙️ 多種執行模式** - 支援 pynput、pyautogui、win32api

---

## 🚀 快速開始

### 方法一: 使用安裝包 (推薦)
1. 下載最新版本: [Releases](https://github.com/LucienWooo/ChroLens_Mimic/releases)
2. 執行 `ChroLens_Mimic_Setup.exe`
3. 按照提示完成安裝
4. 雙擊桌面圖示啟動

### 方法二: 從原始碼執行
```bash
# 1. Clone 專案
git clone https://github.com/LucienWooo/ChroLens_Mimic.git
cd ChroLens_Mimic

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 啟動程式
cd main
python ChroLens_Mimic.py
```

### 第一個腳本
```
# 每秒點擊螢幕中央
#開始
>左鍵點擊(960,540), 延遲100ms, T=0s000
>延遲1000ms, T=0s100
>跳轉#開始, T=1s100
```

**更多範例請查看** → [📦 範例模板庫](./templates/)

---

## 📚 使用場景

### 🎮 遊戲自動化
- ✅ 自動戰鬥、自動撿取道具
- ✅ 自動任務、自動升級
- ✅ 自動簽到、自動領取獎勵
- ✅ 掛機腳本、循環打怪

### 💼 辦公自動化
- ✅ Excel 批次處理
- ✅ 自動填寫表單
- ✅ 定時發送訊息
- ✅ 重複性資料整理

### 🧪 測試自動化
- ✅ UI 自動化測試
- ✅ 重複性操作測試
- ✅ 壓力測試

### 🎨 創意應用
- ✅ 自動繪圖
- ✅ 批次處理圖片
- ✅ 自動化影片剪輯

---

## 🎯 核心優勢

### vs TinyTask
- ✅ 支援圖片辨識 (TinyTask 只能固定座標)
- ✅ 支援條件判斷 (TinyTask 只能線性執行)
- ✅ 支援觸發器系統 (TinyTask 無背景監控)
- ✅ 文字腳本可編輯 (TinyTask 二進位格式)

### vs AutoHotkey
- ✅ 圖形化介面,無需學習語法
- ✅ 一鍵錄製,自動生成腳本
- ✅ 內建圖片辨識和 AI 偵測
- ✅ 視覺化流程圖顯示

### vs Python + PyAutoGUI
- ✅ 無需寫程式碼
- ✅ 即時錄製與播放
- ✅ 內建完整的自動化功能
- ✅ 友善的使用者介面

---

## 📖 文件與資源

### 📚 學習資源
- [🚀 快速入門指南](./QUICK_START.md) - 5 分鐘上手
- [📦 範例模板庫](./templates/) - 實用腳本範例
- [📖 完整指令文檔](https://lucienwooo.github.io/ChroLens_Mimic/) - 所有指令說明
- [🎨 圖形模式教學](./web/src/app/script-editor/) - 視覺化編輯

### 🔧 進階主題
- [🤖 YOLO AI 整合](./main/yolo_detector.py) - AI 物件偵測
- [📝 OCR 文字辨識](./main/ocr_trigger.py) - 文字識別
- [🎯 狀態機系統](./templates/05_進階應用_狀態機戰鬥AI.txt) - 複雜邏輯
- [⚡ 觸發器系統](./templates/03_遊戲掛機_自動撿取.txt) - 背景監控

---

## 🛠️ 技術架構

### 核心技術
- **Python 3.8+** - 主要開發語言
- **Tkinter** - GUI 框架
- **OpenCV** - 圖片辨識
- **YOLOv8** - AI 物件偵測
- **Tesseract OCR** - 文字辨識
- **pynput / pyautogui** - 輸入控制

### 專案結構
```
ChroLens_Mimic/
├── main/                  # 主程式
│   ├── ChroLens_Mimic.py # 主視窗
│   ├── recorder.py       # 錄製/播放引擎
│   ├── text_script_editor.py # 文字編輯器
│   ├── yolo_detector.py  # YOLO 偵測器
│   └── ocr_trigger.py    # OCR 辨識器
├── templates/            # 範例模板
├── web/                  # Web 文件
├── pic/                  # 圖片資源
└── installer/            # 安裝程式
```

---

## 🤝 貢獻指南

歡迎貢獻! 你可以:
- 🐛 回報 Bug
- 💡 提出新功能建議
- 📝 改進文件
- 🎨 分享你的腳本範例

### 如何貢獻
1. Fork 本專案
2. 建立你的分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 💸 支持作者

如果這個專案幫助了你,請考慮支持作者!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/B0B51FBVA8)

**這些程式幫你省下的時間,分一點來抖內吧!給我錢錢!** 💰  
**These scripts saved you time—share a bit and donate. Give me money!** 💰  
**このツールで浮いた時間、ちょっとだけ投げ銭して?お金ちょうだい!** 💰

---

## 📞 聯絡與支援

- 💬 **Discord 社群**: [加入 ChroLens Discord](https://discord.gg/72Kbs4WPPn)
- 🐛 **回報問題**: [GitHub Issues](https://github.com/LucienWooo/ChroLens_Mimic/issues)
- 📖 **查看文檔**: [完整文檔](https://lucienwooo.github.io/ChroLens_Mimic/)
- 🌐 **ChroLens 專案**: [巴哈姆特介紹](https://home.gamer.com.tw/artwork.php?sn=6150515)

---

## 📜 授權條款

本專案採用 [MIT License](./LICENSE) 授權

---

## 🌏 多語言支援

<details>
<summary>🇯🇵 日本語の紹介</summary>

![ChroLens_Mimic](./pic/clm2.2jp.png)

**ChroLens_Mimic** は、Windows 上のマウス・キーボードの操作を滑らかかつシンプルに記録・再生できる **"マクロ録画＆再生ツール"** です。

**TinyTask** や **AutoHotkey（AHK）のレコーディング機能** に似た使いやすさを目指していて、プログラミング不要で、単純な繰り返し作業から軽度の自動化まで幅広く活用できます。

特にゲーマーの定番である TinyTask の直感的な操作性や、AHK のようにホットキーだけで起動・停止できる便利さが、ChroLens_Mimic の強みです。

使い方は録画開始（Record）→停止（Stop）→再生（Play）、繰り返し指定、ホットキー設定も可能。

</details>

<details>
<summary>🇺🇸 English Introduction</summary>

![ChroLens_Mimic](./pic/clm2.2en.png)

**ChroLens_Mimic** is a lightweight macro recorder for Windows that lets you record and replay mouse and keyboard actions—much like **TinyTask** or AutoHotkey's built-in macro recorder.

Aimed at users who want no‑code automation, ChroLens_Mimic combines TinyTask's simplicity (just record → stop → play) with AutoHotkey's hotkey‑based control.

You can loop playback, assign hotkeys, and save your macros for everyday automation tasks—whether for work or casual use.

If you're familiar with TinyTask's one‑click simplicity or AHK's scripting flexibility, you'll find ChroLens_Mimic a natural fit for reducing repetitive tasks.

</details>

---

<div align="center">

**⭐ 如果這個專案對你有幫助,請給個 Star! ⭐**

Made with ❤️ by [LucienWooo](https://github.com/LucienWooo)

</div>