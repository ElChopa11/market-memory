"""Quant closed-verdict helper for listings ideas. Not a call. No R/sizing."""

from __future__ import annotations

from mm_flow.verdict import VERDICT_UNTRADEABLE, VERDICT_UNAVAILABLE
from mm_listings.config import ListingsConfig
from mm_listings.models import ListingDeal, PostListingTrack


def listings_quant_verdict(
    deal: ListingDeal,
    track: PostListingTrack,
    *,
    liquidity_verdict: str,
    config: ListingsConfig,
    base_rate_claimed: bool,
) -> tuple[str, tuple[str, ...]]:
    codes: list[str] = []
    days = track.days_of_price_history
    if liquidity_verdict == VERDICT_UNAVAILABLE and days is None:
        return "INSUFFICIENT_DATA", ("listings_feed_unavailable",)
    if days is not None and days < int(config.thin_history_days):
        codes.append("thin_history")
        return "INSUFFICIENT_DATA", tuple(codes)
    if liquidity_verdict == VERDICT_UNTRADEABLE:
        codes.append("untradeable_at_size_observation_only")
        return "DEFER", tuple(codes)
    if not base_rate_claimed:
        codes.append("n_below_min_no_base_rate")
        return "DEFER", tuple(codes)
    if track.reclaimed_offer or track.reclaimed_day1_vwap:
        codes.append("reclaim_observed")
        return "MONITOR", tuple(codes)
    codes.append("listed_path_incomplete")
    return "DEFER", tuple(codes)
