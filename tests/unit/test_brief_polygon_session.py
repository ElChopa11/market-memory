"""Polygon session freshness and gate-by-default policy load.

Product rule: has a newer US RTH session bar become due that we are not showing?
Calendar-day age is not that rule. Grace after 16:00 ET is pending, not stale.
"""

from __future__ import annotations

import inspect
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
import yaml

from mm_briefing.config import load_briefing_settings
from mm_briefing.fetchers import LiveMacroFetcher, _parse_polygon_aggs
from mm_briefing.freshness import (
    DOCUMENTED_DELAYED_PLAN_RECENCY_MINUTES,
    EARLY_CLOSE_LIMITATIONS,
    FULL_CLOSE_FALSE_STALE,
    PENDING_SESSION_NOTE,
    PROVISIONAL_POLYGON_GRACE_MINUTES,
    STALE_SESSION_NOTE,
    FreshnessConfigError,
    apply_print_freshness,
    assess_us_rth_session,
    format_print_quality,
    gate_snapshot_freshness,
    load_freshness_config,
    polygon_bar_session_date,
    required_live_sources,
)
from mm_briefing.models import AssetPrint, MacroSnapshot
from mm_briefing.render import _since_close_bullets


ROOT = Path(__file__).resolve().parents[2]
NY = ZoneInfo("America/New_York")
UTC = timezone.utc


def _et(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=NY)


def _utc_midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _session_macro(*, grace_minutes: int = PROVISIONAL_POLYGON_GRACE_MINUTES) -> dict:
    return {
        "freshness": {
            "polygon": {
                "policy": "session",
                "cadence": "us_rth_daily",
                "session_timezone": "America/New_York",
                "rth_close": "16:00",
                "grace_minutes": grace_minutes,
            }
        },
        "live": {
            "polygon": {
                "enabled": True,
                "symbols": {"ES": {"ticker": "SPY"}},
            }
        },
    }


def _print(session: date, *, last: float = 510.0, prior: float = 500.0) -> AssetPrint:
    return AssetPrint(
        symbol="ES",
        name="SPY ETF (proxy for S&P 500; not ES futures)",
        last=last,
        prior_close=prior,
        unit="usd",
        data_quality="ok",
        source="polygon",
        as_of=_utc_midnight(session),
    )


def _gate(shown: date, clock: datetime, *, grace_minutes: int = PROVISIONAL_POLYGON_GRACE_MINUTES) -> MacroSnapshot:
    cfg = load_freshness_config(_session_macro(grace_minutes=grace_minutes))
    snap = MacroSnapshot(
        as_of=clock,
        prior_us_close=clock,
        assets=(_print(shown),),
        data_quality="ok",
        source="live",
    )
    return gate_snapshot_freshness(snap, reference_as_of=clock, config=cfg)


def test_bar_session_date_accepts_utc_midnight_and_midnight_et() -> None:
    tuesday = date(2026, 3, 10)
    assert polygon_bar_session_date(_utc_midnight(tuesday)) == tuesday
    assert polygon_bar_session_date(datetime(2026, 3, 10, 0, 0, tzinfo=NY)) == tuesday
    assert polygon_bar_session_date(_et(tuesday, 16, 0)) == tuesday
    # Midnight ET in January is 05:00 UTC, not the previous UTC date.
    assert polygon_bar_session_date(datetime(2026, 1, 5, 0, 0, tzinfo=NY)) == date(2026, 1, 5)


def test_before_rth_close_prior_session_is_fresh() -> None:
    tuesday = date(2026, 3, 10)
    monday = date(2026, 3, 9)
    gated = _gate(monday, _et(tuesday, 8, 0))
    row = gated.assets[0]
    assert row.data_quality == "ok"
    assert row.freshness_note is None
    assert row.change_pct == pytest.approx(2.0)
    assert "pending session" not in " ".join(gated.notes)


def test_grace_window_keeps_prior_close_fresh_with_pending_note() -> None:
    tuesday = date(2026, 3, 10)
    monday = date(2026, 3, 9)
    clock = _et(tuesday, 16, 10)  # 10m after 16:00, inside 20m grace
    gated = _gate(monday, clock)
    row = gated.assets[0]
    assert row.data_quality == "ok"
    assert row.freshness_note == PENDING_SESSION_NOTE
    assert row.change is not None
    assert format_print_quality(row, reference_as_of=clock) == "fresh (pending session)"
    assert any("pending session" in note for note in gated.notes)
    assert any("half-days" in note for note in gated.notes)
    bullets = "\n".join(_since_close_bullets((row,), knowledge_as_of=clock))
    assert "fresh (pending session)" in bullets
    assert "+2.00%" in bullets


