"""Language gate for factor-card markdown. Research-only; no order instructions."""

from __future__ import annotations

import re

_FORBIDDEN: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("MAKE call-language", re.compile(r"\bmake\b", re.IGNORECASE)),
    ("active-call language", re.compile(r"\bactive[-\s_]?calls?\b", re.IGNORECASE)),
    ("high confidence", re.compile(r"\bhigh\s+confidence\b", re.IGNORECASE)),
    ("buy language", re.compile(r"\bbuy\b", re.IGNORECASE)),
    ("sell language", re.compile(r"\bsell\b", re.IGNORECASE)),
    ("order language", re.compile(r"\b(place\s+an?\s+order|market\s+order|limit\s+order|submit\s+order)\b", re.IGNORECASE)),
    ("direction instruction", re.compile(r"\bgo\s+(long|short)\b", re.IGNORECASE)),
    ("execution instruction", re.compile(r"\b(entry\s+at|take\s+profit|stop\s+loss)\b", re.IGNORECASE)),
)


class QuantLanguageError(ValueError):
    """Factor-card markdown failed the research-only language gate."""


def language_violations(text: str) -> list[str]:
    return sorted({label for label, pattern in _FORBIDDEN if pattern.search(text)})


def assert_language_clean(text: str) -> None:
    hits = language_violations(text)
    if hits:
        raise QuantLanguageError("quant factor card contains forbidden language: " + ", ".join(hits))
