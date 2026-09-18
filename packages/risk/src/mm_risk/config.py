"""Load versioned risk YAML. Never prints secrets. live.yaml is Principal-owned."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mm_common.hashing import canonical_json, sha256_hex

_PLACEHOLDERS = frozenset({"", "-", "n/a", "na", "none", "null", "tbd", "todo", "?", "unknown"})


@dataclass(frozen=True)
class RiskConfig:
    schema_version: int
    environment: str
    live_trading_enabled: bool
    risk_budget_usd: float
    per_thesis_max_loss_bps: int
    max_leverage: float
    daily_loss_limit_bps: int
    max_concentration_pct: float
    max_open_theses: int | None
    instruments_allowlist: tuple[str, ...]
    require_invalidation: bool
    require_max_loss: bool
    kill_switch_path: str
    llm_at_order_time: bool
    untradeable_action: str
    untradeable_rule_id: str
    event_risk_action: str
    event_risk_haircut_pct: float
    event_risk_rule_id: str
    raw: dict[str, Any]
    source: str

    @property
    def config_version(self) -> str:
        digest = sha256_hex(canonical_json(self.raw))[:16]
        return f"{self.environment}:schema{self.schema_version}:{digest}"


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a YAML mapping")
    return data


def load_risk_config(repo_root: Path, *, environment: str = "paper") -> RiskConfig:
    root = Path(repo_root)
    env = environment.strip().lower()
    if env not in {"paper", "sim", "live"}:
        raise ValueError(f"unknown risk environment {environment!r}")
    defaults = load_yaml(root / "config" / "risk" / "defaults.yaml")
    overlay = load_yaml(root / "config" / "risk" / "environments" / f"{env}.yaml")
    raw = _merge(defaults, overlay)
    allow = tuple(str(item).upper() for item in (raw.get("instruments_allowlist") or ()))
    max_open = raw.get("max_open_theses")
    liq = raw.get("liquidity") if isinstance(raw.get("liquidity"), dict) else {}
    untrade = liq.get("untradeable_at_size") if isinstance(liq.get("untradeable_at_size"), dict) else {}
    event = raw.get("event_risk") if isinstance(raw.get("event_risk"), dict) else {}
    return RiskConfig(
        schema_version=int(raw.get("schema_version") or 1),
        environment=str(raw.get("environment") or env),
        live_trading_enabled=bool(raw.get("live_trading_enabled")),
        risk_budget_usd=float(raw.get("risk_budget_usd") or 0),
        per_thesis_max_loss_bps=int(raw.get("per_thesis_max_loss_bps") or 0),
        max_leverage=float(raw.get("max_leverage") or 1.0),
        daily_loss_limit_bps=int(raw.get("daily_loss_limit_bps") or 0),
        max_concentration_pct=float(raw.get("max_concentration_pct") or 0),
        max_open_theses=None if max_open is None else int(max_open),
        instruments_allowlist=allow,
        require_invalidation=bool(raw.get("require_invalidation", True)),
        require_max_loss=bool(raw.get("require_max_loss", True)),
        kill_switch_path=str(raw.get("kill_switch_path") or "config/halt.flag"),
        llm_at_order_time=bool(raw.get("llm_at_order_time")),
        untradeable_action=str(untrade.get("action") or "block").lower(),
        untradeable_rule_id=str(untrade.get("rule_id") or "untradeable_at_size"),
        event_risk_action=str(event.get("action") or "haircut").lower(),
        event_risk_haircut_pct=float(event.get("haircut_pct") or 50),
        event_risk_rule_id=str(event.get("rule_id") or "event_risk"),
        raw=raw,
        source=f"config/risk/environments/{env}.yaml",
    )


def halt_flag_present(repo_root: Path, kill_switch_path: str) -> bool:
    return (Path(repo_root) / kill_switch_path).is_file()


def blank_or_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in _PLACEHOLDERS
