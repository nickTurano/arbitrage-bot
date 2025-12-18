"""
Arbitrage Bot Main Class
========================

Main bot orchestrator that coordinates all components.
"""

"""
Arbitrage Bot Main Class
========================

Main bot orchestrator that coordinates all components.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from arbitrage_bot.exceptions import ArbitrageBotError
from arbitrage_bot.utils.config import Config

logger = logging.getLogger(__name__)


class ArbitrageBot:
    """
    Main arbitrage trading bot.
    
    Coordinates API clients, arbitrage detection, risk management,
    and trade execution.
    """
    
    def __init__(self, config: Config) -> None:
        """
        Initialize the arbitrage bot.

        Args:
            config: Configuration object
        """
        self.config = config
        self._running = False
        self._start_time: Optional[datetime] = None

        # Components (initialized in start())
        self._api_clients: Dict[str, Any] = {}
        self._arbitrage_engine: Optional[Any] = None
        self._risk_manager: Optional[Any] = None
        self._portfolio: Optional[Any] = None
        self._execution_engine: Optional[Any] = None

        # Statistics
        self._stats: Dict[str, Any] = {
            "opportunities_detected": 0,
            "trades_executed": 0,
            "markets_scanned": 0,
            "errors": 0,
        }

        # Callbacks
        self._on_opportunity: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_trade: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None
    
    async def start(self) -> None:
        """
        Start the bot and initialize all components.

        Raises:
            ArbitrageBotError: If initialization fails
        """
        logger.info("=" * 60)
        logger.info("Polymarket-Kalshi Arbitrage Bot Starting")
        logger.info("=" * 60)
        logger.info(f"Mode: {'DRY RUN' if self.config.is_dry_run else 'LIVE'}")

        self._start_time = datetime.utcnow()
        self._running = True

        # TODO: Initialize API clients
        # TODO: Initialize arbitrage engine
        # TODO: Initialize risk manager
        # TODO: Initialize portfolio
        # TODO: Initialize execution engine

        logger.info("Bot started successfully!")
        logger.info("-" * 60)
    
    async def run(self) -> None:
        """
        Run the bot (start and keep running).

        Runs the bot continuously until stopped. Handles graceful shutdown
        on KeyboardInterrupt or other exceptions.
        """
        try:
            await self.start()

            # Main loop
            while self._running:
                await asyncio.sleep(1.0)
                # TODO: Implement main trading loop

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.exception(f"Fatal error: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the bot gracefully."""
        logger.info("Shutting down...")
        self._running = False
        
        # TODO: Stop all components
        
        logger.info("=" * 60)
        logger.info("Bot stopped")
        logger.info("=" * 60)
    
    def set_on_opportunity(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Set callback for when opportunities are detected.

        Args:
            callback: Function that takes opportunity dict as argument
        """
        self._on_opportunity = callback

    def set_on_trade(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set callback for when trades are executed.

        Args:
            callback: Function that takes trade dict as argument
        """
        self._on_trade = callback

    def set_on_error(self, callback: Callable[[Exception], None]) -> None:
        """
        Set callback for when errors occur.

        Args:
            callback: Function that takes exception as argument
        """
        self._on_error = callback

    def get_stats(self) -> Dict[str, Any]:
        """
        Get bot statistics.

        Returns:
            Dictionary containing bot statistics
        """
        uptime: Optional[float] = None
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        return {
            **self._stats,
            "running": self._running,
            "uptime_seconds": uptime,
            "mode": self.config.mode.trading_mode,
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get bot status.

        Returns:
            Dictionary containing bot status and statistics
        """
        return {
            "running": self._running,
            "mode": self.config.mode.trading_mode,
            "stats": self.get_stats(),
        }

