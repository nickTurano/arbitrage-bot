# Kalshi ↔ Sportsbook Arbitrage Bot — Development Backlog

## ⚠️ Repo Reality Check

The upstream repo (`earthskyorg/Polymarket-Kalshi-Arbitrage-Bot`) is **scaffolding, not a working bot.**

**What's real:**
- ✅ Project structure & architecture pattern
- ✅ Data models (`Market`, `OrderBook`, `Opportunity`, `Order`, `Trade`, `Position`)
- ✅ Config system (YAML + .env)
- ✅ Exception hierarchy
- ✅ CLI skeleton
- ✅ FastAPI dashboard shell
- ✅ Terminal UI shell

**What's stubs (TODO / missing files):**
- ❌ `api/kalshi_client.py` — **file does not exist**, only referenced in `__init__.py`
- ❌ `api/polymarket_client.py` — same, does not exist
- ❌ `core/arbitrage_engine.py` — does not exist
- ❌ `core/market_matcher.py` — does not exist
- ❌ `core/execution_engine.py` — does not exist
- ❌ `core/risk_manager.py` — does not exist
- ❌ `core/portfolio.py` — does not exist
- ❌ `bot.py` main loop — all TODOs
- ❌ `scanner.py` scan logic — all TODOs
- ❌ Dashboard endpoints — return empty/hardcoded data

We keep the models, config, and project structure. Everything else gets built.

---

## Ticket Backlog

### EPIC 1 — Strip & Prep
Remove Polymarket dependencies. Rebase the repo for Kalshi ↔ Sportsbook arb.

---

**[TICKET-01] Remove Polymarket**
- Delete `api/polymarket_client.py` import from `api/__init__.py`
- Remove `py-clob-client`, `web3`, `eth-account` from `requirements.txt` (Polymarket/crypto deps)
- Remove Polymarket URLs from `APIConfig` in `config.py`
- Remove Polymarket env vars from `.env` loading
- Remove `OpportunityType.CROSS_PLATFORM` — replace with `SPORTSBOOK_ARB`
- Update `config.yaml.example`

**[TICKET-02] Add Sportsbook models**
New file: `models/sportsbook.py`
- `Sportsbook` enum — `DRAFTKINGS`, `FANDUEL`, `BETMGM`, `CAESARS`, `POINTSBET`, etc.
- `OddsFormat` enum — `AMERICAN`, `DECIMAL`, `IMPLIED_PROBABILITY`
- `SportsLine` dataclass:
  - `sportsbook: Sportsbook`
  - `event_id: str`
  - `market_type: str` (moneyline, spread, over_under)
  - `home_odds / away_odds: float` (American format)
  - `timestamp: datetime`
- `ArbitrageOpportunity` dataclass (extends or replaces `Opportunity`):
  - `kalshi_market_id: str`
  - `kalshi_side: str` (YES/NO)
  - `kalshi_price: float`
  - `sportsbook: Sportsbook`
  - `sportsbook_implied_prob: float`
  - `net_edge: float` (after fees both sides)
  - `max_fill_size: float` (limited by Kalshi liquidity)
  - `legs: List[Leg]` — ordered execution plan

**[TICKET-03] Add fee calculator for sportsbooks**
New file: `utils/fees.py`
- `kalshi_fee(contract_price: float) -> float` — tiered fee schedule (~0.7% avg)
- `sportsbook_vig(american_odds: float) -> float` — extract vig from the line
- `american_to_implied(odds: float) -> float` — convert American odds to implied probability
- `implied_to_american(prob: float) -> float` — reverse conversion
- `net_edge(kalshi_price, sportsbook_implied, kalshi_fee, sb_vig) -> float`

---

### EPIC 2 — Data Layer (Scan)
Build the two data feeds and the matching engine.

---

**[TICKET-04] Kalshi API client**
New file: `api/kalshi_client.py`
Wrap Kalshi's REST API (`https://api.kalshi.com/trade-api/v2`):
- Auth: API key + RSA private key signing (per Kalshi docs)
- `get_markets(filters) -> List[Market]` — list active markets, filterable by sport/category
- `get_market(market_id) -> Market` — single market detail
- `get_orderbook(market_id) -> OrderBook` — live order book
- `place_order(market_id, side, price, size) -> Order`
- `get_positions() -> List[Position]`
- `get_balance() -> float`
- Rate limiting: respect Kalshi's rate limits, back off on 429
- Retry logic: exponential backoff on transient failures
- Dry-run mode: simulate fills locally when `config.is_dry_run`

**[TICKET-05] Sportsbook odds client (The Odds API)**
New file: `api/sportsbook_client.py`
Wrap The Odds API (`https://api.the-odds-api.com`):
- Auth: API key in query params
- `get_sports() -> List[Sport]` — available sports
- `get_odds(sport, regions, markets) -> List[EventOdds]`
  - regions: `us`
  - markets: `h2h` (moneyline), `spreads`, `totals`
  - bookmakers: configurable list
