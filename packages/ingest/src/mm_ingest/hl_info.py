"""Read-only Hyperliquid /info HTTP client.

No exchange module, no signing, no private keys, no user-private endpoints.
Bounded retry on timeout / 429 / 5xx only (read-only POSTs are idempotent).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from mm_common.http import (
    DEFAULT_BACKOFF_CEILING_S,
    DEFAULT_BACKOFF_S,
    DEFAULT_MAX_ATTEMPTS,
    classify_exception,
    classify_http_status,
    compute_backoff_s,
    is_retryable,
    parse_retry_after,
)

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
        "l2Book",
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
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        backoff_s: float = DEFAULT_BACKOFF_S,
        backoff_ceiling_s: float = DEFAULT_BACKOFF_CEILING_S,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.url = url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout, transport=transport)
        self._max_attempts = max(1, int(max_attempts))
        self._backoff_s = backoff_s
        self._backoff_ceiling_s = backoff_ceiling_s
        self._sleep = sleep or time.sleep

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
        last_error: BaseException | None = None
        last_status: int | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._client.post(self.url, json=body, headers={"Content-Type": "application/json"})
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                error_class = classify_exception(exc)
                if is_retryable(error_class) and attempt < self._max_attempts:
                    self._sleep(
                        compute_backoff_s(
                            attempt,
                            backoff_s=self._backoff_s,
                            ceiling_s=self._backoff_ceiling_s,
                            retry_after=None,
                        )
                    )
                    continue
                raise HyperliquidInfoError(f"Hyperliquid info {info_type} failed: {error_class}") from exc
            last_status = response.status_code
            if response.status_code == 200:
                return response.json()
            error_class = classify_http_status(response.status_code)
            if is_retryable(error_class) and attempt < self._max_attempts:
                self._sleep(
                    compute_backoff_s(
                        attempt,
                        backoff_s=self._backoff_s,
                        ceiling_s=self._backoff_ceiling_s,
                        retry_after=parse_retry_after(response),
                    )
                )
                continue
            raise HyperliquidInfoError(f"Hyperliquid info {info_type} failed: {response.status_code}")
        if last_error is not None:
            raise HyperliquidInfoError(f"Hyperliquid info {info_type} failed") from last_error
        raise HyperliquidInfoError(f"Hyperliquid info {info_type} failed: {last_status}")

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

    def l2_book(self, coin: str) -> dict[str, Any]:
        payload = self.post({"type": "l2Book", "coin": coin})
        return payload if isinstance(payload, dict) else {}

    def predicted_fundings(self) -> Any:
        return self.post({"type": "predictedFundings"})

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
