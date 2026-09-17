"""Public-only fetchers for the QUANT-20260917 pack.

Hyperliquid: POST https://api.hyperliquid.xyz/info (allowlisted types only).
Equities: Yahoo Finance v8 chart API (the same public series yfinance uses).

Every HTTP attempt is recorded. 429/5xx retry with exponential backoff + jitter.
No secrets, no signing, no user-private info types.
"""

from __future__ import annotations

import json
import random
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
YAHOO_CHART_HOSTS = (
    "https://query1.finance.yahoo.com/v8/finance/chart",
    "https://query2.finance.yahoo.com/v8/finance/chart",
)
USER_AGENT = (
    "market-memory-quant-pack/20260917 "
    "(+https://github.com/ElChopa11/market-memory; public research snapshot)"
)
HL_ALLOWED_TYPES = frozenset(
    {
        "allMids",
        "metaAndAssetCtxs",
        "fundingHistory",
        "candleSnapshot",
        "predictedFundings",
    }
)
HL_FORBIDDEN_TYPES = frozenset(
    {
        "clearinghouseState",
        "openOrders",
        "frontendOpenOrders",
        "userFills",
        "userFillsByTime",
        "userFunding",
        "userNonFundingLedgerUpdates",
        "historicalOrders",
        "orderStatus",
        "maxBuilderFee",
        "userRateLimit",
        "twapHistory",
        "userTwapSliceFills",
        "userTwapHistory",
        "spotClearinghouseState",
    }
)

SSL_CONTEXT = ssl.create_default_context()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(ts: datetime | None = None) -> str:
    value = ts or utcnow()
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class FetchAttempt:
    started_at: str
    finished_at: str
    source: str
    action: str
    status: int | None
    ok: bool
    error: str | None = None
    bytes: int = 0
    attempt: int = 1
    elapsed_ms: int = 0
    url: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "source": self.source,
            "action": self.action,
            "status": self.status,
            "ok": self.ok,
            "error": self.error,
            "bytes": self.bytes,
            "attempt": self.attempt,
            "elapsed_ms": self.elapsed_ms,
            "url": self.url,
        }


@dataclass
class FetchLog:
    pack_id: str
    started_at: str = field(default_factory=iso)
    finished_at: str | None = None
    attempts: list[FetchAttempt] = field(default_factory=list)

    def add(self, attempt: FetchAttempt) -> None:
        self.attempts.append(attempt)

    def count_status(self, code: int) -> int:
        return sum(1 for row in self.attempts if row.status == code)

    def failures(self) -> list[FetchAttempt]:
        return [row for row in self.attempts if not row.ok]

    def as_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "attempt_count": len(self.attempts),
            "http_429_count": self.count_status(429),
            "failure_count": len(self.failures()),
            "attempts": [row.as_dict() for row in self.attempts],
        }


class FetchError(RuntimeError):
    pass


def _sleep_backoff(attempt: int, base: float = 1.0, cap: float = 32.0) -> float:
    delay = min(cap, base * (2 ** (attempt - 1)))
    delay = delay + random.uniform(0.0, 0.35 * delay)
    time.sleep(delay)
    return delay


