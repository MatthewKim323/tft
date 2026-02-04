"""
TFT Bot Action Executor

Executes bot decisions by controlling mouse/keyboard.
Converts Action objects into actual game inputs.
"""

import time
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class ActionExecutor:
    """
    Executes TFT actions via mouse control
    
    Coordinate system based on calibrated ROIs.
    All positions are relative to the TFT game window.
    """
    
    # Default positions at 2560x1664 resolution (adjust via calibration)
    DEFAULT_POSITIONS = {
        # Shop slots (5 slots, centered in shop region)
        "shop_slot_0": (560, 1500),
        "shop_slot_1": (860, 1500),
        "shop_slot_2": (1160, 1500),
        "shop_slot_3": (1460, 1500),
        "shop_slot_4": (1760, 1500),
        
        # Shop buttons
        "buy_xp": (500, 1580),
        "reroll": (640, 1580),
        "lock_shop": (780, 1580),
        
        # Bench slots (9 slots)
        "bench_slot_0": (440, 1260),
        "bench_slot_1": (560, 1260),
        "bench_slot_2": (680, 1260),
        "bench_slot_3": (800, 1260),
        "bench_slot_4": (920, 1260),
        "bench_slot_5": (1040, 1260),
        "bench_slot_6": (1160, 1260),
        "bench_slot_7": (1280, 1260),
        "bench_slot_8": (1400, 1260),
        
        # Item inventory (rough positions)
        "item_0": (40, 300),
        "item_1": (40, 380),
        "item_2": (40, 460),
        "item_3": (40, 540),
        "item_4": (40, 620),
        
        # Board hex positions (4x7 grid, approximate centers)
        # Row 0 (back row)
        "board_0_0": (600, 340),
        "board_1_0": (760, 340),
        "board_2_0": (920, 340),
        "board_3_0": (1080, 340),
        "board_4_0": (1240, 340),
        "board_5_0": (1400, 340),
        "board_6_0": (1560, 340),
        # Row 1
        "board_0_1": (680, 440),
        "board_1_1": (840, 440),
        "board_2_1": (1000, 440),
        "board_3_1": (1160, 440),
        "board_4_1": (1320, 440),
        "board_5_1": (1480, 440),
        # Row 2
        "board_0_2": (600, 540),
        "board_1_2": (760, 540),
        "board_2_2": (920, 540),
        "board_3_2": (1080, 540),
        "board_4_2": (1240, 540),
        "board_5_2": (1400, 540),
        "board_6_2": (1560, 540),
        # Row 3 (front row)
        "board_0_3": (680, 640),
        "board_1_3": (840, 640),
        "board_2_3": (1000, 640),
        "board_3_3": (1160, 640),
        "board_4_3": (1320, 640),
        "board_5_3": (1480, 640),
        
        # Sell area
        "sell_area": (1280, 1580),
    }
    
    def __init__(self, 
                 calibration_path: str = None,
                 game_window_offset: Tuple[int, int] = (0, 0),
                 execution_speed: float = 1.0,
                 dry_run: bool = False):
        """
        Initialize action executor
        
        Args:
            calibration_path: Path to roi_calibration.json
            game_window_offset: (x, y) offset to add to all positions
            execution_speed: Speed multiplier (0.5 = slower, 2.0 = faster)
            dry_run: If True, log actions without executing
        """
        self.positions = self.DEFAULT_POSITIONS.copy()
        self.game_offset = game_window_offset
        self.speed = execution_speed
        self.dry_run = dry_run
        
        # Safety settings
        self.move_duration = 0.1 / execution_speed
        self.click_delay = 0.05 / execution_speed
        self.action_delay = 0.3 / execution_speed
        
        if calibration_path:
            self._load_calibration(calibration_path)
        
        if not PYAUTOGUI_AVAILABLE and not dry_run:
            print("Warning: pyautogui not available. Install with: pip install pyautogui")
            self.dry_run = True
        
        # PyAutoGUI safety settings
        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
            pyautogui.PAUSE = 0.05
    
    def _load_calibration(self, path: str):
        """Load calibration data and update positions"""
        path = Path(path)
        if not path.exists():
            print(f"Calibration file not found: {path}")
            return
        
        try:
            with open(path, 'r') as f:
                calibration = json.load(f)
            
            # Update game window offset
            if 'game_window' in calibration:
                gw = calibration['game_window']
                self.game_offset = (gw['x'], gw['y'])
                
                # Scale positions based on calibrated size vs default
                scale_x = gw['width'] / 2560
                scale_y = gw['height'] / 1664
                
                for key, (x, y) in self.DEFAULT_POSITIONS.items():
                    self.positions[key] = (
                        int(gw['x'] + x * scale_x),
                        int(gw['y'] + y * scale_y)
                    )
            
            print(f"Loaded calibration from {path}")
            print(f"Game window offset: {self.game_offset}")
            
        except Exception as e:
            print(f"Error loading calibration: {e}")
    
    def _get_position(self, position_name: str) -> Tuple[int, int]:
        """Get absolute screen position for a named location"""
        if position_name in self.positions:
            return self.positions[position_name]
        
        # Handle dynamic positions (e.g., shop_slot_3)
        if position_name.startswith("shop_slot_"):
            slot = int(position_name.split("_")[-1])
            base = self.positions.get("shop_slot_0", (560, 1500))
            return (base[0] + slot * 300, base[1])
        
        if position_name.startswith("bench_slot_"):
            slot = int(position_name.split("_")[-1])
            base = self.positions.get("bench_slot_0", (440, 1260))
            return (base[0] + slot * 120, base[1])
        
        # Board position parsing (board_X_Y)
        if position_name.startswith("board_"):
            parts = position_name.split("_")
            if len(parts) == 3:
                col, row = int(parts[1]), int(parts[2])
                return self._get_board_position(col, row)
        
        print(f"Unknown position: {position_name}")
        return (0, 0)
    
    def _get_board_position(self, col: int, row: int) -> Tuple[int, int]:
        """Calculate board hex center position"""
        # Hex grid with staggered rows
        base_x = 600 + self.game_offset[0]
        base_y = 340 + self.game_offset[1]
        
        hex_width = 160
        hex_height = 100
        
        # Offset for staggered rows
        row_offset = (row % 2) * (hex_width // 2)
        
        x = base_x + col * hex_width + row_offset
        y = base_y + row * hex_height
        
        return (x, y)
    
    def click(self, x: int, y: int, button: str = 'left'):
        """Execute a mouse click"""
        if self.dry_run:
            print(f"[DRY RUN] Click {button} at ({x}, {y})")
            return
        
        if PYAUTOGUI_AVAILABLE:
            pyautogui.moveTo(x, y, duration=self.move_duration)
            time.sleep(self.click_delay)
            pyautogui.click(button=button)
            time.sleep(self.action_delay)
    
    def click_position(self, position_name: str, button: str = 'left'):
        """Click a named position"""
        x, y = self._get_position(position_name)
        self.click(x, y, button)
    
    def drag(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Drag from one position to another"""
        if self.dry_run:
            print(f"[DRY RUN] Drag from {from_pos} to {to_pos}")
            return
        
        if PYAUTOGUI_AVAILABLE:
            pyautogui.moveTo(from_pos[0], from_pos[1], duration=self.move_duration)
            time.sleep(self.click_delay)
            pyautogui.drag(
                to_pos[0] - from_pos[0],
                to_pos[1] - from_pos[1],
                duration=self.move_duration * 2
            )
            time.sleep(self.action_delay)
    
    # === High-level TFT Actions ===
    
    def buy_shop_champion(self, slot: int):
        """Buy champion from shop slot (0-4)"""
        print(f"Buying champion from shop slot {slot}")
        self.click_position(f"shop_slot_{slot}")
    
    def sell_unit(self, from_bench: bool = True, slot: int = 0):
        """Sell a unit by dragging to sell area"""
        if from_bench:
            from_pos = self._get_position(f"bench_slot_{slot}")
        else:
            # Would need board position
            from_pos = self._get_position(f"board_{slot}_0")
        
        to_pos = self._get_position("sell_area")
        print(f"Selling unit from {'bench' if from_bench else 'board'} slot {slot}")
        self.drag(from_pos, to_pos)
    
    def buy_xp(self):
        """Click buy XP button"""
        print("Buying XP")
        self.click_position("buy_xp")
    
    def reroll(self):
        """Click reroll button"""
        print("Rerolling shop")
        self.click_position("reroll")
    
    def toggle_shop_lock(self):
        """Toggle shop lock"""
        print("Toggling shop lock")
        self.click_position("lock_shop")
    
    def move_unit(self, from_pos: str, to_pos: str):
        """Move a unit from one position to another"""
        from_xy = self._get_position(from_pos)
        to_xy = self._get_position(to_pos)
        print(f"Moving unit from {from_pos} to {to_pos}")
        self.drag(from_xy, to_xy)
    
    def equip_item(self, item_slot: int, target_pos: str):
        """Equip item from inventory to a unit"""
        item_pos = self._get_position(f"item_{item_slot}")
        target_xy = self._get_position(target_pos)
        print(f"Equipping item {item_slot} to {target_pos}")
        self.drag(item_pos, target_xy)
    
    def place_from_bench(self, bench_slot: int, board_col: int, board_row: int):
        """Place a unit from bench to board"""
        from_pos = self._get_position(f"bench_slot_{bench_slot}")
        to_pos = self._get_board_position(board_col, board_row)
        print(f"Placing bench slot {bench_slot} to board ({board_col}, {board_row})")
        self.drag(from_pos, to_pos)
    
    def execute_action(self, action) -> bool:
        """
        Execute a single Action object from the decision engine
        
        Args:
            action: Action object with action_type and params
            
        Returns:
            True if executed successfully
        """
        from .decision_engine import ActionType
        
        try:
            if action.action_type == ActionType.BUY_CHAMPION:
                slot = action.params.get('slot', 0)
                self.buy_shop_champion(slot)
                
            elif action.action_type == ActionType.SELL_CHAMPION:
                location = action.params.get('location', 'bench')
                # Would need to find unit position
                self.sell_unit(from_bench=(location == 'bench'))
                
            elif action.action_type == ActionType.BUY_XP:
                self.buy_xp()
                
            elif action.action_type == ActionType.REROLL:
                self.reroll()
                
            elif action.action_type == ActionType.MOVE_UNIT:
                from_pos = action.params.get('from')
                to_pos = action.params.get('to')
                if from_pos and to_pos:
                    self.move_unit(from_pos, to_pos)
                    
            elif action.action_type == ActionType.EQUIP_ITEM:
                item = action.params.get('item_slot', 0)
                target = action.params.get('target_position', 'board_3_1')
                self.equip_item(item, target)
                
            elif action.action_type == ActionType.TOGGLE_LOCK:
                self.toggle_shop_lock()
                
            elif action.action_type == ActionType.WAIT:
                print("Waiting...")
                time.sleep(0.5)
                
            else:
                print(f"Unknown action type: {action.action_type}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error executing action: {e}")
            return False
    
    def execute_actions(self, actions: list, max_actions: int = 5) -> int:
        """
        Execute a list of actions
        
        Args:
            actions: List of Action objects
            max_actions: Maximum number of actions to execute
            
        Returns:
            Number of actions successfully executed
        """
        executed = 0
        
        for action in actions[:max_actions]:
            print(f"\nExecuting: {action.reason}")
            if self.execute_action(action):
                executed += 1
                time.sleep(self.action_delay)
            else:
                print(f"Failed to execute action")
        
        return executed


class BotRunner:
    """
    Main bot loop that combines state extraction, decision, and execution
    """
    
    def __init__(self, 
                 calibration_path: str = None,
                 dry_run: bool = True):
        from .decision_engine import DecisionEngine
        
        self.engine = DecisionEngine()
        self.executor = ActionExecutor(
            calibration_path=calibration_path,
            dry_run=dry_run
        )
        self.running = False
        self.loop_delay = 2.0  # Seconds between decision cycles
    
    def run_once(self, game_state: Dict[str, Any]) -> List[Any]:
        """Run one decision cycle"""
        actions = self.engine.decide(game_state)
        
        print("\n" + "=" * 40)
        print(self.engine.get_action_summary(actions))
        print("=" * 40)
        
        if not self.executor.dry_run:
            self.executor.execute_actions(actions)
        
        return actions
    
    def run_loop(self, state_getter, max_iterations: int = None):
        """
        Run continuous bot loop
        
        Args:
            state_getter: Callable that returns current game state dict
            max_iterations: Maximum iterations (None for infinite)
        """
        self.running = True
        iteration = 0
        
        print("\n🤖 Bot started! Move mouse to corner to abort (failsafe)")
        
        try:
            while self.running:
                if max_iterations and iteration >= max_iterations:
                    break
                
                # Get current state
                game_state = state_getter()
                
                if game_state:
                    self.run_once(game_state)
                else:
                    print("Could not get game state")
                
                iteration += 1
                time.sleep(self.loop_delay)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the bot loop"""
        self.running = False


def main():
    """Test action executor"""
    print("=" * 50)
    print("TFT Action Executor Test (Dry Run)")
    print("=" * 50)
    
    executor = ActionExecutor(dry_run=True)
    
    print("\nTesting individual actions:")
    executor.buy_shop_champion(2)
    executor.buy_xp()
    executor.reroll()
    executor.place_from_bench(0, 3, 2)
    
    print("\n" + "=" * 50)
    print("Testing with decision engine:")
    print("=" * 50)
    
    from .decision_engine import DecisionEngine, Action, ActionType
    
    # Create test actions
    test_actions = [
        Action(ActionType.BUY_CHAMPION, 1, {'slot': 2, 'champion': 'Zoe'}, "Buy Zoe for upgrade"),
        Action(ActionType.BUY_XP, 5, {}, "Level up"),
        Action(ActionType.REROLL, 10, {}, "Reroll for upgrades"),
    ]
    
    print("\nExecuting test actions:")
    executed = executor.execute_actions(test_actions)
    print(f"\nExecuted {executed} actions")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
