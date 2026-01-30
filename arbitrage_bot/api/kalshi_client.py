"""
Kalshi Client — stub with API key support.

Kalshi integration is preserved and will be activated once
full implementation is complete. API key is loaded from config
or KALSHI_API_KEY environment variable.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2"


class KalshiClient:
    """
    Kalshi API client stub.

    Full implementation pending. Kalshi uses:
    - REST API: https://api.elections.kalshi.com/trade-api/v2
    - Auth: API key + secret (RSA signing)

    The API key is loaded from config or the KALSHI_API_KEY env var.
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        self.api_key: Optional[str] = None

        # Try to load API key
        if config and hasattr(config, "api") and hasattr(config.api, "kalshi_api_key"):
            self.api_key = config.api.kalshi_api_key
        if not self.api_key:
            self.api_key = os.environ.get("KALSHI_API_KEY")

        if self.api_key:
            logger.info("KalshiClient initialized with API key (stub — not yet active)")
        else:
            logger.info("KalshiClient initialized (stub — no API key found)")

    async def get_markets(self) -> List[Dict[str, Any]]:
        """Fetch active Kalshi markets. STUB."""
        logger.warning("KalshiClient.get_markets() not yet implemented")
        return []

    async def get_orderbook(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch order book for a market. STUB."""
        logger.warning("KalshiClient.get_orderbook() not yet implemented")
        return None

    async def place_order(self, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Place an order. STUB."""
        logger.warning("KalshiClient.place_order() not yet implemented")
        return None
