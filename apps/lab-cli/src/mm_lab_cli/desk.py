"""lab desk run — Phase 5d orchestration + optional Phase 5e delivery.

Default is --no-send (dry-run payloads only). --send is gated Telegram.
"""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_desks.naming import PIPELINE, publishing_slugs_help, require_publishing_desk
from mm_desks.orchestrator import run_from_fixture, write_dry_run
from mm_delivery.deliver import deliver
from mm_delivery.payload import SEND_ENABLED, assert_no_send


def add_desk_parser(sub) -> None:
    desk = sub.add_parser("desk", help="run desk orchestrator (default --no-send)")
    desk_sub = desk.add_subparsers(dest="desk_cmd")
    run_p = desk_sub.add_parser("run", help="run one desk or --all against a frozen-day fixture")
    run_p.add_argument("--desk", help=f"desk slug: {publishing_slugs_help()}")
    run_p.add_argument("--all", action="store_true", dest="all_desks", help="run Intel→Research→Quant→IC/Risk→Ops")
    run_p.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON/YAML")
    run_p.add_argument("--no-send", action="store_true", help="dry-run payloads only (default)")
    run_p.add_argument("--send", action="store_true", help="gated Telegram send of the Coord pack")
    run_p.add_argument("--out", type=Path, help="write briefs/YYYY-MM-DD dry-run files here")
    run_p.add_argument("--repo-root", type=Path, default=Path("."))
    run_p.add_argument("--workspace", type=Path, help="optional thesis workspace to apply lifecycle writes")
    run_p.add_argument("--no-db", action="store_true", help="fixture-only (default behaviour)")
    run_p.add_argument("--ignore-quiet-hours", action="store_true")


def dispatch_desk(args: Namespace) -> int:
    import sys

    if getattr(args, "desk_cmd", None) != "run":
        print("usage: lab desk run --desk SLUG|--all --fixture PATH [--no-send|--send]", file=sys.stderr)
        return 2
    send = bool(getattr(args, "send", False))
    no_send = bool(getattr(args, "no_send", False))
    if send and no_send:
        print("lab desk run: use --send or --no-send, not both", file=sys.stderr)
        return 2
    if SEND_ENABLED:
        print("lab desk run: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    if not send:
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
    if slug:
        try:
            require_publishing_desk(slug)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
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
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if args.out is not None else None
    if out_root is not None:
        written = write_dry_run(result, out_root=out_root, repo_root=root)
    completeness = 100.0
    for row in result.desks:
        if row.slug == "ops":
            completeness = float(row.completeness_pct)
            break
    delivery = None
    if result.pack_markdown:
        delivery = deliver(
            result.pack_markdown,
            desk="ops",
            as_of=result.as_of_knowledge,
            send=send,
            kind="desk_pack",
            completeness_pct=completeness,
            repo=root,
            out_root=out_root,
            session_date=result.session_date,
            respect_quiet_hours=not bool(getattr(args, "ignore_quiet_hours", False)),
        )
        if delivery.written:
            written.update(delivery.written)
    payload = result.as_public_dict()
    payload["written"] = written
    payload["no_send"] = not send
    payload["send"] = False
    if delivery is not None:
        payload["delivery"] = delivery.as_public_dict()
        payload["telegram_payload_hash"] = delivery.payload_hash
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and (delivery is None or not delivery.sent):
        return 2
    return 0
