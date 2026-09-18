"""lab deliver — Phase 5e Telegram delivery. Dry-run default. No live API in pytest."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from mm_common.naming import require_publishing_desk, require_route_slug, route_slugs_help
from mm_common.time import parse_utc, utcnow
from mm_delivery.deliver import deliver
from mm_delivery.inbound import handle_inbound
from mm_delivery.payload import SEND_ENABLED
from mm_desks.orchestrator import PIPELINE, run_from_fixture


def add_deliver_parser(sub) -> None:
    deliver_p = sub.add_parser("deliver", help="deliver a desk pack (default --no-send; Telegram Bot API)")
    deliver_sub = deliver_p.add_subparsers(dest="deliver_cmd")

    pack_p = deliver_sub.add_parser("pack", help="build Telegram payload from an Ops pack or markdown")
    _add_pack_args(pack_p)

    test_p = deliver_sub.add_parser(
        "test",
        help="manual real send of a one-line ping (operator-only; pytest never hits live API)",
    )
    test_p.add_argument("--desk", default="ops", help=f"desk slug (route + TELEGRAM_CHAT_ID[_DESK]); {route_slugs_help()}")
    test_p.add_argument("--repo-root", type=Path, default=Path("."))
    test_p.add_argument("--out", type=Path, help="write payload under briefs/ (default: repo root)")
    test_p.add_argument("--ignore-quiet-hours", action="store_true")
    test_p.add_argument(
        "--i-mean-it",
        action="store_true",
        help="required for a live POST; without it, writes payload only",
    )

    inbound_p = deliver_sub.add_parser("inbound", help="read-only inbound stub (/status /brief /desk /idea /gaps /halt)")
    inbound_p.add_argument("text", help="inbound message text")
    inbound_p.add_argument("--uid", help="telegram user id (unknown uid is a silent drop)")

    fan_p = deliver_sub.add_parser("fanout", help="per-desk deliver + Ops mirror (default --no-send)")
    _add_pack_args(fan_p)

    watch_p = deliver_sub.add_parser(
        "watchlist",
        help="Ops-owned fan-out of a Research watchlist scan (default --no-send)",
    )
    watch_p.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON used by lab watchlist scan")
    watch_p.add_argument("--no-send", action="store_true", help="dry-run (default)")
    watch_p.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    watch_p.add_argument("--out", type=Path, help="write watchlist artifacts + telegram payload")
    watch_p.add_argument("--repo-root", type=Path, default=Path("."))
    watch_p.add_argument("--no-db", action="store_true")
    watch_p.add_argument("--ignore-quiet-hours", action="store_true")

    _add_pack_args(deliver_p)


def _add_pack_args(parser) -> None:
    parser.add_argument("--desk", default="ops", help=f"desk slug to route (default ops; {route_slugs_help()})")
    parser.add_argument("--fixture", type=Path, help="frozen-day fixture; runs desk pipeline then delivers pack")
    parser.add_argument("--from-markdown", type=Path, help="deliver this markdown file instead of a fixture pack")
    parser.add_argument("--as-of", help="UTC as_of_knowledge (required with --from-markdown)")
    parser.add_argument("--no-send", action="store_true", help="dry-run (default)")
    parser.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    parser.add_argument("--out", type=Path, help="write exact payload under briefs/YYYY-MM-DD/")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--ignore-quiet-hours", action="store_true")


def dispatch_deliver(args: Namespace) -> int:
    cmd = getattr(args, "deliver_cmd", None)
    if cmd == "inbound":
        uid = getattr(args, "uid", None)
        allow_uids = None
        if uid is not None:
            # Explicit uid without allowlist → treat as unknown unless it matches itself via env later.
            allow_uids = ()
        reply = handle_inbound(str(args.text), uid=uid, allow_uids=allow_uids if uid else None)
        print(json.dumps(reply.canonical(), sort_keys=True))
        return 0 if reply.ok or reply.silent else 2
    if cmd == "fanout":
        from mm_delivery.fanout import fanout_desk

        send = _want_send(args)
        if send is None:
            return 2
        loaded = _load_source(args, Path(args.repo_root).resolve(), str(getattr(args, "desk", None) or "ops"))
        if loaded is None:
            return 2
        markdown, as_of, completeness, session_date, extra = loaded
        result = fanout_desk(
            markdown,
            desk=str(getattr(args, "desk", None) or "ops"),
            as_of=as_of,
            send=bool(send),
            completeness_pct=completeness,
            repo=Path(args.repo_root).resolve(),
            out_root=Path(args.out).resolve() if getattr(args, "out", None) else Path(args.repo_root).resolve(),
        )
        payload = result.as_public_dict()
        payload.update(extra)
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0
    if cmd == "watchlist":
        return _cmd_watchlist(args)
    if cmd == "test":
        return _cmd_test(args)
    if cmd in {None, "pack"}:
        return _cmd_pack(args)
    print("usage: lab deliver pack|fanout|watchlist|test|inbound", file=sys.stderr)
    return 2


def _want_send(args: Namespace) -> bool | None:
    send = bool(getattr(args, "send", False))
    no_send = bool(getattr(args, "no_send", False))
    if send and no_send:
        print("lab deliver: use --send or --no-send, not both", file=sys.stderr)
        return None
    return send


def _cmd_pack(args: Namespace) -> int:
    send = _want_send(args)
    if send is None:
        return 2
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    root = Path(args.repo_root).resolve()
    desk = str(getattr(args, "desk", None) or "ops")
    loaded = _load_source(args, root, desk)
    if loaded is None:
        return 2
    markdown, as_of, completeness, session_date, extra = loaded
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    result = deliver(
        markdown,
        desk=desk,
        as_of=as_of,
        send=send,
        kind="desk_pack",
        completeness_pct=completeness,
        repo=root,
        out_root=out_root,
        session_date=session_date,
        respect_quiet_hours=not bool(getattr(args, "ignore_quiet_hours", False)),
    )
    payload = result.as_public_dict()
    payload["no_send"] = not send
    payload.update(extra)
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and not result.sent:
        return 2
    return 0


def _cmd_watchlist(args: Namespace) -> int:
    send = _want_send(args)
    if send is None:
        return 2
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    from mm_desks.watchlist import run_watchlist_from_fixture, write_watchlist_artifacts
    from mm_delivery.watchlist import deliver_watchlist

    root = Path(args.repo_root).resolve()
    run = run_watchlist_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    if getattr(args, "out", None):
        written = write_watchlist_artifacts(run, out_root=out_root)
    result = deliver_watchlist(
        run.canonical(),
        as_of=run.as_of_knowledge,
        send=bool(send),
        repo=root,
        out_root=out_root,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not send
    payload["send"] = bool(result.primary.sent)
    payload["publisher"] = "ops"
    payload["product"] = "watchlist"
    payload["n_llm_calls"] = run.llm_calls
    payload["watchlist_content_hash"] = run.content_hash
    payload["written"] = written
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and not result.primary.sent:
        return 2
    return 0 if run.status != "FAILED" else 2


def _cmd_test(args: Namespace) -> int:
    live = bool(getattr(args, "i_mean_it", False))
    root = Path(args.repo_root).resolve()
    desk = str(args.desk)
    as_of = utcnow()
    markdown = (
        "delivery test ping from lab deliver test\n"
        "Not an order. Not Execution. Live trading remains HARD-GATED.\n"
    )
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    result = deliver(
        markdown,
        desk=desk,
        as_of=as_of,
        send=live,
        kind="test",
        completeness_pct=100.0,
        repo=root,
        out_root=out_root,
        session_date=as_of.date().isoformat(),
        respect_quiet_hours=not bool(getattr(args, "ignore_quiet_hours", False)),
    )
    payload = result.as_public_dict()
    payload["no_send"] = not live
    payload["test"] = True
    print(json.dumps(payload, sort_keys=True, indent=2))
    if live and not result.sent:
        return 2
    return 0


def _load_source(args: Namespace, root: Path, desk: str):
    fixture = getattr(args, "fixture", None)
    from_md = getattr(args, "from_markdown", None)
    if bool(fixture) == bool(from_md):
        print("lab deliver pack: require exactly one of --fixture or --from-markdown", file=sys.stderr)
        return None
    if from_md:
        try:
            require_route_slug(desk)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return None
        path = Path(from_md)
        if not path.is_file():
            print(f"markdown not found: {path}", file=sys.stderr)
            return None
        as_of_raw = getattr(args, "as_of", None)
        if not as_of_raw:
            print("lab deliver --from-markdown requires --as-of", file=sys.stderr)
            return None
        as_of = parse_utc(str(as_of_raw))
        markdown = path.read_text(encoding="utf-8")
        return markdown, as_of, 100.0, as_of.date().isoformat(), {}
    try:
        require_publishing_desk(desk)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return None
    result = run_from_fixture(
        Path(fixture),
        repo_root=root,
        slugs=PIPELINE,
        send=False,
    )
    markdown = result.pack_markdown or ""
    if desk != "ops":
        for row in result.desks:
            if row.slug != desk:
                continue
            for art in row.artifacts:
                if art.kind == "markdown" and art.content:
                    markdown = art.content
                    break
    completeness = 100.0
    for row in result.desks:
        if row.slug == desk or (desk == "ops" and row.slug == "ops"):
            completeness = float(row.completeness_pct)
            break
    extra = {"fixture_id": result.fixture_id, "desk_content_hash": result.content_hash}
    return markdown, result.as_of_knowledge, completeness, result.session_date, extra
