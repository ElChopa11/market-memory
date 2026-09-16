"""Gates: paper cannot open without invalidation + max loss (Phase 4)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from mm_paper.errors import (
    MAX_LOSS_NOT_POSITIVE,
    MISSING_INVALIDATION,
    MISSING_MAX_LOSS,
    PaperGateError,
)

PLACEHOLDERS = frozenset(
    {
        "",
        "-",
        "n/a",
        "na",
        "none",
        "null",
        "tbd",
        "todo",
        "?",
        "unknown",
        "placeholder",
    }
)

_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


def _blank_or_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in PLACEHOLDERS


def require_invalidation(value: str | None) -> str:
    if _blank_or_placeholder(value):
        raise PaperGateError(MISSING_INVALIDATION)
    assert value is not None
    return value.strip()


def parse_max_loss(value: str | None) -> tuple[str, Decimal]:
    if _blank_or_placeholder(value):
        raise PaperGateError(MISSING_MAX_LOSS)
    assert value is not None
    text = value.strip()
    match = _NUMBER.search(text.replace(",", ""))
    if match is None:
        raise PaperGateError(MISSING_MAX_LOSS)
    try:
        amount = Decimal(match.group(0))
    except InvalidOperation as exc:
        raise PaperGateError(MISSING_MAX_LOSS) from exc
    if amount <= 0:
        raise PaperGateError(MAX_LOSS_NOT_POSITIVE)
    return text, amount


def require_open_fields(*, invalidation: str | None, max_loss: str | None) -> tuple[str, str, Decimal]:
    inv = require_invalidation(invalidation)
    raw, amount = parse_max_loss(max_loss)
    return inv, raw, amount
