"""
Opportunity Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OpportunityType(Enum):
    """Type of trading opportunity detected."""
    BUNDLE_LONG = "bundle_long"    # Buy YES + NO when sum < 1
    BUNDLE_SHORT = "bundle_short"  # Sell YES + NO when sum > 1
    MM_BID = "mm_bid"              # Market-making bid placement
    MM_ASK = "mm_ask"              # Market-making ask placement
    CROSS_PLATFORM = "cross_platform"  # Cross-platform arbitrage


@dataclass
class Opportunity:
    """Trading opportunity detected by the arbitrage engine."""
    opportunity_id: str
    opportunity_type: OpportunityType
    market_id: str
    edge: float  # Expected profit margin
    
    # Pricing snapshot
    best_bid_yes: Optional[float] = None
    best_ask_yes: Optional[float] = None
    best_bid_no: Optional[float] = None
    best_ask_no: Optional[float] = None
    
    # Sizing
    suggested_size: float = 0.0
    max_size: float = 0.0  # Limited by liquidity
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    acted_upon: bool = False
    
    @property
    def is_bundle_arb(self) -> bool:
        return self.opportunity_type in (OpportunityType.BUNDLE_LONG, OpportunityType.BUNDLE_SHORT)
    
    @property
    def is_market_making(self) -> bool:
        return self.opportunity_type in (OpportunityType.MM_BID, OpportunityType.MM_ASK)
    
    @property
    def is_cross_platform(self) -> bool:
        return self.opportunity_type == OpportunityType.CROSS_PLATFORM

