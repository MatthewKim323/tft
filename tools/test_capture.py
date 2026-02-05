#!/usr/bin/env python3
"""
Quick test script for screen capture and ROI visualization
Run this to verify screen regions are calibrated correctly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_extraction.capture import ScreenCapture

def main():
    print("TFT Screen Capture Test")
    print("=" * 40)
    
    with ScreenCapture() as capture:
        print(f"Screen resolution: {capture.screen_width}x{capture.screen_height}")
        
        # Test capture speed
        print("\nTesting capture speed...")
        for _ in range(10):
            capture.capture_full_screen()
        print(f"Average capture time: {capture.avg_capture_time:.2f}ms")
        print(f"Estimated max FPS: {capture.estimated_fps:.1f}")
        
        # Save debug image with regions
        print("\nSaving debug image with ROI regions...")
        path = capture.draw_regions_debug("debug_regions.png")
        print(f"Saved to: {path}")
        
        print("\n" + "=" * 40)
        print("Check debug_regions.png to verify region positions!")
        print("If regions are wrong, adjust values in state_extraction/config.py")

if __name__ == "__main__":
    main()
