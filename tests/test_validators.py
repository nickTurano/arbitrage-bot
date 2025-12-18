"""
Tests for Validators
"""

import pytest
from arbitrage_bot.utils.validators import (
    validate_config,
    validate_order,
    validate_price,
    validate_percentage,
)
from arbitrage_bot.exceptions import ConfigurationError, InvalidOrderError
from arbitrage_bot.utils.config import Config
from arbitrage_bot.models.market import TokenType
from arbitrage_bot.models.order import OrderSide


class TestConfigValidator:
    """Tests for configuration validation."""
    
    def test_valid_config(self, test_config):
        """Test validating a valid config."""
        validate_config(test_config)  # Should not raise
    
    def test_invalid_trading_mode(self):
        """Test invalid trading mode."""
        config = Config()
        config.mode.trading_mode = "invalid"
        
        with pytest.raises(ConfigurationError):
            validate_config(config)
    
    def test_negative_min_edge(self):
        """Test negative min_edge."""
        config = Config()
        config.trading.min_edge = -0.01
        
        with pytest.raises(ConfigurationError):
            validate_config(config)


class TestOrderValidator:
    """Tests for order validation."""
    
    def test_valid_order(self):
        """Test validating a valid order."""
        validate_order(
            market_id="test_1",
            token_type="yes",
            side="buy",
            price=0.45,
            size=100.0,
        )  # Should not raise
    
    def test_invalid_price(self):
        """Test invalid price."""
        with pytest.raises(InvalidOrderError):
            validate_order(
                market_id="test_1",
                token_type="yes",
                side="buy",
                price=-0.45,
                size=100.0,
            )
    
    def test_price_too_high(self):
        """Test price > 1.0."""
        with pytest.raises(InvalidOrderError):
            validate_order(
                market_id="test_1",
                token_type="yes",
                side="buy",
                price=1.5,
                size=100.0,
            )
    
    def test_invalid_size(self):
        """Test invalid size."""
        with pytest.raises(InvalidOrderError):
            validate_order(
                market_id="test_1",
                token_type="yes",
                side="buy",
                price=0.45,
                size=-100.0,
            )


class TestPriceValidator:
    """Tests for price validation."""
    
    def test_valid_price(self):
        """Test validating a valid price."""
        validate_price(0.45)  # Should not raise
    
    def test_negative_price(self):
        """Test negative price."""
        with pytest.raises(ValueError):
            validate_price(-0.45)
    
    def test_price_too_high(self):
        """Test price > 1.0."""
        with pytest.raises(ValueError):
            validate_price(1.5)


class TestPercentageValidator:
    """Tests for percentage validation."""
    
    def test_valid_percentage(self):
        """Test validating a valid percentage."""
        validate_percentage(50.0)  # Should not raise
    
    def test_negative_percentage(self):
        """Test negative percentage."""
        with pytest.raises(ValueError):
            validate_percentage(-10.0)
    
    def test_percentage_too_high(self):
        """Test percentage > 100."""
        with pytest.raises(ValueError):
            validate_percentage(150.0)

