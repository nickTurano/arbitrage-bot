"""
Polymarket-Kalshi Arbitrage Bot
================================

A professional arbitrage trading bot for Polymarket and Kalshi prediction markets.

This package provides:
- Cross-platform arbitrage detection
- Market matching algorithms
- Risk management
- Trade execution
- Multiple UI options
"""

__version__ = "1.0.0"
__author__ = "Polymarket-Kalshi Arbitrage Bot Contributors"

from arbitrage_bot.bot import ArbitrageBot
from arbitrage_bot.scanner import MarketScanner

# Core components (will be available when implemented)
try:
    from arbitrage_bot.core.arbitrage_engine import ArbitrageEngine
    from arbitrage_bot.core.market_matcher import MarketMatcher
    from arbitrage_bot.core.execution_engine import ExecutionEngine
    from arbitrage_bot.core.risk_manager import RiskManager
    from arbitrage_bot.core.portfolio import Portfolio
except ImportError:
    # Components not yet implemented
    ArbitrageEngine = None
    MarketMatcher = None
    ExecutionEngine = None
    RiskManager = None
    Portfolio = None

__all__ = [
    "ArbitrageBot",
    "MarketScanner",
    "ArbitrageEngine",
    "MarketMatcher",
    "ExecutionEngine",
    "RiskManager",
    "Portfolio",
]

