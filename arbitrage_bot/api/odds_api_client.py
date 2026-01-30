"""
TheOddsAPI Client
=================

Fetches live odds from multiple sportsbooks via TheOddsAPI.
Uses American odds format (moneyline integers).

Tracks remaining API credits via response headers:
  X-Requests-Remaining  — credits left this billing period
  X-Requests-Used       — credits consumed so far

Base URL: https://api.the-odds-api.com/v4
Auth:     ?apiKey={key} query parameter

Credit cost per request = number of bookmakers returned.
We guard against exhaustion: raise OddsAPIError if < 10 credits remain.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Sport:
    sport_key: str
    title: str
    active: bool = True


@dataclass
class Outcome:
    name: str
    price: int  # American odds (e.g. -150, +240)
    point: Optional[float] = None  # spread / total value, if applicable


@dataclass
class Market:
    key: str  # h2h | spreads | totals
    outcomes: List[Outcome] = field(default_factory=list)


@dataclass
class Bookmaker:
    key: str  # e.g. "fanduel"
    title: str
    last_update: Optional[datetime] = None
    markets: List[Market] = field(default_factory=list)


@dataclass
class Event:
    id: str
    sport_key: str
    commence_time: datetime
    home_team: str
    away_team: str
    bookmakers: List[Bookmaker] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.home_team} vs {self.away_team}"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class OddsAPIError(Exception):
    """Raised on API errors or credit exhaustion."""

    pass


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class OddsAPIClient:
    """
    Async client for TheOddsAPI v4.

    Usage:
        async with OddsAPIClient(api_key="...") as client:
            sports = await client.get_sports()
            events = await client.get_odds("americanfootball_nfl")
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("ODDS_API_KEY", "")
        if not self.api_key:
            raise OddsAPIError(
                "No API key provided. Pass api_key= or set ODDS_API_KEY env var. "
                "Get a free key at https://the-odds-api.com/"
            )
        self._session: Optional[aiohttp.ClientSession] = None
        self.credits_remaining: Optional[int] = None
        self.credits_used: Optional[int] = None

    # -- session lifecycle --------------------------------------------------

    async def __aenter__(self) -> "OddsAPIClient":
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

    # -- credit guard -------------------------------------------------------

    def _check_credits(self) -> None:
        """Raise if we're dangerously low on credits."""
        if self.credits_remaining is not None and self.credits_remaining < 10:
            raise OddsAPIError(
                f"API credits nearly exhausted: {self.credits_remaining} remaining. "
                "Renew at https://the-odds-api.com/"
            )

    def _update_credits(self, headers: Dict[str, str]) -> None:
        """Parse credit headers from response."""
        remaining = headers.get("X-Requests-Remaining")
        used = headers.get("X-Requests-Used")
        if remaining is not None:
            self.credits_remaining = int(remaining)
        if used is not None:
            self.credits_used = int(used)

    # -- internal request ---------------------------------------------------

    async def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        """Make an authenticated GET request."""
        self._check_credits()
        session = self._ensure_session()

        all_params: Dict[str, str] = {"apiKey": self.api_key}
        if params:
            all_params.update(params)

        url = f"{BASE_URL}{path}"
        async with session.get(url, params=all_params) as resp:
            self._update_credits(dict(resp.headers))

            if resp.status == 401:
                raise OddsAPIError("Authentication failed — check your API key.")
            if resp.status == 429:
                raise OddsAPIError("Rate limited by TheOddsAPI. Back off and retry.")
            if resp.status != 200:
                body = await resp.text()
                raise OddsAPIError(f"HTTP {resp.status}: {body}")

            return await resp.json()

    # -- public API ---------------------------------------------------------

    async def get_sports(self) -> List[Sport]:
        """
        List all available sports.

        Returns:
            List of Sport objects (only active ones).
        """
        data = await self._get("/sports")
        return [
            Sport(
                sport_key=s["sport_key"],
                title=s["title"],
                active=s.get("active", True),
            )
            for s in data
            if s.get("active", True)
        ]

    async def get_odds(
        self,
        sport_key: str,
        regions: Optional[List[str]] = None,
        markets: Optional[List[str]] = None,
        bookmakers: Optional[List[str]] = None,
    ) -> List[Event]:
        """
        Fetch current odds for a sport.

        Args:
            sport_key:   e.g. "americanfootball_nfl"
            regions:     e.g. ["us"] — determines which bookmakers are returned
            markets:     e.g. ["h2h", "spreads", "totals"]
            bookmakers:  filter to specific books, e.g. ["fanduel", "draftkings"]

        Returns:
            List of Event objects with bookmaker odds populated.

        Note:
            Each bookmaker returned per event costs 1 API credit.
            Pass bookmakers= to limit credits consumed.
        """
        regions = regions or ["us"]
        markets = markets or ["h2h"]

        params: Dict[str, str] = {
            "regions": ",".join(regions),
            "markets": ",".join(markets),
        }
        if bookmakers:
            params["bookmakers"] = ",".join(bookmakers)

        data = await self._get(f"/sports/{sport_key}/odds", params=params)
        return [self._parse_event(e) for e in data]

    async def get_event_odds(
        self,
        sport_key: str,
        event_ids: List[str],
        regions: Optional[List[str]] = None,
        markets: Optional[List[str]] = None,
    ) -> List[Event]:
        """
        Fetch odds for specific events only.

        Args:
            sport_key:  e.g. "americanfootball_nfl"
            event_ids:  list of event IDs to query
            regions:    e.g. ["us"]
            markets:    e.g. ["h2h", "spreads", "totals"]

        Returns:
            List of Event objects matching the requested IDs.
        """
        regions = regions or ["us"]
        markets = markets or ["h2h"]

        params: Dict[str, str] = {
            "regions": ",".join(regions),
            "markets": ",".join(markets),
            "eventIds": ",".join(event_ids),
        }

        data = await self._get(f"/sports/{sport_key}/odds", params=params)
        return [self._parse_event(e) for e in data]

    # -- parsing ------------------------------------------------------------

    @staticmethod
    def _parse_event(raw: Dict[str, Any]) -> Event:
        """Parse a raw API event dict into an Event dataclass."""
        bookmakers: List[Bookmaker] = []

        for bm in raw.get("bookmakers", []):
            markets: List[Market] = []
            for mkt in bm.get("markets", []):
                outcomes = [
                    Outcome(
                        name=o["name"],
                        price=int(o["price"]),
                        point=o.get("point"),
                    )
                    for o in mkt.get("outcomes", [])
                ]
                markets.append(Market(key=mkt["key"], outcomes=outcomes))

            last_update = None
            if bm.get("last_update"):
                try:
                    last_update = datetime.fromisoformat(
                        bm["last_update"].replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass

            bookmakers.append(
                Bookmaker(
                    key=bm["key"],
                    title=bm.get("title", bm["key"]),
                    last_update=last_update,
                    markets=markets,
                )
            )

        commence_time = datetime.fromisoformat(
            raw["commence_time"].replace("Z", "+00:00")
        )

        return Event(
            id=raw["id"],
            sport_key=raw["sport_key"],
            commence_time=commence_time,
            home_team=raw["home_team"],
            away_team=raw["away_team"],
            bookmakers=bookmakers,
        )
