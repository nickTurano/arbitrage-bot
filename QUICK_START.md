# Quick Start Guide

## Unified Entry Point

The project now has a **unified `main.py`** at the root that lets you access both implementations easily.

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure (choose one or both)
# For FastAPI:
cp polymarket-arbitrage/config.yaml polymarket-arbitrage/config.local.yaml
# Edit config.local.yaml

# For Terminal UI:
cp Polymarket-Kalshi-Arbitrage/.env.example Polymarket-Kalshi-Arbitrage/.env
# Edit .env
```

## Running the Bot

### Using the Unified Package

```bash
# FastAPI Dashboard (default)
arbitrage-bot run

# Terminal UI
arbitrage-bot run --ui terminal

# Bot only (no UI)
arbitrage-bot run --ui none

# Market scan
arbitrage-bot scan --min-profit 2.0
```

## UI Options

The unified package supports multiple UI options:

### FastAPI Dashboard (Default)
- ✅ Production-ready REST API
- ✅ Comprehensive risk management
- ✅ Better portfolio tracking
- ✅ More features (bundle arb, market making)
- ✅ Real-time data feed
- ✅ Simulation mode for testing

### Terminal UI
- ✅ Beautiful terminal-style interface
- ✅ Web3 wallet integration (MetaMask)
- ✅ Interactive filters
- ✅ WebSocket real-time updates

### Headless Mode
- ✅ Run without UI for automated trading
- ✅ Perfect for production deployments

## Configuration Quick Reference

### Configuration (config.yaml)
```yaml
mode:
  trading_mode: "dry_run"  # Always start here!
  data_mode: "real"
  cross_platform_enabled: true

trading:
  min_edge: 0.01
  default_order_size: 5

risk:
  max_global_exposure: 50
```

Or use environment variables (.env):
```bash
POLYMARKET_API_KEY=your_key
POLYMARKET_PRIVATE_KEY=your_key
KALSHI_API_KEY=your_key
DRY_RUN=true
```

## Common Commands

```bash
# Start FastAPI dashboard
python main.py

# Start terminal UI on custom port
python main.py --ui terminal --port 3000

# Run market scan
python main.py --scan

# Run bot in live mode (be careful!)
python main.py --live

# Verbose logging
python main.py -v
```

## Getting Help

- See [README.md](README.md) for full documentation
- See [SETUP.md](SETUP.md) for detailed setup
- Check `PROJECT_STATUS.md` for current features

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure API keys
3. ✅ Run in dry-run mode first
4. ✅ Monitor for opportunities
5. ✅ Start with small trades

---

**Remember**: Always start in dry-run mode and with small amounts!

