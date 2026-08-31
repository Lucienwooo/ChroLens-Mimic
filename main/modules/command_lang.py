# command_lang.py
# 腳本指令的本地化對照表與轉換函式

COMMAND_MAP_EN = {
    "左鍵點擊": "LeftClick",
    "右鍵點擊": "RightClick",
    "中鍵點擊": "MiddleClick",
    "左鍵雙擊": "LeftDoubleClick",
    "移動至": "MoveTo",
    "相對移動": "MoveRelative",
    "滾輪": "Scroll",
    "延遲": "Delay",
    "隨機延遲": "RandomDelay",
    "按下": "KeyDown",
    "放開": "KeyUp",
    "按": "Press",
    "辨識": "Recognize",
    "辨識任一": "RecognizeAny",
    "點擊圖片": "ClickImage",
    "等待文字": "WaitText",
    "點擊文字": "ClickText",
    "設定變數": "SetVar",
    "變數加1": "IncVar",
    "變數減1": "DecVar",
    "重複": "Repeat",
    "執行腳本": "RunScript",
    "重複結束": "EndRepeat",
    "定時觸發": "TimerTrigger",
    "定時結束": "EndTimer",
    "條件觸發": "ConditionTrigger",
    "條件結束": "EndCondition",
    "優先偵測": "PriorityDetect",
    "優先偵測結束": "EndPriorityDetect",
    "狀態機": "StateMachine",
    "狀態機結束": "EndStateMachine",
    "狀態": "State",
    "切換": "Transition",
    "當偵測到": "WhenDetected",
    "當偵測結束": "EndDetect",
    "執行緒": "Thread",
    "執行緒結束": "EndThread",
    "計數器": "Counter",
    "計時器": "Timer",
    "重置計數器": "ResetCounter",
    "重置計時器": "ResetTimer",
    "開始": "Start",
    "結束": "End",
    "每隔": "Interval",
    "每隔結束": "EndInterval",
    "隨機執行": "RandomExec",
    "if變數": "ifVar",
    "if文字": "ifText",
    "if任一存在": "ifAnyExist",
    "if全部存在": "ifAllExist",
    "YOLO偵測": "YOLODetect",
    "自動辨識輸入驗證碼": "AutoCaptcha",
    "等待圖像": "WaitImage",
    "尋找圖像": "FindImage",
    "辨識(beta)": "RecognizeBeta",
    "座標左點擊": "CoordLeftClick",
    "座標右點擊": "CoordRightClick",
    "輸入字": "InputText",
    "拖曳": "Drag",
    "滾動": "Scroll",
    "等待": "Wait",
    "尋找": "Find",
    "模組內容": "ModuleContent",
    "儲存修改": "SaveChanges",
    "更新網格": "UpdateGrid",
}

# 建立反向對照表

COMMAND_MAP_JP = {
    "左鍵點擊": "左クリック",
    "右鍵點擊": "右クリック",
    "中鍵點擊": "中クリック",
    "左鍵雙擊": "左ダブルクリック",
    "移動至": "移動",
    "相對移動": "相対移動",
    "滾輪": "スクロール",
    "延遲": "待機",
    "隨機延遲": "ランダム待機",
    "按下": "押す",
    "放開": "離す",
    "按": "タップ",
    "辨識": "認識",
    "辨識任一": "任意認識",
    "點擊圖片": "画像クリック",
    "等待文字": "文字待機",
    "點擊文字": "文字クリック",
    "設定變數": "変数設定",
    "變數加1": "変数加算",
    "變數減1": "変数減算",
    "重複": "反復",
    "執行腳本": "スクリプト実行",
    "重複結束": "反復終了",
    "定時觸發": "タイマー開始",
    "定時結束": "タイマー終了",
    "條件觸發": "条件開始",
    "條件結束": "条件終了",
    "優先偵測": "優先検出",
    "優先偵測結束": "優先検出終了",
    "狀態機": "ステートマシン",
    "狀態機結束": "ステートマシン終了",
    "狀態": "ステート",
    "切換": "遷移",
    "當偵測到": "検出時",
    "當偵測結束": "検出終了",
    "執行緒": "スレッド",
    "執行緒結束": "スレッド終了",
    "計數器": "カウンター",
    "計時器": "タイマー",
    "重置計數器": "カウンターリセット",
    "重置計時器": "タイマーリセット",
    "開始": "開始",
    "結束": "終了",
    "每隔": "間隔",
    "每隔結束": "間隔終了",
    "隨機執行": "ランダム実行",
    "if變數": "if変数",
    "if文字": "if文字",
    "if任一存在": "if任意存在",
    "if全部存在": "if全て存在",
    "YOLO偵測": "YOLO検出",
    "自動辨識輸入驗證碼": "自動キャプチャ",
    "等待圖像": "画像待機",
    "尋找圖像": "画像検索",
    "辨識(beta)": "認識(beta)",
    "座標左點擊": "座標左クリック",
    "座標右點擊": "座標右クリック",
    "輸入字": "文字入力",
    "拖曳": "ドラッグ",
    "滾動": "スクロール",
    "等待": "待機",
    "尋找": "検索",
    "模組內容": "モジュール内容",
    "儲存修改": "変更保存",
    "更新網格": "グリッド更新",
    "範圍": "範囲",
    "等待圖片": "画像待機",
    "OCR點擊": "OCRクリック",
    "輸入文字": "文字入力"
}

