# Arbitrage Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Async](https://img.shields.io/badge/Async-aiohttp-purple.svg)

**Cross-platform arbitrage detection for sportsbooks and prediction markets**

Scans FanDuel, DraftKings, BetMGM, Caesars, Bovada, Polymarket, and Kalshi for mispriced lines and risk-free arbitrage opportunities.

</div>

---

## What It Does

Two independent engines running in the same package:

| Engine | Markets | Strategy |
|--------|---------|----------|
| **Sportsbook Arb** | FanDuel, DraftKings, BetMGM, Caesars, Bovada | Cross-book arbitrage + value betting across US sportsbooks |
| **Prediction Market Arb** | Polymarket, Kalshi | Cross-platform arbitrage + bundle arbitrage on prediction markets |

Both share the same models, config system, and risk controls.

---

## Quick Start

### 1. Get an API key

**Sportsbooks** — Sign up at [the-odds-api.com](https://the-odds-api.com/) for a free key (500 credits/mo). The $30/mo tier (20K credits) is recommended for continuous scanning.

**Prediction markets** — Kalshi and Polymarket API keys are loaded from environment variables when those engines are activated.

### 2. Install

```bash
git clone https://github.com/nickTurano/arbitrage-bot.git
cd arbitrage-bot

python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 3. Run — Sportsbook Scanner

```bash
# One-shot scan (dry run — prints opportunities, places nothing):
ODDS_API_KEY=your_key python run_sportsbook.py

# Continuous scanning (re-scans every 30s):
ODDS_API_KEY=your_key python run_sportsbook.py --loop

# Specific sports only:
ODDS_API_KEY=your_key python run_sportsbook.py --sports americanfootball_nfl basketball_nba

# Specific bookmakers only:
ODDS_API_KEY=your_key python run_sportsbook.py --bookmakers fanduel draftkings

# Tighten/loosen thresholds:
ODDS_API_KEY=your_key python run_sportsbook.py --min-edge 0.01 --min-edge-vb 0.03
```

### 4. Run — Prediction Market Scanner

```bash
# (Polymarket/Kalshi clients are stubs — pending full implementation)
arbitrage-bot scan
```

---

## Architecture

```
arbitrage-bot/
├── arbitrage_bot/
│   ├── api/
│   │   ├── odds_api_client.py      # TheOddsAPI v4 async client (sportsbooks)
│   │   ├── fanduel_client.py       # FanDuel wrapper + stubbed bet placement
│   │   ├── polymarket_client.py    # Polymarket client (stub)
│   │   └── kalshi_client.py        # Kalshi client (stub, loads API key)
│   ├── core/
│   │   ├── arb_engine.py           # Cross-book arb + value bet detection
│   │   └── budget_tracker.py       # Budget management & P&L tracking
│   ├── models/
│   │   ├── market.py               # Order books, price levels
│   │   ├── opportunity.py          # Opportunity types (bundle, cross-platform, MM)
│   │   ├── order.py                # Order lifecycle states
│   │   ├── trade.py                # Executed trade records
│   │   └── position.py             # Position tracking
│   ├── utils/
│   │   ├── config.py               # YAML + env config loader
│   │   ├── logger.py               # Structured logging
│   │   └── validators.py           # Input validation
│   ├── bot.py                      # Main orchestrator (prediction markets)
│   ├── scanner.py                  # One-shot market scanner
│   └── cli.py                      # CLI entry point
├── run_sportsbook.py               # Sportsbook scanner entry point
├── config.yaml.example             # Full config reference
├── requirements.txt
└── tests/
```

---

## How the Sportsbook Engine Works

### Cross-Book Arbitrage

When the same event is priced differently across sportsbooks, a risk-free profit can sometimes be extracted by betting both sides.

**Example:**
- FanDuel: Cowboys +150 → implied probability 40.0%
- DraftKings: Buccaneers +140 → implied probability 41.7%
- Sum of implied probs: **81.7%** (< 100%)
- Edge: **18.3%** — guaranteed profit regardless of outcome

The engine finds the best available price for each outcome across all books, checks whether the implied probabilities sum to less than 1.0, and calculates optimal stake splits.

### Value Betting

When a single bookmaker offers meaningfully better odds than the market consensus, it's a +EV (positive expected value) bet even though it's not risk-free.

The engine averages implied probabilities across all books as a "true" estimate, then flags any outcome where a single book's implied probability is more than 5% below that consensus (meaning the book is offering better odds than it should).

### Risk Controls

All enforced in-engine, not configurable:

| Limit | Value | Description |
|-------|-------|-------------|
| Max single leg | $50 | Never bet more than this on one leg |
| Max arb total | $100 | Never risk more than this across all legs of one arb |
| Default mode | Dry run | No bets execute without `--live` flag |

### Budget Management

The bot tracks a project budget across three buckets:

| Bucket | Amount | Purpose |
|--------|--------|---------|
| API | $60 | TheOddsAPI subscription (2 months @ $30/mo) |
| Bankroll | $200 | Active betting capital |
| Reserve | $740 | Unlocked in $100 increments after 10+ settled bets with positive P&L |

Budget state persists to `logs/budget.json` across restarts.

---

## Configuration

Copy `config.yaml.example` to `config.yaml` and fill in your keys. Or skip the config file entirely and use environment variables:

```bash
# Required for sportsbook scanning:
ODDS_API_KEY=your_the_odds_api_key

# For prediction markets (when implemented):
KALSHI_API_KEY=your_kalshi_key
POLYMARKET_PRIVATE_KEY=your_polymarket_key
```

See `config.yaml.example` for the full reference — every setting is documented inline.

---

## Testing

```bash
# Run test suite:
pytest

# Run with coverage:
pytest --cov=arbitrage_bot --cov-report=html

# Quick smoke test (no API key needed):
python -c "
from arbitrage_bot.core.arb_engine import ArbEngine, american_to_implied_prob
assert abs(american_to_implied_prob(-150) - 0.60) < 0.001
print('Engine math OK')
"
```

---

## What's Not Implemented Yet

| Feature | Status | Notes |
|---------|--------|-------|
| Live bet placement (FanDuel) | Stub | FanDuel has no public API. Options: browser automation or alert-only mode |
| Polymarket client | Stub | API structure in place, pending implementation |
| Kalshi client | Stub | API key loading works, trading logic pending |
| Bundle arbitrage | Stub | Detection logic planned for prediction market engine |
| Historical backtesting | Planned | TheOddsAPI offers historical odds on paid tiers |

---

## License

MIT — see [LICENSE](LICENSE)

---

> **Disclaimer:** This software is for educational and research purposes. Sports betting involves risk of loss. Always start in dry-run mode, use small stakes, and understand the risks before deploying real capital.
