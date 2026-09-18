"""Fill templates/output-contract.md from desk outputs. Degrade, never invent."""

from __future__ import annotations

from datetime import datetime

from mm_common.time import in_ops_tz
from mm_desks.protocol import DeskContext, DeskOutput
from mm_desks.universe import membership_of

_UNAVAILABLE = "unavailable"


def _desk(ctx: DeskContext, slug: str) -> DeskOutput | None:
    return ctx.prior.get(slug)


def _tape_rows(ctx: DeskContext) -> list[str]:
    rows: list[str] = []
    for slug in ("crypto", "equities"):
        out = _desk(ctx, slug)
        if not out:
            continue
        for item in out.payload.get("tape") or []:
            value = item.get("value")
            if value in (None, "", _UNAVAILABLE):
                value = _UNAVAILABLE
            oid = item.get("observation_id") or "—"
            rows.append(
                f"| {item.get('instrument')} | {item.get('metric')} | {value} | "
                f"{item.get('source') or '—'} | {item.get('freshness') or _UNAVAILABLE} | {oid} |"
            )
    intel = _desk(ctx, "intel")
    if intel:
        for feed in intel.payload.get("feeds") or []:
            if feed.get("status") != "ok":
                continue
            oid = feed.get("observation_id") or "—"
            rows.append(
                f"| — | {feed.get('source_id')} | {feed.get('status')} | intel | "
                f"{feed.get('freshness') or _UNAVAILABLE} | {oid} |"
            )
    if not rows:
        rows.append(f"| — | — | {_UNAVAILABLE} | — | {_UNAVAILABLE} | — |")
    return rows


def _gaps(ctx: DeskContext) -> list[str]:
    rows: list[str] = []
    intel = _desk(ctx, "intel")
    if intel:
        for source_id in intel.payload.get("required_missing") or []:
            rows.append(f"| {source_id} missing | Intel assemble DEGRADED | Data & Market Memory Desk |")
        for feed in intel.payload.get("feeds") or []:
            if feed.get("status") != "ok":
                rows.append(
                    f"| {feed.get('source_id')} {feed.get('status')} | not invented | Data & Market Memory Desk |"
                )
    quant = _desk(ctx, "quant")
    if quant:
        for card in quant.payload.get("cards") or []:
            for gap in card.get("gaps") or []:
                rows.append(f"| {card.get('instrument')} {gap} | factor unavailable | Quant & Market Structure Desk |")
    for slug in ("intel", "crypto", "equities", "quant", "skeptic", "risk"):
        out = _desk(ctx, slug)
        if out is not None and out.status == "FAILED":
            err = out.error_class or "desk_error"
            rows.append(f"| {slug} {err} | Coord assembled with desk FAILED | {out.desk} |")
    if _desk(ctx, "coord") is None:
        rows.append("| flow/macro/regime note | Phase 6b parked | Macro & Cross-Asset Desk |")
    if not rows:
        rows.append("| none listed | — | — |")
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        out.append(row)
    return out


