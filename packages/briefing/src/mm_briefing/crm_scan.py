"""Chart's watchlist CRM scan as one section of the Sydney morning brief.

Data and awareness only. Not a trade instruction. Words, sigma and percent
only: no entry, stop, target, R:R, price or level is ever rendered.

``apply_crm_scan(markdown, None)`` returns the brief byte-for-byte. The
section is added only when a caller passes a scan (``lab brief close
--crm-scan PATH``). A missing, unreadable, stale, malformed, or level-shaped
scan renders one line, ``CRM scan unavailable (<reason>)``. It never raises
and never blocks the brief.

Spec: ``docs/specs/crm-brief-section.md``. Freeze: not on the 06:30 path
before capture 11 (Mon 12 Oct 2026) has scored.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mm_common.time import as_utc, parse_utc
from mm_briefing.schedule import SYDNEY_TZ

# Lockstep with ``mm_briefing.morning.PHONE_LINE_MAX``. Asserted equal in tests.
PHONE_LINE_MAX = 42
SCHEMA = "crm-scan/v1"
UNAVAILABLE = "CRM scan unavailable"
# A scan older than this at render time is stale. Chart's manual scan runs
# overnight Sydney; 12h covers a scan taken after ~18:30 AEDT the night before.
MAX_AGE = timedelta(hours=12)
# A scan stamped later than render time (clock skew allowance) is rejected.
MAX_FUTURE_SKEW = timedelta(minutes=5)
COMPACT_MAX_LINES = 8
NEAREST_MAX = 5

FORMING_LINE = "Forming bars UNREAD. Not backtested."
FULL_CAVEAT = (
    "Forming-bar signals UNREAD. BUY->26w counts are on-screen history only, "
    "not a backtest. Data only, not a trade instruction."
)

# Free text (symbols, regime words, notes) may not carry a digit, a currency
# sign, or a level word. Numbers only come from typed fields the renderer formats.
_TEXT_RE = re.compile(r"^[A-Za-z][A-Za-z .\-/]{0,23}$")
_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9]{0,11}(-P)?$")
_BANNED_WORDS = (
    "entry",
    "entries",
    "stop",
    "stops",
    "sl",
    "tp",
    "target",
    "targets",
    "take profit",
    "r:r",
    "rr",
    "risk/reward",
    "risk reward",
    "level",
    "levels",
    "band",
    "bands",
    "long position",
    "short position",
    "position tool",
    "drawing",
    "drawings",
    "invalidation",
    "limit",
    "buy at",
    "sell at",
    "price",
)
_BANNED_RE = re.compile(
    r"(?<![A-Za-z])(" + "|".join(re.escape(word) for word in _BANNED_WORDS) + r")(?![A-Za-z])",
    re.IGNORECASE,
)
_CURRENCY_RE = re.compile(r"[$€£¥₩]|\bUSD\b|\bUSDT\b|\bUSDC\b")
# Numeric tokens that may appear in a rendered CRM line.
_ALLOWED_NUMBER_RES = (
    re.compile(r"^[+\-]?\d+(\.\d+)?σ$"),  # sigma vs 1Y VWAP
    re.compile(r"^[+\-]?\d+(\.\d+)?%$"),  # percent
    re.compile(r"^(\d{1,2}|100)$"),  # CR score 0..100, integer only
    re.compile(r"^n\d{1,3}$"),  # signal count
    re.compile(r"^\d{1,2}w$"),  # weeks
    re.compile(r"^(1W|3D)$"),  # timeframe
    re.compile(r"^\d{2}:\d{2}$"),  # scan clock, heading only
)
_NUMERIC_TOKEN_RE = re.compile(r"[+\-]?[A-Za-z]*\d[\w.:%σ]*")


class CrmScanError(ValueError):
    """The scan cannot be shown. ``reason`` is the short word on the unavailable line."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(detail or reason)
        self.reason = reason


@dataclass(frozen=True)
class CrmRow:
    symbol: str
    cr: int | None
    label: str | None
    sigma: float | None
    to_deep_value_pct: float | None
    below_realized: bool = False
    buy_26w_n: int | None = None
    buy_26w_pct: float | None = None
    buy_26w_hit_pct: float | None = None


@dataclass(frozen=True)
class CrmScan:
    captured_at: datetime
    timeframe: str
    nearest: tuple[CrmRow, ...]
    warming: tuple[CrmRow, ...]
    stretched: tuple[CrmRow, ...]
    stretched_notes: dict[str, str]
    insufficient: tuple[str, ...]
    symbols_scanned: int | None = None


