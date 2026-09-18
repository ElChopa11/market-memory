"""Skeptic invalidation quality for the PLAYBOOK (Phase 6c)."""

from __future__ import annotations

import re
from typing import Any

_DAYS_RE = re.compile(r"(\d+)\s*(d|day|days)\b", re.I)


def parse_horizon_days(horizon: str | None) -> float | None:
    if not horizon:
        return None
    match = _DAYS_RE.search(str(horizon))
    if not match:
        return None
    return float(match.group(1))


def invalidation_lookback_ok(*, lookback_days: float | None, horizon_days: float | None) -> bool:
    if lookback_days is None or horizon_days is None:
        return True
    return float(lookback_days) >= float(horizon_days) / 2.0


def daily_print_on_multiday(*, horizon_days: float | None, invalidation_kind: str | None) -> bool:
    """True when the invalidator is illegal (daily print on multi-day thesis)."""
    if horizon_days is None or horizon_days <= 1:
        return False
    kind = (invalidation_kind or "").strip().lower()
    return kind in {"daily_print", "daily-print", "single_daily_print"}


def flow_single_print(invalidation_kind: str | None) -> bool:
    kind = (invalidation_kind or "").strip().lower()
    return kind in {"flow_single_print", "single_print", "single_flow_print"}


def evaluate_invalidation(thesis: Any) -> list[dict[str, Any]]:
    horizon = parse_horizon_days(getattr(thesis, "horizon", None) if thesis is not None else None)
    lookback = getattr(thesis, "invalidation_lookback_days", None) if thesis is not None else None
    kind = getattr(thesis, "invalidation_kind", None) if thesis is not None else None
    items = []
    ok_lookback = invalidation_lookback_ok(lookback_days=lookback, horizon_days=horizon)
    items.append(
        {
            "code": "invalidation_lookback",
            "ok": ok_lookback,
            "detail": "lookback >= thesis_horizon/2" if ok_lookback else "lookback < thesis_horizon/2",
            "fail_mode": "return",
        }
    )
    daily_bad = daily_print_on_multiday(horizon_days=horizon, invalidation_kind=kind)
    items.append(
        {
            "code": "daily_print_multiday",
            "ok": not daily_bad,
            "detail": "daily-print invalidators on multi-day theses rejected at Skeptic",
            "fail_mode": "return",
        }
    )
    flow_bad = flow_single_print(kind)
    items.append(
        {
            "code": "flow_invalidator_rolling",
            "ok": not flow_bad,
            "detail": "flow invalidators use rolling net/z, never single print",
            "fail_mode": "return",
        }
    )
    return items
