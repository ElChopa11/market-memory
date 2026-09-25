"""Hyperliquid conditions from Market Memory observations (or a frozen fixture).

Live fallback uses the read-only public /info allowlist only — no wallet/user types.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from mm_common.hashing import normalize_numeric
from mm_common.time import as_utc, parse_utc
from mm_ingest.hl_info import HyperliquidInfoClient, HyperliquidInfoError
from mm_memory.models import Observation
from mm_memory.queries import what_did_we_know
from mm_provenance.normalize import HL_BASE_URL, normalize_asset_snapshot, normalize_liquidations
from mm_briefing.models import HL_BRIEF_INSTRUMENTS, HLInstrumentState, HLMetric, worst_quality

SNAPSHOT_METRICS = ("funding", "open_interest", "mid_px", "mark_px", "oracle_px")
LIVE_INFO_SOURCE = "hyperliquid.info /info"


def hl_from_payload(payload: dict[str, Any]) -> tuple[HLInstrumentState, ...]:
    instruments = payload.get("instruments") or []
    out: list[HLInstrumentState] = []
    for row in instruments:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("instrument") or "").upper()
        metrics_raw = row.get("metrics") or {}
        metrics: dict[str, HLMetric] = {}
        if isinstance(metrics_raw, dict):
            for name, spec in metrics_raw.items():
                if not isinstance(spec, dict):
                    continue
                metrics[str(name)] = _metric_from_dict(symbol, str(name), spec)
        liqs = tuple(
            _metric_from_dict(symbol, "liquidation", spec)
            for spec in (row.get("liquidations") or [])
            if isinstance(spec, dict)
        )
        levels = row.get("levels") or {}
        level_pairs = tuple(sorted((str(k), str(v)) for k, v in levels.items())) if isinstance(levels, dict) else ()
        quality = str(row.get("data_quality") or "ok")
        for metric in metrics.values():
            quality = worst_quality(quality, metric.data_quality)
        as_of_raw = row.get("as_of_knowledge") or payload.get("as_of_knowledge")
        as_of = parse_utc(str(as_of_raw)) if as_of_raw else None
        if as_of is not None:
            metrics = {
                name: metric if metric.as_of_knowledge is not None else replace(metric, as_of_knowledge=as_of)
                for name, metric in metrics.items()
            }
            liqs = tuple(
                metric if metric.as_of_knowledge is not None else replace(metric, as_of_knowledge=as_of)
                for metric in liqs
            )
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics=metrics,
                liquidations=liqs,
                levels=level_pairs,
                data_quality=quality,
                as_of_knowledge=as_of,
                source=str(row.get("source") or payload.get("source") or "hyperliquid.info"),
            )
        )
    return tuple(sorted(out, key=lambda row: row.instrument))


def hl_from_memory(
    session: Session,
    as_of: datetime,
    *,
    instruments: tuple[str, ...] = HL_BRIEF_INSTRUMENTS,
    lookback: timedelta = timedelta(hours=18),
) -> tuple[HLInstrumentState, ...]:
    knowledge = as_utc(as_of)
    rows = what_did_we_know(session, knowledge)
    wanted = {symbol.upper() for symbol in instruments}
    grouped: dict[str, list[Observation]] = {symbol: [] for symbol in wanted}
    for row in rows:
        if row.instrument in grouped:
            grouped[row.instrument].append(row)
    out: list[HLInstrumentState] = []
    window_start = knowledge - lookback
    for symbol in sorted(wanted):
        obs = grouped[symbol]
        metrics: dict[str, HLMetric] = {}
        for name in SNAPSHOT_METRICS:
            latest = _latest(obs, name)
            if latest is not None:
                metrics[name] = _metric_from_observation(latest)
        prior_oi = _previous(obs, "open_interest", after=metrics.get("open_interest"))
        if prior_oi is not None:
            metrics["prior_open_interest"] = _metric_from_observation(prior_oi)
        liqs = tuple(
            _metric_from_observation(row)
            for row in obs
            if row.metric == "liquidation" and _obs_time(row) >= window_start
        )
        levels = _levels_from_obs(obs, metrics)
        quality = "ok" if obs else "unavailable"
        for metric in metrics.values():
            quality = worst_quality(quality, metric.data_quality)
        if not metrics:
            quality = worst_quality(quality, "unavailable")
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics=metrics,
                liquidations=liqs,
                levels=levels,
                data_quality=quality,
                as_of_knowledge=knowledge,
                source="market_memory",
            )
        )
    return tuple(out)


def hl_has_metrics(states: tuple[HLInstrumentState, ...]) -> bool:
    return any(state.metrics for state in states)


def ensure_hl_instruments(
    states: tuple[HLInstrumentState, ...],
    *,
    instruments: tuple[str, ...] = HL_BRIEF_INSTRUMENTS,
    as_of: datetime | None = None,
    source: str = "none",
) -> tuple[HLInstrumentState, ...]:
    by_inst = {row.instrument: row for row in states}
    out: list[HLInstrumentState] = []
    for symbol in instruments:
        if symbol in by_inst:
            out.append(by_inst[symbol])
            continue
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics={},
                liquidations=(),
                levels=(),
                data_quality="unavailable",
                as_of_knowledge=as_of,
                source=source,
            )
        )
    extras = [row for row in states if row.instrument not in instruments]
    return tuple(out + extras)


def hl_from_live_info(
    client: HyperliquidInfoClient,
    *,
    instruments: tuple[str, ...] = HL_BRIEF_INSTRUMENTS,
    captured_at: datetime,
    include_liquidations: bool = True,
) -> tuple[HLInstrumentState, ...]:
    """Snapshot via allowlisted public /info types. Does not invent missing fields.

    ``prevDayPx`` is read from the same ``metaAndAssetCtxs`` body. The close
    path sets ``include_liquidations`` false so that one call is the whole fetch.
    """
    wanted = tuple(symbol.upper() for symbol in instruments)
    captured = as_utc(captured_at)
    try:
        ctxs = client.meta_and_asset_ctxs()
    except HyperliquidInfoError as exc:
        return ensure_hl_instruments(
            (),
            instruments=wanted,
            as_of=captured,
            source=f"{LIVE_INFO_SOURCE} unavailable ({exc.__class__.__name__})",
        )
    envelopes = normalize_asset_snapshot(
        ctxs,
        instruments=wanted,
        ingested_at=captured,
        published_at=captured,
    )
    grouped: dict[str, dict[str, HLMetric]] = {symbol: {} for symbol in wanted}
    qualities: dict[str, str] = {symbol: "unavailable" for symbol in wanted}
    for envelope in envelopes:
        symbol = envelope.instrument.upper()
        if symbol not in grouped:
            continue
        if envelope.metric not in SNAPSHOT_METRICS:
            continue
        value = envelope.identity.value
        if value is None:
            value = envelope.payload.get("value")
        metric = HLMetric(
            instrument=symbol,
            metric=envelope.metric,
            value=None if value is None else str(value),
            observation_id=None,
            claim_hash=envelope.claim_hash,
            data_quality=envelope.data_quality.value,
            market_time=envelope.market_time,
            as_of_knowledge=envelope.as_of_knowledge or envelope.ingested_at,
            source_url=f"{HL_BASE_URL} type={envelope.source_url_or_id}",
        )
        grouped[symbol][envelope.metric] = metric
        if value is not None:
            qualities[symbol] = worst_quality(qualities[symbol] if qualities[symbol] != "unavailable" else "ok", metric.data_quality)
        else:
            qualities[symbol] = worst_quality(qualities[symbol], "partial" if grouped[symbol] else "unavailable")

    for symbol, raw_prev in _prev_day_px_by_name(ctxs).items():
        if symbol not in grouped:
            continue
        grouped[symbol]["prev_day_px"] = HLMetric(
            instrument=symbol,
            metric="prev_day_px",
            value=raw_prev,
            observation_id=None,
            claim_hash=None,
            data_quality="ok",
            market_time=captured,
            as_of_knowledge=captured,
            source_url=f"{HL_BASE_URL} type=metaAndAssetCtxs",
        )
        qualities[symbol] = worst_quality(
            "ok" if qualities[symbol] == "unavailable" else qualities[symbol],
            "ok",
        )

    liquidations: dict[str, list[HLMetric]] = {symbol: [] for symbol in wanted}
    if include_liquidations:
        for coin in wanted:
            try:
                trades = client.recent_trades(coin)
            except HyperliquidInfoError:
                continue
            for envelope in normalize_liquidations(trades, ingested_at=captured):
                if envelope.instrument.upper() != coin:
                    continue
                value = envelope.identity.value
                liquidations[coin].append(
                    HLMetric(
                        instrument=coin,
                        metric="liquidation",
                        value=None if value is None else str(value),
                        observation_id=None,
                        claim_hash=envelope.claim_hash,
                        data_quality=envelope.data_quality.value,
                        market_time=envelope.market_time,
                        as_of_knowledge=envelope.as_of_knowledge or envelope.ingested_at,
                        source_url=f"{HL_BASE_URL} type=recentTrades",
                    )
                )

    out: list[HLInstrumentState] = []
    for symbol in wanted:
        metrics = grouped[symbol]
        quality = qualities[symbol]
        for metric in metrics.values():
            quality = worst_quality(quality, metric.data_quality)
        if not metrics:
            quality = "unavailable"
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics=metrics,
                liquidations=tuple(liquidations[symbol]),
                levels=_levels_from_obs([], metrics),
                data_quality=quality,
                as_of_knowledge=captured,
                source=LIVE_INFO_SOURCE,
            )
        )
    return tuple(out)


def _prev_day_px_by_name(meta_and_ctxs: Any) -> dict[str, str]:
    """``prevDayPx`` from the metaAndAssetCtxs body the snapshot call already fetched."""
    if not isinstance(meta_and_ctxs, list) or len(meta_and_ctxs) < 2:
        return {}
    meta, rows = meta_and_ctxs[0], meta_and_ctxs[1]
    universe = meta.get("universe", []) if isinstance(meta, dict) else []
    if not isinstance(rows, list):
        return {}
    out: dict[str, str] = {}
    for idx, asset in enumerate(universe):
        if not isinstance(asset, dict) or idx >= len(rows):
            continue
        ctx = rows[idx]
        if not isinstance(ctx, dict):
            continue
        raw = ctx.get("prevDayPx")
        if raw is None or raw == "":
            continue
        out[str(asset.get("name", "")).upper()] = str(raw)
    return out


def hl_states_from_ctx_snapshot(
    payload: dict[str, Any],
    *,
    captured_at: datetime,
) -> tuple[HLInstrumentState, ...]:
    """Build close-path states from a stored metaAndAssetCtxs extract. No network."""
    captured = as_utc(captured_at)
    order = tuple(str(name).upper() for name in (payload.get("order") or ()))
    ctxs = payload.get("ctx") or {}
    out: list[HLInstrumentState] = []
    field_map = (
        ("mid_px", "midPx"),
        ("prev_day_px", "prevDayPx"),
        ("funding", "funding"),
        ("open_interest", "openInterest"),
        ("mark_px", "markPx"),
        ("oracle_px", "oraclePx"),
    )
    for symbol in order:
        spec = ctxs.get(symbol) if isinstance(ctxs, dict) else None
        if not isinstance(spec, dict):
            out.append(
                HLInstrumentState(
                    instrument=symbol,
                    metrics={},
                    liquidations=(),
                    levels=(),
                    data_quality="unavailable",
                    as_of_knowledge=captured,
                    source=LIVE_INFO_SOURCE,
                )
            )
            continue
        metrics: dict[str, HLMetric] = {}
        for metric_name, key in field_map:
            raw = spec.get(key)
            if raw is None or raw == "":
                continue
            metrics[metric_name] = HLMetric(
                instrument=symbol,
                metric=metric_name,
                value=str(raw),
                observation_id=None,
                claim_hash=None,
                data_quality="ok",
                market_time=captured,
                as_of_knowledge=captured,
                source_url=f"{HL_BASE_URL} type=metaAndAssetCtxs",
            )
        quality = "ok" if metrics.get("mid_px") is not None else "unavailable"
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics=metrics,
                liquidations=(),
                levels=_levels_from_obs([], metrics),
                data_quality=quality,
                as_of_knowledge=captured,
                source=str(payload.get("source") or LIVE_INFO_SOURCE),
            )
        )
    return tuple(out)


def oi_change_pct(state: HLInstrumentState) -> float | None:
    current = state.metric("open_interest")
    prior = state.metric("prior_open_interest")
    if current is None or prior is None or current.value is None or prior.value is None:
        return None
    try:
        now = float(current.value)
        then = float(prior.value)
    except ValueError:
        return None
    if then == 0:
        return None
    return (now - then) / then * 100.0


def funding_value(state: HLInstrumentState) -> float | None:
    metric = state.metric("funding")
    if metric is None or metric.value is None:
        return None
    try:
        return float(metric.value)
    except ValueError:
        return None


def liquidation_size_sum(state: HLInstrumentState) -> float:
    total = 0.0
    for row in state.liquidations:
        if row.value is None:
            continue
        try:
            total += float(row.value)
        except ValueError:
            continue
    return total


def basis_mark_oracle(state: HLInstrumentState) -> float | None:
    mark = state.metric("mark_px")
    oracle = state.metric("oracle_px")
    if mark is None or oracle is None or mark.value is None or oracle.value is None:
        return None
    try:
        return float(mark.value) - float(oracle.value)
    except ValueError:
        return None


def _metric_from_dict(instrument: str, metric: str, spec: dict[str, Any]) -> HLMetric:
    market_time = spec.get("market_time")
    parsed = parse_utc(str(market_time)) if market_time else None
    as_of_raw = spec.get("as_of_knowledge") or spec.get("ingested_at")
    as_of = parse_utc(str(as_of_raw)) if as_of_raw else None
    value = spec.get("value")
    return HLMetric(
        instrument=instrument,
        metric=metric,
        value=None if value is None else str(value),
        observation_id=str(spec["observation_id"]) if spec.get("observation_id") else None,
        claim_hash=str(spec["claim_hash"]) if spec.get("claim_hash") else None,
        data_quality=str(spec.get("data_quality") or "ok"),
        market_time=parsed,
        as_of_knowledge=as_of,
        source_url=str(spec["source_url"]) if spec.get("source_url") else None,
    )


def _metric_from_observation(row: Observation) -> HLMetric:
    payload = row.payload_json or {}
    value = payload.get("value")
    if value is None:
        value = normalize_numeric(payload.get("raw")) if isinstance(payload.get("raw"), (int, float, str)) else None
    source_url = row.source_url_or_id
    return HLMetric(
        instrument=row.instrument,
        metric=row.metric,
        value=None if value is None else str(value),
        observation_id=row.id,
        claim_hash=row.claim_hash,
        data_quality=row.data_quality,
        market_time=row.market_time,
        as_of_knowledge=row.as_of_knowledge,
        source_url=source_url,
    )


def _obs_time(row: Observation) -> datetime:
    return row.market_time or row.ingested_at


def _latest(rows: list[Observation], metric: str) -> Observation | None:
    matches = [row for row in rows if row.metric == metric]
    if not matches:
        return None
    matches.sort(key=lambda row: (_obs_time(row), row.ingested_at, row.id))
    return matches[-1]


def _previous(rows: list[Observation], metric: str, *, after: HLMetric | None) -> Observation | None:
    matches = [row for row in rows if row.metric == metric]
    if after is not None and after.observation_id:
        matches = [row for row in matches if row.id != after.observation_id]
    if not matches:
        return None
    matches.sort(key=lambda row: (_obs_time(row), row.ingested_at, row.id))
    return matches[-1]


def _levels_from_obs(obs: list[Observation], metrics: dict[str, HLMetric]) -> tuple[tuple[str, str], ...]:
    highs: list[float] = []
    lows: list[float] = []
    for row in obs:
        if row.metric != "candle_close":
            continue
        raw = (row.payload_json or {}).get("raw") or {}
        high = _float(raw.get("h") or raw.get("high"))
        low = _float(raw.get("l") or raw.get("low"))
        if high is not None:
            highs.append(high)
        if low is not None:
            lows.append(low)
    pairs: list[tuple[str, str]] = []
    if highs:
        pairs.append(("session_high", _fmt_num(max(highs))))
    if lows:
        pairs.append(("session_low", _fmt_num(min(lows))))
    mark = metrics.get("mark_px")
    oracle = metrics.get("oracle_px")
    if mark and oracle and mark.value is not None and oracle.value is not None:
        try:
            pairs.append(("basis_mark_minus_oracle", _fmt_num(float(mark.value) - float(oracle.value))))
        except ValueError:
            pass
    return tuple(sorted(pairs))


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_num(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"
