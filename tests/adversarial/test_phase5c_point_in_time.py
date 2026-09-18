"""Adversarial PIT: Phase 5c factors key off as_of_knowledge, never market_time."""

from __future__ import annotations

from pathlib import Path

from mm_common.time import parse_utc
from mm_quant.config import load_quant_config
from mm_quant.factors import FactorRegistry
from mm_quant.panel import load_panel_file
from mm_quant.series import visible_bars

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "phase5c"
WATERMARK = parse_utc("2026-09-18T00:05:00Z")
AFTER_TRAP = parse_utc("2026-09-26T00:00:00Z")


def test_lookahead_bars_hidden_until_ingested() -> None:
    trap = load_panel_file(FIXTURES / "lookahead_trap.json")
    leaked_if_market_time = [
        bar for bar in trap.bars if bar.market_time <= WATERMARK and (bar.observation_id or "").startswith("trap-")
    ]
    assert leaked_if_market_time, "fixture must include a trap whose exchange time is before the watermark"
    visible = visible_bars(trap.bars, WATERMARK)
    assert all(not (bar.observation_id or "").startswith("trap-") for bar in visible)
    later = visible_bars(trap.bars, AFTER_TRAP)
    assert any((bar.observation_id or "").startswith("trap-") for bar in later)


def test_factors_ignore_future_knowledge() -> None:
    honest = load_panel_file(FIXTURES / "panel.json")
    trap = load_panel_file(FIXTURES / "lookahead_trap.json")
    reg = FactorRegistry(load_quant_config(ROOT))
    a = reg.compute_all("BTC", honest, WATERMARK)
    b = reg.compute_all("BTC", trap, WATERMARK)
    def _core(row):
        return (row.name, row.status, row.value, row.window, row.payload.get("matrix") is not None)
    assert [_core(row) for row in a] == [_core(row) for row in b]
    assert a[0].value == b[0].value
    nvda_a = reg.compute("momentum_short", "NVDA", honest, WATERMARK)
    nvda_b = reg.compute("momentum_short", "NVDA", trap, WATERMARK)
    assert nvda_a.value == nvda_b.value
    assert nvda_a.status == nvda_b.status


def test_future_watermark_sees_trap_and_changes_momentum() -> None:
    honest = load_panel_file(FIXTURES / "panel.json")
    trap = load_panel_file(FIXTURES / "lookahead_trap.json")
    reg = FactorRegistry(load_quant_config(ROOT))
    honest_m = reg.compute("momentum_short", "BTC", honest, AFTER_TRAP)
    trap_m = reg.compute("momentum_short", "BTC", trap, AFTER_TRAP)
    assert honest_m.status == "ok"
    assert trap_m.status == "ok"
    assert trap_m.value != honest_m.value
    assert trap_m.value is not None and trap_m.value > 1.0
