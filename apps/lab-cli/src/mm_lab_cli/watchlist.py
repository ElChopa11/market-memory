"""lab watchlist scan — Phase 6c-4 Research daily scan. Default --no-send. Zero LLM."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.watchlist import run_watchlist_from_fixture, write_watchlist_artifacts
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_watchlist_parser(sub) -> None:
    p = sub.add_parser(
        "watchlist",
        help="run Research watchlist monitor over locked universe (default --no-send)",
    )
    scan = p.add_subparsers(dest="watchlist_cmd")
    sp = scan.add_parser("scan", help="daily scan of in_universe ∪ watch_only (not a call)")
    sp.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON/YAML")
    sp.add_argument("--repo-root", type=Path, default=Path("."))
    sp.add_argument("--out", type=Path, help="write research/watchlist/YYYY-MM-DD/ here")
    sp.add_argument("--no-send", action="store_true", help="dry-run (default)")
    sp.add_argument("--no-db", action="store_true", help="fixture-only (default behaviour)")


def dispatch_watchlist(args: Namespace) -> int:
    if getattr(args, "watchlist_cmd", None) != "scan":
        print("usage: lab watchlist scan --fixture PATH --no-send", file=sys.stderr)
        return 2
    if SEND_ENABLED:
        print("lab watchlist scan: SEND_ENABLED must stay false", file=sys.stderr)
        return 2
    try:
        assert_no_send(send_requested=False)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    result = run_watchlist_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    if args.out:
        written = write_watchlist_artifacts(result, out_root=Path(args.out).resolve())
    payload = result.as_public_dict()
    payload["written"] = written
    payload["no_send"] = True
    payload["send"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status != "FAILED" else 2
