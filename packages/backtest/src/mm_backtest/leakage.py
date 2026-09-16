"""Detect look-ahead / leakage in raw backtest fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mm_backtest.bars import parse_as_of

LOOKAHEAD_KEYS = frozenset(
    {
        "future_close",
        "future_high",
        "future_low",
        "future_open",
        "next_close",
        "next_return",
        "next_high",
        "lookahead",
        "look_ahead",
        "t_plus_1",
        "ahead_close",
        "forward_close",
        "label_future",
    }
)


@dataclass(frozen=True)
class LeakageFinding:
    index: int
    message: str
    key: str | None = None


def scan_fixture_for_lookahead(payload: dict[str, Any] | list[Any]) -> list[LeakageFinding]:
    """Return findings for an intentional or accidental look-ahead fixture.

    Flags:
    - forbidden future fields (`future_close`, `next_return`, …)
    - `available_at` / `ingested_at` strictly before `market_time` (close known early)
    """
    if isinstance(payload, list):
        bars = payload
    else:
        bars = payload.get("bars") or payload.get("candles") or []
        if isinstance(bars, dict):
            flattened: list[Any] = []
            for rows in bars.values():
                flattened.extend(rows)
            bars = flattened
    findings: list[LeakageFinding] = []
    for idx, raw in enumerate(bars):
        if not isinstance(raw, dict):
            continue
        findings.extend(_scan_bar(idx, raw))
    return findings


def _scan_bar(index: int, raw: dict[str, Any]) -> list[LeakageFinding]:
    findings: list[LeakageFinding] = []
    for key in raw:
        lowered = key.lower().replace("-", "_")
        if lowered in LOOKAHEAD_KEYS or any(token in lowered for token in ("future_", "next_return", "lookahead")):
            findings.append(
                LeakageFinding(
                    index=index,
                    key=key,
                    message=f"bar[{index}] has look-ahead field {key!r}",
                )
            )
    market_raw = raw.get("market_time", raw.get("T", raw.get("t", raw.get("time"))))
    available_raw = raw.get("available_at", raw.get("as_of", raw.get("ingested_at", raw.get("knowledge_time"))))
    if market_raw is not None and available_raw is not None:
        try:
            market_time = parse_as_of(market_raw)
            available_at = parse_as_of(available_raw)
        except (ValueError, TypeError, OverflowError):
            return findings
        if available_at < market_time:
            findings.append(
                LeakageFinding(
                    index=index,
                    key="available_at",
                    message=(
                        f"bar[{index}] available_at {available_at.isoformat()} is before "
                        f"market_time {market_time.isoformat()} (close known early)"
                    ),
                )
            )
    return findings


def has_lookahead(payload: dict[str, Any] | list[Any]) -> bool:
    return bool(scan_fixture_for_lookahead(payload))
