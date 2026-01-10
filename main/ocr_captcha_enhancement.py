"""
ChroLens_Mimic OCR 驗證碼辨識改進方案
針對 image-509.png 類型的噪點驗證碼
"""

# 改進方向 1: 增強預處理管道
def enhanced_captcha_preprocessing(image):
    """
    針對噪點驗證碼的增強預處理
    """
    import cv2
    import numpy as np
    
    # 1. 轉灰階
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # 2. 去噪（針對椒鹽噪點）
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # 3. 形態學操作去除小噪點
    kernel = np.ones((2,2), np.uint8)
    morph = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
    
    # 4. 自適應二值化
    binary = cv2.adaptiveThreshold(
        morph, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        blockSize=11, 
        C=2
    )
    
    # 5. 放大 2-3 倍提高辨識率
    scaled = cv2.resize(binary, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    return scaled

# 改進方向 2: 多次嘗試取最佳結果
def multi_attempt_ocr(image):
    """
    使用多種預處理方法，取最可信的結果
    """
    import pytesseract
    from PIL import Image
    
    results = []
    
    # 嘗試 1: 標準預處理
    img1 = enhanced_captcha_preprocessing(image)
    text1 = pytesseract.image_to_string(
        Image.fromarray(img1), 
        lang='eng',
        config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    ).strip()
    results.append(text1)
    
    # 嘗試 2: 反色處理
    img2 = cv2.bitwise_not(img1)
    text2 = pytesseract.image_to_string(
        Image.fromarray(img2), 
        lang='eng',
        config='--psm 7 --oem 3'
    ).strip()
    results.append(text2)
    
    # 嘗試 3: 更激進的去噪
    img3 = cv2.medianBlur(img1, 3)
    text3 = pytesseract.image_to_string(
        Image.fromarray(img3), 
        lang='eng',
        config='--psm 7'
    ).strip()
    results.append(text3)
    
    # 取最長的非空結果
    valid_results = [r for r in results if r and len(r) >= 3]
    if valid_results:
        return max(valid_results, key=len)
    return ""

# 改進方向 3: 字元分割（進階）
def segment_and_recognize(image):
    """
    將驗證碼分割成單個字元再辨識
    適用於字元間距明確的驗證碼
    """
    import cv2
    import numpy as np
    
    # 預處理
    processed = enhanced_captcha_preprocessing(image)
    
    # 尋找輪廓
    contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 按 x 座標排序（從左到右）
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])
    
    # 辨識每個字元
    chars = []
    for x, y, w, h in bounding_boxes:
        # 過濾太小的輪廓（噪點）
        if w < 5 or h < 5:
            continue
        
        # 提取單個字元
        char_img = processed[y:y+h, x:x+w]
        
        # 辨識
        text = pytesseract.image_to_string(
            Image.fromarray(char_img),
            lang='eng',
            config='--psm 10 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        ).strip()
        
        if text:
            chars.append(text)
    
    return ''.join(chars)

# 使用範例
"""
在 text_script_editor.py 的 _perform_ocr_and_show_result 方法中：

def do_ocr():
    try:
        # 使用增強的驗證碼辨識
        result_text = multi_attempt_ocr(screenshot)
        
        if not result_text:
            # 如果失敗，嘗試字元分割
            result_text = segment_and_recognize(screenshot)
        
        result_data["text"] = result_text
        dialog.after(0, lambda: update_ui(result_text or "無法辨識"))
    except Exception as e:
        dialog.after(0, lambda: update_ui(f"辨識失敗：{e}"))
"""
