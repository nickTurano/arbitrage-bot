"""
FanDuel Client
==============

Wraps TheOddsAPI filtered to the FanDuel bookmaker.
Provides a clean interface for FanDuel-specific odds queries.

Bet execution is STUBBED — FanDuel has no public API for programmatic
bet placement. Future options:
  1. Browser automation via Selenium/Playwright
  2. Reverse-engineered internal API (risky, ToS violation)
  3. Manual placement with alert system (current approach)
"""

import logging
from typing import Any, Dict, List, Optional

from arbitrage_bot.api.odds_api_client import Event, OddsAPIClient, Sport

logger = logging.getLogger(__name__)

FANDUEL_KEY = "fanduel"


class FanDuelClient:
    """
    FanDuel odds client backed by TheOddsAPI.

    Usage:
        async with OddsAPIClient(api_key="...") as odds_client:
            fd = FanDuelClient(odds_client)
            events = await fd.get_odds("americanfootball_nfl")
    """

    def __init__(self, odds_client: OddsAPIClient) -> None:
        self._client = odds_client

    # -- odds ---------------------------------------------------------------

    async def get_sports(self) -> List[Sport]:
        """Get all active sports (not FanDuel-specific, but useful)."""
        return await self._client.get_sports()

    async def get_odds(
        self,
        sport_key: str,
        regions: Optional[List[str]] = None,
        markets: Optional[List[str]] = None,
    ) -> List[Event]:
        """
        Fetch FanDuel odds for a sport.

        Args:
            sport_key: e.g. "americanfootball_nfl"
            regions:   e.g. ["us"]
            markets:   e.g. ["h2h", "spreads", "totals"]

        Returns:
            Events filtered to FanDuel bookmaker only.
            Events where FanDuel has no data are excluded.
        """
        events = await self._client.get_odds(
            sport_key=sport_key,
            regions=regions,
            markets=markets,
            bookmakers=[FANDUEL_KEY],
        )
        # Filter out events where FanDuel returned no data
        return [e for e in events if e.bookmakers]

    # -- execution (stub) ---------------------------------------------------

    async def place_bet(
        self,
        event_id: str,
        outcome: str,
        odds: int,
        stake: float,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Place a bet on FanDuel.

        Currently STUBBED — returns a simulated response in dry_run mode.
        Real execution requires browser automation or undocumented API access.

        Args:
            event_id:  The event to bet on
            outcome:   Which outcome to back (team name or "Over"/"Under")
            odds:      Expected American odds (sanity check)
            stake:     Dollar amount to wager
            dry_run:   If True (default), simulate only

        Returns:
            Dict with keys: status, event_id, outcome, odds, stake, message
        """
        if not dry_run:
            raise NotImplementedError(
                "Live bet execution on FanDuel is not yet implemented. "
                "Use dry_run=True or place bets manually via the FanDuel app."
            )

        logger.info(
            f"[DRY RUN] FanDuel bet simulated: {outcome} @ {odds} "
            f"for ${stake:.2f} on event {event_id}"
        )

        return {
            "status": "simulated",
            "event_id": event_id,
            "outcome": outcome,
            "odds": odds,
            "stake": stake,
            "message": "Dry run — no real bet placed. Enable live execution to bet.",
        }
