"""Phase 6c drawdown ladder, cluster netting, invalidation, post-mortem."""

from __future__ import annotations

from pathlib import Path

from mm_desks.invalidation import daily_print_on_multiday, evaluate_invalidation, flow_single_print
from mm_desks.models import ThesisSnapshot
from mm_desks.postmortem import PostMortemRequired, assert_can_publish_new_idea, template_exists
from mm_risk.clusters import load_cluster_config
from mm_risk.drawdown import evaluate_drawdown, load_drawdown_config
from mm_risk.engine import evaluate
from mm_risk.models import RiskIntent

ROOT = Path(__file__).resolve().parents[2]


def test_n1_drawdown_changes_nothing() -> None:
    cfg = load_drawdown_config(ROOT)
    d = evaluate_drawdown(rolling_dd_pct=20.0, n_points=1, config=cfg)
    assert d.action == "none"
    assert d.size_mult == 1.0


def test_drawdown_sleeve_half_and_dry() -> None:
    cfg = load_drawdown_config(ROOT)
    half = evaluate_drawdown(rolling_dd_pct=8.0, n_points=10, config=cfg)
    assert half.action == "sleeve_half"
    assert half.size_mult == 0.5
    dry = evaluate_drawdown(rolling_dd_pct=15.0, n_points=10, config=cfg)
    assert dry.action == "dry_review"
    blocked = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="x",
            max_loss="2%",
            environment="paper",
            rolling_drawdown_pct=20.0,
            drawdown_n=10,
        ),
        repo_root=ROOT,
    )
    assert blocked.decision == "block"
    assert blocked.rule_id == "drawdown_dry_review"


def test_cluster_config_is_versioned_not_hand_named_in_engine() -> None:
    cfg = load_cluster_config(ROOT)
    assert "crypto-beta" in cfg.clusters
    assert "semis" in cfg.clusters
    text = (ROOT / "packages" / "risk" / "src" / "mm_risk" / "engine.py").read_text(encoding="utf-8")
    assert "crypto-beta" not in text
    over = evaluate(
        RiskIntent(
            instrument="BTC",
            invalidation="x",
            max_loss="2%",
            environment="paper",
            cluster_id="crypto-beta",
            cluster_exposure_pct=80.0,
        ),
        repo_root=ROOT,
    )
    assert over.decision == "block"
    assert over.rule_id == "cluster_concentration"


def test_daily_print_and_flow_single_print_rejected() -> None:
    assert daily_print_on_multiday(horizon_days=5, invalidation_kind="daily_print") is True
    assert flow_single_print("flow_single_print") is True
    thesis = ThesisSnapshot(
        slug="X",
        status="in_skeptic",
        author="Crypto Desk",
        instrument="BTC",
        invalidation="close below yesterday",
        max_loss="2%",
        horizon="5d",
        reviewer="Independent Skeptic",
        invalidation_kind="daily_print",
        invalidation_lookback_days=1,
    )
    items = evaluate_invalidation(thesis)
    assert any(not row["ok"] and row["code"] == "daily_print_multiday" for row in items)
    assert any(not row["ok"] and row["code"] == "invalidation_lookback" for row in items)


def test_post_mortem_template_exists_and_blocks() -> None:
    assert template_exists(ROOT)
    try:
        assert_can_publish_new_idea(
            instrument="BTC",
            closed_slugs=("THESIS-BTC-CLOSED",),
            research_root=ROOT / "research",
            repo_root=ROOT,
        )
        raise AssertionError("missing post-mortem must block")
    except PostMortemRequired:
        pass
