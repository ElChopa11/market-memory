"""lab schedule — miss sweep is the scheduler control. Heartbeat-on-fire is a log.

Hybrid Step 4: Hive → lab CLI writes a completion JSON row the miss sweep can
load (ops/reports/scheduler/completions/, optional schedule_heartbeat table).
"""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_desks.completions import load_disk_completions, record_cli_completion, resolve_completions_dir
from mm_desks.scheduler import (
    completion_from_mapping,
    load_catalog,
    load_fixture,
    load_known_missed_baseline,
    miss_sweep,
    parse_baseline_before,
    render_backfill_markdown,
    resolve_baseline_path,
    write_incident_artifact,
    write_known_missed_baseline,
    WrongAnchorError,
)


def add_schedule_parser(sub) -> None:
    sched = sub.add_parser("schedule", help="scheduler miss sweep (control) + completion log")
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

    rec = inner.add_parser("record-fire", help="stamp a completion row (disk always; DB unless --no-db)")
    _add_heartbeat_args(rec)

    beat = inner.add_parser(
        "heartbeat",
        help="Hive/CLI completion writer: run_id, trigger, fire time, offset vs anchor, exit status",
    )
    _add_heartbeat_args(beat)

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


def _add_heartbeat_args(parser) -> None:
    parser.add_argument("--routine-id", required=True)
    parser.add_argument("--fired-at", help="UTC instant (ISO-8601); default now")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--exit-status", type=int, default=0, help="CLI process exit (0=ok; failed is still a fire)")
    parser.add_argument("--payload-path", default="", help="path to briefs/ payload if any")
    parser.add_argument("--cli", default="lab schedule heartbeat")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--completions-dir", type=Path)
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--source", default="lab.cli")


def _add_sweep_args(parser) -> None:
    parser.add_argument("--fixture", type=Path, help="frozen catalog+completions YAML (CI clock)")
    parser.add_argument("--now", help="UTC instant (ISO-8601); fixture clock in CI")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, help="directory for OPEN miss artifact")
    parser.add_argument(
        "--completions-dir",
        type=Path,
        help="load disk completion rows (Hive CLI path). Default: ops/reports/scheduler/completions",
    )
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--lookback-days", type=int, default=None)
    parser.add_argument(
        "--baseline-before",
        help="label closed windows before this Australia/Sydney date as known-missed "
        "(pass 'today' or YYYY-MM-DD). Writes ops/reports/scheduler/known-missed-baseline.yaml",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        help="known-missed baseline path (default: ops/reports/scheduler/known-missed-baseline.yaml)",
    )


def dispatch_schedule(args: Namespace) -> int:
    cmd = getattr(args, "schedule_cmd", None)
    if cmd in {"miss-check", "heartbeat-check", None}:
        if cmd is None:
            print("usage: lab schedule miss-check|heartbeat-check|heartbeat|record-fire|backfill", file=sys.stderr)
            return 2
        return _cmd_miss_check(args)
    if cmd in {"record-fire", "heartbeat"}:
        return _cmd_record_fire(args)
    if cmd == "backfill":
        return _cmd_backfill(args)
    print("usage: lab schedule miss-check|heartbeat-check|heartbeat|record-fire|backfill", file=sys.stderr)
    return 2


def _merge_disk(args: Namespace, root: Path, catalog, completions: list) -> list:
    """Fixture clock stays isolated unless --completions-dir is explicit (tests)."""
    override = getattr(args, "completions_dir", None)
    if getattr(args, "fixture", None) and override is None:
        return completions
    dest = resolve_completions_dir(root, override)
    disk = load_disk_completions(dest, catalog=catalog)
    return [*completions, *disk]


def _load_state(args: Namespace):
    root = Path(args.repo_root).resolve()
    now = parse_utc(args.now) if getattr(args, "now", None) else utcnow()
    if getattr(args, "fixture", None):
        catalog, completions, fixture_now = load_fixture(Path(args.fixture), root=root)
        if fixture_now is not None and not getattr(args, "now", None):
            now = fixture_now
        return root, catalog, _merge_disk(args, root, catalog, list(completions)), now
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
    completions = _merge_disk(args, root, catalog, completions)
    return root, catalog, completions, now


def _cmd_miss_check(args: Namespace) -> int:
    root, catalog, completions, now = _load_state(args)
    cutoff = None
    if getattr(args, "baseline_before", None):
        cutoff = parse_baseline_before(str(args.baseline_before), now)
    baseline_override = getattr(args, "baseline_file", None)
    known = {}
    baseline_path = None
    if getattr(args, "fixture", None) and baseline_override is None and cutoff is None:
        known = {}
    else:
        baseline_path = resolve_baseline_path(root, baseline_override)
        known = load_known_missed_baseline(baseline_path)
    result = miss_sweep(
        catalog,
        completions,
        now,
        lookback_days=getattr(args, "lookback_days", None),
        known_missed=known,
        baseline_before=cutoff,
        baseline_path=baseline_path,
    )
    if cutoff is not None:
        dest = baseline_path or resolve_baseline_path(root, baseline_override)
        write_known_missed_baseline(
            dest,
            now=now,
            cutoff=cutoff,
            windows=result.known_missed,
            existing=known,
        )
        result = miss_sweep(
            catalog,
            completions,
            now,
            lookback_days=getattr(args, "lookback_days", None),
            known_missed=load_known_missed_baseline(dest),
            baseline_before=cutoff,
            baseline_path=dest,
        )
        baseline_path = dest
    artifact = None
    if result.escalated:
        out_dir = Path(args.out).resolve() if getattr(args, "out", None) else (root / "ops" / "reports" / "scheduler" / "incidents")
        artifact = write_incident_artifact(result, out_dir=out_dir)
        result = result.with_artifact(str(artifact))
    payload = result.canonical()
    payload["completions_dir"] = str(resolve_completions_dir(root, getattr(args, "completions_dir", None)))
    if baseline_path is not None:
        payload["baseline_path"] = str(baseline_path)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if result.escalated else 0


def _cmd_record_fire(args: Namespace) -> int:
    root = Path(args.repo_root).resolve()
    fired = parse_utc(str(args.fired_at)) if getattr(args, "fired_at", None) else utcnow()
    try:
        record = record_cli_completion(
            root=root,
            routine_id=str(args.routine_id),
            fired_at=fired,
            run_id=str(args.run_id or "") or None,
            exit_status=int(getattr(args, "exit_status", 0)),
            payload_path=str(getattr(args, "payload_path", "") or "") or None,
            cli=str(getattr(args, "cli", "") or "lab schedule heartbeat"),
            source=str(args.source),
            persist_db=not bool(args.no_db),
            dsn=getattr(args, "dsn", None),
            completions_dir=getattr(args, "completions_dir", None),
        )
    except WrongAnchorError as exc:
        payload = exc.as_public_dict()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "wrote": False}), file=sys.stderr)
        return 2
    dest = resolve_completions_dir(root, getattr(args, "completions_dir", None))
    payload = record.canonical()
    payload["completions_dir"] = str(dest)
    print(json.dumps(payload, indent=2, sort_keys=True))
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
        "completions_dir": str(resolve_completions_dir(root, getattr(args, "completions_dir", None))),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if sweep.escalated else 0
