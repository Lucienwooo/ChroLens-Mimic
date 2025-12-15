# -*- coding: utf-8 -*-
"""
Mini Metro 風格變體設計方案
提供5種不同的視覺風格供選擇

使用方法：
1. 這個文件可以直接用任何文本編輯器打開查看
2. 複製你喜歡的風格代碼，替換 text_script_editor.py 中的對應方法
3. 或者運行本文件查看示例視覺效果

如果無法在 VS Code 中打開：
- 右鍵點擊文件 → 選擇「打開方式」→ 選擇「文本編輯器」
- 或使用記事本、Notepad++ 等任何文本編輯器打開
"""

import tkinter as tk
from tkinter import ttk

# ============================================================
# 方案 1: 經典 Mini Metro 風格（當前已應用）
# 特點：圓形站點、粗線條、鮮豔配色、只用直線和90度角
# ============================================================

def draw_workflow_node_style1(self, label, commands):
    """方案1：經典 Mini Metro - 圓形站點，鮮艷配色"""
    if label not in self.workflow_nodes:
        return
    
    node_data = self.workflow_nodes[label]
    x, y = node_data['x'], node_data['y']
    
    has_condition = any(c.startswith('>>>') for c in commands)
    is_start = label == list(self.workflow_nodes.keys())[0] if self.workflow_nodes else False
    is_end = not any(conn[0] == label for conn in self.workflow_connections)
    
    radius = 35
    
    # Mini Metro 經典配色
    if is_start:
        fill_color = "#00b300"  # 綠線
    elif is_end:
        fill_color = "#e63946"  # 紅線
    elif has_condition:
        fill_color = "#f77f00"  # 橙線
    else:
        fill_color = "#0077be"  # 藍線
    
    # 繪製圓形
    shape_id = self.workflow_canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill=fill_color,
        outline="#ffffff",
        width=4,
        tags="node_shape"
    )
    node_data['items'].append(shape_id)
    
    # 文字
    label_text = label.replace('#', '')[:4]
    text_id = self.workflow_canvas.create_text(
        x, y,
        text=label_text,
        fill="#ffffff",
        font=("LINE Seed TW", 11, "bold"),
        tags="node_text"
    )
    node_data['items'].append(text_id)


# ============================================================
# 方案 2: 雙圈站點風格
# 特點：內外雙圈設計、更立體、保持簡潔
# ============================================================

def draw_workflow_node_style2(self, label, commands):
    """方案2：雙圈站點 - 內外圈設計，更有層次感"""
    if label not in self.workflow_nodes:
        return
    
    node_data = self.workflow_nodes[label]
    x, y = node_data['x'], node_data['y']
    
    has_condition = any(c.startswith('>>>') for c in commands)
    is_start = label == list(self.workflow_nodes.keys())[0] if self.workflow_nodes else False
    is_end = not any(conn[0] == label for conn in self.workflow_connections)
    
    outer_radius = 38
    inner_radius = 28
    
    # 配色方案
    if is_start:
        outer_color = "#00b300"
        inner_color = "#ffffff"
    elif is_end:
        outer_color = "#e63946"
        inner_color = "#ffffff"
    elif has_condition:
        outer_color = "#f77f00"
        inner_color = "#ffffff"
    else:
        outer_color = "#0077be"
        inner_color = "#ffffff"
    
    # 外圈
    outer_id = self.workflow_canvas.create_oval(
        x - outer_radius, y - outer_radius,
        x + outer_radius, y + outer_radius,
        fill=outer_color,
        outline="",
        tags="node_shape"
    )
    node_data['items'].append(outer_id)
    
    # 內圈
    inner_id = self.workflow_canvas.create_oval(
        x - inner_radius, y - inner_radius,
        x + inner_radius, y + inner_radius,
        fill=inner_color,
        outline="",
        tags="node_shape"
    )
    node_data['items'].append(inner_id)
    
    # 文字
    label_text = label.replace('#', '')[:4]
    text_id = self.workflow_canvas.create_text(
        x, y,
        text=label_text,
        fill=outer_color,
        font=("LINE Seed TW", 10, "bold"),
        tags="node_text"
    )
    node_data['items'].append(text_id)


# ============================================================
# 方案 3: 扁平圓形 + 陰影
# 特點：扁平設計、柔和陰影、現代感
# ============================================================