- Parse response into `List[SportsLine]`
- Cache layer: odds don't change every second — cache with TTL (e.g., 5s for live, 30s for pre-game)
- Usage tracking: free tier is limited (500 requests/month) — log remaining quota from response headers

**[TICKET-06] Market matcher**
New file: `core/market_matcher.py`
Match Kalshi event contracts to sportsbook lines:
- Kalshi markets have structured metadata (sport, teams, event type)
- Sportsbook lines have event names, team names, start times
- Matching logic:
  1. Filter by sport
  2. Match on team names (fuzzy match, handle abbreviations — e.g., "KC" = "Kansas City Chiefs")
  3. Match on event start time (within tolerance window)
  4. Match on market type (moneyline ↔ Kalshi winner contract, spread ↔ Kalshi spread contract)
- Output: `List[MatchedPair]` — confirmed Kalshi market ↔ sportsbook line pairs
- Confidence scoring — only act on matches above threshold (configurable, default 0.85)

---

### EPIC 3 — Detection Engine (Detect)

---

**[TICKET-07] Arbitrage scanner / detection engine**
New file: `core/arbitrage_engine.py`
Core detection loop:
- Input: stream of `MatchedPair` objects (Kalshi price + sportsbook line)
- For each pair:
  1. Convert sportsbook odds → implied probability (strip vig)
  2. Get Kalshi best ask (if betting YES) or best bid (if betting NO)
  3. Calculate net edge: `sportsbook_implied_prob - kalshi_price - fees`
  4. If edge > `config.trading.min_edge`:
     - Calculate max fill size (min of Kalshi liquidity at that level, per-book bet cap)
     - Emit `ArbitrageOpportunity`
- Edge decay: opportunities expire fast — attach a `detected_at` timestamp, discard if stale (>2s old)
- Deduplication: don't re-emit the same opportunity if it hasn't changed

**[TICKET-08] Continuous scan loop**
Wire the scanner into `bot.py`:
- Poll cycle: fetch Kalshi orderbooks + sportsbook odds every N seconds (configurable, start at 2s)
- Run market matcher → arbitrage engine → emit opportunities
- Feed opportunities to execution engine (EPIC 4)
- Feed opportunities to dashboard (via callback)
- Log all scans for backtesting replay

---

### EPIC 4 — Execution Engine (Trade)

---

**[TICKET-09] Kalshi order executor**
New file: `core/execution_engine.py` (Kalshi section)
- Place limit orders on Kalshi via API client
- Order sizing: use `suggested_size` from opportunity, cap at liquidity
- Fill monitoring: poll order status until filled, partially filled, or timeout
- Timeout handling: cancel order if not filled within `order_timeout_seconds`
- Dry-run: simulate fill with configurable probability (`config.mode.fill_probability`)

**[TICKET-10] Sportsbook bet executor**
New file: `api/sportsbook_executor.py`
This is the hardest piece — sportsbooks have no public API.
Options (implement in order of priority):
1. **The Odds API does NOT support placing bets** — it's read-only
2. **Browser automation** — use Playwright/Selenium to place bets on sportsbook web apps
   - Login flow, navigate to event, select line, enter amount, confirm
   - Session management (cookies, auth tokens)
   - Fragile — likely to break on UI changes
3. **Mobile API reverse engineering** — capture sportsbook mobile app API calls, replay them
   - More stable than web scraping, but ToS violation risk
   - Start with one book, expand later

**Phase 1 recommendation: Browser automation via Playwright**
- `place_bet(sportsbook, event_id, side, amount) -> BetResult`
- Per-sportsbook strategy classes (each book has a different UI)
- Start with ONE book (e.g., DraftKings) — get it working, then template for others
- Dry-run mode: skip actual placement, return simulated result

**[TICKET-11] Legging risk manager**
Coordinates the two-leg execution:
- **Strategy: Fill Kalshi first (thin side), then sportsbook (liquid side)**
- Step 1: Place Kalshi order, wait for fill
- Step 2: If Kalshi fills → place sportsbook bet immediately
- Step 3: If Kalshi does NOT fill within timeout → cancel, move on
- Step 4: If sportsbook bet fails after Kalshi fill → **alert immediately**, hold Kalshi position (now a naked bet)
- Partial fill handling: if Kalshi partially fills, size sportsbook bet to match filled amount only
- Leg timeout: configurable (default 3s for Kalshi fill wait)

---

### EPIC 5 — Risk & Account Management (Protect)

---

