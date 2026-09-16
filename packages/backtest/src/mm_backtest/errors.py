"""Backtest errors. Never include secrets or live trading paths."""

from __future__ import annotations


class BacktestError(Exception):
    """Base error for the evaluation harness."""


class LookAheadError(BacktestError):
    """Raised when code or a fixture tries to see the future."""


class FixtureLookAheadError(LookAheadError):
    """Intentional or accidental look-ahead in a candle/event fixture."""


class PointInTimeError(LookAheadError):
    """A point-in-time view refused a future bar or observation."""
