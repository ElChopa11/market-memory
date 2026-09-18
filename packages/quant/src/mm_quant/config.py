"""Load versioned quant factor + regime config. Thresholds live in YAML, not model weights."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_FACTORS_REL = Path("config/quant/factors.yaml")
DEFAULT_REGIME_REL = Path("config/quant/regime.yaml")


@dataclass(frozen=True)
class MomentumWindows:
    equity_short_bars: int = 21
    equity_long_bars: int = 63
    crypto_short_bars: int = 30
    crypto_long_bars: int = 90


@dataclass(frozen=True)
class VolWindows:
    short_bars: int = 20
    long_bars: int = 60
    crypto_ann_factor: float = 365.0
    equity_ann_factor: float = 252.0
    min_bars: int = 20


@dataclass(frozen=True)
class ZScoreSpec:
    window: int = 20


@dataclass(frozen=True)
class AdxSpec:
    period: int = 14
    min_bars: int = 28


@dataclass(frozen=True)
class RelativeStrengthSpec:
    crypto_benchmark: str = "BTC"
    equity_benchmark: str = "SPY"
    sector_etfs: dict[str, str] | None = None
    instrument_sector: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.sector_etfs is None:
            object.__setattr__(self, "sector_etfs", {"semiconductors": "SMH", "financials": "XLF"})
        if self.instrument_sector is None:
            object.__setattr__(
                self,
                "instrument_sector",
                {
                    "NVDA": "semiconductors",
                    "AVGO": "semiconductors",
                    "SMH": "semiconductors",
                    "JPM": "financials",
                    "XLF": "financials",
                },
            )


@dataclass(frozen=True)
class BreadthSpec:
    sma_window: int = 20
    min_names: int = 3


@dataclass(frozen=True)
class CorrSpec:
    window: int = 60
    min_overlap: int = 20


@dataclass(frozen=True)
class BetaSpec:
    window: int = 60
    min_overlap: int = 20


@dataclass(frozen=True)
class SizingSpec:
    vol_target: float = 0.10
    vol_target_base_fraction: float = 1.0
    fixed_fraction: float = 0.01
    cap_pct: float = 5.0


@dataclass(frozen=True)
class StatsSpec:
    bootstrap_seed: int = 42
    bootstrap_draws: int = 500
    walk_forward_train_min: int = 40
    walk_forward_test_size: int = 10
    walk_forward_step: int = 10
    walk_forward_embargo: int = 1


@dataclass(frozen=True)
class RegimeThresholds:
    version: str = "2026-09-18"
    vol_low: float = 0.20
    vol_high: float = 0.50
    adx_trending: float = 25.0
    zscore_stretched: float = 2.0
    funding_crowded: float = 0.0003
    min_inputs_for_tag: int = 2


@dataclass(frozen=True)
class QuantConfig:
    version: str = "2026-09-18"
    kind: str = "quant_factor_library"
    desk: str = "Quant & Market Structure Desk"
    momentum: MomentumWindows = field(default_factory=MomentumWindows)
    realised_vol: VolWindows = field(default_factory=VolWindows)
    zscore: ZScoreSpec = field(default_factory=ZScoreSpec)
    adx: AdxSpec = field(default_factory=AdxSpec)
    relative_strength: RelativeStrengthSpec = field(default_factory=RelativeStrengthSpec)
    breadth: BreadthSpec = field(default_factory=BreadthSpec)
    correlation: CorrSpec = field(default_factory=CorrSpec)
    beta: BetaSpec = field(default_factory=BetaSpec)
    sizing: SizingSpec = field(default_factory=SizingSpec)
    stats: StatsSpec = field(default_factory=StatsSpec)
    regime: RegimeThresholds = field(default_factory=RegimeThresholds)
    crypto_assets: tuple[str, ...] = ("BTC", "ETH", "UNI", "AAVE")

    @classmethod
    def defaults(cls) -> QuantConfig:
        return cls()

    def is_crypto(self, instrument: str) -> bool:
        return instrument.upper() in {name.upper() for name in self.crypto_assets}

    def ann_factor(self, instrument: str) -> float:
        if self.is_crypto(instrument):
            return self.realised_vol.crypto_ann_factor
        return self.realised_vol.equity_ann_factor

    def momentum_windows(self, instrument: str) -> tuple[int, int]:
        if self.is_crypto(instrument):
            return self.momentum.crypto_short_bars, self.momentum.crypto_long_bars
        return self.momentum.equity_short_bars, self.momentum.equity_long_bars

    def sector_etf(self, instrument: str) -> str | None:
        sector = (self.relative_strength.instrument_sector or {}).get(instrument.upper())
        if not sector:
            return None
        return (self.relative_strength.sector_etfs or {}).get(sector)


def _req_float(data: dict[str, Any], key: str) -> float:
    if key not in data:
        raise ValueError(f"missing threshold {key!r}")
    return float(data[key])


def _req_int(data: dict[str, Any], key: str) -> int:
    if key not in data:
        raise ValueError(f"missing int {key!r}")
    return int(data[key])


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def load_quant_config(root: Path | None = None) -> QuantConfig:
    """Load `config/quant/*.yaml`. Missing files raise — never invent thresholds."""
    base = root if root is not None else Path.cwd()
    factors_path = base / DEFAULT_FACTORS_REL
    regime_path = base / DEFAULT_REGIME_REL
    factors = load_yaml(factors_path)
    regime = load_yaml(regime_path)
    mom = factors.get("momentum") or {}
    vol = factors.get("realised_vol") or {}
    z = factors.get("zscore") or {}
    adx = factors.get("adx") or {}
    rs = factors.get("relative_strength") or {}
    breadth = factors.get("breadth") or {}
    corr = factors.get("correlation") or {}
    beta = factors.get("beta") or {}
    sizing = factors.get("sizing") or {}
    stats = factors.get("stats") or {}
    vol_th = regime.get("vol") or {}
    adx_th = regime.get("adx") or {}
    z_th = regime.get("zscore") or {}
    fund_th = regime.get("funding") or {}
    crypto = tuple(str(x).upper() for x in (factors.get("crypto_assets") or ["BTC", "ETH", "UNI", "AAVE"]))
    return QuantConfig(
        version=str(factors.get("version") or "unknown"),
        kind=str(factors.get("kind") or "quant_factor_library"),
        desk=str(factors.get("desk") or "Quant & Market Structure Desk"),
        momentum=MomentumWindows(
            equity_short_bars=_req_int(mom, "equity_short_bars"),
            equity_long_bars=_req_int(mom, "equity_long_bars"),
            crypto_short_bars=_req_int(mom, "crypto_short_bars"),
            crypto_long_bars=_req_int(mom, "crypto_long_bars"),
        ),
        realised_vol=VolWindows(
            short_bars=_req_int(vol, "short_bars"),
            long_bars=_req_int(vol, "long_bars"),
            crypto_ann_factor=_req_float(vol, "crypto_ann_factor"),
            equity_ann_factor=_req_float(vol, "equity_ann_factor"),
            min_bars=_req_int(vol, "min_bars"),
        ),
        zscore=ZScoreSpec(window=_req_int(z, "window")),
        adx=AdxSpec(period=_req_int(adx, "period"), min_bars=_req_int(adx, "min_bars")),
        relative_strength=RelativeStrengthSpec(
            crypto_benchmark=str(rs.get("crypto_benchmark") or "BTC"),
            equity_benchmark=str(rs.get("equity_benchmark") or "SPY"),
            sector_etfs={str(k): str(v) for k, v in (rs.get("sector_etfs") or {}).items()},
            instrument_sector={str(k).upper(): str(v) for k, v in (rs.get("instrument_sector") or {}).items()},
        ),
        breadth=BreadthSpec(
            sma_window=_req_int(breadth, "sma_window"),
            min_names=_req_int(breadth, "min_names"),
        ),
        correlation=CorrSpec(
            window=_req_int(corr, "window"),
            min_overlap=_req_int(corr, "min_overlap"),
        ),
        beta=BetaSpec(
            window=_req_int(beta, "window"),
            min_overlap=_req_int(beta, "min_overlap"),
        ),
        sizing=SizingSpec(
            vol_target=_req_float(sizing, "vol_target"),
            vol_target_base_fraction=_req_float(sizing, "vol_target_base_fraction"),
            fixed_fraction=_req_float(sizing, "fixed_fraction"),
            cap_pct=_req_float(sizing, "cap_pct"),
        ),
        stats=StatsSpec(
            bootstrap_seed=_req_int(stats, "bootstrap_seed"),
            bootstrap_draws=_req_int(stats, "bootstrap_draws"),
            walk_forward_train_min=_req_int(stats, "walk_forward_train_min"),
            walk_forward_test_size=_req_int(stats, "walk_forward_test_size"),
            walk_forward_step=_req_int(stats, "walk_forward_step"),
            walk_forward_embargo=_req_int(stats, "walk_forward_embargo"),
        ),
        regime=RegimeThresholds(
            version=str(regime.get("version") or "unknown"),
            vol_low=_req_float(vol_th, "low"),
            vol_high=_req_float(vol_th, "high"),
            adx_trending=_req_float(adx_th, "trending"),
            zscore_stretched=_req_float(z_th, "stretched"),
            funding_crowded=_req_float(fund_th, "crowded"),
            min_inputs_for_tag=_req_int(regime, "min_inputs_for_tag"),
        ),
        crypto_assets=crypto,
    )