UI_TRANSLATIONS = {
    # Categories
    "圖片辨識": {"English": "Image Recognition", "日本語": "画像認識"},
    "滑鼠鍵盤": {"English": "Mouse & Keyboard", "日本語": "マウス・キーボード"},
    "流程控制": {"English": "Flow Control", "日本語": "フロー制御"},
    "迴圈控制": {"English": "Loop Control", "日本語": "ループ制御"},
    "多條件與隨機": {"English": "Conditions & Random", "日本語": "条件・ランダム"},
    "計時系統": {"English": "Timing System", "日本語": "タイマーシステム"},
    
    # Button Names
    "範圍辨識": {"English": "Region Recog", "日本語": "範囲認識"},
    "移動至圖片": {"English": "Move to Image", "日本語": "画像へ移動"},
    "點擊圖片": {"English": "Click Image", "日本語": "画像クリック"},
    "條件判斷": {"English": "Condition IF", "日本語": "条件分岐"},
    "等待圖片": {"English": "Wait Image", "日本語": "画像待機"},
    "驗證碼辨識beta": {"English": "Captcha OCR", "日本語": "CAPTCHA認識"},
    "座標左鍵點擊": {"English": "Coord L-Click", "日本語": "座標左クリック"},
    "座標右鍵點擊": {"English": "Coord R-Click", "日本語": "座標右クリック"},
    "滑鼠移動": {"English": "Mouse Move", "日本語": "マウス移動"},
    "相對移動": {"English": "Move Relative", "日本語": "相対移動"},
    "滑鼠滾輪": {"English": "Mouse Scroll", "日本語": "スクロール"},
    "按下按鍵": {"English": "Key Down", "日本語": "キー押下"},
    "放開按鍵": {"English": "Key Up", "日本語": "キー離す"},
    "輸入文字": {"English": "Input Text", "日本語": "文字入力"},
    "拖曳 (捕捉起點與終點)": {"English": "Drag (Start->End)", "日本語": "ドラッグ"},
    "新增標籤": {"English": "Add Label", "日本語": "ラベル追加"},
    "跳轉標籤": {"English": "Jump to Label", "日本語": "ラベルへジャンプ"},
    "條件失敗跳轉": {"English": "Jump on Fail", "日本語": "失敗時ジャンプ"},
    "延遲等待": {"English": "Delay Wait", "日本語": "待機"},
    "重複N次": {"English": "Repeat N times", "日本語": "N回反復"},
    "條件迴圈": {"English": "Condition Loop", "日本語": "条件ループ"},
    "全部圖片存在": {"English": "If All Exist", "日本語": "全て存在する場合"},
    "任一圖片存在": {"English": "If Any Exists", "日本語": "いずれか存在する場合"},
    "隨機延遲": {"English": "Random Delay", "日本語": "ランダム待機"},
    "隨機分支": {"English": "Random Branch", "日本語": "ランダム分岐"},
    "計數器觸發": {"English": "Counter Trigger", "日本語": "カウンタートリガー"},
    "計時器觸發": {"English": "Timer Trigger", "日本語": "タイマートリガー"},
    "重置計數器": {"English": "Reset Counter", "日本語": "カウンターリセット"},
    "重置計時器": {"English": "Reset Timer", "日本語": "タイマーリセット"},
    "開始": {"English": "Start", "日本語": "開始"},
    "結束": {"English": "End", "日本語": "終了"},

    # Grid Mode Labels
    "延遲等待": {"English": "Delay", "日本語": "待機"},
    "備註": {"English": "Note", "日本語": "備考"},
    "( 空白行 )": {"English": "( Blank )", "日本語": "( 空白行 )"},
    "圖片名稱": {"English": "Image Name", "日本語": "画像名"},
    "圖片名稱 (用 | 分隔)": {"English": "Images (split by |)", "日本語": "画像名 (|で区切る)"},
    "範圍 (x,y,w,h)": {"English": "Region (x,y,w,h)", "日本語": "範囲 (x,y,w,h)"},
    "目標文字與偏移": {"English": "Target Text & Offset", "日本語": "目標文字とオフセット"},
    "( 無參數 )": {"English": "( No Params )", "日本語": "( パラメータなし )"},
    "座標(X,Y) 或 圖片名": {"English": "Coord(X,Y) or Image", "日本語": "座標(X,Y) または 画像名"},
    "按鍵名稱 / 內容": {"English": "Key Name / Content", "日本語": "キー名 / 内容"},
    "時間 (ms)": {"English": "Time (ms)", "日本語": "時間 (ms)"},
    "次數": {"English": "Times", "日本語": "回数"},
    "標籤名稱": {"English": "Label Name", "日本語": "ラベル名"},
    "運算式 / 條件": {"English": "Expression / Cond", "日本語": "式 / 条件"},
}

