"""Intel desk (Tier 2): read-only assemble of ingest/health facts. No theses."""

from __future__ import annotations

from datetime import datetime

from mm_desks.fixture import REQUIRED_FEEDS
from mm_desks.models import FrozenDay
from mm_desks.protocol import (
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)

SLUG = "intel"
TIER = "2"
DISPLAY_NAME = "Data & Market Memory Desk"


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    day: FrozenDay = ctx.fixture
    feeds = day.feeds
    expected = len(feeds)
    present = sum(1 for row in feeds if row.status == "ok")
    required_missing = any(row.source_id in REQUIRED_FEEDS and row.status != "ok" for row in feeds)
    notes: list[str] = []
    for row in feeds:
        if row.status != "ok":
            notes.append(f"{row.source_id}: {row.status} ({row.freshness}); not invented")
    provenance = tuple(row.observation_id for row in feeds if row.observation_id)
    lines = [
        f"# Intel assemble — {day.session_date}",
        "",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of.isoformat()}",
        f"- **Fixture:** {day.fixture_id}",
        "- **Role:** facts only. No thesis, no Quant verdict, no order.",
        "",
        "| source_id | status | freshness | required | observation_id | notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in feeds:
        oid = row.observation_id or "—"
        req = "yes" if row.required else "no"
        note = row.notes.replace("|", "/") or "—"
        lines.append(f"| {row.source_id} | {row.status} | {row.freshness} | {req} | {oid} | {note} |")
    lines.extend(["", "Degrade, never invent. Missing feeds stay unavailable.", ""])
    artifact = DeskArtifact(name="intel-assemble", kind="markdown", content="\n".join(lines), relpath="intel.md")
    payload = {
        "feeds": [row.canonical() for row in feeds],
        "required_missing": sorted(
            row.source_id for row in feeds if row.source_id in REQUIRED_FEEDS and row.status != "ok"
        ),
        "data_quality": "unavailable" if present == 0 else ("partial" if required_missing or present < expected else "fresh"),
    }
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status_from_slots(
            present=present,
            expected=expected,
            required_missing=required_missing,
        ),
        completeness_pct=completeness_pct(present, expected),
        provenance_ids=provenance,
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=tuple(notes),
        payload=payload,
    )


class IntelDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
