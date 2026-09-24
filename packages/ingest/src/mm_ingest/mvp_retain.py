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

PR 114 wide history backfill is not wired. The CLI refuses to open Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from mm_common.enums import DataQuality
from mm_common.hashing import normalize_numeric
from mm_common.http import ERROR_NONE
from mm_common.schemas import ObservationEnvelope
from mm_common.time import as_utc, from_unix_ms
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
    extras = {
        "capture_kind": SNAPSHOT_CAPTURE_KIND,
        "retain_series": SERIES,
        "captured_at": captured.isoformat(),
    }
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
    from mm_common.time import parse_utc

    return parse_utc(value)
