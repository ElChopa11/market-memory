"""Read-only ingest pipeline: HL public info → envelopes → Postgres (+ optional objects)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from mm_common.schemas import ObservationEnvelope
from mm_common.time import parse_window, to_unix_ms, utcnow
from mm_memory.object_store import NullObjectStore, ObjectPointer, ObjectStore, raw_object_key
from mm_memory.repository import ObservationRepository, PutResult
from mm_provenance import (
    HL_BASE_URL,
    HL_SOURCE_KIND,
    HL_SOURCE_NAME,
    HL_TOS_NOTES,
    normalize_all_mids,
    normalize_asset_snapshot,
    normalize_candles,
    normalize_funding_history,
    normalize_liquidations,
)
from mm_ingest.config import load_ingest_settings, load_instruments
from mm_ingest.hl_info import HyperliquidInfoClient


@dataclass
class IngestStats:
    created: int = 0
    duplicates: int = 0
    contradicted: int = 0
    envelopes: int = 0
    instruments: list[str] = field(default_factory=list)
    object_store: str = "null"

    def add(self, result: PutResult) -> None:
        if result.created:
            self.created += 1
        else:
            self.duplicates += 1
        if result.contradicted:
            self.contradicted += 1


def persist_envelopes(
    session: Session,
    envelopes: list[ObservationEnvelope],
    *,
    object_store: ObjectStore | None = None,
    raw_payloads: dict[str, Any] | None = None,
) -> IngestStats:
    repo = ObservationRepository(session)
    source = repo.ensure_source(
        name=HL_SOURCE_NAME,
        kind=HL_SOURCE_KIND.value,
        base_url=HL_BASE_URL,
        trust_tier=4,
        tos_notes=HL_TOS_NOTES,
    )
    store = object_store or NullObjectStore()
    stats = IngestStats(envelopes=len(envelopes), object_store=getattr(store, "backend", type(store).__name__))
    for envelope in envelopes:
        pointer = _store_raw(store, envelope, raw_payloads=raw_payloads)
        result = repo.put_observation(envelope, source=source, raw_pointer=pointer)
        stats.add(result)
        if envelope.instrument not in stats.instruments:
            stats.instruments.append(envelope.instrument)
    session.flush()
    return stats


def _store_raw(
    store: ObjectStore,
    envelope: ObservationEnvelope,
    *,
    raw_payloads: dict[str, Any] | None,
) -> ObjectPointer | None:
    payload = envelope.payload.get("raw", envelope.payload)
    if raw_payloads is not None:
        payload = raw_payloads
    key = raw_object_key(
        source=envelope.source_name,
        instrument=envelope.instrument,
        metric=envelope.metric,
        claim_hash=envelope.claim_hash,
        ingested_at_iso=envelope.ingested_at.isoformat(),
    )
    pointer = store.put_json(key, payload)
    if not pointer.key:
        return None
    return pointer


def ingest_from_client(
    session: Session,
    client: HyperliquidInfoClient,
    *,
    instruments: list[str] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    window: str = "7d",
    object_store: ObjectStore | None = None,
    candle_interval: str = "1h",
    stale_after_seconds: int = 120,
) -> IngestStats:
    now = utcnow()
    if start is None or end is None:
        start, end = parse_window(window, now=end or now)
    symbols = instruments or load_instruments()
    start_ms, end_ms = to_unix_ms(start), to_unix_ms(end)
    # Window start/end bound historical series only (fundingHistory, candles).
    # Snapshot polls have no exchange event time: lab capture is ingested_at / published_at.
    snapshot_ingested = now
    snapshot_published = now

    envelopes: list[ObservationEnvelope] = []
    mids = client.all_mids()
    envelopes.extend(
        normalize_all_mids(
            mids,
            instruments=symbols,
            ingested_at=snapshot_ingested,
            published_at=snapshot_published,
            stale_after_seconds=stale_after_seconds,
        )
    )
    ctxs = client.meta_and_asset_ctxs()
    envelopes.extend(
        normalize_asset_snapshot(
            ctxs,
            instruments=symbols,
            ingested_at=snapshot_ingested,
            published_at=snapshot_published,
            stale_after_seconds=stale_after_seconds,
        )
    )
    for coin in symbols:
        funding = client.iter_funding_history(coin, start_ms, end_ms)
        envelopes.extend(normalize_funding_history(funding, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))
        candles = client.iter_candles(coin, candle_interval, start_ms, end_ms)
        envelopes.extend(normalize_candles(candles, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))
        trades = client.recent_trades(coin)
        envelopes.extend(normalize_liquidations(trades, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))

    return persist_envelopes(session, envelopes, object_store=object_store)


def ingest_from_fixture(
    session: Session,
    fixture: dict[str, Any],
    *,
    object_store: ObjectStore | None = None,
    stale_after_seconds: int = 120,
    instruments: list[str] | None = None,
) -> IngestStats:
    symbols = instruments or fixture.get("instruments") or load_instruments()
    envelopes: list[ObservationEnvelope] = []

    snapshot_ingested = _dt(fixture.get("snapshot_ingested_at") or fixture.get("ingested_at"))
    # Lab capture time for the snapshot poll — not an exchange event clock.
    snapshot_published = _dt(fixture.get("snapshot_published_at") or fixture.get("published_at") or snapshot_ingested)

    if "all_mids" in fixture or "allMids" in fixture:
        envelopes.extend(
            normalize_all_mids(
                fixture.get("all_mids") or fixture.get("allMids") or {},
                instruments=symbols,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after_seconds,
            )
        )
    if "meta_and_asset_ctxs" in fixture or "metaAndAssetCtxs" in fixture:
        envelopes.extend(
            normalize_asset_snapshot(
                fixture.get("meta_and_asset_ctxs") or fixture.get("metaAndAssetCtxs") or [],
                instruments=symbols,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after_seconds,
            )
        )
    funding = fixture.get("funding_history") or fixture.get("fundingHistory") or {}
    if isinstance(funding, dict):
        for rows in funding.values():
            envelopes.extend(normalize_funding_history(rows, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))
    elif isinstance(funding, list):
        envelopes.extend(normalize_funding_history(funding, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))

    candles = fixture.get("candles") or fixture.get("candleSnapshot") or {}
    if isinstance(candles, dict):
        for rows in candles.values():
            envelopes.extend(normalize_candles(rows, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))
    elif isinstance(candles, list):
        envelopes.extend(normalize_candles(candles, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))

    trades = fixture.get("recent_trades") or fixture.get("recentTrades") or {}
    if isinstance(trades, dict):
        for rows in trades.values():
            envelopes.extend(normalize_liquidations(rows, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))
    elif isinstance(trades, list):
        envelopes.extend(normalize_liquidations(trades, ingested_at=snapshot_ingested, stale_after_seconds=stale_after_seconds))

    return persist_envelopes(session, envelopes, object_store=object_store)


def load_fixture_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text)
    else:
        import json

        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("fixture must be a JSON/YAML object")
    return data


def _dt(value: Any) -> datetime:
    from mm_common.time import parse_utc, utcnow

    if value is None:
        return utcnow()
    if isinstance(value, datetime):
        return value
    return parse_utc(str(value))


def default_pipeline_settings() -> dict[str, Any]:
    return load_ingest_settings()
