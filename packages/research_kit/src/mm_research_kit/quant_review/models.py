"""Quant Review Board types. Research-only; not a call generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


ENGINE_VERSION = "imp-001.1"
BOARD_FOOTER = "Research only. Not a trade instruction, allocation decision, or execution approval."
MAX_RESEARCH_PRIORITY = 3
UNUSUAL_SESSION_PP = 2.0
STALE_AFTER_HOURS_DEFAULT = 36
RECLAIM_MIN_HOLD_SESSIONS = 2

LABEL_RELATIVE_VALUE = "RELATIVE_VALUE"
LABEL_RECLAIM_CANDIDATE = "RECLAIM_CANDIDATE"
LABEL_UNEXECUTABLE_ARB = "UNEXECUTABLE_ARB"
LABEL_ARBITRAGE = "ARBITRAGE"


class QuantVerdict(StrEnum):
    RESEARCH_PRIORITY = "RESEARCH_PRIORITY"
    MONITOR = "MONITOR"
    DEFER = "DEFER"
    REJECT = "REJECT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class QuantReasonCode(StrEnum):
    NO_MISPRICING = "NO_MISPRICING"
    NO_CATALYST = "NO_CATALYST"
    RECLAIM_UNCONFIRMED = "RECLAIM_UNCONFIRMED"
    ALREADY_PRICED = "ALREADY_PRICED"
    DUPLICATE_BETA = "DUPLICATE_BETA"
    CORRELATED_EXPOSURE = "CORRELATED_EXPOSURE"
    INADEQUATE_LIQUIDITY = "INADEQUATE_LIQUIDITY"
    STALE_OR_PARTIAL_DATA = "STALE_OR_PARTIAL_DATA"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    UNEXECUTABLE_ARB = "UNEXECUTABLE_ARB"
    EVENT_RISK = "EVENT_RISK"
    DILUTION_OR_LOCKUP_RISK = "DILUTION_OR_LOCKUP_RISK"
    THESIS_NOT_FALSIFIABLE = "THESIS_NOT_FALSIFIABLE"


class QuantTrack(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


VERDICT_VALUES = tuple(v.value for v in QuantVerdict)
REASON_CODE_VALUES = tuple(c.value for c in QuantReasonCode)
TRACK_VALUES = tuple(t.value for t in QuantTrack)

PROMOTION_CRITERIA = (
    "fresh_attributable_data",
    "defined_benchmark_peers",
    "specific_anomaly",
    "overlooked_reason",
    "catalyst_or_trigger",
    "single_falsifiable_invalidation",
    "acceptable_liquidity",
    "no_unaddressed_duplicate_beta_or_dq",
    "independent_skeptic_review_required",
)

BLOCKING_PROMOTION_CODES = frozenset(
    {
        QuantReasonCode.NO_MISPRICING,
        QuantReasonCode.NO_CATALYST,
        QuantReasonCode.RECLAIM_UNCONFIRMED,
        QuantReasonCode.ALREADY_PRICED,
        QuantReasonCode.DUPLICATE_BETA,
        QuantReasonCode.CORRELATED_EXPOSURE,
        QuantReasonCode.INADEQUATE_LIQUIDITY,
        QuantReasonCode.STALE_OR_PARTIAL_DATA,
        QuantReasonCode.INSUFFICIENT_HISTORY,
        QuantReasonCode.UNEXECUTABLE_ARB,
        QuantReasonCode.EVENT_RISK,
        QuantReasonCode.DILUTION_OR_LOCKUP_RISK,
        QuantReasonCode.THESIS_NOT_FALSIFIABLE,
    }
)


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    raw_symbols: tuple[str, ...]
    asset_class: str
    venue: str
    sector: str
    benchmark: str
    peers: tuple[str, ...]
    tracks: tuple[str, ...]
    post_ipo: bool = False
    listing_date: str | None = None
    role: str = "name"


@dataclass(frozen=True)
class UniverseSpec:
    version: str
    status: str
    kind: str
    instruments: tuple[InstrumentSpec, ...]
    symbol_map: dict[str, str]
    peer_groups: dict[str, tuple[str, ...]]
    arb_pairs: tuple[tuple[str, str, str], ...]
    notes: tuple[str, ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()

    def by_symbol(self) -> dict[str, InstrumentSpec]:
        return {row.symbol: row for row in self.instruments}


@dataclass(frozen=True)
class EvidenceRow:
    claim: str
    source: str
    timestamp: str
    capture: str
    evidence_confidence: float
    provenance: str


@dataclass(frozen=True)
class InstrumentPrint:
    raw_symbol: str
    symbol: str
    last: float | None
    chg: float | None
    chg_pct: float | None
    source: str
    timestamp: str
    capture: str
    data_quality: str = "ok"
    evidence_confidence: float = 0.4


@dataclass(frozen=True)
class SeriesOverlay:
    symbol: str
    source: str
    asof: str
    captured_at: str
    last_close: float | None = None
    ret_short: float | None = None
    ret_long: float | None = None
    rel_short: float | None = None
    rel_long: float | None = None
    rv_20d: float | None = None
    rv_60d: float | None = None
    mdd: float | None = None
    n_bars: int | None = None
    bench: str | None = None
    data_quality: str = "ok"
    notes: str = ""
    adv: float | None = None


@dataclass(frozen=True)
class MemoryOverlay:
    symbol: str
    observation_id: str
    metric: str
    value: str | None
    data_quality: str
    as_of_knowledge: str
    claim_hash: str | None = None


@dataclass(frozen=True)
class ReclaimObservables:
    prior_breakdown_level: str | None = None
    reclaim_of_level: str | None = None
    hold_sessions: int = 0
    notes: str = ""

    @property
    def confirmed(self) -> bool:
        return bool(
            self.prior_breakdown_level
            and self.reclaim_of_level
            and self.hold_sessions >= RECLAIM_MIN_HOLD_SESSIONS
        )


@dataclass(frozen=True)
class ArbPackage:
    venue_a: str | None = None
    venue_b: str | None = None
    same_or_convertible_exposure: bool = False
    gross_spread: float | None = None
    costs_complete: bool = False
    fill_size: float | None = None
    liquidity_note: str | None = None
    latency_ops_risk: str | None = None
    net_after_costs: float | None = None

    @property
    def complete_executable(self) -> bool:
        return bool(
            self.venue_a
            and self.venue_b
            and self.same_or_convertible_exposure
            and self.gross_spread is not None
            and self.costs_complete
            and self.fill_size is not None
            and self.liquidity_note
            and self.latency_ops_risk
            and self.net_after_costs is not None
            and self.net_after_costs > 0
        )


@dataclass(frozen=True)
class PromotionChecklist:
    fresh_attributable_data: bool
    defined_benchmark_peers: bool
    specific_anomaly: bool
    overlooked_reason: bool
    catalyst_or_trigger: bool
    single_falsifiable_invalidation: bool
    acceptable_liquidity: bool
    no_unaddressed_duplicate_beta_or_dq: bool
    independent_skeptic_review_required: bool
    independent_skeptic_verdict: str = "pending"

    @property
    def all_met(self) -> bool:
        return all(getattr(self, name) for name in PROMOTION_CRITERIA)

    def as_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name) for name in PROMOTION_CRITERIA
        } | {"independent_skeptic_verdict": self.independent_skeptic_verdict}


@dataclass
class QuantCard:
    instrument: str
    raw_symbols: tuple[str, ...]
    review_date: str
    as_of_knowledge: str
    tracks: tuple[str, ...]
    sector: str
    benchmark: str
    peers: tuple[str, ...]
    data_quality: str
    unusual: str
    evidence: tuple[EvidenceRow, ...]
    relative_and_structure: str
    why_overlooked: str
    alternative_case: str
    catalyst: str
    invalidation: str
    liquidity: str
    verdict: str
    reason_codes: tuple[str, ...]
    labels: tuple[str, ...]
    what_must_change: str
    promotion: PromotionChecklist
    post_ipo: bool = False
    executable_arb: bool = False
    addressed_warnings: tuple[str, ...] = ()

    def reason_code_set(self) -> set[str]:
        return set(self.reason_codes)


@dataclass(frozen=True)
class ReviewSnapshot:
    as_of_knowledge: datetime
    source: str
    prints: tuple[InstrumentPrint, ...]
    overlays: tuple[SeriesOverlay, ...] = ()
    memory: tuple[MemoryOverlay, ...] = ()
    reclaim: dict[str, ReclaimObservables] = field(default_factory=dict)
    arb_packages: dict[str, ArbPackage] = field(default_factory=dict)
    catalysts: dict[str, str] = field(default_factory=dict)
    invalidations: dict[str, str] = field(default_factory=dict)
    overlooked: dict[str, str] = field(default_factory=dict)
    liquidity_ok: dict[str, bool] = field(default_factory=dict)
    addressed_warnings: dict[str, tuple[str, ...]] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def print_for(self, symbol: str) -> InstrumentPrint | None:
        for row in self.prints:
            if row.symbol == symbol:
                return row
        return None

    def overlay_for(self, symbol: str) -> SeriesOverlay | None:
        for row in self.overlays:
            if row.symbol == symbol:
                return row
        return None


@dataclass(frozen=True)
class BoardResult:
    review_date: str
    as_of_knowledge: str
    generated_at: str
    universe_version: str
    params_hash: str
    cards: tuple[QuantCard, ...]
    board_markdown: str
    coverage_notes: tuple[str, ...]
    concentration_warnings: tuple[str, ...]
    what_changed: str
    prior_board: str | None
