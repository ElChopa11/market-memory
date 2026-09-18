"""lab queue — Phase 6e improvement-queue hygiene. Read-only. No auto-merge / no gate waiver."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.queue import can_start, load_queue, refuse_forbidden


def add_queue_parser(sub) -> None:
    p = sub.add_parser(
        "queue",
        help="improvement-queue hygiene (read-only; no auto-merge)",
    )
    q = p.add_subparsers(dest="queue_cmd")
    check = q.add_parser("check", help="parse ops/improvement-queue.md; fail on dual IN_PROGRESS")
    check.add_argument("--repo-root", type=Path, default=Path("."))
    start = q.add_parser(
        "can-start",
        help="READY→IN_PROGRESS aid (does not write the queue; does not waive gates)",
    )
    start.add_argument("item_id", help="IMP-XXX")
    start.add_argument("--repo-root", type=Path, default=Path("."))
    for forbidden in ("merge", "waive"):
        banned = q.add_parser(forbidden, help="refused")
        banned.add_argument("--repo-root", type=Path, default=Path("."))


def dispatch_queue(args: Namespace) -> int:
    cmd = getattr(args, "queue_cmd", None)
    blocked = refuse_forbidden(cmd)
    if blocked:
        print(blocked, file=sys.stderr)
        return 2
    root = Path(getattr(args, "repo_root", Path("."))).resolve()
    report = load_queue(root)
    payload = report.as_public_dict()
    if cmd == "can-start":
        ok, reason = can_start(str(args.item_id), report)
        payload["can_start"] = {"id": args.item_id, "ok": ok, "reason": reason}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if ok and report.ok else 2
    if cmd in {None, "check"}:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if report.ok else 2
    print("usage: lab queue check | lab queue can-start IMP-XXX", file=sys.stderr)
    return 2
