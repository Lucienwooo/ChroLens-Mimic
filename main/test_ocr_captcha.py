"""
測試不同 OCR 方法辨識 image-509.png 驗證碼
目標：76N8
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract

# 載入圖片
img_path = r"c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\images\templates\image-509.png"
original = Image.open(img_path)
img_cv = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2BGR)

print("=" * 60)
print("測試不同 OCR 預處理方法")
print("=" * 60)

# 方法 1: 基礎灰階 + 二值化
print("\n[方法 1] 基礎灰階 + Otsu 二值化")
gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
text1 = pytesseract.image_to_string(
    Image.fromarray(binary), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text1}'")

# 方法 2: 去噪 + 二值化
print("\n[方法 2] 去噪 + 二值化")
denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
_, binary2 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
text2 = pytesseract.image_to_string(
    Image.fromarray(binary2), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text2}'")

# 方法 3: 自適應二值化
print("\n[方法 3] 自適應二值化")
adaptive = cv2.adaptiveThreshold(
    gray, 255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    blockSize=11, 
    C=2
)
text3 = pytesseract.image_to_string(
    Image.fromarray(adaptive), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text3}'")

# 方法 4: 形態學去噪 + 二值化
print("\n[方法 4] 形態學去噪 + 二值化")
kernel = np.ones((2,2), np.uint8)
morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
_, binary4 = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
text4 = pytesseract.image_to_string(
    Image.fromarray(binary4), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text4}'")

# 方法 5: 放大 3 倍 + 去噪 + 二值化
print("\n[方法 5] 放大 3 倍 + 去噪 + 二值化")
scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
denoised_scaled = cv2.fastNlMeansDenoising(scaled, None, h=10, templateWindowSize=7, searchWindowSize=21)
_, binary5 = cv2.threshold(denoised_scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
text5 = pytesseract.image_to_string(
    Image.fromarray(binary5), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text5}'")

# 方法 6: 反色處理
print("\n[方法 6] 反色 + 二值化")
inverted = cv2.bitwise_not(gray)
_, binary6 = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
text6 = pytesseract.image_to_string(
    Image.fromarray(binary6), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text6}'")

# 方法 7: 中值濾波去噪
print("\n[方法 7] 中值濾波 + 二值化")
median = cv2.medianBlur(gray, 3)
_, binary7 = cv2.threshold(median, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
text7 = pytesseract.image_to_string(
    Image.fromarray(binary7), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text7}'")

# 方法 8: 嘗試不同 PSM 模式
print("\n[方法 8] PSM 6 (單一文字區塊)")
text8 = pytesseract.image_to_string(
    Image.fromarray(binary2), 
    lang='eng',
    config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text8}'")

# 方法 9: PSM 8 (單字)
print("\n[方法 9] PSM 8 (單字)")
text9 = pytesseract.image_to_string(
    Image.fromarray(binary2), 
    lang='eng',
    config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text9}'")

# 方法 10: 組合最佳方法
print("\n[方法 10] 組合：放大 4 倍 + 強力去噪 + 自適應二值化")
scaled4x = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
denoised_strong = cv2.fastNlMeansDenoising(scaled4x, None, h=15, templateWindowSize=7, searchWindowSize=21)
adaptive_scaled = cv2.adaptiveThreshold(
    denoised_strong, 255, 
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 
    blockSize=15, 
    C=3
)
text10 = pytesseract.image_to_string(
    Image.fromarray(adaptive_scaled), 
    lang='eng',
    config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
).strip()
print(f"結果: '{text10}'")

# 統計結果
print("\n" + "=" * 60)
print("結果統計")
print("=" * 60)
results = [text1, text2, text3, text4, text5, text6, text7, text8, text9, text10]
valid_results = [r for r in results if r]
print(f"有效結果數: {len(valid_results)}/{len(results)}")
print(f"所有結果: {valid_results}")

# 檢查是否有正確答案
target = "76N8"
correct = [r for r in valid_results if r == target]
if correct:
    print(f"\n✓ 成功辨識！找到 {len(correct)} 個正確結果")
else:
    print(f"\n✗ 未能正確辨識，目標是 '{target}'")
    # 顯示最接近的結果
    if valid_results:
        from difflib import SequenceMatcher
        similarities = [(r, SequenceMatcher(None, r, target).ratio()) for r in valid_results]
        similarities.sort(key=lambda x: x[1], reverse=True)
        print(f"最接近的結果: '{similarities[0][0]}' (相似度: {similarities[0][1]:.2%})")
