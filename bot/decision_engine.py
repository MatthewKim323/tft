"""
TFT Bot Decision Engine

Consumes game state JSON and outputs prioritized actions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path

from .evaluator import BoardEvaluator, EconomyEvaluator, BoardStrength, EconomyState


class ActionType(Enum):
    """Types of actions the bot can perform"""
    BUY_CHAMPION = "buy_champion"
    SELL_CHAMPION = "sell_champion"
    BUY_XP = "buy_xp"
    REROLL = "reroll"
    MOVE_UNIT = "move_unit"
    EQUIP_ITEM = "equip_item"
    TOGGLE_LOCK = "toggle_lock"
    WAIT = "wait"


@dataclass
class Action:
    """A single action to execute"""
    action_type: ActionType
    priority: int  # Lower = higher priority
    params: Dict[str, Any]
    reason: str
    
    def __repr__(self):
        return f"Action({self.action_type.value}, priority={self.priority}, {self.reason})"


@dataclass
class Strategy:
    """Current bot strategy"""
    name: str  # "econ", "slow_roll", "fast_8", "all_in"
    target_level: int
    roll_threshold: int  # Gold threshold to start rolling
    key_champions: List[str]  # Champions to prioritize


class DecisionEngine:
    """
    Main bot brain - analyzes state and generates actions
    
    Decision flow:
    1. Parse game state
    2. Evaluate board and economy
    3. Select strategy based on conditions
    4. Generate prioritized action list
    """
    
    # Strategy templates
    STRATEGIES = {
        "econ": Strategy("econ", 8, 50, []),
        "slow_roll": Strategy("slow_roll", 6, 50, []),  # Roll at 50 gold maintaining interest
        "fast_8": Strategy("fast_8", 8, 30, []),  # Rush level 8
        "all_in": Strategy("all_in", 9, 0, []),  # Spend everything
    }
    
    def __init__(self, tft_data_path: str = None):
        self.board_eval = BoardEvaluator(tft_data_path)
        self.econ_eval = EconomyEvaluator()
        self.current_strategy: Strategy = self.STRATEGIES["econ"]
        self._action_history: List[Action] = []
        
    def decide(self, game_state: Dict[str, Any]) -> List[Action]:
        """
        Main decision function - analyze state and return prioritized actions
        
        Args:
            game_state: Full game state JSON from state_builder
            
        Returns:
            List of Actions sorted by priority (execute in order)
        """
        actions: List[Action] = []
        
        # Evaluate current state
        board_strength = self.board_eval.evaluate_board(game_state)
        econ_state = self.econ_eval.evaluate(game_state)
        
        # Select strategy based on game phase
        self._update_strategy(game_state, board_strength, econ_state)
        
        # Generate actions based on strategy
        actions.extend(self._generate_shop_actions(game_state, econ_state))
        actions.extend(self._generate_level_actions(game_state, econ_state))
        actions.extend(self._generate_board_actions(game_state, board_strength))
        
        # Sort by priority
        actions.sort(key=lambda a: a.priority)
        
        # If no actions, wait
        if not actions:
            actions.append(Action(
                action_type=ActionType.WAIT,
                priority=100,
                params={},
                reason="No actions needed"
            ))
        
        self._action_history.extend(actions)
        return actions
    
    def _update_strategy(self, game_state: Dict[str, Any], 
                         board_strength: BoardStrength,
                         econ_state: EconomyState):
        """Update current strategy based on game state"""
        player = game_state.get('player', {})
        stage_info = game_state.get('stage', {})
        
        health = player.get('health', 100)
        gold = econ_state.gold
        level = player.get('level', 1)
        
        # Parse stage
        stage_str = stage_info.get('current', '1-1')
        try:
            stage = int(stage_str.split('-')[0])
        except:
            stage = 1
        
        # Strategy selection logic
        if health <= 20:
            # Desperate - all in
            self.current_strategy = self.STRATEGIES["all_in"]
        elif stage >= 5 and level >= 7:
            # Late game - push levels
            self.current_strategy = self.STRATEGIES["fast_8"]
        elif stage >= 3 and board_strength.tier == "weak" and gold >= 50:
            # Mid game with weak board - start rolling
            self.current_strategy = self.STRATEGIES["slow_roll"]
        else:
            # Default - econ up
            self.current_strategy = self.STRATEGIES["econ"]
    
    def _generate_shop_actions(self, game_state: Dict[str, Any],
                               econ_state: EconomyState) -> List[Action]:
        """Generate shop-related actions (buy, reroll)"""
        actions = []
        shop = game_state.get('shop', [])
        board = game_state.get('board', [])
        bench = game_state.get('bench', [])
        player = game_state.get('player', {})
        gold = player.get('gold', 0)
        
        # Find potential upgrades
        upgrades = self.board_eval.find_upgrades(game_state)
        upgrade_names = {u['champion'] for u in upgrades if u['need'] == 1}
        
        # Evaluate shop champions
        for slot_idx, shop_unit in enumerate(shop):
            champ_name = shop_unit.get('champion', '').lower()
            cost = shop_unit.get('cost', 1)
            
            if not champ_name or gold < cost:
                continue
            
            # Priority 1: Buy if it completes an upgrade
            if champ_name in upgrade_names:
                actions.append(Action(
                    action_type=ActionType.BUY_CHAMPION,
                    priority=1,
                    params={'slot': slot_idx, 'champion': champ_name, 'cost': cost},
                    reason=f"Completes {champ_name} 2-star upgrade"
                ))
                continue
            
            # Priority 2: Buy pairs for future upgrades
            for upgrade in upgrades:
                if upgrade['champion'] == champ_name and upgrade['need'] == 2:
                    actions.append(Action(
                        action_type=ActionType.BUY_CHAMPION,
                        priority=10,
                        params={'slot': slot_idx, 'champion': champ_name, 'cost': cost},
                        reason=f"Building toward {champ_name} upgrade"
                    ))
                    break
            
            # Priority 3: Buy key champions for current comp
            if champ_name in [c.lower() for c in self.current_strategy.key_champions]:
                actions.append(Action(
                    action_type=ActionType.BUY_CHAMPION,
                    priority=15,
                    params={'slot': slot_idx, 'champion': champ_name, 'cost': cost},
                    reason=f"Key champion for {self.current_strategy.name} strategy"
                ))
        
        # Reroll decision
        if econ_state.should_roll and gold >= 2:
            actions.append(Action(
                action_type=ActionType.REROLL,
                priority=20,
                params={},
                reason=f"Rolling to find upgrades ({self.current_strategy.name} strategy)"
            ))
        
        return actions
    
    def _generate_level_actions(self, game_state: Dict[str, Any],
                                econ_state: EconomyState) -> List[Action]:
        """Generate leveling actions"""
        actions = []
        player = game_state.get('player', {})
        gold = player.get('gold', 0)
        level = player.get('level', 1)
        
        if econ_state.should_level:
            actions.append(Action(
                action_type=ActionType.BUY_XP,
                priority=5,
                params={'current_level': level},
                reason=f"Level up to {level + 1} ({self.current_strategy.name} strategy)"
            ))
        
        return actions
    
    def _generate_board_actions(self, game_state: Dict[str, Any],
                                board_strength: BoardStrength) -> List[Action]:
        """Generate board management actions (positioning, items)"""
        actions = []
        board = game_state.get('board', [])
        bench = game_state.get('bench', [])
        items = game_state.get('items', [])
        
        # Find unequipped items that should be placed
        if items and board:
            # Find best item holder (usually highest cost/star unit)
            best_unit = None
            best_score = 0
            
            for unit in board:
                item_slots = 3 - len(unit.get('items', []))
                if item_slots > 0:
                    score = self.board_eval.get_champion_power(unit)
                    if score > best_score:
                        best_score = score
                        best_unit = unit
            
            if best_unit and items:
                actions.append(Action(
                    action_type=ActionType.EQUIP_ITEM,
                    priority=25,
                    params={
                        'item': items[0],
                        'target': best_unit.get('champion', '')
                    },
                    reason=f"Equip {items[0]} to {best_unit.get('champion', '')}"
                ))
        
        # Check if we should sell any weak units
        if bench:
            for bench_unit in bench:
                champ = bench_unit.get('champion', '')
                star = bench_unit.get('star', 1)
                
                # Sell 1-star units that aren't part of upgrades
                upgrades = self.board_eval.find_upgrades(game_state)
                upgrade_names = {u['champion'] for u in upgrades}
                
                if star == 1 and champ.lower() not in upgrade_names:
                    actions.append(Action(
                        action_type=ActionType.SELL_CHAMPION,
                        priority=30,
                        params={'champion': champ, 'location': 'bench'},
                        reason=f"Sell {champ} (not building toward upgrade)"
                    ))
        
        return actions
    
    def get_action_summary(self, actions: List[Action]) -> str:
        """Get human-readable summary of actions"""
        if not actions:
            return "No actions"
        
        lines = ["Bot Actions:"]
        for i, action in enumerate(actions[:5]):  # Top 5
            lines.append(f"  {i+1}. [{action.action_type.value}] {action.reason}")
        
        if len(actions) > 5:
            lines.append(f"  ... and {len(actions) - 5} more")
        
        return "\n".join(lines)
    
    def set_strategy(self, strategy_name: str, key_champions: List[str] = None):
        """Manually set bot strategy"""
        if strategy_name in self.STRATEGIES:
            self.current_strategy = self.STRATEGIES[strategy_name]
            if key_champions:
                self.current_strategy.key_champions = key_champions
            print(f"Strategy set to: {strategy_name}")
    
    def get_state_summary(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of current game state analysis"""
        board_strength = self.board_eval.evaluate_board(game_state)
        econ_state = self.econ_eval.evaluate(game_state)
        upgrades = self.board_eval.find_upgrades(game_state)
        
        return {
            "strategy": self.current_strategy.name,
            "board_tier": board_strength.tier,
            "board_score": round(board_strength.total_score, 1),
            "gold": econ_state.gold,
            "interest": econ_state.interest,
            "should_level": econ_state.should_level,
            "should_roll": econ_state.should_roll,
            "upgrades_available": len([u for u in upgrades if u['need'] == 1]),
        }


