# Setup Guide

This guide will help you set up the Polymarket-Kalshi Arbitrage Bot.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- (Optional) MetaMask browser extension for Polymarket trading
- (Optional) Kalshi account with API access

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Polymarket-Kalshi-Arbitrage-Bot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure

The unified package supports both YAML and .env configuration:

**YAML Configuration (Recommended):**
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

**Environment Variables:**
```bash
# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

**Configuration Options:**
- Set `trading_mode: "dry_run"` initially
- Configure API keys and wallet private key
- Adjust risk limits
- Choose UI preference

### 5. Get API Keys

#### Kalshi API Keys

1. Create account at [kalshi.com](https://kalshi.com)
2. Complete identity verification
3. Go to Settings > API
4. Generate new API key pair
5. Store securely - the secret is only shown once!

#### Polymarket

Polymarket uses Web3 wallet authentication:

1. Install MetaMask browser extension
2. Create or import a wallet
3. Add Polygon network to MetaMask
4. Fund wallet with MATIC (for gas) and USDC (for trading)
5. For programmatic access, export your private key (keep secure!)

### 6. Test the Setup

#### Test the Bot

```bash
# Run in dry-run mode
arbitrage-bot run --ui none

# Test market scan
arbitrage-bot scan --min-profit 2.0
```

### 7. Run with Dashboard

#### FastAPI Dashboard (Default)

```bash
arbitrage-bot run
# Open http://localhost:8000
```

#### Terminal UI

```bash
arbitrage-bot run --ui terminal
# Open http://localhost:8080
```

#### Headless Mode

```bash
arbitrage-bot run --ui none
```

## Configuration Tips

### Start Small

- Set `trading_mode: "dry_run"` initially
- Use small order sizes: `default_order_size: 5`
- Set conservative risk limits: `max_global_exposure: 50`

### Monitor First

- Run for a few hours in dry-run mode
- Review logs and opportunities
- Understand how the bot behaves

### Gradual Rollout

1. **Week 1**: Dry-run mode, monitor opportunities
2. **Week 2**: Small live trades ($5-10 per trade)
3. **Week 3**: Gradually increase if profitable
4. **Ongoing**: Monitor and adjust risk limits

## Troubleshooting

### Import Errors

```bash
# Make sure you're in the virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### API Connection Issues

- Check your internet connection
- Verify API keys are correct
- Check if APIs are rate-limiting you
- Review logs for specific error messages

### Web3/Wallet Issues

- Ensure MetaMask is installed and unlocked
- Check Polygon network is added to MetaMask
- Verify wallet has MATIC for gas
- Check browser console for errors

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
python main.py server --port 3000
```

## Next Steps

1. Read the main [README.md](README.md) for detailed documentation
2. Review the configuration files for all available options
3. Start with dry-run mode and monitor for opportunities
4. Join discussions and report issues on GitHub

## Support

- Check the [README.md](README.md) for detailed documentation
- Review code comments for implementation details
- Open an issue on GitHub for bugs or questions

