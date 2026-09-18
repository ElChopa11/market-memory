"""Ops-owned Telegram channel matrix bound to the naming layer (IMP-021 / 6c-5).

Unknown slugs fail closed. Coord is orchestration only — not a publishing desk
and not the publisher. Delivery owner is Ops.
"""

from __future__ import annotations

from mm_common.naming import (
    LISTINGS,
    OPS,
    PUBLISHING_DESKS,
    QUANT,
    RESEARCH,
    RETIRED_DESK_SLUGS,
    ROUTE_SLUGS,
    SCORECARD,
    SLEEVE_MAP,
    UnknownNameError,
    WATCHLIST,
    require_publishing_desk,
    require_route_slug,
)
from mm_delivery.config import TelegramSettings

WATCHLIST_PRODUCT = WATCHLIST
LISTINGS_PRODUCT = LISTINGS
SCORECARD_PRODUCT = SCORECARD
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
    _assert_sleeve_product(settings, WATCHLIST_PRODUCT, desk=RESEARCH)
    _assert_sleeve_product(settings, LISTINGS_PRODUCT, desk=RESEARCH)
    _assert_sleeve_product(settings, SCORECARD_PRODUCT, desk=QUANT)


def _assert_sleeve_product(settings: TelegramSettings, slug: str, *, desk: str) -> None:
    product = settings.product(slug)
    if product is None:
        raise UnknownNameError(f"{slug} delivery product missing from telegram.yaml")
    if product.desk != desk:
        raise UnknownNameError(
            f"{slug} product desk must be {desk!r} (naming sleeve_map); got {product.desk!r}"
        )
    if product.sleeve != slug:
        raise UnknownNameError(f"{slug} product sleeve must be {slug!r}")
    if SLEEVE_MAP.get(product.sleeve) != desk:
        raise UnknownNameError(f"{slug} sleeve must map to {desk}")
    if product.kind != slug:
        raise UnknownNameError(f"{slug} product kind must be {slug!r}")
    if settings.thresholds.spec(slug) is None:
        raise UnknownNameError(f"{slug} kind needs a numeric threshold (never alert without one)")
