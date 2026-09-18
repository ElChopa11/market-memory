"""Desk runner protocol (Phase 5d / IMP-012, mesh header in Phase 6a / IMP-014).

Each desk implements ``run(as_of, ctx) -> DeskOutput``. Research-only.
Must not depend on the execution package or signing surfaces. Telegram send is Ops-owned delivery (`mm_delivery.deliver`), not the runner. Coord/Don is orchestration only. The mesh bus is Postgres LISTEN/NOTIFY (no Redis).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_research_kit.state_machine import TransitionLog

ENGINE_VERSION = "imp-019.1"
LIVE_TRADING_ENABLED = False
REGIME_PLACEHOLDER = "unset"
OP_OBSERVATION = "observation"
OP_PAPER = "paper"
OP_VALUES = (OP_OBSERVATION, OP_PAPER)

OK = "OK"
DEGRADED = "DEGRADED"
FAILED = "FAILED"
DESK_STATUS_VALUES = (OK, DEGRADED, FAILED)


class DeskStatus(StrEnum):
    OK = OK
    DEGRADED = DEGRADED
    FAILED = FAILED


@dataclass(frozen=True)
class DeskArtifact:
    """Git-friendly desk product. Missing tape stays unavailable — never invented."""

    name: str
    kind: str
    content: str
    relpath: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "content": self.content,
            "relpath": self.relpath,
        }


@dataclass(frozen=True)
class DeskOutput:
    """Typed desk result. Completeness is coverage of expected slots, not conviction."""

    desk: str
    slug: str
    tier: str
    status: str
    completeness_pct: float
    provenance_ids: tuple[str, ...]
    artifacts: tuple[DeskArtifact, ...]
    as_of_knowledge: datetime
    notes: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)
    cadence: str = "daily"
    op: str = "observation"
    regime: str = "unset"
    error_class: str | None = None
    universe: str = "mixed"
    sources: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    n: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        object.__setattr__(self, "provenance_ids", tuple(sorted(self.provenance_ids)))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "missing", tuple(self.missing))
        if self.status not in DESK_STATUS_VALUES:
            raise ValueError(f"unknown desk status {self.status!r}")
        if self.op not in OP_VALUES:
            raise ValueError(f"op must be paper|observation, got {self.op!r}")
        pct = float(self.completeness_pct)
        if pct < 0 or pct > 100:
            raise ValueError("completeness_pct must be in [0, 100]")
        object.__setattr__(self, "completeness_pct", round(pct, 2))
        if self.n is None:
            object.__setattr__(self, "n", len(self.artifacts))

    def header(self) -> dict[str, Any]:
        """Principal Phase 6 message header (regime from Intel's macro sleeve when it succeeds)."""
        from mm_common.time import in_ops_tz

        return {
            "desk": self.slug,
            "as_of_utc": self.as_of_knowledge.isoformat(),
            "as_of_sydney": in_ops_tz(self.as_of_knowledge).isoformat(),
            "status": self.status,
            "n": int(self.n or 0),
            "completeness": self.completeness_pct,
            "regime": self.regime,
            "op": self.op,
            "universe": self.universe,
            "sources": list(self.sources),
            "missing": list(self.missing),
        }

    def canonical(self) -> dict[str, Any]:
        return {
            "desk": self.desk,
            "slug": self.slug,
            "tier": self.tier,
            "status": self.status,
            "completeness_pct": self.completeness_pct,
            "provenance_ids": list(self.provenance_ids),
            "artifacts": [row.canonical() for row in self.artifacts],
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "notes": list(self.notes),
            "payload": self.payload,
            "cadence": self.cadence,
            "op": self.op,
            "regime": self.regime,
            "error_class": self.error_class,
            "universe": self.universe,
            "sources": list(self.sources),
            "missing": list(self.missing),
            "n": int(self.n or 0),
        }

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))


@dataclass
class DeskContext:
    """Shared runner context. ``as_of`` is the knowledge watermark, not wall clock."""

    repo_root: Path
    fixture: Any
    send_enabled: bool = False
    prior: dict[str, DeskOutput] = field(default_factory=dict)
    events: list[TransitionLog] = field(default_factory=list)
    workspace: Path | None = None
    thesis: Any = None


class Desk(Protocol):
    slug: str
    tier: str
    display_name: str

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput: ...


def completeness_pct(present: int, expected: int) -> float:
    if expected <= 0:
        return 100.0
    return round(100.0 * max(present, 0) / expected, 2)


def status_from_slots(*, present: int, expected: int, failed: bool = False, required_missing: bool = False) -> str:
    if failed:
        return FAILED
    if expected <= 0:
        return OK
    if required_missing or present < expected:
        return DEGRADED
    return OK
