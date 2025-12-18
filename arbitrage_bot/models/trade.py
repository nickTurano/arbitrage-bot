"""
Trade Models
"""

from dataclasses import dataclass, field
from datetime import datetime

from arbitrage_bot.models.market import TokenType
from arbitrage_bot.models.order import OrderSide


@dataclass
class Trade:
    """Executed trade."""
    trade_id: str
    order_id: str
    market_id: str
    token_type: TokenType
    side: OrderSide
    price: float
    size: float
    fee: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def notional(self) -> float:
        """Calculate trade notional."""
        return self.price * self.size
    
    @property
    def net_cost(self) -> float:
        """Calculate net cost including fees."""
        return self.notional + self.fee