def test_after_grace_prior_bar_is_stale_and_has_no_delta() -> None:
    """One calendar day is enough once the new session bar is due. The old >3 hack stayed fresh."""
    tuesday = date(2026, 3, 10)
    monday = date(2026, 3, 9)
    clock = _et(tuesday, 16, 30)
    gated = _gate(monday, clock)
    row = gated.assets[0]
    assert row.data_quality == "stale"
    assert row.last == 510.0
    assert row.prior_close == 500.0
    assert row.change is None
    assert row.change_pct is None
    assert row.freshness_note == STALE_SESSION_NOTE
    label = format_print_quality(row, reference_as_of=clock)
    assert label == "stale (newer session bar expected)"
    assert "1d" not in label
    bullets = "\n".join(_since_close_bullets((row,), knowledge_as_of=clock))
    assert "n/a" in bullets
    assert "stale (newer session bar expected)" in bullets


def test_showing_the_due_session_bar_is_fresh_after_grace() -> None:
    tuesday = date(2026, 3, 10)
    clock = _et(tuesday, 16, 30)
    row = _gate(tuesday, clock).assets[0]
    assert row.data_quality == "ok"
    assert row.freshness_note is None
    assert row.change_pct == pytest.approx(2.0)


def test_monday_morning_friday_bar_is_fresh() -> None:
    """No Monday bar is due yet. A 3-calendar-day Friday print is still the right close."""
    monday = date(2026, 3, 9)
    friday = date(2026, 3, 6)
    row = _gate(friday, _et(monday, 10, 0)).assets[0]
    assert row.data_quality == "ok"
    assert row.freshness_note is None


def test_monday_evening_friday_bar_is_stale_even_though_calendar_age_is_3() -> None:
    """Forever-fresh hole: age 3 is not > 3, but Monday's bar is already due."""
    monday = date(2026, 3, 9)
    friday = date(2026, 3, 6)
    clock = _et(monday, 16, 30)
    row = _gate(friday, clock).assets[0]
    assert (clock.date() - friday).days == 3
    assert row.data_quality == "stale"
    assert row.change is None


def test_weekend_friday_bar_stays_fresh() -> None:
    friday = date(2026, 3, 13)
    saturday = _et(date(2026, 3, 14), 11, 0)
    row = _gate(friday, saturday).assets[0]
    assert row.data_quality == "ok"
    assert row.freshness_note is None


def test_est_close_is_16_00_local_not_utc() -> None:
    """Sydney-morning 20:30 UTC is 15:30 EST (before the close) and 16:30 EDT (after grace)."""
    monday = date(2026, 1, 5)
    tuesday = date(2026, 1, 6)
    winter_cron = datetime(2026, 1, 6, 20, 30, tzinfo=UTC)
    assert winter_cron.astimezone(NY).hour == 15
    winter = _gate(monday, winter_cron).assets[0]
    assert winter.data_quality == "ok"
    assert winter.freshness_note is None

    pending = _gate(monday, _et(tuesday, 16, 10)).assets[0]
    assert pending.freshness_note == PENDING_SESSION_NOTE
    assert pending.data_quality == "ok"

    due = _gate(monday, _et(tuesday, 16, 30)).assets[0]
    assert due.data_quality == "stale"

    summer_cron = datetime(2026, 3, 10, 20, 30, tzinfo=UTC)
    assert summer_cron.astimezone(NY).strftime("%H:%M") == "16:30"
    summer = _gate(date(2026, 3, 9), summer_cron).assets[0]
    assert summer.data_quality == "stale"
    assert summer.change is None


def test_hardcoded_1600_does_not_treat_14_00_as_past_close() -> None:
    """Early-close false-fresh window: 14:00 ET is still before the hard-coded 16:00 close."""
    wednesday = date(2026, 3, 11)
    tuesday = date(2026, 3, 10)
    clock = _et(wednesday, 14, 0)
    assessed = assess_us_rth_session(
        _utc_midnight(tuesday),
        clock,
        grace_minutes=20,
        rth_close=time(16, 0),
    )
    assert assessed.phase == "before_close"
    assert assessed.status == "fresh"
    row = _gate(tuesday, clock).assets[0]
    assert row.data_quality == "ok"
    assert row.freshness_note is None


def test_weekday_with_no_session_calendar_marks_prior_bar_stale_after_grace() -> None:
    """MLK Monday 2026-01-19 has no holiday exception. Prior Friday is stale after grace.

    That is a known false-stale when the NYSE is closed. Half-days are the other gap.
    """
    mlk = date(2026, 1, 19)
    assert mlk.weekday() == 0
    friday = date(2026, 1, 16)
    row = _gate(friday, _et(mlk, 16, 30)).assets[0]
    assert row.data_quality == "stale"


