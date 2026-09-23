"""Standing brief gap lines. Paper only. Not a source and not a size."""

from __future__ import annotations

# Principal day order 2026-09-23 P3 context. Do not invent a new earnings feed here.
GATE5_EARNINGS_GAPS_LINE = (
    "Gate 5 is lockup + macro only "
    "(0/15 Polygon confirmation; Benzinga 403; events=ticker_change only)"
)


def with_gate5_gaps_line(text: str) -> str:
    """Put the standing Gate 5 earnings limitation on the brief GAPS line."""
    line = f"GAPS: {GATE5_EARNINGS_GAPS_LINE}"
    body = text or ""
    if line in body:
        return body if body.endswith("\n") else body + "\n"
    rest = body.lstrip("\n")
    if not rest:
        return line + "\n"
    if not rest.endswith("\n"):
        rest += "\n"
    return f"{line}\n{rest}"
