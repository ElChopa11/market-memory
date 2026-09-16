"""Hyperliquid conditions from Market Memory observations (or a frozen fixture)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from mm_common.hashing import normalize_numeric
from mm_common.time import as_utc, parse_utc
from mm_memory.models import Observation
from mm_memory.queries import what_did_we_know
from mm_briefing.models import HLInstrumentState, HLMetric, worst_quality

SNAPSHOT_METRICS = ("funding", "open_interest", "mid_px", "mark_px", "oracle_px")


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
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics=metrics,
                liquidations=liqs,
                levels=level_pairs,
                data_quality=quality,
            )
        )
    return tuple(sorted(out, key=lambda row: row.instrument))


def hl_from_memory(
    session: Session,
    as_of: datetime,
    *,
    instruments: tuple[str, ...] = ("BTC", "ETH"),
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
        quality = "ok" if obs else "partial"
        for metric in metrics.values():
            quality = worst_quality(quality, metric.data_quality)
        if not obs:
            quality = "partial"
        out.append(
            HLInstrumentState(
                instrument=symbol,
                metrics=metrics,
                liquidations=liqs,
                levels=levels,
                data_quality=quality,
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
    value = spec.get("value")
    return HLMetric(
        instrument=instrument,
        metric=metric,
        value=None if value is None else str(value),
        observation_id=str(spec["observation_id"]) if spec.get("observation_id") else None,
        claim_hash=str(spec["claim_hash"]) if spec.get("claim_hash") else None,
        data_quality=str(spec.get("data_quality") or "ok"),
        market_time=parsed,
    )


def _metric_from_observation(row: Observation) -> HLMetric:
    payload = row.payload_json or {}
    value = payload.get("value")
    if value is None:
        value = normalize_numeric(payload.get("raw")) if isinstance(payload.get("raw"), (int, float, str)) else None
    return HLMetric(
        instrument=row.instrument,
        metric=row.metric,
        value=None if value is None else str(value),
        observation_id=row.id,
        claim_hash=row.claim_hash,
        data_quality=row.data_quality,
        market_time=row.market_time,
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
