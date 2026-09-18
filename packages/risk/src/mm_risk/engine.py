"""Deterministic allow/block engine. Code + versioned config only. No LLM."""

from __future__ import annotations

from pathlib import Path

from mm_common.enums import RiskDecision
from mm_risk.config import RiskConfig, blank_or_placeholder, halt_flag_present, load_risk_config
from mm_risk.models import RiskIntent, RiskResult

RULE_LLM_FORBIDDEN = "llm_at_order_time_forbidden"
RULE_LIVE_GATED = "live_trading_hard_gated"
RULE_HALT = "halt_active"
RULE_NOT_ALLOWLISTED = "instrument_not_allowlisted"
RULE_MISSING_INVALIDATION = "missing_invalidation"
RULE_MISSING_MAX_LOSS = "missing_max_loss"
RULE_LEVERAGE = "leverage_exceeds_max"
RULE_ALLOW = "allow_config"


def _block(rule_id: str, config: RiskConfig, *reasons: str) -> RiskResult:
    return RiskResult(
        decision=RiskDecision.BLOCK.value,
        rule_id=rule_id,
        config_version=config.config_version,
        reasons=reasons,
        terminal=True,
        live_trading_enabled=bool(config.live_trading_enabled),
    )


def _allow(config: RiskConfig, *reasons: str) -> RiskResult:
    return RiskResult(
        decision=RiskDecision.ALLOW.value,
        rule_id=RULE_ALLOW,
        config_version=config.config_version,
        reasons=reasons or ("all configured gates passed",),
        terminal=False,
        live_trading_enabled=bool(config.live_trading_enabled),
    )


def evaluate(
    intent: RiskIntent,
    *,
    repo_root: Path,
    config: RiskConfig | None = None,
    halt: bool | None = None,
) -> RiskResult:
    """Allow or BLOCK from versioned YAML. Never calls an LLM. Never submits orders."""
    cfg = config or load_risk_config(repo_root, environment=intent.environment)
    if cfg.llm_at_order_time:
        return _block(RULE_LLM_FORBIDDEN, cfg, "config sets llm_at_order_time; forbidden")
    env = (intent.environment or cfg.environment).strip().lower()
    if env == "live" or cfg.live_trading_enabled:
        return _block(
            RULE_LIVE_GATED,
            cfg,
            "live trading is hard-gated (live_trading_enabled remains false; live path is later)",
        )
    if halt is None:
        halt_on = bool(intent.halt) or halt_flag_present(repo_root, cfg.kill_switch_path)
    else:
        halt_on = bool(halt)
    if halt_on:
        return _block(RULE_HALT, cfg, f"halt flag active ({cfg.kill_switch_path})")
    instrument = intent.instrument.strip().upper()
    if instrument not in cfg.instruments_allowlist:
        return _block(
            RULE_NOT_ALLOWLISTED,
            cfg,
            f"{instrument} is not on the versioned allowlist {list(cfg.instruments_allowlist)}",
        )
    if cfg.require_invalidation and blank_or_placeholder(intent.invalidation):
        return _block(RULE_MISSING_INVALIDATION, cfg, "invalidation is required and missing")
    if cfg.require_max_loss and blank_or_placeholder(intent.max_loss):
        return _block(RULE_MISSING_MAX_LOSS, cfg, "max_loss is required and missing")
    if float(intent.leverage) > float(cfg.max_leverage):
        return _block(
            RULE_LEVERAGE,
            cfg,
            f"leverage {intent.leverage} exceeds max_leverage {cfg.max_leverage}",
        )
    return _allow(
        cfg,
        f"allow {instrument} under {cfg.environment} config {cfg.config_version}",
    )
