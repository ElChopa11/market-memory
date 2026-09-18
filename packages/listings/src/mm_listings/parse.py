"""Parse listing deals / filings / history from mappings. Degrade, never invent."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_common.time import parse_utc
from mm_listings.models import (
    FILING_F1,
    FILING_S1,
    INDEX_KIND_VALUES,
    KIND_DIRECT,
    KIND_IPO,
    FilingEvent,
    IndexEvent,
    ListingDeal,
    ListingOutcome,
)


def _ts(raw: dict[str, Any], *keys: str, fallback: datetime | None = None) -> datetime:
    for key in keys:
        if raw.get(key):
            return parse_utc(str(raw[key]))
    if fallback is not None:
        return fallback
    raise ValueError(f"missing timestamp among {keys}")


def _float(raw: dict[str, Any], key: str) -> float | None:
    value = raw.get(key)
    if value in (None, "", "unavailable"):
        return None
    return float(value)


def _bool(raw: dict[str, Any], key: str) -> bool | None:
    value = raw.get(key)
    if value in (None, "", "unavailable"):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return None


def parse_deal(raw: dict[str, Any], *, fixture_id: str | None, fallback: datetime) -> ListingDeal:
    kind = str(raw.get("kind") or KIND_IPO).lower()
    if kind not in {KIND_IPO, KIND_DIRECT}:
        kind = KIND_IPO
    known = _ts(raw, "as_of_knowledge", "ingested_at", fallback=fallback)
    ingested = _ts(raw, "ingested_at", "as_of_knowledge", fallback=known)
    filing_as_of = None
    if raw.get("filing_as_of"):
        filing_as_of = parse_utc(str(raw["filing_as_of"]))
    underwriters = tuple(str(item) for item in (raw.get("lead_underwriters") or ()) if item)
    filing_type = raw.get("filing_type")
    if filing_type not in {FILING_S1, FILING_F1, None}:
        filing_type = str(filing_type) if filing_type else None
    return ListingDeal(
        instrument=str(raw.get("instrument") or raw.get("symbol") or "").upper(),
        kind=kind,
        as_of_knowledge=known,
        ingested_at=ingested,
        pricing_low=_float(raw, "pricing_low"),
        pricing_high=_float(raw, "pricing_high"),
        offer_price=_float(raw, "offer_price"),
        deal_size_usd=_float(raw, "deal_size_usd"),
        float_pct=_float(raw, "float_pct"),
        shares_offered=_float(raw, "shares_offered"),
        shares_outstanding=_float(raw, "shares_outstanding"),
        lead_underwriters=underwriters,
        expected_pricing_date=None if not raw.get("expected_pricing_date") else str(raw["expected_pricing_date"]),
        listing_date=None if not raw.get("listing_date") else str(raw["listing_date"])[:10],
        lockup_expiry=None if not raw.get("lockup_expiry") else str(raw["lockup_expiry"])[:10],
        index_inclusion_eligible=_bool(raw, "index_inclusion_eligible"),
        filing_type=None if filing_type in (None, "") else str(filing_type),
        filing_as_of=filing_as_of,
        borrow_available=_bool(raw, "borrow_available"),
        spread_bps=_float(raw, "spread_bps"),
        depth_usd=_float(raw, "depth_usd"),
        adv_notional=_float(raw, "adv_notional"),
        observation_id=None if raw.get("observation_id") is None else str(raw["observation_id"]),
        fixture_id=str(raw.get("fixture_id") or fixture_id) if (raw.get("fixture_id") or fixture_id) else None,
        source=str(raw.get("source") or "fixture"),
    )


def parse_filing(raw: dict[str, Any], *, fallback: datetime) -> FilingEvent:
    known = _ts(raw, "as_of_knowledge", "ingested_at", fallback=fallback)
    ingested = _ts(raw, "ingested_at", "as_of_knowledge", fallback=known)
    filed = parse_utc(str(raw["filed_at"])) if raw.get("filed_at") else None
    filing_type = str(raw.get("filing_type") or FILING_S1)
    return FilingEvent(
        instrument=str(raw.get("instrument") or "").upper(),
        filing_type=filing_type,
        as_of_knowledge=known,
        ingested_at=ingested,
        filed_at=filed,
        name=str(raw.get("name") or f"{filing_type} filing"),
        observation_id=None if raw.get("observation_id") is None else str(raw["observation_id"]),
        source=str(raw.get("source") or "fixture"),
    )


def parse_index_event(raw: dict[str, Any], *, fallback: datetime) -> IndexEvent:
    kind = str(raw.get("kind") or raw.get("action") or "rebalance").lower()
    if kind not in INDEX_KIND_VALUES:
        kind = "rebalance"
    known = _ts(raw, "as_of_knowledge", "ingested_at", fallback=fallback)
    ingested = _ts(raw, "ingested_at", "as_of_knowledge", fallback=known)
    return IndexEvent(
        instrument=str(raw.get("instrument") or raw.get("symbol") or "").upper(),
        kind=kind,
        as_of_knowledge=known,
        ingested_at=ingested,
        effective_date=None if not raw.get("effective_date") else str(raw["effective_date"])[:10],
        index_name=str(raw.get("index_name") or raw.get("index") or ""),
        observation_id=None if raw.get("observation_id") is None else str(raw["observation_id"]),
        source=str(raw.get("source") or "fixture"),
    )


def parse_outcome(raw: dict[str, Any], *, fixture_id: str | None, fallback: datetime) -> ListingOutcome:
    known = _ts(raw, "as_of_knowledge", "ingested_at", fallback=fallback)
    ingested = _ts(raw, "ingested_at", "as_of_knowledge", fallback=known)
    rec_offer = _bool(raw, "reclaimed_offer")
    rec_vwap = _bool(raw, "reclaimed_day1_vwap")
    return ListingOutcome(
        instrument=str(raw.get("instrument") or "").upper(),
        listing_date=str(raw.get("listing_date") or "")[:10],
        as_of_knowledge=known,
        ingested_at=ingested,
        offer_price=_float(raw, "offer_price"),
        ret_30d=_float(raw, "ret_30d"),
        ret_90d=_float(raw, "ret_90d"),
        reclaimed_offer=rec_offer,
        reclaimed_day1_vwap=rec_vwap,
        observation_id=None if raw.get("observation_id") is None else str(raw["observation_id"]),
        fixture_id=str(raw.get("fixture_id") or fixture_id) if (raw.get("fixture_id") or fixture_id) else None,
    )
