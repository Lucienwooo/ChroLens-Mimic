# -*- coding: utf-8 -*-
"""
ChroLens 編輯器模組管理
提供自訂模組的儲存、載入和展開功能

v2.7.3 - 從 text_script_editor.py 拆分
"""

import os
import re
import tkinter as tk
from tkinter import messagebox, simpledialog


class ModulesMixin:
    """自訂模組管理 Mixin 類別
    
    為 TextCommandEditor 提供自訂模組功能。
    
    需要主類別提供:
    - self.text_editor: Text widget
    - self.modules_dir: 模組儲存目錄
    - self.script_dir: 腳本儲存目錄
    """
    
    def _init_modules_dir(self):
        """初始化模組目錄"""
        if not hasattr(self, 'modules_dir'):
            self.modules_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "scripts", "modules"
            )
        
        if not os.path.exists(self.modules_dir):
            os.makedirs(self.modules_dir)
    
    def _get_module_list(self):
        """取得所有已儲存的模組列表"""
        self._init_modules_dir()
        
        modules = []
        if os.path.exists(self.modules_dir):
            for f in os.listdir(self.modules_dir):
                if f.startswith("mod_") and f.endswith(".txt"):
                    name = f[4:-4]  # 移除 "mod_" 前綴和 ".txt" 後綴
                    modules.append(name)
        return sorted(modules)
    
    def _save_selection_as_module(self):
        """將選取的文字儲存為自訂模組"""
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            if not selected_text.strip():
                messagebox.showwarning("警告", "請先選取要儲存的指令")
                return
        except tk.TclError:
            messagebox.showwarning("警告", "請先選取要儲存的指令")
            return
        
        # 詢問模組名稱
        name = simpledialog.askstring(
            "儲存為模組",
            "請輸入模組名稱：\n（不需要加 mod_ 前綴）",
            parent=self
        )
        
        if not name:
            return
        
        # 清理名稱
        name = name.strip()
        if name.startswith("mod_"):
            name = name[4:]
        
        self._init_modules_dir()
        
        # 儲存模組
        module_path = os.path.join(self.modules_dir, f"mod_{name}.txt")
        try:
            with open(module_path, "w", encoding="utf-8") as f:
                f.write(selected_text)
            messagebox.showinfo("成功", f"模組 '{name}' 已儲存")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗: {e}")
    
    def _save_new_module_inline(self):
        """儲存新模組（內嵌版）"""
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected_text = ""
        
        if not selected_text.strip():
            content = self.text_editor.get("1.0", tk.END).strip()
        else:
            content = selected_text
        
        if not content:
            messagebox.showwarning("警告", "沒有可儲存的內容")
            return
        
        name = simpledialog.askstring(
            "儲存模組",
            "請輸入模組名稱：",
            parent=self
        )
        
        if not name:
            return
        
        name = name.strip()
        if name.startswith("mod_"):
            name = name[4:]
        
        self._init_modules_dir()
        module_path = os.path.join(self.modules_dir, f"mod_{name}.txt")
        
        try:
            with open(module_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", f"模組 '{name}' 已儲存")
            
            # 刷新模組列表顯示
            if hasattr(self, '_refresh_module_list'):
                self._refresh_module_list()
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗: {e}")
    
    def _insert_module_inline(self):
        """插入選取的模組（內嵌版）"""
        if not hasattr(self, 'module_listbox'):
            return
        
        selection = self.module_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請先選擇要插入的模組")
            return
        
        module_name = self.module_listbox.get(selection[0])
        self._insert_module_reference(module_name)
    
    def _insert_module_reference(self, module_name):
        """插入模組引用到編輯器"""
        # 插入模組引用語法
        reference = f">#mod_{module_name}"
        self.text_editor.insert(tk.INSERT, reference + "\n")
    
    def _insert_module_from_menu(self, module_name):
        """從右鍵選單插入模組"""
        self._insert_module_reference(module_name)
    
    def _delete_module_inline(self):
        """刪除選取的模組（內嵌版）"""
        if not hasattr(self, 'module_listbox'):
            return
        
        selection = self.module_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請先選擇要刪除的模組")
            return
        
        module_name = self.module_listbox.get(selection[0])
        
        if not messagebox.askyesno("確認刪除", f"確定要刪除模組 '{module_name}' 嗎？"):
            return
        
        self._init_modules_dir()
        module_path = os.path.join(self.modules_dir, f"mod_{module_name}.txt")
        
        try:
            if os.path.exists(module_path):
                os.remove(module_path)
                messagebox.showinfo("成功", f"模組 '{module_name}' 已刪除")
                
                if hasattr(self, '_refresh_module_list'):
                    self._refresh_module_list()
        except Exception as e:
            messagebox.showerror("錯誤", f"刪除失敗: {e}")
    
    def _get_module_content(self, module_name):
        """獲取模組內容（用於預覽和引用）"""
        self._init_modules_dir()
        module_path = os.path.join(self.modules_dir, f"mod_{module_name}.txt")
        
        if os.path.exists(module_path):
            try:
                with open(module_path, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                pass
        return None
    
    def _expand_module_references(self, text_content):
        """展開模組引用：將 >#mod_a 替換為模組內容
        
        用於在保存或執行時，將標記引用替換為實際的模組內容
        
        規則：
        1. >#mod_xxx 會被展開為模組內容
        2. >>#label 和 >>>#label 是分支跳轉，不會被展開
        3. 模組檔案儲存為 mod_模組名.txt
        
        Args:
            text_content: 原始文字內容
            
        Returns:
            展開後的文字內容
        """
        self._init_modules_dir()
        
        result_lines = []
        lines = text_content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            # 檢查是否是模組引用 (>#mod_xxx)
            if stripped.startswith('>#mod_'):
                # 提取模組名稱
                module_name = stripped[6:]  # 移除 >#mod_ 前綴
                
                # 載入模組內容
                module_content = self._get_module_content(module_name)
                
                if module_content:
                    # 展開模組內容
                    result_lines.append(f"# [模組開始: {module_name}]")
                    result_lines.extend(module_content.split('\n'))
                    result_lines.append(f"# [模組結束: {module_name}]")
                else:
                    # 模組不存在，保留原始引用
                    result_lines.append(line)
                    result_lines.append(f"# 警告：找不到模組 {module_name}")
            else:
                # 非模組引用，保留原始行
                result_lines.append(line)
        
        return '\n'.join(result_lines)
