import tkinter as tk
import math
import os
import re
from PIL import Image, ImageTk

class EditorFlowchartMixin:
    def _parse_and_draw_workflow(self, text_content):
        try:
            from modules.command_lang import translate_script_line_to_canonical
            lines = text_content.splitlines()
            text_content = "\n".join([translate_script_line_to_canonical(line) for line in lines])
        except ImportError:
            pass
        """解析文字指令並繪製 Workflow 流程圖（PCB v11 風格）"""
        # Alias System: Expand colloquial aliases first
        text_content = self._expand_alias_commands(text_content)

        # 清空畫布
        self.workflow_canvas.delete("all")
        self.workflow_nodes = {}
        self.workflow_connections = []
        
        #  新增：PCB 風格資料結構 
        self.pcb_nodes = []  # [{x, y, width, height, name, row, col, type, tag}]
        self.pcb_connections = []  # [(from_idx, to_idx, path_type)]
        self.pcb_groups = []  # [{nodes: [...], color, name}]
        self.pcb_router = None
        
        #  v2.8.2: 重設並行區塊追蹤
        self.parallel_threads = {}  # {parallel_label: [thread_labels]}
        
        # PCB 佈局參數
        start_x = 80
        start_y = 80
        h_gap = 180  # 水平間距
        v_gap = 80   # 垂直間距（縮小以配合分叉）
        node_width = 150
        node_height = 36
        
        # 解析標籤和指令
        lines = text_content.split('\n')
        current_label = None
        label_commands = {}  # {label: [commands]}
        label_order = []  # 保持標籤順序
        
        #  v2.8.0: 追蹤區塊結構
        block_stack = []  # 追蹤區塊嵌套
        
        #  v2.8.0: 追蹤背景任務（觸發器、並行區塊等）
        background_labels = []  # 背景執行緒的標籤
        main_labels = []  # 主執行緒的標籤
        
        #  v2.8.1: 追蹤軌跡區塊和滑鼠動作
        in_trajectory = False  # 是否在軌跡區塊內
        pending_trajectory_info = ""  # 待處理的軌跡資訊
        action_counter = 0  # 動作計數器
        connection_labels = {}  # 連線標籤 {(from_label, to_label): label_text}
        last_action_label = None  # 上一個動作的標籤
        
        #  自動添加起點
        start_label = '#[起點]'
        label_commands[start_label] = []
        label_order.append(start_label)
        last_action_label = start_label
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('##'):
                continue
            
            #  v2.8.1: 識別軌跡區塊
            if line.startswith('# [軌跡]'):
                # 提取軌跡摘要資訊
                pending_trajectory_info = "軌跡"
                in_trajectory = True
                continue
            elif line == '# [軌跡開始]':
                in_trajectory = True
                continue
            elif line == '# [軌跡結束]':
                in_trajectory = False
                continue
            elif in_trajectory and line.startswith('>移動至'):
                # 跳過軌跡內的移動指令
                continue
            
            #  v2.8.1: 識別滑鼠點擊動作（在軌跡外）
            if (line.startswith('>左鍵點擊') or line.startswith('>右鍵點擊') or 
                line.startswith('>中鍵點擊') or line.startswith('>左鍵雙擊')):
                action_counter += 1
                # 提取點擊動作的簡化名稱
                if '>左鍵點擊' in line:
                    action_name = '左鍵點擊'
                elif '>右鍵點擊' in line:
                    action_name = '右鍵點擊'
                elif '>中鍵點擊' in line:
                    action_name = '中鍵點擊'
                elif '>左鍵雙擊' in line:
                    action_name = '左鍵雙擊'
                else:
                    action_name = '點擊'
                
                # 創建動作節點
                action_label = f'#[{action_name}_{action_counter}]'
                label_commands[action_label] = [line]
                label_order.append(action_label)
                
                # 記錄連線標籤（如果有待處理的軌跡）
                if last_action_label and pending_trajectory_info:
                    connection_labels[(last_action_label, action_label)] = pending_trajectory_info
                    pending_trajectory_info = ""  # 清除已使用的軌跡資訊
                
                last_action_label = action_label
                continue
            
            #  v2.8.0: 識別新的區塊結構（視為特殊標籤）
            # 並行區塊
            if line == '>並行開始':
                # 創建唯一的並行區塊標籤
                parallel_count = sum(1 for l in label_order if '[並行區塊' in l)
                block_label = f'#[並行區塊{parallel_count + 1}]' if parallel_count > 0 else '#[並行區塊]'
                label_commands[block_label] = []
                label_order.append(block_label)
                current_label = block_label
                # 追蹤此並行區塊包含的執行緒
                if not hasattr(self, 'parallel_threads'):
                    self.parallel_threads = {}  # {parallel_label: [thread_labels]}
                self.parallel_threads[block_label] = []
                block_stack.append(('parallel', block_label))
                continue
            elif line == '>並行結束':
                if block_stack and block_stack[-1][0] == 'parallel':
                    block_stack.pop()
                current_label = None
                continue
            elif line.startswith('>執行緒>'):
                thread_name = line[4:].strip()
                thread_label = f'#[執行緒:{thread_name}]'
                label_commands[thread_label] = []
                label_order.append(thread_label)
                current_label = thread_label
                # 記錄此執行緒屬於哪個並行區塊
                if block_stack and block_stack[-1][0] == 'parallel':
                    parallel_label = block_stack[-1][1]
                    self.parallel_threads[parallel_label].append(thread_label)
                continue
            elif line == '>執行緒結束':
                current_label = None
                continue
            
            # 觸發器（視為背景執行緒）
            if line.startswith('>每隔>'):
                interval = line[4:].strip()
                trigger_label = f'#[定時:{interval}]'
                label_commands[trigger_label] = []
                label_order.append(trigger_label)
                background_labels.append(trigger_label)  # 標記為背景
                current_label = trigger_label
                continue
            elif line == '>每隔結束':
                current_label = None
                continue
            elif line.startswith('>當偵測到>'):
                target = line[6:].split(',')[0].strip()
                trigger_label = f'#[監聽:{target}]'
                label_commands[trigger_label] = []
                label_order.append(trigger_label)
                background_labels.append(trigger_label)  # 標記為背景
                current_label = trigger_label
                continue
            elif line == '>當偵測結束':
                current_label = None
                continue
            elif line.startswith('>優先偵測>'):
                target = line[6:].strip()
                trigger_label = f'#[優先:{target}]'
                label_commands[trigger_label] = []
                label_order.append(trigger_label)
                current_label = trigger_label
                continue
            elif line == '>優先偵測結束':
                current_label = None
                continue
            
            # 狀態機
            if line.startswith('>狀態機>'):
                machine_name = line[5:].strip()
                sm_label = f'#[狀態機:{machine_name}]'
                label_commands[sm_label] = []
                label_order.append(sm_label)
                current_label = sm_label
                block_stack.append('state_machine')
                continue
            elif line == '>狀態機結束':
                if block_stack and block_stack[-1] == 'state_machine':
                    block_stack.pop()
                current_label = None
                continue
            elif line.startswith('>狀態>'):
                state_def = line[4:].strip()
                state_name = state_def.replace(', 初始', '').replace(',初始', '').strip()
                is_initial = '初始' in state_def
                state_label = f'#[狀態:{state_name}]{"(初始)" if is_initial else ""}'
                label_commands[state_label] = []
                label_order.append(state_label)
                current_label = state_label
                continue
            
            # 識別一般標籤（視為主執行緒）
            #  v2.8.2: 跳過 "# " 開頭的註解（如 "# 並行區塊範例"）
            if line.startswith('#') and not line.startswith('##') and not line.startswith('# [') and not line.startswith('# '):
                current_label = line
                label_commands[current_label] = []
                label_order.append(current_label)
                main_labels.append(current_label)  # 標記為主執行緒
            elif current_label:
                label_commands[current_label].append(line)
        
        #  自動添加終點
        end_label = '#[終點]'
        label_commands[end_label] = []
        label_order.append(end_label)
        
        if not label_order:
            return
        
        # 將標籤分配到行 (row) - 根據跳轉關係
        label_to_row = {}
        label_to_col = {}
        current_row = 0
        current_col = 0
        
        # 計算每個標籤的類型
        label_types = {}
        for label, commands in label_commands.items():
            #  v2.8.0: 識別特殊區塊類型
            if '[起點]' in label:
                label_types[label] = "start"
            elif '[終點]' in label:
                label_types[label] = "end"
            elif '[並行區塊]' in label:
                label_types[label] = "parallel"
            elif '[執行緒:' in label:
                label_types[label] = "thread"
            elif '[定時:' in label or '[監聽:' in label or '[優先:' in label:
                label_types[label] = "trigger"
            elif '[狀態機:' in label:
                label_types[label] = "state_machine"
            elif '[狀態:' in label:
                label_types[label] = "state"
            #  v2.8.1: 識別滑鼠動作節點
            elif '[左鍵點擊' in label or '[右鍵點擊' in label or '[中鍵點擊' in label or '[左鍵雙擊' in label:
                label_types[label] = "action"
            elif any(c.startswith('>>>') for c in commands):
                label_types[label] = "condition"
            else:
                label_types[label] = "label"
        
        # 簡單佈局：根據依賴關係排列
        # 簡單佈局：根據依賴關係與順序排列
        visited = set()
        
        def assign_position(label, row, col):
            if label in visited:
                return col
            visited.add(label)
            label_to_row[label] = row
            label_to_col[label] = col
            
            # 優先處理跳轉關係 (>># 或 >>>#)
            commands = label_commands.get(label, [])
            for cmd in commands:
                if cmd.startswith('>>#'):
                    target = '#' + cmd.split('#')[1].split(',')[0].strip()
                    if target in label_order and target not in visited:
                        assign_position(target, row, col + 1)
                elif cmd.startswith('>>>#'):
                    target = '#' + cmd.split('#')[1].split(',')[0].strip()
                    if target in label_order and target not in visited:
                        assign_position(target, row + 1, col)
            
            #  v2.8.2: 處理自動順序流 - 如果下一個標籤在腳本中緊隨其後，則向右排列
            idx = label_order.index(label) if label in label_order else -1
            if idx != -1 and idx + 1 < len(label_order):
                next_label = label_order[idx + 1]
                # 排除特殊功能標籤，讓主流程橫向發展
                if next_label not in visited and not any(kw in next_label for kw in ['[定時:', '[監聽:', '[優先:', '[終點]']):
                    assign_position(next_label, row, col + 1)
            
            return col
        
        # 從起點開始繪製
        if label_order:
            assign_position(label_order[0], 0, 0)
        
        # 填充任何脫漏的標籤
        for label in label_order:
            if label not in label_to_row:
                max_r = max(label_to_row.values()) if label_to_row else 0
                assign_position(label, max_r + 1, 0)
        
        # 將終點放置在最右側
        if end_label in label_order:
            final_col = max(label_to_col.values()) if label_to_col else 0
            label_to_row[end_label] = label_to_row.get(start_label, 0)
            label_to_col[end_label] = final_col + 1
        
        
        #  v2.8.2: 處理並行區塊的分叉佈局
        # 讓並行區塊的執行緒垂直分叉顯示
        if hasattr(self, 'parallel_threads') and self.parallel_threads:
            for parallel_label, thread_labels in self.parallel_threads.items():
                if parallel_label in label_to_row and len(thread_labels) > 0:
                    parallel_col = label_to_col.get(parallel_label, 0)
                    parallel_row = label_to_row.get(parallel_label, 0)
                    
                    # 計算執行緒的垂直分佈
                    # 執行緒從並行區塊的右側開始，垂直分叉
                    thread_start_col = parallel_col + 1
                    thread_count = len(thread_labels)
                    
                    for i, thread_label in enumerate(thread_labels):
                        if thread_label in label_to_row:
                            #  v2.8.2: 增加垂直間距，讓分叉更清晰
                            # 將執行緒均勻分布在並行區塊的上下
                            # 例如 2 個執行緒：row -1 和 +1（間距 2）
                            # 例如 3 個執行緒：row -1.5, 0, +1.5（間距 1.5）
                            spacing = 1.5  # 執行緒間距係數
                            center_offset = (thread_count - 1) / 2.0
                            offset = (i - center_offset) * spacing
                            new_row = parallel_row + offset
                            
                            label_to_row[thread_label] = new_row
                            label_to_col[thread_label] = thread_start_col
        
        # 創建 PCB 節點
        label_to_idx = {}
        for label in label_order:
            row = label_to_row.get(label, 0)
            col = label_to_col.get(label, 0)
            
            x = start_x + col * h_gap
            y = start_y + row * v_gap
            
            idx = len(self.pcb_nodes)
            label_to_idx[label] = idx
            
            # 判斷節點類型
            node_type = label_types.get(label, "label")
            
            self.pcb_nodes.append({
                "x": x, "y": y,
                "width": node_width, "height": node_height,
                "name": label, "row": row, "col": col,
                "type": node_type, "tag": f"pcb_node_{idx}",
                "commands": label_commands.get(label, []),
            })
            
            # 同時建立舊格式 (兼容)
            self.workflow_nodes[label] = {
                'x': x, 'y': y, 'level': row, 'items': [],
                'connections': 0,
            }
        
        # 解析連線
        #  v2.8.0: 首先從起點連接到所有背景任務和主執行緒第一個標籤
        start_idx = label_to_idx.get('#[起點]')
        if start_idx is not None:
            # 連接到所有背景任務
            for bg_label in background_labels:
                bg_idx = label_to_idx.get(bg_label)
                if bg_idx is not None:
                    self.pcb_connections.append((start_idx, bg_idx, "parallel"))
            
            # 連接到主執行緒第一個標籤
            if main_labels:
                first_main_idx = label_to_idx.get(main_labels[0])
                if first_main_idx is not None:
                    self.pcb_connections.append((start_idx, first_main_idx, "main"))
        
        #  v2.8.2: 並行區塊連接到其所屬執行緒（分叉連線）
        if hasattr(self, 'parallel_threads') and self.parallel_threads:
            for parallel_label, thread_labels in self.parallel_threads.items():
                parallel_idx = label_to_idx.get(parallel_label)
                if parallel_idx is not None:
                    for thread_label in thread_labels:
                        thread_idx = label_to_idx.get(thread_label)
                        if thread_idx is not None:
                            self.pcb_connections.append((parallel_idx, thread_idx, "fork"))
        
        for label, commands in label_commands.items():
            from_idx = label_to_idx.get(label)
            if from_idx is None:
                continue
            
            success_target = None
            fail_target = None
            
            for cmd in commands:
                if cmd.startswith('>>#'):
                    success_target = '#' + cmd.split('#')[1].split(',')[0].strip()
                elif cmd.startswith('>>>#'):
                    fail_target = '#' + cmd.split('#')[1].split(',')[0].strip()
            
            # 找下一個順序標籤（main 連線）
            label_idx_in_order = label_order.index(label) if label in label_order else -1
            if label_idx_in_order >= 0 and label_idx_in_order < len(label_order) - 1:
                next_label = label_order[label_idx_in_order + 1]
                next_idx = label_to_idx.get(next_label)
                
                #  v2.8.2: 跳過並行區塊到執行緒的連線（已經用 fork 處理）
                is_parallel_to_thread = False
                if hasattr(self, 'parallel_threads') and self.parallel_threads:
                    for parallel_label, thread_labels in self.parallel_threads.items():
                        if label == parallel_label and next_label in thread_labels:
                            is_parallel_to_thread = True
                            break
                        # 也跳過執行緒到下一個執行緒的連線
                        if label in thread_labels and next_label in thread_labels:
                            is_parallel_to_thread = True
                            break
                
                # 如果已經有 success/fail 跳轉，不添加 main
                if next_idx is not None and success_target != next_label and fail_target != next_label and not is_parallel_to_thread:
                    # 判斷是否為迴圈（向左回頭）
                    if self.pcb_nodes[next_idx]["col"] < self.pcb_nodes[from_idx]["col"]:
                        self.pcb_connections.append((from_idx, next_idx, "loop"))
                    else:
                        self.pcb_connections.append((from_idx, next_idx, "main"))
            
            # 添加 success 連線
            if success_target and success_target in label_to_idx:
                to_idx = label_to_idx[success_target]
                path_type = "loop" if self.pcb_nodes[to_idx]["col"] < self.pcb_nodes[from_idx]["col"] else "success"
                self.pcb_connections.append((from_idx, to_idx, path_type))
                self.workflow_connections.append((label, success_target, 'success'))
            
            # 添加 failure 連線
            if fail_target and fail_target in label_to_idx:
                to_idx = label_to_idx[fail_target]
                path_type = "loop" if self.pcb_nodes[to_idx]["col"] < self.pcb_nodes[from_idx]["col"] else "failure"
                self.pcb_connections.append((from_idx, to_idx, path_type))
                self.workflow_connections.append((label, fail_target, 'fail'))
        
        # 自動生成群組（根據類型分組）
        condition_nodes = [i for i, n in enumerate(self.pcb_nodes) if n["type"] == "condition"]
        if condition_nodes:
            self.pcb_groups.append({
                "nodes": condition_nodes,
                "color": "#8957e5",
                "name": "條件判斷區"
            })
        
        #  v2.8.1: 儲存連線標籤（用於軌跡標籤顯示）
        self.pcb_connection_labels = {}
        for (from_label, to_label), label_text in connection_labels.items():
            from_idx = label_to_idx.get(from_label)
            to_idx = label_to_idx.get(to_label)
            if from_idx is not None and to_idx is not None:
                self.pcb_connection_labels[(from_idx, to_idx)] = label_text
        
        # 繪製
        self._draw_pcb_graph()
    

    def _create_canvas_node(self, text, color, x, y, original_command=None):
        """在畫布上創建節點（n8n 工作流程圖風格）
        
        n8n 風格特點：
        - 左側圓形圖示區域
        - 右側卡片顯示標題和描述
        - 左側輸入連接點
        - 右側輸出連接點
        - 深色背景配淺色文字
        """
        node_idx = len(self.canvas_nodes)
        node_tag = f"node_{node_idx}"
        
        # === n8n 風格節點尺寸 ===
        node_width = 200
        node_height = 70
        icon_size = 40  # 圖示圓形直徑
        icon_margin = 10  # 圖示左邊距
        border_radius = 8
        
        # 判斷節點類型
        is_condition = '條件判斷' in text or '如果' in text or '辨識' in text or 'if' in text.lower()
        is_label = text.startswith('標籤:') or text.startswith('#')
        is_mouse = '移動' in text or '點擊' in text or '拖曳' in text or '滾輪' in text
        is_keyboard = text.startswith('@') or '按鍵' in text
        is_wait = '等待' in text or '延遲' in text
        is_loop = '迴圈' in text or '重複' in text
        
        # 根據類型選擇圖示顏色和符號
        if is_condition:
            icon_color = "#c586c0"  # 紫色 - 條件判斷
            icon_symbol = "?"
            border_color = "#9c27b0"
        elif is_label:
            icon_color = "#4ec9b0"  # 青綠色 - 標籤
            icon_symbol = "#"
            border_color = "#00bcd4"
        elif is_mouse:
            icon_color = "#569cd6"  # 藍色 - 滑鼠
            icon_symbol = ""
            border_color = "#2196f3"
        elif is_keyboard:
            icon_color = "#9cdcfe"  # 淺藍色 - 鍵盤
            icon_symbol = ""
            border_color = "#03a9f4"
        elif is_wait:
            icon_color = "#dcdcaa"  # 黃色 - 等待
            icon_symbol = ""
            border_color = "#ffc107"
        elif is_loop:
            icon_color = "#ce9178"  # 橘色 - 迴圈
            icon_symbol = "↻"
            border_color = "#ff9800"
        else:
            icon_color = color
            icon_symbol = "▶"
            border_color = "#666666"
        
        # === 創建節點元素 ===
        
        # 1. 陰影效果（輕微偏移）
        shadow = self.canvas.create_rectangle(
            x + 3, y + 3,
            x + node_width + 3, y + node_height + 3,
            fill="#0a0a0a",
            outline="",
            tags=("shadow", node_tag)
        )
        
        # 2. 主卡片背景（深灰色圓角矩形）
        card_bg = self._create_rounded_rectangle(
            x, y,
            x + node_width, y + node_height,
            radius=border_radius,
            fill="#2d2d30",
            outline=border_color,
            width=2,
            tags=("node", "card_bg", node_tag)
        )
        
        # 3. 左側圖示背景圓形
        icon_x = x + icon_margin + icon_size // 2
        icon_y = y + node_height // 2
        
        icon_bg = self.canvas.create_oval(
            icon_x - icon_size // 2, icon_y - icon_size // 2,
            icon_x + icon_size // 2, icon_y + icon_size // 2,
            fill=icon_color,
            outline="",
            tags=("node", "icon_bg", node_tag)
        )
        
        # 4. 圖示符號
        icon_text = self.canvas.create_text(
            icon_x, icon_y,
            text=icon_symbol,
            fill="white",
            font=font_tuple(14, "bold"),
            tags=("node", "icon_text", node_tag)
        )
        
        # 5. 標題文字（在圖示右側）
        text_x = x + icon_margin + icon_size + 12
        text_y = y + node_height // 2 - 8
        
        # 標題（主要顯示文字，限制長度）
        display_title = text[:20] + "..." if len(text) > 20 else text
        
        title_text = self.canvas.create_text(
            text_x, text_y,
            text=display_title,
            fill="white",
            font=font_tuple(10, "bold"),
            anchor="w",  # 左對齊
            tags=("node", "title_text", node_tag)
        )
        
        # 6. 副標題/描述（較小的灰色文字）
        subtitle_y = y + node_height // 2 + 10
        
        # 從原始指令提取類型描述
        if is_condition:
            subtitle = "條件判斷"
        elif is_label:
            subtitle = "標籤節點"
        elif is_mouse:
            subtitle = "滑鼠動作"
        elif is_keyboard:
            subtitle = "鍵盤輸入"
        elif is_wait:
            subtitle = "等待延遲"
        elif is_loop:
            subtitle = "迴圈控制"
        else:
            subtitle = "動作指令"
        
        subtitle_text = self.canvas.create_text(
            text_x, subtitle_y,
            text=subtitle,
            fill="#888888",
            font=font_tuple(8),
            anchor="w",
            tags=("node", "subtitle_text", node_tag)
        )
        
        # 7. 輸入連接點（左側小圓形）
        port_radius = 6
        input_port = self.canvas.create_oval(
            x - port_radius, icon_y - port_radius,
            x + port_radius, icon_y + port_radius,
            fill="#1e1e1e",
            outline=border_color,
            width=2,
            tags=("node", "input_port", node_tag)
        )
        
        # 8. 輸出連接點（右側小圓形）
        output_port = self.canvas.create_oval(
            x + node_width - port_radius, icon_y - port_radius,
            x + node_width + port_radius, icon_y + port_radius,
            fill="#1e1e1e",
            outline=border_color,
            width=2,
            tags=("node", "output_port", node_tag)
        )
        
        # 如果是條件判斷，添加第二個輸出連接點（用於失敗分支）
        output_port_2 = None
        if is_condition:
            output_port_2 = self.canvas.create_oval(
                x + node_width - port_radius, icon_y + 15 - port_radius,
                x + node_width + port_radius, icon_y + 15 + port_radius,
                fill="#1e1e1e",
                outline="#F44336",  # 紅色表示失敗分支
                width=2,
                tags=("node", "output_port_2", node_tag)
            )
        
        # 儲存節點資料
        node_data = {
            "rect": card_bg,
            "text": title_text,
            "shadow": shadow,
            "icon_bg": icon_bg,
            "icon_text": icon_text,
            "subtitle_text": subtitle_text,
            "input_port": input_port,
            "output_port": output_port,
            "output_port_2": output_port_2,
            "command": text,
            "original_command": original_command if original_command else text,
            "color": color,
            "icon_color": icon_color,
            "border_color": border_color,
            "x": x,
            "y": y,
            "width": node_width,
            "height": node_height,
            "is_condition": is_condition,
            "is_label": is_label
        }
        self.canvas_nodes.append(node_data)
        
        return node_idx
    

    def _connect_nodes(self, idx1, idx2, label=None):
        """連接兩個節點 - 使用 n8n 風格的 Bezier 曲線（左到右流向）"""
        if idx1 < 0 or idx1 >= len(self.canvas_nodes) or idx2 < 0 or idx2 >= len(self.canvas_nodes):
            return
        
        node1 = self.canvas_nodes[idx1]
        node2 = self.canvas_nodes[idx2]
        
        # 獲取節點尺寸（n8n 風格節點）
        node_width = node1.get("width", 200)
        node_height = node1.get("height", 70)
        
        # 計算起點（從節點右側中心）和終點（到節點左側中心）
        # n8n 風格是左到右流向
        x1 = node1["x"] + node_width  # 節點右側
        y1 = node1["y"] + node_height // 2  # 節點中心高度
        x2 = node2["x"]  # 節點左側
        y2 = node2["y"] + node2.get("height", 70) // 2  # 節點中心高度
        
        # 根據標籤選擇顏色
        if label == "成功" or label == "True":
            line_color = "#4CAF50"  # 綠色表示成功
            glow_color = "#81C784"
        elif label == "失敗" or label == "False":
            line_color = "#F44336"  # 紅色表示失敗
            glow_color = "#E57373"
        else:
            line_color = "#8B8B8B"  # 灰色表示普通連接（更接近 n8n 風格）
            glow_color = "#666666"
        
        # 計算連線索引（用於多輸出時的垂直偏移）
        existing_connections = [c for c in self.canvas_connections if c["from"] == idx1]
        connection_index = len(existing_connections)
        
        # 計算來自同一目標節點的連線數（用於輸入端偏移）
        incoming_connections = [c for c in self.canvas_connections if c["to"] == idx2]
        incoming_index = len(incoming_connections)
        
        # 輸出端垂直偏移（每條線間隔 15 像素）
        output_offset = (connection_index - 0.5) * 15 if connection_index > 0 else 0
        y1 += output_offset
        
        # 輸入端垂直偏移
        input_offset = (incoming_index - 0.5) * 15 if incoming_index > 0 else 0
        y2 += input_offset
        
        # === Bezier 曲線計算 ===
        # 計算水平距離和控制點偏移
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # 控制點偏移量（根據距離動態調整，創建平滑曲線）
        # 較長的距離需要更大的控制點偏移
        control_offset = max(50, min(dx * 0.4, 150))
        
        # 處理特殊情況：目標在左邊（需要繞回）
        if x2 < x1:
            # 需要先向右再繞回左邊
            control_offset = max(80, dy * 0.5 + 50)
            
            # 使用更複雜的路徑：右出 -> 下/上繞 -> 左入
            mid_y = (y1 + y2) / 2
            
            # 創建 S 形曲線的控制點
            cp1_x = x1 + control_offset
            cp1_y = y1
            cp2_x = x2 - control_offset
            cp2_y = y2
            
            # 如果垂直差距大，調整控制點
            if dy > 100:
                cp1_y = y1 + (y2 - y1) * 0.3
                cp2_y = y2 - (y2 - y1) * 0.3
        else:
            # 正常左到右流向
            cp1_x = x1 + control_offset
            cp1_y = y1
            cp2_x = x2 - control_offset
            cp2_y = y2
        
        # 使用多點近似 Bezier 曲線（tkinter 的 smooth=True 會自動平滑）
        # 計算貝塞爾曲線上的多個點
        bezier_points = []
        num_segments = 20  # 分段數量，越多越平滑
        
        for i in range(num_segments + 1):
            t = i / num_segments
            # 三次貝塞爾曲線公式
            # B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt
            
            px = mt3 * x1 + 3 * mt2 * t * cp1_x + 3 * mt * t2 * cp2_x + t3 * x2
            py = mt3 * y1 + 3 * mt2 * t * cp1_y + 3 * mt * t2 * cp2_y + t3 * y2
            
            bezier_points.extend([px, py])
        
        # 繪製發光效果（外層粗線）
        glow_line = self.canvas.create_line(
            *bezier_points,
            fill=glow_color,
            width=5,
            smooth=True,
            splinesteps=36,
            tags="connection_glow"
        )
        
        # 繪製主連接線
        line = self.canvas.create_line(
            *bezier_points,
            fill=line_color,
            width=2,
            smooth=True,
            splinesteps=36,
            tags="connection"
        )
        
        # 繪製終點箭頭（小圓形端點，n8n 風格）
        arrow_radius = 4
        arrow_end = self.canvas.create_oval(
            x2 - arrow_radius, y2 - arrow_radius,
            x2 + arrow_radius, y2 + arrow_radius,
            fill=line_color,
            outline="",
            tags="connection_arrow"
        )
        
        # 繪製起點連接點（小圓形）
        start_dot = self.canvas.create_oval(
            x1 - 3, y1 - 3,
            x1 + 3, y1 + 3,
            fill=line_color,
            outline="",
            tags="connection_start"
        )
        
        # 如果有標籤，添加帶背景的文字
        label_text = None
        label_bg = None
        if label:
            # 將標籤放在曲線中間位置
            label_x = (x1 + x2) / 2
            label_y = (y1 + y2) / 2 - 15  # 稍微往上偏移避免與線重疊
            
            # 創建標籤背景（圓角矩形效果）
            label_bg = self.canvas.create_rectangle(
                label_x - 25, label_y - 10,
                label_x + 25, label_y + 10,
                fill="#1e1e1e",
                outline=line_color,
                width=1,
                tags="connection_label_bg"
            )
            
            # 創建標籤文字
            label_text = self.canvas.create_text(
                label_x, label_y,
                text=label,
                fill=line_color,
                font=font_tuple(8, "bold"),
                tags="connection_label"
            )
        
        self.canvas_connections.append({
            "line": line,
            "glow_line": glow_line,
            "arrow_end": arrow_end,
            "start_dot": start_dot,
            "label_text": label_text,
            "label_bg": label_bg,
            "from": idx1,
            "to": idx2,
            "connection_index": connection_index,
            "bezier_points": bezier_points,
            "control_points": (cp1_x, cp1_y, cp2_x, cp2_y)
        })
        
        # 將連接線移到節點下層
        self.canvas.tag_lower("connection_label_bg")
        self.canvas.tag_lower("connection_label")
        self.canvas.tag_lower("connection_arrow")
        self.canvas.tag_lower("connection_start")
        self.canvas.tag_lower("connection")
        self.canvas.tag_lower("connection_glow")
        self.canvas.tag_lower("grid")
    

    def _draw_marker_container(self, marker_item, x, y):
        """繪製標記容器（n8n 風格）
        包含標記名和子元素，支援左到右布局
        返回: 容器高度
        """
        marker_name = marker_item['name']
        children = marker_item['children']
        
        # n8n 風格尺寸
        header_height = 35  # 標記名標題高度
        child_height = 40   # 每個子元素高度
        padding = 10        # 內邊距
        spacing = 5         # 子元素間距
        icon_size = 28      # 圖示大小
        port_radius = 6     # 連接點半徑
        
        # 計算容器尺寸
        total_child_height = len(children) * (child_height + spacing) if children else 20
        container_height = header_height + total_child_height + padding * 2
        container_width = 200
        
        # 繪製陰影
        shadow = self.canvas.create_rectangle(
            x + 3, y + 3,
            x + container_width + 3, y + container_height + 3,
            fill="#0a0a0a",
            outline="",
            tags=("shadow", "marker_shadow")
        )
        
        # 繪製容器外框（圓角矩形）
        container_rect = self._create_rounded_rectangle(
            x, y,
            x + container_width, y + container_height,
            radius=8,
            fill="#2d2d30",
            outline="#00bcd4",  # 青色邊框
            width=2,
            tags=("marker_container",)
        )
        
        # 繪製標題區域背景
        header_bg = self.canvas.create_rectangle(
            x + 2, y + 2,
            x + container_width - 2, y + header_height,
            fill="#1e1e1e",
            outline="",
            tags=("marker_header",)
        )
        
        # 繪製圖示圓形
        icon_x = x + padding + icon_size // 2
        icon_y = y + header_height // 2
        
        icon_bg = self.canvas.create_oval(
            icon_x - icon_size // 2, icon_y - icon_size // 2,
            icon_x + icon_size // 2, icon_y + icon_size // 2,
            fill="#4ec9b0",  # 青綠色
            outline="",
            tags=("marker_icon",)
        )
        
        # 繪製圖示符號
        icon_text = self.canvas.create_text(
            icon_x, icon_y,
            text="#",
            fill="white",
            font=font_tuple(12, "bold"),
            tags=("marker_icon_text",)
        )
        
        # 繪製標記名（在圖示右側）
        marker_text = self.canvas.create_text(
            x + padding + icon_size + 10,
            y + header_height // 2,
            text=marker_name,
            fill="#4ec9b0",
            font=font_tuple(10, "bold"),
            anchor="w",
            tags=("marker_name",)
        )
        
        # 繪製輸入連接點（左側）
        input_port_y = y + container_height // 2
        input_port = self.canvas.create_oval(
            x - port_radius, input_port_y - port_radius,
            x + port_radius, input_port_y + port_radius,
            fill="#1e1e1e",
            outline="#00bcd4",
            width=2,
            tags=("marker_input_port",)
        )
        
        # 繪製輸出連接點（右側）
        output_port = self.canvas.create_oval(
            x + container_width - port_radius, input_port_y - port_radius,
            x + container_width + port_radius, input_port_y + port_radius,
            fill="#1e1e1e",
            outline="#00bcd4",
            width=2,
            tags=("marker_output_port",)
        )
        
        # 儲存標記容器作為一個特殊節點
        marker_node = {
            "rect": container_rect,
            "text": marker_text,
            "shadow": shadow,
            "container_rect": container_rect,
            "header_bg": header_bg,
            "icon_bg": icon_bg,
            "icon_text": icon_text,
            "marker_text": marker_text,
            "input_port": input_port,
            "output_port": output_port,
            "command": marker_name,
            "original_command": marker_name,
            "color": "#4ec9b0",
            "x": x,
            "y": y,
            "width": container_width,
            "height": container_height,
            "is_marker": True,
            "marker_children": [],
            "child_elements": []
        }
        
        # 繪製子元素
        child_y = y + header_height + padding
        for i, child in enumerate(children):
            color = self._get_command_color(child)
            display_text = self._get_command_display_text(child)
            
            # 子元素框
            child_x = x + padding
            child_width = container_width - padding * 2
            
            child_rect = self.canvas.create_rectangle(
                child_x, child_y,
                child_x + child_width, child_y + child_height,
                fill=color,
                outline="#555555",
                width=1,
                tags=("marker_child",)
            )
            
            child_text_elem = self.canvas.create_text(
                child_x + 8,
                child_y + child_height // 2,
                text=display_text[:25] + "..." if len(display_text) > 25 else display_text,
                fill="white",
                font=font_tuple(8),
                anchor="w",
                tags=("marker_child_text",)
            )
            
            # 儲存到標記節點的子元素列表
            marker_node["marker_children"].append(child)
            marker_node["child_elements"].append({
                "rect": child_rect,
                "text": child_text_elem,
                "x": child_x,
                "y": child_y
            })
            
            child_y += child_height + spacing
        
        # 將標記節點加入節點列表
        self.canvas_nodes.append(marker_node)
        
        return container_height
    

    def _apply_syntax_highlighting(self):
        """套用語法高亮 (VS Code Dark+ 配色) - 優化版"""
        try:
            #  修正：處理所有行而非僅可見區域，確保長腳本完整著色
            # 取得整份檔案的總行數
            total_lines = int(self.text_editor.index("end-1c").split('.')[0])
            
            # 處理整份檔案
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
            
            # 定義需要高亮的模式 (Dracula 配色方案)
            
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
                (r'>執行緒>.+', 'syntax_flow'),
                (r'>執行緒結束', 'syntax_flow'),
                (r'>並行結束', 'syntax_flow'),
                # 狀態機
                (r'>狀態機>.+', 'syntax_flow'),
                (r'>狀態>.+', 'syntax_flow'),
                (r'>切換>.+', 'syntax_flow'),
                (r'>>切換>.+', 'syntax_flow'),
                (r'>>>切換>.+', 'syntax_flow'),
                (r'>狀態機結束', 'syntax_flow'),
            ]
            
            # 流程控制 (紅色) - 優先順序最高
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
                (r'自動辨識輸入驗證碼', 'syntax_ocr'),
            ]
            
            # 鍵盤操作 (淡紫色)
            patterns_keyboard = [
                (r'按下\w+', 'syntax_keyboard'),
                (r'放開\w+', 'syntax_keyboard'),
                (r'按(?![下放])\S+', 'syntax_keyboard'),  # 按但不是按下/按放
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
            
            # 圖片名稱 (黃色) - pic + 數字
            patterns_picname = [
                (r'pic\d+', 'syntax_picname'),
            ]
            
            # 時間參數 (粉紅色)
            patterns_time = [
                (r'T=\d+[smh]\d*', 'syntax_time'),
            ]
            
            # 備註 (灰色) - 優先處理
            patterns_comment = [
                (r'^# .+', 'syntax_comment'),         # 行首的 # 後接空格的備註
            ]
            
            # 標籤 (青色)
            patterns_label = [
                (r'^#b\S+', 'label_foldable'),        # 行首的 #b 標籤 (可摺疊)
                (r'^#/\S+', 'label_end'),             # 行首的 #/ 標籤 (結束標記)
                (r'^#\S+', 'syntax_label'),           # 行首的其他 # 標籤
            ]
            
            # 模組引用 (金色 - 特殊標記)
            patterns_module_ref = [
                (r'>#mod_[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),  # >#mod_a 模組引用
                (r'>>#[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),     # >>#標籤 分支跳轉
                (r'>>>#[\w\u4e00-\u9fa5]+', 'syntax_module_ref'),    # >>>#標籤 分支跳轉
            ]
            
            # 符號 (淡紫色) - 最後處理
            patterns_symbol = [
                (r'^>>>', 'syntax_symbol'),           # 行首的 >>>
                (r'^>>', 'syntax_symbol'),            # 行首的 >>
                (r'^>', 'syntax_symbol'),             # 行首的 >
                (r',', 'syntax_symbol'),              # 逗號
            ]
            
            # 按順序合併所有模式 (優先順序從高到低)
            all_patterns = (patterns_trigger + patterns_comment + patterns_flow + patterns_condition + patterns_delay + 
                          patterns_ocr + patterns_keyboard + patterns_mouse + 
                          patterns_image + patterns_picname + patterns_time + 
                          patterns_module_ref + patterns_label + patterns_symbol)
            
            # 逐行處理（調整行號以配合範圍）
            lines = content.split('\n')
            for offset, line in enumerate(lines):
                line_num = start_line + offset
                for pattern, tag in all_patterns:
                    for match in re.finditer(pattern, line):
                        start_idx = f"{line_num}.{match.start()}"
                        end_idx = f"{line_num}.{match.end()}"
                        self.text_editor.tag_add(tag, start_idx, end_idx)
            
            # 呼叫 Linter 邏輯檢查器
            self._validate_script(content)
        
        except Exception as e:
            pass


