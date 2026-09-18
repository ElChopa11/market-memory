"""Phase 6d listings / IPO screen (IMP-017).

Research product. Not a sixth desk. Deterministic fixture scan. Closed Quant
verdicts only. Quant owns trade math (inherited hash). IC/Risk gates still
required. No LLM. No send. No universe promotion.
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.naming import (
    LISTINGS,
    RESEARCH,
    desk_display,
    desk_tier,
    require_publishing_desk,
    sleeve_display,
)
from mm_common.time import as_utc
from mm_desks.envelope import DeskEnvelope, envelope_from_output, stamp_output
from mm_desks.fixture import load_frozen_day
from mm_desks.ladder import make_artifact, run_content_hash, stamp_run_hash
from mm_desks.models import FrozenDay
from mm_desks.playbook import round_trip_envelopes
from mm_desks.protocol import (
    DEGRADED,
    FAILED,
    OK,
    DeskArtifact,
    DeskContext,
    DeskOutput,
    completeness_pct,
)
from mm_flow.config import load_flow_config
from mm_listings.config import load_listings_config
from mm_listings.engine import compute_listings
from mm_listings.ladder import LISTINGS_LADDER, listings_ladder_payloads
from mm_listings.models import CARD_FOOTER, ENGINE_VERSION, ListingsSnapshot
from mm_listings.observations import snapshot_envelopes
from mm_listings.parse import parse_deal, parse_filing, parse_index_event, parse_outcome
from mm_quant.panel import load_panel_file, panel_from_mapping
from mm_research_kit.quant_review.language import assert_language_clean

PRODUCT_SLUG = LISTINGS
LISTINGS_CFG_REL = Path("config/listings/desk.yaml")
NO_INVENTED_MATH = "listings_does_not_invent_trade_math"
FOOTER = CARD_FOOTER
IC_GATES = {
    "skeptic_required": True,
    "risk_required": True,
    "self_approve": False,
    "paper_open": False,
    "principal_override_required_for_block": True,
}


@dataclass(frozen=True)
class ListingsRun:
    run_id: str
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    status: str
    error_class: str | None
    completeness: float
    content_hash: str
    snapshot: ListingsSnapshot
    notes: tuple[str, ...]
    gaps: tuple[str, ...]
    output: DeskOutput
    envelopes: tuple[DeskEnvelope, ...]
    markdown: str
    llm_calls: int = 0
    engine_version: str = ENGINE_VERSION
    product: str = PRODUCT_SLUG
    png_by_hash: dict[str, bytes] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        snap = self.snapshot.canonical()
        return {
            "run_id": self.run_id,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "fixture_id": self.fixture_id,
            "session_date": self.session_date,
            "status": self.status,
            "error_class": self.error_class,
            "completeness": self.completeness,
            "content_hash": self.content_hash,
            "ideas": snap["ideas"],
            "index_events": snap["index_events"],
            "filings": snap["filings"],
            "base_rates": snap["base_rates"],
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "engine_version": self.engine_version,
            "product": self.product,
            "desk": RESEARCH,
            "desk_display": desk_display(RESEARCH),
            "llm_calls": self.llm_calls,
            "footer": FOOTER,
            "ic_gates": dict(IC_GATES),
            "promote": False,
            "no_listing_day": bool(self.snapshot.payload.get("no_listing_day")),
        }

    def as_public_dict(self) -> dict[str, Any]:
        ideas = self.snapshot.ideas
        return {
            "run_id": self.run_id,
            "status": self.status,
            "error_class": self.error_class,
            "content_hash": self.content_hash,
            "completeness": self.completeness,
            "n": len(ideas) + len(self.snapshot.index_events),
            "n_ideas": len(ideas),
            "n_index_events": len(self.snapshot.index_events),
            "n_unavailable": sum(1 for idea in ideas if idea.track.status == "unavailable"),
            "n_llm_calls": self.llm_calls,
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "desk": RESEARCH,
            "desk_display": desk_display(RESEARCH),
            "product": sleeve_display(LISTINGS),
            "engine_version": self.engine_version,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "send": False,
            "no_send": True,
            "promote": False,
            "ic_gates": dict(IC_GATES),
            "quant_verdicts": {idea.instrument: idea.quant_verdict for idea in ideas},
            "base_rate_claimed": self.snapshot.base_rates.claimed,
        }


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
        "trade_math_by_instrument": {
            str(key).upper(): str(value)
            for key, value in dict(raw.get("trade_math_by_instrument") or {}).items()
            if key and value
        },
    }


def _inherited_math(ctx: DeskContext, explicit: dict[str, str]) -> dict[str, str]:
    math_by = dict(explicit)
    playbook = ctx.fixture.raw.get("playbook") if isinstance(ctx.fixture.raw.get("playbook"), dict) else {}
    for row in playbook.get("ideas") or []:
        if not isinstance(row, dict):
            continue
        inst = str(row.get("instrument") or "").upper()
        digest = row.get("trade_math_hash") or row.get("content_hash")
        if inst and digest and inst not in math_by:
            math_by[inst] = str(digest)
    quant = ctx.prior.get("quant")
    if quant is not None:
        for card in (quant.payload or {}).get("cards") or []:
            inst = str(card.get("instrument") or "").upper()
            digest = card.get("trade_math_hash") or card.get("content_hash")
            if inst and digest and inst not in math_by:
                math_by[inst] = str(digest)
    return math_by


def _cell(value: object) -> str:
    return "unavailable" if value is None else str(value)


def render_markdown(snap: ListingsSnapshot, *, session_date: str, content_hash: str, status: str) -> str:
    product = sleeve_display(LISTINGS)
    desk = desk_display(RESEARCH)
    br = snap.base_rates
    if br.claimed:
        base_line = (
            f"n={br.n}, median 30d={br.median_30d}, reclaim hit rate={br.reclaim_hit_rate} "
            "(own Market Memory history)"
        )
    else:
        base_line = f"**no base-rate claim** — {br.reason} (n={br.n}, n_min={br.n_min})"
    lines = [
        f"# {product} — {session_date}",
        "",
        f"- **Desk / tier:** {desk} / {desk_tier(RESEARCH)}",
        f"- **Product:** {product} (`{LISTINGS}`)",
        f"- **Knowledge watermark (as_of_knowledge):** {snap.as_of_knowledge.isoformat()}",
        f"- **Config version:** {snap.config_version}",
        f"- **Engine:** {ENGINE_VERSION}",
        f"- **content_hash:** `{content_hash}`",
        f"- **Status:** {status}",
        f"- **Base rates:** {base_line}",
        "- **LLM:** none on this fixture path",
        "- **Send:** no",
        "- **Universe:** screen-only. Does not expand Principal membership.",
        "- **IC/Risk:** Skeptic and Risk gates still required. No self-approve. Paper stays closed.",
        "",
        FOOTER,
        "",
        "## Upcoming deals",
        "",
        "| instrument | kind | range | deal size | float % | offered / outstanding | leads | pricing date | lockup | index elig. | filing | quant_verdict |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not snap.ideas:
        lines.append(
            "| — | — | unavailable | unavailable | unavailable | unavailable | — | — | — | — | — | — |"
        )
    for idea in snap.ideas:
        deal = idea.deal
        rng = f"{_cell(deal.pricing_low)}–{_cell(deal.pricing_high)}"
        leads = ", ".join(deal.lead_underwriters) or "unavailable"
        elig = "unavailable" if deal.index_inclusion_eligible is None else str(deal.index_inclusion_eligible)
        filing = deal.filing_type or "unavailable"
        lines.append(
            f"| {deal.instrument} | {deal.kind} | {rng} | {_cell(deal.deal_size_usd)} | {_cell(deal.float_pct)} | "
            f"{_cell(deal.shares_offered)} / {_cell(deal.shares_outstanding)} | {leads} | "
            f"{deal.expected_pricing_date or 'unavailable'} | {deal.lockup_expiry or 'unavailable'} | "
            f"{elig} | {filing} | {idea.quant_verdict} |"
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
        lines.append(
            "| — | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |"
        )
    for idea in snap.ideas:
        w = idea.warning
        borrow = "unavailable" if w.borrow_available is None else str(w.borrow_available)
        lines.append(
            f"| {idea.instrument} | {_cell(w.float_size)} | {_cell(w.days_of_price_history)} | {borrow} | "
            f"{_cell(w.spread_bps)} | {_cell(w.depth_usd)} | {_cell(w.lockup_proximity_days)} | {w.liquidity_verdict} |"
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
        lines.append(
            "| — | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |"
        )
    for idea in snap.ideas:
        t = idea.track
        ohlc = (
            f"O={_cell(t.day1_open)} H={_cell(t.day1_high)} L={_cell(t.day1_low)} C={_cell(t.day1_close)} "
            f"vs offer {_cell(t.day1_vs_offer)}"
        )
        rec_o = "unavailable" if t.reclaimed_offer is None else str(t.reclaimed_offer)
        rec_v = "unavailable" if t.reclaimed_day1_vwap is None else str(t.reclaimed_day1_vwap)
        lines.append(
            f"| {idea.instrument} | {ohlc} | {_cell(t.day1_vwap)} | {_cell(t.ret_30d)} | {_cell(t.ret_90d)} | "
            f"{_cell(t.drawdown_from_day1_high)} | {rec_o} | {rec_v} |"
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
            "## Gaps",
            "",
        ]
    )
    gaps = list(snap.gaps) or ["none"]
    for gap in gaps:
        lines.append(f"- {gap}")
    lines.extend(
        [
            "",
            "Closed Quant verdicts only. Listings inherits Quant trade_math_hash and does not invent R. "
            "UNTRADEABLE_AT_SIZE = observation only; Risk blocks by `rule_id`. "
            "IC/Risk gates still required. Post-IPO reclaim screen remains `lab equities reclaim-screen`.",
            "",
            "## Footer",
            "",
            FOOTER,
            "",
        ]
    )
    text = "\n".join(lines)
    assert_language_clean(text)
    return text


def _status_for(snap: ListingsSnapshot, *, missing_feed: bool, no_listing: bool, complete_empty: bool) -> str:
    if missing_feed:
        return DEGRADED
    if no_listing and complete_empty:
        return OK
    if snap.data_quality == "unavailable":
        return DEGRADED
    if snap.data_quality == "partial":
        return DEGRADED
    if not snap.ideas and not snap.index_events:
        return OK
    return OK


def _ladder_artifacts(snap: ListingsSnapshot, as_of: datetime, ctx: DeskContext, math_hash: str) -> tuple[DeskArtifact, ...]:
    payloads = listings_ladder_payloads(snap)
    inherited = str(payloads.get("trade_math_hash") or math_hash or NO_INVENTED_MATH)
    run_id = sha256_hex(
        canonical_json(
            {
                "desk": RESEARCH,
                "product": PRODUCT_SLUG,
                "as_of": as_of.isoformat(),
                "fixture_id": ctx.fixture.fixture_id,
                "engine": ENGINE_VERSION,
            }
        )
    )[:26]
    built = []
    for artifact_type in LISTINGS_LADDER:
        built.append(
            make_artifact(
                artifact_type=artifact_type,
                run_id=run_id,
                trade_math_hash=inherited,
                as_of=as_of,
                payload=payloads[artifact_type],
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


def run_listings(
    as_of: datetime,
    ctx: DeskContext,
    *,
    day: FrozenDay | None = None,
) -> ListingsRun:
    require_publishing_desk(RESEARCH)
    sleeve_display(LISTINGS)
    frozen = day if day is not None else ctx.fixture
    as_of = as_utc(as_of)
    cfg = load_listings_config(ctx.repo_root)
    flow_cfg = load_flow_config(ctx.repo_root)
    inputs = listings_inputs(DeskContext(repo_root=ctx.repo_root, fixture=frozen, send_enabled=False, prior=ctx.prior))
    math_by = _inherited_math(ctx, inputs["trade_math_by_instrument"])
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
    no_listing = bool(snap.payload.get("no_listing_day"))
    expected = max(len(inputs["deals"]) + len(inputs["index_events"]), 0)
    present = len(snap.ideas) + len(snap.index_events)
    if no_listing and cfg.no_listing_day_is_complete and not inputs["missing_feed"]:
        completeness = 100.0
        status = OK
    else:
        completeness = completeness_pct(present, expected if expected else 1)
        status = _status_for(
            snap,
            missing_feed=bool(inputs["missing_feed"]),
            no_listing=no_listing,
            complete_empty=cfg.no_listing_day_is_complete,
        )
        if inputs["missing_feed"]:
            completeness = 0.0
            status = DEGRADED
        elif expected == 0 and not inputs["missing_feed"]:
            completeness = 100.0
            status = OK
    notes: list[str] = []
    if no_listing:
        notes.append("no listing day; zero LLM")
    if not snap.base_rates.claimed:
        notes.append(snap.base_rates.reason)
    for idea in snap.ideas:
        if idea.observation_only:
            notes.append(f"{idea.instrument}: UNTRADEABLE_AT_SIZE observation only")
        notes.extend(f"{idea.instrument}: {n}" for n in idea.warning.notes)
        if idea.trade_math_hash:
            notes.append(f"{idea.instrument}: inherited trade_math_hash")
        else:
            notes.append(f"{idea.instrument}: {NO_INVENTED_MATH}")
    notes.append("IC/Risk gates required; no self-approve; paper stays closed")
    run_id = sha256_hex(
        canonical_json(
            {
                "as_of": as_of.isoformat(),
                "fixture_id": frozen.fixture_id,
                "engine": ENGINE_VERSION,
                "product": PRODUCT_SLUG,
            }
        )
    )[:26]
    body_for_hash = {
        "run_id": run_id,
        "as_of_knowledge": as_of.isoformat(),
        "fixture_id": frozen.fixture_id,
        "engine_version": ENGINE_VERSION,
        "ideas": [idea.canonical() for idea in snap.ideas],
        "index_events": [row.canonical() for row in snap.index_events],
        "filings": [row.canonical() for row in snap.filings],
        "base_rates": snap.base_rates.canonical(),
        "status": status,
        "completeness": completeness,
        "gaps": list(snap.gaps),
    }
    digest = sha256_hex(canonical_json(body_for_hash))
    markdown = render_markdown(snap, session_date=frozen.session_date, content_hash=digest, status=status)
    artifact = DeskArtifact(
        name="listings-ipo",
        kind="markdown",
        content=markdown,
        relpath="listings.md",
    )
    primary_math = next((idea.trade_math_hash for idea in snap.ideas if idea.trade_math_hash), NO_INVENTED_MATH)
    ladder = _ladder_artifacts(snap, as_of, ctx, str(primary_math))
    envelopes_obs = snapshot_envelopes(snap, ingested_at=as_of)
    provenance = tuple(env.claim_hash for env in envelopes_obs)
    payload = {
        "product": PRODUCT_SLUG,
        "product_display": sleeve_display(LISTINGS),
        "desk": RESEARCH,
        "promote": False,
        "llm": False,
        "send": False,
        "ideas": [idea.canonical() for idea in snap.ideas],
        "index_events": [row.canonical() for row in snap.index_events],
        "filings": [row.canonical() for row in snap.filings],
        "base_rates": snap.base_rates.canonical(),
        "verdicts": snap.verdicts(),
        "quant_verdicts": {idea.instrument: idea.quant_verdict for idea in snap.ideas},
        "observation_only": {idea.instrument: idea.observation_only for idea in snap.ideas},
        "warnings": {idea.instrument: idea.warning.canonical() for idea in snap.ideas},
        "llm_calls": 0,
        "n_llm_calls": 0,
        "no_listing_day": no_listing,
        "claim_hashes": list(provenance),
        "ladder": [row.name for row in ladder],
        "engine_version": ENGINE_VERSION,
        "footer": FOOTER,
        "ic_gates": dict(IC_GATES),
        "trade_math_inherited": {idea.instrument: idea.trade_math_hash for idea in snap.ideas},
    }
    output = DeskOutput(
        desk=desk_display(RESEARCH),
        slug=RESEARCH,
        tier=desk_tier(RESEARCH),
        status=status if status != FAILED else FAILED,
        completeness_pct=completeness,
        provenance_ids=provenance,
        artifacts=(artifact,) + ladder,
        as_of_knowledge=as_of,
        notes=tuple(dict.fromkeys(notes)),
        payload=payload,
        cadence="daily",
        op="observation",
        universe="screen_only",
        n=len(snap.ideas) + len(snap.index_events),
        missing=snap.gaps,
        sources=tuple(
            sorted(
                {idea.deal.source for idea in snap.ideas if idea.deal.source} | {"mm_listings.derived"}
            )
        ),
    )
    stamped = stamp_output(output, ctx)
    env = envelope_from_output(stamped, repo_root=ctx.repo_root)
    envelopes = round_trip_envelopes((env,))
    return ListingsRun(
        run_id=run_id,
        as_of_knowledge=as_of,
        fixture_id=frozen.fixture_id,
        session_date=frozen.session_date,
        status=stamped.status,
        error_class=stamped.error_class,
        completeness=stamped.completeness_pct,
        content_hash=digest,
        snapshot=snap,
        notes=tuple(dict.fromkeys(notes)),
        gaps=snap.gaps,
        output=stamped,
        envelopes=envelopes,
        markdown=markdown,
        llm_calls=0,
    )


def run_listings_from_fixture(path: Path, *, repo_root: Path) -> ListingsRun:
    root = Path(repo_root).resolve()
    day = load_frozen_day(Path(path), repo_root=root)
    ctx = DeskContext(repo_root=root, fixture=day, send_enabled=False)
    return run_listings(day.as_of_knowledge, ctx, day=day)


def write_listings_artifacts(run: ListingsRun, *, out_root: Path) -> dict[str, str]:
    day_dir = Path(out_root).resolve() / "research" / "listings" / run.session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    json_path = day_dir / "listings.json"
    md_path = day_dir / "listings.md"
    sha_path = day_dir / "listings.sha256"
    json_path.write_text(json.dumps(run.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(run.markdown if run.markdown.endswith("\n") else run.markdown + "\n", encoding="utf-8")
    sha_path.write_text(run.content_hash + "\n", encoding="utf-8")
    return {
        "listings.json": str(json_path),
        "listings.md": str(md_path),
        "listings.sha256": str(sha_path),
    }
