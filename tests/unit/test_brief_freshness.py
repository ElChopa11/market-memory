"""FRED / Pulse freshness: quality from observation age, not fetch success."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_briefing.config import load_briefing_settings
from mm_briefing.fetchers import LiveMacroFetcher, complete_cross_asset
from mm_briefing.freshness import (
    DEFAULT_FRED_DAILY_MAX_BUSINESS_LAG_DAYS,
    DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS,
    AGE_BASIS_BUSINESS,
    apply_print_freshness,
    business_age_days,
    calendar_age_days,
    format_quality_with_age,
    gate_snapshot_freshness,
    load_freshness_config,
    quality_from_observation_age,
)
from mm_briefing.models import AssetPrint, MacroSnapshot, pulse_quality


ROOT = Path(__file__).resolve().parents[2]
# US Close Brief incident: brief 2026-09-22, FRED US10Y as-of 2026-09-18 (4 calendar days).
BRIEF_AS_OF = datetime(2026, 9, 22, 20, 15, tzinfo=timezone.utc)
OBS_AS_OF = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)
PRIOR = datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc)
# Monthly FRED stamp often month-start; ~40d behind brief is legitimate for CPI/NFP.
CPI_OBS_AS_OF = datetime(2026, 8, 13, 0, 0, tzinfo=timezone.utc)  # age 40d vs 2026-09-22


def test_repo_macro_yaml_documents_fred_default_and_monthly_overrides() -> None:
    settings = load_briefing_settings(ROOT)
    cfg = load_freshness_config(settings.macro)
    rule = cfg.rule_for(source="fred")
    assert rule is not None
    assert rule.cadence == "daily"
    assert rule.age_basis == AGE_BASIS_BUSINESS
    # Daily threshold is 1 business day, not 1 calendar day.
    assert rule.max_calendar_lag_days == DEFAULT_FRED_DAILY_MAX_BUSINESS_LAG_DAYS == 1

    us10y = cfg.lag_for(source="fred", symbol="US10Y")
    assert us10y is not None
    assert us10y.cadence == "daily"
    assert us10y.max_lag_days == 1
    assert us10y.age_basis == "business"

    # Unlisted daily symbol still gets the source default (not monthly).
    dgs_other = cfg.lag_for(source="fred", symbol="US2Y")
    assert dgs_other is not None
    assert (dgs_other.cadence, dgs_other.max_lag_days, dgs_other.age_basis) == ("daily", 1, "business")

    cpi = cfg.lag_for(source="fred", symbol="CPI")
    assert cpi is not None
    assert cpi.cadence == "monthly"
    assert cpi.max_lag_days == DEFAULT_FRED_MONTHLY_MAX_CALENDAR_LAG_DAYS
    assert cpi.age_basis == "calendar"
    nfp = cfg.lag_for(source="fred", symbol="NFP", series_id="PAYEMS")
    assert nfp is not None
    assert (nfp.cadence, nfp.max_lag_days, nfp.age_basis) == ("monthly", 45, "calendar")
    # Match monthly override by FRED series id alone.
    cpi_id = cfg.lag_for(source="fred", series_id="CPIAUCSL")
    assert cpi_id is not None
    assert (cpi_id.cadence, cpi_id.max_lag_days, cpi_id.age_basis) == ("monthly", 45, "calendar")


def test_calendar_age_four_days_behind_brief() -> None:
    assert calendar_age_days(OBS_AS_OF, BRIEF_AS_OF) == 4
    assert calendar_age_days(CPI_OBS_AS_OF, BRIEF_AS_OF) == 40


def test_fred_observation_four_days_behind_cannot_be_fresh() -> None:
    """Incident case: daily age 4d with max_lag 2 → stale; display never fresh."""
    quality = quality_from_observation_age(
        "ok",
        observation_as_of=OBS_AS_OF,
        reference_as_of=BRIEF_AS_OF,
        max_calendar_lag_days=2,
    )
    assert quality == "stale"
    assert pulse_quality(quality) == "stale"
    assert format_quality_with_age(
        quality,
        observation_as_of=OBS_AS_OF,
        reference_as_of=BRIEF_AS_OF,
    ) == "stale (4d)"


def test_fred_within_threshold_stays_ok() -> None:
    # Calendar-basis comparator only (explicit lag 2). Not the daily FRED gate.
    # Daily FRED uses business-day age; see test_friday_print_is_fresh_on_monday.
    same = quality_from_observation_age(
        "ok",
        observation_as_of=BRIEF_AS_OF,
        reference_as_of=BRIEF_AS_OF,
        max_calendar_lag_days=2,
    )
    assert same == "ok"
    assert pulse_quality(same) == "fresh"
    two_days = quality_from_observation_age(
        "ok",
        observation_as_of=datetime(2026, 9, 20, tzinfo=timezone.utc),
        reference_as_of=BRIEF_AS_OF,
        max_calendar_lag_days=2,
    )
    assert two_days == "ok"
    three_days = quality_from_observation_age(
        "ok",
        observation_as_of=datetime(2026, 9, 19, tzinfo=timezone.utc),
        reference_as_of=BRIEF_AS_OF,
        max_calendar_lag_days=2,
    )
    assert three_days == "stale"


def test_monthly_fred_40d_old_not_falsely_stale_under_daily_default() -> None:
    """CPI/NFP at ~40d must stay ok under monthly override; daily default would wrong-stale."""
    cfg = load_freshness_config(load_briefing_settings(ROOT).macro)
    # Under daily default alone, age 40 would be stale — that is the bug we must not reintroduce.
    assert (
        quality_from_observation_age(
            "ok",
            observation_as_of=CPI_OBS_AS_OF,
            reference_as_of=BRIEF_AS_OF,
            max_calendar_lag_days=2,
        )
        == "stale"
    )

    cpi = AssetPrint(
        symbol="CPI",
        name="CPI",
        last=3.1,
        prior_close=3.0,
        unit="%",
        data_quality="ok",
        source="fred",
        as_of=CPI_OBS_AS_OF,
    )
    gated = apply_print_freshness(cpi, reference_as_of=BRIEF_AS_OF, config=cfg)
    assert calendar_age_days(CPI_OBS_AS_OF, BRIEF_AS_OF) == 40
    assert gated.data_quality == "ok"
    assert pulse_quality(gated.data_quality) == "fresh"

    nfp = AssetPrint(
        symbol="NFP",
        name="Nonfarm payrolls",
        last=150.0,
        prior_close=140.0,
        unit="idx",
        data_quality="ok",
        source="fred",
        as_of=CPI_OBS_AS_OF,
    )
    assert apply_print_freshness(nfp, reference_as_of=BRIEF_AS_OF, config=cfg).data_quality == "ok"


def test_monthly_fred_stale_only_past_its_own_threshold() -> None:
    cfg = load_freshness_config(load_briefing_settings(ROOT).macro)
    # age 46 > monthly 45 → stale; still would also be stale under daily, but threshold is series-own.
    old = datetime(2026, 8, 7, tzinfo=timezone.utc)  # 46 days before 2026-09-22
    assert calendar_age_days(old, BRIEF_AS_OF) == 46
    cpi = AssetPrint(
        symbol="CPI",
        name="CPI",
        last=3.1,
        prior_close=3.0,
        unit="%",
        data_quality="ok",
        source="fred",
        as_of=old,
    )
    gated = apply_print_freshness(cpi, reference_as_of=BRIEF_AS_OF, config=cfg)
    assert gated.data_quality == "stale"
    assert format_quality_with_age(
        gated.data_quality,
        observation_as_of=old,
        reference_as_of=BRIEF_AS_OF,
    ) == "stale (46d)"


def test_unavailable_not_promoted_by_age_gate() -> None:
    assert (
        quality_from_observation_age(
            "unavailable",
            observation_as_of=OBS_AS_OF,
            reference_as_of=BRIEF_AS_OF,
            max_calendar_lag_days=2,
        )
        == "unavailable"
    )


def test_apply_print_freshness_gates_fred_only() -> None:
    fred = AssetPrint(
        symbol="US10Y",
        name="US 10Y yield",
        last=4.12,
        prior_close=4.05,
        unit="%",
        data_quality="ok",
        source="fred",
        as_of=OBS_AS_OF,
    )
    gated = apply_print_freshness(fred, reference_as_of=BRIEF_AS_OF)
    assert gated.data_quality == "stale"
    assert gated.last == 4.12  # never invent / wipe the figure

    fixture = AssetPrint(
        symbol="US10Y",
        name="US 10Y yield",
        last=4.12,
        prior_close=4.05,
        unit="%",
        data_quality="ok",
        source="fixture",
        as_of=OBS_AS_OF,
    )
    assert apply_print_freshness(fixture, reference_as_of=BRIEF_AS_OF).data_quality == "ok"


def test_complete_cross_asset_downgrades_aged_fred() -> None:
    snap = MacroSnapshot(
        as_of=BRIEF_AS_OF,
        prior_us_close=PRIOR,
        assets=(
            AssetPrint(
                symbol="US10Y",
                name="US 10Y yield",
                last=4.12,
                prior_close=4.05,
                unit="%",
                data_quality="ok",
                source="fred",
                as_of=OBS_AS_OF,
            ),
        ),
        data_quality="ok",
        source="live",
    )
    filled = complete_cross_asset(snap)
    us10y = filled.by_symbol()["US10Y"]
    assert us10y.data_quality == "stale"
    assert pulse_quality(us10y.data_quality) != "fresh"
    # Other required slots fill as unavailable; roll-up is worst across slots.
    assert filled.data_quality in {"stale", "unavailable", "partial"}
    assert pulse_quality(us10y.data_quality) == "stale"


def test_complete_cross_asset_keeps_monthly_fred_fresh_at_40d() -> None:
    snap = MacroSnapshot(
        as_of=BRIEF_AS_OF,
        prior_us_close=PRIOR,
        assets=(
            AssetPrint(
                symbol="CPI",
                name="CPI",
                last=3.1,
                prior_close=3.0,
                unit="%",
                data_quality="ok",
                source="fred",
                as_of=CPI_OBS_AS_OF,
            ),
            AssetPrint(
                symbol="US10Y",
                name="US 10Y yield",
                last=4.12,
                prior_close=4.05,
                unit="%",
                data_quality="ok",
                source="fred",
                as_of=OBS_AS_OF,
            ),
        ),
        data_quality="ok",
        source="live",
    )
    filled = complete_cross_asset(snap, freshness=load_freshness_config(load_briefing_settings(ROOT).macro))
    assert filled.by_symbol()["CPI"].data_quality == "ok"
    assert pulse_quality(filled.by_symbol()["CPI"].data_quality) == "fresh"
    assert filled.by_symbol()["US10Y"].data_quality == "stale"


def test_live_fred_fetcher_four_day_old_observation_is_stale() -> None:
    """HTTP succeeds with a 4-day-old FRED print → quality stale, not fresh."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "series_id=DGS10" in str(request.url)
        return httpx.Response(
            200,
            json={
                "observations": [
                    {"date": "2026-09-18", "value": "4.12"},
                    {"date": "2026-09-17", "value": "4.05"},
                ]
            },
        )

    spec = {
        "freshness": {
            "fred": {
                "cadence": "daily",
                "age_basis": "business",
                "max_lag_days": 1,
                "series": {
                    "US10Y": {"cadence": "daily", "age_basis": "business", "fred_series_id": "DGS10"},
                    "CPI": {
                        "cadence": "monthly",
                        "age_basis": "calendar",
                        "max_lag_days": 45,
                        "fred_series_id": "CPIAUCSL",
                    },
                },
            }
        },
        "live": {
            "enabled": True,
            "fred": {
                "enabled": True,
                "api_key_env": "FRED_API_KEY",
                "series": {"US10Y": "DGS10"},
            },
            "stooq": {"enabled": False},
            "coingecko": {"enabled": False},
        },
    }
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, env={"FRED_API_KEY": "test-key"}, sleep=lambda _: None).fetch(
        BRIEF_AS_OF, prior_us_close=PRIOR
    )
    assert len(snap.assets) == 1
    row = snap.assets[0]
    assert row.symbol == "US10Y"
    assert row.last == 4.12
    assert row.data_quality == "stale"
    assert pulse_quality(row.data_quality) == "stale"
    assert calendar_age_days(row.as_of, BRIEF_AS_OF) == 4


