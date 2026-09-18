"""Retired publishing slug. Coord/Don is orchestration only; Ops publishes the pack."""

from __future__ import annotations

from mm_desks.ops import DISPLAY_NAME, PIPELINE_FOR_PACK, OpsDesk, run

SLUG = "ops"
TIER = "1"
CoordDesk = OpsDesk

__all__ = ["CoordDesk", "DISPLAY_NAME", "PIPELINE_FOR_PACK", "SLUG", "TIER", "run"]
