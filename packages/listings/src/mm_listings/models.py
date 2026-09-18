"""Typed listings / IPO models. Research-only; not an order surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from mm_common.hashing import canonical_json, normalize_numeric, sha256_hex
from mm_common.time import as_utc
from mm_quant.models import ProvenanceRef

ENGINE_VERSION = "imp-017.1"
CARD_FOOTER = (
    "Research only. Listings desk product is not an order, fill, or execution approval. "
    "Quant owns R/sizing. UNTRADEABLE_AT_SIZE is observation only; Risk blocks by rule_id."
)
UNAVAILABLE = "unavailable"
OK = "ok"
PARTIAL = "partial"
STATUS_VALUES = (OK, PARTIAL, UNAVAILABLE)

KIND_IPO = "ipo"
KIND_DIRECT = "direct"
KIND_VALUES = (KIND_IPO, KIND_DIRECT)

FILING_S1 = "S-1"
FILING_F1 = "F-1"
FILING_VALUES = (FILING_S1, FILING_F1)

INDEX_ADD = "add"
INDEX_DELETE = "delete"
INDEX_REBALANCE = "rebalance"
INDEX_KIND_VALUES = (INDEX_ADD, INDEX_DELETE, INDEX_REBALANCE)

QUANT_VERDICTS = (
    "RESEARCH_PRIORITY",
    "MONITOR",
    "DEFER",
    "REJECT",
    "INSUFFICIENT_DATA",
)


def _iso(value: datetime) -> str:
    return as_utc(value).isoformat()


def _num(value: float | None) -> float | None:
    if value is None:
        return None
    return normalize_numeric(value)


@dataclass(frozen=True)
class ListingDeal:
    """Upcoming or recently priced IPO / direct listing. Missing fields stay None."""

    instrument: str
    kind: str
    as_of_knowledge: datetime
    ingested_at: datetime
    pricing_low: float | None = None
    pricing_high: float | None = None
    offer_price: float | None = None
    deal_size_usd: float | None = None
    float_pct: float | None = None
    shares_offered: float | None = None
    shares_outstanding: float | None = None
    lead_underwriters: tuple[str, ...] = ()
    expected_pricing_date: str | None = None
    listing_date: str | None = None
    lockup_expiry: str | None = None
    index_inclusion_eligible: bool | None = None
    filing_type: str | None = None
    filing_as_of: datetime | None = None
    borrow_available: bool | None = None
    spread_bps: float | None = None
    depth_usd: float | None = None
    adv_notional: float | None = None
    observation_id: str | None = None
    fixture_id: str | None = None
    source: str = "fixture"

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument", self.instrument.upper())
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        object.__setattr__(self, "ingested_at", as_utc(self.ingested_at))
        if self.kind not in KIND_VALUES:
            raise ValueError(f"unknown listing kind {self.kind!r}")
        if self.filing_as_of is not None:
            object.__setattr__(self, "filing_as_of", as_utc(self.filing_as_of))

    def provenance(self) -> ProvenanceRef:
        return ProvenanceRef(
            as_of_knowledge=_iso(self.as_of_knowledge),
            observation_id=self.observation_id,
            fixture_id=self.fixture_id,
            instrument=self.instrument,
            metric="listing_deal",
        )

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "kind": self.kind,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "ingested_at": _iso(self.ingested_at),
            "pricing_low": _num(self.pricing_low),
            "pricing_high": _num(self.pricing_high),
            "offer_price": _num(self.offer_price),
            "deal_size_usd": _num(self.deal_size_usd),
            "float_pct": _num(self.float_pct),
            "shares_offered": _num(self.shares_offered),
            "shares_outstanding": _num(self.shares_outstanding),
            "lead_underwriters": list(self.lead_underwriters),
            "expected_pricing_date": self.expected_pricing_date,
            "listing_date": self.listing_date,
            "lockup_expiry": self.lockup_expiry,
            "index_inclusion_eligible": self.index_inclusion_eligible,
            "filing_type": self.filing_type,
            "filing_as_of": None if self.filing_as_of is None else _iso(self.filing_as_of),
            "borrow_available": self.borrow_available,
            "spread_bps": _num(self.spread_bps),
            "depth_usd": _num(self.depth_usd),
            "adv_notional": _num(self.adv_notional),
            "observation_id": self.observation_id,
            "fixture_id": self.fixture_id,
            "source": self.source,
        }


@dataclass(frozen=True)
class FilingEvent:
    instrument: str
    filing_type: str
    as_of_knowledge: datetime
    ingested_at: datetime
    filed_at: datetime | None = None
    name: str = ""
    observation_id: str | None = None
    source: str = "fixture"

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument", self.instrument.upper())
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        object.__setattr__(self, "ingested_at", as_utc(self.ingested_at))
        if self.filed_at is not None:
            object.__setattr__(self, "filed_at", as_utc(self.filed_at))

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "filing_type": self.filing_type,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "ingested_at": _iso(self.ingested_at),
            "filed_at": None if self.filed_at is None else _iso(self.filed_at),
            "name": self.name,
            "observation_id": self.observation_id,
            "source": self.source,
        }


@dataclass(frozen=True)
class IndexEvent:
    """Index add / delete / rebalance. Separate stream from IPO deals."""

    instrument: str
    kind: str
    as_of_knowledge: datetime
    ingested_at: datetime
    effective_date: str | None = None
    index_name: str = ""
    observation_id: str | None = None
    source: str = "fixture"

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument", self.instrument.upper())
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        object.__setattr__(self, "ingested_at", as_utc(self.ingested_at))
        if self.kind not in INDEX_KIND_VALUES:
            raise ValueError(f"unknown index event kind {self.kind!r}")

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "kind": self.kind,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "ingested_at": _iso(self.ingested_at),
            "effective_date": self.effective_date,
            "index_name": self.index_name,
            "observation_id": self.observation_id,
            "source": self.source,
        }


@dataclass(frozen=True)
class ListingOutcome:
    """Closed listing path stored in Market Memory. PIT-gated by as_of_knowledge."""

    instrument: str
    listing_date: str
    as_of_knowledge: datetime
    ingested_at: datetime
    offer_price: float | None = None
    ret_30d: float | None = None
    ret_90d: float | None = None
    reclaimed_offer: bool | None = None
    reclaimed_day1_vwap: bool | None = None
    observation_id: str | None = None
    fixture_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "instrument", self.instrument.upper())
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        object.__setattr__(self, "ingested_at", as_utc(self.ingested_at))

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "listing_date": self.listing_date,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "ingested_at": _iso(self.ingested_at),
            "offer_price": _num(self.offer_price),
            "ret_30d": _num(self.ret_30d),
            "ret_90d": _num(self.ret_90d),
            "reclaimed_offer": self.reclaimed_offer,
            "reclaimed_day1_vwap": self.reclaimed_day1_vwap,
            "observation_id": self.observation_id,
            "fixture_id": self.fixture_id,
        }


@dataclass(frozen=True)
class WarningBlock:
    """Mandatory on every listings idea. Missing stays unavailable — never invented."""

    float_size: float | None
    days_of_price_history: int | None
    borrow_available: bool | None
    spread_bps: float | None
    depth_usd: float | None
    lockup_proximity_days: int | None
    liquidity_verdict: str
    status: str
    notes: tuple[str, ...] = ()

    def canonical(self) -> dict[str, Any]:
        return {
            "float_size": _num(self.float_size),
            "days_of_price_history": self.days_of_price_history,
            "borrow_available": self.borrow_available,
            "spread_bps": _num(self.spread_bps),
            "depth_usd": _num(self.depth_usd),
            "lockup_proximity_days": self.lockup_proximity_days,
            "liquidity_verdict": self.liquidity_verdict,
            "status": self.status,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PostListingTrack:
    instrument: str
    as_of_knowledge: datetime
    listing_date: str | None
    offer_price: float | None
    day1_open: float | None
    day1_high: float | None
    day1_low: float | None
    day1_close: float | None
    day1_vwap: float | None
    day1_vs_offer: float | None
    ret_30d: float | None
    ret_90d: float | None
    drawdown_from_day1_high: float | None
    reclaimed_offer: bool | None
    reclaimed_day1_vwap: bool | None
    days_of_price_history: int | None
    status: str
    gaps: tuple[str, ...] = ()

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "listing_date": self.listing_date,
            "offer_price": _num(self.offer_price),
            "day1_open": _num(self.day1_open),
            "day1_high": _num(self.day1_high),
            "day1_low": _num(self.day1_low),
            "day1_close": _num(self.day1_close),
            "day1_vwap": _num(self.day1_vwap),
            "day1_vs_offer": _num(self.day1_vs_offer),
            "ret_30d": _num(self.ret_30d),
            "ret_90d": _num(self.ret_90d),
            "drawdown_from_day1_high": _num(self.drawdown_from_day1_high),
            "reclaimed_offer": self.reclaimed_offer,
            "reclaimed_day1_vwap": self.reclaimed_day1_vwap,
            "days_of_price_history": self.days_of_price_history,
            "status": self.status,
            "gaps": list(self.gaps),
        }


@dataclass(frozen=True)
class BaseRateSummary:
    n: int
    n_min: int
    claimed: bool
    median_30d: float | None
    reclaim_hit_rate: float | None
    reason: str
    window: str = "own_history"

    def canonical(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "n_min": self.n_min,
            "claimed": self.claimed,
            "median_30d": _num(self.median_30d),
            "reclaim_hit_rate": _num(self.reclaim_hit_rate),
            "reason": self.reason,
            "window": self.window,
        }


@dataclass(frozen=True)
class ListingIdea:
    instrument: str
    kind: str
    deal: ListingDeal
    track: PostListingTrack
    warning: WarningBlock
    liquidity_verdict: str
    quant_verdict: str
    reason_codes: tuple[str, ...]
    observation_only: bool
    trade_math_hash: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "kind": self.kind,
            "deal": self.deal.canonical(),
            "track": self.track.canonical(),
            "warning": self.warning.canonical(),
            "liquidity_verdict": self.liquidity_verdict,
            "quant_verdict": self.quant_verdict,
            "reason_codes": list(self.reason_codes),
            "observation_only": self.observation_only,
            "trade_math_hash": self.trade_math_hash,
        }


@dataclass(frozen=True)
class ListingsSnapshot:
    as_of_knowledge: datetime
    config_version: str
    data_quality: str
    ideas: tuple[ListingIdea, ...]
    index_events: tuple[IndexEvent, ...]
    filings: tuple[FilingEvent, ...]
    base_rates: BaseRateSummary
    gaps: tuple[str, ...]
    provenance: tuple[ProvenanceRef, ...]
    llm_calls: int = 0
    footer: str = CARD_FOOTER
    engine_version: str = ENGINE_VERSION
    payload: dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "config_version": self.config_version,
            "data_quality": self.data_quality,
            "engine_version": self.engine_version,
            "ideas": [row.canonical() for row in self.ideas],
            "index_events": [row.canonical() for row in self.index_events],
            "filings": [row.canonical() for row in self.filings],
            "base_rates": self.base_rates.canonical(),
            "gaps": list(self.gaps),
            "llm_calls": self.llm_calls,
            "footer": self.footer,
            "payload": self.payload,
        }

    def result_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))

    def verdicts(self) -> dict[str, str]:
        return {idea.instrument: idea.liquidity_verdict for idea in self.ideas}
