# Development Guide

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd Polymarket-Kalshi-Arbitrage-Bot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
make install-dev
```

## Project Structure

```
arbitrage_bot/
├── __init__.py           # Package initialization
├── cli.py                # Command-line interface
├── exceptions.py         # Custom exceptions
│
├── api/                  # API Clients
│   ├── __init__.py
│   ├── polymarket_client.py
│   └── kalshi_client.py
│
├── core/                 # Core Trading Logic
│   ├── __init__.py
│   ├── arbitrage_engine.py
│   ├── market_matcher.py
│   ├── execution_engine.py
│   ├── risk_manager.py
│   └── portfolio.py
│
├── models/               # Data Models
│   ├── __init__.py
│   ├── market.py
│   ├── order.py
│   ├── position.py
│   ├── trade.py
│   └── opportunity.py
│
├── ui/                   # User Interfaces
│   ├── __init__.py
│   ├── fastapi_dashboard.py
│   └── terminal.py
│
└── utils/                # Utilities
    ├── __init__.py
    ├── config.py
    ├── logger.py
    └── validators.py
```

## Development Workflow

### 1. Make Changes

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make your changes
# ...

# Format code
make format

# Run checks
make check
```

### 2. Write Tests

```bash
# Write tests in tests/
pytest tests/test_my_feature.py -v

# Run all tests
make test
```

### 3. Commit

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: Add new feature"

# Push
git push origin feature/my-feature
```

### 4. Create Pull Request

- Open a PR on GitHub
- Ensure all checks pass
- Request review

## Code Standards

### Type Hints

Always use type hints:

```python
from typing import Optional, List
from arbitrage_bot.models import Market

def get_markets(limit: int = 10) -> List[Market]:
    """Get markets."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_profit(price: float, size: float) -> float:
    """Calculate profit from price and size.
    
    Args:
        price: Price per unit
        size: Number of units
        
    Returns:
        Total profit
        
    Raises:
        ValueError: If price or size is negative
    """
    if price < 0 or size < 0:
        raise ValueError("Price and size must be non-negative")
    return price * size
```

### Error Handling

Use custom exceptions:

```python
from arbitrage_bot.exceptions import InvalidOrderError

if price <= 0:
    raise InvalidOrderError(f"Invalid price: {price}")
```

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing order", extra={"order_id": order_id})
logger.error("Failed to process", exc_info=True)
```

## Testing

### Writing Tests

```python
import pytest
from arbitrage_bot.models import Market

def test_market_creation():
    """Test creating a market."""
    market = Market(
        market_id="test_1",
        condition_id="0x123",
        question="Test?",
    )
    assert market.market_id == "test_1"
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_models.py

# With coverage
pytest --cov=arbitrage_bot --cov-report=html
```

## Common Tasks

```bash
# Format code
make format

# Lint
make lint

# Type check
make type-check

# Run all checks
make check

# Run bot
make run

# Scan markets
make scan

# Clean build artifacts
make clean
```

## Debugging

### Enable Debug Logging

```bash
arbitrage-bot run --verbose
```

### Use Python Debugger

```python
import pdb; pdb.set_trace()
```

## Building

```bash
# Build distribution
make build

# Install from wheel
pip install dist/polymarket_kalshi_arbitrage_bot-1.0.0-py3-none-any.whl
```

## Release Process

1. Update version in `pyproject.toml` and `setup.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Build and publish: `make build && twine upload dist/*`

---

Happy coding! 🚀

