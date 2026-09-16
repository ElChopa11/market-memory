"""Market Pulse CLI: lab brief preopen|close|alert-check. No trading credentials."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_briefing.config import AlertSettings, load_alert_settings, load_briefing_settings
from mm_briefing.engine import default_macro_fetcher, generate_from_sources, load_fixture_file
from mm_briefing.store import index_brief, write_brief
from mm_memory.db import dsn_from_env, session_scope


def add_brief_parser(sub) -> None:
    brief = sub.add_parser("brief", help="generate Market Pulse briefs")
    brief_sub = brief.add_subparsers(dest="brief_cmd")
    for name, help_text in (
        ("preopen", "US pre-market/open brief"),
        ("close", "US close brief"),
        ("alert-check", "threshold-gated intraday alert check (no spam)"),
    ):
        p = brief_sub.add_parser(name, help=help_text)
        p.add_argument("--as-of", help="UTC instant (ISO-8601)")
        p.add_argument("--fixture", type=Path, help="frozen JSON/YAML briefing fixture")
        p.add_argument("--out", type=Path, help="repo root to write briefs/YYYY/MM/DD/")
        p.add_argument("--repo-root", type=Path, default=Path("."))
        p.add_argument("--dsn")
        p.add_argument("--no-db", action="store_true")
        p.add_argument(
            "--no-thresholds",
            action="store_true",
            help="(tests) run alert-check with empty thresholds; must not push",
        )


def dispatch_brief(args: Namespace) -> int:
    cmd = args.brief_cmd
    if cmd is None:
        print("usage: lab brief preopen|close|alert-check")
        return 2
    kind = {"preopen": "preopen", "close": "close", "alert-check": "alert"}[cmd]
    root = Path(args.repo_root).resolve()
    settings = load_briefing_settings(root)
    fixture = load_fixture_file(args.fixture) if args.fixture else None
    as_of = parse_utc(args.as_of) if args.as_of else utcnow()
    fetcher = default_macro_fetcher(settings, fixture)
    alert_settings = None
    if kind == "alert" and getattr(args, "no_thresholds", False):
        alert_settings = AlertSettings(
            enabled=True,
            require_threshold_config=True,
            interval_minutes=15,
            types=(),
        )
    elif kind == "alert":
        alert_settings = load_alert_settings(root / "config" / "briefing" / "alerts.yaml")

    session_cm = None
    session = None
    if not args.no_db and fixture is None:
        session_cm = session_scope(args.dsn or dsn_from_env())
        session = session_cm.__enter__()
    try:
        doc, decision = generate_from_sources(
            kind,
            settings=settings,
            as_of=as_of,
            macro_fetcher=fetcher,
            session=session,
            fixture=fixture,
            alert_settings=alert_settings,
        )
    finally:
        if session_cm is not None:
            session_cm.__exit__(None, None, None)

    if kind == "alert":
        payload = {
            "pushed": bool(decision.pushed) if decision else False,
            "reason": decision.reason if decision else "no_decision",
            "count": len(decision.events) if decision else 0,
        }
        if doc is None:
            print(json.dumps(payload, indent=2))
            return 0
        path = _persist(doc, args, root)
        payload["path"] = str(path)
        payload["content_hash"] = doc.content_hash
        print(json.dumps(payload, indent=2))
        return 0

    assert doc is not None
    path = _persist(doc, args, root)
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


def _persist(doc, args: Namespace, root: Path) -> Path:
    out_root = Path(args.out).resolve() if args.out else root
    path = write_brief(doc, root=out_root)
    if not args.no_db:
        try:
            with session_scope(args.dsn or dsn_from_env()) as session:
                index_brief(session, doc, artifact_path=path, root=out_root)
        except Exception as exc:  # pragma: no cover
            print(json.dumps({"warn": f"brief index skipped: {exc.__class__.__name__}"}))
    return path
