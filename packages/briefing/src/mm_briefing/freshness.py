"""Observation-age freshness for Market Pulse.

Quality must derive from observation age vs the series' expected cadence,
not from fetch success alone. A number labelled fresh that is days old is
worse than a gap.

Age is measured in calendar days between the observation date
(``AssetPrint.as_of`` / FRED observation ``date``) and the brief knowledge
clock (``as_of_knowledge`` / capture ``as_of``). Never use ``published_at``
alone as the knowledge clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from mm_common.time import as_utc
from mm_briefing.models import AssetPrint, MacroSnapshot, pulse_quality, worst_quality

# Principal-reasonable default for FRED daily series (e.g. US10Y / DGS10):
# stale when calendar age exceeds this many days (age > N → stale).
# T+0 / T+1 / T+2 remain eligible for fresh; T+3+ (weekend+Monday lag) and
# the US Close 2026-09-22 / as-of 2026-09-18 incident (4d) cannot be fresh.
DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS = 2

# Source keys gated in this PR (Fix 1). Stooq / CoinGecko left unchanged.
_GATED_SOURCES = frozenset({"fred"})


@dataclass(frozen=True)
class SourceFreshnessRule:
    """Per-source (or per-series) cadence threshold for Pulse quality."""

    source: str
    cadence: str
    max_calendar_lag_days: int
    series: tuple[str, ...] = ()

    def applies_to(self, *, source: str, symbol: str | None = None) -> bool:
        if source.strip().lower() != self.source.strip().lower():
            return False
        if not self.series:
            return True
        if symbol is None:
            return False
        return symbol.strip().upper() in {s.upper() for s in self.series}


@dataclass(frozen=True)
class FreshnessConfig:
    """Loaded from ``config/briefing/macro.yaml`` ``freshness:`` (or defaults)."""

    rules: tuple[SourceFreshnessRule, ...] = ()

    def rule_for(self, *, source: str, symbol: str | None = None) -> SourceFreshnessRule | None:
        for rule in self.rules:
            if rule.applies_to(source=source, symbol=symbol):
                return rule
        return None


def default_freshness_config() -> FreshnessConfig:
    return FreshnessConfig(
        rules=(
            SourceFreshnessRule(
                source="fred",
                cadence="daily",
                max_calendar_lag_days=DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS,
            ),
        )
    )


def load_freshness_config(macro: Mapping[str, Any] | None) -> FreshnessConfig:
    """Parse ``freshness`` from macro.yaml. Missing block → FRED daily default."""
    if not macro:
        return default_freshness_config()
    raw = macro.get("freshness")
    if not isinstance(raw, dict) or not raw:
        # Prefer nested under live.fred when top-level freshness absent.
        live = macro.get("live") if isinstance(macro.get("live"), dict) else {}
        fred = live.get("fred") if isinstance(live, dict) and isinstance(live.get("fred"), dict) else {}
        if isinstance(fred, dict) and "max_calendar_lag_days" in fred:
            lag = int(fred["max_calendar_lag_days"])
            return FreshnessConfig(
                rules=(
                    SourceFreshnessRule(
                        source="fred",
                        cadence=str(fred.get("cadence") or "daily"),
                        max_calendar_lag_days=lag,
                        series=tuple(str(s) for s in (fred.get("series") or {}).keys()),
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
        series_raw = spec.get("series") or ()
        if isinstance(series_raw, dict):
            series = tuple(str(k) for k in series_raw.keys())
        elif isinstance(series_raw, (list, tuple)):
            series = tuple(str(s) for s in series_raw)
        else:
            series = ()
        rules.append(
            SourceFreshnessRule(
                source=source_key,
                cadence=str(spec.get("cadence") or "daily"),
                max_calendar_lag_days=int(lag),
                series=series,
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
) -> AssetPrint:
    """Recompute ``data_quality`` from age when a gated source rule applies."""
    cfg = config or default_freshness_config()
    rule = cfg.rule_for(source=row.source, symbol=row.symbol)
    if rule is None:
        return row
    new_quality = quality_from_observation_age(
        row.data_quality,
        observation_as_of=row.as_of,
        reference_as_of=reference_as_of,
        max_calendar_lag_days=rule.max_calendar_lag_days,
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