def http_json(
    log: FetchLog,
    *,
    source: str,
    action: str,
    url: str,
    body: dict[str, Any] | None = None,
    max_tries: int = 6,
    timeout: float = 45.0,
) -> Any:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    last_error: str | None = None
    for attempt in range(1, max_tries + 1):
        started = utcnow()
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST" if payload is not None else "GET",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,*/*",
                "Content-Type": "application/json" if payload is not None else "text/plain",
            },
        )
        status: int | None = None
        raw = b""
        try:
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=timeout) as resp:
                status = int(resp.status)
                raw = resp.read()
            finished = utcnow()
            log.add(
                FetchAttempt(
                    started_at=iso(started),
                    finished_at=iso(finished),
                    source=source,
                    action=action,
                    status=status,
                    ok=True,
                    bytes=len(raw),
                    attempt=attempt,
                    elapsed_ms=int((finished - started).total_seconds() * 1000),
                    url=url,
                )
            )
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            err_body = b""
            try:
                err_body = exc.read() or b""
            except Exception:
                err_body = b""
            last_error = f"HTTP {status}: {err_body[:240]!r}"
            finished = utcnow()
            retryable = status == 429 or status >= 500
            log.add(
                FetchAttempt(
                    started_at=iso(started),
                    finished_at=iso(finished),
                    source=source,
                    action=action,
                    status=status,
                    ok=False,
                    error=last_error,
                    bytes=len(err_body),
                    attempt=attempt,
                    elapsed_ms=int((finished - started).total_seconds() * 1000),
                    url=url,
                )
            )
            if retryable and attempt < max_tries:
                _sleep_backoff(attempt)
                continue
            raise FetchError(f"{source} {action} failed: {last_error}") from exc
        except Exception as exc:  # noqa: BLE001 — record network/parse failures honestly
            last_error = f"{type(exc).__name__}: {exc}"
            finished = utcnow()
            log.add(
                FetchAttempt(
                    started_at=iso(started),
                    finished_at=iso(finished),
                    source=source,
                    action=action,
                    status=status,
                    ok=False,
                    error=last_error,
                    bytes=len(raw),
                    attempt=attempt,
                    elapsed_ms=int((finished - started).total_seconds() * 1000),
                    url=url,
                )
            )
            if attempt < max_tries:
                _sleep_backoff(attempt)
                continue
            raise FetchError(f"{source} {action} failed: {last_error}") from exc
    raise FetchError(f"{source} {action} failed: {last_error}")


def hl_info(log: FetchLog, body: dict[str, Any]) -> Any:
    info_type = str(body.get("type") or "")
    if info_type in HL_FORBIDDEN_TYPES:
        raise FetchError(f"refusing non-public Hyperliquid info type {info_type!r}")
    if info_type not in HL_ALLOWED_TYPES:
        raise FetchError(f"Hyperliquid info type {info_type!r} is not on the public allowlist")
    return http_json(
        log,
        source="hyperliquid.info",
        action=info_type,
        url=HL_INFO_URL,
        body=body,
    )


def yahoo_daily_adj_closes(
    log: FetchLog,
    ticker: str,
    *,
    period1: int,
    period2: int,
) -> list[dict[str, Any]]:
    """Daily Yahoo chart bars. Prefer adjclose; fall back to close. Skip nulls."""
    query = f"{ticker}?period1={period1}&period2={period2}&interval=1d&events=div%2Csplits&includeAdjustedClose=true"
    last_error: str | None = None
    for host in YAHOO_CHART_HOSTS:
        url = f"{host}/{query}"
        try:
            payload = http_json(
                log,
                source="yahoo.finance.chart",
                action=f"chart:{ticker}",
                url=url,
            )
        except FetchError as exc:
            last_error = str(exc)
            continue
        chart = payload.get("chart") if isinstance(payload, dict) else None
        if not isinstance(chart, dict):
            last_error = f"unexpected Yahoo payload for {ticker}"
            continue
        if chart.get("error"):
            last_error = f"Yahoo error for {ticker}: {chart.get('error')}"
            continue
        results = chart.get("result") or []
        if not results:
            last_error = f"Yahoo empty result for {ticker}"
            continue
        result = results[0]
        timestamps = result.get("timestamp") or []
        indicators = result.get("indicators") or {}
        adj = ((indicators.get("adjclose") or [{}])[0] or {}).get("adjclose")
        raw_close = ((indicators.get("quote") or [{}])[0] or {}).get("close")
        series = adj if isinstance(adj, list) and any(v is not None for v in adj) else raw_close
        price_field = "adjclose" if series is adj else "close"
        if not isinstance(series, list) or not timestamps:
            last_error = f"Yahoo missing closes for {ticker}"
            continue
        rows: list[dict[str, Any]] = []
        for ts, price in zip(timestamps, series):
            if ts is None or price is None:
                continue
            try:
                px = float(price)
            except (TypeError, ValueError):
                continue
            if px <= 0:
                continue
            day = datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
            rows.append(
                {
                    "date": day,
                    "ticker": ticker,
                    "close": px,
                    "price_field": price_field,
                    "source": "yahoo.finance.chart",
                    "unix_ts": int(ts),
                }
            )
        if not rows:
            last_error = f"Yahoo produced zero usable bars for {ticker}"
            continue
        rows.sort(key=lambda row: (row["date"], row["unix_ts"]))
        return rows
    raise FetchError(last_error or f"Yahoo fetch failed for {ticker}")


