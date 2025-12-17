# -*- coding: utf-8 -*-
"""
n8n 風格圖形編輯器預覽版本 v11
動態群組框：
- 群組框隨節點移動自動調整大小
- 不屬於群組的節點被覆蓋時會變灰色
"""

import tkinter as tk
from tkinter import ttk, colorchooser

try:
    import ttkbootstrap as tb
    USE_BOOTSTRAP = True
except ImportError:
    tb = ttk
    USE_BOOTSTRAP = False


DEFAULT_COLORS = {
    "main": "#8B8B8B",
    "success": "#3fb950",
    "failure": "#f85149",
    "loop": "#58a6ff",
}

LINE_WIDTH = 4
GRID_SIZE = 10
GRAY_COLOR = "#4a4a4a"  # 灰色警告色


class GlobalRouter:
    """全域碰撞偵測布線器"""
    
    def __init__(self, nodes):
        self.nodes = nodes
        self.h_segments = {}
        self.v_segments = {}
        self.label_rects = []
        self.line_count = 0
        self._mark_nodes_as_blocked()
    
    def _mark_nodes_as_blocked(self):
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
        return round(val / GRID_SIZE) * GRID_SIZE
    
    def _is_h_free(self, y, x1, x2, check_nodes=True, from_node_idx=None, to_node_idx=None):
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
        min_x, max_x = min(x1, x2), max(x1, x2)
        for i, rect in enumerate(self.node_rects):
            if i == from_idx or i == to_idx:
                continue
            if rect["x1"] < max_x and rect["x2"] > min_x:
                if rect["y1"] <= y1 <= rect["y2"]:
                    return False
        return True
    
    def _is_label_pos_free(self, x, y, w=30, h=16):
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
            x, y = path[-2]
            return (x, y - 20)
        
        return path[len(path) // 2] if path else (0, 0)
    
    def _mark_used(self, path, line_id):
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
        for offset in range(0, 400, GRID_SIZE):
            test_y = base_y + offset * direction
            if self._is_h_free(test_y, x1, x2):
                return test_y
        return base_y + 250 * direction
    
    def _find_v_channel(self, base_x, y1, y2, direction=1):
        for offset in range(0, 400, GRID_SIZE):
            test_x = base_x + offset * direction
            if self._is_v_free(test_x, y1, y2):
                return test_x
        return base_x + 250 * direction
    
    def route(self, from_node, to_node, path_type, from_idx=None, to_idx=None):
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


class N8nStyleGraphPreview:
    """PCB 風格預覽 v11 - 動態群組框"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PCB v11 (動態群組框)")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0d1117")
        
        self.colors = DEFAULT_COLORS.copy()
        self.nodes = []
        self.connections = []
        self.connection_defs = []
        self.group_defs = []  # 群組定義
        self.groups = []  # 群組畫布元素
        self.router = None
        
        self.start_x = 140
        self.start_y = 140
        self.h_gap = 210
        self.v_gap = 110
        self.node_width = 135
        self.node_height = 38
        
        self.drag_data = {"node_idx": None, "x": 0, "y": 0}
        self.pan_data = {"active": False, "x": 0, "y": 0}
        self.canvas_scale = 1.0
        
        self._create_ui()
        self.root.after(100, self._load_sample_script)
    
    def _create_ui(self):
        main_frame = tk.Frame(self.root, bg="#0d1117")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        toolbar = tk.Frame(main_frame, bg="#161b22", height=50)
        toolbar.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            toolbar, text="🔌 PCB v11 | 動態群組框 | 節點覆蓋警告",
            font=("Microsoft JhengHei", 12, "bold"),
            fg="#c9d1d9", bg="#161b22"
        ).pack(side="left", padx=15, pady=10)
        
        color_frame = tk.Frame(toolbar, bg="#161b22")
        color_frame.pack(side="right", padx=10)
        
        for path_type, label in [("main", "主流程"), ("success", "成功"), ("failure", "失敗"), ("loop", "迴圈")]:
            btn = tk.Button(
                color_frame, text=f"● {label}", fg=self.colors[path_type],
                bg="#21262d", relief="flat", font=("Microsoft JhengHei", 9),
                command=lambda pt=path_type: self._choose_color(pt)
            )
            btn.pack(side="left", padx=3)
            setattr(self, f"btn_{path_type}", btn)
        
        tk.Button(
            toolbar, text="🔄 重新布線", command=self._reload,
            bg="#21262d", fg="#c9d1d9", relief="flat", padx=8
        ).pack(side="right", padx=10)
        
        canvas_frame = tk.Frame(main_frame, bg="#010409", bd=1, relief="solid")
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#010409", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Button-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_end)
        
        self.status_label = tk.Label(
            main_frame, text="💡 拖動節點時群組框會自動調整 | 被覆蓋的非群組節點會變灰色",
            font=("Microsoft JhengHei", 9), fg="#8b949e", bg="#0d1117"
        )
        self.status_label.pack(fill="x", pady=(5, 0))
    
    def _choose_color(self, path_type):
        color = colorchooser.askcolor(title=f"選擇 {path_type} 顏色", initialcolor=self.colors[path_type])
        if color[1]:
            self.colors[path_type] = color[1]
            btn = getattr(self, f"btn_{path_type}", None)
            if btn:
                btn.config(fg=color[1])
            self._reload()
    
    def _load_sample_script(self):
        node_defs = [
            {"name": "#開始", "type": "label", "row": 0, "col": 0},
            {"name": ">移動至(500,300)", "type": "mouse", "row": 0, "col": 1},
            {"name": ">點擊(左鍵)", "type": "mouse", "row": 0, "col": 2},
            {"name": "等待 1000ms", "type": "wait", "row": 0, "col": 3},
            
            {"name": "#檢查登入", "type": "condition", "row": 1, "col": 0},
            {"name": "#輸入帳號", "type": "label", "row": 1, "col": 1},
            {"name": "@按鍵>tab", "type": "keyboard", "row": 1, "col": 2},
            {"name": "等待 200ms", "type": "wait", "row": 1, "col": 3},
            
            {"name": "#輸入密碼", "type": "label", "row": 2, "col": 0},
            {"name": ">移動至(450,350)", "type": "mouse", "row": 2, "col": 1},
            {"name": "#驗證登入", "type": "condition", "row": 2, "col": 2},
            {"name": "等待 2000ms", "type": "wait", "row": 2, "col": 3},
            
            {"name": "#登入失敗", "type": "label", "row": 3, "col": 0},
            {"name": "#登入成功", "type": "label", "row": 3, "col": 1},
            {"name": "#資料處理", "type": "label", "row": 3, "col": 2},
            {"name": "#結束", "type": "label", "row": 3, "col": 3},
        ]
        
        self.connection_defs = [
            (12, 4, "loop"),
            (4, 12, "failure"),
            (10, 12, "failure"),
            (4, 5, "success"),
            (10, 13, "success"),
            (13, 14, "success"),
            (14, 15, "success"),
            (0, 1, "main"), (1, 2, "main"), (2, 3, "main"), (3, 4, "main"),
            (5, 6, "main"), (6, 7, "main"), (7, 8, "main"),
            (8, 9, "main"), (9, 10, "main"),
        ]
        
        # ★ 儲存群組定義供動態更新使用 ★
        self.group_defs = [
            {"nodes": [4, 5, 6, 7], "color": "#f85149", "name": "登入檢查區"},
            {"nodes": [8, 9, 10], "color": "#3fb950", "name": "驗證區"},
            {"nodes": [12], "color": "#f85149", "name": "失敗處理"},
            {"nodes": [13, 14, 15], "color": "#3fb950", "name": "成功流程"},
        ]
        
        self._draw_nodes(node_defs)
        self._draw_connections()
        self._draw_groups()
        self._check_group_overlaps()
        
        self.canvas.tag_lower("connection")
    
    def _draw_groups(self):
        """繪製動態群組框"""
        # 刪除舊的群組框
        self.canvas.delete("group")
        self.canvas.delete("group_label")
        self.groups = []
        
        padding = 15
        for group in self.group_defs:
            if not group["nodes"]:
                continue
            
            # ★ 根據實際節點位置計算邊界（不是初始位置）★
            group_nodes = [self.nodes[i] for i in group["nodes"] if i < len(self.nodes)]
            if not group_nodes:
                continue
            
            min_x = min(n["x"] for n in group_nodes) - padding
            min_y = min(n["y"] for n in group_nodes) - padding
            max_x = max(n["x"] + n["width"] for n in group_nodes) + padding
            max_y = max(n["y"] + n["height"] for n in group_nodes) + padding
            
            rect_id = self.canvas.create_rectangle(
                min_x, min_y, max_x, max_y,
                outline=group["color"], width=2, fill="", dash=(4, 2),
                tags=("group", "all_elements")
            )
            label_id = self.canvas.create_text(
                min_x + 4, min_y - 6, text=group.get("name", ""),
                fill=group["color"], font=("Microsoft JhengHei", 7),
                anchor="w", tags=("group_label", "all_elements")
            )
            
            self.groups.append({
                "rect": rect_id,
                "label": label_id,
                "node_indices": group["nodes"],
                "color": group["color"],
                "bounds": {"x1": min_x, "y1": min_y, "x2": max_x, "y2": max_y}
            })
    
    def _check_group_overlaps(self):
        """檢查並標記被群組框覆蓋但不屬於該群組的節點"""
        # 先恢復所有節點的原始顏色
        for node in self.nodes:
            node["grayed"] = False
            style = self._get_style(node["name"], node.get("type", ""))
            self._update_node_color(node, style["border"], style["icon_color"])
        
        # 檢查每個群組
        for group in self.groups:
            bounds = group["bounds"]
            member_indices = set(group["node_indices"])
            
            # 檢查每個節點
            for idx, node in enumerate(self.nodes):
                if idx in member_indices:
                    continue  # 跳過群組成員
                
                # 檢查節點是否被群組框覆蓋
                node_x1, node_y1 = node["x"], node["y"]
                node_x2 = node["x"] + node["width"]
                node_y2 = node["y"] + node["height"]
                
                # 如果有重疊
                if not (node_x2 < bounds["x1"] or node_x1 > bounds["x2"] or
                        node_y2 < bounds["y1"] or node_y1 > bounds["y2"]):
                    # 這個節點被覆蓋了但不屬於群組 -> 變灰色
                    node["grayed"] = True
                    self._update_node_color(node, GRAY_COLOR, GRAY_COLOR)
    
    def _update_node_color(self, node, border_color, icon_color):
        """更新節點顏色"""
        node_tag = node["tag"]
        
        # 找到節點的卡片和圖示元素
        items = self.canvas.find_withtag(node_tag)
        for item in items:
            item_type = self.canvas.type(item)
            tags = self.canvas.gettags(item)
            
            if "node_card" in tags:
                self.canvas.itemconfig(item, outline=border_color)
            elif "port" in tags:
                self.canvas.itemconfig(item, outline=border_color)
            elif item_type == "oval" and "port" not in tags:
                # 這是圖示背景
                self.canvas.itemconfig(item, fill=icon_color)
    
    def _draw_nodes(self, node_defs):
        for node_def in node_defs:
            x = self.start_x + node_def["col"] * self.h_gap
            y = self.start_y + node_def["row"] * self.v_gap
            self._create_node(node_def["name"], node_def["type"], x, y, node_def["row"], node_def["col"])
    
    def _create_node(self, name, node_type, x, y, row, col):
        node_idx = len(self.nodes)
        node_tag = f"node_{node_idx}"
        w, h = self.node_width, self.node_height
        style = self._get_style(name, node_type)
        
        self.canvas.create_rectangle(x + 2, y + 2, x + w + 2, y + h + 2,
            fill="#010409", outline="", tags=(node_tag, "all_elements"))
        
        self.canvas.create_rectangle(x, y, x + w, y + h,
            fill="#161b22", outline=style["border"], width=2,
            tags=(node_tag, "all_elements", "node_card"))
        
        icon_x, icon_y = x + 16, y + h // 2
        self.canvas.create_oval(icon_x - 9, icon_y - 9, icon_x + 9, icon_y + 9,
            fill=style["icon_color"], outline="", tags=(node_tag, "all_elements"))
        self.canvas.create_text(icon_x, icon_y, text=style["icon"], fill="white",
            font=("Microsoft JhengHei", 7, "bold"), tags=(node_tag, "all_elements"))
        
        display_name = name[:9] + ".." if len(name) > 9 else name
        self.canvas.create_text(x + 28, y + h // 2, text=display_name,
            fill="#c9d1d9", font=("Microsoft JhengHei", 7),
            anchor="w", tags=(node_tag, "all_elements", "node_text"))
        
        self.canvas.create_oval(x - 3, icon_y - 3, x + 3, icon_y + 3,
            fill="#161b22", outline=style["border"], width=2,
            tags=(node_tag, "all_elements", "port"))
        self.canvas.create_oval(x + w - 3, icon_y - 3, x + w + 3, icon_y + 3,
            fill="#161b22", outline=style["border"], width=2,
            tags=(node_tag, "all_elements", "port"))
        
        self.nodes.append({
            "tag": node_tag, "x": x, "y": y,
            "width": w, "height": h, "name": name,
            "row": row, "col": col, "type": node_type,
            "grayed": False,
        })
        return node_idx
    
    def _draw_connections(self):
        self.router = GlobalRouter(self.nodes)
        
        for from_idx, to_idx, path_type in self.connection_defs:
            if from_idx < len(self.nodes) and to_idx < len(self.nodes):
                from_node = self.nodes[from_idx]
                to_node = self.nodes[to_idx]
                path = self.router.route(from_node, to_node, path_type, from_idx, to_idx)
                self._draw_path(path, path_type, from_idx, to_idx)
    
    def _draw_path(self, path, path_type, from_idx, to_idx):
        color = self.colors.get(path_type, self.colors["main"])
        conn_tag = f"conn_{len(self.connections)}"
        
        if len(path) >= 2:
            points = []
            for px, py in path:
                points.extend([px, py])
            
            self.canvas.create_line(
                *points, fill=color, width=LINE_WIDTH,
                capstyle="round", joinstyle="round",
                tags=(conn_tag, "all_elements", "connection")
            )
        
        if path_type in ("success", "failure", "loop"):
            labels = {"success": "成功", "failure": "失敗", "loop": "重試"}
            lx, ly = self.router.find_label_position(path)
            
            self.canvas.create_rectangle(
                lx - 14, ly - 7, lx + 14, ly + 7,
                fill="#161b22", outline=color, width=1,
                tags=(conn_tag, "all_elements", "connection", "label")
            )
            self.canvas.create_text(
                lx, ly, text=labels.get(path_type, ""),
                fill=color, font=("Microsoft JhengHei", 6, "bold"),
                tags=(conn_tag, "all_elements", "connection", "label")
            )
        
        self.connections.append({
            "tag": conn_tag, "from": from_idx, "to": to_idx,
            "path_type": path_type, "path": path,
        })
    
    def _get_style(self, name, node_type):
        if node_type == "condition" or "檢查" in name or "驗證" in name:
            return {"icon": "?", "icon_color": "#8957e5", "border": "#8957e5"}
        elif name.startswith("#"):
            return {"icon": "#", "icon_color": "#58a6ff", "border": "#58a6ff"}
        elif "移動" in name or "點擊" in name or node_type == "mouse":
            return {"icon": "🖱", "icon_color": "#1f6feb", "border": "#1f6feb"}
        elif name.startswith("@") or node_type == "keyboard":
            return {"icon": "⌨", "icon_color": "#39d353", "border": "#39d353"}
        elif "等待" in name or node_type == "wait":
            return {"icon": "⏱", "icon_color": "#d29922", "border": "#d29922"}
        return {"icon": "▶", "icon_color": "#6e7681", "border": "#6e7681"}
    
    def _on_click(self, event):
        items = self.canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)
        for item in items:
            for tag in self.canvas.gettags(item):
                if tag.startswith("node_"):
                    self.drag_data = {"node_idx": int(tag.split("_")[1]), "x": event.x, "y": event.y}
                    return
        self.pan_data = {"active": True, "x": event.x, "y": event.y}
        self.canvas.config(cursor="fleur")
    
    def _on_drag(self, event):
        if self.drag_data.get("node_idx") is not None:
            dx, dy = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
            node = self.nodes[self.drag_data["node_idx"]]
            self.canvas.move(node["tag"], dx, dy)
            node["x"] += dx
            node["y"] += dy
            self.drag_data["x"], self.drag_data["y"] = event.x, event.y
            
            # ★ 更新群組框和連線 ★
            self._redraw_connections()
            self._draw_groups()
            self._check_group_overlaps()
            
        elif self.pan_data.get("active"):
            dx, dy = event.x - self.pan_data["x"], event.y - self.pan_data["y"]
            self.canvas.move("all_elements", dx, dy)
            for node in self.nodes:
                node["x"] += dx
                node["y"] += dy
            self.pan_data["x"], self.pan_data["y"] = event.x, event.y
    
    def _on_release(self, event):
        self.drag_data["node_idx"] = None
        self.pan_data["active"] = False
        self.canvas.config(cursor="crosshair")
    
    def _on_zoom(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        new_scale = self.canvas_scale * scale
        if 0.3 <= new_scale <= 3.0:
            self.canvas_scale = new_scale
            self.canvas.scale("all_elements", event.x, event.y, scale, scale)
            for node in self.nodes:
                node["x"] = event.x + (node["x"] - event.x) * scale
                node["y"] = event.y + (node["y"] - event.y) * scale
                node["width"] *= scale
                node["height"] *= scale
    
    def _on_pan_start(self, event):
        self.pan_data = {"active": True, "x": event.x, "y": event.y}
        self.canvas.config(cursor="fleur")
    
    def _on_pan_move(self, event):
        if self.pan_data.get("active"):
            dx, dy = event.x - self.pan_data["x"], event.y - self.pan_data["y"]
            self.canvas.move("all_elements", dx, dy)
            for node in self.nodes:
                node["x"] += dx
                node["y"] += dy
            self.pan_data["x"], self.pan_data["y"] = event.x, event.y
    
    def _on_pan_end(self, event):
        self.pan_data["active"] = False
        self.canvas.config(cursor="crosshair")
    
    def _redraw_connections(self):
        self.canvas.delete("connection")
        self.connections = []
        self._draw_connections()
        self.canvas.tag_lower("connection")
    
    def _reload(self):
        self.canvas.delete("all")
        self.nodes, self.connections, self.groups = [], [], []
        self.canvas_scale = 1.0
        self._load_sample_script()


def main():
    root = tb.Window(themename="darkly") if USE_BOOTSTRAP else tk.Tk()
    if not USE_BOOTSTRAP:
        root.configure(bg="#0d1117")
    N8nStyleGraphPreview(root)
    root.mainloop()


if __name__ == "__main__":
    main()
