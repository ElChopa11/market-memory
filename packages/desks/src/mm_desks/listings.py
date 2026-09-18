"""Listings / IPO desk (Phase 6d). Upcoming deals, index events, post-listing path. No orders."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_desks.ladder import make_artifact, stamp_run_hash, run_content_hash
from mm_desks.protocol import (
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
    status_from_slots,
)
from mm_flow.config import load_flow_config
from mm_listings.config import load_listings_config
from mm_listings.engine import compute_listings
from mm_listings.ladder import LISTINGS_LADDER, listings_ladder_payloads
from mm_listings.models import ListingsSnapshot
from mm_listings.observations import snapshot_envelopes
from mm_listings.parse import parse_deal, parse_filing, parse_index_event, parse_outcome
from mm_quant.panel import load_panel_file, panel_from_mapping

SLUG = "listings"
TIER = "listings"
DISPLAY_NAME = "Listings / IPO Desk"


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(text)
    return json.loads(text)


def _block(ctx: DeskContext) -> dict[str, Any]:
    raw = ctx.fixture.raw.get("listings")
    return raw if isinstance(raw, dict) else {}


def _extend_from_path(ctx: DeskContext, rel: str | None, key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not rel:
        return rows
    payload = _load_json(ctx.repo_root / str(rel))
    if isinstance(payload, dict):
        rows.extend(list(payload.get(key) or payload.get("rows") or payload.get("events") or []))
    elif isinstance(payload, list):
        rows.extend(payload)
    return rows


def listings_inputs(ctx: DeskContext) -> dict[str, Any]:
    raw = _block(ctx)
    fallback = ctx.fixture.as_of_knowledge
    fixture_id = ctx.fixture.fixture_id
    deals_raw = list(raw.get("deals") or []) + _extend_from_path(ctx, raw.get("deals_path"), "deals")
    filings_raw = list(raw.get("filings") or []) + _extend_from_path(ctx, raw.get("filings_path"), "filings")
    index_raw = list(raw.get("index_events") or []) + _extend_from_path(
        ctx, raw.get("index_events_path"), "events"
    )
    history_raw = list(raw.get("history") or []) + _extend_from_path(ctx, raw.get("history_path"), "history")
    deals = tuple(
        parse_deal(row, fixture_id=fixture_id, fallback=fallback)
        for row in deals_raw
        if isinstance(row, dict) and (row.get("instrument") or row.get("symbol"))
    )
    filings = tuple(parse_filing(row, fallback=fallback) for row in filings_raw if isinstance(row, dict))
    index_events = tuple(
        parse_index_event(row, fallback=fallback) for row in index_raw if isinstance(row, dict)
    )
    history = tuple(
        parse_outcome(row, fixture_id=fixture_id, fallback=fallback)
        for row in history_raw
        if isinstance(row, dict)
    )
    panel = ctx.fixture.panel
    if raw.get("panel_path"):
        panel = load_panel_file(ctx.repo_root / str(raw["panel_path"]))
    if isinstance(raw.get("panel"), dict):
        panel = panel_from_mapping(raw["panel"])
    return {
        "deals": deals,
        "filings": filings,
        "index_events": index_events,
        "history": history,
        "panel": panel,
        "missing_feed": bool(raw.get("missing_feed")),
    }


def _render_markdown(snap: ListingsSnapshot, session_date: str) -> str:
    br = snap.base_rates
    if br.claimed:
        base_line = (
            f"n={br.n}, median 30d={br.median_30d}, reclaim hit rate={br.reclaim_hit_rate} "
            f"(own Market Memory history)"
        )
    else:
        base_line = f"**no base-rate claim** — {br.reason} (n={br.n}, n_min={br.n_min})"
    lines = [
        f"# Listings / IPO — {session_date}",
        "",
        f"- **Knowledge watermark (as_of_knowledge):** {snap.as_of_knowledge.isoformat()}",
        f"- **Config version:** {snap.config_version}",
        "- **Role:** listings / IPO desk product. Not an order. Quant owns R/sizing.",
        f"- **Base rates:** {base_line}",
        f"- **LLM calls this run:** {snap.llm_calls}",
        "",
        "## Upcoming deals",
        "",
        "| instrument | kind | range | deal size | float % | offered / outstanding | leads | pricing date | lockup | index elig. | filing |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not snap.ideas:
        lines.append("| — | — | unavailable | unavailable | unavailable | unavailable | — | — | — | — | — |")
    for idea in snap.ideas:
        deal = idea.deal
        low = "unavailable" if deal.pricing_low is None else deal.pricing_low
        high = "unavailable" if deal.pricing_high is None else deal.pricing_high
        rng = f"{low}–{high}"
        size = "unavailable" if deal.deal_size_usd is None else deal.deal_size_usd
        flt = "unavailable" if deal.float_pct is None else deal.float_pct
        offered = "unavailable" if deal.shares_offered is None else deal.shares_offered
        outst = "unavailable" if deal.shares_outstanding is None else deal.shares_outstanding
        leads = ", ".join(deal.lead_underwriters) or "unavailable"
        elig = "unavailable" if deal.index_inclusion_eligible is None else str(deal.index_inclusion_eligible)
        filing = deal.filing_type or "unavailable"
        lines.append(
            f"| {deal.instrument} | {deal.kind} | {rng} | {size} | {flt} | {offered} / {outst} | "
            f"{leads} | {deal.expected_pricing_date or 'unavailable'} | {deal.lockup_expiry or 'unavailable'} | "
            f"{elig} | {filing} |"
        )
    lines.extend(
        [
            "",
            "## Mandatory warning block",
            "",
            "| instrument | float size | days of price history | borrow | spread_bps | depth_usd | lockup proximity (d) | liquidity |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not snap.ideas:
        lines.append("| — | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |")
    for idea in snap.ideas:
        w = idea.warning

        def cell(value: object) -> str:
            return "unavailable" if value is None else str(value)

        borrow = "unavailable" if w.borrow_available is None else str(w.borrow_available)
        lines.append(
            f"| {idea.instrument} | {cell(w.float_size)} | {cell(w.days_of_price_history)} | {borrow} | "
            f"{cell(w.spread_bps)} | {cell(w.depth_usd)} | {cell(w.lockup_proximity_days)} | {w.liquidity_verdict} |"
        )
        for note in w.notes:
            lines.append(f"- {idea.instrument}: {note}")
    lines.extend(
        [
            "",
            "## Post-listing tracking",
            "",
            "| instrument | day1 OHLC vs offer | day1 VWAP | 30d | 90d | DD from day1 high | reclaim offer | reclaim day1 VWAP |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not snap.ideas:
        lines.append("| — | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |")
    for idea in snap.ideas:
        t = idea.track

        def cell(value: object) -> str:
            return "unavailable" if value is None else str(value)

        ohlc = (
            f"O={cell(t.day1_open)} H={cell(t.day1_high)} L={cell(t.day1_low)} C={cell(t.day1_close)} "
            f"vs offer {cell(t.day1_vs_offer)}"
        )
        rec_o = "unavailable" if t.reclaimed_offer is None else str(t.reclaimed_offer)
        rec_v = "unavailable" if t.reclaimed_day1_vwap is None else str(t.reclaimed_day1_vwap)
        lines.append(
            f"| {idea.instrument} | {ohlc} | {cell(t.day1_vwap)} | {cell(t.ret_30d)} | {cell(t.ret_90d)} | "
            f"{cell(t.drawdown_from_day1_high)} | {rec_o} | {rec_v} |"
        )
    lines.extend(
        [
            "",
            "## Index events (separate stream)",
            "",
            "| instrument | kind | index | effective | as_of_knowledge |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if not snap.index_events:
        lines.append("| — | — | unavailable | unavailable | — |")
    for event in snap.index_events:
        lines.append(
            f"| {event.instrument} | {event.kind} | {event.index_name or 'unavailable'} | "
            f"{event.effective_date or 'unavailable'} | {event.as_of_knowledge.isoformat()} |"
        )
    lines.extend(
        [
            "",
            "Closed Quant verdicts only. Listings does not invent trade math. "
            "UNTRADEABLE_AT_SIZE = observation only; Risk blocks by `rule_id`.",
            "Degrade, never invent. Post-IPO reclaim screen remains `lab equities reclaim-screen`.",
            "",
        ]
    )
    return "\n".join(lines)


def _ladder_artifacts(snap: ListingsSnapshot, as_of: datetime, ctx: DeskContext) -> tuple[DeskArtifact, ...]:
    payloads = listings_ladder_payloads(snap)
    math_hash = str(payloads.get("trade_math_hash") or "listings_does_not_invent_trade_math")
    run_id = sha256_hex(
        canonical_json(
            {
                "desk": SLUG,
                "as_of": as_of.isoformat(),
                "fixture_id": ctx.fixture.fixture_id,
                "engine": "imp-017.1",
            }
        )
    )[:26]
    built = []
    for artifact_type in LISTINGS_LADDER:
        built.append(
            make_artifact(
                artifact_type=artifact_type,
                run_id=run_id,
                trade_math_hash=math_hash,
                as_of=as_of,
                payload=payloads[artifact_type],
                desk=SLUG,
                threshold=0.0,
            )
        )
    digest = run_content_hash(tuple(built))
    stamped = stamp_run_hash(tuple(built), digest)
    out: list[DeskArtifact] = []
    for row in stamped:
        out.append(
            DeskArtifact(
                name=f"listings-{row.artifact_type.lower()}",
                kind="json",
                content=canonical_json(row.canonical()),
                relpath=f"listings-{row.artifact_type.lower()}.json",
            )
        )
    return tuple(out)


def run(as_of: datetime, ctx: DeskContext) -> DeskOutput:
    cfg = load_listings_config(ctx.repo_root)
    flow_cfg = load_flow_config(ctx.repo_root)
    inputs = listings_inputs(ctx)
    quant = ctx.prior.get("quant")
    math_by: dict[str, str] = {}
    if quant is not None:
        for card in (quant.payload or {}).get("cards") or []:
            inst = str(card.get("instrument") or "").upper()
            digest = card.get("trade_math_hash") or card.get("content_hash")
            if inst and digest:
                math_by[inst] = str(digest)
    snap = compute_listings(
        deals=inputs["deals"],
        filings=inputs["filings"],
        index_events=inputs["index_events"],
        history=inputs["history"],
        panel=inputs["panel"],
        watermark=as_of,
        config=cfg,
        flow_config=flow_cfg,
        repo_root=ctx.repo_root,
        missing_feed=bool(inputs["missing_feed"]),
        trade_math_by_instrument=math_by,
    )
    envelopes = snapshot_envelopes(snap, ingested_at=as_of)
    md = _render_markdown(snap, ctx.fixture.session_date)
    artifact = DeskArtifact(name="listings-ipo", kind="markdown", content=md, relpath="listings.md")
    ladder = _ladder_artifacts(snap, as_of, ctx)
    no_listing = bool(snap.payload.get("no_listing_day"))
    expected = max(len(inputs["deals"]) + len(inputs["index_events"]), 0)
    present = len(snap.ideas) + len(snap.index_events)
    if no_listing and cfg.no_listing_day_is_complete and not inputs["missing_feed"]:
        expected = 0
        present = 0
        status = "OK"
        completeness = 100.0
    else:
        status = status_from_slots(
            present=present,
            expected=max(expected, 1) if inputs["missing_feed"] else max(expected, 1 if expected else 0),
            required_missing=bool(inputs["missing_feed"]),
        )
        completeness = completeness_pct(present, expected if expected else 1)
        if expected == 0 and not inputs["missing_feed"]:
            status = "OK"
            completeness = 100.0
    notes: list[str] = []
    if no_listing:
        notes.append("no listing day; zero LLM")
    if not snap.base_rates.claimed:
        notes.append(snap.base_rates.reason)
    for idea in snap.ideas:
        if idea.observation_only:
            notes.append(f"{idea.instrument}: UNTRADEABLE_AT_SIZE observation only")
        notes.extend(f"{idea.instrument}: {n}" for n in idea.warning.notes)
    provenance = [env.claim_hash for env in envelopes]
    sources = tuple(
        sorted(
            {
                idea.deal.observation_id or "mm_listings.derived"
                for idea in snap.ideas
                if idea.deal.observation_id
            }
            | {"mm_listings.derived"}
        )
    )
    return DeskOutput(
        desk=DISPLAY_NAME,
        slug=SLUG,
        tier=TIER,
        status=status,
        completeness_pct=completeness,
        provenance_ids=tuple(provenance),
        artifacts=(artifact,) + ladder,
        as_of_knowledge=as_of,
        notes=tuple(dict.fromkeys(notes)),
        sources=sources,
        missing=snap.gaps,
        n=len(snap.ideas) + len(snap.index_events),
        payload={
            "ideas": [idea.canonical() for idea in snap.ideas],
            "index_events": [row.canonical() for row in snap.index_events],
            "filings": [row.canonical() for row in snap.filings],
            "base_rates": snap.base_rates.canonical(),
            "verdicts": snap.verdicts(),
            "quant_verdicts": {idea.instrument: idea.quant_verdict for idea in snap.ideas},
            "observation_only": {idea.instrument: idea.observation_only for idea in snap.ideas},
            "warnings": {idea.instrument: idea.warning.canonical() for idea in snap.ideas},
            "llm_calls": snap.llm_calls,
            "no_listing_day": no_listing,
            "claim_hashes": [env.claim_hash for env in envelopes],
            "ladder": [row.name for row in ladder],
        },
    )


class ListingsDesk:
    slug = SLUG
    tier = TIER
    display_name = DISPLAY_NAME

    def run(self, as_of: datetime, ctx: DeskContext) -> DeskOutput:
        return run(as_of, ctx)
