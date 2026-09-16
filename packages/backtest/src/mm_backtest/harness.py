"""Event/bar replay harness. Same params_hash → same result_hash."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from mm_backtest.bars import Bar, KnowledgeFact
from mm_backtest.errors import BacktestError
from mm_backtest.params import bars_hash, facts_hash, params_hash, result_hash
from mm_backtest.pit import PointInTimeView
from mm_backtest.strategy import Strategy
from mm_common.time import as_utc


def _dec(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def apply_slippage(price: Decimal, side: str, slippage_bps: Decimal) -> Decimal:
    bps = slippage_bps / Decimal("10000")
    if side == "buy":
        return price * (Decimal("1") + bps)
    if side == "sell":
        return price * (Decimal("1") - bps)
    raise BacktestError(f"unknown side {side!r}")


@dataclass
class Fill:
    as_of: datetime
    side: str
    qty: Decimal
    price: Decimal
    slippage_bps: Decimal
    mark: Decimal

    def canonical(self) -> dict[str, str]:
        return {
            "as_of": self.as_of.isoformat(),
            "side": self.side,
            "qty": format(self.qty, "f"),
            "price": format(self.price, "f"),
            "slippage_bps": format(self.slippage_bps, "f"),
            "mark": format(self.mark, "f"),
        }


@dataclass
class EquityPoint:
    as_of: datetime
    equity: Decimal
    cash: Decimal
    position: Decimal
    mark: Decimal

    def canonical(self) -> dict[str, str]:
        return {
            "as_of": self.as_of.isoformat(),
            "equity": format(self.equity, "f"),
            "cash": format(self.cash, "f"),
            "position": format(self.position, "f"),
            "mark": format(self.mark, "f"),
        }


@dataclass
class BacktestResult:
    params_hash: str
    result_hash: str
    bars_hash: str
    strategy: str
    instrument: str
    fills: list[Fill] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)
    metrics: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)

    def canonical_result(self) -> dict[str, Any]:
        return {
            "fills": [fill.canonical() for fill in self.fills],
            "equity_curve": [point.canonical() for point in self.equity_curve],
            "metrics": dict(sorted(self.metrics.items())),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "params_hash": self.params_hash,
            "result_hash": self.result_hash,
            "bars_hash": self.bars_hash,
            "strategy": self.strategy,
            "instrument": self.instrument,
            "metrics": self.metrics,
            "n_fills": len(self.fills),
            "n_bars": len(self.equity_curve),
        }


@dataclass(frozen=True)
class BacktestParams:
    instrument: str = "BTC"
    strategy: str = "buy_hold"
    strategy_params: dict[str, str] | None = None
    initial_cash: Decimal = Decimal("10000")
    slippage_bps: Decimal = Decimal("0")
    start: datetime | None = None
    end: datetime | None = None
    qty: str = "1"


def replay_clock(bars: list[Bar], *, start: datetime | None = None, end: datetime | None = None) -> list[datetime]:
    stamps = sorted({bar.available_at for bar in bars})
    if start is not None:
        start = as_utc(start)
        stamps = [ts for ts in stamps if ts >= start]
    if end is not None:
        end = as_utc(end)
        stamps = [ts for ts in stamps if ts <= end]
    return stamps


def run_backtest(
    bars: list[Bar],
    strategy: Strategy,
    *,
    instrument: str | None = None,
    facts: list[KnowledgeFact] | None = None,
    initial_cash: Decimal | str = Decimal("10000"),
    slippage_bps: Decimal | str = Decimal("0"),
    start: datetime | None = None,
    end: datetime | None = None,
) -> BacktestResult:
    if not bars:
        raise BacktestError("no bars to replay")
    instrument = instrument or bars[0].instrument
    relevant = [bar for bar in bars if bar.instrument == instrument]
    if not relevant:
        raise BacktestError(f"no bars for instrument {instrument}")
    facts = facts or []
    cash = _dec(initial_cash)
    slip = _dec(slippage_bps)
    position = Decimal("0")
    fills: list[Fill] = []
    curve: list[EquityPoint] = []

    for as_of in replay_clock(relevant, start=start, end=end):
        view = PointInTimeView.at(as_of=as_of, instrument=instrument, bars=relevant, facts=facts)
        bar = view.last
        if bar is None:
            continue
        signal = strategy.on_bar(view, position)
        if signal is not None:
            qty = _dec(signal.qty)
            if qty <= 0:
                raise BacktestError("signal qty must be positive")
            price = apply_slippage(bar.close, signal.side, slip)
            if signal.side == "buy":
                cash -= price * qty
                position += qty
            elif signal.side == "sell":
                cash += price * qty
                position -= qty
            else:
                raise BacktestError(f"unknown side {signal.side!r}")
            fills.append(
                Fill(
                    as_of=as_of,
                    side=signal.side,
                    qty=qty,
                    price=price,
                    slippage_bps=slip,
                    mark=bar.close,
                )
            )
        equity = cash + position * bar.close
        curve.append(EquityPoint(as_of=as_of, equity=equity, cash=cash, position=position, mark=bar.close))

    if not curve:
        raise BacktestError("replay produced no equity points (check start/end vs available_at)")

    initial = _dec(initial_cash)
    final = curve[-1].equity
    total_return = (final / initial - Decimal("1")) if initial != 0 else Decimal("0")
    peak = curve[0].equity
    max_dd = Decimal("0")
    for point in curve:
        if point.equity > peak:
            peak = point.equity
        if peak > 0:
            dd = (peak - point.equity) / peak
            if dd > max_dd:
                max_dd = dd

    resolved_start = curve[0].as_of.isoformat()
    resolved_end = curve[-1].as_of.isoformat()
    param_payload = {
        "bars_hash": bars_hash(relevant),
        "facts_hash": facts_hash(facts),
        "strategy": strategy.name,
        "strategy_params": strategy.params(),
        "instrument": instrument,
        "initial_cash": format(initial, "f"),
        "slippage_bps": format(slip, "f"),
        "start": resolved_start,
        "end": resolved_end,
    }
    metrics = {
        "initial_cash": format(initial, "f"),
        "final_equity": format(final, "f"),
        "total_return": format(total_return, "f"),
        "max_drawdown": format(max_dd, "f"),
        "n_fills": str(len(fills)),
        "final_position": format(position, "f"),
        "final_cash": format(cash, "f"),
    }
    result = BacktestResult(
        params_hash="",
        result_hash="",
        bars_hash=param_payload["bars_hash"],
        strategy=strategy.name,
        instrument=instrument,
        fills=fills,
        equity_curve=curve,
        metrics=metrics,
        params=param_payload,
    )
    result.params_hash = params_hash(param_payload)
    result.result_hash = result_hash(result.canonical_result())
    return result