@dataclass(frozen=True)
class CrmUnavailable:
    reason: str


# ---------------------------------------------------------------------------
# Level-free guard


def level_free(line: str) -> bool:
    """True when a rendered line carries no level-shaped value.

    Rejects a currency sign or quote-currency word, a banned level word, and
    any numeric token that is not sigma, percent, a 0..100 CR score, a count,
    weeks, a timeframe, or the scan clock.
    """
    if _CURRENCY_RE.search(line):
        return False
    if _BANNED_RE.search(line):
        return False
    for token in _NUMERIC_TOKEN_RE.findall(line):
        token = token.rstrip(".,;:)")
        if not any(rx.match(token) for rx in _ALLOWED_NUMBER_RES):
            # Fails safe: a digit-bearing ticker also trips this and the
            # section degrades to the unavailable line.
            return False
    return True


def _check_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CrmScanError("malformed", f"{field} is not text")
    text = value.strip()
    if not _TEXT_RE.match(text) or _BANNED_RE.search(text) or _CURRENCY_RE.search(text):
        raise CrmScanError("level guard", f"{field} not level-free: {text!r}")
    return text


def _check_symbol(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CrmScanError("malformed", f"{field} is not text")
    symbol = value.strip().upper()
    if not _SYMBOL_RE.match(symbol):
        raise CrmScanError("level guard", f"{field} not a short symbol: {value!r}")
    return symbol


def _check_number(value: Any, field: str, *, lo: float, hi: float, integer: bool = False) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CrmScanError("malformed", f"{field} is not a number")
    number = float(value)
    if not math.isfinite(number) or number < lo or number > hi:
        raise CrmScanError("level guard", f"{field} out of range: {value!r}")
    if integer:
        if number != int(number):
            raise CrmScanError("level guard", f"{field} is not an integer: {value!r}")
        return int(number)
    return number


# ---------------------------------------------------------------------------
# Load


def load_crm_scan(path: Path | str | None) -> CrmScan | CrmUnavailable:
    """Read the scan sidecar. Never raises."""
    if path is None:
        return CrmUnavailable("missing")
    target = Path(path)
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return CrmUnavailable("missing")
    try:
        data = json.loads(text)
    except ValueError:
        return CrmUnavailable("malformed")
    try:
        return parse_crm_scan(data)
    except CrmScanError as exc:
        return CrmUnavailable(exc.reason)


def parse_crm_scan(data: Any) -> CrmScan:
    if not isinstance(data, dict):
        raise CrmScanError("malformed", "scan is not an object")
    if data.get("schema") != SCHEMA:
        raise CrmScanError("malformed", f"schema is not {SCHEMA}")
    if str(data.get("forming_bar") or "").upper() != "UNREAD":
        # Forming-bar shapes are never read into the brief.
        raise CrmScanError("malformed", "forming_bar must be UNREAD")
    try:
        captured = as_utc(parse_utc(str(data.get("captured_at") or "")))
    except (TypeError, ValueError):
        raise CrmScanError("malformed", "captured_at") from None
    timeframe = str(data.get("timeframe") or "1W")
    if timeframe not in {"1W", "3D"}:
        raise CrmScanError("malformed", "timeframe")
    nearest = tuple(_row(item, f"nearest[{i}]") for i, item in enumerate(_list(data, "nearest")))
    warming = tuple(_row(item, f"warming[{i}]") for i, item in enumerate(_list(data, "warming")))
    stretched_raw = _list(data, "stretched")
    stretched = tuple(_row(item, f"stretched[{i}]") for i, item in enumerate(stretched_raw))
    notes: dict[str, str] = {}
    for row, item in zip(stretched, stretched_raw):
        note = item.get("note") if isinstance(item, dict) else None
        if note:
            notes[row.symbol] = _check_text(note, f"stretched[{row.symbol}].note")
    insufficient = tuple(_check_symbol(item, "insufficient") for item in _list(data, "insufficient"))
    scanned = _check_number(data.get("symbols_scanned"), "symbols_scanned", lo=0, hi=999, integer=True)
    if not nearest:
        raise CrmScanError("empty", "no full CRM readings")
    return CrmScan(
        captured_at=captured,
        timeframe=timeframe,
        nearest=nearest,
        warming=warming,
        stretched=stretched,
        stretched_notes=notes,
        insufficient=insufficient,
        symbols_scanned=scanned,  # type: ignore[arg-type]
    )


def _list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key) or []
    if not isinstance(value, list):
        raise CrmScanError("malformed", f"{key} is not a list")
    return value


