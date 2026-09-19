"""IMP-039 Phase 1 unconditional event-class base rates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mm_common.naming import BASE_RATE, QUANT, SLEEVE_MAP, sleeve_display
from mm_common.time import parse_utc
from mm_quant.base_rates import (
    CANDIDATE_BENCHMARKS,
    DIP_TOUCH,
    NO_CLAIM_REASON,
    PULLBACK_EMA_TOUCH,
    ZONE_BOUNDARY_TOUCH,
    compute_unconditional_base_rates,
    load_base_rate_config,
    params_hash_for,
    snapshot_from_fixture,
)
from mm_quant.language import language_violations
from mm_quant.models import SeriesBar

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "tests" / "fixtures" / "phase1_base_rates" / "panel.json"
TRAP = ROOT / "tests" / "fixtures" / "phase1_base_rates" / "lookahead_trap.json"


def _bar(inst: str, i: int, close: float, high: float | None = None, low: float | None = None) -> SeriesBar:
    ts = datetime(2024, 1, 2, tzinfo=timezone.utc) + timedelta(days=i)
    know = ts + timedelta(hours=4)
    return SeriesBar(
        instrument=inst,
        market_time=ts,
        as_of_knowledge=know,
        ingested_at=know,
        open=close,
        high=close + 1.0 if high is None else high,
        low=close - 1.0 if low is None else low,
        close=close,
        asset_class="crypto",
    )


def test_sleeve_is_quant_not_a_desk() -> None:
    assert SLEEVE_MAP[BASE_RATE] == QUANT
    assert sleeve_display(BASE_RATE).startswith("Quant")
    assert CANDIDATE_BENCHMARKS == {
        "C-001": ZONE_BOUNDARY_TOUCH,
        "C-002": DIP_TOUCH,
        "C-003": PULLBACK_EMA_TOUCH,
    }


def test_fixture_detects_all_three_classes_without_claim() -> None:
    snap = snapshot_from_fixture(PANEL, repo_root=ROOT)
    assert snap.instrument_set == ("BTC", "NVDA")
    assert snap.as_of_knowledge == snap.ingested_at
    assert snap.n_llm_calls == 0
    classes = {e.event_class for e in snap.events}
    assert classes == {DIP_TOUCH, ZONE_BOUNDARY_TOUCH, PULLBACK_EMA_TOUCH}
    by_class = {r.event_class: r for r in snap.rates}
    assert set(by_class) == classes
    for rate in snap.rates:
        assert rate.n >= 1
        assert rate.n < rate.n_min
        assert rate.claimed is False
        assert rate.reason == NO_CLAIM_REASON
        assert rate.hit_rate is None
    assert by_class[DIP_TOUCH].cites_candidate == "C-002"
    assert by_class[ZONE_BOUNDARY_TOUCH].cites_candidate == "C-001"
    assert by_class[PULLBACK_EMA_TOUCH].cites_candidate == "C-003"
    assert snap.cost_model["clip_is_not_a_size"] is True
    assert "size_pct" not in snap.canonical()


def test_params_hash_stable_and_independent_of_results() -> None:
    cfg = load_base_rate_config(ROOT)
    a = params_hash_for(cfg)
    b = params_hash_for(cfg)
    assert a == b
    snap = snapshot_from_fixture(PANEL, repo_root=ROOT)
    assert snap.params_hash == a
    other = dict(cfg)
    other["n_min"] = 99
    assert params_hash_for(other) != a


def test_n_below_min_is_no_claim_even_with_events() -> None:
    bars = tuple(_bar("BTC", i, 100 + i * 0.2) for i in range(8))
    cfg = load_base_rate_config(ROOT)
    snap = compute_unconditional_base_rates(
        bars,
        bars[-1].as_of_knowledge,
        config=cfg,
        fixture_id="short",
    )
    assert all(r.claimed is False for r in snap.rates)
    assert all(r.hit_rate is None for r in snap.rates)


def test_claimed_when_n_meets_min() -> None:
    """Repeating dip geometry until n >= n_min. Not a candidate study."""
    cfg = dict(load_base_rate_config(ROOT))
    cfg["n_min"] = 5
    closes: list[float] = []
    lows: list[float] = []
    px = 100.0
    for _i in range(24):
        px += 1.0
        closes.append(px)
        lows.append(px - 0.15)
    for _cycle in range(8):
        for _up in range(8):
            px += 1.2
            closes.append(px)
            lows.append(px - 0.15)
        px -= 2.0
        closes.append(px)
        lows.append(px - 12.0)
        px += 4.0
        closes.append(px)
        lows.append(px - 0.15)
    bars = tuple(
        _bar("BTC", i, closes[i], high=closes[i] + 0.4, low=lows[i]) for i in range(len(closes))
    )
    snap = compute_unconditional_base_rates(
        bars,
        bars[-1].as_of_knowledge,
        config=cfg,
        fixture_id="rich-dips",
    )
    dip = next(r for r in snap.rates if r.event_class == DIP_TOUCH)
    assert dip.n >= dip.n_min
    assert dip.claimed is True
    assert dip.hit_rate is not None
    assert 0.0 <= dip.hit_rate <= 1.0
    assert dip.median_fwd_return is not None


def test_memory_repository_does_not_import_quant() -> None:
    src = (ROOT / "packages" / "memory" / "src" / "mm_memory" / "base_rate_repository.py").read_text(
        encoding="utf-8"
    )
    assert "mm_quant" not in src
    assert "from mm_quant" not in src


def test_lookahead_trap_hides_later_bars() -> None:
    full = snapshot_from_fixture(PANEL, repo_root=ROOT)
    trap = snapshot_from_fixture(TRAP, repo_root=ROOT)
    cut = trap.as_of_knowledge
    assert any(e.trigger_available_at > cut for e in full.events)
    assert all(e.trigger_available_at <= cut for e in trap.events)
    assert len(trap.events) < len(full.events)


def test_language_and_non_goals() -> None:
    snap = snapshot_from_fixture(PANEL, repo_root=ROOT)
    blob = " ".join(snap.notes) + " " + snap.canonical()["footer"]
    assert "DO NOT SIZE" in blob
    assert language_violations(blob) == []
    for rate in snap.rates:
        assert language_violations(rate.definition) == []


def test_config_keeps_gates_closed() -> None:
    cfg = load_base_rate_config(ROOT)
    assert cfg.get("sizing") is False
    assert cfg.get("scan_gate") is False
    assert cfg.get("promote") is False
    assert cfg.get("llm") is False
    assert cfg.get("send") is False
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
