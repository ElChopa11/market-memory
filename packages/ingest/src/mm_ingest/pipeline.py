"""Read-only ingest pipeline: public feeds → envelopes → Postgres (+ optional objects).

Phase 5b adds Polygon equities, HL structure, spot DQ, FRED/calendar. No signing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from mm_common.http import ERROR_NONE
from mm_common.schemas import ObservationEnvelope
from mm_common.time import parse_window, to_unix_ms, utcnow
from mm_memory.object_store import NullObjectStore, ObjectPointer, ObjectStore, raw_object_key
from mm_memory.repository import ObservationRepository, PutResult
from mm_provenance import (
    HL_TOS_NOTES,
    normalize_all_mids,
    normalize_asset_snapshot,
    normalize_candles,
    normalize_funding_history,
    normalize_liquidations,
)
from mm_ingest.config import load_equity_instruments, load_ingest_settings, load_instruments
from mm_ingest.degrade import feed_status_envelope
from mm_ingest.equities.normalize import (
    normalize_corporate_actions,
    normalize_earnings,
    normalize_ohlcv_bars,
)
from mm_ingest.equities.polygon import parse_aggs, parse_dividends, parse_earnings_events, parse_splits
from mm_ingest.hl_info import HyperliquidInfoClient
from mm_ingest.edgar import envelopes_from_stored_or_error
from mm_ingest.macro import calendar_envelopes_from_payload, normalize_fred_observations
from mm_ingest.sources import meta_for
from mm_ingest.spot import cross_check_envelopes, spot_prints_from_fixture
from mm_ingest.structure import (
    normalize_basis_snapshot,
    normalize_l2_book,
    normalize_predicted_fundings,
)


@dataclass
class IngestStats:
    created: int = 0
    duplicates: int = 0
    contradicted: int = 0
    envelopes: int = 0
    instruments: list[str] = field(default_factory=list)
    object_store: str = "null"
    sources: list[str] = field(default_factory=list)
    dry_run: bool = False

    def add(self, result: PutResult) -> None:
        if result.created:
            self.created += 1
        else:
            self.duplicates += 1
        if result.contradicted:
            self.contradicted += 1

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "duplicates": self.duplicates,
            "contradicted": self.contradicted,
            "envelopes": self.envelopes,
            "instruments": self.instruments,
            "sources": self.sources,
            "object_store": self.object_store,
            "dry_run": self.dry_run,
        }


def persist_envelopes(
    session: Session,
    envelopes: list[ObservationEnvelope],
    *,
    object_store: ObjectStore | None = None,
    raw_payloads: dict[str, Any] | None = None,
    trust_tier: int | None = None,
) -> IngestStats:
    repo = ObservationRepository(session)
    store = object_store or NullObjectStore()
    stats = IngestStats(envelopes=len(envelopes), object_store=getattr(store, "backend", type(store).__name__))
    sources: dict[str, Any] = {}
    for envelope in envelopes:
        name = envelope.source_name
        if name not in sources:
            spec = meta_for(name, kind=envelope.source_kind.value)
            sources[name] = repo.ensure_source(
                name=spec.name,
                kind=spec.kind.value,
                base_url=spec.base_url or None,
                trust_tier=trust_tier if trust_tier is not None else spec.trust_tier,
                tos_notes=spec.tos_notes or HL_TOS_NOTES,
            )
            stats.sources.append(name)
        pointer = _store_raw(store, envelope, raw_payloads=raw_payloads)
        result = repo.put_observation(envelope, source=sources[name], raw_pointer=pointer)
        stats.add(result)
        if envelope.instrument not in stats.instruments:
            stats.instruments.append(envelope.instrument)
    session.flush()
    return stats


def stats_from_envelopes(envelopes: list[ObservationEnvelope], *, dry_run: bool = True) -> IngestStats:
    instruments: list[str] = []
    sources: list[str] = []
    for envelope in envelopes:
        if envelope.instrument not in instruments:
            instruments.append(envelope.instrument)
        if envelope.source_name not in sources:
            sources.append(envelope.source_name)
    return IngestStats(
        envelopes=len(envelopes),
        instruments=instruments,
        sources=sources,
        object_store="none",
        dry_run=dry_run,
    )


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
    include_structure: bool = True,
) -> IngestStats:
    now = utcnow()
    if start is None or end is None:
        start, end = parse_window(window, now=end or now)
    symbols = instruments or load_instruments()
    start_ms, end_ms = to_unix_ms(start), to_unix_ms(end)
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

    if include_structure:
        envelopes.extend(
            _structure_from_client(
                client,
                symbols,
                snapshot_ingested,
                snapshot_published,
                stale_after_seconds,
                ctxs=ctxs,
            )
        )

    return persist_envelopes(session, envelopes, object_store=object_store)


def _structure_from_client(
    client: Any,
    symbols: list[str],
    ingested_at: datetime,
    published_at: datetime,
    stale_after_seconds: int,
    ctxs: list[Any] | None = None,
) -> list[ObservationEnvelope]:
    out: list[ObservationEnvelope] = []
    if ctxs is None:
        meta_fn = getattr(client, "meta_and_asset_ctxs", None)
        if callable(meta_fn):
            try:
                ctxs = meta_fn()
            except Exception:  # noqa: BLE001 — degrade, never invent
                ctxs = None
    if ctxs is not None:
        out.extend(
            normalize_basis_snapshot(
                ctxs,
                instruments=symbols,
                ingested_at=ingested_at,
                published_at=published_at,
                stale_after_seconds=stale_after_seconds,
            )
        )
    predicted_fn = getattr(client, "predicted_fundings", None)
    if callable(predicted_fn):
        try:
            predicted = predicted_fn()
            out.extend(
                normalize_predicted_fundings(
                    predicted,
                    instruments=symbols,
                    ingested_at=ingested_at,
                    published_at=published_at,
                    stale_after_seconds=stale_after_seconds,
                )
            )
        except Exception:  # noqa: BLE001
            for coin in symbols:
                out.append(
                    feed_status_envelope(
                        source_name="hyperliquid.info",
                        instrument=coin,
                        ingested_at=ingested_at,
                        published_at=published_at,
                        error_class="http_error",
                        metric="predicted_funding",
                        notes=("predictedFundings unavailable; not invented",),
                        venue="perp",
                    )
                )
    l2_fn = getattr(client, "l2_book", None)
    if callable(l2_fn):
        for coin in symbols:
            try:
                book = l2_fn(coin)
                out.extend(
                    normalize_l2_book(
                        book,
                        instrument=coin,
                        ingested_at=ingested_at,
                        published_at=published_at,
                        stale_after_seconds=stale_after_seconds,
                    )
                )
            except Exception:  # noqa: BLE001
                out.extend(
                    normalize_l2_book(
                        None,
                        instrument=coin,
                        ingested_at=ingested_at,
                        published_at=published_at,
                        stale_after_seconds=stale_after_seconds,
                    )
                )
    return out


def ingest_from_fixture(
    session: Session,
    fixture: dict[str, Any],
    *,
    object_store: ObjectStore | None = None,
    stale_after_seconds: int = 120,
    instruments: list[str] | None = None,
) -> IngestStats:
    envelopes = envelopes_from_fixture(
        fixture,
        stale_after_seconds=stale_after_seconds,
        instruments=instruments,
    )
    return persist_envelopes(session, envelopes, object_store=object_store)


def envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    stale_after_seconds: int = 120,
    instruments: list[str] | None = None,
) -> list[ObservationEnvelope]:
    symbols = instruments or fixture.get("instruments") or load_instruments()
    snapshot_ingested = _dt(fixture.get("snapshot_ingested_at") or fixture.get("ingested_at"))
    snapshot_published = _dt(fixture.get("snapshot_published_at") or fixture.get("published_at") or snapshot_ingested)
    envelopes: list[ObservationEnvelope] = []

    envelopes.extend(
        _hl_envelopes_from_fixture(
            fixture,
            symbols=symbols,
            snapshot_ingested=snapshot_ingested,
            snapshot_published=snapshot_published,
            stale_after_seconds=stale_after_seconds,
        )
    )
    envelopes.extend(
        _structure_envelopes_from_fixture(
            fixture,
            symbols=symbols,
            snapshot_ingested=snapshot_ingested,
            snapshot_published=snapshot_published,
            stale_after_seconds=stale_after_seconds,
        )
    )
    envelopes.extend(
        _polygon_envelopes_from_fixture(
            fixture,
            snapshot_ingested=snapshot_ingested,
            stale_after_seconds=stale_after_seconds,
        )
    )
    envelopes.extend(
        _spot_envelopes_from_fixture(
            fixture,
            symbols=symbols,
            snapshot_ingested=snapshot_ingested,
            snapshot_published=snapshot_published,
            stale_after_seconds=stale_after_seconds,
        )
    )
    envelopes.extend(_fred_envelopes_from_fixture(fixture, snapshot_ingested=snapshot_ingested, stale_after_seconds=stale_after_seconds))
    envelopes.extend(
        _calendar_envelopes_from_fixture(fixture, snapshot_ingested=snapshot_ingested, stale_after_seconds=stale_after_seconds)
    )
    envelopes.extend(_edgar_envelopes_from_fixture(fixture, snapshot_ingested=snapshot_ingested, stale_after_seconds=stale_after_seconds))
    return envelopes


def _hl_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    symbols: list[str],
    snapshot_ingested: datetime,
    snapshot_published: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    envelopes: list[ObservationEnvelope] = []
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
    return envelopes


def _structure_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    symbols: list[str],
    snapshot_ingested: datetime,
    snapshot_published: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    envelopes: list[ObservationEnvelope] = []
    ctxs = fixture.get("meta_and_asset_ctxs") or fixture.get("metaAndAssetCtxs")
    if ctxs is not None and (fixture.get("kind") in {"hl_structure", "structure"} or "basis" in fixture or fixture.get("include_basis")):
        envelopes.extend(
            normalize_basis_snapshot(
                ctxs,
                instruments=symbols,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after_seconds,
            )
        )
    elif fixture.get("kind") in {"hl_structure", "structure"} and ctxs is not None:
        envelopes.extend(
            normalize_basis_snapshot(
                ctxs,
                instruments=symbols,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after_seconds,
            )
        )
    l2 = fixture.get("l2_book") or fixture.get("l2Book") or {}
    if isinstance(l2, dict) and l2:
        if "coin" in l2 or "levels" in l2:
            coin = str(l2.get("coin") or (symbols[0] if symbols else "BTC"))
            envelopes.extend(
                normalize_l2_book(
                    l2,
                    instrument=coin,
                    ingested_at=snapshot_ingested,
                    published_at=snapshot_published,
                    stale_after_seconds=stale_after_seconds,
                )
            )
        else:
            for coin, book in l2.items():
                envelopes.extend(
                    normalize_l2_book(
                        book,
                        instrument=str(coin),
                        ingested_at=snapshot_ingested,
                        published_at=snapshot_published,
                        stale_after_seconds=stale_after_seconds,
                    )
                )
    predicted = fixture.get("predicted_fundings") or fixture.get("predictedFundings")
    if predicted is not None:
        envelopes.extend(
            normalize_predicted_fundings(
                predicted,
                instruments=symbols,
                ingested_at=snapshot_ingested,
                published_at=snapshot_published,
                stale_after_seconds=stale_after_seconds,
            )
        )
    return envelopes


def _polygon_aggs_block(
    aggs: dict[str, Any],
    *,
    ingested: datetime,
    stale_after_seconds: int,
    default_timespan: str = "day",
) -> list[ObservationEnvelope]:
    envelopes: list[ObservationEnvelope] = []
    for ticker, payload in aggs.items():
        timespan = str((payload or {}).get("timespan") or default_timespan) if isinstance(payload, dict) else default_timespan
        multiplier = int((payload or {}).get("multiplier") or 1) if isinstance(payload, dict) else 1
        if (
            isinstance(payload, dict)
            and payload.get("error_class")
            and payload.get("error_class") != ERROR_NONE
            and not payload.get("results")
        ):
            envelopes.append(
                feed_status_envelope(
                    source_name="polygon",
                    instrument=str(ticker).upper(),
                    ingested_at=ingested,
                    error_class=str(payload.get("error_class")),
                    metric="ohlcv_close",
                    notes=("Polygon aggs unavailable; no bars invented",),
                    venue="equity",
                )
            )
            continue
        bars = parse_aggs(payload, ticker=str(ticker), timespan=timespan, multiplier=multiplier)
        envelopes.extend(normalize_ohlcv_bars(bars, ingested_at=ingested, stale_after_seconds=stale_after_seconds))
    return envelopes


def _polygon_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    snapshot_ingested: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    block = fixture.get("polygon") or fixture.get("equities")
    if block is None and fixture.get("kind") in {"polygon", "equities"}:
        block = fixture
    if not isinstance(block, dict):
        return []
    if fixture.get("kind") not in {"polygon", "equities"} and "polygon" not in fixture and "aggs" not in block:
        if "aggs" not in fixture:
            return []
        block = fixture
    envelopes: list[ObservationEnvelope] = []
    ingested = _dt(block.get("ingested_at") or snapshot_ingested)
    aggs = block.get("aggs") or {}
    if isinstance(aggs, dict):
        envelopes.extend(_polygon_aggs_block(aggs, ingested=ingested, stale_after_seconds=stale_after_seconds))
    intraday = block.get("intraday") or {}
    if isinstance(intraday, dict) and intraday:
        envelopes.extend(_polygon_aggs_block(intraday, ingested=ingested, stale_after_seconds=stale_after_seconds, default_timespan="minute"))
    dividends = block.get("dividends") or {}
    if isinstance(dividends, dict):
        for ticker, payload in dividends.items():
            if isinstance(payload, dict) and payload.get("error_class") and not payload.get("results"):
                envelopes.append(
                    feed_status_envelope(
                        source_name="polygon",
                        instrument=str(ticker).upper(),
                        ingested_at=ingested,
                        error_class=str(payload.get("error_class")),
                        metric="dividend",
                        notes=("Polygon dividends unavailable; not invented",),
                        venue="equity",
                    )
                )
                continue
            envelopes.extend(
                normalize_corporate_actions(parse_dividends(payload, ticker=str(ticker)), ingested_at=ingested, stale_after_seconds=stale_after_seconds)
            )
    splits = block.get("splits") or {}
    if isinstance(splits, dict):
        for ticker, payload in splits.items():
            envelopes.extend(
                normalize_corporate_actions(parse_splits(payload, ticker=str(ticker)), ingested_at=ingested, stale_after_seconds=stale_after_seconds)
            )
    earnings = block.get("earnings") or {}
    if isinstance(earnings, dict):
        for ticker, payload in earnings.items():
            if isinstance(payload, dict) and payload.get("error_class") and not (payload.get("results") or payload.get("events")):
                envelopes.append(
                    feed_status_envelope(
                        source_name="polygon",
                        instrument=str(ticker).upper(),
                        ingested_at=ingested,
                        error_class=str(payload.get("error_class")),
                        metric="earnings",
                        notes=("Polygon earnings calendar unavailable on this plan; not invented",),
                        venue="equity",
                    )
                )
                continue
            envelopes.extend(
                normalize_earnings(parse_earnings_events(payload, ticker=str(ticker)), ingested_at=ingested, stale_after_seconds=stale_after_seconds)
            )
    missing_env = block.get("missing_env")
    if missing_env:
        tickers = block.get("instruments") or load_equity_instruments()
        for ticker in tickers:
            envelopes.append(
                feed_status_envelope(
                    source_name="polygon",
                    instrument=str(ticker).upper(),
                    ingested_at=ingested,
                    error_class="missing_env",
                    notes=("missing env POLYGON_API_KEY; Polygon unavailable (error_class=missing_env)",),
                    venue="equity",
                    source_url_or_id="missing_env:POLYGON_API_KEY",
                )
            )
    return envelopes


def _spot_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    symbols: list[str],
    snapshot_ingested: datetime,
    snapshot_published: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    block = fixture.get("spot") or fixture.get("spot_cross_check")
    if block is None and fixture.get("kind") in {"spot", "spot_cross_check"}:
        block = fixture
    if not isinstance(block, dict):
        return []
    envelopes: list[ObservationEnvelope] = []
    ingested = _dt(block.get("ingested_at") or snapshot_ingested)
    published = _dt(block.get("published_at") or snapshot_published)
    divergence_bps = float(block.get("divergence_bps") or 50)
    perp = {}
    raw_perp = block.get("perp_mids") or block.get("perp") or {}
    if isinstance(raw_perp, dict):
        for key, val in raw_perp.items():
            try:
                perp[str(key).upper()] = float(val)
            except (TypeError, ValueError):
                continue
    if not perp:
        mids = fixture.get("all_mids") or fixture.get("allMids") or {}
        if isinstance(mids, dict):
            for key, val in mids.items():
                try:
                    perp[str(key).upper()] = float(val)
                except (TypeError, ValueError):
                    continue
    wanted = [str(s).upper() for s in (block.get("instruments") or symbols)]
    for provider in ("coingecko", "binance"):
        payload = block.get(provider)
        error_class = ERROR_NONE
        if isinstance(payload, dict) and payload.get("error_class") and not any(
            k for k in payload if k not in {"error_class", "notes"}
        ):
            error_class = str(payload.get("error_class"))
            prints: dict[str, float] = {}
        else:
            prints = spot_prints_from_fixture(payload, provider=provider) if payload is not None else {}
            if payload is None:
                continue
            if isinstance(payload, dict) and payload.get("error_class"):
                error_class = str(payload.get("error_class"))
        source_name = "coingecko" if provider == "coingecko" else "binance.public"
        envelopes.extend(
            cross_check_envelopes(
                perp_mids=perp,
                spot=prints,
                spot_source=source_name,
                instruments=wanted,
                ingested_at=ingested,
                published_at=published,
                divergence_bps=divergence_bps,
                stale_after_seconds=stale_after_seconds,
                spot_error_class=error_class,
            )
        )
    return envelopes


def _fred_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    snapshot_ingested: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    block = fixture.get("fred")
    if block is None and fixture.get("kind") in {"fred", "macro"}:
        block = fixture
    if not isinstance(block, dict):
        return []
    ingested = _dt(block.get("ingested_at") or snapshot_ingested)
    if block.get("missing_env") or block.get("error_class") == "missing_env":
        series = block.get("series") or {"US10Y": "DGS10"}
        return [
            feed_status_envelope(
                source_name="fred",
                instrument=str(symbol).upper(),
                ingested_at=ingested,
                error_class="missing_env",
                notes=("missing env FRED_API_KEY; FRED unavailable (error_class=missing_env)",),
                venue="macro",
                source_url_or_id="missing_env:FRED_API_KEY",
            )
            for symbol in series
        ]
    observations = block.get("series") or block.get("observations") or {}
    envelopes: list[ObservationEnvelope] = []
    if isinstance(observations, dict):
        for symbol, payload in observations.items():
            series_id = str(symbol)
            body = payload
            if isinstance(payload, dict) and "series_id" in payload:
                series_id = str(payload.get("series_id") or symbol)
                body = payload
            envelopes.extend(
                normalize_fred_observations(
                    body if "observations" in (body or {}) else {"observations": body if isinstance(body, list) else []},
                    instrument=str(symbol).upper(),
                    series_id=series_id,
                    ingested_at=ingested,
                    stale_after_seconds=stale_after_seconds,
                )
            )
    return envelopes


def _edgar_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    snapshot_ingested: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    block = fixture.get("edgar")
    if isinstance(block, list):
        block = {"filings": block, "ingested_at": fixture.get("ingested_at")}
    if block is None and fixture.get("kind") in {"edgar", "filings", "lockup"}:
        block = fixture
    if not isinstance(block, dict):
        return []
    ingested = _dt(block.get("ingested_at") or snapshot_ingested)
    rows = block.get("filings") or block.get("documents") or []
    extra = block.get("eight_k") or block.get("8k") or []
    envelopes: list[ObservationEnvelope] = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                envelopes.extend(
                    envelopes_from_stored_or_error(row, ingested_at=ingested, stale_after_seconds=stale_after_seconds)
                )
    if isinstance(extra, list):
        for row in extra:
            if isinstance(row, dict):
                body = dict(row)
                body.setdefault("form", "8-K")
                envelopes.extend(
                    envelopes_from_stored_or_error(body, ingested_at=ingested, stale_after_seconds=stale_after_seconds)
                )
    if block.get("error_class") and not rows and not extra:
        envelopes.extend(
            envelopes_from_stored_or_error(
                {
                    "instrument": str(block.get("instrument") or "EDGAR"),
                    "error_class": str(block.get("error_class")),
                    "notes": block.get("notes"),
                    "url": block.get("url"),
                },
                ingested_at=ingested,
                stale_after_seconds=stale_after_seconds,
            )
        )
    return envelopes


def _calendar_envelopes_from_fixture(
    fixture: dict[str, Any],
    *,
    snapshot_ingested: datetime,
    stale_after_seconds: int,
) -> list[ObservationEnvelope]:
    block = fixture.get("calendar")
    if block is None and fixture.get("kind") in {"calendar", "economic_calendar"}:
        block = fixture
    if not isinstance(block, dict):
        return []
    ingested = _dt(block.get("ingested_at") or snapshot_ingested)
    return calendar_envelopes_from_payload(block, ingested_at=ingested, stale_after_seconds=stale_after_seconds)


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
