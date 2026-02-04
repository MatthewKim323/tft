#!/usr/bin/env python3
"""
TFT Bot - Main Entry Point

Combines state extraction with decision engine to play TFT automatically.

Usage:
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
    print("🎮 TFT Bot - Analysis Mode")
    print("=" * 60)
    
    try:
        from state_extraction.state_builder import StateBuilder
        from bot.decision_engine import DecisionEngine
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed.")
        return
    
    # Initialize components
    print("\nInitializing...")
    state_builder = StateBuilder()
    engine = DecisionEngine()
    
    # Capture and analyze
    print("Capturing game state...")
    game_state = state_builder.build_state_fast()
    
    if not game_state:
        print("Could not capture game state. Make sure TFT is visible.")
        return
    
    # Show state
    print("\n📊 Game State:")
    print(json.dumps(game_state, indent=2, default=str)[:2000] + "...")
    
    # Get analysis
    summary = engine.get_state_summary(game_state)
    print("\n📈 Analysis:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Get recommended actions
    actions = engine.decide(game_state)
    print("\n" + engine.get_action_summary(actions))
    
    state_builder.close()
    print("\n" + "=" * 60)


def run_dry_mode():
    """Run continuous analysis without mouse control"""
    print("\n" + "=" * 60)
    print("🎮 TFT Bot - Dry Run Mode (Analysis Only)")
    print("=" * 60)
    print("Press Ctrl+C to stop\n")
    
    try:
        from state_extraction.state_builder import StateBuilder
        from bot.decision_engine import DecisionEngine
    except ImportError as e:
        print(f"Import error: {e}")
        return
    
    state_builder = StateBuilder()
    engine = DecisionEngine()
    
    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            game_state = state_builder.build_state_fast()
            
            if game_state:
                summary = engine.get_state_summary(game_state)
                
                # One-line status
                player = game_state.get('player', {})
                stage = game_state.get('stage', {}).get('current', '?')
                print(f"Stage: {stage} | HP: {player.get('health', '?')} | Gold: {player.get('gold', '?')} | Level: {player.get('level', '?')}")
                print(f"Board: {summary['board_tier']} ({summary['board_score']}) | Strategy: {summary['strategy']}")
                
                actions = engine.decide(game_state)
                if actions:
                    print(f"Top Action: {actions[0].reason}")
            else:
                print("Could not get game state")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped")
    finally:
        state_builder.close()


def run_live_mode(calibration_path: str = None):
    """Run bot with actual mouse control"""
    print("\n" + "=" * 60)
    print("🎮 TFT Bot - LIVE Mode")
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
        return state_builder.build_state_fast()
    
    runner = BotRunner(
        calibration_path=calibration_path,
        dry_run=False
    )
    
    print("\n🚀 Starting in 3 seconds...")
    time.sleep(3)
    
    try:
        runner.run_loop(get_state)
    finally:
        state_builder.close()


def test_components():
    """Test all bot components"""
    print("\n" + "=" * 60)
    print("🧪 TFT Bot - Component Test")
    print("=" * 60)
    
    # Test imports
    print("\n1. Testing imports...")
    try:
        from state_extraction.capture import ScreenCapture
        print("   ✓ ScreenCapture")
    except ImportError as e:
        print(f"   ✗ ScreenCapture: {e}")
    
    try:
        from state_extraction.ocr import OCREngine
        print("   ✓ OCREngine")
    except ImportError as e:
        print(f"   ✗ OCREngine: {e}")
    
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
        from bot.decision_engine import DecisionEngine
        print("   ✓ DecisionEngine")
    except ImportError as e:
        print(f"   ✗ DecisionEngine: {e}")
    
    try:
        from bot.evaluator import BoardEvaluator, EconomyEvaluator
        print("   ✓ Evaluators")
    except ImportError as e:
        print(f"   ✗ Evaluators: {e}")
    
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
    
    # Test decision engine with sample data
    print("\n3. Testing decision engine...")
    try:
        from bot.decision_engine import DecisionEngine
        engine = DecisionEngine()
        
        sample_state = {
            "player": {"health": 70, "gold": 45, "level": 6},
            "stage": {"current": "3-3"},
            "board": [{"champion": "Veigar", "star": 2, "items": []}],
            "bench": [],
            "shop": [{"champion": "Lulu", "cost": 2}],
            "traits": [{"name": "Sorcerer", "tier": "gold"}],
            "items": []
        }
        
        actions = engine.decide(sample_state)
        print(f"   ✓ Generated {len(actions)} actions")
        if actions:
            print(f"   ✓ Top action: {actions[0].reason}")
    except Exception as e:
        print(f"   ✗ Decision engine failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Component test complete!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="TFT Bot - Automated TFT Player")
    
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
        print("\n🎮 TFT Bot")
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
