"""
Market Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class TokenType(Enum):
    """Token type in a binary market."""
    YES = "yes"
    NO = "no"


@dataclass
class PriceLevel:
    """Single price level in an order book."""
    price: float
    size: float
    
    def __post_init__(self) -> None:
        self.price = float(self.price)
        self.size = float(self.size)


@dataclass
class OrderBookSide:
    """One side of an order book (bids or asks)."""

    levels: List[PriceLevel] = field(default_factory=list)
    
    @property
    def best_price(self) -> Optional[float]:
        """Get the best price on this side."""
        if not self.levels:
            return None
        return self.levels[0].price
    
    @property
    def best_size(self) -> Optional[float]:
        """Get the size at the best price."""
        if not self.levels:
            return None
        return self.levels[0].size
    
    def get_depth(self, levels: int = 5) -> List[PriceLevel]:
        """
        Get top N levels of depth.

        Args:
            levels: Number of levels to return

        Returns:
            List of price levels
        """
        return self.levels[:levels]
    
    def total_size(self, levels: int = 5) -> float:
        """Get total size in top N levels."""
        return sum(level.size for level in self.levels[:levels])


@dataclass
class TokenOrderBook:
    """Order book for a single token (YES or NO)."""
    token_type: TokenType
    bids: OrderBookSide = field(default_factory=OrderBookSide)
    asks: OrderBookSide = field(default_factory=OrderBookSide)
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def best_bid(self) -> Optional[float]:
        return self.bids.best_price
    
    @property
    def best_ask(self) -> Optional[float]:
        return self.asks.best_price
    
    @property
    def spread(self) -> Optional[float]:
        """Calculate bid-ask spread."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid
    
    @property
    def mid_price(self) -> Optional[float]:
        """Calculate mid price."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / 2


@dataclass
class OrderBook:
    """Complete order book for a market (YES and NO tokens)."""
    market_id: str
    yes: TokenOrderBook = field(default_factory=lambda: TokenOrderBook(TokenType.YES))
    no: TokenOrderBook = field(default_factory=lambda: TokenOrderBook(TokenType.NO))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def best_bid_yes(self) -> Optional[float]:
        return self.yes.best_bid
    
    @property
    def best_ask_yes(self) -> Optional[float]:
        return self.yes.best_ask
    
    @property
    def best_bid_no(self) -> Optional[float]:
        return self.no.best_bid
    
    @property
    def best_ask_no(self) -> Optional[float]:
        return self.no.best_ask
    
    @property
    def total_ask(self) -> Optional[float]:
        """Sum of best ask prices (YES + NO)."""
        if self.best_ask_yes is None or self.best_ask_no is None:
            return None
        return self.best_ask_yes + self.best_ask_no
    
    @property
    def total_bid(self) -> Optional[float]:
        """Sum of best bid prices (YES + NO)."""
        if self.best_bid_yes is None or self.best_bid_no is None:
            return None
        return self.best_bid_yes + self.best_bid_no


@dataclass
class Market:
    """Market information."""
    market_id: str
    condition_id: str
    question: str
    description: str = ""
    
    # Token IDs
    yes_token_id: str = ""
    no_token_id: str = ""
    
    # Market state
    active: bool = True
    closed: bool = False
    resolved: bool = False
    resolution: Optional[str] = None  # "YES", "NO", or None
    
    # Volume and liquidity
    volume_24h: float = 0.0
    liquidity: float = 0.0
    
    # Timestamps
    created_at: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Metadata
    category: str = ""
    tags: List[str] = field(default_factory=list)
