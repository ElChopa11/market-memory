"""Coordinator CLI: status, migrate, ingest, research, briefs, backtest, paper ledger, source-health, equities screen.

Must not hold trading credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_lab_cli.backtest import add_backtest_parser, dispatch_backtest
from mm_lab_cli.briefing import add_brief_parser, dispatch_brief
from mm_lab_cli.deliver import add_deliver_parser, dispatch_deliver
from mm_lab_cli.desk import add_desk_parser, dispatch_desk
from mm_lab_cli.mesh import add_mesh_parser, dispatch_mesh
from mm_lab_cli.playbook import add_playbook_parser, dispatch_playbook
from mm_lab_cli.watchlist import add_watchlist_parser, dispatch_watchlist
from mm_lab_cli.paper import dispatch_paper, add_paper_parser
from mm_lab_cli.equities import add_equities_parser, dispatch_equities
from mm_lab_cli.quant_review import add_quant_review_parser, dispatch_quant_review
from mm_lab_cli.research import dispatch_skeptic, dispatch_thesis, run_research_command
from mm_lab_cli.source_health import add_source_health_parser, dispatch_source_health
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.migrate import current_revision, upgrade_head
from mm_memory.queries import what_did_we_know


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lab", description="market-memory coordinator CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="show phase and hard-gates")
    sub.add_parser("migrate", help="apply Alembic migrations to Postgres")

    ingest = sub.add_parser("ingest", help="read-only public ingest (HL /info, Polygon, FRED/calendar)")
    ingest.add_argument("--window", default="7d", help="lookback window, e.g. 7d, 24h")
    ingest.add_argument("--start", help="UTC start instant (ISO-8601)")
    ingest.add_argument("--end", help="UTC end instant (ISO-8601)")
    ingest.add_argument("--fixture", type=Path, help="JSON/YAML fixture instead of live HTTP")
    ingest.add_argument("--no-objects", action="store_true", help="do not write raw payloads to MinIO/S3")
    ingest.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN)")
    ingest.add_argument(
        "--no-db",
        action="store_true",
        help="dry-run: normalize fixture envelopes without Postgres or object store",
    )

    know = sub.add_parser("what-did-we-know", help="point-in-time observations (as_of_knowledge <= T)")
    know.add_argument("--at", required=True, help="UTC instant (ISO-8601)")
    know.add_argument("--instrument", help="filter by instrument (locked HL perps: BTC, ETH, UNI, AAVE)")
    know.add_argument("--metric", help="filter metric name")
    know.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN)")
    know.add_argument("--limit", type=int, default=50)

    thesis = sub.add_parser("thesis", help="create and advance research thesis workspaces")
    thesis_sub = thesis.add_subparsers(dest="thesis_cmd")
    new_p = thesis_sub.add_parser("new", help="create a thesis workspace from intent (one command)")
    new_p.add_argument("--goal", help="intent goal (one sentence); required unless --from-intent")
    new_p.add_argument("--from-intent", help="path to an existing intent.md")
    new_p.add_argument("--owner", default="Research")
    new_p.add_argument("--why-now", default="no observation yet")
    new_p.add_argument("--out-of-scope", default="live trading; execution; Market Pulse")
    new_p.add_argument("--instrument", default="BTC")
    new_p.add_argument("--horizon", default="")
    new_p.add_argument("--deadline", default="")
    new_p.add_argument("--hypothesis", default="")
    _add_research_common(new_p)

    link_p = thesis_sub.add_parser("link-evidence", help="link an observation id to a thesis")
    link_p.add_argument("slug", help="THESIS-XXXX or workspace path")
    link_p.add_argument("--observation", required=True, dest="observation")
    link_p.add_argument("--role", default="supports", help="supports|opposes|context")
    link_p.add_argument("--notes", default="")
    _add_research_common(link_p)

    adv = thesis_sub.add_parser("advance", help="advance lifecycle status when DoD is met")
    adv.add_argument("slug")
    adv.add_argument("--to", required=True, help="draft|in_research|in_skeptic|paper|rejected|retired")
    _add_research_common(adv)

    list_p = thesis_sub.add_parser("list", help="list theses (rejected remain queryable)")
    list_p.add_argument("--status", help="filter status (rejected is a first-class filter)")
    _add_research_common(list_p)

    show_p = thesis_sub.add_parser("show")
    show_p.add_argument("slug")
    _add_research_common(show_p)

    skeptic = sub.add_parser("skeptic", help="open or record an independent skeptic review")
    skeptic_sub = skeptic.add_subparsers(dest="skeptic_cmd")
    open_p = skeptic_sub.add_parser("open", help="enter in_skeptic (requires evidence links)")
    open_p.add_argument("slug")
    open_p.add_argument("--reviewer", required=True)
    _add_research_common(open_p)

    rec = skeptic_sub.add_parser("record", help="record verdict: pass|revise|reject")
    rec.add_argument("slug")
    rec.add_argument("--verdict", required=True, choices=("pass", "revise", "reject"))
    rec.add_argument("--reviewer", required=True)
    rec.add_argument("--findings", default="")
    _add_research_common(rec)

    add_brief_parser(sub)
    add_desk_parser(sub)
    add_mesh_parser(sub)
    add_deliver_parser(sub)
    add_playbook_parser(sub)
    add_watchlist_parser(sub)
    add_backtest_parser(sub)
    add_paper_parser(sub)
    add_quant_review_parser(sub)
    add_source_health_parser(sub)
    add_equities_parser(sub)

    args = parser.parse_args(argv)
    if args.cmd is None or args.cmd == "status":
        return cmd_status()
    if args.cmd == "migrate":
        return cmd_migrate()
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "what-did-we-know":
        return cmd_what_did_we_know(args)
    if args.cmd == "thesis":
        return run_research_command(dispatch_thesis, args)
    if args.cmd == "skeptic":
        return run_research_command(dispatch_skeptic, args)
    if args.cmd == "brief":
        return dispatch_brief(args)
    if args.cmd == "desk":
        return dispatch_desk(args)
    if args.cmd == "mesh":
        return dispatch_mesh(args)
    if args.cmd == "deliver":
        return dispatch_deliver(args)
    if args.cmd == "playbook":
        return dispatch_playbook(args)
    if args.cmd == "watchlist":
        return dispatch_watchlist(args)
    if args.cmd == "backtest":
        return dispatch_backtest(args)
    if args.cmd == "paper":
        return dispatch_paper(args)
    if args.cmd == "quant-review":
        return dispatch_quant_review(args)
    if args.cmd in {"data", "dq"}:
        return dispatch_source_health(args)
    if args.cmd == "equities":
        return dispatch_equities(args)
    parser.print_help()
    return 2


def _add_research_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--research-root", type=Path, default=Path("research"))
    parser.add_argument("--templates-root", type=Path, default=Path("templates"))
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN)")
    parser.add_argument("--no-db", action="store_true", help="git artifacts only (no Market Memory index)")


def cmd_status() -> int:
    print("market-memory lab CLI (Phase 6 in progress — 6c-4 watchlist monitor on five-desk roster; 6c-2 naming + 6c PLAYBOOK on main; Phase 5 complete; Phase 4 backtest/paper remain)")
    print("Live trading: HARD-GATED")
    print("Research cannot access trading credentials.")
    print("research_kit writes git artifacts only; it does not import execution or ingest private keys.")
    print("Ingest: Hyperliquid public /info + Polygon (POLYGON_API_KEY env) + FRED/calendar. No signing, no private keys.")
    print("Equities vendor: polygon (Principal lock; Ask is N/A). Missing POLYGON_API_KEY → unavailable, never invent.")
    print("Point-in-time: what_did_we_know(T) uses as_of_knowledge <= T (lockstep with ingested_at). published_at and market_time never gate knowledge.")
    print("Theses: lab thesis new | link-evidence | advance ; lab skeptic open | record")
    print("Briefs: lab brief preopen | close | alert-check (alerts require threshold config)")
    print("Backtest: lab backtest run --fixture PATH (same params_hash → same result)")
    print("Paper: lab paper open|close|list (cannot open without invalidation + max loss)")
    print("Quant review: lab quant-review --fixture PATH --no-db (decision board; not a call generator)")
    print("Source health: lab data source-health (alias: lab dq report) — ops/reports/source-health/")
    print("Equities screen: lab equities reclaim-screen --fixture PATH --no-db (Post-IPO / reclaim triage; not a trading decision)")
    print("Desk run: lab desk run --all --fixture PATH --no-send (deterministic pack; default dry-run)")
    from mm_common.naming import roster_lines

    print("Publishing desks: " + "; ".join(roster_lines()) + ". Coord is orchestration only.")
    print("Mesh: lab mesh dry --fixture PATH --no-db (PG NOTIFY bus; --kill-desk leaves FAILED + error_class)")
    print("Deliver: lab deliver pack --fixture PATH --no-send | lab deliver test --desk SLUG (live send only with --i-mean-it)")
    print("Playbook: lab playbook run --fixture PATH --no-send (artifact ladder; LLM writer/critic only)")
    print("Watchlist: lab watchlist scan --fixture PATH --no-send (locked in_universe ∪ watch_only; not a call)")
    print("Dry-run ingest without keys: lab ingest --fixture tests/fixtures/phase5b/polygon_ohlcv.json --no-db")
    print("Rejected theses remain queryable learning records.")
    print(f"UTC now: {utcnow().isoformat()}")
    print("Ops timezone: Australia/Sydney (display only; all rows are timestamptz UTC).")
    print("US session timezone: America/New_York (DST via zoneinfo).")
    return 0


def cmd_migrate() -> int:
    dsn = dsn_from_env()
    upgrade_head(dsn)
    rev = current_revision(dsn)
    print(f"migrated to {rev}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    from mm_ingest.config import load_ingest_settings, load_instruments
    from mm_ingest.hl_info import HyperliquidInfoClient
    from mm_ingest.pipeline import (
        envelopes_from_fixture,
        ingest_from_client,
        ingest_from_fixture,
        load_fixture_file,
        stats_from_envelopes,
    )

    settings = load_ingest_settings()
    if args.no_db:
        if not args.fixture:
            print("lab ingest --no-db requires --fixture (offline dry-run; no live keys)", file=sys.stderr)
            return 2
        fixture = load_fixture_file(args.fixture)
        envelopes = envelopes_from_fixture(
            fixture,
            stale_after_seconds=int(settings.get("stale_after_seconds", 120)),
            instruments=fixture.get("instruments") or load_instruments(),
        )
        stats = stats_from_envelopes(envelopes, dry_run=True)
        payload = stats.as_public_dict()
        payload["qualities"] = sorted({e.data_quality.value for e in envelopes})
        print(json.dumps(payload))
        return 0

    from mm_memory.db import dsn_from_env, session_scope
    from mm_memory.object_store import ObjectStoreConfigError, object_store_from_env

    dsn = args.dsn or dsn_from_env()
    try:
        store = object_store_from_env(enabled=not args.no_objects and bool(settings.get("store_raw_objects", True)))
    except ObjectStoreConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    instruments = load_instruments()
    with session_scope(dsn) as session:
        if args.fixture:
            fixture = load_fixture_file(args.fixture)
            stats = ingest_from_fixture(
                session,
                fixture,
                object_store=store,
                stale_after_seconds=int(settings.get("stale_after_seconds", 120)),
                instruments=fixture.get("instruments") or instruments,
            )
        else:
            start = parse_utc(args.start) if args.start else None
            end = parse_utc(args.end) if args.end else None
            attempts, backoff = 2, 0.25
            limits = settings.get("rate_limits") if isinstance(settings.get("rate_limits"), dict) else {}
            hl_lim = limits.get("hyperliquid") if isinstance(limits, dict) else {}
            if isinstance(hl_lim, dict):
                attempts = int(hl_lim.get("max_attempts") or attempts)
                backoff = float(hl_lim.get("backoff_s") or backoff)
            with HyperliquidInfoClient(
                url=str(settings.get("info_url")),
                max_attempts=attempts,
                backoff_s=backoff,
            ) as client:
                stats = ingest_from_client(
                    session,
                    client,
                    instruments=instruments,
                    start=start,
                    end=end,
                    window=args.window,
                    object_store=store,
                    candle_interval=str(settings.get("candle_interval", "1h")),
                    stale_after_seconds=int(settings.get("stale_after_seconds", 120)),
                )
    print(json.dumps(stats.as_public_dict()))
    return 0


def cmd_what_did_we_know(args: argparse.Namespace) -> int:
    ts = parse_utc(args.at)
    dsn = args.dsn or dsn_from_env()
    with session_scope(dsn) as session:
        rows = what_did_we_know(session, ts, instrument=args.instrument, metric=args.metric)
    payload = [
        {
            "id": row.id,
            "instrument": row.instrument,
            "metric": row.metric,
            "claim_text": row.claim_text,
            "claim_hash": row.claim_hash,
            "data_quality": row.data_quality,
            "published_at": row.published_at.isoformat(),
            "ingested_at": row.ingested_at.isoformat(),
            "market_time": row.market_time.isoformat() if row.market_time else None,
            "as_of_knowledge": row.as_of_knowledge.isoformat(),
        }
        for row in rows[: args.limit]
    ]
    print(json.dumps({"at": ts.isoformat(), "count": len(rows), "shown": len(payload), "observations": payload}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
