"""Observation freshness for Market Pulse.

Quality is not fetch success. The gate is the default: every live source the
brief will turn on must declare a policy when this config loads, or load
fails. There is no allow-list that leaves the other sources forever-fresh.

FRED keeps a per-series **calendar** lag (daily default 2; monthly CPI/NFP
override). That rule is unchanged. Age is calendar days between the
observation date (``AssetPrint.as_of`` / FRED ``date``) and the brief
knowledge clock (``as_of_knowledge`` / capture ``as_of``). Never use
``published_at`` alone as the knowledge clock.

Polygon US RTH ETF proxies use a **session** rule. The product question is
whether a newer session bar has become due that this print does not show.
Calendar-day age is not that rule. Before the cash close, and during the
provisional grace after 16:00 America/New_York, the prior close stays fresh.
The grace window is an explicit pending-session note, not ``stale``. After
the grace, a print from an older session is stale. Half-days and weekday
holidays are not modeled.

CoinGecko and Hyperliquid are capture-stamped **snapshots**. A stamp older
than the declared lag is stale.

A stale print does not yield a change. Callers must not compute a delta from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mm_common.time import as_utc
from mm_briefing.models import AssetPrint, MacroSnapshot, pulse_quality, worst_quality


# Principal-reasonable default for FRED *daily* series (e.g. US10Y / DGS10):
# stale when calendar age exceeds this many days (age > N → stale).
# Monthly series must override — a global daily lag would false-stale CPI/NFP.
DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS = 2
DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS = 45

# Hard-coded regular cash close. Early closes (13:00 ET) are not modeled.
DEFAULT_RTH_CLOSE = time(16, 0)
DEFAULT_SESSION_TZ = "America/New_York"

# Publish lag for the brief's endpoint
# ``GET /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}``.
# Read 2026-09-24 from
# https://massive.com/docs/rest/stocks/aggregates/custom-bars
# (Plan Recency table): Stocks Starter and Stocks Developer are
# "15-minute delayed"; Stocks Advanced / Business are real-time; Stocks Basic
# is "End-of-day" with no minute in that table.
# A live stopwatch was not run: POLYGON_API_KEY was unset, so no request
# was sent to api.polygon.io. This repo does not name which stocks plan the
# key is on. Grace is the documented 15-minute delayed-plan recency plus a
# 5-minute buffer. It does not claim to measure Basic end-of-day.
DOCUMENTED_DELAYED_PLAN_RECENCY_MINUTES = 15
PROVISIONAL_POLYGON_GRACE_MINUTES = DOCUMENTED_DELAYED_PLAN_RECENCY_MINUTES + 5

# 16:00 ET does not describe these sessions. Until that clock, a missing new
# bar stays fresh (false-fresh). They are not in the session calendar.
EARLY_CLOSE_LIMITATIONS = (
    "Friday after Thanksgiving (13:00 ET)",
    "Christmas Eve when it is a weekday (13:00 ET)",
    "July 3 when it is a midweek session (13:00 ET)",
)
# After 16:00 ET plus grace the prior bar is stale even though no session ran.
FULL_CLOSE_FALSE_STALE = (
    "New Year's Day",
    "Martin Luther King Jr. Day",
    "Presidents Day",
    "Good Friday",
    "Memorial Day",
    "Juneteenth",
    "Independence Day",
    "Labor Day",
    "Thanksgiving Day",
    "Christmas Day",
)

PENDING_SESSION_NOTE = "pending session"
STALE_SESSION_NOTE = "newer session bar expected"
MISSING_SESSION_NOTE = "session date missing"
SNAPSHOT_LAG_NOTE = "snapshot lag"
MISSING_SNAPSHOT_CLOCK_NOTE = "snapshot clock missing"
UNDECLARED_POLICY_NOTE = "undeclared freshness policy"

_POLICIES = frozenset({"calendar", "session", "snapshot", "exempt"})
_TERMINAL_QUALITY = frozenset({"unavailable", "rejected", "contradicted"})


class FreshnessConfigError(ValueError):
    """Enabled live source has no usable lag/session policy."""


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
    """Per-source freshness policy + optional per-series calendar overrides."""

    source: str
    cadence: str
    max_calendar_lag_days: int
    series_overrides: tuple[SeriesFreshnessOverride, ...] = ()
    policy: str = "calendar"
    session_timezone: str = DEFAULT_SESSION_TZ
    rth_close: time = DEFAULT_RTH_CLOSE
    grace_minutes: int = 0
    max_snapshot_lag_minutes: int = 0
    exemption: str | None = None

    def applies_to(self, *, source: str) -> bool:
        return source.strip().lower() == self.source.strip().lower()

    def resolve(
        self, *, symbol: str | None = None, series_id: str | None = None
    ) -> tuple[str, int]:
        """Return ``(cadence, max_calendar_lag_days)`` for a calendar-policy series.

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
    required_sources: frozenset[str] = frozenset()

    def rule_for(self, *, source: str) -> SourceFreshnessRule | None:
        key = _policy_source_key(source)
        for rule in self.rules:
            if rule.applies_to(source=key):
                return rule
        return None

    def lag_for(
        self,
        *,
        source: str,
        symbol: str | None = None,
        series_id: str | None = None,
    ) -> tuple[str, int] | None:
        """Resolved calendar ``(cadence, max_lag)``, or None when not a calendar policy."""
        rule = self.rule_for(source=source)
        if rule is None or rule.policy != "calendar":
            return None
        return rule.resolve(symbol=symbol, series_id=series_id)


