"""Idempotent HTTP GET/POST helpers for Pulse, source-health, and Telegram delivery.

Classify failures; bounded retries only on timeout / connect / 429 / 5xx.
Exponential backoff with jitter; honour Retry-After; ceiling of several seconds.
Callers must not scrape HTML, invent prints, or log secrets.
Does not talk to Hyperliquid signing (ingest uses the same backoff helpers).
"""

from __future__ import annotations

import os
import random
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

ERROR_NONE = "none"
ERROR_TIMEOUT = "timeout"
ERROR_UNREACHABLE = "unreachable"
ERROR_HTTP_404 = "http_404"
ERROR_HTTP_5XX = "http_5xx"
ERROR_HTTP = "http_error"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_TOS_OR_BLOCKED = "tos_or_blocked"
ERROR_PARSE = "parse_error"
ERROR_MISSING_ENV = "missing_env"
ERROR_CONFIG = "config_error"
ERROR_SKIPPED = "skipped"
ERROR_NOT_ON_PLAN = "not_on_plan"
ERROR_GENERIC = "error"

RETRYABLE_ERROR_CLASSES = frozenset(
    {
        ERROR_TIMEOUT,
        ERROR_UNREACHABLE,
        ERROR_RATE_LIMITED,
        ERROR_HTTP_5XX,
    }
)

# Align Pulse live fetch with source-health probes: fail closed on slow sources.
DEFAULT_TIMEOUT = 8.0
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BACKOFF_S = 0.25
DEFAULT_BACKOFF_CEILING_S = 8.0
DEFAULT_JITTER_RATIO = 1.0  # full jitter in [0, exp]

MISSING_ENV_OPERATOR_HINT = (
    "set the named env var in the local shell, gitignored `.env`, or CI repository secrets "
    "— never commit the value"
)


@dataclass(frozen=True)
class HttpGetResult:
    error_class: str
    attempts: int
    latency_ms: float
    status_code: int | None = None
    text: str | None = None
    json_payload: Any = None
    exception_name: str | None = None
    response: httpx.Response | None = None
    retry_after_s: float | None = None

    @property
    def ok(self) -> bool:
        return self.error_class == ERROR_NONE and self.status_code == 200


def classify_http_status(status_code: int) -> str:
    if status_code == 404:
        return ERROR_HTTP_404
    if status_code in {401, 403, 451}:
        return ERROR_TOS_OR_BLOCKED
    if status_code == 429:
        return ERROR_RATE_LIMITED
    if 500 <= status_code <= 599:
        return ERROR_HTTP_5XX
    if 400 <= status_code <= 499:
        return ERROR_HTTP
    if 200 <= status_code <= 299:
        return ERROR_NONE
    return ERROR_HTTP


def classify_exception(exc: BaseException) -> str:
    """Map transport/library exceptions. Source-specific overlays stay at the caller."""
    name = type(exc).__name__
    text = f"{name} {exc}".lower()
    if isinstance(exc, httpx.TimeoutException) or "timeout" in name.lower():
        return ERROR_TIMEOUT
    if isinstance(exc, httpx.ConnectError) or "connect" in name.lower() or "refused" in text:
        return ERROR_UNREACHABLE
    if isinstance(exc, httpx.HTTPStatusError):
        return classify_http_status(exc.response.status_code)
    if "timeout" in text:
        return ERROR_TIMEOUT
    if "operational" in name.lower() or "unreachable" in text:
        return ERROR_UNREACHABLE
    return ERROR_GENERIC


def is_retryable(error_class: str) -> bool:
    return error_class in RETRYABLE_ERROR_CLASSES


def _public_http_source(url: str) -> str:
    """Hostname only. Never the path or query (API keys and bot tokens live there)."""
    host = urlparse(url).hostname or ""
    return host or "http"


