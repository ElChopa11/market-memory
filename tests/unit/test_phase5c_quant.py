"""Phase 5c / IMP-011 factor library: formulas, degrade-never-invent, determinism."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from mm_common.time import parse_utc
from mm_quant.card import build_quant_card, render_quant_card
from mm_quant.config import QuantConfig, load_quant_config
from mm_quant.factors import FACTOR_NAMES, FactorRegistry
from mm_quant.mathutil import realised_vol, trailing_return, zscore
from mm_quant.panel import load_panel_file
from mm_quant.regime import classify_regime
from mm_quant.sizing import fixed_fractional_budget_pct, vol_targeted_budget_pct
from mm_quant.stats import (
    bootstrap_ci,
    deflated_sharpe,
    expectancy,
    mae_mfe,
    multiple_testing_haircut,
    sample_size,
    t_stat,
    walk_forward_splits,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "phase5c"
WATERMARK = parse_utc("2026-09-18T00:05:00Z")


def _registry() -> FactorRegistry:
    return FactorRegistry(load_quant_config(ROOT))


def test_registry_names_match_catalog() -> None:
    assert FactorRegistry().names() == FACTOR_NAMES
    for name in (
        "momentum_short",
        "momentum_long",
        "realised_vol_short",
        "realised_vol_long",
        "adx",
        "zscore",
        "funding_carry",
        "basis_carry",
        "relative_strength_btc",
        "relative_strength_sector",
        "breadth",
        "correlation_matrix",
        "beta",
    ):
        assert name in FACTOR_NAMES


def test_yaml_thresholds_are_explicit() -> None:
    cfg = load_quant_config(ROOT)
    assert cfg.version == "2026-09-18"
    assert cfg.regime.version == "2026-09-18"
    assert cfg.regime.vol_low == 0.20
    assert cfg.regime.vol_high == 0.50
    assert cfg.regime.adx_trending == 25.0
    assert cfg.regime.zscore_stretched == 2.0
    assert cfg.regime.funding_crowded == 0.0003
    assert cfg.regime.min_inputs_for_tag == 2
    factors_text = (ROOT / "config/quant/factors.yaml").read_text(encoding="utf-8")
    regime_text = (ROOT / "config/quant/regime.yaml").read_text(encoding="utf-8")
    assert "vol_target" in factors_text
    assert "trending: 25.0" in regime_text


def test_hand_momentum_matches_formula() -> None:
    prices = (100.0, 101.0, 102.5, 101.5, 100.0, 99.0, 101.0, 103.0, 104.0, 106.0)
    assert trailing_return(prices, 5) == 106.0 / 100.0 - 1.0
    panel = load_panel_file(FIXTURES / "hand_panel.json")
    base = QuantConfig.defaults()
    cfg = replace(
        base,
        momentum=replace(base.momentum, crypto_short_bars=5, crypto_long_bars=8),
        realised_vol=replace(base.realised_vol, short_bars=5, long_bars=8, min_bars=5),
        zscore=replace(base.zscore, window=5),
    )
    reg = FactorRegistry(cfg)
    wm = parse_utc("2026-09-12T00:05:00Z")
    mom = reg.compute("momentum_short", "BTC", panel, wm)
    assert mom.status == "ok"
    assert mom.value == 106.0 / 100.0 - 1.0
    assert mom.provenance
    assert all(ref.as_of_knowledge for ref in mom.provenance)
    z = zscore(prices, 5)
    got = reg.compute("zscore", "BTC", panel, wm)
    assert got.status == "ok"
    assert got.value == z
    fund = reg.compute("funding_carry", "BTC", panel, wm)
    assert fund.status == "ok"
    assert fund.value == 0.0002
    assert any(ref.observation_id == "hand-BTC-funding" for ref in fund.provenance)


def test_realised_vol_formula() -> None:
    rets = (0.01, -0.02, 0.015, 0.0, 0.01)
    vol = realised_vol(rets, 5, 365.0)
    assert vol is not None
    mean = sum(rets) / 5
    var = sum((x - mean) ** 2 for x in rets) / 4
    assert abs(vol - (var**0.5) * (365.0**0.5)) < 1e-12


def test_panel_factors_ok_and_consume_hl_structure() -> None:
    panel = load_panel_file(FIXTURES / "panel.json")
    reg = _registry()
    factors = {row.name: row for row in reg.compute_all("BTC", panel, WATERMARK)}
    assert factors["momentum_short"].status == "ok"
    assert factors["momentum_long"].status == "ok"
    assert factors["realised_vol_short"].status == "ok"
    assert factors["realised_vol_long"].status == "ok"
    assert factors["adx"].status == "ok"
    assert factors["zscore"].status == "ok"
    assert factors["funding_carry"].status == "ok"
    assert factors["funding_carry"].value == 0.00012
    assert factors["basis_carry"].status == "ok"
    assert factors["basis_carry"].value == 0.0003077
    assert any(ref.observation_id == "fx-BTC-funding-0001" for ref in factors["funding_carry"].provenance)
    assert factors["relative_strength_btc"].status == "unavailable"
    eth = {row.name: row for row in reg.compute_all("ETH", panel, WATERMARK)}
    assert eth["relative_strength_btc"].status == "ok"
    nvda = {row.name: row for row in reg.compute_all("NVDA", panel, WATERMARK)}
    assert nvda["relative_strength_sector"].status == "ok"
    assert nvda["relative_strength_sector"].inputs.get("benchmark") == "SMH"
    assert nvda["beta"].status == "ok"
    assert factors["breadth"].status in {"ok", "partial"}
    assert factors["correlation_matrix"].status in {"ok", "partial"}
    matrix = factors["correlation_matrix"].payload["matrix"]
    assert matrix["BTC"]["BTC"] == 1.0
    assert matrix["NVDA"]["NVDA"] == 1.0


def test_missing_feeds_degrade_never_invent() -> None:
    panel = load_panel_file(FIXTURES / "missing_feeds.json")
    reg = _registry()
    factors = {row.name: row for row in reg.compute_all("BTC", panel, WATERMARK)}
    assert factors["funding_carry"].status == "unavailable"
    assert factors["funding_carry"].value is None
    assert factors["basis_carry"].status == "unavailable"
    assert factors["basis_carry"].value is None
    assert factors["adx"].status == "unavailable"
    assert factors["relative_strength_sector"].status == "unavailable"
    assert factors["beta"].status == "unavailable"
    assert factors["momentum_short"].status == "ok"
    assert "not invented" in factors["basis_carry"].reason or "missing" in factors["basis_carry"].reason


def test_quant_card_deterministic_hash() -> None:
    panel = load_panel_file(FIXTURES / "panel.json")
    cfg = load_quant_config(ROOT)
    first = build_quant_card("BTC", panel, WATERMARK, config=cfg)
    second = build_quant_card("BTC", panel, WATERMARK, config=cfg)
    assert first.params_hash == second.params_hash
    assert first.result_hash() == second.result_hash()
    assert first.canonical() == second.canonical()
    md = render_quant_card(first)
    assert first.params_hash in md
    assert "as_of_knowledge" in md
    assert "fx-BTC-funding-0001" in md
    assert "Research only" in md
    assert "budget_fraction_pct" in md
    assert "buy" not in md.lower()
    assert "high confidence" not in md.lower()


def test_regime_uses_yaml_thresholds() -> None:
    panel = load_panel_file(FIXTURES / "panel.json")
    cfg = load_quant_config(ROOT)
    reg = FactorRegistry(cfg)
    factors = reg.compute_all("BTC", panel, WATERMARK)
    regime = classify_regime(factors, watermark=WATERMARK, config=cfg)
    assert regime.tag != "unavailable"
    assert regime.thresholds_version == cfg.regime.version
    assert "vol_low" in regime.driving_inputs["thresholds"]
    tight = QuantConfig(
        version=cfg.version,
        momentum=cfg.momentum,
        realised_vol=cfg.realised_vol,
        zscore=cfg.zscore,
        adx=cfg.adx,
        relative_strength=cfg.relative_strength,
        breadth=cfg.breadth,
        correlation=cfg.correlation,
        beta=cfg.beta,
        sizing=cfg.sizing,
        stats=cfg.stats,
        regime=type(cfg.regime)(
            version="test-tight",
            vol_low=0.0000001,
            vol_high=0.0000002,
            adx_trending=cfg.regime.adx_trending,
            zscore_stretched=cfg.regime.zscore_stretched,
            funding_crowded=cfg.regime.funding_crowded,
            min_inputs_for_tag=cfg.regime.min_inputs_for_tag,
        ),
        crypto_assets=cfg.crypto_assets,
    )
    other = classify_regime(factors, watermark=WATERMARK, config=tight)
    assert other.tag != regime.tag or other.tag.startswith("high_vol")
    assert other.thresholds_version == "test-tight"


def test_sizing_is_budget_fraction_only() -> None:
    wm = datetime(2026, 9, 18, tzinfo=timezone.utc)
    hint = vol_targeted_budget_pct(0.20, target_vol=0.10, cap_pct=5.0, as_of_knowledge=wm)
    assert hint.status == "ok"
    assert hint.budget_fraction_pct == 5.0  # 50% uncapped, clipped to 5
    missing = vol_targeted_budget_pct(None, target_vol=0.10, cap_pct=5.0, as_of_knowledge=wm)
    assert missing.status == "unavailable"
    assert missing.budget_fraction_pct is None
    fixed = fixed_fractional_budget_pct(0.01, cap_pct=5.0, as_of_knowledge=wm)
    assert fixed.budget_fraction_pct == 1.0


def test_stats_helpers() -> None:
    rets = tuple(0.01 * ((-1) ** i) + 0.002 for i in range(40))
    n = sample_size(rets)
    assert n.n == 40 and n.status == "ok"
    t = t_stat(rets)
    assert t.status == "ok" and t.t_stat is not None and t.ci_low is not None
    boot = bootstrap_ci(rets, draws=200, seed=42)
    boot2 = bootstrap_ci(rets, draws=200, seed=42)
    assert boot.status == "ok"
    assert boot.ci_low == boot2.ci_low and boot.ci_high == boot2.ci_high
    dsr = deflated_sharpe(rets, n_trials=5, periods_per_year=252.0)
    assert dsr.status == "ok" and dsr.deflated_sharpe is not None
    dsr_one = deflated_sharpe(rets, n_trials=1, periods_per_year=252.0)
    assert dsr_one.deflated_sharpe is not None
    # More trials → stricter deflated Sharpe (lower).
    assert dsr.deflated_sharpe < dsr_one.deflated_sharpe
    assert multiple_testing_haircut(1.2, 4) == 0.6
    splits = walk_forward_splits(80, train_min=40, test_size=10, step=10, embargo=1)
    assert splits
    assert splits[0].train_end == 40
    assert splits[0].test_start == 41
    assert splits[0].test_end == 51
    mm = mae_mfe((100.0, 98.0, 105.0, 101.0))
    assert mm.status == "ok"
    assert mm.mae == 98.0 / 100.0 - 1.0
    assert mm.mfe == 105.0 / 100.0 - 1.0
    exp = expectancy((0.1, -0.05, 0.2, -0.1))
    assert exp.status == "ok" and exp.expectancy is not None


def test_live_flag_and_no_execution_attr() -> None:
    import mm_quant

    assert mm_quant.LIVE_TRADING_ENABLED is False
    assert mm_quant.__phase__ == 5
    assert not hasattr(mm_quant, "sign")
    assert not hasattr(mm_quant, "submit_order")
