"""IDs, time, hashing, and shared schemas. Must not hold secrets or talk to Hyperliquid."""

from mm_common.enums import (
    DATA_QUALITY_VALUES,
    EVIDENCE_ROLE_VALUES,
    EVIDENCE_TYPE_VALUES,
    OBSERVATION_RELATION_VALUES,
    PHASE2_STATUS_VALUES,
    SKEPTIC_VERDICT_VALUES,
    SOURCE_KIND_VALUES,
    STATUSES_REQUIRING_EVIDENCE,
    THESIS_STATUS_VALUES,
    DataQuality,
    EvidenceRole,
    EvidenceType,
    ObservationRelation,
    SkepticVerdict,
    SourceKind,
    ThesisStatus,
)
from mm_common.hashing import canonical_json, claim_hash, normalize_numeric, sha256_hex
from mm_common.ids import new_ulid
from mm_common.schemas import ClaimIdentity, ObservationEnvelope
from mm_common.time import OPS_TZ, as_utc, from_unix_ms, in_ops_tz, parse_utc, parse_window, to_unix_ms, utcnow

__phase__ = 2
LIVE_TRADING_ENABLED = False

__all__ = [
    "ClaimIdentity",
    "DATA_QUALITY_VALUES",
    "DataQuality",
    "EVIDENCE_ROLE_VALUES",
    "EVIDENCE_TYPE_VALUES",
    "EvidenceRole",
    "EvidenceType",
    "LIVE_TRADING_ENABLED",
    "OBSERVATION_RELATION_VALUES",
    "OPS_TZ",
    "ObservationEnvelope",
    "ObservationRelation",
    "PHASE2_STATUS_VALUES",
    "SKEPTIC_VERDICT_VALUES",
    "SkepticVerdict",
    "SOURCE_KIND_VALUES",
    "STATUSES_REQUIRING_EVIDENCE",
    "SourceKind",
    "THESIS_STATUS_VALUES",
    "ThesisStatus",
    "as_utc",
    "canonical_json",
    "claim_hash",
    "from_unix_ms",
    "in_ops_tz",
    "new_ulid",
    "normalize_numeric",
    "parse_utc",
    "parse_window",
    "sha256_hex",
    "to_unix_ms",
    "utcnow",
]
