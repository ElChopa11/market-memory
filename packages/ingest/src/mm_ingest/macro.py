"""Macro ingest: FRED series + fixture-friendly economic calendar.

Missing FRED_API_KEY → unavailable, never a fake series.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml

from mm_common.enums import EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    ERROR_MISSING_ENV,
    ERROR_NONE,
    ERROR_PARSE,
    ERROR_RATE_LIMITED,
    http_get,
    missing_env_notes,
)
from mm_common.schemas import ObservationEnvelope
from mm_common.time import parse_utc
from mm_ingest.degrade import feed_status_envelope
from mm_ingest.rate_limit import RateLimitBudget
from mm_ingest.sources import (
    CALENDAR_SOURCE_NAME,
    FRED_BASE_URL,
    FRED_SOURCE_NAME,
)
from mm_provenance.envelope import build_envelope

API_KEY_ENV = "FRED_API_KEY"


def fetch_fred_series(
    *,
    series: Mapping[str, str],
    ingested_at: datetime,
    env: Mapping[str, str] | None = None,
    http_client: httpx.Client | None = None,
    base_url: str = FRED_BASE_URL,
    api_key_env: str = API_KEY_ENV,
    budget: RateLimitBudget | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] | None = None,
    stale_after_seconds: int = 120,
) -> tuple[list[ObservationEnvelope], str]:
    key = _getenv(api_key_env, env)
    symbols = [str(s).upper() for s in series]
    if not key:
        notes = missing_env_notes(api_key_env, source="FRED")
        envelopes = [
            feed_status_envelope(
                source_name=FRED_SOURCE_NAME,
                instrument=symbol,
                ingested_at=ingested_at,
                error_class=ERROR_MISSING_ENV,
                notes=notes,
                venue="macro",
                source_url_or_id=f"missing_env:{api_key_env}",
            )
            for symbol in symbols
        ]
        return envelopes, ERROR_MISSING_ENV

    owns = http_client is None
    client = http_client or httpx.Client(timeout=8.0)
    limiter = budget or RateLimitBudget(name="fred", max_requests_per_minute=20)
    out: list[ObservationEnvelope] = []
    last_error = ERROR_NONE
    try:
        for symbol, series_id in series.items():
            if not limiter.allow():
                last_error = ERROR_RATE_LIMITED
                out.append(
                    feed_status_envelope(
                        source_name=FRED_SOURCE_NAME,
                        instrument=str(symbol).upper(),
                        ingested_at=ingested_at,
                        error_class=ERROR_RATE_LIMITED,
                        notes=("FRED rate-limit budget exhausted; no series invented",),
                        venue="macro",
                    )
                )
                continue
            params = {
                "series_id": series_id,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 5,
            }
            kwargs: dict[str, Any] = {
                "params": params,
                "max_attempts": max_attempts,
                "parse_json": True,
            }
            if sleep is not None:
                kwargs["sleep"] = sleep
            result = http_get(client, base_url, **kwargs)
            if not result.ok:
                last_error = result.error_class
                out.append(
                    feed_status_envelope(
                        source_name=FRED_SOURCE_NAME,
                        instrument=str(symbol).upper(),
                        ingested_at=ingested_at,
                        error_class=result.error_class,
                        notes=(f"FRED HTTP failed (error_class={result.error_class}); key not printed",),
                        venue="macro",
                        source_url_or_id=f"fred:{series_id}",
                    )
                )
                continue
            payload = result.json_payload if isinstance(result.json_payload, dict) else {}
            out.extend(
                normalize_fred_observations(
                    payload,
                    instrument=str(symbol).upper(),
                    series_id=str(series_id),
                    ingested_at=ingested_at,
                    stale_after_seconds=stale_after_seconds,
                )
            )
    finally:
        if owns:
            client.close()
    return out, last_error


def normalize_fred_observations(
    payload: Any,
    *,
    instrument: str,
    series_id: str,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    if not isinstance(payload, dict):
        return [
            feed_status_envelope(
                source_name=FRED_SOURCE_NAME,
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("FRED payload is not an object; no series invented",),
                venue="macro",
                source_url_or_id=f"fred:{series_id}",
            )
        ]
    rows = payload.get("observations") or []
    if not isinstance(rows, list) or not rows:
        return [
            feed_status_envelope(
                source_name=FRED_SOURCE_NAME,
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("FRED returned no observations; no series invented",),
                venue="macro",
                source_url_or_id=f"fred:{series_id}",
            )
        ]
    out: list[ObservationEnvelope] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = row.get("value")
        if raw in {None, "", "."}:
            continue
        value = normalize_numeric(raw)
        date_s = str(row.get("date") or "")
        if not date_s or value is None:
            continue
        market_time = datetime.fromisoformat(f"{date_s}T00:00:00+00:00").astimezone(timezone.utc)
        row_ingested = _row_ingested(row, ingested_at)
        out.append(
            build_envelope(
                source_name=FRED_SOURCE_NAME,
                source_kind=SourceKind.MACRO,
                source_url_or_id=f"fred:{series_id}:{date_s}",
                instrument=instrument,
                metric="fred_observation",
                value=value,
                published_at=market_time,
                ingested_at=row_ingested,
                market_time=market_time,
                payload={"series_id": series_id, "raw": {"date": date_s}, "historical": True},
                extras={"series_id": series_id},
                historical=True,
                stale_after_seconds=stale_after_seconds,
                venue="macro",
                evidence_type=EvidenceType.METRIC,
            )
        )
    if not out:
        return [
            feed_status_envelope(
                source_name=FRED_SOURCE_NAME,
                instrument=instrument,
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("FRED observations unparseable; no series invented",),
                venue="macro",
                source_url_or_id=f"fred:{series_id}",
            )
        ]
    return out


def calendar_envelopes_from_path(
    path: Path,
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    if not path.is_file():
        return [
            feed_status_envelope(
                source_name=CALENDAR_SOURCE_NAME,
                instrument="US",
                ingested_at=ingested_at,
                error_class="config_error",
                notes=(f"{path} missing; no live calendar invented",),
                venue="macro",
            )
        ]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return calendar_envelopes_from_payload(data, ingested_at=ingested_at, stale_after_seconds=stale_after_seconds)


def calendar_envelopes_from_payload(
    payload: Any,
    *,
    ingested_at: datetime,
    stale_after_seconds: int = 120,
) -> list[ObservationEnvelope]:
    if not isinstance(payload, dict):
        return [
            feed_status_envelope(
                source_name=CALENDAR_SOURCE_NAME,
                instrument="US",
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("calendar payload is not a mapping; no events invented",),
                venue="macro",
            )
        ]
    events = payload.get("events") or payload.get("calendar") or []
    source = str(payload.get("source") or "fixture")
    if not isinstance(events, list):
        return [
            feed_status_envelope(
                source_name=CALENDAR_SOURCE_NAME,
                instrument="US",
                ingested_at=ingested_at,
                error_class=ERROR_PARSE,
                notes=("calendar events is not a list; no events invented",),
                venue="macro",
            )
        ]
    out: list[ObservationEnvelope] = []
    for row in events:
        if not isinstance(row, dict):
            continue
        when_raw = row.get("when") or row.get("datetime")
        name = str(row.get("name") or "")
        if not when_raw or not name:
            continue
        when = parse_utc(str(when_raw)) if not isinstance(when_raw, datetime) else when_raw
        row_ingested = _row_ingested(row, ingested_at)
        extras = {"name": name}
        out.append(
            build_envelope(
                source_name=CALENDAR_SOURCE_NAME,
                source_kind=SourceKind.MACRO,
                source_url_or_id=f"calendar:{name}:{when.isoformat()}",
                instrument=str(row.get("region") or "US").upper(),
                metric="calendar_event",
                value=name,
                published_at=when,
                ingested_at=row_ingested,
                market_time=when,
                payload={
                    "source": source,
                    "importance": str(row.get("importance") or "medium"),
                    "notes": str(row.get("notes") or ""),
                    "fixture": True,
                },
                extras=extras,
                historical=True,
                stale_after_seconds=stale_after_seconds,
                venue="macro",
                evidence_type=EvidenceType.FACT,
            )
        )
    return out


def _getenv(name: str, env: Mapping[str, str] | None) -> str | None:
    if env is not None:
        raw = env.get(name)
    else:
        raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw)


def _row_ingested(row: dict[str, Any], default: datetime) -> datetime:
    extra = row.get("ingested_at")
    if extra is None:
        return default
    if isinstance(extra, datetime):
        return extra
    return parse_utc(str(extra))
