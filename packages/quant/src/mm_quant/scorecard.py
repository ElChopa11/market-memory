"""Like-for-like pack scoring (Phase 6e / IMP-030).

Quant-owned. Comparable packs share product + schedule_anchor + universe and
carry no incomparable tag. Provenance (content_hash, as_of_knowledge, sources)
rides every row. Incomparable pairs are tagged, never scored as equals.

Not a call. Not sizing. Not Execution. Must not import mm_execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import yaml

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc, parse_utc

ENGINE_VERSION = "imp-030.1"
COMPARABLE = "COMPARABLE"
NOT_COMPARABLE = "NOT_COMPARABLE"
VERDICTS = (COMPARABLE, NOT_COMPARABLE)

REASON_SCHEDULE = "schedule_anchor_mismatch"
REASON_PRODUCT = "product_mismatch"
REASON_UNIVERSE = "universe_mismatch"
REASON_TAGGED = "tagged_incomparable"
REASON_LOOKAHEAD = "as_of_knowledge_lookahead"
REASON_MISSING_PROVENANCE = "missing_provenance"

COMPARABILITY_KEYS = ("product", "schedule_anchor", "universe")
FOOTER = (
    "Not a call. Like-for-like only when product, schedule_anchor, and universe "
    "match and no incomparable tag applies. Incomparable artifacts stay tagged. "
    "Quant owns the math; Ops publishes. Coord orchestrates."
)


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_scorecard_config(root: Path | None = None) -> dict[str, Any]:
    base = repo_root(root)
    desk = _load_yaml(base / "config" / "scorecards" / "desk.yaml")
    tags = _load_yaml(base / "config" / "scorecards" / "tags.yaml")
    return {"desk": desk, "tags": tags}


def load_incomparable_tags(root: Path | None = None) -> tuple[dict[str, Any], ...]:
    cfg = load_scorecard_config(root)
    rows = cfg.get("tags", {}).get("tags") or []
    return tuple(row for row in rows if isinstance(row, dict))


@dataclass(frozen=True)
class PackRecord:
    """One desk pack / brief artifact with provenance. Missing fields stay unavailable."""

    pack_id: str
    product: str
    schedule_anchor: str
    universe: str
    as_of_knowledge: datetime
    content_hash: str
    status: str
    completeness: float | None
    n: int | None
    sources: tuple[str, ...]
    missing: tuple[str, ...]
    tags: tuple[str, ...]
    local_time: str | None = None
    timezone: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "product": self.product,
            "schedule_anchor": self.schedule_anchor,
            "universe": self.universe,
            "as_of_knowledge": self.as_of_knowledge.isoformat(),
            "content_hash": self.content_hash,
            "status": self.status,
            "completeness": self.completeness,
            "n": self.n,
            "sources": list(self.sources),
            "missing": list(self.missing),
            "tags": list(self.tags),
            "local_time": self.local_time,
            "timezone": self.timezone,
        }


@dataclass(frozen=True)
class PairScore:
    """One pairwise scorecard row. Numeric like-for-like scores exist only when comparable."""

    left_id: str
    right_id: str
    verdict: str
    reason_codes: tuple[str, ...]
    comparable: bool
    completeness_delta: float | None
    hash_identity: bool | None
    status_match: bool | None
    source_overlap: float | None
    left_hash: str
    right_hash: str
    left_as_of: str
    right_as_of: str
    note: str

    def canonical(self) -> dict[str, Any]:
        return {
            "left_id": self.left_id,
            "right_id": self.right_id,
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
            "comparable": self.comparable,
            "completeness_delta": self.completeness_delta,
            "hash_identity": self.hash_identity,
            "status_match": self.status_match,
            "source_overlap": self.source_overlap,
            "left_hash": self.left_hash,
            "right_hash": self.right_hash,
            "left_as_of": self.left_as_of,
            "right_as_of": self.right_as_of,
            "note": self.note,
        }


def pack_from_mapping(raw: Mapping[str, Any]) -> PackRecord:
    as_of = raw.get("as_of_knowledge")
    if as_of is None:
        raise ValueError("pack requires as_of_knowledge")
    watermark = as_of if isinstance(as_of, datetime) else parse_utc(str(as_of))
    completeness = raw.get("completeness")
    n = raw.get("n")
    return PackRecord(
        pack_id=str(raw.get("pack_id") or raw.get("id") or ""),
        product=str(raw.get("product") or ""),
        schedule_anchor=str(raw.get("schedule_anchor") or ""),
        universe=str(raw.get("universe") or ""),
        as_of_knowledge=as_utc(watermark),
        content_hash=str(raw.get("content_hash") or ""),
        status=str(raw.get("status") or "unavailable"),
        completeness=None if completeness is None else float(completeness),
        n=None if n is None else int(n),
        sources=tuple(str(s) for s in (raw.get("sources") or [])),
        missing=tuple(str(s) for s in (raw.get("missing") or [])),
        tags=tuple(str(s) for s in (raw.get("tags") or [])),
        local_time=None if raw.get("local_time") is None else str(raw.get("local_time")),
        timezone=None if raw.get("timezone") is None else str(raw.get("timezone")),
    )


def _tag_blocks(pack: PackRecord, tags: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    blocked: list[str] = []
    pack_tags = set(pack.tags)
    for row in tags:
        tag_id = str(row.get("id") or "")
        if not tag_id or tag_id not in pack_tags:
            continue
        if row.get("comparable") is False:
            blocked.append(tag_id)
            reason = str(row.get("reason_code") or REASON_TAGGED)
            if reason not in blocked:
                blocked.append(reason)
    return tuple(blocked)


def comparability_reasons(
    left: PackRecord,
    right: PackRecord,
    *,
    tags: tuple[dict[str, Any], ...] = (),
    as_of: datetime | None = None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if as_of is not None:
        clock = as_utc(as_of)
        if left.as_of_knowledge > clock or right.as_of_knowledge > clock:
            reasons.append(REASON_LOOKAHEAD)
    if left.product != right.product:
        reasons.append(REASON_PRODUCT)
    if left.schedule_anchor != right.schedule_anchor:
        reasons.append(REASON_SCHEDULE)
    if left.universe != right.universe:
        reasons.append(REASON_UNIVERSE)
    if not left.content_hash or not right.content_hash:
        reasons.append(REASON_MISSING_PROVENANCE)
    left_block = _tag_blocks(left, tags)
    right_block = _tag_blocks(right, tags)
    if left_block or right_block:
        if REASON_TAGGED not in reasons:
            reasons.append(REASON_TAGGED)
        for extra in (*left_block, *right_block):
            if extra not in reasons and extra != REASON_TAGGED:
                # tag ids ride along for operators; reason_code already listed
                if extra.endswith("_mismatch") or extra == REASON_SCHEDULE:
                    if extra not in reasons:
                        reasons.append(extra)
    # Explicit: a tagged 90m pack vs a 30m pack is never like-for-like even if
    # an operator forgot the schedule_anchor field.
    for row in tags:
        tag_id = str(row.get("id") or "")
        if tag_id not in {*left.tags, *right.tags}:
            continue
        observed = str(row.get("observed_anchor") or "")
        canonical = str(row.get("canonical_anchor") or "")
        anchors = {left.schedule_anchor, right.schedule_anchor}
        if observed and canonical and observed in anchors and canonical in anchors and observed != canonical:
            if REASON_SCHEDULE not in reasons:
                reasons.append(REASON_SCHEDULE)
            if REASON_TAGGED not in reasons:
                reasons.append(REASON_TAGGED)
    return tuple(reasons)


def _overlap(left: tuple[str, ...], right: tuple[str, ...]) -> float | None:
    if not left and not right:
        return 1.0
    union = set(left) | set(right)
    if not union:
        return None
    return len(set(left) & set(right)) / float(len(union))


def score_pair(
    left: PackRecord,
    right: PackRecord,
    *,
    tags: tuple[dict[str, Any], ...] = (),
    as_of: datetime | None = None,
) -> PairScore:
    reasons = comparability_reasons(left, right, tags=tags, as_of=as_of)
    comparable = not reasons
    if not comparable:
        note = "not like-for-like; tagged or mismatched provenance — no numeric compare"
        return PairScore(
            left_id=left.pack_id,
            right_id=right.pack_id,
            verdict=NOT_COMPARABLE,
            reason_codes=reasons,
            comparable=False,
            completeness_delta=None,
            hash_identity=None,
            status_match=None,
            source_overlap=None,
            left_hash=left.content_hash,
            right_hash=right.content_hash,
            left_as_of=left.as_of_knowledge.isoformat(),
            right_as_of=right.as_of_knowledge.isoformat(),
            note=note,
        )
    delta = None
    if left.completeness is not None and right.completeness is not None:
        delta = round(left.completeness - right.completeness, 4)
    return PairScore(
        left_id=left.pack_id,
        right_id=right.pack_id,
        verdict=COMPARABLE,
        reason_codes=(),
        comparable=True,
        completeness_delta=delta,
        hash_identity=left.content_hash == right.content_hash,
        status_match=left.status == right.status,
        source_overlap=_overlap(left.sources, right.sources),
        left_hash=left.content_hash,
        right_hash=right.content_hash,
        left_as_of=left.as_of_knowledge.isoformat(),
        right_as_of=right.as_of_knowledge.isoformat(),
        note="like-for-like; provenance attached; not a call",
    )


def visible_packs(
    packs: tuple[PackRecord, ...],
    *,
    as_of: datetime,
) -> tuple[PackRecord, ...]:
    """Point-in-time: packs with as_of_knowledge > run clock stay invisible."""
    clock = as_utc(as_of)
    return tuple(p for p in packs if p.as_of_knowledge <= clock)


def score_packs(
    packs: tuple[PackRecord, ...],
    *,
    as_of: datetime,
    tags: tuple[dict[str, Any], ...] = (),
) -> tuple[PairScore, ...]:
    visible = visible_packs(packs, as_of=as_of)
    rows: list[PairScore] = []
    for i, left in enumerate(visible):
        for right in visible[i + 1 :]:
            rows.append(score_pair(left, right, tags=tags, as_of=as_of))
    return tuple(rows)


def pair_digest(rows: tuple[PairScore, ...]) -> str:
    return sha256_hex(canonical_json([row.canonical() for row in rows]))
