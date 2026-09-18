"""Hive PLAYBOOK artifact ladder. One run emits the set. Shared run_id + content_hash."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_desks.dq import assert_no_letter_grade, completeness, populated_count, publish_allowed
from mm_desks.envelope import DeskEnvelope
from mm_desks.naming import (
    ARTIFACT_TYPES,
    artifact_desk,
    artifact_display,
    require_artifact_type,
    require_publishing_desk,
)
from mm_quant.trade_math import TradeMathMismatch

MAX_IDEAS = 3
ENGINE_VERSION = "imp-019.1"


@dataclass(frozen=True)
class LadderArtifact:
    artifact_type: str
    run_id: str
    run_content_hash: str
    trade_math_hash: str
    as_of_knowledge: datetime
    payload: dict[str, Any]
    desk: str = ""
    status: str = "OK"
    gaps: tuple[str, ...] = ()
    completeness: float = 1.0

    def __post_init__(self) -> None:
        require_artifact_type(self.artifact_type)
        owner = self.desk or artifact_desk(self.artifact_type)
        require_publishing_desk(owner)
        object.__setattr__(self, "desk", owner)
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        assert_no_letter_grade(self.payload)

    @property
    def display_name(self) -> str:
        return artifact_display(self.artifact_type)

    def canonical(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "run_id": self.run_id,
            "run_content_hash": self.run_content_hash,
            "trade_math_hash": self.trade_math_hash,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "payload": self.payload,
            "desk": self.desk,
            "status": self.status,
            "gaps": list(self.gaps),
            "completeness": self.completeness,
            "engine_version": ENGINE_VERSION,
        }

    def content_hash(self) -> str:
        body = dict(self.canonical())
        body.pop("run_content_hash", None)
        return sha256_hex(canonical_json(body))

    def as_envelope_body(self) -> dict[str, Any]:
        return self.canonical() | {"content_hash": self.content_hash()}


def required_fields_for(artifact_type: str, spec: dict[str, Any] | None = None) -> tuple[str, ...]:
    require_artifact_type(artifact_type)
    defaults = {
        "DAILY_BIAS": ("instrument", "direction", "conviction", "level", "trade_math_hash"),
        "EDGE_SCAN": ("instrument", "catalyst", "source", "as_of", "invalidator", "trade_math_hash"),
        "INTEL_PACKET": ("instrument", "detail", "trade_math_hash"),
        "CHART_ARTIFACT": ("instrument", "levels", "png_filename", "trade_math_hash"),
        "OFFICIAL_BRIEF": ("executive_cut", "trade_math_hash"),
        "STATE_CARD": ("instrument", "state", "permission", "rearm", "trade_math_hash"),
    }
    if spec and artifact_type in (spec.get("required_fields") or {}):
        return tuple(spec["required_fields"][artifact_type])
    return defaults[artifact_type]


def score_artifact(artifact_type: str, payload: dict[str, Any], spec: dict[str, Any] | None = None) -> tuple[float, tuple[str, ...]]:
    required = required_fields_for(artifact_type, spec)
    present, expected, missing = populated_count(payload, required)
    return completeness(present, expected), missing


def make_artifact(
    *,
    artifact_type: str,
    run_id: str,
    trade_math_hash: str,
    as_of: datetime,
    payload: dict[str, Any],
    run_content_hash: str = "",
    desk: str = "",
    spec: dict[str, Any] | None = None,
    threshold: float = 0.8,
    status: str = "OK",
) -> LadderArtifact:
    payload = dict(payload)
    payload.setdefault("trade_math_hash", trade_math_hash)
    require_artifact_type(artifact_type)
    owner = desk or artifact_desk(artifact_type)
    require_publishing_desk(owner)
    ratio, missing = score_artifact(artifact_type, payload, spec)
    art_status = status
    if not publish_allowed(ratio, threshold) and artifact_type != "OFFICIAL_BRIEF":
        art_status = "FAILED"
    return LadderArtifact(
        artifact_type=artifact_type,
        run_id=run_id,
        run_content_hash=run_content_hash,
        trade_math_hash=trade_math_hash,
        as_of_knowledge=as_of,
        payload=payload,
        desk=owner,
        status=art_status,
        gaps=missing,
        completeness=ratio,
    )


def run_content_hash(artifacts: tuple[LadderArtifact, ...]) -> str:
    payload = {
        "run_id": artifacts[0].run_id if artifacts else "",
        "types": [row.artifact_type for row in artifacts],
        "hashes": [row.content_hash() for row in artifacts],
        "math": [row.trade_math_hash for row in artifacts],
    }
    return sha256_hex(canonical_json(payload))


def stamp_run_hash(artifacts: tuple[LadderArtifact, ...], digest: str) -> tuple[LadderArtifact, ...]:
    stamped = []
    for row in artifacts:
        stamped.append(
            LadderArtifact(
                artifact_type=row.artifact_type,
                run_id=row.run_id,
                run_content_hash=digest,
                trade_math_hash=row.trade_math_hash,
                as_of_knowledge=row.as_of_knowledge,
                payload=row.payload,
                desk=row.desk,
                status=row.status,
                gaps=row.gaps,
                completeness=row.completeness,
            )
        )
    return tuple(stamped)


def assert_math_inherited(artifacts: tuple[LadderArtifact, ...], expected: str) -> None:
    for row in artifacts:
        if row.trade_math_hash != expected:
            raise TradeMathMismatch(f"{row.artifact_type} inherited trade math mismatch")


def artifact_to_envelope(artifact: LadderArtifact, *, envelope_id: str | None = None) -> DeskEnvelope:
    from mm_common.ids import new_ulid
    from mm_common.time import in_ops_tz

    body = artifact.as_envelope_body()
    owner = require_publishing_desk(artifact.desk or artifact_desk(artifact.artifact_type))
    require_artifact_type(artifact.artifact_type)
    header_body = {
        "desk": owner.slug,
        "as_of_utc": artifact.as_of_knowledge.isoformat(),
        "as_of_sydney": in_ops_tz(artifact.as_of_knowledge).isoformat(),
        "status": artifact.status,
        "n": 1,
        "completeness": round(artifact.completeness * 100.0, 2),
        "regime": "unset",
        "op": "observation",
        "universe": "mixed",
        "sources": [],
        "missing": list(artifact.gaps),
        "cadence": "daily",
        "error_class": None,
        "channel": f"desk.ladder.{artifact.artifact_type.lower()}.output",
        "body": body,
    }
    digest = sha256_hex(canonical_json(header_body))
    return DeskEnvelope(
        desk=header_body["desk"],
        as_of_utc=artifact.as_of_knowledge,
        as_of_sydney=header_body["as_of_sydney"],
        status=artifact.status if artifact.status in {"OK", "DEGRADED", "FAILED"} else "OK",
        n=1,
        completeness=float(header_body["completeness"]),
        regime="unset",
        op="observation",
        universe="mixed",
        sources=(),
        missing=artifact.gaps,
        cadence="daily",
        channel=header_body["channel"],
        content_hash=digest,
        body=body,
        envelope_id=envelope_id or new_ulid(),
    )
