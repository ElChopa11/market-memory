"""Prompt-hash strategy decay-watch (Phase 6f / IMP-031).

Quant-owned hash math. Detects prompt and config drift via SHA-256.
Mismatch is a NOTIFY / queue *signal* only: no auto-disable, no gate waiver,
no invented like-for-like scorecard numbers for NOT_COMPARABLE tags.

Must not import mm_execution. Not a call. Not a sixth desk.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from mm_common.hashing import canonical_json, sha256_hex
from mm_quant.scorecard import NOT_COMPARABLE, PairScore

ENGINE_VERSION = "imp-031.1"
WATCH_ENABLED = True
PHASE = "6f"
ITEM = "IMP-031"

MATCH = "MATCH"
MISMATCH = "MISMATCH"
MISSING = "MISSING"
UNPINNED = "UNPINNED"
FILE_VERDICTS = (MATCH, MISMATCH, MISSING, UNPINNED)

KIND_PROMPT = "prompt"
KIND_CONFIG = "config"

FOOTER = (
    "Not a call. Prompt and config hashes are versioned. Mismatch emits a "
    "NOTIFY/queue signal. Does not waive Skeptic or Risk. Does not invent "
    "like-for-like scores for tagged incomparable packs. Quant owns the math; "
    "Ops publishes. Coord orchestrates."
)
NO_INVENTED_SCORE = "decay_does_not_invent_comparable_scorecards"
NO_AUTO_WAIVE = "decay_does_not_waive_gates"
NO_AUTO_DISABLE = "decay_does_not_auto_disable_prompts"
FORBIDDEN_ACTIONS = frozenset({"merge", "waive", "auto-merge", "auto-waive", "close-open", "promote-live", "auto-disable"})


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


def load_decay_config(root: Path | None = None) -> dict[str, Any]:
    path = repo_root(root) / "config" / "scorecards" / "decay.yaml"
    data = _load_yaml(path)
    return data if data else {"watch_enabled": False, "phase": PHASE, "item": ITEM, "prompt_files": [], "config_files": []}


def _file_specs(cfg: Mapping[str, Any], key: str, kind: str) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for raw in cfg.get(key) or []:
        if isinstance(raw, str):
            rows.append({"path": raw, "expected_sha256": "", "kind": kind})
            continue
        if not isinstance(raw, dict):
            continue
        path = str(raw.get("path") or raw.get("rel") or "")
        if not path:
            continue
        rows.append(
            {
                "path": path,
                "expected_sha256": str(raw.get("expected_sha256") or raw.get("sha256") or ""),
                "kind": kind,
            }
        )
    return tuple(rows)


def watched_specs(cfg: Mapping[str, Any] | None = None, root: Path | None = None) -> tuple[dict[str, str], ...]:
    data = dict(cfg or load_decay_config(root))
    return _file_specs(data, "prompt_files", KIND_PROMPT) + _file_specs(data, "config_files", KIND_CONFIG)


@dataclass(frozen=True)
class HashRow:
    path: str
    kind: str
    expected_sha256: str
    observed_sha256: str
    present: bool
    verdict: str

    def canonical(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "expected_sha256": self.expected_sha256,
            "observed_sha256": self.observed_sha256,
            "present": self.present,
            "verdict": self.verdict,
        }


def _verdict(*, present: bool, expected: str, observed: str) -> str:
    if not present:
        return MISSING
    if not expected:
        return UNPINNED
    if expected == observed:
        return MATCH
    return MISMATCH


def hash_row(spec: Mapping[str, str], *, root: Path, override: str | None = None) -> HashRow:
    rel = str(spec.get("path") or "")
    path = root / rel
    present = path.is_file()
    observed = sha256_hex(path.read_bytes()) if present else ""
    expected = str(override if override is not None else spec.get("expected_sha256") or "")
    return HashRow(
        path=rel,
        kind=str(spec.get("kind") or KIND_PROMPT),
        expected_sha256=expected,
        observed_sha256=observed,
        present=present,
        verdict=_verdict(present=present, expected=expected, observed=observed),
    )


def prompt_hashes(root: Path | None = None) -> tuple[dict[str, str], ...]:
    """Compat shape used by the 6e stub: path / sha256 / present."""
    base = repo_root(root)
    rows: list[dict[str, str]] = []
    for spec in watched_specs(root=base):
        if spec["kind"] != KIND_PROMPT:
            continue
        row = hash_row(spec, root=base)
        rows.append({"path": row.path, "sha256": row.observed_sha256, "present": str(row.present).lower()})
    return tuple(rows)


def watch_rows(
    root: Path | None = None,
    *,
    expected_overrides: Mapping[str, str] | None = None,
    extra_specs: tuple[Mapping[str, str], ...] = (),
) -> tuple[HashRow, ...]:
    base = repo_root(root)
    cfg = load_decay_config(base)
    overrides = {str(k): str(v) for k, v in dict(expected_overrides or {}).items()}
    rows: list[HashRow] = []
    for spec in (*watched_specs(cfg, root=base), *extra_specs):
        override = overrides.get(str(spec.get("path") or ""))
        rows.append(hash_row(spec, root=base, override=override))
    return tuple(rows)


def overall_verdict(rows: tuple[HashRow, ...]) -> str:
    if not rows:
        return MISSING
    verdicts = {row.verdict for row in rows}
    if MISMATCH in verdicts:
        return MISMATCH
    if MISSING in verdicts or UNPINNED in verdicts:
        return MISSING if MISSING in verdicts else UNPINNED
    return MATCH


def queue_signal(rows: tuple[HashRow, ...]) -> dict[str, Any]:
    """Operator-facing signal. Does not write ops/improvement-queue.md."""
    drifted = tuple(row.path for row in rows if row.verdict != MATCH)
    active = bool(drifted)
    return {
        "kind": "NOTIFY" if active else "none",
        "active": active,
        "auto_write": False,
        "auto_waive": False,
        "auto_merge": False,
        "auto_disable": False,
        "auto_close_open": False,
        "item": None,
        "paths": list(drifted),
        "note": (
            "hash drift recorded; operator may intake a queue item. "
            "Helper does not write the queue, waive gates, or close OPEN incidents."
            if active
            else "hashes match pinned versions; no queue signal"
        ),
    }


def attach_scorecard_pairs(pairs: tuple[PairScore, ...] | tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    """Pass through scorecard pairs. Never invent a comparable score for NOT_COMPARABLE."""
    out: list[dict[str, Any]] = []
    for raw in pairs:
        row = dict(raw.canonical()) if isinstance(raw, PairScore) else dict(raw)
        verdict = str(row.get("verdict") or "")
        comparable = bool(row.get("comparable"))
        if verdict == NOT_COMPARABLE or not comparable:
            row["verdict"] = NOT_COMPARABLE
            row["comparable"] = False
            row["completeness_delta"] = None
            row["hash_identity"] = None
            row["status_match"] = None
            row["source_overlap"] = None
            row["decay_invented_score"] = False
            note = str(row.get("note") or "")
            if NO_INVENTED_SCORE not in note:
                row["note"] = (note + " " if note else "") + NO_INVENTED_SCORE
        else:
            row["decay_invented_score"] = False
        refuse_invented_comparable((row,))
        out.append(row)
    return tuple(out)


def refuse_invented_comparable(rows: tuple[Mapping[str, Any], ...]) -> None:
    for row in rows:
        verdict = str(row.get("verdict") or "")
        if verdict != NOT_COMPARABLE and row.get("comparable") is not False:
            continue
        if row.get("completeness_delta") is not None or row.get("hash_identity") is not None:
            raise ValueError("decay must not invent like-for-like scores for NOT_COMPARABLE packs")
        if row.get("comparable") is True or verdict == "COMPARABLE":
            raise ValueError("decay must not flip NOT_COMPARABLE packs to comparable")


def refuse_forbidden(action: str | None) -> str | None:
    if not action:
        return None
    key = action.strip().lower()
    if key in FORBIDDEN_ACTIONS:
        return (
            f"decay watch refuses {key!r}: no auto-merge, no gate waiver, "
            "no auto-disable, no auto-close of OPEN incidents"
        )
    return None


def decay_watch_payload(
    root: Path | None = None,
    *,
    expected_overrides: Mapping[str, str] | None = None,
    extra_specs: tuple[Mapping[str, str], ...] = (),
    scorecard_pairs: tuple[PairScore, ...] | tuple[Mapping[str, Any], ...] = (),
) -> dict[str, Any]:
    cfg = load_decay_config(root)
    if cfg.get("auto_disable") is True or cfg.get("auto_waive") is True or cfg.get("auto_merge") is True:
        raise ValueError("decay watch must keep auto_disable/auto_waive/auto_merge false")
    watch_on = bool(cfg.get("watch_enabled", WATCH_ENABLED))
    rows = watch_rows(root, expected_overrides=expected_overrides, extra_specs=extra_specs)
    attached = attach_scorecard_pairs(scorecard_pairs) if scorecard_pairs else ()
    signal = queue_signal(rows)
    digest = sha256_hex(
        canonical_json(
            {
                "engine_version": ENGINE_VERSION,
                "rows": [row.canonical() for row in rows],
                "scorecard_pairs": list(attached),
            }
        )
    )
    return {
        "watch_enabled": watch_on,
        "phase": str(cfg.get("phase") or PHASE),
        "item": str(cfg.get("item") or ITEM),
        "engine_version": ENGINE_VERSION,
        "alert_path": str(cfg.get("alert_path") or "ops"),
        "math_desk": str(cfg.get("math_desk") or "quant"),
        "auto_disable": False,
        "auto_waive": False,
        "auto_merge": False,
        "overall": overall_verdict(rows),
        "rows": [row.canonical() for row in rows],
        "prompt_hashes": [dict(row) for row in prompt_hashes(root)],
        "n_match": sum(1 for row in rows if row.verdict == MATCH),
        "n_mismatch": sum(1 for row in rows if row.verdict == MISMATCH),
        "n_missing": sum(1 for row in rows if row.verdict == MISSING),
        "n_unpinned": sum(1 for row in rows if row.verdict == UNPINNED),
        "queue_signal": signal,
        "scorecard_pairs": list(attached),
        "content_hash": digest,
        "footer": FOOTER,
        "note": (
            "6f prompt-hash decay watch. Mismatch → NOTIFY/queue signal. "
            "Does not waive gates or invent scorecard numbers."
        ),
    }


def decay_stub_payload(root: Path | None = None) -> dict[str, Any]:
    """Compat alias for IMP-030 scorecard embedding."""
    return decay_watch_payload(root)
