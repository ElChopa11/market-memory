"""Read-only Hyperliquid public-info ingest. Must not sign orders or use API wallets."""

from mm_ingest.hl_info import (
    ALLOWED_INFO_TYPES,
    DEFAULT_INFO_URL,
    FORBIDDEN_INFO_TYPES,
    HyperliquidInfoClient,
    HyperliquidInfoError,
)
from mm_ingest.pipeline import ingest_from_client, ingest_from_fixture, load_fixture_file, persist_envelopes

__phase__ = 1
LIVE_TRADING_ENABLED = False

__all__ = [
    "ALLOWED_INFO_TYPES",
    "DEFAULT_INFO_URL",
    "FORBIDDEN_INFO_TYPES",
    "HyperliquidInfoClient",
    "HyperliquidInfoError",
    "LIVE_TRADING_ENABLED",
    "ingest_from_client",
    "ingest_from_fixture",
    "load_fixture_file",
    "persist_envelopes",
]
