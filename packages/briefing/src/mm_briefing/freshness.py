"""Observation-age freshness for Market Pulse.

Quality must derive from observation age vs the series' expected cadence,
not from fetch success alone. A number labelled fresh that is days old is
worse than a gap.

Age is measured in calendar days between the observation date
(``AssetPrint.as_of`` / FRED observation ``date``) and the brief knowledge
clock (``as_of_knowledge`` / capture ``as_of``). Never use ``published_at``
alone as the knowledge clock.

FRED lag is **per-series with a default**: daily series inherit
``max_calendar_lag_days`` (default 2); monthly / low-cadence series set an
override so a legitimate 30–45d CPI/NFP print is not falsely stale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from mm_common.time import as_utc
from mm_briefing.models import AssetPrint, MacroSnapshot, pulse_quality, worst_quality

# Principal-reasonable default for FRED *daily* series (e.g. US10Y / DGS10):
# stale when calendar age exceeds this many days (age > N → stale).
# Monthly series must override — a global daily lag would false-stale CPI/NFP.
DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS = 2
DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS = 45

# Source keys gated in this PR (Fix 1). Stooq / CoinGecko left unchanged.
_GATED_SOURCES = frozenset({"fred"})


@dataclass(frozen=True)
class SeriesFreshnessOverride:
    """Per-series cadence override (Pulse symbol and/or FRED series id)."""

    symbol: str
    cadence: str
    max_calendar_lag_days: int
    fred_series_id: str | None = None

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

    def applies_to(self, *, source: str) -> bool:
        return source.strip().lower() == self.source.strip().lower()

    def resolve(
        self, *, symbol: str | None = None, series_id: str | None = None
    ) -> tuple[str, int]:
        """Return ``(cadence, max_calendar_lag_days)`` for a series.

        Explicit per-series override wins; otherwise the source default
        (daily lag for FRED) applies.
        """
        for override in self.series_overrides:
            if override.matches(symbol=symbol, series_id=series_id):
                return override.cadence, override.max_calendar_lag_days
        return self.cadence, self.max_calendar_lag_days


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
    ) -> tuple[str, int] | None:
        """Resolved ``(cadence, max_lag)`` or None when source is not gated."""
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
        ),
        SeriesFreshnessOverride(
            symbol="NFP",
            cadence="monthly",
            max_calendar_lag_days=DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS,
            fred_series_id="PAYEMS",
        ),
    )


def default_freshness_config() -> FreshnessConfig:
    return FreshnessConfig(
        rules=(
            SourceFreshnessRule(
                source="fred",
                cadence="daily",
                max_calendar_lag_days=DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS,
                series_overrides=default_fred_monthly_overrides(),
            ),
        )
    )


def _parse_series_overrides(
    raw: Any, *, default_cadence: str, default_lag: int
) -> tuple[SeriesFreshnessOverride, ...]:
    if not isinstance(raw, dict) or not raw:
        return ()
    out: list[SeriesFreshnessOverride] = []
    for key, spec in raw.items():
        symbol = str(key).strip().upper()
        if not symbol:
            continue
        if spec is None or spec is True:
            # Explicit listing with no override → inherits source default at resolve time.
            # Still record so operators can see the symbol is acknowledged; lag = default.
            out.append(
                SeriesFreshnessOverride(
                    symbol=symbol,
                    cadence=default_cadence,
                    max_calendar_lag_days=default_lag,
                )
            )
            continue
        if not isinstance(spec, dict):
            continue
        # Empty mapping ``US10Y: {}`` → inherit source default.
        lag_raw = spec.get("max_calendar_lag_days")
        cadence = str(spec.get("cadence") or default_cadence)
        lag = int(lag_raw) if lag_raw is not None else default_lag
        fred_id = spec.get("fred_series_id") or spec.get("series_id")
        out.append(
            SeriesFreshnessOverride(
                symbol=symbol,
                cadence=cadence,
                max_calendar_lag_days=lag,
                fred_series_id=str(fred_id).upper() if fred_id else None,
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
            "max_calendar_lag_days" in fred or isinstance(fred.get("freshness_series"), dict)
        ):
            lag = int(fred.get("max_calendar_lag_days") or DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS)
            cadence = str(fred.get("cadence") or "daily")
            overrides = _parse_series_overrides(
                fred.get("freshness_series") or fred.get("series_freshness"),
                default_cadence=cadence,
                default_lag=lag,
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
                    ),
                )
            )
        return default_freshness_config()

    rules: list[SourceFreshnessRule] = []
    for source, spec in raw.items():
        if not isinstance(spec, dict):
            continue
        source_key = str(source).strip().lower()
        if source_key not in _GATED_SOURCES and "max_calendar_lag_days" not in spec:
            continue
        lag = spec.get("max_calendar_lag_days")
        if lag is None:
            if source_key == "fred":
                lag = DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS
            else:
                continue
        cadence = str(spec.get("cadence") or "daily")
        overrides = _parse_series_overrides(
            spec.get("series"),
            default_cadence=cadence,
            default_lag=int(lag),
        )
        if source_key == "fred" and not overrides:
            overrides = default_fred_monthly_overrides()
        rules.append(
            SourceFreshnessRule(
                source=source_key,
                cadence=cadence,
                max_calendar_lag_days=int(lag),
                series_overrides=overrides,
            )
        )
    if not rules:
        return default_freshness_config()
    return FreshnessConfig(rules=tuple(rules))


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
    max_calendar_lag_days: int,
) -> str:
    """Downgrade to stale when calendar age exceeds the cadence threshold.

    Does not invent values. Does not promote unavailable/partial/rejected up.
    Fetch success (``ok``) alone is not enough for display ``fresh``.
    """
    if quality in {"unavailable", "rejected", "contradicted"}:
        return quality
    age = calendar_age_days(observation_as_of, reference_as_of)
    if age is None:
        return quality
    if age > max_calendar_lag_days:
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
    _cadence, max_lag = resolved
    new_quality = quality_from_observation_age(
        row.data_quality,
        observation_as_of=row.as_of,
        reference_as_of=reference_as_of,
        max_calendar_lag_days=max_lag,
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
) -> str:
    """Pulse display label; when stale, append calendar age (e.g. ``stale (4d)``)."""
    label = pulse_quality(quality)
    if label != "stale":
        return label
    age = calendar_age_days(observation_as_of, reference_as_of)
    if age is None or age < 0:
        return label
    return f"stale ({age}d)"


def _as_date(value: datetime | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_utc(value).date()
    return value
