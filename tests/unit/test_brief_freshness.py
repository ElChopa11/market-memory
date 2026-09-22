"""FRED / Pulse freshness: quality from observation age, not fetch success."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_briefing.config import load_briefing_settings
from mm_briefing.fetchers import LiveMacroFetcher, complete_cross_asset
from mm_briefing.freshness import (
    DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS,
    apply_print_freshness,
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


def test_repo_macro_yaml_documents_fred_lag_threshold() -> None:
    settings = load_briefing_settings(ROOT)
    cfg = load_freshness_config(settings.macro)
    rule = cfg.rule_for(source="fred", symbol="US10Y")
    assert rule is not None
    assert rule.cadence == "daily"
    assert rule.max_calendar_lag_days == DEFAULT_FRED_MAX_CALENDAR_LAG_DAYS == 2


def test_calendar_age_four_days_behind_brief() -> None:
    assert calendar_age_days(OBS_AS_OF, BRIEF_AS_OF) == 4


def test_fred_observation_four_days_behind_cannot_be_fresh() -> None:
    """Incident case: age 4d with max_lag 2 → stale; display never fresh."""
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
    # Same-day and T+2 remain eligible for fresh (age <= 2).
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
        "freshness": {"fred": {"cadence": "daily", "max_calendar_lag_days": 2}},
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


def test_gate_snapshot_uses_config_threshold() -> None:
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
                as_of=datetime(2026, 9, 20, tzinfo=timezone.utc),  # age 2 → ok at lag 2
            ),
        ),
        data_quality="ok",
        source="live",
    )
    assert gate_snapshot_freshness(snap).assets[0].data_quality == "ok"
    tight = load_freshness_config({"freshness": {"fred": {"max_calendar_lag_days": 1}}})
    assert gate_snapshot_freshness(snap, config=tight).assets[0].data_quality == "stale"
