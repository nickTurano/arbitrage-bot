"""
Sportsbook Arbitrage Engine
============================

Two strategies:

1. CROSS-BOOK ARBITRAGE
   Same event, different sportsbooks offer different lines.
   If the sum of implied probabilities across the best available
   prices is < 1.0, a risk-free arbitrage exists.

   Math (2-outcome market like h2h):
     implied_prob = american_odds_to_prob(price)
     edge = 1 - (prob_A + prob_B)
     If edge > 0 → arb exists.
     Optimal stakes: stake_i = (bankroll / implied_prob_i) normalized
     so that total_stake = target_total.

2. VALUE BETTING
   Compare a single book's implied probability to a consensus
   estimate (average implied prob across all books).
   If a book offers meaningfully better odds than consensus
   (implied prob is lower → better price for the bettor),
   it's a +EV value bet.

   Edge = consensus_prob - book_implied_prob
   Flag if edge > min_edge_value_bet (default 5%).

Hard limits enforced by the engine:
  - max_single_leg:  $50  (never bet more than this on one leg)
  - max_arb_total:   $100 (max combined stake across all legs of one arb)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from arbitrage_bot.api.odds_api_client import Event, Market

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hard limits — cannot be overridden by config
# ---------------------------------------------------------------------------
MAX_SINGLE_LEG: float = 50.0
MAX_ARB_TOTAL: float = 100.0


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


@dataclass
class ArbLeg:
    """One leg of an arbitrage or value bet."""

    bookmaker: str       # e.g. "fanduel"
    outcome: str         # team name, "Over", "Under", etc.
    odds: int            # American odds
    implied_prob: float  # converted from odds
    stake: float         # recommended dollar amount
    point: Optional[float] = None  # spread/total value if applicable


@dataclass
class ArbOpportunity:
    """A detected arbitrage or value-betting opportunity."""

    event_id: str
    event_name: str      # "Team A vs Team B"
    sport: str           # sport_key
    market_type: str     # h2h | spreads | totals
    strategy: str        # "cross_book_arb" | "value_bet"
    edge: float          # expected profit as decimal (0.03 = 3%)
    legs: List[ArbLeg] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Odds conversion utilities
# ---------------------------------------------------------------------------


def american_to_implied_prob(price: int) -> float:
    """
    Convert American odds to implied probability (0–1).

    Negative odds (favorite):  prob = |price| / (|price| + 100)
    Positive odds (underdog):  prob = 100 / (price + 100)
    """
    if price < 0:
        return abs(price) / (abs(price) + 100.0)
    else:
        return 100.0 / (price + 100.0)


def implied_prob_to_american(prob: float) -> int:
    """
    Convert implied probability back to American odds (rounded).
    """
    if prob <= 0 or prob >= 1:
        raise ValueError(f"Probability must be between 0 and 1, got {prob}")
    if prob >= 0.5:
        return -round((prob * 100) / (1 - prob))
    else:
        return round((100 * (1 - prob)) / prob)


def american_to_decimal(price: int) -> float:
    """
    Convert American odds to decimal odds.

    Decimal odds = 1 / implied_probability (without vig).
    This gives the payout per unit stake (including the stake).
    """
    return 1.0 / american_to_implied_prob(price)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ArbEngine:
    """
    Sportsbook arbitrage detection engine.

    Config keys consumed (all optional, with defaults):
        sportsbooks.min_edge            — minimum edge for cross-book arb (default 0.005)
        sportsbooks.min_edge_value_bet  — minimum edge for value bets (default 0.05)
        budget.max_single_bet           — hard-capped at MAX_SINGLE_LEG ($50)
        budget.max_arb_total            — hard-capped at MAX_ARB_TOTAL ($100)
    """

    def __init__(
        self,
        min_edge: float = 0.005,
        min_edge_value_bet: float = 0.05,
        max_single_bet: float = MAX_SINGLE_LEG,
        max_arb_total: float = MAX_ARB_TOTAL,
    ) -> None:
        # Enforce hard caps regardless of what's passed
        self.min_edge = min_edge
        self.min_edge_value_bet = min_edge_value_bet
        self.max_single_bet = min(max_single_bet, MAX_SINGLE_LEG)
        self.max_arb_total = min(max_arb_total, MAX_ARB_TOTAL)

    # -- main entry ---------------------------------------------------------

    def scan_events(self, events: List[Event]) -> List[ArbOpportunity]:
        """
        Scan a list of events for arbitrage opportunities.

        Checks both cross-book arb and value bets across all
        markets (h2h, spreads, totals) found in the events.

        Args:
            events: List of Event objects with bookmaker odds populated.

        Returns:
            List of ArbOpportunity, sorted by edge descending.
        """
        opportunities: List[ArbOpportunity] = []

        for event in events:
            # Collect all market types present across bookmakers
            market_types = self._collect_market_types(event)

            for market_type in market_types:
                # Cross-book arbitrage
                arbs = self._detect_cross_book_arb(event, market_type)
                opportunities.extend(arbs)

                # Value bets
                vbs = self._detect_value_bets(event, market_type)
                opportunities.extend(vbs)

        # Sort by edge descending (best opportunities first)
        opportunities.sort(key=lambda o: o.edge, reverse=True)
        return opportunities

    # -- cross-book arbitrage -----------------------------------------------

    def _detect_cross_book_arb(
        self, event: Event, market_type: str
    ) -> List[ArbOpportunity]:
        """
        Detect cross-book arbitrage for a specific market type.

        Complementary outcome rules (only these pairs can be arbed):
          h2h:     Team A vs Team B  (two team names, no point)
          spreads: Team A -X  ↔  Team B +X  (same |X|, opposite signs)
          totals:  Over X  ↔  Under X  (same X)

        For each valid complementary pair, we find the best price for
        each side across all bookmakers. If the sum of implied probs
        is < 1.0 AND the best prices come from different books, an
        arbitrage opportunity exists.
        """
        arb_opps: List[ArbOpportunity] = []

        if market_type == "h2h":
            arb_opps.extend(self._detect_h2h_arb(event))
        elif market_type == "spreads":
            arb_opps.extend(self._detect_spread_arb(event))
        elif market_type == "totals":
            arb_opps.extend(self._detect_totals_arb(event))

        return arb_opps

    def _detect_h2h_arb(self, event: Event) -> List[ArbOpportunity]:
        """
        H2H: two outcomes are the two team names. Complementary by definition.
        Find the best price for each team across all books.
        """
        # Collect all h2h prices per team across books
        team_prices: Dict[str, List[Dict[str, Any]]] = {}

        for bm in event.bookmakers:
            market = self._find_market(bm.markets, "h2h")
            if not market:
                continue
            for outcome in market.outcomes:
                team_prices.setdefault(outcome.name, []).append(
                    {
                        "bookmaker": bm.key,
                        "outcome": outcome.name,
                        "odds": outcome.price,
                        "implied_prob": american_to_implied_prob(outcome.price),
                        "point": None,
                    }
                )

        if len(team_prices) != 2:
            return []

        return self._check_two_outcome_arb(event, "h2h", team_prices)

    def _detect_spread_arb(self, event: Event) -> List[ArbOpportunity]:
        """
        Spreads: complementary pair is Team A at -X  ↔  Team B at +X.
        (Same absolute spread value, opposite signs.)

        Group all spread outcomes by absolute point value, then within
        each group pair the negative-point outcome with the positive-point
        outcome. Those two are the only valid arb pair.
        """
        # Collect all spread outcomes: keyed by (abs_point, sign)
        # sign: "neg" for point < 0 (favorite), "pos" for point > 0 (underdog)
        by_abs_point: Dict[float, Dict[str, List[Dict[str, Any]]]] = {}

        for bm in event.bookmakers:
            market = self._find_market(bm.markets, "spreads")
            if not market:
                continue
            for outcome in market.outcomes:
                if outcome.point is None:
                    continue
                abs_pt = abs(outcome.point)
                sign = "neg" if outcome.point < 0 else "pos"

                by_abs_point.setdefault(abs_pt, {}).setdefault(sign, []).append(
                    {
                        "bookmaker": bm.key,
                        "outcome": outcome.name,
                        "odds": outcome.price,
                        "implied_prob": american_to_implied_prob(outcome.price),
                        "point": outcome.point,
                    }
                )

        arb_opps: List[ArbOpportunity] = []
        for abs_pt, sides in by_abs_point.items():
            if "neg" not in sides or "pos" not in sides:
                continue  # need both sides of the spread

            # The complementary pair: favorite (-X) and underdog (+X)
            pair = {
                sides["neg"][0]["outcome"]: sides["neg"],   # e.g. "Flyers" at -1.5
                sides["pos"][0]["outcome"]: sides["pos"],   # e.g. "Kings" at +1.5
            }

            # Sanity: must be two different teams
            if len(pair) != 2:
                continue

            arb_opps.extend(
                self._check_two_outcome_arb(event, "spreads", pair)
            )

        return arb_opps

    def _detect_totals_arb(self, event: Event) -> List[ArbOpportunity]:
        """
        Totals: complementary pair is Over X  ↔  Under X (same X).
        Group by point value, then pair Over with Under.
        """
        # Collect totals outcomes keyed by (point_value, over/under)
        by_point: Dict[float, Dict[str, List[Dict[str, Any]]]] = {}

        for bm in event.bookmakers:
            market = self._find_market(bm.markets, "totals")
            if not market:
                continue
            for outcome in market.outcomes:
                if outcome.point is None:
                    continue
                side = outcome.name.lower()  # "over" or "under"
                if side not in ("over", "under"):
                    continue

                by_point.setdefault(outcome.point, {}).setdefault(side, []).append(
                    {
                        "bookmaker": bm.key,
                        "outcome": outcome.name,
                        "odds": outcome.price,
                        "implied_prob": american_to_implied_prob(outcome.price),
                        "point": outcome.point,
                    }
                )

        arb_opps: List[ArbOpportunity] = []
        for point, sides in by_point.items():
            if "over" not in sides or "under" not in sides:
                continue

            pair = {
                "Over": sides["over"],
                "Under": sides["under"],
            }

            arb_opps.extend(
                self._check_two_outcome_arb(event, "totals", pair)
            )

        return arb_opps

    def _check_two_outcome_arb(
        self,
        event: Event,
        market_type: str,
        outcome_data: Dict[str, List[Dict[str, Any]]],
    ) -> List[ArbOpportunity]:
        """
        Given two outcomes with their best prices across books,
        check if a cross-book arb exists.
        """
        if len(outcome_data) != 2:
            return []

        outcomes = list(outcome_data.values())
        names = list(outcome_data.keys())

        # Find the BEST price (lowest implied prob = best odds for bettor) per outcome
        best_a = min(outcomes[0], key=lambda x: x["implied_prob"])
        best_b = min(outcomes[1], key=lambda x: x["implied_prob"])

        # Must be from different bookmakers for cross-book arb
        if best_a["bookmaker"] == best_b["bookmaker"]:
            return []

        sum_probs = best_a["implied_prob"] + best_b["implied_prob"]
        edge = 1.0 - sum_probs

        if edge < self.min_edge:
            return []

        # Calculate optimal stakes
        # For guaranteed profit on total stake T:
        #   stake_A = T * (1 - implied_prob_A) ... no.
        # Correct formula: to guarantee profit P on a 2-leg arb:
        #   stake_A = T / decimal_odds_A
        #   stake_B = T / decimal_odds_B
        #   where T = stake_A + stake_B (total outlay)
        # Solve: T = T/dec_A + T/dec_B → 1 = 1/dec_A + 1/dec_B
        # That's the break-even. For actual profit, we size so that
        # min(payout_A, payout_B) > T.
        #
        # Simpler: pick T = max_arb_total, then:
        #   stake_A = T * prob_A / (prob_A + prob_B) ... no.
        #
        # Standard Kelly-style: to guarantee payout P on total stake T:
        #   stake_A = P / dec_A,  stake_B = P / dec_B
        #   T = stake_A + stake_B = P * (1/dec_A + 1/dec_B) = P * (prob_A + prob_B)
        #   P = T / (prob_A + prob_B)
        #
        # So: stake_A = T * prob_A / (prob_A + prob_B)
        #     stake_B = T * prob_B / (prob_A + prob_B)
        # Profit = P - T = T * (1/(prob_A+prob_B) - 1) = T * edge / (1 - edge)

        total_stake = self.max_arb_total  # use max available
        prob_sum = best_a["implied_prob"] + best_b["implied_prob"]
        stake_a = total_stake * best_a["implied_prob"] / prob_sum
        stake_b = total_stake * best_b["implied_prob"] / prob_sum

        # Enforce single-leg cap
        if stake_a > self.max_single_bet or stake_b > self.max_single_bet:
            # Scale down to fit
            scale = self.max_single_bet / max(stake_a, stake_b)
            stake_a *= scale
            stake_b *= scale
            total_stake = stake_a + stake_b

        # Round to cents
        stake_a = round(stake_a, 2)
        stake_b = round(stake_b, 2)

        # Determine expiry from event commence time
        expires_at = event.commence_time if event.commence_time else None

        # Clean outcome name for display (strip point suffix)
        name_a = names[0].split("|")[0]
        name_b = names[1].split("|")[0]

        legs = [
            ArbLeg(
                bookmaker=best_a["bookmaker"],
                outcome=name_a,
                odds=best_a["odds"],
                implied_prob=best_a["implied_prob"],
                stake=stake_a,
                point=best_a.get("point"),
            ),
            ArbLeg(
                bookmaker=best_b["bookmaker"],
                outcome=name_b,
                odds=best_b["odds"],
                implied_prob=best_b["implied_prob"],
                stake=stake_b,
                point=best_b.get("point"),
            ),
        ]

        return [
            ArbOpportunity(
                event_id=event.id,
                event_name=event.name,
                sport=event.sport_key,
                market_type=market_type,
                strategy="cross_book_arb",
                edge=round(edge, 6),
                legs=legs,
                expires_at=expires_at,
            )
        ]

    # -- value betting ------------------------------------------------------

    def _detect_value_bets(
        self, event: Event, market_type: str
    ) -> List[ArbOpportunity]:
        """
        Detect value bets by comparing each bookmaker's line to the
        consensus (average implied probability across all books).

        A value bet exists when a book's implied prob for an outcome
        is significantly LOWER than consensus — meaning the book is
        offering better odds than the market average.

        Grouping key: outcome_name + signed point value.
        This ensures we only compare like-for-like:
          - h2h:     "Cowboys" across all books
          - spreads: "Cowboys|-1.5" vs "Cowboys|-1.5" (not vs "Cowboys|+1.5")
          - totals:  "Over|5.5" across all books
        """
        # Collect all implied probs per (outcome, signed point) across books
        outcome_probs: Dict[str, List[Dict[str, Any]]] = {}

        for bm in event.bookmakers:
            market = self._find_market(bm.markets, market_type)
            if not market:
                continue

            for outcome in market.outcomes:
                # Key includes the signed point so spreads don't cross-contaminate
                key = outcome.name
                if outcome.point is not None:
                    key = f"{outcome.name}|{outcome.point}"

                outcome_probs.setdefault(key, []).append(
                    {
                        "bookmaker": bm.key,
                        "outcome": outcome.name,
                        "odds": outcome.price,
                        "implied_prob": american_to_implied_prob(outcome.price),
                        "point": outcome.point,
                    }
                )

        value_bets: List[ArbOpportunity] = []

        for key, entries in outcome_probs.items():
            if len(entries) < 3:
                # Need at least 3 books for a meaningful consensus
                continue

            # Consensus = average implied prob across all books
            consensus = sum(e["implied_prob"] for e in entries) / len(entries)

            for entry in entries:
                # Edge: how much better is this book vs consensus?
                # Positive edge = book's implied prob is LOWER than consensus
                # (meaning the book is offering better odds for the bettor)
                edge = consensus - entry["implied_prob"]

                if edge < self.min_edge_value_bet:
                    continue

                # Stake: scale with edge confidence, capped at max_single_bet
                stake = min(
                    self.max_single_bet * min(edge / 0.10, 1.0),
                    self.max_single_bet,
                )
                stake = round(stake, 2)

                expires_at = event.commence_time if event.commence_time else None

                legs = [
                    ArbLeg(
                        bookmaker=entry["bookmaker"],
                        outcome=entry["outcome"],
                        odds=entry["odds"],
                        implied_prob=entry["implied_prob"],
                        stake=stake,
                        point=entry.get("point"),
                    )
                ]

                value_bets.append(
                    ArbOpportunity(
                        event_id=event.id,
                        event_name=event.name,
                        sport=event.sport_key,
                        market_type=market_type,
                        strategy="value_bet",
                        edge=round(edge, 6),
                        legs=legs,
                        expires_at=expires_at,
                    )
                )

        return value_bets

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _collect_market_types(event: Event) -> List[str]:
        """Get all unique market types present across bookmakers."""
        types: set = set()
        for bm in event.bookmakers:
            for mkt in bm.markets:
                types.add(mkt.key)
        return list(types)

    @staticmethod
    def _find_market(markets: List[Market], market_type: str) -> Optional[Market]:
        """Find a market by type key."""
        for m in markets:
            if m.key == market_type:
                return m
        return None

    # -- cross-platform (Kalshi ↔ Sportsbooks) -----------------------------

    def scan_cross_platform(
        self,
        kalshi_games: List[Any],  # List[KalshiGame] — loose type to avoid circular import
        sportsbook_events: List[Event],
    ) -> List[ArbOpportunity]:
        """
        Compare Kalshi game contract prices against sportsbook h2h lines.

        Kalshi contracts are binary: YES pays $1 if the team wins.
        The yes_mid price (0–1) is the implied probability.

        Sportsbooks express the same probability via American odds on h2h.

        If these diverge across platforms, it's a cross-platform value
        opportunity. We flag when the gap exceeds min_edge_value_bet.

        Note: true risk-free cross-platform arb is harder to execute than
        same-platform arb (different settlement timing, margin requirements).
        We treat these as value bets with a "kalshi_vs_sportsbook" strategy tag.

        Args:
            kalshi_games:      List of KalshiGame objects from KalshiClient
            sportsbook_events: List of Event objects from OddsAPIClient

        Returns:
            List of ArbOpportunity with strategy="cross_platform_value"
        """
        opportunities: List[ArbOpportunity] = []

        # Index sportsbook events by team name for fast lookup
        # Key: team_name → list of (event, h2h_market)
        sb_by_team: Dict[str, List[Dict[str, Any]]] = {}
        for event in sportsbook_events:
            h2h = self._find_market(
                [m for bm in event.bookmakers for m in bm.markets], "h2h"
            )
            if not h2h:
                # Gather h2h from each bookmaker separately
                pass

            for bm in event.bookmakers:
                h2h_mkt = self._find_market(bm.markets, "h2h")
                if not h2h_mkt:
                    continue
                for outcome in h2h_mkt.outcomes:
                    sb_by_team.setdefault(outcome.name, []).append(
                        {
                            "event": event,
                            "bookmaker": bm.key,
                            "outcome": outcome.name,
                            "odds": outcome.price,
                            "implied_prob": american_to_implied_prob(outcome.price),
                        }
                    )

        # For each Kalshi game, try to match against sportsbook events
        for game in kalshi_games:
            opps = self._match_kalshi_game(game, sb_by_team)
            opportunities.extend(opps)

        opportunities.sort(key=lambda o: o.edge, reverse=True)
        return opportunities

    def _match_kalshi_game(
        self, game: Any, sb_by_team: Dict[str, List[Dict[str, Any]]]
    ) -> List[ArbOpportunity]:
        """
        Match one Kalshi game against sportsbook data and detect divergences.
        """
        opps: List[ArbOpportunity] = []

        # Check each side of the Kalshi game
        for market, team_full in [
            (game.home_market, game.home_team_full),
            (game.away_market, game.away_team_full),
        ]:
            if not market or not team_full or market.implied_prob is None:
                continue
            if market.volume_24h < 5:
                # Skip illiquid Kalshi markets
                continue

            kalshi_prob = market.implied_prob

            # Find sportsbook prices for the same team in the same matchup
            sb_entries = sb_by_team.get(team_full, [])
            if not sb_entries:
                continue

            # Determine the opponent from the Kalshi game
            opponent_full = (
                game.away_team_full
                if team_full == game.home_team_full
                else game.home_team_full
            )

            # Both teams must be resolved to verify it's the same game
            if not opponent_full:
                logger.debug(f"Skipping {team_full}: opponent not resolved")
                continue

            # Match sportsbook entries where:
            #   1. The event contains the opponent as the other team
            #   2. The game date is within 12 hours (same game, not a future matchup)
            kalshi_close = market.close_time
            matched_sb: List[Dict[str, Any]] = []
            for entry in sb_entries:
                event = entry["event"]
                event_teams = {event.home_team, event.away_team}

                # Opponent must be in the sportsbook event
                if opponent_full not in event_teams:
                    continue

                # Date proximity check: Kalshi close_time should be within
                # ~12 hours of the sportsbook commence_time (same game)
                if kalshi_close and event.commence_time:
                    from datetime import timedelta
                    delta = abs((kalshi_close - event.commence_time).total_seconds())
                    if delta > 43200:  # 12 hours
                        continue

                matched_sb.append(entry)

            if not matched_sb:
                continue

            # Get sportsbook consensus implied prob for this team
            sb_probs = [e["implied_prob"] for e in matched_sb]
            sb_consensus = sum(sb_probs) / len(sb_probs)

            # Compare Kalshi vs sportsbook consensus
            # Edge = how much better one platform is vs the other
            # If Kalshi prob < sb_consensus: Kalshi is offering better odds
            #   → buy YES on Kalshi (it's underpriced)
            # If Kalshi prob > sb_consensus: sportsbooks are offering better odds
            #   → bet against this team on sportsbooks (they're underpriced)

            edge = abs(kalshi_prob - sb_consensus)
            if edge < self.min_edge_value_bet:
                continue

            # Determine the recommended action
            if kalshi_prob < sb_consensus:
                # Kalshi is cheaper — buy YES on Kalshi
                action_platform = "kalshi"
                action_desc = f"BUY YES on Kalshi ({market.ticker})"
                stake = min(
                    self.max_single_bet * min(edge / 0.10, 1.0),
                    self.max_single_bet,
                )
                legs = [
                    ArbLeg(
                        bookmaker="kalshi",
                        outcome=f"{team_full} (YES)",
                        odds=implied_prob_to_american(kalshi_prob),
                        implied_prob=kalshi_prob,
                        stake=round(stake, 2),
                        point=None,
                    )
                ]
            else:
                # Sportsbooks are cheaper — bet this team on the best sportsbook
                best_sb = min(matched_sb, key=lambda e: e["implied_prob"])
                action_platform = best_sb["bookmaker"]
                action_desc = f"BET {team_full} on {best_sb['bookmaker']}"
                stake = min(
                    self.max_single_bet * min(edge / 0.10, 1.0),
                    self.max_single_bet,
                )
                legs = [
                    ArbLeg(
                        bookmaker=best_sb["bookmaker"],
                        outcome=team_full,
                        odds=best_sb["odds"],
                        implied_prob=best_sb["implied_prob"],
                        stake=round(stake, 2),
                        point=None,
                    )
                ]

            event_name = f"{game.away_team_full or game.away_team_short} vs {game.home_team_full or game.home_team_short}"
            expires_at = market.close_time

            opps.append(
                ArbOpportunity(
                    event_id=game.event_ticker,
                    event_name=event_name,
                    sport=game.series,
                    market_type="h2h_cross_platform",
                    strategy="cross_platform_value",
                    edge=round(edge, 6),
                    legs=legs,
                    expires_at=expires_at,
                )
            )

        return opps
