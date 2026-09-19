"""Ticker-reuse / entity-splice continuity check for Polygon equities series.

Polygon aggregates daily bars by **ticker string**. Resolving a ticker to a
qualified id (e.g. ``NASDAQ:SPCX`` → SpaceX) does **not** prove the returned
series belongs to that entity: the same string may previously have been a
different listing (SPCX was The SPAC and New Issue ETF before the 2026 IPO).

Principal 2026-09-19: N-sigma / 1.4826×MAD is a tail-insensitive scale.
Measuring a fat-tail equity day against it always yields a large multiple.
Retuning N is parameter fitting. **N-sigma is not a VOID decision.**

Three rules (A/B void; C flag only):

**A. Listing-date violation → VOID.** First bar precedes known ``listed_on``.
Deterministic. SPCX stays VOID under A.

**B. Sustained level shift → VOID.** This is what ticker reuse actually is.
Suspect-bar selection: scan **every** index ``i`` that has a full
``window`` bars strictly before and ``window`` bars strictly after
(default window=20). Do not invent a window. The reported suspect bar is
the scanned index whose ``median(close after) / median(close before)`` is
most extreme (max of ratio and 1/ratio). VOID if that ratio ``>= 3.0`` or
``<= 1/3``. Reuse = permanent level change; a crash/spike that reverts
does not. Fewer than 20 bars each side → skip B with reason, do not invent.

**C. Single-bar extreme → FLAG only, never VOID.** A flag is information; a
void is a decision. Optional diagnostic: log ``max |1-bar| / (1.4826×MAD)``
but that multiple **must not void**.

The adapter still returns raw bars (degrade-never-invent: do not silently
trim or invent a spliced-clean series). Callers that **compute or pool**
(Phase-1 instrument base rates) MUST exclude a **voided** series from the
void-excluded pool, and MUST keep a **flagged** series in the compute pool.
Paper only. Not a size. Not a call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from statistics import median
from typing import Any, Sequence

# Diagnostic only — 1.4826 ≈ 1 / Φ⁻¹(0.75): MAD → Gaussian-consistent sigma.
# MUST NOT decide VOID. Retuning a multiple of this scale is parameter fitting.
MAD_TO_SIGMA = 1.4826

LEVEL_SHIFT_WINDOW = 20
LEVEL_SHIFT_RATIO = 3.0
SINGLE_BAR_FLAG_ABS = 0.20  # |1-bar simple return| >= 20% → FLAG, never VOID

REASON_TICKER_REUSE = "suspected_ticker_reuse"
REASON_SINGLE_BAR_EXTREME = "single_bar_extreme"
TRIGGER_LISTING_DATE = "listing_date"
TRIGGER_LEVEL_SHIFT = "level_shift"
TRIGGER_SINGLE_BAR = "single_bar_extreme"
METHOD = "listing_date;level_shift_20_20;single_bar_flag"


@dataclass(frozen=True)
class ContinuityVerdict:
    void: bool
    flag: bool
    reason_code: str
    flag_code: str
    method: str
    detail: str
    n_bars: int
    first: date | None
    last: date | None
    listed_on: date | None
    robust_sigma: float | None
    max_abs_1bar: float | None
    max_abs_1bar_in_sigma: float | None
    level_shift_ratio: float | None
    level_shift_date: date | None
    level_shift_skip_reason: str | None
    triggers: tuple[str, ...]
    void_triggers: tuple[str, ...]
    flag_triggers: tuple[str, ...]

    @property
    def flagged(self) -> bool:
        """Legacy alias: True iff the series is VOID (rule A or B). Never C-only."""
        return self.void


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text[:10])


def _bar_date(bar: Any) -> date | None:
    if isinstance(bar, (tuple, list)) and bar:
        return _as_date(bar[0])
    d = getattr(bar, "date", None)
    if d is not None:
        return _as_date(d)
    mt = getattr(bar, "market_time", None)
    if mt is not None:
        return _as_date(mt)
    return None


def _bar_close(bar: Any) -> float | None:
    if isinstance(bar, (tuple, list)) and len(bar) >= 2:
        try:
            return float(bar[1])
        except (TypeError, ValueError):
            return None
    raw = getattr(bar, "close", None)
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _dated_closes(bars: Sequence[Any]) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    for bar in bars:
        d = _bar_date(bar)
        c = _bar_close(bar)
        if d is None or c is None:
            continue
        out.append((d, c))
    out.sort(key=lambda row: row[0])
    return out


def _robust_sigma(returns: Sequence[float]) -> float:
    if not returns:
        return 0.0
    mid = median(returns)
    mad = median([abs(r - mid) for r in returns])
    return MAD_TO_SIGMA * float(mad)


def _scan_level_shift(
    rows: Sequence[tuple[date, float]],
    *,
    window: int,
    ratio_cut: float,
) -> tuple[float | None, date | None, bool, str | None]:
    """Return (ratio, suspect_date, fired, skip_reason).

    Suspect bar = every index with a full ``window`` closes strictly before
    and strictly after is scanned. The reported bar is the most extreme
    ratio. Skip (do not invent) when no index has 20/20.
    """
    n = len(rows)
    if window <= 0:
        return None, None, False, "level-shift window is not positive"
    if n < 2 * window + 1:
        return None, None, False, f"fewer than {window} bars each side"

    best_ratio: float | None = None
    best_date: date | None = None
    best_extreme = 1.0
    fired = False
    eligible = 0
    for i in range(window, n - window):
        before = [rows[j][1] for j in range(i - window, i)]
        after = [rows[j][1] for j in range(i + 1, i + 1 + window)]
        if len(before) < window or len(after) < window:
            continue
        med_b = float(median(before))
        med_a = float(median(after))
        if med_b <= 0:
            continue
        eligible += 1
        ratio = med_a / med_b
        if ratio <= 0:
            continue
        extreme = max(ratio, 1.0 / ratio)
        if extreme >= best_extreme or best_ratio is None:
            best_extreme = extreme
            best_ratio = ratio
            best_date = rows[i][0]
        if ratio >= ratio_cut or ratio <= (1.0 / ratio_cut):
            fired = True
    if eligible == 0 or best_ratio is None:
        return None, None, False, f"fewer than {window} bars each side"
    return best_ratio, best_date, fired, None


def check_bar_continuity(
    bars: Sequence[Any],
    *,
    listed_on: date | None = None,
    level_shift_window: int = LEVEL_SHIFT_WINDOW,
    level_shift_ratio: float = LEVEL_SHIFT_RATIO,
    single_bar_flag_abs: float = SINGLE_BAR_FLAG_ABS,
) -> ContinuityVerdict:
    """Return a verdict for a dated close series (script ``Bar`` or ``OHLCVBar``).

    N-sigma / MAD is computed as a diagnostic on max |1-bar| only. It never
    voids. Pass ``listed_on`` for rule A. Rules B and C always run.
    """
    rows = _dated_closes(bars)
    n = len(rows)
    first = rows[0][0] if rows else None
    last = rows[-1][0] if rows else None
    returns: list[float] = []
    for i in range(1, n):
        prev = rows[i - 1][1]
        if prev > 0:
            returns.append(rows[i][1] / prev - 1.0)
    max_abs = max((abs(r) for r in returns), default=None)
    sigma = _robust_sigma(returns) if returns else None
    sigma_mult = None
    if max_abs is not None and sigma and sigma > 0:
        sigma_mult = max_abs / sigma

    ratio, shift_date, shift_fired, shift_skip = _scan_level_shift(
        rows,
        window=int(level_shift_window),
        ratio_cut=float(level_shift_ratio),
    )

    void_triggers: list[str] = []
    flag_triggers: list[str] = []
    if listed_on is not None and first is not None and first < listed_on:
        void_triggers.append(TRIGGER_LISTING_DATE)
    if shift_fired:
        void_triggers.append(TRIGGER_LEVEL_SHIFT)
    if max_abs is not None and max_abs >= float(single_bar_flag_abs):
        flag_triggers.append(TRIGGER_SINGLE_BAR)

    void = bool(void_triggers)
    flag = bool(flag_triggers)
    bits: list[str] = []
    if TRIGGER_LISTING_DATE in void_triggers:
        bits.append(
            f"rule A listing-date: first bar {first.isoformat() if first else 'n/a'} precedes "
            f"known listing {listed_on.isoformat() if listed_on else 'n/a'} (bar count {n})"
        )
    if TRIGGER_LEVEL_SHIFT in void_triggers:
        bits.append(
            f"rule B sustained level-shift: median({level_shift_window} after)/"
            f"median({level_shift_window} before)={ratio:.4f} on suspect bar "
            f"{shift_date.isoformat() if shift_date else 'n/a'} "
            f"(scan every index with a full {level_shift_window}/{level_shift_window} "
            f"window; VOID if ratio >= {level_shift_ratio:g} or <= {1.0 / level_shift_ratio:g})"
        )
    elif shift_skip:
        bits.append(f"rule B skipped: {shift_skip}")
    elif ratio is not None:
        bits.append(
            f"rule B clear: most-extreme 20/20 median ratio={ratio:.4f} "
            f"(suspect bar {shift_date.isoformat() if shift_date else 'n/a'}; cut {level_shift_ratio:g})"
        )
    if TRIGGER_SINGLE_BAR in flag_triggers:
        sigma_bit = (
            f"; robust-sigma multiple {sigma_mult:.2f} (diagnostic only, not a void)"
            if sigma_mult is not None
            else "; robust-sigma multiple n/a (diagnostic only, not a void)"
        )
        bits.append(
            f"rule C single-bar FLAG: max |1-bar|={max_abs:.4f} "
            f"(>= {single_bar_flag_abs:g}; stays in compute pool){sigma_bit}"
        )
    if not bits:
        bits.append("clears listing-date and 20/20 level-shift; no single-bar FLAG")
    detail = "; ".join(bits)
    return ContinuityVerdict(
        void=void,
        flag=flag,
        reason_code=REASON_TICKER_REUSE if void else "",
        flag_code=REASON_SINGLE_BAR_EXTREME if flag else "",
        method=METHOD,
        detail=detail,
        n_bars=n,
        first=first,
        last=last,
        listed_on=listed_on,
        robust_sigma=sigma,
        max_abs_1bar=max_abs,
        max_abs_1bar_in_sigma=sigma_mult,
        level_shift_ratio=ratio,
        level_shift_date=shift_date,
        level_shift_skip_reason=shift_skip,
        triggers=tuple(void_triggers + [t for t in flag_triggers if t not in void_triggers]),
        void_triggers=tuple(void_triggers),
        flag_triggers=tuple(flag_triggers),
    )


def check_ohlcv_continuity(
    bars: Sequence[Any],
    *,
    listed_on: date | None = None,
    level_shift_window: int = LEVEL_SHIFT_WINDOW,
    level_shift_ratio: float = LEVEL_SHIFT_RATIO,
    single_bar_flag_abs: float = SINGLE_BAR_FLAG_ABS,
) -> ContinuityVerdict:
    """Adapter-facing alias. Same check as :func:`check_bar_continuity`."""
    return check_bar_continuity(
        bars,
        listed_on=listed_on,
        level_shift_window=level_shift_window,
        level_shift_ratio=level_shift_ratio,
        single_bar_flag_abs=single_bar_flag_abs,
    )
