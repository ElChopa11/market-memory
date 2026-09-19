"""lab data source-health / lab dq report — read-only Data desk product."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_common.time import utcnow
from mm_lab_cli.edgar import add_edgar_parser, cmd_edgar
from mm_source_health.engine import generate_source_health
from mm_source_health.probes import DEFAULT_TIMEOUT
from mm_source_health.store import write_source_health_report


def _add_health_args(parser) -> None:
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="repo root (config + ops/reports)")
    parser.add_argument("--out", type=Path, help="root to write ops/reports/ (default: --repo-root)")
    parser.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN); never printed")
    parser.add_argument("--no-db", action="store_true", help="skip Postgres reachability probe")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP/DB timeout seconds")
    parser.add_argument("--as-of", help="UTC instant for generated_at (ISO-8601); default now")


def add_source_health_parser(sub) -> None:
    data = sub.add_parser("data", help="Data & Market Memory desk commands (read-only)")
    data_sub = data.add_subparsers(dest="data_cmd")
    health = data_sub.add_parser("source-health", help="standing source-health / data-quality report")
    _add_health_args(health)
    add_edgar_parser(data_sub)

    dq = sub.add_parser("dq", help="data-quality aliases")
    dq_sub = dq.add_subparsers(dest="dq_cmd")
    report = dq_sub.add_parser("report", help="alias for lab data source-health")
    _add_health_args(report)


def dispatch_source_health(args: Namespace) -> int:
    cmd = getattr(args, "data_cmd", None) or getattr(args, "dq_cmd", None)
    if args.cmd == "data" and cmd is None:
        print("usage: lab data source-health")
        return 2
    if args.cmd == "dq" and cmd is None:
        print("usage: lab dq report")
        return 2
    if cmd == "edgar":
        return cmd_edgar(args)
    if cmd not in {"source-health", "report"}:
        print("usage: lab data source-health | lab data edgar | lab dq report")
        return 2
    return cmd_source_health(args)


def cmd_source_health(args: Namespace) -> int:
    from mm_common.time import parse_utc

    repo_root = Path(args.repo_root).resolve()
    out_root = Path(args.out).resolve() if args.out else repo_root
    command = "lab dq report" if args.cmd == "dq" else "lab data source-health"
    generated_at = parse_utc(args.as_of) if args.as_of else utcnow()
    report = generate_source_health(
        repo_root=repo_root,
        captured_at=generated_at,
        timeout=float(args.timeout),
        skip_db=bool(args.no_db),
        dsn=args.dsn,
        command=command,
    )
    path = write_source_health_report(report, root=out_root)
    try:
        rel = str(path.relative_to(out_root))
    except ValueError:
        rel = str(path)
    print(
        json.dumps(
            {
                "command": command,
                "path": rel,
                "content_hash": report.content_hash,
                "overall": report.overall,
                "generated_at": report.generated_at.isoformat(),
                "sources": [
                    {
                        "id": row.source_id,
                        "status": row.status,
                        "pulse_role": row.pulse_role,
                        "error_class": row.error_class,
                        "latency_ms": row.latency_ms,
                        "credentials_present": row.credentials_present,
                        "last_success_at": row.last_success_at.isoformat() if row.last_success_at else None,
                    }
                    for row in report.sources
                ],
            }
        )
    )
    return 0
