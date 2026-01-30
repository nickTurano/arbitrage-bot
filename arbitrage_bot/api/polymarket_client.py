"""
Polymarket Client — stub. Full implementation pending.

Polymarket integration is preserved for future use when the platform
becomes available in the US market.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PolymarketClient:
    """
    Polymarket API client stub.

    Full implementation pending. Polymarket uses:
    - REST: https://clob.polymarket.com
    - WebSocket: wss://ws-subscriptions-clob.polymarket.com/ws/market
    - Gamma API: https://gamma-api.polymarket.com
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        logger.info("PolymarketClient initialized (stub — not yet active)")

    async def get_markets(self) -> List[Dict[str, Any]]:
        """Fetch active Polymarket markets. STUB."""
        logger.warning("PolymarketClient.get_markets() not yet implemented")
        return []

    async def get_orderbook(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch order book for a market. STUB."""
        logger.warning("PolymarketClient.get_orderbook() not yet implemented")
        return None

    async def place_order(self, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Place an order. STUB."""
        logger.warning("PolymarketClient.place_order() not yet implemented")
        return None
