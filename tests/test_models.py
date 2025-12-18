"""
Tests for Data Models
"""

import pytest
from datetime import datetime
from arbitrage_bot.models.market import Market, OrderBook, TokenType, PriceLevel, OrderBookSide
from arbitrage_bot.models.order import Order, OrderSide, OrderStatus
from arbitrage_bot.models.position import Position
from arbitrage_bot.models.trade import Trade
from arbitrage_bot.models.opportunity import Opportunity, OpportunityType


class TestMarket:
    """Tests for Market model."""
    
    def test_market_creation(self):
        """Test creating a market."""
        market = Market(
            market_id="test_1",
            condition_id="0x123",
            question="Test question?",
            active=True,
        )
        assert market.market_id == "test_1"
        assert market.active is True
        assert market.closed is False


class TestOrderBook:
    """Tests for OrderBook model."""
    
    def test_orderbook_creation(self):
        """Test creating an order book."""
        ob = OrderBook(market_id="test_1")
        assert ob.market_id == "test_1"
        assert ob.yes.token_type == TokenType.YES
        assert ob.no.token_type == TokenType.NO
    
    def test_orderbook_properties(self):
        """Test order book properties."""
        ob = OrderBook(market_id="test_1")
        
        # Add some levels
        ob.yes.bids.levels = [
            PriceLevel(price=0.45, size=100),
            PriceLevel(price=0.44, size=200),
        ]
        ob.yes.asks.levels = [
            PriceLevel(price=0.46, size=150),
            PriceLevel(price=0.47, size=180),
        ]
        
        assert ob.best_bid_yes == 0.45
        assert ob.best_ask_yes == 0.46
        assert ob.yes.spread == 0.01


class TestOrder:
    """Tests for Order model."""
    
    def test_order_creation(self):
        """Test creating an order."""
        order = Order(
            order_id="order_1",
            market_id="test_1",
            token_type=TokenType.YES,
            side=OrderSide.BUY,
            price=0.45,
            size=100.0,
        )
        assert order.order_id == "order_1"
        assert order.notional == 45.0
        assert order.is_open is True
    
    def test_order_filled(self):
        """Test order fill status."""
        order = Order(
            order_id="order_1",
            market_id="test_1",
            token_type=TokenType.YES,
            side=OrderSide.BUY,
            price=0.45,
            size=100.0,
            filled_size=100.0,
            status=OrderStatus.FILLED,
        )
        assert order.is_filled is True
        assert order.remaining_size == 0.0


class TestPosition:
    """Tests for Position model."""
    
    def test_position_creation(self):
        """Test creating a position."""
        position = Position(
            market_id="test_1",
            token_type=TokenType.YES,
            size=100.0,
            avg_entry_price=0.45,
        )
        assert position.is_long is True
        assert position.notional == 45.0
    
    def test_unrealized_pnl(self):
        """Test unrealized PnL calculation."""
        position = Position(
            market_id="test_1",
            token_type=TokenType.YES,
            size=100.0,
            avg_entry_price=0.45,
        )
        # Price went up to 0.50
        pnl = position.unrealized_pnl(0.50)
        assert pnl == 5.0  # 100 * (0.50 - 0.45)


class TestOpportunity:
    """Tests for Opportunity model."""
    
    def test_opportunity_creation(self):
        """Test creating an opportunity."""
        opp = Opportunity(
            opportunity_id="opp_1",
            opportunity_type=OpportunityType.BUNDLE_LONG,
            market_id="test_1",
            edge=0.03,
        )
        assert opp.is_bundle_arb is True
        assert opp.is_market_making is False

