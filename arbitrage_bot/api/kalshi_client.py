"""
Kalshi Client
=============

Fetches sports game contracts from Kalshi's public (unauthenticated)
market data API. No API key required for reads.

Supported series:
    KXNBAGAME   — Individual NBA game win contracts
    KXNHLGAME   — Individual NHL game win contracts
    KXNFLGAME   — Individual NFL game win contracts (seasonal)

Contract structure:
    Each game has two binary markets (one per team).
    Ticker: KXNBAGAME-{date}{HOME}{AWAY}-{TEAM}
    Price:  yes_bid / yes_ask in cents (0–100). Mid = implied probability.

Team name matching:
    Kalshi uses short city names in event titles ("Oklahoma City at Denver").
    A lookup table maps these to the full names TheOddsAPI uses
    ("Oklahoma City Thunder", "Denver Nuggets") so we can match events
    across platforms.

Trading endpoints (order placement) require auth via API key + RSA signing.
That's stubbed for now — detection only.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# ---------------------------------------------------------------------------
# Sports series to scan
# ---------------------------------------------------------------------------
SPORTS_SERIES = ["KXNBAGAME", "KXNHLGAME", "KXNFLGAME"]

# ---------------------------------------------------------------------------
# Team name mapping: Kalshi short name → TheOddsAPI full name
# ---------------------------------------------------------------------------
# Kalshi event titles use city/region names. TheOddsAPI uses official team names.
# Keys are lowercase for case-insensitive matching.
TEAM_NAME_MAP: Dict[str, str] = {
    # NBA
    "atlanta": "Atlanta Hawks",
    "boston": "Boston Celtics",
    "brooklyn": "Brooklyn Nets",
    "charlotte": "Charlotte Hornets",
    "chicago": "Chicago Bulls",
    "cleveland": "Cleveland Cavaliers",
    "dallas": "Dallas Mavericks",
    "denver": "Denver Nuggets",
    "detroit": "Detroit Pistons",
    "golden state": "Golden State Warriors",
    "houston": "Houston Rockets",
    "indiana": "Indiana Pacers",
    "los angeles c": "Los Angeles Clippers",
    "los angeles l": "Los Angeles Lakers",
    "la clippers": "Los Angeles Clippers",
    "la lakers": "Los Angeles Lakers",
    "memphis": "Memphis Grizzlies",
    "miami": "Miami Heat",
    "milwaukee": "Milwaukee Bucks",
    "minnesota": "Minnesota Timberwolves",
    "new orleans": "New Orleans Pelicans",
    "new york": "New York Knicks",
    "oklahoma city": "Oklahoma City Thunder",
    "orlando": "Orlando Magic",
    "philadelphia": "Philadelphia 76ers",
    "phoenix": "Phoenix Suns",
    "portland": "Portland Trail Blazers",
    "sacramento": "Sacramento Kings",
    "san antonio": "San Antonio Spurs",
    "toronto": "Toronto Raptors",
    "utah": "Utah Jazz",
    "washington": "Washington Wizards",
    # NHL
    "anaheim": "Anaheim Ducks",
    "arizona": "Arizona Coyotes",
    "calgary": "Calgary Flames",
    "carolina": "Carolina Hurricanes",
    "chicago": "Chicago Blackhawks",  # context-dependent, NBA=Bulls handled above
    "colorado": "Colorado Avalanche",
    "columbus": "Columbus Blue Jackets",
    "dallas": "Dallas Stars",  # context-dependent
    "detroit": "Detroit Red Wings",  # context-dependent
    "edmonton": "Edmonton Oilers",
    "florida": "Florida Panthers",
    "los angeles": "Los Angeles Kings",
    "minnesota": "Minnesota Wild",  # context-dependent
    "montreal": "Montreal Canadiens",
    "nashville": "Nashville Predators",
    "new jersey": "New Jersey Devils",
    "ny islanders": "New York Islanders",
    "ny rangers": "New York Rangers",
    "ottawa": "Ottawa Senators",
    "philadelphia": "Philadelphia Flyers",  # context-dependent
    "pittsburgh": "Pittsburgh Penguins",
    "san jose": "San Jose Sharks",
    "seattle": "Seattle Kraken",
    "tampa bay": "Tampa Bay Lightning",
    "toronto": "Toronto Maple Leafs",  # context-dependent
    "vancouver": "Vancouver Canucks",
    "vegas": "Vegas Golden Knights",
    "washington": "Washington Capitals",  # context-dependent
    "winnipeg": "Winnipeg Jets",
    # NHL-specific abbreviations that appear in tickers
    "st. louis": "St. Louis Blues",
    "utah mammoth": "Utah Mammoth",  # new NHL expansion team
}

# Sport-specific overrides for ambiguous city names
# When we know the series (KXNBAGAME vs KXNHLGAME), use these
SPORT_OVERRIDES: Dict[str, Dict[str, str]] = {
    "KXNBAGAME": {
        "chicago": "Chicago Bulls",
        "dallas": "Dallas Mavericks",
        "detroit": "Detroit Pistons",
        "minnesota": "Minnesota Timberwolves",
        "philadelphia": "Philadelphia 76ers",
        "toronto": "Toronto Raptors",
        "washington": "Washington Wizards",
        "los angeles": "Los Angeles Lakers",  # default; C/L suffixes handled separately
    },
    "KXNHLGAME": {
        "chicago": "Chicago Blackhawks",
        "dallas": "Dallas Stars",
        "detroit": "Detroit Red Wings",
        "minnesota": "Minnesota Wild",
        "philadelphia": "Philadelphia Flyers",
        "toronto": "Toronto Maple Leafs",
        "washington": "Washington Capitals",
        "los angeles": "Los Angeles Kings",
    },
}


def resolve_team_name(short_name: str, series: str) -> Optional[str]:
    """
    Map a Kalshi short/city team name to the full TheOddsAPI name.

    Args:
        short_name: e.g. "Oklahoma City", "Los Angeles L"
        series:     e.g. "KXNBAGAME" — used to resolve ambiguous cities

    Returns:
        Full team name or None if not found.
    """
    key = short_name.strip().lower()

    # Check sport-specific overrides first
    overrides = SPORT_OVERRIDES.get(series, {})
    if key in overrides:
        return overrides[key]

    # Fall back to general map
    return TEAM_NAME_MAP.get(key)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class KalshiMarket:
    """A single Kalshi binary market (one side of a game)."""

    ticker: str
    event_ticker: str
    series: str           # e.g. "KXNBAGAME"
    team_short: str       # Kalshi's short name, e.g. "Oklahoma City"
    team_full: Optional[str] = None  # Resolved full name, e.g. "Oklahoma City Thunder"
    yes_bid: Optional[float] = None  # cents (0–100)
    yes_ask: Optional[float] = None
    implied_prob: Optional[float] = None  # mid price as 0–1 probability
    volume_24h: int = 0
    close_time: Optional[datetime] = None
    title: str = ""


@dataclass
class KalshiGame:
    """A matched pair of Kalshi markets for one game (home + away)."""

    event_ticker: str
    series: str
    home_team_short: str
    away_team_short: str
    home_team_full: Optional[str] = None
    away_team_full: Optional[str] = None
    home_market: Optional[KalshiMarket] = None
    away_market: Optional[KalshiMarket] = None
    close_time: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class KalshiClient:
    """
    Async client for Kalshi sports game contracts.

    Usage:
        async with KalshiClient() as client:
            games = await client.get_sports_games()
    """

    def __init__(self, config: Any = None) -> None:
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "KalshiClient":
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    # -- public API ---------------------------------------------------------

    async def get_sports_games(
        self,
        series: Optional[List[str]] = None,
    ) -> List[KalshiGame]:
        """
        Fetch all open sports game contracts and pair them into games.

        Args:
            series: Which series to scan. Defaults to all known sports series.

        Returns:
            List of KalshiGame objects (paired home/away markets).
        """
        series = series or SPORTS_SERIES
        all_games: List[KalshiGame] = []

        for s in series:
            markets = await self._get_series_markets(s)
            games = self._pair_markets(markets, s)
            all_games.extend(games)

        logger.info(f"Kalshi: fetched {len(all_games)} games across {len(series)} series")
        return all_games

    # -- internal -----------------------------------------------------------

    async def _get_series_markets(self, series_ticker: str) -> List[KalshiMarket]:
        """Fetch all open markets for a series and parse them."""
        session = self._ensure_session()
        url = f"{BASE_URL}/markets"
        params = {
            "series_ticker": series_ticker,
            "status": "open",
            "limit": 500,
        }

        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Kalshi API returned {resp.status} for {series_ticker}")
                    return []
                data = await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"Kalshi API error for {series_ticker}: {e}")
            return []

        markets: List[KalshiMarket] = []
        for m in data.get("markets", []):
            parsed = self._parse_market(m, series_ticker)
            if parsed:
                markets.append(parsed)

        return markets

    @staticmethod
    def _parse_market(raw: Dict[str, Any], series: str) -> Optional[KalshiMarket]:
        """Parse a raw Kalshi market dict into a KalshiMarket."""
        ticker = raw.get("ticker", "")
        event_ticker = raw.get("event_ticker", "")
        title = raw.get("title", "")

        # Extract team short name from ticker.
        # Format: KXNBAGAME-26FEB01OKCDEN-OKC  (last segment after final dash)
        # But we also need the event title to get the full short name.
        # Event title format: "Oklahoma City at Denver Winner?"
        # The ticker's last segment is an abbreviation (OKC, DEN, etc.)
        parts = ticker.split("-")
        team_abbrev = parts[-1] if len(parts) >= 3 else ""

        # Parse the event title to get the full short names
        # "Oklahoma City at Denver Winner?" → ["Oklahoma City", "Denver"]
        team_short: Optional[str] = None
        if " at " in title:
            matchup = title.split(" Winner?")[0] if " Winner?" in title else title
            teams = matchup.split(" at ")
            if len(teams) == 2:
                away_name = teams[0].strip()
                home_name = teams[1].strip()
                # Figure out which team this market is for by matching abbreviation
                # Try to match abbrev to one of the team names
                if team_abbrev.upper() in home_name.upper().replace(" ", "").replace(".", ""):
                    team_short = home_name
                elif team_abbrev.upper() in away_name.upper().replace(" ", "").replace(".", ""):
                    team_short = away_name
                else:
                    # Fallback: use abbreviation length heuristic
                    # The market ticker's last segment typically matches the first letters
                    team_short = home_name if ticker.endswith(f"-{team_abbrev}") else away_name

        if not team_short:
            # Can't determine team — skip
            return None

        # Resolve to full name
        team_full = resolve_team_name(team_short, series)

        # Parse prices (in cents, 0–100)
        yes_bid = raw.get("yes_bid")
        yes_ask = raw.get("yes_ask")
        implied_prob = None
        if yes_bid is not None and yes_ask is not None and yes_ask > 0:
            implied_prob = (yes_bid + yes_ask) / 200.0  # cents to 0–1

        # Parse close time
        close_time = None
        if raw.get("close_time"):
            try:
                close_time = datetime.fromisoformat(
                    raw["close_time"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        return KalshiMarket(
            ticker=ticker,
            event_ticker=event_ticker,
            series=series,
            team_short=team_short,
            team_full=team_full,
            yes_bid=yes_bid,
            yes_ask=yes_ask,
            implied_prob=implied_prob,
            volume_24h=raw.get("volume_24h", 0),
            close_time=close_time,
            title=title,
        )

    @staticmethod
    def _pair_markets(markets: List[KalshiMarket], series: str) -> List[KalshiGame]:
        """
        Group markets by event_ticker and pair them into games.
        Each game should have exactly 2 markets (one per team).
        """
        by_event: Dict[str, List[KalshiMarket]] = {}
        for m in markets:
            by_event.setdefault(m.event_ticker, []).append(m)

        games: List[KalshiGame] = []
        for event_ticker, mkt_list in by_event.items():
            if len(mkt_list) != 2:
                continue  # skip incomplete pairs

            # Determine home/away from event title
            # Title: "Away at Home Winner?"
            title = mkt_list[0].title
            home_short, away_short = None, None
            if " at " in title:
                matchup = title.split(" Winner?")[0] if " Winner?" in title else title
                parts = matchup.split(" at ")
                if len(parts) == 2:
                    away_short = parts[0].strip()
                    home_short = parts[1].strip()

            # Assign markets to home/away
            home_market, away_market = None, None
            for m in mkt_list:
                if m.team_short == home_short:
                    home_market = m
                elif m.team_short == away_short:
                    away_market = m

            if not home_market or not away_market:
                # Fallback: just assign by order
                home_market = mkt_list[0]
                away_market = mkt_list[1]
                home_short = home_market.team_short
                away_short = away_market.team_short

            games.append(
                KalshiGame(
                    event_ticker=event_ticker,
                    series=series,
                    home_team_short=home_short or "",
                    away_team_short=away_short or "",
                    home_team_full=home_market.team_full if home_market else None,
                    away_team_full=away_market.team_full if away_market else None,
                    home_market=home_market,
                    away_market=away_market,
                    close_time=home_market.close_time if home_market else None,
                )
            )

        return games

    # -- trading stub -------------------------------------------------------

    async def place_order(self, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Place an order on Kalshi. STUB — requires auth implementation."""
        raise NotImplementedError(
            "Kalshi order placement requires API key + RSA signing. Not yet implemented."
        )
