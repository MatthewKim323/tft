#!/usr/bin/env python3
"""
TFT Bot - Main Entry Point

Combines state extraction with AI coach to play TFT.

Usage:
    # Test components
    python run_bot.py --test
    
    # Dry run (no mouse control, just analysis)
    python run_bot.py --dry-run
    
    # Live mode (actually controls mouse)
    python run_bot.py --live
    
    # Single analysis
    python run_bot.py --analyze
"""

import argparse
import time
import json
from pathlib import Path


def run_analysis_mode():
    """Run single game state analysis"""
    print("\n" + "=" * 60)
    print("TFT Bot - Analysis Mode")
    print("=" * 60)
    
    try:
        from state_extraction.state_builder import StateBuilder
        from bot.coach import TFTCoach
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed.")
        return
    
    # Initialize components
    print("\nInitializing...")
    state_builder = StateBuilder()
    coach = TFTCoach()
    
    # Capture and analyze
    print("Capturing game state...")
    game_state = state_builder.build_state_fast()
    
    if not game_state:
        print("Could not capture game state. Make sure TFT is visible.")
        return
    
    # Show state
    print("\n📊 Game State:")
    state_dict = game_state.to_dict()
    print(f"  Stage: {state_dict.get('stage', {}).get('current', '?')}")
    print(f"  HP: {state_dict.get('player', {}).get('health', '?')}")
    print(f"  Gold: {state_dict.get('player', {}).get('gold', '?')}")
    print(f"  Level: {state_dict.get('player', {}).get('level', '?')}")
    print(f"  Board: {len(state_dict.get('board', []))} units")
    print(f"  Shop: {len(state_dict.get('shop', []))} champions")
    
    # Get coach recommendation
    decision = coach.analyze(state_dict)
    
    print("\n🎯 Coach Recommendation:")
    print(f"  Action: {decision.decision.action.value}")
    print(f"  Target: {decision.decision.target}")
    print(f"  Priority: {decision.decision.priority.value}")
    print(f"  Reason: {decision.decision.reasoning}")
    
    state_builder.close()
    print("\n" + "=" * 60)


def run_dry_mode():
    """Run continuous analysis without mouse control"""
    print("\n" + "=" * 60)
    print("TFT Bot - Dry Run Mode (Analysis Only)")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    try:
        from state_extraction.state_builder import StateBuilder
        from bot.coach import TFTCoach
    except ImportError as e:
        print(f"Import error: {e}")
        return
    
    state_builder = StateBuilder()
    coach = TFTCoach()
    
    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            game_state = state_builder.build_state_fast()
            
            if game_state:
                state_dict = game_state.to_dict()
                player = state_dict.get('player', {})
                stage = state_dict.get('stage', {}).get('current', '?')
                
                # One-line status
                print(f"Stage: {stage} | HP: {player.get('health', '?')} | Gold: {player.get('gold', '?')} | Level: {player.get('level', '?')}")
                
                # Get recommendation
                decision = coach.analyze(state_dict)
                print(f"Coach: [{decision.decision.priority.value.upper()}] {decision.decision.action.value} - {decision.decision.target}")
                print(f"       {decision.decision.reasoning}")
            else:
                print("Could not get game state")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\nStopped")
    finally:
        state_builder.close()


def run_live_mode(calibration_path: str = None):
    """Run bot with actual mouse control"""
    print("\n" + "=" * 60)
    print("TFT Bot - LIVE Mode")
    print("⚠️  Bot will control your mouse!")
    print("⚠️  Move mouse to corner to abort (failsafe)")
    print("=" * 60)
    
    confirm = input("\nType 'START' to begin: ")
    if confirm.upper() != 'START':
        print("Aborted.")
        return
    
    try:
        from state_extraction.state_builder import StateBuilder
        from bot.actions import BotRunner
    except ImportError as e:
        print(f"Import error: {e}")
        return
    
    state_builder = StateBuilder()
    
    def get_state():
        state = state_builder.build_state_fast()
        return state.to_dict() if state else {}
    
    runner = BotRunner(
        calibration_path=calibration_path,
        dry_run=False
    )
    
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    try:
        runner.run_loop(get_state)
    finally:
        state_builder.close()


