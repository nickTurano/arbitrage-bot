"""
Pytest Configuration and Fixtures
"""

import pytest
from pathlib import Path
from arbitrage_bot.utils.config import Config


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    config = Config()
    config.mode.trading_mode = "dry_run"
    config.mode.data_mode = "simulation"
    config.trading.min_edge = 0.01
    config.risk.max_global_exposure = 1000.0
    return config


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "market_id": "test_market_1",
        "condition_id": "0x123",
        "question": "Will test event happen?",
        "active": True,
        "closed": False,
    }


@pytest.fixture
def sample_orderbook_data():
    """Sample order book data for testing."""
    return {
        "market_id": "test_market_1",
        "yes": {
            "bids": [{"price": 0.45, "size": 100}, {"price": 0.44, "size": 200}],
            "asks": [{"price": 0.46, "size": 150}, {"price": 0.47, "size": 180}],
        },
        "no": {
            "bids": [{"price": 0.54, "size": 100}, {"price": 0.53, "size": 200}],
            "asks": [{"price": 0.55, "size": 150}, {"price": 0.56, "size": 180}],
        },
    }

