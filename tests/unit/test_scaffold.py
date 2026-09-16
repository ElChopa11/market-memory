"""Scaffold tests — layout, hard-gates, lifecycle DoD."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TEMPLATES = [
    "intent.md",
    "thesis.md",
    "research-plan.md",
    "skeptic-review.md",
    "unicorn-card.md",
    "paper-trade.md",
    "promotion-decision.md",
    "post-mortem.md",
    "evidence-links.md",
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
    ):
        assert (ROOT / rel).exists(), rel


def test_live_trading_hard_gated() -> None:
    live = yaml.safe_load((ROOT / "config/risk/environments/live.yaml").read_text())
    defaults = yaml.safe_load((ROOT / "config/risk/defaults.yaml").read_text())
    assert live["live_trading_enabled"] is False
    assert defaults["live_trading_enabled"] is False
    assert live["risk_budget_usd"] == 0


def test_instruments_are_btc_eth_perps() -> None:
    data = yaml.safe_load((ROOT / "config/instruments/perps.yaml").read_text())
    symbols = {row["symbol"] for row in data["instruments"]}
    assert symbols == {"BTC", "ETH"}
    assert data["kind"] == "perpetual"
    assert data["venue"] == "hyperliquid"


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
