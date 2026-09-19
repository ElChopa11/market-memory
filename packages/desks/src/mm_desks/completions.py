"""Filesystem completion log for Hive → lab CLI fires (IMP-046 / Hybrid Step 4).

Miss sweep (IMP-042) is still the control: closed window + no completion → miss.
This module is the row the sweep can observe on the executed path (Hive clock
→ lab CLI), including ``--no-db``. Heartbeat-on-fire remains a log.

Must not import mm_execution, sign, or talk to Telegram live.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Mapping

from mm_common.time import as_utc, utcnow
from mm_desks.scheduler import (
    Completion,
    Catalog,
    load_catalog,
    stamp_fire,
    completion_from_mapping,
)

COMPLETIONS_REL = Path("ops") / "reports" / "scheduler" / "completions"
COMPLETIONS_ENV = "MM_SCHEDULE_COMPLETIONS_DIR"
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")

DEFAULT_BRIEF_ROUTINES = {
    "preopen": "lab.pulse.preopen",
    "close": "lab.pulse.close",
}
DEFAULT_DELIVER_ROUTINES = {
    "watchlist": "lab.delivery.watchlist",
    "listings": "lab.delivery.listings",
    "scorecard": "lab.delivery.scorecard",
    "decay": "lab.delivery.decay",
}


def resolve_completions_dir(
    root: Path,
    override: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Explicit --completions-dir wins, then env, then repo canonical path."""
    if override:
        return Path(override)
    env = environ if environ is not None else os.environ
    raw = str(env.get(COMPLETIONS_ENV) or "").strip()
    if raw:
        return Path(raw)
    return Path(root) / COMPLETIONS_REL


def completion_filename(record: Completion) -> str:
    anchor = as_utc(record.scheduled_anchor_ts).strftime("%Y%m%dT%H%M%SZ")
    safe = _SAFE_ID.sub("_", record.routine_id).strip("._") or "routine"
    return f"{safe}__{anchor}.json"


def write_completion(record: Completion, *, dest_dir: Path) -> Path:
    """Idempotent on (routine_id, scheduled_anchor_ts). Higher-rank status wins."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / completion_filename(record)
    if path.is_file():
        try:
            existing = completion_from_mapping(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
            existing = None
        rank = {"ok": 3, "late": 2, "skipped": 1, "missed": 0}
        if existing is not None and rank.get(record.status, 0) < rank.get(existing.status, 0):
            return path
    path.write_text(json.dumps(record.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_disk_completions(dest_dir: Path, *, catalog: Catalog | None = None) -> list[Completion]:
    if not dest_dir.is_dir():
        return []
    rows: list[Completion] = []
    for path in sorted(dest_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or not raw.get("routine_id"):
            continue
        try:
            rows.append(completion_from_mapping(raw, catalog=catalog))
        except (KeyError, ValueError, TypeError):
            continue
    return rows


def infer_routine_id(
    *,
    explicit: str | None = None,
    brief_kind: str | None = None,
    deliver_cmd: str | None = None,
) -> str | None:
    """Hive passes --routine-id (grok.*). Lab defaults stamp pulse/delivery ids only."""
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    if brief_kind:
        return DEFAULT_BRIEF_ROUTINES.get(str(brief_kind))
    if deliver_cmd:
        return DEFAULT_DELIVER_ROUTINES.get(str(deliver_cmd))
    return None


def record_cli_completion(
    *,
    root: Path,
    routine_id: str,
    fired_at: datetime | None = None,
    run_id: str | None = None,
    exit_status: int | None = None,
    payload_path: str | None = None,
    cli: str | None = None,
    source: str = "lab.cli",
    persist_db: bool = False,
    dsn: str | None = None,
    completions_dir: Path | str | None = None,
    catalog: Catalog | None = None,
) -> Completion:
    """Write a completion row the miss sweep can load. DB persist is optional.

    A failed CLI run is still a fire (exit_status != 0). Silence (no row) is the miss.
    """
    cat = catalog if catalog is not None else load_catalog(root)
    routine = cat.by_id().get(str(routine_id))
    if routine is None:
        raise ValueError(f"unknown routine_id {routine_id}")
    fired = as_utc(fired_at or utcnow())
    rid = str(run_id or f"{routine.routine_id}-{fired.strftime('%Y%m%dT%H%M%SZ')}")
    record = stamp_fire(
        routine,
        fired_at=fired,
        run_id=rid,
        as_of_knowledge=fired,
        source=source,
        exit_status=exit_status,
        payload_path=payload_path,
        cli=cli,
    )
    dest = resolve_completions_dir(root, completions_dir)
    write_completion(record, dest_dir=dest)
    if persist_db:
        from mm_memory.db import dsn_from_env, session_scope
        from mm_memory.heartbeat_repository import persist_heartbeat

        with session_scope(dsn or dsn_from_env()) as session:
            persist_heartbeat(session, record.canonical())
    return record
