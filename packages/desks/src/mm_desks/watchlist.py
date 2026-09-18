"""Phase 6c-4 watchlist monitor + daily scan (IMP-020).

Research product over the Principal-locked universe (in_universe ∪ watch_only).
Deterministic fixture scan. No Quant verdicts. No trade calls. No LLM. No send.
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.naming import (
    RESEARCH,
    WATCHLIST,
    artifact_display,
    desk_display,
    desk_tier,
    require_publishing_desk,
    sleeve_display,
)
from mm_common.time import as_utc
from mm_desks.envelope import DeskEnvelope, envelope_from_output, stamp_output
from mm_desks.fixture import load_frozen_day
from mm_desks.models import FrozenDay, TapeRow
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
from mm_desks.universe import (
    MEMBERSHIP_DEFERRED,
    MEMBERSHIP_IN_UNIVERSE,
    MEMBERSHIP_WATCH_ONLY,
    MembershipName,
    deferred_must_cut,
    locked_watchlist,
)
from mm_research_kit.quant_review.language import assert_language_clean

ENGINE_VERSION = "imp-020.1"
PRODUCT_SLUG = WATCHLIST
WATCHLIST_CFG_REL = Path("config/desks/watchlist.yaml")
MONITOR_STATES = ("COVERED", "PARTIAL", "UNAVAILABLE")
FRESHNESS_VALUES = ("fresh", "stale", "partial", "unavailable")
FOOTER = (
    "Not a call. Not a Quant verdict. Locked membership is not promotion. "
    "deferred_must_cut names stay archived. Missing tape stays unavailable."
)

_FRESHNESS_RANK = {"fresh": 0, "stale": 1, "partial": 2, "unavailable": 3}


@dataclass(frozen=True)
class WatchlistRow:
    instrument: str
    membership: str
    sleeve: str
    sleeve_display: str
    asset_class: str
    monitor_state: str
    freshness: str
    metrics: tuple[dict[str, Any], ...]
    playbook_setup: bool
    notes: str
    provenance_ids: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        first = self.metrics[0] if self.metrics else {}
        usable = next((item for item in self.metrics if item.get("value") not in (None, "", "unavailable")), None)
        return {
            "instrument": self.instrument,
            "membership": self.membership,
            "sleeve": self.sleeve,
            "sleeve_display": self.sleeve_display,
            "asset_class": self.asset_class,
            "monitor_state": self.monitor_state,
            "freshness": self.freshness,
            "metrics": list(self.metrics),
            "playbook_setup": self.playbook_setup,
            "notes": self.notes,
            "provenance_ids": list(self.provenance_ids),
            "value": None if usable is None else usable.get("value"),
            "source": str((usable or first).get("source") or ""),
            "observation_id": None if usable is None else usable.get("observation_id"),
        }


@dataclass(frozen=True)
class WatchlistRun:
    run_id: str
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    status: str
    error_class: str | None
    completeness: float
    content_hash: str
    rows: tuple[WatchlistRow, ...]
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
        return {
            "run_id": self.run_id,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "fixture_id": self.fixture_id,
            "session_date": self.session_date,
            "status": self.status,
            "error_class": self.error_class,
            "completeness": self.completeness,
            "content_hash": self.content_hash,
            "rows": [row.canonical() for row in self.rows],
            "notes": list(self.notes),
            "gaps": list(self.gaps),
            "engine_version": self.engine_version,
            "product": self.product,
            "desk": RESEARCH,
            "desk_display": desk_display(RESEARCH),
            "llm_calls": self.llm_calls,
            "footer": FOOTER,
        }

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "error_class": self.error_class,
            "content_hash": self.content_hash,
            "completeness": self.completeness,
            "n": len(self.rows),
            "n_covered": sum(1 for row in self.rows if row.monitor_state == "COVERED"),
            "n_partial": sum(1 for row in self.rows if row.monitor_state == "PARTIAL"),
            "n_unavailable": sum(1 for row in self.rows if row.monitor_state == "UNAVAILABLE"),
            "n_llm_calls": self.llm_calls,
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "desk": RESEARCH,
            "desk_display": desk_display(RESEARCH),
            "product": sleeve_display(WATCHLIST),
            "engine_version": self.engine_version,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "send": False,
            "no_send": True,
        }


def load_watchlist_spec(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root) / WATCHLIST_CFG_REL
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def deterministic_run_id(*, as_of: datetime, fixture_id: str) -> str:
    return sha256_hex(
        canonical_json(
            {
                "as_of": as_utc(as_of).isoformat(),
                "fixture_id": fixture_id,
                "engine": ENGINE_VERSION,
                "product": PRODUCT_SLUG,
            }
        )
    )[:26]


def _playbook_instruments(day: FrozenDay) -> set[str]:
    block = day.raw.get("playbook") if isinstance(day.raw.get("playbook"), dict) else {}
    ideas = block.get("ideas") or []
    names: set[str] = set()
    for row in ideas:
        if isinstance(row, dict) and row.get("instrument"):
            names.add(str(row["instrument"]).upper())
    return names


def _worst_freshness(values: tuple[str, ...]) -> str:
    if not values:
        return "unavailable"
    return max(values, key=lambda item: _FRESHNESS_RANK.get(item, 3))


def _metrics_for(instrument: str, tape: tuple[TapeRow, ...]) -> tuple[dict[str, Any], ...]:
    out: list[dict[str, Any]] = []
    for row in tape:
        if row.instrument != instrument:
            continue
        out.append(
            {
                "metric": row.metric,
                "value": row.value,
                "source": row.source,
                "freshness": row.freshness if row.freshness in FRESHNESS_VALUES else "unavailable",
                "observation_id": row.observation_id,
            }
        )
    return tuple(out)


def _scan_name(
    name: MembershipName,
    *,
    tape: tuple[TapeRow, ...],
    playbook_names: set[str],
    deferred: set[str],
) -> WatchlistRow:
    if name.instrument in deferred:
        raise ValueError(f"deferred_must_cut name {name.instrument} is not on the locked watchlist")
    metrics = _metrics_for(name.instrument, tape)
    usable = tuple(row for row in metrics if row.get("value") not in (None, "", "unavailable"))
    freshness_vals = tuple(str(row.get("freshness") or "unavailable") for row in usable) or ("unavailable",)
    freshness = _worst_freshness(freshness_vals)
    if not metrics:
        state = "UNAVAILABLE"
        notes = f"{name.instrument}: tape unavailable; not invented"
        freshness = "unavailable"
    elif not usable:
        state = "UNAVAILABLE"
        notes = f"{name.instrument}: tape listed without values; not invented"
        freshness = "unavailable"
    elif len(usable) < len(metrics) or freshness in {"partial", "stale"}:
        state = "PARTIAL" if len(usable) < len(metrics) or freshness == "partial" else "COVERED"
        notes = ""
        if freshness == "stale" and state == "COVERED":
            notes = f"{name.instrument}: stale tape; still covered"
    else:
        state = "COVERED"
        notes = ""
    playbook_setup = name.instrument in playbook_names
    if playbook_setup:
        extra = f"PLAYBOOK {artifact_display('EDGE_SCAN')} setup present (not a call; math stays on lab playbook run)"
        notes = f"{notes}; {extra}".strip("; ")
    provenance = tuple(str(row["observation_id"]) for row in metrics if row.get("observation_id"))
    return WatchlistRow(
        instrument=name.instrument,
        membership=name.membership,
        sleeve=name.sleeve,
        sleeve_display=sleeve_display(name.sleeve),
        asset_class=name.asset_class,
        monitor_state=state,
        freshness=freshness,
        metrics=metrics,
        playbook_setup=playbook_setup,
        notes=notes,
        provenance_ids=provenance,
    )


def render_markdown(run_meta: dict[str, Any], rows: tuple[WatchlistRow, ...]) -> str:
    product = sleeve_display(WATCHLIST)
    desk = desk_display(RESEARCH)
    lines = [
        f"# {product} — {run_meta['session_date']}",
        "",
        f"- **Desk / tier:** {desk} / {desk_tier(RESEARCH)}",
        f"- **Product:** {product} (`{WATCHLIST}`)",
        f"- **Knowledge watermark (as_of_knowledge):** {run_meta['as_of_knowledge']}",
        f"- **Universe:** locked `in_universe` ∪ `watch_only` (config/universe.yaml {run_meta['universe_version']})",
        f"- **Engine:** {ENGINE_VERSION}",
        f"- **content_hash:** `{run_meta['content_hash']}`",
        f"- **Status:** {run_meta['status']}",
        f"- **Completeness:** {run_meta['completeness']}% of locked names with tape",
        "- **LLM:** none on this fixture path",
        "- **Send:** no",
        "",
        FOOTER,
        "",
        "| instrument | membership | sleeve | monitor_state | freshness | metrics | observation_ids | playbook_setup |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        metric_bits = []
        for item in row.metrics:
            value = item["value"] if item["value"] is not None else "unavailable"
            metric_bits.append(f"{item['metric']}={value} ({item['freshness']})")
        metrics = "; ".join(metric_bits) if metric_bits else "unavailable"
        oids = ", ".join(row.provenance_ids) if row.provenance_ids else "—"
        setup = "yes" if row.playbook_setup else "no"
        lines.append(
            f"| {row.instrument} | {row.membership} | {row.sleeve} | {row.monitor_state} | "
            f"{row.freshness} | {metrics} | {oids} | {setup} |"
        )
    lines.extend(
        [
            "",
            "## Gaps",
            "",
        ]
    )
    gaps = [row.notes for row in rows if row.notes] or ["none"]
    for gap in gaps:
        lines.append(f"- {gap}")
    lines.extend(["", "## Footer", "", FOOTER, ""])
    text = "\n".join(lines)
    assert_language_clean(text)
    return text


def _status_for(rows: tuple[WatchlistRow, ...], *, failed: bool) -> str:
    if failed:
        return FAILED
    if not rows:
        return FAILED
    if all(row.monitor_state == "UNAVAILABLE" for row in rows):
        return DEGRADED
    if any(row.monitor_state != "COVERED" for row in rows):
        return DEGRADED
    return OK


def run_watchlist(
    as_of: datetime,
    ctx: DeskContext,
    *,
    day: FrozenDay | None = None,
) -> WatchlistRun:
    require_publishing_desk(RESEARCH)
    sleeve_display(WATCHLIST)
    spec = load_watchlist_spec(ctx.repo_root)
    frozen = day if day is not None else ctx.fixture
    as_of = as_utc(as_of)
    names = locked_watchlist(ctx.repo_root)
    deferred = set(deferred_must_cut(ctx.repo_root))
    if any(row.instrument in deferred for row in names):
        raise ValueError("locked watchlist leaked a deferred_must_cut name")
    if spec.get("promote"):
        raise ValueError("watchlist config must not enable promotion")
    if spec.get("llm"):
        raise ValueError("watchlist config must not enable LLM")
    include = tuple(spec.get("include") or (MEMBERSHIP_IN_UNIVERSE, MEMBERSHIP_WATCH_ONLY))
    if MEMBERSHIP_DEFERRED in include:
        raise ValueError("watchlist must not include deferred_must_cut")
    playbook_names = _playbook_instruments(frozen)
    rows = tuple(
        _scan_name(name, tape=frozen.tape, playbook_names=playbook_names, deferred=deferred) for name in names
    )
    covered = sum(1 for row in rows if row.monitor_state in {"COVERED", "PARTIAL"})
    completeness = completeness_pct(covered, len(rows))
    notes = tuple(row.notes for row in rows if row.notes)
    gaps = tuple(row.instrument for row in rows if row.monitor_state == "UNAVAILABLE")
    status = _status_for(rows, failed=False)
    run_id = deterministic_run_id(as_of=as_of, fixture_id=frozen.fixture_id)
    universe_version = str((_load_universe_version(ctx.repo_root)))
    payload = {
        "product": PRODUCT_SLUG,
        "product_display": sleeve_display(WATCHLIST),
        "desk": RESEARCH,
        "include": list(include),
        "exclude": [MEMBERSHIP_DEFERRED],
        "promote": False,
        "llm": False,
        "universe_version": universe_version,
        "instruments": [row.instrument for row in rows],
        "membership": {row.instrument: row.membership for row in rows},
        "rows": [row.canonical() for row in rows],
        "tape": [row.canonical() for row in rows],
        "playbook_setups": sorted(name for name in playbook_names if name in {row.instrument for row in rows}),
        "engine_version": ENGINE_VERSION,
        "footer": FOOTER,
        "n_llm_calls": 0,
    }
    body_for_hash = {
        "run_id": run_id,
        "as_of_knowledge": as_of.isoformat(),
        "fixture_id": frozen.fixture_id,
        "engine_version": ENGINE_VERSION,
        "rows": [row.canonical() for row in rows],
        "status": status,
        "completeness": completeness,
    }
    digest = sha256_hex(canonical_json(body_for_hash))
    markdown = render_markdown(
        {
            "session_date": frozen.session_date,
            "as_of_knowledge": as_of.isoformat(),
            "universe_version": universe_version,
            "content_hash": digest,
            "status": status,
            "completeness": completeness,
        },
        rows,
    )
    artifact = DeskArtifact(
        name="watchlist-scan",
        kind="markdown",
        content=markdown,
        relpath="watchlist.md",
    )
    provenance = tuple(oid for row in rows for oid in row.provenance_ids)
    output = DeskOutput(
        desk=desk_display(RESEARCH),
        slug=RESEARCH,
        tier=desk_tier(RESEARCH),
        status=status,
        completeness_pct=completeness,
        provenance_ids=provenance,
        artifacts=(artifact,),
        as_of_knowledge=as_of,
        notes=notes,
        payload=payload,
        cadence="daily",
        op="observation",
        universe="mixed",
        n=len(rows),
        missing=gaps,
        sources=tuple(sorted({str(item.get("source")) for row in rows for item in row.metrics if item.get("source")})),
    )
    stamped = stamp_output(output, ctx)
    env = envelope_from_output(stamped, repo_root=ctx.repo_root)
    envelopes = round_trip_envelopes((env,))
    return WatchlistRun(
        run_id=run_id,
        as_of_knowledge=as_of,
        fixture_id=frozen.fixture_id,
        session_date=frozen.session_date,
        status=stamped.status,
        error_class=stamped.error_class,
        completeness=stamped.completeness_pct,
        content_hash=digest,
        rows=rows,
        notes=notes,
        gaps=gaps,
        output=stamped,
        envelopes=envelopes,
        markdown=markdown,
        llm_calls=0,
    )


def _load_universe_version(repo_root: Path) -> str:
    path = Path(repo_root) / "config" / "universe.yaml"
    if not path.is_file():
        return "unknown"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("version"):
        return str(data["version"])
    return "unknown"


def run_watchlist_from_fixture(path: Path, *, repo_root: Path) -> WatchlistRun:
    root = Path(repo_root).resolve()
    day = load_frozen_day(Path(path), repo_root=root)
    ctx = DeskContext(repo_root=root, fixture=day, send_enabled=False)
    return run_watchlist(day.as_of_knowledge, ctx, day=day)


def write_watchlist_artifacts(run: WatchlistRun, *, out_root: Path) -> dict[str, str]:
    day_dir = Path(out_root).resolve() / "research" / "watchlist" / run.session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    json_path = day_dir / "watchlist.json"
    md_path = day_dir / "watchlist.md"
    sha_path = day_dir / "watchlist.sha256"
    json_path.write_text(json.dumps(run.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(run.markdown if run.markdown.endswith("\n") else run.markdown + "\n", encoding="utf-8")
    sha_path.write_text(run.content_hash + "\n", encoding="utf-8")
    return {
        "watchlist.json": str(json_path),
        "watchlist.md": str(md_path),
        "watchlist.sha256": str(sha_path),
    }
