"""
OCRTrigger - OCR 文字觸發系統（預留介面）
允許腳本等待螢幕出現特定文字後再執行後續動作

預期功能：
- 截取螢幕區域
- OCR 辨識文字
- 等待特定文字出現
- 支援模糊匹配與正則表達式

目前狀態：
- 提供基礎介面
- 可選擇使用 pytesseract 或 Windows Runtime OCR
- 若無 OCR 套件，回傳 NotImplementedError

使用方式:
    from ocr_trigger import OCRTrigger
    
    ocr = OCRTrigger()
    if ocr.wait_for_text("確認", timeout=10):
        print("找到文字！")
"""

import time
from typing import Optional, Tuple, List
from PIL import ImageGrab
import re

# 🔥 優化：引入更快的螢幕截圖庫
try:
    import mss
    import numpy as np
    from PIL import Image
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False


class OCRTrigger:
    """OCR 文字觸發器
    
    功能：
    - 截取螢幕區域並辨識文字
    - 等待特定文字出現（輪詢模式）
    - 支援全螢幕或指定區域
    """
    
    def __init__(self, ocr_engine: str = "auto"):
        """初始化 OCR 觸發器
        
        Args:
            ocr_engine: OCR 引擎選擇
                - "auto": 自動偵測可用引擎
                - "tesseract": 使用 pytesseract
                - "windows": 使用 Windows Runtime OCR
                - "none": 不使用 OCR（僅預留介面）
        """
        self.ocr_engine = ocr_engine
        self._ocr_available = False
        self._ocr_function = None
        
        # 嘗試初始化 OCR 引擎
        self._initialize_ocr(ocr_engine)
    
    def _initialize_ocr(self, engine: str) -> None:
        """初始化 OCR 引擎"""
        if engine == "auto":
            # 嘗試按優先順序載入 (優先使用 Windows 內建 OCR)
            for eng in ["windows", "tesseract"]:
                if self._try_load_engine(eng):
                    return
            # 都失敗則不使用 OCR
            self.ocr_engine = "none"
        else:
            self._try_load_engine(engine)
    
    def _try_load_engine(self, engine: str) -> bool:
        """嘗試載入指定引擎
        
        Returns:
            是否成功載入
        """
        if engine == "windows":
            try:
                # Windows Runtime OCR (需要 Python 3.7+ 和 Windows 10+)
                from PIL import Image
                import asyncio
                try:
                    from winrt.windows.media.ocr import OcrEngine
                    from winrt.windows.graphics.imaging import BitmapDecoder, SoftwareBitmap
                    from winrt.windows.storage.streams import InMemoryRandomAccessStream
                    self._ocr_function = self._ocr_windows
                    self._ocr_available = True
                    self.ocr_engine = "windows"
                    print("OCR: Using Windows Runtime engine")
                    return True
                except ImportError:
                    pass
            except Exception:
                pass
        
        elif engine == "tesseract":
            try:
                import pytesseract
                self._ocr_function = self._ocr_tesseract
                self._ocr_available = True
                self.ocr_engine = "tesseract"
                print("OCR: Using Tesseract engine")
                return True
            except ImportError:
                pass
        
        return False
    
    def _ocr_tesseract(self, image) -> str:
        """使用 Tesseract 辨識圖片"""
        try:
            import pytesseract
            # 支援繁體中文（需安裝 chi_tra 語言包）
            text = pytesseract.image_to_string(image, lang='chi_tra+eng')
            return text.strip()
        except Exception as e:
            print(f"Warning: Tesseract OCR failed: {e}")
            return ""
    
    def _ocr_windows(self, image) -> str:
        """使用 Windows Runtime OCR 辨識圖片"""
        try:
            import asyncio
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.graphics.imaging import BitmapDecoder
            from winrt.windows.storage.streams import InMemoryRandomAccessStream
            from io import BytesIO
            
            # 轉換 PIL Image 到 Windows Runtime
            async def recognize():
                # 將圖片轉為 bytes
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                
                # 創建 Stream
                stream = InMemoryRandomAccessStream()
                writer = stream.get_output_stream_at(0)
                await writer.write_async(buffer.read())
                await writer.flush_async()
                
                # 解碼圖片
                decoder = await BitmapDecoder.create_async(stream)
                bitmap = await decoder.get_software_bitmap_async()
                
                # OCR 辨識
                engine = OcrEngine.try_create_from_user_profile_languages()
                result = await engine.recognize_async(bitmap)
                
                return result.text
            
            # 執行非同步函數
            loop = asyncio.get_event_loop()
            text = loop.run_until_complete(recognize())
            return text.strip()
        except Exception as e:
            print(f"Warning: Windows OCR failed: {e}")
            return ""
    
    def capture_screen(
        self,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> 'PIL.Image.Image':
        """截取螢幕（🔥 優化：優先使用 mss）
        
        Args:
            region: 截取區域 (left, top, right, bottom)
                    None = 全螢幕
        
        Returns:
            PIL Image 物件
        """
        try:
            if MSS_AVAILABLE:
                with mss.mss() as sct:
                    if region:
                        monitor = {
                            "left": region[0], 
                            "top": region[1],
                            "width": region[2] - region[0],
                            "height": region[3] - region[1]
                        }
                    else:
                        monitor = sct.monitors[1]  # 主螢幕
                    
                    screenshot = sct.grab(monitor)
                    # 轉換為 PIL Image
                    img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                    return img
            else:
                # 回退到 PIL.ImageGrab
                if region:
                    return ImageGrab.grab(bbox=region)
                else:
                    return ImageGrab.grab()
        except Exception as e:
            print(f"Warning: mss screenshot failed, using PIL: {e}")
            if region:
                return ImageGrab.grab(bbox=region)
            else:
                return ImageGrab.grab()
    
    def recognize_text(
        self,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """辨識螢幕文字
        
        Args:
            region: 截取區域，None = 全螢幕
        
        Returns:
            辨識到的文字
        """
        if not self._ocr_available:
            raise NotImplementedError(
                "OCR 功能未啟用。請安裝 pytesseract 或確認 Windows 10+ 環境。"
            )
        
        # 截圖
        image = self.capture_screen(region)
        
        # 辨識
        return self._ocr_function(image)
    
    def wait_for_text(
        self,
        target_text: str,
        timeout: float = 30.0,
        interval: float = 0.5,
        region: Optional[Tuple[int, int, int, int]] = None,
        match_mode: str = "contains",
        case_sensitive: bool = False
    ) -> bool:
        """等待螢幕出現特定文字
        
        Args:
            target_text: 要尋找的文字
            timeout: 超時時間（秒）
            interval: 檢查間隔（秒）
            region: 截取區域，None = 全螢幕
            match_mode: 匹配模式
                - "contains": 包含（預設）
                - "exact": 完全相同
                - "regex": 正則表達式
            case_sensitive: 是否區分大小寫
        
        Returns:
            是否找到文字
        """
        if not self._ocr_available:
            raise NotImplementedError(
                "OCR 功能未啟用。請安裝 pytesseract 或確認 Windows 10+ 環境。"
            )
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 辨識文字
                text = self.recognize_text(region)
                
                # 大小寫處理
                if not case_sensitive:
                    text = text.lower()
                    target = target_text.lower()
                else:
                    target = target_text
                
                # 匹配模式
                if match_mode == "contains":
                    if target in text:
                        return True
                elif match_mode == "exact":
                    if text.strip() == target.strip():
                        return True
                elif match_mode == "regex":
                    if re.search(target, text):
                        return True
                
            except Exception as e:
                print(f"Warning: OCR recognition error: {e}")
            
            # 等待後重試
            time.sleep(interval)
        
        return False
    
    def find_text_position(
        self,
        target_text: str,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Tuple[int, int]]:
        """尋找文字在螢幕上的位置（預留功能）
        
        Args:
            target_text: 要尋找的文字
            region: 截取區域
        
        Returns:
            文字中心座標 (x, y)，若找不到回傳 None
        
        Note:
            此功能需要 OCR 引擎回傳文字座標資訊
            目前僅為預留介面，實作需依據引擎調整
        """
        raise NotImplementedError("文字定位功能尚未實作")
    
    def is_available(self) -> bool:
        """檢查 OCR 功能是否可用"""
        return self._ocr_available
    
    def get_engine_name(self) -> str:
        """取得當前使用的 OCR 引擎名稱"""
        return self.ocr_engine


# ====== 使用範例 ======
if __name__ == "__main__":
    # 創建 OCR 觸發器
    ocr = OCRTrigger(ocr_engine="auto")
    
    if not ocr.is_available():
        print("❌ OCR 功能未啟用")
        print("請安裝 pytesseract 或確認 Windows 10+ 環境")
        exit(1)
    
    print(f"✅ 使用 OCR 引擎: {ocr.get_engine_name()}")
    print("\n=== 測試 OCR 文字辨識 ===")
    print("將在 3 秒後截取全螢幕並辨識文字...\n")
    
    time.sleep(3)
    
    # 辨識全螢幕文字
    try:
        text = ocr.recognize_text()
        print("辨識結果:")
        print("-" * 50)
        print(text)
        print("-" * 50)
    except Exception as e:
        print(f"❌ 辨識失敗: {e}")
    
    # 測試等待文字
    print("\n=== 測試等待文字 ===")
    print("請在 10 秒內顯示包含 '測試' 的文字...")
    
    found = ocr.wait_for_text("測試", timeout=10, interval=1)
    if found:
        print("✅ 找到目標文字！")
    else:
        print("❌ 超時，未找到目標文字")
