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
