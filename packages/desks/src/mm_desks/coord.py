"""Coord / Ops (Tier 1): calendar stub + output-contract pack from desk outputs."""

from __future__ import annotations

from datetime import datetime, timedelta

from mm_common.time import as_utc, in_ops_tz
from mm_desks.pack import render_output_contract
from mm_desks.protocol import (
    DEGRADED,
    FAILED,
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)
from mm_delivery.payload import prepare_payload

SLUG = "coord"
TIER = "1"
DISPLAY_NAME = "Chief of Staff / Hive Coordinator"

PIPELINE_FOR_PACK = ("intel", "crypto", "equities", "listings", "flow", "macro", "quant", "skeptic", "risk")


def _overall(outputs: dict[str, DeskOutput]) -> str:
    statuses = [outputs[slug].status for slug in PIPELINE_FOR_PACK if slug in outputs]
    if FAILED in statuses:
        return FAILED
    if DEGRADED in statuses:
        return DEGRADED
    return "OK"


def _present_count(ctx: DeskContext) -> tuple[int, list[str], list[str]]:
    missing = [slug for slug in PIPELINE_FOR_PACK if slug not in ctx.prior]
    failed = [
        slug
        for slug in PIPELINE_FOR_PACK
        if slug in ctx.prior and ctx.prior[slug].status == FAILED
    ]
    present = len(PIPELINE_FOR_PACK) - len(missing) - len(failed)
    return present, missing, failed


def _calendar_lines(ctx: DeskContext, as_of: datetime) -> tuple[str, ...]:
    events = ctx.fixture.calendar
    start = as_utc(as_of) - timedelta(hours=6)
    end = as_utc(as_of) + timedelta(hours=36)
    relevant = tuple(row for row in events if start <= row.when <= end)
    if not relevant:
        return ("none (calendar stub; no events in window)",)
    lines = []
    for row in relevant:
        extra = f" — {row.notes}" if row.notes else ""
        lines.append(f"- {row.when.isoformat()} {row.region} {row.importance} {row.name}{extra}")
    return tuple(lines)


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    present, missing, failed = _present_count(ctx)
    calendar = _calendar_lines(ctx, as_of)
    pack_md = render_output_contract(as_of, ctx, calendar_lines=calendar)
    payload_obj = prepare_payload(pack_md)
    sydney = in_ops_tz(as_of).isoformat()
    overall = _overall(ctx.prior)
    if missing and overall == "OK":
        overall = DEGRADED
    notes = tuple(f"missing desk output: {slug}" for slug in missing)
    notes = notes + tuple(f"{slug} FAILED ({ctx.prior[slug].error_class})" for slug in failed)
    if ctx.prior.get("intel") and ctx.prior["intel"].status == DEGRADED:
        notes = notes + tuple(ctx.prior["intel"].notes)
    artifacts = (
        DeskArtifact(name="output-contract", kind="markdown", content=pack_md, relpath="desk-pack.md"),
        DeskArtifact(
            name="no-send-payload",
            kind="json",
            content=payload_obj.content_hash,
            relpath="no-send.json",
        ),
    )
    provenance: list[str] = []
    for slug in PIPELINE_FOR_PACK:
        out = ctx.prior.get(slug)
        if out:
            provenance.extend(out.provenance_ids)
    desk_status = FAILED if overall == FAILED else status_from_slots(
        present=present,
        expected=len(PIPELINE_FOR_PACK),
        failed=bool(failed),
        required_missing=bool(missing),
    )
    if overall == DEGRADED and desk_status == "OK":
        desk_status = DEGRADED
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=desk_status,
        completeness_pct=completeness_pct(present, len(PIPELINE_FOR_PACK)),
        provenance_ids=tuple(provenance),
        artifacts=artifacts,
        as_of_knowledge=as_of,
        notes=notes,
        payload={
            "overall_status": overall,
            "as_of_sydney": sydney,
            "calendar": list(calendar),
            "content_hash": payload_obj.content_hash,
            "send": False,
            "send_enabled": False,
            "pack_markdown": pack_md,
            "no_send_reason": payload_obj.reason,
            "assembled_desks": [slug for slug in PIPELINE_FOR_PACK if slug in ctx.prior],
            "desk_error_class": {
                slug: ctx.prior[slug].error_class
                for slug in PIPELINE_FOR_PACK
                if slug in ctx.prior and ctx.prior[slug].error_class
            },
        },
    )


class CoordDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
