import math

class GlobalRouter:
    """全域碰撞偵測布線器 - PCB 風格 (v2.8.3: 支援視覺縮放)"""
    
    def __init__(self, nodes, scale=1.0):
        self.nodes = nodes
        self.scale = scale
        # 基於縮放比例動態調整網格
        self.grid_size = max(2, int(PCB_GRID_SIZE * scale))
        self.h_segments = {}
        self.v_segments = {}
        self.label_rects = []
        self.node_rects = []
        self.line_count = 0
        self._mark_nodes_as_blocked()
    
    def _mark_nodes_as_blocked(self):
        self.node_rects = []
        #  Padding 隨比例縮放
        padding = 4 * self.scale
        for node in self.nodes:
            # 使用 .get 以防寬高度缺失
            w = node.get("width", 150)
            h = node.get("height", 36)
            self.node_rects.append({
                "x1": node["x"] - padding,
                "y1": node["y"] - padding,
                "x2": node["x"] + w + padding,
                "y2": node["y"] + h + padding,
            })
    
    def _snap(self, val):
        return round(val / self.grid_size) * self.grid_size
    
    def _is_h_free(self, y, x1, x2, check_nodes=True, from_node_idx=None, to_node_idx=None):
        y_key = self._snap(y)
        x1, x2 = min(x1, x2), max(x1, x2)
        safe_dist = 5 * self.scale
        
        if y_key in self.h_segments:
            for sx1, sx2, _ in self.h_segments[y_key]:
                if not (x2 <= sx1 - safe_dist or x1 >= sx2 + safe_dist):
                    return False
        
        if check_nodes:
            for i, rect in enumerate(self.node_rects):
                if from_node_idx is not None and i == from_node_idx: continue
                if to_node_idx is not None and i == to_node_idx: continue
                if rect["y1"] <= y <= rect["y2"]:
                    if not (x2 <= rect["x1"] or x1 >= rect["x2"]):
                        return False
        return True
    
    def _is_v_free(self, x, y1, y2, check_nodes=True, from_node_idx=None, to_node_idx=None):
        x_key = self._snap(x)
        y1, y2 = min(y1, y2), max(y1, y2)
        safe_dist = 5 * self.scale
        
        if x_key in self.v_segments:
            for sy1, sy2, _ in self.v_segments[x_key]:
                if not (y2 <= sy1 - safe_dist or y1 >= sy2 + safe_dist):
                    return False
        
        if check_nodes:
            for i, rect in enumerate(self.node_rects):
                if from_node_idx is not None and i == from_node_idx: continue
                if to_node_idx is not None and i == to_node_idx: continue
                if rect["x1"] <= x <= rect["x2"]:
                    if not (y2 <= rect["y1"] or y1 >= rect["y2"]):
                        return False
        return True
    
    def _can_direct_connect(self, x1, y1, x2, y2, from_idx, to_idx):
        min_x, max_x = min(x1, x2), max(x1, x2)
        for i, rect in enumerate(self.node_rects):
            if i == from_idx or i == to_idx: continue
            if rect["x1"] < max_x and rect["x2"] > min_x:
                if rect["y1"] <= y1 <= rect["y2"]:
                    return False
        return True
    
    def _is_label_pos_free(self, x, y, w=30, h=16):
        w, h = w * self.scale, h * self.scale
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
        scale_off20 = 20 * self.scale
        scale_off10 = 10 * self.scale
        
        for i in range(len(path)):
            x, y = path[i]
            for offset_y in [0, -scale_off20, scale_off20]:
                test_y = y + offset_y
                if self._is_label_pos_free(x, test_y):
                    self.label_rects.append({"x1": x - scale_off20, "y1": test_y - scale_off10, "x2": x + scale_off20, "y2": test_y + scale_off10})
                    return (x, test_y)
        mid = len(path) // 2
        return path[mid] if path else (0, 0)
    
    def _mark_used(self, path, line_id):
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            if abs(y2 - y1) < 2:
                y_key = self._snap(y1)
                if y_key not in self.h_segments: self.h_segments[y_key] = []
                self.h_segments[y_key].append((min(x1, x2), max(x1, x2), line_id))
            elif abs(x2 - x1) < 2:
                x_key = self._snap(x1)
                if x_key not in self.v_segments: self.v_segments[x_key] = []
                self.v_segments[x_key].append((min(y1, y2), max(y1, y2), line_id))
    
    def _find_h_channel(self, base_y, x1, x2, direction=1):
        for offset in range(0, int(400 * self.scale), self.grid_size):
            test_y = base_y + offset * direction
            if self._is_h_free(test_y, x1, x2):
                return test_y
        return base_y + (250 * self.scale) * direction
    
    def _find_v_channel(self, base_x, y1, y2, direction=1):
        for offset in range(0, int(400 * self.scale), self.grid_size):
            test_x = base_x + offset * direction
            if self._is_v_free(test_x, y1, y2):
                return test_x
        return base_x + (250 * self.scale) * direction
    
    def route(self, from_node, to_node, path_type, from_idx=None, to_idx=None):
        self.line_count += 1
        
        #  使用即時縮放後的寬高 (使用 .get 確保安全)
        fw = from_node.get("width", 150)
        fh = from_node.get("height", 36)
        tw = to_node.get("width", 150)
        th = to_node.get("height", 36)
        
        x1 = from_node["x"] + fw
        y1 = from_node["y"] + fh // 2
        x2 = to_node["x"]
        y2 = to_node["y"] + th // 2
        
        path = [(x1, y1)]
        dx = x2 - x1
        off15 = 15 * self.scale
        off20 = 20 * self.scale
        
        # 1. 向右發展的情形
        if dx > 0:
            # 如果在同一行，嘗試直線連接
            if from_node.get("row") == to_node.get("row") and self._can_direct_connect(x1, y1, x2, y2, from_idx, to_idx):
                path.append((x2, y1))
            else:
                # 不同行或有障礙，使用三段式佈線 (H-V-H)
                # 分叉 (fork) 類型通常需要更早的轉折，讓視覺更像分支
                split_ratio = 0.3 if path_type == "fork" else 0.5
                mid_x = x1 + dx * split_ratio
                
                path.append((mid_x, y1))
                path.append((mid_x, y2))
                path.append((x2, y2))
        
        # 2. 向左發展的情形 (重試或跳轉)
        elif dx <= 0:
            off30 = 30 * self.scale
            off40 = 40 * self.scale
            off50 = 50 * self.scale
            
            if path_type == "loop":
                top_y = min(n["y"] for n in self.nodes) - off50
                channel_y = self._find_h_channel(top_y, min(x1, x2) - off30, max(x1, x2) + off30, -1)
            elif path_type == "failure":
                bottom_y = max(n["y"] + n.get("height", 36) for n in self.nodes) + off50
                channel_y = self._find_h_channel(bottom_y, min(x1, x2) - off30, max(x1, x2) + off30, 1)
            else:
                channel_y = self._find_h_channel(min(n["y"] for n in self.nodes) - off40, min(x1, x2) - off30, max(x1, x2) + off30, -1)
            
            exit_x = x1 + off20
            entry_x = x2 - off20
            path.append((exit_x, y1))
            path.append((exit_x, channel_y))
            path.append((entry_x, channel_y))
            path.append((entry_x, y2))
            path.append((x2, y2))
        
        # 3. 垂直發展的情形 (罕見)
        else:
            path.append((x2, y2))
            
        return path