def test_polygon_parser_does_not_use_a_calendar_day_hack() -> None:
    source = inspect.getsource(_parse_polygon_aggs)
    assert "> 3" not in source
    assert "days >" not in source


def test_live_polygon_fetch_after_grace_is_stale_without_delta() -> None:
    monday = date(2026, 3, 9)
    friday = date(2026, 3, 6)
    clock = _et(date(2026, 3, 10), 16, 30)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"o": 490.0, "c": 500.0, "t": int(_utc_midnight(friday).timestamp() * 1000)},
                    {"o": 500.0, "c": 510.0, "t": int(_utc_midnight(monday).timestamp() * 1000)},
                ]
            },
        )

    spec = _session_macro()
    spec["live"]["polygon"]["api_key_env"] = "POLYGON_API_KEY"
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, env={"POLYGON_API_KEY": "test-key"}, sleep=lambda _: None).fetch(
        clock, prior_us_close=clock
    )
    row = snap.by_symbol()["ES"]
    assert row.as_of == _utc_midnight(monday)
    assert row.last == 510.0
    assert row.prior_close == 500.0
    assert row.data_quality == "stale"
    assert row.change is None


def test_live_polygon_fetch_inside_grace_is_pending_not_stale() -> None:
    monday = date(2026, 3, 9)
    clock = _et(date(2026, 3, 10), 16, 10)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": [{"o": 500.0, "c": 510.0, "t": int(_utc_midnight(monday).timestamp() * 1000)}]},
        )

    spec = _session_macro()
    spec["live"]["polygon"]["api_key_env"] = "POLYGON_API_KEY"
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, env={"POLYGON_API_KEY": "test-key"}, sleep=lambda _: None).fetch(
        clock, prior_us_close=clock
    )
    row = snap.by_symbol()["ES"]
    assert row.data_quality == "ok"
    assert row.freshness_note == PENDING_SESSION_NOTE
    assert row.change is not None
    assert any("pending session" in note for note in snap.notes)


def test_repo_macro_declares_policies_for_enabled_live_sources() -> None:
    macro = load_briefing_settings(ROOT).macro
    required = required_live_sources(macro)
    assert required == frozenset({"fred", "polygon", "coingecko", "hyperliquid"})
    assert "stooq" not in required
    cfg = load_freshness_config(macro)
    assert cfg.required_sources == required
    assert cfg.rule_for(source="fred") is not None
    assert cfg.rule_for(source="fred").policy == "calendar"
    assert cfg.lag_for(source="fred", symbol="US10Y") == ("daily", 2)
    assert cfg.lag_for(source="fred", symbol="CPI") == ("monthly", 45)
    polygon = cfg.rule_for(source="polygon")
    assert polygon is not None
    assert polygon.policy == "session"
    assert DOCUMENTED_DELAYED_PLAN_RECENCY_MINUTES == 15
    assert polygon.grace_minutes == PROVISIONAL_POLYGON_GRACE_MINUTES == 20
    assert polygon.grace_minutes == DOCUMENTED_DELAYED_PLAN_RECENCY_MINUTES + 5
    assert EARLY_CLOSE_LIMITATIONS == (
        "Friday after Thanksgiving (13:00 ET)",
        "Christmas Eve when it is a weekday (13:00 ET)",
        "July 3 when it is a midweek session (13:00 ET)",
    )
    assert "Thanksgiving Day" in FULL_CLOSE_FALSE_STALE
    assert "Christmas Day" in FULL_CLOSE_FALSE_STALE
    runbook = (ROOT / "docs" / "runbooks" / "market-pulse.md").read_text(encoding="utf-8")
    for name in EARLY_CLOSE_LIMITATIONS:
        assert name in runbook
    for name in FULL_CLOSE_FALSE_STALE:
        assert name in runbook
    assert polygon.rth_close == time(16, 0)
    assert polygon.session_timezone == "America/New_York"
    assert cfg.rule_for(source="coingecko").policy == "snapshot"
    assert cfg.rule_for(source="coingecko").max_snapshot_lag_minutes == 20
    hl = cfg.rule_for(source="hyperliquid.info /info")
    assert hl is not None and hl.policy == "snapshot"
    text = (ROOT / "packages" / "briefing" / "src" / "mm_briefing" / "freshness.py").read_text(encoding="utf-8")
    assert "_GATED_SOURCES" not in text
    raw = yaml.safe_load((ROOT / "config" / "briefing" / "macro.yaml").read_text(encoding="utf-8"))
    assert raw["freshness"]["polygon"]["policy"] == "session"
    assert "max_calendar_lag_days" not in raw["freshness"]["polygon"]


