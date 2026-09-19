"""Ticker-reuse / entity-splice continuity check for Polygon equities series.

Polygon aggregates daily bars by **ticker string**. Resolving a ticker to a
qualified id (e.g. ``NASDAQ:SPCX`` → SpaceX) does **not** prove the returned
series belongs to that entity: the same string may previously have been a
different listing (SPCX was The SPAC and New Issue ETF before the 2026 IPO).

A series is flagged ``suspected_ticker_reuse`` when either:

1. **Listing date.** Any bar (including the first) precedes the instrument's
   known identity-start / listing date.
2. **N-sigma jump.** A single-bar simple return exceeds ``N`` robust-sigma,
   with ``N = 8`` and ``sigma = 1.4826 * MAD(1-bar simple returns)``.
   If MAD is 0 (flat / illiquid tape) any ``|r| > 5%`` is also a flag — the
   splice signature of a dead ETF tape then a new listing.

The adapter still returns raw bars (degrade-never-invent: do not silently
trim or invent a spliced-clean series). Callers that **compute or pool**
(Phase-1 instrument base rates) MUST exclude a flagged series from those
pools. Paper only. Not a size. Not a call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from statistics import median
from typing import Any, Sequence

CONTINUITY_N_SIGMA = 8.0
# 1.4826 ≈ 1 / Φ⁻¹(0.75): MAD → Gaussian-consistent sigma.
MAD_TO_SIGMA = 1.4826
# When MAD is 0, a jump this large is still a splice flag (not ordinary noise).
MAD_ZERO_ABS_FLOOR = 0.05
REASON_TICKER_REUSE = "suspected_ticker_reuse"


@dataclass(frozen=True)
class ContinuityVerdict:
    flagged: bool
    reason_code: str
    method: str
    detail: str
    n_bars: int
    first: date | None
    last: date | None
    listed_on: date | None
    n_sigma: float
    robust_sigma: float | None
    max_abs_1bar: float | None
    max_abs_1bar_in_sigma: float | None
    triggers: tuple[str, ...]


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


def check_bar_continuity(
    bars: Sequence[Any],
    *,
    listed_on: date | None = None,
    n_sigma: float = CONTINUITY_N_SIGMA,
    mad_zero_abs_floor: float = MAD_ZERO_ABS_FLOOR,
) -> ContinuityVerdict:
    """Return a verdict for a dated close series (script ``Bar`` or ``OHLCVBar``)."""
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

    triggers: list[str] = []
    if listed_on is not None and first is not None and first < listed_on:
        triggers.append("listing_date")
    if returns:
        if sigma is not None and sigma == 0.0 and max_abs is not None and max_abs > mad_zero_abs_floor:
            triggers.append("n_sigma")
        elif sigma_mult is not None and sigma_mult > n_sigma:
            triggers.append("n_sigma")

    flagged = bool(triggers)
    bits: list[str] = []
    if "listing_date" in triggers:
        bits.append(
            f"first bar {first.isoformat() if first else 'n/a'} precedes known listing "
            f"{listed_on.isoformat() if listed_on else 'n/a'} (bar count {n})"
        )
    if "n_sigma" in triggers:
        if sigma == 0.0:
            bits.append(
                f"flat-tape jump: max |1-bar|={max_abs:.4f} with MAD=0 "
                f"(floor {mad_zero_abs_floor:.2f}; N={n_sigma:g})"
            )
        else:
            bits.append(
                f"max |1-bar|={max_abs:.4f} = {sigma_mult:.2f}× robust-sigma "
                f"(N={n_sigma:g}, sigma={sigma:.4f}, method=1.4826*MAD)"
            )
    detail = "; ".join(bits) if bits else "clears listing-date and N-sigma continuity"
    method = "listing_date;robust_mad_n_sigma" if listed_on is not None else "robust_mad_n_sigma"
    return ContinuityVerdict(
        flagged=flagged,
        reason_code=REASON_TICKER_REUSE if flagged else "",
        method=method,
        detail=detail,
        n_bars=n,
        first=first,
        last=last,
        listed_on=listed_on,
        n_sigma=float(n_sigma),
        robust_sigma=sigma,
        max_abs_1bar=max_abs,
        max_abs_1bar_in_sigma=sigma_mult,
        triggers=tuple(triggers),
    )


def check_ohlcv_continuity(
    bars: Sequence[Any],
    *,
    listed_on: date | None = None,
    n_sigma: float = CONTINUITY_N_SIGMA,
    mad_zero_abs_floor: float = MAD_ZERO_ABS_FLOOR,
) -> ContinuityVerdict:
    """Adapter-facing alias. Same check as :func:`check_bar_continuity`."""
    return check_bar_continuity(
        bars,
        listed_on=listed_on,
        n_sigma=n_sigma,
        mad_zero_abs_floor=mad_zero_abs_floor,
    )
