"""Phase 1 unconditional event-class base rates (IMP-039).

Quant-owned. Paper / fixture only. These are the event classes C-001/002/003
measure against — not the candidate signals themselves.

  dip_touch            — close-above rising SMA20, then a low at/through SMA20
  zone_boundary_touch  — any prior consolidation boundary (no X·ATR departure)
  pullback_ema_touch   — first-entry pullback to EMA after an N-bar breakout

No sizing. No scan-gate. No candidate study results. n < n_min → no claim.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any, Mapping

import yaml

from mm_common.hashing import canonical_json, normalize_numeric, sha256_hex
from mm_common.time import as_utc, parse_utc
from mm_quant.mathutil import ema_series, sma_series, wilder_atr_series
from mm_quant.models import SeriesBar
from mm_quant.panel import load_panel_file, panel_from_mapping
from mm_quant.trade_math import load_trade_math_config

ENGINE_VERSION = "imp-039.1"
DIP_TOUCH = "dip_touch"
ZONE_BOUNDARY_TOUCH = "zone_boundary_touch"
PULLBACK_EMA_TOUCH = "pullback_ema_touch"
EVENT_CLASSES = (DIP_TOUCH, ZONE_BOUNDARY_TOUCH, PULLBACK_EMA_TOUCH)

# Candidate citation: which C-* study measures against which class.
CANDIDATE_BENCHMARKS = {
    "C-001": ZONE_BOUNDARY_TOUCH,
    "C-002": DIP_TOUCH,
    "C-003": PULLBACK_EMA_TOUCH,
}

NO_CLAIM_REASON = "n below configured minimum; no base-rate claim"
FOOTER = (
    "Unconditional event-class base rates. Paper only. Not a call. "
    "DO NOT SIZE. Not a scan-gate. Not a C-001/C-002/C-003 study. "
    "n < n_min → no claim. Knowledge clock is as_of_knowledge "
    "(lockstep ingested_at). Never published_at / market_time."
)
DEFAULT_CONFIG_REL = Path("config") / "quant" / "base_rates.yaml"


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_base_rate_config(root: Path | None = None) -> dict[str, Any]:
    base = repo_root(root)
    data = _load_yaml(base / DEFAULT_CONFIG_REL)
    trade = load_trade_math_config(base)
    cost_cfg = trade.get("cost") if isinstance(trade.get("cost"), dict) else {}
    default = {
        "n_min": int(trade.get("min_sample") or 20),
        "atr_period": 14,
        "survivorship_tag": "survivorship_uncontrolled",
        "cost": {
            "taker_fee": float(cost_cfg.get("taker_fee") or 0.00045),
            "slippage_bps": 5.0,
            "funding_rate": 0.0,
            "expected_hold_hours": float(cost_cfg.get("default_hold_hours") or 24),
            "default_clip": float(cost_cfg.get("default_clip") or 10000),
            "formula": (
                "taker_fee*2 + slippage_bps/1e4*2 + "
                "funding_rate*(expected_hold_hours/24)"
            ),
        },
        "instrument_set": {
            "primary": [
                {"symbol": "BTC", "membership": "in_universe", "watchlist_tier": "universe"},
                {"symbol": "NVDA", "membership": "in_universe", "watchlist_tier": "universe"},
            ]
        },
        "window": {
            "bar": "daily_completed",
            "start": "2022-01-01",
            "end": "2026-09-18",
        },
        "classes": {
            DIP_TOUCH: {
                "sma_period": 20,
                "horizon_bars": 5,
                "invalidation_atr": 1.5,
                "side": "bounce",
                "cites": "C-002",
            },
            ZONE_BOUNDARY_TOUCH: {
                "base_bars": 5,
                "max_height_atr": 0.8,
                "touch_tolerance_atr": 0.25,
                "horizon_bars": 10,
                "invalidation_atr": 0.5,
                "side": "fade",
                "cites": "C-001",
            },
            PULLBACK_EMA_TOUCH: {
                "ema_period": 20,
                "breakout_lookback": 20,
                "horizon_bars": 15,
                "invalidation_atr": 0.3,
                "side": "continuation",
                "cites": "C-003",
            },
        },
    }
    merged = _deep_merge(default, data)
    return merged


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _num(value: float | None) -> float | None:
    if value is None:
        return None
    raw = normalize_numeric(value)
    return None if raw is None else float(raw)


def _iso(value: datetime) -> str:
    return as_utc(value).isoformat()


def cost_fraction(cost: Mapping[str, Any], *, funding_rate: float | None = None) -> float:
    """Notional fraction. Clip is a cost clip only — DO NOT SIZE."""
    taker = float(cost.get("taker_fee") or 0.0)
    slip_bps = float(cost.get("slippage_bps") or 0.0)
    fund = float(cost.get("funding_rate") if funding_rate is None else funding_rate)
    hold = float(cost.get("expected_hold_hours") or 24.0)
    return (taker * 2.0) + (slip_bps / 1e4 * 2.0) + (fund * (hold / 24.0))


def params_hash_for(config: Mapping[str, Any]) -> str:
    payload = {
        "engine_version": ENGINE_VERSION,
        "n_min": int(config.get("n_min") or 20),
        "atr_period": int(config.get("atr_period") or 14),
        "cost": dict(config.get("cost") or {}),
        "instrument_set": dict(config.get("instrument_set") or {}),
        "window": dict(config.get("window") or {}),
        "classes": dict(config.get("classes") or {}),
        "survivorship_tag": str(config.get("survivorship_tag") or "survivorship_uncontrolled"),
    }
    return sha256_hex(canonical_json(payload))


@dataclass(frozen=True)
class EventTouch:
    """One unconditional event. Outcome fields are None when H bars are not yet visible."""

    event_class: str
    instrument: str
    side: int  # +1 hypothesized up, -1 hypothesized down
    trigger_index: int
    trigger_available_at: datetime
    trigger_close: float
    atr: float | None
    level: float
    horizon_bars: int
    invalidation_atr: float
    fwd_return: float | None
    signed_fwd_return: float | None
    hit: bool | None
    r_after_cost: float | None
    censored: bool

    def canonical(self) -> dict[str, Any]:
        return {
            "event_class": self.event_class,
            "instrument": self.instrument,
            "side": self.side,
            "trigger_index": self.trigger_index,
            "trigger_available_at": _iso(self.trigger_available_at),
            "trigger_close": _num(self.trigger_close),
            "atr": _num(self.atr),
            "level": _num(self.level),
            "horizon_bars": self.horizon_bars,
            "invalidation_atr": self.invalidation_atr,
            "fwd_return": _num(self.fwd_return),
            "signed_fwd_return": _num(self.signed_fwd_return),
            "hit": self.hit,
            "r_after_cost": _num(self.r_after_cost),
            "censored": self.censored,
        }


@dataclass(frozen=True)
class ClassRate:
    event_class: str
    n: int
    n_min: int
    n_censored: int
    claimed: bool
    hit_rate: float | None
    median_fwd_return: float | None
    mean_r_after_cost: float | None
    reason: str
    cites_candidate: str
    definition: str

    def canonical(self) -> dict[str, Any]:
        return {
            "event_class": self.event_class,
            "n": self.n,
            "n_min": self.n_min,
            "n_censored": self.n_censored,
            "claimed": self.claimed,
            "hit_rate": _num(self.hit_rate),
            "median_fwd_return": _num(self.median_fwd_return),
            "mean_r_after_cost": _num(self.mean_r_after_cost),
            "reason": self.reason,
            "cites_candidate": self.cites_candidate,
            "definition": self.definition,
        }


@dataclass(frozen=True)
class BaseRateSnapshot:
    """Memory-shaped unconditional pack. Persist this; do not invent a print."""

    as_of_knowledge: datetime
    ingested_at: datetime
    params_hash: str
    content_hash: str
    fixture_id: str
    instrument_set: tuple[str, ...]
    window: dict[str, Any]
    cost_model: dict[str, Any]
    rates: tuple[ClassRate, ...]
    events: tuple[EventTouch, ...]
    notes: tuple[str, ...]
    survivorship_tag: str
    engine_version: str = ENGINE_VERSION
    n_llm_calls: int = 0
    extras: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "as_of_knowledge", as_utc(self.as_of_knowledge))
        object.__setattr__(self, "ingested_at", as_utc(self.ingested_at))

    def canonical(self) -> dict[str, Any]:
        return {
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "ingested_at": _iso(self.ingested_at),
            "params_hash": self.params_hash,
            "content_hash": self.content_hash,
            "fixture_id": self.fixture_id,
            "instrument_set": list(self.instrument_set),
            "window": dict(self.window),
            "cost_model": dict(self.cost_model),
            "rates": [row.canonical() for row in self.rates],
            "n_events": len(self.events),
            "notes": list(self.notes),
            "survivorship_tag": self.survivorship_tag,
            "engine_version": self.engine_version,
            "n_llm_calls": self.n_llm_calls,
            "candidate_benchmarks": dict(CANDIDATE_BENCHMARKS),
            "sizing": False,
            "scan_gate": False,
            "promote": False,
            "paper_only": True,
            "footer": FOOTER,
        }

    def memory_row(self, rate: ClassRate) -> dict[str, Any]:
        """One Market Memory row per event class."""
        return {
            "event_class": rate.event_class,
            "as_of_knowledge": _iso(self.as_of_knowledge),
            "ingested_at": _iso(self.ingested_at),
            "params_hash": self.params_hash,
            "content_hash": self.content_hash,
            "instrument_set": list(self.instrument_set),
            "window": dict(self.window),
            "cost_model": dict(self.cost_model),
            "n": rate.n,
            "n_min": rate.n_min,
            "claimed": rate.claimed,
            "hit_rate": _num(rate.hit_rate),
            "median_fwd_return": _num(rate.median_fwd_return),
            "mean_r_after_cost": _num(rate.mean_r_after_cost),
            "reason": rate.reason,
            "cites_candidate": rate.cites_candidate,
            "survivorship_tag": self.survivorship_tag,
            "engine_version": self.engine_version,
            "fixture_id": self.fixture_id,
        }


def _visible_bars(bars: tuple[SeriesBar, ...], watermark: datetime) -> tuple[SeriesBar, ...]:
    cut = as_utc(watermark)
    return tuple(b for b in bars if as_utc(b.as_of_knowledge) <= cut)


def _ohlc(bars: tuple[SeriesBar, ...]) -> tuple[list[float], list[float], list[float], list[float]]:
    opens: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []
    for bar in bars:
        closes.append(float(bar.close))
        opens.append(float(bar.close if bar.open is None else bar.open))
        highs.append(float(bar.close if bar.high is None else bar.high))
        lows.append(float(bar.close if bar.low is None else bar.low))
    return opens, highs, lows, closes


def _outcome(
    *,
    event_class: str,
    instrument: str,
    side: int,
    trigger_index: int,
    bars: tuple[SeriesBar, ...],
    atr: float | None,
    level: float,
    horizon: int,
    invalidation_atr: float,
    cost_frac: float,
) -> EventTouch:
    bar = bars[trigger_index]
    exit_idx = trigger_index + horizon
    censored = exit_idx >= len(bars)
    fwd = None
    signed = None
    hit = None
    r_cost = None
    if not censored:
        entry = float(bar.close)
        exit_px = float(bars[exit_idx].close)
        if entry != 0:
            fwd = exit_px / entry - 1.0
            signed = side * fwd
            hit = signed > 0
        if atr is not None and atr > 0 and entry != 0:
            stop = entry - (side * invalidation_atr * atr)
            risk = abs(entry - stop)
            if risk > 0:
                r_raw = side * (exit_px - entry) / risk
                cost_r = cost_frac * entry / risk
                r_cost = r_raw - cost_r
    return EventTouch(
        event_class=event_class,
        instrument=instrument,
        side=side,
        trigger_index=trigger_index,
        trigger_available_at=as_utc(bar.as_of_knowledge),
        trigger_close=float(bar.close),
        atr=atr,
        level=level,
        horizon_bars=horizon,
        invalidation_atr=invalidation_atr,
        fwd_return=fwd,
        signed_fwd_return=signed,
        hit=hit,
        r_after_cost=r_cost,
        censored=censored,
    )


def detect_dip_touches(
    bars: tuple[SeriesBar, ...],
    *,
    instrument: str,
    sma_period: int,
    atr_period: int,
    horizon_bars: int,
    invalidation_atr: float,
    cost_frac: float,
) -> tuple[EventTouch, ...]:
    """Uptrend = rising SMA. Touch = first low at/through SMA after a close above it."""
    if len(bars) < sma_period + 2:
        return ()
    _o, highs, lows, closes = _ohlc(bars)
    smas = sma_series(closes, sma_period)
    atrs = wilder_atr_series(highs, lows, closes, atr_period)
    found: list[EventTouch] = []
    for t in range(1, len(bars)):
        sma_now = smas[t]
        sma_prev = smas[t - 1]
        if sma_now is None or sma_prev is None:
            continue
        if sma_now <= sma_prev:
            continue
        if closes[t - 1] <= sma_prev:
            continue
        if lows[t - 1] <= sma_prev:
            continue
        if lows[t] > sma_now:
            continue
        found.append(
            _outcome(
                event_class=DIP_TOUCH,
                instrument=instrument,
                side=1,
                trigger_index=t,
                bars=bars,
                atr=atrs[t],
                level=sma_now,
                horizon=horizon_bars,
                invalidation_atr=invalidation_atr,
                cost_frac=cost_frac,
            )
        )
    return tuple(found)


def detect_zone_boundary_touches(
    bars: tuple[SeriesBar, ...],
    *,
    instrument: str,
    base_bars: int,
    max_height_atr: float,
    touch_tolerance_atr: float,
    atr_period: int,
    horizon_bars: int,
    invalidation_atr: float,
    cost_frac: float,
) -> tuple[EventTouch, ...]:
    """Any prior consolidation boundary. No X·ATR departure (that filter is C-001)."""
    if len(bars) < max(base_bars, atr_period + 1) + 1:
        return ()
    _o, highs, lows, closes = _ohlc(bars)
    atrs = wilder_atr_series(highs, lows, closes, atr_period)
    zones: list[tuple[int, float, float, float]] = []
    i = base_bars - 1
    while i < len(bars):
        atr = atrs[i]
        if atr is None or atr <= 0:
            i += 1
            continue
        sl_h = highs[i - base_bars + 1 : i + 1]
        sl_l = lows[i - base_bars + 1 : i + 1]
        height = max(sl_h) - min(sl_l)
        if height <= max_height_atr * atr:
            zones.append((i, min(sl_l), max(sl_h), atr))
            i += base_bars
        else:
            i += 1
    found: list[EventTouch] = []
    used: set[int] = set()
    for end, zlow, zhigh, z_atr in zones:
        tol = touch_tolerance_atr * z_atr
        for t in range(end + 1, len(bars)):
            if t in used:
                continue
            low = lows[t]
            high = highs[t]
            demand = low <= zlow + tol and high >= zlow - tol
            supply = high >= zhigh - tol and low <= zhigh + tol
            if not demand and not supply:
                continue
            # Prefer the nearer edge when both fire on the same bar.
            side = 1
            level = zlow
            if supply and (not demand or abs(high - zhigh) < abs(low - zlow)):
                side = -1
                level = zhigh
            used.add(t)
            found.append(
                _outcome(
                    event_class=ZONE_BOUNDARY_TOUCH,
                    instrument=instrument,
                    side=side,
                    trigger_index=t,
                    bars=bars,
                    atr=atrs[t] if atrs[t] is not None else z_atr,
                    level=level,
                    horizon=horizon_bars,
                    invalidation_atr=invalidation_atr,
                    cost_frac=cost_frac,
                )
            )
            break
    return tuple(found)


def detect_pullback_ema_touches(
    bars: tuple[SeriesBar, ...],
    *,
    instrument: str,
    ema_period: int,
    breakout_lookback: int,
    atr_period: int,
    horizon_bars: int,
    invalidation_atr: float,
    cost_frac: float,
) -> tuple[EventTouch, ...]:
    """First-entry class: first EMA touch after an N-bar extreme breakout.

    A pullback that never forms is not labeled from the future. Second-entry
    filters stay with C-003 and are not applied here.
    """
    need = max(ema_period, breakout_lookback, atr_period + 1) + 1
    if len(bars) < need:
        return ()
    _o, highs, lows, closes = _ohlc(bars)
    emas = ema_series(closes, ema_period)
    atrs = wilder_atr_series(highs, lows, closes, atr_period)
    found: list[EventTouch] = []
    i = breakout_lookback
    while i < len(bars):
        prior_h = highs[i - breakout_lookback : i]
        prior_l = lows[i - breakout_lookback : i]
        ext_high = max(prior_h)
        ext_low = min(prior_l)
        close = closes[i]
        side = 0
        if close > ext_high:
            side = 1
        elif close < ext_low:
            side = -1
        if side == 0:
            i += 1
            continue
        for u in range(i + 1, len(bars)):
            ema = emas[u]
            if ema is None:
                continue
            if side == 1 and lows[u] < lows[i]:
                break
            if side == -1 and highs[u] > highs[i]:
                break
            touched = lows[u] <= ema if side == 1 else highs[u] >= ema
            if not touched:
                continue
            found.append(
                _outcome(
                    event_class=PULLBACK_EMA_TOUCH,
                    instrument=instrument,
                    side=side,
                    trigger_index=u,
                    bars=bars,
                    atr=atrs[u],
                    level=ema,
                    horizon=horizon_bars,
                    invalidation_atr=invalidation_atr,
                    cost_frac=cost_frac,
                )
            )
            i = u
            break
        i += 1
    return tuple(found)


def summarize_class(
    events: tuple[EventTouch, ...],
    *,
    event_class: str,
    n_min: int,
    cites_candidate: str,
    definition: str,
) -> ClassRate:
    complete = tuple(e for e in events if not e.censored and e.signed_fwd_return is not None)
    n = len(complete)
    n_censored = sum(1 for e in events if e.censored)
    if n < n_min:
        return ClassRate(
            event_class=event_class,
            n=n,
            n_min=n_min,
            n_censored=n_censored,
            claimed=False,
            hit_rate=None,
            median_fwd_return=None,
            mean_r_after_cost=None,
            reason=NO_CLAIM_REASON,
            cites_candidate=cites_candidate,
            definition=definition,
        )
    hits = [1.0 if e.hit else 0.0 for e in complete]
    fwds = [float(e.signed_fwd_return or 0.0) for e in complete]
    rs = [float(e.r_after_cost) for e in complete if e.r_after_cost is not None]
    return ClassRate(
        event_class=event_class,
        n=n,
        n_min=n_min,
        n_censored=n_censored,
        claimed=True,
        hit_rate=sum(hits) / n,
        median_fwd_return=float(median(fwds)),
        mean_r_after_cost=(sum(rs) / len(rs)) if rs else None,
        reason=f"own-history n={n} (min {n_min})",
        cites_candidate=cites_candidate,
        definition=definition,
    )


_DEFINITIONS = {
    DIP_TOUCH: (
        "First low at/through rising SMA20 after a completed close above that SMA. "
        "Unconditional dip class. C-002 adds the triple-RSI filter on top of this class."
    ),
    ZONE_BOUNDARY_TOUCH: (
        "First later touch of any prior consolidation boundary "
        "(base_bars bars with height <= max_height_atr · ATR). "
        "No X·ATR departure confirm. C-001 adds that confirm plus first-return fade."
    ),
    PULLBACK_EMA_TOUCH: (
        "First EMA touch after a completed N-bar extreme breakout that does not "
        "take out the breakout bar extreme. First-entry class. "
        "C-003 adds the second pullback + trigger."
    ),
}


def compute_unconditional_base_rates(
    bars: tuple[SeriesBar, ...],
    watermark: datetime,
    *,
    config: Mapping[str, Any],
    fixture_id: str = "fixture",
    funding_by_instrument: Mapping[str, float] | None = None,
) -> BaseRateSnapshot:
    """PIT: only bars with as_of_knowledge <= watermark. Never invent a claim."""
    cfg = dict(config)
    visible = _visible_bars(bars, watermark)
    instruments = tuple(sorted({b.instrument.upper() for b in visible}))
    n_min = int(cfg.get("n_min") or 20)
    atr_period = int(cfg.get("atr_period") or 14)
    cost = dict(cfg.get("cost") or {})
    classes = cfg.get("classes") if isinstance(cfg.get("classes"), dict) else {}
    digest = params_hash_for(cfg)
    notes: list[str] = [
        "unconditional event classes only; candidate filters are not applied",
        "DO NOT SIZE; default_clip is a cost clip only",
        str(cfg.get("survivorship_tag") or "survivorship_uncontrolled"),
    ]
    all_events: list[EventTouch] = []
    rates: list[ClassRate] = []
    fund_map = {str(k).upper(): float(v) for k, v in (funding_by_instrument or {}).items()}

    dip_cfg = classes.get(DIP_TOUCH) if isinstance(classes.get(DIP_TOUCH), dict) else {}
    zone_cfg = classes.get(ZONE_BOUNDARY_TOUCH) if isinstance(classes.get(ZONE_BOUNDARY_TOUCH), dict) else {}
    pb_cfg = classes.get(PULLBACK_EMA_TOUCH) if isinstance(classes.get(PULLBACK_EMA_TOUCH), dict) else {}

    for inst in instruments:
        inst_bars = tuple(
            sorted(
                (b for b in visible if b.instrument.upper() == inst),
                key=lambda b: (as_utc(b.as_of_knowledge), as_utc(b.market_time)),
            )
        )
        fund = fund_map.get(inst, float(cost.get("funding_rate") or 0.0))
        # Equities carry funding_rate = 0; crypto may pass a fixture funding print.
        asset = next((b.asset_class for b in inst_bars if b.asset_class), "unknown")
        if str(asset).lower() in {"equity", "etf"}:
            fund = 0.0
        frac = cost_fraction(cost, funding_rate=fund)
        all_events.extend(
            detect_dip_touches(
                inst_bars,
                instrument=inst,
                sma_period=int(dip_cfg.get("sma_period") or 20),
                atr_period=atr_period,
                horizon_bars=int(dip_cfg.get("horizon_bars") or 5),
                invalidation_atr=float(dip_cfg.get("invalidation_atr") or 1.5),
                cost_frac=frac,
            )
        )
        all_events.extend(
            detect_zone_boundary_touches(
                inst_bars,
                instrument=inst,
                base_bars=int(zone_cfg.get("base_bars") or 5),
                max_height_atr=float(zone_cfg.get("max_height_atr") or 0.8),
                touch_tolerance_atr=float(zone_cfg.get("touch_tolerance_atr") or 0.25),
                atr_period=atr_period,
                horizon_bars=int(zone_cfg.get("horizon_bars") or 10),
                invalidation_atr=float(zone_cfg.get("invalidation_atr") or 0.5),
                cost_frac=frac,
            )
        )
        all_events.extend(
            detect_pullback_ema_touches(
                inst_bars,
                instrument=inst,
                ema_period=int(pb_cfg.get("ema_period") or 20),
                breakout_lookback=int(pb_cfg.get("breakout_lookback") or 20),
                atr_period=atr_period,
                horizon_bars=int(pb_cfg.get("horizon_bars") or 15),
                invalidation_atr=float(pb_cfg.get("invalidation_atr") or 0.3),
                cost_frac=frac,
            )
        )

    events = tuple(all_events)
    for event_class in EVENT_CLASSES:
        cls_cfg = classes.get(event_class) if isinstance(classes.get(event_class), dict) else {}
        cites = str(cls_cfg.get("cites") or {DIP_TOUCH: "C-002", ZONE_BOUNDARY_TOUCH: "C-001", PULLBACK_EMA_TOUCH: "C-003"}[event_class])
        rates.append(
            summarize_class(
                tuple(e for e in events if e.event_class == event_class),
                event_class=event_class,
                n_min=n_min,
                cites_candidate=cites,
                definition=_DEFINITIONS[event_class],
            )
        )

    if not instruments:
        notes.append("no visible bars at watermark; degrade, never invent a rate")

    window = dict(cfg.get("window") or {})
    as_of = as_utc(watermark)
    body_for_hash = {
        "as_of_knowledge": _iso(as_of),
        "params_hash": digest,
        "instrument_set": list(instruments),
        "window": window,
        "cost_model": {
            **cost,
            "total_fraction": _num(cost_fraction(cost)),
            "clip_is_not_a_size": True,
        },
        "rates": [row.canonical() for row in rates],
        "engine_version": ENGINE_VERSION,
    }
    content = sha256_hex(canonical_json(body_for_hash))
    return BaseRateSnapshot(
        as_of_knowledge=as_of,
        ingested_at=as_of,
        params_hash=digest,
        content_hash=content,
        fixture_id=fixture_id,
        instrument_set=instruments,
        window=window,
        cost_model=body_for_hash["cost_model"],
        rates=tuple(rates),
        events=events,
        notes=tuple(notes),
        survivorship_tag=str(cfg.get("survivorship_tag") or "survivorship_uncontrolled"),
    )


def snapshot_from_mapping(
    data: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    watermark: datetime | None = None,
) -> BaseRateSnapshot:
    panel = panel_from_mapping(dict(data))
    raw_as_of = data.get("as_of_knowledge")
    as_of = watermark or (parse_utc(str(raw_as_of)) if raw_as_of else None)
    if as_of is None:
        if panel.bars:
            as_of = max(b.as_of_knowledge for b in panel.bars)
        else:
            as_of = parse_utc("2026-09-18T00:00:00Z")
    fund = data.get("funding_by_instrument") if isinstance(data.get("funding_by_instrument"), dict) else {}
    return compute_unconditional_base_rates(
        panel.bars,
        as_of,
        config=config,
        fixture_id=str(data.get("fixture_id") or panel.fixture_id or "fixture"),
        funding_by_instrument=fund,
    )


def snapshot_from_fixture(path: Path, *, repo_root: Path | None = None) -> BaseRateSnapshot:
    root = Path(repo_root or ".").resolve()
    cfg = load_base_rate_config(root)
    panel = load_panel_file(Path(path))
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    as_of = None
    if isinstance(data, dict) and data.get("as_of_knowledge"):
        as_of = parse_utc(str(data["as_of_knowledge"]))
    elif panel.bars:
        as_of = max(b.as_of_knowledge for b in panel.bars)
    else:
        as_of = parse_utc("2026-09-18T00:00:00Z")
    fund = data.get("funding_by_instrument") if isinstance(data, dict) and isinstance(data.get("funding_by_instrument"), dict) else {}
    return compute_unconditional_base_rates(
        panel.bars,
        as_of,
        config=cfg,
        fixture_id=str(panel.fixture_id or Path(path).stem),
        funding_by_instrument=fund,
    )
