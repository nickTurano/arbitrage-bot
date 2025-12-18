"""
Custom Exceptions for Arbitrage Bot
====================================

Professional exception hierarchy for better error handling.
"""


class ArbitrageBotError(Exception):
    """Base exception for all arbitrage bot errors."""
    pass


class ConfigurationError(ArbitrageBotError):
    """Raised when there's a configuration error."""
    pass


class APIError(ArbitrageBotError):
    """Base exception for API-related errors."""
    pass


class PolymarketAPIError(APIError):
    """Raised when Polymarket API returns an error."""
    pass


class KalshiAPIError(APIError):
    """Raised when Kalshi API returns an error."""
    pass


class ConnectionError(APIError):
    """Raised when unable to connect to API."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass


class TradingError(ArbitrageBotError):
    """Base exception for trading-related errors."""
    pass


class InsufficientFundsError(TradingError):
    """Raised when there are insufficient funds for a trade."""
    pass


class InvalidOrderError(TradingError):
    """Raised when an order is invalid."""
    pass


class RiskLimitExceededError(TradingError):
    """Raised when a risk limit is exceeded."""
    pass


class MarketNotFoundError(ArbitrageBotError):
    """Raised when a market is not found."""
    pass


class OrderBookError(ArbitrageBotError):
    """Raised when there's an error with order book data."""
    pass


class MatchingError(ArbitrageBotError):
    """Raised when market matching fails."""
    pass

