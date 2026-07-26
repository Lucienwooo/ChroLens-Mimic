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
}

# 建立反向對照表
REVERSE_MAP = {v: k for k, v in COMMAND_MAP_EN.items()}

def get_localized_cmd(cmd_str: str, lang_code: str = "繁體中文") -> str:
    """將標準中文指令轉換為目標語言的指令"""
    if lang_code == "繁體中文":
        return cmd_str
        
    # 如果是其他語言 (English, 日本語) 統一使用英文版指令
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
    """給文字編輯器按鈕產生的字串使用，把字串內的中文指令取代成英文"""
    if lang_code == "繁體中文":
        return ui_string
        
    res = ui_string
    for zh_cmd, en_cmd in COMMAND_MAP_EN.items():
        if zh_cmd in res:
            # 為了避免誤判，只取代有特定分隔符號相鄰的字串
            # 對於按鈕生成的字串，通常會像 ">左鍵點擊(100,200)"
            res = res.replace(">" + zh_cmd, ">" + en_cmd)
            res = res.replace(zh_cmd + ">", en_cmd + ">")
            res = res.replace(zh_cmd + "(", en_cmd + "(")
            res = res.replace(zh_cmd + ",", en_cmd + ",")
            # 處理某些單獨只有指令的狀況
            if res.endswith(zh_cmd):
                res = res[:-len(zh_cmd)] + en_cmd
    return res
