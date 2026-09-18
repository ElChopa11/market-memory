"""Phase 6b / IMP-015: macro regime classifier + EVENT_RISK."""

from __future__ import annotations

from pathlib import Path

from mm_desks.orchestrator import run_from_fixture
from mm_desks.protocol import DEGRADED, OK
from mm_macro.config import load_macro_config
from mm_macro.engine import compute_macro
from mm_macro.models import MacroPoint
from mm_macro.regime import classify_macro_regime
from mm_common.time import parse_utc

ROOT = Path(__file__).resolve().parents[2]
HAPPY = ROOT / "tests" / "fixtures" / "phase6b" / "frozen_day.json"
EVENT = ROOT / "tests" / "fixtures" / "phase6b" / "event_risk.json"
MISSING = ROOT / "tests" / "fixtures" / "phase6b" / "missing_feeds.json"
WATERMARK = parse_utc("2026-09-18T00:05:00Z")


def test_regime_tag_from_two_driving_inputs() -> None:
    cfg = load_macro_config(ROOT)
    result = classify_macro_regime({"VIX": 16.5, "DXY": 103.2}, watermark=WATERMARK, config=cfg)
    assert result.status == "ok"
    assert result.tag == "risk_on_usd_mid"
    assert result.confidence > 0
    driving = result.driving_inputs
    assert driving["VIX"] == 16.5
    assert driving["DXY"] == 103.2
    assert driving["thresholds"]["vix_risk_on_below"] == cfg.vix.risk_on_below


def test_missing_driver_is_unavailable_never_invented() -> None:
    cfg = load_macro_config(ROOT)
    result = classify_macro_regime({"VIX": 16.5, "DXY": None}, watermark=WATERMARK, config=cfg)
    assert result.tag == "unavailable"
    assert result.status == "unavailable"
    assert result.confidence == 0.0


def test_threshold_change_changes_tag() -> None:
    cfg = load_macro_config(ROOT)
    a = classify_macro_regime({"VIX": 16.5, "DXY": 103.2}, watermark=WATERMARK, config=cfg)
    # Push VIX through the risk_off threshold.
    b = classify_macro_regime({"VIX": 40.0, "DXY": 103.2}, watermark=WATERMARK, config=cfg)
    assert a.tag != b.tag
    assert b.tag == "risk_off_usd_mid"


def test_macro_desk_happy_path_regime_and_no_event_risk() -> None:
    result = run_from_fixture(HAPPY, repo_root=ROOT, slugs=("intel",))
    intel = result.desks[0]
    macro = intel.payload["macro"]
    assert intel.status == OK
    assert intel.regime == "risk_on_usd_mid"
    assert macro["regime_tag"] == "risk_on_usd_mid"
    assert macro["event_risk"]["tagged"] is False
    assert set(macro["missing"]) == set()


def test_event_risk_within_window_exposes_rule_id() -> None:
    result = run_from_fixture(EVENT, repo_root=ROOT, slugs=("intel",))
    er = result.desks[0].payload["macro"]["event_risk"]
    assert er["tagged"] is True
    assert er["rule_id"] == "event_risk"
    assert er["size_haircut_pct"] is not None
    assert "FOMC" in (er["event_name"] or "")


def test_missing_macro_feeds_degraded() -> None:
    result = run_from_fixture(MISSING, repo_root=ROOT, slugs=("intel",))
    intel = result.desks[0]
    macro = intel.payload["macro"]
    assert intel.status == DEGRADED
    assert intel.regime == "unset"
    assert "VIX" in macro["missing"]
    assert "DXY" in macro["missing"]


def test_compute_macro_pit_ignores_future_points() -> None:
    future = MacroPoint(
        instrument="VIX",
        metric="fred_observation",
        as_of_knowledge=parse_utc("2026-09-26T00:00:00Z"),
        value=99.0,
        observation_id="trap",
    )
    present = MacroPoint(
        instrument="VIX",
        metric="fred_observation",
        as_of_knowledge=WATERMARK,
        value=16.5,
        observation_id="now",
    )
    dxy = MacroPoint(
        instrument="DXY",
        metric="fred_observation",
        as_of_knowledge=WATERMARK,
        value=103.2,
        observation_id="dxy",
    )
    snap = compute_macro(series=(present, future, dxy), calendar=(), watermark=WATERMARK, repo_root=ROOT)
    assert snap.regime.driving_inputs["VIX"] == 16.5
    assert snap.regime.tag == "risk_on_usd_mid"
