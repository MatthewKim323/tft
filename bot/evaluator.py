"""
Board and Economy Evaluator for TFT Bot

Evaluates current game state to inform decision-making.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class ChampionTier:
    """Champion cost/tier information"""
    name: str
    cost: int
    traits: List[str]


@dataclass
class TraitBonus:
    """Trait bonus thresholds"""
    name: str
    thresholds: List[int]  # e.g., [2, 4, 6] for bronze/silver/gold


@dataclass
class BoardStrength:
    """Evaluated board strength"""
    total_score: float
    unit_score: float  # Raw unit power
    synergy_score: float  # Trait bonuses
    item_score: float  # Item value
    positioning_score: float  # Positioning quality
    
    @property
    def tier(self) -> str:
        """Get strength tier: weak, average, strong, dominant"""
        if self.total_score >= 80:
            return "dominant"
        elif self.total_score >= 60:
            return "strong"
        elif self.total_score >= 40:
            return "average"
        else:
            return "weak"


@dataclass
class EconomyState:
    """Current economy evaluation"""
    gold: int
    interest: int  # Gold from interest (0-5)
    streak_bonus: int  # Win/loss streak gold
    should_econ: bool  # Should we save for interest?
    should_roll: bool  # Should we spend gold rolling?
    should_level: bool  # Should we buy XP?


class BoardEvaluator:
    """Evaluates board strength and composition"""
    
    # Champion base power by cost (approximate)
    COST_POWER = {1: 10, 2: 20, 3: 35, 4: 55, 5: 80}
    
    # Star level multipliers
    STAR_MULTIPLIER = {1: 1.0, 2: 1.8, 3: 3.0}
    
    # Item value (approximate power boost)
    ITEM_VALUE = {
        "component": 5,
        "completed": 15,
        "radiant": 25,
        "artifact": 20,
    }
    
    # Trait tier bonuses
    TRAIT_TIER_BONUS = {
        "bronze": 5,
        "silver": 12,
        "gold": 25,
        "chromatic": 40,
    }
    
    def __init__(self, tft_data_path: str = None):
        """
        Initialize evaluator with TFT data
        
        Args:
            tft_data_path: Path to tft_data.json with champion/trait info
        """
        self.champions: Dict[str, ChampionTier] = {}
        self.traits: Dict[str, TraitBonus] = {}
        
        if tft_data_path is None:
            tft_data_path = Path(__file__).parent.parent / "tft_data.json"
        
        self._load_tft_data(tft_data_path)
    
    def _load_tft_data(self, path: str):
        """Load champion and trait data"""
        path = Path(path)
        if not path.exists():
            print(f"Warning: TFT data not found at {path}")
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Load champions
            for champ in data.get('champions', []):
                name = champ.get('name', champ.get('apiName', ''))
                cost = champ.get('cost', 1)
                traits = champ.get('traits', [])
                
                if name:
                    self.champions[name.lower()] = ChampionTier(name, cost, traits)
            
            # Load traits
            for trait in data.get('traits', []):
                name = trait.get('name', trait.get('apiName', ''))
                # Extract thresholds from effects
                thresholds = []
                for effect in trait.get('effects', []):
                    if 'minUnits' in effect:
                        thresholds.append(effect['minUnits'])
                
                if name and thresholds:
                    self.traits[name.lower()] = TraitBonus(name, sorted(thresholds))
            
            print(f"Loaded {len(self.champions)} champions, {len(self.traits)} traits")
            
        except Exception as e:
            print(f"Error loading TFT data: {e}")
    
    def get_champion_power(self, champion: Dict[str, Any]) -> float:
        """
        Calculate power of a single champion
        
        Args:
            champion: Dict with 'champion', 'star', 'items'
        """
        name = champion.get('champion', '').lower()
        star = champion.get('star', 1)
        items = champion.get('items', [])
        
        # Base power from cost
        champ_data = self.champions.get(name)
        cost = champ_data.cost if champ_data else 1
        base_power = self.COST_POWER.get(cost, 10)
        
        # Apply star multiplier
        power = base_power * self.STAR_MULTIPLIER.get(star, 1.0)
        
        # Add item value
        for item in items:
            if item:  # Non-empty item
                power += self.ITEM_VALUE.get("completed", 15)
        
        return power
    
    def evaluate_board(self, game_state: Dict[str, Any]) -> BoardStrength:
        """
        Evaluate total board strength
        
        Args:
            game_state: Full game state JSON
        """
        board = game_state.get('board', [])
        traits = game_state.get('traits', [])
        
        # Calculate unit score
        unit_score = 0
        item_count = 0
        
        for unit in board:
            unit_score += self.get_champion_power(unit)
            item_count += len(unit.get('items', []))
        
        # Normalize to 0-100 scale (assuming max ~8 units at full power)
        max_unit_power = 8 * 80 * 3.0  # 8 five-costs at 3-star
        unit_score = min(100, (unit_score / max_unit_power) * 100)
        
        # Calculate synergy score
        synergy_score = 0
        for trait in traits:
            tier = trait.get('tier', '').lower()
            bonus = self.TRAIT_TIER_BONUS.get(tier, 0)
            synergy_score += bonus
        
        # Normalize synergy (assume max ~5 active traits at gold)
        synergy_score = min(100, (synergy_score / 125) * 100)
        
        # Item score
        item_score = min(100, (item_count * 15 / 24) * 100)  # Max ~24 items
        
        # Positioning score (placeholder - would need spatial analysis)
        positioning_score = 50  # Default neutral
        
        # Total weighted score
        total = (
            unit_score * 0.4 +
            synergy_score * 0.25 +
            item_score * 0.2 +
            positioning_score * 0.15
        )
        
        return BoardStrength(
            total_score=total,
            unit_score=unit_score,
            synergy_score=synergy_score,
            item_score=item_score,
            positioning_score=positioning_score
        )
    
    def find_upgrades(self, game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find potential champion upgrades (pairs that can become 2-star)
        
        Returns list of champions that have pairs on board/bench
        """
        board = game_state.get('board', [])
        bench = game_state.get('bench', [])
        
        # Count champions
        counts: Dict[str, int] = {}
        for unit in board + bench:
            name = unit.get('champion', '').lower()
            star = unit.get('star', 1)
            if star == 1:  # Only count 1-stars for 2-star upgrades
                counts[name] = counts.get(name, 0) + 1
        
        # Find pairs (need 3 for upgrade)
        upgrades = []
        for name, count in counts.items():
            if count >= 2:
                upgrades.append({
                    'champion': name,
                    'count': count,
                    'need': 3 - count
                })
        
        return sorted(upgrades, key=lambda x: x['need'])


