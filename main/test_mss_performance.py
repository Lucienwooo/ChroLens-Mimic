# -*- coding: utf-8 -*-
"""
mss 性能測試腳本
比較 mss 和 PIL.ImageGrab 的截圖性能差異
"""

import time
import sys
from PIL import ImageGrab

# 測試參數
NUM_TESTS = 10

def test_pil_speed():
    """測試 PIL.ImageGrab 的速度"""
    print("Testing PIL.ImageGrab performance...")
    start = time.time()
    for i in range(NUM_TESTS):
        screenshot = ImageGrab.grab()
    end = time.time()
    avg_time = (end - start) / NUM_TESTS
    print(f"  Average time: {avg_time*1000:.2f}ms per screenshot")
    return avg_time

def test_mss_speed():
    """測試 mss 的速度（優化版：重用 mss 實例）"""
    try:
        import mss
        print("Testing mss performance...")
        start = time.time()
        with mss.mss() as sct:
            for i in range(NUM_TESTS):
                screenshot = sct.grab(sct.monitors[1])
        end = time.time()
        avg_time = (end - start) / NUM_TESTS
        print(f"  Average time: {avg_time*1000:.2f}ms per screenshot")
        return avg_time
    except ImportError:
        print("  mss not installed")
        return None

def main():
    print("=" * 60)
    print("ChroLens_Mimic - Screenshot Performance Test")
    print("=" * 60)
    print(f"Number of tests: {NUM_TESTS}\n")
    
    # 測試 PIL
    pil_time = test_pil_speed()
    
    print()
    
    # 測試 mss
    mss_time = test_mss_speed()
    
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    
    if mss_time:
        speedup = pil_time / mss_time
        print(f"PIL.ImageGrab:  {pil_time*1000:.2f}ms")
        print(f"mss:            {mss_time*1000:.2f}ms")
        print(f"\nPerformance boost: {speedup:.2f}x faster!")
        print(f"Time saved per screenshot: {(pil_time - mss_time)*1000:.2f}ms")
        
        # 估算在實際使用中的性能提升
        print("\nEstimated benefits:")
        print(f"  - 100 screenshots: save {(pil_time - mss_time)*100:.2f}s")
        print(f"  - 1000 screenshots: save {(pil_time - mss_time)*1000:.2f}s")
    else:
        print("mss library not available")
        print("Install with: pip install mss")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
