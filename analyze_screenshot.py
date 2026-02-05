#!/usr/bin/env python3
r"""
TFT Manual Analysis Trigger

Press hotkey to trigger analysis via the API.
Results appear in the dashboard AND terminal.

Usage:
    1. Start the API: python run_state_api.py --manual
    2. Start frontend: cd frontend && npm run dev
    3. Run this: python analyze_screenshot.py

Hotkeys:
    \  = Trigger analysis (capture + analyze + show result)
    q  = Quit
"""

import sys
import json
import requests
from datetime import datetime

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("Install pynput: pip install pynput")

API_URL = "http://127.0.0.1:8000"


class ManualTrigger:
    """Trigger manual analysis via API"""
    
    def __init__(self):
        self.running = True
        
        # Check API is running
        try:
            resp = requests.get(f"{API_URL}/status", timeout=10)
            status = resp.json()
            mode = status.get('mode', 'unknown')
            print(f"✓ Connected to API (mode: {mode})")
        except Exception as e:
            print(f"✗ Cannot connect to API! Error: {e}")
            print("  Make sure to run: python run_state_api.py --manual")
            sys.exit(1)
        
        print("\n" + "=" * 50)
        print("HOTKEYS:")
        print("  \\  = Analyze (capture + analyze)")
        print("  q  = Quit")
        print("=" * 50 + "\n")
        print("Waiting for hotkey...\n")
    
    def trigger_analysis(self):
        """Call the API to trigger analysis"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] Triggering analysis...")
        
        try:
            resp = requests.post(f"{API_URL}/analyze", timeout=30)
            
            if resp.status_code != 200:
                print(f"  ✗ Error: {resp.text}")
                return
            
            result = resp.json()
            
            # Display game state
            game_state = result.get('game_state', {})
            player = game_state.get('player', {})
            stage = game_state.get('stage', {}).get('current', '?')
            
            print(f"\n  📊 GAME STATE")
            print(f"     Stage: {stage}")
            print(f"     HP: {player.get('health', '?')}")
            print(f"     Gold: {player.get('gold', '?')}")
            print(f"     Level: {player.get('level', '?')}")
            
            shop = game_state.get('shop', [])
            if shop:
                champs = [s.get('champion', '?') for s in shop[:5]]
                print(f"     Shop: {', '.join(champs)}")
            
            # Display decision
            decision_data = result.get('decision', {})
            decision = decision_data.get('decision', {})
            
            action = decision.get('action', '?').upper()
            target = decision.get('target', '?')
            priority = decision.get('priority', '?').upper()
            reasoning = decision.get('reasoning', '?')
            
            # Priority indicator
            if priority == "CRITICAL":
                indicator = "🔴"
            elif priority == "HIGH":
                indicator = "🟠"
            elif priority == "MEDIUM":
                indicator = "🟢"
            else:
                indicator = "🔵"
            
            print(f"\n  🎯 COACH RECOMMENDATION")
            print(f"     [{indicator} {priority}]")
            print(f"     Action: {action}")
            print(f"     Target: {target}")
            print(f"     Why: {reasoning}")
            
            # Screenshot path
            screenshot = result.get('screenshot_path')
            if screenshot:
                print(f"\n  📸 Screenshot: {screenshot}")
            
            print("\n" + "-" * 50)
            print("(Decision also sent to dashboard)")
            
        except requests.Timeout:
            print("  ✗ Timeout - analysis took too long")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def on_press(self, key):
        """Handle key presses"""
        try:
            if hasattr(key, 'char'):
                if key.char == '\\':
                    self.trigger_analysis()
                elif key.char == 'q':
                    print("\nQuitting...")
                    self.running = False
                    return False
        except:
            pass
    
    def run(self):
        """Main loop"""
        if not PYNPUT_AVAILABLE:
            print("pynput not available. Using input mode.")
            while self.running:
                cmd = input("\nPress Enter to analyze (or 'q' to quit): ").strip().lower()
                if cmd == 'q':
                    break
                else:
                    self.trigger_analysis()
            return
        
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()
        
        print("Done!")


def main():
    print("=" * 50)
    print("TFT Manual Analysis Trigger")
    print("=" * 50)
    
    trigger = ManualTrigger()
    trigger.run()


if __name__ == "__main__":
    main()
