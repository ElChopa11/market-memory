"""Merge sleeve outputs into one publishing-desk DeskOutput. Not a desk."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from mm_desks.protocol import (
    DEGRADED,
    FAILED,
    OK,
    DeskArtifact,
    DeskOutput,
    completeness_pct,
)

_RANK = {OK: 0, DEGRADED: 1, FAILED: 2}


def worst_status(*statuses: str) -> str:
    rank = 0
    for status in statuses:
        rank = max(rank, _RANK.get(status, 1))
    for name, value in ((FAILED, 2), (DEGRADED, 1), (OK, 0)):
        if rank == value:
            return name
    return DEGRADED


def combine_outputs(
    *,
    desk: str,
    slug: str,
    tier: str,
    as_of: datetime,
    parts: tuple[DeskOutput, ...],
    payload: dict[str, Any],
    extra_artifacts: tuple[DeskArtifact, ...] = (),
    extra_notes: tuple[str, ...] = (),
    regime: str | None = None,
    op: str | None = None,
) -> DeskOutput:
    if not parts:
        raise ValueError("combine_outputs requires at least one part")
    artifacts: list[DeskArtifact] = []
    notes: list[str] = list(extra_notes)
    provenance: list[str] = []
    sources: list[str] = []
    missing: list[str] = []
    present = 0
    expected = 0
    statuses: list[str] = []
    for part in parts:
        statuses.append(part.status)
        artifacts.extend(part.artifacts)
        notes.extend(part.notes)
        provenance.extend(part.provenance_ids)
        sources.extend(part.sources)
        missing.extend(part.missing)
        # Completeness is coverage of expected slots across sleeves.
        expected += 100
        present += part.completeness_pct
    artifacts.extend(extra_artifacts)
    tag = regime
    if not tag or tag in {"unset", "", "unavailable"}:
        for part in parts:
            if part.regime and part.regime not in {"unset", "", "unavailable"}:
                tag = part.regime
                break
    return DeskOutput(
        desk=desk,
        slug=slug,
        tier=tier,
        status=worst_status(*statuses),
        completeness_pct=completeness_pct(int(round(present)), max(expected, 1)),
        provenance_ids=tuple(provenance),
        artifacts=tuple(artifacts),
        as_of_knowledge=as_of,
        notes=tuple(dict.fromkeys(notes)),
        payload=payload,
        regime=tag or parts[0].regime,
        op=op or parts[0].op,
        sources=tuple(dict.fromkeys(sources)),
        missing=tuple(dict.fromkeys(missing)),
        error_class=next((p.error_class for p in parts if p.error_class), None),
    )
