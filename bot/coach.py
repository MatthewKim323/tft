"""
TFT AI Coach - Decision Engine

The brain that analyzes game state and outputs recommendations.
Unlike the bot executor, this only suggests - you execute manually.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .analyzers import EconomyAnalyzer, BoardAnalyzer, ShopAnalyzer
from .decisions import (
    CoachDecision, Decision, AlternativeAction,
    DecisionAction, DecisionPriority,
    buy_decision, sell_decision, level_decision, reroll_decision, hold_decision
)


class TFTCoach:
    """
    AI Coach that analyzes game state and provides recommendations
    
    Usage:
        coach = TFTCoach()
        decision = coach.analyze(game_state)
        print(decision.to_json())  # Send to frontend
    """
    
    def __init__(self, tft_data_path: str = None):
        self.economy_analyzer = EconomyAnalyzer()
        self.board_analyzer = BoardAnalyzer(tft_data_path)
        self.shop_analyzer = ShopAnalyzer(tft_data_path)
        
        # Track decision history
        self.decision_history: List[CoachDecision] = []
    
    def analyze(self, game_state: Dict[str, Any]) -> CoachDecision:
        """
        Analyze game state and return coach decision
        
        Args:
            game_state: Full game state dict from state_builder
            
        Returns:
            CoachDecision ready to send to frontend
        """
        # Run all analyzers
        economy = self.economy_analyzer.analyze(game_state)
        board = self.board_analyzer.analyze(game_state)
        shop = self.shop_analyzer.analyze(game_state)
        
        # Estimate lobby position
        position = self.board_analyzer.estimate_lobby_position(
            economy.health, 
            board.total_power
        )
        
        # Generate main decision and alternatives
        decision, alternatives = self._generate_decisions(
            game_state, economy, board, shop
        )
        
        # Create coach decision
        coach_decision = CoachDecision.create(
            game_state=game_state,
            economy_status=economy.status,
            board_strength=board.power_tier,
            position_estimate=position,
            decision=decision,
            alternatives=alternatives
        )
        
        # Track history
        self.decision_history.append(coach_decision)
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)
        
        return coach_decision
    
    def _generate_decisions(self, 
                           game_state: Dict[str, Any],
                           economy,  # EconomyAnalysis
                           board,    # BoardAnalysis
                           shop      # ShopAnalysis
                           ) -> tuple[Decision, List[AlternativeAction]]:
        """
        Generate main decision and alternatives based on analysis
        
        Priority order:
        1. Buy if it completes an upgrade (MUST BUY)
        2. Level if at standard timing
        3. Buy pairs for future upgrades
        4. Reroll if critical HP
        5. Hold/eco if nothing valuable
        """
        alternatives: List[AlternativeAction] = []
        player = game_state.get('player', {})
        gold = player.get('gold', 0)
        
        # Check for must-buy upgrades
        if shop.best_buy and shop.best_buy.priority == "must_buy":
            main_decision = buy_decision(
                champion=shop.best_buy.champion,
                slot=shop.best_buy.slot,
                reason=shop.best_buy.reason,
                priority=DecisionPriority.CRITICAL
            )
            
            # Add alternatives
            if economy.should_level:
                alternatives.append(AlternativeAction(
                    action=DecisionAction.LEVEL,
                    reasoning=f"Could level to {economy.level + 1} instead"
                ))
            
            alternatives.append(AlternativeAction(
                action=DecisionAction.HOLD,
                reasoning=f"Save for {economy.gold_to_next_interest}g more interest"
            ))
            
            return main_decision, alternatives
        
        # Check for standard level timing
        if economy.should_level:
            main_decision = level_decision(
                to_level=economy.level + 1,
                reason=economy.reasoning,
                priority=DecisionPriority.HIGH
            )
            
            if shop.best_buy:
                alternatives.append(AlternativeAction(
                    action=DecisionAction.BUY,
                    reasoning=f"Buy {shop.best_buy.champion} - {shop.best_buy.reason}"
                ))
            
            alternatives.append(AlternativeAction(
                action=DecisionAction.HOLD,
                reasoning="Save gold for later power spike"
            ))
            
            return main_decision, alternatives
        
        # Check for high-value buys
        if shop.best_buy and shop.best_buy.priority in ["high", "medium"]:
            main_decision = buy_decision(
                champion=shop.best_buy.champion,
                slot=shop.best_buy.slot,
                reason=shop.best_buy.reason,
                priority=DecisionPriority.MEDIUM if shop.best_buy.priority == "medium" else DecisionPriority.HIGH
            )
            
            alternatives.append(AlternativeAction(
                action=DecisionAction.HOLD,
                reasoning=f"Eco to {((gold // 10) + 1) * 10}g for +1 interest"
            ))
            
            if economy.should_roll:
                alternatives.append(AlternativeAction(
                    action=DecisionAction.REROLL,
                    reasoning="Reroll to find more upgrades"
                ))
            
            return main_decision, alternatives
        
        # Check if should roll
        if economy.should_roll:
            should_roll, roll_reason = self.shop_analyzer.should_reroll(
                game_state, economy.status
            )
            
            if should_roll:
                main_decision = reroll_decision(
                    reason=roll_reason,
                    priority=DecisionPriority.HIGH if economy.status in ["desperate", "critical"] else DecisionPriority.MEDIUM
                )
                
                alternatives.append(AlternativeAction(
                    action=DecisionAction.HOLD,
                    reasoning="Save gold to maintain interest"
                ))
                
                if economy.should_level:
                    alternatives.append(AlternativeAction(
                        action=DecisionAction.LEVEL,
                        reasoning=f"Level to {economy.level + 1} for higher tier units"
                    ))
                
                return main_decision, alternatives
        
        # Check for sellable units (bench management)
        if board.sellable_units and len(game_state.get('bench', [])) >= 7:
            sell_target = board.sellable_units[0]
            main_decision = sell_decision(
                champion=sell_target.title(),
                reason=f"Clear bench space - {sell_target} has no pair",
                priority=DecisionPriority.LOW
            )
            
            alternatives.append(AlternativeAction(
                action=DecisionAction.HOLD,
                reasoning="Keep for potential pivot"
            ))
            
            return main_decision, alternatives
        
        # Default: HOLD and eco
        hold_reason = "Save gold - "
        if economy.gold_to_next_interest > 0 and economy.gold_to_next_interest <= 5:
            hold_reason += f"{economy.gold_to_next_interest}g to next interest threshold"
        elif gold >= 50:
            hold_reason += "at max interest, wait for good shop"
        else:
            hold_reason += f"building economy ({gold}g → 50g)"
        
        main_decision = hold_decision(hold_reason)
        
        # Always suggest alternatives
        if gold >= 2:
            alternatives.append(AlternativeAction(
                action=DecisionAction.REROLL,
                reasoning="Could reroll to find upgrades"
            ))
        
        if economy.level < 9:
            alternatives.append(AlternativeAction(
                action=DecisionAction.LEVEL,
                reasoning=f"Could level to {economy.level + 1}"
            ))
        
        return main_decision, alternatives
    
    def get_quick_summary(self, game_state: Dict[str, Any]) -> str:
        """Get a one-line summary of what to do"""
        decision = self.analyze(game_state)
        
        action = decision.decision.action.value
        target = decision.decision.target
        priority = decision.decision.priority.value.upper()
        
        return f"[{priority}] {action}: {target}"
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decision history"""
        return [d.to_dict() for d in self.decision_history[-limit:]]


