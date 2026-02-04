"""
TFT Bot - Decision Engine and Action Executor

This package contains the bot brain that:
1. Parses game state JSON
2. Evaluates board strength and economy
3. Selects optimal strategy
4. Generates prioritized actions
"""

try:
    from .decision_engine import DecisionEngine, Action, ActionType
    from .evaluator import BoardEvaluator, EconomyEvaluator
    from .actions import ActionExecutor, BotRunner
    
    __all__ = [
        "DecisionEngine",
        "Action",
        "ActionType",
        "BoardEvaluator",
        "EconomyEvaluator",
        "ActionExecutor",
        "BotRunner",
    ]
except ImportError as e:
    print(f"Bot module import warning: {e}")
    __all__ = []
