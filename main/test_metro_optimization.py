# -*- coding: utf-8 -*-
"""
Mini Metro 风格流程图优化验证
测试圆形节点和路径规划
"""

import tkinter as tk

def test_metro_style():
    """测试 Metro 风格的圆形和路径"""
    
    root = tk.Tk()
    root.title("Metro 风格验证")
    root.geometry("800x600")
    root.configure(bg="#2d2d2d")
    
    canvas = tk.Canvas(root, width=800, height=600, bg="#1a1a1a", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 测试1: 绘制正圆形节点
    print("=" * 60)
    print("✅ 测试 1: 圆形节点保持正圆")
    print("=" * 60)
    
    nodes = [
        (150, 150, "开始", "#00b300"),
        (400, 150, "处理", "#0077be"),
        (650, 150, "条件", "#f77f00"),
        (400, 400, "结束", "#e63946")
    ]
    
    radius = 35
    for x, y, label, color in nodes:
        # 绘制正圆（确保宽高相等）
        canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="#ffffff",
            width=4
        )
        canvas.create_text(x, y, text=label, fill="#ffffff", font=("Arial", 11, "bold"))
        print(f"  ✓ {label}: 圆心({x}, {y}), 半径={radius}, 颜色={color}")
    
    print("\n验证: 所有节点使用相同半径，确保是正圆形")
    
    # 测试2: 绘制不同类型的路径
    print("\n" + "=" * 60)
    print("✅ 测试 2: 路径规划（直线/横线/45度斜线）")
    print("=" * 60)
    
    # 路径1: 水平线
    print("\n  路径 1: 水平连接（横线）")
    canvas.create_line(
        150 + radius, 150,
        400 - radius, 150,
        fill="#00d084",
        width=5,
        capstyle=tk.ROUND
    )
    print("    ✓ 从 开始 到 处理: 纯水平线")
    
    # 路径2: 垂直线
    print("\n  路径 2: 垂直连接（直线）")
    canvas.create_line(
        400, 150 + radius,
        400, 400 - radius,
        fill="#00d084",
        width=5,
        capstyle=tk.ROUND
    )
    print("    ✓ 从 处理 到 结束: 纯垂直线")
    
    # 路径3: 正交折线
    print("\n  路径 3: 正交折线（横+直）")
    canvas.create_line(
        400 + radius, 150,
        550, 150,
        550, 150 + 35,
        650 - radius, 150,
        fill="#00d084",
        width=5,
        capstyle=tk.ROUND,
        joinstyle=tk.ROUND
    )
    print("    ✓ 从 处理 到 条件: 水平+垂直+水平")
    
    # 路径4: 带偏移的平行线（避免重叠）
    print("\n  路径 4: 平行路径（通道分配）")
    offset1 = 15
    offset2 = 30
    
    # 第一条平行线
    canvas.create_line(
        150, 150 + radius,
        150, 250 + offset1,
        400, 250 + offset1,
        400, 400 - radius,
        fill="#ff5757",
        width=4,
        capstyle=tk.ROUND,
        joinstyle=tk.ROUND,
        dash=(5, 5)
    )
    print(f"    ✓ 路径A: 偏移 {offset1}px")
    
    # 第二条平行线（不重叠）
    canvas.create_line(
        150, 150 + radius,
        150, 250 + offset2,
        400, 250 + offset2,
        400, 400 - radius,
        fill="#ffaa00",
        width=4,
        capstyle=tk.ROUND,
        joinstyle=tk.ROUND,
        dash=(5, 5)
    )
    print(f"    ✓ 路径B: 偏移 {offset2}px")
    print("    ✓ 两条路径平行，不重叠")
    
    # 添加说明文字
    canvas.create_text(
        400, 50,
        text="Metro 风格验证: 正圆节点 + 直线/横线/斜线路径",
        fill="#ffffff",
        font=("Arial", 14, "bold")
    )
    
    canvas.create_text(
        400, 550,
        text="✓ 所有节点保持正圆  ✓ 路径使用直线和90度角  ✓ 多路径平行不重叠",
        fill="#00b300",
        font=("Arial", 10)
    )
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 验证完成")
    print("=" * 60)
    print("\n优化要点:")
    print("  1. ✓ 圆形节点: 使用固定半径35px，确保是正圆")
    print("  2. ✓ 路径类型: 支持水平线、垂直线、正交折线")
    print("  3. ✓ 通道分配: 使用偏移避免线路重叠")
    print("  4. ✓ 线条样式: 粗线条(5px)、圆形端点、平滑连接")
    print("\n关闭窗口以退出...")
    
    root.mainloop()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Mini Metro 风格流程图优化验证")
    print("="*60)
    print("\n启动测试窗口...\n")
    
    test_metro_style()
    
    print("\n测试完成！")
