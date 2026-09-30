"""Print rank-eligible equity closes from retain envelopes already in hand.

The lines are display only. They are not a rank, a size, or an order.
No second Polygon GET and no Neon read happen here. The clock is
``payload.session_date`` plus ``market_time``. ``as_of_knowledge`` is ingest
time and is not the equity session.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from mm_briefing.divergences import fmt_pct, fmt_px
from mm_common.time import as_utc, parse_utc

# Lockstep with ``mm_briefing.morning.PHONE_LINE_MAX``. The morning module
# stays untouched; this copy is asserted equal in tests.
PHONE_LINE_MAX = 42

# ``config/ingest/mvp_retain.yaml`` polygon.tickers minus QQQ (already the NQ row).
RANK_ELIGIBLE_EQUITIES: tuple[str, ...] = (
    "CRCL",
    "TSLA",
    "SPCX",
    "NVDA",
    "BB",
    "GLXY",
    "IBIT",
    "BMNR",
    "MRNA",
    "GOOG",
    "HOOD",
    "NOW",
    "CBRS",
    "MSTR",
    "STRC",
    "AMD",
)
_RANK = frozenset(RANK_ELIGIBLE_EQUITIES)
_RESOLUTIONS = frozenset({"grouped_daily", "grouped_daily_prior_session"})
_PROOF = "proof"

_STOP_HEADS = frozenset(
    {
        "SPY",
        "QQQ",
        "US10Y",
        "UUP",
        "USO",
        "VIX",
        "BTC",
        "ETH",
        "SOL",
        "HYPE",
        "NEAR",
        "ARB",
        "UNI",
        "VVV",
        "ZEC",
        "DOGE",
        "XMR",
        "CHIP",
        "LTC",
        "PURR",
        "UTC",
        "NY",
        "SYD",
        "Health",
        "EQUITY",
        "US",
        "obs",
        "Positioning",
        "Unexpected",
        "Lab",
        "Assumptions",
        "Catalysts",
    }
)
_SECTIONS = ("Unexpected", "Lab hooks", "Assumptions", "Catalysts")


@dataclass(frozen=True)
class EquityClosePrint:
    """Lines that qualified, and rank-eligible names that did not."""

    lines: tuple[str, ...]
    missing: tuple[str, ...]


def load_equity_capture_file(path: Path) -> dict[str, Any]:
    """Read a runner temp file. Does not fetch and does not open Neon."""
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, list):
        return {"envelopes": data}
    if isinstance(data, dict) and isinstance(data.get("envelopes"), list):
        return data
    raise ValueError("equity capture file must be a list or an object with envelopes")


def write_equity_capture_file(path: Path, envelopes: Any) -> None:
    """Write polygon ``close`` rows from envelopes already built. Not a git commit."""
    rows: list[dict[str, Any]] = []
    for item in envelopes or ():
        row = _dump_row(item)
        if row is None or not _is_polygon_close(row):
            continue
        rows.append(row)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps({"envelopes": rows}, separators=(",", ":"))
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(blob, encoding="utf-8")
    temporary.replace(target)


class EquityCaptureWriter:
    """Delegating store. Dumps in-memory closes, then persists.

    A dump error does not skip the persist. A missing file leaves the brief
    body unchanged.
    """

    def __init__(self, inner: Any, path: Path) -> None:
        self._inner = inner
        self._path = Path(path)

    def persist(self, envelopes: Any) -> Any:
        try:
            write_equity_capture_file(self._path, envelopes)
        except Exception:
            pass
        return self._inner.persist(envelopes)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def equity_close_print(envelopes: Any, *, header_date: date) -> EquityClosePrint:
    """Format the 16 names. First qualifying row for a ticker wins.

    A name is printed only when ``metric`` is ``close``, ``payload.value`` is
    present, ``resolution`` is a grouped-daily resolution, ``payload.session_date``
    equals ``market_time``'s calendar date, and that date equals ``header_date``
    (the T-1 date from ``expected_equity_session``). Anything else is a gap.
    QQQ is not printed again. A missing prior close prints the level only.
    """
    rows, prior_rows = _split_input(envelopes)
    priors = _prior_prices(prior_rows, header_date=header_date)
    chosen: dict[str, str] = {}
    for row in rows:
        parsed = _qualify(row, header_date=header_date)
        if parsed is None:
            continue
        ticker, value = parsed
        if ticker in chosen:
            continue
        line = _format_line(ticker, value, _prior_for(row, ticker, priors, session_date=header_date))
        if line is None:
            continue
        chosen[ticker] = line
    lines = tuple(chosen[ticker] for ticker in RANK_ELIGIBLE_EQUITIES if ticker in chosen)
    missing = tuple(ticker for ticker in RANK_ELIGIBLE_EQUITIES if ticker not in chosen)
    return EquityClosePrint(lines=lines, missing=missing)


def apply_equity_close(markdown: str, envelopes: Any, *, header_date: date) -> str:
    """Insert qualified lines after SPY/QQQ and append missing names to ``gaps:``."""
    printed = equity_close_print(envelopes, header_date=header_date)
    if not printed.lines and not printed.missing:
        return markdown
    parts = _split_fence(markdown)
    if parts is None:
        return markdown
    prefix, lines, suffix = parts
    if printed.lines:
        at = _price_insert_at(lines)
        lines[at:at] = list(printed.lines)
    if printed.missing:
        _merge_gaps(lines, printed.missing)
    return prefix + "\n".join(lines) + suffix


def _dump_row(item: Any) -> dict[str, Any] | None:
    if isinstance(item, dict):
        return item
    dump = getattr(item, "model_dump", None)
    if dump is None:
        return None
    row = dump(mode="json")
    if not isinstance(row, dict):
        return None
    return row


def _is_polygon_close(row: dict[str, Any]) -> bool:
    if str(row.get("metric") or "") != "close":
        return False
    if str(row.get("source_name") or "") != "polygon":
        return False
    return True


def _split_input(envelopes: Any) -> tuple[list[Any], list[Any]]:
    if isinstance(envelopes, dict):
        rows = envelopes.get("envelopes")
        priors = envelopes.get("priors")
        return (
            list(rows) if isinstance(rows, list) else [],
            list(priors) if isinstance(priors, list) else [],
        )
    if isinstance(envelopes, (list, tuple)):
        return list(envelopes), []
    return [], []


def _qualify(row: Any, *, header_date: date) -> tuple[str, float] | None:
    if not isinstance(row, dict):
        return None
    ticker = str(row.get("instrument") or "").upper()
    if ticker not in _RANK:
        return None
    source = row.get("source_name")
    if source not in (None, "polygon"):
        return None
    url = row.get("source_url_or_id")
    if url not in (None, "") and not str(url).startswith("grouped_daily:"):
        return None
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    if not _metric_is_close(row.get("metric"), payload.get("metric")):
        return None
    if str(payload.get("capture_kind") or "") == _PROOF:
        return None
    if payload.get("resolution") not in _RESOLUTIONS:
        return None
    session = _parse_date(payload.get("session_date"))
    if session is None or session != header_date:
        return None
    market = _market_date(row.get("market_time"))
    if market is None or market != session:
        return None
    value = _parse_price(payload.get("value"))
    if value is None:
        return None
    return ticker, value


def _metric_is_close(top: Any, inner: Any) -> bool:
    if top is not None and str(top) != "close":
        return False
    if inner is not None and str(inner) != "close":
        return False
    return top is not None or inner is not None


def _prior_for(row: dict[str, Any], ticker: str, priors: dict[str, float], *, session_date: date) -> float | None:
    dated = _parse_date(row.get("prior_session_date"))
    market = _market_date(row.get("prior_market_time")) if row.get("prior_market_time") not in (None, "") else None
    if dated is not None and dated >= session_date:
        return None
    if market is not None and market >= session_date:
        return None
    direct = _parse_price(row.get("prior_value"))
    if direct is not None:
        return direct
    return priors.get(ticker)


def _prior_prices(rows: list[Any], *, header_date: date) -> dict[str, float]:
    """Prior closes the caller already put in the file. A later bar is ignored."""
    found: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("instrument") or "").upper()
        if ticker not in _RANK:
            continue
        if str(row.get("metric") or "close") != "close":
            continue
        session = _parse_date(row.get("session_date"))
        market = _market_date(row.get("market_time")) if row.get("market_time") not in (None, "") else None
        if session is not None and session >= header_date:
            continue
        if market is not None and market >= header_date:
            continue
        if session is not None and market is not None and session != market:
            continue
        price = _parse_price(row.get("value"))
        if price is None or ticker in found:
            continue
        found[ticker] = price
    return found


def _format_line(ticker: str, value: float, prior: float | None) -> str | None:
    head = f"{ticker} {fmt_px(value)}"
    if len(head) > PHONE_LINE_MAX:
        return None
    pct = _percent(value, prior)
    if pct is None:
        return head
    full = f"{head} {pct}"
    if len(full) <= PHONE_LINE_MAX:
        return full
    return head


def _percent(value: float, prior: float | None) -> str | None:
    if prior is None or prior == 0:
        return None
    return fmt_pct((value - prior) / prior * 100.0)


def _parse_price(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        value = text
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        try:
            return as_utc(value).date()
        except ValueError:
            return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _market_date(value: Any) -> date | None:
    """UTC calendar date. Same rule as the morning observation date. Not NY wall time."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        try:
            return as_utc(value).date()
        except ValueError:
            return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if "T" in text or text.endswith("Z") or "+" in text[10:] or "-" in text[10:]:
        try:
            return parse_utc(text).date()
        except (TypeError, ValueError):
            return None
    return _parse_date(text)


