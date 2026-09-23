"""One-off history backfill for a fresh Market Memory database.

Polygon daily bars, full FRED DGS10/DGS2, and Hyperliquid daily candles.
Does not change ``lab ingest`` (hourly HL window) or the live brief fetch
(``limit`` 2). No signing. No Telegram.

Sequence: after ``lab migrate``, before recurring ingest-persist.
Dispatch stays gated in GitHub Actions (``i_mean_it_backfill`` default false).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mm_common.http import ERROR_NONE
from mm_common.schemas import ObservationEnvelope
from mm_common.time import to_unix_ms, utcnow
from mm_ingest.config import load_ingest_settings, load_instruments, load_yaml, repo_root
from mm_ingest.equities.interface import EquitiesQuery
from mm_ingest.equities.normalize import normalize_ohlcv_bars
from mm_ingest.equities.polygon import PolygonEquitiesAdapter
from mm_ingest.hl_info import HyperliquidInfoClient, HyperliquidInfoError
from mm_ingest.macro import fetch_fred_series
from mm_ingest.pipeline import persist_envelopes
from mm_ingest.rate_limit import RateLimitBudget, retry_from_settings
from mm_ingest.sources import POLYGON_BASE_URL
from mm_memory.models import Observation
from mm_memory.object_store import ObjectStore
from mm_provenance.normalize import normalize_candles

# Free-tier calendar cap already used by the phase-1 base-rate script.
POLYGON_LOOKBACK_CALENDAR_DAYS = 730
# Vendor max page size. ~500 daily sessions in 730 calendar days fit in one page.
POLYGON_BACKFILL_AGG_LIMIT = 50000
POLYGON_ENDPOINT = (
    "GET https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
    "?adjusted=true&limit=50000"
)

# Legs of 2s10s. The spread is not stored; DGS10 minus DGS2 is derivable.
FRED_BACKFILL_SERIES: dict[str, str] = {"US10Y": "DGS10", "US2Y": "DGS2"}
FRED_ENDPOINT = "GET https://api.stlouisfed.org/fred/series/observations"

# Crypto trades every calendar day. 90 days is more than 60 daily sessions.
HL_DAILY_INTERVAL = "1d"
HL_DAILY_LOOKBACK_DAYS = 90
HL_MIN_SESSIONS = 60
# Confirmed on a public candleSnapshot (interval 1d): open time is `t` (unix ms).
# `T` is the candle close time. `i` is the interval. `s` is the coin. `c` is the close.
HL_CANDLE_OPEN_TIME_FIELD = "t"
HL_ENDPOINT = "POST https://api.hyperliquid.xyz/info type=candleSnapshot"


@dataclass
class MinutePacer:
    """Sleep only when the next call would exceed ``max_per_minute`` in this window.

    ``RateLimitBudget`` counts and then refuses. It does not wait for the next
    minute. This pacer is the wait. With four Polygon tickers and a budget of
    five, ``acquire`` does not sleep.
    """

    max_per_minute: int
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    slept_s: float = 0.0
    _window_started: float | None = None
    _used: int = 0

    def acquire(self) -> None:
        now = self.clock()
        if self._window_started is None or (now - self._window_started) >= 60.0:
            self._window_started = now
            self._used = 0
        limit = max(1, int(self.max_per_minute))
        if self._used >= limit:
            wait = 60.0 - (now - self._window_started)
            if wait > 0:
                self.sleep(wait)
                self.slept_s += wait
            self._window_started = self.clock()
            self._used = 0
        self._used += 1


@dataclass
class HistoryBackfillPlan:
    polygon_tickers: tuple[str, ...]
    polygon_slots: tuple[str, ...]
    polygon_rpm: int
    fred_series: dict[str, str]
    fred_rpm: int
    hl_coins: tuple[str, ...]
    hl_rpm: int
    as_of: str
    polygon_start: str
    polygon_end: str
    hl_start: str
    hl_end: str

    @property
    def polygon_calls(self) -> int:
        return len(self.polygon_tickers)

    @property
    def fred_calls(self) -> int:
        # One request per series. Both series are far under FRED's 100000 default.
        return len(self.fred_series)

    @property
    def hl_calls(self) -> int:
        # 90 daily bars is under the 500-row page in iter_candles, so one POST per coin.
        return len(self.hl_coins)

    @property
    def polygon_multi_minute(self) -> bool:
        return self.polygon_calls > max(1, self.polygon_rpm)

    def as_public_dict(self) -> dict[str, Any]:
        if self.polygon_multi_minute:
            batches = (self.polygon_calls + self.polygon_rpm - 1) // self.polygon_rpm
            polygon_duration = (
                f"{self.polygon_calls} calls at {self.polygon_rpm}/min needs about "
                f"{batches} minute(s). MinutePacer sleeps until the window resets. "
                "http_get still retries 429/5xx (max_attempts 5, backoff_s 0.25, ceiling 8s)."
            )
        else:
            polygon_duration = (
                f"{self.polygon_calls} calls at {self.polygon_rpm} req/min fit in one minute. "
                "Not multi-minute. MinutePacer does not sleep. "
                "http_get still retries 429/5xx (max_attempts 5, backoff_s 0.25, ceiling 8s)."
            )
        return {
            "sequence": "after lab migrate on the fresh database, before recurring ingest-persist",
            "do_not_run": "DO NOT RUN until the Principal says so after the Thursday unattended fire",
            "polygon": {
                "endpoint": POLYGON_ENDPOINT,
                "adjusted": True,
                "agg_limit": POLYGON_BACKFILL_AGG_LIMIT,
                "lookback_calendar_days": POLYGON_LOOKBACK_CALENDAR_DAYS,
                "start": self.polygon_start,
                "end": self.polygon_end,
                "slots": list(self.polygon_slots),
                "tickers": list(self.polygon_tickers),
                "approx_api_calls": self.polygon_calls,
                "rate_limit_per_minute": self.polygon_rpm,
                "rate_limit_duration": polygon_duration,
                "timestamp_field": "t (unix ms)",
                "metric": "ohlcv_close",
                "pagination": (
                    "one GET per ticker; adapter does not follow next_url. "
                    f"limit={POLYGON_BACKFILL_AGG_LIMIT} holds this daily window."
                ),
            },
            "fred": {
                "endpoint": FRED_ENDPOINT,
                "series": dict(self.fred_series),
                "lookback": "full series (limit omitted; API default 100000). Not limit=5.",
                "approx_api_calls": self.fred_calls,
                "rate_limit_per_minute": self.fred_rpm,
                "rate_limit_duration": (
                    f"{self.fred_calls} calls at {self.fred_rpm} req/min. One page each. Not multi-minute."
                ),
                "timestamp_field": "observations[].date at T00:00:00Z",
                "metric": "fred_observation",
                "spread": "2s10s is DGS10 minus DGS2. This job does not write a spread row.",
                "brief_unchanged": "live brief fetch remains limit=2 for the series in config/briefing/macro.yaml",
            },
            "hyperliquid": {
                "endpoint": HL_ENDPOINT,
                "interval": HL_DAILY_INTERVAL,
                "lookback_calendar_days": HL_DAILY_LOOKBACK_DAYS,
                "min_sessions": HL_MIN_SESSIONS,
                "start": self.hl_start,
                "end": self.hl_end,
                "coins": list(self.hl_coins),
                "approx_api_calls": self.hl_calls,
                "rate_limit_per_minute": self.hl_rpm,
                "rate_limit_duration": (
                    f"{self.hl_calls} POSTs at {self.hl_rpm} req/min. One page each "
                    "(under the 500-row cursor). Not multi-minute. "
                    "Client retries timeout/429/5xx with the ingest.yaml backoff."
                ),
                "timestamp_field": (
                    f"{HL_CANDLE_OPEN_TIME_FIELD} unix ms open time "
                    "(response also has T close ms, s coin, i interval, c close)"
                ),
                "metric": "candle_close",
            },
            "idempotency": (
                "Same claim_hash is not a second observation row. "
                "put_observation selects on claim_hash and inserts ON CONFLICT DO NOTHING "
                "on observation_claim_hash_uidx. claim_hash excludes ingested_at. "
                "A revised value is a new claim_hash and a contradicts link, not an in-place update. "
                "This job skips the raw-object put when that claim_hash already exists."
            ),
            "as_of": self.as_of,
        }


@dataclass
class HistoryCollectResult:
    envelopes: list[ObservationEnvelope] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    polygon_bars: dict[str, int] = field(default_factory=dict)
    fred_rows: dict[str, int] = field(default_factory=dict)
    hl_sessions: dict[str, int] = field(default_factory=dict)
    calls: dict[str, int] = field(default_factory=dict)
    pacer_slept_s: float = 0.0

    def hl_below_minimum(self) -> dict[str, int]:
        return {coin: count for coin, count in self.hl_sessions.items() if count < HL_MIN_SESSIONS}

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "errors": list(self.errors),
            "polygon_bars": dict(self.polygon_bars),
            "fred_rows": dict(self.fred_rows),
            "hl_sessions": dict(self.hl_sessions),
            "hl_below_minimum": self.hl_below_minimum(),
            "calls": dict(self.calls),
            "pacer_slept_s": self.pacer_slept_s,
            "envelopes": len(self.envelopes),
        }


def brief_polygon_slots(macro: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    """Tape/brief equity slots from ``live.polygon.symbols``. VIX stays structural."""
    live = macro.get("live") if isinstance(macro.get("live"), dict) else {}
    polygon = live.get("polygon") if isinstance(live, dict) else {}
    symbols = polygon.get("symbols") if isinstance(polygon, dict) else {}
    if not isinstance(symbols, dict):
        return ()
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for slot, meta in symbols.items():
        if isinstance(meta, dict):
            ticker = str(meta.get("ticker") or "").strip().upper()
        else:
            ticker = str(meta or "").strip().upper()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        out.append((str(slot).upper(), ticker))
    return tuple(out)


def history_backfill_plan(
    *,
    now: datetime | None = None,
    repo: Path | None = None,
) -> HistoryBackfillPlan:
    root = repo or repo_root()
    moment = now or utcnow()
    settings = load_ingest_settings(root / "config" / "ingest.yaml")
    limits = settings.get("rate_limits") if isinstance(settings.get("rate_limits"), dict) else {}
    polygon_rpm = _rpm(limits, "polygon", default=5)
    fred_rpm = _rpm(limits, "fred", default=20)
    hl_rpm = _rpm(limits, "hyperliquid", default=60)
    macro = load_yaml(root / "config" / "briefing" / "macro.yaml")
    slots = brief_polygon_slots(macro)
    end_day = moment.date()
    start_day = end_day - timedelta(days=POLYGON_LOOKBACK_CALENDAR_DAYS)
    hl_start = moment - timedelta(days=HL_DAILY_LOOKBACK_DAYS)
    return HistoryBackfillPlan(
        polygon_tickers=tuple(ticker for _slot, ticker in slots),
        polygon_slots=tuple(f"{slot}:{ticker}" for slot, ticker in slots),
        polygon_rpm=polygon_rpm,
        fred_series=dict(FRED_BACKFILL_SERIES),
        fred_rpm=fred_rpm,
        hl_coins=tuple(load_instruments(root / "config" / "instruments" / "perps.yaml")),
        hl_rpm=hl_rpm,
        as_of=moment.isoformat(),
        polygon_start=start_day.isoformat(),
        polygon_end=end_day.isoformat(),
        hl_start=hl_start.isoformat(),
        hl_end=moment.isoformat(),
    )


def collect_history_backfill(
    plan: HistoryBackfillPlan,
    *,
    ingested_at: datetime,
    polygon: PolygonEquitiesAdapter,
    hl_client: HyperliquidInfoClient,
    env: dict[str, str] | None = None,
    fred_budget: RateLimitBudget | None = None,
    pacer: MinutePacer | None = None,
    stale_after_seconds: int = 120,
) -> HistoryCollectResult:
    """HTTP only. Does not open Postgres."""
    result = HistoryCollectResult()
    pace = pacer or MinutePacer(max_per_minute=plan.polygon_rpm)
    start = datetime.fromisoformat(plan.polygon_start + "T00:00:00+00:00")
    end = datetime.fromisoformat(plan.polygon_end + "T00:00:00+00:00")
    for ticker in plan.polygon_tickers:
        pace.acquire()
        polygon.last_error_class = ERROR_NONE
        polygon.last_notes = ()
        bars = polygon.ohlcv_daily(
            EquitiesQuery(
                tickers=(ticker,),
                start=start,
                end=end,
                ingested_at=ingested_at,
                include_intraday=False,
                include_corporate_actions=False,
                include_earnings=False,
            )
        )
        result.calls["polygon"] = result.calls.get("polygon", 0) + 1
        if polygon.last_error_class != ERROR_NONE:
            result.errors.append(f"polygon {ticker} error_class={polygon.last_error_class}")
            continue
        if not bars:
            result.errors.append(f"polygon {ticker} returned 0 bars")
            continue
        result.polygon_bars[ticker] = len(bars)
        result.envelopes.extend(
            normalize_ohlcv_bars(bars, ingested_at=ingested_at, stale_after_seconds=stale_after_seconds)
        )

    fred_limiter = fred_budget or RateLimitBudget(name="fred", max_requests_per_minute=plan.fred_rpm)
    fred_envs, fred_error = fetch_fred_series(
        series=plan.fred_series,
        ingested_at=ingested_at,
        env=env,
        budget=fred_limiter,
        stale_after_seconds=stale_after_seconds,
        limit=None,
        page_all=True,
    )
    result.calls["fred"] = fred_limiter.used
    real_fred = [row for row in fred_envs if row.metric == "fred_observation"]
    if fred_error != ERROR_NONE or len(real_fred) != len(fred_envs) or not real_fred:
        result.errors.append(f"fred error_class={fred_error} rows={len(real_fred)}")
    else:
        for row in real_fred:
            result.fred_rows[row.instrument] = result.fred_rows.get(row.instrument, 0) + 1
        missing = [symbol for symbol in plan.fred_series if symbol not in result.fred_rows]
        if missing:
            result.errors.append("fred missing series " + ",".join(missing))
        else:
            result.envelopes.extend(real_fred)

    hl_start_ms = to_unix_ms(datetime.fromisoformat(plan.hl_start))
    hl_end_ms = to_unix_ms(datetime.fromisoformat(plan.hl_end))
    for coin in plan.hl_coins:
        try:
            rows = hl_client.iter_candles(coin, HL_DAILY_INTERVAL, hl_start_ms, hl_end_ms)
        except HyperliquidInfoError as exc:
            result.calls["hyperliquid"] = result.calls.get("hyperliquid", 0) + 1
            result.errors.append(f"hyperliquid {coin} {exc}")
            continue
        result.calls["hyperliquid"] = result.calls.get("hyperliquid", 0) + 1
        candles = normalize_candles(rows, ingested_at=ingested_at, stale_after_seconds=stale_after_seconds)
        result.hl_sessions[coin] = len(candles)
        if not candles:
            result.errors.append(f"hyperliquid {coin} returned 0 daily candles")
            continue
        result.envelopes.extend(candles)
    result.pacer_slept_s = pace.slept_s
    return result


def persist_history_envelopes(
    session: Session,
    envelopes: list[ObservationEnvelope],
    *,
    object_store: ObjectStore | None = None,
) -> Any:
    """Persist claims. An existing ``claim_hash`` does not write another row or raw object."""
    fresh: list[ObservationEnvelope] = []
    seen: set[str] = set()
    duplicate_envelopes = 0
    for envelope in envelopes:
        if envelope.claim_hash in seen:
            duplicate_envelopes += 1
            continue
        seen.add(envelope.claim_hash)
        existing = session.scalar(select(Observation).where(Observation.claim_hash == envelope.claim_hash))
        if existing is not None:
            duplicate_envelopes += 1
            continue
        fresh.append(envelope)
    stats = persist_envelopes(session, fresh, object_store=object_store)
    stats.duplicates += duplicate_envelopes
    stats.envelopes = len(envelopes)
    return stats


def _rpm(limits: Any, name: str, *, default: int) -> int:
    spec = limits.get(name) if isinstance(limits, dict) else None
    if isinstance(spec, dict) and spec.get("max_requests_per_minute") is not None:
        return int(spec["max_requests_per_minute"])
    return default


def polygon_adapter_for_plan(
    plan: HistoryBackfillPlan,
    *,
    env: dict[str, str] | None = None,
    settings: dict[str, Any] | None = None,
) -> PolygonEquitiesAdapter:
    loaded = settings if settings is not None else load_ingest_settings()
    attempts, backoff, _ceiling = retry_from_settings(loaded, "polygon")
    equities = loaded.get("equities") if isinstance(loaded.get("equities"), dict) else {}
    base = str(equities.get("base_url") or POLYGON_BASE_URL)
    # Size the in-process counter to this one-shot. It does not reset each minute.
    # MinutePacer enforces config/ingest.yaml's 5/min.
    budget = RateLimitBudget(name="polygon", max_requests_per_minute=max(plan.polygon_calls, 1))
    return PolygonEquitiesAdapter(
        base_url=base,
        env=env,
        max_attempts=attempts,
        backoff_s=backoff,
        budget=budget,
        agg_limit=POLYGON_BACKFILL_AGG_LIMIT,
    )


def hl_client_for_settings(settings: dict[str, Any] | None = None) -> HyperliquidInfoClient:
    loaded = settings if settings is not None else load_ingest_settings()
    attempts, backoff, ceiling = retry_from_settings(loaded, "hyperliquid")
    return HyperliquidInfoClient(
        url=str(loaded.get("info_url")),
        max_attempts=attempts,
        backoff_s=backoff,
        backoff_ceiling_s=ceiling,
    )