def hl_asset_snapshot(log: FetchLog, coins: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    mids = hl_info(log, {"type": "allMids"})
    ctxs = hl_info(log, {"type": "metaAndAssetCtxs"})
    if not isinstance(ctxs, list) or len(ctxs) < 2:
        raise FetchError("metaAndAssetCtxs did not return [meta, assetCtxs]")
    meta, assets = ctxs[0], ctxs[1]
    universe = meta.get("universe") if isinstance(meta, dict) else None
    if not isinstance(universe, list) or not isinstance(assets, list):
        raise FetchError("metaAndAssetCtxs universe/assetCtxs missing")
    wanted = {coin.upper() for coin in coins}
    out: dict[str, dict[str, Any]] = {}
    for idx, asset in enumerate(universe):
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name") or "").upper()
        if name not in wanted:
            continue
        ctx = assets[idx] if idx < len(assets) and isinstance(assets[idx], dict) else {}
        mid = None
        if isinstance(mids, dict) and mids.get(name) is not None:
            try:
                mid = float(mids[name])
            except (TypeError, ValueError):
                mid = None
        out[name] = {
            "coin": name,
            "mid_px": _f(mid if mid is not None else ctx.get("midPx")),
            "mark_px": _f(ctx.get("markPx")),
            "oracle_px": _f(ctx.get("oraclePx")),
            "funding": _f(ctx.get("funding")),
            "open_interest": _f(ctx.get("openInterest")),
            "day_ntl_vlm": _f(ctx.get("dayNtlVlm")),
            "premium": _f(ctx.get("premium")),
            "prev_day_px": _f(ctx.get("prevDayPx")),
            "universe_index": idx,
        }
    missing = sorted(wanted - set(out))
    if missing:
        raise FetchError(f"coins missing from Hyperliquid universe: {missing}")
    return out


def hl_daily_candles(log: FetchLog, coin: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    payload = hl_info(
        log,
        {
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": "1d", "startTime": start_ms, "endTime": end_ms},
        },
    )
    if not isinstance(payload, list):
        raise FetchError(f"candleSnapshot for {coin} was not a list")
    rows: list[dict[str, Any]] = []
    for bar in payload:
        if not isinstance(bar, dict):
            continue
        close = _f(bar.get("c"))
        open_ms = bar.get("t")
        if close is None or close <= 0 or open_ms is None:
            continue
        day = datetime.fromtimestamp(int(open_ms) / 1000.0, tz=timezone.utc).date().isoformat()
        rows.append(
            {
                "date": day,
                "ticker": coin,
                "close": close,
                "open": _f(bar.get("o")),
                "high": _f(bar.get("h")),
                "low": _f(bar.get("l")),
                "volume": _f(bar.get("v")),
                "n_trades": bar.get("n"),
                "open_ms": int(open_ms),
                "close_ms": int(bar["T"]) if bar.get("T") is not None else None,
                "source": "hyperliquid.info.candleSnapshot",
                "interval": "1d",
            }
        )
    rows.sort(key=lambda row: row["date"])
    return rows


def hl_funding_history(log: FetchLog, coin: str, start_ms: int, end_ms: int | None = None) -> list[dict[str, Any]]:
    body: dict[str, Any] = {"type": "fundingHistory", "coin": coin, "startTime": start_ms}
    if end_ms is not None:
        body["endTime"] = end_ms
    payload = hl_info(log, body)
    if not isinstance(payload, list):
        raise FetchError(f"fundingHistory for {coin} was not a list")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        rate = _f(item.get("fundingRate"))
        when = item.get("time")
        if rate is None or when is None:
            continue
        rows.append(
            {
                "coin": str(item.get("coin") or coin).upper(),
                "funding_rate": rate,
                "premium": _f(item.get("premium")),
                "time_ms": int(when),
                "time_utc": datetime.fromtimestamp(int(when) / 1000.0, tz=timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z"),
                "source": "hyperliquid.info.fundingHistory",
            }
        )
    rows.sort(key=lambda row: row["time_ms"])
    return rows


def _f(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
