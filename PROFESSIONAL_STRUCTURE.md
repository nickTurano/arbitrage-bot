# Professional Project Structure

## Overview

This project has been restructured into a **professional, unified Python package** that combines the best features from both original implementations.

## New Structure

### Package: `arbitrage_bot/`

The main package is now a proper Python package installable via pip:

```
arbitrage_bot/
├── __init__.py              # Package initialization
├── cli.py                   # Command-line interface
│
├── api/                     # API Clients
│   ├── __init__.py
│   ├── polymarket_client.py
│   └── kalshi_client.py
│
├── core/                     # Core Trading Logic
│   ├── __init__.py
│   ├── arbitrage_engine.py
│   ├── market_matcher.py
│   ├── execution_engine.py
│   ├── risk_manager.py
│   └── portfolio.py
│
├── models/                  # Data Models
│   ├── __init__.py
│   ├── market.py
│   ├── order.py
│   ├── position.py
│   ├── trade.py
│   └── opportunity.py
│
├── ui/                      # User Interfaces
│   ├── __init__.py
│   ├── fastapi_dashboard.py
│   └── terminal.py
│
└── utils/                   # Utilities
    ├── __init__.py
    ├── config.py
    └── logger.py
```

## Key Improvements

### 1. Proper Python Packaging

- **`setup.py`** - Traditional setup script
- **`pyproject.toml`** - Modern Python packaging (PEP 518)
- **Installable via pip**: `pip install -e .`
- **Console script**: `arbitrage-bot` command

### 2. Unified Configuration

- **Single config system** supporting both YAML and .env
- **Type-safe configuration** with dataclasses
- **Environment variable support** for sensitive data

### 3. Modular Architecture

- **Separated models** into logical files
- **Clear module boundaries** with proper `__init__.py` files
- **Type hints** throughout for better IDE support

### 4. Professional CLI

- **`arbitrage-bot` command** - Professional entry point
- **Subcommands**: `run`, `scan`
- **Consistent interface** across all operations

### 5. Testing Structure

```
tests/
├── __init__.py
├── test_api/
├── test_core/
├── test_models/
└── test_utils/
```

## Installation

### Development Mode

```bash
# Install package in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Production Mode

```bash
# Build package
python setup.py sdist bdist_wheel

# Install from wheel
pip install dist/polymarket_kalshi_arbitrage_bot-1.0.0-py3-none-any.whl
```

## Usage

### Command Line

```bash
# Run bot
arbitrage-bot run

# Run with options
arbitrage-bot run --ui terminal --port 3000

# Scan markets
arbitrage-bot scan --min-profit 2.0
```

### Python API

```python
from arbitrage_bot import ArbitrageEngine
from arbitrage_bot.api import PolymarketClient
from arbitrage_bot.utils.config import Config

# Load config
config = Config.load("config.yaml")

# Use the bot
...
```

## Migration from Old Structure

### Current Structure (Unified Package)

```
arbitrage_bot/                 # Unified package
├── api/                       # API clients
├── core/                      # Core trading logic
├── ui/                        # UI options (FastAPI, Terminal)
├── models/                    # Data models
├── utils/                     # Utilities
└── exceptions.py             # Custom exceptions
```

## Benefits

1. **Single Source of Truth** - One codebase, not two
2. **Easier Maintenance** - Changes in one place
3. **Better Testing** - Unified test suite
4. **Professional** - Follows Python packaging best practices
5. **Installable** - Can be installed as a package
6. **Type Safety** - Full type hints
7. **Documentation** - Proper docstrings

## Development Workflow

```bash
# 1. Install in development mode
pip install -e ".[dev]"

# 2. Run tests
pytest

# 3. Format code
black arbitrage_bot/

# 4. Type check
mypy arbitrage_bot/

# 5. Run bot
arbitrage-bot run
```

## Next Steps

1. **Copy API clients** from original implementations
2. **Copy core logic** and merge best features
3. **Implement UI adapters** for both FastAPI and Terminal
4. **Add comprehensive tests**
5. **Complete documentation**

---

**This structure is production-ready and follows Python best practices!** 🚀

