"""Deterministic strategy protocol used by the replay harness."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from mm_backtest.pit import PointInTimeView


@dataclass(frozen=True)
class Signal:
    side: str  # buy | sell
    qty: Decimal

    def canonical(self) -> dict[str, str]:
        return {"side": self.side, "qty": format(self.qty, "f")}


class Strategy(Protocol):
    name: str

    def params(self) -> dict[str, str]: ...

    def on_bar(self, view: PointInTimeView, position: Decimal) -> Signal | None: ...


class BuyHoldStrategy:
    """Buy `qty` on the first visible bar; hold. Deterministic."""

    name = "buy_hold"

    def __init__(self, qty: Decimal | str = Decimal("1")) -> None:
        self.qty = Decimal(str(qty))

    def params(self) -> dict[str, str]:
        return {"qty": format(self.qty, "f")}

    def on_bar(self, view: PointInTimeView, position: Decimal) -> Signal | None:
        if view.last is None or position != 0:
            return None
        return Signal(side="buy", qty=self.qty)


class ThresholdStrategy:
    """Long when last close >= threshold; flatten when close < threshold."""

    name = "threshold"

    def __init__(self, threshold: Decimal | str, qty: Decimal | str = Decimal("1")) -> None:
        self.threshold = Decimal(str(threshold))
        self.qty = Decimal(str(qty))

    def params(self) -> dict[str, str]:
        return {"threshold": format(self.threshold, "f"), "qty": format(self.qty, "f")}

    def on_bar(self, view: PointInTimeView, position: Decimal) -> Signal | None:
        bar = view.last
        if bar is None:
            return None
        if bar.close >= self.threshold and position == 0:
            return Signal(side="buy", qty=self.qty)
        if bar.close < self.threshold and position > 0:
            return Signal(side="sell", qty=position)
        return None


def build_strategy(name: str, params: dict[str, str] | None = None) -> Strategy:
    params = params or {}
    key = name.strip().lower().replace("-", "_")
    if key in {"buy_hold", "buyhold", "buy_and_hold"}:
        return BuyHoldStrategy(qty=params.get("qty", "1"))
    if key in {"threshold", "breakout"}:
        if "threshold" not in params:
            raise ValueError("threshold strategy requires param threshold")
        return ThresholdStrategy(threshold=params["threshold"], qty=params.get("qty", "1"))
    raise ValueError(f"unknown strategy {name!r}; use buy_hold or threshold")
