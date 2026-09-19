"""lab base-rate compute — Phase 1 unconditional event-class rates. Default --no-db. Zero LLM."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.base_rates import run_base_rates_from_fixture, write_base_rate_artifacts
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_base_rate_parser(sub) -> None:
    p = sub.add_parser(
        "base-rate",
        help="compute unconditional event-class base rates (default --no-db; paper only)",
    )
    scan = p.add_subparsers(dest="base_rate_cmd")
    sp = scan.add_parser("compute", help="dip / zone-boundary / first-entry EMA rates (not a candidate study)")
    sp.add_argument("--fixture", type=Path, required=True, help="frozen OHLCV panel JSON")
    sp.add_argument("--repo-root", type=Path, default=Path("."))
    sp.add_argument("--out", type=Path, help="write research/quant/base-rates/YYYY-MM-DD/ here")
    sp.add_argument("--no-send", action="store_true", help="dry-run (default)")
    sp.add_argument("--no-db", action="store_true", help="fixture artifacts only (default behaviour)")
    sp.add_argument("--dsn", help="optional Postgres DSN to persist event_base_rate rows")


def dispatch_base_rate(args: Namespace) -> int:
    if getattr(args, "base_rate_cmd", None) != "compute":
        print("usage: lab base-rate compute --fixture PATH --no-db", file=sys.stderr)
        return 2
    if SEND_ENABLED:
        print("lab base-rate compute: SEND_ENABLED must stay false", file=sys.stderr)
        return 2
    try:
        assert_no_send(send_requested=False)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    result = run_base_rates_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if args.out else root
    written = write_base_rate_artifacts(result, out_root=out_root)
    persisted: list[str] = []
    if args.dsn and not args.no_db:
        from mm_memory.base_rate_repository import persist_memory_rows
        from mm_memory.db import session_scope

        with session_scope(args.dsn) as session:
            persisted = persist_memory_rows(session, result.canonical()["memory_rows"])
    payload = result.as_public_dict()
    payload["written"] = written
    payload["persisted_ids"] = persisted
    payload["no_send"] = True
    payload["send"] = False
    payload["no_db"] = bool(args.no_db or not args.dsn)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status != "FAILED" else 2
