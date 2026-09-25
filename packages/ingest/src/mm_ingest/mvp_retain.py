"""Forward-only MVP retain into the existing observation pipeline.

Three HTTP calls when a caller runs :func:`capture_mvp_retain`:

1. Hyperliquid ``metaAndAssetCtxs`` for 19 BOUND perps.
2. Polygon grouped-daily (one GET) filtered to 17 US names.
3. Hyperliquid ``spotMetaAndAssetCtxs`` for DRV/USDC spot pair index 700.

DRV is PRICE-ONLY: ``mid_px`` and nothing else. A null ``midPx`` stays partial;
``markPx`` is never copied into ``mid_px``. A fixture may pass an already-fetched
spot payload; the capture helper always requests call 3.

Consecutive captures keep the caller-supplied timestamp on the claim identity
so an unchanged value does not collapse, and so a later value is not a
contradiction of the prior capture. The interval between those timestamps is
stored on the payload when a prior timestamp is supplied. Quadrant deltas are
not computed here.

PR 114 wide history backfill is not wired. ``lab retain --fixture --no-db``
does not open Postgres. ``lab retain morning`` is the Sydney morning persist path.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from mm_common.enums import DataQuality
from mm_common.hashing import normalize_numeric
from mm_common.http import ERROR_NONE
from mm_common.schemas import ObservationEnvelope
from mm_common.time import OPS_TZ, as_utc, from_unix_ms, parse_utc, utcnow
from mm_ingest.config import load_yaml, repo_root
from mm_ingest.equities.polygon import GROUPED_DAILY_PATH
from mm_ingest.pipeline import persist_envelopes
from mm_provenance.envelope import build_envelope
from mm_provenance.normalize import HL_SOURCE_KIND, HL_SOURCE_NAME, SNAPSHOT_CAPTURE_KIND

SERIES = "mvp_retain"
HISTORY_BACKFILL_WIRED = False
LIVE_NEON_ENABLED = False
HL_INFO_TYPE = "metaAndAssetCtxs"
SPOT_INFO_TYPE = "spotMetaAndAssetCtxs"
PRICE_ONLY_SYMBOL = "DRV"
SPOT_PAIR_INDEX = 700
CAPTURE_TIMEOUT_S = 90.0
EXPECTED_INSTRUMENTS = 37
NY_TZ = ZoneInfo("America/New_York")
_CASH_CLOSE = time(16, 0)

# Proof-of-write. The morning job counts rows for this capture's captured_at
# after commit and puts that count in the DM. Substitute the stored timestamp.
CAPTURE_ROWS_SQL = (
    "SELECT COUNT(*) FROM observation "
    "WHERE payload_json->>'retain_series' = 'mvp_retain' "
    "AND payload_json->>'captured_at' = :captured_at"
)
ANCHOR_EXISTS_SQL = (
    "SELECT COUNT(*) FROM observation "
    "WHERE payload_json->>'retain_series' = 'mvp_retain' "
    "AND payload_json->>'anchor_date' = :anchor_date"
)
PRIOR_CAPTURE_SQL = (
    "SELECT payload_json->>'captured_at' FROM observation "
    "WHERE payload_json->>'retain_series' = 'mvp_retain' "
    "AND COALESCE(payload_json->>'anchor_date', '') <> :anchor_date "
    "AND payload_json->>'captured_at' IS NOT NULL "
    "AND payload_json->>'captured_at' < :before "
    "ORDER BY payload_json->>'captured_at' DESC "
    "LIMIT 1"
)

_HL_FIELDS: dict[str, tuple[str, ...]] = {
    "mid_px": ("midPx", "mid"),
    "funding": ("funding",),
    "open_interest": ("openInterest", "open_interest"),
}

_BOUND_METRICS = ("open_interest", "funding", "mid_px")
_EQUITY_METRIC = "close"


@dataclass(frozen=True)
class MvpRetainSpec:
    bound_symbols: tuple[str, ...]
    bound_metrics: tuple[str, ...]
    price_only_symbol: str
    price_only_metrics: tuple[str, ...]
    spot_index: int
    spot_pair: str
    equity_symbols: tuple[str, ...]
    equity_metric: str
    dropped: frozenset[str]
    venue_queue: frozenset[str]
    blocked: frozenset[str]
    monitor: frozenset[str]

    @property
    def instrument_count(self) -> int:
        return len(self.bound_symbols) + 1 + len(self.equity_symbols)


def load_mvp_retain_spec(path: Path | None = None) -> MvpRetainSpec:
    spec_path = path or (repo_root() / "config" / "ingest" / "mvp_retain.yaml")
    data = load_yaml(spec_path)
    if data.get("forward_only") is not True or data.get("history_backfill") is not False:
        raise ValueError("mvp retain spec must be forward-only with history backfill off")
    if data.get("fixed_slot_window") is not False:
        raise ValueError("mvp retain spec must not declare a fixed slot window")
    hl = data.get("hl") or {}
    bound = hl.get("bound_perps") or {}
    names = bound.get("names") or []
    bound_symbols = tuple(str(row["symbol"]).upper() for row in names)
    bound_metrics = tuple(str(m) for m in (bound.get("metrics") or []))
    price_rows = hl.get("price_only") or []
    if len(price_rows) != 1:
        raise ValueError("mvp retain spec must list exactly one PRICE-ONLY name")
    price = price_rows[0]
    polygon = data.get("polygon") or {}
    equity_symbols = tuple(str(t).upper() for t in (polygon.get("tickers") or []))
    tiers = hl.get("tiers") or {}
    spec = MvpRetainSpec(
        bound_symbols=bound_symbols,
        bound_metrics=bound_metrics,
        price_only_symbol=str(price.get("symbol") or "").upper(),
        price_only_metrics=tuple(str(m) for m in (price.get("metrics") or [])),
        spot_index=int(price.get("spot_index")),
        spot_pair=str(price.get("pair") or ""),
        equity_symbols=equity_symbols,
        equity_metric=str(polygon.get("metric") or ""),
        dropped=frozenset(str(s).upper() for s in (hl.get("dropped") or [])),
        venue_queue=frozenset(str(s).upper() for s in (data.get("venue_queue") or [])),
        blocked=frozenset(str(s).upper() for s in (tiers.get("blocked") or [])),
        monitor=frozenset(str(s).upper() for s in (tiers.get("monitor") or [])),
    )
    _validate_spec(spec)
    _validate_calls(data.get("calls"))
    return spec


def _validate_spec(spec: MvpRetainSpec) -> None:
    if len(spec.bound_symbols) != 19 or len(set(spec.bound_symbols)) != 19:
        raise ValueError("mvp retain bound perps must be 19 distinct symbols")
    if spec.bound_metrics != _BOUND_METRICS:
        raise ValueError("bound metrics must be open_interest, funding, mid_px")
    if "LIT" not in spec.bound_symbols or "LTC" not in spec.bound_symbols:
        raise ValueError("LIT and LTC are both bound")
    if "PURR" not in spec.bound_symbols:
        raise ValueError("PURR is a bound perp")
    if spec.price_only_symbol != PRICE_ONLY_SYMBOL or spec.price_only_symbol in spec.bound_symbols:
        raise ValueError("PRICE-ONLY symbol must be DRV and not a bound perp")
    if spec.price_only_metrics != ("mid_px",):
        raise ValueError("DRV retains mid_px only")
    if spec.spot_index != SPOT_PAIR_INDEX or spec.spot_pair != "DRV/USDC":
        raise ValueError("DRV spot pair must be DRV/USDC index 700")
    if len(spec.equity_symbols) != 17 or len(set(spec.equity_symbols)) != 17:
        raise ValueError("polygon filter must be 17 distinct tickers")
    if spec.equity_metric != _EQUITY_METRIC:
        raise ValueError("equity retain metric must be close")
    if spec.instrument_count != 37:
        raise ValueError("retain membership must be 19 + 1 + 17")
    retain = set(spec.bound_symbols) | {spec.price_only_symbol} | set(spec.equity_symbols)
    if retain & spec.dropped:
        raise ValueError("dropped names must not be retained")
    if "KNT" not in spec.dropped or "KNTQ" not in spec.dropped:
        raise ValueError("KNT and KNTQ stay dropped")
    if retain & spec.venue_queue:
        raise ValueError("venue-queue names must not be retained")
    expected_queue = {"SPX", "NQ1!", "CL1!", "BTC1!", "SAMSUN", "KOSDA"}
    if spec.venue_queue != expected_queue:
        raise ValueError("venue queue drifted from the six non-grouped names")
    if spec.blocked != {"CASHCAT", "PONS"}:
        raise ValueError("blocked tier must be CASHCAT and PONS")
    if spec.monitor != {"JUP", "NIL", "DRV"}:
        raise ValueError("monitor tier must be JUP, NIL, and DRV")
    overlap = set(spec.bound_symbols) & set(spec.equity_symbols)
    if overlap or spec.price_only_symbol in spec.equity_symbols:
        raise ValueError("HL symbols and equity tickers must not overlap")


def _validate_calls(calls: Any) -> None:
    if not isinstance(calls, list) or len(calls) != 3:
        raise ValueError("mvp retain spec must list exactly three HTTP calls")
    if calls[0].get("info_type") != HL_INFO_TYPE:
        raise ValueError("call 1 must be metaAndAssetCtxs")
    if calls[1].get("path") != GROUPED_DAILY_PATH:
        raise ValueError("call 2 must be Polygon grouped-daily")
    if calls[2].get("info_type") != SPOT_INFO_TYPE:
        raise ValueError("call 3 must be spotMetaAndAssetCtxs")
    if calls[2].get("spot_index") != SPOT_PAIR_INDEX:
        raise ValueError("call 3 must target spot pair index 700")


def http_plan(session_date: date | None = None) -> tuple[dict[str, Any], ...]:
    """The only three requests this retain path is allowed to make."""
    if session_date is not None and isinstance(session_date, datetime):
        raise TypeError("session_date must be a calendar date, not a timestamp range")
    path = GROUPED_DAILY_PATH if session_date is None else GROUPED_DAILY_PATH.format(date=session_date.isoformat())
    return (
        {
            "call": 1,
            "transport": "hyperliquid.info",
            "method": "POST",
            "body": {"type": HL_INFO_TYPE},
        },
        {
            "call": 2,
            "transport": "polygon",
            "method": "GET",
            "path": path,
            "params": {"adjusted": "true", "include_otc": "false"},
        },
        {
            "call": 3,
            "transport": "hyperliquid.info",
            "method": "POST",
            "body": {"type": SPOT_INFO_TYPE},
        },
    )


def build_retain_envelopes(
    spec: MvpRetainSpec,
    *,
    meta_and_asset_ctxs: Any,
    grouped_daily: Any | None,
    captured_at: datetime,
    prior_captured_at: datetime | None = None,
    session_date: date | None = None,
    spot_meta_and_asset_ctxs: Any | None = None,
    grouped_error: str | None = None,
) -> list[ObservationEnvelope]:
    """Normalize one capture into observation envelopes. No HTTP. No database."""
    captured = as_utc(captured_at)
    if session_date is not None and isinstance(session_date, datetime):
        raise TypeError("session_date must be one calendar date")
    envelopes: list[ObservationEnvelope] = []
    perp_ctxs = _index_perp_ctxs(meta_and_asset_ctxs)
    for symbol in spec.bound_symbols:
        ctx = perp_ctxs.get(symbol)
        for metric in spec.bound_metrics:
            envelopes.append(
                _hl_metric_envelope(
                    spec,
                    symbol=symbol,
                    metric=metric,
                    ctx=ctx,
                    captured_at=captured,
                    quadrant_eligible=True,
                    venue="perp",
                    source_url_or_id=HL_INFO_TYPE,
                    resolution="metaAndAssetCtxs" if ctx is not None else "absent_from_metaAndAssetCtxs",
                )
            )
    envelopes.append(
        _drv_envelope(
            spec,
            perp_ctxs=perp_ctxs,
            spot_payload=spot_meta_and_asset_ctxs,
            captured_at=captured,
        )
    )
    envelopes.extend(
        _equity_envelopes(
            spec,
            grouped_daily=grouped_daily,
            grouped_error=grouped_error,
            captured_at=captured,
            session_date=session_date,
        )
    )
    _stamp_interval(envelopes, captured_at=captured, prior_captured_at=prior_captured_at)
    return envelopes


def capture_mvp_retain(
    spec: MvpRetainSpec,
    *,
    hl_client: Any,
    polygon_adapter: Any,
    session_date: date,
    captured_at: datetime,
    prior_captured_at: datetime | None = None,
) -> list[ObservationEnvelope]:
    """Perp meta, one grouped-daily read, then spot meta for DRV. No Postgres."""
    if isinstance(session_date, datetime) or not isinstance(session_date, date):
        raise TypeError("capture_mvp_retain takes one session date")
    ctxs = hl_client.meta_and_asset_ctxs()
    grouped, error = polygon_adapter.grouped_daily(session_date)
    spot = hl_client.spot_meta_and_asset_ctxs()
    return build_retain_envelopes(
        spec,
        meta_and_asset_ctxs=ctxs,
        grouped_daily=grouped,
        grouped_error=error,
        captured_at=captured_at,
        prior_captured_at=prior_captured_at,
        session_date=session_date,
        spot_meta_and_asset_ctxs=spot,
    )


def persist_mvp_retain(session: Any, envelopes: list[ObservationEnvelope], **kwargs: Any) -> Any:
    """Delegate to the existing observation writer.

    Live callers must not use this against Neon until Principal lifts the gate.
    ``LIVE_NEON_ENABLED`` stays false; the CLI does not call this function.
    """
    if not envelopes:
        raise ValueError("refusing to persist an empty retain capture")
    return persist_envelopes(session, envelopes, **kwargs)


def retain_from_fixture(path: Path, *, spec: MvpRetainSpec | None = None) -> dict[str, Any]:
    """Dry-run a fixture capture. Does not open a database or the network."""
    from mm_ingest.pipeline import load_fixture_file

    spec = spec or load_mvp_retain_spec()
    fixture = load_fixture_file(path)
    captured_at = _required_time(fixture.get("captured_at"), field="captured_at")
    prior_raw = fixture.get("prior_captured_at")
    prior = _required_time(prior_raw, field="prior_captured_at") if prior_raw else None
    session_raw = fixture.get("session_date")
    session_date = date.fromisoformat(str(session_raw)) if session_raw else None
    envelopes = build_retain_envelopes(
        spec,
        meta_and_asset_ctxs=fixture.get("metaAndAssetCtxs"),
        grouped_daily=fixture.get("polygon_grouped"),
        captured_at=captured_at,
        prior_captured_at=prior,
        session_date=session_date,
        spot_meta_and_asset_ctxs=fixture.get("spotMetaAndAssetCtxs"),
        grouped_error=fixture.get("grouped_error"),
    )
    return public_summary(
        envelopes,
        spec=spec,
        captured_at=captured_at,
        session_date=session_date,
    )


def public_summary(
    envelopes: list[ObservationEnvelope],
    *,
    spec: MvpRetainSpec,
    captured_at: datetime,
    session_date: date | None,
) -> dict[str, Any]:
    metrics_by: dict[str, list[str]] = {}
    for envelope in envelopes:
        bucket = metrics_by.setdefault(envelope.instrument, [])
        if envelope.metric not in bucket:
            bucket.append(envelope.metric)
    intervals = sorted({e.payload.get("interval_seconds") for e in envelopes if "interval_seconds" in e.payload})
    quadrant_labels = [e for e in envelopes if e.metric in {"quadrant", "quadrant_label"}]
    return {
        "live": False,
        "gated": True,
        "neon": False,
        "history_backfill": False,
        "backfill_wired": HISTORY_BACKFILL_WIRED,
        "sm_slot_window": False,
        "calls": len(http_plan(session_date)),
        "call_plan": list(http_plan(session_date)),
        "instruments": len(metrics_by),
        "bound_perps": sum(1 for symbol in spec.bound_symbols if symbol in metrics_by),
        "price_only": 1 if spec.price_only_symbol in metrics_by else 0,
        "equities": sum(1 for symbol in spec.equity_symbols if symbol in metrics_by),
        "envelopes": len(envelopes),
        "symbols": list(metrics_by),
        "drv_metrics": metrics_by.get(spec.price_only_symbol, []),
        "purr_metrics": metrics_by.get("PURR", []),
        "knt_present": any(symbol in metrics_by for symbol in ("KNT", "KNTQ", "KNTUSDC")),
        "venue_queue_present": any(symbol in metrics_by for symbol in spec.venue_queue),
        "captured_at": as_utc(captured_at).isoformat(),
        "interval_seconds": intervals[0] if len(intervals) == 1 else None,
        "quadrant_labels": len(quadrant_labels),
        "market_time_null_hl": sum(
            1 for e in envelopes if e.instrument in spec.bound_symbols and e.market_time is None
        ),
    }


def _stamp_interval(
    envelopes: list[ObservationEnvelope],
    *,
    captured_at: datetime,
    prior_captured_at: datetime | None,
) -> None:
    if prior_captured_at is None:
        return
    prior = as_utc(prior_captured_at)
    seconds = int((captured_at - prior).total_seconds())
    if seconds <= 0:
        raise ValueError("prior capture must be strictly earlier than this capture")
    for envelope in envelopes:
        envelope.payload["prior_captured_at"] = prior.isoformat()
        envelope.payload["interval_seconds"] = seconds
        envelope.payload["pair"] = "consecutive_capture"


def _drv_envelope(
    spec: MvpRetainSpec,
    *,
    perp_ctxs: dict[str, dict[str, Any]],
    spot_payload: Any | None,
    captured_at: datetime,
) -> ObservationEnvelope:
    """PRICE-ONLY. Never emits funding or open interest."""
    if spot_payload is not None:
        ctx, status = _find_drv_spot(spot_payload)
        if status == "spot":
            return _hl_metric_envelope(
                spec,
                symbol=spec.price_only_symbol,
                metric="mid_px",
                ctx=ctx,
                captured_at=captured_at,
                quadrant_eligible=False,
                venue="spot",
                source_url_or_id=SPOT_INFO_TYPE,
                resolution="spot_index_700",
            )
        return _hl_metric_envelope(
            spec,
            symbol=spec.price_only_symbol,
            metric="mid_px",
            ctx=None,
            captured_at=captured_at,
            quadrant_eligible=False,
            venue="spot",
            source_url_or_id=SPOT_INFO_TYPE,
            resolution=status,
        )
    perp_ctx = perp_ctxs.get(spec.price_only_symbol)
    if perp_ctx is not None:
        return _hl_metric_envelope(
            spec,
            symbol=spec.price_only_symbol,
            metric="mid_px",
            ctx=perp_ctx,
            captured_at=captured_at,
            quadrant_eligible=False,
            venue="spot",
            source_url_or_id=HL_INFO_TYPE,
            resolution="perp_name_price_only",
        )
    return _hl_metric_envelope(
        spec,
        symbol=spec.price_only_symbol,
        metric="mid_px",
        ctx=None,
        captured_at=captured_at,
        quadrant_eligible=False,
        venue="spot",
        source_url_or_id=HL_INFO_TYPE,
        resolution="absent_from_metaAndAssetCtxs",
    )


def _find_drv_spot(payload: Any) -> tuple[dict[str, Any] | None, str]:
    """Locate DRV/USDC @700 by universe position, not by ctxs[700]."""
    if not isinstance(payload, list) or len(payload) < 2:
        return None, "absent"
    meta, ctxs = payload[0], payload[1]
    if not isinstance(meta, dict) or not isinstance(ctxs, list):
        return None, "absent"
    universe = meta.get("universe") or []
    if not isinstance(universe, list):
        return None, "absent"
    found: dict[str, Any] | None = None
    for i, asset in enumerate(universe):
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "").upper()
        index = asset.get("index")
        if index != SPOT_PAIR_INDEX and name not in {"@700", "DRV/USDC"}:
            continue
        token_ids = asset.get("tokens")
        resolved = _token_names(meta, token_ids) if isinstance(token_ids, list) else None
        tokens_ok = resolved == ["DRV", "USDC"] or (resolved is None and name == "DRV/USDC")
        if name == "@700" and resolved is None:
            tokens_ok = False
        if name in {"@700", "DRV/USDC"} and index == SPOT_PAIR_INDEX and tokens_ok:
            if found is not None:
                return None, "mismatch"
            ctx = ctxs[i] if i < len(ctxs) and isinstance(ctxs[i], dict) else {}
            found = ctx
            continue
        return None, "mismatch"
    if found is None:
        return None, "absent"
    return found, "spot"


def _token_names(meta: dict[str, Any], token_ids: list[Any]) -> list[str] | None:
    tokens = meta.get("tokens")
    if not isinstance(tokens, list):
        return None
    by_index: dict[Any, str] = {}
    for token in tokens:
        if isinstance(token, dict) and token.get("index") is not None:
            by_index[token.get("index")] = str(token.get("name") or "").upper()
    return [by_index.get(token_id, "") for token_id in token_ids]


def _equity_envelopes(
    spec: MvpRetainSpec,
    *,
    grouped_daily: Any | None,
    grouped_error: str | None,
    captured_at: datetime,
    session_date: date | None,
) -> list[ObservationEnvelope]:
    failed = grouped_error not in (None, "", ERROR_NONE)
    rows = {} if failed else _filter_grouped(grouped_daily, set(spec.equity_symbols))
    out: list[ObservationEnvelope] = []
    for ticker in spec.equity_symbols:
        row = rows.get(ticker)
        close = None if row is None else row.get("c")
        bar_ms = None if row is None else row.get("t")
        market_time = from_unix_ms(int(bar_ms)) if bar_ms is not None else None
        missing: tuple[str, ...] = ()
        if close is None:
            missing = ("c",)
        elif bar_ms is None:
            missing = ("t",)
        resolution = "grouped_daily"
        if failed:
            resolution = f"grouped_daily_{grouped_error}"
        elif row is None:
            resolution = "absent_from_grouped_daily"
        payload = _policy_payload(
            spec,
            symbol=ticker,
            quadrant_eligible=False,
            resolution=resolution,
            raw=row if row is not None else {},
        )
        if session_date is not None:
            payload["session_date"] = session_date.isoformat()
        if failed:
            payload["error_class"] = grouped_error
        out.append(
            _envelope(
                source_name="polygon",
                source_url_or_id=f"grouped_daily:{ticker}",
                instrument=ticker,
                metric=spec.equity_metric,
                value=normalize_numeric(close) if close is not None else None,
                captured_at=captured_at,
                market_time=market_time,
                payload=payload,
                missing_fields=missing,
                venue="equity",
            )
        )
    return out


def _filter_grouped(payload: Any, wanted: set[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    results = payload.get("results") or []
    if not isinstance(results, list):
        return {}
    found: dict[str, dict[str, Any]] = {}
    for row in results:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("T") or "").upper()
        if ticker in wanted and ticker not in found:
            found[ticker] = row
    return found


def _hl_metric_envelope(
    spec: MvpRetainSpec,
    *,
    symbol: str,
    metric: str,
    ctx: dict[str, Any] | None,
    captured_at: datetime,
    quadrant_eligible: bool,
    venue: str,
    source_url_or_id: str,
    resolution: str,
) -> ObservationEnvelope:
    keys = _HL_FIELDS[metric]
    # midPx null stays missing. markPx is not a stand-in for mid.
    raw = _ctx_value(ctx or {}, *keys)
    missing = () if raw is not None else keys
    payload = _policy_payload(
        spec,
        symbol=symbol,
        quadrant_eligible=quadrant_eligible,
        resolution=resolution,
        raw=ctx or {},
    )
    payload["hl_type"] = source_url_or_id if source_url_or_id in {HL_INFO_TYPE, SPOT_INFO_TYPE} else HL_INFO_TYPE
    return _envelope(
        source_name=HL_SOURCE_NAME,
        source_url_or_id=source_url_or_id,
        instrument=symbol,
        metric=metric,
        value=normalize_numeric(raw) if raw is not None else None,
        captured_at=captured_at,
        market_time=None,
        payload=payload,
        missing_fields=missing,
        venue=venue,
    )


def _envelope(
    *,
    source_name: str,
    source_url_or_id: str,
    instrument: str,
    metric: str,
    value: str | None,
    captured_at: datetime,
    market_time: datetime | None,
    payload: dict[str, Any],
    missing_fields: tuple[str, ...],
    venue: str,
) -> ObservationEnvelope:
    captured = as_utc(captured_at)
    captured_iso = captured.isoformat()
    extras = {
        "capture_kind": SNAPSHOT_CAPTURE_KIND,
        "retain_series": SERIES,
        "captured_at": captured_iso,
    }
    payload = dict(payload)
    payload["captured_at"] = captured_iso
    return build_envelope(
        source_name=source_name,
        source_kind=HL_SOURCE_KIND,
        source_url_or_id=source_url_or_id,
        instrument=instrument,
        metric=metric,
        value=value,
        published_at=captured,
        ingested_at=captured,
        market_time=market_time,
        payload=payload,
        extras=extras,
        historical=False,
        missing_fields=missing_fields,
        venue=venue,
        data_quality=DataQuality.PARTIAL if missing_fields else None,
    )


def _policy_payload(
    spec: MvpRetainSpec,
    *,
    symbol: str,
    quadrant_eligible: bool,
    resolution: str,
    raw: dict[str, Any],
) -> dict[str, Any]:
    tier = None
    if symbol in spec.blocked:
        tier = "blocked"
    elif symbol in spec.monitor:
        tier = "monitor"
    return {
        "retain_series": SERIES,
        "forward_only": True,
        "history_backfill": False,
        "policy": "store_only",
        "quadrant_eligible": quadrant_eligible,
        "watch_tier": tier,
        "resolution": resolution,
        "raw": raw,
    }


def _index_perp_ctxs(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) < 2:
        return {}
    meta, ctxs = payload[0], payload[1]
    universe = meta.get("universe") if isinstance(meta, dict) else None
    if not isinstance(universe, list) or not isinstance(ctxs, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for i, asset in enumerate(universe):
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "").upper()
        if not name:
            continue
        ctx = ctxs[i] if i < len(ctxs) and isinstance(ctxs[i], dict) else {}
        out[name] = ctx
    return out


def _ctx_value(ctx: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in ctx and ctx[key] is not None:
            return ctx[key]
    return None


def _required_time(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        return as_utc(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"fixture {field} must be an explicit UTC timestamp")
    return parse_utc(value)


@dataclass(frozen=True)
class MorningCaptureResult:
    """One morning attempt. ``line`` is the DM status line. Never raises to the job."""

    line: str
    capture_rows: int | None
    anchor_date: str | None
    captured_at: str | None
    prior_captured_at: str | None
    wrote: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "line": self.line,
            "capture_rows": self.capture_rows,
            "anchor_date": self.anchor_date,
            "captured_at": self.captured_at,
            "prior_captured_at": self.prior_captured_at,
            "wrote": self.wrote,
        }


def sydney_anchor_date(scheduled_for: str | datetime) -> date:
    """Sydney calendar date of the stamp's ``scheduled_for`` anchor."""
    if isinstance(scheduled_for, datetime):
        stamp = as_utc(scheduled_for)
    else:
        text = str(scheduled_for or "").strip()
        if not text:
            raise ValueError("scheduled_for missing")
        stamp = parse_utc(text)
    return stamp.astimezone(OPS_TZ).date()


