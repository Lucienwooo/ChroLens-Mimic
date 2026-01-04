# -*- coding: utf-8 -*-
"""
YOLOv8s 物件偵測模組
ChroLens-Mimic v2.8.2

提供基於 YOLOv8s 的物件偵測功能，用於自動化腳本中的物件識別。
"""

import os
import sys
import numpy as np
from typing import Optional, List, Tuple, Dict, Any

# OpenCV
try:
    import cv2
except ImportError:
    cv2 = None

# 嘗試載入 ultralytics (YOLOv8)
YOLO_AVAILABLE = False
YOLO = None

try:
    from ultralytics import YOLO as UltralyticsYOLO
    YOLO = UltralyticsYOLO
    YOLO_AVAILABLE = True
except ImportError:
    pass


class YOLODetector:
    """YOLOv8s 物件偵測器
    
    封裝 YOLOv8s 模型的載入與偵測功能，提供簡易 API 供 ChroLens-Mimic 使用。
    
    使用範例:
        detector = YOLODetector()
        detector.load_model()  # 自動下載 yolov8s.pt
        
        # 偵測螢幕上的物件
        results = detector.detect_screen()
        
        # 尋找特定物件
        pos = detector.find_object("button")
    """
    
    # 預設模型路徑
    DEFAULT_MODEL = "yolov8s.pt"
    
    # COCO 類別名稱（YOLOv8 預設）
    COCO_CLASSES = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
        "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
        "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
        "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
        "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
        "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
        "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
        "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
        "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
        "toothbrush"
    ]
    
    def __init__(self, logger=None):
        """初始化偵測器
        
        Args:
            logger: 日誌記錄函式（可選）
        """
        self.model = None
        self.model_path = None
        self.logger = logger or print
        self.is_loaded = False
        self.custom_classes = {}  # 自訂物件類別
        
    def _log(self, message: str):
        """記錄日誌"""
        if callable(self.logger):
            self.logger(f"[YOLO] {message}")
    
    @staticmethod
    def is_available() -> bool:
        """檢查 YOLO 是否可用
        
        Returns:
            bool: True 如果 ultralytics 套件已安裝
        """
        return YOLO_AVAILABLE
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """載入 YOLO 模型
        
        Args:
            model_path: 模型路徑（可選），預設使用 yolov8s.pt
            
        Returns:
            bool: 是否成功載入
        """
        if not YOLO_AVAILABLE:
            self._log("❌ ultralytics 套件未安裝，請執行: pip install ultralytics")
            return False
        
        try:
            # 使用預設或指定的模型
            self.model_path = model_path or self.DEFAULT_MODEL
            
            self._log(f"正在載入模型: {self.model_path}")
            
            # 載入模型（如果模型不存在會自動下載）
            self.model = YOLO(self.model_path)
            
            self.is_loaded = True
            self._log(f"✅ 模型載入成功: {self.model_path}")
            return True
            
        except Exception as e:
            self._log(f"❌ 模型載入失敗: {e}")
            self.is_loaded = False
            return False
    
    def detect(self, image: np.ndarray, confidence: float = 0.5, 
               classes: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """偵測圖片中的物件
        
        Args:
            image: OpenCV 格式的圖片 (BGR)
            confidence: 信心度閾值 (0-1)
            classes: 要偵測的類別 ID 列表（可選）
            
        Returns:
            List[Dict]: 偵測結果列表，每個結果包含:
                - class_id: 類別 ID
                - class_name: 類別名稱
                - confidence: 信心度
                - bbox: 邊界框 (x1, y1, x2, y2)
                - center: 中心點 (x, y)
        """
        if not self.is_loaded:
            self._log("❌ 模型尚未載入")
            return []
        
        try:
            # 執行推論
            results = self.model(image, conf=confidence, classes=classes, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                    
                for i, box in enumerate(boxes):
                    # 取得邊界框座標
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # 計算中心點
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    
                    # 取得類別和信心度
                    class_id = int(box.cls[0].cpu().numpy())
                    conf = float(box.conf[0].cpu().numpy())
                    
                    # 類別名稱
                    if class_id < len(self.COCO_CLASSES):
                        class_name = self.COCO_CLASSES[class_id]
                    else:
                        class_name = f"class_{class_id}"
                    
                    detections.append({
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": conf,
                        "bbox": (int(x1), int(y1), int(x2), int(y2)),
                        "center": (center_x, center_y)
                    })
            
            return detections
            
        except Exception as e:
            self._log(f"❌ 偵測失敗: {e}")
            return []
    
    def detect_screen(self, region: Optional[Tuple[int, int, int, int]] = None,
                     confidence: float = 0.5) -> List[Dict[str, Any]]:
        """偵測螢幕上的物件
        
        Args:
            region: 搜尋區域 (x1, y1, x2, y2)，None 表示全螢幕
            confidence: 信心度閾值
            
        Returns:
            List[Dict]: 偵測結果列表
        """
        try:
            from PIL import ImageGrab
            
            # 截取螢幕
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()
            
            # 轉換為 OpenCV 格式
            screen_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 執行偵測
            detections = self.detect(screen_cv, confidence)
            
            # 如果有指定區域，調整座標
            if region and detections:
                for det in detections:
                    x1, y1, x2, y2 = det["bbox"]
                    det["bbox"] = (x1 + region[0], y1 + region[1], 
                                   x2 + region[0], y2 + region[1])
                    cx, cy = det["center"]
                    det["center"] = (cx + region[0], cy + region[1])
            
            return detections
            
        except Exception as e:
            self._log(f"❌ 螢幕偵測失敗: {e}")
            return []
    
    def find_object(self, class_name: str, confidence: float = 0.5,
                   region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """在螢幕上尋找特定物件
        
        Args:
            class_name: 物件類別名稱（如 "person", "laptop", "cell phone"）
            confidence: 信心度閾值
            region: 搜尋區域
            
        Returns:
            (x, y) 物件中心座標，或 None
        """
        detections = self.detect_screen(region, confidence)
        
        # 尋找匹配的物件
        for det in detections:
            if det["class_name"].lower() == class_name.lower():
                self._log(f"✅ 找到 '{class_name}' 於 {det['center']} (信心度: {det['confidence']:.2f})")
                return det["center"]
        
        self._log(f"❌ 未找到 '{class_name}'")
        return None
    
    def find_all_objects(self, class_name: str, confidence: float = 0.5,
                        region: Optional[Tuple[int, int, int, int]] = None) -> List[Dict[str, Any]]:
        """在螢幕上尋找所有指定類別的物件
        
        Args:
            class_name: 物件類別名稱
            confidence: 信心度閾值
            region: 搜尋區域
            
        Returns:
            List[Dict]: 所有匹配物件的偵測結果
        """
        detections = self.detect_screen(region, confidence)
        
        matching = [det for det in detections 
                   if det["class_name"].lower() == class_name.lower()]
        
        self._log(f"找到 {len(matching)} 個 '{class_name}'")
        return matching
    
    def get_available_classes(self) -> List[str]:
        """取得可偵測的類別列表
        
        Returns:
            List[str]: COCO 類別名稱列表
        """
        return self.COCO_CLASSES.copy()
    
    def train_custom_model(self, data_yaml: str, epochs: int = 100, 
                          imgsz: int = 640) -> Optional[str]:
        """訓練自訂模型（進階功能）
        
        Args:
            data_yaml: 資料集配置 YAML 路徑
            epochs: 訓練週期數
            imgsz: 圖片大小
            
        Returns:
            str: 訓練後的模型路徑，或 None
        """
        if not self.is_loaded:
            self._log("❌ 請先載入基礎模型")
            return None
        
        try:
            self._log(f"開始訓練自訂模型 (epochs={epochs})")
            
            results = self.model.train(data=data_yaml, epochs=epochs, imgsz=imgsz)
            
            # 取得最佳權重路徑
            best_path = results.save_dir / "weights" / "best.pt"
            if os.path.exists(best_path):
                self._log(f"✅ 訓練完成，模型儲存於: {best_path}")
                return str(best_path)
            
            return None
            
        except Exception as e:
            self._log(f"❌ 訓練失敗: {e}")
            return None


# 全域偵測器實例（延遲初始化）
_detector_instance: Optional[YOLODetector] = None


def get_detector(logger=None) -> YOLODetector:
    """取得全域 YOLO 偵測器實例
    
    Args:
        logger: 日誌記錄函式
        
    Returns:
        YOLODetector: 偵測器實例
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YOLODetector(logger=logger)
    return _detector_instance


# 便捷函式
def detect_objects_on_screen(confidence: float = 0.5, 
                            region: Optional[Tuple[int, int, int, int]] = None,
                            auto_load: bool = True) -> List[Dict[str, Any]]:
    """快速偵測螢幕上的物件
    
    Args:
        confidence: 信心度閾值
        region: 搜尋區域
        auto_load: 是否自動載入模型
        
    Returns:
        List[Dict]: 偵測結果
    """
    detector = get_detector()
    
    if not detector.is_loaded and auto_load:
        if not detector.load_model():
            return []
    
    return detector.detect_screen(region, confidence)


def find_object_on_screen(class_name: str, confidence: float = 0.5,
                         region: Optional[Tuple[int, int, int, int]] = None,
                         auto_load: bool = True) -> Optional[Tuple[int, int]]:
    """快速在螢幕上尋找特定物件
    
    Args:
        class_name: 物件類別名稱
        confidence: 信心度閾值
        region: 搜尋區域
        auto_load: 是否自動載入模型
        
    Returns:
        (x, y) 或 None
    """
    detector = get_detector()
    
    if not detector.is_loaded and auto_load:
        if not detector.load_model():
            return None
    
    return detector.find_object(class_name, confidence, region)
