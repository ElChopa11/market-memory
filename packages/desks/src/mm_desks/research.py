"""Research desk (Investment Research): crypto + equities sleeves. Chart is a product, not a desk."""

from __future__ import annotations

from datetime import datetime

from mm_desks.crypto import run as run_crypto
from mm_desks.equities import run as run_equities
from mm_desks.combine import combine_outputs
from mm_desks.protocol import DeskContext, DeskOutput
from mm_desks.roster import RESEARCH, DESK_META

SLUG = RESEARCH
TIER = DESK_META[RESEARCH][1]
DISPLAY_NAME = DESK_META[RESEARCH][0]


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    crypto = run_crypto(as_of, ctx)
    equities = run_equities(as_of, ctx)
    tape = list(crypto.payload.get("tape") or []) + list(equities.payload.get("tape") or [])
    intent = "none"
    if crypto.payload.get("intent") and crypto.payload.get("intent") != "none":
        intent = str(crypto.payload["intent"])
    elif equities.payload.get("intent") and equities.payload.get("intent") != "none":
        intent = str(equities.payload["intent"])
    payload = {
        "sleeves": ("crypto", "equities", "chart"),
        "crypto": crypto.payload,
        "equities": equities.payload,
        "tape": tape,
        "intent": intent,
        "instruments": sorted(
            set(crypto.payload.get("instruments") or []) | set(equities.payload.get("instruments") or [])
        ),
    }
    return combine_outputs(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        as_of=as_of,
        parts=(crypto, equities),
        payload=payload,
    )


class ResearchDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
