"""Phase 6c-1 publishing roster: exactly five desks (Principal hive).

Don/Coord is orchestration only — not a publishing desk. Delivery is Ops-owned.
Retired Phase-5/6a slugs (crypto, equities, flow, macro, chart, skeptic, risk,
coord-as-desk, briefing) map into these five; helper modules may remain.

Boundary: a comment containing mm_execution must not fail CI grep.
# never import mm_execution from this package (statement form is gated).
"""

from __future__ import annotations

# Canonical publishing desks (Principal lock, Phase 6c-1).
INTEL = "intel"
RESEARCH = "research"
QUANT = "quant"
IC_RISK = "ic_risk"
OPS = "ops"

PUBLISHING_DESKS: tuple[str, ...] = (INTEL, RESEARCH, QUANT, IC_RISK, OPS)
PIPELINE: tuple[str, ...] = PUBLISHING_DESKS
# Ops assembles the pack; mesh requires the four upstream publishers.
MESH_DESKS: tuple[str, ...] = (INTEL, RESEARCH, QUANT, IC_RISK)

ASSEMBLE_CHANNEL = "coord.assemble"
DQ_CHANNEL = "dq.event"

DESK_META: dict[str, tuple[str, str]] = {
    INTEL: ("Intel (Market Intelligence)", "2"),
    RESEARCH: ("Research (Investment Research)", "3"),
    QUANT: ("Quant", "4"),
    IC_RISK: ("IC/Risk (Investment Committee & Risk)", "5-6"),
    OPS: ("Ops", "1"),
}

# Retired publishing slugs. Not in PIPELINE. Helpers may still exist.
RETIRED_DESK_SLUGS: tuple[str, ...] = (
    "crypto",
    "equities",
    "flow",
    "macro",
    "chart",
    "skeptic",
    "risk",
    "coord",
    "briefing",
)

SLEEVE_MAP: dict[str, str] = {
    "crypto": RESEARCH,
    "equities": RESEARCH,
    "chart": RESEARCH,
    "flow": INTEL,
    "macro": INTEL,
    "briefing": INTEL,
    "skeptic": IC_RISK,
    "risk": IC_RISK,
    "coord": OPS,
}

GATES_IN_IC_RISK: tuple[str, ...] = ("skeptic", "risk")
