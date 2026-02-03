"""
Training Data Capture Tool for TFT YOLO Model
Captures screenshots during gameplay for annotation

Global hotkeys work even when TFT is focused:
  \   - Capture all regions
  ]   - Capture full screen only (augments, carousel, etc.)
  F10 - Capture board only
  F11 - Toggle auto-capture
  F12 - Quit
"""

import os
import time
import sys
import threading
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available. Preview disabled.")

try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("pynput not available. Install with: pip install pynput")

from state_extraction.capture import ScreenCapture
from state_extraction.config import Config


class TrainingDataCapture:
    """
    Captures screenshots for YOLO training data
    
    Usage:
        1. Run this script while playing TFT
        2. Press 'c' to capture current frame
        3. Press 'a' to enable auto-capture mode
        4. Press 'q' to quit
    """
    
    def __init__(self, output_dir: str = None):
        # Default to screenshots folder inside project
        if output_dir is None:
            project_root = Path(__file__).parent.parent
            output_dir = project_root / "screenshots"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for different regions
        self.dirs = {
            "full": self.output_dir / "full",
            "board": self.output_dir / "board",
            "bench": self.output_dir / "bench",
            "shop": self.output_dir / "shop",
            "items": self.output_dir / "items",
            "players": self.output_dir / "players",
        }
        for d in self.dirs.values():
            d.mkdir(exist_ok=True)
        
        self.capture = ScreenCapture()
        self.capture_count = 0
        self.auto_capture = False
        self.auto_interval = 2.0  # seconds between auto captures
    
    def capture_frame(self, regions: list = None):
        """
        Capture and save frame(s)
        
        Args:
            regions: List of region names to capture, or None for all
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        regions = regions or ["full", "board", "bench", "shop", "items", "players"]
        
        saved_files = []
        for region_name in regions:
            if region_name == "full":
                frame = self.capture.capture_full_screen()
            elif region_name == "items":
                frame = self.capture.capture_region("item_inventory")
            elif region_name == "players":
                frame = self.capture.capture_region("opponent_portraits")
            else:
                frame = self.capture.capture_region(region_name)
            
            if frame:
                filename = f"{timestamp}_{region_name}.png"
                filepath = self.dirs.get(region_name, self.output_dir) / filename
                frame.save(str(filepath))
                saved_files.append(f"  📸 {region_name}: {filename}")
        
        self.capture_count += 1
        print(f"\n{'='*40}")
        print(f"✅ CAPTURED #{self.capture_count}")
        print(f"{'='*40}")
        for f in saved_files:
            print(f)
        print(f"{'='*40}\n")
    
    def run_interactive(self):
        """
        Run interactive capture mode with GLOBAL hotkeys
        
        Global Hotkeys (work even when TFT is focused):
            F9  - Capture all regions
            F10 - Capture board only  
            F11 - Toggle auto-capture
            F12 - Quit
        """
        print("\n" + "=" * 50)
        print("       TFT Training Data Capture")
        print("=" * 50)
        print("\n🎮 GLOBAL HOTKEYS (work while playing TFT):")
        print("   \\   → Capture all regions")
        print("   ]   → Capture full screen only (augments/carousel)")
        print("   F10 → Capture board only")
        print("   F11 → Toggle auto-capture")
        print("   F12 → Quit")
        print(f"\n📁 Saving to: {self.output_dir}")
        print("=" * 50 + "\n")
        
        if not PYNPUT_AVAILABLE:
            print("⚠️  pynput not available. Using basic mode.")
            print("   Install with: pip install pynput")
            return self._run_basic_mode()
        
        self.running = True
        self.pending_capture = None
        last_auto_time = time.time()
        
        # Set up global hotkey listener
        def on_press(key):
            try:
                # Check for '\' key (backslash)
                if hasattr(key, 'char') and key.char == '\\':
                    self.pending_capture = "all"
                # Check for ']' key (right bracket)
                elif hasattr(key, 'char') and key.char == ']':
                    self.pending_capture = "fullscreen"
                elif key == pynput_keyboard.Key.f10:
                    self.pending_capture = "board"
                elif key == pynput_keyboard.Key.f11:
                    self.auto_capture = not self.auto_capture
                    status = "ON ✓" if self.auto_capture else "OFF"
                    print(f"🔄 Auto-capture: {status}")
                elif key == pynput_keyboard.Key.f12:
                    self.running = False
                    return False  # Stop listener
            except:
                pass
        
        # Start hotkey listener in background
        listener = pynput_keyboard.Listener(on_press=on_press)
        listener.start()
        
        print("✅ Listening for hotkeys... Play TFT!")
        print("   Press \\ for all regions, ] for full screen only")
        print("")
        
        try:
            while self.running:
                # Handle pending captures from hotkeys
                if self.pending_capture == "all":
                    self.capture_frame()
                    self.pending_capture = None
                elif self.pending_capture == "fullscreen":
                    self.capture_frame(["full"])
                    self.pending_capture = None
                elif self.pending_capture == "board":
                    self.capture_frame(["board"])
                    self.pending_capture = None
                
                # Handle auto-capture
                if self.auto_capture:
                    if time.time() - last_auto_time >= self.auto_interval:
                        self.capture_frame()
                        last_auto_time = time.time()
                
                time.sleep(0.1)  # Small sleep to prevent CPU spinning
        
        except KeyboardInterrupt:
            print("\n⛔ Interrupted by Ctrl+C")
        
        finally:
            listener.stop()
            self.capture.close()
        
        print(f"\n📊 Total frames captured: {self.capture_count}")
        print(f"📁 Saved to: {self.output_dir}")
    
    def _run_basic_mode(self):
        """Basic mode without OpenCV preview"""
        print("Press Enter to capture, 'q' to quit")
        
        try:
            while True:
                cmd = input("> ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == '' or cmd == 'c':
                    self.capture_frame()
                elif cmd == 'b':
                    self.capture_frame(["board"])
                elif cmd == 's':
                    self.capture_frame(["shop"])
        finally:
            self.capture.close()
        
        print(f"\nTotal frames captured: {self.capture_count}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture TFT training data")
    parser.add_argument("--output", "-o", default=None,
                       help="Output directory for screenshots (default: project/screenshots)")
    parser.add_argument("--auto", "-a", action="store_true",
                       help="Enable auto-capture immediately")
    parser.add_argument("--interval", "-i", type=float, default=2.0,
                       help="Auto-capture interval in seconds")
    
    args = parser.parse_args()
    
    capturer = TrainingDataCapture(args.output)
    capturer.auto_capture = args.auto
    capturer.auto_interval = args.interval
    capturer.run_interactive()


if __name__ == "__main__":
    main()
