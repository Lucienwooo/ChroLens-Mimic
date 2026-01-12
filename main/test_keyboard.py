# -*- coding: utf-8 -*-
"""
按鍵功能測試腳本 - ChroLens_Mimic
用於測試所有按鍵的錄製和執行功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from keyboard_handler import KeyboardHandler
import time


def print_section(title):
    """打印區塊標題"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_key_normalization():
    """測試按鍵名稱標準化"""
    print_section("測試 1: 按鍵名稱標準化")
    
    handler = KeyboardHandler(logger=print)
    
    test_cases = [
        ('alt_l', 'alt'),
        ('alt_r', 'alt'),
        ('left alt', 'alt'),
        ('ctrl_l', 'ctrl'),
        ('control', 'ctrl'),
        ('shift_r', 'shift'),
        ('return', 'enter'),
        ('escape', 'esc'),
        ('F1', 'f1'),
        ('a', 'a'),
    ]
    
    passed = 0
    failed = 0
    
    for input_key, expected in test_cases:
        result = handler.normalize_key_name(input_key)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{input_key}' → '{result}' (期望: '{expected}')")
    
    print(f"\n結果: {passed} 通過, {failed} 失敗")
    return failed == 0


def test_modifier_detection():
    """測試修飾鍵偵測"""
    print_section("測試 2: 修飾鍵偵測")
    
    handler = KeyboardHandler(logger=print)
    
    test_cases = [
        ('alt', True),
        ('ctrl', True),
        ('shift', True),
        ('win', True),
        ('a', False),
        ('f1', False),
        ('enter', False),
    ]
    
    passed = 0
    failed = 0
    
    for key, expected in test_cases:
        result = handler.is_modifier_key(key)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{key}' 是修飾鍵: {result} (期望: {expected})")
    
    print(f"\n結果: {passed} 通過, {failed} 失敗")
    return failed == 0


def test_key_press_release():
    """測試按鍵按下和釋放記錄"""
    print_section("測試 3: 按鍵按下/釋放記錄")
    
    handler = KeyboardHandler(logger=print)
    
    # 測試單一按鍵
    print("\n[測試] 單一按鍵 'a'")
    event1 = handler.record_key_press('a')
    print(f"  按下事件: {event1['name']}, 時間: {event1['time']:.3f}")
    
    time.sleep(0.1)
    
    event2 = handler.record_key_release('a')
    print(f"  釋放事件: {event2['name']}, 持續: {event2['duration']:.3f}s")
    
    # 測試組合鍵
    print("\n[測試] 組合鍵 Alt+F")
    event3 = handler.record_key_press('alt')
    print(f"  按下 Alt: {event3['pressed_keys']}")
    
    event4 = handler.record_key_press('f')
    print(f"  按下 F: {event4['pressed_keys']}")
    
    event5 = handler.record_key_release('f')
    print(f"  釋放 F")
    
    event6 = handler.record_key_release('alt')
    print(f"  釋放 Alt")
    
    # 檢查狀態
    pressed = handler.get_pressed_keys()
    print(f"\n當前按下的鍵: {pressed}")
    
    if len(pressed) == 0:
        print("✓ 所有按鍵已正確釋放")
        return True
    else:
        print(f"✗ 仍有按鍵未釋放: {pressed}")
        return False


def test_key_sequence_validation():
    """測試按鍵序列驗證"""
    print_section("測試 4: 按鍵序列驗證")
    
    handler = KeyboardHandler(logger=print)
    
    # 正確的序列
    print("\n[測試] 正確的按鍵序列")
    correct_events = [
        {'type': 'keyboard', 'event': 'down', 'name': 'a'},
        {'type': 'keyboard', 'event': 'up', 'name': 'a'},
        {'type': 'keyboard', 'event': 'down', 'name': 'alt'},
        {'type': 'keyboard', 'event': 'down', 'name': 'f'},
        {'type': 'keyboard', 'event': 'up', 'name': 'f'},
        {'type': 'keyboard', 'event': 'up', 'name': 'alt'},
    ]
    
    issues = handler.validate_key_sequence(correct_events)
    if not issues:
        print("✓ 序列正確，沒有問題")
    else:
        print(f"✗ 發現問題: {issues}")
    
    # 不正確的序列（缺少釋放）
    print("\n[測試] 不正確的按鍵序列（缺少釋放）")
    incorrect_events = [
        {'type': 'keyboard', 'event': 'down', 'name': 'alt'},
        {'type': 'keyboard', 'event': 'down', 'name': 'f'},
        {'type': 'keyboard', 'event': 'up', 'name': 'f'},
        # 缺少 alt 的釋放
    ]
    
    issues = handler.validate_key_sequence(incorrect_events)
    if issues:
        print(f"✓ 正確偵測到問題: {issues}")
        return True
    else:
        print("✗ 未能偵測到問題")
        return False


def test_release_all():
    """測試釋放所有按鍵"""
    print_section("測試 5: 釋放所有按鍵")
    
    handler = KeyboardHandler(logger=print)
    
    # 模擬按下多個鍵
    print("\n[模擬] 按下多個鍵")
    handler.record_key_press('alt')
    handler.record_key_press('ctrl')
    handler.record_key_press('a')
    
    pressed = handler.get_pressed_keys()
    print(f"當前按下: {pressed}")
    
    # 釋放所有鍵
    print("\n[執行] 釋放所有按鍵")
    handler.release_all_keys()
    
    pressed_after = handler.get_pressed_keys()
    print(f"釋放後: {pressed_after}")
    
    if len(pressed_after) == 0:
        print("✓ 所有按鍵已釋放")
        return True
    else:
        print(f"✗ 仍有按鍵未釋放: {pressed_after}")
        return False


def run_all_tests():
    """執行所有測試"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  ChroLens-Mimic 按鍵功能測試套件".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    tests = [
        ("按鍵名稱標準化", test_key_normalization),
        ("修飾鍵偵測", test_modifier_detection),
        ("按鍵按下/釋放記錄", test_key_press_release),
        ("按鍵序列驗證", test_key_sequence_validation),
        ("釋放所有按鍵", test_release_all),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 測試 '{name}' 發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 總結
    print_section("測試總結")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{status}: {name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗")
    
    return passed == total


if __name__ == "__main__":
    print("\n按鍵功能測試腳本")
    print("此腳本會測試按鍵處理的各項功能")
    print("\n注意: 此測試不會實際按下鍵盤按鍵，只測試邏輯")
    print("若要測試實際按鍵執行，請使用 ChroLens_Mimic 主程式\n")
    
    input("按 Enter 開始測試...")
    
    success = run_all_tests()
    
    print("\n" + "="*60)
    input("\n測試完成，按 Enter 退出...")
    
    sys.exit(0 if success else 1)
