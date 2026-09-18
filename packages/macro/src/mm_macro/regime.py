"""Cross-asset regime classifier. Two driving inputs from YAML. Never invent."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from mm_macro.config import MacroConfig
from mm_macro.models import OK, UNAVAILABLE, RegimeResult


def _bucket_vix(vix: float, cfg: MacroConfig) -> str:
    if vix < cfg.vix.risk_on_below:
        return "risk_on"
    if vix > cfg.vix.risk_off_above:
        return "risk_off"
    return "risk_neutral"


def _bucket_dxy(dxy: float, cfg: MacroConfig) -> str:
    if dxy < cfg.dxy.weak_below:
        return "usd_weak"
    if dxy > cfg.dxy.strong_above:
        return "usd_strong"
    return "usd_mid"


def classify_macro_regime(
    values: Mapping[str, float | None],
    *,
    watermark: datetime,
    config: MacroConfig,
) -> RegimeResult:
    vix = values.get("VIX")
    dxy = values.get("DXY")
    driving = {
        "VIX": vix,
        "DXY": dxy,
        "thresholds": {
            "version": config.version,
            "vix_risk_on_below": config.vix.risk_on_below,
            "vix_risk_off_above": config.vix.risk_off_above,
            "dxy_weak_below": config.dxy.weak_below,
            "dxy_strong_above": config.dxy.strong_above,
            "min_inputs_for_tag": config.min_inputs_for_tag,
        },
        "optional": {
            "T10Y2Y": values.get("T10Y2Y"),
            "HY_OAS": values.get("HY_OAS"),
            "WTI": values.get("WTI"),
            "US10Y": values.get("US10Y"),
            "US2Y": values.get("US2Y"),
        },
    }
    present = [name for name in ("VIX", "DXY") if values.get(name) is not None]
    if vix is None or dxy is None or len(present) < config.min_inputs_for_tag:
        return RegimeResult(
            tag=UNAVAILABLE,
            confidence=0.0,
            as_of_knowledge=watermark,
            status=UNAVAILABLE,
            driving_inputs=driving,
            thresholds_version=config.version,
            reason=f"need VIX+DXY; present={present}",
        )

    tag = f"{_bucket_vix(vix, config)}_{_bucket_dxy(dxy, config)}"
    vix_span = max(config.vix.risk_off_above - config.vix.risk_on_below, 1e-12)
    dxy_span = max(config.dxy.strong_above - config.dxy.weak_below, 1e-12)
    vix_mid = (config.vix.risk_on_below + config.vix.risk_off_above) / 2.0
    dxy_mid = (config.dxy.weak_below + config.dxy.strong_above) / 2.0
    vix_sharp = min(1.0, abs(vix - vix_mid) / vix_span)
    dxy_sharp = min(1.0, abs(dxy - dxy_mid) / dxy_span)
    optional_n = sum(values.get(name) is not None for name in ("T10Y2Y", "HY_OAS", "WTI", "US10Y", "US2Y"))
    coverage = (2 + optional_n) / 7
    confidence = max(0.0, min(1.0, 0.5 * coverage + 0.25 * vix_sharp + 0.25 * dxy_sharp))
    return RegimeResult(
        tag=tag,
        confidence=confidence,
        as_of_knowledge=watermark,
        status=OK,
        driving_inputs=driving,
        thresholds_version=config.version,
        reason="explicit YAML thresholds; driving inputs VIX + DXY",
    )
