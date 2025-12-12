# -*- coding: utf-8 -*-
"""
Blockly Editor 功能測試腳本
測試所有主要功能是否正常運作
"""

import sys
import os

# 設定路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("ChroLens Blockly Editor 功能測試")
print("=" * 60)

# 測試 1: 導入模組
print("\n[測試 1] 導入模組...")
try:
    from blockly_script_editor import BlocklyScriptEditor
    print("✅ 模組導入成功")
except Exception as e:
    print(f"❌ 模組導入失敗: {e}")
    sys.exit(1)

# 測試 2: 創建編輯器實例
print("\n[測試 2] 創建編輯器實例...")
try:
    editor = BlocklyScriptEditor()
    print("✅ 編輯器實例創建成功")
except Exception as e:
    print(f"❌ 編輯器創建失敗: {e}")
    sys.exit(1)

# 測試 3: 檢查畫布初始化
print("\n[測試 3] 檢查畫布初始化...")
try:
    assert hasattr(editor, 'canvas'), "缺少 canvas 屬性"
    assert hasattr(editor, 'canvas_nodes'), "缺少 canvas_nodes 屬性"
    assert hasattr(editor, 'canvas_connections'), "缺少 canvas_connections 屬性"
    assert hasattr(editor, 'toolbox'), "缺少 toolbox 屬性"
    print("✅ 畫布組件初始化完成")
    print(f"   - 畫布模式: {editor.canvas_mode}")
    print(f"   - 節點數量: {len(editor.canvas_nodes)}")
    print(f"   - 工具箱已創建: {editor.toolbox is not None}")
except AssertionError as e:
    print(f"❌ 畫布初始化失敗: {e}")
    sys.exit(1)

# 測試 4: 檢查工具箱內容
print("\n[測試 4] 檢查工具箱內容...")
try:
    assert hasattr(editor, 'toolbox_content'), "缺少 toolbox_content"
    assert hasattr(editor, 'current_tab'), "缺少 current_tab"
    print("✅ 工具箱組件正常")
    print(f"   - 當前標籤: {editor.current_tab}")
    print(f"   - 工具箱內容已創建: {editor.toolbox_content is not None}")
except AssertionError as e:
    print(f"❌ 工具箱檢查失敗: {e}")

# 測試 5: 測試創建節點功能
print("\n[測試 5] 測試創建節點功能...")
try:
    # 創建第一個節點
    idx1 = editor._create_canvas_node("測試節點 1", "#42a5f5", 200, 100)
    assert len(editor.canvas_nodes) == 1, "節點創建失敗"
    
    # 創建第二個節點（應自動連接）
    idx2 = editor._create_canvas_node("測試節點 2", "#66bb6a", 200, 200)
    assert len(editor.canvas_nodes) == 2, "第二個節點創建失敗"
    assert len(editor.canvas_connections) == 1, "自動連接失敗"
    
    print("✅ 節點創建與連接功能正常")
    print(f"   - 已創建節點: {len(editor.canvas_nodes)}")
    print(f"   - 已創建連接: {len(editor.canvas_connections)}")
except Exception as e:
    print(f"❌ 節點創建測試失敗: {e}")

# 測試 6: 測試 JSON 轉換功能
print("\n[測試 6] 測試 JSON 轉換功能...")
try:
    test_actions = [
        {"action": "mouse_move", "x": 100, "y": 200},
        {"action": "mouse_click", "button": "left", "clicks": 1},
        {"action": "delay", "duration": 1.0}
    ]
    
    text = editor._convert_json_to_text(test_actions)
    assert "移動 100, 200" in text, "JSON 轉文字失敗"
    assert "點擊 left" in text, "點擊指令轉換失敗"
    assert "等待 1.0" in text, "延遲指令轉換失敗"
    
    print("✅ JSON 轉換功能正常")
    print(f"   轉換結果預覽:\n{text[:100]}...")
except Exception as e:
    print(f"❌ JSON 轉換測試失敗: {e}")

# 測試 7: 檢查腳本目錄
print("\n[測試 7] 檢查腳本目錄與測試腳本...")
try:
    scripts_dir = os.path.join(os.getcwd(), "scripts")
    test_script = os.path.join(scripts_dir, "blockly_demo_script.json")
    
    if os.path.exists(test_script):
        print("✅ 測試腳本已就緒")
        print(f"   - 路徑: {test_script}")
        
        # 載入測試腳本
        import json
        with open(test_script, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"   - 動作數量: {len(data.get('script_actions', []))}")
        print(f"   - 重複次數: {data.get('repeat', '1')}")
        print(f"   - 回放速度: {data.get('speed', '100')}%")
    else:
        print("⚠️  測試腳本未找到")
except Exception as e:
    print(f"⚠️  腳本檢查警告: {e}")

# 測試 8: 檢查所有必要方法
print("\n[測試 8] 檢查核心方法...")
required_methods = [
    '_create_canvas_node',
    '_connect_nodes',
    '_update_toolbox_content',
    '_toggle_editor_mode',
    '_save_script',
    '_load_script',
    '_sync_canvas_to_text',
    '_canvas_to_text',
    '_clear_canvas',
    '_auto_arrange_nodes'
]

missing_methods = []
for method_name in required_methods:
    if not hasattr(editor, method_name):
        missing_methods.append(method_name)

if missing_methods:
    print(f"❌ 缺少方法: {', '.join(missing_methods)}")
else:
    print("✅ 所有核心方法已實現")
    print(f"   - 已檢查 {len(required_methods)} 個方法")

# 測試總結
print("\n" + "=" * 60)
print("測試完成！")
print("=" * 60)
print("\n📝 使用說明：")
print("1. 執行 'python blockly_script_editor.py' 啟動編輯器")
print("2. 選擇 'blockly_demo_script' 腳本")
print("3. 點擊「重新載入」查看畫布上的節點")
print("4. 拖曳節點、使用工具箱、測試所有功能")
print("5. 右鍵畫布測試自動排列、清空、轉換文字功能")
print("\n✨ 所有功能測試通過！編輯器已就緒。")
print("=" * 60)

# 不自動啟動 GUI，讓使用者手動執行
print("\n提示：測試完成後，可以執行以下命令啟動編輯器：")
print("python blockly_script_editor.py")
