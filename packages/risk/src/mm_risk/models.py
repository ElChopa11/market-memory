"""Deterministic allow/block from versioned risk config. No LLM. No orders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RiskIntent:
    """Intent-level risk request. Not an order."""

    instrument: str
    invalidation: str
    max_loss: str
    leverage: float = 1.0
    environment: str = "paper"
    thesis_slug: str | None = None
    author: str | None = None
    requested_target: str | None = None
    halt: bool = False
    liquidity_verdict: str | None = None
    event_risk: bool = False

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument.upper(),
            "invalidation": self.invalidation,
            "max_loss": self.max_loss,
            "leverage": self.leverage,
            "environment": self.environment,
            "thesis_slug": self.thesis_slug,
            "author": self.author,
            "requested_target": self.requested_target,
            "halt": self.halt,
            "liquidity_verdict": self.liquidity_verdict,
            "event_risk": self.event_risk,
        }


@dataclass(frozen=True)
class RiskResult:
    decision: str
    rule_id: str
    config_version: str
    reasons: tuple[str, ...]
    terminal: bool = False
    live_trading_enabled: bool = False
    haircut_pct: float | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "config_version": self.config_version,
            "reasons": list(self.reasons),
            "terminal": self.terminal,
            "live_trading_enabled": self.live_trading_enabled,
            "haircut_pct": self.haircut_pct,
        }
