"""Phase 1 unconditional base-rate artifacts (IMP-039).

Quant product. Not a sixth desk. Deterministic fixture compute. Paper only.
No sizing. No scan-gate. No C-001/002/003 study results.
# Boundary comment: packages here must not import mm_execution (statement form is gated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.naming import QUANT, desk_display, desk_tier, require_publishing_desk, sleeve_display
from mm_common.time import as_utc, parse_utc
from mm_desks.envelope import DeskEnvelope, envelope_from_output, stamp_output
from mm_desks.playbook import round_trip_envelopes
from mm_desks.protocol import DEGRADED, FAILED, OK, DeskArtifact, DeskContext, DeskOutput, completeness_pct
from mm_quant.base_rates import (
    ENGINE_VERSION,
    EVENT_CLASSES,
    FOOTER,
    BaseRateSnapshot,
    load_base_rate_config,
    snapshot_from_mapping,
)
from mm_quant.language import assert_language_clean

PRODUCT_SLUG = "base_rate"
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
class BaseRateRun:
    run_id: str
    as_of_knowledge: datetime
    fixture_id: str
    session_date: str
    status: str
    error_class: str | None
    completeness: float
    content_hash: str
    params_hash: str
    snapshot: BaseRateSnapshot
    notes: tuple[str, ...]
    gaps: tuple[str, ...]
    output: DeskOutput
    envelopes: tuple[DeskEnvelope, ...]
    markdown: str
    llm_calls: int = 0
    engine_version: str = ENGINE_VERSION

    def canonical(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "as_of_knowledge": as_utc(self.as_of_knowledge).isoformat(),
            "ingested_at": as_utc(self.snapshot.ingested_at).isoformat(),
            "fixture_id": self.fixture_id,
            "session_date": self.session_date,
            "status": self.status,
            "error_class": self.error_class,
            "completeness": self.completeness,
            "content_hash": self.content_hash,
            "params_hash": self.params_hash,
            "desk": QUANT,
            "product": PRODUCT_SLUG,
            "product_display": sleeve_display(PRODUCT_SLUG),
            "promote": False,
            "sizing": False,
            "scan_gate": False,
            "paper_only": True,
            "n_llm_calls": self.llm_calls,
            "engine_version": self.engine_version,
            "snapshot": self.snapshot.canonical(),
            "memory_rows": [self.snapshot.memory_row(rate) for rate in self.snapshot.rates],
            "notes": list(self.notes),
            "gaps": list(self.gaps),
            "ic_gates": dict(IC_GATES),
            "footer": FOOTER,
        }

    def as_public_dict(self) -> dict[str, Any]:
        return self.canonical()


def render_markdown(run: "BaseRateRun") -> str:
    rate_lines = []
    for rate in run.snapshot.rates:
        claim = "claimed" if rate.claimed else "no claim"
        hit = "n/a" if rate.hit_rate is None else f"{rate.hit_rate:.4f}"
        med = "n/a" if rate.median_fwd_return is None else f"{rate.median_fwd_return:.6f}"
        mean_r = "n/a" if rate.mean_r_after_cost is None else f"{rate.mean_r_after_cost:.6f}"
        rate_lines.append(
            f"- **{rate.event_class}** ({claim}) n={rate.n} n_min={rate.n_min} "
            f"n_censored={rate.n_censored} hit_rate={hit} median_signed_fwd={med} "
            f"mean_R_after_cost={mean_r} → cites {rate.cites_candidate}. {rate.reason}"
        )
    cite_lines = [
        "- C-001 (supply/demand zone) cites `zone_boundary_touch` as the unconditional range-boundary class. Extra filter: X·ATR departure confirm.",
        "- C-002 (triple RSI MR) cites `dip_touch` as the unconditional SMA20-uptrend dip class. Extra filter: three RSIs ≤ Z.",
        "- C-003 (second-entry pullback) cites `pullback_ema_touch` as the first-entry class. Extra filter: second pullback + trigger.",
        "- A later study records `delta vs event_base_rate.params_hash` + `as_of_knowledge`. It does not recompute these rates.",
    ]
    gap_block = "- none" if not run.gaps else "\n".join(f"- {g}" for g in run.gaps)
    inst = ", ".join(run.snapshot.instrument_set) or "(none visible)"
    body = "\n".join(
        [
            f"# Unconditional event-class base rates ({run.session_date})",
            "",
            f"- **Desk:** {desk_display(QUANT)} · sleeve `{PRODUCT_SLUG}`",
            f"- **as_of_knowledge:** {as_utc(run.as_of_knowledge).isoformat()}",
            f"- **ingested_at:** {as_utc(run.snapshot.ingested_at).isoformat()} (lockstep)",
            f"- **params_hash:** `{run.params_hash}`",
            f"- **content_hash:** `{run.content_hash}`",
            f"- **fixture_id:** {run.fixture_id}",
            f"- **instrument set:** {inst}",
            f"- **window:** {run.snapshot.window.get('start')} .. {run.snapshot.window.get('end')} ({run.snapshot.window.get('bar')})",
            f"- **cost model:** {run.snapshot.cost_model.get('formula')} (clip is not a size)",
            f"- **survivorship:** {run.snapshot.survivorship_tag}",
            f"- **status:** {run.status}",
            "",
            "## Rates",
            "",
            *rate_lines,
            "",
            "## How C-001 / C-002 / C-003 cite this pack",
            "",
            *cite_lines,
            "",
            "## Gaps",
            "",
            gap_block,
            "",
            FOOTER,
        ]
    )
    assert_language_clean(body)
    return body


def _status_for(*, n_instruments: int, n_classes: int, failed: bool) -> str:
    if failed:
        return FAILED
    if n_instruments == 0:
        return DEGRADED
    if n_classes < len(EVENT_CLASSES):
        return DEGRADED
    return OK


def run_base_rates(as_of: datetime, ctx: DeskContext, *, payload: Mapping[str, Any] | None = None) -> BaseRateRun:
    require_publishing_desk(QUANT)
    root = Path(ctx.repo_root).resolve()
    cfg = load_base_rate_config(root)
    if str(cfg.get("desk") or QUANT) != QUANT:
        raise ValueError("base_rate desk must be quant")
    if cfg.get("promote") is True or cfg.get("llm") is True or cfg.get("send") is True or cfg.get("sizing") is True:
        raise ValueError("base_rate must keep promote/llm/send/sizing false")
    raw = dict(payload or {})
    fixture_id = str(raw.get("fixture_id") or (ctx.fixture.fixture_id if ctx.fixture else "base-rate"))
    watermark = as_of
    if raw.get("as_of_knowledge"):
        watermark = parse_utc(str(raw["as_of_knowledge"]))
    snapshot = snapshot_from_mapping(raw, config=cfg, watermark=watermark)
    session_date = str(raw.get("session_date") or as_utc(watermark).date().isoformat())
    notes = list(snapshot.notes)
    gaps: list[str] = []
    if not snapshot.instrument_set:
        gaps.append("bars")
    unclaimed = [r.event_class for r in snapshot.rates if not r.claimed]
    if unclaimed:
        notes.append("no claim on: " + ", ".join(unclaimed))
    status = _status_for(
        n_instruments=len(snapshot.instrument_set),
        n_classes=len(snapshot.rates),
        failed=False,
    )
    completeness = completeness_pct(len(snapshot.rates), len(EVENT_CLASSES))
    run_id = deterministic_run_id(as_of=watermark, fixture_id=fixture_id)
    markdown_placeholder = ""
    run = BaseRateRun(
        run_id=run_id,
        as_of_knowledge=as_utc(watermark),
        fixture_id=fixture_id,
        session_date=session_date,
        status=status,
        error_class=None,
        completeness=completeness,
        content_hash=snapshot.content_hash,
        params_hash=snapshot.params_hash,
        snapshot=snapshot,
        notes=tuple(notes),
        gaps=tuple(gaps),
        output=DeskOutput(
            desk=desk_display(QUANT),
            slug=QUANT,
            tier=desk_tier(QUANT),
            status=status,
            completeness_pct=completeness,
            provenance_ids=(snapshot.params_hash, snapshot.content_hash),
            artifacts=(),
            as_of_knowledge=watermark,
            notes=tuple(notes),
            payload={},
        ),
        envelopes=(),
        markdown=markdown_placeholder,
    )
    markdown = render_markdown(run)
    artifact = DeskArtifact(
        name="unconditional-base-rates",
        kind="markdown",
        content=markdown,
        relpath="unconditional.md",
    )
    output = DeskOutput(
        desk=desk_display(QUANT),
        slug=QUANT,
        tier=desk_tier(QUANT),
        status=status,
        completeness_pct=completeness,
        provenance_ids=(snapshot.params_hash, snapshot.content_hash),
        artifacts=(artifact,),
        as_of_knowledge=watermark,
        notes=tuple(notes),
        payload={
            "product": PRODUCT_SLUG,
            "product_display": sleeve_display(PRODUCT_SLUG),
            "desk": QUANT,
            "promote": False,
            "llm": False,
            "sizing": False,
            "scan_gate": False,
            "params_hash": snapshot.params_hash,
            "content_hash": snapshot.content_hash,
            "memory_rows": [snapshot.memory_row(rate) for rate in snapshot.rates],
            "engine_version": ENGINE_VERSION,
            "footer": FOOTER,
            "n_llm_calls": 0,
            "ic_gates": dict(IC_GATES),
        },
        cadence="study",
        op="observation",
        universe="locked_membership_primary",
        n=sum(r.n for r in snapshot.rates),
        missing=tuple(gaps),
        sources=("fixture_ohlcv",),
    )
    stamped = stamp_output(output, ctx)
    env = envelope_from_output(stamped, repo_root=root)
    envelopes = round_trip_envelopes((env,))
    return BaseRateRun(
        run_id=run_id,
        as_of_knowledge=as_utc(watermark),
        fixture_id=fixture_id,
        session_date=session_date,
        status=stamped.status,
        error_class=stamped.error_class,
        completeness=stamped.completeness_pct,
        content_hash=snapshot.content_hash,
        params_hash=snapshot.params_hash,
        snapshot=snapshot,
        notes=tuple(notes),
        gaps=tuple(gaps),
        output=stamped,
        envelopes=envelopes,
        markdown=markdown,
        llm_calls=0,
    )


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    return data


def run_base_rates_from_fixture(path: Path, *, repo_root: Path) -> BaseRateRun:
    root = Path(repo_root).resolve()
    raw = _load_json(Path(path))
    as_of = parse_utc(str(raw.get("as_of_knowledge") or "2026-09-18T00:00:00Z"))
    ctx = DeskContext(repo_root=root, fixture=None, send_enabled=False)
    return run_base_rates(as_of, ctx, payload=raw)


def write_base_rate_artifacts(run: BaseRateRun, *, out_root: Path) -> dict[str, str]:
    day_dir = Path(out_root).resolve() / "research" / "quant" / "base-rates" / run.session_date
    day_dir.mkdir(parents=True, exist_ok=True)
    json_path = day_dir / "unconditional.json"
    md_path = day_dir / "unconditional.md"
    sha_path = day_dir / "unconditional.sha256"
    json_path.write_text(json.dumps(run.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(run.markdown if run.markdown.endswith("\n") else run.markdown + "\n", encoding="utf-8")
    sha_path.write_text(run.content_hash + "\n", encoding="utf-8")
    return {
        "unconditional.json": str(json_path),
        "unconditional.md": str(md_path),
        "unconditional.sha256": str(sha_path),
    }