def test_live_fred_fetcher_monthly_cpi_40d_stays_fresh() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "series_id=CPIAUCSL" in str(request.url)
        return httpx.Response(
            200,
            json={
                "observations": [
                    {"date": "2026-08-13", "value": "3.1"},
                    {"date": "2026-07-13", "value": "3.0"},
                ]
            },
        )

    spec = {
        "freshness": {
            "fred": {
                "cadence": "daily",
                "age_basis": "business",
                "max_lag_days": 1,
                "series": {
                    "CPI": {
                        "cadence": "monthly",
                        "age_basis": "calendar",
                        "max_lag_days": 45,
                        "fred_series_id": "CPIAUCSL",
                    },
                },
            }
        },
        "live": {
            "enabled": True,
            "fred": {
                "enabled": True,
                "api_key_env": "FRED_API_KEY",
                "series": {"CPI": "CPIAUCSL"},
            },
            "stooq": {"enabled": False},
            "coingecko": {"enabled": False},
        },
    }
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, env={"FRED_API_KEY": "test-key"}, sleep=lambda _: None).fetch(
        BRIEF_AS_OF, prior_us_close=PRIOR
    )
    row = snap.assets[0]
    assert row.symbol == "CPI"
    assert row.last == 3.1
    assert calendar_age_days(row.as_of, BRIEF_AS_OF) == 40
    assert row.data_quality == "ok"
    assert pulse_quality(row.data_quality) == "fresh"


