"""Scaffold tests — layout, hard-gates, lifecycle DoD."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TEMPLATES = [
    "intent.md",
    "thesis.md",
    "crypto-thesis-card.md",
    "equities-thesis-card.md",
    "research-plan.md",
    "skeptic-review.md",
    "unicorn-card.md",
    "quant-card.md",
    "quant-factor-card.md",
    "quant-review-board.md",
    "post-ipo-reclaim-screen.md",
    "paper-trade.md",
    "promotion-decision.md",
    "post-mortem.md",
    "evidence-links.md",
    "output-contract.md",
]

REQUIRED_PACKAGES = [
    "common",
    "memory",
    "ingest",
    "provenance",
    "research_kit",
    "backtest",
    "risk",
    "paper",
    "execution",
    "briefing",
    "unicorn",
    "desks",
    "quant",
    "flow",
    "macro",
    "delivery",
    "listings",
]


def test_templates_present() -> None:
    for name in REQUIRED_TEMPLATES:
        assert (ROOT / "templates" / name).is_file(), name


def test_package_stubs_present() -> None:
    for name in REQUIRED_PACKAGES:
        pkg = ROOT / "packages" / name
        assert (pkg / "README.md").is_file(), name
        assert (pkg / "pyproject.toml").is_file(), name


def test_core_docs_present() -> None:
    for rel in (
        "AGENTS.md",
        "ADR/0001-v1-monorepo.md",
        "docs/founding-brief.md",
        "docs/security-model.md",
        "docs/research-lifecycle.md",
        "docs/runbooks/ingest.md",
        "docs/runbooks/research-workspace.md",
        "docs/runbooks/market-pulse.md",
        "docs/runbooks/backtest.md",
        "docs/runbooks/paper-trade.md",
        "config/schedules/market-pulse.yaml",
        "config/briefing/alerts.yaml",
        "docker-compose.yml",
        "scripts/check-lifecycle.sh",
        "config/ingest.yaml",
        "config/universe.yaml",
        "config/quant_review_universe.yaml",
        "config/instruments/perps.yaml",
        "ops/improvement-queue.md",
        "ops/plans/IMP-001-quant-review-board.md",
        "ops/plans/IMP-005-active-call-language-debt.md",
        "ops/plans/IMP-006-post-ipo-reclaim-screen.md",
        "ops/plans/IMP-007-thesis-card-templates.md",
        "ops/plans/IMP-008-quant-locked-research-priority-pass.md",
        "ops/plans/IMP-009-phase5a-desk-boundaries.md",
        "ops/plans/IMP-010-phase5b-polygon-hl-structure.md",
        "ops/plans/IMP-011-phase5c-quant-factors.md",
        "ops/plans/IMP-012-phase5d-desk-runners.md",
        "ops/plans/IMP-013-phase5e-telegram.md",
        "ops/plans/IMP-014-phase6a-pg-notify-mesh.md",
        "ops/plans/IMP-015-phase6b-flow-macro-regime.md",
        "ops/plans/IMP-016-phase6c-telegram-fanout.md",
        "ops/plans/IMP-020-phase6c4-watchlist.md",
        "ops/plans/IMP-017-phase6d-listings-ipo.md",
        "ADR/0004-desk-mesh-pg-notify.md",
        "ADR/0005-flow-macro-regime.md",
        "ADR/0009-phase6c4-watchlist.md",
        "ADR/0011-phase6d-listings.md",
        "config/desks/cadence.yaml",
        "config/flow/liquidity.yaml",
        "config/macro/regimes.yaml",
        "config/quant/factors.yaml",
        "config/quant/regime.yaml",
        "docs/runbooks/quant-desk.md",
        "ADR/0002-desk-delivery-architecture.md",
        "ADR/0003-telegram-delivery.md",
        "config/quant_review_locked_universe.yaml",
        "config/equities/post_ipo_reclaim.yaml",
        "docs/runbooks/post-ipo-reclaim.md",
        "docs/runbooks/thesis-cards.md",
        "docs/runbooks/desks.md",
        "docs/runbooks/listings.md",
        "docs/runbooks/base-rates.md",
        "ops/plans/IMP-039-candidate-strategy-intake.md",
        "ops/plans/IMP-040-phase1-unconditional-base-rates.md",
        "ops/plans/IMP-041-desk-knowledge-base.md",
        "ops/plans/IMP-042-scheduler-heartbeat.md",
        "docs/runbooks/scheduler.md",
        "ADR/0018-schedule-heartbeat.md",
        "config/schedules/routines.yaml",
        "ADR/0016-edgar-adapter.md",
        "ADR/0017-unconditional-base-rates.md",
        "config/quant/base_rates.yaml",
        "docs/runbooks/telegram.md",
        "docs/runbooks/flow-desk.md",
        "docs/runbooks/macro-desk.md",
        "docs/runbooks/polygon-hl-structure.md",
    ):
        assert (ROOT / rel).exists(), rel


def test_live_trading_hard_gated() -> None:
    live = yaml.safe_load((ROOT / "config/risk/environments/live.yaml").read_text())
    defaults = yaml.safe_load((ROOT / "config/risk/defaults.yaml").read_text())
    assert live["live_trading_enabled"] is False
    assert defaults["live_trading_enabled"] is False
    assert live["risk_budget_usd"] == 0


def test_controlled_universe_is_locked_2026_09_17() -> None:
    universe = yaml.safe_load((ROOT / "config/universe.yaml").read_text())
    assert universe["version"] == "2026-09-17"
    assert universe["status"] == "locked"
    assert universe["crypto_perps"] == ["BTC", "ETH", "UNI", "AAVE"]
    assert universe["equities"] == ["NVDA", "AVGO", "SMH", "MSFT", "META", "JPM", "XLF", "XOM"]
    assert universe["in_universe"]["crypto_perps"] == ["BTC"]
    assert universe["in_universe"]["equities"] == ["NVDA", "AVGO", "MSFT", "META", "JPM", "XOM"]
    assert universe["watch_only"]["crypto_perps"] == ["ETH", "UNI", "AAVE"]
    assert universe["watch_only"]["equities"] == ["SMH", "XLF"]
    assert universe["deferred_must_cut"]["crypto"] == ["HYPE", "SOL", "XRP", "ARB", "NEAR", "LINK"]
    assert universe["deferred_must_cut"]["equities"] == ["GLD", "LLY"]
    notes = "\n".join(universe.get("notes") or [])
    assert "Intent-level watchlist only" in notes
    assert "not all survivors are equal priority" in notes
    assert "UNIVERSE-20260917-shortlist.md" in notes
    assert "UNIVERSE-20260917-skeptic-review.md" in notes
    assert "UNIVERSE-20260917-call-cards.md" in notes
    assert "PR #13" in notes
    assert "UNIVERSE-20260917-call-cards-skeptic.md" in notes
    assert "PR #14" in notes
    assert "EXPECTATIONS-20260917-methodology-scorecard.md" in notes
    assert "PR #22" in notes
    assert "EXPECTATIONS-20260917-fail-patch-changelog.md" in notes
    assert "PR #23" in notes
    assert "BTC-beta watch" in notes
    assert "monitor ≪ JPM" in notes
    membership = set(universe["crypto_perps"]) | set(universe["equities"])
    in_universe = set(universe["in_universe"]["crypto_perps"]) | set(universe["in_universe"]["equities"])
    watch_only = set(universe["watch_only"]["crypto_perps"]) | set(universe["watch_only"]["equities"])
    deferred = set(universe["deferred_must_cut"]["crypto"]) | set(universe["deferred_must_cut"]["equities"])
    assert in_universe.isdisjoint(watch_only)
    assert in_universe | watch_only == membership
    assert set(universe["in_universe"]["crypto_perps"]) | set(universe["watch_only"]["crypto_perps"]) == set(
        universe["crypto_perps"]
    )
    assert set(universe["in_universe"]["equities"]) | set(universe["watch_only"]["equities"]) == set(
        universe["equities"]
    )
    assert not (membership & deferred)
    assert not (in_universe & deferred)
    assert not (watch_only & deferred)


def test_hl_perps_match_locked_universe() -> None:
    universe = yaml.safe_load((ROOT / "config/universe.yaml").read_text())
    data = yaml.safe_load((ROOT / "config/instruments/perps.yaml").read_text())
    enabled = [row["symbol"] for row in data["instruments"] if row.get("enabled", True)]
    assert enabled == universe["crypto_perps"]
    assert data["kind"] == "perpetual"
    assert data["venue"] == "hyperliquid"
    # Watch-only crypto still ingest; demotion is thesis-priority membership, not ingest membership.
    assert set(universe["watch_only"]["crypto_perps"]).issubset(set(enabled))
    equity_names = set(universe["equities"]) | set(universe["deferred_must_cut"]["equities"])
    assert not (set(enabled) & equity_names), "equities are briefing/future-feed watchlist, not HL ingest"
    deferred_crypto = set(universe["deferred_must_cut"]["crypto"])
    assert not (set(enabled) & deferred_crypto), "Skeptic must-cuts must stay out of HL ingest"


def test_compose_defines_postgres_and_minio() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    assert "postgres:16" in compose
    assert "quay.io/minio/minio" in compose
    assert "quay.io/minio/mc" in compose
    data = yaml.safe_load(compose)
    assert "postgres" in data["services"]
    assert "minio" in data["services"]


def test_gitignore_excludes_env_and_halt() -> None:
    text = (ROOT / ".gitignore").read_text()
    assert ".env" in text
    assert "config/halt.flag" in text
    assert "!.env.example" in text


def test_agents_research_has_no_trading_credentials() -> None:
    text = (ROOT / "AGENTS.md").read_text()
    assert "Research cannot access trading credentials" in text
