"""Market Memory enumerations from the founding proposal."""

from __future__ import annotations

from enum import StrEnum


class SourceKind(StrEnum):
    EXCHANGE = "exchange"
    ONCHAIN = "onchain"
    MACRO = "macro"
    NEWS = "news"
    INTERNAL = "internal"


class EvidenceType(StrEnum):
    FACT = "fact"
    QUOTE = "quote"
    METRIC = "metric"
    COMMENTARY = "commentary"
    DERIVED = "derived"


class DataQuality(StrEnum):
    OK = "ok"
    STALE = "stale"
    PARTIAL = "partial"
    CONTRADICTED = "contradicted"
    REJECTED = "rejected"


class ObservationRelation(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DUPLICATE = "duplicate"
    UPDATES = "updates"


class ThesisStatus(StrEnum):
    DRAFT = "draft"
    IN_RESEARCH = "in_research"
    IN_SKEPTIC = "in_skeptic"
    PAPER = "paper"
    LIVE = "live"
    REJECTED = "rejected"
    RETIRED = "retired"


class EvidenceRole(StrEnum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    CONTEXT = "context"


class SkepticVerdict(StrEnum):
    PASS = "pass"
    REVISE = "revise"
    REJECT = "reject"


SOURCE_KIND_VALUES = tuple(kind.value for kind in SourceKind)
EVIDENCE_TYPE_VALUES = tuple(kind.value for kind in EvidenceType)
DATA_QUALITY_VALUES = tuple(kind.value for kind in DataQuality)
OBSERVATION_RELATION_VALUES = tuple(kind.value for kind in ObservationRelation)
THESIS_STATUS_VALUES = tuple(kind.value for kind in ThesisStatus)
EVIDENCE_ROLE_VALUES = tuple(kind.value for kind in EvidenceRole)
SKEPTIC_VERDICT_VALUES = tuple(kind.value for kind in SkepticVerdict)

# Phase 2 may set these; paper/live remain later-phase promotions.
PHASE2_STATUS_VALUES = (
    ThesisStatus.DRAFT.value,
    ThesisStatus.IN_RESEARCH.value,
    ThesisStatus.IN_SKEPTIC.value,
    ThesisStatus.REJECTED.value,
    ThesisStatus.RETIRED.value,
)
STATUSES_REQUIRING_EVIDENCE = (
    ThesisStatus.IN_SKEPTIC.value,
    ThesisStatus.PAPER.value,
    ThesisStatus.LIVE.value,
)