def test_business_age_matches_half_open_weekday_count() -> None:
    friday = datetime(2026, 9, 18, tzinfo=timezone.utc)
    monday = datetime(2026, 9, 21, tzinfo=timezone.utc)
    wednesday = datetime(2026, 9, 23, tzinfo=timezone.utc)
    assert business_age_days(friday, monday) == 1
    assert business_age_days(monday, wednesday) == 2
    assert business_age_days(monday, monday) == 0
    # Weekend does not add a business day: Sunday → Tuesday counts Monday only.
    assert business_age_days(datetime(2026, 9, 20, tzinfo=timezone.utc), BRIEF_AS_OF) == 1


def test_friday_print_is_fresh_on_monday() -> None:
    """Principal case. Friday as_of + following Monday must render fresh.

    Calendar-day lag=1 would mark this stale (3 calendar days). That gate is not shipped.
    """
    friday = datetime(2026, 9, 18, tzinfo=timezone.utc)
    monday = datetime(2026, 9, 21, 20, 15, tzinfo=timezone.utc)
    assert calendar_age_days(friday, monday) == 3
    assert business_age_days(friday, monday) == 1
    cfg = load_freshness_config(load_briefing_settings(ROOT).macro)
    row = AssetPrint(
        symbol="US10Y",
        name="US 10Y yield",
        last=4.12,
        prior_close=4.05,
        unit="%",
        data_quality="ok",
        source="fred",
        as_of=friday,
    )
    gated = apply_print_freshness(row, reference_as_of=monday, config=cfg)
    assert gated.data_quality == "ok"
    assert pulse_quality(gated.data_quality) == "fresh"
    assert (
        format_quality_with_age(
            gated.data_quality,
            observation_as_of=friday,
            reference_as_of=monday,
            age_basis="business",
        )
        == "fresh"
    )


