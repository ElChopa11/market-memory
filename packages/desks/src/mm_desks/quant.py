"""Quant desk (Tier 4): call mm_quant factors/cards. Not a trading decision."""

from __future__ import annotations

from datetime import datetime

from mm_desks.protocol import (
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)
from mm_quant.card import build_quant_card, render_quant_card
from mm_quant.config import load_quant_config
from mm_desks.roster import DESK_META, QUANT

from mm_desks.roster import DESK_META, QUANT

SLUG = QUANT
TIER = DESK_META[QUANT][1]
DISPLAY_NAME = DESK_META[QUANT][0]

_CLOSED = ("RESEARCH_PRIORITY", "MONITOR", "DEFER", "REJECT", "INSUFFICIENT_DATA")


def _verdict(data_quality: str) -> tuple[str, str]:
    if data_quality == "unavailable":
        return "INSUFFICIENT_DATA", "factor_layer_unavailable"
    if data_quality == "partial":
        return "MONITOR", "factor_layer_partial"
    return "MONITOR", "factor_layer_ok"


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    day = ctx.fixture
    cfg = load_quant_config(ctx.repo_root)
    instruments = day.quant_instruments or (day.thesis.instrument,)
    cards = []
    artifacts: list[DeskArtifact] = []
    provenance: list[str] = []
    ok_cards = 0
    notes: list[str] = []
    for name in instruments:
        card = build_quant_card(name, day.panel, as_of, config=cfg)
        cards.append(card)
        markdown = render_quant_card(card)
        artifacts.append(
            DeskArtifact(
                name=f"quant-card-{name}",
                kind="markdown",
                content=markdown,
                relpath=f"quant-{name}.md",
            )
        )
        if card.data_quality != "unavailable":
            ok_cards += 1
        else:
            notes.append(f"{name}: factor data_quality=unavailable; not invented")
        if card.data_quality == "partial":
            notes.append(f"{name}: partial factors listed as gaps (not invented)")
        for ref in card.provenance:
            if ref.observation_id:
                provenance.append(ref.observation_id)
    expected = len(instruments) or 1
    primary = cards[0] if cards else None
    verdict, reason = _verdict(primary.data_quality if primary else "unavailable")
    payload = {
        "verdict": verdict,
        "reason_codes": [reason],
        "closed_set": list(_CLOSED),
        "instruments": list(instruments),
        "cards": [
            {
                "instrument": card.instrument,
                "data_quality": card.data_quality,
                "params_hash": card.params_hash,
                "result_hash": card.result_hash(),
                "regime_tag": card.regime.tag,
                "gaps": list(card.gaps),
            }
            for card in cards
        ],
    }
    header = [
        f"# Quant desk — factor layer {day.session_date}",
        "",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of.isoformat()}",
        f"- **Verdict:** `{verdict}` (closed set; not a call)",
        f"- **Reason code(s):** {reason}",
        f"- **Config version:** {cfg.version}",
        "",
        "Factor math from `mm_quant`. Intent-level budget fraction is not an order.",
        "",
    ]
    summary = DeskArtifact(
        name="quant-summary",
        kind="markdown",
        content="\n".join(header),
        relpath="quant.md",
    )
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status_from_slots(present=ok_cards, expected=expected),
        completeness_pct=completeness_pct(ok_cards, expected),
        provenance_ids=tuple(provenance),
        artifacts=(summary, *artifacts),
        as_of_knowledge=as_of,
        notes=tuple(notes),
        payload=payload,
    )


class QuantDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
