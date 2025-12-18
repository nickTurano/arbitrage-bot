# Architecture Overview

## Project Structure

This project combines two implementations into a unified arbitrage bot:

```
Polymarket-Kalshi-Arbitrage-Bot/
│
├── arbitrage_bot/            # ⭐ Main package
│   ├── api/                  # API clients
│   ├── core/                 # Trading logic
│   ├── models/               # Data models
│   ├── ui/                   # User interfaces
│   ├── utils/                # Utilities
│   └── cli.py               # CLI entry point
│
├── tests/                    # Test suite
├── config.yaml.example      # Configuration template
├── requirements.txt          # Dependencies
└── setup.py                 # Setup script
```

## Unified Entry Point

The `main.py` at the root provides a single interface to both implementations:

```python
python main.py                    # FastAPI (default)
python main.py --ui terminal      # Terminal UI
python main.py --bot-only         # Bot without UI
python main.py --scan             # Market scan
```

## How It Works

### Command Routing

```
arbitrage-bot CLI
  ├── run --ui fastapi → FastAPIDashboard
  ├── run --ui terminal → TerminalUI
  ├── run --ui none → ArbitrageBot (headless)
  └── scan → MarketScanner
```

### Package Structure

#### Main Package (`arbitrage_bot/`)

**Architecture:**
- Unified Python package
- Modular design
- Async/await throughout
- Type hints everywhere
- Comprehensive error handling

**Key Components:**
- `api/` - API clients (Polymarket, Kalshi)
- `core/` - Trading logic (arbitrage engine, market matcher, execution, risk management)
- `models/` - Data models (market, order, position, trade, opportunity)
- `ui/` - User interfaces (FastAPI dashboard, Terminal UI)
- `utils/` - Utilities (config, logger, validators)
- `exceptions.py` - Custom exception hierarchy

**Configuration:** Unified system supporting both YAML and .env

## Data Flow

### Cross-Platform Arbitrage

```
1. Fetch Markets
   ├── Polymarket API → Market List
   └── Kalshi API → Market List

2. Match Markets
   └── Market Matcher → Matched Pairs

3. Monitor Prices
   ├── Polymarket Order Books
   └── Kalshi Order Books

4. Detect Arbitrage
   └── Cross-Platform Arb Engine → Opportunities

5. Execute Trades
   ├── Risk Manager (validate)
   ├── Execution Engine (place orders)
   └── Portfolio (track positions)
```

### Market Matching Algorithm

Both implementations use similar matching strategies:

1. **Text Normalization** - Remove stop words, lowercase, etc.
2. **Fuzzy Matching** - SequenceMatcher or fuzzywuzzy
3. **Entity Extraction** - Names, dates, numbers, teams
4. **Category Filtering** - Match within categories (politics, sports, etc.)
5. **Sports-Specific** - Team name recognition (NFL, NBA)

## Configuration Management

### FastAPI (YAML)
- Single `config.yaml` file
- Hierarchical structure
- Supports multiple modes (dry-run, live, simulation)

### Terminal UI (Environment Variables)
- `.env` file
- Simple key-value pairs
- Easy to override per environment

## API Clients

Both implementations have their own API clients, but they serve the same purpose:

- **Polymarket Client**: Connects to Polymarket CLOB API and Gamma API
- **Kalshi Client**: Connects to Kalshi Trading API v2

## Core Trading Logic

### Arbitrage Detection

1. **Bundle Arbitrage**: YES + NO prices don't sum to $1.00
2. **Cross-Platform**: Same market priced differently on two platforms
3. **Market Making**: Wide spreads that can be captured

### Risk Management

- Position limits per market
- Global exposure limits
- Daily loss limits
- Kill switch
- Drawdown protection

### Execution

- Order placement
- Fill monitoring
- Slippage tracking
- Timeout handling

## UI Options

### FastAPI Dashboard
- REST API endpoints
- WebSocket for real-time updates
- Embedded HTML dashboard
- More comprehensive metrics

### Terminal UI
- Flask-SocketIO
- Terminal-style design
- Web3 wallet integration
- Interactive filters

## Future Improvements

1. **Unified API Client** - Merge both implementations into one
2. **Unified Core Logic** - Single arbitrage engine
3. **Unified Configuration** - One config system
4. **Plugin Architecture** - Allow easy UI switching
5. **Shared Models** - Common data models

## Design Decisions

### Why Keep Both Implementations?

1. **Different Use Cases**: FastAPI for production, Terminal UI for demos
2. **Different Config Styles**: YAML vs .env
3. **Different Architectures**: FastAPI vs Flask
4. **User Choice**: Let users pick what works for them

### Why Unified Entry Point?

1. **Easier Onboarding**: One command to run
2. **Consistent Interface**: Same CLI for both
3. **Future-Proof**: Easy to add more implementations
4. **Documentation**: Single place to document usage

---

This architecture allows the project to evolve while maintaining backward compatibility with both implementations.

