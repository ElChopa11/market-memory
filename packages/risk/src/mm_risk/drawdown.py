"""Drawdown ladder from versioned YAML. n=1 changes nothing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DRAWDOWN_REL = Path("config/risk/drawdown.yaml")


@dataclass(frozen=True)
class DrawdownConfig:
    version: str
    sleeve_half_pct: float
    dry_review_pct: float
    n_equals_1_noop: bool
    rule_id_half: str
    rule_id_dry: str


@dataclass(frozen=True)
class DrawdownDecision:
    action: str
    rule_id: str | None
    size_mult: float
    notes: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "rule_id": self.rule_id,
            "size_mult": self.size_mult,
            "notes": list(self.notes),
        }


def load_drawdown_config(repo_root: Path) -> DrawdownConfig:
    path = Path(repo_root) / DRAWDOWN_REL
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if not isinstance(data, dict):
        data = {}
    return DrawdownConfig(
        version=str(data.get("version") or "imp-016.1"),
        sleeve_half_pct=float(data.get("sleeve_half_pct") or 8),
        dry_review_pct=float(data.get("dry_review_pct") or 15),
        n_equals_1_noop=bool(data.get("n_equals_1_noop", True)),
        rule_id_half=str(data.get("rule_id_half") or "drawdown_sleeve_half"),
        rule_id_dry=str(data.get("rule_id_dry") or "drawdown_dry_review"),
    )


def evaluate_drawdown(
    *,
    rolling_dd_pct: float | None,
    n_points: int,
    config: DrawdownConfig,
) -> DrawdownDecision:
    if rolling_dd_pct is None:
        return DrawdownDecision("none", None, 1.0, ("no rolling drawdown sample",))
    if config.n_equals_1_noop and n_points <= 1:
        return DrawdownDecision("none", None, 1.0, ("n=1 changes nothing",))
    dd = abs(float(rolling_dd_pct))
    if dd >= float(config.dry_review_pct):
        return DrawdownDecision(
            "dry_review",
            config.rule_id_dry,
            0.0,
            (f"rolling -{dd:g}% >= -{config.dry_review_pct:g}% dry+review",),
        )
    if dd >= float(config.sleeve_half_pct):
        return DrawdownDecision(
            "sleeve_half",
            config.rule_id_half,
            0.5,
            (f"rolling -{dd:g}% >= -{config.sleeve_half_pct:g}% sleeve halves",),
        )
    return DrawdownDecision("none", None, 1.0, ("drawdown ladder not triggered",))
