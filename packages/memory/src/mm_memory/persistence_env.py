"""Env names for managed Postgres (Neon) and an S3-compatible object store (R2).

Names only. This module holds no values and does not connect.

GitHub Actions is the execution host that writes (ADR 0019). These names are
Actions secret names (or, for ``S3_REGION``, a non-secret workflow env var).
They do not belong on the bot box.

The ``MINIO_*`` names are what the client reads first. They are not a MinIO-only
backend: ``endpoint_url`` comes from the env value (MinIO locally, R2 when
Principal supplies an R2 endpoint).
"""

from __future__ import annotations

from mm_common.env import (
    MINIO_ACCESS_KEY_ENV,
    MINIO_BUCKET_ENV,
    MINIO_ENDPOINT_ENV,
    MINIO_SECRET_KEY_ENV,
    POSTGRES_DSN_ENV,
)

S3_ENDPOINT_ALIAS = "S3_ENDPOINT"
S3_BUCKET_ALIAS = "S3_BUCKET"
AWS_ACCESS_KEY_ID_ALIAS = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY_ALIAS = "AWS_SECRET_ACCESS_KEY"
MINIO_ROOT_USER_ALIAS = "MINIO_ROOT_USER"
MINIO_ROOT_PASSWORD_ALIAS = "MINIO_ROOT_PASSWORD"

# Not a secret. R2 wants ``auto``. Unset keeps local MinIO on us-east-1.
S3_REGION_ENV = "S3_REGION"
MINIO_REGION_ALIAS = "MINIO_REGION"
AWS_DEFAULT_REGION_ALIAS = "AWS_DEFAULT_REGION"
DEFAULT_S3_REGION = "us-east-1"

# Repository secrets Principal creates before any live wire. One name each.
# Aliases above are accepted by the client; do not also set the alias.
ACTIONS_SECRET_NAMES: tuple[str, ...] = (
    POSTGRES_DSN_ENV,
    MINIO_ENDPOINT_ENV,
    MINIO_BUCKET_ENV,
    MINIO_ACCESS_KEY_ENV,
    MINIO_SECRET_KEY_ENV,
)
