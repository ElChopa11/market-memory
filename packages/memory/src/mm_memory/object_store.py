"""S3-compatible object-store pointers (checksum + key). Never stores secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from mm_common.hashing import canonical_json, sha256_hex


@dataclass(frozen=True)
class ObjectPointer:
    bucket: str
    key: str
    checksum_sha256: str
    byte_size: int
    content_type: str = "application/json"


class ObjectStore(Protocol):
    def put_bytes(self, key: str, data: bytes, *, content_type: str = "application/json") -> ObjectPointer: ...

    def put_json(self, key: str, payload: Any) -> ObjectPointer: ...


class NullObjectStore:
    """No-op store: ingest still works; observations have no raw pointer."""

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


class InMemoryObjectStore:
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


class S3ObjectStore:
    """MinIO / S3 via boto3. Credentials come from the environment, never from git."""

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

        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
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


def object_store_from_env(*, enabled: bool = True) -> ObjectStore:
    if not enabled:
        return NullObjectStore()
    endpoint = os.environ.get("MINIO_ENDPOINT") or os.environ.get("S3_ENDPOINT")
    access = os.environ.get("MINIO_ACCESS_KEY") or os.environ.get("MINIO_ROOT_USER") or os.environ.get("AWS_ACCESS_KEY_ID")
    secret = os.environ.get("MINIO_SECRET_KEY") or os.environ.get("MINIO_ROOT_PASSWORD") or os.environ.get("AWS_SECRET_ACCESS_KEY")
    bucket = os.environ.get("MINIO_BUCKET") or os.environ.get("S3_BUCKET") or "market-memory"
    if not endpoint or not access or not secret:
        return InMemoryObjectStore(bucket=bucket)
    return S3ObjectStore(endpoint_url=endpoint, bucket=bucket, access_key=access, secret_key=secret)


def raw_object_key(*, source: str, instrument: str, metric: str, claim_hash: str, ingested_at_iso: str) -> str:
    day = ingested_at_iso[:10].replace("-", "/")
    return f"raw/{source}/{day}/{instrument}/{metric}/{claim_hash[:16]}.json"