@dataclass(frozen=True)
class SessionFreshness:
    """Session-rule result for one Polygon daily bar vs the knowledge clock."""

    status: str
    phase: str
    expected_session: date
    shown_session: date | None
    note: str | None


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
    """FRED calendar default used when no macro spec is in hand.

    This is not a live-brief config. A spec that enables live sources must
    declare each policy or ``load_freshness_config`` raises.
    """
    return FreshnessConfig(
        rules=(
            SourceFreshnessRule(
                source="fred",
                cadence="daily",
                max_calendar_lag_days=DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS,
                series_overrides=default_fred_monthly_overrides(),
                policy="calendar",
            ),
        )
    )


def required_live_sources(macro: Mapping[str, Any] | None) -> frozenset[str]:
    """Live sources the brief will turn on.

    Static ``enabled: false`` still counts when the source has a symbol map,
    because ``live_macro_spec`` enables those maps on ``--live``. A mapping
    with no ``live`` block is a partial snippet and is not enforced.
    """
    if not isinstance(macro, Mapping) or "live" not in macro:
        return frozenset()
    live = macro.get("live")
    if not isinstance(live, dict):
        return frozenset()
    found: set[str] = set()
    if _block_active(live.get("stooq"), "symbols"):
        found.add("stooq")
    if _block_active(live.get("polygon"), "symbols", "structural_unavailable"):
        found.add("polygon")
    if _block_active(live.get("fred"), "series"):
        found.add("fred")
    if _block_active(live.get("coingecko"), "ids"):
        found.add("coingecko")
    crypto = macro.get("crypto_pulse")
    if isinstance(crypto, dict):
        sor = str(crypto.get("source_of_record") or "").strip().lower()
        if sor in {"hyperliquid", "hl"}:
            found.add("hyperliquid")
    return frozenset(found)


def load_freshness_config(macro: Mapping[str, Any] | None) -> FreshnessConfig:
    """Parse ``freshness`` from macro.yaml.

    Missing block and no live sources → FRED daily default + monthly overrides.
    Any source ``required_live_sources`` names must have a policy or load raises.
    """
    if not macro:
        return default_freshness_config()
    required = required_live_sources(macro)
    raw = macro.get("freshness")
    if not isinstance(raw, dict) or not raw:
        cfg = _legacy_fred_or_default(macro)
    else:
        rules: list[SourceFreshnessRule] = []
        for source, spec in raw.items():
            if not isinstance(spec, dict):
                raise FreshnessConfigError(
                    f"freshness.{source} must be a mapping with a policy"
                )
            rules.append(_parse_source_rule(str(source), spec))
        cfg = FreshnessConfig(rules=tuple(rules)) if rules else _legacy_fred_or_default(macro)
    return _enforce_required(cfg, required)


