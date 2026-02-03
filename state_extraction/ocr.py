"""
OCR Module for TFT State Extraction
Extracts text values like gold, HP, level, stage from game HUD
"""

import re
from typing import Optional, Dict, Tuple, Any
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not installed. Run: pip install opencv-python")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("Warning: EasyOCR not installed. Run: pip install easyocr")

from .capture import CapturedFrame
from .config import Config


class OCRExtractor:
    """
    OCR-based text extraction for TFT HUD elements
    Optimized for extracting numeric values from game UI
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._reader = None
        self._initialized = False
    
    def _init_reader(self):
        """Lazy initialization of EasyOCR reader (slow to load)"""
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR required. Install with: pip install easyocr")
        
        if not self._initialized:
            print("Initializing OCR engine (this may take a moment)...")
            self._reader = easyocr.Reader(
                self.config.ocr_lang,
                gpu=True,  # Use GPU if available
                verbose=False
            )
            self._initialized = True
            print("OCR engine ready")
    
    @property
    def reader(self):
        """Get OCR reader, initializing if needed"""
        if not self._initialized:
            self._init_reader()
        return self._reader
    
    def preprocess_for_ocr(self, image: np.ndarray, mode: str = "light_text") -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image: Input BGR image
            mode: "light_text" for light text on dark bg, "dark_text" for dark on light
        """
        if not CV2_AVAILABLE:
            return image
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Scale up small images for better OCR
        height, width = gray.shape
        if height < 50:
            scale = 50 / height
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        if mode == "light_text":
            # Light text on dark background (most TFT HUD elements)
            # Threshold to make text white on black
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        else:
            # Dark text on light background
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Slight blur to reduce noise
        thresh = cv2.GaussianBlur(thresh, (3, 3), 0)
        
        return thresh
    
    def extract_text(self, frame: CapturedFrame, preprocess: bool = True) -> str:
        """
        Extract text from a captured frame
        
        Args:
            frame: CapturedFrame to extract text from
            preprocess: Whether to preprocess image
        
        Returns:
            Extracted text string
        """
        image = frame.image
        
        if preprocess:
            image = self.preprocess_for_ocr(image)
        
        results = self.reader.readtext(image, detail=0)
        return ' '.join(results).strip()
    
    def extract_number(self, frame: CapturedFrame, default: int = 0) -> int:
        """Extract numeric value from frame"""
        text = self.extract_text(frame)
        # Extract digits only
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return default
    
    def extract_gold(self, frame: CapturedFrame) -> int:
        """Extract gold amount from gold region"""
        return self.extract_number(frame, default=0)
    
    def extract_health(self, frame: CapturedFrame) -> int:
        """Extract health value from health region"""
        return self.extract_number(frame, default=100)
    
    def extract_level(self, frame: CapturedFrame) -> int:
        """Extract player level from level region"""
        level = self.extract_number(frame, default=1)
        # Clamp to valid TFT levels
        return max(1, min(10, level))
    
    def extract_stage(self, frame: CapturedFrame) -> Dict[str, Any]:
        """
        Extract stage info (e.g., "3-2")
        
        Returns:
            {"current": "3-2", "phase": "combat/planning/carousel"}
        """
        text = self.extract_text(frame)
        
        # Look for stage pattern like "3-2" or "4-5"
        match = re.search(r'(\d+)-(\d+)', text)
        
        if match:
            stage_num = int(match.group(1))
            round_num = int(match.group(2))
            current = f"{stage_num}-{round_num}"
            
            # Determine phase based on round
            if round_num == 4:  # Carousel rounds
                phase = "carousel"
            elif round_num in [1, 2, 3]:  # PvE rounds
                phase = "pve" if stage_num == 1 else "combat"
            else:
                phase = "combat"
            
            return {"current": current, "phase": phase}
        
        return {"current": "1-1", "phase": "planning"}
    
    def extract_xp(self, frame: CapturedFrame) -> Dict[str, int]:
        """
        Extract XP progress (current/required)
        Note: This might need visual analysis of progress bar
        """
        text = self.extract_text(frame)
        
        # Look for pattern like "12/24" or "12 / 24"
        match = re.search(r'(\d+)\s*/\s*(\d+)', text)
        
        if match:
            return {
                "current": int(match.group(1)),
                "required": int(match.group(2))
            }
        
        # Default XP values by level
        return {"current": 0, "required": 4}
    
    def extract_all_hud(self, frames: Dict[str, CapturedFrame]) -> Dict[str, Any]:
        """
        Extract all HUD values from OCR regions
        
        Args:
            frames: Dict of captured frames from OCR regions
        
        Returns:
            Dict with gold, health, level, stage, xp
        """
        result = {
            "gold": 0,
            "health": 100,
            "level": 1,
            "stage": {"current": "1-1", "phase": "planning"},
            "xp": {"current": 0, "required": 4}
        }
        
        if "gold" in frames:
            result["gold"] = self.extract_gold(frames["gold"])
        
        if "health" in frames:
            result["health"] = self.extract_health(frames["health"])
        
        if "level" in frames:
            result["level"] = self.extract_level(frames["level"])
        
        if "stage" in frames:
            result["stage"] = self.extract_stage(frames["stage"])
        
        return result


# XP requirements by level for reference
XP_REQUIREMENTS = {
    1: 0,
    2: 2,
    3: 2,
    4: 6,
    5: 10,
    6: 20,
    7: 36,
    8: 56,
    9: 80,
    10: 0  # Max level
}


def test_ocr():
    """Test OCR extraction"""
    from .capture import ScreenCapture
    
    print("Testing OCR extraction...")
    
    with ScreenCapture() as capture:
        ocr = OCRExtractor()
        
        # Capture OCR regions
        frames = capture.capture_ocr_regions()
        
        # Extract values
        results = ocr.extract_all_hud(frames)
        
        print("\nExtracted HUD values:")
        print(f"  Gold: {results['gold']}")
        print(f"  Health: {results['health']}")
        print(f"  Level: {results['level']}")
        print(f"  Stage: {results['stage']}")


if __name__ == "__main__":
    test_ocr()
