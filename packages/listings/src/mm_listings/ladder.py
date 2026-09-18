"""Listings subset of the 6c artifact ladder payloads. Quant owns trade math hashes.

Listings inherits trade_math_hash. It does not invent R/sizing. PLAYBOOK types keep
their naming-layer owning desks (intel / ops). Research remains the publishing desk
for the listings screen itself.
"""

from __future__ import annotations

from typing import Any

from mm_listings.models import ListingsSnapshot

LISTINGS_LADDER = ("INTEL_PACKET", "STATE_CARD", "OFFICIAL_BRIEF")


def _state_for(idea) -> str:
    if idea.observation_only:
        return "observation_only"
    if idea.quant_verdict == "INSUFFICIENT_DATA":
        return "thin_history"
    if idea.quant_verdict == "MONITOR":
        return "reclaim_watch"
    return "listed_watch"


def listings_ladder_payloads(snapshot: ListingsSnapshot) -> dict[str, dict[str, Any]]:
    """STATE_CARD / INTEL_PACKET / OFFICIAL_BRIEF bodies. Templates only; no R invented here."""
    primary = snapshot.ideas[0] if snapshot.ideas else None
    instrument = primary.instrument if primary else "NONE"
    math_hash = (
        primary.trade_math_hash if primary and primary.trade_math_hash else "listings_does_not_invent_trade_math"
    )
    no_listing = bool(snapshot.payload.get("no_listing_day"))
    intel = {
        "instrument": instrument,
        "detail": {
            "ideas": [row.canonical() for row in snapshot.ideas],
            "index_events": [row.canonical() for row in snapshot.index_events],
            "filings": [row.canonical() for row in snapshot.filings],
            "base_rates": snapshot.base_rates.canonical(),
            "gaps": list(snapshot.gaps),
        },
        "trade_math_hash": math_hash,
    }
    if primary is None:
        state = {
            "instrument": instrument,
            "state": "no_listing_day" if no_listing else "unavailable",
            "permission": "none",
            "rearm": "next listing or index event",
            "trade_math_hash": math_hash,
        }
        brief = {
            "executive_cut": "no listing day" if no_listing else "listings feed unavailable",
            "trade_math_hash": math_hash,
        }
    else:
        warn = primary.warning.canonical()
        state = {
            "instrument": instrument,
            "state": _state_for(primary),
            "permission": "observation_only" if primary.observation_only else "research",
            "rearm": "lockup expiry" if warn.get("lockup_proximity_days") is not None else "next session",
            "warning": warn,
            "trade_math_hash": math_hash,
        }
        br = snapshot.base_rates
        if br.claimed:
            base_line = f"own-history n={br.n} median_30d={br.median_30d} reclaim_hit_rate={br.reclaim_hit_rate}"
        else:
            base_line = br.reason
        brief = {
            "executive_cut": (
                f"{instrument} {primary.kind} liquidity={primary.liquidity_verdict} "
                f"verdict={primary.quant_verdict}; {base_line}"
            ),
            "warning": warn,
            "trade_math_hash": math_hash,
        }
    return {
        "INTEL_PACKET": intel,
        "STATE_CARD": state,
        "OFFICIAL_BRIEF": brief,
        "trade_math_hash": math_hash,
    }
