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


def test_http_5xx_retries_once_then_fails() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503, text="down")

    result = http_get(_client(handler), "https://example.test/", sleep=lambda _: None)
    assert result.error_class == ERROR_HTTP_5XX
    assert result.attempts == DEFAULT_MAX_ATTEMPTS
    assert calls["n"] == 2


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


def test_timeout_retries_once() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ReadTimeout("read timeout")

    result = http_get(_client(handler), "https://example.test/", sleep=lambda _: None)
    assert result.error_class == ERROR_TIMEOUT
    assert result.attempts == 2
    assert calls["n"] == 2
    assert result.exception_name == "ReadTimeout"


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
