#!/usr/bin/env python3
"""
Sportsbook Arbitrage Runner
============================

Entry point for the sportsbook arb scanner.

Usage:
    # One-shot scan (dry run, prints results):
    python run_sportsbook.py

    # Continuous scanning loop:
    python run_sportsbook.py --loop

    # Specify API key on command line (overrides config/env):
    python run_sportsbook.py --api-key YOUR_KEY

    # Live mode (CAUTION — would execute real bets if placement were implemented):
    python run_sportsbook.py --live

Env vars:
    ODDS_API_KEY     — TheOddsAPI key (preferred over config file)

Config:
    Copy config.yaml.example → config.yaml and fill in your key.
    Or just set the env var — no config file needed for a quick test.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional

# ---------------------------------------------------------------------------
# Ensure the package is importable even without pip install -e .
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arbitrage_bot.api.odds_api_client import OddsAPIClient, Event
from arbitrage_bot.core.arb_engine import ArbEngine, ArbOpportunity, american_to_decimal
from arbitrage_bot.core.budget_tracker import BudgetTracker
from arbitrage_bot.core.opportunity_tracker import OpportunityTracker

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sportsbook_runner")

# ---------------------------------------------------------------------------
# Default sports to scan
# ---------------------------------------------------------------------------
DEFAULT_SPORTS = [
    "americanfootball_nfl",
    "basketball_nba",
    "baseball_mlb",
    "icehockey_nhl",
]

# ---------------------------------------------------------------------------
# State-licensed bookmaker presets
# ---------------------------------------------------------------------------
# Only includes books that (a) are licensed in the state AND (b) appear on
# TheOddsAPI. Offshore books (Bovada, MyBookie, BetOnline, LowVig, BetUS)
# are excluded from all presets — can't legally bet there from the US.
#
# Sources: state gaming commission websites + TheOddsAPI bookmaker list.
# Update these when licensing changes.
# ---------------------------------------------------------------------------
STATE_BOOKMAKERS = {
    "ny": ["fanduel", "draftkings", "betmgm", "caesars"],
    "nj": ["fanduel", "draftkings", "betmgm", "caesars", "betrivers", "unibet"],
    "pa": ["fanduel", "draftkings", "betmgm", "caesars", "betrivers", "unibet", "barstool"],
    "il": ["fanduel", "draftkings", "betmgm", "caesars", "betrivers", "barstool"],
    "nv": ["fanduel", "draftkings", "betmgm", "caesars"],
    "mi": ["fanduel", "draftkings", "betmgm", "caesars", "betrivers", "barstool"],
    "oh": ["fanduel", "draftkings", "betmgm", "caesars", "betrivers", "barstool"],
    "co": ["fanduel", "draftkings", "betmgm", "caesars", "betrivers", "barstool"],
}

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def format_american_odds(price: int) -> str:
    """Format American odds with explicit sign."""
    return f"+{price}" if price > 0 else str(price)


def format_leg(leg, index: int) -> str:
    """Format a single leg of an opportunity."""
    point_str = ""
    if leg.point is not None:
        point_str = f" ({leg.point:+.1f})"

    return (
        f"    • {leg.bookmaker.upper()}: {leg.outcome}{point_str} "
        f"@ {format_american_odds(leg.odds)} "
        f"→ Stake ${leg.stake:.2f}"
    )


def print_opportunity(opp: ArbOpportunity, index: int) -> None:
    """Print a single opportunity in a readable format."""
    strategy_label = (
        "CROSS-BOOK ARB" if opp.strategy == "cross_book_arb" else "VALUE BET"
    )
    edge_pct = opp.edge * 100

    # Flag live (in-progress) games — these move fast
    now = datetime.now(timezone.utc)
    live_tag = " 🔴 LIVE" if opp.expires_at and opp.expires_at <= now else ""

    print(f"\n[{index}] {strategy_label} — {edge_pct:.2f}% edge{live_tag}")
    print(f"    {opp.sport.replace('_', ' ').title()}: {opp.event_name}")
    print(f"    Market: {opp.market_type.upper()}")

    for i, leg in enumerate(opp.legs):
        print(format_leg(leg, i))

    # Calculate expected profit
    total_stake = sum(leg.stake for leg in opp.legs)
    if opp.strategy == "cross_book_arb":
        # Guaranteed profit = edge / (1 - edge) * total_stake ... approx edge * total_stake for small edge
        guaranteed_profit = total_stake * opp.edge / (1.0 - opp.edge)
        print(f"    Guaranteed profit on ${total_stake:.2f} total stake: ${guaranteed_profit:.2f}")
    else:
        # Value bet: expected value
        expected_value = total_stake * opp.edge
        print(f"    Expected value on ${total_stake:.2f} stake: +${expected_value:.2f}")

    if opp.expires_at:
        print(f"    Expires: {opp.expires_at.strftime('%Y-%m-%d %H:%M UTC')}")


def _print_tracked_opportunity(rec: dict, index: int) -> None:
    """Print a tracked opportunity record (serialized dict from OpportunityTracker)."""
    strategy_label = (
        "CROSS-BOOK ARB" if rec["strategy"] == "cross_book_arb" else "VALUE BET"
    )
    edge_pct = rec["edge"] * 100

    # Flag live games
    now = datetime.now(timezone.utc)
    live_tag = ""
    if rec.get("expires_at"):
        try:
            expires = datetime.fromisoformat(rec["expires_at"])
            if expires <= now:
                live_tag = " 🔴 LIVE"
        except (ValueError, TypeError):
            pass

    print(f"  [{index}] {strategy_label} — {edge_pct:.2f}% edge{live_tag}  (id: {rec['id']})")
    print(f"      {rec['sport'].replace('_', ' ').title()}: {rec['event_name']}")
    print(f"      Market: {rec['market_type'].upper()}")

    for leg in rec["legs"]:
        point_str = f" ({leg['point']:+.1f})" if leg.get("point") is not None else ""
        odds_str = f"+{leg['odds']}" if leg["odds"] > 0 else str(leg["odds"])
        print(f"      • {leg['bookmaker'].upper()}: {leg['outcome']}{point_str} @ {odds_str} → ${leg['stake']:.2f}")

    total_stake = sum(leg["stake"] for leg in rec["legs"])
    if rec["strategy"] == "cross_book_arb":
        profit = total_stake * rec["edge"] / (1.0 - rec["edge"])
        print(f"      Guaranteed profit on ${total_stake:.2f} stake: ${profit:.2f}")
    else:
        ev = total_stake * rec["edge"]
        print(f"      Expected value on ${total_stake:.2f} stake: +${ev:.2f}")

    if rec.get("expires_at"):
        print(f"      Expires: {rec['expires_at']}")
    print()


def print_scan_header(
    credits_remaining: Optional[int],
    credits_used: Optional[int],
    num_events: int,
    sports_scanned: List[str],
    dry_run: bool,
) -> None:
    """Print the scan header."""
    mode_label = "DRY RUN" if dry_run else "⚠️  LIVE"
    print("\n" + "=" * 60)
    print(f"  🏈 SPORTSBOOK ARB SCAN  [{mode_label}]")
    print("=" * 60)

    if credits_remaining is not None:
        print(f"  Credits: {credits_remaining:,} remaining", end="")
        if credits_used is not None:
            print(f" ({credits_used:,} used this period)", end="")
        print()

    print(f"  Scanned: {len(sports_scanned)} sports, {num_events} events")
    print(f"  Sports: {', '.join(s.split('_')[-1].upper() for s in sports_scanned)}")
    print("-" * 60)


def print_scan_footer(opportunities: List[ArbOpportunity], dry_run: bool) -> None:
    """Print scan summary footer."""
    print("\n" + "-" * 60)
    if not opportunities:
        print("  No opportunities found.")
    else:
        cross_arbs = [o for o in opportunities if o.strategy == "cross_book_arb"]
        value_bets = [o for o in opportunities if o.strategy == "value_bet"]
        print(f"  Found: {len(cross_arbs)} cross-book arbs, {len(value_bets)} value bets")

    if dry_run:
        print("\n  🛑 DRY RUN — no bets placed.")
        print("     Run with --live to enable execution (when implemented).")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Core scanning logic
# ---------------------------------------------------------------------------


async def run_scan(
    api_key: str,
    sports: List[str],
    bookmakers: Optional[List[str]] = None,
    min_edge: float = 0.005,
    min_edge_value_bet: float = 0.05,
    dry_run: bool = True,
) -> tuple:
    """
    Run a single scan cycle.

    Returns:
        (opportunities, credits_remaining, credits_used, total_events)
    """
    engine = ArbEngine(min_edge=min_edge, min_edge_value_bet=min_edge_value_bet)
    all_events: List[Event] = []

    async with OddsAPIClient(api_key=api_key) as client:
        for sport in sports:
            try:
                logger.info(f"Scanning {sport}...")
                events = await client.get_odds(
                    sport_key=sport,
                    regions=["us"],
                    markets=["h2h", "spreads", "totals"],
                    bookmakers=bookmakers,
                )
                all_events.extend(events)
                logger.info(f"  → {len(events)} events fetched")
            except Exception as e:
                logger.error(f"  ✗ Error scanning {sport}: {e}")
                continue

        # Tag in-progress vs upcoming for display (no filtering — live games
        # are prime arb targets since books update at different speeds)
        now = datetime.now(timezone.utc)
        live_count = sum(1 for e in all_events if e.commence_time <= now)
        if live_count:
            logger.info(f"  {live_count} game(s) currently in progress (included in scan)")

        # Run arb detection
        opportunities = engine.scan_events(all_events)

        return (
            opportunities,
            client.credits_remaining,
            client.credits_used,
            len(all_events),
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sportsbook arbitrage scanner — finds cross-book arb and value bets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="TheOddsAPI key (overrides ODDS_API_KEY env var and config)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously (re-scan every 30s) instead of one-shot",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Live mode. Currently has no effect (bet execution not yet implemented).",
    )
    parser.add_argument(
        "--sports",
        type=str,
        nargs="+",
        default=None,
        help="Sports to scan (default: NFL, NBA, MLB, NHL)",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        choices=list(STATE_BOOKMAKERS.keys()),
        help="Filter to bookmakers licensed in this state (e.g. ny, nj, pa). Overrides --bookmakers.",
    )
    parser.add_argument(
        "--bookmakers",
        type=str,
        nargs="+",
        default=None,
        help="Bookmakers to include (default: all US books). Ignored if --state is set.",
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.005,
        help="Minimum edge for cross-book arb (default: 0.5%%)",
    )
    parser.add_argument(
        "--min-edge-vb",
        type=float,
        default=0.05,
        help="Minimum edge for value bets (default: 5%%)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Scan interval in seconds for --loop mode (default: 30)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # Resolve API key: CLI flag > env var
    api_key = args.api_key or os.environ.get("ODDS_API_KEY", "")
    if not api_key:
        print("❌ No API key found!")
        print("   Set ODDS_API_KEY env var or pass --api-key YOUR_KEY")
        print("   Get a free key at: https://the-odds-api.com/")
        sys.exit(1)

    sports = args.sports or DEFAULT_SPORTS
    dry_run = not args.live

    # Resolve bookmaker list: --state wins over --bookmakers
    bookmakers: Optional[List[str]] = None
    if args.state:
        bookmakers = STATE_BOOKMAKERS[args.state]
        logger.info(f"State filter: {args.state.upper()} → {bookmakers}")
    elif args.bookmakers:
        bookmakers = args.bookmakers

    # Load trackers
    budget = BudgetTracker.load()
    opp_tracker = OpportunityTracker.load()

    print(budget.summary())

    scan_count = 0

    while True:
        scan_count += 1
        if args.loop:
            print(f"\n\n{'─' * 60}")
            print(f"  Scan #{scan_count} — {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
            print(f"{'─' * 60}")

        try:
            (
                opportunities,
                credits_remaining,
                credits_used,
                total_events,
            ) = await run_scan(
                api_key=api_key,
                sports=sports,
                bookmakers=bookmakers,
                min_edge=args.min_edge,
                min_edge_value_bet=args.min_edge_vb,
                dry_run=dry_run,
            )

            # Ingest into tracker — returns only NEW (not recently seen) opportunities
            new_opps = opp_tracker.ingest(opportunities)
            opp_tracker.save()

            # Print header
            print_scan_header(
                credits_remaining=credits_remaining,
                credits_used=credits_used,
                num_events=total_events,
                sports_scanned=sports,
                dry_run=dry_run,
            )

            if args.loop and opportunities:
                # In loop mode: only show NEW opportunities (skip re-seen ones)
                if new_opps:
                    print(f"\n  🆕 {len(new_opps)} NEW opportunity(ies) detected:\n")
                    for i, rec in enumerate(new_opps[:10], 1):
                        _print_tracked_opportunity(rec, i)
                else:
                    print(f"\n  📋 {len(opportunities)} opportunity(ies) on radar (already tracked, no new ones)")
            elif opportunities:
                # One-shot mode: show everything
                for i, opp in enumerate(opportunities[:10], 1):
                    print_opportunity(opp, i)
                if len(opportunities) > 10:
                    print(f"\n  ... and {len(opportunities) - 10} more opportunities")

            print_scan_footer(opportunities, dry_run)

            # In loop mode, show tracker state
            if args.loop:
                print(f"  📊 Tracker: {opp_tracker.summary()}")

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            if not args.loop:
                raise

        if not args.loop:
            break

        logger.info(f"Next scan in {args.interval}s...")
        await asyncio.sleep(args.interval)


if __name__ == "__main__":
    asyncio.run(main())
