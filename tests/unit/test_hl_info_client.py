"""Hyperliquid info client allowlist — no private or signing surfaces."""

from __future__ import annotations

import json

import httpx
import pytest

from mm_ingest.hl_info import ALLOWED_INFO_TYPES, FORBIDDEN_INFO_TYPES, HyperliquidInfoClient, HyperliquidInfoError


def test_forbidden_info_types_are_refused() -> None:
    client = HyperliquidInfoClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))
    forbidden = (
        "clearinghouseState",
        "openOrders",
        "frontendOpenOrders",
        "userFills",
        "userFillsByTime",
        "userFunding",
        "orderStatus",
        "spotClearinghouseState",
        "historicalOrders",
    )
    for info_type in forbidden:
        with pytest.raises(HyperliquidInfoError, match="refusing non-public"):
            client.post({"type": info_type, "user": "0x" + "0" * 40})
    assert "clearinghouseState" in FORBIDDEN_INFO_TYPES
    assert not (FORBIDDEN_INFO_TYPES & ALLOWED_INFO_TYPES)


def test_unknown_info_type_is_refused() -> None:
    client = HyperliquidInfoClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))
    with pytest.raises(HyperliquidInfoError, match="allowlist"):
        client.post({"type": "notARealType"})


def test_all_mids_uses_public_info_body() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"BTC": "1.0", "ETH": "2.0"})

    client = HyperliquidInfoClient(
        url="https://api.hyperliquid.xyz/info",
        transport=httpx.MockTransport(handler),
    )
    mids = client.all_mids()
    assert mids["BTC"] == "1.0"
    assert seen["body"] == {"type": "allMids"}
    assert "/info" in str(seen["url"])


def test_hl_info_429_honours_retry_after_with_shared_backoff() -> None:
    calls = {"n": 0}
    sleeps: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, json={"error": "rate"}, headers={"Retry-After": "2.5"})
        return httpx.Response(200, json={"BTC": "1"})

    client = HyperliquidInfoClient(
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
        max_attempts=5,
    )
    assert client.all_mids()["BTC"] == "1"
    assert calls["n"] == 3
    assert sleeps[0] >= 2.5
