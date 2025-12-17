# ChroLens Mimic Japanese Language Pack

## 概要 / Overview

このパッケージは ChroLens Mimic に日本語フォントサポートを追加します。

This package adds Japanese font support to ChroLens Mimic.

## 內容 / Contents

```
japanese_pack/
├── install_japanese.bat    # インストーラー / Installer
├── fonts/
│   └── NotoSansJP-Regular.ttf  # 日本語フォント（手動ダウンロード必要）
├── lang_ja_extended.json   # 拡張日本語翻訳
└── README.md              # このファイル
```

## 安裝步驟 / Installation

### 1. フォントのダウンロード / Download Font

**Noto Sans JP** をダウンロード：
Download **Noto Sans JP**:

https://fonts.google.com/noto/specimen/Noto+Sans+JP

ダウンロードした **NotoSansJP-Regular.ttf** を `fonts/` フォルダに配置
Place the downloaded **NotoSansJP-Regular.ttf** in the `fonts/` folder

### 2. インストーラー実行 / Run Installer

`install_japanese.bat` をダブルクリック
Double-click `install_japanese.bat`

インストーラーは以下を自動的に行います：
The installer will automatically:

- フォントを ChroLens Mimic に登録 / Register font to ChroLens Mimic
- 拡張言語設定をコピー / Copy extended language settings
- 必要なディレクトリを作成 / Create necessary directories

### 3. 言語選択 / Select Language

1. ChroLens_Mimic.exe を起動 / Launch ChroLens_Mimic.exe
2. **Language** ドロップダウンから「**日本語**」を選択 / Select "**日本語**" from **Language** dropdown
3. プログラムを再起動 / Restart the program

## 注意事項 / Notes

- **パッケージサイズ**: 約 15-20MB / Approx. 15-20MB
- **対象バージョン**: ChroLens Mimic v2.7.3+
- **フォントライセンス**: SIL Open Font License 1.1
  - 商用利用可能 / Commercial use allowed
  - 改変・再配布可能 / Modification and redistribution allowed

## アンインストール / Uninstallation

以下のファイルを削除：
Delete the following files:

```
ChroLens_Mimic/
├── TTF/NotoSansJP-Regular.ttf
└── languages/lang_ja_extended.json
```

## トラブルシューティング / Troubleshooting

### Q: フォントが表示されない

**A**:

1. TTF フォルダに NotoSansJP-Regular.ttf があるか確認
2. プログラムを完全に再起動

### Q: インストーラーがエラーを表示

**A**:

1. `language_packs\japanese_pack\` 内で実行しているか確認
2. ChroLens_Mimic.exe が存在するか確認

### Q: Font not displaying

**A**:

1. Check if NotoSansJP-Regular.ttf exists in TTF folder
2. Fully restart the program

### Q: Installer shows error

**A**:

1. Verify running from `language_packs\japanese_pack\`
2. Confirm ChroLens_Mimic.exe exists

## サポート / Support

問題が発生した場合：
If you encounter issues:

- Discord: https://discord.gg/72Kbs4WPPn
- GitHub Issues: https://github.com/Lucienwooo/ChroLens-Mimic/issues

## ライセンス / License

- **Noto Sans JP**: SIL Open Font License 1.1
- **ChroLens Mimic**: MIT License (本体に準拠 / Follows main program)

---

**作者** / **Creator**: Lucien  
**バージョン** / **Version**: 1.0  
**更新日** / **Updated**: 2025-12-17
