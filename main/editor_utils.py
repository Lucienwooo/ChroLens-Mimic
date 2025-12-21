# -*- coding: utf-8 -*-
"""
ChroLens 編輯器工具模組
包含共用工具函式、常數和 PCB 風格布線器

v2.7.3 - 從 text_script_editor.py 拆分
"""

import os
import tkinter as tk
from tkinter import font as tkfont

# 🔧 載入 LINE Seed 字體
LINE_SEED_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TTF", "LINESeedTW_TTF_Rg.ttf")
try:
    import pyglet
    if os.path.exists(LINE_SEED_FONT_PATH):
        pyglet.font.add_file(LINE_SEED_FONT_PATH)
        LINE_SEED_FONT_LOADED = True
    else:
        LINE_SEED_FONT_LOADED = False
except:
    LINE_SEED_FONT_LOADED = False


# ========== PCB 風格布線器常數 ==========
PCB_COLORS = {
    "main": "#ff8c00",      # 預設線路顏色（橙色）
    "inactive": "#6e7681",  # 無作用節點的連線用灰色
    "success": "#3fb950",   # 成功路徑（綠色）
    "failure": "#f85149",   # 失敗路徑（紅色）
    "loop": "#58a6ff",      # 循環路徑（藍色）
}

PCB_LINE_WIDTH = 4
PCB_GRID_SIZE = 10
PCB_GRAY_COLOR = "#4a4a4a"


def font_tuple(size, weight=None, monospace=False):
    """
    回傳字體元組
    :param size: 字體大小
    :param weight: 字體粗細 (可選)
    :param monospace: 是否使用等寬字體
    :return: 字體元組
    """
    # 優先使用 LINE Seed 字體
    if LINE_SEED_FONT_LOADED:
        fam = "LINE Seed TW"
    else:
        fam = "Consolas" if monospace else "Microsoft JhengHei"
    if weight:
        return (fam, size, weight)
    return (fam, size)