def get_ui_text(zh_text, lang_code):
    if lang_code == "繁體中文" or zh_text not in UI_TRANSLATIONS:
        return zh_text
    return UI_TRANSLATIONS[zh_text].get(lang_code, zh_text)

REVERSE_MAP = {v: k for k, v in COMMAND_MAP_EN.items()}
for k, v in COMMAND_MAP_JP.items():
    REVERSE_MAP[v] = k
# command_lang.py
# 腳本指令的本地化對照表與轉換函式

COMMAND_MAP_EN = {
    "左鍵點擊": "LeftClick",
    "右鍵點擊": "RightClick",
    "中鍵點擊": "MiddleClick",
    "左鍵雙擊": "LeftDoubleClick",
    "移動至": "MoveTo",
    "相對移動": "MoveRelative",
    "滾輪": "Scroll",
    "延遲": "Delay",
    "隨機延遲": "RandomDelay",
    "按下": "KeyDown",
    "放開": "KeyUp",
    "按": "Press",
    "辨識": "Recognize",
    "辨識任一": "RecognizeAny",
    "點擊圖片": "ClickImage",
    "等待文字": "WaitText",
    "點擊文字": "ClickText",
    "設定變數": "SetVar",
    "變數加1": "IncVar",
    "變數減1": "DecVar",
    "重複": "Repeat",
    "執行腳本": "RunScript",
    "重複結束": "EndRepeat",
    "定時觸發": "TimerTrigger",
    "定時結束": "EndTimer",
    "條件觸發": "ConditionTrigger",
    "條件結束": "EndCondition",
    "優先偵測": "PriorityDetect",
    "優先偵測結束": "EndPriorityDetect",
    "狀態機": "StateMachine",
    "狀態機結束": "EndStateMachine",
    "狀態": "State",
    "切換": "Transition",
    "當偵測到": "WhenDetected",
    "當偵測結束": "EndDetect",
    "執行緒": "Thread",
    "執行緒結束": "EndThread",
    "計數器": "Counter",
    "計時器": "Timer",
    "重置計數器": "ResetCounter",
    "重置計時器": "ResetTimer",
    "開始": "Start",
    "結束": "End",
    "每隔": "Interval",
    "每隔結束": "EndInterval",
    "隨機執行": "RandomExec",
    "if變數": "ifVar",
    "if文字": "ifText",
    "if任一存在": "ifAnyExist",
    "if全部存在": "ifAllExist",
    "YOLO偵測": "YOLODetect",
    "自動辨識輸入驗證碼": "AutoCaptcha",
    "等待圖像": "WaitImage",
    "尋找圖像": "FindImage",
    "辨識(beta)": "RecognizeBeta",
    "座標左點擊": "CoordLeftClick",
    "座標右點擊": "CoordRightClick",
    "輸入字": "InputText",
    "拖曳": "Drag",
    "滾動": "Scroll",
    "等待": "Wait",
    "尋找": "Find",
    "模組內容": "ModuleContent",
    "儲存修改": "SaveChanges",
    "更新網格": "UpdateGrid",
}

