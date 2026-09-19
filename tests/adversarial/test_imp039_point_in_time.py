"""Adversarial PIT: later bars cannot leak into unconditional base rates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mm_common.time import parse_utc
from mm_quant.base_rates import compute_unconditional_base_rates, load_base_rate_config, snapshot_from_fixture
from mm_quant.models import SeriesBar

ROOT = Path(__file__).resolve().parents[2]
TRAP = ROOT / "tests" / "fixtures" / "phase1_base_rates" / "lookahead_trap.json"
PANEL = ROOT / "tests" / "fixtures" / "phase1_base_rates" / "panel.json"


def test_trap_watermark_excludes_future_triggers() -> None:
    full = snapshot_from_fixture(PANEL, repo_root=ROOT)
    trap = snapshot_from_fixture(TRAP, repo_root=ROOT)
    cut = trap.as_of_knowledge
    leaked = [e for e in trap.events if e.trigger_available_at > cut]
    assert leaked == []
    future = [e for e in full.events if e.trigger_available_at > cut]
    assert future
    trap_ids = {(e.event_class, e.instrument, e.trigger_index) for e in trap.events}
    full_visible = {
        (e.event_class, e.instrument, e.trigger_index)
        for e in full.events
        if e.trigger_available_at <= cut
    }
    assert trap_ids == full_visible


def test_outcome_uses_only_visible_horizon_bars() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    bars = []
    px = 100.0
    for i in range(40):
        px += 1.0
        ts = start + timedelta(days=i)
        know = ts + timedelta(hours=4)
        bars.append(
            SeriesBar(
                instrument="BTC",
                market_time=ts,
                as_of_knowledge=know,
                ingested_at=know,
                open=px,
                high=px + 0.5,
                low=px - 0.5,
                close=px,
            )
        )
    # Dip on last visible bar; horizon bars exist only after the watermark.
    last = bars[-1]
    dip_ts = last.market_time
    dip_know = last.as_of_knowledge
    bars = bars[:-1] + [
        SeriesBar(
            instrument="BTC",
            market_time=dip_ts,
            as_of_knowledge=dip_know,
            ingested_at=dip_know,
            open=px,
            high=px,
            low=px - 30.0,
            close=px - 8.0,
        )
    ]
    future = []
    fpx = px - 8.0
    for i in range(1, 8):
        fpx += 2.0
        ts = dip_ts + timedelta(days=i)
        know = ts + timedelta(hours=4)
        future.append(
            SeriesBar(
                instrument="BTC",
                market_time=ts,
                as_of_knowledge=know,
                ingested_at=know,
                open=fpx,
                high=fpx + 0.4,
                low=fpx - 0.4,
                close=fpx,
            )
        )
    cfg = load_base_rate_config(ROOT)
    cut = compute_unconditional_base_rates(tuple(bars + future), dip_know, config=cfg, fixture_id="cut")
    full = compute_unconditional_base_rates(
        tuple(bars + future), future[-1].as_of_knowledge, config=cfg, fixture_id="full"
    )
    dip_cut = [e for e in cut.events if e.event_class == "dip_touch"]
    dip_full = [e for e in full.events if e.event_class == "dip_touch"]
    assert dip_cut
    assert all(e.censored for e in dip_cut)
    assert any(not e.censored for e in dip_full)


def test_published_at_is_not_the_clock() -> None:
    snap = snapshot_from_fixture(PANEL, repo_root=ROOT)
    assert snap.as_of_knowledge == snap.ingested_at
    assert "published_at" not in snap.canonical()
    parse_utc(snap.canonical()["as_of_knowledge"])
