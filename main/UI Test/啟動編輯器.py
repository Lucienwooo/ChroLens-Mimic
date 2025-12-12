# -*- coding: utf-8 -*-
"""
Blockly Script Editor 啟動器
快速啟動 Blockly 風格的 ChroLens 指令編輯器
"""

import sys
import os

# 確保可以導入相關模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockly_script_editor import BlocklyScriptEditor

if __name__ == "__main__":
    editor = BlocklyScriptEditor()
    editor.run()
