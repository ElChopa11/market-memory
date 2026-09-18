"""Load versioned flow / liquidity YAML. Thresholds live in config, not model weights."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_LIQUIDITY_REL = Path("config/flow/liquidity.yaml")


@dataclass(frozen=True)
class SlippageSpec:
    budget_bps: float = 10.0
    thin_bps: float = 5.0
    impact_coeff: float = 1.0
    adv_k: float = 0.1


@dataclass(frozen=True)
class FlowConfig:
    version: str = "2026-09-18"
    kind: str = "flow_liquidity_thresholds"
    desk: str = "Flow / Liquidity Desk"
    clip_sizes_usd: tuple[float, ...] = (10_000.0, 50_000.0, 100_000.0, 250_000.0)
    slippage: SlippageSpec = field(default_factory=SlippageSpec)
    thin_max_clip_usd: float = 50_000.0
    funding_z_window: int = 20
    oi_lookback: int = 1
    adv_window: int = 20
    spread_proxy_levels: int = 5

    @classmethod
    def defaults(cls) -> FlowConfig:
        return cls()


def _req_float(data: dict[str, Any], key: str) -> float:
    if key not in data:
        raise ValueError(f"missing flow threshold {key!r}")
    return float(data[key])


def _req_int(data: dict[str, Any], key: str) -> int:
    if key not in data:
        raise ValueError(f"missing flow int {key!r}")
    return int(data[key])


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def load_flow_config(root: Path | None = None) -> FlowConfig:
    """Load `config/flow/liquidity.yaml`. Missing file raises — never invent thresholds."""
    base = root if root is not None else Path.cwd()
    path = base / DEFAULT_LIQUIDITY_REL
    raw = load_yaml(path)
    slip = raw.get("slippage") if isinstance(raw.get("slippage"), dict) else {}
    clips = raw.get("clip_sizes_usd") or []
    if not isinstance(clips, list) or not clips:
        raise ValueError("clip_sizes_usd must be a non-empty list")
    return FlowConfig(
        version=str(raw.get("version") or "unknown"),
        kind=str(raw.get("kind") or "flow_liquidity_thresholds"),
        desk=str(raw.get("desk") or "Flow / Liquidity Desk"),
        clip_sizes_usd=tuple(float(x) for x in clips),
        slippage=SlippageSpec(
            budget_bps=_req_float(slip, "budget_bps"),
            thin_bps=_req_float(slip, "thin_bps"),
            impact_coeff=_req_float(slip, "impact_coeff"),
            adv_k=_req_float(slip, "adv_k"),
        ),
        thin_max_clip_usd=_req_float(raw, "thin_max_clip_usd"),
        funding_z_window=_req_int(raw, "funding_z_window"),
        oi_lookback=_req_int(raw, "oi_lookback"),
        adv_window=_req_int(raw, "adv_window"),
        spread_proxy_levels=_req_int(raw, "spread_proxy_levels"),
    )
