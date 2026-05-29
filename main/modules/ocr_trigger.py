# -*- coding: utf-8 -*-
"""
OCR 辨識觸發器模組
提供文字辨識、驗證碼辨識以及基於文字的自動化功能
"""

import cv2
import numpy as np
import time
import os

# 嘗試匯入 OCR 庫
OCR_ENGINE_TYPE = None
try:
    import cnocr
    OCR_ENGINE_TYPE = 'cnocr'
except ImportError:
    try:
        import ddddocr
        OCR_ENGINE_TYPE = 'ddddocr'
    except ImportError:
        try:
            import pytesseract
            OCR_ENGINE_TYPE = 'pytesseract'
        except ImportError:
            pass

class OCRTrigger:
    def __init__(self, ocr_engine="auto", logger=None):
        self.logger = logger or (lambda s: None)
        self.engine_type = OCR_ENGINE_TYPE
        self.ocr_instance = None
        
        if ocr_engine != "auto":
            self.engine_type = ocr_engine
            
        self._init_engine()

    def _init_engine(self):
        if self.engine_type == 'cnocr':
            try:
                from cnocr import CnOcr
                self.ocr_instance = CnOcr()
            except Exception as e:
                self.logger(f"[OCR] cnocr 初始化失敗: {e}")
                try:
                    import ddddocr
                    self.engine_type = 'ddddocr'
                    self.ocr_instance = ddddocr.DdddOcr(show_ad=False)
                except Exception:
                    try:
                        import pytesseract
                        self.engine_type = 'pytesseract'
                    except Exception:
                        self.engine_type = None
        elif self.engine_type == 'ddddocr':
            try:
                # 關閉 ddddocr 的日誌輸出，保持介面整潔
                self.ocr_instance = ddddocr.DdddOcr(show_ad=False)
            except Exception as e:
                self.logger(f"[OCR] ddddocr 初始化失敗: {e}")
                self.engine_type = None
        elif self.engine_type == 'pytesseract':
            # pytesseract 不需要初始化實例，但需要確保 Tesseract 已安裝
            pass

    def is_available(self):
        return self.engine_type is not None

    def get_engine_name(self):
        return self.engine_type or "None"

    def _ensure_bgr(self, img):
        """ 確保影像為 BGR 格式 (3通道) """
        if not isinstance(img, np.ndarray):
            # PIL Image 轉 numpy
            img_np = np.array(img)
            if len(img_np.shape) == 2: # L
                return cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            elif img_np.shape[2] == 3: # RGB
                return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            elif img_np.shape[2] == 4: # RGBA
                return cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
            return img_np

        if len(img.shape) == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if img.shape[2] == 4:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _ensure_gray(self, img):
        """ 確保影像為灰度格式 (1通道) """
        if not isinstance(img, np.ndarray):
            img = np.array(img)
            
        if len(img.shape) == 2:
            return img
        if img.shape[2] == 4:
            return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def recognize(self, img, is_captcha=True):
        """
        辨識圖片中的文字
        img: numpy BGR 陣列 或 PIL Image
        is_captcha: 是否為驗證碼模式
        """
        if not self.is_available() or img is None:
            return ""

        try:
            # 1. 影像預處理 - 確保為 BGR numpy 陣列
            img = self._ensure_bgr(img)

            # 如果是驗證碼且可用 ddddocr，執行多策略辨識
            if is_captcha:
                dddd_inst = None
                if self.engine_type == 'ddddocr':
                    dddd_inst = self.ocr_instance
                else:
                    try:
                        if not hasattr(self, '_dddd_fallback_instance') or self._dddd_fallback_instance is None:
                            import ddddocr
                            self._dddd_fallback_instance = ddddocr.DdddOcr(show_ad=False)
                        dddd_inst = self._dddd_fallback_instance
                    except:
                        pass
                
                if dddd_inst is not None:
                    # 【策略一】直接對原始影像進行 ddddocr
                    try:
                        _, img_encoded = cv2.imencode(".png", img)
                        res = dddd_inst.classification(img_encoded.tobytes()).strip()
                        if 3 <= len(res) <= 7:
                            return res
                    except:
                        pass

                    # 【策略二】簡單灰度化 + 兩倍放大
                    try:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        resized_gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                        _, img_encoded = cv2.imencode(".png", resized_gray)
                        res = dddd_inst.classification(img_encoded.tobytes()).strip()
                        if 3 <= len(res) <= 7:
                            return res
                    except:
                        pass

            # ----------------------------------------------------
            # 標準預處理流程 (用於非驗證碼，或當前不使用 ddddocr 時)
            # ----------------------------------------------------
            if is_captcha:
                # 針對驗證碼的去噪與強化
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                denoised = cv2.medianBlur(gray, 3)
                thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                            cv2.THRESH_BINARY_INV, 11, 2)
                kernel = np.ones((2,2), np.uint8)
                processed = cv2.dilate(thresh, kernel, iterations=1)
            else:
                processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 2. 執行辨識
            if self.engine_type == 'cnocr':
                # cnocr 支援 numpy 陣列，直接使用單行辨識
                res = self.ocr_instance.ocr_for_single_line(img)
                text = res.get('text', '').strip() if res else ''
                
                # 如果結果為空或可信度低，嘗試在灰度圖上辨識
                if not text or res.get('score', 0) < 0.2:
                    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    res_gray = self.ocr_instance.ocr_for_single_line(gray_img)
                    if res_gray and res_gray.get('score', 0) > res.get('score', 0):
                        text = res_gray.get('text', '').strip()
                        
                # 預處理中英文按鈕文字中的常見邊緣符號或括號噪點
                text = text.replace('|V', '').replace('|v', '').replace('|', '')
                text = text.replace('（', '').replace('）', '').replace('(', '').replace(')', '')
                return text.strip()

            elif self.engine_type == 'ddddocr':
                _, img_encoded = cv2.imencode(".png", processed)
                result = self.ocr_instance.classification(img_encoded.tobytes())
                return result.strip()
            
            elif self.engine_type == 'pytesseract':
                import pytesseract
                config = '--psm 7' if is_captcha else '--psm 3'
                result = pytesseract.image_to_string(processed, config=config, lang='eng+chi_sim+chi_tra')
                return result.strip()
                
        except Exception as e:
            self.logger(f"[OCR] 辨識過程中發生錯誤: {e}")
            return ""
        
        return ""

    def find_text_position(self, snapshot, target_text, match_mode="contains", region=None):
        """
        在截圖中尋找特定文字的位置
        snapshot: numpy BGR 陣列
        target_text: 目標文字
        region: 搜尋區域 (x, y, w, h)
        """
        if not self.is_available() or snapshot is None:
            return None

        try:
            if self.engine_type == 'cnocr':
                res_list = self.ocr_instance.ocr(snapshot)
                for item in res_list:
                    text = item.get('text', '').strip()
                    if not text:
                        continue
                        
                    is_match = False
                    if match_mode == "exact":
                        is_match = (text == target_text)
                    elif match_mode == "contains":
                        is_match = (target_text in text)
                        
                    if is_match:
                        pos = item.get('position')
                        if pos is not None and len(pos) == 4:
                            x_coords = [p[0] for p in pos]
                            y_coords = [p[1] for p in pos]
                            res_x = int(sum(x_coords) / 4)
                            res_y = int(sum(y_coords) / 4)
                            
                            if region:
                                res_x += region[0]
                                res_y += region[1]
                            return (res_x, res_y)

            elif self.engine_type == 'pytesseract':
                import pytesseract
                from pytesseract import Output
                
                # 預處理
                gray = self._ensure_gray(snapshot)
                
                # 取得詳細資料
                data = pytesseract.image_to_data(gray, output_type=Output.DICT, lang='eng+chi_sim+chi_tra')
                
                for i in range(len(data['text'])):
                    text = data['text'][i].strip()
                    if not text:
                        continue
                        
                    is_match = False
                    if match_mode == "exact":
                        is_match = (text == target_text)
                    elif match_mode == "contains":
                        is_match = (target_text in text)
                    
                    if is_match:
                        # 找到文字位置
                        x = data['left'][i]
                        y = data['top'][i]
                        w = data['width'][i]
                        h = data['height'][i]
                        
                        # 返回中心點
                        res_x = x + w // 2
                        res_y = y + h // 2
                        
                        # 如果有指定區域，需要偏移座標
                        if region:
                            res_x += region[0]
                            res_y += region[1]
                            
                        return (res_x, res_y)
            
            elif self.engine_type == 'ddddocr':
                # ddddocr 偵測模式：獲取所有文字區塊的座標
                # 注意：ddddocr 需建立一個帶 det=True 的實例來進行偵測
                try:
                    if not hasattr(self, '_det_instance'):
                        self._det_instance = ddddocr.DdddOcr(det=True, show_ad=False)
                    
                    # 轉換為 PIL Image 以供 ddddocr 使用 (如果需要)
                    from PIL import Image
                    if isinstance(snapshot, np.ndarray):
                        # ddddocr detection 需要 RGB 格式
                        if len(snapshot.shape) == 2:
                            pil_img = Image.fromarray(cv2.cvtColor(snapshot, cv2.COLOR_GRAY2RGB))
                        elif snapshot.shape[2] == 4:
                            pil_img = Image.fromarray(cv2.cvtColor(snapshot, cv2.COLOR_BGRA2RGB))
                        else:
                            pil_img = Image.fromarray(cv2.cvtColor(snapshot, cv2.COLOR_BGR2RGB))
                    else:
                        pil_img = snapshot
                        
                    # 1. 偵測所有可能的文字區塊
                    import io
                    img_byte_arr = io.BytesIO()
                    pil_img.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    poses = self._det_instance.detection(img_bytes)
                    
                    # 2. 遍歷區塊進行辨識，尋找目標文字
                    for box in poses:
                        x1, y1, x2, y2 = box
                        # 擷取該區塊進行 OCR
                        crop = snapshot[y1:y2, x1:x2]
                        text = self.recognize(crop, is_captcha=False).strip()
                        
                        is_match = False
                        if match_mode == "exact":
                            is_match = (text == target_text)
                        elif match_mode == "contains":
                            is_match = (target_text in text)
                            
                        if is_match:
                            res_x = (x1 + x2) // 2
                            res_y = (y1 + y2) // 2
                            
                            if region:
                                res_x += region[0]
                                res_y += region[1]
                            return (res_x, res_y)
                except Exception as det_e:
                    self.logger(f"[OCR] ddddocr 偵測失敗: {det_e}")
                    pass
                
        except Exception as e:
            self.logger(f"[OCR] 尋找文字位置失敗: {e}")
            
        return None

    def _get_image_entropy(self, img):
        """ 計算影像熵 (可用於判斷是否為嘈雜的驗證碼) """
        try:
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_norm = hist.ravel() / (hist.sum() + 1e-7)
            logs = np.log2(hist_norm + 1e-7)
            return -1 * (hist_norm * logs).sum()
        except:
            return 0

    def find_captcha_on_screen(self, snapshot):
        """
        [AI 主動搜尋] 在全螢幕中自動尋找看起來像驗證碼的區塊
        回傳: (x, y, w, h, text, crop) 或 None
        """
        if not self.is_available() or snapshot is None:
            return None
            
        try:
            # 1. 影像預處理
            gray = self._ensure_gray(snapshot)
            # 使用自適應二值化突出矩形邊界
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # 2. 尋找輪廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            candidates = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # 3. 篩選條件 (驗證碼通常是矩形)
                aspect_ratio = w / float(h) if h > 0 else 0
                # 寬度通常在 60-600 (適配 4K)，高度在 20-200，寬高比 1.5-6.0
                if 60 < w < 600 and 20 < h < 200 and 1.5 < aspect_ratio < 6.0:
                    # 擷取該區域
                    crop = snapshot[y:y+h, x:x+w]
                    
                    # 額外篩選：計算資訊熵 (Captcha 通常雜訊多，熵值較高)
                    entropy = self._get_image_entropy(crop)
                    if entropy < 3.0: # 稍微放寬門檻 (適配不同 DPI)
                        continue
                        
                    # 辨識內容
                    text = self.recognize(crop, is_captcha=True).strip()
                    
                    # 如果辨識出 3-7 個字元，且包含英數，則視為潛在驗證碼
                    if 3 <= len(text) <= 7:
                        # 儲存信心得分 (字元數 + 熵)
                        score = len(text) + entropy
                        candidates.append((x, y, w, h, text, crop, score))
            
            if not candidates:
                return None
            
            # 4. 排序：選擇信心得分最高的
            candidates.sort(key=lambda x: x[6], reverse=True)
            best = candidates[0]
            # 返回 (x, y, w, h, text, crop)
            return (best[0], best[1], best[2], best[3], best[4], best[5])
            
        except Exception as e:
            self.logger(f"[OCR] 自動搜尋驗證碼失敗: {e}")
            return None

    def wait_for_text(self, target_text, capture_func, timeout=10.0, match_mode="contains", interval=0.5):
        """
        循環檢查文字是否出現
        capture_func: 用於獲取截圖的函數
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            snapshot = capture_func()
            if snapshot is not None:
                # 如果 snapshot 是 PIL Image，轉換為 numpy 並確保為 BGR
                snapshot = self._ensure_bgr(snapshot)
                
                text = self.recognize(snapshot, is_captcha=False)
                
                is_match = False
                if match_mode == "exact":
                    is_match = (text == target_text)
                elif match_mode == "contains":
                    is_match = (target_text in text)
                
                if is_match:
                    return True
            
            time.sleep(interval)
        return False
