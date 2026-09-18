"""Adversarial PIT: Phase 6b flow/macro key off as_of_knowledge, never market_time."""

from __future__ import annotations

from pathlib import Path

from mm_common.time import parse_utc
from mm_desks.fixture import load_frozen_day
from mm_desks.flow import flow_panel
from mm_desks.macro import macro_calendar, macro_series
from mm_desks.protocol import DeskContext
from mm_flow.config import load_flow_config
from mm_flow.engine import compute_flow
from mm_macro.config import load_macro_config
from mm_macro.engine import compute_macro

ROOT = Path(__file__).resolve().parents[2]
HONEST = ROOT / "tests" / "fixtures" / "phase6b" / "frozen_day.json"
TRAP = ROOT / "tests" / "fixtures" / "phase6b" / "lookahead_trap.json"
WATERMARK = parse_utc("2026-09-18T00:05:00Z")
AFTER = parse_utc("2026-09-26T00:00:00Z")


def test_flow_ignores_future_funding_print() -> None:
    honest = load_frozen_day(HONEST, repo_root=ROOT)
    trap = load_frozen_day(TRAP, repo_root=ROOT)
    cfg = load_flow_config(ROOT)
    a = compute_flow("BTC", flow_panel(DeskContext(repo_root=ROOT, fixture=honest, thesis=honest.thesis)), WATERMARK, config=cfg)
    b = compute_flow("BTC", flow_panel(DeskContext(repo_root=ROOT, fixture=trap, thesis=trap.thesis)), WATERMARK, config=cfg)
    za = next(row for row in a.metrics if row.name == "funding_z")
    zb = next(row for row in b.metrics if row.name == "funding_z")
    assert za.value == zb.value
    assert za.status == zb.status
    later = compute_flow("BTC", flow_panel(DeskContext(repo_root=ROOT, fixture=trap, thesis=trap.thesis)), AFTER, config=cfg)
    z_later = next(row for row in later.metrics if row.name == "funding_z")
    assert z_later.value != za.value


def test_macro_ignores_future_vix_and_uningested_event() -> None:
    honest = load_frozen_day(HONEST, repo_root=ROOT)
    trap = load_frozen_day(TRAP, repo_root=ROOT)
    cfg = load_macro_config(ROOT)
    ctx_h = DeskContext(repo_root=ROOT, fixture=honest, thesis=honest.thesis)
    ctx_t = DeskContext(repo_root=ROOT, fixture=trap, thesis=trap.thesis)
    a = compute_macro(series=macro_series(ctx_h), calendar=macro_calendar(ctx_h), watermark=WATERMARK, config=cfg)
    b = compute_macro(series=macro_series(ctx_t), calendar=macro_calendar(ctx_t), watermark=WATERMARK, config=cfg)
    assert a.regime.tag == b.regime.tag
    assert a.regime.driving_inputs["VIX"] == b.regime.driving_inputs["VIX"]
    assert b.event_risk.tagged is False
    later = compute_macro(series=macro_series(ctx_t), calendar=macro_calendar(ctx_t), watermark=AFTER, config=cfg)
    assert later.regime.tag != a.regime.tag
    assert later.event_risk.tagged is True
    assert later.event_risk.rule_id == "event_risk"
    assert later.event_risk.event_name and "FOMC" in later.event_risk.event_name
