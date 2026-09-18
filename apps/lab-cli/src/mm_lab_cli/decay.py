"""lab decay watch — Phase 6f Quant prompt-hash drift watch. Default --no-send. Zero LLM."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.decay import refuse_forbidden, run_decay_from_fixture, write_decay_artifacts
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_decay_parser(sub) -> None:
    p = sub.add_parser(
        "decay",
        help="run Quant prompt-hash decay watch (default --no-send)",
    )
    scan = p.add_subparsers(dest="decay_cmd")
    sp = scan.add_parser("watch", help="hash versioned prompts/configs; mismatch is a NOTIFY/queue signal")
    sp.add_argument("--fixture", type=Path, required=True, help="frozen decay JSON/YAML")
    sp.add_argument("--repo-root", type=Path, default=Path("."))
    sp.add_argument("--out", type=Path, help="write research/decay/YYYY-MM-DD/ here")
    sp.add_argument("--no-send", action="store_true", help="dry-run (default)")
    sp.add_argument("--no-db", action="store_true", help="fixture-only (default behaviour)")
    sp.add_argument("--waive", action="store_true", help="forbidden")
    sp.add_argument("--merge", action="store_true", help="forbidden")


def dispatch_decay(args: Namespace) -> int:
    if getattr(args, "decay_cmd", None) != "watch":
        print("usage: lab decay watch --fixture PATH --no-send", file=sys.stderr)
        return 2
    for flag, name in ((getattr(args, "merge", False), "merge"), (getattr(args, "waive", False), "waive")):
        if flag:
            print(refuse_forbidden(name), file=sys.stderr)
            return 2
    if SEND_ENABLED:
        print("lab decay watch: SEND_ENABLED must stay false", file=sys.stderr)
        return 2
    try:
        assert_no_send(send_requested=False)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    result = run_decay_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    if args.out:
        written = write_decay_artifacts(result, out_root=Path(args.out).resolve())
    payload = result.as_public_dict()
    payload["written"] = written
    payload["no_send"] = True
    payload["send"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.status != "FAILED" else 2
