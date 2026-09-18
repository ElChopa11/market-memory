"""Phase 6e pack scorecard (IMP-030).

Quant product. Not a sixth desk. Deterministic fixture compare. Like-for-like
only. Incomparable artifacts stay tagged. Decay watch (IMP-031 / 6f) records
prompt hashes and alerts Ops on drift. No LLM. No send. No universe promotion.
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
    QUANT,
    SCORECARD,
    desk_display,
    desk_tier,
    require_publishing_desk,
    sleeve_display,
)
from mm_common.time import as_utc, parse_utc
from mm_desks.envelope import DeskEnvelope, envelope_from_output, stamp_output
from mm_desks.playbook import round_trip_envelopes
from mm_desks.protocol import DEGRADED, FAILED, OK, DeskArtifact, DeskContext, DeskOutput, completeness_pct
from mm_quant.decay import decay_watch_payload
from mm_quant.scorecard import (
    ENGINE_VERSION,
    FOOTER,
    COMPARABLE,
    NOT_COMPARABLE,
    PackRecord,
    PairScore,
    load_incomparable_tags,
    load_scorecard_config,
    pack_from_mapping,
    pair_digest,
    score_packs,
    visible_packs,
)
from mm_research_kit.quant_review.language import assert_language_clean

PRODUCT_SLUG = SCORECARD
NO_INVENTED_SCORE = "incomparable_packs_are_not_scored_like_for_like"
IC_GATES = {
    "skeptic_required": True,
    "risk_required": True,
    "self_approve": False,
    "paper_open": False,
    "principal_override_required_for_block": True,
}


def deterministic_run_id(*, as_of: datetime, fixture_id: str) -> str:
    return sha256_hex(canonical_json({"as_of": as_utc(as_of).isoformat(), "fixture_id": fixture_id}))[:16]


@dataclass(frozen=True)
class ScorecardRun:
    run_id: str
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    status: str
    error_class: str | None
    completeness: float
    content_hash: str
    packs: tuple[PackRecord, ...]
    pairs: tuple[PairScore, ...]
    notes: tuple[str, ...]
    gaps: tuple[str, ...]
    output: DeskOutput
    envelopes: tuple[DeskEnvelope, ...]
    markdown: str
    llm_calls: int = 0
    engine_version: str = ENGINE_VERSION
    product: str = PRODUCT_SLUG
    decay_stub: dict[str, Any] | None = None

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
            "packs": [p.canonical() for p in self.packs],
            "pairs": [p.canonical() for p in self.pairs],
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
            "decay_stub": dict(self.decay_stub or {}),
        }

    def as_public_dict(self) -> dict[str, Any]:
        comparable = sum(1 for row in self.pairs if row.verdict == COMPARABLE)
        tagged = sum(1 for row in self.pairs if row.verdict == NOT_COMPARABLE)
        return {
            "run_id": self.run_id,
            "status": self.status,
            "error_class": self.error_class,
            "content_hash": self.content_hash,
            "completeness": self.completeness,
            "n": len(self.packs),
            "n_pairs": len(self.pairs),
            "n_comparable": comparable,
            "n_not_comparable": tagged,
            "n_llm_calls": self.llm_calls,
            "gaps": list(self.gaps),
            "notes": list(self.notes),
            "desk": QUANT,
            "desk_display": desk_display(QUANT),
            "product": sleeve_display(SCORECARD),
            "engine_version": self.engine_version,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "send": False,
            "no_send": True,
            "promote": False,
            "ic_gates": dict(IC_GATES),
            "decay_watch_enabled": bool((self.decay_stub or {}).get("watch_enabled")),
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
    packs: tuple[PackRecord, ...],
    pairs: tuple[PairScore, ...],
    gaps: tuple[str, ...],
    decay_stub: dict[str, Any],
) -> str:
    pack_lines = [
        "| pack_id | product | schedule_anchor | as_of_knowledge | content_hash | tags |",
        "|---|---|---|---|---|---|",
    ]
    for pack in packs:
        tags = ",".join(pack.tags) if pack.tags else "—"
        pack_lines.append(
            f"| {pack.pack_id} | {pack.product} | {pack.schedule_anchor} | "
            f"{pack.as_of_knowledge.isoformat()} | `{pack.content_hash[:12]}` | {tags} |"
        )
    pair_lines = [
        "| left | right | verdict | reasons | completeness_delta | hash_identity |",
        "|---|---|---|---|---|---|",
    ]
    for row in pairs:
        reasons = ",".join(row.reason_codes) if row.reason_codes else "—"
        delta = "—" if row.completeness_delta is None else str(row.completeness_delta)
        ident = "—" if row.hash_identity is None else str(row.hash_identity)
        pair_lines.append(
            f"| {row.left_id} | {row.right_id} | {row.verdict} | {reasons} | {delta} | {ident} |"
        )
    gap_block = "\n".join(f"- {g}" for g in (gaps or ("none",)))
    decay_line = (
        f"Decay watch: watch_enabled={decay_stub.get('watch_enabled')} "
        f"phase={decay_stub.get('phase')} item={decay_stub.get('item')} "
        f"overall={decay_stub.get('overall')} "
        "(prompt hashes versioned; mismatch is a NOTIFY/queue signal)."
    )
    body = "\n".join(
        [
            f"# Quant pack scorecard — {session_date}",
            "",
            f"- **desk:** {desk_display(QUANT)} (`{QUANT}`)",
            f"- **product:** {sleeve_display(SCORECARD)} (`{SCORECARD}`)",
            f"- **as_of_knowledge:** {as_of}",
            f"- **status:** {status}",
            f"- **completeness:** {completeness}%",
            f"- **content_hash:** `{content_hash}`",
            "- **Not a sixth desk.** Unknown slug `scorecard` fails closed as a desk.",
            "- Send: no (default). Publisher: Ops. Coord is not the publisher.",
            "",
            "## Packs (provenance)",
            "",
            *pack_lines,
            "",
            "## Pairwise like-for-like",
            "",
            *pair_lines,
            "",
            "## Gaps",
            "",
            gap_block,
            "",
            decay_line,
            "",
            FOOTER,
            f"`{NO_INVENTED_SCORE}`",
        ]
    )
    assert_language_clean(body)
    return body


def _status_for(*, n_visible: int, n_raw: int, failed: bool) -> str:
    if failed:
        return FAILED
    if n_raw == 0 or n_visible == 0:
        return DEGRADED
    if n_visible < n_raw:
        return DEGRADED
    return OK


def run_scorecard(as_of: datetime, ctx: DeskContext, *, payload: Mapping[str, Any] | None = None) -> ScorecardRun:
    require_publishing_desk(QUANT)
    root = Path(ctx.repo_root).resolve()
    cfg = load_scorecard_config(root)
    desk_cfg = cfg.get("desk") or {}
    if str(desk_cfg.get("desk") or QUANT) != QUANT:
        raise ValueError("scorecard desk must be quant")
    if desk_cfg.get("promote") is True or desk_cfg.get("llm") is True or desk_cfg.get("send") is True:
        raise ValueError("scorecard must keep promote/llm/send false")
    raw = dict(payload or {})
    fixture_id = str(raw.get("fixture_id") or ctx.fixture.fixture_id if ctx.fixture else "scorecard")
    session_date = str(raw.get("session_date") or as_utc(as_of).date().isoformat())
    watermark = as_of
    if raw.get("as_of_knowledge"):
        watermark = parse_utc(str(raw["as_of_knowledge"]))
    raw_packs = raw.get("packs") or []
    packs = tuple(pack_from_mapping(row) for row in raw_packs if isinstance(row, dict))
    tags = load_incomparable_tags(root)
    visible = visible_packs(packs, as_of=watermark)
    hidden = tuple(p.pack_id for p in packs if p not in visible)
    pairs = score_packs(packs, as_of=watermark, tags=tags)
    notes: list[str] = []
    gaps: list[str] = []
    if hidden:
        gaps.extend(f"lookahead:{pid}" for pid in hidden)
        notes.append("packs with as_of_knowledge after the run clock stayed invisible")
    tagged_ids = sorted({tid for pack in visible for tid in pack.tags})
    if tagged_ids:
        notes.append("tagged incomparable: " + ", ".join(tagged_ids))
    if not visible:
        gaps.append("packs")
        notes.append("no visible packs; degrade, never invent a compare")
    decay = decay_watch_payload(root)
    notes.append(str(decay.get("note") or "decay stub"))
    status = _status_for(n_visible=len(visible), n_raw=len(packs), failed=False)
    completeness = completeness_pct(len(visible), len(packs) if packs else 1)
    run_id = deterministic_run_id(as_of=watermark, fixture_id=fixture_id)
    body_for_hash = {
        "run_id": run_id,
        "as_of_knowledge": as_utc(watermark).isoformat(),
        "fixture_id": fixture_id,
        "engine_version": ENGINE_VERSION,
        "packs": [p.canonical() for p in visible],
        "pairs": [p.canonical() for p in pairs],
        "status": status,
        "completeness": completeness,
        "decay_stub": {"watch_enabled": decay.get("watch_enabled"), "item": decay.get("item")},
    }
    digest = sha256_hex(canonical_json(body_for_hash))
    markdown = render_markdown(
        session_date=session_date,
        as_of=as_utc(watermark).isoformat(),
        content_hash=digest,
        status=status,
        completeness=completeness,
        packs=visible,
        pairs=pairs,
        gaps=tuple(gaps),
        decay_stub=decay,
    )
    artifact = DeskArtifact(
        name="pack-scorecard",
        kind="markdown",
        content=markdown,
        relpath="scorecard.md",
    )
    output = DeskOutput(
        desk=desk_display(QUANT),
        slug=QUANT,
        tier=desk_tier(QUANT),
        status=status,
        completeness_pct=completeness,
        provenance_ids=tuple(p.content_hash for p in visible if p.content_hash),
        artifacts=(artifact,),
        as_of_knowledge=watermark,
        notes=tuple(notes),
        payload={
            "product": PRODUCT_SLUG,
            "product_display": sleeve_display(SCORECARD),
            "desk": QUANT,
            "promote": False,
            "llm": False,
            "pairs": [p.canonical() for p in pairs],
            "packs": [p.canonical() for p in visible],
            "engine_version": ENGINE_VERSION,
            "footer": FOOTER,
            "n_llm_calls": 0,
            "ic_gates": dict(IC_GATES),
            "decay_stub": decay,
        },
        cadence="daily",
        op="observation",
        universe="mixed",
        n=len(visible),
        missing=tuple(gaps),
        sources=tuple(sorted({src for p in visible for src in p.sources})),
    )
    stamped = stamp_output(output, ctx)
    env = envelope_from_output(stamped, repo_root=root)
    envelopes = round_trip_envelopes((env,))
    return ScorecardRun(
        run_id=run_id,
        as_of_knowledge=as_utc(watermark),
        fixture_id=fixture_id,
        session_date=session_date,
        status=stamped.status,
        error_class=stamped.error_class,
        completeness=stamped.completeness_pct,
        content_hash=digest,
        packs=visible,
        pairs=pairs,
        notes=tuple(notes),
        gaps=tuple(gaps),
        output=stamped,
        envelopes=envelopes,
        markdown=markdown,
        llm_calls=0,
        decay_stub=decay,
    )


def run_scorecard_from_fixture(path: Path, *, repo_root: Path) -> ScorecardRun:
    root = Path(repo_root).resolve()
    raw = _load_json(Path(path))
    if not isinstance(raw, dict):
        raise ValueError("scorecard fixture must be a mapping")
    as_of = parse_utc(str(raw.get("as_of_knowledge") or "2026-09-18T13:05:00Z"))
    ctx = DeskContext(repo_root=root, fixture=None, send_enabled=False)
    return run_scorecard(as_of, ctx, payload=raw)


def write_scorecard_artifacts(run: ScorecardRun, *, out_root: Path) -> dict[str, str]:
    day_dir = Path(out_root).resolve() / "research" / "scorecards" / run.session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    json_path = day_dir / "scorecard.json"
    md_path = day_dir / "scorecard.md"
    sha_path = day_dir / "scorecard.sha256"
    json_path.write_text(json.dumps(run.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(run.markdown if run.markdown.endswith("\n") else run.markdown + "\n", encoding="utf-8")
    sha_path.write_text(run.content_hash + "\n", encoding="utf-8")
    return {
        "scorecard.json": str(json_path),
        "scorecard.md": str(md_path),
        "scorecard.sha256": str(sha_path),
    }
