"""lab desk run — Phase 5d orchestration. Fixture-only. --no-send. No Telegram."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_desks.orchestrator import PIPELINE, run_from_fixture, write_dry_run
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_desk_parser(sub) -> None:
    desk = sub.add_parser("desk", help="run desk orchestrator (Phase 5d; --no-send)")
    desk_sub = desk.add_subparsers(dest="desk_cmd")
    run_p = desk_sub.add_parser("run", help="run one desk or --all against a frozen-day fixture")
    run_p.add_argument("--desk", help="desk slug: intel|crypto|equities|quant|skeptic|risk|coord")
    run_p.add_argument("--all", action="store_true", dest="all_desks", help="run Intel→3a|3b→Quant→Skeptic→Risk→Coord")
    run_p.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON/YAML")
    run_p.add_argument("--no-send", action="store_true", help="dry-run payloads only (required in 5d; send is 5e)")
    run_p.add_argument("--send", action="store_true", help="forbidden in Phase 5d")
    run_p.add_argument("--out", type=Path, help="write briefs/YYYY-MM-DD dry-run files here")
    run_p.add_argument("--repo-root", type=Path, default=Path("."))
    run_p.add_argument("--workspace", type=Path, help="optional thesis workspace to apply lifecycle writes")
    run_p.add_argument("--no-db", action="store_true", help="fixture-only (default behaviour in 5d)")


def dispatch_desk(args: Namespace) -> int:
    import sys

    if getattr(args, "desk_cmd", None) != "run":
        print("usage: lab desk run --desk SLUG|--all --fixture PATH --no-send", file=sys.stderr)
        return 2
    if bool(getattr(args, "send", False)):
        print("lab desk run: Telegram send is Phase 5e; pass --no-send", file=sys.stderr)
        return 2
    if SEND_ENABLED:
        print("lab desk run: SEND_ENABLED must stay false in Phase 5d", file=sys.stderr)
        return 2
    try:
        assert_no_send(send_requested=False)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    slug = getattr(args, "desk", None)
    all_desks = bool(getattr(args, "all_desks", False))
    if all_desks and slug:
        print("lab desk run: use --desk SLUG or --all, not both", file=sys.stderr)
        return 2
    if not all_desks and not slug:
        print("lab desk run: require --desk SLUG or --all", file=sys.stderr)
        return 2
    if slug and slug not in PIPELINE:
        print(f"unknown desk {slug!r}; choose from {', '.join(PIPELINE)}", file=sys.stderr)
        return 2
    slugs = PIPELINE if all_desks else (slug,)
    root = Path(args.repo_root).resolve()
    result = run_from_fixture(
        Path(args.fixture),
        repo_root=root,
        slugs=slugs,
        workspace=Path(args.workspace).resolve() if getattr(args, "workspace", None) else None,
        send=False,
    )
    written = {}
    if args.out is not None:
        written = write_dry_run(result, out_root=Path(args.out).resolve())
    payload = result.as_public_dict()
    payload["written"] = written
    payload["no_send"] = True
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0
