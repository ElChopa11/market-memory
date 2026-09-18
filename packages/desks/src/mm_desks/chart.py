"""Chart product (Research sleeve): deterministic levels computed ONCE and quoted by others. PNG filename = content_hash. Not a publishing desk."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc
from mm_quant.models import SeriesBar

ENGINE_VERSION = "imp-016.1"


@dataclass(frozen=True)
class ChartLevels:
    instrument: str
    as_of_knowledge: datetime
    prior_high: float | None
    prior_low: float | None
    session_vwap: float | None
    session_avwap: float | None
    value_area_high: float | None
    value_area_low: float | None
    value_area_poc: float | None
    range_high: float | None
    range_low: float | None
    gaps: tuple[dict[str, float], ...]
    provenance_ids: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def canonical(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "as_of_knowledge": as_utc(self.as_of_knowledge).isoformat(),
            "prior_high": self.prior_high,
            "prior_low": self.prior_low,
            "session_vwap": self.session_vwap,
            "session_avwap": self.session_avwap,
            "value_area_high": self.value_area_high,
            "value_area_low": self.value_area_low,
            "value_area_poc": self.value_area_poc,
            "range_high": self.range_high,
            "range_low": self.range_low,
            "gaps": [dict(row) for row in self.gaps],
            "provenance_ids": list(self.provenance_ids),
            "notes": list(self.notes),
            "engine_version": ENGINE_VERSION,
        }

    def content_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical()))


def _typical(bar: SeriesBar) -> float | None:
    high = bar.high if bar.high is not None else bar.close
    low = bar.low if bar.low is not None else bar.close
    if high is None or low is None or bar.close is None:
        return None
    return (high + low + bar.close) / 3.0


def compute_levels(instrument: str, bars: tuple[SeriesBar, ...], *, as_of: datetime) -> ChartLevels:
    """Prior H/L, session VWAP + AVWAP, value area, range, gaps. Missing stays missing."""
    scoped = tuple(b for b in bars if b.instrument.upper() == instrument.upper() and b.as_of_knowledge <= as_utc(as_of))
    notes: list[str] = []
    if not scoped:
        notes.append("no bars at as_of; levels unavailable (not invented)")
        return ChartLevels(
            instrument=instrument.upper(),
            as_of_knowledge=as_of,
            prior_high=None,
            prior_low=None,
            session_vwap=None,
            session_avwap=None,
            value_area_high=None,
            value_area_low=None,
            value_area_poc=None,
            range_high=None,
            range_low=None,
            gaps=(),
            provenance_ids=(),
            notes=tuple(notes),
        )
    session_date = as_utc(scoped[-1].market_time).date()
    session = tuple(b for b in scoped if as_utc(b.market_time).date() == session_date)
    prior = tuple(b for b in scoped if as_utc(b.market_time).date() < session_date)
    if not session:
        session = scoped[-min(len(scoped), 24) :]
        notes.append("session inferred from last bars (fixture)")
    highs = [b.high for b in session if b.high is not None]
    lows = [b.low for b in session if b.low is not None]
    range_high = max(highs) if highs else max(b.close for b in session)
    range_low = min(lows) if lows else min(b.close for b in session)
    prior_high = None
    prior_low = None
    if prior:
        ph = [b.high for b in prior if b.high is not None]
        pl = [b.low for b in prior if b.low is not None]
        prior_high = max(ph) if ph else max(b.close for b in prior)
        prior_low = min(pl) if pl else min(b.close for b in prior)
    vwap = _vwap(session)
    avwap = vwap  # single-session fixture: AVWAP from session open == VWAP
    poc, vah, val = _value_area(session)
    gaps: list[dict[str, float]] = []
    if prior and session:
        prev_close = prior[-1].close
        sess_open = session[0].open if session[0].open is not None else session[0].close
        if abs(sess_open - prev_close) / prev_close >= 0.001:
            gaps.append({"from": prev_close, "to": sess_open})
    provenance = tuple(b.observation_id for b in session if b.observation_id)
    return ChartLevels(
        instrument=instrument.upper(),
        as_of_knowledge=as_of,
        prior_high=prior_high,
        prior_low=prior_low,
        session_vwap=vwap,
        session_avwap=avwap,
        value_area_high=vah,
        value_area_low=val,
        value_area_poc=poc,
        range_high=range_high,
        range_low=range_low,
        gaps=tuple(gaps),
        provenance_ids=provenance,
        notes=tuple(notes),
    )


def _vwap(bars: tuple[SeriesBar, ...]) -> float | None:
    num = 0.0
    den = 0.0
    for bar in bars:
        typical = _typical(bar)
        vol = bar.volume if bar.volume is not None else 1.0
        if typical is None or vol <= 0:
            continue
        num += typical * vol
        den += vol
    if den <= 0:
        return None
    return num / den


def _value_area(bars: tuple[SeriesBar, ...]) -> tuple[float | None, float | None, float | None]:
    """POC = volume-weighted typical; VA = 70% of volume around POC (fixture approximation)."""
    priced: list[tuple[float, float]] = []
    for bar in bars:
        typical = _typical(bar)
        vol = bar.volume if bar.volume is not None else 1.0
        if typical is None:
            continue
        priced.append((typical, vol))
    if not priced:
        return None, None, None
    total = sum(v for _, v in priced)
    poc = max(priced, key=lambda row: row[1])[0]
    ordered = sorted(priced, key=lambda row: abs(row[0] - poc))
    acc = 0.0
    included: list[float] = []
    for px, vol in ordered:
        included.append(px)
        acc += vol
        if acc >= 0.70 * total:
            break
    return poc, max(included), min(included)


def render_png(levels: ChartLevels, closes: tuple[float, ...]) -> bytes:
    """Dark-theme PNG. Deterministic. Stdlib only (no paid deps)."""
    width, height = 160, 90
    bg = (20, 24, 32)
    grid = (40, 48, 64)
    line = (120, 200, 180)
    level_c = (230, 180, 80)
    pixels = [bg] * (width * height)
    for y in range(0, height, 15):
        for x in range(width):
            pixels[y * width + x] = grid
    if closes:
        lo = min(closes)
        hi = max(closes)
        span = (hi - lo) or 1.0
        pts = []
        for i, px in enumerate(closes):
            x = int(i * (width - 1) / max(1, len(closes) - 1))
            y = int((height - 1) * (1.0 - (px - lo) / span))
            pts.append((x, y))
        for i in range(1, len(pts)):
            _draw_line(pixels, width, height, pts[i - 1], pts[i], line)
        for name in ("session_vwap", "prior_high", "prior_low"):
            val = getattr(levels, name)
            if val is None:
                continue
            y = int((height - 1) * (1.0 - (val - lo) / span))
            y = max(0, min(height - 1, y))
            for x in range(width):
                pixels[y * width + x] = level_c
    return _encode_png(width, height, pixels)


def _draw_line(pixels: list[tuple[int, int, int]], w: int, h: int, a: tuple[int, int], b: tuple[int, int], color) -> None:
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        if 0 <= x0 < w and 0 <= y0 < h:
            pixels[y0 * w + x0] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def _encode_png(width: int, height: int, pixels: list[tuple[int, int, int]]) -> bytes:
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw.extend((r, g, b))
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def png_filename(content_hash: str) -> str:
    return f"{content_hash}.png"
