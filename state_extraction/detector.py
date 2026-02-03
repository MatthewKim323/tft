"""
YOLO Detector Module for TFT State Extraction
Detects champions, items, and star levels on the game board
"""

import os
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Run: pip install ultralytics")

from .capture import CapturedFrame
from .config import Config, BOARD_HEXES, BENCH_SLOTS, SHOP_SLOTS


@dataclass
class Detection:
    """Single detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


@dataclass
class BoardUnit:
    """A unit on the board or bench"""
    champion: str
    star_level: int
    items: List[str]
    position: Tuple[int, int]  # (row, col) for board, (slot,) for bench
    confidence: float


class YOLODetector:
    """
    YOLO-based object detection for TFT game elements
    Detects: Champions, Items, Star indicators, Traits
    """
    
    # Class mappings (will be populated from trained model)
    CHAMPION_CLASSES = []  # Loaded from tft_data.json
    ITEM_CLASSES = []
    TRAIT_CLASSES = []
    
    def __init__(self, config: Optional[Config] = None, model_path: Optional[str] = None):
        self.config = config or Config()
        self.model_path = model_path or self.config.yolo_model_path
        self._model = None
        self._initialized = False
        
        # Load TFT data for class names
        self._load_tft_data()
    
    def _load_tft_data(self):
        """Load champion/item names from tft_data.json"""
        import json
        
        tft_data_path = self.config.tft_data_path
        if os.path.exists(tft_data_path):
            with open(tft_data_path, 'r') as f:
                data = json.load(f)
            
            # Extract champion names
            if 'champions' in data:
                self.CHAMPION_CLASSES = [c.get('name', c.get('apiName', '')) 
                                        for c in data['champions']]
            
            # Extract item names
            if 'items' in data:
                self.ITEM_CLASSES = [i.get('name', i.get('apiName', '')) 
                                    for i in data['items']]
            
            print(f"Loaded {len(self.CHAMPION_CLASSES)} champions, {len(self.ITEM_CLASSES)} items")
    
    def _init_model(self):
        """Initialize YOLO model"""
        if not YOLO_AVAILABLE:
            raise ImportError("ultralytics required. Install with: pip install ultralytics")
        
        if not self._initialized:
            if os.path.exists(self.model_path):
                print(f"Loading YOLO model from {self.model_path}...")
                self._model = YOLO(self.model_path)
            else:
                print(f"Model not found at {self.model_path}")
                print("Using pretrained YOLOv8n as placeholder...")
                self._model = YOLO('yolov8n.pt')
            
            self._initialized = True
            print("YOLO detector ready")
    
    @property
    def model(self):
        """Get YOLO model, initializing if needed"""
        if not self._initialized:
            self._init_model()
        return self._model
    
    def detect(self, frame: CapturedFrame) -> List[Detection]:
        """
        Run detection on a frame
        
        Args:
            frame: CapturedFrame to detect objects in
        
        Returns:
            List of Detection objects
        """
        results = self.model(
            frame.image,
            conf=self.config.yolo_confidence_threshold,
            iou=self.config.yolo_iou_threshold,
            verbose=False
        )
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                detections.append(Detection(
                    class_name=cls_name,
                    confidence=conf,
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                    center=(center_x, center_y)
                ))
        
        return detections
    
    def detect_board(self, frame: CapturedFrame) -> List[BoardUnit]:
        """
        Detect units on the game board
        Maps detections to hex positions
        """
        detections = self.detect(frame)
        units = []
        
        for det in detections:
            # Skip non-champion detections
            if det.class_name not in self.CHAMPION_CLASSES:
                continue
            
            # Find closest hex position
            position = self._find_closest_hex(det.center)
            
            # Detect star level (would need separate detection)
            star_level = 1  # Default, needs actual detection
            
            units.append(BoardUnit(
                champion=det.class_name,
                star_level=star_level,
                items=[],  # Would need item detection
                position=position,
                confidence=det.confidence
            ))
        
        return units
    
    def detect_bench(self, frame: CapturedFrame) -> List[BoardUnit]:
        """Detect units on the bench"""
        detections = self.detect(frame)
        units = []
        
        for det in detections:
            if det.class_name not in self.CHAMPION_CLASSES:
                continue
            
            slot = self._find_closest_bench_slot(det.center)
            
            units.append(BoardUnit(
                champion=det.class_name,
                star_level=1,
                items=[],
                position=(slot,),
                confidence=det.confidence
            ))
        
        return units
    
    def detect_shop(self, frame: CapturedFrame) -> List[Dict[str, Any]]:
        """Detect champions in shop"""
        detections = self.detect(frame)
        shop_units = []
        
        for det in detections:
            if det.class_name not in self.CHAMPION_CLASSES:
                continue
            
            slot = self._find_closest_shop_slot(det.center)
            
            shop_units.append({
                "slot": slot,
                "champion": det.class_name,
                "cost": self._get_champion_cost(det.class_name),
                "confidence": det.confidence
            })
        
        return shop_units
    
    def detect_items(self, frame: CapturedFrame) -> List[str]:
        """Detect items in item inventory"""
        detections = self.detect(frame)
        items = []
        
        for det in detections:
            if det.class_name in self.ITEM_CLASSES:
                items.append(det.class_name)
        
        return items
    
    def _find_closest_hex(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """Find the closest hex position to a point"""
        min_dist = float('inf')
        closest = (0, 0)
        
        for pos, coords in BOARD_HEXES.items():
            dist = ((point[0] - coords[0]) ** 2 + (point[1] - coords[1]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = pos
        
        return closest
    
    def _find_closest_bench_slot(self, point: Tuple[int, int]) -> int:
        """Find the closest bench slot to a point"""
        min_dist = float('inf')
        closest = 0
        
        for slot, coords in BENCH_SLOTS.items():
            dist = ((point[0] - coords[0]) ** 2 + (point[1] - coords[1]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = slot
        
        return closest
    
    def _find_closest_shop_slot(self, point: Tuple[int, int]) -> int:
        """Find the closest shop slot to a point"""
        min_dist = float('inf')
        closest = 0
        
        for slot, coords in SHOP_SLOTS.items():
            dist = ((point[0] - coords[0]) ** 2 + (point[1] - coords[1]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest = slot
        
        return closest
    
    def _get_champion_cost(self, champion_name: str) -> int:
        """Get champion cost from TFT data"""
        # Would look up from tft_data.json
        # Default to 1 cost
        return 1
    
    def draw_detections(self, frame: CapturedFrame, detections: List[Detection]) -> np.ndarray:
        """Draw detection boxes on frame for debugging"""
        img = frame.image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = (0, 255, 0)  # Green
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(img, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return img


def test_detector():
    """Test YOLO detection"""
    from .capture import ScreenCapture
    
    print("Testing YOLO detector...")
    
    with ScreenCapture() as capture:
        detector = YOLODetector()
        
        # Capture board region
        frame = capture.capture_region("board")
        if frame:
            detections = detector.detect(frame)
            print(f"\nDetected {len(detections)} objects on board:")
            for det in detections:
                print(f"  {det.class_name}: {det.confidence:.2f} at {det.center}")


if __name__ == "__main__":
    test_detector()