def us_cash_session_date(ts: datetime) -> date:
    """Last completed US cash session date (16:00 America/New_York, weekdays)."""
    local = as_utc(ts).astimezone(NY_TZ)
    day = local.date()
    if local.time() < _CASH_CLOSE:
        day = day - timedelta(days=1)
    while day.weekday() >= 5:
        day = day - timedelta(days=1)
    return day


def capture_failed_line(reason: str) -> str:
    text = " ".join(str(reason or "").split())
    if text == "timeout":
        return "CAPTURE: FAILED timeout"
    if not text:
        text = "capture"
    if len(text) > 80:
        text = text[:80]
    return f"CAPTURE: FAILED {text}"


def capture_exists_line(anchor_date: date) -> str:
    return f"CAPTURE: exists for {anchor_date.isoformat()}, not rewritten"


def capture_rows_line(*, rows: int, captured_at: str, prior_captured_at: str | None, instruments: int) -> str:
    prior = prior_captured_at or "none"
    return f"CAPTURE: {rows}/{instruments} rows @ {captured_at} · prior {prior}"


def _failed_result(reason: str, *, anchor_date: str | None = None) -> MorningCaptureResult:
    return MorningCaptureResult(
        line=capture_failed_line(reason),
        capture_rows=None,
        anchor_date=anchor_date,
        captured_at=None,
        prior_captured_at=None,
        wrote=False,
    )