def main():
    """Test decision engine"""
    print("=" * 60)
    print("TFT Decision Engine Test")
    print("=" * 60)
    
    engine = DecisionEngine()
    
    # Sample game state
    sample_state = {
        "timestamp": "2026-02-03T14:32:05Z",
        "stage": {"current": "3-2", "phase": "planning"},
        "player": {
            "health": 78,
            "gold": 34,
            "level": 6,
            "xp": {"current": 12, "required": 24}
        },
        "board": [
            {"slot": [2, 1], "champion": "Veigar", "star": 2, "items": ["Rabadon"]},
            {"slot": [3, 1], "champion": "Lulu", "star": 2, "items": []},
            {"slot": [1, 2], "champion": "Zoe", "star": 1, "items": []},
            {"slot": [4, 2], "champion": "Heimerdinger", "star": 1, "items": ["Blue Buff"]},
        ],
        "bench": [
            {"slot": 0, "champion": "Lulu", "star": 1, "items": []},
            {"slot": 1, "champion": "Zoe", "star": 1, "items": []},
        ],
        "shop": [
            {"slot": 0, "champion": "Zoe", "cost": 3},
            {"slot": 1, "champion": "Teemo", "cost": 3},
            {"slot": 2, "champion": "Garen", "cost": 1},
            {"slot": 3, "champion": "Darius", "cost": 2},
            {"slot": 4, "champion": "Veigar", "cost": 3},
        ],
        "items": ["BF Sword", "Chain Vest"],
        "traits": [
            {"name": "Sorcerer", "count": 4, "tier": "gold"},
            {"name": "Yordle", "count": 3, "tier": "silver"}
        ],
        "augments": ["Celestial Blessing"]
    }
    
    # Get state summary
    summary = engine.get_state_summary(sample_state)
    print("\nState Analysis:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Get actions
    actions = engine.decide(sample_state)
    print("\n" + engine.get_action_summary(actions))
    
    # Show detailed actions
    print("\nDetailed Action List:")
    for action in actions:
        print(f"  Priority {action.priority}: {action}")
        print(f"    Params: {action.params}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