def draw_workflow_node_style3(self, label, commands):
    """方案3：扁平圓形 + 陰影 - 現代扁平化設計"""
    if label not in self.workflow_nodes:
        return
    
    node_data = self.workflow_nodes[label]
    x, y = node_data['x'], node_data['y']
    
    has_condition = any(c.startswith('>>>') for c in commands)
    is_start = label == list(self.workflow_nodes.keys())[0] if self.workflow_nodes else False
    is_end = not any(conn[0] == label for conn in self.workflow_connections)
    
    radius = 32
    shadow_offset = 3
    
    # 配色（柔和的扁平色）
    if is_start:
        fill_color = "#2ecc71"  # 翠綠
        shadow_color = "#27ae60"
    elif is_end:
        fill_color = "#e74c3c"  # 紅色
        shadow_color = "#c0392b"
    elif has_condition:
        fill_color = "#f39c12"  # 金黃
        shadow_color = "#d68910"
    else:
        fill_color = "#3498db"  # 藍色
        shadow_color = "#2980b9"
    
    # 陰影圈
    shadow_id = self.workflow_canvas.create_oval(
        x - radius + shadow_offset, y - radius + shadow_offset,
        x + radius + shadow_offset, y + radius + shadow_offset,
        fill=shadow_color,
        outline="",
        tags="node_shape"
    )
    node_data['items'].append(shadow_id)
    
    # 主圓形
    main_id = self.workflow_canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill=fill_color,
        outline="",
        tags="node_shape"
    )
    node_data['items'].append(main_id)
    
    # 文字
    label_text = label.replace('#', '')[:4]
    text_id = self.workflow_canvas.create_text(
        x, y,
        text=label_text,
        fill="#ffffff",
        font=("LINE Seed TW", 11, "bold"),
        tags="node_text"
    )
    node_data['items'].append(text_id)


# ============================================================
# 方案 4: 圓形 + 圖標式設計
# 特點：不同類型用不同圖案、更直觀
# ============================================================

def draw_workflow_node_style4(self, label, commands):
    """方案4：圓形 + 圖標 - 用圖案區分節點類型"""
    if label not in self.workflow_nodes:
        return
    
    node_data = self.workflow_nodes[label]
    x, y = node_data['x'], node_data['y']
    
    has_condition = any(c.startswith('>>>') for c in commands)
    is_start = label == list(self.workflow_nodes.keys())[0] if self.workflow_nodes else False
    is_end = not any(conn[0] == label for conn in self.workflow_connections)
    
    radius = 35
    
    # 統一背景色（淺色）
    base_color = "#f0f0f0"
    
    # 主圓形
    main_id = self.workflow_canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill=base_color,
        outline="#cccccc",
        width=2,
        tags="node_shape"
    )
    node_data['items'].append(main_id)
    
    # 根據類型繪製內部圖案
    if is_start:
        # 開始：綠色播放三角形
        points = [x-10, y-12, x-10, y+12, x+12, y]
        icon_id = self.workflow_canvas.create_polygon(
            points,
            fill="#00b300",
            outline="",
            tags="node_icon"
        )
        node_data['items'].append(icon_id)
        
    elif is_end:
        # 結束：紅色方形
        icon_id = self.workflow_canvas.create_rectangle(
            x-12, y-12, x+12, y+12,
            fill="#e63946",
            outline="",
            tags="node_icon"
        )
        node_data['items'].append(icon_id)
        
    elif has_condition:
        # 條件：橙色菱形
        points = [x, y-15, x+15, y, x, y+15, x-15, y]
        icon_id = self.workflow_canvas.create_polygon(
            points,
            fill="#f77f00",
            outline="",
            tags="node_icon"
        )
        node_data['items'].append(icon_id)
        
    else:
        # 一般：藍色圓形
        icon_id = self.workflow_canvas.create_oval(
            x-12, y-12, x+12, y+12,
            fill="#0077be",
            outline="",
            tags="node_icon"
        )
        node_data['items'].append(icon_id)
    
    # 標籤文字在下方
    label_text = label.replace('#', '')
    if len(label_text) > 6:
        label_text = label_text[:6]
    
    text_id = self.workflow_canvas.create_text(
        x, y + radius + 12,
        text=label_text,
        fill="#333333",
        font=("LINE Seed TW", 9),
        tags="node_text"
    )
    node_data['items'].append(text_id)


# ============================================================
# 方案 5: 霓虹燈管風格
# 特點：發光效果、鮮豔高對比、賽博朋克感
# ============================================================

def draw_workflow_node_style5(self, label, commands):
    """方案5：霓虹燈管風格 - 發光效果，賽博風格"""
    if label not in self.workflow_nodes:
        return
    
    node_data = self.workflow_nodes[label]
    x, y = node_data['x'], node_data['y']
    
    has_condition = any(c.startswith('>>>') for c in commands)
    is_start = label == list(self.workflow_nodes.keys())[0] if self.workflow_nodes else False
    is_end = not any(conn[0] == label for conn in self.workflow_connections)
    
    radius = 35
    
    # 霓虹配色
    if is_start:
        glow_color = "#00ff88"  # 青綠
        core_color = "#ffffff"
    elif is_end:
        glow_color = "#ff0055"  # 洋紅
        core_color = "#ffffff"
    elif has_condition:
        glow_color = "#ffaa00"  # 橙黃
        core_color = "#ffffff"
    else:
        glow_color = "#00aaff"  # 電藍
        core_color = "#ffffff"
    
    # 外發光層（多層模擬發光效果）
    for i in range(3, 0, -1):
        glow_radius = radius + i * 3
        opacity_hex = format(int(255 * 0.15 * i), '02x')
        
        glow_id = self.workflow_canvas.create_oval(
            x - glow_radius, y - glow_radius,
            x + glow_radius, y + glow_radius,
            fill=glow_color,
            outline="",
            tags="node_glow"
        )
        node_data['items'].append(glow_id)
    
    # 主圓形（發光核心）
    main_id = self.workflow_canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill=glow_color,
        outline=core_color,
        width=3,
        tags="node_shape"
    )
    node_data['items'].append(main_id)
    
    # 內核
    core_id = self.workflow_canvas.create_oval(
        x - 15, y - 15,
        x + 15, y + 15,
        fill=core_color,
        outline="",
        tags="node_core"
    )
    node_data['items'].append(core_id)
    
    # 文字（發光色）
    label_text = label.replace('#', '')[:3]
    text_id = self.workflow_canvas.create_text(
        x, y,
        text=label_text,
        fill=glow_color,
        font=("LINE Seed TW", 10, "bold"),
        tags="node_text"
    )
    node_data['items'].append(text_id)