class GlobalRouter:
    """全域碰撞偵測布線器 - PCB 風格
    
    用於圖形模式的線路碰撞偵測和路徑計算，
    確保連接線不會穿過節點或相互重疊。
    """
    
    def __init__(self, nodes):
        self.nodes = nodes
        self.h_segments = {}
        self.v_segments = {}
        self.label_rects = []
        self.line_count = 0
        self._mark_nodes_as_blocked()
    
    def _mark_nodes_as_blocked(self):
        """標記節點位置為阻擋區域"""
        self.node_rects = []
        padding = 4
        for node in self.nodes:
            self.node_rects.append({
                "x1": node["x"] - padding,
                "y1": node["y"] - padding,
                "x2": node["x"] + node["width"] + padding,
                "y2": node["y"] + node["height"] + padding,
            })
    
    def _snap(self, val):
        """對齊到網格"""
        return round(val / PCB_GRID_SIZE) * PCB_GRID_SIZE
    
    def _is_h_free(self, y, x1, x2, check_nodes=True, from_node_idx=None, to_node_idx=None):
        """檢查水平線段是否空閒"""
        y_key = self._snap(y)
        x1, x2 = min(x1, x2), max(x1, x2)
        
        if y_key in self.h_segments:
            for sx1, sx2, _ in self.h_segments[y_key]:
                if not (x2 <= sx1 - 5 or x1 >= sx2 + 5):
                    return False
        
        if check_nodes:
            for i, rect in enumerate(self.node_rects):
                if from_node_idx is not None and i == from_node_idx:
                    continue
                if to_node_idx is not None and i == to_node_idx:
                    continue
                if rect["y1"] <= y <= rect["y2"]:
                    if not (x2 <= rect["x1"] or x1 >= rect["x2"]):
                        return False
        return True
    
    def _is_v_free(self, x, y1, y2, check_nodes=True, from_node_idx=None, to_node_idx=None):
        """檢查垂直線段是否空閒"""
        x_key = self._snap(x)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        if x_key in self.v_segments:
            for sy1, sy2, _ in self.v_segments[x_key]:
                if not (y2 <= sy1 - 5 or y1 >= sy2 + 5):
                    return False
        
        if check_nodes:
            for i, rect in enumerate(self.node_rects):
                if from_node_idx is not None and i == from_node_idx:
                    continue
                if to_node_idx is not None and i == to_node_idx:
                    continue
                if rect["x1"] <= x <= rect["x2"]:
                    if not (y2 <= rect["y1"] or y1 >= rect["y2"]):
                        return False
        return True
    
    def _can_direct_connect(self, x1, y1, x2, y2, from_idx, to_idx):
        """檢查是否可以直接連接"""
        min_x, max_x = min(x1, x2), max(x1, x2)
        for i, rect in enumerate(self.node_rects):
            if i == from_idx or i == to_idx:
                continue
            if rect["x1"] < max_x and rect["x2"] > min_x:
                if rect["y1"] <= y1 <= rect["y2"]:
                    return False
        return True
    
    def _is_label_pos_free(self, x, y, w=30, h=16):
        """檢查標籤位置是否空閒"""
        for rect in self.label_rects:
            if not (x + w < rect["x1"] or x - w > rect["x2"] or
                    y + h < rect["y1"] or y - h > rect["y2"]):
                return False
        for rect in self.node_rects:
            if not (x + w < rect["x1"] or x - w > rect["x2"] or
                    y + h < rect["y1"] or y - h > rect["y2"]):
                return False
        return True
    
    def find_label_position(self, path):
        """找到適合放置標籤的位置"""
        for i in range(len(path)):
            x, y = path[i]
            for offset_y in [0, -20, 20, -40, 40]:
                test_y = y + offset_y
                if self._is_label_pos_free(x, test_y):
                    self.label_rects.append({
                        "x1": x - 20, "y1": test_y - 10,
                        "x2": x + 20, "y2": test_y + 10,
                    })
                    return (x, test_y)
        
        mid = len(path) // 2
        if mid < len(path):
            x, y = path[mid]
            for offset_x in [-30, 30, -60, 60]:
                for offset_y in [0, -15, 15]:
                    test_x, test_y = x + offset_x, y + offset_y
                    if self._is_label_pos_free(test_x, test_y):
                        self.label_rects.append({
                            "x1": test_x - 20, "y1": test_y - 10,
                            "x2": test_x + 20, "y2": test_y + 10,
                        })
                        return (test_x, test_y)
        
        if len(path) >= 2:
            return (path[-2][0], path[-2][1] - 20)
        return path[len(path) // 2] if path else (0, 0)
    
    def _mark_used(self, path, line_id):
        """標記路徑為已使用"""
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            if abs(y2 - y1) < 3:
                y_key = self._snap(y1)
                if y_key not in self.h_segments:
                    self.h_segments[y_key] = []
                self.h_segments[y_key].append((min(x1, x2), max(x1, x2), line_id))
            elif abs(x2 - x1) < 3:
                x_key = self._snap(x1)
                if x_key not in self.v_segments:
                    self.v_segments[x_key] = []
                self.v_segments[x_key].append((min(y1, y2), max(y1, y2), line_id))
    
    def _find_h_channel(self, base_y, x1, x2, direction=1):
        """找到空閒的水平通道"""
        for offset in range(0, 400, PCB_GRID_SIZE):
            test_y = base_y + offset * direction
            if self._is_h_free(test_y, x1, x2):
                return test_y
        return base_y + 250 * direction
    
    def _find_v_channel(self, base_x, y1, y2, direction=1):
        """找到空閒的垂直通道"""
        for offset in range(0, 400, PCB_GRID_SIZE):
            test_x = base_x + offset * direction
            if self._is_v_free(test_x, y1, y2):
                return test_x
        return base_x + 250 * direction
    
    def route(self, from_node, to_node, path_type, from_idx=None, to_idx=None):
        """計算兩個節點之間的路徑
        
        Args:
            from_node: 起始節點
            to_node: 目標節點
            path_type: 路徑類型 ("main", "success", "failure", "loop")
            from_idx: 起始節點索引（用於避免碰撞檢測）
            to_idx: 目標節點索引（用於避免碰撞檢測）
            
        Returns:
            路徑點列表
        """
        self.line_count += 1
        line_id = self.line_count
        
        x1 = from_node["x"] + from_node["width"]
        y1 = from_node["y"] + from_node["height"] // 2
        x2 = to_node["x"]
        y2 = to_node["y"] + to_node["height"] // 2
        
        path = [(x1, y1)]
        
        dx = x2 - x1
        going_right = dx > 0
        going_left = dx < 0
        same_row = from_node.get("row") == to_node.get("row")
        
        if going_right and same_row:
            can_direct = self._can_direct_connect(x1, y1, x2, y2, from_idx, to_idx)
            line_free = self._is_h_free(y1, x1, x2, check_nodes=False)
            
            if can_direct and line_free:
                path.append((x2, y1))
            else:
                channel_y = self._find_h_channel(y1 - 20, x1, x2, -1)
                path.append((x1 + 15, y1))
                path.append((x1 + 15, channel_y))
                path.append((x2 - 15, channel_y))
                path.append((x2 - 15, y2))
        
        elif going_right:
            mid_x = (x1 + x2) // 2
            if self._is_v_free(mid_x, min(y1, y2), max(y1, y2), from_node_idx=from_idx, to_node_idx=to_idx):
                path.append((mid_x, y1))
                path.append((mid_x, y2))
            else:
                mid_x = self._find_v_channel(mid_x, min(y1, y2), max(y1, y2), 1)
                path.append((mid_x, y1))
                path.append((mid_x, y2))
        
        elif going_left:
            if path_type == "loop":
                top_y = min(n["y"] for n in self.nodes) - 50
                channel_y = self._find_h_channel(top_y, min(x1, x2) - 30, max(x1, x2) + 30, -1)
            elif path_type == "failure":
                bottom_y = max(n["y"] + n["height"] for n in self.nodes) + 50
                channel_y = self._find_h_channel(bottom_y, min(x1, x2) - 30, max(x1, x2) + 30, 1)
            else:
                channel_y = self._find_h_channel(
                    min(n["y"] for n in self.nodes) - 40,
                    min(x1, x2) - 30, max(x1, x2) + 30, -1
                )
            
            exit_x = self._find_v_channel(x1 + 20, min(y1, channel_y), max(y1, channel_y), 1)
            entry_x = self._find_v_channel(x2 - 20, min(y2, channel_y), max(y2, channel_y), -1)
            
            path.append((exit_x, y1))
            path.append((exit_x, channel_y))
            path.append((entry_x, channel_y))
            path.append((entry_x, y2))
        
        else:
            test_x = x1 + 15
            if self._is_v_free(test_x, min(y1, y2), max(y1, y2), from_node_idx=from_idx, to_node_idx=to_idx):
                path.append((test_x, y2))
            else:
                mid_x = self._find_v_channel(x1 + 15, min(y1, y2), max(y1, y2), 1)
                path.append((mid_x, y1))
                path.append((mid_x, y2))
        
        path.append((x2, y2))
        self._mark_used(path, line_id)
        return path
