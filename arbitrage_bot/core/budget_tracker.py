"""
Budget Tracker
==============

Manages the $1,000 project budget across three buckets:
  - API budget:        $60   (TheOddsAPI subscription costs)
  - Betting bankroll:  $200  (active capital for placing bets)
  - Reserve:           $740  (held back until strategy is validated)

Persists state to logs/budget.json so it survives restarts.

Budget release policy:
  Reserve can be moved to bankroll in $100 increments, but only
  when the bot has demonstrated positive P&L over at least 10 settled bets.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_BUDGET_PATH = "logs/budget.json"


@dataclass
class BetRecord:
    """Record of a single bet (for P&L tracking)."""

    bet_id: str
    event_id: str
    outcome: str
    bookmaker: str
    odds: int
    stake: float
    result: Optional[str] = None  # "win", "loss", "pending", "void"
    payout: float = 0.0
    pnl: float = 0.0
    placed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    settled_at: Optional[str] = None


@dataclass
class BudgetState:
    """
    Current budget allocation and P&L state.
    """

    # Allocations
    total_budget: float = 1000.0
    api_budget: float = 60.0
    betting_bankroll: float = 200.0
    reserve: float = 740.0

    # Tracking
    api_spent: float = 0.0
    betting_pnl: float = 0.0  # running P&L on settled bets
    bets_placed: int = 0
    bets_settled: int = 0

    # Bet history
    bets: List[BetRecord] = field(default_factory=list)

    # Metadata
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def active_bankroll(self) -> float:
        """Current bankroll including P&L."""
        return self.betting_bankroll + self.betting_pnl

    @property
    def api_remaining(self) -> float:
        """Remaining API budget."""
        return self.api_budget - self.api_spent

    @property
    def can_bet(self) -> bool:
        """Whether we have enough bankroll to place a minimum bet ($2)."""
        return self.active_bankroll >= 2.0

    @property
    def pending_stakes(self) -> float:
        """Total capital tied up in pending bets."""
        return sum(b.stake for b in self.bets if b.result == "pending")

    @property
    def available_bankroll(self) -> float:
        """Bankroll minus pending stakes."""
        return self.active_bankroll - self.pending_stakes

    @property
    def can_release_reserve(self) -> bool:
        """
        Whether reserve can be released to bankroll.
        Requires: at least 10 settled bets AND positive P&L.
        """
        return self.bets_settled >= 10 and self.betting_pnl > 0 and self.reserve > 0


class BudgetTracker:
    """
    Manages and persists the project budget.

    Usage:
        tracker = BudgetTracker.load()  # or BudgetTracker() for fresh
        tracker.record_bet(...)
        tracker.record_win(...)
        tracker.save()
    """

    def __init__(self, state: Optional[BudgetState] = None, path: str = DEFAULT_BUDGET_PATH) -> None:
        self.state = state or BudgetState()
        self.path = path

    # -- persistence --------------------------------------------------------

    def save(self) -> None:
        """Persist budget state to JSON file."""
        self.state.last_updated = datetime.now(timezone.utc).isoformat()
        filepath = Path(self.path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self.state)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Budget state saved to {filepath}")

    @classmethod
    def load(cls, path: str = DEFAULT_BUDGET_PATH) -> "BudgetTracker":
        """Load budget state from disk, or create fresh if missing."""
        filepath = Path(path)
        if filepath.exists():
            try:
                with open(filepath) as f:
                    data = json.load(f)
                # Reconstruct BetRecords
                bets = [BetRecord(**b) for b in data.pop("bets", [])]
                state = BudgetState(**data)
                state.bets = bets
                logger.info(f"Budget state loaded from {filepath}")
                return cls(state=state, path=path)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to load budget state: {e}. Starting fresh.")

        logger.info("No budget state found. Initializing fresh.")
        return cls(path=path)

    # -- API spending -------------------------------------------------------

    def record_api_spend(self, amount: float) -> None:
        """Record an API cost (e.g. monthly subscription)."""
        self.state.api_spent += amount
        if self.state.api_remaining < 0:
            logger.warning(
                f"⚠️  API budget exceeded! Spent: ${self.state.api_spent:.2f}, "
                f"Budget: ${self.state.api_budget:.2f}"
            )
        self.save()

    # -- bet lifecycle ------------------------------------------------------

    def record_bet(
        self,
        event_id: str,
        outcome: str,
        bookmaker: str,
        odds: int,
        stake: float,
    ) -> Optional[BetRecord]:
        """
        Record a new bet placement.

        Returns None and logs a warning if insufficient bankroll.
        """
        if stake > self.state.available_bankroll:
            logger.warning(
                f"⚠️  Insufficient bankroll for ${stake:.2f} bet. "
                f"Available: ${self.state.available_bankroll:.2f}"
            )
            return None

        if stake > 50.0:
            logger.warning(
                f"⚠️  Stake ${stake:.2f} exceeds $50 single-bet limit. Capping."
            )
            stake = 50.0

        bet = BetRecord(
            bet_id=f"bet_{self.state.bets_placed + 1:06d}",
            event_id=event_id,
            outcome=outcome,
            bookmaker=bookmaker,
            odds=odds,
            stake=stake,
            result="pending",
        )

        self.state.bets.append(bet)
        self.state.bets_placed += 1
        logger.info(f"Bet placed: {bet.bet_id} — {outcome} @ {odds} for ${stake:.2f}")
        self.save()
        return bet

    def record_win(self, bet_id: str) -> None:
        """Mark a pending bet as won and update P&L."""
        bet = self._find_bet(bet_id)
        if not bet:
            logger.warning(f"Bet {bet_id} not found")
            return

        if bet.result != "pending":
            logger.warning(f"Bet {bet_id} is not pending (status: {bet.result})")
            return

        # Calculate payout from American odds
        if bet.odds < 0:
            payout = bet.stake + (bet.stake * 100.0 / abs(bet.odds))
        else:
            payout = bet.stake + (bet.stake * bet.odds / 100.0)

        bet.payout = round(payout, 2)
        bet.pnl = round(payout - bet.stake, 2)
        bet.result = "win"
        bet.settled_at = datetime.now(timezone.utc).isoformat()

        self.state.betting_pnl += bet.pnl
        self.state.bets_settled += 1

        logger.info(
            f"Bet {bet_id} WON: payout ${bet.payout:.2f}, P&L +${bet.pnl:.2f} "
            f"(total P&L: ${self.state.betting_pnl:.2f})"
        )
        self.save()

    def record_loss(self, bet_id: str) -> None:
        """Mark a pending bet as lost and update P&L."""
        bet = self._find_bet(bet_id)
        if not bet:
            logger.warning(f"Bet {bet_id} not found")
            return

        if bet.result != "pending":
            logger.warning(f"Bet {bet_id} is not pending (status: {bet.result})")
            return

        bet.payout = 0.0
        bet.pnl = -bet.stake
        bet.result = "loss"
        bet.settled_at = datetime.now(timezone.utc).isoformat()

        self.state.betting_pnl += bet.pnl
        self.state.bets_settled += 1

        logger.warning(
            f"Bet {bet_id} LOST: -${bet.stake:.2f} "
            f"(total P&L: ${self.state.betting_pnl:.2f})"
        )

        if not self.state.can_bet:
            logger.warning("⚠️  BANKROLL CRITICALLY LOW — cannot place new bets!")

        self.save()

    def record_void(self, bet_id: str) -> None:
        """Mark a bet as voided (push/cancelled). Stake is returned."""
        bet = self._find_bet(bet_id)
        if not bet:
            return

        bet.payout = bet.stake  # stake returned
        bet.pnl = 0.0
        bet.result = "void"
        bet.settled_at = datetime.now(timezone.utc).isoformat()
        self.state.bets_settled += 1

        logger.info(f"Bet {bet_id} VOIDED — stake returned.")
        self.save()

    # -- reserve management -------------------------------------------------

    def release_from_reserve(self, amount: float) -> bool:
        """
        Move funds from reserve to betting bankroll.

        Policy: Only allowed after 10+ settled bets with positive P&L.
        Releases in $100 increments max.

        Returns True if successful, False otherwise.
        """
        if not self.state.can_release_reserve:
            logger.warning(
                f"⚠️  Cannot release reserve yet. Need 10+ settled bets with "
                f"positive P&L. Current: {self.state.bets_settled} settled, "
                f"P&L: ${self.state.betting_pnl:.2f}"
            )
            return False

        amount = min(amount, 100.0)  # max $100 per release
        amount = min(amount, self.state.reserve)  # can't release more than available

        if amount <= 0:
            return False

        self.state.reserve -= amount
        self.state.betting_bankroll += amount
        logger.info(
            f"Released ${amount:.2f} from reserve → bankroll. "
            f"Reserve: ${self.state.reserve:.2f}, Bankroll: ${self.state.active_bankroll:.2f}"
        )
        self.save()
        return True

    # -- helpers ------------------------------------------------------------

    def _find_bet(self, bet_id: str) -> Optional[BetRecord]:
        for bet in self.state.bets:
            if bet.bet_id == bet_id:
                return bet
        return None

    def summary(self) -> str:
        """Return a formatted budget summary string."""
        lines = [
            "=" * 50,
            "💰 BUDGET SUMMARY",
            "=" * 50,
            f"  Total budget:        ${self.state.total_budget:>8.2f}",
            f"  API budget:          ${self.state.api_budget:>8.2f}  (spent: ${self.state.api_spent:.2f})",
            f"  Betting bankroll:    ${self.state.betting_bankroll:>8.2f}",
            f"  Reserve:             ${self.state.reserve:>8.2f}",
            "-" * 50,
            f"  Active bankroll:     ${self.state.active_bankroll:>8.2f}",
            f"  Pending stakes:      ${self.state.pending_stakes:>8.2f}",
            f"  Available:           ${self.state.available_bankroll:>8.2f}",
            f"  Running P&L:         ${self.state.betting_pnl:>+8.2f}",
            f"  Bets: {self.state.bets_placed} placed, {self.state.bets_settled} settled",
            f"  Can bet: {'✅' if self.state.can_bet else '❌'}  |  Can release reserve: {'✅' if self.state.can_release_reserve else '❌'}",
            "=" * 50,
        ]
        return "\n".join(lines)
