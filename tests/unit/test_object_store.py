"""Object-store pointers store checksum + key, not secrets.

Fail closed when durable storage is required but unconfigured. In-memory is
opt-in development only. NullObjectStore must not invent raw_object keys.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mm_common.hashing import canonical_json, sha256_hex
from mm_memory.object_store import (
    FilesystemObjectStore,
    InMemoryObjectStore,
    NullObjectStore,
    ObjectStoreConfigError,
    S3ObjectStore,
    object_store_from_env,
    raw_object_key,
    s3_region_from_env,
)


def test_in_memory_store_checksum_matches_payload() -> None:
    store = InMemoryObjectStore(bucket="market-memory")
    payload = {"coin": "BTC", "fundingRate": "0.0001"}
    pointer = store.put_json("raw/example.json", payload)
    assert pointer.bucket == "market-memory"
    assert pointer.key == "raw/example.json"
    assert pointer.checksum_sha256 == sha256_hex(canonical_json(payload))
    assert "secret" not in pointer.key
    assert store.objects[pointer.key] == canonical_json(payload).encode("utf-8")
    assert store.get_bytes(pointer.key) == canonical_json(payload).encode("utf-8")


def test_null_store_does_not_keep_bytes() -> None:
    pointer = NullObjectStore().put_json("raw/example.json", {"a": 1})
    assert pointer.key == ""
    assert pointer.bucket == ""
    assert len(pointer.checksum_sha256) == 64
    with pytest.raises(FileNotFoundError):
        NullObjectStore().get_bytes("raw/example.json")


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


def test_from_env_misconfigured_s3_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MM_OBJECT_STORE", raising=False)
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_USER", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_PASSWORD", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    with pytest.raises(ObjectStoreConfigError, match="Failing closed"):
        object_store_from_env(enabled=True)


def test_from_env_partial_minio_env_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MM_OBJECT_STORE", raising=False)
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_USER", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_PASSWORD", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    with pytest.raises(ObjectStoreConfigError, match="Failing closed"):
        object_store_from_env()


def test_from_env_explicit_memory_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MM_OBJECT_STORE", "memory")
    store = object_store_from_env(enabled=True)
    assert isinstance(store, InMemoryObjectStore)
    assert store.backend == "memory"


def test_from_env_disabled_is_null(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MM_OBJECT_STORE", raising=False)
    store = object_store_from_env(enabled=False)
    assert isinstance(store, NullObjectStore)
    monkeypatch.setenv("MM_OBJECT_STORE", "none")
    store = object_store_from_env(enabled=True)
    assert isinstance(store, NullObjectStore)


def test_from_env_filesystem_requires_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MM_OBJECT_STORE", "filesystem")
    monkeypatch.delenv("MM_OBJECT_STORE_PATH", raising=False)
    with pytest.raises(ObjectStoreConfigError, match="MM_OBJECT_STORE_PATH"):
        object_store_from_env()


def test_from_env_filesystem_is_durable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MM_OBJECT_STORE", "filesystem")
    monkeypatch.setenv("MM_OBJECT_STORE_PATH", str(tmp_path))
    store = object_store_from_env()
    assert isinstance(store, FilesystemObjectStore)
    pointer = store.put_json("raw/restart.json", {"ok": True})
    restarted = FilesystemObjectStore(root=tmp_path, bucket=store.bucket)
    assert restarted.get_bytes(pointer.key) == canonical_json({"ok": True}).encode("utf-8")


def test_in_memory_restart_loses_bytes_durable_path_does_not(tmp_path: Path) -> None:
    """The old silent-fallback bug: a new InMemoryObjectStore cannot retrieve bytes.

    Durable filesystem still returns the payload after a 'restart'.
    """
    payload = {"coin": "BTC", "mid": "65000"}
    ephemeral = InMemoryObjectStore()
    pointer = ephemeral.put_json("raw/btc.json", payload)
    assert ephemeral.get_bytes(pointer.key)

    restarted_memory = InMemoryObjectStore()
    with pytest.raises(FileNotFoundError, match="in-memory object missing"):
        restarted_memory.get_bytes(pointer.key)

    durable = FilesystemObjectStore(root=tmp_path)
    durable_pointer = durable.put_json("raw/btc.json", payload)
    restarted_fs = FilesystemObjectStore(root=tmp_path)
    assert restarted_fs.get_bytes(durable_pointer.key) == canonical_json(payload).encode("utf-8")


def test_s3_region_defaults_us_east_1_and_honours_s3_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("S3_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    monkeypatch.delenv("AWS_REGION", raising=False)
    assert s3_region_from_env() == "us-east-1"

    monkeypatch.delenv("MM_OBJECT_STORE", raising=False)
    monkeypatch.setenv("MINIO_ENDPOINT", "https://example.r2.cloudflarestorage.com")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "test-access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "test-secret")
    monkeypatch.delenv("MINIO_BUCKET", raising=False)
    monkeypatch.delenv("S3_BUCKET", raising=False)
    monkeypatch.setenv("S3_REGION", "auto")
    store = object_store_from_env()
    assert isinstance(store, S3ObjectStore)
    assert store.bucket == "market-memory"
    assert store.region == "auto"
    assert store._client.meta.region_name == "auto"


def test_from_env_unknown_backend_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MM_OBJECT_STORE", "redis")
    with pytest.raises(ObjectStoreConfigError, match="Unknown MM_OBJECT_STORE"):
        object_store_from_env()


def test_from_env_does_not_read_unrelated_env_as_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Incomplete MinIO must not degrade to InMemoryObjectStore."""
    for key in list(os.environ):
        if key.startswith(("MINIO_", "S3_", "AWS_ACCESS", "AWS_SECRET", "MM_OBJECT")):
            monkeypatch.delenv(key, raising=False)
    with pytest.raises(ObjectStoreConfigError):
        object_store_from_env()
    # Explicit memory remains the only path to InMemoryObjectStore from env.
    monkeypatch.setenv("MM_OBJECT_STORE", "memory")
    assert isinstance(object_store_from_env(), InMemoryObjectStore)
