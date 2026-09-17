"""Market Pulse worker. Must not execute trades. Alerts require thresholds."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import default_macro_fetcher, generate_from_sources, load_fixture_file
from mm_briefing.schedule import fires_between, next_fire
from mm_briefing.store import index_brief, write_brief
from mm_memory.db import dsn_from_env, session_scope

__phase__ = 3
LIVE_TRADING_ENABLED = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="briefing-worker", description="Market Pulse worker (no trading)")
    sub = parser.add_subparsers(dest="cmd")

    once = sub.add_parser("once", help="generate one brief or alert-check")
    _add_gen_args(once)

    nxt = sub.add_parser("next", help="print the next DST-aware fire times")
    nxt.add_argument("--from", dest="start", help="UTC instant (default now)")
    nxt.add_argument("--days", type=int, default=7)

    run = sub.add_parser("run", help="sleep until the next preopen/close fire and generate")
    run.add_argument("--once", action="store_true", help="exit after one fire (tests / supervised loops)")
    run.add_argument("--fixture", type=Path)
    run.add_argument("--out", type=Path)
    run.add_argument("--dsn")
    run.add_argument("--no-db", action="store_true")
    run.add_argument("--poll-seconds", type=float, default=30.0)

    args = parser.parse_args(argv)
    if args.cmd == "once":
        return cmd_once(args)
    if args.cmd == "next":
        return cmd_next(args)
    if args.cmd == "run":
        return cmd_run(args)
    parser.print_help()
    return 2


def _add_gen_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kind", required=True, choices=("preopen", "close", "alert"))
    parser.add_argument("--as-of", help="UTC instant (ISO-8601)")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--out", type=Path, help="repo root to write briefs/ into")
    parser.add_argument("--dsn")
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path("."))


def cmd_once(args: argparse.Namespace) -> int:
    settings = load_briefing_settings(Path(args.repo_root).resolve() if args.repo_root else None)
    fixture = load_fixture_file(args.fixture) if args.fixture else None
    as_of = parse_utc(args.as_of) if args.as_of else utcnow()
    live = bool(getattr(args, "live", False)) and fixture is None
    generated_at = utcnow() if live else None
    fetcher = default_macro_fetcher(settings, fixture)
    session_cm = None
    session = None
    if not args.no_db and fixture is None:
        session_cm = session_scope(args.dsn or dsn_from_env())
        session = session_cm.__enter__()
    try:
        doc, decision = generate_from_sources(
            args.kind,
            settings=settings,
            as_of=as_of,
            macro_fetcher=fetcher,
            session=session,
            fixture=fixture,
            generated_at=generated_at,
            live=live,
        )
    finally:
        if session_cm is not None:
            session_cm.__exit__(None, None, None)

    if args.kind == "alert":
        payload = {
            "pushed": bool(decision.pushed) if decision else False,
            "reason": decision.reason if decision else "no_decision",
            "count": len(decision.events) if decision else 0,
        }
        if doc is None:
            print(json.dumps(payload, indent=2))
            return 0
        path = _write(doc, args)
        payload["path"] = str(path)
        payload["content_hash"] = doc.content_hash
        print(json.dumps(payload, indent=2))
        return 0

    assert doc is not None
    path = _write(doc, args)
    print(
        json.dumps(
            {
                "kind": doc.kind,
                "session_date": doc.session_date.isoformat(),
                "path": str(path),
                "content_hash": doc.content_hash,
                "data_quality": doc.data_quality,
            },
            indent=2,
        )
    )
    return 0


def _write(doc, args: argparse.Namespace) -> Path:
    root = Path(args.out or args.repo_root or ".").resolve()
    path = write_brief(doc, root=root)
    if not args.no_db:
        try:
            with session_scope(args.dsn or dsn_from_env()) as session:
                index_brief(session, doc, artifact_path=path, root=root)
        except Exception as exc:  # pragma: no cover - index is optional
            print(json.dumps({"warn": f"brief index skipped: {exc.__class__.__name__}"}), file=sys.stderr)
    return path


def cmd_next(args: argparse.Namespace) -> int:
    settings = load_briefing_settings()
    start = parse_utc(args.start) if args.start else utcnow()
    from datetime import timedelta

    rows = fires_between(start, start + timedelta(days=args.days), settings.schedule)
    payload = [
        {
            "kind": row.kind,
            "utc": row.when_utc.isoformat(),
            "session": row.when_session.isoformat(),
            "lab": row.when_lab.isoformat(),
            "session_date": row.session_date.isoformat(),
        }
        for row in rows
    ]
    nxt = next_fire(start, settings.schedule)
    print(
        json.dumps(
            {
                "from": start.isoformat(),
                "next": None
                if nxt is None
                else {
                    "kind": nxt.kind,
                    "utc": nxt.when_utc.isoformat(),
                    "session": nxt.when_session.isoformat(),
                    "lab": nxt.when_lab.isoformat(),
                },
                "fires": payload,
            },
            indent=2,
        )
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Supervised loop. Tests should pass --once with a fixture rather than sleeping."""
    settings = load_briefing_settings()
    now = utcnow()
    fire = next_fire(now, settings.schedule)
    if fire is None:
        print(json.dumps({"error": "no fire in horizon"}))
        return 1
    delay = (fire.when_utc - now).total_seconds()
    if delay > 0 and not args.once:
        time.sleep(min(delay, max(args.poll_seconds, 0)))
        return cmd_run(args)
    ns = argparse.Namespace(
        kind=fire.kind,
        as_of=fire.when_utc.isoformat(),
        fixture=args.fixture,
        out=args.out,
        dsn=args.dsn,
        no_db=args.no_db,
        repo_root=Path("."),
    )
    return cmd_once(ns)


if __name__ == "__main__":
    sys.exit(main())
