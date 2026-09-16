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


SOURCE_KIND_VALUES = tuple(kind.value for kind in SourceKind)
EVIDENCE_TYPE_VALUES = tuple(kind.value for kind in EvidenceType)
DATA_QUALITY_VALUES = tuple(kind.value for kind in DataQuality)
OBSERVATION_RELATION_VALUES = tuple(kind.value for kind in ObservationRelation)
