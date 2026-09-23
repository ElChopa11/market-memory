"""Bounded GET retries and closed error classes for Pulse + source-health."""

from __future__ import annotations

import httpx

from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    ERROR_HTTP_404,
    ERROR_HTTP_5XX,
    ERROR_NONE,
    ERROR_PARSE,
    ERROR_RATE_LIMITED,
    ERROR_TIMEOUT,
    ERROR_TOS_OR_BLOCKED,
    ERROR_UNREACHABLE,
    classify_exception,
    classify_http_status,
    http_get,
    http_post,
    is_retryable,
    missing_env_notes,
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)


def test_classify_http_status_closed_vocabulary() -> None:
    assert classify_http_status(200) == ERROR_NONE
    assert classify_http_status(404) == ERROR_HTTP_404
    assert classify_http_status(503) == ERROR_HTTP_5XX
    assert classify_http_status(429) == ERROR_RATE_LIMITED
    assert classify_http_status(403) == ERROR_TOS_OR_BLOCKED
    assert classify_http_status(401) == ERROR_TOS_OR_BLOCKED
    assert classify_http_status(451) == ERROR_TOS_OR_BLOCKED
    assert classify_http_status(400) == "http_error"
    assert is_retryable(ERROR_HTTP_404) is False
    assert is_retryable(ERROR_TOS_OR_BLOCKED) is False
    assert is_retryable(ERROR_HTTP_5XX) is True
    assert is_retryable(ERROR_TIMEOUT) is True
    assert is_retryable(ERROR_RATE_LIMITED) is True


def test_classify_timeout_and_connect() -> None:
    assert classify_exception(httpx.ReadTimeout("read timeout")) == ERROR_TIMEOUT
    assert classify_exception(httpx.ConnectError("connection refused")) == ERROR_UNREACHABLE


def test_http_404_is_terminal_no_retry() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, text="no")

    result = http_get(_client(handler), "https://stooq.com/q/l/", sleep=lambda _: None)
    assert result.error_class == ERROR_HTTP_404
    assert result.status_code == 404
    assert result.attempts == 1
    assert calls["n"] == 1
    assert result.ok is False


def test_http_5xx_retries_until_max_attempts_then_fails() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503, text="down")

    result = http_get(_client(handler), "https://example.test/", sleep=sleeps.append, rng=lambda: 0.0)
    assert result.error_class == ERROR_HTTP_5XX
    assert result.attempts == DEFAULT_MAX_ATTEMPTS
    assert calls["n"] == DEFAULT_MAX_ATTEMPTS
    assert len(sleeps) == DEFAULT_MAX_ATTEMPTS - 1


def test_http_5xx_then_200_succeeds() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="down")
        return httpx.Response(200, text="ok")

    result = http_get(_client(handler), "https://example.test/", sleep=lambda _: None)
    assert result.ok is True
    assert result.text == "ok"
    assert result.attempts == 2
    assert calls["n"] == 2


def test_timeout_retries_until_max_attempts() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ReadTimeout("read timeout")

    result = http_get(_client(handler), "https://example.test/", sleep=lambda _: None)
    assert result.error_class == ERROR_TIMEOUT
    assert result.attempts == DEFAULT_MAX_ATTEMPTS
    assert calls["n"] == DEFAULT_MAX_ATTEMPTS
    assert result.exception_name == "ReadTimeout"


def test_exponential_backoff_honours_retry_after_and_ceiling() -> None:
    from mm_common.http import DEFAULT_BACKOFF_CEILING_S, compute_backoff_s

    # attempt=4 → 0.25 * 8 = 2.0; full jitter with rng=1.0 → 2.0
    assert compute_backoff_s(4, backoff_s=0.25, ceiling_s=8.0, rng=lambda: 1.0) == 2.0
    # attempt=10 → exp huge but capped at ceiling before jitter
    assert compute_backoff_s(10, backoff_s=0.25, ceiling_s=8.0, rng=lambda: 1.0) == 8.0
    # Retry-After wins even above ceiling
    assert (
        compute_backoff_s(1, backoff_s=0.25, ceiling_s=8.0, retry_after=12.0, rng=lambda: 0.0) == 12.0
    )
    assert DEFAULT_BACKOFF_CEILING_S == 8.0


def test_http_429_uses_retry_after_header() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, text="slow", headers={"Retry-After": "3"})
        return httpx.Response(200, text="ok")

    result = http_get(
        _client(handler),
        "https://example.test/",
        sleep=sleeps.append,
        rng=lambda: 0.0,
        max_attempts=5,
    )
    assert result.ok is True
    assert calls["n"] == 3
    assert sleeps[0] >= 3.0
    assert result.attempts == 3


def test_bad_json_is_parse_error_not_retried() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, text="not-json")

    result = http_get(
        _client(handler),
        "https://api.stlouisfed.org/fred/series/observations",
        parse_json=True,
        sleep=lambda _: None,
    )
    assert result.error_class == ERROR_PARSE
    assert result.attempts == 1
    assert calls["n"] == 1


def test_missing_env_notes_never_include_a_value() -> None:
    notes = missing_env_notes("FRED_API_KEY", source="FRED")
    blob = " ".join(notes)
    assert "FRED_API_KEY" in blob
    assert "missing_env" in blob
    assert "never commit" in blob
    assert "sk-" not in blob
    assert "secret" in blob.lower() or "CI" in blob


def test_tos_blocked_not_retried() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(403, text="forbidden")

    result = http_get(_client(handler), "https://stooq.com/q/l/", sleep=lambda _: None)
    assert result.error_class == ERROR_TOS_OR_BLOCKED
    assert calls["n"] == 1


def test_http_post_json_succeeds_on_200() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(200, json={"ok": True})

    result = http_post(_client(handler), "https://telegram.test/sendMessage", json_body={"text": "x"})
    assert result.ok is True
    assert result.json_payload == {"ok": True}


def test_rate_limit_header_log_is_opt_in_and_omits_url(capsys, monkeypatch) -> None:
    """P0.4: hostname + status + rate-limit headers only. Never the request URL."""
    monkeypatch.delenv("MM_LOG_RATE_LIMIT_HEADERS", raising=False)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text="ok",
            headers={"X-RateLimit-Remaining": "12", "Authorization": "secret-token"},
        )

    url = "https://api.coingecko.com/api/v3/simple/price?x-cg-demo-api-key=supersecret"
    http_get(_client(handler), url, sleep=lambda _: None, max_attempts=1)
    quiet = capsys.readouterr().err
    assert quiet == ""

    monkeypatch.setenv("MM_LOG_RATE_LIMIT_HEADERS", "1")

    def limited(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow", headers={"Retry-After": "3", "Set-Cookie": "session=sekrit"})

    http_get(_client(limited), url, sleep=lambda _: None, max_attempts=1)
    err = capsys.readouterr().err
    assert "source=api.coingecko.com" in err
    assert "status=429" in err
    assert "retry-after=3" in err.lower()
    assert "supersecret" not in err
    assert "sekrit" not in err
    assert "simple/price" not in err
    assert "secret-token" not in err
