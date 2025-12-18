"""
Position Models
"""

from dataclasses import dataclass

from arbitrage_bot.models.market import TokenType


@dataclass
class Position:
    """Position in a market."""
    market_id: str
    token_type: TokenType
    size: float  # Positive for long, negative for short
    avg_entry_price: float = 0.0
    realized_pnl: float = 0.0
    
    @property
    def notional(self) -> float:
        """Calculate position notional value."""
        return abs(self.size) * self.avg_entry_price
    
    @property
    def is_long(self) -> bool:
        return self.size > 0
    
    @property
    def is_short(self) -> bool:
        return self.size < 0
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL at current price."""
        if self.size == 0:
            return 0.0
        return self.size * (current_price - self.avg_entry_price)

