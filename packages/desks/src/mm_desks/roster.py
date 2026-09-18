"""Phase 6c-1 publishing roster: exactly five desks (Principal hive).

Display names live in ``mm_common.naming`` / ``config/desks/naming.yaml`` (Phase 6c-2).
Don/Coord is orchestration only — not a publishing desk. Delivery is Ops-owned.
Retired Phase-5/6a slugs (crypto, equities, flow, macro, chart, skeptic, risk,
coord-as-desk, briefing) map into these five; helper modules may remain.

Boundary: a comment containing mm_execution must not fail CI grep.
# never import mm_execution from this package (statement form is gated).
"""

from __future__ import annotations

from mm_desks.naming import (
    ASSEMBLE_CHANNEL,
    DESK_META,
    DQ_CHANNEL,
    GATES_IN_IC_RISK,
    IC_RISK,
    INTEL,
    MESH_DESKS,
    OPS,
    PIPELINE,
    PUBLISHING_DESKS,
    QUANT,
    RESEARCH,
    RETIRED_DESK_SLUGS,
    SLEEVE_MAP,
)

__all__ = [
    "ASSEMBLE_CHANNEL",
    "DESK_META",
    "DQ_CHANNEL",
    "GATES_IN_IC_RISK",
    "IC_RISK",
    "INTEL",
    "MESH_DESKS",
    "OPS",
    "PIPELINE",
    "PUBLISHING_DESKS",
    "QUANT",
    "RESEARCH",
    "RETIRED_DESK_SLUGS",
    "SLEEVE_MAP",
]
