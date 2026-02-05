"""
Economy Analyzer - Gold management decisions

Analyzes:
- Current gold and interest
- When to level vs save
- When to roll vs eco
- Streak bonuses
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class EconomyAnalysis:
    """Result of economy analysis"""
    gold: int
    interest: int
    streak_gold: int
    total_income: int
    health: int
    level: int
    stage: str
    
    # Recommendations
    status: str  # "healthy", "stable", "critical", "desperate"
    should_save: bool
    should_level: bool
    should_roll: bool
    gold_to_next_interest: int
    
    # Reasoning
    reasoning: str


class EconomyAnalyzer:
    """Analyzes economy and recommends gold management"""
    
    # Interest thresholds
    INTEREST_THRESHOLDS = [10, 20, 30, 40, 50]
    
    # Standard level timings (stage: target level)
    LEVEL_TIMINGS = {
        "1": 3,
        "2": 5,
        "3": 6,
        "4": 7,
        "5": 8,
        "6": 9,
    }
    
    # Level costs (level: XP cost to reach it)
    LEVEL_COSTS = {
        4: 6,
        5: 10,
        6: 20,
        7: 36,
        8: 56,
        9: 80,
    }
    
    def analyze(self, game_state: Dict[str, Any]) -> EconomyAnalysis:
        """
        Analyze economy and return recommendations
        
        Args:
            game_state: Full game state dict
            
        Returns:
            EconomyAnalysis with recommendations and reasoning
        """
        player = game_state.get('player', {})
        stage_info = game_state.get('stage', {})
        
        gold = player.get('gold', 0)
        health = player.get('health', 100)
        level = player.get('level', 1)
        
        stage_str = stage_info.get('current', '1-1')
        try:
            stage_num = int(stage_str.split('-')[0])
        except:
            stage_num = 1
        
        # Calculate interest
        interest = min(5, gold // 10)
        
        # Calculate gold to next interest threshold
        current_threshold = (gold // 10) * 10
        next_threshold = current_threshold + 10
        gold_to_next = next_threshold - gold if next_threshold <= 50 else 0
        
        # Estimate streak bonus (would need history tracking)
        streak_gold = 0  # TODO: Track from game history
        
        # Total projected income
        total_income = 5 + interest + streak_gold
        
        # Determine health status
        if health <= 20:
            status = "desperate"
        elif health <= 40:
            status = "critical"
        elif health <= 60:
            status = "stable"
        else:
            status = "healthy"
        
        # Target level for current stage
        target_level = self.LEVEL_TIMINGS.get(str(stage_num), level)
        
        # Decision logic
        should_save = False
        should_level = False
        should_roll = False
        reasoning_parts = []
        
        # Check if we should level
        if level < target_level:
            level_cost = self.LEVEL_COSTS.get(level + 1, 100)
            if gold >= level_cost + 10:  # Keep some eco
                should_level = True
                reasoning_parts.append(f"Level to {level + 1} (standard timing for stage {stage_num})")
        
        # Check if we should save for interest
        if gold < 50 and gold_to_next <= 5 and status != "desperate":
            should_save = True
            reasoning_parts.append(f"Save {gold_to_next}g to hit {next_threshold}g interest threshold")
        
        # Check if we should roll
        if status == "desperate":
            should_roll = True
            reasoning_parts.append("HP critical - roll to stabilize board")
        elif status == "critical" and gold >= 30:
            should_roll = True
            reasoning_parts.append("Low HP - spend gold to find upgrades")
        elif level >= target_level and gold >= 50 and stage_num >= 4:
            should_roll = True
            reasoning_parts.append("At level cap with excess gold - roll for upgrades")
        
        # Override: don't save if desperate
        if status == "desperate":
            should_save = False
        
        # Default reasoning
        if not reasoning_parts:
            if should_save:
                reasoning_parts.append("Eco up - maintain gold for interest")
            else:
                reasoning_parts.append("Standard economy phase")
        
        return EconomyAnalysis(
            gold=gold,
            interest=interest,
            streak_gold=streak_gold,
            total_income=total_income,
            health=health,
            level=level,
            stage=stage_str,
            status=status,
            should_save=should_save,
            should_level=should_level,
            should_roll=should_roll,
            gold_to_next_interest=gold_to_next,
            reasoning=" | ".join(reasoning_parts)
        )
    
    def get_level_advice(self, current_level: int, gold: int, stage: str) -> Optional[str]:
        """Get specific leveling advice"""
        try:
            stage_num = int(stage.split('-')[0])
            round_num = int(stage.split('-')[1])
        except:
            return None
        
        # Specific level timing advice
        if stage == "2-1" and current_level < 4:
            return "Level to 4 at 2-1 (standard)"
        elif stage == "2-5" and current_level < 5:
            return "Level to 5 at 2-5 (standard)"
        elif stage == "3-2" and current_level < 6:
            return "Level to 6 at 3-2 (standard)"
        elif stage == "4-1" and current_level < 7:
            return "Level to 7 at 4-1 (standard)"
        elif stage == "4-5" and current_level < 8 and gold >= 50:
            return "Level to 8 at 4-5 (fast 8)"
        elif stage == "5-1" and current_level < 8:
            return "Level to 8 at 5-1 (standard)"
        
        return None
