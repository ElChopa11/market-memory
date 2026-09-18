"""One formatter module: tick, %, $M/$B, z, signed deltas. Unknowns are '?' named in gaps."""

from __future__ import annotations

from typing import Any, Sequence

from mm_common.naming import telegram_header, with_telegram_header

UNKNOWN = "?"


def format_tick(value: float | None, tick: float = 0.5) -> str:
    if value is None:
        return UNKNOWN
    if tick <= 0:
        return f"{value}"
    snapped = round(float(value) / tick) * tick
    if abs(tick - int(tick)) < 1e-12:
        return f"{snapped:.0f}"
    decimals = max(0, str(tick).rstrip("0")[::-1].find("."))
    return f"{snapped:.{max(decimals, 1)}f}"


def format_pct(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    return f"{float(value) * 100.0:.2f}%"


def format_notional(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    abs_v = abs(float(value))
    sign = "-" if value < 0 else ""
    if abs_v >= 1_000_000_000:
        return f"{sign}${abs_v / 1_000_000_000:.1f}B"
    if abs_v >= 1_000_000:
        return f"{sign}${abs_v / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"{sign}${abs_v / 1_000:.1f}K"
    return f"{sign}${abs_v:.1f}"


def format_z(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    return f"{float(value):.2f}"


def format_delta(value: float | None) -> str:
    if value is None:
        return UNKNOWN
    sign = "+" if value > 0 else ""
    return f"{sign}{float(value):.2f}"


def deltas(*, last: float | None, prior: float | None, window_20d: float | None) -> dict[str, str]:
    vs_prior = None if last is None or prior is None else last - prior
    vs_20d = None if last is None or window_20d is None else last - window_20d
    return {"vs_prior": format_delta(vs_prior), "vs_20d": format_delta(vs_20d)}


def monospace_table(headers: Sequence[str], rows: Sequence[Sequence[Any]], *, gaps: list[str] | None = None) -> str:
    str_rows = [[UNKNOWN if cell is None else str(cell) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))
    def fmt(cells: Sequence[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    lines = [fmt(list(headers)), "-+-".join("-" * w for w in widths)]
    for row in str_rows:
        padded = list(row) + [UNKNOWN] * (len(headers) - len(row))
        if gaps is not None:
            for i, cell in enumerate(padded):
                if cell == UNKNOWN:
                    gaps.append(headers[i] if i < len(headers) else f"col{i}")
        lines.append(fmt(padded[: len(headers)]))
    return "```\n" + "\n".join(lines) + "\n```"


def desk_header(slug: str, *, artifact_type: str | None = None) -> str:
    """Telegram / pack banner from the naming layer. Unknown slug fails closed."""
    return telegram_header(slug, artifact_type=artifact_type)


def headed_markdown(markdown: str, slug: str, *, artifact_type: str | None = None) -> str:
    return with_telegram_header(markdown, slug, artifact_type=artifact_type)


def ideas_header(n_shown: int, n_total: int) -> str:
    if n_total <= 0:
        return "no actionable setup"
    if n_shown < n_total:
        return f"{n_shown} ideas shown; {n_total - n_shown} cut (max 3)"
    return f"{n_shown} ideas"
