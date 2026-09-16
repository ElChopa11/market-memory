"""Truth cell: normalize, quality-flag, and envelope observations.

Must not trade or access execution credentials.
"""

from mm_provenance.envelope import build_envelope
from mm_provenance.normalize import (
    HL_BASE_URL,
    HL_SOURCE_KIND,
    HL_SOURCE_NAME,
    HL_TOS_NOTES,
    SNAPSHOT_CAPTURE_KIND,
    SNAPSHOT_EXTRAS,
    normalize_all_mids,
    normalize_asset_snapshot,
    normalize_candles,
    normalize_funding_history,
    normalize_liquidations,
)
from mm_provenance.quality import assess_quality

__phase__ = 1
LIVE_TRADING_ENABLED = False

__all__ = [
    "HL_BASE_URL",
    "HL_SOURCE_KIND",
    "HL_SOURCE_NAME",
    "HL_TOS_NOTES",
    "SNAPSHOT_CAPTURE_KIND",
    "SNAPSHOT_EXTRAS",
    "LIVE_TRADING_ENABLED",
    "assess_quality",
    "build_envelope",
    "normalize_all_mids",
    "normalize_asset_snapshot",
    "normalize_candles",
    "normalize_funding_history",
    "normalize_liquidations",
]
