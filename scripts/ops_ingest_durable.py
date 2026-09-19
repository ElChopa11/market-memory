#!/usr/bin/env python3
"""Durable read-only Hyperliquid /info ingest with 429 backoff and partial success.

Public /info only. Fails closed if MinIO/S3 is not configured.
Does not use --no-objects or MM_OBJECT_STORE=memory.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import httpx

from mm_common.time import parse_window, to_unix_ms, utcnow
from mm_ingest.config import load_ingest_settings, load_instruments
from mm_ingest.hl_info import HyperliquidInfoClient, HyperliquidInfoError
from mm_ingest.pipeline import persist_envelopes
from mm_memory.db import dsn_from_env, session_scope
from mm_memory.object_store import ObjectStoreConfigError, object_store_from_env
from mm_provenance import (
    normalize_all_mids,
    normalize_asset_snapshot,
    normalize_candles,
    normalize_funding_history,
)


class RetryingInfoClient(HyperliquidInfoClient):
    """Same allowlist as HyperliquidInfoClient; retries 429/5xx with exponential backoff."""

    def __init__(self, *args: Any, max_attempts: int = 8, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.max_attempts = max_attempts

    def post(self, body: dict[str, Any]) -> Any:
        delay = 1.0
        last_error: Exception | None = None
        info_type = str(body.get("type", ""))
        for attempt in range(1, self.max_attempts + 1):
            try:
                return super().post(body)
            except HyperliquidInfoError as exc:
                last_error = exc
                code = _status_code(exc)
                if code not in {429, 500, 502, 503, 504}:
                    raise
                print(
                    json.dumps({"event": "retry", "info_type": info_type, "status": code, "attempt": attempt, "sleep_s": delay}),
                    file=sys.stderr,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                print(
                    json.dumps({"event": "retry", "info_type": info_type, "error": type(exc).__name__, "attempt": attempt, "sleep_s": delay}),
                    file=sys.stderr,
                )
            if attempt == self.max_attempts:
                break
            time.sleep(delay)
            delay = min(delay * 2, 60)
        raise HyperliquidInfoError(f"Hyperliquid info {info_type} exhausted retries: {last_error}") from last_error


def _status_code(exc: HyperliquidInfoError) -> int | None:
    cause = exc.__cause__
    if isinstance(cause, httpx.HTTPStatusError):
        return cause.response.status_code
    text = str(exc)
    for token in text.split():
        if token.isdigit():
            return int(token)
    return None


def _persist(dsn: str, envelopes: list[Any], store: Any) -> dict[str, Any]:
    if not envelopes:
        return {"created": 0, "duplicates": 0, "envelopes": 0}
    with session_scope(dsn) as session:
        stats = persist_envelopes(session, envelopes, object_store=store)
    return {
        "created": stats.created,
        "duplicates": stats.duplicates,
        "contradicted": stats.contradicted,
        "envelopes": stats.envelopes,
        "object_store": stats.object_store,
    }


def main() -> int:
    settings = load_ingest_settings()
    try:
        store = object_store_from_env(enabled=bool(settings.get("store_raw_objects", True)))
    except ObjectStoreConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if getattr(store, "backend", "") in {"memory", "null"}:
        print(f"Refusing non-durable object store backend={store.backend!r}", file=sys.stderr)
        return 2

    dsn = dsn_from_env()
    instruments = load_instruments()
    stale_after = int(settings.get("stale_after_seconds", 120))
    candle_interval = str(settings.get("candle_interval", "1h"))
    now = utcnow()
    start, end = parse_window("7d", now=now)
    start_ms, end_ms = to_unix_ms(start), to_unix_ms(end)
    snapshot_ingested = now
    snapshot_published = now
    gaps: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "instruments": instruments,
        "candle_interval": candle_interval,
        "object_store": store.backend,
        "steps": [],
        "gaps": gaps,
    }

    with RetryingInfoClient(url=str(settings.get("info_url"))) as client:
        try:
            mids = client.all_mids()
            ctxs = client.meta_and_asset_ctxs()
        except Exception as exc:
            gaps.append({"feed": "metaAndAssetCtxs/allMids", "error": str(exc)})
            print(json.dumps(summary, indent=2))
            return 1
        envelopes = []
        envelopes.extend(
            normalize_all_mids(
                mids,
                instruments=instruments,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after,
            )
        )
        envelopes.extend(
            normalize_asset_snapshot(
                ctxs,
                instruments=instruments,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after,
            )
        )
        stats = _persist(dsn, envelopes, store)
        summary["steps"].append({"feed": "snapshots", **stats})

        # BTC historical first; ETH is a cheap follow-on (partial success if a later call 429s).
        historical_coins = ["BTC", "ETH"] if "ETH" in instruments else ["BTC"]
        for coin in historical_coins:
            try:
                funding = client.iter_funding_history(coin, start_ms, end_ms)
                stats = _persist(dsn, normalize_funding_history(funding, ingested_at=snapshot_ingested, stale_after_seconds=stale_after), store)
                summary["steps"].append({"feed": f"fundingHistory:{coin}", "rows": len(funding), **stats})
            except Exception as exc:
                gaps.append({"feed": f"fundingHistory:{coin}", "error": str(exc)})
            try:
                candles = client.iter_candles(coin, candle_interval, start_ms, end_ms)
                stats = _persist(dsn, normalize_candles(candles, ingested_at=snapshot_ingested, stale_after_seconds=stale_after), store)
                summary["steps"].append({"feed": f"candleSnapshot:{coin}:{candle_interval}", "rows": len(candles), **stats})
            except Exception as exc:
                gaps.append({"feed": f"candleSnapshot:{coin}:{candle_interval}", "error": str(exc)})

    print(json.dumps(summary, indent=2))
    return 0 if not any(g["feed"].startswith("fundingHistory:BTC") or g["feed"] == "snapshots" for g in gaps) else 1


if __name__ == "__main__":
    sys.exit(main())
