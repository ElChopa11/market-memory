"""Alerts must not push without numeric thresholds; example types use observations."""

from __future__ import annotations

from mm_briefing.alerts import MISSING_THRESHOLD_REASON, evaluate_alerts
from mm_briefing.config import AlertSettings, AlertTypeThresholds
from mm_briefing.hl import hl_from_payload
from mm_briefing.engine import load_fixture_file
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"


def _hl():
    return hl_from_payload(load_fixture_file(FIXTURE)["hyperliquid"])


def test_missing_thresholds_never_push() -> None:
    settings = AlertSettings(enabled=True, require_threshold_config=True, interval_minutes=15, types=())
    decision = evaluate_alerts(_hl(), settings)
    assert decision.pushed is False
    assert decision.reason == MISSING_THRESHOLD_REASON
    assert decision.events == ()


def test_disabled_alerts_never_push() -> None:
    settings = AlertSettings(
        enabled=False,
        require_threshold_config=True,
        interval_minutes=15,
        types=(
            AlertTypeThresholds(
                alert_type="liquidation_spike",
                enabled=True,
                params={"min_size": 0.01},
            ),
        ),
    )
    decision = evaluate_alerts(_hl(), settings)
    assert decision.pushed is False
    assert decision.reason == "alerts_disabled"


def test_liquidation_spike_respects_min_size() -> None:
    hl = _hl()
    quiet = AlertSettings(
        enabled=True,
        require_threshold_config=True,
        interval_minutes=15,
        types=(AlertTypeThresholds("liquidation_spike", True, {"min_size": 99.0}),),
    )
    assert evaluate_alerts(hl, quiet).pushed is False

    noisy = AlertSettings(
        enabled=True,
        require_threshold_config=True,
        interval_minutes=15,
        types=(AlertTypeThresholds("liquidation_spike", True, {"min_size": 1.0}),),
    )
    fired = evaluate_alerts(hl, noisy)
    assert fired.pushed is True
    assert fired.reason == "threshold_crossed"
    assert len(fired.events) == 1
    event = fired.events[0]
    assert event.alert_type == "liquidation_spike"
    assert event.instrument == "BTC"
    assert "01FROZENBTCLIQ000000000001" in event.evidence


def test_funding_oi_divergence_requires_opposite_signs_and_thresholds() -> None:
    hl = _hl()
    settings = AlertSettings(
        enabled=True,
        require_threshold_config=True,
        interval_minutes=15,
        types=(
            AlertTypeThresholds(
                "funding_oi_divergence",
                True,
                {"min_abs_funding": 0.0003, "min_oi_change_pct": 5.0},
            ),
        ),
    )
    # Frozen day: BTC funding +0.0004 with OI +20% — same sign, must not fire.
    decision = evaluate_alerts(hl, settings)
    assert decision.pushed is False
    assert decision.reason == "no_threshold_crossed"


def test_same_alert_is_not_re_pushed() -> None:
    hl = _hl()
    settings = AlertSettings(
        enabled=True,
        require_threshold_config=True,
        interval_minutes=15,
        types=(AlertTypeThresholds("liquidation_spike", True, {"min_size": 1.0}),),
    )
    first = evaluate_alerts(hl, settings)
    assert first.pushed is True
    second = evaluate_alerts(hl, settings, prior_identity_hashes=[first.events[0].identity_hash])
    assert second.pushed is False
    assert second.reason == "no_threshold_crossed"
