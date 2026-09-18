"""Intent-level budget-fraction helpers. Return % of research budget only. No orders."""

from __future__ import annotations

from datetime import datetime

from mm_quant.models import SizingHint, UNAVAILABLE, OK


def _clip(value: float, cap_pct: float) -> float:
    if cap_pct < 0:
        cap_pct = 0.0
    if value < 0:
        value = 0.0
    if value > cap_pct:
        return cap_pct
    return value


def vol_targeted_budget_pct(
    realised_vol: float | None,
    *,
    target_vol: float,
    base_fraction: float = 1.0,
    cap_pct: float = 5.0,
    as_of_knowledge: datetime,
    provenance=(),
) -> SizingHint:
    """budget_fraction_pct = clip((target_vol / realised_vol) * base_fraction * 100, cap).

    Missing or non-positive realised vol → unavailable (never invent 0).
    """
    inputs = {
        "realised_vol": realised_vol,
        "target_vol": target_vol,
        "base_fraction": base_fraction,
        "cap_pct": cap_pct,
    }
    if realised_vol is None or realised_vol <= 0 or target_vol <= 0:
        return SizingHint(
            method="vol_targeted",
            budget_fraction_pct=None,
            status=UNAVAILABLE,
            as_of_knowledge=as_of_knowledge,
            inputs=inputs,
            provenance=tuple(provenance),
            reason="realised vol or target vol missing/non-positive",
        )
    raw = (target_vol / realised_vol) * base_fraction * 100.0
    return SizingHint(
        method="vol_targeted",
        budget_fraction_pct=_clip(raw, cap_pct),
        status=OK,
        as_of_knowledge=as_of_knowledge,
        inputs=inputs | {"uncapped_pct": raw},
        provenance=tuple(provenance),
        reason="intent-level vol-targeted budget fraction",
    )


def fixed_fractional_budget_pct(
    fraction: float,
    *,
    cap_pct: float = 5.0,
    as_of_knowledge: datetime,
    provenance=(),
) -> SizingHint:
    """budget_fraction_pct = clip(fraction * 100, cap). Missing/invalid fraction → unavailable."""
    inputs = {"fraction": fraction, "cap_pct": cap_pct}
    if fraction is None or fraction < 0:
        return SizingHint(
            method="fixed_fractional",
            budget_fraction_pct=None,
            status=UNAVAILABLE,
            as_of_knowledge=as_of_knowledge,
            inputs=inputs,
            provenance=tuple(provenance),
            reason="fraction missing/negative",
        )
    raw = fraction * 100.0
    return SizingHint(
        method="fixed_fractional",
        budget_fraction_pct=_clip(raw, cap_pct),
        status=OK,
        as_of_knowledge=as_of_knowledge,
        inputs=inputs | {"uncapped_pct": raw},
        provenance=tuple(provenance),
        reason="intent-level fixed-fractional budget fraction",
    )
