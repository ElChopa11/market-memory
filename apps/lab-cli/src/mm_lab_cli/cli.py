"""Coordinator CLI: status, migrate, ingest, what-did-we-know.

Must not hold trading credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from mm_common.time import parse_utc, utcnow
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.migrate import current_revision, upgrade_head
from mm_memory.object_store import object_store_from_env
from mm_memory.queries import what_did_we_know


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lab", description="market-memory coordinator CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="show phase and hard-gates")
    sub.add_parser("migrate", help="apply Alembic migrations to Postgres")

    ingest = sub.add_parser("ingest", help="read-only Hyperliquid info ingest")
    ingest.add_argument("--window", default="7d", help="lookback window, e.g. 7d, 24h")
    ingest.add_argument("--start", help="UTC start instant (ISO-8601)")
    ingest.add_argument("--end", help="UTC end instant (ISO-8601)")
    ingest.add_argument("--fixture", type=Path, help="JSON/YAML fixture instead of live HTTP")
    ingest.add_argument("--no-objects", action="store_true", help="do not write raw payloads to MinIO/S3")
    ingest.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN)")

    know = sub.add_parser("what-did-we-know", help="point-in-time observations (ingested_at <= T)")
    know.add_argument("--at", required=True, help="UTC instant (ISO-8601)")
    know.add_argument("--instrument", help="filter BTC/ETH")
    know.add_argument("--metric", help="filter metric name")
    know.add_argument("--dsn", help="Postgres DSN (default POSTGRES_DSN)")
    know.add_argument("--limit", type=int, default=50)

    args = parser.parse_args(argv)
    if args.cmd is None or args.cmd == "status":
        return cmd_status()
    if args.cmd == "migrate":
        return cmd_migrate()
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "what-did-we-know":
        return cmd_what_did_we_know(args)
    parser.print_help()
    return 2


def cmd_status() -> int:
    print("market-memory lab CLI (Phase 1 — read-only ingest + Market Memory)")
    print("Live trading: HARD-GATED")
    print("Research cannot access trading credentials.")
    print("Ingest: Hyperliquid public /info only (no signing, no private keys).")
    print("Point-in-time: what_did_we_know(T) uses ingested_at <= T, never published_at alone.")
    print(f"UTC now: {utcnow().isoformat()}")
    print("Ops timezone: Australia/Sydney (display only; all rows are timestamptz UTC).")
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
    from mm_ingest.pipeline import ingest_from_client, ingest_from_fixture, load_fixture_file

    dsn = args.dsn or dsn_from_env()
    settings = load_ingest_settings()
    store = object_store_from_env(enabled=not args.no_objects and bool(settings.get("store_raw_objects", True)))
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
            with HyperliquidInfoClient(url=str(settings.get("info_url"))) as client:
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
    print(
        json.dumps(
            {
                "created": stats.created,
                "duplicates": stats.duplicates,
                "contradicted": stats.contradicted,
                "envelopes": stats.envelopes,
                "instruments": stats.instruments,
            }
        )
    )
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
