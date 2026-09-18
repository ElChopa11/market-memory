"""Compute a PIT listings snapshot. Degrade, never invent. Zero LLM by default.

# Boundary comment: this package must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_flow.config import FlowConfig, load_flow_config
from mm_listings.base_rates import compute_base_rates
from mm_listings.config import ListingsConfig, load_listings_config
from mm_listings.decide import listings_quant_verdict
from mm_listings.liquidity import listings_liquidity_verdict
from mm_listings.models import (
    OK,
    PARTIAL,
    UNAVAILABLE,
    FilingEvent,
    IndexEvent,
    ListingDeal,
    ListingIdea,
    ListingOutcome,
    ListingsSnapshot,
)
from mm_listings.series import visible_deals, visible_filings, visible_index_events
from mm_listings.tracking import track_listing
from mm_listings.warnings import warning_block
from mm_quant.models import MarketPanel, ProvenanceRef, SeriesBar
from mm_quant.series import bars_for, visible_panel


def _quality(*, ideas: tuple[ListingIdea, ...], gaps: tuple[str, ...], missing_feed: bool) -> str:
    if missing_feed:
        return UNAVAILABLE
    if not ideas and not gaps:
        return OK
    statuses = {idea.track.status for idea in ideas}
    if UNAVAILABLE in statuses or PARTIAL in statuses or gaps:
        return PARTIAL
    return OK


def compute_listings(
    *,
    deals: tuple[ListingDeal, ...],
    filings: tuple[FilingEvent, ...] = (),
    index_events: tuple[IndexEvent, ...] = (),
    history: tuple[ListingOutcome, ...] = (),
    panel: MarketPanel | None = None,
    watermark: datetime,
    config: ListingsConfig | None = None,
    flow_config: FlowConfig | None = None,
    repo_root=None,
    missing_feed: bool = False,
    trade_math_by_instrument: dict[str, str] | None = None,
) -> ListingsSnapshot:
    cfg = config or load_listings_config(repo_root)
    flow_cfg = flow_config or (load_flow_config(repo_root) if repo_root is not None else None)
    cut = as_utc(watermark)
    vis_deals = visible_deals(deals, cut)
    vis_filings = visible_filings(filings, cut)
    vis_index = visible_index_events(index_events, cut)
    base = compute_base_rates(history, cut, config=cfg)
    gaps: list[str] = []
    if missing_feed:
        gaps.append("listings_feed")
        vis_deals = ()
        vis_filings = ()
        vis_index = ()
    ideas: list[ListingIdea] = []
    provenance: list[ProvenanceRef] = []
    vis_panel = visible_panel(panel, cut) if panel is not None else None
    math_map = trade_math_by_instrument or {}
    for deal in vis_deals:
        if not deal.instrument:
            gaps.append("instrument")
            continue
        bars: tuple[SeriesBar, ...] = ()
        if vis_panel is not None:
            bars = bars_for(vis_panel, deal.instrument)
        track = track_listing(deal, bars, cut)
        verdict = listings_liquidity_verdict(deal, cut, flow_config=flow_cfg, repo_root=repo_root)
        warn = warning_block(deal, track, liquidity_verdict=verdict, watermark=cut, config=cfg)
        q_verdict, codes = listings_quant_verdict(
            deal,
            track,
            liquidity_verdict=verdict,
            config=cfg,
            base_rate_claimed=base.claimed,
        )
        observation_only = verdict == "UNTRADEABLE_AT_SIZE"
        math_hash = math_map.get(deal.instrument)
        ideas.append(
            ListingIdea(
                instrument=deal.instrument,
                kind=deal.kind,
                deal=deal,
                track=track,
                warning=warn,
                liquidity_verdict=verdict,
                quant_verdict=q_verdict,
                reason_codes=codes,
                observation_only=observation_only,
                trade_math_hash=math_hash,
            )
        )
        provenance.append(deal.provenance())
        for gap in track.gaps:
            gaps.append(f"{deal.instrument}:{gap}")
    unique_gaps = tuple(dict.fromkeys(gaps))
    quality = _quality(ideas=tuple(ideas), gaps=unique_gaps, missing_feed=missing_feed)
    return ListingsSnapshot(
        as_of_knowledge=cut,
        config_version=cfg.version,
        data_quality=quality,
        ideas=tuple(ideas),
        index_events=vis_index,
        filings=vis_filings,
        base_rates=base,
        gaps=unique_gaps,
        provenance=tuple(provenance),
        llm_calls=0,
        payload={
            "n_deals": len(ideas),
            "n_index_events": len(vis_index),
            "n_filings": len(vis_filings),
            "n_history_visible": base.n,
            "no_listing_day": len(ideas) == 0 and len(vis_index) == 0 and not missing_feed,
        },
    )
