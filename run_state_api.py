#!/usr/bin/env python3
"""
Run the TFT State Extraction API Server

Usage:
    python run_state_api.py

API Endpoints:
    GET  /           - Health check
    GET  /state      - Get current game state
    GET  /state/player - Get player HUD info only
    GET  /regions    - Get ROI definitions
    WS   /ws/state   - Real-time state streaming
"""

import sys
from pathlib import Path

# Add state_extraction to path
sys.path.insert(0, str(Path(__file__).parent))

from state_extraction.api import run_server

if __name__ == "__main__":
    print("=" * 50)
    print("TFT State Extraction API Server")
    print("=" * 50)
    print("\nMake sure TFT is running and visible on screen!")
    print("\nEndpoints:")
    print("  http://127.0.0.1:8000/        - Health check")
    print("  http://127.0.0.1:8000/state   - Get game state")
    print("  http://127.0.0.1:8000/docs    - API documentation")
    print("  ws://127.0.0.1:8000/ws/state  - WebSocket stream")
    print("\n" + "=" * 50)
    
    run_server(host="127.0.0.1", port=8000)
