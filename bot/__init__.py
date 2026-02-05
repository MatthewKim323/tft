"""
TFT Bot - AI Coach and Action Executor

Modules:
- coach.py: Main AI coach that analyzes game state and recommends actions
- decisions.py: Decision types and formatting
- actions.py: Mouse controller for executing bot actions
- analyzers/: Game state analysis (economy, board, shop)
"""

try:
    from .coach import TFTCoach
    from .decisions import CoachDecision, Decision, DecisionAction, DecisionPriority
    from .actions import ActionExecutor, BotRunner
    
    __all__ = [
        "TFTCoach",
        "CoachDecision",
        "Decision",
        "DecisionAction",
        "DecisionPriority",
        "ActionExecutor",
        "BotRunner",
    ]
except ImportError as e:
    print(f"Bot module import warning: {e}")
    __all__ = []
