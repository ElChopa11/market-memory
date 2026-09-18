"""Phase 6 desk envelope: Principal header + content_hash idempotency.

Header fields: desk, as_of (UTC + Sydney), status, n, completeness, regime
(from the Macro desk when Phase 6b succeeds; otherwise the 6a `unset`
placeholder), op=paper|observation, universe, sources/missing.
Body is a passthrough of the Phase 5d DeskOutput canonical payload.
``envelope_id`` is not hashed — re-run same as_of → identical content_hash
unless observations change.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.ids import new_ulid
from mm_common.time import as_utc, in_ops_tz, parse_utc
from mm_desks.cadence import (
    OP_VALUES,
    REGIME_PLACEHOLDER,
    cadence_for,
    desk_display,
    desk_tier,
    load_cadence,
)
from mm_desks.protocol import FAILED, DeskArtifact, DeskContext, DeskOutput
from mm_desks.universe import membership_of

ERROR_CLASS_MISSING = "desk_missing"
ERROR_CLASS_KILLED = "desk_killed"
ERROR_CLASS_ERROR = "desk_error"
ERROR_CLASS_TIMEOUT = "desk_timeout"
ERROR_CLASS_VALUES = (
    ERROR_CLASS_MISSING,
    ERROR_CLASS_KILLED,
    ERROR_CLASS_ERROR,
    ERROR_CLASS_TIMEOUT,
)

NOTIFY_MAX_BYTES = 8000


def infer_n(output: DeskOutput) -> int:
    payload = output.payload or {}
    if output.slug == "intel":
        return len(payload.get("feeds") or [])
    if output.slug in {"crypto", "equities"}:
        return len(payload.get("tape") or [])
    if output.slug == "quant":
        return len(payload.get("cards") or [])
    if output.slug == "flow":
        return len(payload.get("snapshots") or payload.get("instruments") or [])
    if output.slug == "macro":
        return len(payload.get("series") or [])
    if output.slug == "coord":
        prior = payload.get("desks") or payload.get("assembled_desks")
        if isinstance(prior, list):
            return len(prior)
        return int(output.n or 0) or len(output.artifacts)
    if output.n:
        return int(output.n)
    return len(output.artifacts)


def infer_sources_missing(output: DeskOutput) -> tuple[tuple[str, ...], tuple[str, ...]]:
    payload = output.payload or {}
    sources: list[str] = []
    missing: list[str] = []
    for feed in payload.get("feeds") or []:
        sid = str(feed.get("source_id") or "")
        if not sid:
            continue
        if feed.get("status") == "ok":
            sources.append(sid)
        else:
            missing.append(sid)
    for row in payload.get("tape") or []:
        src = str(row.get("source") or "")
        value = row.get("value")
        freshness = str(row.get("freshness") or "")
        unavailable = value in (None, "", "unavailable") or freshness == "unavailable"
        if unavailable:
            if src:
                missing.append(src)
        elif src:
            sources.append(src)
    for item in payload.get("required_missing") or []:
        missing.append(str(item))
    if output.missing:
        missing.extend(output.missing)
    if output.sources:
        sources.extend(output.sources)
    return tuple(sorted(set(sources))), tuple(sorted(set(missing)))


def infer_universe(output: DeskOutput, ctx: DeskContext | None) -> str:
    if output.universe and output.universe != "mixed":
        return output.universe
    if output.slug in {"intel", "coord", "quant", "skeptic", "risk", "flow", "macro"}:
        return "mixed"
    if ctx is not None and ctx.thesis is not None:
        return membership_of(ctx.thesis.instrument, ctx.repo_root)
    return "mixed"


def resolved_regime(output: DeskOutput, ctx: DeskContext | None) -> str:
    """Use a successful macro tag; never overwrite a real tag with `unset`."""
    if output.regime and output.regime not in {REGIME_PLACEHOLDER, "", "unavailable"}:
        return output.regime
    if ctx is None:
        return output.regime or REGIME_PLACEHOLDER
    macro = ctx.prior.get("macro")
    if macro is not None:
        tag = str((macro.payload or {}).get("regime_tag") or macro.regime or "")
        if tag and tag not in {REGIME_PLACEHOLDER, "unavailable"}:
            return tag
    return load_cadence(ctx.repo_root).regime_placeholder or REGIME_PLACEHOLDER


def apply_regime_to_context(ctx: DeskContext) -> None:
    """Copy a successful macro regime tag onto every desk output in ``ctx.prior``."""
    macro = ctx.prior.get("macro")
    if macro is None:
        return
    tag = str((macro.payload or {}).get("regime_tag") or macro.regime or "")
    if not tag or tag in {REGIME_PLACEHOLDER, "unavailable"}:
        return
    for slug, output in list(ctx.prior.items()):
        if output.regime != tag:
            ctx.prior[slug] = replace(output, regime=tag)


def stamp_output(output: DeskOutput, ctx: DeskContext) -> DeskOutput:
    """Fill cadence / header metadata without changing observation-derived status."""
    spec = cadence_for(output.slug, ctx.repo_root)
    sources, missing = infer_sources_missing(output)
    regime = resolved_regime(output, ctx)
    return replace(
        output,
        cadence=spec.cadence,
        op=spec.op if spec.op in OP_VALUES else output.op,
        regime=regime,
        universe=infer_universe(output, ctx),
        sources=sources,
        missing=missing,
        n=infer_n(output),
    )


def failed_desk_output(
    slug: str,
    as_of: datetime,
    *,
    error_class: str,
    repo_root: Any | None = None,
    notes: tuple[str, ...] = (),
) -> DeskOutput:
    if error_class not in ERROR_CLASS_VALUES:
        raise ValueError(f"unknown error_class {error_class!r}")
    spec = cadence_for(slug, repo_root)
    watermark = as_utc(as_of)
    note = notes or (f"{error_class}: desk {slug} did not publish",)
    return DeskOutput(
        desk=desk_display(slug),
        slug=slug,
        tier=desk_tier(slug),
        status=FAILED,
        completeness_pct=0.0,
        provenance_ids=(),
        artifacts=(),
        as_of_knowledge=watermark,
        notes=note,
        payload={"error_class": error_class, "degrade_never_invent": True},
        cadence=spec.cadence,
        op=spec.op,
        regime=REGIME_PLACEHOLDER,
        error_class=error_class,
        universe="mixed",
        sources=(),
        missing=(slug,),
        n=0,
    )


def output_from_canonical(data: dict[str, Any]) -> DeskOutput:
    artifacts = tuple(
        DeskArtifact(
            name=str(row["name"]),
            kind=str(row["kind"]),
            content=str(row.get("content") or ""),
            relpath=row.get("relpath"),
        )
        for row in (data.get("artifacts") or [])
    )
    as_of = data.get("as_of_knowledge")
    watermark = as_of if isinstance(as_of, datetime) else parse_utc(str(as_of))
    return DeskOutput(
        desk=str(data["desk"]),
        slug=str(data["slug"]),
        tier=str(data["tier"]),
        status=str(data["status"]),
        completeness_pct=float(data.get("completeness_pct") or 0),
        provenance_ids=tuple(data.get("provenance_ids") or ()),
        artifacts=artifacts,
        as_of_knowledge=watermark,
        notes=tuple(data.get("notes") or ()),
        payload=dict(data.get("payload") or {}),
        cadence=str(data.get("cadence") or "daily"),
        op=str(data.get("op") or "observation"),
        regime=str(data.get("regime") or REGIME_PLACEHOLDER),
        error_class=data.get("error_class"),
        universe=str(data.get("universe") or "mixed"),
        sources=tuple(data.get("sources") or ()),
        missing=tuple(data.get("missing") or ()),
        n=int(data["n"]) if data.get("n") is not None else None,
    )


@dataclass(frozen=True)
class DeskEnvelope:
    """Durable mesh envelope. Persist this; NOTIFY only ids/keys."""

    desk: str
    as_of_utc: datetime
    as_of_sydney: str
    status: str
    n: int
    completeness: float
    regime: str
    op: str
    universe: str
    sources: tuple[str, ...]
    missing: tuple[str, ...]
    cadence: str
    channel: str
    content_hash: str
    body: dict[str, Any]
    envelope_id: str = field(default_factory=new_ulid)
    error_class: str | None = None
    alert_channel: str | None = None
    dq_channel: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_utc", as_utc(self.as_of_utc))
        object.__setattr__(self, "sources", tuple(sorted(self.sources)))
        object.__setattr__(self, "missing", tuple(sorted(self.missing)))
        if self.op not in OP_VALUES:
            raise ValueError(f"op must be paper|observation, got {self.op!r}")
        if self.error_class is not None and self.error_class not in ERROR_CLASS_VALUES:
            raise ValueError(f"unknown error_class {self.error_class!r}")

    def header(self) -> dict[str, Any]:
        return {
            "desk": self.desk,
            "as_of_utc": self.as_of_utc.isoformat(),
            "as_of_sydney": self.as_of_sydney,
            "status": self.status,
            "n": self.n,
            "completeness": self.completeness,
            "regime": self.regime,
            "op": self.op,
            "universe": self.universe,
            "sources": list(self.sources),
            "missing": list(self.missing),
            "cadence": self.cadence,
            "error_class": self.error_class,
        }

    def canonical(self) -> dict[str, Any]:
        """Hashable payload. Excludes envelope_id (ULID) so re-runs stay stable."""
        return {
            "header": self.header(),
            "channel": self.channel,
            "body": self.body,
        }

    def notify_payload(self) -> dict[str, Any]:
        payload = {
            "id": self.envelope_id,
            "desk": self.desk,
            "as_of": self.as_of_utc.isoformat(),
            "content_hash": self.content_hash,
            "channel": self.channel,
            "status": self.status,
        }
        blob = canonical_json(payload)
        if len(blob.encode("utf-8")) > NOTIFY_MAX_BYTES:
            raise ValueError("NOTIFY payload exceeds Postgres 8000-byte limit")
        return payload

    def as_row(self) -> dict[str, Any]:
        return {
            "id": self.envelope_id,
            "desk": self.desk,
            "channel": self.channel,
            "as_of_knowledge": self.as_of_utc,
            "as_of_sydney": self.as_of_sydney,
            "status": self.status,
            "n": self.n,
            "completeness_pct": self.completeness,
            "regime": self.regime,
            "op": self.op,
            "universe": self.universe,
            "sources": list(self.sources),
            "missing": list(self.missing),
            "cadence": self.cadence,
            "content_hash": self.content_hash,
            "error_class": self.error_class,
            "body_json": self.body,
            "alert_channel": self.alert_channel,
            "dq_channel": self.dq_channel,
        }


def envelope_from_output(
    output: DeskOutput,
    *,
    repo_root: Any | None = None,
    envelope_id: str | None = None,
) -> DeskEnvelope:
    spec = cadence_for(output.slug, repo_root)
    header_body = {
        "desk": output.slug,
        "as_of_utc": output.as_of_knowledge.isoformat(),
        "as_of_sydney": in_ops_tz(output.as_of_knowledge).isoformat(),
        "status": output.status,
        "n": int(output.n if output.n is not None else infer_n(output)),
        "completeness": output.completeness_pct,
        "regime": output.regime or REGIME_PLACEHOLDER,
        "op": output.op,
        "universe": output.universe,
        "sources": list(output.sources),
        "missing": list(output.missing),
        "cadence": output.cadence or spec.cadence,
        "error_class": output.error_class,
        "channel": spec.output_channel,
        "body": output.canonical(),
    }
    digest = sha256_hex(canonical_json(header_body))
    return DeskEnvelope(
        desk=output.slug,
        as_of_utc=output.as_of_knowledge,
        as_of_sydney=header_body["as_of_sydney"],
        status=output.status,
        n=int(header_body["n"]),
        completeness=output.completeness_pct,
        regime=str(header_body["regime"]),
        op=output.op,
        universe=output.universe,
        sources=output.sources,
        missing=output.missing,
        cadence=str(header_body["cadence"]),
        channel=spec.output_channel,
        content_hash=digest,
        body=output.canonical(),
        envelope_id=envelope_id or new_ulid(),
        error_class=output.error_class,
        alert_channel=spec.alert_channel,
        dq_channel=spec.dq_channel,
    )


def envelope_from_row(row: Any) -> DeskEnvelope:
    body = dict(getattr(row, "body_json", None) or {})
    return DeskEnvelope(
        desk=str(row.desk),
        as_of_utc=row.as_of_knowledge,
        as_of_sydney=str(row.as_of_sydney),
        status=str(row.status),
        n=int(row.n),
        completeness=float(row.completeness_pct),
        regime=str(row.regime),
        op=str(row.op),
        universe=str(row.universe),
        sources=tuple(row.sources or ()),
        missing=tuple(row.missing or ()),
        cadence=str(row.cadence),
        channel=str(row.channel),
        content_hash=str(row.content_hash),
        body=body,
        envelope_id=str(row.id),
        error_class=row.error_class,
        alert_channel=getattr(row, "alert_channel", None),
        dq_channel=getattr(row, "dq_channel", None),
    )
