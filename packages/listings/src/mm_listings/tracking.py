"""Post-listing tracking: Day-1 OHLC vs offer, VWAP, 30d/90d, drawdown, reclaim.

Reuses the Equities post-IPO reclaim *definitions* (offer / day-1 VWAP reclaim).
Never invents a print. Knowledge clock is as_of_knowledge.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from mm_common.time import as_utc, parse_utc
from mm_listings.models import OK, PARTIAL, UNAVAILABLE, ListingDeal, PostListingTrack
from mm_quant.models import SeriesBar


def _parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        try:
            return parse_utc(str(value)).date()
        except (ValueError, TypeError):
            return None


def _bar_day(bar: SeriesBar) -> date:
    return as_utc(bar.market_time).date()


def _typical(bar: SeriesBar) -> float | None:
    parts = [bar.close]
    if bar.high is not None:
        parts.append(bar.high)
    if bar.low is not None:
        parts.append(bar.low)
    if not parts:
        return None
    return sum(parts) / len(parts)


def day1_vwap(bars: tuple[SeriesBar, ...]) -> float | None:
    """Session VWAP from typical price × volume. Missing volume → unavailable."""
    if not bars:
        return None
    numer = 0.0
    denom = 0.0
    for bar in bars:
        typical = _typical(bar)
        vol = bar.volume
        if typical is None or vol is None or vol <= 0:
            continue
        numer += typical * vol
        denom += vol
    if denom <= 0:
        return None
    return numer / denom


def _close_on_or_after(bars: tuple[SeriesBar, ...], target: date, *, window_days: int) -> float | None:
    end = target + timedelta(days=window_days)
    chosen: SeriesBar | None = None
    for bar in bars:
        day = _bar_day(bar)
        if day < target:
            continue
        if day > end:
            break
        chosen = bar
    if chosen is None:
        return None
    # Prefer a bar on/after the window end when present; otherwise last visible in window.
    for bar in reversed(bars):
        day = _bar_day(bar)
        if day == end or (target <= day <= end and (end - day).days <= 5):
            if day >= target:
                return bar.close
    return chosen.close


def _ret(end: float | None, start: float | None) -> float | None:
    if end is None or start is None or start == 0:
        return None
    return (end / start) - 1.0


def _reclaimed(bars: tuple[SeriesBar, ...], level: float | None, *, after: date) -> bool | None:
    if level is None or not bars:
        return None
    saw_below = False
    reclaimed = False
    for bar in bars:
        if _bar_day(bar) < after:
            continue
        if bar.close < level:
            saw_below = True
        if saw_below and bar.close >= level:
            reclaimed = True
            break
    if not saw_below:
        # Never traded below the level in the visible window — reclaim is not a hit.
        return False
    return reclaimed


def track_listing(
    deal: ListingDeal,
    bars: tuple[SeriesBar, ...],
    watermark: datetime,
) -> PostListingTrack:
    cut = as_utc(watermark)
    visible = tuple(
        bar
        for bar in bars
        if as_utc(bar.as_of_knowledge) <= cut
        and as_utc(bar.ingested_at or bar.as_of_knowledge) <= cut
    )
    listing_day = _parse_day(deal.listing_date)
    gaps: list[str] = []
    day1: tuple[SeriesBar, ...] = ()
    if listing_day is None:
        gaps.append("listing_date")
    else:
        day1 = tuple(bar for bar in visible if _bar_day(bar) == listing_day)
        if not day1:
            gaps.append("day1_bars")

    d_open = day1[0].open if day1 and day1[0].open is not None else (day1[0].close if day1 else None)
    highs = [bar.high for bar in day1 if bar.high is not None]
    lows = [bar.low for bar in day1 if bar.low is not None]
    d_high = max(highs) if highs else (day1[0].close if day1 else None)
    d_low = min(lows) if lows else (day1[0].close if day1 else None)
    d_close = day1[-1].close if day1 else None
    vwap = day1_vwap(day1) if day1 else None
    if day1 and vwap is None:
        gaps.append("day1_vwap")
    offer = deal.offer_price
    if offer is None:
        gaps.append("offer_price")
    vs_offer = _ret(d_close, offer)

    ret_30 = None
    ret_90 = None
    dd = None
    rec_offer = None
    rec_vwap = None
    days_hist = len({_bar_day(bar) for bar in visible}) if visible else (0 if listing_day is not None else None)
    if listing_day is None:
        days_hist = None
        gaps.append("price_history")
    elif days_hist == 0:
        gaps.append("price_history")

    if listing_day is not None and visible:
        post = tuple(bar for bar in visible if _bar_day(bar) >= listing_day)
        ret_30 = _ret(_close_on_or_after(post, listing_day, window_days=30), offer)
        ret_90 = _ret(_close_on_or_after(post, listing_day, window_days=90), offer)
        if d_high is None or d_high <= 0:
            gaps.append("day1_high")
        else:
            trough = None
            for bar in post:
                low = bar.low if bar.low is not None else bar.close
                trough = low if trough is None else min(trough, low)
            if trough is not None:
                dd = (trough / d_high) - 1.0
        rec_offer = _reclaimed(post, offer, after=listing_day)
        rec_vwap = _reclaimed(post, vwap, after=listing_day)
        if ret_30 is None:
            gaps.append("ret_30d")
        if ret_90 is None:
            gaps.append("ret_90d")

    if not visible:
        status = UNAVAILABLE
    elif gaps:
        status = PARTIAL
    else:
        status = OK
    return PostListingTrack(
        instrument=deal.instrument,
        as_of_knowledge=cut,
        listing_date=deal.listing_date,
        offer_price=offer,
        day1_open=d_open,
        day1_high=d_high,
        day1_low=d_low,
        day1_close=d_close,
        day1_vwap=vwap,
        day1_vs_offer=vs_offer,
        ret_30d=ret_30,
        ret_90d=ret_90,
        drawdown_from_day1_high=dd,
        reclaimed_offer=rec_offer,
        reclaimed_day1_vwap=rec_vwap,
        days_of_price_history=days_hist,
        status=status,
        gaps=tuple(gaps),
    )
