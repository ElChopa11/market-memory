"""Observation-age freshness for Market Pulse.

Quality must derive from observation age vs the series' expected cadence,
not from fetch success alone. A number labelled fresh that is days old is
worse than a gap.

Daily FRED (US10Y / DGS10 and any daily series on the FRED default) uses
**business-day** age: Mon–Fri only, half-open ``[obs, ref)``, equivalent to
``numpy.busday_count(obs, ref)`` with the default weekmask and **no** holiday
calendar. Stale when business age **> 1**. Friday's print read on the
following Monday is 1 business day and stays fresh. A calendar-day lag of 1
is not the daily gate (it false-stales every Monday).

Monthly / low-cadence overrides (CPI, NFP) stay on **calendar** age with
their own lag (default 45). Never use ``published_at`` alone as the
knowledge clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Mapping, NamedTuple

from mm_common.time import as_utc
from mm_briefing.models import AssetPrint, MacroSnapshot, pulse_quality, worst_quality

# Daily FRED gate: business days, not calendar days.
# Stale when business age > this value (age 0–1 fresh, age >= 2 stale).
# Friday → Monday = 1 business day = fresh. Do not set this as a calendar lag.
DEFAULT_FRED_DAILY_MAX_BUSINESS_LAG_DAYS = 1
# Historical calendar comparator default. Not the daily FRED gate.
# Calendar-day lag=1 false-stales a Friday print on Monday and is not shipped.
DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS = 2
DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS = 45
AGE_BASIS_BUSINESS = "business"
AGE_BASIS_CALENDAR = "calendar"

# Source keys gated in this PR (Fix 1). Stooq / CoinGecko left unchanged.
_GATED_SOURCES = frozenset({"fred"})


class FreshnessLag(NamedTuple):
    """Resolved lag. ``max_lag_days`` is business days when ``age_basis`` is business."""

    cadence: str
    max_lag_days: int
    age_basis: str


@dataclass(frozen=True)
class SeriesFreshnessOverride:
    """Per-series cadence override (Pulse symbol and/or FRED series id)."""

    symbol: str
    cadence: str
    max_calendar_lag_days: int
    fred_series_id: str | None = None
    age_basis: str = AGE_BASIS_CALENDAR

    def matches(self, *, symbol: str | None = None, series_id: str | None = None) -> bool:
        sym = (symbol or "").strip().upper()
        sid = (series_id or "").strip().upper()
        if sym and sym == self.symbol.strip().upper():
            return True
        if sid and self.fred_series_id and sid == self.fred_series_id.strip().upper():
            return True
        return False


@dataclass(frozen=True)
class SourceFreshnessRule:
    """Per-source default cadence + optional per-series overrides."""

    source: str
    cadence: str
    max_calendar_lag_days: int
    series_overrides: tuple[SeriesFreshnessOverride, ...] = ()
    age_basis: str = AGE_BASIS_BUSINESS

    def applies_to(self, *, source: str) -> bool:
        return source.strip().lower() == self.source.strip().lower()

    def resolve(
        self, *, symbol: str | None = None, series_id: str | None = None
    ) -> FreshnessLag:
        """Return the lag for a series. Per-series override wins.

        Daily default is business-day age. Monthly overrides keep calendar age.
        ``max_lag_days`` uses the basis on the returned lag — it is not always
        a calendar-day count.
        """
        for override in self.series_overrides:
            if override.matches(symbol=symbol, series_id=series_id):
                return FreshnessLag(
                    override.cadence,
                    override.max_calendar_lag_days,
                    override.age_basis,
                )
        return FreshnessLag(self.cadence, self.max_calendar_lag_days, self.age_basis)


@dataclass(frozen=True)
class FreshnessConfig:
    """Loaded from ``config/briefing/macro.yaml`` ``freshness:`` (or defaults)."""

    rules: tuple[SourceFreshnessRule, ...] = ()

    def rule_for(self, *, source: str) -> SourceFreshnessRule | None:
        for rule in self.rules:
            if rule.applies_to(source=source):
                return rule
        return None

    def lag_for(
        self,
        *,
        source: str,
        symbol: str | None = None,
        series_id: str | None = None,
    ) -> FreshnessLag | None:
        """Resolved lag, or None when the source is not gated.

        Tuple shape is ``(cadence, max_lag_days, age_basis)``.
        """
        rule = self.rule_for(source=source)
        if rule is None:
            return None
        return rule.resolve(symbol=symbol, series_id=series_id)


def default_fred_monthly_overrides() -> tuple[SeriesFreshnessOverride, ...]:
    """Standing monthly / low-cadence FRED overrides (Pulse symbol keys)."""
    return (
        SeriesFreshnessOverride(
            symbol="CPI",
            cadence="monthly",
            max_calendar_lag_days=DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS,
            fred_series_id="CPIAUCSL",
            age_basis=AGE_BASIS_CALENDAR,
        ),
        SeriesFreshnessOverride(
            symbol="NFP",
            cadence="monthly",
            max_calendar_lag_days=DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS,
            fred_series_id="PAYEMS",
            age_basis=AGE_BASIS_CALENDAR,
        ),
    )


def default_freshness_config() -> FreshnessConfig:
    return FreshnessConfig(
        rules=(
            SourceFreshnessRule(
                source="fred",
                cadence="daily",
                max_calendar_lag_days=DEFAULT_FRED_DAILY_MAX_BUSINESS_LAG_DAYS,
                series_overrides=default_fred_monthly_overrides(),
                age_basis=AGE_BASIS_BUSINESS,
            ),
        )
    )


def _age_basis_for(spec: Mapping[str, Any], cadence: str, *, default: str) -> str:
    raw = spec.get("age_basis")
    if raw is not None and str(raw).strip():
        basis = str(raw).strip().lower()
        if basis not in {AGE_BASIS_BUSINESS, AGE_BASIS_CALENDAR}:
            raise ValueError(f"age_basis must be business or calendar, got {raw!r}")
        return basis
    if cadence == "monthly":
        return AGE_BASIS_CALENDAR
    return default


def _lag_number(spec: Mapping[str, Any], default: int) -> int:
    """Prefer ``max_lag_days``. ``max_calendar_lag_days`` remains an accepted alias.

    The unit is ``age_basis`` on the same rule, not the key name.
    """
    if spec.get("max_lag_days") is not None:
        return int(spec["max_lag_days"])
    if spec.get("max_calendar_lag_days") is not None:
        return int(spec["max_calendar_lag_days"])
    return default


def _parse_series_overrides(
    raw: Any,
    *,
    default_cadence: str,
    default_lag: int,
    default_age_basis: str = AGE_BASIS_BUSINESS,
) -> tuple[SeriesFreshnessOverride, ...]:
    if not isinstance(raw, dict) or not raw:
        return ()
    out: list[SeriesFreshnessOverride] = []
    for key, spec in raw.items():
        symbol = str(key).strip().upper()
        if not symbol:
            continue
        if spec is None or spec is True:
            out.append(
                SeriesFreshnessOverride(
                    symbol=symbol,
                    cadence=default_cadence,
                    max_calendar_lag_days=default_lag,
                    age_basis=_age_basis_for({}, default_cadence, default=default_age_basis),
                )
            )
            continue
        if not isinstance(spec, dict):
            continue
        cadence = str(spec.get("cadence") or default_cadence)
        lag = _lag_number(spec, default_lag)
        basis = _age_basis_for(spec, cadence, default=default_age_basis)
        fred_id = spec.get("fred_series_id") or spec.get("series_id")
        out.append(
            SeriesFreshnessOverride(
                symbol=symbol,
                cadence=cadence,
                max_calendar_lag_days=lag,
                fred_series_id=str(fred_id).upper() if fred_id else None,
                age_basis=basis,
            )
        )
    return tuple(out)


def load_freshness_config(macro: Mapping[str, Any] | None) -> FreshnessConfig:
    """Parse ``freshness`` from macro.yaml. Missing block → FRED daily default + monthly overrides."""
    if not macro:
        return default_freshness_config()
    raw = macro.get("freshness")
    if not isinstance(raw, dict) or not raw:
        live = macro.get("live") if isinstance(macro.get("live"), dict) else {}
        fred = live.get("fred") if isinstance(live, dict) and isinstance(live.get("fred"), dict) else {}
        if isinstance(fred, dict) and (
            "max_calendar_lag_days" in fred
            or "max_lag_days" in fred
            or isinstance(fred.get("freshness_series"), dict)
        ):
            cadence = str(fred.get("cadence") or "daily")
            basis = _age_basis_for(fred, cadence, default=AGE_BASIS_BUSINESS)
            default_lag = (
                DEFAULT_FRED_DAILY_MAX_BUSINESS_LAG_DAYS
                if basis == AGE_BASIS_BUSINESS
                else DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS
            )
            lag = _lag_number(fred, default_lag)
            overrides = _parse_series_overrides(
                fred.get("freshness_series") or fred.get("series_freshness"),
                default_cadence=cadence,
                default_lag=lag,
                default_age_basis=basis,
            )
            if not overrides:
                overrides = default_fred_monthly_overrides()
            return FreshnessConfig(
                rules=(
                    SourceFreshnessRule(
                        source="fred",
                        cadence=cadence,
                        max_calendar_lag_days=lag,
                        series_overrides=overrides,
                        age_basis=basis,
                    ),
                )
            )
        return default_freshness_config()

    rules: list[SourceFreshnessRule] = []
    for source, spec in raw.items():
        if not isinstance(spec, dict):
            continue
        source_key = str(source).strip().lower()
        if source_key not in _GATED_SOURCES and "max_calendar_lag_days" not in spec and "max_lag_days" not in spec:
            continue
        cadence = str(spec.get("cadence") or "daily")
        basis = _age_basis_for(spec, cadence, default=AGE_BASIS_BUSINESS)
        default_lag = (
            DEFAULT_FRED_DAILY_MAX_BUSINESS_LAG_DAYS
            if basis == AGE_BASIS_BUSINESS
            else DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS
        )
        if spec.get("max_lag_days") is None and spec.get("max_calendar_lag_days") is None:
            if source_key != "fred":
                continue
            lag = default_lag
        else:
            lag = _lag_number(spec, default_lag)
        overrides = _parse_series_overrides(
            spec.get("series"),
            default_cadence=cadence,
            default_lag=int(lag),
            default_age_basis=basis,
        )
        if source_key == "fred" and not overrides:
            overrides = default_fred_monthly_overrides()
        rules.append(
            SourceFreshnessRule(
                source=source_key,
                cadence=cadence,
                max_calendar_lag_days=int(lag),
                series_overrides=overrides,
                age_basis=basis,
            )
        )
    if not rules:
        return default_freshness_config()
    return FreshnessConfig(rules=tuple(rules))


def business_age_days(
    observation_as_of: datetime | date | None,
    reference_as_of: datetime | date | None,
) -> int | None:
    """Weekday count equivalent to ``numpy.busday_count(obs, ref)``.

    Half-open ``[observation date, reference date)``. Monday–Friday only.
    No US holiday calendar. Friday → the following Monday is **1**.
    Same calendar date is **0**. A reference before the observation is negative.
    """
    obs = _as_date(observation_as_of)
    ref = _as_date(reference_as_of)
    if obs is None or ref is None:
        return None
    if obs == ref:
        return 0
    sign = 1
    start, end = obs, ref
    if end < start:
        sign = -1
        start, end = end, start
    days = (end - start).days
    full_weeks, extra = divmod(days, 7)
    count = full_weeks * 5
    # date.weekday(): Monday=0 … Sunday=6. Count weekdays in the partial week.
    for offset in range(extra):
        if (start + timedelta(days=offset)).weekday() < 5:
            count += 1
    return sign * count


def calendar_age_days(
    observation_as_of: datetime | date | None,
    reference_as_of: datetime | date | None,
) -> int | None:
    """Calendar-day age of an observation vs the brief knowledge clock.

    Returns None when either clock is missing. Uses UTC calendar dates for
    datetimes (``as_of_knowledge`` / FRED observation date).
    """
    obs = _as_date(observation_as_of)
    ref = _as_date(reference_as_of)
    if obs is None or ref is None:
        return None
    return (ref - obs).days


def quality_from_observation_age(
    quality: str,
    *,
    observation_as_of: datetime | date | None,
    reference_as_of: datetime | date | None,
    max_calendar_lag_days: int | None = None,
    max_lag_days: int | None = None,
    age_basis: str = AGE_BASIS_CALENDAR,
) -> str:
    """Downgrade to stale when age exceeds the cadence threshold.

    ``age_basis="calendar"`` counts calendar days (monthly CPI/NFP).
    ``age_basis="business"`` counts Mon–Fri half-open days (daily FRED).
    The numeric limit is ``max_lag_days`` when passed, else ``max_calendar_lag_days``
    (alias kept so existing call sites still compile). The unit is ``age_basis``,
    not the parameter name.

    Does not invent values. Does not promote unavailable/partial/rejected up.
    Fetch success (``ok``) alone is not enough for display ``fresh``.
    """
    limit = max_lag_days if max_lag_days is not None else max_calendar_lag_days
    if limit is None:
        raise TypeError("max_lag_days is required")
    if quality in {"unavailable", "rejected", "contradicted"}:
        return quality
    if age_basis == AGE_BASIS_BUSINESS:
        age = business_age_days(observation_as_of, reference_as_of)
    elif age_basis == AGE_BASIS_CALENDAR:
        age = calendar_age_days(observation_as_of, reference_as_of)
    else:
        raise ValueError(f"unknown age_basis {age_basis!r}")
    if age is None:
        return quality
    if age > limit:
        return worst_quality(quality, "stale")
    return quality


def apply_print_freshness(
    row: AssetPrint,
    *,
    reference_as_of: datetime,
    config: FreshnessConfig | None = None,
    series_id: str | None = None,
) -> AssetPrint:
    """Recompute ``data_quality`` from age when a gated source rule applies."""
    cfg = config or default_freshness_config()
    resolved = cfg.lag_for(source=row.source, symbol=row.symbol, series_id=series_id)
    if resolved is None:
        return row
    new_quality = quality_from_observation_age(
        row.data_quality,
        observation_as_of=row.as_of,
        reference_as_of=reference_as_of,
        max_lag_days=resolved.max_lag_days,
        age_basis=resolved.age_basis,
    )
    if new_quality == row.data_quality:
        return row
    return AssetPrint(
        symbol=row.symbol,
        name=row.name,
        last=row.last,
        prior_close=row.prior_close,
        unit=row.unit,
        data_quality=new_quality,
        source=row.source,
        open=row.open,
        as_of=row.as_of,
        observation_id=row.observation_id,
        source_url=row.source_url,
        quoted_symbol=row.quoted_symbol,
        structural_unavailable=row.structural_unavailable,
    )


def gate_snapshot_freshness(
    snapshot: MacroSnapshot,
    *,
    reference_as_of: datetime | None = None,
    config: FreshnessConfig | None = None,
) -> MacroSnapshot:
    """Apply cadence gates to every asset; roll up snapshot ``data_quality``."""
    cfg = config or default_freshness_config()
    ref = as_utc(reference_as_of or snapshot.as_of)
    assets = tuple(apply_print_freshness(row, reference_as_of=ref, config=cfg) for row in snapshot.assets)
    quality = snapshot.data_quality
    for row in assets:
        quality = worst_quality(quality, row.data_quality)
    if assets == snapshot.assets and quality == snapshot.data_quality:
        return snapshot
    return MacroSnapshot(
        as_of=snapshot.as_of,
        prior_us_close=snapshot.prior_us_close,
        assets=assets,
        data_quality=quality,
        source=snapshot.source,
        notes=snapshot.notes,
    )


def format_quality_with_age(
    quality: str,
    *,
    observation_as_of: datetime | date | None,
    reference_as_of: datetime | date | None,
    age_basis: str = AGE_BASIS_CALENDAR,
) -> str:
    """Pulse display label. Stale appends age: ``stale (4d)`` or ``stale (2bd)``.

    ``bd`` is business days (Mon–Fri, no holiday calendar). ``d`` is calendar days.
    """
    label = pulse_quality(quality)
    if label != "stale":
        return label
    if age_basis == AGE_BASIS_BUSINESS:
        age = business_age_days(observation_as_of, reference_as_of)
        unit = "bd"
    elif age_basis == AGE_BASIS_CALENDAR:
        age = calendar_age_days(observation_as_of, reference_as_of)
        unit = "d"
    else:
        raise ValueError(f"unknown age_basis {age_basis!r}")
    if age is None or age < 0:
        return label
    return f"stale ({age}{unit})"


def _as_date(value: datetime | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_utc(value).date()
    return value