# ============================================================
# 連接線風格變體
# ============================================================

def draw_connections_style1_sharp(self):
    """連接線方案1：銳利直角（Metro原版）"""
    # 這是當前已應用的版本
    # 特點：只用直線和90度角，最經典的Metro風格
    pass


def draw_connections_style2_curved(self):
    """連接線方案2：圓角轉彎（柔和版）"""
    # 在轉角處使用圓弧過渡
    # 視覺更柔和，但仍保持Metro的簡潔感
    pass


def draw_connections_style3_diagonal(self):
    """連接線方案3：45度斜線（動態版）"""
    # 允許使用45度斜線
    # 更靈活，路徑更短
    pass


def draw_connections_style4_bezier(self):
    """連接線方案4：貝塞爾曲線（流暢版）"""
    # 使用平滑曲線連接
    # 最流暢，但不太像Metro
    pass


def draw_connections_style5_neon(self):
    """連接線方案5：霓虹燈管（發光版）"""
    # 配合霓虹站點風格
    # 線條有發光效果
    pass


# ============================================================
# 使用說明
# ============================================================
"""
如何應用這些風格：

1. 打開 text_script_editor.py

2. 找到 _draw_workflow_node 方法（約在第7260行）

3. 將整個方法替換為你喜歡的風格（例如 draw_workflow_node_style2）

4. 記得把方法名改回 _draw_workflow_node

5. 保存並重新運行程序

推薦組合：
- 經典清爽：方案1（圓形） + 當前連接線
- 現代扁平：方案3（陰影） + 連接線方案2（圓角）
- 直觀易懂：方案4（圖標） + 連接線方案1（直角）
- 賽博風格：方案5（霓虹） + 連接線方案5（發光）
- 精緻優雅：方案2（雙圈） + 連接線方案3（斜線）
"""


# ============================================================
# 示例運行程序（可選）
# ============================================================

if __name__ == "__main__":
    """
    運行此檔案以查看各種風格的示例
    """
    
    print("=" * 60)
    print("Mini Metro 風格變體設計方案")
    print("=" * 60)
    print()
    print("📌 本檔案包含 5 種不同的視覺風格代碼")
    print()
    print("✅ 方案 1: 經典 Mini Metro（圓形站點，鮮豔配色）")
    print("✅ 方案 2: 雙圈站點（內外雙圈，更有層次）")
    print("✅ 方案 3: 扁平陰影（現代扁平化設計）")
    print("✅ 方案 4: 圖標式（用圖案區分節點類型）")
    print("✅ 方案 5: 霓虹燈管（發光效果，賽博風格）")
    print()
    print("=" * 60)
    print("📖 使用方法：")
    print("=" * 60)
    print()
    print("1. 在本檔案中找到你喜歡的風格代碼")
    print("   例如：draw_workflow_node_style2")
    print()
    print("2. 複製整個函數（從 def 到最後）")
    print()
    print("3. 打開 text_script_editor.py")
    print()
    print("4. 搜索並找到 '_draw_workflow_node' 方法")
    print()
    print("5. 用複製的代碼替換整個方法")
    print()
    print("6. 將函數名改回 '_draw_workflow_node'")
    print("   （去掉 style1/style2 等後綴）")
    print()
    print("7. 保存文件並重新運行程序")
    print()
    print("=" * 60)
    print("🎨 推薦組合：")
    print("=" * 60)
    print()
    print("• 日常使用：方案 1（經典 Metro）")
    print("• 專業展示：方案 2（雙圈站點）")
    print("• 現代應用：方案 3（扁平陰影）")
    print("• 教學文檔：方案 4（圖標式）")
    print("• 創意展示：方案 5（霓虹燈管）")
    print()
    print("=" * 60)
    print()
    print("💡 提示：也可以打開 metro_style_comparison.html")
    print("   在瀏覽器中查看各風格的視覺對比")
    print()
    
    input("按 Enter 鍵退出...")
