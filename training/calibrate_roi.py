"""
ROI Calibration Tool for TFT Screen Capture
Click to define the TFT game window boundaries, auto-calculate all ROI offsets.

Usage:
    python training/calibrate_roi.py

Instructions:
    1. Make sure TFT is visible on screen
    2. Click the TOP-LEFT corner of the TFT game area
    3. Click the BOTTOM-RIGHT corner of the TFT game area
    4. ROIs will be automatically calculated and saved
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np

try:
    from state_extraction.capture import ScreenCapture
    CAPTURE_AVAILABLE = True
except ImportError:
    CAPTURE_AVAILABLE = False
    print("Warning: state_extraction not available")


class ROICalibrator:
    """Interactive tool to calibrate ROI positions for TFT screen capture"""
    
    # Standard TFT ROI ratios (relative to game window size)
    # Based on 2560x1664 reference resolution
    ROI_RATIOS = {
        "items": {"x": 0, "y": 0.072, "w": 0.031, "h": 0.685},      # Extended down
        "traits": {"x": 0.031, "y": 0.072, "w": 0.102, "h": 0.685}, # Extended down
        "board": {"x": 0.141, "y": 0.072, "w": 0.687, "h": 0.625},
        "players": {"x": 0.828, "y": 0.072, "w": 0.172, "h": 0.709},
        "bench": {"x": 0.141, "y": 0.673, "w": 0.594, "h": 0.132},  # Pushed up
        "shop": {"x": 0.141, "y": 0.805, "w": 0.633, "h": 0.195},   # Pushed up + extended right
        "top_hud": {"x": 0.141, "y": 0, "w": 0.687, "h": 0.072},
    }
    
    def __init__(self):
        self.clicks = []
        self.image = None
        self.window_name = "TFT ROI Calibration - Click TOP-LEFT then BOTTOM-RIGHT"
        self.calibration_file = Path(__file__).parent.parent / "roi_calibration.json"
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.clicks.append((x, y))
            print(f"Click {len(self.clicks)}: ({x}, {y})")
            
            # Draw click marker
            color = (0, 255, 0) if len(self.clicks) == 1 else (0, 0, 255)
            cv2.circle(self.image, (x, y), 10, color, -1)
            cv2.putText(self.image, f"{len(self.clicks)}", (x + 15, y + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            if len(self.clicks) == 2:
                # Draw rectangle
                cv2.rectangle(self.image, self.clicks[0], self.clicks[1], (255, 0, 0), 2)
                self.draw_roi_preview()
            
            cv2.imshow(self.window_name, self.image)
    
    def draw_roi_preview(self):
        """Draw preview of all ROIs based on clicks"""
        if len(self.clicks) < 2:
            return
        
        x1, y1 = self.clicks[0]
        x2, y2 = self.clicks[1]
        
        # Ensure correct order
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        colors = {
            "items": (255, 0, 0),      # Blue
            "traits": (0, 255, 0),      # Green
            "board": (0, 255, 255),     # Yellow
            "players": (255, 0, 255),   # Magenta
            "bench": (0, 165, 255),     # Orange
            "shop": (255, 255, 0),      # Cyan
            "top_hud": (128, 128, 255), # Pink
        }
        
        for name, ratios in self.ROI_RATIOS.items():
            rx = int(left + ratios["x"] * width)
            ry = int(top + ratios["y"] * height)
            rw = int(ratios["w"] * width)
            rh = int(ratios["h"] * height)
            
            color = colors.get(name, (255, 255, 255))
            cv2.rectangle(self.image, (rx, ry), (rx + rw, ry + rh), color, 2)
            cv2.putText(self.image, name, (rx + 5, ry + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def calculate_rois(self) -> dict:
        """Calculate absolute pixel ROIs from clicks"""
        if len(self.clicks) < 2:
            return {}
        
        x1, y1 = self.clicks[0]
        x2, y2 = self.clicks[1]
        
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        rois = {
            "game_window": {
                "x": left,
                "y": top,
                "width": width,
                "height": height
            }
        }
        
        for name, ratios in self.ROI_RATIOS.items():
            rois[name] = {
                "x": int(left + ratios["x"] * width),
                "y": int(top + ratios["y"] * height),
                "width": int(ratios["w"] * width),
                "height": int(ratios["h"] * height)
            }
        
        return rois
    
    def save_calibration(self, rois: dict):
        """Save calibration to JSON file"""
        with open(self.calibration_file, 'w') as f:
            json.dump(rois, f, indent=2)
        print(f"\n✅ Calibration saved to: {self.calibration_file}")
    
    def run(self):
        """Run the calibration tool"""
        print("\n" + "=" * 60)
        print("       TFT ROI Calibration Tool")
        print("=" * 60)
        print("\nInstructions:")
        print("  1. Make sure TFT is visible on your screen")
        print("  2. Click the TOP-LEFT corner of the game area")
        print("  3. Click the BOTTOM-RIGHT corner of the game area")
        print("  4. Press 's' to SAVE calibration")
        print("  5. Press 'r' to RESET and try again")
        print("  6. Press 'q' to QUIT")
        print("=" * 60 + "\n")
        
        # Capture screen
        if CAPTURE_AVAILABLE:
            capture = ScreenCapture()
            frame = capture.capture_full_screen()
            self.image = frame.image.copy()
            self.original = frame.image.copy()
            capture.close()
        else:
            print("Error: Cannot capture screen")
            return
        
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 800)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        cv2.imshow(self.window_name, self.image)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("Quit without saving")
                break
            elif key == ord('r'):
                # Reset
                self.clicks = []
                self.image = self.original.copy()
                cv2.imshow(self.window_name, self.image)
                print("Reset - click again")
            elif key == ord('s'):
                if len(self.clicks) >= 2:
                    rois = self.calculate_rois()
                    self.save_calibration(rois)
                    self.print_rois(rois)
                    break
                else:
                    print("Need 2 clicks before saving!")
        
        cv2.destroyAllWindows()
    
    def print_rois(self, rois: dict):
        """Print calculated ROIs"""
        print("\n" + "=" * 60)
        print("       Calculated ROIs")
        print("=" * 60)
        
        for name, roi in rois.items():
            print(f"\n{name}:")
            print(f"  x={roi['x']}, y={roi['y']}, w={roi['width']}, h={roi['height']}")
        
        print("\n" + "=" * 60)
        print("\nTo use these ROIs, update state_extraction/config.py")
        print("or load from roi_calibration.json")
        print("=" * 60)


def load_calibration(path: str = None) -> dict:
    """Load saved calibration from JSON"""
    if path is None:
        path = Path(__file__).parent.parent / "roi_calibration.json"
    
    if Path(path).exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}


def main():
    calibrator = ROICalibrator()
    calibrator.run()


if __name__ == "__main__":
    main()