def _row(item: Any, field: str) -> CrmRow:
    if not isinstance(item, dict):
        raise CrmScanError("malformed", f"{field} is not an object")
    allowed = {
        "symbol",
        "cr",
        "label",
        "sigma",
        "to_deep_value_pct",
        "below_realized",
        "buy_26w_n",
        "buy_26w_pct",
        "buy_26w_hit_pct",
        "note",
    }
    extra = set(item) - allowed
    if extra:
        # An unknown key could carry a level. Reject rather than ignore.
        raise CrmScanError("level guard", f"{field} has unknown keys {sorted(extra)}")
    label = item.get("label")
    return CrmRow(
        symbol=_check_symbol(item.get("symbol"), f"{field}.symbol"),
        cr=_check_number(item.get("cr"), f"{field}.cr", lo=0, hi=100, integer=True),  # type: ignore[arg-type]
        label=_check_text(label, f"{field}.label") if label is not None else None,
        sigma=_check_number(item.get("sigma"), f"{field}.sigma", lo=-20, hi=20),  # type: ignore[arg-type]
        to_deep_value_pct=_check_number(
            item.get("to_deep_value_pct"), f"{field}.to_deep_value_pct", lo=-100, hi=100
        ),  # type: ignore[arg-type]
        below_realized=bool(item.get("below_realized") is True),
        buy_26w_n=_check_number(item.get("buy_26w_n"), f"{field}.buy_26w_n", lo=0, hi=999, integer=True),  # type: ignore[arg-type]
        buy_26w_pct=_check_number(item.get("buy_26w_pct"), f"{field}.buy_26w_pct", lo=-100, hi=1000),  # type: ignore[arg-type]
        buy_26w_hit_pct=_check_number(item.get("buy_26w_hit_pct"), f"{field}.buy_26w_hit_pct", lo=0, hi=100),  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# Render


def fmt_sigma(value: float) -> str:
    return f"{value:+.2f}σ"


def fmt_dv(value: float | None) -> str:
    if value is None:
        return "DV n/a"
    return f"{abs(value):.1f}% to DV"


def crm_section_lines(
    scan: CrmScan | CrmUnavailable | None,
    *,
    generated_at: datetime,
    compact: bool = True,
) -> list[str]:
    """Lines for the section. ``[]`` when no scan was requested. Never raises."""
    if scan is None:
        return []
    try:
        if isinstance(scan, CrmUnavailable):
            return [f"{UNAVAILABLE} ({scan.reason})"]
        age = as_utc(generated_at) - scan.captured_at
        if age > MAX_AGE:
            return [f"{UNAVAILABLE} (stale)"]
        if age < -MAX_FUTURE_SKEW:
            return [f"{UNAVAILABLE} (future stamp)"]
        lines = _compact_lines(scan) if compact else _full_lines(scan)
        if any(len(line) > PHONE_LINE_MAX for line in lines):
            return [f"{UNAVAILABLE} (width)"]
        if not all(level_free(line) for line in lines):
            return [f"{UNAVAILABLE} (level guard)"]
        if compact and len(lines) > COMPACT_MAX_LINES:
            return [f"{UNAVAILABLE} (length)"]
        return lines
    except Exception:  # never block the brief
        return [f"{UNAVAILABLE} (error)"]


def _clock(scan: CrmScan) -> str:
    syd = scan.captured_at.astimezone(SYDNEY_TZ)
    return f"{syd.strftime('%H:%M')} {syd.tzname() or 'SYD'}"


def _row_line(row: CrmRow, *, star: bool) -> str:
    mark = "*" if star and row.below_realized else ""
    parts = [f"{row.symbol}{mark}"]
    if row.cr is not None:
        parts.append(str(row.cr))
    if row.label:
        parts.append(row.label)
    if row.sigma is not None:
        parts.append(fmt_sigma(row.sigma))
    parts.append(fmt_dv(row.to_deep_value_pct))
    return " ".join(parts)


def _stretched_bits(scan: CrmScan) -> list[str]:
    bits: list[str] = []
    for row in scan.stretched:
        if row.cr is not None and row.label:
            bits.append(f"{row.symbol} {row.cr} {row.label}")
        elif row.sigma is not None:
            bits.append(f"{row.symbol} {fmt_sigma(row.sigma)}")
        else:
            bits.append(row.symbol)
    return bits


def _compact_lines(scan: CrmScan) -> list[str]:
    lines = [f"CRM {scan.timeframe}, DV=deep value (Chart {_clock(scan)})"]
    rows = [row for row in scan.nearest if row.to_deep_value_pct is not None][: NEAREST_MAX - 1]
    lines.extend(_row_line(row, star=True) for row in rows)
    bits = _stretched_bits(scan)
    if bits:
        stretched = "Stretched: " + bits[0]
        for bit in bits[1:]:
            trial = f"{stretched}, {bit}"
            if len(trial) > PHONE_LINE_MAX:
                break
            stretched = trial
        lines.append(stretched)
    footer = FORMING_LINE
    if any(row.below_realized for row in rows):
        starred = "*below realized. " + FORMING_LINE.split(". ")[0] + "."
        lines.append(starred)
        footer = "Not backtested. Not a trade instruction."
    lines.append(footer)
    return lines[:COMPACT_MAX_LINES]


def _full_lines(scan: CrmScan) -> list[str]:
    head = f"CRM {scan.timeframe} watch, data only"
    sub = f"Chart scan {_clock(scan)}"
    if scan.symbols_scanned:
        sub += f", n{scan.symbols_scanned}"
    lines = [head, sub, "Nearest deep value (DV):"]
    shown = scan.nearest[:NEAREST_MAX]
    for row in shown:
        lines.append(_row_line(row, star=True))
        if row.buy_26w_n is not None:
            stats = [f" BUY->26w n{row.buy_26w_n}"]
            if row.buy_26w_pct is not None:
                stats.append(f"{row.buy_26w_pct:+.0f}%")
            if row.buy_26w_hit_pct is not None:
                stats.append(f"{row.buy_26w_hit_pct:.0f}% hit")
            lines.append(" ".join(stats))
    if any(row.below_realized for row in shown):
        lines.append("*below realized")
    if scan.warming:
        lines.append("Perps warming up, no score:")
        lines.extend(_wrap_bits([f"{r.symbol} {fmt_sigma(r.sigma)}" for r in scan.warming if r.sigma is not None]))
    bits = _stretched_bits(scan)
    if bits:
        for row in scan.stretched:
            note = scan.stretched_notes.get(row.symbol)
            if note:
                bits = [f"{b} ({note})" if b.startswith(row.symbol + " ") and row.cr is not None else b for b in bits]
        lines.append("Stretched:")
        lines.extend(_wrap_bits(bits))
    if scan.insufficient:
        lines.append("Thin history (no σ):")
        lines.extend(_wrap_bits(list(scan.insufficient), sep=" "))
    lines.extend(_wrap_text(FULL_CAVEAT))
    return lines


def _wrap_bits(bits: list[str], *, sep: str = ", ") -> list[str]:
    out: list[str] = []
    current = ""
    for bit in bits:
        trial = bit if not current else f"{current}{sep}{bit}"
        if len(" " + trial) <= PHONE_LINE_MAX:
            current = trial
        else:
            if current:
                out.append(" " + current)
            current = bit
    if current:
        out.append(" " + current)
    return out


def _wrap_text(text: str) -> list[str]:
    words = text.split(" ")
    out: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if len(trial) <= PHONE_LINE_MAX:
            current = trial
        else:
            out.append(current)
            current = word
    if current:
        out.append(current)
    return out


# ---------------------------------------------------------------------------
# Insert into the brief


def apply_crm_scan(
    markdown: str,
    scan: CrmScan | CrmUnavailable | None,
    *,
    generated_at: datetime,
    compact: bool = True,
) -> str:
    """Append the section as the last block inside the brief's code fence.

    ``scan=None`` returns ``markdown`` unchanged. Any failure returns either
    the unavailable line or the original markdown; it never raises.
    """
    if scan is None:
        return markdown
    try:
        section = crm_section_lines(scan, generated_at=generated_at, compact=compact)
        if not section:
            return markdown
        start = markdown.find("```\n")
        if start < 0:
            return markdown
        body_start = start + len("```\n")
        end = markdown.find("\n```", body_start)
        if end < 0:
            return markdown
        body = markdown[body_start:end].rstrip("\n")
        block = "\n".join(section)
        return markdown[:body_start] + body + "\n\n" + block + markdown[end:]
    except Exception:
        return markdown
