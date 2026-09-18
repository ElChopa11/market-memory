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
RULE_UNTRADEABLE = "untradeable_at_size"
RULE_EVENT_RISK = "event_risk"
RULE_CLUSTER = "cluster_concentration"
RULE_DRAWDOWN_DRY = "drawdown_dry_review"
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


def _allow(config: RiskConfig, *reasons: str, rule_id: str = RULE_ALLOW, haircut_pct: float | None = None) -> RiskResult:
    return RiskResult(
        decision=RiskDecision.ALLOW.value,
        rule_id=rule_id,
        config_version=config.config_version,
        reasons=reasons or ("all configured gates passed",),
        terminal=False,
        live_trading_enabled=bool(config.live_trading_enabled),
        haircut_pct=haircut_pct,
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
    if intent.cluster_exposure_pct is not None:
        from mm_risk.clusters import load_cluster_config

        clusters = load_cluster_config(repo_root)
        cap = float(clusters.max_cluster_pct)
        if float(intent.cluster_exposure_pct) > cap:
            return _block(
                clusters.rule_id or RULE_CLUSTER,
                cfg,
                f"cluster {intent.cluster_id or '?'} exposure {intent.cluster_exposure_pct} > {cap} (trailing-corr config)",
            )
    if intent.rolling_drawdown_pct is not None:
        from mm_risk.drawdown import evaluate_drawdown, load_drawdown_config

        dd_cfg = load_drawdown_config(repo_root)
        decision = evaluate_drawdown(
            rolling_dd_pct=intent.rolling_drawdown_pct,
            n_points=int(intent.drawdown_n),
            config=dd_cfg,
        )
        if decision.action == "dry_review":
            return _block(decision.rule_id or RULE_DRAWDOWN_DRY, cfg, *decision.notes)
        if decision.action == "sleeve_half":
            return _allow(
                cfg,
                *decision.notes,
                rule_id=decision.rule_id or "drawdown_sleeve_half",
                haircut_pct=50.0,
            )
    verdict = (intent.liquidity_verdict or "").strip().upper()
    if verdict == "UNTRADEABLE_AT_SIZE" and cfg.untradeable_action == "block":
        return _block(
            cfg.untradeable_rule_id or RULE_UNTRADEABLE,
            cfg,
            "liquidity verdict UNTRADEABLE_AT_SIZE auto-blocks from versioned YAML",
        )
    if intent.event_risk and cfg.event_risk_action == "haircut":
        return _allow(
            cfg,
            f"EVENT_RISK size haircut {cfg.event_risk_haircut_pct:g}% under {cfg.event_risk_rule_id}",
            rule_id=cfg.event_risk_rule_id or RULE_EVENT_RISK,
            haircut_pct=float(cfg.event_risk_haircut_pct),
        )
    return _allow(
        cfg,
        f"allow {instrument} under {cfg.environment} config {cfg.config_version}",
    )
