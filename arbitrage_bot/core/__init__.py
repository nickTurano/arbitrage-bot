"""
Core trading logic: arbitrage detection and budget management.
"""

from arbitrage_bot.core.arb_engine import ArbEngine, ArbOpportunity, ArbLeg
from arbitrage_bot.core.budget_tracker import BudgetTracker, BudgetState

__all__ = ["ArbEngine", "ArbOpportunity", "ArbLeg", "BudgetTracker", "BudgetState"]