def _split_fence(markdown: str) -> tuple[str, list[str], str] | None:
    start = markdown.find("```\n")
    if start < 0:
        return None
    body_start = start + len("```\n")
    end = markdown.find("\n```", body_start)
    if end < 0:
        return None
    body = markdown[body_start:end]
    return markdown[:body_start], body.split("\n"), markdown[end:]


def _price_insert_at(lines: list[str]) -> int:
    for head in ("QQQ", "SPY"):
        idx = _first_row(lines, head)
        if idx is None:
            continue
        cursor = idx + 1
        while cursor < len(lines) and lines[cursor] and not _stops(lines[cursor]):
            cursor += 1
        return cursor
    for head in ("US10Y", "UUP", "USO", "VIX", "BTC", "ETH", "SOL", "Positioning"):
        idx = _first_row(lines, head)
        if idx is not None:
            return idx
    span = _gaps_span(lines)
    if span is not None:
        return span[0]
    return len(lines)


def _stops(line: str) -> bool:
    if line.startswith("gaps:"):
        return True
    if _is_section_line(line):
        return True
    return line.split(" ", 1)[0] in _STOP_HEADS


def _is_section_line(line: str) -> bool:
    return line in _SECTIONS or any(line.startswith(name + " ") for name in _SECTIONS)


