"""Mandatory warning block on every listings idea. Missing stays unavailable."""

from __future__ import annotations

from datetime import date, datetime

from mm_common.time import as_utc, parse_utc
from mm_listings.config import ListingsConfig
from mm_listings.models import OK, PARTIAL, UNAVAILABLE, ListingDeal, PostListingTrack, WarningBlock


def _lockup_days(expiry: str | None, watermark: datetime) -> int | None:
    if not expiry:
        return None
    try:
        day = date.fromisoformat(str(expiry)[:10])
    except ValueError:
        try:
            day = parse_utc(str(expiry)).date()
        except (ValueError, TypeError):
            return None
    return (day - as_utc(watermark).date()).days


def warning_block(
    deal: ListingDeal,
    track: PostListingTrack,
    *,
    liquidity_verdict: str,
    watermark: datetime,
    config: ListingsConfig,
) -> WarningBlock:
    notes: list[str] = []
    float_size = None
    if deal.shares_offered is not None:
        float_size = deal.shares_offered
    elif deal.float_pct is not None and deal.shares_outstanding is not None:
        float_size = deal.float_pct * deal.shares_outstanding
    if float_size is None:
        notes.append("float_size unavailable (not invented)")
    days = track.days_of_price_history
    if days is None:
        notes.append("days_of_price_history unavailable (not invented)")
    elif days < int(config.thin_history_days):
        notes.append(f"thin history ({days}d < {config.thin_history_days}d)")
    if deal.borrow_available is None:
        notes.append("borrow_available unavailable (no paid borrow feed)")
    if deal.spread_bps is None:
        notes.append("spread_bps unavailable (not invented)")
    if deal.depth_usd is None:
        notes.append("depth_usd unavailable (not invented)")
    lockup = _lockup_days(deal.lockup_expiry, watermark)
    if lockup is None:
        notes.append("lockup_proximity_days unavailable (not invented)")
    elif abs(lockup) <= int(config.lockup_near_days):
        notes.append(f"lockup within {config.lockup_near_days}d ({lockup}d)")
    missing = [
        name
        for name, value in (
            ("float_size", float_size),
            ("days_of_price_history", days),
            ("borrow_available", deal.borrow_available),
            ("spread_bps", deal.spread_bps),
            ("depth_usd", deal.depth_usd),
            ("lockup_proximity_days", lockup),
        )
        if value is None
    ]
    if liquidity_verdict in {"unavailable", UNAVAILABLE} or missing:
        status = UNAVAILABLE if len(missing) == 6 else PARTIAL
    else:
        status = OK
    if liquidity_verdict == "UNTRADEABLE_AT_SIZE":
        notes.append("UNTRADEABLE_AT_SIZE — observation only; Risk blocks by rule_id")
    if days is None:
        notes.append("SMA200 = n/a (insufficient history: unavailable bars)")
    elif days < 200:
        notes.append(f"SMA200 = n/a (insufficient history: {days} bars)")
    notes.append("listings ideas use post-IPO framework (offer, day-1 VWAP, reclaim, listing base rates) — not SMA200")
    return WarningBlock(
        float_size=float_size,
        days_of_price_history=days,
        borrow_available=deal.borrow_available,
        spread_bps=deal.spread_bps,
        depth_usd=deal.depth_usd,
        lockup_proximity_days=lockup,
        liquidity_verdict=liquidity_verdict,
        status=status,
        notes=tuple(notes),
    )
