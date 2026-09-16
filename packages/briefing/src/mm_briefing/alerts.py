"""Threshold-gated intraday alerts. No push without numeric thresholds."""

from __future__ import annotations

from typing import Any, Iterable

from mm_common.hashing import claim_hash
from mm_briefing.config import AlertSettings
from mm_briefing.hl import funding_value, liquidation_size_sum, oi_change_pct
from mm_briefing.models import AlertDecision, AlertEvent, HLInstrumentState


MISSING_THRESHOLD_REASON = "threshold_config_required"


def evaluate_alerts(
    hl: tuple[HLInstrumentState, ...],
    settings: AlertSettings,
    *,
    prior_identity_hashes: Iterable[str] = (),
) -> AlertDecision:
    if not settings.enabled:
        return AlertDecision(pushed=False, reason="alerts_disabled")
    if settings.require_threshold_config and not settings.has_thresholds():
        return AlertDecision(pushed=False, reason=MISSING_THRESHOLD_REASON)

    types = settings.type_map()
    if not any(row.enabled and _has_numeric(row.params) for row in types.values()):
        return AlertDecision(pushed=False, reason=MISSING_THRESHOLD_REASON)

    seen = set(prior_identity_hashes)
    events: list[AlertEvent] = []
    for state in hl:
        liq_spec = types.get("liquidation_spike")
        if liq_spec is not None and liq_spec.enabled:
            event = _liquidation_spike(state, liq_spec.params)
            if event is not None and event.identity_hash not in seen:
                events.append(event)
                seen.add(event.identity_hash)
        fund_spec = types.get("funding_oi_divergence")
        if fund_spec is not None and fund_spec.enabled:
            event = _funding_oi(state, fund_spec.params)
            if event is not None and event.identity_hash not in seen:
                events.append(event)
                seen.add(event.identity_hash)

    if not events:
        return AlertDecision(pushed=False, reason="no_threshold_crossed", events=())
    return AlertDecision(pushed=True, reason="threshold_crossed", events=tuple(events))


def _has_numeric(params: dict[str, Any]) -> bool:
    return any(isinstance(value, (int, float)) and not isinstance(value, bool) for value in params.values())


def _liquidation_spike(state: HLInstrumentState, params: dict[str, Any]) -> AlertEvent | None:
    threshold = _float_param(params, "min_size")
    if threshold is None:
        return None
    total = liquidation_size_sum(state)
    if total < threshold:
        return None
    evidence = tuple(row.observation_id for row in state.liquidations if row.observation_id)
    payload = {
        "alert_type": "liquidation_spike",
        "instrument": state.instrument,
        "min_size": threshold,
        "total": total,
        "observation_ids": list(evidence),
    }
    return AlertEvent(
        alert_type="liquidation_spike",
        instrument=state.instrument,
        detail=f"{state.instrument} liquidation size {total:.4f} >= min_size {threshold}",
        evidence=evidence,
        threshold={"min_size": threshold, "window_minutes": params.get("window_minutes", 60)},
        identity_hash=claim_hash(payload),
    )


def _funding_oi(state: HLInstrumentState, params: dict[str, Any]) -> AlertEvent | None:
    min_funding = _float_param(params, "min_abs_funding")
    min_oi = _float_param(params, "min_oi_change_pct")
    if min_funding is None or min_oi is None:
        return None
    funding = funding_value(state)
    oi = oi_change_pct(state)
    if funding is None or oi is None:
        return None
    if abs(funding) < min_funding or abs(oi) < min_oi:
        return None
    if funding == 0 or oi == 0:
        return None
    if (funding > 0) == (oi > 0):
        return None
    evidence: list[str] = []
    for name in ("funding", "open_interest", "prior_open_interest"):
        metric = state.metric(name)
        if metric and metric.observation_id:
            evidence.append(metric.observation_id)
    payload = {
        "alert_type": "funding_oi_divergence",
        "instrument": state.instrument,
        "funding": funding,
        "oi_change_pct": oi,
        "observation_ids": evidence,
    }
    return AlertEvent(
        alert_type="funding_oi_divergence",
        instrument=state.instrument,
        detail=(
            f"{state.instrument} funding {funding:.6f} vs OI {oi:+.2f}% "
            f"(thresholds abs_funding {min_funding}, abs_oi_pct {min_oi})"
        ),
        evidence=tuple(evidence),
        threshold={"min_abs_funding": min_funding, "min_oi_change_pct": min_oi},
        identity_hash=claim_hash(payload),
    )


def _float_param(params: dict[str, Any], key: str) -> float | None:
    value = params.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)
