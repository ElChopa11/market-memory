"""Flow / liquidity desk (Phase 6b). Derived metrics from existing HL + equity tape."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_desks.protocol import (
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)
from mm_flow.config import load_flow_config
from mm_flow.engine import compute_flow
from mm_flow.models import VERDICT_UNAVAILABLE
from mm_flow.observations import snapshot_envelopes
from mm_quant.models import MarketPanel, StructurePoint
from mm_quant.panel import panel_from_mapping
from mm_common.time import parse_utc

SLUG = "flow"
TIER = "flow"
DISPLAY_NAME = "Flow / Liquidity Desk"


def _point(raw: dict[str, Any], *, fixture_id: str | None) -> StructurePoint:
    as_of = raw.get("as_of_knowledge") or raw.get("ingested_at")
    if as_of is None:
        raise ValueError("flow structure point missing as_of_knowledge")
    value = raw.get("value")
    return StructurePoint(
        instrument=str(raw["instrument"]).upper(),
        metric=str(raw["metric"]),
        as_of_knowledge=parse_utc(str(as_of)),
        ingested_at=parse_utc(str(raw.get("ingested_at") or as_of)),
        value=None if value is None else float(value),
        observation_id=None if raw.get("observation_id") is None else str(raw.get("observation_id")),
        fixture_id=str(raw.get("fixture_id") or fixture_id) if (raw.get("fixture_id") or fixture_id) else None,
        data_quality=str(raw.get("data_quality") or "ok"),
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extra_structure(ctx: DeskContext) -> tuple[StructurePoint, ...]:
    raw = ctx.fixture.raw.get("flow") if isinstance(ctx.fixture.raw.get("flow"), dict) else {}
    fixture_id = ctx.fixture.fixture_id
    rows: list[dict[str, Any]] = list(raw.get("structure") or [])
    rel = raw.get("structure_path")
    if rel:
        payload = _load_json(ctx.repo_root / str(rel))
        if isinstance(payload, dict):
            rows.extend(list(payload.get("structure") or payload.get("points") or []))
            fixture_id = str(payload.get("fixture_id") or fixture_id)
        elif isinstance(payload, list):
            rows.extend(payload)
    return tuple(_point(row, fixture_id=fixture_id) for row in rows if isinstance(row, dict))


def flow_panel(ctx: DeskContext) -> MarketPanel:
    panel = ctx.fixture.panel
    extra = extra_structure(ctx)
    raw = ctx.fixture.raw.get("flow") if isinstance(ctx.fixture.raw.get("flow"), dict) else {}
    if raw.get("panel_path"):
        from mm_quant.panel import load_panel_file

        panel = load_panel_file(ctx.repo_root / str(raw["panel_path"]))
    if isinstance(raw.get("panel"), dict):
        panel = panel_from_mapping(raw["panel"])
    if not extra:
        return panel
    return MarketPanel(
        bars=panel.bars,
        structure=panel.structure + extra,
        fixture_id=panel.fixture_id,
        sector_of=dict(panel.sector_of),
        asset_class_of=dict(panel.asset_class_of),
    )


def _instruments(ctx: DeskContext) -> tuple[str, ...]:
    raw = ctx.fixture.raw.get("flow") if isinstance(ctx.fixture.raw.get("flow"), dict) else {}
    listed = tuple(str(item).upper() for item in (raw.get("instruments") or ()))
    if listed:
        return listed
    return ctx.fixture.quant_instruments or (ctx.fixture.thesis.instrument,)


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    cfg = load_flow_config(ctx.repo_root)
    panel = flow_panel(ctx)
    instruments = _instruments(ctx)
    snapshots = [compute_flow(name, panel, as_of, config=cfg) for name in instruments]
    envelopes = []
    for snap in snapshots:
        envelopes.extend(snapshot_envelopes(snap, ingested_at=as_of))
    present = sum(1 for snap in snapshots if snap.verdict.verdict != VERDICT_UNAVAILABLE)
    notes: list[str] = []
    for snap in snapshots:
        if snap.data_quality != "ok":
            notes.append(f"{snap.instrument}: flow data_quality={snap.data_quality}; gaps={list(snap.gaps)}")
        if snap.verdict.verdict == VERDICT_UNAVAILABLE:
            notes.append(f"{snap.instrument}: liquidity verdict unavailable (not invented)")
    provenance = [env.claim_hash for env in envelopes]
    for snap in snapshots:
        for ref in snap.provenance:
            if ref.observation_id:
                provenance.append(ref.observation_id)
    lines = [
        f"# Flow / liquidity — {ctx.fixture.session_date}",
        "",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of.isoformat()}",
        f"- **Config version:** {cfg.version}",
        "- **Role:** derived liquidity metrics. Not an order. Clip sizes are research notionals.",
        "",
        "| instrument | verdict | max_clip_usd | funding_z | oi_delta | basis | spread_bps | depth_usd | adv |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for snap in snapshots:
        by_name = {row.name: row for row in snap.metrics}

        def _cell(name: str) -> str:
            row = by_name.get(name)
            if row is None or row.value is None or row.status == "unavailable":
                return "unavailable"
            return f"{row.value:.6g}"

        max_clip = snap.verdict.max_clip_usd
        lines.append(
            f"| {snap.instrument} | {snap.verdict.verdict} | "
            f"{'unavailable' if max_clip is None else max_clip} | "
            f"{_cell('funding_z')} | {_cell('oi_delta')} | {_cell('basis')} | "
            f"{_cell('spread_bps')} | {_cell('depth_usd')} | {_cell('adv_notional')} |"
        )
    lines.extend(["", "Degrade, never invent. Missing book/ADV stays unavailable.", ""])
    artifact = DeskArtifact(name="flow-liquidity", kind="markdown", content="\n".join(lines), relpath="flow.md")
    sources = tuple(sorted({ref.observation_id or "mm_flow.derived" for snap in snapshots for ref in snap.provenance if ref.observation_id}))
    missing = tuple(sorted({gap for snap in snapshots for gap in snap.gaps}))
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status_from_slots(present=present, expected=max(len(instruments), 1), required_missing=present == 0),
        completeness_pct=completeness_pct(present, max(len(instruments), 1)),
        provenance_ids=tuple(provenance),
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=tuple(notes),
        sources=sources or ("mm_flow.derived",),
        missing=missing,
        payload={
            "instruments": list(instruments),
            "snapshots": [snap.canonical() for snap in snapshots],
            "verdicts": {snap.instrument: snap.verdict.verdict for snap in snapshots},
            "max_clip_usd": {snap.instrument: snap.verdict.max_clip_usd for snap in snapshots},
            "claim_hashes": [env.claim_hash for env in envelopes],
        },
    )


class FlowDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
