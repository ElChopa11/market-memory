"""Point-in-time helpers for listings. Knowledge clock is as_of_knowledge."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import as_utc
from mm_listings.models import FilingEvent, IndexEvent, ListingDeal, ListingOutcome
from mm_quant.models import MarketPanel, SeriesBar
from mm_quant.series import bars_for, visible_panel


def visible_deals(deals: tuple[ListingDeal, ...], watermark: datetime) -> tuple[ListingDeal, ...]:
    cut = as_utc(watermark)
    return tuple(
        row
        for row in deals
        if as_utc(row.as_of_knowledge) <= cut and as_utc(row.ingested_at) <= cut
    )


def visible_filings(rows: tuple[FilingEvent, ...], watermark: datetime) -> tuple[FilingEvent, ...]:
    cut = as_utc(watermark)
    return tuple(
        row
        for row in rows
        if as_utc(row.as_of_knowledge) <= cut and as_utc(row.ingested_at) <= cut
    )


def visible_index_events(rows: tuple[IndexEvent, ...], watermark: datetime) -> tuple[IndexEvent, ...]:
    cut = as_utc(watermark)
    return tuple(
        row
        for row in rows
        if as_utc(row.as_of_knowledge) <= cut and as_utc(row.ingested_at) <= cut
    )


def visible_outcomes(rows: tuple[ListingOutcome, ...], watermark: datetime) -> tuple[ListingOutcome, ...]:
    cut = as_utc(watermark)
    return tuple(
        row
        for row in rows
        if as_utc(row.as_of_knowledge) <= cut and as_utc(row.ingested_at) <= cut
    )


def visible_closes(panel: MarketPanel, instrument: str, watermark: datetime) -> tuple[SeriesBar, ...]:
    vis = visible_panel(panel, watermark)
    return bars_for(vis, instrument)
