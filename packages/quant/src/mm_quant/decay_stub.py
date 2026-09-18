"""Phase 6e stub of prompt-hash decay *inputs*. Full watch is IMP-031 / 6f.

Records SHA-256 of versioned prompt files. Does not alert, disable, or
auto-roll prompts. watch_enabled stays false.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mm_common.hashing import sha256_hex

STUB_VERSION = "imp-030.1"
WATCH_ENABLED = False
PHASE = "6f-parked"
ITEM = "IMP-031"


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def load_decay_stub_config(root: Path | None = None) -> dict[str, Any]:
    path = repo_root(root) / "config" / "scorecards" / "decay.yaml"
    if not path.is_file():
        return {"watch_enabled": False, "phase": PHASE, "item": ITEM, "prompt_files": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def prompt_hashes(root: Path | None = None) -> tuple[dict[str, str], ...]:
    base = repo_root(root)
    cfg = load_decay_stub_config(base)
    rows: list[dict[str, str]] = []
    for rel in cfg.get("prompt_files") or []:
        path = base / str(rel)
        digest = sha256_hex(path.read_bytes()) if path.is_file() else ""
        rows.append({"path": str(rel), "sha256": digest, "present": str(path.is_file()).lower()})
    return tuple(rows)


def decay_stub_payload(root: Path | None = None) -> dict[str, Any]:
    cfg = load_decay_stub_config(root)
    return {
        "watch_enabled": bool(cfg.get("watch_enabled", WATCH_ENABLED)),
        "phase": str(cfg.get("phase") or PHASE),
        "item": str(cfg.get("item") or ITEM),
        "stub_version": STUB_VERSION,
        "prompt_hashes": [dict(row) for row in prompt_hashes(root)],
        "note": "6e records prompt hashes only. Strategy decay-watch is IMP-031 / 6f.",
    }


def assert_stub_does_not_watch(root: Path | None = None) -> None:
    payload = decay_stub_payload(root)
    if payload["watch_enabled"]:
        raise ValueError("6e decay stub must keep watch_enabled false (full watch is 6f)")
    if payload["phase"] != PHASE:
        raise ValueError(f"6e decay stub phase must be {PHASE!r}")
