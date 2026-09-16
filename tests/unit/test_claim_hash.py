"""Claim hashing and numeric normalization."""

from __future__ import annotations

from datetime import datetime, timezone

from mm_common.hashing import claim_hash, normalize_numeric
from mm_common.schemas import ClaimIdentity


def test_numeric_normalization_collides_equivalent_decimals() -> None:
    assert normalize_numeric("65000.0") == normalize_numeric("65000.00")
    assert normalize_numeric("-0.0") == "0"


def test_claim_hash_ignores_key_order() -> None:
    a = {"source_name": "hyperliquid.info", "instrument": "BTC", "metric": "mid_px", "value": "1"}
    b = {"value": "1", "metric": "mid_px", "instrument": "BTC", "source_name": "hyperliquid.info"}
    assert claim_hash(a) == claim_hash(b)


def test_claim_hash_changes_with_value() -> None:
    ts = datetime(2026, 9, 9, tzinfo=timezone.utc)
    left = ClaimIdentity(
        source_name="hyperliquid.info",
        instrument="BTC",
        metric="funding",
        market_time=ts,
        value="0.0001",
    )
    right = ClaimIdentity(
        source_name="hyperliquid.info",
        instrument="BTC",
        metric="funding",
        market_time=ts,
        value="0.0002",
    )
    assert claim_hash(left.hash_payload()) != claim_hash(right.hash_payload())
    assert left.slot_payload() == right.slot_payload()