def _first_row(lines: list[str], head: str) -> int | None:
    prefix = head + " "
    for index, line in enumerate(lines):
        if line == head or line.startswith(prefix):
            return index
    return None


def _gaps_span(lines: list[str]) -> tuple[int, int] | None:
    for index, line in enumerate(lines):
        if line.startswith("gaps:"):
            end = index + 1
            while end < len(lines) and _is_gap_continuation(lines[end]):
                end += 1
            return index, end
    return None


def _is_gap_continuation(line: str) -> bool:
    """A wrapped ``gaps:`` piece. A sentence such as a trade-status line is not one."""
    if not line or line.startswith("gaps:") or _is_section_line(line):
        return False
    parts = [part.strip() for part in line.split(",")]
    if not parts or any(not part for part in parts):
        return False
    for part in parts:
        if part.endswith(" 24h"):
            symbol = part[: -len(" 24h")].strip()
            if symbol.isalnum() and symbol.isupper():
                continue
            return False
        if part.isalnum() and part.isupper():
            continue
        return False
    return True


def _merge_gaps(lines: list[str], missing: tuple[str, ...]) -> None:
    span = _gaps_span(lines)
    if span is None:
        wrapped = _wrap_gaps(_append_tokens([], missing))
        _insert_new_gaps(lines, wrapped)
        return
    start, end = span
    tokens = _gap_tokens(lines[start:end])
    merged = _append_tokens(tokens, missing)
    if merged == tokens:
        return
    lines[start:end] = _wrap_gaps(merged)


def _append_tokens(tokens: list[str], missing: tuple[str, ...]) -> list[str]:
    seen = set(tokens)
    out = list(tokens)
    for name in missing:
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _gap_tokens(block: list[str]) -> list[str]:
    text = " ".join(line.strip() for line in block)
    if text.startswith("gaps:"):
        text = text[len("gaps:") :]
    return [part.strip() for part in text.split(",") if part.strip()]


def _wrap_gaps(tokens: list[str]) -> list[str]:
    return _wrap_line("gaps: " + ", ".join(tokens))


def _insert_new_gaps(lines: list[str], wrapped: list[str]) -> None:
    positioning = _first_row(lines, "Positioning")
    if positioning is not None:
        end = positioning + 1
        while end < len(lines) and lines[end] and not _is_section_line(lines[end]):
            if lines[end].startswith("gaps:"):
                break
            end += 1
        lines[end:end] = wrapped
        return
    for index, line in enumerate(lines):
        if _is_section_line(line):
            at = index - 1 if index > 0 and lines[index - 1] == "" else index
            lines[at:at] = [*wrapped, ""]
            return
    if lines and lines[-1] != "":
        lines.append("")
    lines.extend(wrapped)


def _wrap_line(text: str, width: int = PHONE_LINE_MAX) -> list[str]:
    raw = text.rstrip()
    if raw == "":
        return [""]
    if len(raw) <= width:
        return [raw]
    words = [word for word in raw.split(" ") if word]
    wrapped: list[str] = []
    current = ""
    for word in words:
        while len(word) > width:
            if current:
                wrapped.append(current)
                current = ""
            wrapped.append(word[:width])
            word = word[width:]
        if not word:
            continue
        trial = word if not current else f"{current} {word}"
        if len(trial) <= width:
            current = trial
        else:
            if current:
                wrapped.append(current)
            current = word
    if current:
        wrapped.append(current)
    return wrapped or [""]
