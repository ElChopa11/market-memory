"""Phase 6f prompt-hash decay watch (IMP-031).

Quant product. Not a sixth desk. Detects prompt/config drift via SHA-256.
Mismatch → mesh NOTIFY on desk.quant.alert plus an Ops-owned queue signal.
Does not write the queue, waive gates, auto-disable prompts, or invent
like-for-like scorecard numbers for NOT_COMPARABLE tags.
No LLM. No send.
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.naming import (
    DECAY,
    QUANT,
    desk_display,
    desk_tier,
    require_publishing_desk,
    sleeve_display,
)
from mm_common.time import as_utc, parse_utc
from mm_desks.bus import InMemoryBus, InMemoryEnvelopeStore
from mm_desks.envelope import DeskEnvelope, envelope_from_output, stamp_output
from mm_desks.mesh import CoordMeshWorker
from mm_desks.playbook import round_trip_envelopes
from mm_desks.protocol import DEGRADED, FAILED, OK, DeskArtifact, DeskContext, DeskOutput, completeness_pct
from mm_desks.scorecard import run_scorecard_from_fixture
from mm_quant.decay import (
    ENGINE_VERSION,
    FOOTER,
    ITEM,
    MATCH,
    MISSING,
    NO_AUTO_DISABLE,
    NO_AUTO_WAIVE,
    NO_INVENTED_SCORE,
    decay_watch_payload,
    refuse_forbidden,
)
from mm_research_kit.quant_review.language import assert_language_clean

PRODUCT_SLUG = DECAY
IC_GATES = {
    "skeptic_required": True,
    "risk_required": True,
    "self_approve": False,
    "paper_open": False,
    "principal_override_required_for_block": True,
}


def deterministic_run_id(*, as_of: datetime, fixture_id: str) -> str:
    return sha256_hex(canonical_json({"as_of": as_utc(as_of).isoformat(), "fixture_id": fixture_id, "product": DECAY}))[:16]


@dataclass(frozen=True)
class DecayRun:
    run_id: str
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    status: str
    error_class: str | None
    completeness: float
    content_hash: str
    overall: str
    notes: tuple[str, ...]
    gaps: tuple[str, ...]
    output: DeskOutput
    envelopes: tuple[DeskEnvelope, ...]
    notify_channels: tuple[str, ...]
    notify_events: tuple[dict[str, Any], ...]
    markdown: str
    payload: dict[str, Any]
    llm_calls: int = 0
    engine_version: str = ENGINE_VERSION
    product: str = PRODUCT_SLUG
    alerted: bool = False

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
            "overall": self.overall,
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "engine_version": self.engine_version,
            "product": self.product,
            "desk": QUANT,
            "desk_display": desk_display(QUANT),
            "llm_calls": self.llm_calls,
            "footer": FOOTER,
            "ic_gates": dict(IC_GATES),
            "promote": False,
            "auto_waive": False,
            "auto_disable": False,
            "notify_channels": list(self.notify_channels),
            "alerted": self.alerted,
            "decay_watch": dict(self.payload),
            "queue_signal": dict(self.payload.get("queue_signal") or {}),
            "scorecard_pairs": list(self.payload.get("scorecard_pairs") or []),
            "rows": list(self.payload.get("rows") or []),
        }

    def as_public_dict(self) -> dict[str, Any]:
        signal = self.payload.get("queue_signal") or {}
        return {
            "run_id": self.run_id,
            "status": self.status,
            "error_class": self.error_class,
            "content_hash": self.content_hash,
            "completeness": self.completeness,
            "overall": self.overall,
            "n": int(self.payload.get("n_match") or 0)
            + int(self.payload.get("n_mismatch") or 0)
            + int(self.payload.get("n_missing") or 0)
            + int(self.payload.get("n_unpinned") or 0),
            "n_match": self.payload.get("n_match"),
            "n_mismatch": self.payload.get("n_mismatch"),
            "n_missing": self.payload.get("n_missing"),
            "n_llm_calls": self.llm_calls,
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "desk": QUANT,
            "desk_display": desk_display(QUANT),
            "product": sleeve_display(DECAY),
            "engine_version": self.engine_version,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "send": False,
            "no_send": True,
            "promote": False,
            "ic_gates": dict(IC_GATES),
            "decay_watch_enabled": True,
            "alerted": self.alerted,
            "notify_channels": list(self.notify_channels),
            "queue_signal_kind": signal.get("kind"),
            "queue_signal_auto_write": False,
            "auto_waive": False,
        }


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(text)
    return json.loads(text)


def render_markdown(
    *,
    session_date: str,
    as_of: str,
    content_hash: str,
    status: str,
    completeness: float,
    overall: str,
    rows: tuple[dict[str, Any], ...],
    gaps: tuple[str, ...],
    queue_signal: Mapping[str, Any],
    scorecard_pairs: tuple[dict[str, Any], ...],
) -> str:
    hash_lines = [
        "| path | kind | verdict | expected | observed |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        expected = str(row.get("expected_sha256") or "—")[:12]
        observed = str(row.get("observed_sha256") or "—")[:12]
        hash_lines.append(
            f"| {row.get('path')} | {row.get('kind')} | {row.get('verdict')} | `{expected}` | `{observed}` |"
        )
    pair_lines: list[str] = []
    if scorecard_pairs:
        pair_lines = [
            "",
            "## Attached scorecard pairs (not re-scored)",
            "",
            "| left | right | verdict | comparable | completeness_delta | hash_identity |",
            "|---|---|---|---|---|---|",
        ]
        for row in scorecard_pairs:
            delta = "—" if row.get("completeness_delta") is None else str(row.get("completeness_delta"))
            ident = "—" if row.get("hash_identity") is None else str(row.get("hash_identity"))
            pair_lines.append(
                f"| {row.get('left_id')} | {row.get('right_id')} | {row.get('verdict')} | "
                f"{row.get('comparable')} | {delta} | {ident} |"
            )
        pair_lines.append("")
        pair_lines.append(f"`{NO_INVENTED_SCORE}`")
    gap_block = "\n".join(f"- {g}" for g in (gaps or ("none",)))
    signal_kind = str(queue_signal.get("kind") or "none")
    body = "\n".join(
        [
            f"# Quant prompt-hash decay watch — {session_date}",
            "",
            f"- **desk:** {desk_display(QUANT)} (`{QUANT}`)",
            f"- **product:** {sleeve_display(DECAY)} (`{DECAY}`)",
            f"- **as_of_knowledge:** {as_of}",
            f"- **status:** {status}",
            f"- **overall:** {overall}",
            f"- **completeness:** {completeness}%",
            f"- **content_hash:** `{content_hash}`",
            "- **Not a sixth desk.** Unknown slug `decay` fails closed as a desk.",
            "- Send: no (default). Publisher: Ops. Coord is not the publisher.",
            f"- Queue signal: `{signal_kind}` (does not write the queue).",
            f"- `{NO_AUTO_WAIVE}`. `{NO_AUTO_DISABLE}`.",
            "",
            "## Watched hashes",
            "",
            *hash_lines,
            *pair_lines,
            "",
            "## Gaps",
            "",
            gap_block,
            "",
            FOOTER,
            f"`{ITEM}`",
        ]
    )
    assert_language_clean(body)
    return body


def _status_for(overall: str, *, n_rows: int) -> str:
    if n_rows == 0:
        return DEGRADED
    if overall == MATCH:
        return OK
    return DEGRADED


def run_decay_watch(as_of: datetime, ctx: DeskContext, *, payload: Mapping[str, Any] | None = None) -> DecayRun:
    require_publishing_desk(QUANT)
    root = Path(ctx.repo_root).resolve()
    raw = dict(payload or {})
    fixture_id = str(raw.get("fixture_id") or (ctx.fixture.fixture_id if ctx.fixture else "decay"))
    session_date = str(raw.get("session_date") or as_utc(as_of).date().isoformat())
    watermark = as_of
    if raw.get("as_of_knowledge"):
        watermark = parse_utc(str(raw["as_of_knowledge"]))
    overrides = raw.get("expected_overrides") if isinstance(raw.get("expected_overrides"), dict) else {}
    extra: list[dict[str, str]] = []
    for row in raw.get("extra_files") or []:
        if isinstance(row, dict) and row.get("path"):
            extra.append(
                {
                    "path": str(row["path"]),
                    "expected_sha256": str(row.get("expected_sha256") or ""),
                    "kind": str(row.get("kind") or "config"),
                }
            )
    scorecard_pairs: tuple[Any, ...] = ()
    scorecard_rel = raw.get("scorecard_fixture")
    if scorecard_rel:
        scorecard_path = Path(str(scorecard_rel))
        if not scorecard_path.is_absolute():
            scorecard_path = root / scorecard_path
        scorecard = run_scorecard_from_fixture(scorecard_path, repo_root=root)
        scorecard_pairs = scorecard.pairs
    watch = decay_watch_payload(
        root,
        expected_overrides={str(k): str(v) for k, v in overrides.items()},
        extra_specs=tuple(extra),
        scorecard_pairs=scorecard_pairs,
    )
    rows = tuple(watch.get("rows") or [])
    attached = tuple(watch.get("scorecard_pairs") or [])
    overall = str(watch.get("overall") or MISSING)
    notes: list[str] = [str(watch.get("note") or "decay watch")]
    gaps: list[str] = []
    for row in rows:
        if row.get("verdict") != MATCH:
            gaps.append(f"{row.get('verdict')}:{row.get('path')}")
    if not rows:
        gaps.append("watched_files")
        notes.append("no watched files; degrade, never invent a match")
    if attached:
        notes.append("scorecard pairs attached without re-scoring; NOT_COMPARABLE stays tagged")
    signal = dict(watch.get("queue_signal") or {})
    if signal.get("active"):
        notes.append("NOTIFY/queue signal armed; helper does not write the queue")
    status = _status_for(overall, n_rows=len(rows))
    completeness = completeness_pct(
        int(watch.get("n_match") or 0),
        len(rows) if rows else 1,
    )
    run_id = deterministic_run_id(as_of=watermark, fixture_id=fixture_id)
    body_for_hash = {
        "run_id": run_id,
        "as_of_knowledge": as_utc(watermark).isoformat(),
        "fixture_id": fixture_id,
        "engine_version": ENGINE_VERSION,
        "overall": overall,
        "rows": list(rows),
        "scorecard_pairs": list(attached),
        "status": status,
        "completeness": completeness,
        "queue_signal": {"kind": signal.get("kind"), "active": signal.get("active")},
    }
    digest = sha256_hex(canonical_json(body_for_hash))
    markdown = render_markdown(
        session_date=session_date,
        as_of=as_utc(watermark).isoformat(),
        content_hash=digest,
        status=status,
        completeness=completeness,
        overall=overall,
        rows=rows,
        gaps=tuple(gaps),
        queue_signal=signal,
        scorecard_pairs=attached,
    )
    artifact = DeskArtifact(
        name="decay-watch",
        kind="markdown",
        content=markdown,
        relpath="decay.md",
    )
    output = DeskOutput(
        desk=desk_display(QUANT),
        slug=QUANT,
        tier=desk_tier(QUANT),
        status=status,
        completeness_pct=completeness,
        provenance_ids=tuple(str(row.get("observed_sha256") or "") for row in rows if row.get("observed_sha256")),
        artifacts=(artifact,),
        as_of_knowledge=watermark,
        notes=tuple(notes),
        payload={
            "product": PRODUCT_SLUG,
            "product_display": sleeve_display(DECAY),
            "desk": QUANT,
            "promote": False,
            "llm": False,
            "overall": overall,
            "rows": list(rows),
            "engine_version": ENGINE_VERSION,
            "footer": FOOTER,
            "n_llm_calls": 0,
            "ic_gates": dict(IC_GATES),
            "decay_watch": watch,
            "queue_signal": signal,
            "auto_waive": False,
            "auto_disable": False,
        },
        cadence="daily",
        op="observation",
        universe="mixed",
        n=len(rows),
        missing=tuple(gaps),
        sources=("config/prompts", "config/scorecards", "config/llm"),
    )
    stamped = stamp_output(output, ctx)
    env = envelope_from_output(stamped, repo_root=root)
    envelopes = round_trip_envelopes((env,))
    bus = InMemoryBus()
    worker = CoordMeshWorker(InMemoryEnvelopeStore(), bus, repo_root=root)
    alert = overall != MATCH
    published = worker.publish(env, alert=alert)
    notify_events = tuple({"channel": event.channel, "payload": dict(event.payload)} for event in bus.events)
    return DecayRun(
        run_id=run_id,
        as_of_knowledge=as_utc(watermark),
        fixture_id=fixture_id,
        session_date=session_date,
        status=stamped.status,
        error_class=stamped.error_class,
        completeness=stamped.completeness_pct,
        content_hash=digest,
        overall=overall,
        notes=tuple(notes),
        gaps=tuple(gaps),
        output=stamped,
        envelopes=envelopes,
        notify_channels=published.channels,
        notify_events=notify_events,
        markdown=markdown,
        payload=watch,
        llm_calls=0,
        alerted=alert,
    )


def run_decay_from_fixture(path: Path, *, repo_root: Path) -> DecayRun:
    root = Path(repo_root).resolve()
    raw = _load_json(Path(path))
    if not isinstance(raw, dict):
        raise ValueError("decay fixture must be a mapping")
    as_of = parse_utc(str(raw.get("as_of_knowledge") or "2026-09-18T13:05:00Z"))
    ctx = DeskContext(repo_root=root, fixture=None, send_enabled=False)
    return run_decay_watch(as_of, ctx, payload=raw)


def write_decay_artifacts(run: DecayRun, *, out_root: Path) -> dict[str, str]:
    day_dir = Path(out_root).resolve() / "research" / "decay" / run.session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    json_path = day_dir / "decay.json"
    md_path = day_dir / "decay.md"
    sha_path = day_dir / "decay.sha256"
    json_path.write_text(json.dumps(run.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(run.markdown if run.markdown.endswith("\n") else run.markdown + "\n", encoding="utf-8")
    sha_path.write_text(run.content_hash + "\n", encoding="utf-8")
    return {
        "decay.json": str(json_path),
        "decay.md": str(md_path),
        "decay.sha256": str(sha_path),
    }


__all__ = [
    "DecayRun",
    "NO_INVENTED_SCORE",
    "PRODUCT_SLUG",
    "refuse_forbidden",
    "run_decay_from_fixture",
    "run_decay_watch",
    "write_decay_artifacts",
]