def maybe_log_rate_limit_headers(response: httpx.Response | None, *, source: str) -> None:
    """Print status and rate-limit headers when ``MM_LOG_RATE_LIMIT_HEADERS=1``.

    Allowlisted names only (``Retry-After``, ``*ratelimit*``). Never the request
    URL, never ``Authorization``, never secret values. Opt-in so pytest stays quiet.
    """
    flag = (os.environ.get("MM_LOG_RATE_LIMIT_HEADERS") or "").strip().lower()
    if flag not in {"1", "true", "yes"}:
        return
    if response is None:
        print(f"rate-limit headers source={source} status=none headers=(none)", file=sys.stderr)
        return
    picked: list[str] = []
    for key, value in response.headers.items():
        lowered = key.lower()
        if lowered != "retry-after" and "ratelimit" not in lowered:
            continue
        text = str(value).replace("\n", " ").replace("\r", " ").strip()
        if len(text) > 80:
            text = text[:80]
        picked.append(f"{key}={text}")
    blob = "; ".join(picked) if picked else "(none)"
    print(
        f"rate-limit headers source={source} status={response.status_code} headers={blob}",
        file=sys.stderr,
    )


def missing_env_notes(env_name: str, *, source: str) -> tuple[str, ...]:
    """Honest unavailable copy when a required env var is absent. Never includes the value."""
    return (
        f"missing env {env_name}; {source} unavailable (error_class={ERROR_MISSING_ENV})",
        MISSING_ENV_OPERATOR_HINT,
        "key value not printed",
    )


def http_get(
    client: httpx.Client,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_s: float = DEFAULT_BACKOFF_S,
    backoff_ceiling_s: float = DEFAULT_BACKOFF_CEILING_S,
    sleep: Callable[[float], None] = time.sleep,
    parse_json: bool = False,
    rng: Callable[[], float] | None = None,
) -> HttpGetResult:
    """GET with bounded retries. 404 / 401 / 403 are terminal (do not scrape around them)."""
    return _request(
        client,
        "GET",
        url,
        params=params,
        headers=headers,
        max_attempts=max_attempts,
        backoff_s=backoff_s,
        backoff_ceiling_s=backoff_ceiling_s,
        sleep=sleep,
        parse_json=parse_json,
        rng=rng,
    )


def http_post(
    client: httpx.Client,
    url: str,
    *,
    json_body: Mapping[str, Any] | None = None,
    data: Mapping[str, Any] | None = None,
    files: Any = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_s: float = DEFAULT_BACKOFF_S,
    backoff_ceiling_s: float = DEFAULT_BACKOFF_CEILING_S,
    sleep: Callable[[float], None] = time.sleep,
    parse_json: bool = True,
    rng: Callable[[], float] | None = None,
) -> HttpGetResult:
    """POST with the same closed error classes and bounded retries as GET."""
    return _request(
        client,
        "POST",
        url,
        json_body=json_body,
        data=data,
        files=files,
        max_attempts=max_attempts,
        backoff_s=backoff_s,
        backoff_ceiling_s=backoff_ceiling_s,
        sleep=sleep,
        parse_json=parse_json,
        rng=rng,
    )