def test_daily_business_age_zero_and_one_fresh_two_stale() -> None:
    cfg = load_freshness_config(load_briefing_settings(ROOT).macro)
    monday = datetime(2026, 9, 21, tzinfo=timezone.utc)
    wednesday = datetime(2026, 9, 23, 20, 15, tzinfo=timezone.utc)
    assert business_age_days(monday, wednesday) == 2

    def _row(as_of: datetime) -> AssetPrint:
        return AssetPrint(
            symbol="US10Y",
            name="US 10Y yield",
            last=4.12,
            prior_close=4.05,
            unit="%",
            data_quality="ok",
            source="fred",
            as_of=as_of,
        )

    same = apply_print_freshness(_row(wednesday), reference_as_of=wednesday, config=cfg)
    assert same.data_quality == "ok"
    one = apply_print_freshness(
        _row(datetime(2026, 9, 22, tzinfo=timezone.utc)),
        reference_as_of=wednesday,
        config=cfg,
    )
    assert business_age_days(datetime(2026, 9, 22, tzinfo=timezone.utc), wednesday) == 1
    assert one.data_quality == "ok"
    two = apply_print_freshness(_row(monday), reference_as_of=wednesday, config=cfg)
    assert two.data_quality == "stale"
    assert pulse_quality(two.data_quality) == "stale"
    assert (
        format_quality_with_age(
            two.data_quality,
            observation_as_of=monday,
            reference_as_of=wednesday,
            age_basis="business",
        )
        == "stale (2bd)"
    )


def test_gate_snapshot_uses_business_day_threshold() -> None:
    """Mon 2026-09-21 read on Wed 2026-09-23 is 2 business days → stale at lag 1."""
    monday = datetime(2026, 9, 21, tzinfo=timezone.utc)
    wednesday = datetime(2026, 9, 23, 20, 15, tzinfo=timezone.utc)
    snap = MacroSnapshot(
        as_of=wednesday,
        prior_us_close=PRIOR,
        assets=(
            AssetPrint(
                symbol="US10Y",
                name="US 10Y yield",
                last=4.12,
                prior_close=4.05,
                unit="%",
                data_quality="ok",
                source="fred",
                as_of=monday,
            ),
        ),
        data_quality="ok",
        source="live",
    )
    assert gate_snapshot_freshness(snap).assets[0].data_quality == "stale"
    # Explicit calendar basis is not the daily product. Age 2 calendar with lag 2 stays ok.
    calendar_cfg = load_freshness_config(
        {"freshness": {"fred": {"cadence": "daily", "age_basis": "calendar", "max_lag_days": 2}}}
    )
    assert gate_snapshot_freshness(snap, config=calendar_cfg).assets[0].data_quality == "ok"
