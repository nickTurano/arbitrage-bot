"""
Order Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from arbitrage_bot.models.market import TokenType


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


@dataclass
class Order:
    """Trading order."""
    order_id: str
    market_id: str
    token_type: TokenType
    side: OrderSide
    price: float
    size: float
    filled_size: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    
    # Metadata
    strategy_tag: str = ""  # e.g., "bundle_arb", "mm"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def remaining_size(self) -> float:
        """Get unfilled size."""
        return self.size - self.filled_size
    
    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING)
    
    @property
    def notional(self) -> float:
        """Calculate notional value."""
        return self.price * self.size

