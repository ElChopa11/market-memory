"""lab scorecard compare — Phase 6e Quant like-for-like pack scoring. Default --no-send. Zero LLM."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.scorecard import run_scorecard_from_fixture, write_scorecard_artifacts
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_scorecard_parser(sub) -> None:
    p = sub.add_parser(
        "scorecard",
        help="run Quant like-for-like pack scorecard (default --no-send)",
    )
    scan = p.add_subparsers(dest="scorecard_cmd")
    sp = scan.add_parser("compare", help="score packs like-for-like; tag incomparable (not a call)")
    sp.add_argument("--fixture", type=Path, required=True, help="frozen pack JSON/YAML")
    sp.add_argument("--repo-root", type=Path, default=Path("."))
    sp.add_argument("--out", type=Path, help="write research/scorecards/YYYY-MM-DD/ here")
    sp.add_argument("--no-send", action="store_true", help="dry-run (default)")
    sp.add_argument("--no-db", action="store_true", help="fixture-only (default behaviour)")


def dispatch_scorecard(args: Namespace) -> int:
    if getattr(args, "scorecard_cmd", None) != "compare":
        print("usage: lab scorecard compare --fixture PATH --no-send", file=sys.stderr)
        return 2
    if SEND_ENABLED:
        print("lab scorecard compare: SEND_ENABLED must stay false", file=sys.stderr)
        return 2
    try:
        assert_no_send(send_requested=False)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    result = run_scorecard_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    if args.out:
        written = write_scorecard_artifacts(result, out_root=Path(args.out).resolve())
    payload = result.as_public_dict()
    payload["written"] = written
    payload["no_send"] = True
    payload["send"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status != "FAILED" else 2