def test_missing_policy_for_enabled_source_fails_load() -> None:
    macro = yaml.safe_load((ROOT / "config" / "briefing" / "macro.yaml").read_text(encoding="utf-8"))
    del macro["freshness"]["polygon"]
    with pytest.raises(FreshnessConfigError, match="polygon"):
        load_freshness_config(macro)

    stooq_only = {"live": {"stooq": {"enabled": True, "symbols": {"ES": "es.f"}}}}
    with pytest.raises(FreshnessConfigError, match="stooq"):
        load_freshness_config(stooq_only)

    both = {
        "live": {"coingecko": {"ids": {"BTC": "bitcoin"}}},
        "crypto_pulse": {"source_of_record": "hyperliquid"},
    }
    with pytest.raises(FreshnessConfigError, match="coingecko") as exc:
        load_freshness_config(both)
    assert "hyperliquid" in str(exc.value)


def test_exemption_requires_a_reason_and_is_explicit() -> None:
    bare = {
        "live": {"stooq": {"enabled": True, "symbols": {"ES": "es.f"}}},
        "freshness": {"stooq": {"policy": "exempt"}},
    }
    with pytest.raises(FreshnessConfigError, match="exemption"):
        load_freshness_config(bare)

    named = {
        "live": {"stooq": {"enabled": True, "symbols": {"ES": "es.f"}}},
        "freshness": {
            "stooq": {
                "policy": "exempt",
                "exemption": "optional canary; not a Pulse primary path",
            }
        },
    }
    cfg = load_freshness_config(named)
    assert cfg.rule_for(source="stooq").exemption.startswith("optional canary")
    old = AssetPrint(
        symbol="ES",
        name="ES",
        last=1.0,
        prior_close=1.0,
        data_quality="ok",
        source="stooq",
        as_of=datetime(2026, 1, 1, tzinfo=UTC),
    )
    gated = apply_print_freshness(old, reference_as_of=datetime(2026, 3, 10, tzinfo=UTC), config=cfg)
    assert gated.data_quality == "ok"


def test_polygon_calendar_policy_is_rejected() -> None:
    spec = {
        "freshness": {"polygon": {"policy": "calendar", "max_calendar_lag_days": 3}},
        "live": {"polygon": {"enabled": True, "symbols": {"ES": {"ticker": "SPY"}}}},
    }
    with pytest.raises(FreshnessConfigError, match="session"):
        load_freshness_config(spec)


def test_snapshot_policy_stales_a_lagging_hyperliquid_mid() -> None:
    cfg = load_freshness_config(load_briefing_settings(ROOT).macro)
    clock = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
    fresh = AssetPrint(
        symbol="BTC",
        name="BTC",
        last=100.0,
        prior_close=90.0,
        data_quality="ok",
        source="hyperliquid.info /info",
        as_of=clock,
    )
    assert apply_print_freshness(fresh, reference_as_of=clock, config=cfg).data_quality == "ok"
    lagged = AssetPrint(
        symbol="BTC",
        name="BTC",
        last=100.0,
        prior_close=90.0,
        data_quality="ok",
        source="hyperliquid.info /info",
        as_of=clock - timedelta(minutes=21),
    )
    gated = apply_print_freshness(lagged, reference_as_of=clock, config=cfg)
    assert gated.data_quality == "stale"
    assert gated.change is None
    assert gated.freshness_note == "snapshot lag"


def test_snapshot_without_a_clock_is_not_fresh() -> None:
    cfg = load_freshness_config(load_briefing_settings(ROOT).macro)
    row = AssetPrint(
        symbol="BTC",
        name="BTC",
        last=100.0,
        prior_close=None,
        data_quality="ok",
        source="coingecko",
        as_of=None,
    )
    gated = apply_print_freshness(row, reference_as_of=datetime(2026, 3, 10, tzinfo=UTC), config=cfg)
    assert gated.data_quality == "stale"
    assert gated.freshness_note == "snapshot clock missing"


def test_fred_calendar_display_is_unchanged() -> None:
    """Session notes must not replace the FRED calendar-age label."""
    from mm_briefing.freshness import format_quality_with_age

    brief = datetime(2026, 9, 22, 20, 15, tzinfo=UTC)
    obs = datetime(2026, 9, 18, tzinfo=UTC)
    row = AssetPrint(
        symbol="US10Y",
        name="US 10Y yield",
        last=4.12,
        prior_close=4.05,
        unit="%",
        data_quality="stale",
        source="fred",
        as_of=obs,
    )
    assert format_print_quality(row, reference_as_of=brief) == format_quality_with_age(
        "stale", observation_as_of=obs, reference_as_of=brief
    )
    assert format_print_quality(row, reference_as_of=brief) == "stale (4d)"
