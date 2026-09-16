"""Read-only ingest process. Must not sign or submit orders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mm_common.time import parse_utc
from mm_ingest.config import load_ingest_settings, load_instruments
from mm_ingest.hl_info import HyperliquidInfoClient
from mm_ingest.pipeline import ingest_from_client, ingest_from_fixture, load_fixture_file
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.object_store import ObjectStoreConfigError, object_store_from_env

__phase__ = 1
LIVE_TRADING_ENABLED = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ingest-once", description="One-shot read-only Hyperliquid info ingest")
    parser.add_argument("--window", default="7d")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--no-objects", action="store_true")
    parser.add_argument("--dsn")
    args = parser.parse_args(argv)

    dsn = args.dsn or dsn_from_env()
    settings = load_ingest_settings()
    try:
        store = object_store_from_env(enabled=not args.no_objects and bool(settings.get("store_raw_objects", True)))
    except ObjectStoreConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    instruments = load_instruments()
    with session_scope(dsn) as session:
        if args.fixture:
            stats = ingest_from_fixture(
                session,
                load_fixture_file(args.fixture),
                object_store=store,
                stale_after_seconds=int(settings.get("stale_after_seconds", 120)),
                instruments=instruments,
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
                "object_store": stats.object_store,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
