"""Quant-owned trade math (Phase 6c / IMP-016). Computed once; artifacts inherit.

Artifacts must not recompute R. prior(judgement) is excluded from expectancy
and sizing. Not an order. Leverage is a ceiling only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from mm_common.hashing import canonical_json, normalize_numeric, sha256_hex

ENGINE_VERSION = "imp-016.1"
KIND_BASE_RATE = "base_rate"
KIND_PRIOR = "prior"
KIND_MODEL = "model"
P_KINDS = (KIND_BASE_RATE, KIND_PRIOR, KIND_MODEL)
DEFAULT_TRADE_MATH_REL = Path("config/quant/trade_math.yaml")


@dataclass(frozen=True)
class ProbabilityProvenance:
    """Every p carries provenance. prior(judgement) is never used for expectancy/sizing."""

    kind: str
    value: float
    n: int | None = None
    window: str | None = None
    name: str | None = None
    version: str | None = None
    judgement: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in P_KINDS:
            raise ValueError(f"unknown p provenance kind {self.kind!r}")

    def label(self) -> str:
        if self.kind == KIND_BASE_RATE:
            return f"base_rate(n={self.n}, window={self.window})"
        if self.kind == KIND_PRIOR:
            return "prior(judgement)"
        return f"model({self.name}, {self.version})"

    def usable_for_expectancy(self) -> bool:
        return self.kind != KIND_PRIOR

    def canonical(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": normalize_numeric(self.value),
            "n": self.n,
            "window": self.window,
            "name": self.name,
            "version": self.version,
            "judgement": self.judgement,
            "label": self.label(),
        }


@dataclass(frozen=True)
class CostModel:
    taker_fee: float
    est_slippage: float
    funding_rate: float
    expected_hold: float
    clip: float

    @property
    def total(self) -> float:
        return (self.taker_fee * 2.0) + self.est_slippage + (self.funding_rate * self.expected_hold)

    def canonical(self) -> dict[str, Any]:
        return {
            "taker_fee": normalize_numeric(self.taker_fee),
            "est_slippage": normalize_numeric(self.est_slippage),
            "funding_rate": normalize_numeric(self.funding_rate),
            "expected_hold": normalize_numeric(self.expected_hold),
            "clip": normalize_numeric(self.clip),
            "total": normalize_numeric(self.total),
            "formula": "taker_fee*2 + est_slippage(clip) + funding_rate * expected_hold",
        }


@dataclass(frozen=True)
class TradeMath:
    """Single source of R / expectancy / size. Hash this; do not recompute downstream."""

    instrument: str
    entry: float
    stop: float
    targets: tuple[float, ...]
    risk_per_unit: float | None
    r_targets: tuple[float | None, ...]
    expectancy: float | None
    size_pct: float
    cost: CostModel
    p_win: ProbabilityProvenance
    avg_r_win: float
    min_sample: int
    sample_n: int
    below_min_sample: bool
    leverage_capped: bool
    notes: tuple[str, ...] = ()
    asset_class: str = "unknown"
    engine_version: str = ENGINE_VERSION
    inputs: dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "asset_class": self.asset_class,
            "entry": normalize_numeric(self.entry),
            "stop": normalize_numeric(self.stop),
            "targets": [normalize_numeric(t) for t in self.targets],
            "risk_per_unit": None if self.risk_per_unit is None else normalize_numeric(self.risk_per_unit),
            "r_targets": [None if r is None else normalize_numeric(r) for r in self.r_targets],
            "expectancy": None if self.expectancy is None else normalize_numeric(self.expectancy),
            "size_pct": normalize_numeric(self.size_pct),
            "cost": self.cost.canonical(),
            "p_win": self.p_win.canonical(),
            "avg_r_win": normalize_numeric(self.avg_r_win),
            "min_sample": self.min_sample,
            "sample_n": self.sample_n,
            "below_min_sample": self.below_min_sample,
            "leverage_capped": self.leverage_capped,
            "notes": list(self.notes),
            "engine_version": self.engine_version,
            "inputs": self.inputs,
        }

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))


def load_trade_math_config(repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or ".")
    path = root / DEFAULT_TRADE_MATH_REL
    if not path.is_file():
        return {
            "min_sample": 20,
            "risk_budget_pct": 1.0,
            "max_leverage": 1.0,
            "cost": {"taker_fee": 0.00045, "default_clip": 10000, "default_hold_hours": 24},
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def risk_per_unit(entry: float, stop: float) -> float | None:
    gap = abs(float(entry) - float(stop))
    if gap <= 0:
        return None
    return gap


def r_target(entry: float, target: float, risk: float | None) -> float | None:
    if risk is None or risk <= 0:
        return None
    return abs(float(target) - float(entry)) / risk


def expectancy_after_costs(
    *,
    p_win: ProbabilityProvenance,
    avg_r_win: float,
    cost: CostModel,
    risk: float | None,
) -> tuple[float | None, tuple[str, ...]]:
    """(p_win * avg_R_win) - ((1-p_win) * 1) after costs. prior(judgement) excluded."""
    notes: list[str] = []
    if not p_win.usable_for_expectancy():
        notes.append("prior(judgement) excluded from expectancy and sizing")
        return None, tuple(notes)
    if risk is None or risk <= 0:
        notes.append("risk_per_unit missing/non-positive; expectancy unavailable")
        return None, tuple(notes)
    p = float(p_win.value)
    if p < 0 or p > 1:
        notes.append("p_win outside [0, 1]; expectancy unavailable")
        return None, tuple(notes)
    raw = (p * float(avg_r_win)) - ((1.0 - p) * 1.0)
    cost_r = cost.total / risk
    return raw - cost_r, tuple(notes)


def vol_targeted_size_pct(
    *,
    risk_budget_pct: float,
    stop_distance_atr: float | None,
    atr_pct: float | None,
    max_leverage: float,
) -> tuple[float, bool, tuple[str, ...]]:
    """size_pct = risk_budget_pct / (stop_distance_atr * atr_pct). Leverage is a ceiling only."""
    notes: list[str] = []
    if stop_distance_atr is None or atr_pct is None or stop_distance_atr <= 0 or atr_pct <= 0:
        notes.append("vol inputs missing/non-positive; size_pct=0")
        return 0.0, False, tuple(notes)
    raw = float(risk_budget_pct) / (float(stop_distance_atr) * float(atr_pct))
    if raw < 0:
        raw = 0.0
    ceiling = max(0.0, float(max_leverage) * 100.0)
    if raw > ceiling:
        notes.append(f"leverage cap is a ceiling only; clipped {raw:.6g} -> {ceiling:.6g}")
        return ceiling, True, tuple(notes)
    return raw, False, tuple(notes)


def compute_trade_math(
    *,
    instrument: str,
    entry: float,
    stop: float,
    targets: tuple[float, ...] | list[float],
    p_win: ProbabilityProvenance,
    avg_r_win: float,
    atr_pct: float | None,
    stop_distance_atr: float | None,
    funding_rate: float = 0.0,
    est_slippage: float | None = None,
    clip: float | None = None,
    expected_hold: float | None = None,
    asset_class: str = "unknown",
    repo_root: Path | None = None,
    config: Mapping[str, Any] | None = None,
) -> TradeMath:
    """Compute the full inherited math object. Callers must not recompute R."""
    cfg = dict(config) if config is not None else load_trade_math_config(repo_root)
    cost_cfg = cfg.get("cost") if isinstance(cfg.get("cost"), dict) else {}
    min_sample = int(cfg.get("min_sample") or 20)
    risk_budget_pct = float(cfg.get("risk_budget_pct") or 1.0)
    max_leverage = float(cfg.get("max_leverage") or 1.0)
    taker = float(cost_cfg.get("taker_fee") or 0.00045)
    default_clip = float(cost_cfg.get("default_clip") or 10000)
    default_hold = float(cost_cfg.get("default_hold_hours") or 24)
    used_clip = default_clip if clip is None else float(clip)
    used_hold = default_hold if expected_hold is None else float(expected_hold)
    slip = 0.0 if est_slippage is None else float(est_slippage)
    cost = CostModel(
        taker_fee=taker,
        est_slippage=slip,
        funding_rate=float(funding_rate),
        expected_hold=used_hold,
        clip=used_clip,
    )
    risk = risk_per_unit(entry, stop)
    tgt = tuple(float(t) for t in targets)
    rs = tuple(r_target(entry, t, risk) for t in tgt)
    notes: list[str] = []
    sample_n = int(p_win.n or 0)
    below = sample_n < min_sample
    if below:
        notes.append(f"n={sample_n} < min_sample={min_sample}; desk states it; size_pct=0")
    exp, exp_notes = expectancy_after_costs(p_win=p_win, avg_r_win=avg_r_win, cost=cost, risk=risk)
    notes.extend(exp_notes)
    if not p_win.usable_for_expectancy():
        size_pct, capped, size_notes = 0.0, False, ("prior(judgement) excluded from sizing",)
        notes.extend(size_notes)
        exp = None
    elif below:
        size_pct, capped = 0.0, False
    else:
        size_pct, capped, size_notes = vol_targeted_size_pct(
            risk_budget_pct=risk_budget_pct,
            stop_distance_atr=stop_distance_atr,
            atr_pct=atr_pct,
            max_leverage=max_leverage,
        )
        notes.extend(size_notes)
    inputs = {
        "risk_budget_pct": risk_budget_pct,
        "stop_distance_atr": stop_distance_atr,
        "atr_pct": atr_pct,
        "max_leverage": max_leverage,
        "formula": "risk_budget_pct / (stop_distance_atr * atr_pct)",
        "same_logic_crypto_equities": True,
    }
    return TradeMath(
        instrument=str(instrument).upper(),
        entry=float(entry),
        stop=float(stop),
        targets=tgt,
        risk_per_unit=risk,
        r_targets=rs,
        expectancy=exp,
        size_pct=float(size_pct),
        cost=cost,
        p_win=p_win,
        avg_r_win=float(avg_r_win),
        min_sample=min_sample,
        sample_n=sample_n,
        below_min_sample=below,
        leverage_capped=capped,
        notes=tuple(notes),
        asset_class=asset_class,
        inputs=inputs,
    )


def inherited_hash(math: TradeMath) -> str:
    return math.content_hash()


def assert_inherited_math(expected_hash: str, actual_hash: str, *, artifact_type: str) -> None:
    if expected_hash != actual_hash:
        raise TradeMathMismatch(f"{artifact_type} trade_math_hash mismatch")


class TradeMathMismatch(ValueError):
    """Raised when an artifact recomputed or drifted from Quant-owned math."""
