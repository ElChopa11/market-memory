"""Load versioned macro regime + EVENT_RISK YAML. Thresholds live in config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_REGIME_REL = Path("config/macro/regimes.yaml")


@dataclass(frozen=True)
class VixSpec:
    metric: str = "VIX"
    risk_on_below: float = 18.0
    risk_off_above: float = 25.0


@dataclass(frozen=True)
class DxySpec:
    metric: str = "DXY"
    weak_below: float = 100.0
    strong_above: float = 106.0


@dataclass(frozen=True)
class EventRiskSpec:
    window_minutes: int = 30
    high_importance: tuple[str, ...] = ("high",)
    rule_id: str = "event_risk"
    size_haircut_pct: float = 50.0
    cb_name_tokens: tuple[str, ...] = ("FOMC", "CPI", "NFP", "PCE", "GDP")


@dataclass(frozen=True)
class MacroConfig:
    version: str = "2026-09-18"
    kind: str = "macro_regime_thresholds"
    desk: str = "Macro & Cross-Asset Desk"
    min_inputs_for_tag: int = 2
    driving: tuple[str, ...] = ("VIX", "DXY")
    vix: VixSpec = field(default_factory=VixSpec)
    dxy: DxySpec = field(default_factory=DxySpec)
    fred_series: dict[str, str] = field(default_factory=dict)
    event_risk: EventRiskSpec = field(default_factory=EventRiskSpec)
    curve_metric: str = "T10Y2Y"
    credit_metric: str = "HY_OAS"
    commodities_metric: str = "WTI"
    inverted_below: float = 0.0
    credit_stressed_above: float = 500.0

    @classmethod
    def defaults(cls) -> MacroConfig:
        return cls()


def _req_float(data: dict[str, Any], key: str) -> float:
    if key not in data:
        raise ValueError(f"missing macro threshold {key!r}")
    return float(data[key])


def _req_int(data: dict[str, Any], key: str) -> int:
    if key not in data:
        raise ValueError(f"missing macro int {key!r}")
    return int(data[key])


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def load_macro_config(root: Path | None = None) -> MacroConfig:
    """Load `config/macro/regimes.yaml`. Missing file raises — never invent thresholds."""
    base = root if root is not None else Path.cwd()
    raw = load_yaml(base / DEFAULT_REGIME_REL)
    vix = raw.get("vix") if isinstance(raw.get("vix"), dict) else {}
    dxy = raw.get("dxy") if isinstance(raw.get("dxy"), dict) else {}
    curve = raw.get("curve") if isinstance(raw.get("curve"), dict) else {}
    credit = raw.get("credit") if isinstance(raw.get("credit"), dict) else {}
    comm = raw.get("commodities") if isinstance(raw.get("commodities"), dict) else {}
    event = raw.get("event_risk") if isinstance(raw.get("event_risk"), dict) else {}
    driving = tuple(str(x).upper() for x in (raw.get("driving") or ["VIX", "DXY"]))
    fred = {str(k).upper(): str(v) for k, v in (raw.get("fred_series") or {}).items()}
    high = tuple(str(x).lower() for x in (event.get("high_importance") or ["high"]))
    tokens = tuple(str(x) for x in (event.get("cb_name_tokens") or []))
    return MacroConfig(
        version=str(raw.get("version") or "unknown"),
        kind=str(raw.get("kind") or "macro_regime_thresholds"),
        desk=str(raw.get("desk") or "Macro & Cross-Asset Desk"),
        min_inputs_for_tag=_req_int(raw, "min_inputs_for_tag"),
        driving=driving,
        vix=VixSpec(
            metric=str(vix.get("metric") or "VIX"),
            risk_on_below=_req_float(vix, "risk_on_below"),
            risk_off_above=_req_float(vix, "risk_off_above"),
        ),
        dxy=DxySpec(
            metric=str(dxy.get("metric") or "DXY"),
            weak_below=_req_float(dxy, "weak_below"),
            strong_above=_req_float(dxy, "strong_above"),
        ),
        fred_series=fred,
        event_risk=EventRiskSpec(
            window_minutes=int(event.get("window_minutes") or 30),
            high_importance=high,
            rule_id=str(event.get("rule_id") or "event_risk"),
            size_haircut_pct=float(event.get("size_haircut_pct") or 50),
            cb_name_tokens=tokens,
        ),
        curve_metric=str(curve.get("metric") or "T10Y2Y"),
        credit_metric=str(credit.get("metric") or "HY_OAS"),
        commodities_metric=str(comm.get("metric") or "WTI"),
        inverted_below=float(curve.get("inverted_below") or 0.0),
        credit_stressed_above=float(credit.get("stressed_above") or 500.0),
    )
