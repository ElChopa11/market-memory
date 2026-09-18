"""lab listings scan — Phase 6d Research IPO/listings screen. Default --no-send. Zero LLM."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.listings import run_listings_from_fixture, write_listings_artifacts
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_listings_parser(sub) -> None:
    p = sub.add_parser(
        "listings",
        help="run Research listings / IPO screen (default --no-send)",
    )
    scan = p.add_subparsers(dest="listings_cmd")
    sp = scan.add_parser("scan", help="IPO / direct listing / index-event screen (not a call)")
    sp.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON/YAML")
    sp.add_argument("--repo-root", type=Path, default=Path("."))
    sp.add_argument("--out", type=Path, help="write research/listings/YYYY-MM-DD/ here")
    sp.add_argument("--no-send", action="store_true", help="dry-run (default)")
    sp.add_argument("--no-db", action="store_true", help="fixture-only (default behaviour)")


def dispatch_listings(args: Namespace) -> int:
    if getattr(args, "listings_cmd", None) != "scan":
        print("usage: lab listings scan --fixture PATH --no-send", file=sys.stderr)
        return 2
    if SEND_ENABLED:
        print("lab listings scan: SEND_ENABLED must stay false", file=sys.stderr)
        return 2
    try:
        assert_no_send(send_requested=False)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    result = run_listings_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    if args.out:
        written = write_listings_artifacts(result, out_root=Path(args.out).resolve())
    payload = result.as_public_dict()
    payload["written"] = written
    payload["no_send"] = True
    payload["send"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status != "FAILED" else 2
