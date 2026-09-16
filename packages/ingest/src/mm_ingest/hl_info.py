"""Read-only Hyperliquid /info HTTP client.

No exchange module, no signing, no private keys, no user-private endpoints.
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_INFO_URL = "https://api.hyperliquid.xyz/info"

ALLOWED_INFO_TYPES = frozenset(
    {
        "allMids",
        "meta",
        "metaAndAssetCtxs",
        "fundingHistory",
        "candleSnapshot",
        "predictedFundings",
        "recentTrades",
    }
)

# User-private or trading surfaces — never called by this client.
FORBIDDEN_INFO_TYPES = frozenset(
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


class HyperliquidInfoError(RuntimeError):
    pass


class HyperliquidInfoClient:
    """POST https://api.hyperliquid.xyz/info — public market data only."""

    def __init__(
        self,
        *,
        url: str = DEFAULT_INFO_URL,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.url = url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout, transport=transport)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> HyperliquidInfoClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def post(self, body: dict[str, Any]) -> Any:
        info_type = str(body.get("type", ""))
        if info_type in FORBIDDEN_INFO_TYPES:
            raise HyperliquidInfoError(f"refusing non-public info type {info_type!r}")
        if info_type not in ALLOWED_INFO_TYPES:
            raise HyperliquidInfoError(f"info type {info_type!r} is not on the read-only allowlist")
        response = self._client.post(self.url, json=body, headers={"Content-Type": "application/json"})
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HyperliquidInfoError(f"Hyperliquid info {info_type} failed: {exc.response.status_code}") from exc
        return response.json()

    def all_mids(self) -> dict[str, Any]:
        payload = self.post({"type": "allMids"})
        return payload if isinstance(payload, dict) else {}

    def meta_and_asset_ctxs(self) -> list[Any]:
        payload = self.post({"type": "metaAndAssetCtxs"})
        return payload if isinstance(payload, list) else []

    def funding_history(self, coin: str, start_ms: int, end_ms: int | None = None) -> list[dict[str, Any]]:
        body: dict[str, Any] = {"type": "fundingHistory", "coin": coin, "startTime": start_ms}
        if end_ms is not None:
            body["endTime"] = end_ms
        payload = self.post(body)
        return payload if isinstance(payload, list) else []

    def candle_snapshot(self, coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        payload = self.post(
            {
                "type": "candleSnapshot",
                "req": {"coin": coin, "interval": interval, "startTime": start_ms, "endTime": end_ms},
            }
        )
        return payload if isinstance(payload, list) else []

    def recent_trades(self, coin: str) -> list[dict[str, Any]]:
        try:
            payload = self.post({"type": "recentTrades", "coin": coin})
        except HyperliquidInfoError:
            return []
        return payload if isinstance(payload, list) else []

    def iter_funding_history(self, coin: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor = start_ms
        while cursor <= end_ms:
            chunk = self.funding_history(coin, cursor, end_ms)
            if not chunk:
                break
            out.extend(chunk)
            last = int(chunk[-1].get("time") or cursor)
            if last <= cursor or len(chunk) < 500:
                break
            cursor = last + 1
        return out

    def iter_candles(self, coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        cursor = start_ms
        while cursor <= end_ms:
            chunk = self.candle_snapshot(coin, interval, cursor, end_ms)
            if not chunk:
                break
            out.extend(chunk)
            last = int(chunk[-1].get("t") or cursor)
            if last <= cursor or len(chunk) < 500:
                break
            cursor = last + 1
        return out
