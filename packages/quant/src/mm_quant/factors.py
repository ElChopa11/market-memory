"""Research-only factor registry. PIT-safe. Degrade, never invent."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from mm_common.hashing import canonical_json, sha256_hex
from mm_quant.config import QuantConfig
from mm_quant.mathutil import adx_wilder, beta, pearson, realised_vol, sma, trailing_return, zscore
from mm_quant.models import (
    ENGINE_VERSION,
    FactorValue,
    MarketPanel,
    OK,
    PARTIAL,
    ProvenanceRef,
    SeriesBar,
    UNAVAILABLE,
)
from mm_quant.series import aligned_return_pairs, bars_for, closes, latest_structure, simple_returns, visible_panel

FACTOR_NAMES = (
    "momentum_short",
    "momentum_long",
    "realised_vol_short",
    "realised_vol_long",
    "adx",
    "zscore",
    "funding_carry",
    "basis_carry",
    "relative_strength_btc",
    "relative_strength_sector",
    "breadth",
    "correlation_matrix",
    "beta",
)

ComputeFn = Callable[[str, MarketPanel, datetime, QuantConfig], FactorValue]


def _unavailable(
    name: str,
    watermark: datetime,
    reason: str,
    *,
    window: int | None = None,
    provenance: tuple[ProvenanceRef, ...] = (),
    inputs: dict | None = None,
) -> FactorValue:
    return FactorValue(
        name=name,
        status=UNAVAILABLE,
        as_of_knowledge=watermark,
        window=window,
        provenance=provenance,
        inputs=inputs or {},
        reason=reason,
    )


def _ok(
    name: str,
    watermark: datetime,
    value: float | None,
    *,
    unit: str = "",
    window: int | None = None,
    provenance: tuple[ProvenanceRef, ...] = (),
    inputs: dict | None = None,
    payload: dict | None = None,
    reason: str = "",
    status: str = OK,
) -> FactorValue:
    return FactorValue(
        name=name,
        status=status,
        as_of_knowledge=watermark,
        value=value,
        unit=unit,
        window=window,
        payload=payload or {},
        inputs=inputs or {},
        provenance=provenance,
        reason=reason,
    )


def _bar_prov(bars: tuple[SeriesBar, ...]) -> tuple[ProvenanceRef, ...]:
    if not bars:
        return ()
    first, last = bars[0], bars[-1]
    refs = [first.provenance(), last.provenance()]
    # Deduplicate identical endpoints.
    out: list[ProvenanceRef] = []
    seen: set[tuple] = set()
    for ref in refs:
        key = (ref.observation_id, ref.as_of_knowledge, ref.metric)
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return tuple(out)


def _momentum(kind: str) -> ComputeFn:
    def _compute(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
        name = f"momentum_{kind}"
        short, long = config.momentum_windows(instrument)
        window = short if kind == "short" else long
        bars = bars_for(panel, instrument)
        prices = closes(bars)
        value = trailing_return(prices, window)
        if value is None:
            return _unavailable(
                name,
                watermark,
                f"need {window + 1} PIT bars; have {len(prices)}",
                window=window,
                provenance=_bar_prov(bars),
            )
        return _ok(
            name,
            watermark,
            value,
            unit="fraction",
            window=window,
            provenance=_bar_prov(bars),
            inputs={"n_prices": len(prices), "start_close": prices[-1 - window], "end_close": prices[-1]},
            reason=f"trailing {window}-bar return",
        )

    return _compute


def _vol(kind: str) -> ComputeFn:
    def _compute(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
        name = f"realised_vol_{kind}"
        window = config.realised_vol.short_bars if kind == "short" else config.realised_vol.long_bars
        bars = bars_for(panel, instrument)
        rets = simple_returns(closes(bars))
        ann = config.ann_factor(instrument)
        value = realised_vol(rets, window, ann)
        if value is None:
            return _unavailable(
                name,
                watermark,
                f"need {window} PIT returns; have {len(rets)}",
                window=window,
                provenance=_bar_prov(bars),
            )
        return _ok(
            name,
            watermark,
            value,
            unit="annualised",
            window=window,
            provenance=_bar_prov(bars),
            inputs={"n_returns": len(rets), "ann_factor": ann, "window": window},
            reason="sample stdev (ddof=1) * sqrt(ann_factor)",
        )

    return _compute


def compute_adx(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
    bars = bars_for(panel, instrument)
    highs = [bar.high if bar.high is not None else bar.close for bar in bars]
    lows = [bar.low if bar.low is not None else bar.close for bar in bars]
    cls = [bar.close for bar in bars]
    if any(bar.high is None or bar.low is None for bar in bars) and len(bars) >= config.adx.min_bars:
        # High/low missing: degrade rather than invent a range.
        return _unavailable(
            "adx",
            watermark,
            "high/low missing; ADX-style trend not invented from close-only",
            window=config.adx.period,
            provenance=_bar_prov(bars),
            inputs={"n_bars": len(bars)},
        )
    value = adx_wilder(highs, lows, cls, config.adx.period)
    if value is None:
        return _unavailable(
            "adx",
            watermark,
            f"need {config.adx.min_bars} OHLC bars; have {len(bars)}",
            window=config.adx.period,
            provenance=_bar_prov(bars),
        )
    return _ok(
        "adx",
        watermark,
        value,
        unit="index",
        window=config.adx.period,
        provenance=_bar_prov(bars),
        inputs={"n_bars": len(bars), "period": config.adx.period},
        reason="Wilder ADX-style",
    )


def compute_zscore(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
    bars = bars_for(panel, instrument)
    prices = closes(bars)
    window = config.zscore.window
    value = zscore(prices, window)
    if value is None:
        return _unavailable(
            "zscore",
            watermark,
            f"need {window} PIT closes with positive stdev; have {len(prices)}",
            window=window,
            provenance=_bar_prov(bars),
        )
    return _ok(
        "zscore",
        watermark,
        value,
        unit="sigma",
        window=window,
        provenance=_bar_prov(bars),
        inputs={"n_prices": len(prices), "last": prices[-1]},
        reason="(close - mean) / sample stdev",
    )


def compute_funding_carry(
    instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig
) -> FactorValue:
    funding = latest_structure(panel, instrument, "funding")
    predicted = latest_structure(panel, instrument, "predicted_funding")
    chosen = funding if funding is not None and funding.value is not None else predicted
    provenance = tuple(p.provenance() for p in (funding, predicted) if p is not None)
    if chosen is None or chosen.value is None:
        return _unavailable(
            "funding_carry",
            watermark,
            "funding and predicted_funding missing or null (Phase 5b fields not invented)",
            provenance=provenance,
            inputs={"has_funding": funding is not None, "has_predicted_funding": predicted is not None},
        )
    status = OK if funding is not None and funding.value is not None else PARTIAL
    return _ok(
        "funding_carry",
        watermark,
        chosen.value,
        unit="rate",
        provenance=provenance,
        inputs={
            "metric": chosen.metric,
            "funding": None if funding is None else funding.value,
            "predicted_funding": None if predicted is None else predicted.value,
        },
        reason="HL funding when present else predicted_funding",
        status=status,
    )


def compute_basis_carry(
    instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig
) -> FactorValue:
    mark = latest_structure(panel, instrument, "basis_mark_oracle")
    spot = latest_structure(panel, instrument, "basis_perp_spot")
    chosen = mark if mark is not None and mark.value is not None else spot
    provenance = tuple(p.provenance() for p in (mark, spot) if p is not None)
    if chosen is None or chosen.value is None:
        return _unavailable(
            "basis_carry",
            watermark,
            "basis_mark_oracle and basis_perp_spot missing or null (Phase 5b fields not invented)",
            provenance=provenance,
            inputs={"has_basis_mark_oracle": mark is not None, "has_basis_perp_spot": spot is not None},
        )
    status = OK if mark is not None and mark.value is not None else PARTIAL
    return _ok(
        "basis_carry",
        watermark,
        chosen.value,
        unit="fraction",
        provenance=provenance,
        inputs={
            "metric": chosen.metric,
            "basis_mark_oracle": None if mark is None else mark.value,
            "basis_perp_spot": None if spot is None else spot.value,
        },
        reason="basis_mark_oracle when present else basis_perp_spot",
        status=status,
    )


def _relative(name: str, bench: str | None) -> ComputeFn:
    def _compute(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
        short, _long = config.momentum_windows(instrument)
        if not bench:
            return _unavailable(name, watermark, "benchmark not configured", window=short)
        if instrument.upper() == bench.upper() and name == "relative_strength_btc":
            return _unavailable(
                name,
                watermark,
                "instrument is the BTC benchmark; relative strength vs self is not reported",
                window=short,
            )
        left = bars_for(panel, instrument)
        right = bars_for(panel, bench)
        if not right:
            return _unavailable(
                name,
                watermark,
                f"benchmark {bench} series missing — not invented",
                window=short,
                provenance=_bar_prov(left),
                inputs={"benchmark": bench},
            )
        inst_ret = trailing_return(closes(left), short)
        bench_ret = trailing_return(closes(right), short)
        if inst_ret is None or bench_ret is None:
            return _unavailable(
                name,
                watermark,
                f"need {short + 1} overlapping PIT bars vs {bench}",
                window=short,
                provenance=_bar_prov(left) + _bar_prov(right),
                inputs={"benchmark": bench, "n_instrument": len(left), "n_benchmark": len(right)},
            )
        return _ok(
            name,
            watermark,
            inst_ret - bench_ret,
            unit="fraction",
            window=short,
            provenance=_bar_prov(left) + _bar_prov(right),
            inputs={
                "benchmark": bench,
                "instrument_return": inst_ret,
                "benchmark_return": bench_ret,
            },
            reason="name trailing return minus benchmark trailing return (not alpha)",
        )

    return _compute


def compute_rs_btc(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
    return _relative("relative_strength_btc", config.relative_strength.crypto_benchmark)(
        instrument, panel, watermark, config
    )


def compute_rs_sector(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
    sector_etf = config.sector_etf(instrument)
    bench = sector_etf or (
        None if config.is_crypto(instrument) else config.relative_strength.equity_benchmark
    )
    if config.is_crypto(instrument) and not sector_etf:
        return _unavailable(
            "relative_strength_sector",
            watermark,
            "no equity sector/ETF mapping for this crypto name",
            inputs={"instrument": instrument},
        )
    if not sector_etf and bench:
        # Equity without a sector map: try the equity benchmark when that series exists.
        result = _relative("relative_strength_sector", bench)(instrument, panel, watermark, config)
        if result.status == UNAVAILABLE:
            return result
        return FactorValue(
            name=result.name,
            status=PARTIAL,
            as_of_knowledge=result.as_of_knowledge,
            value=result.value,
            unit=result.unit,
            window=result.window,
            payload=result.payload,
            inputs=result.inputs | {"fallback": "equity_benchmark"},
            provenance=result.provenance,
            reason="sector ETF missing; used equity benchmark when present",
        )
    return _relative("relative_strength_sector", bench)(instrument, panel, watermark, config)


def compute_breadth(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
    window = config.breadth.sma_window
    names = sorted({bar.instrument.upper() for bar in panel.bars})
    above = 0
    counted = 0
    missing: list[str] = []
    provenance: list[ProvenanceRef] = []
    for name in names:
        bars = bars_for(panel, name)
        prices = closes(bars)
        mean = sma(prices, window)
        if mean is None:
            missing.append(name)
            continue
        counted += 1
        if prices[-1] > mean:
            above += 1
        provenance.extend(_bar_prov(bars))
    if counted < config.breadth.min_names:
        return _unavailable(
            "breadth",
            watermark,
            f"need {config.breadth.min_names} names with SMA; have {counted}",
            window=window,
            provenance=tuple(provenance),
            inputs={"counted": counted, "missing": missing, "universe": names},
        )
    frac = above / counted
    status = OK if not missing else PARTIAL
    return _ok(
        "breadth",
        watermark,
        frac,
        unit="fraction",
        window=window,
        provenance=tuple(provenance[:8]),
        payload={"above": above, "counted": counted, "missing": missing},
        inputs={"above": above, "counted": counted, "n_names": len(names)},
        reason="fraction of names with close > SMA",
        status=status,
    )


def compute_correlation(
    instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig
) -> FactorValue:
    names = sorted({bar.instrument.upper() for bar in panel.bars})
    window = config.correlation.window
    min_overlap = config.correlation.min_overlap
    matrix: dict[str, dict[str, float | None]] = {}
    used_pairs = 0
    for a in names:
        matrix[a] = {}
        for b in names:
            if a == b:
                matrix[a][b] = 1.0
                continue
            pairs = aligned_return_pairs(bars_for(panel, a), bars_for(panel, b))
            sl = pairs[-window:] if len(pairs) >= window else pairs
            if len(sl) < min_overlap:
                matrix[a][b] = None
                continue
            xs = [p[0] for p in sl]
            ys = [p[1] for p in sl]
            matrix[a][b] = pearson(xs, ys)
            if matrix[a][b] is not None:
                used_pairs += 1
    if len(names) < 2:
        return _unavailable(
            "correlation_matrix",
            watermark,
            "need at least two series",
            window=window,
            inputs={"names": names},
        )
    scalar = matrix.get(instrument.upper(), {}).get(instrument.upper(), 1.0)
    # Instrument's mean pairwise corr excluding self, ignoring nulls.
    row = matrix.get(instrument.upper(), {})
    others = [v for k, v in row.items() if k != instrument.upper() and v is not None]
    mean_pairwise = (sum(others) / len(others)) if others else None
    status = OK if others else PARTIAL if names else UNAVAILABLE
    if mean_pairwise is None and not others:
        return _unavailable(
            "correlation_matrix",
            watermark,
            "insufficient overlapping returns for pairwise corr",
            window=window,
            payload={"matrix": matrix},
            inputs={"names": names, "min_overlap": min_overlap},
        )
    return _ok(
        "correlation_matrix",
        watermark,
        mean_pairwise,
        unit="mean_pairwise",
        window=window,
        payload={"matrix": matrix, "diagonal": scalar},
        inputs={"n_names": len(names), "used_pairs": used_pairs, "min_overlap": min_overlap},
        reason="pairwise Pearson on overlapping PIT returns; diagonal forced to 1",
        status=status,
    )


def compute_beta(instrument: str, panel: MarketPanel, watermark: datetime, config: QuantConfig) -> FactorValue:
    if config.is_crypto(instrument):
        bench = config.relative_strength.crypto_benchmark
    else:
        bench = config.sector_etf(instrument) or config.relative_strength.equity_benchmark
    left = bars_for(panel, instrument)
    right = bars_for(panel, bench)
    if instrument.upper() == bench.upper():
        return _unavailable(
            "beta",
            watermark,
            "instrument is the benchmark; beta vs self is not reported",
            window=config.beta.window,
            inputs={"benchmark": bench},
        )
    if not right:
        return _unavailable(
            "beta",
            watermark,
            f"benchmark {bench} series missing — not invented",
            window=config.beta.window,
            provenance=_bar_prov(left),
            inputs={"benchmark": bench},
        )
    pairs = aligned_return_pairs(left, right)
    sl = pairs[-config.beta.window :] if len(pairs) >= config.beta.window else pairs
    if len(sl) < config.beta.min_overlap:
        return _unavailable(
            "beta",
            watermark,
            f"need {config.beta.min_overlap} overlapping returns vs {bench}; have {len(sl)}",
            window=config.beta.window,
            provenance=_bar_prov(left) + _bar_prov(right),
            inputs={"benchmark": bench, "n_pairs": len(sl)},
        )
    xs = [p[0] for p in sl]
    ys = [p[1] for p in sl]
    value = beta(xs, ys)
    if value is None:
        return _unavailable(
            "beta",
            watermark,
            "benchmark variance is zero or beta undefined",
            window=config.beta.window,
            provenance=_bar_prov(left) + _bar_prov(right),
            inputs={"benchmark": bench},
        )
    return _ok(
        "beta",
        watermark,
        value,
        unit="beta",
        window=config.beta.window,
        provenance=_bar_prov(left) + _bar_prov(right),
        inputs={"benchmark": bench, "n_pairs": len(sl)},
        reason="OLS beta of instrument returns on benchmark returns",
    )


_COMPUTE: dict[str, ComputeFn] = {
    "momentum_short": _momentum("short"),
    "momentum_long": _momentum("long"),
    "realised_vol_short": _vol("short"),
    "realised_vol_long": _vol("long"),
    "adx": compute_adx,
    "zscore": compute_zscore,
    "funding_carry": compute_funding_carry,
    "basis_carry": compute_basis_carry,
    "relative_strength_btc": compute_rs_btc,
    "relative_strength_sector": compute_rs_sector,
    "breadth": compute_breadth,
    "correlation_matrix": compute_correlation,
    "beta": compute_beta,
}


class FactorRegistry:
    """Named PIT-safe factors. Empty in 5a; implemented in 5c (IMP-011)."""

    def __init__(self, config: QuantConfig | None = None) -> None:
        self.config = config or QuantConfig.defaults()
        self._compute = dict(_COMPUTE)

    def names(self) -> tuple[str, ...]:
        return FACTOR_NAMES

    def compute(
        self,
        name: str,
        instrument: str,
        panel: MarketPanel,
        watermark: datetime,
    ) -> FactorValue:
        if name not in self._compute:
            return _unavailable(name, watermark, f"unknown factor {name}")
        pit = visible_panel(panel, watermark)
        return self._compute[name](instrument.upper(), pit, watermark, self.config)

    def compute_all(
        self,
        instrument: str,
        panel: MarketPanel,
        watermark: datetime,
    ) -> tuple[FactorValue, ...]:
        return tuple(self.compute(name, instrument, panel, watermark) for name in self.names())


def factors_hash(values: tuple[FactorValue, ...], *, config_version: str, watermark: datetime) -> str:
    payload = {
        "engine": ENGINE_VERSION,
        "config_version": config_version,
        "watermark": watermark.isoformat(),
        "factors": [row.canonical() for row in values],
    }
    return sha256_hex(canonical_json(payload))