def render_output_contract(as_of: datetime, ctx: DeskContext, *, calendar_lines: tuple[str, ...]) -> str:
    day = ctx.fixture
    thesis = ctx.thesis
    intel = _desk(ctx, "intel")
    quant = _desk(ctx, "quant")
    skeptic = _desk(ctx, "skeptic")
    risk = _desk(ctx, "risk")
    data_quality = "unavailable"
    if intel:
        data_quality = str(intel.payload.get("data_quality") or "partial")
    membership = membership_of(thesis.instrument, ctx.repo_root) if thesis else "not_in_membership"
    lifecycle = thesis.status if thesis else "draft"
    quant_verdict = (quant.payload.get("verdict") if quant else None) or "unset"
    quant_reasons = ", ".join((quant.payload.get("reason_codes") if quant else None) or []) or "—"
    skeptic_verdict = (skeptic.payload.get("verdict") if skeptic else None) or "pending"
    fail_mode = skeptic.payload.get("fail_mode") if skeptic else None
    if fail_mode == "return":
        skeptic_verdict_label = "revise (FAIL return)"
    elif fail_mode == "archive":
        skeptic_verdict_label = "reject (FAIL archive)"
    else:
        skeptic_verdict_label = skeptic_verdict
    risk_decision = (risk.payload.get("decision") if risk else None) or "pending"
    rule_id = (risk.payload.get("rule_id") if risk else None) or "—"
    config_version = (risk.payload.get("config_version") if risk else None) or "—"
    terminal = "yes" if risk and risk.payload.get("terminal") else "no"
    intent_row = "none"
    if thesis and thesis.intent:
        inv = thesis.invalidation or _UNAVAILABLE
        intent_row = (
            f"| {thesis.instrument} | {thesis.intent} | {inv} | {thesis.horizon or '—'} | "
            f"{', '.join(thesis.evidence_ids) or '—'} |"
        )
    skeptic_findings = "—"
    if skeptic and skeptic.notes:
        skeptic_findings = "; ".join(skeptic.notes)
    calendar = "\n".join(calendar_lines) if calendar_lines else "none"

    lines = [
        "# Output contract (Principal briefing)",
        "",
        "Research / desk product copy for the Principal. **Not an order. Not Execution. Not a Skeptic or Risk self-clear.**",
        "",
        f"- **Engine:** imp-014.1",
        f"- **Fixture:** {day.fixture_id}",
        "",
        "## HEADER",
        "",
        f"- **As-of (Australia/Sydney):** {in_ops_tz(as_of).isoformat()}",
        f"- **Knowledge watermark (as_of_knowledge):** {as_of.isoformat()}",
        "- **Authoring desk / tier:** 3a Crypto | 3b Equities | 4 Quant | other: Coord pack",
        f"- **Universe membership:** `{membership}`",
        f"- **Lifecycle status:** `{lifecycle}`",
        f"- **Intent / thesis id:** {thesis.slug if thesis else '—'}",
        f"- **Data quality:** `{data_quality}`",
        "",
        "## TAPE",
        "",
        "What the tape showed at the watermark. Source + freshness on every row. No invented last print.",
        "",
        "| instrument | metric | value | source | freshness | observation_id |",
        "| --- | --- | --- | --- | --- | --- |",
        *_tape_rows(ctx),
        "",
        "## WHAT CHANGED",
        "",
        day.what_changed or "none",
        "",
        "## TRADE IDEAS (intent-only)",
        "",
        "Falsifiable intents, not orders. Each row needs invalidation language. No size. No execution path.",
        "",
        "| instrument | intent (one sentence) | invalidation | horizon | evidence refs |",
        "| --- | --- | --- | --- | --- |",
        intent_row,
        "",
        "## QUANT NOTE",
        "",
        f"- **Verdict:** `{quant_verdict}`",
        f"- **Reason code(s):** {quant_reasons}",
        "- **Relative-value / reclaim / structure (not executable-arb unless criteria are complete):** factor layer only",
        "",
        "## SKEPTIC FLAGS",
        "",
        f"- **Independent Skeptic of record:** {(thesis.reviewer if thesis else 'Independent Skeptic')} (not the author)",
        f"- **Verdict:** `{skeptic_verdict_label}`",
        f"- **Leakage / look-ahead / crowding / already-priced / invalidation quality:** {skeptic_findings}",
        "",
        "## RISK STATUS",
        "",
        f"- **Decision:** `{risk_decision}`",
        f"- **rule_id / config_version:** `{rule_id}` / `{config_version}`",
        f"- **BLOCK terminal?** {terminal} (no paper/live) unless Principal override recorded",
        "- **Principal override:** `none`",
        "",
        "## BOOK",
        "",
        "Paper/shadow book only. Live is later and hard-gated. Empty is honest.",
        "",
        "| thesis_id | paper status | invalidation | max loss | notes |",
        "| --- | --- | --- | --- | --- |",
        "| — | none | — | — | paper not opened by desk runners |",
        "",
        "## CALENDAR (stub)",
        "",
        calendar,
        "",
        "## DATA GAPS",
        "",
        "Always list. Telegram delivery is 5e; flow/macro/regime is Phase 6b (parked).",
        "",
        "| gap | impact | owner desk |",
        "| --- | --- | --- |",
        *_gaps(ctx),
        "",
        "Live remains hard-gated. This file does not authorise paper or live. No secrets.",
        "",
    ]
    return "\n".join(lines) + "\n"
