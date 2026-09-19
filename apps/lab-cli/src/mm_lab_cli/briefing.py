"""Market Pulse CLI: lab brief preopen|close|alert-check. No trading credentials."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_briefing.config import AlertSettings, load_alert_settings, load_briefing_settings
from mm_briefing.engine import default_macro_fetcher, generate_from_sources, load_fixture_file
from mm_briefing.store import index_brief, write_brief
from mm_lab_cli.completion import add_completion_args, fired_at_from_args, stamp_cli_fire
from mm_lab_cli.env_preflight import prepare_brief
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
        p.add_argument("--out", type=Path, help="repo root to write briefs/")
        p.add_argument("--repo-root", type=Path, default=Path("."))
        p.add_argument("--dsn")
        p.add_argument("--no-db", action="store_true")
        p.add_argument(
            "--live",
            action="store_true",
            help="fetch public macro + Hyperliquid /info (degrade to unavailable; never invent)",
        )
        p.add_argument(
            "--no-thresholds",
            action="store_true",
            help="(tests) run alert-check with empty thresholds; must not push",
        )
        add_completion_args(p)


def dispatch_brief(args: Namespace) -> int:
    cmd = args.brief_cmd
    if cmd is None:
        print("usage: lab brief preopen|close|alert-check")
        return 2
    kind = {"preopen": "preopen", "close": "close", "alert-check": "alert"}[cmd]
    fired_at = fired_at_from_args(args)
    rc = 2
    payload_path = None
    try:
        rc, payload_path = _run_brief(args, kind)
    except Exception as exc:
        print(json.dumps({"error": exc.__class__.__name__, "detail": str(exc)}))
        rc = 2
    finally:
        stamp_cli_fire(
            args,
            exit_status=rc,
            payload_path=payload_path,
            brief_kind=kind if kind != "alert" else None,
            cli=f"lab brief {cmd}",
            fired_at=fired_at,
            source="lab.brief",
        )
    return rc


def _run_brief(args: Namespace, kind: str) -> tuple[int, str | None]:
    prepare_brief()
    root = Path(args.repo_root).resolve()
    settings = load_briefing_settings(root)
    fixture = load_fixture_file(args.fixture) if args.fixture else None
    as_of = parse_utc(args.as_of) if args.as_of else utcnow()
    live = bool(getattr(args, "live", False)) and fixture is None
    generated_at = utcnow() if live else None
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
            generated_at=generated_at,
            alert_settings=alert_settings,
            live=live,
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
            return 0, None
        path = _persist(doc, args, root)
        payload["path"] = str(path)
        payload["content_hash"] = doc.content_hash
        print(json.dumps(payload, indent=2))
        return 0, str(path)

    assert doc is not None
    path = _persist(doc, args, root)
    from mm_briefing.store import artifact_relpath, dod_relpath

    payload = {
        "kind": doc.kind,
        "session_date": doc.session_date.isoformat(),
        "path": str(path),
        "legacy_path": str((Path(args.out).resolve() if args.out else root) / artifact_relpath(doc)),
        "content_hash": doc.content_hash,
        "data_quality": doc.data_quality,
    }
    dod = dod_relpath(doc)
    if dod is not None:
        payload["dod_path"] = str((Path(args.out).resolve() if args.out else root) / dod)
    print(json.dumps(payload, indent=2))
    return 0, str(path)


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
