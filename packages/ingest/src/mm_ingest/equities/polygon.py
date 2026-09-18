"""Polygon.io default equities adapter (Principal lock). Env key only.

Read-only REST. No order endpoints. Degrade-never-invent.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

import httpx

from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_TIMEOUT,
    ERROR_MISSING_ENV,
    ERROR_NONE,
    ERROR_PARSE,
    ERROR_RATE_LIMITED,
    http_get,
    missing_env_notes,
)
from mm_common.time import from_unix_ms, parse_utc
from mm_ingest.equities.interface import DEFAULT_EQUITIES_VENDOR, EquitiesQuery
from mm_ingest.equities.models import CorporateAction, EarningsEvent, OHLCVBar
from mm_ingest.rate_limit import RateLimitBudget
from mm_ingest.sources import POLYGON_BASE_URL, POLYGON_SOURCE_NAME

API_KEY_ENV = "POLYGON_API_KEY"
DAILY_PATH = "/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start}/{end}"
DIVIDENDS_PATH = "/v3/reference/dividends"
SPLITS_PATH = "/v3/reference/splits"
# Documented reference events. Free/starter plans often 403/404 — classify, never invent.
EVENTS_PATH = "/vX/reference/tickers/{ticker}/events"


class PolygonEquitiesAdapter:
    """Default EquitiesAdapter. Ask is N/A — Principal already chose Polygon."""

    vendor = DEFAULT_EQUITIES_VENDOR
    source_name = POLYGON_SOURCE_NAME
    api_key_env = API_KEY_ENV

    def __init__(
        self,
        *,
        base_url: str = POLYGON_BASE_URL,
        api_key: str | None = None,
        env: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_s: float = 0.25,
        budget: RateLimitBudget | None = None,
        sleep: Callable[[float], None] | None = None,
        daily_multiplier: int = 1,
        daily_timespan: str = "day",
        intraday_multiplier: int = 5,
        intraday_timespan: str = "minute",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._env = dict(env) if env is not None else None
        self._api_key = api_key
        self._owns = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)
        self._max_attempts = max_attempts
        self._backoff_s = backoff_s
        self._sleep = sleep
        self.budget = budget or RateLimitBudget(name="polygon", max_requests_per_minute=5)
        self.daily_multiplier = daily_multiplier
        self.daily_timespan = daily_timespan
        self.intraday_multiplier = intraday_multiplier
        self.intraday_timespan = intraday_timespan
        self.last_error_class = ERROR_NONE
        self.last_notes: tuple[str, ...] = ()

    def close(self) -> None:
        if self._owns:
            self._http.close()

    def __enter__(self) -> PolygonEquitiesAdapter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def resolve_api_key(self) -> str | None:
        if self._api_key:
            return self._api_key
        if self._env is not None:
            raw = self._env.get(self.api_key_env)
        else:
            raw = os.environ.get(self.api_key_env)
        if raw is None or str(raw).strip() == "":
            return None
        return str(raw)

    def missing_key_notes(self) -> tuple[str, ...]:
        self.last_error_class = ERROR_MISSING_ENV
        self.last_notes = missing_env_notes(self.api_key_env, source="Polygon")
        return self.last_notes

    def ohlcv_daily(self, query: EquitiesQuery) -> tuple[OHLCVBar, ...]:
        return self._ohlcv(query, multiplier=self.daily_multiplier, timespan=self.daily_timespan)

    def ohlcv_intraday(self, query: EquitiesQuery) -> tuple[OHLCVBar, ...]:
        return self._ohlcv(query, multiplier=self.intraday_multiplier, timespan=self.intraday_timespan)

    def corporate_actions(self, query: EquitiesQuery) -> tuple[CorporateAction, ...]:
        if self.resolve_api_key() is None:
            self.missing_key_notes()
            return ()
        rows: list[CorporateAction] = []
        for ticker in query.tickers:
            rows.extend(self._dividends(ticker, query))
            rows.extend(self._splits(ticker, query))
        return tuple(rows)

    def earnings_calendar(self, query: EquitiesQuery) -> tuple[EarningsEvent, ...]:
        if self.resolve_api_key() is None:
            self.missing_key_notes()
            return ()
        rows: list[EarningsEvent] = []
        for ticker in query.tickers:
            rows.extend(self._events(ticker, query))
        return tuple(rows)

    def _ohlcv(self, query: EquitiesQuery, *, multiplier: int, timespan: str) -> tuple[OHLCVBar, ...]:
        if self.resolve_api_key() is None:
            self.missing_key_notes()
            return ()
        start = query.start.date().isoformat()
        end = query.end.date().isoformat()
        out: list[OHLCVBar] = []
        for ticker in query.tickers:
            path = DAILY_PATH.format(
                ticker=ticker.upper(),
                multiplier=multiplier,
                timespan=timespan,
                start=start,
                end=end,
            )
            payload, error_class = self._get(path)
            if error_class != ERROR_NONE:
                self.last_error_class = error_class
                continue
            out.extend(parse_aggs(payload, ticker=ticker, timespan=timespan, multiplier=multiplier))
        return tuple(out)

    def _dividends(self, ticker: str, query: EquitiesQuery) -> list[CorporateAction]:
        payload, error_class = self._get(
            DIVIDENDS_PATH,
            params={"ticker": ticker.upper(), "limit": 20, "order": "desc", "sort": "ex_dividend_date"},
        )
        if error_class != ERROR_NONE:
            self.last_error_class = error_class
            return []
        return parse_dividends(payload, ticker=ticker)

    def _splits(self, ticker: str, query: EquitiesQuery) -> list[CorporateAction]:
        payload, error_class = self._get(
            SPLITS_PATH,
            params={"ticker": ticker.upper(), "limit": 20, "order": "desc", "sort": "execution_date"},
        )
        if error_class != ERROR_NONE:
            self.last_error_class = error_class
            return []
        return parse_splits(payload, ticker=ticker)

    def _events(self, ticker: str, query: EquitiesQuery) -> list[EarningsEvent]:
        path = EVENTS_PATH.format(ticker=ticker.upper())
        payload, error_class = self._get(path)
        if error_class != ERROR_NONE:
            self.last_error_class = error_class
            return []
        return parse_earnings_events(payload, ticker=ticker)

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> tuple[Any, str]:
        if not self.budget.allow():
            self.last_error_class = ERROR_RATE_LIMITED
            self.last_notes = (f"polygon rate-limit budget exhausted ({self.budget.name})",)
            return None, ERROR_RATE_LIMITED
        key = self.resolve_api_key()
        if not key:
            self.missing_key_notes()
            return None, ERROR_MISSING_ENV
        query = dict(params or {})
        query["apiKey"] = key
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        kwargs: dict[str, Any] = {
            "params": query,
            "max_attempts": self._max_attempts,
            "backoff_s": self._backoff_s,
            "parse_json": True,
        }
        if self._sleep is not None:
            kwargs["sleep"] = self._sleep
        result = http_get(self._http, url, **kwargs)
        if not result.ok:
            return None, result.error_class
        payload = result.json_payload
        if payload is None:
            return None, ERROR_PARSE
        return payload, ERROR_NONE


def parse_aggs(
    payload: Any,
    *,
    ticker: str,
    timespan: str,
    multiplier: int,
) -> list[OHLCVBar]:
    if not isinstance(payload, dict):
        return []
    results = payload.get("results") or []
    if not isinstance(results, list):
        return []
    out: list[OHLCVBar] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        ts = row.get("t")
        if ts is None:
            continue
        market_time = from_unix_ms(int(ts))
        close = _maybe_float(row.get("c"))
        out.append(
            OHLCVBar(
                ticker=ticker.upper(),
                open=_maybe_float(row.get("o")),
                high=_maybe_float(row.get("h")),
                low=_maybe_float(row.get("l")),
                close=close,
                volume=_maybe_float(row.get("v")),
                vwap=_maybe_float(row.get("vw")),
                transactions=int(row["n"]) if row.get("n") is not None else None,
                market_time=market_time,
                timespan=timespan,
                multiplier=multiplier,
                raw=row,
            )
        )
    return out


def parse_dividends(payload: Any, *, ticker: str) -> list[CorporateAction]:
    results = _results(payload)
    out: list[CorporateAction] = []
    for row in results:
        ex_date = str(row.get("ex_dividend_date") or row.get("exDate") or "")
        if not ex_date:
            continue
        out.append(
            CorporateAction(
                ticker=str(row.get("ticker") or ticker).upper(),
                kind="dividend",
                market_time=_date_utc(ex_date),
                cash_amount=_maybe_float(row.get("cash_amount") or row.get("cashAmount")),
                declaration_date=_opt_str(row.get("declaration_date")),
                ex_date=ex_date,
                pay_date=_opt_str(row.get("pay_date")),
                record_date=_opt_str(row.get("record_date")),
                raw=row,
            )
        )
    return out


def parse_splits(payload: Any, *, ticker: str) -> list[CorporateAction]:
    results = _results(payload)
    out: list[CorporateAction] = []
    for row in results:
        exec_date = str(row.get("execution_date") or row.get("exDate") or "")
        if not exec_date:
            continue
        out.append(
            CorporateAction(
                ticker=str(row.get("ticker") or ticker).upper(),
                kind="split",
                market_time=_date_utc(exec_date),
                split_from=_maybe_float(row.get("split_from") or row.get("from")),
                split_to=_maybe_float(row.get("split_to") or row.get("to")),
                ex_date=exec_date,
                raw=row,
            )
        )
    return out


def parse_earnings_events(payload: Any, *, ticker: str) -> list[EarningsEvent]:
    """Keep only rows that look like earnings. Empty/unknown shapes → no invented events."""
    if not isinstance(payload, dict):
        return []
    results = payload.get("results") or payload.get("events") or []
    if isinstance(results, dict):
        results = results.get("events") or results.get("data") or []
    if not isinstance(results, list):
        return []
    out: list[EarningsEvent] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("type") or row.get("event_type") or row.get("name") or "").lower()
        if "earn" not in kind and kind not in {"earnings", "eps"}:
            continue
        when = row.get("date") or row.get("start_date") or row.get("datetime") or row.get("t")
        if when is None:
            continue
        if isinstance(when, (int, float)):
            market_time = from_unix_ms(int(when))
        else:
            market_time = _date_utc(str(when))
        out.append(
            EarningsEvent(
                ticker=ticker.upper(),
                market_time=market_time,
                event_type="earnings",
                fiscal_period=_opt_str(row.get("fiscal_period") or row.get("period")),
                raw=row,
            )
        )
    return out


def _results(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    rows = payload.get("results") or []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_str(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _date_utc(value: str) -> datetime:
    text = value.strip()
    if "T" in text:
        return parse_utc(text)
    return datetime.fromisoformat(f"{text}T00:00:00+00:00").astimezone(timezone.utc)
