"""Hive PLAYBOOK runner (Phase 6c). Artifact ladder + Quant math + optional writer.

LLM is WRITER/CRITIC only. A no-setup fixture day makes zero LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_desks.chart import compute_levels, png_filename, render_png
from mm_desks.dq import publish_allowed
from mm_desks.envelope import DeskEnvelope, envelope_from_row
from mm_desks.fixture import load_frozen_day
from mm_desks.ladder import (
    ARTIFACT_TYPES,
    ENGINE_VERSION,
    MAX_IDEAS,
    LadderArtifact,
    artifact_to_envelope,
    assert_math_inherited,
    make_artifact,
    run_content_hash,
    stamp_run_hash,
)
from mm_desks.llm.budget import ERROR_BUDGET_EXCEEDED, TokenBudget, load_token_budget, write_day_disable_flag
from mm_desks.llm.client import LlmClient, LlmResult
from mm_desks.llm.context import build_writer_payload, cap_rows
from mm_desks.llm.grounding import (
    GroundingError,
    ProvenanceRow,
    assert_claim_tags,
    assert_named_entities,
    assert_no_backfill,
    assert_render,
    substitute_placeholders,
)
from mm_desks.llm.ledger import LlmCallRecord
from mm_desks.llm.prompts import load_prompt
from mm_desks.models import FrozenDay
from mm_desks.postmortem import PostMortemRequired, assert_can_publish_new_idea, template_exists
from mm_desks.protocol import DEGRADED, FAILED, OK
from mm_quant.models import SeriesBar
from mm_quant.trade_math import (
    ProbabilityProvenance,
    TradeMath,
    TradeMathMismatch,
    compute_trade_math,
)

PLAYBOOK_CFG_REL = Path("config/playbook/ladder.yaml")


@dataclass(frozen=True)
class PlaybookRun:
    run_id: str
    as_of_knowledge: datetime
    fixture_id: str
    status: str
    error_class: str | None
    completeness: float
    artifacts: tuple[LadderArtifact, ...]
    content_hash: str
    trade_math_hash: str
    llm_calls: tuple[LlmCallRecord, ...]
    notes: tuple[str, ...]
    gaps: tuple[str, ...]
    envelopes: tuple[DeskEnvelope, ...]
    png_by_hash: dict[str, bytes] = field(default_factory=dict)
    ops_escalation: str | None = None
    engine_version: str = ENGINE_VERSION

    def canonical(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "fixture_id": self.fixture_id,
            "status": self.status,
            "error_class": self.error_class,
            "completeness": self.completeness,
            "content_hash": self.content_hash,
            "trade_math_hash": self.trade_math_hash,
            "artifacts": [row.canonical() for row in self.artifacts],
            "notes": list(self.notes),
            "gaps": list(self.gaps),
            "engine_version": self.engine_version,
            "llm_calls": [row.canonical() for row in self.llm_calls],
            "ops_escalation": self.ops_escalation,
        }

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "error_class": self.error_class,
            "content_hash": self.content_hash,
            "trade_math_hash": self.trade_math_hash,
            "completeness": self.completeness,
            "n_artifacts": len(self.artifacts),
            "n_llm_calls": len(self.llm_calls),
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "ops_escalation": self.ops_escalation,
        }


def deterministic_run_id(*, as_of: datetime, fixture_id: str) -> str:
    return sha256_hex(
        canonical_json(
            {
                "as_of": as_utc(as_of).isoformat(),
                "fixture_id": fixture_id,
                "engine": ENGINE_VERSION,
            }
        )
    )[:26]


def load_playbook_spec(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root) / PLAYBOOK_CFG_REL
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _ideas(day: FrozenDay) -> list[dict[str, Any]]:
    block = day.raw.get("playbook") if isinstance(day.raw.get("playbook"), dict) else {}
    ideas = block.get("ideas") or day.raw.get("ideas") or []
    return [dict(row) for row in ideas if isinstance(row, dict)]


def _p_win(raw: dict[str, Any]) -> ProbabilityProvenance:
    p = raw.get("p_win") if isinstance(raw.get("p_win"), dict) else {}
    kind = str(p.get("kind") or "base_rate")
    return ProbabilityProvenance(
        kind=kind,
        value=float(p.get("value") or 0.0),
        n=None if p.get("n") is None else int(p.get("n")),
        window=None if p.get("window") is None else str(p.get("window")),
        name=None if p.get("name") is None else str(p.get("name")),
        version=None if p.get("version") is None else str(p.get("version")),
        judgement=None if p.get("judgement") is None else str(p.get("judgement")),
    )


def _templated_no_setup(*, as_of: str, gaps: list[str]) -> str:
    gap_line = ", ".join(gaps) if gaps else "none named"
    return (
        "no actionable setup\n"
        f"as_of={as_of}\n"
        f"gaps: {gap_line}\n"
        "Abstention is correct. Not a call.\n"
    )


def _feeds_missing(day: FrozenDay) -> tuple[str, ...]:
    missing = []
    for feed in day.feeds:
        if feed.status != "ok":
            missing.append(feed.source_id)
    return tuple(missing)


def _evidence_dates(day: FrozenDay) -> set[str]:
    dates = {day.session_date, as_utc(day.as_of_knowledge).date().isoformat()}
    return dates


def run_playbook(
    day: FrozenDay,
    *,
    repo_root: Path,
    llm: LlmClient | None = None,
    budget: TokenBudget | None = None,
    force_math_mismatch: bool = False,
    research_root: Path | None = None,
    closed_slugs: tuple[str, ...] = (),
) -> PlaybookRun:
    as_of = as_utc(day.as_of_knowledge)
    run_id = deterministic_run_id(as_of=as_of, fixture_id=day.fixture_id)
    spec = load_playbook_spec(repo_root)
    threshold = float(spec.get("dq_publish_threshold") or 0.8)
    max_ideas = int(spec.get("max_ideas") or MAX_IDEAS)
    notes: list[str] = []
    gaps: list[str] = []
    missing_feeds = _feeds_missing(day)
    gaps.extend(missing_feeds)
    if any("fred" in m.lower() for m in missing_feeds):
        gaps.append("rates")
        notes.append("FRED unavailable; rates not invented")

    ideas_all = _ideas(day)
    n_total = len(ideas_all)
    ideas = ideas_all[:max_ideas]
    if n_total > max_ideas:
        notes.append(f"{max_ideas} ideas shown; {n_total - max_ideas} cut (max 3)")

    no_setup = n_total == 0
    tok = budget or load_token_budget(repo_root)
    client = llm
    llm_records: list[LlmCallRecord] = []

    # Completeness of fixture tape vs inventory as a stand-in for "fields".
    expected_slots = max(1, len(day.inventory) + max(1, n_total) * 6)
    present_slots = sum(1 for f in day.feeds if f.status == "ok") + len(ideas) * 6
    fixture_completeness = present_slots / expected_slots

    status = OK
    error_class: str | None = None
    ops_escalation: str | None = None
    math_hash = sha256_hex(b"no-setup")
    math_by_instrument: dict[str, TradeMath] = {}

    try:
        if not template_exists(repo_root):
            raise PostMortemRequired("templates/post-mortem.md missing")
        if ideas and closed_slugs:
            for idea in ideas:
                assert_can_publish_new_idea(
                    instrument=str(idea.get("instrument") or ""),
                    closed_slugs=closed_slugs,
                    research_root=research_root or (Path(repo_root) / "research"),
                    repo_root=repo_root,
                )
    except PostMortemRequired as exc:
        status = FAILED
        error_class = "post_mortem_required"
        notes.append(str(exc))
        ideas = []
        no_setup = True

    if ideas and not publish_allowed(fixture_completeness, threshold):
        notes.append(
            f"DQ completeness {fixture_completeness:.2f} below threshold {threshold}; no idea published"
        )
        ideas = []
        no_setup = True
        status = DEGRADED if status == OK else status
        gaps.append("dq_below_threshold")

    if fixture_completeness < 0.5 and not ideas:
        notes.append("low-completeness fixture; gaps-heavy no-idea brief")
        no_setup = True

    for idea in ideas:
        try:
            math = compute_trade_math(
                instrument=str(idea.get("instrument") or "UNK"),
                entry=float(idea["entry"]),
                stop=float(idea["stop"]),
                targets=tuple(float(t) for t in (idea.get("targets") or ())),
                p_win=_p_win(idea),
                avg_r_win=float(idea.get("avg_R_win") or idea.get("avg_r_win") or 1.0),
                atr_pct=None if idea.get("atr_pct") is None else float(idea.get("atr_pct")),
                stop_distance_atr=None
                if idea.get("stop_distance_atr") is None
                else float(idea.get("stop_distance_atr")),
                funding_rate=float(idea.get("funding_rate") or 0.0),
                est_slippage=None if idea.get("est_slippage") is None else float(idea.get("est_slippage")),
                asset_class=str(idea.get("asset_class") or "unknown"),
                repo_root=repo_root,
            )
        except (KeyError, TypeError, ValueError) as exc:
            status = FAILED
            error_class = "trade_math_failed"
            notes.append(str(exc))
            no_setup = True
            ideas = []
            break
        math_by_instrument[math.instrument] = math
        notes.extend(math.notes)
        math_hash = math.content_hash()
        if math.below_min_sample:
            notes.append(f"{math.instrument}: n < min_sample; size_pct=0")

    # Chart levels once per instrument in the idea set (or thesis instrument on no-setup).
    instruments = [str(i.get("instrument") or "").upper() for i in ideas] or [day.thesis.instrument.upper()]
    instruments = list(dict.fromkeys(instruments))[:MAX_IDEAS]
    bars: tuple[SeriesBar, ...] = day.panel.bars
    levels_by = {name: compute_levels(name, bars, as_of=as_of) for name in instruments}
    png_by_hash: dict[str, bytes] = {}

    inherited = math_hash
    artifacts: list[LadderArtifact] = []

    # --- DAILY_BIAS (template, zero LLM) ---
    bias_rows = []
    for idea in ideas[:MAX_IDEAS]:
        inst = str(idea.get("instrument") or "").upper()
        lv = levels_by.get(inst)
        level = idea.get("level")
        if level is None and lv is not None:
            level = lv.session_vwap
        bias_rows.append(
            {
                "instrument": inst,
                "direction": idea.get("direction") or "?",
                "conviction": idea.get("conviction") or "?",
                "level": level if level is not None else "?",
            }
        )
    if not bias_rows:
        bias_payload = {
            "instrument": instruments[0],
            "direction": "none",
            "conviction": "n/a",
            "level": "n/a",
            "trade_math_hash": inherited,
            "executive": "no actionable setup",
        }
    else:
        bias_payload = {
            "instrument": bias_rows[0]["instrument"],
            "direction": bias_rows[0]["direction"],
            "conviction": bias_rows[0]["conviction"],
            "level": bias_rows[0]["level"],
            "ideas": bias_rows,
            "trade_math_hash": inherited,
            "n_cut": max(0, n_total - len(bias_rows)),
        }
    artifacts.append(
        make_artifact(
            artifact_type="DAILY_BIAS",
            run_id=run_id,
            trade_math_hash=inherited,
            as_of=as_of,
            payload=bias_payload,
            spec=spec,
            threshold=threshold,
        )
    )

    # --- EDGE_SCAN (template SCAN_CARD; prose optional writer) ---
    primary = ideas[0] if ideas else None
    edge_prose = _templated_no_setup(as_of=as_of.isoformat(), gaps=gaps)
    used_writer = False
    if primary is not None and not no_setup:
        edge_payload_base = {
            "instrument": str(primary.get("instrument") or "").upper(),
            "catalyst": primary.get("catalyst") or "?",
            "source": primary.get("source") or "?",
            "as_of": as_of.isoformat(),
            "invalidator": primary.get("invalidator") or "?",
            "trade_math_hash": inherited,
        }
        if client is not None and client.completer is not None:
            used_writer = True
            prompt = load_prompt("EDGE_SCAN", repo_root)
            summary = cap_rows(
                [{"instrument": edge_payload_base["instrument"], "catalyst": "see evidence"}],
                tok.summary_row_cap,
            )
            payload = build_writer_payload(
                prefix=prompt.text,
                summary_rows=summary,
                cap=tok.summary_row_cap,
                evidence={
                    "instruments": instruments,
                    "sources": [str(primary.get("source") or "")],
                    "dates": sorted(_evidence_dates(day)),
                    "gaps": gaps,
                },
            )
            result = client.complete(
                artifact_type="EDGE_SCAN",
                desk_slug="coord",
                run_id=run_id,
                prompt=prompt,
                user_payload=payload,
            )
            llm_records.extend(client.records[len(llm_records) :])
            edge_prose, status, error_class, ops_escalation, notes = _apply_writer(
                result,
                status=status,
                error_class=error_class,
                ops_escalation=ops_escalation,
                notes=notes,
                tok=tok,
                repo_root=repo_root,
                fallback=edge_prose,
                day=day,
                instruments=set(instruments),
                sources={str(primary.get("source") or "")},
                math_by=math_by_instrument,
                levels_by=levels_by,
                missing_feeds=missing_feeds,
                gaps=gaps,
            )
        else:
            edge_prose = (
                f"{edge_payload_base['catalyst']} (observed)\n"
                f"source {edge_payload_base['source']} reported catalyst at {as_of.date().isoformat()}\n"
                f"invalidator: {edge_payload_base['invalidator']}\n"
            )
    else:
        edge_payload_base = {
            "instrument": instruments[0],
            "catalyst": "none",
            "source": "n/a",
            "as_of": as_of.isoformat(),
            "invalidator": "n/a",
            "trade_math_hash": inherited,
        }
    artifacts.append(
        make_artifact(
            artifact_type="EDGE_SCAN",
            run_id=run_id,
            trade_math_hash=inherited,
            as_of=as_of,
            payload=edge_payload_base | {"prose": edge_prose, "scan_card": "template"},
            spec=spec,
            threshold=threshold,
        )
    )

    # --- INTEL_PACKET (template) ---
    detail = {
        "feeds": [f.canonical() for f in day.feeds],
        "missing": list(missing_feeds),
        "ideas": ideas,
        "trade_math": None if not math_by_instrument else next(iter(math_by_instrument.values())).canonical(),
    }
    artifacts.append(
        make_artifact(
            artifact_type="INTEL_PACKET",
            run_id=run_id,
            trade_math_hash=inherited,
            as_of=as_of,
            payload={
                "instrument": instruments[0],
                "detail": detail,
                "trade_math_hash": inherited,
            },
            spec=spec,
            threshold=0.0,
        )
    )

    # --- CHART_ARTIFACT (template, zero LLM) ---
    inst0 = instruments[0]
    lv = levels_by[inst0]
    chart_hash = lv.content_hash()
    closes = tuple(b.close for b in bars if b.instrument.upper() == inst0)
    png = render_png(lv, closes)
    png_name = png_filename(chart_hash)
    png_by_hash[chart_hash] = png
    artifacts.append(
        make_artifact(
            artifact_type="CHART_ARTIFACT",
            run_id=run_id,
            trade_math_hash=inherited,
            as_of=as_of,
            payload={
                "instrument": inst0,
                "levels": lv.canonical(),
                "png_filename": png_name,
                "png_content_hash": chart_hash,
                "trade_math_hash": inherited,
            },
            spec=spec,
            threshold=threshold if closes else 0.0,
        )
    )

    # --- OFFICIAL_BRIEF (writer optional) ---
    brief_text = _templated_no_setup(as_of=as_of.isoformat(), gaps=gaps)
    if ideas and not no_setup and client is not None and client.completer is not None:
        prompt = load_prompt("OFFICIAL_BRIEF", repo_root)
        result = client.complete(
            artifact_type="OFFICIAL_BRIEF",
            desk_slug="coord",
            run_id=run_id,
            prompt=prompt,
            user_payload=build_writer_payload(
                prefix=prompt.text,
                summary_rows=[{"instrument": instruments[0], "bias": bias_rows[0]["direction"] if bias_rows else "none"}],
                cap=tok.summary_row_cap,
                evidence={
                    "instruments": instruments,
                    "sources": list({str(i.get("source") or "") for i in ideas}),
                    "dates": sorted(_evidence_dates(day)),
                    "gaps": gaps,
                },
            ),
        )
        llm_records.extend([r for r in client.records if r not in llm_records])
        brief_text, status, error_class, ops_escalation, notes = _apply_writer(
            result,
            status=status,
            error_class=error_class,
            ops_escalation=ops_escalation,
            notes=notes,
            tok=tok,
            repo_root=repo_root,
            fallback=brief_text,
            day=day,
            instruments=set(instruments),
            sources={str(i.get("source") or "") for i in ideas},
            math_by=math_by_instrument,
            levels_by=levels_by,
            missing_feeds=missing_feeds,
            gaps=gaps,
        )
    elif ideas:
        brief_text = f"no LLM; templated cut for {instruments[0]} (observed)\n" + ideas_line(bias_rows, n_total)

    artifacts.append(
        make_artifact(
            artifact_type="OFFICIAL_BRIEF",
            run_id=run_id,
            trade_math_hash=inherited,
            as_of=as_of,
            payload={
                "executive_cut": brief_text[:1200],
                "trade_math_hash": inherited,
                "n_ideas": len(ideas),
            },
            spec=spec,
            threshold=0.0,
        )
    )

    # --- STATE_CARD (template, zero LLM) ---
    for inst in instruments:
        idea = next((i for i in ideas if str(i.get("instrument") or "").upper() == inst), None)
        permission = "OFF" if no_setup or not ideas else str((idea or {}).get("permission") or "OFF")
        artifacts.append(
            make_artifact(
                artifact_type="STATE_CARD",
                run_id=run_id,
                trade_math_hash=inherited,
                as_of=as_of,
                payload={
                    "instrument": inst,
                    "state": str((idea or {}).get("state") or "flat"),
                    "permission": permission,
                    "rearm": str((idea or {}).get("rearm") or "n/a"),
                    "trade_math_hash": inherited,
                },
                spec=spec,
                threshold=threshold,
            )
        )

    typed = tuple(a for a in artifacts if a.artifact_type in ARTIFACT_TYPES)
    try:
        if force_math_mismatch:
            raise TradeMathMismatch("forced trade math mismatch")
        assert_math_inherited(typed, inherited)
    except TradeMathMismatch as exc:
        status = FAILED
        error_class = "math_mismatch"
        notes.append(str(exc))

    digest = run_content_hash(typed)
    typed = stamp_run_hash(typed, digest)
    envelopes = tuple(artifact_to_envelope(row) for row in typed)

    if used_writer is False and client is not None:
        llm_records = tuple(client.records)  # type: ignore[assignment]
    else:
        llm_records = tuple(client.records) if client is not None else tuple(llm_records)

    # no-setup must not have called the completer
    n_llm = len(llm_records) if client is not None and client.completer is not None and not no_setup else (
        len(client.records) if client is not None else 0
    )
    if no_setup and client is not None and any(r.input_tokens or r.output_tokens for r in client.records):
        status = FAILED
        error_class = "llm_on_no_setup"
        notes.append("no-setup day must run with zero LLM calls")

    if no_setup and (client is None or client.completer is None):
        n_llm = 0
        llm_records = ()

    return PlaybookRun(
        run_id=run_id,
        as_of_knowledge=as_of,
        fixture_id=day.fixture_id,
        status=status,
        error_class=error_class,
        completeness=round(fixture_completeness * 100.0, 2),
        artifacts=typed,
        content_hash=digest,
        trade_math_hash=inherited,
        llm_calls=tuple(llm_records) if not no_setup else (),
        notes=tuple(notes),
        gaps=tuple(dict.fromkeys(gaps)),
        envelopes=envelopes,
        png_by_hash=png_by_hash,
        ops_escalation=ops_escalation,
    )


def ideas_line(bias_rows: list[dict[str, Any]], n_total: int) -> str:
    shown = len(bias_rows)
    if n_total <= 0:
        return "no actionable setup"
    if shown < n_total:
        return f"{shown} ideas shown; {n_total - shown} cut (max 3)"
    return f"{shown} ideas"


def _apply_writer(
    result: LlmResult,
    *,
    status: str,
    error_class: str | None,
    ops_escalation: str | None,
    notes: list[str],
    tok: TokenBudget,
    repo_root: Path,
    fallback: str,
    day: FrozenDay,
    instruments: set[str],
    sources: set[str],
    math_by: dict[str, TradeMath],
    levels_by: dict[str, Any],
    missing_feeds: tuple[str, ...],
    gaps: list[str],
) -> tuple[str, str, str | None, str | None, list[str]]:
    if result.error_class == "grounding_failed":
        notes.append("NUMERIC/ENTITY LOCK: writer output failed grounding")
        return fallback, FAILED, "grounding_failed", ops_escalation, notes
    if result.error_class in {ERROR_BUDGET_EXCEEDED, "llm_day_disabled"}:
        notes.append("per_run token budget exceeded; templated output; no idea published from writer")
        if result.error_class == ERROR_BUDGET_EXCEEDED:
            status = DEGRADED
            error_class = ERROR_BUDGET_EXCEEDED
            ops_escalation = "coord: budget_exceeded — complete with templated output, never silent truncate"
            notes.append("no idea published (budget_exceeded)")
        else:
            status = DEGRADED
            error_class = result.error_class
            write_day_disable_flag(repo_root, tok.disable_flag)
            ops_escalation = "coord: llm_day_disabled — Principal reset required"
        return fallback, status, error_class, ops_escalation, notes
    if result.templated or not result.ok:
        notes.append("writer schema/budget fallback to template")
        if status == OK:
            status = DEGRADED
        if error_class is None:
            error_class = result.error_class or "schema_fail"
        return fallback, status, error_class, ops_escalation, notes
    try:
        assert_claim_tags(list(result.claim_tags))
        rows = _placeholder_rows(math_by, levels_by, day)
        rendered = substitute_placeholders(result.prose, rows)
        assert_render(rendered, rows)
        assert_named_entities(
            rendered,
            instruments=instruments,
            sources=sources,
            dates=_evidence_dates(day),
        )
        assert_no_backfill(rendered, missing_feeds=missing_feeds, gaps=tuple(gaps))
        return rendered, status, error_class, ops_escalation, notes
    except GroundingError as exc:
        notes.append(str(exc))
        return fallback, FAILED, "grounding_failed", ops_escalation, notes


def _placeholder_rows(
    math_by: dict[str, TradeMath],
    levels_by: dict[str, Any],
    day: FrozenDay,
) -> dict[str, ProvenanceRow]:
    rows: dict[str, ProvenanceRow] = {}
    for inst, math in math_by.items():
        key = inst.lower()
        prov = f"math:{math.content_hash()[:12]}"
        rows[f"{key}_entry"] = ProvenanceRow(f"{key}_entry", f"{math.entry}", prov, "computed")
        rows[f"{key}_stop"] = ProvenanceRow(f"{key}_stop", f"{math.stop}", prov, "computed")
        if math.r_targets:
            r0 = math.r_targets[0]
            rows["r_target_1"] = ProvenanceRow("r_target_1", f"{r0}", prov, "computed")
            rows[f"{key}_r_target_1"] = ProvenanceRow(f"{key}_r_target_1", f"{r0}", prov, "computed")
        last = next((b.close for b in reversed(day.panel.bars) if b.instrument.upper() == inst), None)
        if last is not None:
            rows[f"{key}_last"] = ProvenanceRow(f"{key}_last", f"{last}", f"obs:{inst}:last", "observed")
    for inst, lv in levels_by.items():
        key = inst.lower()
        if lv.session_vwap is not None:
            rows[f"{key}_vwap"] = ProvenanceRow(
                f"{key}_vwap", f"{lv.session_vwap}", f"chart:{lv.content_hash()[:12]}", "computed"
            )
    rows.setdefault("btc_last", rows.get("btc_last", ProvenanceRow("btc_last", "n/a", "missing", "observed")))
    return rows


def run_playbook_from_fixture(
    path: Path,
    *,
    repo_root: Path,
    llm: LlmClient | None = None,
    budget: TokenBudget | None = None,
    force_math_mismatch: bool = False,
    closed_slugs: tuple[str, ...] = (),
    research_root: Path | None = None,
) -> PlaybookRun:
    day = load_frozen_day(path, repo_root=repo_root)
    return run_playbook(
        day,
        repo_root=repo_root,
        llm=llm,
        budget=budget,
        force_math_mismatch=force_math_mismatch,
        closed_slugs=closed_slugs,
        research_root=research_root,
    )


def round_trip_envelopes(envelopes: tuple[DeskEnvelope, ...]) -> tuple[DeskEnvelope, ...]:
    """envelope → row-shaped mapping → envelope for every artifact."""
    out = []
    for env in envelopes:
        row = _Row(env.as_row())
        again = envelope_from_row(row)
        if again.content_hash != env.content_hash:
            raise ValueError(f"envelope round-trip hash drift for {env.desk}")
        out.append(again)
    return tuple(out)


class _Row:
    def __init__(self, data: dict[str, Any]) -> None:
        self.id = data["id"]
        self.desk = data["desk"]
        self.channel = data["channel"]
        self.as_of_knowledge = data["as_of_knowledge"]
        self.as_of_sydney = data["as_of_sydney"]
        self.status = data["status"]
        self.n = data["n"]
        self.completeness_pct = data["completeness_pct"]
        self.regime = data["regime"]
        self.op = data["op"]
        self.universe = data["universe"]
        self.sources = data["sources"]
        self.missing = data["missing"]
        self.cadence = data["cadence"]
        self.content_hash = data["content_hash"]
        self.error_class = data["error_class"]
        self.body_json = data["body_json"]
        self.alert_channel = data.get("alert_channel")
        self.dq_channel = data.get("dq_channel")
