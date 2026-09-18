"""Ops-owned Telegram channel matrix bound to the naming layer (IMP-021 / 6c-5).

Unknown slugs fail closed. Coord is orchestration only — not a publishing desk
and not the publisher. Delivery owner is Ops.
"""

from __future__ import annotations

from mm_common.naming import (
    OPS,
    PUBLISHING_DESKS,
    RESEARCH,
    RETIRED_DESK_SLUGS,
    ROUTE_SLUGS,
    SLEEVE_MAP,
    UnknownNameError,
    WATCHLIST,
    require_publishing_desk,
    require_route_slug,
)
from mm_delivery.config import TelegramSettings

WATCHLIST_PRODUCT = WATCHLIST
PUBLISHER = OPS


def assert_channel_matrix(settings: TelegramSettings) -> None:
    """Fail closed when telegram.yaml drifts from mm_common.naming or Ops ownership."""
    if settings.publisher != OPS or settings.owner != OPS:
        raise UnknownNameError(
            f"delivery publisher/owner must be {OPS!r}; Coord is orchestration only"
        )
    if settings.coordinator not in {"orchestration_only", "coord"}:
        raise UnknownNameError("coordinator must be orchestration_only (not a publisher)")
    configured = set(settings.desks)
    required = set(ROUTE_SLUGS)
    missing = tuple(slug for slug in ROUTE_SLUGS if slug not in configured)
    extra = tuple(sorted(configured - required))
    retired = tuple(sorted(configured & set(RETIRED_DESK_SLUGS)))
    if missing or extra or retired:
        raise UnknownNameError(
            "telegram channel matrix must match naming routes "
            f"{ROUTE_SLUGS}; missing={missing} extra={extra} retired={retired}"
        )
    for slug in configured:
        require_route_slug(slug)
    for slug in PUBLISHING_DESKS:
        require_publishing_desk(slug)
        if slug not in settings.desks:
            raise UnknownNameError(f"publishing desk {slug!r} missing from telegram.yaml")
    product = settings.product(WATCHLIST_PRODUCT)
    if product is None:
        raise UnknownNameError("watchlist delivery product missing from telegram.yaml")
    if product.desk != RESEARCH:
        raise UnknownNameError(
            f"watchlist product desk must be {RESEARCH!r} (naming sleeve_map); got {product.desk!r}"
        )
    if product.sleeve != WATCHLIST:
        raise UnknownNameError(f"watchlist product sleeve must be {WATCHLIST!r}")
    if SLEEVE_MAP.get(product.sleeve) != RESEARCH:
        raise UnknownNameError("watchlist sleeve must map to research")
    if product.kind != WATCHLIST:
        raise UnknownNameError(f"watchlist product kind must be {WATCHLIST!r}")
    if settings.thresholds.spec(WATCHLIST) is None:
        raise UnknownNameError("watchlist kind needs a numeric threshold (never alert without one)")
