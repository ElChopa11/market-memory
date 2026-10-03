"""S3-compatible object-store pointers (checksum + key). Never stores secrets.

Default ingest requires a durable backend (MinIO/S3, or an explicit filesystem root).
In-memory storage is development-only and must be opted into via MM_OBJECT_STORE=memory.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from mm_common.hashing import canonical_json, sha256_hex
from mm_memory.persistence_env import (
    AWS_ACCESS_KEY_ID_ALIAS,
    AWS_DEFAULT_REGION_ALIAS,
    AWS_SECRET_ACCESS_KEY_ALIAS,
    DEFAULT_S3_REGION,
    MINIO_ACCESS_KEY_ENV,
    MINIO_BUCKET_ENV,
    MINIO_ENDPOINT_ENV,
    MINIO_REGION_ALIAS,
    MINIO_ROOT_PASSWORD_ALIAS,
    MINIO_ROOT_USER_ALIAS,
    MINIO_SECRET_KEY_ENV,
    S3_BUCKET_ALIAS,
    S3_ENDPOINT_ALIAS,
    S3_REGION_ENV,
)

logger = logging.getLogger(__name__)

# Explicit development-only backend. Bytes vanish when the process exits.
DEV_MEMORY_BACKEND = "memory"


class ObjectStoreConfigError(RuntimeError):
    """Raw-object persistence was required but no durable store is configured."""


@dataclass(frozen=True)
class ObjectPointer:
    bucket: str
    key: str
    checksum_sha256: str
    byte_size: int
    content_type: str = "application/json"


class ObjectStore(Protocol):
    backend: str

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/json") -> ObjectPointer: ...

    def put_json(self, key: str, payload: Any) -> ObjectPointer: ...

    def get_bytes(self, key: str) -> bytes: ...


class NullObjectStore:
    """No-op store: ingest still works; observations have no raw pointer."""

    backend = "null"

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/json") -> ObjectPointer:
        return ObjectPointer(
            bucket="",
            key="",
            checksum_sha256=sha256_hex(data),
            byte_size=len(data),
            content_type=content_type,
        )

    def put_json(self, key: str, payload: Any) -> ObjectPointer:
        data = canonical_json(payload).encode("utf-8")
        return self.put_bytes(key, data)

    def get_bytes(self, key: str) -> bytes:
        raise FileNotFoundError("NullObjectStore does not persist bytes")


class InMemoryObjectStore:
    """Process-local bytes. DEVELOPMENT ONLY — gone after restart.

    Enable via MM_OBJECT_STORE=memory. Never the default for real ingest.
    """

    backend = DEV_MEMORY_BACKEND

    def __init__(self, *, bucket: str = "market-memory") -> None:
        self.bucket = bucket
        self.objects: dict[str, bytes] = {}

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/json") -> ObjectPointer:
        self.objects[key] = data
        return ObjectPointer(
            bucket=self.bucket,
            key=key,
            checksum_sha256=sha256_hex(data),
            byte_size=len(data),
            content_type=content_type,
        )

    def put_json(self, key: str, payload: Any) -> ObjectPointer:
        data = canonical_json(payload).encode("utf-8")
        return self.put_bytes(key, data)

    def get_bytes(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError as exc:
            raise FileNotFoundError(f"in-memory object missing after restart or never stored: {key}") from exc


class FilesystemObjectStore:
    """Durable local filesystem backend (explicit MM_OBJECT_STORE=filesystem)."""

    backend = "filesystem"

    def __init__(self, *, root: str | Path, bucket: str = "market-memory") -> None:
        self.bucket = bucket
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        relative = Path(key)
        if relative.is_absolute() or ".." in relative.parts:
            raise ObjectStoreConfigError(f"refusing unsafe object key: {key!r}")
        return self.root / self.bucket / relative

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/json") -> ObjectPointer:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return ObjectPointer(
            bucket=self.bucket,
            key=key,
            checksum_sha256=sha256_hex(data),
            byte_size=len(data),
            content_type=content_type,
        )

    def put_json(self, key: str, payload: Any) -> ObjectPointer:
        data = canonical_json(payload).encode("utf-8")
        return self.put_bytes(key, data)

    def get_bytes(self, key: str) -> bytes:
        path = self._path_for(key)
        if not path.is_file():
            raise FileNotFoundError(f"filesystem object missing: {path}")
        return path.read_bytes()


class S3ObjectStore:
    """S3-compatible store via boto3 (local MinIO or Cloudflare R2).

    ``endpoint_url`` is an argument from the environment. Nothing here is
    hardcoded to a MinIO host. Credentials come from the environment, never from git.
    """

    backend = "s3"

    def __init__(
        self,
        *,
        endpoint_url: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ) -> None:
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.region = region
        # endpoint_url is whatever the env supplied (local MinIO or Cloudflare R2).
        # Path-style addressing works for both. Checksums stay when_required so
        # boto3's default CRC32 trailers are not sent to R2.
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
                s3={"addressing_style": "path"},
            ),
        )

    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/json") -> ObjectPointer:
        checksum = sha256_hex(data)
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata={"checksum-sha256": checksum},
        )
        return ObjectPointer(
            bucket=self.bucket,
            key=key,
            checksum_sha256=checksum,
            byte_size=len(data),
            content_type=content_type,
        )

    def put_json(self, key: str, payload: Any) -> ObjectPointer:
        data = canonical_json(payload).encode("utf-8")
        return self.put_bytes(key, data)

    def get_bytes(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"].read()
        if not isinstance(body, (bytes, bytearray)):
            raise TypeError("S3 get_object Body did not return bytes")
        return bytes(body)


def _env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


def s3_region_from_env() -> str:
    """Signing region. Unset → ``us-east-1`` (local MinIO). R2 sets ``S3_REGION=auto``."""
    return _env(S3_REGION_ENV, MINIO_REGION_ALIAS, AWS_DEFAULT_REGION_ALIAS) or DEFAULT_S3_REGION


def object_store_from_env(*, enabled: bool = True) -> ObjectStore:
    """Resolve the raw-object backend.

    Fail closed when persistence is required and MinIO/S3 (or an explicit
    filesystem root) is incomplete. Never silently fall back to in-memory.
    """
    if not enabled:
        logger.info("object store backend=null (raw objects disabled)")
        return NullObjectStore()

    backend = (os.environ.get("MM_OBJECT_STORE") or "s3").strip().lower()
    bucket = _env(MINIO_BUCKET_ENV, S3_BUCKET_ALIAS) or "market-memory"

    if backend in {"none", "null", "disabled", "off"}:
        logger.info("object store backend=null (MM_OBJECT_STORE=%s)", backend)
        return NullObjectStore()

    if backend in {DEV_MEMORY_BACKEND, "inmemory", "in-memory"}:
        logger.warning(
            "object store backend=memory (DEVELOPMENT ONLY; bytes vanish on process exit). "
            "Default ingest requires MinIO/S3 or MM_OBJECT_STORE=filesystem."
        )
        return InMemoryObjectStore(bucket=bucket)

    if backend in {"filesystem", "fs", "file"}:
        root = _env("MM_OBJECT_STORE_PATH")
        if not root:
            raise ObjectStoreConfigError(
                "MM_OBJECT_STORE=filesystem requires MM_OBJECT_STORE_PATH. "
                "Refusing to ingest before any raw_object database pointer is created."
            )
        store = FilesystemObjectStore(root=root, bucket=bucket)
        logger.info("object store backend=filesystem path=%s bucket=%s", store.root, bucket)
        return store

    if backend not in {"s3", "minio"}:
        raise ObjectStoreConfigError(
            f"Unknown MM_OBJECT_STORE={backend!r}. "
            "Use s3 (default), filesystem, memory (development only), or none."
        )

    endpoint = _env(MINIO_ENDPOINT_ENV, S3_ENDPOINT_ALIAS)
    access = _env(MINIO_ACCESS_KEY_ENV, MINIO_ROOT_USER_ALIAS, AWS_ACCESS_KEY_ID_ALIAS)
    secret = _env(MINIO_SECRET_KEY_ENV, MINIO_ROOT_PASSWORD_ALIAS, AWS_SECRET_ACCESS_KEY_ALIAS)
    if not endpoint or not access or not secret:
        raise ObjectStoreConfigError(
            "Raw-object persistence is required but MinIO/S3 is not fully configured "
            "(need MINIO_ENDPOINT or S3_ENDPOINT, plus access and secret keys). "
            "Failing closed before any raw_object database pointer is created. "
            "For fixture ingest without objects, pass --no-objects or set store_raw_objects: false. "
            "For development-only in-memory bytes, set MM_OBJECT_STORE=memory. "
            "For a durable local directory, set MM_OBJECT_STORE=filesystem and MM_OBJECT_STORE_PATH."
        )
    region = s3_region_from_env()
    logger.info("object store backend=s3 endpoint=%s bucket=%s region=%s", endpoint, bucket, region)
    return S3ObjectStore(
        endpoint_url=endpoint,
        bucket=bucket,
        access_key=access,
        secret_key=secret,
        region=region,
    )


def raw_object_key(*, source: str, instrument: str, metric: str, claim_hash: str, ingested_at_iso: str) -> str:
    day = ingested_at_iso[:10].replace("-", "/")
    return f"raw/{source}/{day}/{instrument}/{metric}/{claim_hash[:16]}.json"