def morning_capture_if_sending(
    *,
    already_delivered: bool,
    run: Callable[[], MorningCaptureResult],
) -> MorningCaptureResult | None:
    """Capture only on the path that is going to send. ``already_delivered`` does not."""
    if already_delivered:
        return None
    return run()


def _dsn_present(dsn: str | None) -> bool:
    return bool(dsn and str(dsn).strip())


@contextmanager
def _neon_session(dsn: str, *, statement_timeout_ms: int = 15000):
    """Short-lived Neon session. Does not log the DSN."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from mm_memory.db import normalize_dsn

    engine = create_engine(
        normalize_dsn(dsn),
        echo=False,
        future=True,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 8},
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    session = factory()
    try:
        session.execute(text(f"SET LOCAL statement_timeout = {int(statement_timeout_ms)}"))
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


class NeonRetainStore:
    """Read and write MVP retain rows. Callers supply a DSN; this store does not invent one."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def count_for_anchor(self, anchor_date: str) -> int:
        from sqlalchemy import text

        with _neon_session(self._dsn) as session:
            value = session.execute(text(ANCHOR_EXISTS_SQL), {"anchor_date": anchor_date}).scalar()
        return _as_count(value)

    def prior_captured_at(self, anchor_date: str, before: str) -> str | None:
        from sqlalchemy import text

        with _neon_session(self._dsn) as session:
            value = session.execute(
                text(PRIOR_CAPTURE_SQL),
                {"anchor_date": anchor_date, "before": before},
            ).scalar()
        if value is None:
            return None
        text_value = str(value).strip()
        return text_value or None

    def persist(self, envelopes: list[ObservationEnvelope]) -> None:
        with _neon_session(self._dsn, statement_timeout_ms=20000) as session:
            persist_mvp_retain(session, envelopes)

    def count_for_captured_at(self, captured_at: str) -> int:
        from sqlalchemy import text

        with _neon_session(self._dsn) as session:
            value = session.execute(text(CAPTURE_ROWS_SQL), {"captured_at": captured_at}).scalar()
        return _as_count(value)