**[TICKET-12] Risk manager**
New file: `core/risk_manager.py`
- Per-book bet size caps (stay below sportsbook radar — e.g., max $500/bet on DraftKings)
- Per-book daily volume cap (e.g., max $2000/day per book)
- Global max exposure across all open positions
- Max daily loss — kill switch triggers if breached
- Max drawdown — if portfolio drops X% from high water mark, pause trading
- Opportunity filter: reject opportunities below liquidity threshold
- Kill switch: emergency stop, cancel all open orders, no new trades

**[TICKET-13] Portfolio / balance tracker**
New file: `core/portfolio.py`
- Track balances on: Kalshi + each sportsbook
- Track all open positions (Kalshi contracts held, pending sportsbook bets)
- Track realized P&L (closed arbs)
- Track unrealized P&L (open positions marked to market)
- Daily P&L reset
- Balance refresh: periodically sync actual balances from Kalshi API (sportsbooks harder — may need to scrape)

**[TICKET-14] Book rotation / spread logic**
- When an arb opportunity is detected, route it to the sportsbook with:
  - Most remaining daily volume headroom
  - Least recent activity (spread action out over time)
  - Highest remaining bet size cap
- If all books are at their caps for that event → skip
- Log routing decisions for analysis

**[TICKET-15] Ban detection**
- Monitor sportsbook accounts for:
  - Bet limits being imposed
  - "Cooling off" periods
  - Account flags / restricted status
- Alert immediately on detection
- Auto-route future action away from flagged books
- Graceful degradation: if N books are banned, reduce trading volume proportionally

---

### EPIC 6 — Monitoring & Backtesting (Learn)

---

**[TICKET-16] Wire up FastAPI dashboard**
Update `ui/fastapi_dashboard.py`:
- `/api/opportunities` — live stream of detected opportunities
- `/api/trades` — recent executed trades with both legs
- `/api/positions` — open positions across all platforms
- `/api/portfolio` — balance + P&L summary
- `/api/stats` — fill rates, edge decay, scan latency
- `/api/books` — per-sportsbook status (balance, daily volume used, ban status)
- WebSocket endpoint for real-time updates

**[TICKET-17] Logging & replay**
- Structured JSON logging for every:
  - Scan cycle (markets seen, edges calculated)
  - Opportunity detected
  - Execution attempt (each leg)
  - Fill / rejection / timeout
- Log to file + optionally to a sink (for backtesting replay)
- Replay mode: feed historical logs back through the scanner to validate detection logic

**[TICKET-18] Backtesting**
- Replay historical Kalshi orderbook data + sportsbook odds
- Simulate the full pipeline: match → detect → execute (with simulated fill)
- Report: opportunities found, fill rate, net P&L, edge distribution
- Requires historical data collection (start logging immediately)

---

### EPIC 7 — Hardening

---

**[TICKET-19] Test suite**
- Unit tests for: fee calculator, odds conversion, market matcher, risk manager
- Integration tests for: Kalshi client (against sandbox/dry-run), scanner loop
- Simulation tests: full pipeline dry-run with mocked data

**[TICKET-20] Config & secrets management**
- All API keys, sportsbook credentials in `.env` only — never in code or logs
- Kalshi private key stored securely (file path in config, not inline)
- Sportsbook session tokens rotated periodically

---

## Execution Order (Recommended)

```
Phase 1 — Foundation
  TICKET-01  Strip Polymarket
  TICKET-02  Sportsbook models
  TICKET-03  Fee calculator

Phase 2 — Data Feeds
  TICKET-04  Kalshi API client
  TICKET-05  Sportsbook odds client
  TICKET-06  Market matcher

Phase 3 — Detection
  TICKET-07  Arbitrage engine
  TICKET-08  Scan loop (wire into bot.py)

Phase 4 — Execution (DraftKings first)
  TICKET-09  Kalshi executor
  TICKET-10  Sportsbook executor (Playwright, DK only)
  TICKET-11  Legging risk manager

Phase 5 — Risk & Portfolio
  TICKET-12  Risk manager
  TICKET-13  Portfolio tracker
  TICKET-14  Book rotation
  TICKET-15  Ban detection

Phase 6 — Monitoring
  TICKET-16  Dashboard
  TICKET-17  Logging
  TICKET-18  Backtesting
  TICKET-19  Tests
  TICKET-20  Secrets
```

---

## Open Questions (Decide Before Coding)

1. **Kalshi API key** — Do you have one? Need key + RSA private key.
2. **The Odds API key** — Need one. Free tier = 500 req/month (not enough for prod). Budget for paid tier?
3. **Sportsbook accounts** — Which books do you have? Start with the one you're most comfortable with for Playwright automation.
4. **Starting capital** — Determines position sizing, number of books needed, and risk config.
5. **Target sports** — NFL and NBA recommended first (most liquid on Kalshi).
6. **Execution priority** — Start with detection-only (scan + alert, no auto-trade) or go straight to full auto?
