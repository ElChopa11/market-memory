"""Object-store pointers store checksum + key, not secrets."""

from __future__ import annotations

from mm_common.hashing import canonical_json, sha256_hex
from mm_memory.object_store import InMemoryObjectStore, NullObjectStore, raw_object_key


def test_in_memory_store_checksum_matches_payload() -> None:
    store = InMemoryObjectStore(bucket="market-memory")
    payload = {"coin": "BTC", "fundingRate": "0.0001"}
    pointer = store.put_json("raw/example.json", payload)
    assert pointer.bucket == "market-memory"
    assert pointer.key == "raw/example.json"
    assert pointer.checksum_sha256 == sha256_hex(canonical_json(payload))
    assert "secret" not in pointer.key
    assert store.objects[pointer.key] == canonical_json(payload).encode("utf-8")


def test_null_store_does_not_keep_bytes() -> None:
    pointer = NullObjectStore().put_json("raw/example.json", {"a": 1})
    assert pointer.key == ""
    assert len(pointer.checksum_sha256) == 64


def test_raw_object_key_is_stable_and_safe() -> None:
    key = raw_object_key(
        source="hyperliquid.info",
        instrument="BTC",
        metric="funding",
        claim_hash="abc123def4567890ffff",
        ingested_at_iso="2026-09-10T00:05:00+00:00",
    )
    assert key.startswith("raw/hyperliquid.info/2026/09/10/BTC/funding/")
    assert key.endswith(".json")
