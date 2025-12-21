# -*- coding: utf-8 -*-
"""
ChroLens 編輯器語法高亮模組
提供 VS Code Dark+ 風格的語法高亮功能

v2.7.3 - 從 text_script_editor.py 拆分
"""

import re
import tkinter as tk


class SyntaxMixin:
    """語法高亮 Mixin 類別
    
    為 TextCommandEditor 提供語法高亮功能。
    使用 VS Code Dark+ 配色方案。
    
    需要主類別提供:
    - self.text_editor: Text widget
    - self.after(): Tk after 方法
    - self.after_cancel(): Tk after_cancel 方法
    """
    
    def _configure_syntax_tags(self):
        """配置語法高亮標籤樣式 (VS Code Dark+ 配色)"""
        # 符號 (淡紫色/淡灰色)
        self.text_editor.tag_configure("syntax_symbol", foreground="#c586c0")
        
        # 時間參數 (粉紅色)
        self.text_editor.tag_configure("syntax_time", foreground="#ce9178")
        
        # 標籤 (青綠色)
        self.text_editor.tag_configure("syntax_label", foreground="#4ec9b0")
        
        # 可摺疊標籤 (青綠色 + 底線)
        self.text_editor.tag_configure("label_foldable", foreground="#4ec9b0", underline=True)
        
        # 標籤結束 (淡灰色)
        self.text_editor.tag_configure("label_end", foreground="#6e7681")
        
        # 鍵盤操作 (淺藍色)
        self.text_editor.tag_configure("syntax_keyboard", foreground="#9cdcfe")
        
        # 滑鼠操作 (藍色)
        self.text_editor.tag_configure("syntax_mouse", foreground="#569cd6")
        
        # 圖片辨識 (綠色)
        self.text_editor.tag_configure("syntax_image", foreground="#3fb950")
        
        # 圖片名稱 (黃色)
        self.text_editor.tag_configure("syntax_picname", foreground="#dcdcaa")
        
        # 條件判斷 (橘色)
        self.text_editor.tag_configure("syntax_condition", foreground="#ce9178")
        
        # OCR 文字辨識 (青色)
        self.text_editor.tag_configure("syntax_ocr", foreground="#4ec9b0")
        
        # 延遲控制 (橘色/黃橘)
        self.text_editor.tag_configure("syntax_delay", foreground="#dcdcaa")
        
        # 流程控制 (紫色)
        self.text_editor.tag_configure("syntax_flow", foreground="#c586c0")
        
        # 備註 (灰色)
        self.text_editor.tag_configure("syntax_comment", foreground="#6a9955")
        
        # 模組引用 (金色)
        self.text_editor.tag_configure("syntax_module_ref", foreground="#ffd700")
    
    def _on_text_modified(self, event=None):
        """文字內容修改時觸發語法高亮（優化版：防抖動處理）"""
        # 重置 modified 標誌
        self.text_editor.edit_modified(False)
        
        # 使用防抖動機制：取消之前的延遲任務
        if hasattr(self, '_highlight_after_id'):
            self.after_cancel(self._highlight_after_id)
        
        # 延遲執行語法高亮以提高效能（延長至150ms避免卡頓）
        self._highlight_after_id = self.after(150, self._apply_syntax_highlighting)
    
    def _apply_syntax_highlighting_to_widget(self, text_widget):
        """為指定的Text小工具套用語法高亮"""
        try:
            content = text_widget.get("1.0", "end-1c")
            
            # 定義需要高亮的模式 (VS Code Dark+ 配色方案)
            patterns = [
                (r'跳到#\S+', 'syntax_flow'),
                (r'停止', 'syntax_flow'),
                (r'if>', 'syntax_condition'),
                (r'如果存在>', 'syntax_condition'),
                (r'延遲\d+ms', 'syntax_delay'),
                (r'if文字>', 'syntax_ocr'),
                (r'等待文字>', 'syntax_ocr'),
                (r'點擊文字>', 'syntax_ocr'),
                (r'按下\w+', 'syntax_keyboard'),
                (r'放開\w+', 'syntax_keyboard'),
                (r'按(?![下放])\S+', 'syntax_keyboard'),
                (r'移動至\(', 'syntax_mouse'),
                (r'左鍵點擊\(', 'syntax_mouse'),
                (r'右鍵點擊\(', 'syntax_mouse'),
                (r'滾輪\(', 'syntax_mouse'),
                (r'辨識>', 'syntax_image'),
                (r'移動至>', 'syntax_image'),
                (r'左鍵點擊>', 'syntax_image'),
                (r'右鍵點擊>', 'syntax_image'),
                (r'pic\w+', 'syntax_picname'),
                (r'T=\d+[smh]\d*', 'syntax_time'),
                (r'^#\S+', 'syntax_label'),
                (r'>>#\S+', 'syntax_label'),
                (r'>>>#\S+', 'syntax_label'),
                (r'^# .*', 'syntax_comment'),
                (r'^>>>', 'syntax_symbol'),
                (r'^>>', 'syntax_symbol'),
                (r'^>', 'syntax_symbol'),
                (r',', 'syntax_symbol'),
            ]
            
            # 逐行處理
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern, tag in patterns:
                    for match in re.finditer(pattern, line):
                        start_idx = f"{line_num}.{match.start()}"
                        end_idx = f"{line_num}.{match.end()}"
                        text_widget.tag_add(tag, start_idx, end_idx)
        except:
            pass
    
    def _apply_syntax_highlighting(self):
        """套用語法高亮 (VS Code Dark+ 配色) - 優化版"""
        try:
            # 取得整份文件的總行數
            total_lines = int(self.text_editor.index("end-1c").split('.')[0])
            
            # 處理整份文件
            start_line = 1
            end_line = total_lines
            
            # 移除舊標籤（全域）
            for tag in ["syntax_symbol", "syntax_time", "syntax_label", "syntax_keyboard",
                       "syntax_mouse", "syntax_image", "syntax_condition", "syntax_ocr",
                       "syntax_delay", "syntax_flow", "syntax_picname", "syntax_comment",
                       "syntax_module_ref", "label_foldable", "label_end"]:
                self.text_editor.tag_remove(tag, "1.0", "end")
            
            # 獲取全部文字內容
            content = self.text_editor.get(f"{start_line}.0", f"{end_line}.end")
            
            # 定義需要高亮的模式 (按優先順序排列)
            
            # 觸發器系統 (紫色) - 優先順序最高
            patterns_trigger = [
                (r'>每隔>\d+(秒|分鐘|ms)', 'syntax_condition'),
                (r'>每隔結束', 'syntax_condition'),
                (r'>當偵測到>.+', 'syntax_condition'),
                (r'>當偵測結束', 'syntax_condition'),
                (r'>優先偵測>.+', 'syntax_flow'),
                (r'>優先偵測結束', 'syntax_flow'),
                # 並行區塊
                (r'>並行開始', 'syntax_flow'),
                (r'>線程>.+', 'syntax_flow'),
                (r'>線程結束', 'syntax_flow'),
                (r'>並行結束', 'syntax_flow'),
                # 狀態機
                (r'>狀態機>.+', 'syntax_flow'),
                (r'>狀態>.+', 'syntax_flow'),
                (r'>切換>.+', 'syntax_flow'),
                (r'>>切換>.+', 'syntax_flow'),
                (r'>>>切換>.+', 'syntax_flow'),
                (r'>狀態機結束', 'syntax_flow'),
            ]
            
            # 流程控制 (紅色)
            patterns_flow = [
                (r'跳到#\S+', 'syntax_flow'),
                (r'停止', 'syntax_flow'),
            ]
            
            # 條件判斷 (橘色)
            patterns_condition = [
                (r'if>', 'syntax_condition'),
                (r'如果存在>', 'syntax_condition'),
            ]
            
            # 延遲控制 (橘色)
            patterns_delay = [
                (r'延遲\d+ms', 'syntax_delay'),
                (r'延遲時間', 'syntax_delay'),
            ]
            
            # OCR 文字辨識 (青色)
            patterns_ocr = [
                (r'if文字>', 'syntax_ocr'),
                (r'等待文字>', 'syntax_ocr'),
                (r'點擊文字>', 'syntax_ocr'),
            ]
            
            # 鍵盤操作 (淡紫色)
            patterns_keyboard = [
                (r'按下\w+', 'syntax_keyboard'),
                (r'放開\w+', 'syntax_keyboard'),
                (r'按(?![下放])\S+', 'syntax_keyboard'),
            ]
            
            # 滑鼠座標操作 (藍色)
            patterns_mouse = [
                (r'移動至\(', 'syntax_mouse'),
                (r'左鍵點擊\(', 'syntax_mouse'),
                (r'右鍵點擊\(', 'syntax_mouse'),
                (r'中鍵點擊\(', 'syntax_mouse'),
                (r'雙擊\(', 'syntax_mouse'),
                (r'按下left鍵\(', 'syntax_mouse'),
                (r'放開left鍵\(', 'syntax_mouse'),
                (r'滾輪\(', 'syntax_mouse'),
            ]
            
            # 圖片辨識 (綠色)
            patterns_image = [
                (r'辨識>', 'syntax_image'),
                (r'移動至>', 'syntax_image'),
                (r'左鍵點擊>', 'syntax_image'),
                (r'右鍵點擊>', 'syntax_image'),
                (r'辨識任一>', 'syntax_image'),
            ]
            
            # 圖片名稱 (黃色)
            patterns_picname = [
                (r'pic\d+', 'syntax_picname'),
            ]
            
            # 時間參數 (粉紅色)
            patterns_time = [
                (r'T=\d+[smh]\d*', 'syntax_time'),
            ]
            
            # 備註 (灰色)
            patterns_comment = [
                (r'^# .+', 'syntax_comment'),
            ]
            
            # 標籤 (青色)
            patterns_label = [
                (r'^#b\S+', 'label_foldable'),
                (r'^#/\S+', 'label_end'),
                (r'^#\S+', 'syntax_label'),
            ]
            
            # 模組引用 (金色)
            patterns_module_ref = [
                (r'>#mod_[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),
                (r'>>#[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),
                (r'>>>#[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),
            ]
            
            # 符號 (淡紫色)
            patterns_symbol = [
                (r'^>>>', 'syntax_symbol'),
                (r'^>>', 'syntax_symbol'),
                (r'^>', 'syntax_symbol'),
                (r',', 'syntax_symbol'),
            ]
            
            # 按順序合併所有模式
            all_patterns = (
                patterns_trigger + patterns_comment + patterns_flow + 
                patterns_condition + patterns_delay + patterns_ocr + 
                patterns_keyboard + patterns_mouse + patterns_image + 
                patterns_picname + patterns_time + patterns_module_ref + 
                patterns_label + patterns_symbol
            )
            
            # 逐行處理
            lines = content.split('\n')
            for offset, line in enumerate(lines):
                line_num = start_line + offset
                for pattern, tag in all_patterns:
                    for match in re.finditer(pattern, line):
                        start_idx = f"{line_num}.{match.start()}"
                        end_idx = f"{line_num}.{match.end()}"
                        self.text_editor.tag_add(tag, start_idx, end_idx)
        
        except Exception as e:
            # 靜默處理錯誤，避免影響編輯器使用
            pass
    
    def _get_command_color(self, command):
        """根據指令類型返回對應的顏色（與VS Code語法高亮一致）"""
        # 註解
        if command.startswith('#'):
            return "#6a9955"
        
        # 滑鼠操作（藍色系）
        if command.startswith('>'):
            if '移動至' in command:
                return "#569cd6"
            elif '點擊' in command:
                return "#569cd6"
            elif '拖曳' in command:
                return "#569cd6"
            elif '滾輪' in command:
                return "#569cd6"
            return "#569cd6"
        
        # 鍵盤操作（淺藍色）
        if command.startswith('@'):
            return "#9cdcfe"
        
        # 等待延遲（淺黃色）
        if command.startswith('等待'):
            return "#dcdcaa"
        
        # 標籤（青綠色）
        if command.startswith('標籤:'):
            return "#4ec9b0"
        
        # 圖片辨識（青綠色）
        if command.startswith('找圖'):
            return "#4ec9b0"
        
        # OCR文字（青綠色）
        if command.startswith('找字'):
            return "#4ec9b0"
        
        # 流程控制（紫色）
        if '條件判斷' in command or '迴圈' in command or '如果' in command or '否則' in command:
            return "#c586c0"
        
        # 時間格式（橘色）
        if 'T=' in command:
            return "#ce9178"
        
        return "#d4d4d4"  # 預設 - 淺灰色
