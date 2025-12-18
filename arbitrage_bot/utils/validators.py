"""
Input Validators
===============

Professional validation functions for configuration and inputs.
"""

from typing import Any, Optional

from arbitrage_bot.exceptions import ConfigurationError, InvalidOrderError


def validate_config(config: Any) -> None:
    """
    Validate configuration object.

    Args:
        config: Configuration object to validate

    Raises:
        ConfigurationError: If configuration is invalid
    """
    if not config:
        raise ConfigurationError("Configuration is required")

    # Validate trading mode
    if hasattr(config, "mode"):
        if config.mode.trading_mode not in ("dry_run", "live"):
            raise ConfigurationError(
                f"Invalid trading_mode: {config.mode.trading_mode}. "
                "Must be 'dry_run' or 'live'"
            )

    # Validate min_edge
    if hasattr(config, "trading"):
        if config.trading.min_edge < 0:
            raise ConfigurationError("min_edge must be non-negative")
        if config.trading.min_edge > 1:
            raise ConfigurationError("min_edge must be <= 1.0 (100%)")

    # Validate risk limits
    if hasattr(config, "risk"):
        if config.risk.max_global_exposure <= 0:
            raise ConfigurationError("max_global_exposure must be positive")
        if config.risk.max_position_per_market <= 0:
            raise ConfigurationError("max_position_per_market must be positive")


def validate_order(
    market_id: str,
    token_type: Any,
    side: Any,
    price: float,
    size: float,
) -> None:
    """
    Validate order parameters.

    Args:
        market_id: Market identifier
        token_type: Token type (YES or NO)
        side: Order side (BUY or SELL)
        price: Order price
        size: Order size

    Raises:
        InvalidOrderError: If order is invalid
    """
    if not market_id:
        raise InvalidOrderError("market_id is required")

    if price <= 0:
        raise InvalidOrderError(f"Invalid price: {price}. Must be positive")

    if price > 1.0:
        raise InvalidOrderError(f"Invalid price: {price}. Must be <= 1.0")

    if size <= 0:
        raise InvalidOrderError(f"Invalid size: {size}. Must be positive")

    if token_type not in ("yes", "no"):
        raise InvalidOrderError(f"Invalid token_type: {token_type}")

    if side not in ("buy", "sell"):
        raise InvalidOrderError(f"Invalid side: {side}")


def validate_price(price: float, name: str = "price") -> None:
    """
    Validate a price value.

    Args:
        price: Price to validate
        name: Name of the price field for error messages

    Raises:
        ValueError: If price is invalid
    """
    if not isinstance(price, (int, float)):
        raise ValueError(f"{name} must be a number")

    if price < 0:
        raise ValueError(f"{name} must be non-negative")

    if price > 1.0:
        raise ValueError(f"{name} must be <= 1.0")


def validate_percentage(value: float, name: str = "percentage") -> None:
    """
    Validate a percentage value (0-100).

    Args:
        value: Percentage to validate
        name: Name of the field for error messages

    Raises:
        ValueError: If percentage is invalid
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    if value < 0:
        raise ValueError(f"{name} must be non-negative")

    if value > 100:
        raise ValueError(f"{name} must be <= 100")