def calendar_age_days(
    observation_as_of: datetime | date | None,
    reference_as_of: datetime | date | None,
) -> int | None:
    """Calendar-day age of an observation vs the brief knowledge clock.

    Returns None when either clock is missing. Uses UTC calendar dates for
    datetimes (``as_of_knowledge`` / FRED observation date). FRED only —
    Polygon session freshness does not use this.
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
    if quality in _TERMINAL_QUALITY:
        return quality
    age = calendar_age_days(observation_as_of, reference_as_of)
    if age is None:
        return quality
    if age > max_calendar_lag_days:
        return worst_quality(quality, "stale")
    return quality


def polygon_bar_session_date(bar_as_of: datetime, *, session_tz: str = DEFAULT_SESSION_TZ) -> date:
    """US session date of a Polygon daily bar timestamp.

    Stocks daily aggs are commonly stamped at midnight America/New_York
    (04:00 or 05:00 UTC). This repo's fixtures also use midnight UTC as the
    day bucket. Both map to the session date. Any other stamp uses the
    America/New_York calendar date (a 16:00 ET close belongs to that date).
    """
    utc = as_utc(bar_as_of)
    if utc.timetz().replace(tzinfo=None) == time(0, 0):
        return utc.date()
    et = utc.astimezone(ZoneInfo(session_tz))
    return et.date()


def assess_us_rth_session(
    bar_as_of: datetime | None,
    reference_as_of: datetime,
    *,
    grace_minutes: int,
    rth_close: time = DEFAULT_RTH_CLOSE,
    session_tz: str = DEFAULT_SESSION_TZ,
) -> SessionFreshness:
    """Whether ``bar_as_of`` is the latest US RTH session that should already be published.

    ``grace_minutes`` is the gap after the hard-coded cash close before a
    missing new bar becomes stale. That gap is pending, not stale.
    """
    phase, expected = _expected_published_session(
        reference_as_of,
        grace_minutes=grace_minutes,
        rth_close=rth_close,
        session_tz=session_tz,
    )
    if bar_as_of is None:
        return SessionFreshness(
            status="stale",
            phase=phase,
            expected_session=expected,
            shown_session=None,
            note=MISSING_SESSION_NOTE,
        )
    shown = polygon_bar_session_date(bar_as_of, session_tz=session_tz)
    if shown < expected:
        return SessionFreshness(
            status="stale",
            phase=phase,
            expected_session=expected,
            shown_session=shown,
            note=STALE_SESSION_NOTE,
        )
    if shown == expected and phase == "pending":
        return SessionFreshness(
            status="pending",
            phase=phase,
            expected_session=expected,
            shown_session=shown,
            note=PENDING_SESSION_NOTE,
        )
    return SessionFreshness(
        status="fresh",
        phase=phase,
        expected_session=expected,
        shown_session=shown,
        note=None,
    )


def pending_session_snapshot_note(*, grace_minutes: int, rth_close: time) -> str:
    hhmm = f"{rth_close.hour:02d}:{rth_close.minute:02d}"
    return (
        "polygon pending session: showing the prior US RTH close; "
        f"the newer daily bar is not yet expected "
        f"(provisional grace {grace_minutes}m after {hhmm} America/New_York; "
        "half-days and weekday holidays are not in this calendar)"
    )


def apply_print_freshness(
    row: AssetPrint,
    *,
    reference_as_of: datetime,
    config: FreshnessConfig | None = None,
    series_id: str | None = None,
) -> AssetPrint:
    """Recompute ``data_quality`` when a source policy applies."""
    cfg = config or default_freshness_config()
    rule = cfg.rule_for(source=row.source)
    if rule is None:
        key = _policy_source_key(row.source)
        if key in cfg.required_sources and row.data_quality not in _TERMINAL_QUALITY:
            return _restamp(row, data_quality=worst_quality(row.data_quality, "stale"), note=UNDECLARED_POLICY_NOTE)
        return row
    if row.data_quality in _TERMINAL_QUALITY:
        return row
    if rule.policy == "exempt":
        return row
    if rule.policy == "calendar":
        _cadence, max_lag = rule.resolve(symbol=row.symbol, series_id=series_id)
        new_quality = quality_from_observation_age(
            row.data_quality,
            observation_as_of=row.as_of,
            reference_as_of=reference_as_of,
            max_calendar_lag_days=max_lag,
        )
        note = row.freshness_note
        if new_quality == row.data_quality and note == row.freshness_note:
            return row
        return _restamp(row, data_quality=new_quality, note=note)
    if rule.policy == "session":
        assessed = assess_us_rth_session(
            row.as_of,
            reference_as_of,
            grace_minutes=rule.grace_minutes,
            rth_close=rule.rth_close,
            session_tz=rule.session_timezone,
        )
        if assessed.status == "stale":
            new_quality = worst_quality(row.data_quality, "stale")
            note = assessed.note
        elif assessed.status == "pending":
            new_quality = row.data_quality
            note = PENDING_SESSION_NOTE
        else:
            new_quality = row.data_quality
            note = None
        if new_quality == row.data_quality and note == row.freshness_note:
            return row
        return _restamp(row, data_quality=new_quality, note=note)
    if rule.policy == "snapshot":
        return _apply_snapshot(row, reference_as_of=reference_as_of, max_minutes=rule.max_snapshot_lag_minutes)
    raise FreshnessConfigError(f"unknown freshness policy {rule.policy!r} for {rule.source}")


def gate_snapshot_freshness(
    snapshot: MacroSnapshot,
    *,
    reference_as_of: datetime | None = None,
    config: FreshnessConfig | None = None,
) -> MacroSnapshot:
    """Apply source policies to every asset; roll up snapshot ``data_quality``."""
    cfg = config or default_freshness_config()
    ref = as_utc(reference_as_of or snapshot.as_of)
    assets = tuple(apply_print_freshness(row, reference_as_of=ref, config=cfg) for row in snapshot.assets)
    quality = snapshot.data_quality
    for row in assets:
        quality = worst_quality(quality, row.data_quality)
    notes = list(snapshot.notes)
    for row in assets:
        if row.freshness_note != PENDING_SESSION_NOTE:
            continue
        rule = cfg.rule_for(source=row.source)
        if rule is None or rule.policy != "session":
            continue
        note = pending_session_snapshot_note(grace_minutes=rule.grace_minutes, rth_close=rule.rth_close)
        if note not in notes:
            notes.append(note)
        break
    note_tuple = tuple(notes)
    if assets == snapshot.assets and quality == snapshot.data_quality and note_tuple == snapshot.notes:
        return snapshot
    return MacroSnapshot(
        as_of=snapshot.as_of,
        prior_us_close=snapshot.prior_us_close,
        assets=assets,
        data_quality=quality,
        source=snapshot.source,
        notes=note_tuple,
    )


def format_quality_with_age(
    quality: str,
    *,
    observation_as_of: datetime | date | None,
    reference_as_of: datetime | date | None,
) -> str:
    """Pulse display label; when stale, append calendar age (e.g. ``stale (4d)``).

    Calendar age is the FRED display. Session-policy rows carry ``freshness_note``
    and use :func:`format_print_quality` so the label is not a day count.
    """
    label = pulse_quality(quality)
    if label != "stale":
        return label
    age = calendar_age_days(observation_as_of, reference_as_of)
    if age is None or age < 0:
        return label
    return f"stale ({age}d)"


def format_print_quality(
    row: AssetPrint,
    *,
    reference_as_of: datetime | date | None,
) -> str:
    """Pulse cell for one print. Session/snapshot notes replace the calendar-day suffix."""
    label = pulse_quality(row.data_quality)
    if row.freshness_note:
        return f"{label} ({row.freshness_note})"
    if reference_as_of is not None:
        return format_quality_with_age(
            row.data_quality,
            observation_as_of=row.as_of,
            reference_as_of=reference_as_of,
        )
    return label


def _apply_snapshot(row: AssetPrint, *, reference_as_of: datetime, max_minutes: int) -> AssetPrint:
    if row.as_of is None:
        return _restamp(
            row,
            data_quality=worst_quality(row.data_quality, "stale"),
            note=MISSING_SNAPSHOT_CLOCK_NOTE,
        )
    age_minutes = (as_utc(reference_as_of) - as_utc(row.as_of)).total_seconds() / 60.0
    if age_minutes > max_minutes:
        return _restamp(row, data_quality=worst_quality(row.data_quality, "stale"), note=SNAPSHOT_LAG_NOTE)
    if row.freshness_note is None:
        return row
    return _restamp(row, data_quality=row.data_quality, note=None)


def _restamp(row: AssetPrint, *, data_quality: str, note: str | None) -> AssetPrint:
    return AssetPrint(
        symbol=row.symbol,
        name=row.name,
        last=row.last,
        prior_close=row.prior_close,
        unit=row.unit,
        data_quality=data_quality,
        source=row.source,
        open=row.open,
        as_of=row.as_of,
        observation_id=row.observation_id,
        source_url=row.source_url,
        freshness_note=note,
    )


def _expected_published_session(
    reference_as_of: datetime,
    *,
    grace_minutes: int,
    rth_close: time,
    session_tz: str,
) -> tuple[str, date]:
    tz = ZoneInfo(session_tz)
    local = as_utc(reference_as_of).astimezone(tz)
    day = local.date()
    if day.weekday() >= 5:
        return "weekend", _previous_weekday(day)
    close_local = datetime(
        day.year,
        day.month,
        day.day,
        rth_close.hour,
        rth_close.minute,
        rth_close.second,
        tzinfo=tz,
    )
    publish_local = close_local + timedelta(minutes=grace_minutes)
    if local < close_local:
        return "before_close", _previous_weekday(day)
    if local < publish_local:
        return "pending", _previous_weekday(day)
    return "due", day


def _previous_weekday(day: date) -> date:
    cursor = day - timedelta(days=1)
    while cursor.weekday() >= 5:
        cursor -= timedelta(days=1)
    return cursor


def _policy_source_key(source: str) -> str:
    key = source.strip().lower()
    if key.startswith("hyperliquid"):
        return "hyperliquid"
    return key


def _block_active(block: Any, *content_keys: str) -> bool:
    if not isinstance(block, dict):
        return False
    if block.get("enabled") is True:
        return True
    for key in content_keys:
        value = block.get(key)
        if isinstance(value, dict) and len(value) > 0:
            return True
    return False


def _enforce_required(cfg: FreshnessConfig, required: frozenset[str]) -> FreshnessConfig:
    if not required:
        return cfg
    missing = sorted(source for source in required if cfg.rule_for(source=source) is None)
    if missing:
        joined = ", ".join(missing)
        raise FreshnessConfigError(
            "enabled live source(s) lack a freshness policy: "
            f"{joined}. Declare freshness.<source>.policy "
            "(calendar, session, or snapshot) or policy: exempt with a non-empty exemption. "
            "Ungated sources must not render as fresh."
        )
    return FreshnessConfig(rules=cfg.rules, required_sources=required)


def _legacy_fred_or_default(macro: Mapping[str, Any]) -> FreshnessConfig:
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
                    policy="calendar",
                ),
            )
        )
    return default_freshness_config()


def _parse_source_rule(source: str, spec: Mapping[str, Any]) -> SourceFreshnessRule:
    source_key = source.strip().lower()
    if not source_key:
        raise FreshnessConfigError("freshness source name is empty")
    policy = str(spec.get("policy") or "").strip().lower()
    if not policy:
        if source_key == "fred":
            policy = "calendar"
        else:
            raise FreshnessConfigError(
                f"freshness.{source_key}.policy is required "
                "(calendar, session, snapshot, or exempt)"
            )
    if policy not in _POLICIES:
        raise FreshnessConfigError(f"freshness.{source_key}.policy {policy!r} is not a known policy")
    if source_key == "polygon" and policy != "session":
        raise FreshnessConfigError(
            "polygon freshness policy must be session "
            "(calendar-day lag is not the US RTH product rule)"
        )
    cadence = str(spec.get("cadence") or ("daily" if policy == "calendar" else policy))
    if policy == "exempt":
        reason = str(spec.get("exemption") or spec.get("reason") or "").strip()
        if not reason:
            raise FreshnessConfigError(
                f"freshness.{source_key} exemption requires a non-empty exemption reason"
            )
        return SourceFreshnessRule(
            source=source_key,
            cadence="exempt",
            max_calendar_lag_days=0,
            policy="exempt",
            exemption=reason,
        )
    if policy == "calendar":
        lag_raw = spec.get("max_calendar_lag_days")
        if lag_raw is None:
            if source_key == "fred":
                lag_raw = DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS
            else:
                raise FreshnessConfigError(
                    f"freshness.{source_key} calendar policy requires max_calendar_lag_days"
                )
        lag = int(lag_raw)
        overrides = _parse_series_overrides(
            spec.get("series"),
            default_cadence=cadence,
            default_lag=lag,
        )
        if source_key == "fred" and not overrides:
            overrides = default_fred_monthly_overrides()
        return SourceFreshnessRule(
            source=source_key,
            cadence=cadence,
            max_calendar_lag_days=lag,
            series_overrides=overrides,
            policy="calendar",
        )
    if policy == "session":
        if "grace_minutes" not in spec:
            raise FreshnessConfigError(
                f"freshness.{source_key} session policy requires grace_minutes "
                "(provisional; do not omit and hope for a hidden default)"
            )
        grace = int(spec["grace_minutes"])
        if grace < 0:
            raise FreshnessConfigError(f"freshness.{source_key}.grace_minutes must be >= 0")
        if "rth_close" not in spec:
            raise FreshnessConfigError(
                f"freshness.{source_key} session policy requires rth_close "
                "(this pass hard-codes 16:00 America/New_York; half-days are not modeled)"
            )
        rth_close = _parse_hhmm(spec.get("rth_close"), source_key=source_key)
        session_tz = str(spec.get("session_timezone") or "").strip()
        if not session_tz:
            raise FreshnessConfigError(f"freshness.{source_key} session policy requires session_timezone")
        try:
            ZoneInfo(session_tz)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise FreshnessConfigError(
                f"freshness.{source_key}.session_timezone {session_tz!r} is not a zone"
            ) from exc
        return SourceFreshnessRule(
            source=source_key,
            cadence=cadence,
            max_calendar_lag_days=0,
            policy="session",
            session_timezone=session_tz,
            rth_close=rth_close,
            grace_minutes=grace,
        )
    if "max_snapshot_lag_minutes" not in spec:
        raise FreshnessConfigError(
            f"freshness.{source_key} snapshot policy requires max_snapshot_lag_minutes"
        )
    lag_minutes = int(spec["max_snapshot_lag_minutes"])
    if lag_minutes < 0:
        raise FreshnessConfigError(f"freshness.{source_key}.max_snapshot_lag_minutes must be >= 0")
    return SourceFreshnessRule(
        source=source_key,
        cadence=cadence,
        max_calendar_lag_days=0,
        policy="snapshot",
        max_snapshot_lag_minutes=lag_minutes,
    )


def _parse_hhmm(value: Any, *, source_key: str) -> time:
    parts = str(value).strip().split(":")
    if len(parts) < 2:
        raise FreshnessConfigError(f"freshness.{source_key}.rth_close {value!r} is not HH:MM")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
    except ValueError as exc:
        raise FreshnessConfigError(f"freshness.{source_key}.rth_close {value!r} is not HH:MM") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise FreshnessConfigError(f"freshness.{source_key}.rth_close {value!r} is out of range")
    return time(hour, minute, second)


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


def _as_date(value: datetime | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_utc(value).date()
    return value
