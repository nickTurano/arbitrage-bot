"""
Opportunity Tracker
====================

Persists detected opportunities to logs/opportunities.json.
Deduplicates across scans so the same arb isn't re-reported every 30 seconds.

Dedup key: (event_id, market_type, strategy, frozenset of leg bookmakers)
Dedup window: an opportunity is considered "seen" for TTL seconds after
first detection. After that it can be flagged again (in case the line
re-emerges after moving).

Each opportunity record on disk:
    id              — stable dedup key (hash)
    first_seen      — ISO timestamp of first detection
    last_seen       — ISO timestamp of most recent detection
    notified        — whether a Discord alert has been sent
    event_id, event_name, sport, market_type, strategy, edge
    legs            — list of {bookmaker, outcome, odds, point, stake}
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from arbitrage_bot.core.arb_engine import ArbOpportunity

logger = logging.getLogger(__name__)

DEFAULT_PATH = "logs/opportunities.json"
DEFAULT_TTL_SECONDS = 300  # 5 minutes — won't re-flag same opp within this window


def _make_id(opp: ArbOpportunity) -> str:
    """
    Stable dedup ID for an opportunity.
    Based on: event_id + market_type + strategy + sorted bookmaker keys.
    """
    leg_books = sorted(leg.bookmaker for leg in opp.legs)
    raw = f"{opp.event_id}|{opp.market_type}|{opp.strategy}|{','.join(leg_books)}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _serialize_opp(opp: ArbOpportunity, opp_id: str) -> Dict[str, Any]:
    """Convert an ArbOpportunity into a JSON-serializable dict."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": opp_id,
        "first_seen": now,
        "last_seen": now,
        "notified": False,
        "event_id": opp.event_id,
        "event_name": opp.event_name,
        "sport": opp.sport,
        "market_type": opp.market_type,
        "strategy": opp.strategy,
        "edge": opp.edge,
        "legs": [
            {
                "bookmaker": leg.bookmaker,
                "outcome": leg.outcome,
                "odds": leg.odds,
                "implied_prob": leg.implied_prob,
                "stake": leg.stake,
                "point": leg.point,
            }
            for leg in opp.legs
        ],
        "expires_at": opp.expires_at.isoformat() if opp.expires_at else None,
    }


class OpportunityTracker:
    """
    Tracks and deduplicates arbitrage opportunities across scan cycles.

    Usage:
        tracker = OpportunityTracker.load()
        new_opps = tracker.ingest(opportunities)   # returns only NEW ones
        tracker.save()
    """

    def __init__(
        self,
        path: str = DEFAULT_PATH,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self.path = path
        self.ttl_seconds = ttl_seconds
        # In-memory index: opp_id → record dict
        self._records: Dict[str, Dict[str, Any]] = {}

    # -- persistence --------------------------------------------------------

    def save(self) -> None:
        """Write all records to disk."""
        filepath = Path(self.path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(list(self._records.values()), f, indent=2)

    @classmethod
    def load(cls, path: str = DEFAULT_PATH, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> "OpportunityTracker":
        """Load from disk, or start fresh."""
        tracker = cls(path=path, ttl_seconds=ttl_seconds)
        filepath = Path(path)
        if filepath.exists():
            try:
                with open(filepath) as f:
                    records = json.load(f)
                for rec in records:
                    tracker._records[rec["id"]] = rec
                logger.debug(f"Loaded {len(records)} opportunity records from {path}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load opportunity log: {e}. Starting fresh.")
        return tracker

    # -- core logic ---------------------------------------------------------

    def ingest(self, opportunities: List[ArbOpportunity]) -> List[Dict[str, Any]]:
        """
        Process a batch of detected opportunities.

        Returns only the NEW ones (not seen within the TTL window).
        Updates last_seen for previously-seen opportunities.
        """
        now = datetime.now(timezone.utc)
        new_records: List[Dict[str, Any]] = []

        for opp in opportunities:
            opp_id = _make_id(opp)
            existing = self._records.get(opp_id)

            if existing:
                # Already seen — check if it's outside the TTL window
                last_seen = datetime.fromisoformat(existing["last_seen"])
                age_seconds = (now - last_seen).total_seconds()

                # Update last_seen regardless
                existing["last_seen"] = now.isoformat()
                # Update edge if it changed
                existing["edge"] = opp.edge

                if age_seconds < self.ttl_seconds:
                    # Within TTL — not new, skip
                    continue
                else:
                    # Outside TTL — treat as re-emerged, flag as new again
                    existing["notified"] = False
                    new_records.append(existing)
            else:
                # Brand new opportunity
                record = _serialize_opp(opp, opp_id)
                self._records[opp_id] = record
                new_records.append(record)

        return new_records

    def mark_notified(self, opp_id: str) -> None:
        """Mark an opportunity as notified (alert sent)."""
        if opp_id in self._records:
            self._records[opp_id]["notified"] = True

    def get_unnotified(self) -> List[Dict[str, Any]]:
        """Get all opportunities that haven't been notified yet."""
        return [r for r in self._records.values() if not r.get("notified")]

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all tracked opportunities, sorted by edge descending."""
        return sorted(self._records.values(), key=lambda r: r.get("edge", 0), reverse=True)

    def summary(self) -> str:
        """One-line summary of tracker state."""
        total = len(self._records)
        unnotified = len(self.get_unnotified())
        return f"{total} total opportunities tracked, {unnotified} unnotified"
