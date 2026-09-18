"""Read-only public ingest (Hyperliquid /info + Polygon equities). Must not sign orders or use API wallets."""

from mm_ingest.equities import DEFAULT_EQUITIES_VENDOR, get_equities_adapter
from mm_ingest.hl_info import (
    ALLOWED_INFO_TYPES,
    DEFAULT_INFO_URL,
    FORBIDDEN_INFO_TYPES,
    HyperliquidInfoClient,
    HyperliquidInfoError,
)
from mm_ingest.pipeline import (
    envelopes_from_fixture,
    ingest_from_client,
    ingest_from_fixture,
    load_fixture_file,
    persist_envelopes,
    stats_from_envelopes,
)

__phase__ = 1
LIVE_TRADING_ENABLED = False
EQUITIES_VENDOR = DEFAULT_EQUITIES_VENDOR

__all__ = [
    "ALLOWED_INFO_TYPES",
    "DEFAULT_EQUITIES_VENDOR",
    "DEFAULT_INFO_URL",
    "EQUITIES_VENDOR",
    "FORBIDDEN_INFO_TYPES",
    "HyperliquidInfoClient",
    "HyperliquidInfoError",
    "LIVE_TRADING_ENABLED",
    "envelopes_from_fixture",
    "get_equities_adapter",
    "ingest_from_client",
    "ingest_from_fixture",
    "load_fixture_file",
    "persist_envelopes",
    "stats_from_envelopes",
]
