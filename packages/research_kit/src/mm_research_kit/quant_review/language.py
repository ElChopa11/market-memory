"""Language gate for Quant Review Board output. Research-only."""

from __future__ import annotations

import re

from mm_research_kit.errors import GateError
from mm_research_kit.quant_review.models import LABEL_ARBITRAGE, QuantCard

# Patterns must not include CI-forbidden signing tokens.
_FORBIDDEN: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("MAKE call-language", re.compile(r"\bMAKE\b")),
    ("active-call language", re.compile(r"\bactive[-\s_]?calls?\b", re.IGNORECASE)),
    ("confidence-as-verdict", re.compile(r"\b(high|low|medium)\s+confidence\s+(verdict|call)\b", re.IGNORECASE)),
    ("trade sizing", re.compile(r"\b(position\s+size|size\s+the\s+position|% of portfolio|contracts?\s+of)\b", re.IGNORECASE)),
    ("notional sizing", re.compile(r"\b(notional|allocate|allocation\s+of)\b", re.IGNORECASE)),
    ("order language", re.compile(r"\b(place\s+an?\s+order|market\s+order|limit\s+order|submit\s+order)\b", re.IGNORECASE)),
    ("order language", re.compile(r"\b(buy\s+now|sell\s+now|go\s+long|go\s+short)\b", re.IGNORECASE)),
    ("execution instruction", re.compile(r"\b(entry\s+at|take\s+profit|stop\s+loss)\b", re.IGNORECASE)),
)


def language_violations(text: str) -> list[str]:
    return sorted({label for label, pattern in _FORBIDDEN if pattern.search(text)})


def assert_language_clean(text: str) -> None:
    hits = language_violations(text)
    if hits:
        raise GateError("quant review output contains forbidden language: " + ", ".join(hits))


def arbitrage_label_ok(card: QuantCard) -> bool:
    has_label = LABEL_ARBITRAGE in card.labels
    if has_label and not card.executable_arb:
        return False
    if card.executable_arb and LABEL_ARBITRAGE not in card.labels:
        return False
    return True
