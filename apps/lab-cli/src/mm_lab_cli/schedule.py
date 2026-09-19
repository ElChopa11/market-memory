"""lab schedule — miss sweep is the scheduler control. Heartbeat-on-fire is a log."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_desks.scheduler import (
    completion_from_mapping,
    load_catalog,
    load_fixture,
    miss_sweep,
    render_backfill_markdown,
    stamp_fire,
    write_incident_artifact,
)


def add_schedule_parser(sub) -> None:
    sched = sub.add_parser("schedule", help="scheduler miss sweep (control) + heartbeat log")
    inner = sched.add_subparsers(dest="schedule_cmd")

    miss = inner.add_parser(
        "miss-check",
        help="MERGE-BLOCKING: closed window + no completion → non-zero + OPEN artifact",
    )
    _add_sweep_args(miss)

    # Alias: operators may type heartbeat-check; it still runs the miss sweep.
    hb = inner.add_parser(
        "heartbeat-check",
        help="alias of miss-check (the control). Does not treat heartbeat writes as a pass.",
    )
    _add_sweep_args(hb)

    rec = inner.add_parser("record-fire", help="secondary: stamp a completion log row for a fire")
    rec.add_argument("--routine-id", required=True)
    rec.add_argument("--fired-at", required=True, help="UTC instant (ISO-8601)")
    rec.add_argument("--run-id", default="")
    rec.add_argument("--repo-root", type=Path, default=Path("."))
    rec.add_argument("--dsn")
    rec.add_argument("--no-db", action="store_true")
    rec.add_argument("--source", default="lab")

    backfill = inner.add_parser(
        "backfill",
        help="reconcile configured routines vs completions; write backfill markdown",
    )
    _add_sweep_args(backfill)
    backfill.add_argument(
        "--report-out",
        type=Path,
        help="write ops/reports/scheduler/backfill-YYYY-MM-DD.md (default under --out or cwd)",
    )


def _add_sweep_args(parser) -> None:
    parser.add_argument("--fixture", type=Path, help="frozen catalog+completions YAML (CI clock)")
    parser.add_argument("--now", help="UTC instant (ISO-8601); fixture clock in CI")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, help="directory for OPEN miss artifact")
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--lookback-days", type=int, default=None)


def dispatch_schedule(args: Namespace) -> int:
    cmd = getattr(args, "schedule_cmd", None)
    if cmd in {"miss-check", "heartbeat-check", None}:
        if cmd is None:
            print("usage: lab schedule miss-check|heartbeat-check|record-fire|backfill", file=sys.stderr)
            return 2
        return _cmd_miss_check(args)
    if cmd == "record-fire":
        return _cmd_record_fire(args)
    if cmd == "backfill":
        return _cmd_backfill(args)
    print("usage: lab schedule miss-check|heartbeat-check|record-fire|backfill", file=sys.stderr)
    return 2


def _load_state(args: Namespace):
    root = Path(args.repo_root).resolve()
    now = parse_utc(args.now) if getattr(args, "now", None) else utcnow()
    if getattr(args, "fixture", None):
        catalog, completions, fixture_now = load_fixture(Path(args.fixture), root=root)
        if fixture_now is not None and not getattr(args, "now", None):
            now = fixture_now
        return root, catalog, list(completions), now
    catalog = load_catalog(root)
    completions = []
    if not args.no_db:
        try:
            from mm_memory.db import dsn_from_env, session_scope
            from mm_memory.heartbeat_repository import load_completions

            with session_scope(args.dsn or dsn_from_env()) as session:
                completions = [
                    completion_from_mapping(row, catalog=catalog) for row in load_completions(session)
                ]
        except Exception as exc:  # pragma: no cover - optional db
            print(json.dumps({"warn": f"heartbeat load skipped: {exc.__class__.__name__}"}), file=sys.stderr)
    return root, catalog, completions, now


def _cmd_miss_check(args: Namespace) -> int:
    root, catalog, completions, now = _load_state(args)
    result = miss_sweep(catalog, completions, now, lookback_days=getattr(args, "lookback_days", None))
    artifact = None
    if result.escalated:
        out_dir = Path(args.out).resolve() if getattr(args, "out", None) else (root / "ops" / "reports" / "scheduler" / "incidents")
        artifact = write_incident_artifact(result, out_dir=out_dir)
        result = result.with_artifact(str(artifact))
    payload = result.canonical()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if result.escalated else 0


def _cmd_record_fire(args: Namespace) -> int:
    root = Path(args.repo_root).resolve()
    catalog = load_catalog(root)
    routine = catalog.by_id().get(str(args.routine_id))
    if routine is None:
        print(json.dumps({"error": f"unknown routine_id {args.routine_id}"}), file=sys.stderr)
        return 2
    fired = parse_utc(str(args.fired_at))
    run_id = str(args.run_id or f"{routine.routine_id}-{fired.strftime('%Y%m%dT%H%M%SZ')}")
    record = stamp_fire(routine, fired_at=fired, run_id=run_id, as_of_knowledge=fired, source=str(args.source))
    if not args.no_db:
        try:
            from mm_memory.db import dsn_from_env, session_scope
            from mm_memory.heartbeat_repository import persist_heartbeat

            with session_scope(args.dsn or dsn_from_env()) as session:
                persist_heartbeat(session, record.canonical())
        except Exception as exc:  # pragma: no cover
            print(json.dumps({"warn": f"heartbeat persist skipped: {exc.__class__.__name__}"}), file=sys.stderr)
    print(json.dumps(record.canonical(), indent=2, sort_keys=True))
    return 0


def _cmd_backfill(args: Namespace) -> int:
    root, catalog, completions, now = _load_state(args)
    lookback = getattr(args, "lookback_days", None)
    text = render_backfill_markdown(catalog, completions, as_of=now, lookback_days=lookback)
    out = getattr(args, "report_out", None)
    if out is None:
        base = Path(args.out).resolve() if getattr(args, "out", None) else (root / "ops" / "reports" / "scheduler")
        out = base / f"backfill-{now.date().isoformat()}.md"
    else:
        out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    sweep = miss_sweep(catalog, completions, now, lookback_days=lookback)
    payload = {
        "path": str(out),
        "as_of_knowledge": sweep.as_of_knowledge.isoformat(),
        "n_missed": len(sweep.misses),
        "control": "miss_sweep",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if sweep.escalated else 0
