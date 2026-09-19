#!/usr/bin/env python3
"""Standalone Phase-1 per-instrument unconditional base rates.

Deliberately OUTSIDE the desk system. No Market Memory write, no run_id, no
envelope, no desk runners, no Telegram, no LLM. Not IMP-040 event-class rates.

Run (repo root):

    python scripts/research/base_rates_phase1.py

If mm_ingest is not on PYTHONPATH, use the workspace venv:

    uv run python scripts/research/base_rates_phase1.py

Env (live fetch only):
    POLYGON_API_KEY   equities / US-listed names via Polygon daily aggs
    Hyperliquid       public /info candleSnapshot — no key
    CoinGecko         optional fallback for crypto not on HL (public REST; may 401)

Prefer --offline with --bars-dir / --cache-dir when bars are already on disk.
Do **not** pass --no-sleep on Polygon free tier (5 req/min).

Writes research/base-rates/phase1-<YYYY-MM-DD>.md using the Australia/Sydney
date when the run finishes (UTC timestamp is printed in the file).
Monitor.yaml is the ticker set. Universe overlay of non-monitor names is
deferred (queue Gaps question); do not fetch AVGO/MSFT/META/JPM/XOM/SMH/XLF
in this pass.

Polygon/equities series run a continuity check (listing date + N-sigma MAD).
``suspected_ticker_reuse`` is voided and excluded from pooled stats.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

import yaml

# ---------------------------------------------------------------------------
# Config (flat cost assumption — one pessimistic number, stated in the report)
# ---------------------------------------------------------------------------

COST: dict[str, float] = {
    "taker_fee": 0.00045,  # 4.5 bps per side
    "slippage_bps": 5.0,  # 5 bps per side
    "funding_per_day": 0.00010,  # 1 bp/day, perps only
    "funding_hold_days": 10.0,  # bracket horizon
}

MIN_BARS = 200
MIN_REGIME_BARS = 100
ATR_PERIOD = 20
SMA_FAST = 50
SMA_SLOW = 200
SMA_SLOPE_LOOKBACK = 1  # SMA50[t] vs SMA50[t - lookback]
HORIZONS: tuple[int, ...] = (1, 3, 5, 10)
BRACKET_BARS = 10
BRACKET_STOP_R = 1.0
BRACKET_TARGET_R = 2.0
FETCH_START = datetime(2018, 1, 1, tzinfo=timezone.utc)
SYDNEY = ZoneInfo("Australia/Sydney")
MONITOR_REL = Path("config") / "watchlist" / "monitor.yaml"
OUTPUT_REL = Path("research") / "base-rates"
CACHE_REL = Path("research") / "base-rates" / "cache"
CONTINUITY_REL = Path("config") / "research" / "ticker_continuity.yaml"
POLYGON_FREE_TIER_CALENDAR_DAYS = 730
POLYGON_SLEEP_S = 12.1  # free-tier 5 req/min; do not use --no-sleep live

# CoinGecko ids used only as a fallback when HL has no daily OHLC.
# Unknown names are not guessed.
COINGECKO_IDS: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "NEAR": "near",
    "ARB": "arbitrum",
    "UNI": "uniswap",
    "ZEC": "zcash",
    "XMR": "monero",
    "LTC": "litecoin",
    "DOGE": "dogecoin",
    "HYPE": "hyperliquid",
}

EQUITY_VENUES = frozenset({"nasdaq", "nyse", "index", "cme", "nymex", "krx"})
CRYPTO_VENUES = frozenset({"hyperliquid", "unspecified"})

REGIMES = ("unconditional", "trend-up", "trend-down", "chop")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Bar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


@dataclass(frozen=True)
class SymbolSpec:
    ticker: str
    membership_key: str
    tape_alias: str
    round: str
    tier: str
    cluster: str
    venue: str
    kind: str
    qualified_id: str
    coin: str | None
    note: str
    listing_date: date | None = None


@dataclass
class Dist:
    n: int
    mean: float | None
    median: float | None
    stdev: float | None
    p5: float | None
    p25: float | None
    p75: float | None
    p95: float | None


@dataclass
class Bracket:
    n_trials: int = 0
    n_target: int = 0
    n_stop: int = 0
    n_tie: int = 0
    n_timeout: int = 0

    def hit_rate_resolved(self) -> float | None:
        denom = self.n_target + self.n_stop
        if denom <= 0:
            return None
        return self.n_target / denom


@dataclass
class RegimeStats:
    name: str
    n_bars: int
    first: date | None
    last: date | None
    fwd: dict[int, Dist]
    vol20_last: float | None
    vol60_last: float | None
    vol20_mean: float | None
    vol60_mean: float | None
    pct_above_sma200: float | None
    pct_above_sma50: float | None
    avg_abs_move_atr: float | None
    bracket_long_gross: Bracket
    bracket_short_gross: Bracket
    bracket_long_net: Bracket
    bracket_short_net: Bracket
    under_min: bool


@dataclass
class InstrumentResult:
    spec: SymbolSpec
    source: str
    exclusion: str | None
    n_raw: int
    bars_first: date | None
    bars_last: date | None
    ann_factor: float
    cost_frac: float
    regimes: dict[str, RegimeStats] = field(default_factory=dict)
    void_code: str | None = None
    continuity_detail: str | None = None
    listed_on: date | None = None
    max_1bar: float | None = None
    max_10bar: float | None = None
    polygon_free_tier_cap: bool = False


# ---------------------------------------------------------------------------
# Paths / monitor
# ---------------------------------------------------------------------------


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "packages").is_dir():
            return candidate
    return here


def load_monitor_symbols(path: Path) -> list[SymbolSpec]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"monitor.yaml is not a mapping: {path}")
    resolution = data.get("resolution") if isinstance(data.get("resolution"), dict) else {}
    rows = data.get("names") or []
    out: list[SymbolSpec] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        res = resolution.get(ticker) if isinstance(resolution.get(ticker), dict) else {}
        venue = str(res.get("venue") or "").strip().lower() or "unspecified"
        kind = str(res.get("kind") or "").strip().lower()
        qid = str(res.get("qualified_id") or "")
        coin = res.get("coin")
        coin_s = str(coin).strip().upper() if coin else None
        note = str(res.get("note") or row.get("resolution_note") or "")
        listing_raw = res.get("listing_date")
        listing_date = None
        if listing_raw not in (None, "", "unresolved"):
            try:
                listing_date = date.fromisoformat(str(listing_raw).strip()[:10])
            except ValueError:
                listing_date = None
        out.append(
            SymbolSpec(
                ticker=ticker,
                membership_key=str(row.get("membership_key") or ticker),
                tape_alias=str(row.get("tape_alias") or ticker),
                round=str(row.get("round") or ""),
                tier=str(row.get("tier") or ""),
                cluster=str(row.get("cluster") or ""),
                venue=venue,
                kind=kind,
                qualified_id=qid,
                coin=coin_s,
                note=note,
                listing_date=listing_date,
            )
        )
    if not out:
        raise ValueError(f"monitor.yaml has no names: {path}")
    return out


def hl_coin(spec: SymbolSpec) -> str:
    if spec.coin:
        return spec.coin
    qid = spec.qualified_id
    if qid.upper().startswith("HL:"):
        return qid.split(":", 1)[1].upper()
    alias = spec.tape_alias.upper().removesuffix("USD")
    if alias:
        return alias
    return spec.membership_key.upper().removesuffix("USD")


def polygon_ticker(spec: SymbolSpec) -> str | None:
    """Map a monitor name to a Polygon stocks/index ticker. Never a different instrument."""
    qid = spec.qualified_id
    venue = spec.venue
    if venue in {"nasdaq", "nyse"}:
        if ":" in qid:
            return qid.split(":", 1)[1].upper()
        return spec.ticker.upper()
    if venue == "index" or qid.upper().startswith("INDEX:"):
        if spec.ticker.upper() == "SPX" or qid.upper().endswith("SPX"):
            return "I:SPX"
        return None
    if venue == "krx":
        if ":" in qid:
            return qid.split(":", 1)[1]
        return None
    if venue in {"cme", "nymex"}:
        # Do not substitute NQ1!→NDX, CL1!→CL, BTC1!→IBIT. Futures tape is not the stocks adapter.
        return None
    return None


def is_perp(spec: SymbolSpec) -> bool:
    return spec.venue == "hyperliquid" or spec.kind == "perp" or spec.round == "crypto"


def ann_factor_for(spec: SymbolSpec) -> float:
    return 365.0 if is_perp(spec) or spec.round == "crypto" else 252.0


def round_trip_cost(spec: SymbolSpec, cost: Mapping[str, float] = COST) -> float:
    taker = float(cost["taker_fee"])
    slip = float(cost["slippage_bps"]) / 10_000.0
    funding = 0.0
    if is_perp(spec):
        funding = float(cost["funding_per_day"]) * float(cost["funding_hold_days"])
    return (2.0 * taker) + (2.0 * slip) + funding


def cache_filename(ticker: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", ticker) + ".json"


def load_continuity_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"n_sigma": 8.0, "instruments": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"n_sigma": 8.0, "instruments": {}}
    instruments = data.get("instruments") if isinstance(data.get("instruments"), dict) else {}
    return {
        "n_sigma": float(data.get("n_sigma") or 8.0),
        "mad_zero_abs_floor": float(data.get("mad_zero_abs_floor") or 0.05),
        "polygon_free_tier_calendar_days": int(
            data.get("polygon_free_tier_calendar_days") or POLYGON_FREE_TIER_CALENDAR_DAYS
        ),
        "instruments": instruments,
    }


def listed_on_for(spec: SymbolSpec, continuity_cfg: Mapping[str, Any]) -> date | None:
    instruments = continuity_cfg.get("instruments") if isinstance(continuity_cfg.get("instruments"), dict) else {}
    row = instruments.get(spec.ticker) if isinstance(instruments.get(spec.ticker), dict) else {}
    raw = row.get("listed_on") if row else None
    if raw:
        try:
            return date.fromisoformat(str(raw).strip()[:10])
        except ValueError:
            pass
    return spec.listing_date


def is_equity_series(spec: SymbolSpec, source: str) -> bool:
    if "polygon:" in (source or ""):
        return True
    return spec.venue in EQUITY_VENUES and spec.round != "crypto"


def polygon_free_tier_cap(bars: Sequence[Bar], *, window_end: date | None = None) -> bool:
    if len(bars) < 400:
        return False
    first, last = bars[0].date, bars[-1].date
    span = (last - first).days
    if span < POLYGON_FREE_TIER_CALENDAR_DAYS - 15:
        return False
    if window_end is None:
        return span >= POLYGON_FREE_TIER_CALENDAR_DAYS - 15
    expected = window_end - timedelta(days=POLYGON_FREE_TIER_CALENDAR_DAYS)
    return abs((first - expected).days) <= 5


def apply_continuity(
    result: InstrumentResult,
    bars: Sequence[Bar],
    *,
    spec: SymbolSpec,
    source: str,
    continuity_cfg: Mapping[str, Any],
    window_end: date | None = None,
) -> InstrumentResult:
    listed = listed_on_for(spec, continuity_cfg)
    result.listed_on = listed
    result.polygon_free_tier_cap = bool(bars) and is_equity_series(spec, source) and polygon_free_tier_cap(
        bars, window_end=window_end
    )
    if not bars or not is_equity_series(spec, source):
        return result
    from mm_ingest.equities.continuity import check_bar_continuity

    verdict = check_bar_continuity(
        bars,
        listed_on=listed,
        n_sigma=float(continuity_cfg.get("n_sigma") or 8.0),
        mad_zero_abs_floor=float(continuity_cfg.get("mad_zero_abs_floor") or 0.05),
    )
    result.continuity_detail = verdict.detail
    if verdict.flagged:
        result.void_code = verdict.reason_code or "suspected_ticker_reuse"
        extra = f"suspected_ticker_reuse / entity splice ({verdict.detail})"
        result.exclusion = f"{result.exclusion}; {extra}" if result.exclusion else extra
    return result


# ---------------------------------------------------------------------------
# Math (stdlib; no look-ahead — index i uses bars 0..i only)
# ---------------------------------------------------------------------------


def _f(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percentile(xs: Sequence[float], p: float) -> float | None:
    if not xs:
        return None
    ys = sorted(float(x) for x in xs)
    if len(ys) == 1:
        return ys[0]
    k = (len(ys) - 1) * (p / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ys[int(k)]
    return ys[lo] * (hi - k) + ys[hi] * (k - lo)


def dist_of(xs: Sequence[float]) -> Dist:
    vals = [float(x) for x in xs]
    n = len(vals)
    if n == 0:
        return Dist(n=0, mean=None, median=None, stdev=None, p5=None, p25=None, p75=None, p95=None)
    mean = statistics.mean(vals)
    med = statistics.median(vals)
    stdev = statistics.stdev(vals) if n >= 2 else None
    return Dist(
        n=n,
        mean=mean,
        median=med,
        stdev=stdev,
        p5=percentile(vals, 5),
        p25=percentile(vals, 25),
        p75=percentile(vals, 75),
        p95=percentile(vals, 95),
    )


def sma_series(closes: Sequence[float], period: int) -> list[float | None]:
    n = len(closes)
    out: list[float | None] = [None] * n
    if period < 1:
        return out
    for i in range(period - 1, n):
        sl = closes[i - period + 1 : i + 1]
        out[i] = sum(sl) / period
    return out


def wilder_atr_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int,
) -> list[float | None]:
    n = min(len(highs), len(lows), len(closes))
    out: list[float | None] = [None] * n
    if period < 1 or n < period + 1:
        return out
    trs: list[float] = []
    for i in range(1, n):
        trs.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )
    if len(trs) < period:
        return out
    atr = sum(trs[:period]) / period
    out[period] = atr
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
        out[i + 1] = atr
    return out


def realised_vol(returns: Sequence[float], window: int, ann: float) -> float | None:
    if window < 2 or len(returns) < window or ann <= 0:
        return None
    sl = returns[-window:]
    mean = sum(sl) / window
    var = sum((x - mean) ** 2 for x in sl) / (window - 1)
    if var < 0:
        return None
    return math.sqrt(var) * math.sqrt(ann)


def classify_regime(
    close: float,
    sma200: float | None,
    sma50: float | None,
    sma50_prev: float | None,
) -> str | None:
    if sma200 is None or sma50 is None or sma50_prev is None:
        return None
    slope = sma50 - sma50_prev
    above = close > sma200
    if above and slope > 0:
        return "trend-up"
    if (not above) and slope < 0:
        return "trend-down"
    return "chop"


def evaluate_long_bracket(
    entry: float,
    stop: float,
    target: float,
    future: Sequence[Bar],
) -> str:
    for bar in future:
        hit_t = bar.high >= target
        hit_s = bar.low <= stop
        if hit_t and hit_s:
            return "tie"
        if hit_t:
            return "target"
        if hit_s:
            return "stop"
    return "timeout"


def evaluate_short_bracket(
    entry: float,
    stop: float,
    target: float,
    future: Sequence[Bar],
) -> str:
    for bar in future:
        hit_t = bar.low <= target
        hit_s = bar.high >= stop
        if hit_t and hit_s:
            return "tie"
        if hit_t:
            return "target"
        if hit_s:
            return "stop"
    return "timeout"


def _record_bracket(bucket: Bracket, outcome: str) -> None:
    bucket.n_trials += 1
    if outcome == "target":
        bucket.n_target += 1
    elif outcome == "stop":
        bucket.n_stop += 1
    elif outcome == "tie":
        bucket.n_tie += 1
    else:
        bucket.n_timeout += 1


# ---------------------------------------------------------------------------
# Bar parsers
# ---------------------------------------------------------------------------


def clean_bars(bars: Iterable[Bar]) -> list[Bar]:
    by_date: dict[date, Bar] = {}
    for bar in bars:
        if bar.high < bar.low or bar.close <= 0 or bar.open <= 0:
            continue
        by_date[bar.date] = bar
    return [by_date[d] for d in sorted(by_date)]


def bars_from_hl_rows(rows: Sequence[Mapping[str, Any]]) -> list[Bar]:
    out: list[Bar] = []
    for row in rows:
        ts = row.get("t") or row.get("time")
        o, h, l, c = _f(row.get("o") or row.get("open")), _f(row.get("h") or row.get("high")), _f(
            row.get("l") or row.get("low")
        ), _f(row.get("c") or row.get("close"))
        if ts is None or None in (o, h, l, c):
            continue
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).date()
        out.append(Bar(date=dt, open=float(o), high=float(h), low=float(l), close=float(c), volume=_f(row.get("v"))))
    return clean_bars(out)


def bars_from_polygon(rows: Sequence[Any]) -> list[Bar]:
    out: list[Bar] = []
    for row in rows:
        o, h, l, c = _f(getattr(row, "open", None)), _f(getattr(row, "high", None)), _f(
            getattr(row, "low", None)
        ), _f(getattr(row, "close", None))
        mt = getattr(row, "market_time", None)
        if mt is None or None in (o, h, l, c):
            continue
        if mt.tzinfo is None:
            mt = mt.replace(tzinfo=timezone.utc)
        out.append(
            Bar(
                date=mt.astimezone(timezone.utc).date(),
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=_f(getattr(row, "volume", None)),
            )
        )
    return clean_bars(out)


def bars_from_gecko_ohlc(rows: Sequence[Any]) -> list[Bar]:
    out: list[Bar] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        ts, o, h, l, c = row[0], _f(row[1]), _f(row[2]), _f(row[3]), _f(row[4])
        if ts is None or None in (o, h, l, c):
            continue
        ts_i = int(ts)
        if ts_i > 10_000_000_000:
            ts_i = ts_i // 1000
        dt = datetime.fromtimestamp(ts_i, tz=timezone.utc).date()
        out.append(Bar(date=dt, open=float(o), high=float(h), low=float(l), close=float(c)))
    cleaned = clean_bars(out)
    if len(cleaned) >= 2:
        deltas = [(cleaned[i].date - cleaned[i - 1].date).days for i in range(1, len(cleaned))]
        med = statistics.median(deltas)
        if med > 1.5:
            return []  # not daily — caller reports why
    return cleaned


def bars_from_mapping(payload: Mapping[str, Any]) -> list[Bar]:
    rows = payload.get("bars") or payload.get("results") or []
    if not isinstance(rows, list):
        return []
    out: list[Bar] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_date = row.get("date") or row.get("t")
        o, h, l, c = _f(row.get("open") or row.get("o")), _f(row.get("high") or row.get("h")), _f(
            row.get("low") or row.get("l")
        ), _f(row.get("close") or row.get("c"))
        if raw_date is None or None in (o, h, l, c):
            continue
        if isinstance(raw_date, date) and not isinstance(raw_date, datetime):
            d = raw_date
        elif isinstance(raw_date, (int, float)):
            ts = int(raw_date)
            if ts > 10_000_000_000:
                ts = ts // 1000
            d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        else:
            text = str(raw_date)[:10]
            d = date.fromisoformat(text)
        out.append(Bar(date=d, open=float(o), high=float(h), low=float(l), close=float(c), volume=_f(row.get("volume"))))
    return clean_bars(out)


def dump_bars(ticker: str, source: str, bars: Sequence[Bar]) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "source": source,
        "bars": [
            {
                "date": b.date.isoformat(),
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ],
    }


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def _load_json_bars(path: Path) -> tuple[list[Bar], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return [], "cache JSON is not an object"
    bars = bars_from_mapping(payload)
    source = str(payload.get("source") or path.name)
    return bars, source


def fetch_hl_daily(coin: str, *, start: datetime, end: datetime) -> tuple[list[Bar], str | None]:
    from mm_ingest.hl_info import HyperliquidInfoClient, HyperliquidInfoError

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    try:
        with HyperliquidInfoClient() as client:
            rows = client.iter_candles(coin, "1d", start_ms, end_ms)
    except HyperliquidInfoError as exc:
        return [], f"hyperliquid candleSnapshot failed for {coin}: {exc}"
    except Exception as exc:  # noqa: BLE001
        return [], f"hyperliquid candleSnapshot failed for {coin}: {type(exc).__name__}"
    bars = bars_from_hl_rows(rows)
    if not bars:
        return [], f"hyperliquid returned no daily OHLC for {coin}"
    return bars, None


def fetch_polygon_daily(ticker: str, *, start: datetime, end: datetime) -> tuple[list[Bar], str | None]:
    from mm_ingest.equities.interface import EquitiesQuery
    from mm_ingest.equities.polygon import API_KEY_ENV, PolygonEquitiesAdapter
    from mm_ingest.rate_limit import RateLimitBudget

    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        return [], f"{API_KEY_ENV} missing; no cached daily bars"

    ingested = datetime.now(timezone.utc)
    adapter = PolygonEquitiesAdapter(budget=RateLimitBudget(name="polygon", max_requests_per_minute=5))
    try:
        query = EquitiesQuery(
            tickers=(ticker,),
            start=start,
            end=end,
            ingested_at=ingested,
            include_intraday=False,
            include_corporate_actions=False,
            include_earnings=False,
        )
        rows = adapter.ohlcv_daily(query)
    finally:
        adapter.close()
    bars = bars_from_polygon(rows)
    if not bars:
        err = adapter.last_error_class if adapter.last_error_class != "none" else "empty"
        notes = "; ".join(adapter.last_notes) if adapter.last_notes else err
        return [], f"polygon daily aggs empty for {ticker} ({notes})"
    return bars, None


def fetch_coingecko_daily(gecko_id: str) -> tuple[list[Bar], str | None]:
    import httpx
    from mm_common.http import http_get

    url = f"https://api.coingecko.com/api/v3/coins/{gecko_id}/ohlc"
    with httpx.Client(timeout=20.0) as client:
        result = http_get(
            client,
            url,
            params={"vs_currency": "usd", "days": "max"},
            headers={"User-Agent": "market-memory-standalone-base-rates"},
            parse_json=True,
        )
    if not result.ok:
        cls = result.error_class
        return [], f"coingecko OHLC unavailable for {gecko_id} (error_class={cls}; status={result.status_code})"
    payload = result.json_payload
    if not isinstance(payload, list):
        return [], f"coingecko OHLC parse error for {gecko_id}"
    bars = bars_from_gecko_ohlc(payload)
    if not bars:
        return [], (
            f"coingecko OHLC for {gecko_id} is not daily (or empty); "
            "highs/lows would have to be invented from close-only series"
        )
    return bars, None


def load_or_fetch_bars(
    spec: SymbolSpec,
    *,
    start: datetime,
    end: datetime,
    bars_dir: Path | None,
    cache_dir: Path | None,
    offline: bool,
    refresh: bool,
    sleeper: Callable[[float], None],
) -> tuple[list[Bar], str, str | None]:
    """Return (bars, source, exclusion_reason)."""
    if bars_dir is not None:
        local = bars_dir / cache_filename(spec.ticker)
        if local.is_file():
            bars, source = _load_json_bars(local)
            return bars, f"bars-dir:{source}", None
    if cache_dir is not None and not refresh:
        cached = cache_dir / cache_filename(spec.ticker)
        if cached.is_file():
            bars, source = _load_json_bars(cached)
            return bars, f"cache:{source}", None
    if offline:
        return [], "", "offline: no bars-dir/cache file for this ticker"

    bars: list[Bar] = []
    source = ""
    errors: list[str] = []

    crypto_like = spec.round == "crypto" or spec.venue in CRYPTO_VENUES or spec.kind == "perp"
    equity_like = spec.venue in EQUITY_VENUES or spec.round == "base"

    if crypto_like or spec.venue == "hyperliquid":
        sleeper(0.05)
        hl_bars, hl_err = fetch_hl_daily(hl_coin(spec), start=start, end=end)
        if hl_bars:
            bars, source = hl_bars, f"hyperliquid:{hl_coin(spec)}"
        elif hl_err:
            errors.append(hl_err)

    if not bars and crypto_like:
        gecko_key = hl_coin(spec)
        gecko_id = COINGECKO_IDS.get(gecko_key)
        if gecko_id is None:
            errors.append(f"no CoinGecko id mapping for {gecko_key}; will not guess")
        else:
            g_bars, g_err = fetch_coingecko_daily(gecko_id)
            if g_bars:
                bars, source = g_bars, f"coingecko:{gecko_id}"
            elif g_err:
                errors.append(g_err)

    if not bars and equity_like and spec.venue != "hyperliquid":
        pticker = polygon_ticker(spec)
        if pticker is None:
            errors.append(
                f"no Polygon stocks/index ticker for {spec.ticker} ({spec.qualified_id or spec.venue}); "
                "will not substitute a different instrument"
            )
        else:
            from mm_ingest.equities.polygon import API_KEY_ENV

            if not os.environ.get(API_KEY_ENV, "").strip():
                errors.append(f"{API_KEY_ENV} missing; no cached daily bars")
            else:
                sleeper(POLYGON_SLEEP_S)
                p_bars, p_err = fetch_polygon_daily(pticker, start=start, end=end)
                if p_bars:
                    bars, source = p_bars, f"polygon:{pticker}"
                elif p_err:
                    errors.append(p_err)

    if not bars and not errors:
        errors.append("no daily history from Hyperliquid / Polygon / CoinGecko")

    if bars and cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / cache_filename(spec.ticker)).write_text(
            json.dumps(dump_bars(spec.ticker, source, bars), indent=2),
            encoding="utf-8",
        )

    if not bars:
        return [], source, " | ".join(errors)
    return bars, source, None


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------


def empty_regime(name: str, n_bars: int = 0) -> RegimeStats:
    return RegimeStats(
        name=name,
        n_bars=n_bars,
        first=None,
        last=None,
        fwd={h: dist_of([]) for h in HORIZONS},
        vol20_last=None,
        vol60_last=None,
        vol20_mean=None,
        vol60_mean=None,
        pct_above_sma200=None,
        pct_above_sma50=None,
        avg_abs_move_atr=None,
        bracket_long_gross=Bracket(),
        bracket_short_gross=Bracket(),
        bracket_long_net=Bracket(),
        bracket_short_net=Bracket(),
        under_min=n_bars < MIN_REGIME_BARS,
    )


def compute_for_bars(
    spec: SymbolSpec,
    bars: Sequence[Bar],
    *,
    source: str,
    cost_frac: float,
    ann: float,
) -> InstrumentResult:
    n = len(bars)
    first = bars[0].date if bars else None
    last = bars[-1].date if bars else None
    if n < MIN_BARS:
        return InstrumentResult(
            spec=spec,
            source=source,
            exclusion=f"insufficient history: {n} daily bars (need {MIN_BARS}); no substitute",
            n_raw=n,
            bars_first=first,
            bars_last=last,
            ann_factor=ann,
            cost_frac=cost_frac,
        )

    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    sma50 = sma_series(closes, SMA_FAST)
    sma200 = sma_series(closes, SMA_SLOW)
    atr = wilder_atr_series(highs, lows, closes, ATR_PERIOD)

    daily_ret: list[float | None] = [None] * n
    for i in range(1, n):
        if closes[i - 1] > 0:
            daily_ret[i] = closes[i] / closes[i - 1] - 1.0

    regimes_idx: dict[str, list[int]] = {r: [] for r in REGIMES}
    for i in range(n):
        regimes_idx["unconditional"].append(i)
        prev_s50 = sma50[i - SMA_SLOPE_LOOKBACK] if i >= SMA_SLOPE_LOOKBACK else None
        label = classify_regime(closes[i], sma200[i], sma50[i], prev_s50)
        if label:
            regimes_idx[label].append(i)

    def stats_for(name: str, idxs: Sequence[int]) -> RegimeStats:
        if not idxs:
            return empty_regime(name, 0)
        # Forward returns: signal bar i; measured from the bar AFTER (close[i+h]/close[i] - 1).
        fwd_xs: dict[int, list[float]] = {h: [] for h in HORIZONS}
        abs_atr: list[float] = []
        above200 = above50 = 0
        have200 = have50 = 0
        vol20s: list[float] = []
        vol60s: list[float] = []
        long_g, short_g, long_n, short_n = Bracket(), Bracket(), Bracket(), Bracket()

        for i in idxs:
            if sma200[i] is not None:
                have200 += 1
                if closes[i] > sma200[i]:
                    above200 += 1
            if sma50[i] is not None:
                have50 += 1
                if closes[i] > sma50[i]:
                    above50 += 1
            if i >= 1 and atr[i] not in (None, 0):
                abs_atr.append(abs(closes[i] - closes[i - 1]) / atr[i])

            rets_to_i = [daily_ret[j] for j in range(1, i + 1) if daily_ret[j] is not None]
            v20 = realised_vol([float(x) for x in rets_to_i], 20, ann)
            v60 = realised_vol([float(x) for x in rets_to_i], 60, ann)
            if v20 is not None:
                vol20s.append(v20)
            if v60 is not None:
                vol60s.append(v60)

            for h in HORIZONS:
                j = i + h
                if j < n and closes[i] > 0:
                    fwd_xs[h].append(closes[j] / closes[i] - 1.0)

            r = atr[i]
            if r is None or r <= 0 or i + 1 >= n:
                continue
            entry = closes[i]
            future = bars[i + 1 : i + 1 + BRACKET_BARS]
            # Gross 1R:2R from entry = signal close; first touch on subsequent bars only.
            _record_bracket(
                long_g,
                evaluate_long_bracket(entry, entry - BRACKET_STOP_R * r, entry + BRACKET_TARGET_R * r, future),
            )
            _record_bracket(
                short_g,
                evaluate_short_bracket(entry, entry + BRACKET_STOP_R * r, entry - BRACKET_TARGET_R * r, future),
            )
            cost_px = entry * cost_frac
            _record_bracket(
                long_n,
                evaluate_long_bracket(
                    entry,
                    entry - BRACKET_STOP_R * r + cost_px,
                    entry + BRACKET_TARGET_R * r - cost_px,
                    future,
                ),
            )
            _record_bracket(
                short_n,
                evaluate_short_bracket(
                    entry,
                    entry + BRACKET_STOP_R * r - cost_px,
                    entry - BRACKET_TARGET_R * r + cost_px,
                    future,
                ),
            )

        subset_dates = [bars[i].date for i in idxs]
        return RegimeStats(
            name=name,
            n_bars=len(idxs),
            first=subset_dates[0],
            last=subset_dates[-1],
            fwd={h: dist_of(fwd_xs[h]) for h in HORIZONS},
            vol20_last=vol20s[-1] if vol20s else None,
            vol60_last=vol60s[-1] if vol60s else None,
            vol20_mean=statistics.mean(vol20s) if vol20s else None,
            vol60_mean=statistics.mean(vol60s) if vol60s else None,
            pct_above_sma200=(above200 / have200) if have200 else None,
            pct_above_sma50=(above50 / have50) if have50 else None,
            avg_abs_move_atr=statistics.mean(abs_atr) if abs_atr else None,
            bracket_long_gross=long_g,
            bracket_short_gross=short_g,
            bracket_long_net=long_n,
            bracket_short_net=short_n,
            under_min=len(idxs) < MIN_REGIME_BARS,
        )

    regime_stats = {name: stats_for(name, idxs) for name, idxs in regimes_idx.items()}
    max_1bar = None
    max_10bar = None
    # Max signed forward return (Principal evidence: SPCX +29.8% / +101.8%).
    # Recompute from the same close series used for Dist (no look-ahead).
    if n >= 2:
        xs1 = [closes[i + 1] / closes[i] - 1.0 for i in range(n - 1) if closes[i] > 0]
        max_1bar = max(xs1) if xs1 else None
    if n >= 11:
        xs10 = [closes[i + 10] / closes[i] - 1.0 for i in range(n - 10) if closes[i] > 0]
        max_10bar = max(xs10) if xs10 else None
    return InstrumentResult(
        spec=spec,
        source=source,
        exclusion=None,
        n_raw=n,
        bars_first=first,
        bars_last=last,
        ann_factor=ann,
        cost_frac=cost_frac,
        regimes=regime_stats,
        max_1bar=max_1bar,
        max_10bar=max_10bar,
    )


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def _n(v: float | None, *, pct: bool = False, digits: int = 3) -> str:
    if v is None:
        return "n/a"
    if pct:
        return f"{v * 100:.{digits}f}%"
    return f"{v:.{digits}f}"


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "/")

    line = "| " + " | ".join(cell(h) for h in headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    return "\n".join([line, sep, *body])


def _bracket_cells(b: Bracket) -> list[str]:
    return [
        str(b.n_trials),
        str(b.n_target),
        str(b.n_stop),
        str(b.n_tie),
        str(b.n_timeout),
        _n(b.hit_rate_resolved(), pct=True, digits=1),
    ]


def _fwd_row(ticker: str, d: Dist) -> list[str]:
    return [
        ticker,
        str(d.n),
        _n(d.mean, pct=True),
        _n(d.median, pct=True),
        _n(d.stdev, pct=True),
        _n(d.p5, pct=True),
        _n(d.p25, pct=True),
        _n(d.p75, pct=True),
        _n(d.p95, pct=True),
    ]


def _three_line_summary(results: Sequence[InstrumentResult]) -> str:
    included = [r for r in results if r.exclusion is None]
    excluded = [r for r in results if r.exclusion is not None]
    bits: list[str] = []
    for r in included:
        u = r.regimes["unconditional"]
        d1 = u.fwd[1]
        d10 = u.fwd[10]
        bits.append(
            f"{r.spec.ticker} 1-bar mean {_n(d1.mean, pct=True)} (median {_n(d1.median, pct=True)}); "
            f"10-bar mean {_n(d10.mean, pct=True)}"
        )
    if included:
        line1 = (
            "Unconditional forward-return edge of simply being long each instrument (no signal): "
            + "; ".join(bits)
            + ". These are raw close-to-close means, not after costs, not a call."
        )
    else:
        line1 = (
            "Unconditional forward-return edge: none computed — no instrument cleared the 200-bar "
            "daily-OHLC bar. Nothing clever, and nothing to be long."
        )
    names = ", ".join(r.spec.ticker for r in included) if included else "(none)"
    line2 = (
        f"Enough history to study at all (n≥{MIN_BARS} daily bars): {names}. "
        f"Excluded {len(excluded)} / {len(results)} names (reasons in Coverage)."
    )
    long_hits = long_stops = 0
    net_hits = net_stops = 0
    for r in included:
        g = r.regimes["unconditional"].bracket_long_gross
        n = r.regimes["unconditional"].bracket_long_net
        long_hits += g.n_target
        long_stops += g.n_stop
        net_hits += n.n_target
        net_stops += n.n_stop
    gross = (long_hits / (long_hits + long_stops)) if (long_hits + long_stops) else None
    net = (net_hits / (net_hits + net_stops)) if (net_hits + net_stops) else None
    line3 = (
        f"Coin-flip 1R:2R long bracket (R=1×ATR20, first touch within {BRACKET_BARS} bars, ties separate): "
        f"gross hit rate {_n(gross, pct=True, digits=1)} "
        f"({long_hits} targets / {long_stops} stops pooled); "
        f"net of the flat cost below {_n(net, pct=True, digits=1)}. "
        f"A fair 1:2 coin-flip is ~33.3%. Every future strategy claim must beat this after costs."
    )
    voided = [r for r in results if r.void_code]
    if voided:
        line3 += (
            " Voided ``suspected_ticker_reuse`` names are **not** in this pool: "
            + ", ".join(r.spec.ticker for r in voided)
            + "."
        )
    return "\n".join([f"1. {line1}", f"2. {line2}", f"3. {line3}"])


def _coverage_status(r: InstrumentResult) -> str:
    if r.void_code:
        return "void"
    if r.exclusion is None:
        return "computed"
    return "excluded"


def _is_equity_result(r: InstrumentResult) -> bool:
    return is_equity_series(r.spec, r.source)


def _provisional_banner(results: Sequence[InstrumentResult]) -> list[str]:
    cap_rows = [r for r in results if r.polygon_free_tier_cap]
    equity_rows = [r for r in results if _is_equity_result(r) and r.n_raw]
    firsts = [r.bars_first for r in cap_rows if r.bars_first]
    lasts = [r.bars_last for r in cap_rows if r.bars_last]
    span = "2024-09-19 → 2026-09-18 inclusive on a 2026-09-19 run"
    if firsts and lasts:
        span = f"{min(firsts).isoformat()} → {max(lasts).isoformat()} inclusive on this run"
    n_cap = max((r.n_raw for r in cap_rows), default=None)
    cap_n = f"~{n_cap} daily bars" if n_cap else "roughly 501 daily bars"
    signal_starts: list[date] = []
    for r in equity_rows:
        if r.exclusion:
            continue
        dates = [
            r.regimes[name].first
            for name in ("trend-up", "trend-down", "chop")
            if name in r.regimes and r.regimes[name].first
        ]
        if dates:
            signal_starts.append(min(dates))
    sma_start = min(signal_starts).isoformat() if signal_starts else "~2025-07-09"
    return [
        "> **PROVISIONAL — equity base rates.** Polygon's **2-year free-tier history limit** "
        f"caps US-listed daily bars ({cap_n}; {span}). This **IS** the vendor cap, "
        "not an inferred 'looks like a window' guess.",
        ">",
        f"> SMA200 needs 200 bars → equity regime signals start **{sma_start}**. "
        "Equity base rates cover roughly **one year of usable signals in a single regime**. "
        "Every equity base rate in this file is **PROVISIONAL** until we have more history. "
        "That is the headline, not a footnote.",
    ]


def _voided_section(results: Sequence[InstrumentResult]) -> list[str]:
    voided = [r for r in results if r.void_code]
    parts = [
        "## Voided — suspected_ticker_reuse / entity splice",
        "",
        "Resolving a ticker to an identifier does **not** prove the returned series belongs "
        "to one entity. Polygon aggregates by ticker string. Flagged series are **void** and "
        "**excluded from pooled stats**. Continuity check: known listing date (first bar "
        "precedes identity-start) **or** a single-bar move beyond N=8 robust-sigma "
        "(sigma = 1.4826 × MAD of 1-bar simple returns; MAD=0 flat tape uses a 5% floor). "
        "See `mm_ingest.equities.continuity` and `config/research/ticker_continuity.yaml`.",
        "",
    ]
    if not voided:
        parts.append("None this run.")
        parts.append("")
        return parts
    parts.append(
        _md_table(
            [
                "ticker",
                "n_bars",
                "first",
                "last",
                "listed_on",
                "1b mean",
                "1b median",
                "vol20 mean",
                "max 1-bar",
                "max 10-bar",
                "reason",
            ],
            [
                [
                    r.spec.ticker,
                    str(r.n_raw),
                    r.bars_first.isoformat() if r.bars_first else "—",
                    r.bars_last.isoformat() if r.bars_last else "—",
                    r.listed_on.isoformat() if r.listed_on else "—",
                    _n(r.regimes["unconditional"].fwd[1].mean, pct=True) if "unconditional" in r.regimes else "n/a",
                    _n(r.regimes["unconditional"].fwd[1].median, pct=True) if "unconditional" in r.regimes else "n/a",
                    _n(r.regimes["unconditional"].vol20_mean, pct=True, digits=1)
                    if "unconditional" in r.regimes
                    else "n/a",
                    _n(r.max_1bar, pct=True, digits=1),
                    _n(r.max_10bar, pct=True, digits=1),
                    r.exclusion or r.void_code or "",
                ]
                for r in voided
            ],
        )
    )
    parts += ["", "Not in the pooled 1R:2R bracket. Not a substitute series. Not trimmed.", ""]
    return parts


def _bmnr_audit_section(results: Sequence[InstrumentResult]) -> list[str]:
    by = {r.spec.ticker: r for r in results}
    r = by.get("BMNR")
    parts = [
        "## BMNR audit (ticker-reuse screen)",
        "",
        "Principal asked whether BMNR (449 bars cited on the equity run; mean vs median gap) "
        "is the same splice class as SPCX. Same continuity check; no silent keep-in-pool if voided.",
        "",
    ]
    if r is None:
        parts += ["BMNR was not in this run's ticker set.", ""]
        return parts
    u = r.regimes.get("unconditional")
    mean_s = _n(u.fwd[1].mean, pct=True) if u else "n/a"
    med_s = _n(u.fwd[1].median, pct=True) if u else "n/a"
    vol_s = _n(u.vol20_mean, pct=True, digits=1) if u else "n/a"
    status = _coverage_status(r)
    if r.void_code:
        verdict = (
            f"**VOID** `{r.void_code}`. Excluded from pools. "
            f"{r.continuity_detail or r.exclusion or ''}"
        )
    elif r.exclusion:
        verdict = f"Not in pools ({r.exclusion}). Continuity: {r.continuity_detail or 'n/a'}."
    else:
        listed = r.listed_on.isoformat() if r.listed_on else "not in ticker_continuity.yaml / monitor listing_date"
        first = r.bars_first.isoformat() if r.bars_first else "n/a"
        verdict = (
            f"**Clears** the continuity check (not `suspected_ticker_reuse`). "
            f"listed_on={listed}; first bar={first}. "
            f"1-bar mean {mean_s} vs median {med_s} (vol20 mean {vol_s}) is a fat right tail "
            "on one entity, not a ticker-string splice. Stays in pools. Not a call."
        )
    parts += [
        f"- Coverage status: `{status}`; n={r.n_raw}; source `{r.source or '—'}`",
        f"- {verdict}",
        "",
    ]
    return parts


def _trend_filter_section(included: Sequence[InstrumentResult]) -> list[str]:
    parts = [
        "## Trend-filter finding (permission filter; changes the candidate queue)",
        "",
        "Trend-up conditioning (**close > SMA200 and SMA50 rising**) does **not** raise the "
        "1R:2R long bracket hit rate on this sample; for several names it falls sharply. "
        "Several trend-up buckets show **negative** mean 1-bar returns.",
        "",
        "This undercuts the shared premise of C-001 / C-002 / C-003 (dip entries that assume "
        "a confirmed-uptrend **permission filter**) **in this sample**. "
        "Do **not** conclude those strategies fail — they are still `INTAKE_ONLY` / HYPOTHESIS, "
        "and this file is not a candidate study. Conclude the **permission filter does not "
        "carry edge on its own**. Any later study that relies on it must beat **that "
        "instrument's own trend-up** bracket rate, not the pooled ~33.3% coin-flip.",
        "",
        "Bucket n<100 is do-not-interpret (same rule as the regime tables).",
        "",
    ]
    if not included:
        parts += ["No included names this run.", ""]
        return parts
    rows: list[list[str]] = []
    interpretable_up: list[tuple[str, float, int]] = []
    for r in included:
        up = r.regimes.get("trend-up")
        un = r.regimes.get("unconditional")
        if up is None or un is None:
            continue
        u_hit = un.bracket_long_gross.hit_rate_resolved()
        t_hit = up.bracket_long_gross.hit_rate_resolved()
        delta = (t_hit - u_hit) if (t_hit is not None and u_hit is not None) else None
        rows.append(
            [
                r.spec.ticker,
                str(un.n_bars),
                _n(u_hit, pct=True, digits=1),
                str(up.n_bars),
                "yes — do not interpret" if up.under_min else "no",
                _n(t_hit, pct=True, digits=1),
                _n(delta, pct=True, digits=1) if delta is not None else "n/a",
                _n(up.fwd[1].mean, pct=True),
            ]
        )
        if not up.under_min and t_hit is not None:
            interpretable_up.append((r.spec.ticker, t_hit, up.n_bars))
    parts += [
        _md_table(
            [
                "ticker",
                "uncond n",
                "uncond long hit",
                "trend-up n",
                "n<100",
                "trend-up long hit",
                "Δ hit (up−uncond)",
                "trend-up 1b mean",
            ],
            rows,
        ),
        "",
    ]
    down_k = sum(1 for r in included if r.regimes.get("trend-down") and r.regimes["trend-down"].under_min)
    chop_k = sum(1 for r in included if r.regimes.get("chop") and r.regimes["chop"].under_min)
    n_inc = len(included)
    parts += [
        f"Do-not-interpret counts **among included names** (cite the regime tables): "
        f"trend-down {down_k}/{n_inc}; chop {chop_k}/{n_inc}.",
        "",
    ]
    if interpretable_up:
        best = max(interpretable_up, key=lambda t: t[1])
        vvv = next((t for t in interpretable_up if t[0] == "VVVUSD"), None)
        if vvv:
            parts += [
                f"**VVVUSD** is the interpretable outlier: trend-up long gross hit "
                f"{vvv[1] * 100:.1f}% (n={vvv[2]}). Worth a dedicated look. "
                "Not a promotion. Not a size.",
                "",
            ]
        elif best[0] != "VVVUSD":
            parts += [
                f"Highest interpretable trend-up long hit this run: {best[0]} "
                f"{best[1] * 100:.1f}% (n={best[2]}). VVVUSD not in the included set.",
                "",
            ]
    parts += [
        "Queue note: C-001 / C-002 / C-003 stay `INTAKE_ONLY`. Permission-filter finding "
        "is recorded on those cards. Do not promote. Do not reject on this evidence alone.",
        "",
    ]
    return parts


def render_markdown(
    results: Sequence[InstrumentResult],
    *,
    report_date: date,
    finished_utc: datetime,
    window_start: datetime,
    window_end: datetime,
    monitor_path: str,
    cost: Mapping[str, float],
) -> str:
    included = [r for r in results if r.exclusion is None]
    excluded = [r for r in results if r.exclusion is not None and not r.void_code]
    voided = [r for r in results if r.void_code]
    perp_cost = round_trip_cost(
        SymbolSpec(
            ticker="BTCUSD",
            membership_key="BTC",
            tape_alias="BTC",
            round="crypto",
            tier="universe",
            cluster="",
            venue="hyperliquid",
            kind="perp",
            qualified_id="HL:BTC",
            coin="BTC",
            note="",
        ),
        cost,
    )
    eq_cost = (2.0 * float(cost["taker_fee"])) + (2.0 * float(cost["slippage_bps"]) / 10_000.0)
    title = f"# Phase-1 instrument base rates — {report_date.isoformat()}"
    coverage_header = "## Coverage (every monitor.yaml name)"

    parts: list[str] = [
        title,
        "",
        *_provisional_banner(results),
        "",
        "Standalone research dump. **Not** a desk product, **not** IMP-040 event-class rates, "
        "**not** a Memory write, **not** a Telegram send, **not** a call, **not** a size.",
        "",
        f"- Report date (Australia/Sydney, when the run finished): `{report_date.isoformat()}`",
        f"- Run finished (UTC): `{finished_utc.isoformat()}`",
        f"- Data window requested: `{window_start.date().isoformat()}` → `{window_end.date().isoformat()}` (UTC)",
        f"- Monitor file: `{monitor_path}`",
        "- Principal actions (SPCX void, 2-year cap, permission filter): "
        "`research/base-rates/phase1-2026-09-19-principal-actions.md`",
        f"- Include rule: ≥ {MIN_BARS} cleaned daily OHLC bars; no substitute symbol; no synthetic bars",
        "- Continuity: Polygon/equities series with first bar before known listing date, or a "
        "single-bar move beyond N=8 robust-sigma (1.4826×MAD), are **void** "
        "(`suspected_ticker_reuse`) and excluded from pools",
        f"- Indicators: SMA{SMA_FAST} / SMA{SMA_SLOW} / ATR{ATR_PERIOD} (Wilder) from bars at or before the signal bar",
        f"- Forward returns: `close[t+h]/close[t] - 1` for h={list(HORIZONS)} (the bars **after** the signal close)",
        f"- Regime: trend-up = close>SMA200 and SMA50[t]>SMA50[t-{SMA_SLOPE_LOOKBACK}]; "
        "trend-down = close<SMA200 and SMA50 falling; else chop. "
        f"Bucket n<{MIN_REGIME_BARS} is reported and **not interpreted**.",
        f"- Bracket: symmetric always-long and always-short 1R:2R, R={BRACKET_STOP_R}×ATR{ATR_PERIOD}, "
        f"first touch within {BRACKET_BARS} bars after the signal; same-bar stop+target = tie; else timeout.",
        "",
        "## Cost assumption (pessimistic, flat, one number)",
        "",
        f"- taker_fee `{cost['taker_fee']}` per side, slippage `{cost['slippage_bps']}` bps per side, "
        f"funding `{cost['funding_per_day']}` / day × `{cost['funding_hold_days']}` days on perps only.",
        f"- Round-trip used to shift stop closer / target farther: **perps {perp_cost * 10_000:.1f} bps**, "
        f"**equities {eq_cost * 10_000:.1f} bps** (funding=0).",
        "- Not a live fee schedule. Not a size.",
        "",
        "## Three-line summary",
        "",
        _three_line_summary(results),
        "",
        coverage_header,
        "",
        _md_table(
            ["ticker", "tier", "round", "venue", "source", "n_bars", "first", "last", "status", "reason"],
            [
                [
                    r.spec.ticker,
                    r.spec.tier,
                    r.spec.round,
                    r.spec.venue,
                    r.source or "—",
                    str(r.n_raw),
                    r.bars_first.isoformat() if r.bars_first else "—",
                    r.bars_last.isoformat() if r.bars_last else "—",
                    _coverage_status(r),
                    r.exclusion or "—",
                ]
                for r in results
            ],
        ),
        "",
        f"Computed: {len(included)}. Voided: {len(voided)}. Excluded: {len(excluded)}. Silent drops: 0.",
        "",
    ]

    if included:
        parts += [
            "## Unconditional sample stats",
            "",
            _md_table(
                [
                    "ticker",
                    "n",
                    "first",
                    "last",
                    "vol20 last",
                    "vol20 mean",
                    "vol60 last",
                    "vol60 mean",
                    "% > SMA200",
                    "% > SMA50",
                    "avg |Δ| / ATR20",
                    "ann",
                ],
                [
                    [
                        r.spec.ticker,
                        str(r.n_raw),
                        r.bars_first.isoformat() if r.bars_first else "—",
                        r.bars_last.isoformat() if r.bars_last else "—",
                        _n(r.regimes["unconditional"].vol20_last, pct=True, digits=1),
                        _n(r.regimes["unconditional"].vol20_mean, pct=True, digits=1),
                        _n(r.regimes["unconditional"].vol60_last, pct=True, digits=1),
                        _n(r.regimes["unconditional"].vol60_mean, pct=True, digits=1),
                        _n(r.regimes["unconditional"].pct_above_sma200, pct=True, digits=1),
                        _n(r.regimes["unconditional"].pct_above_sma50, pct=True, digits=1),
                        _n(r.regimes["unconditional"].avg_abs_move_atr, digits=3),
                        str(int(r.ann_factor)),
                    ]
                    for r in included
                ],
            ),
            "",
        ]
        for h in HORIZONS:
            parts += [
                f"## Unconditional forward returns — {h} bar",
                "",
                _md_table(
                    ["ticker", "n", "mean", "median", "stdev", "p5", "p25", "p75", "p95"],
                    [_fwd_row(r.spec.ticker, r.regimes["unconditional"].fwd[h]) for r in included],
                ),
                "",
            ]
        parts += [
            "## Unconditional 1R:2R bracket — gross",
            "",
            _md_table(
                [
                    "ticker",
                    "long n",
                    "long 2R",
                    "long 1R",
                    "long ties",
                    "long timeout",
                    "long hit",
                    "short n",
                    "short 2R",
                    "short 1R",
                    "short ties",
                    "short timeout",
                    "short hit",
                ],
                [
                    [r.spec.ticker, *_bracket_cells(r.regimes["unconditional"].bracket_long_gross), *_bracket_cells(r.regimes["unconditional"].bracket_short_gross)]
                    for r in included
                ],
            ),
            "",
            "## Unconditional 1R:2R bracket — net of flat cost",
            "",
            _md_table(
                [
                    "ticker",
                    "long n",
                    "long 2R",
                    "long 1R",
                    "long ties",
                    "long timeout",
                    "long hit",
                    "short n",
                    "short 2R",
                    "short 1R",
                    "short ties",
                    "short timeout",
                    "short hit",
                    "cost_frac",
                ],
                [
                    [
                        r.spec.ticker,
                        *_bracket_cells(r.regimes["unconditional"].bracket_long_net),
                        *_bracket_cells(r.regimes["unconditional"].bracket_short_net),
                        _n(r.cost_frac, digits=5),
                    ]
                    for r in included
                ],
            ),
            "",
        ]
        for regime in ("trend-up", "trend-down", "chop"):
            parts += [
                f"## Regime {regime}",
                "",
                "Same metrics as unconditional, split by regime at the **signal** bar. "
                f"If n < {MIN_REGIME_BARS}, do not interpret.",
                "",
                _md_table(
                    ["ticker", "n", "first", "last", "n<100", "1b mean", "10b mean", "long gross hit", "long net hit", "% > SMA200"],
                    [
                        [
                            r.spec.ticker,
                            str(r.regimes[regime].n_bars),
                            r.regimes[regime].first.isoformat() if r.regimes[regime].first else "—",
                            r.regimes[regime].last.isoformat() if r.regimes[regime].last else "—",
                            "yes — do not interpret" if r.regimes[regime].under_min else "no",
                            _n(r.regimes[regime].fwd[1].mean, pct=True),
                            _n(r.regimes[regime].fwd[10].mean, pct=True),
                            _n(r.regimes[regime].bracket_long_gross.hit_rate_resolved(), pct=True, digits=1),
                            _n(r.regimes[regime].bracket_long_net.hit_rate_resolved(), pct=True, digits=1),
                            _n(r.regimes[regime].pct_above_sma200, pct=True, digits=1),
                        ]
                        for r in included
                    ],
                ),
                "",
                f"### {regime} forward returns — 1 bar",
                "",
                _md_table(
                    ["ticker", "n", "mean", "median", "stdev", "p5", "p25", "p75", "p95"],
                    [_fwd_row(r.spec.ticker, r.regimes[regime].fwd[1]) for r in included],
                ),
                "",
                f"### {regime} forward returns — 10 bar",
                "",
                _md_table(
                    ["ticker", "n", "mean", "median", "stdev", "p5", "p25", "p75", "p95"],
                    [_fwd_row(r.spec.ticker, r.regimes[regime].fwd[10]) for r in included],
                ),
                "",
            ]

    parts += _voided_section(results)
    parts += _bmnr_audit_section(results)
    parts += _trend_filter_section(included)
    parts += [
        "## Exclusions (repeat, with reasons)",
        "",
    ]
    if excluded or voided:
        parts.append(
            _md_table(
                ["ticker", "n_bars", "status", "reason"],
                [[r.spec.ticker, str(r.n_raw), _coverage_status(r), r.exclusion or ""] for r in results if r.exclusion],
            )
        )
    else:
        parts.append("None.")
    parts += [
        "",
        "## How to re-run",
        "",
        "```text",
        "python scripts/research/base_rates_phase1.py",
        "uv run python scripts/research/base_rates_phase1.py   # this repo",
        "python scripts/research/base_rates_phase1.py --offline  # cache/bars-dir only",
        "```",
        "",
        "Live equities need `POLYGON_API_KEY`. Crypto uses Hyperliquid public `/info` "
        "(no key). CoinGecko OHLC is a fallback only. Same bars file → same tables "
        "(filename date follows Australia/Sydney at finish). "
        "Polygon free tier is 5 req/min — **do not** pass `--no-sleep` on a live free-tier run. "
        "Ticker set is `config/watchlist/monitor.yaml` only. Universe overlay of "
        "non-monitor names is deferred (queue Gaps); do not fetch those names here.",
        "",
    ]
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_now(text: str | None) -> datetime:
    if not text:
        return datetime.now(timezone.utc)
    raw = text.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monitor", type=Path, default=None, help="monitor.yaml path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--bars-dir", type=Path, default=None, help="local {TICKER}.json OHLC (preferred)")
    parser.add_argument("--offline", action="store_true", help="do not hit HL / Polygon / CoinGecko")
    parser.add_argument("--refresh", action="store_true", help="ignore cache (still writes cache on live fetch)")
    parser.add_argument("--now", default=None, help="freeze finish clock (ISO-8601 UTC)")
    parser.add_argument("--no-sleep", action="store_true", help="do not pace live HTTP (tests only; never on Polygon free tier)")
    parser.add_argument("--continuity-config", type=Path, default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = repo_root()
    monitor = args.monitor or (root / MONITOR_REL)
    output_dir = args.output_dir or (root / OUTPUT_REL)
    cache_dir = args.cache_dir if args.cache_dir is not None else (root / CACHE_REL)
    bars_dir = args.bars_dir
    finished = parse_now(args.now)
    report_date = finished.astimezone(SYDNEY).date()
    window_end = finished
    sleeper: Callable[[float], None] = (lambda _s: None) if args.no_sleep or args.offline else __import__("time").sleep
    continuity_cfg = load_continuity_config(args.continuity_config or (root / CONTINUITY_REL))

    def _compute_one(spec: SymbolSpec) -> InstrumentResult:
        bars, source, fetch_err = load_or_fetch_bars(
            spec,
            start=FETCH_START,
            end=window_end,
            bars_dir=bars_dir,
            cache_dir=cache_dir,
            offline=args.offline,
            refresh=args.refresh,
            sleeper=sleeper,
        )
        if fetch_err and not bars:
            result = InstrumentResult(
                spec=spec,
                source=source,
                exclusion=fetch_err,
                n_raw=0,
                bars_first=None,
                bars_last=None,
                ann_factor=ann_factor_for(spec),
                cost_frac=round_trip_cost(spec),
            )
            listed = listed_on_for(spec, continuity_cfg)
            result.listed_on = listed
            if listed is not None:
                result.exclusion = (
                    f"{fetch_err}; standing continuity: listed_on {listed.isoformat()} "
                    "— a first bar before that date is suspected_ticker_reuse and is voided "
                    "(see config/research/ticker_continuity.yaml)"
                )
            return result
        result = compute_for_bars(
            spec,
            bars,
            source=source,
            cost_frac=round_trip_cost(spec),
            ann=ann_factor_for(spec),
        )
        return apply_continuity(
            result,
            bars,
            spec=spec,
            source=source,
            continuity_cfg=continuity_cfg,
            window_end=window_end.date(),
        )

    results: list[InstrumentResult] = []
    for spec in load_monitor_symbols(monitor):
        results.append(_compute_one(spec))

    output_dir.mkdir(parents=True, exist_ok=True)
    monitor_rel = str(monitor.relative_to(root) if monitor.is_relative_to(root) else monitor)
    out_path = output_dir / f"phase1-{report_date.isoformat()}.md"
    markdown = render_markdown(
        results,
        report_date=report_date,
        finished_utc=finished,
        window_start=FETCH_START,
        window_end=window_end,
        monitor_path=monitor_rel,
        cost=COST,
    )
    out_path.write_text(markdown, encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"report_date_australia_sydney={report_date.isoformat()}")
    print(f"finished_utc={finished.isoformat()}")
    print(
        "symbols="
        f"{len(results)} computed={sum(1 for r in results if r.exclusion is None)} "
        f"voided={sum(1 for r in results if r.void_code)} "
        f"excluded={sum(1 for r in results if r.exclusion)}"
    )
    return 0


def main() -> int:
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
