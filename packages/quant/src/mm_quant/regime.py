"""Regime classifier. Thresholds come from config/quant/regime.yaml — not model weights."""

from __future__ import annotations

from datetime import datetime

from mm_quant.config import QuantConfig, RegimeThresholds
from mm_quant.models import FactorValue, OK, RegimeResult, UNAVAILABLE


def _value(factors: dict[str, FactorValue], name: str) -> float | None:
    row = factors.get(name)
    if row is None or row.status == UNAVAILABLE or row.value is None:
        return None
    return row.value


def _bucket_vol(vol: float, th: RegimeThresholds) -> str:
    if vol < th.vol_low:
        return "low_vol"
    if vol > th.vol_high:
        return "high_vol"
    return "mid_vol"


def _bucket_adx(adx: float, th: RegimeThresholds) -> str:
    if adx >= th.adx_trending:
        return "trending"
    return "chop"


def classify_regime(
    factors: tuple[FactorValue, ...] | dict[str, FactorValue],
    *,
    watermark: datetime,
    config: QuantConfig,
) -> RegimeResult:
    th = config.regime
    by_name = {row.name: row for row in factors} if not isinstance(factors, dict) else factors
    vol = _value(by_name, "realised_vol_short")
    adx = _value(by_name, "adx")
    z = _value(by_name, "zscore")
    funding = _value(by_name, "funding_carry")

    driving: dict[str, object] = {
        "realised_vol_short": vol,
        "adx": adx,
        "zscore": z,
        "funding_carry": funding,
        "thresholds": {
            "version": th.version,
            "vol_low": th.vol_low,
            "vol_high": th.vol_high,
            "adx_trending": th.adx_trending,
            "zscore_stretched": th.zscore_stretched,
            "funding_crowded": th.funding_crowded,
            "min_inputs_for_tag": th.min_inputs_for_tag,
        },
    }

    present = [name for name, val in (("vol", vol), ("adx", adx), ("zscore", z), ("funding", funding)) if val is not None]
    # Tag requires vol + ADX (the two explicit regime axes). Suffixes are optional.
    core_present = sum(x is not None for x in (vol, adx))
    if core_present < min(2, th.min_inputs_for_tag) or vol is None or adx is None:
        return RegimeResult(
            tag=UNAVAILABLE,
            confidence=0.0,
            as_of_knowledge=watermark,
            status=UNAVAILABLE,
            driving_inputs=driving,
            thresholds_version=th.version,
            reason=f"need vol+ADX; present={present}",
        )

    parts = [_bucket_vol(vol, th), _bucket_adx(adx, th)]
    if z is not None and abs(z) >= th.zscore_stretched:
        parts.append("stretched")
    if funding is not None and abs(funding) >= th.funding_crowded:
        parts.append("crowded_funding")
    tag = "_".join(parts)

    considered = 4
    available = sum(x is not None for x in (vol, adx, z, funding))
    # Distance-from-threshold sharpness in [0, 1], then scaled by coverage.
    vol_span = max(th.vol_high - th.vol_low, 1e-12)
    vol_sharp = min(1.0, abs(vol - (th.vol_low + th.vol_high) / 2.0) / vol_span)
    adx_sharp = min(1.0, abs(adx - th.adx_trending) / max(th.adx_trending, 1e-12))
    coverage = available / considered
    confidence = max(0.0, min(1.0, 0.5 * coverage + 0.25 * vol_sharp + 0.25 * adx_sharp))

    return RegimeResult(
        tag=tag,
        confidence=confidence,
        as_of_knowledge=watermark,
        status=OK,
        driving_inputs=driving,
        thresholds_version=th.version,
        reason="explicit YAML thresholds",
    )