def main():
    """Test the coach"""
    print("=" * 60)
    print("TFT AI Coach Test")
    print("=" * 60)
    
    coach = TFTCoach()
    
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
    
    # Get coach decision
    decision = coach.analyze(sample_state)
    
    print("\n📊 Game State Summary:")
    print(f"  Stage: {decision.game_state_summary.stage}")
    print(f"  HP: {decision.game_state_summary.health}")
    print(f"  Gold: {decision.game_state_summary.gold}")
    print(f"  Level: {decision.game_state_summary.level}")
    print(f"  Traits: {', '.join(decision.game_state_summary.active_traits)}")
    
    print("\n📈 Analysis:")
    print(f"  Economy: {decision.analysis.economy_status}")
    print(f"  Board: {decision.analysis.board_strength}")
    print(f"  Position: {decision.analysis.position_estimate}")
    
    print("\n🎯 RECOMMENDATION:")
    print(f"  [{decision.decision.priority.value.upper()}] {decision.decision.action.value}")
    print(f"  Target: {decision.decision.target}")
    print(f"  Reason: {decision.decision.reasoning}")
    
    print("\n🔄 Alternatives:")
    for alt in decision.alternative_actions:
        print(f"  - {alt.action.value}: {alt.reasoning}")
    
    print("\n📤 JSON Output:")
    print(decision.to_json())
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
