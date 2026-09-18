"""Optional public spot cross-check (CoinGecko / Binance). DQ divergence, not arb.

Never invent. Missing/rate-limited → unavailable + error_class.
Divergence is a data-quality event, not executable-arb.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import Any

import httpx

from mm_common.enums import DataQuality, EvidenceType, SourceKind
from mm_common.hashing import normalize_numeric
from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    ERROR_NONE,
    ERROR_PARSE,
    ERROR_RATE_LIMITED,
    http_get,
)
from mm_common.schemas import ObservationEnvelope
from mm_ingest.degrade import feed_status_envelope
from mm_ingest.rate_limit import RateLimitBudget
from mm_ingest.sources import (
    BINANCE_BASE_URL,
    BINANCE_SOURCE_NAME,
    COINGECKO_BASE_URL,
    COINGECKO_SOURCE_NAME,
)
from mm_provenance.envelope import build_envelope
from mm_provenance.normalize import HL_SOURCE_NAME, SNAPSHOT_CAPTURE_KIND, SNAPSHOT_EXTRAS

DEFAULT_DIVERGENCE_BPS = 50.0


def fetch_coingecko_usd(
    *,
    ids: Mapping[str, str],
    http_client: httpx.Client,
    base_url: str = COINGECKO_BASE_URL,
    budget: RateLimitBudget | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] | None = None,
) -> tuple[dict[str, float], str]:
    """Map instrument → USD last. Empty + error_class on failure."""
    if not ids:
        return {}, ERROR_PARSE
    limiter = budget or RateLimitBudget(name="coingecko", max_requests_per_minute=10)
    if not limiter.allow():
        return {}, ERROR_RATE_LIMITED
    params = {
        "ids": ",".join(str(v) for v in ids.values()),
        "vs_currencies": "usd",
    }
    kwargs: dict[str, Any] = {"params": params, "max_attempts": max_attempts, "parse_json": True}
    if sleep is not None:
        kwargs["sleep"] = sleep
    result = http_get(http_client, base_url, **kwargs)
    if not result.ok:
        return {}, result.error_class
    payload = result.json_payload if isinstance(result.json_payload, dict) else {}
    out: dict[str, float] = {}
    for symbol, gecko_id in ids.items():
        body = payload.get(gecko_id) or {}
        last = _maybe_float(body.get("usd") if isinstance(body, dict) else None)
        if last is not None:
            out[str(symbol).upper()] = last
    if not out:
        return {}, ERROR_PARSE
    return out, ERROR_NONE


def fetch_binance_usd(
    *,
    symbols: Mapping[str, str],
    http_client: httpx.Client,
    base_url: str = BINANCE_BASE_URL,
    budget: RateLimitBudget | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] | None = None,
) -> tuple[dict[str, float], str]:
    limiter = budget or RateLimitBudget(name="binance", max_requests_per_minute=20)
    out: dict[str, float] = {}
    last_error = ERROR_NONE
    for instrument, pair in symbols.items():
        if not limiter.allow():
            last_error = ERROR_RATE_LIMITED
            break
        kwargs: dict[str, Any] = {
            "params": {"symbol": pair},
            "max_attempts": max_attempts,
            "parse_json": True,
        }
        if sleep is not None:
            kwargs["sleep"] = sleep
        result = http_get(http_client, base_url, **kwargs)
        if not result.ok:
            last_error = result.error_class
            continue
        payload = result.json_payload if isinstance(result.json_payload, dict) else {}
        last = _maybe_float(payload.get("price"))
        if last is None:
            last_error = ERROR_PARSE
            continue
        out[str(instrument).upper()] = last
    if not out:
        return {}, last_error if last_error != ERROR_NONE else ERROR_PARSE
    return out, ERROR_NONE


def spot_prints_from_fixture(payload: Any, *, provider: str) -> dict[str, float]:
    if not isinstance(payload, dict):
        return {}
    out: dict[str, float] = {}
    for symbol, raw in payload.items():
        last = _maybe_float(raw if not isinstance(raw, dict) else raw.get("usd") or raw.get("price") or raw.get("last"))
        if last is not None:
            out[str(symbol).upper()] = last
    return out


def cross_check_envelopes(
    *,
    perp_mids: Mapping[str, float],
    spot: Mapping[str, float],
    spot_source: str,
    instruments: Iterable[str],
    ingested_at: datetime,
    published_at: datetime,
    divergence_bps: float = DEFAULT_DIVERGENCE_BPS,
    stale_after_seconds: int = 120,
    spot_error_class: str = ERROR_NONE,
) -> list[ObservationEnvelope]:
    """Emit spot last + derived basis + optional DQ divergence. Never invent a missing side."""
    wanted = [str(s).upper() for s in instruments]
    out: list[ObservationEnvelope] = []
    source_kind = SourceKind.EXCHANGE
    if spot_error_class != ERROR_NONE and not spot:
        for symbol in wanted:
            out.append(
                feed_status_envelope(
                    source_name=spot_source,
                    instrument=symbol,
                    ingested_at=ingested_at,
                    published_at=published_at,
                    error_class=spot_error_class,
                    metric="spot_px",
                    notes=(f"{spot_source} unavailable; no spot print invented",),
                    venue="spot",
                    source_url_or_id=f"{spot_source}:spot",
                )
            )
        return out

    for symbol in wanted:
        last = spot.get(symbol)
        if last is None:
            out.append(
                feed_status_envelope(
                    source_name=spot_source,
                    instrument=symbol,
                    ingested_at=ingested_at,
                    published_at=published_at,
                    error_class=spot_error_class if spot_error_class != ERROR_NONE else ERROR_PARSE,
                    metric="spot_px",
                    notes=(f"{spot_source} missing {symbol}; no print invented",),
                    venue="spot",
                    source_url_or_id=f"{spot_source}:spot",
                )
            )
            continue
        out.append(
            build_envelope(
                source_name=spot_source,
                source_kind=source_kind,
                source_url_or_id=f"{spot_source}:spot_px",
                instrument=symbol,
                metric="spot_px",
                value=normalize_numeric(last),
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=None,
                payload={"capture_kind": SNAPSHOT_CAPTURE_KIND, "provider": spot_source},
                extras=dict(SNAPSHOT_EXTRAS),
                stale_after_seconds=stale_after_seconds,
                venue="spot",
            )
        )
        perp = perp_mids.get(symbol)
        if perp is None or last == 0:
            continue
        basis = (perp - last) / last
        bps = abs(basis) * 10_000.0
        diverged = bps >= float(divergence_bps)
        extras = dict(SNAPSHOT_EXTRAS)
        extras["vs"] = spot_source
        quality = DataQuality.CONTRADICTED if diverged else None
        out.append(
            build_envelope(
                source_name=HL_SOURCE_NAME,
                source_kind=SourceKind.EXCHANGE,
                source_url_or_id=f"spot_cross_check:{spot_source}",
                instrument=symbol,
                metric="basis_perp_spot",
                value=normalize_numeric(basis),
                published_at=published_at,
                ingested_at=ingested_at,
                market_time=None,
                payload={
                    "derived": True,
                    "spot_source": spot_source,
                    "divergence_bps": bps,
                    "threshold_bps": divergence_bps,
                    "dq_event": "divergence" if diverged else "none",
                    "not_executable_arb": True,
                    "capture_kind": SNAPSHOT_CAPTURE_KIND,
                },
                extras=extras,
                evidence_type=EvidenceType.DERIVED,
                stale_after_seconds=stale_after_seconds,
                venue="perp",
                data_quality=quality,
            )
        )
    return out


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
