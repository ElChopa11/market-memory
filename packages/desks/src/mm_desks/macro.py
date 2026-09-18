"""Intel macro sleeve (Phase 6b). Regime tag + EVENT_RISK. Not a publishing desk. Never invent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.time import parse_utc
from mm_desks.protocol import (
    DEGRADED,
    OK,
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)
from mm_macro.config import load_macro_config
from mm_macro.engine import CATALOG, compute_macro
from mm_macro.models import CalendarEvent, MacroPoint
from mm_macro.observations import snapshot_envelopes

from mm_desks.naming import sleeve_display, sleeve_tier

SLUG = "macro"
TIER = sleeve_tier(SLUG)
DISPLAY_NAME = sleeve_display(SLUG)


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(text)
    return json.loads(text)


def _point(raw: dict[str, Any], *, fixture_id: str | None) -> MacroPoint:
    as_of = raw.get("as_of_knowledge") or raw.get("ingested_at")
    if as_of is None:
        raise ValueError("macro series point missing as_of_knowledge")
    value = raw.get("value")
    return MacroPoint(
        instrument=str(raw.get("instrument") or "").upper(),
        metric=str(raw.get("metric") or "fred_observation"),
        as_of_knowledge=parse_utc(str(as_of)),
        ingested_at=parse_utc(str(raw.get("ingested_at") or as_of)),
        value=None if value in (None, "", "unavailable") else float(value),
        observation_id=None if raw.get("observation_id") is None else str(raw.get("observation_id")),
        fixture_id=fixture_id,
        series_id=None if raw.get("series_id") is None else str(raw.get("series_id")),
    )


def macro_series(ctx: DeskContext) -> tuple[MacroPoint, ...]:
    raw = ctx.fixture.raw.get("macro") if isinstance(ctx.fixture.raw.get("macro"), dict) else {}
    fixture_id = ctx.fixture.fixture_id
    rows: list[dict[str, Any]] = list(raw.get("series") or [])
    rel = raw.get("series_path")
    if rel:
        payload = _load_json(ctx.repo_root / str(rel))
        if isinstance(payload, dict):
            rows.extend(list(payload.get("series") or payload.get("points") or []))
            fixture_id = str(payload.get("fixture_id") or fixture_id)
        elif isinstance(payload, list):
            rows.extend(payload)
    return tuple(_point(row, fixture_id=fixture_id) for row in rows if isinstance(row, dict))


def macro_calendar(ctx: DeskContext) -> tuple[CalendarEvent, ...]:
    out: list[CalendarEvent] = []
    for row in ctx.fixture.calendar:
        ingested = getattr(row, "ingested_at", None)
        out.append(
            CalendarEvent(
                when=row.when,
                name=row.name,
                importance=row.importance,
                region=row.region,
                notes=row.notes,
                source=row.source,
                as_of_knowledge=ingested or ctx.fixture.as_of_knowledge,
                ingested_at=ingested or ctx.fixture.as_of_knowledge,
            )
        )
    raw = ctx.fixture.raw.get("macro") if isinstance(ctx.fixture.raw.get("macro"), dict) else {}
    for item in raw.get("calendar") or []:
        if not isinstance(item, dict) or not item.get("when"):
            continue
        when = parse_utc(str(item["when"]))
        known = item.get("as_of_knowledge") or item.get("ingested_at") or ctx.fixture.as_of_knowledge
        known_dt = parse_utc(str(known)) if not hasattr(known, "isoformat") else known
        out.append(
            CalendarEvent(
                when=when,
                name=str(item.get("name") or "event"),
                importance=str(item.get("importance") or "medium").lower(),
                region=str(item.get("region") or "US"),
                notes=str(item.get("notes") or ""),
                source=str(item.get("source") or "fixture"),
                as_of_knowledge=known_dt,
                ingested_at=known_dt,
            )
        )
    return tuple(out)


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    cfg = load_macro_config(ctx.repo_root)
    snap = compute_macro(
        series=macro_series(ctx),
        calendar=macro_calendar(ctx),
        watermark=as_of,
        config=cfg,
    )
    envelopes = snapshot_envelopes(snap, ingested_at=as_of)
    expected = len(CATALOG)
    present = expected - len(snap.missing)
    notes: list[str] = []
    if snap.missing:
        notes.append(f"missing feeds: {', '.join(snap.missing)} (not invented)")
    if snap.regime.status == "unavailable":
        notes.append("regime tag unavailable; envelope header stays unset until two driving inputs exist")
    if snap.event_risk.tagged:
        notes.append(f"EVENT_RISK {snap.event_risk.rule_id}: {snap.event_risk.reason}")
    regime_tag = snap.regime.tag if snap.regime.status != "unavailable" else "unset"
    lines = [
        f"# Macro regime — {ctx.fixture.session_date}",
        "",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of.isoformat()}",
        f"- **Regime tag:** `{regime_tag}`",
        f"- **Confidence:** {snap.regime.confidence:.3f} (coverage/sharpness; not a call)",
        f"- **Driving inputs:** VIX={snap.payload.get('values', {}).get('VIX')}, "
        f"DXY={snap.payload.get('values', {}).get('DXY')}",
        f"- **EVENT_RISK:** {'yes' if snap.event_risk.tagged else 'no'} (`{snap.event_risk.rule_id}`)",
        f"- **Config version:** {cfg.version}",
        "",
        "| instrument | value | observation_id |",
        "| --- | --- | --- |",
    ]
    by_inst = {row.instrument: row for row in snap.series}
    for name in CATALOG:
        row = by_inst.get(name)
        if row is None or row.value is None:
            lines.append(f"| {name} | unavailable | — |")
        else:
            lines.append(f"| {name} | {row.value} | {row.observation_id or '—'} |")
    lines.extend(["", "Degrade, never invent. Missing FRED/calendar stays unavailable.", ""])
    artifact = DeskArtifact(name="macro-regime", kind="markdown", content="\n".join(lines), relpath="macro.md")
    status = status_from_slots(
        present=present,
        expected=expected,
        required_missing=snap.regime.status == "unavailable",
    )
    if snap.regime.status == "unavailable" and status == OK:
        status = DEGRADED
    sources = tuple(sorted({row.observation_id for row in snap.series if row.observation_id}))
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status,
        completeness_pct=completeness_pct(present, expected),
        provenance_ids=tuple(env.claim_hash for env in envelopes) + tuple(sources),
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=tuple(notes),
        regime=regime_tag,
        sources=sources or ("mm_macro.derived",),
        missing=snap.missing,
        payload={
            "regime_tag": regime_tag,
            "regime": snap.regime.canonical(),
            "event_risk": snap.event_risk.canonical(),
            "series": [row.canonical() for row in snap.series],
            "missing": list(snap.missing),
            "data_quality": snap.data_quality,
            "claim_hashes": [env.claim_hash for env in envelopes],
        },
    )


class MacroDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
