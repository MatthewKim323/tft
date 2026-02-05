"""
Screen Capture Module for TFT State Extraction
Uses macOS screencapture for native resolution captures
"""

import time
import platform
import subprocess
import tempfile
import os
from typing import Optional, Dict, Tuple, Generator
from dataclasses import dataclass
import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not installed. Run: pip install pillow")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not installed. Run: pip install opencv-python")

from .config import GameRegions, Region, Config


@dataclass
class CapturedFrame:
    """Container for a captured frame with metadata"""
    image: np.ndarray
    timestamp: float
    region_name: str
    width: int
    height: int
    
    @property
    def shape(self) -> Tuple[int, int, int]:
        return self.image.shape
    
    def to_pil(self) -> 'Image.Image':
        """Convert to PIL Image"""
        if not PIL_AVAILABLE:
            raise ImportError("PIL not available")
        return Image.fromarray(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
    
    def to_grayscale(self) -> np.ndarray:
        """Convert to grayscale"""
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV not available")
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
    
    def save(self, path: str):
        """Save frame to file"""
        if CV2_AVAILABLE:
            cv2.imwrite(path, self.image)
        elif PIL_AVAILABLE:
            self.to_pil().save(path)


class ScreenCapture:
    """
    Screen capture using macOS screencapture for NATIVE resolution
    Captures at full 1920x1200 (or whatever your actual resolution is)
    """
    
    def __init__(self, config: Optional[Config] = None):
        if platform.system() != "Darwin":
            raise RuntimeError("This capture module is macOS only. Use mss for other platforms.")
        
        self.config = config or Config()
        self.regions = GameRegions()
        
        # Get native screen resolution using screencapture
        self._setup_monitor()
        
        # Performance tracking
        self._frame_times = []
        self._last_capture_time = 0
    
    def _setup_monitor(self):
        """Detect actual native screen resolution"""
        # Capture a test screenshot to get native dimensions
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            # screencapture -x = no sound, captures at native resolution
            subprocess.run(['screencapture', '-x', temp_path], check=True, capture_output=True)
            
            # Read to get dimensions
            img = cv2.imread(temp_path)
            if img is not None:
                self.screen_height, self.screen_width = img.shape[:2]
            else:
                # Fallback
                self.screen_width = 1920
                self.screen_height = 1200
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Update regions for NATIVE resolution
        self.regions.set_resolution(self.screen_width, self.screen_height)
        
        print(f"Screen capture initialized: {self.screen_width}x{self.screen_height} (NATIVE)")
    
    def _capture_native(self) -> np.ndarray:
        """Capture full screen at native resolution using screencapture"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        
        try:
            # screencapture -x = silent capture at native resolution
            subprocess.run(['screencapture', '-x', temp_path], check=True, capture_output=True)
            img = cv2.imread(temp_path)
            return img
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def capture_full_screen(self) -> CapturedFrame:
        """Capture the entire screen at native resolution"""
        timestamp = time.time()
        img = self._capture_native()
        
        self._last_capture_time = time.time() - timestamp
        self._frame_times.append(self._last_capture_time)
        if len(self._frame_times) > 100:
            self._frame_times.pop(0)
        
        return CapturedFrame(
            image=img,
            timestamp=timestamp,
            region_name="full",
            width=img.shape[1],
            height=img.shape[0]
        )
    
    def capture_region(self, region_name: str) -> Optional[CapturedFrame]:
        """Capture a specific named region at native resolution"""
        all_regions = self.regions.get_all_regions()
        if region_name not in all_regions:
            # Only warn once per unknown region to avoid spam
            if not hasattr(self, '_warned_regions'):
                self._warned_regions = set()
            if region_name not in self._warned_regions:
                print(f"⚠ Unknown region: {region_name} (available: {list(all_regions.keys())})")
                self._warned_regions.add(region_name)
            return None
        return self._capture_region(all_regions[region_name])
    
    def _capture_region(self, region: Region) -> CapturedFrame:
        """Capture a region by taking full screenshot and cropping"""
        timestamp = time.time()
        
        # Capture full screen at native resolution
        full_img = self._capture_native()
        
        # Crop to region (coordinates are now in native resolution)
        x, y = region.x, region.y
        w, h = region.width, region.height
        
        # Ensure we don't go out of bounds
        x = max(0, min(x, full_img.shape[1] - 1))
        y = max(0, min(y, full_img.shape[0] - 1))
        x2 = min(x + w, full_img.shape[1])
        y2 = min(y + h, full_img.shape[0])
        
        img = full_img[y:y2, x:x2]
        
        self._last_capture_time = time.time() - timestamp
        self._frame_times.append(self._last_capture_time)
        if len(self._frame_times) > 100:
            self._frame_times.pop(0)
        
        return CapturedFrame(
            image=img,
            timestamp=timestamp,
            region_name=region.name,
            width=img.shape[1],
            height=img.shape[0]
        )
    
    def capture_all_regions(self) -> Dict[str, CapturedFrame]:
        """Capture all defined regions"""
        frames = {}
        for name, region in self.regions.get_all_regions().items():
            frames[name] = self._capture_region(region)
        return frames
    
    def capture_ocr_regions(self) -> Dict[str, CapturedFrame]:
        """Capture only regions that need OCR"""
        frames = {}
        for name, region in self.regions.get_ocr_regions().items():
            frames[name] = self._capture_region(region)
        return frames
    
    def capture_yolo_regions(self) -> Dict[str, CapturedFrame]:
        """Capture only regions that need YOLO detection"""
        frames = {}
        for name, region in self.regions.get_yolo_regions().items():
            frames[name] = self._capture_region(region)
        return frames
    
    def stream_frames(self, fps: int = 10, region_name: str = "full") -> Generator[CapturedFrame, None, None]:
        """
        Generator that yields frames at specified FPS
        
        Usage:
            for frame in capture.stream_frames(fps=10):
                process(frame)
        """
        frame_interval = 1.0 / fps
        
        while True:
            start_time = time.time()
            
            if region_name == "full":
                yield self.capture_full_screen()
            else:
                frame = self.capture_region(region_name)
                if frame:
                    yield frame
            
            # Maintain target FPS
            elapsed = time.time() - start_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
    
    @property
    def avg_capture_time(self) -> float:
        """Average capture time in milliseconds"""
        if not self._frame_times:
            return 0
        return (sum(self._frame_times) / len(self._frame_times)) * 1000
    
    @property
    def estimated_fps(self) -> float:
        """Estimated achievable FPS based on capture times"""
        avg_time = self.avg_capture_time / 1000  # Convert to seconds
        if avg_time == 0:
            return 0
        return 1.0 / avg_time
    
    def draw_regions_debug(self, save_path: str = "debug_regions.png"):
        """
        Capture full screen and draw all ROI regions for debugging/calibration
        """
        frame = self.capture_full_screen()
        img = frame.image.copy()
        
        colors = {
            "gold": (0, 255, 255),      # Yellow
            "health": (0, 0, 255),       # Red
            "level": (255, 0, 0),        # Blue
            "stage": (0, 255, 0),        # Green
            "board": (255, 0, 255),      # Magenta
            "bench": (255, 128, 0),      # Orange
            "shop": (0, 255, 128),       # Cyan
            "item_inventory": (128, 0, 255),
            "augment_display": (255, 255, 0),
            "trait_panel": (128, 128, 255),
            "opponent_portraits": (255, 128, 128),
        }
        
        for name, region in self.regions.get_all_regions().items():
            color = colors.get(name, (255, 255, 255))
            x, y, x2, y2 = region.bbox
            cv2.rectangle(img, (x, y), (x2, y2), color, 2)
            cv2.putText(img, name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        cv2.imwrite(save_path, img)
        print(f"Debug regions image saved to: {save_path}")
        return save_path
    
    def calibrate_interactive(self):
        """
        Interactive calibration mode - shows live capture with regions
        Press 'q' to quit, 's' to save debug image
        """
        print("Interactive calibration mode")
        print("Press 'q' to quit, 's' to save debug image")
        
        cv2.namedWindow("TFT Regions Calibration", cv2.WINDOW_NORMAL)
        
        try:
            while True:
                frame = self.capture_full_screen()
                img = frame.image.copy()
                
                # Draw regions
                for name, region in self.regions.get_all_regions().items():
                    x, y, x2, y2 = region.bbox
                    cv2.rectangle(img, (x, y), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, name, (x, y - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Show FPS
                cv2.putText(img, f"FPS: {self.estimated_fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("TFT Regions Calibration", img)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.draw_regions_debug()
        finally:
            cv2.destroyAllWindows()
    
    def close(self):
        """Clean up resources"""
        pass  # No resources to clean up with screencapture
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Quick test function
def test_capture():
    """Test screen capture functionality"""
    print("Testing screen capture...")
    
    with ScreenCapture() as capture:
        # Test full screen capture
        frame = capture.capture_full_screen()
        print(f"Full screen: {frame.shape}, captured in {capture.avg_capture_time:.2f}ms")
        
        # Test individual regions
        for name in ["gold", "health", "board", "shop"]:
            frame = capture.capture_region(name)
            if frame:
                print(f"Region '{name}': {frame.shape}")
        
        # Save debug image
        capture.draw_regions_debug()
        
        print(f"\nEstimated max FPS: {capture.estimated_fps:.1f}")


if __name__ == "__main__":
    test_capture()
