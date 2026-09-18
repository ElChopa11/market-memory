"""Research crypto sleeve (not a publishing desk). Tape notes from Memory/fixture. No orders."""

from __future__ import annotations

from datetime import datetime

from mm_desks.models import FrozenDay, TapeRow
from mm_desks.protocol import (
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)
from mm_desks.universe import membership_of, universe_crypto

from mm_desks.naming import sleeve_display, sleeve_tier

SLUG = "crypto"
CRYPTO_TIER = sleeve_tier(SLUG)
CRYPTO_DESK = sleeve_display(SLUG)
MUST_NOT = ("execution-import", "signing-surface", "live-order")


def _crypto_rows(day: FrozenDay, ctx: DeskContext) -> tuple[TapeRow, ...]:
    crypto_names = set(universe_crypto(ctx.repo_root))
    out: list[TapeRow] = []
    for row in day.tape:
        if row.asset_class == "equity":
            continue
        if row.asset_class in {"crypto", "perp"} or row.instrument in crypto_names:
            out.append(row)
    return tuple(out)


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    day: FrozenDay = ctx.fixture
    membership_names = universe_crypto(ctx.repo_root) or ("BTC",)
    rows = _crypto_rows(day, ctx)
    expected_names = tuple(dict.fromkeys(row.instrument for row in rows)) or membership_names[:1]
    covered = {row.instrument for row in rows if row.value is not None}
    present = sum(1 for name in expected_names if name in covered)
    notes = tuple(f"{name}: tape unavailable; not invented" for name in expected_names if name not in covered)
    provenance = tuple(row.observation_id for row in rows if row.observation_id)
    lines = [
        f"# {CRYPTO_DESK} note — {day.session_date}",
        "",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of.isoformat()}",
        f"- **Desk / tier:** {CRYPTO_DESK} / {CRYPTO_TIER}",
        f"- **Must not:** {', '.join(MUST_NOT)}",
        "- **Not a call.** Intent-only if a thesis is attached.",
        "",
        "| instrument | membership | metric | value | source | freshness | observation_id |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        value = row.value if row.value is not None else "unavailable"
        membership = (
            row.membership if row.membership != "not_in_membership" else membership_of(row.instrument, ctx.repo_root)
        )
        oid = row.observation_id or "—"
        lines.append(
            f"| {row.instrument} | {membership} | {row.metric} | {value} | {row.source} | {row.freshness} | {oid} |"
        )
    if not rows:
        lines.append("| — | — | — | unavailable | — | unavailable | — |")
    crypto_names = set(membership_names)
    intent = day.thesis.intent if day.thesis.instrument in crypto_names else "none"
    lines.extend(["", "## Intent (not an order)", "", intent or "none", ""])
    artifact = DeskArtifact(name="crypto-note", kind="markdown", content="\n".join(lines), relpath="crypto.md")
    return DeskOutput(
        desk=CRYPTO_DESK,
        slug=SLUG,
        tier=CRYPTO_TIER,
        status=status_from_slots(present=present, expected=len(expected_names)),
        completeness_pct=completeness_pct(present, len(expected_names)),
        provenance_ids=provenance,
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=notes,
        payload={
            "instruments": sorted(covered),
            "expected": list(expected_names),
            "tape": [row.canonical() for row in rows],
            "intent": intent or "none",
        },
    )


class CryptoDesk:
    slug = SLUG
    tier = CRYPTO_TIER
    display_name = CRYPTO_DESK

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