def _as_count(value: Any) -> int:
    """COUNT(*) may arrive as int or Decimal. Anything else is not a row count."""
    if isinstance(value, bool) or value is None:
        raise RuntimeError("read-back mismatch")
    if isinstance(value, int):
        count = value
    else:
        try:
            text = str(value).strip()
            if not text or not text.lstrip("-").isdigit():
                raise RuntimeError("read-back mismatch")
            count = int(text)
        except RuntimeError:
            raise
        except (TypeError, ValueError) as exc:
            raise RuntimeError("read-back mismatch") from exc
    if count < 0:
        raise RuntimeError("read-back mismatch")
    return count


def _run_bounded(fn: Callable[[], MorningCaptureResult], timeout_s: float) -> MorningCaptureResult:
    if timeout_s <= 0:
        return _failed_result("timeout")
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["result"] = fn()
        except Exception:
            box["error"] = "capture"

    thread = threading.Thread(target=target, name="mvp-retain-morning", daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        return _failed_result("timeout")
    if "error" in box:
        return _failed_result("capture")
    result = box.get("result")
    if not isinstance(result, MorningCaptureResult):
        return _failed_result("capture")
    return result


def run_morning_capture(
    *,
    scheduled_for: str | datetime,
    dsn: str | None = None,
    now: datetime | None = None,
    timeout_s: float = CAPTURE_TIMEOUT_S,
    store: Any | None = None,
    hl_client: Any | None = None,
    polygon_adapter: Any | None = None,
    spec: MvpRetainSpec | None = None,
) -> MorningCaptureResult:
    """Fetch, persist, and read back one capture for the Sydney anchor date.

    Any failure becomes a ``CAPTURE: FAILED`` line. The caller still delivers.
    A second call for the same anchor date does not write.
    """
    try:
        anchor = sydney_anchor_date(scheduled_for)
    except (TypeError, ValueError):
        return _failed_result("anchor missing")
    anchor_token = anchor.isoformat()
    if store is None and not _dsn_present(dsn):
        return _failed_result("dsn missing", anchor_date=anchor_token)
    if timeout_s <= 0:
        return _failed_result("timeout", anchor_date=anchor_token)

    def body() -> MorningCaptureResult:
        return _morning_capture_body(
            anchor=anchor,
            dsn=dsn,
            now=now,
            store=store,
            hl_client=hl_client,
            polygon_adapter=polygon_adapter,
            spec=spec,
        )

    result = _run_bounded(body, timeout_s)
    if result.anchor_date is None and result.line.startswith("CAPTURE: FAILED"):
        return MorningCaptureResult(
            line=result.line,
            capture_rows=result.capture_rows,
            anchor_date=anchor_token,
            captured_at=result.captured_at,
            prior_captured_at=result.prior_captured_at,
            wrote=result.wrote,
        )
    return result


def _morning_capture_body(
    *,
    anchor: date,
    dsn: str | None,
    now: datetime | None,
    store: Any | None,
    hl_client: Any | None,
    polygon_adapter: Any | None,
    spec: MvpRetainSpec | None,
) -> MorningCaptureResult:
    anchor_token = anchor.isoformat()
    active = store if store is not None else NeonRetainStore(str(dsn))
    try:
        existing = active.count_for_anchor(anchor_token)
    except Exception:
        return _failed_result("db error", anchor_date=anchor_token)
    if existing > 0:
        return MorningCaptureResult(
            line=capture_exists_line(anchor),
            capture_rows=None,
            anchor_date=anchor_token,
            captured_at=None,
            prior_captured_at=None,
            wrote=False,
        )
    captured = as_utc(now or utcnow())
    captured_iso = captured.isoformat()
    try:
        prior_raw = active.prior_captured_at(anchor_token, captured_iso)
    except Exception:
        return _failed_result("db error", anchor_date=anchor_token)
    prior = _prior_or_none(prior_raw, captured)
    owned_hl = hl_client is None
    owned_poly = polygon_adapter is None
    hl = hl_client
    polygon = polygon_adapter
    try:
        try:
            if owned_hl or owned_poly:
                from mm_ingest.equities.polygon import PolygonEquitiesAdapter
                from mm_ingest.hl_info import HyperliquidInfoClient

                if owned_hl:
                    hl = HyperliquidInfoClient(timeout=20.0, max_attempts=2)
                if owned_poly:
                    polygon = PolygonEquitiesAdapter(timeout=20.0, max_attempts=2)
            envelopes = capture_mvp_retain(
                spec or load_mvp_retain_spec(),
                hl_client=hl,
                polygon_adapter=polygon,
                session_date=us_cash_session_date(captured),
                captured_at=captured,
                prior_captured_at=prior,
            )
        except Exception:
            return _failed_result("fetch", anchor_date=anchor_token)
        for envelope in envelopes:
            envelope.payload["anchor_date"] = anchor_token
        try:
            active.persist(envelopes)
        except Exception:
            return _failed_result("db error", anchor_date=anchor_token)
        try:
            rows = active.count_for_captured_at(captured_iso)
        except Exception:
            return _failed_result("read-back mismatch", anchor_date=anchor_token)
    finally:
        if owned_hl and hl is not None:
            hl.close()
        if owned_poly and polygon is not None:
            polygon.close()
    instruments = EXPECTED_INSTRUMENTS
    if spec is not None:
        instruments = spec.instrument_count
    prior_iso = as_utc(prior).isoformat() if prior is not None else None
    return MorningCaptureResult(
        line=capture_rows_line(
            rows=rows,
            captured_at=captured_iso,
            prior_captured_at=prior_iso,
            instruments=instruments,
        ),
        capture_rows=rows,
        anchor_date=anchor_token,
        captured_at=captured_iso,
        prior_captured_at=prior_iso,
        wrote=True,
    )


def _prior_or_none(raw: str | None, captured: datetime) -> datetime | None:
    if not raw:
        return None
    try:
        prior = parse_utc(str(raw))
    except (TypeError, ValueError):
        return None
    if prior >= captured:
        return None
    return prior