# 建立反向對照表

COMMAND_MAP_JP = {
    "左鍵點擊": "左クリック",
    "右鍵點擊": "右クリック",
    "中鍵點擊": "中クリック",
    "左鍵雙擊": "左ダブルクリック",
    "移動至": "移動",
    "相對移動": "相対移動",
    "滾輪": "スクロール",
    "延遲": "待機",
    "隨機延遲": "ランダム待機",
    "按下": "押す",
    "放開": "離す",
    "按": "タップ",
    "辨識": "認識",
    "辨識任一": "任意認識",
    "點擊圖片": "画像クリック",
    "等待文字": "文字待機",
    "點擊文字": "文字クリック",
    "設定變數": "変数設定",
    "變數加1": "変数加算",
    "變數減1": "変数減算",
    "重複": "反復",
    "執行腳本": "スクリプト実行",
    "重複結束": "反復終了",
    "定時觸發": "タイマー開始",
    "定時結束": "タイマー終了",
    "條件觸發": "条件開始",
    "條件結束": "条件終了",
    "優先偵測": "優先検出",
    "優先偵測結束": "優先検出終了",
    "狀態機": "ステートマシン",
    "狀態機結束": "ステートマシン終了",
    "狀態": "ステート",
    "切換": "遷移",
    "當偵測到": "検出時",
    "當偵測結束": "検出終了",
    "執行緒": "スレッド",
    "執行緒結束": "スレッド終了",
    "計數器": "カウンター",
    "計時器": "タイマー",
    "重置計數器": "カウンターリセット",
    "重置計時器": "タイマーリセット",
    "開始": "開始",
    "結束": "終了",
    "每隔": "間隔",
    "每隔結束": "間隔終了",
    "隨機執行": "ランダム実行",
    "if變數": "if変数",
    "if文字": "if文字",
    "if任一存在": "if任意存在",
    "if全部存在": "if全て存在",
    "YOLO偵測": "YOLO検出",
    "自動辨識輸入驗證碼": "自動キャプチャ",
    "等待圖像": "画像待機",
    "尋找圖像": "画像検索",
    "辨識(beta)": "認識(beta)",
    "座標左點擊": "座標左クリック",
    "座標右點擊": "座標右クリック",
    "輸入字": "文字入力",
    "拖曳": "ドラッグ",
    "滾動": "スクロール",
    "等待": "待機",
    "尋找": "検索",
    "模組內容": "モジュール内容",
    "儲存修改": "変更保存",
    "更新網格": "グリッド更新",
    "範圍": "範囲",
    "等待圖片": "画像待機",
    "OCR點擊": "OCRクリック",
    "輸入文字": "文字入力"
}