def _request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    json_body: Mapping[str, Any] | None = None,
    data: Mapping[str, Any] | None = None,
    files: Any = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_s: float = DEFAULT_BACKOFF_S,
    backoff_ceiling_s: float = DEFAULT_BACKOFF_CEILING_S,
    sleep: Callable[[float], None] = time.sleep,
    parse_json: bool = False,
    rng: Callable[[], float] | None = None,
) -> HttpGetResult:
    started = time.perf_counter()
    attempts_allowed = max(1, int(max_attempts))
    last: HttpGetResult | None = None
    verb = method.upper()
    for attempt in range(1, attempts_allowed + 1):
        try:
            if verb == "GET":
                get_kwargs: dict[str, Any] = {}
                if params:
                    get_kwargs["params"] = dict(params)
                if headers:
                    get_kwargs["headers"] = dict(headers)
                response = client.get(url, **get_kwargs)
            elif verb == "POST":
                kwargs: dict[str, Any] = {}
                if json_body is not None:
                    kwargs["json"] = dict(json_body)
                if data is not None:
                    kwargs["data"] = dict(data)
                if files is not None:
                    kwargs["files"] = files
                if params:
                    kwargs["params"] = dict(params)
                if headers:
                    kwargs["headers"] = dict(headers)
                response = client.post(url, **kwargs)
            else:
                raise ValueError(f"unsupported HTTP method {method!r}")
        except Exception as exc:  # noqa: BLE001 — classify, do not raise into Pulse/delivery
            error_class = classify_exception(exc)
            last = HttpGetResult(
                error_class=error_class,
                attempts=attempt,
                latency_ms=_ms(started),
                exception_name=type(exc).__name__,
            )
            if is_retryable(error_class) and attempt < attempts_allowed:
                sleep(
                    compute_backoff_s(
                        attempt,
                        backoff_s=backoff_s,
                        ceiling_s=backoff_ceiling_s,
                        retry_after=None,
                        rng=rng,
                    )
                )
                continue
            return last
        status = response.status_code
        maybe_log_rate_limit_headers(response, source=_public_http_source(url))
        if status == 200:
            text = response.text
            payload = None
            if parse_json:
                try:
                    payload = response.json()
                except Exception:  # noqa: BLE001
                    return HttpGetResult(
                        error_class=ERROR_PARSE,
                        attempts=attempt,
                        latency_ms=_ms(started),
                        status_code=status,
                        text=text,
                        response=response,
                    )
            return HttpGetResult(
                error_class=ERROR_NONE,
                attempts=attempt,
                latency_ms=_ms(started),
                status_code=status,
                text=text,
                json_payload=payload,
                response=response,
            )
        error_class = classify_http_status(status)
        retry_after = parse_retry_after(response)
        last = HttpGetResult(
            error_class=error_class,
            attempts=attempt,
            latency_ms=_ms(started),
            status_code=status,
            text=response.text,
            response=response,
            retry_after_s=retry_after,
        )
        if is_retryable(error_class) and attempt < attempts_allowed:
            sleep(
                compute_backoff_s(
                    attempt,
                    backoff_s=backoff_s,
                    ceiling_s=backoff_ceiling_s,
                    retry_after=retry_after,
                    rng=rng,
                )
            )
            continue
        return last
    assert last is not None
    return last


def parse_retry_after(response: httpx.Response | None) -> float | None:
    if response is None:
        return None
    raw = response.headers.get("Retry-After") or response.headers.get("retry-after")
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        return None


def compute_backoff_s(
    attempt: int,
    *,
    backoff_s: float = DEFAULT_BACKOFF_S,
    ceiling_s: float = DEFAULT_BACKOFF_CEILING_S,
    retry_after: float | None = None,
    jitter_ratio: float = DEFAULT_JITTER_RATIO,
    rng: Callable[[], float] | None = None,
) -> float:
    """Exponential backoff with jitter; honour Retry-After; cap exponential at ceiling_s.

    ``attempt`` is 1-based (the attempt that just failed). Full jitter draws uniform
    in ``[0, min(ceiling, backoff_s * 2**(attempt-1))]`` when ``jitter_ratio > 0``.
    Retry-After is honoured even when larger than the ceiling (server asked to wait).
    """
    exp = float(backoff_s) * (2 ** max(0, int(attempt) - 1))
    capped_exp = min(max(0.0, exp), max(0.0, float(ceiling_s)))
    draw = (rng or random.random)()
    draw = min(1.0, max(0.0, float(draw)))
    if float(jitter_ratio) <= 0:
        delay = capped_exp
    else:
        delay = capped_exp * draw * min(1.0, float(jitter_ratio))
    if retry_after is not None:
        delay = max(delay, float(retry_after))
    return max(0.0, delay)


def _ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 1)
