"""Phase 6d listings / IPO library. Research-only. No execution imports."""

from mm_listings.config import ListingsConfig, load_listings_config
from mm_listings.engine import compute_listings
from mm_listings.models import BaseRateSummary, ListingDeal, ListingsSnapshot, WarningBlock

__phase__ = 6
LIVE_TRADING_ENABLED = False

__all__ = [
    "BaseRateSummary",
    "LIVE_TRADING_ENABLED",
    "ListingDeal",
    "ListingsConfig",
    "ListingsSnapshot",
    "WarningBlock",
    "compute_listings",
    "load_listings_config",
]
