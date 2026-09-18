"""Redact secrets from notes and exception text. Never print keys or DSN passwords."""

from __future__ import annotations

import re

_DSN_PW = re.compile(r"(postgres(?:ql)?(?:\+psycopg)?://[^:/?#]+:)[^@]+@", re.IGNORECASE)
_AWS_KEY = re.compile(r"(AKIA[0-9A-Z]{16})")
# Common env assignment leaks: NAME=value
_ASSIGNED_SECRETS = re.compile(
    r"\b(FRED_API_KEY|POLYGON_API_KEY|MINIO_SECRET_KEY|MINIO_ACCESS_KEY|MINIO_ROOT_PASSWORD|"
    r"AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|POSTGRES_DSN)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
# Query-string key leaks (FRED `api_key=` on observations URLs)
_QUERY_SECRETS = re.compile(
    r"([?&](?:api_key|apikey|access_key|secret|password|token)=)[^&\s]+",
    re.IGNORECASE,
)


def redact_secrets(text: str) -> str:
    cleaned = _DSN_PW.sub(r"\1***@", text)
    cleaned = _AWS_KEY.sub("AKIA***", cleaned)
    cleaned = _ASSIGNED_SECRETS.sub(lambda m: f"{m.group(1)}=***", cleaned)
    cleaned = _QUERY_SECRETS.sub(r"\1***", cleaned)
    return cleaned


def exception_class(exc: BaseException) -> str:
    return type(exc).__name__