def test_components():
    """Test all bot components"""
    print("\n" + "=" * 60)
    print("TFT Bot - Component Test")
    print("=" * 60)
    
    # Test imports
    print("\n1. Testing imports...")
    
    try:
        from state_extraction.capture import ScreenCapture
        print("   ✓ ScreenCapture")
    except ImportError as e:
        print(f"   ✗ ScreenCapture: {e}")
    
    try:
        from state_extraction.ocr import OCRExtractor
        print("   ✓ OCRExtractor")
    except ImportError as e:
        print(f"   ✗ OCRExtractor: {e}")
    
    try:
        from state_extraction.template_matcher import TemplateMatcher
        print("   ✓ TemplateMatcher")
    except ImportError as e:
        print(f"   ✗ TemplateMatcher: {e}")
    
    try:
        from state_extraction.state_builder import StateBuilder
        print("   ✓ StateBuilder")
    except ImportError as e:
        print(f"   ✗ StateBuilder: {e}")
    
    try:
        from bot.coach import TFTCoach
        print("   ✓ TFTCoach")
    except ImportError as e:
        print(f"   ✗ TFTCoach: {e}")
    
    try:
        from bot.analyzers import EconomyAnalyzer, BoardAnalyzer, ShopAnalyzer
        print("   ✓ Analyzers")
    except ImportError as e:
        print(f"   ✗ Analyzers: {e}")
    
    try:
        from bot.actions import ActionExecutor
        print("   ✓ ActionExecutor")
    except ImportError as e:
        print(f"   ✗ ActionExecutor: {e}")
    
    # Test screen capture
    print("\n2. Testing screen capture...")
    try:
        from state_extraction.capture import ScreenCapture
        capture = ScreenCapture()
        frame = capture.capture_full_screen()
        print(f"   ✓ Captured {frame.width}x{frame.height} screenshot")
        capture.close()
    except Exception as e:
        print(f"   ✗ Capture failed: {e}")
    
    # Test coach with sample data
    print("\n3. Testing AI coach...")
    try:
        from bot.coach import TFTCoach
        coach = TFTCoach()
        
        sample_state = {
            "player": {"health": 70, "gold": 45, "level": 6},
            "stage": {"current": "3-3"},
            "board": [{"champion": "Veigar", "star": 2, "items": []}],
            "bench": [{"champion": "Lulu", "star": 1, "items": []}],
            "shop": [{"slot": 0, "champion": "Lulu", "cost": 2}],
            "traits": [{"name": "Sorcerer", "tier": "gold"}],
            "items": []
        }
        
        decision = coach.analyze(sample_state)
        print(f"   ✓ Generated decision: {decision.decision.action.value}")
        print(f"   ✓ Target: {decision.decision.target}")
    except Exception as e:
        print(f"   ✗ Coach failed: {e}")
    
    print("\n" + "=" * 60)
    print("Component test complete!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="TFT Bot - AI-Powered TFT Coach")
    
    parser.add_argument('--analyze', action='store_true',
                       help='Run single analysis of current game state')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run continuous analysis without mouse control')
    parser.add_argument('--live', action='store_true',
                       help='Run bot with actual mouse control')
    parser.add_argument('--test', action='store_true',
                       help='Test all bot components')
    parser.add_argument('--calibration', type=str,
                       help='Path to ROI calibration file')
    
    args = parser.parse_args()
    
    if args.test:
        test_components()
    elif args.analyze:
        run_analysis_mode()
    elif args.dry_run:
        run_dry_mode()
    elif args.live:
        calibration = args.calibration or "roi_calibration.json"
        run_live_mode(calibration)
    else:
        # Default: show help
        print("\nTFT Bot - AI-Powered TFT Coach")
        print("\nUsage:")
        print("  python run_bot.py --test      # Test all components")
        print("  python run_bot.py --analyze   # Single analysis")
        print("  python run_bot.py --dry-run   # Continuous analysis (no mouse)")
        print("  python run_bot.py --live      # LIVE mode with mouse control")
        print("\nRecommended workflow:")
        print("  1. Run calibration: python training/calibrate_roi.py")
        print("  2. Test components: python run_bot.py --test")
        print("  3. Try dry run:     python run_bot.py --dry-run")
        print("  4. Go live:         python run_bot.py --live")


if __name__ == "__main__":
    main()