class EconomyEvaluator:
    """Evaluates economy and spending decisions"""
    
    # Interest thresholds
    INTEREST_THRESHOLDS = [10, 20, 30, 40, 50]
    
    # Level costs
    LEVEL_COSTS = {
        2: 2, 3: 2, 4: 6, 5: 10, 6: 20, 7: 36, 8: 56, 9: 80, 10: 100
    }
    
    # Stage-based guidelines
    STAGE_GUIDELINES = {
        "1": {"target_level": 3, "min_gold": 10},
        "2": {"target_level": 5, "min_gold": 30},
        "3": {"target_level": 6, "min_gold": 50},
        "4": {"target_level": 7, "min_gold": 50},
        "5": {"target_level": 8, "min_gold": 30},
        "6": {"target_level": 9, "min_gold": 0},
    }
    
    def evaluate(self, game_state: Dict[str, Any]) -> EconomyState:
        """
        Evaluate economy and recommend actions
        
        Args:
            game_state: Full game state JSON
        """
        player = game_state.get('player', {})
        stage_info = game_state.get('stage', {})
        
        gold = player.get('gold', 0)
        level = player.get('level', 1)
        health = player.get('health', 100)
        
        # Parse stage (e.g., "3-2" -> stage 3)
        stage_str = stage_info.get('current', '1-1')
        try:
            stage = int(stage_str.split('-')[0])
        except (ValueError, IndexError):
            stage = 1
        
        # Calculate interest
        interest = min(5, gold // 10)
        
        # Estimate streak bonus (would need history tracking)
        streak_bonus = 0
        
        # Get stage guidelines
        guidelines = self.STAGE_GUIDELINES.get(str(stage), {"target_level": level, "min_gold": 20})
        target_level = guidelines["target_level"]
        min_gold = guidelines["min_gold"]
        
        # Decision logic
        level_cost = self.LEVEL_COSTS.get(level + 1, 100)
        
        # Should we level?
        should_level = (
            level < target_level and
            gold >= level_cost + min_gold and
            gold >= 20  # Maintain some econ
        )
        
        # Should we roll?
        should_roll = (
            level >= target_level and
            gold > min_gold + 2 and
            health < 50  # Roll when low HP
        ) or (
            gold > 50 and  # Can afford to roll
            health < 30  # Desperate
        )
        
        # Should we econ?
        should_econ = (
            gold < 50 and
            health > 50 and
            not should_level
        )
        
        return EconomyState(
            gold=gold,
            interest=interest,
            streak_bonus=streak_bonus,
            should_econ=should_econ,
            should_roll=should_roll,
            should_level=should_level
        )
    
    def get_gold_after_interest(self, current_gold: int) -> int:
        """Calculate gold after round including interest"""
        interest = min(5, current_gold // 10)
        return current_gold + interest + 5  # +5 base gold
    
    def rounds_to_level(self, current_gold: int, level: int) -> int:
        """Estimate rounds needed to afford next level while maintaining interest"""
        cost = self.LEVEL_COSTS.get(level + 1, 100)
        target = cost + 50  # Want to stay at 50+ gold
        
        if current_gold >= target:
            return 0
        
        rounds = 0
        gold = current_gold
        while gold < target and rounds < 20:
            gold = self.get_gold_after_interest(gold)
            rounds += 1
        
        return rounds


def main():
    """Test evaluators"""
    print("=" * 50)
    print("TFT Evaluator Test")
    print("=" * 50)
    
    # Create evaluators
    board_eval = BoardEvaluator()
    econ_eval = EconomyEvaluator()
    
    # Test with sample game state
    sample_state = {
        "player": {
            "health": 65,
            "gold": 42,
            "level": 6
        },
        "stage": {"current": "3-5"},
        "board": [
            {"champion": "Veigar", "star": 2, "items": ["Rabadon"]},
            {"champion": "Lulu", "star": 2, "items": []},
            {"champion": "Zoe", "star": 1, "items": ["Blue Buff"]},
        ],
        "bench": [
            {"champion": "Lulu", "star": 1, "items": []},
        ],
        "traits": [
            {"name": "Sorcerer", "tier": "gold"},
            {"name": "Yordle", "tier": "silver"},
        ]
    }
    
    # Evaluate board
    board_strength = board_eval.evaluate_board(sample_state)
    print("\nBoard Evaluation:")
    print(f"  Total Score: {board_strength.total_score:.1f}")
    print(f"  Unit Power: {board_strength.unit_score:.1f}")
    print(f"  Synergies: {board_strength.synergy_score:.1f}")
    print(f"  Items: {board_strength.item_score:.1f}")
    print(f"  Tier: {board_strength.tier}")
    
    # Find upgrades
    upgrades = board_eval.find_upgrades(sample_state)
    print(f"\nUpgrade Opportunities: {upgrades}")
    
    # Evaluate economy
    econ = econ_eval.evaluate(sample_state)
    print("\nEconomy Evaluation:")
    print(f"  Gold: {econ.gold} (+{econ.interest} interest)")
    print(f"  Should Econ: {econ.should_econ}")
    print(f"  Should Roll: {econ.should_roll}")
    print(f"  Should Level: {econ.should_level}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
