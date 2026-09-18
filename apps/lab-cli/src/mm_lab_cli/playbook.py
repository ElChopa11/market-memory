"""lab playbook — Phase 6c artifact ladder. Default --no-send. Zero live LLM."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_desks.playbook import round_trip_envelopes, run_playbook_from_fixture


def add_playbook_parser(sub) -> None:
    p = sub.add_parser("playbook", help="run Hive PLAYBOOK artifact ladder (default --no-send)")
    run_p = p.add_subparsers(dest="playbook_cmd")
    rp = run_p.add_parser("run", help="emit DAILY_BIAS…STATE_CARD for a frozen-day fixture")
    rp.add_argument("--fixture", type=Path, required=True)
    rp.add_argument("--repo-root", type=Path, default=Path("."))
    rp.add_argument("--out", type=Path, help="write artifacts under briefs/YYYY-MM-DD/")
    rp.add_argument("--no-send", action="store_true", help="dry-run (default)")
    rp.add_argument("--no-db", action="store_true")


def dispatch_playbook(args: Namespace) -> int:
    if getattr(args, "playbook_cmd", None) != "run":
        print("usage: lab playbook run --fixture PATH --no-send", file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    result = run_playbook_from_fixture(Path(args.fixture), repo_root=root)
    round_trip_envelopes(result.envelopes)
    if args.out:
        day_dir = Path(args.out).resolve() / "briefs" / result.as_of_knowledge.date().isoformat()
        day_dir.mkdir(parents=True, exist_ok=True)
        (day_dir / "playbook.json").write_text(json.dumps(result.canonical(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (day_dir / "playbook.sha256").write_text(result.content_hash + "\n", encoding="utf-8")
        for digest, png in result.png_by_hash.items():
            (day_dir / f"{digest}.png").write_bytes(png)
    print(json.dumps(result.as_public_dict(), indent=2, sort_keys=True))
    return 0 if result.status != "FAILED" else 2
