# Polymarket-Kalshi Arbitrage Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)
![Platforms](https://img.shields.io/badge/Platforms-Polymarket%20%7C%20Kalshi-orange.svg)

**Professional arbitrage trading bot for Polymarket and Kalshi prediction markets**

A production-ready, unified Python package for cross-platform arbitrage trading.

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## Cᴏɴᴛᴀᴄᴛ ᴍᴇ Oɴ ʜᴇʀᴇ: 👋 ##

Telegram: https://t.me/opensea712

<div style={{display : flex ; justify-content : space-evenly}}> 
    <a href="https://t.me/opensea712" target="_blank"><img alt="Telegram"
        src="https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white"/></a>
    <a href="https://discordapp.com/users/343286332446998530" target="_blank"><img alt="Discord"
        src="https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white"/></a>
</div>

## 🎯 Features

### Core Capabilities

- **🔀 Cross-Platform Arbitrage** - Detects price differences between Polymarket and Kalshi
- **🔍 Bundle Arbitrage Detection** - Identifies when YES + NO prices don't sum to ~$1.00
- **📊 Market Making** - Captures spreads by placing competitive bid/ask orders  
- **🛡️ Risk Management** - Position limits, loss limits, kill switch
- **🤖 Intelligent Market Matching** - Automatically matches similar predictions using text similarity, sports team matching, and entity extraction
- **💰 Fee Accounting** - Realistic edge calculations including fees & gas costs

### Professional Architecture

- **📦 Proper Python Package** - Installable via pip with `setup.py` and `pyproject.toml`
- **🏗️ Modular Design** - Clean separation of concerns with dedicated modules
- **⚡ Async/Await** - Built with `asyncio` for maximum performance
- **🧪 Comprehensive Testing** - Unit tests with pytest
- **📝 Type Hints** - Full type annotations for better IDE support
- **🔧 Configuration Management** - Unified config system supporting YAML and .env

### UI Options

- **📈 FastAPI Dashboard** - Production-ready REST API and web dashboard
- **🖥️ Terminal UI** - Beautiful terminal-style interface with WebSocket updates
- **🤖 Headless Mode** - Run without UI for automated trading

---

## 📦 Installation

### From Source

```bash
# Clone repository
git clone <your-repo-url>
cd Polymarket-Kalshi-Arbitrage-Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Development Installation

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

---

## 🚀 Quick Start

### 1. Configure

Create a configuration file (`config.yaml`):

```yaml
api:
  api_key: "YOUR_API_KEY"  # Or use environment variables
  private_key: "YOUR_PRIVATE_KEY"

mode:
  trading_mode: "dry_run"  # Always start here!
  data_mode: "real"
  cross_platform_enabled: true

trading:
  min_edge: 0.01  # 1% minimum edge
  default_order_size: 5

risk:
  max_global_exposure: 50
  max_daily_loss: 10
```

Or use environment variables (`.env`):

```bash
POLYMARKET_API_KEY=your_key
POLYMARKET_PRIVATE_KEY=your_key
KALSHI_API_KEY=your_key
DRY_RUN=true
```

### 2. Run

```bash
# Run with FastAPI dashboard (default)
arbitrage-bot run

# Run with terminal UI
arbitrage-bot run --ui terminal

# Run without UI
arbitrage-bot run --ui none

# One-time market scan
arbitrage-bot scan --min-profit 2.0
```

### 3. Access Dashboard

- **FastAPI Dashboard**: http://localhost:8000 (default)
- **Terminal UI**: http://localhost:8080 (when using `--ui terminal`)

---

## 📁 Project Structure

```
Polymarket-Kalshi-Arbitrage-Bot/
├── arbitrage_bot/           # Main package
│   ├── __init__.py
│   ├── api/                 # API clients
│   │   ├── polymarket_client.py
│   │   └── kalshi_client.py
│   ├── core/                # Trading logic
│   │   ├── arbitrage_engine.py
│   │   ├── market_matcher.py
│   │   ├── execution_engine.py
│   │   ├── risk_manager.py
│   │   └── portfolio.py
│   ├── models/              # Data models
│   │   ├── market.py
│   │   ├── order.py
│   │   ├── position.py
│   │   ├── trade.py
│   │   └── opportunity.py
│   ├── ui/                  # User interfaces
│   │   ├── fastapi_dashboard.py
│   │   └── terminal.py
│   ├── utils/              # Utilities
│   │   ├── config.py
│   │   └── logger.py
│   └── cli.py              # Command line interface
│
├── tests/                   # Test suite
├── config.yaml              # Configuration file
├── requirements.txt         # Dependencies
├── setup.py                 # Setup script
├── pyproject.toml          # Modern Python packaging
└── README.md               # This file
```

---

## 🎮 Usage

### Command Line Interface

```bash
# Run bot
arbitrage-bot run [OPTIONS]

# Options:
#   --ui {fastapi,terminal,none}  UI to use (default: fastapi)
#   --config PATH                  Configuration file path
#   --live                         Enable live trading
#   --port PORT                    Server port
#   --host HOST                    Server host
#   -v, --verbose                  Verbose logging

# Scan markets
arbitrage-bot scan [OPTIONS]

# Options:
#   --min-profit FLOAT            Minimum profit percentage
#   --threshold FLOAT             Market matching threshold
#   --output {table,json}         Output format
```

### Python API

```python
from arbitrage_bot import ArbitrageEngine, MarketMatcher
from arbitrage_bot.api import PolymarketClient, KalshiClient
from arbitrage_bot.utils.config import Config

# Load configuration
config = Config.load("config.yaml")

# Initialize clients
async with PolymarketClient() as poly_client:
    async with KalshiClient() as kalshi_client:
        # Use the bot
        ...
```

---

## ⚙️ Configuration

### YAML Configuration

See `config.yaml.example` for full configuration options.

Key sections:
- `api` - API credentials and endpoints
- `trading` - Trading parameters
- `risk` - Risk management limits
- `mode` - Operating mode settings

### Environment Variables

The bot also supports `.env` files:

```bash
POLYMARKET_API_KEY=...
POLYMARKET_PRIVATE_KEY=...
KALSHI_API_KEY=...
KALSHI_API_SECRET=...
DRY_RUN=true
MIN_ARBITRAGE_PROFIT_PCT=1.0
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=arbitrage_bot --cov-report=html

# Run specific test
pytest tests/test_arbitrage_engine.py -v
```

---

## 📚 Documentation

- [SETUP.md](SETUP.md) - Detailed setup instructions
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## ⚠️ Disclaimer

**This software is for educational purposes only.** Trading prediction markets involves significant risk of loss. Past performance does not guarantee future results. Always:

- Start in dry-run mode
- Use small amounts initially
- Monitor actively
- Understand the risks

---

<div align="center">

Made with ☕ and Python

**Professional. Unified. Production-Ready.**

</div>
