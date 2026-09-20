"""CLI helper: stamp a schedule completion row on Hive → lab fires.

Miss sweep remains the control. This is the row it can observe.
"""

from __future__ import annotations

import json
import os
import sys
from argparse import Namespace
from datetime import datetime
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_desks.completions import infer_routine_id, record_cli_completion
from mm_desks.scheduler import WrongAnchorError


def add_completion_args(parser) -> None:
    parser.add_argument(
        "--routine-id",
        default="",
        help="catalog routine id to stamp (Hive clock: grok.sydney_morning / grok.us_pre_market / grok.weekly_investment_review)",
    )
    parser.add_argument("--run-id", default="", help="optional run_id for the completion row")
    parser.add_argument(
        "--completions-dir",
        type=Path,
        help="where to write/read completion JSON (default: ops/reports/scheduler/completions)",
    )


def fired_at_from_args(args: Namespace) -> datetime:
    raw = getattr(args, "as_of", None) or getattr(args, "fired_at", None)
    if raw:
        return parse_utc(str(raw))
    return utcnow()


def stamp_cli_fire(
    args: Namespace,
    *,
    exit_status: int,
    payload_path: str | None = None,
    brief_kind: str | None = None,
    deliver_cmd: str | None = None,
    cli: str | None = None,
    fired_at: datetime | None = None,
    source: str = "lab.cli",
) -> None:
    """Best-effort. A write failure must not hide the original CLI exit status."""
    routine_id = infer_routine_id(
        explicit=getattr(args, "routine_id", None),
        brief_kind=brief_kind,
        deliver_cmd=deliver_cmd,
    )
    if not routine_id:
        return
    root = Path(getattr(args, "repo_root", Path(".")) or Path(".")).resolve()
    persist_db = not bool(getattr(args, "no_db", False))
    if persist_db and os.environ.get("PYTEST_CURRENT_TEST"):
        persist_db = False
    try:
        record_cli_completion(
            root=root,
            routine_id=routine_id,
            fired_at=fired_at or fired_at_from_args(args),
            run_id=str(getattr(args, "run_id", "") or "") or None,
            exit_status=exit_status,
            payload_path=payload_path,
            cli=cli,
            source=source,
            persist_db=persist_db,
            dsn=getattr(args, "dsn", None),
            completions_dir=getattr(args, "completions_dir", None),
        )
    except WrongAnchorError as exc:
        payload = exc.as_public_dict()
        payload["warn"] = "completion row skipped: wrong_anchor"
        print(json.dumps(payload), file=sys.stderr)
    except Exception as exc:  # pragma: no cover - must not mask the fire's exit
        print(json.dumps({"warn": f"completion row skipped: {exc.__class__.__name__}", "wrote": False}), file=sys.stderr)
