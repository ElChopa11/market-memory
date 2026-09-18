"""IC/Risk desk: two gates (Skeptic + Risk), not two desks. No self-approve."""

from __future__ import annotations

from datetime import datetime

from mm_desks.combine import combine_outputs, worst_status
from mm_desks.protocol import DeskContext, DeskOutput
from mm_desks.risk import run as run_risk_gate
from mm_desks.roster import DESK_META, GATES_IN_IC_RISK, IC_RISK
from mm_desks.skeptic import run as run_skeptic_gate

SLUG = IC_RISK
TIER = DESK_META[IC_RISK][1]
DISPLAY_NAME = DESK_META[IC_RISK][0]


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    skeptic = run_skeptic_gate(as_of, ctx)
    risk = run_risk_gate(as_of, ctx)
    payload = {
        "gates": list(GATES_IN_IC_RISK),
        "skeptic": skeptic.payload,
        "risk": risk.payload,
        "two_gates_not_two_desks": True,
    }
    combined = combine_outputs(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        as_of=as_of,
        parts=(skeptic, risk),
        payload=payload,
        op=risk.op,
    )
    # Combine already worst-cases status; keep explicit for the two-gate rule.
    object.__setattr__(combined, "status", worst_status(skeptic.status, risk.status))
    return combined


class IcRiskDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