UI_TRANSLATIONS = {
    # Categories
    "圖片辨識": {"English": "Image Recognition", "日本語": "画像認識"},
    "滑鼠鍵盤": {"English": "Mouse & Keyboard", "日本語": "マウス・キーボード"},
    "流程控制": {"English": "Flow Control", "日本語": "フロー制御"},
    "迴圈控制": {"English": "Loop Control", "日本語": "ループ制御"},
    "多條件與隨機": {"English": "Conditions & Random", "日本語": "条件・ランダム"},
    "計時系統": {"English": "Timing System", "日本語": "タイマーシステム"},
    
    # Button Names
    "範圍辨識": {"English": "Region Recog", "日本語": "範囲認識"},
    "移動至圖片": {"English": "Move to Image", "日本語": "画像へ移動"},
    "點擊圖片": {"English": "Click Image", "日本語": "画像クリック"},
    "條件判斷": {"English": "Condition IF", "日本語": "条件分岐"},
    "等待圖片": {"English": "Wait Image", "日本語": "画像待機"},
    "驗證碼辨識beta": {"English": "Captcha OCR", "日本語": "CAPTCHA認識"},
    "座標左鍵點擊": {"English": "Coord L-Click", "日本語": "座標左クリック"},
    "座標右鍵點擊": {"English": "Coord R-Click", "日本語": "座標右クリック"},
    "滑鼠移動": {"English": "Mouse Move", "日本語": "マウス移動"},
    "相對移動": {"English": "Move Relative", "日本語": "相対移動"},
    "滑鼠滾輪": {"English": "Mouse Scroll", "日本語": "スクロール"},
    "按下按鍵": {"English": "Key Down", "日本語": "キー押下"},
    "放開按鍵": {"English": "Key Up", "日本語": "キー離す"},
    "輸入文字": {"English": "Input Text", "日本語": "文字入力"},
    "拖曳 (捕捉起點與終點)": {"English": "Drag (Start->End)", "日本語": "ドラッグ"},
    "新增標籤": {"English": "Add Label", "日本語": "ラベル追加"},
    "跳轉標籤": {"English": "Jump to Label", "日本語": "ラベルへジャンプ"},
    "條件失敗跳轉": {"English": "Jump on Fail", "日本語": "失敗時ジャンプ"},
    "延遲等待": {"English": "Delay Wait", "日本語": "待機"},
    "重複N次": {"English": "Repeat N times", "日本語": "N回反復"},
    "條件迴圈": {"English": "Condition Loop", "日本語": "条件ループ"},
    "全部圖片存在": {"English": "If All Exist", "日本語": "全て存在する場合"},
    "任一圖片存在": {"English": "If Any Exists", "日本語": "いずれか存在する場合"},
    "隨機延遲": {"English": "Random Delay", "日本語": "ランダム待機"},
    "隨機分支": {"English": "Random Branch", "日本語": "ランダム分岐"},
    "計數器觸發": {"English": "Counter Trigger", "日本語": "カウンタートリガー"},
    "計時器觸發": {"English": "Timer Trigger", "日本語": "タイマートリガー"},
    "重置計數器": {"English": "Reset Counter", "日本語": "カウンターリセット"},
    "重置計時器": {"English": "Reset Timer", "日本語": "タイマーリセット"},
    "開始": {"English": "Start", "日本語": "開始"},
    "結束": {"English": "End", "日本語": "終了"},
}

def get_ui_text(zh_text, lang_code):
    if lang_code == "繁體中文" or zh_text not in UI_TRANSLATIONS:
        return zh_text
    return UI_TRANSLATIONS[zh_text].get(lang_code, zh_text)

REVERSE_MAP = {v: k for k, v in COMMAND_MAP_EN.items()}

def get_localized_cmd(cmd_str: str, lang_code: str = "繁體中文") -> str:
    """將標準中文指令轉換為目標語言的指令"""
    if lang_code == "繁體中文":
        return cmd_str
    elif lang_code == "日本語":
        return COMMAND_MAP_JP.get(cmd_str, cmd_str)
    return COMMAND_MAP_EN.get(cmd_str, cmd_str)

def get_canonical_cmd(cmd_str: str) -> str:
    """將任何語言的指令轉換回標準中文指令，供內部引擎處理"""
    return REVERSE_MAP.get(cmd_str, cmd_str)

def translate_script_line_to_canonical(line: str) -> str:
    """將單行腳本中的英文指令轉回中文，避免破壞正規表達式解析"""
    if not line or not line.startswith('>'):
        return line
        
    res = line
    for en_cmd, zh_cmd in REVERSE_MAP.items():
        if en_cmd in res:
            res = res.replace(">" + en_cmd, ">" + zh_cmd)
            res = res.replace(en_cmd + ">", zh_cmd + ">")
            res = res.replace(en_cmd + "(", zh_cmd + "(")
            res = res.replace(en_cmd + ",", zh_cmd + ",")
    return res

def translate_ui_string(ui_string: str, lang_code: str) -> str:
    """給文字編輯器按鈕產生的字串使用，把字串內的中文指令取代成目標語言"""
    if lang_code == "繁體中文":
        return ui_string
        
    res = ui_string
    target_map = COMMAND_MAP_JP if lang_code == "日本語" else COMMAND_MAP_EN
    
    for zh_cmd, target_cmd in target_map.items():
        if zh_cmd in res:
            res = res.replace(">" + zh_cmd, ">" + target_cmd)
            res = res.replace(zh_cmd + ">", target_cmd + ">")
            res = res.replace(zh_cmd + "(", target_cmd + "(")
            res = res.replace(zh_cmd + ",", target_cmd + ",")
            if res.endswith(zh_cmd):
                res = res[:-len(zh_cmd)] + target_cmd
    return res
    
    