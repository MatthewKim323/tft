#!/usr/bin/env python3
"""
TFT State Extraction API Server

Two modes:
  --manual     : Only analyze when you trigger (press hotkey or call API)
  --auto       : Continuous real-time analysis (autonomous mode)

Usage:
    python run_state_api.py --manual   # Manual mode (recommended for training)
    python run_state_api.py --auto     # Autonomous mode (continuous analysis)
    python run_state_api.py            # Default: manual mode

API Endpoints:
    GET  /              - Health check
    GET  /state         - Get current game state
    GET  /decision      - Get coach decision
    POST /analyze       - Trigger manual analysis (manual mode)
    WS   /ws/decisions  - Stream decisions to dashboard
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="TFT Coach API Server")
    parser.add_argument('--manual', action='store_true', default=True,
                       help='Manual mode - analyze on trigger only (default)')
    parser.add_argument('--auto', action='store_true',
                       help='Autonomous mode - continuous real-time analysis')
    parser.add_argument('--port', type=int, default=8000,
                       help='API port (default: 8000)')
    
    args = parser.parse_args()
    
    # Auto mode overrides manual
    mode = "auto" if args.auto else "manual"
    
    print("=" * 60)
    print("TFT Coach API Server")
    print("=" * 60)
    
    if mode == "manual":
        print("\n📸 MANUAL MODE")
        print("   Analysis runs only when you trigger it.")
        print("   Perfect for training and learning the system.")
        print("\n   Triggers:")
        print("     - Press '\\' key (if hotkey listener running)")
        print("     - POST http://127.0.0.1:8000/analyze")
        print("     - Dashboard 'Analyze' button")
    else:
        print("\n🤖 AUTONOMOUS MODE")
        print("   Continuous real-time analysis.")
        print("   Coach streams decisions automatically.")
    
    print("\n" + "-" * 60)
    print("Endpoints:")
    print(f"  http://127.0.0.1:{args.port}/         - Health check")
    print(f"  http://127.0.0.1:{args.port}/status   - System status")
    print(f"  http://127.0.0.1:{args.port}/state    - Current game state")
    print(f"  http://127.0.0.1:{args.port}/decision - Coach decision")
    print(f"  http://127.0.0.1:{args.port}/analyze  - Trigger analysis (manual)")
    print(f"  http://127.0.0.1:{args.port}/docs     - API documentation")
    print(f"  ws://127.0.0.1:{args.port}/ws/decisions - Decision stream")
    print("-" * 60)
    print("\nMake sure TFT is visible on screen!")
    print("=" * 60 + "\n")
    
    # Set mode in environment for API to read
    import os
    os.environ['TFT_MODE'] = mode
    
    from state_extraction.api import run_server
    run_server(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
