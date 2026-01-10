"""
測試驗證碼辨識 - 使用 Windows OCR（無需安裝 Tesseract）
目標：76N8
"""

import cv2
import numpy as np
from PIL import Image
import asyncio
import sys

# 載入圖片
img_path = r"c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\images\templates\image-509.png"
original = Image.open(img_path)
img_cv = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2BGR)

print("=" * 60)
print("使用 Windows OCR 辨識驗證碼")
print("=" * 60)

async def test_windows_ocr():
    """使用 Windows 10/11 內建 OCR"""
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat
        from winrt.windows.storage.streams import InMemoryRandomAccessStream
        import io
        
        # 準備圖片
        img_bytes = io.BytesIO()
        original.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # 創建 Windows Runtime 流
        stream = InMemoryRandomAccessStream()
        writer = stream.get_output_stream_at(0)
        await writer.write_async(img_bytes.read())
        await writer.flush_async()
        
        # 解碼圖片
        decoder = await BitmapDecoder.create_async(stream)
        software_bitmap = await decoder.get_software_bitmap_async()
        
        # 使用 OCR 引擎
        ocr_engine = OcrEngine.try_create_from_language(
            Windows.Globalization.Language("en-US")
        )
        
        if not ocr_engine:
            print("[✗] Windows OCR 引擎不可用")
            return None
        
        # 辨識
        result = await ocr_engine.recognize_async(software_bitmap)
        text = result.text.strip()
        
        print(f"[Windows OCR] 結果: '{text}'")
        return text
        
    except Exception as e:
        print(f"[✗] Windows OCR 失敗: {e}")
        return None

# 方法 2: 使用 EasyOCR（更準確，但需要下載模型）
def test_easyocr():
    """使用 EasyOCR（需要先安裝：pip install easyocr）"""
    try:
        import easyocr
        
        print("\n[EasyOCR] 初始化...")
        reader = easyocr.Reader(['en'], gpu=False)
        
        # 辨識
        result = reader.readtext(img_path, detail=0, allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        text = ''.join(result).strip()
        
        print(f"[EasyOCR] 結果: '{text}'")
        return text
        
    except ImportError:
        print("[✗] EasyOCR 未安裝")
        print("    安裝指令: pip install easyocr")
        return None
    except Exception as e:
        print(f"[✗] EasyOCR 失敗: {e}")
        return None

# 方法 3: 使用 PaddleOCR（推薦）
def test_paddleocr():
    """使用 PaddleOCR（需要先安裝：pip install paddleocr paddlepaddle）"""
    try:
        from paddleocr import PaddleOCR
        
        print("\n[PaddleOCR] 初始化...")
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        
        # 辨識
        result = ocr.ocr(img_path, cls=True)
        
        if result and result[0]:
            text = ''.join([line[1][0] for line in result[0]]).strip()
            confidence = sum([line[1][1] for line in result[0]]) / len(result[0])
            
            print(f"[PaddleOCR] 結果: '{text}' (信心度: {confidence:.2%})")
            return text
        else:
            print("[PaddleOCR] 無法辨識")
            return None
        
    except ImportError:
        print("[✗] PaddleOCR 未安裝")
        print("    安裝指令: pip install paddleocr paddlepaddle")
        return None
    except Exception as e:
        print(f"[✗] PaddleOCR 失敗: {e}")
        return None

# 執行測試
print("\n測試 1: Windows OCR")
print("-" * 60)
try:
    if sys.platform == 'win32' and sys.version_info >= (3, 7):
        text1 = asyncio.run(test_windows_ocr())
    else:
        print("[跳過] Windows OCR 需要 Windows 10+ 和 Python 3.7+")
        text1 = None
except Exception as e:
    print(f"[✗] 執行失敗: {e}")
    text1 = None

print("\n測試 2: EasyOCR")
print("-" * 60)
text2 = test_easyocr()

print("\n測試 3: PaddleOCR")
print("-" * 60)
text3 = test_paddleocr()

# 統計結果
print("\n" + "=" * 60)
print("結果統計")
print("=" * 60)

results = []
if text1: results.append(("Windows OCR", text1))
if text2: results.append(("EasyOCR", text2))
if text3: results.append(("PaddleOCR", text3))

if results:
    print(f"成功辨識數: {len(results)}/3")
    for method, text in results:
        print(f"  {method}: '{text}'")
    
    # 檢查正確答案
    target = "76N8"
    correct = [m for m, t in results if t == target]
    if correct:
        print(f"\n✓ 成功！{', '.join(correct)} 辨識正確")
    else:
        print(f"\n✗ 目標: '{target}'")
else:
    print("所有方法都失敗了")
    print("\n建議：")
    print("1. 安裝 PaddleOCR: pip install paddleocr paddlepaddle")
    print("2. 或安裝 EasyOCR: pip install easyocr")
