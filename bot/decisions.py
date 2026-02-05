"""
Decision Types for TFT AI Coach

Defines the output format for decisions that get streamed to the frontend.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import json


class DecisionAction(Enum):
    """Types of decisions the coach can make"""
    BUY = "BUY"
    SELL = "SELL"
    LEVEL = "LEVEL"
    REROLL = "REROLL"
    POSITION = "POSITION"
    EQUIP = "EQUIP"
    HOLD = "HOLD"


class DecisionPriority(Enum):
    """Priority levels for decisions"""
    CRITICAL = "critical"  # Must do immediately
    HIGH = "high"          # Should do soon
    MEDIUM = "medium"      # Good to do
    LOW = "low"           # Optional


@dataclass
class GameStateSummary:
    """Condensed game state for decision context"""
    stage: str
    health: int
    gold: int
    level: int
    board_size: int
    bench_size: int
    active_traits: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Analysis:
    """Analysis context for the decision"""
    economy_status: str  # "healthy", "stable", "critical", "desperate"
    board_strength: str  # "weak", "medium", "strong", "dominant"
    win_streak: int
    position_estimate: str  # "1st-2nd", "3rd-4th", etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Decision:
    """A single decision recommendation"""
    action: DecisionAction
    target: str  # e.g., "Veigar in slot 2", "Level 7", etc.
    priority: DecisionPriority
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "target": self.target,
            "priority": self.priority.value,
            "reasoning": self.reasoning
        }


@dataclass
class AlternativeAction:
    """Alternative action the player could take"""
    action: DecisionAction
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "reasoning": self.reasoning
        }


@dataclass
class CoachDecision:
    """
    Complete coach decision output
    
    This is what gets sent to the frontend dashboard
    """
    timestamp: str
    game_state_summary: GameStateSummary
    analysis: Analysis
    decision: Decision
    alternative_actions: List[AlternativeAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "game_state_summary": self.game_state_summary.to_dict(),
            "analysis": self.analysis.to_dict(),
            "decision": self.decision.to_dict(),
            "alternative_actions": [a.to_dict() for a in self.alternative_actions]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def create(cls, 
               game_state: Dict[str, Any],
               economy_status: str,
               board_strength: str,
               position_estimate: str,
               decision: Decision,
               alternatives: List[AlternativeAction] = None) -> 'CoachDecision':
        """
        Factory method to create a CoachDecision from raw data
        """
        player = game_state.get('player', {})
        stage_info = game_state.get('stage', {})
        board = game_state.get('board', [])
        bench = game_state.get('bench', [])
        traits = game_state.get('traits', [])
        
        # Format traits
        trait_strings = []
        for trait in traits:
            name = trait.get('name', '')
            count = trait.get('count', 0)
            tier = trait.get('tier', '')
            if name:
                trait_strings.append(f"{name} {count}")
        
        summary = GameStateSummary(
            stage=stage_info.get('current', '?'),
            health=player.get('health', 0),
            gold=player.get('gold', 0),
            level=player.get('level', 1),
            board_size=len(board),
            bench_size=len(bench),
            active_traits=trait_strings[:5]  # Top 5 traits
        )
        
        analysis = Analysis(
            economy_status=economy_status,
            board_strength=board_strength,
            win_streak=0,  # TODO: track streaks
            position_estimate=position_estimate
        )
        
        return cls(
            timestamp=datetime.now().isoformat(),
            game_state_summary=summary,
            analysis=analysis,
            decision=decision,
            alternative_actions=alternatives or []
        )


# Helper functions for creating common decisions

def buy_decision(champion: str, slot: int, reason: str, priority: DecisionPriority = DecisionPriority.HIGH) -> Decision:
    """Create a BUY decision"""
    return Decision(
        action=DecisionAction.BUY,
        target=f"{champion} in slot {slot + 1}",
        priority=priority,
        reasoning=reason
    )


def sell_decision(champion: str, reason: str, priority: DecisionPriority = DecisionPriority.MEDIUM) -> Decision:
    """Create a SELL decision"""
    return Decision(
        action=DecisionAction.SELL,
        target=champion,
        priority=priority,
        reasoning=reason
    )


def level_decision(to_level: int, reason: str, priority: DecisionPriority = DecisionPriority.HIGH) -> Decision:
    """Create a LEVEL decision"""
    return Decision(
        action=DecisionAction.LEVEL,
        target=f"Level {to_level}",
        priority=priority,
        reasoning=reason
    )


def reroll_decision(reason: str, priority: DecisionPriority = DecisionPriority.MEDIUM) -> Decision:
    """Create a REROLL decision"""
    return Decision(
        action=DecisionAction.REROLL,
        target="Refresh shop",
        priority=priority,
        reasoning=reason
    )


def hold_decision(reason: str) -> Decision:
    """Create a HOLD (do nothing) decision"""
    return Decision(
        action=DecisionAction.HOLD,
        target="Save gold",
        priority=DecisionPriority.LOW,
        reasoning=reason
    )
