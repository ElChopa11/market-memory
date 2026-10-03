#!/usr/bin/env python3
"""Read-only GitHub Actions connectivity probe for Neon and R2.

R2 (secret MINIO_ENDPOINT):
  DNS-resolve the endpoint host and complete a verified TLS handshake
  (default trust store, SNI, certificate check). No S3 API call.

Neon (secret POSTGRES_DSN):
  Connect with SSL. Refuse sslmode=disable and sslmode=allow before any
  socket. Upgrade a missing sslmode, or sslmode=prefer, to require.
  Keep verify-ca and verify-full. Open one transaction, mark it READ ONLY,
  run SELECT 1 and SELECT current_database(), version(), SHOW
  transaction_read_only, then roll the transaction back.

The process prints PASS or FAIL lines and exits 1 when either probe fails.
It does not print the DSN, passwords, or the raw endpoint URL.
"""

from __future__ import annotations

import os
import re
import socket
import ssl
import sys
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

CONNECT_TIMEOUT_S = 15
APPLICATION_NAME = "mm-probe-neon-r2"

SQL_SET_READ_ONLY = "SET TRANSACTION READ ONLY"
SQL_SELECT_ONE = "SELECT 1"
SQL_SELECT_IDENTITY = "SELECT current_database(), version()"
SQL_SHOW_READ_ONLY = "SHOW transaction_read_only"

ALLOWED_SQL = (
    SQL_SET_READ_ONLY,
    SQL_SELECT_ONE,
    SQL_SELECT_IDENTITY,
    SQL_SHOW_READ_ONLY,
)

_REFUSED_SSLMODES = frozenset({"disable", "allow"})
_UPGRADE_SSLMODES = frozenset({"", "prefer"})
_URL_USERINFO = re.compile(r"://([^/\s:@]+):([^/\s@]+)@")
_PASSWORD_KV = re.compile(
    r"(?i)\b(password|secret|token)\s*=\s*('[^']*'|\"[^\"]*\"|\S+)"
)


def r2_tls_target(endpoint: str) -> tuple[str, int]:
    """Return (hostname, tls_port) for a MinIO/R2 endpoint URL or bare host.

    TLS is always the probe. An https URL uses its port (443 when omitted).
    A plaintext URL with an explicit non-443 port is refused so a local
    MinIO :9000 endpoint is not treated as an R2 success.
    """
    raw = endpoint.strip()
    if not raw:
        raise ValueError("MINIO_ENDPOINT is empty")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = parsed.hostname
    if not host:
        raise ValueError("MINIO_ENDPOINT has no host")
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"https", "http"}:
        raise ValueError(f"MINIO_ENDPOINT scheme {scheme!r} is not supported")
    if scheme == "http" and parsed.port not in (None, 443):
        raise ValueError(
            "MINIO_ENDPOINT is plaintext on a non-TLS port; R2 probe expects https"
        )
    port = parsed.port or 443
    return host, port


def resolve_host(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addresses = sorted({item[4][0] for item in infos})
    if not addresses:
        raise OSError("DNS returned no addresses")
    return addresses


def tls_handshake(
    host: str,
    port: int,
    *,
    timeout: float = CONNECT_TIMEOUT_S,
    ssl_context: ssl.SSLContext | None = None,
) -> str:
    ctx = ssl.create_default_context() if ssl_context is None else ssl_context
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            version = ssock.version()
            if not version:
                raise ssl.SSLError("TLS handshake returned no protocol")
            return version


def prepare_neon_conninfo(dsn: str) -> str:
    """Return a libpq conninfo that requires SSL and names this probe.

    Does not open a socket. disable/allow are rejected. prefer and a missing
    sslmode become require. verify-ca and verify-full stay as given.
    """
    raw = dsn.strip()
    if not raw:
        raise ValueError("POSTGRES_DSN is empty")
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    info = conninfo_to_dict(raw)
    mode = str(info.get("sslmode") or "").strip().lower()
    if mode in _REFUSED_SSLMODES:
        raise ValueError(f"sslmode={mode} is refused; this probe requires SSL")
    if mode in _UPGRADE_SSLMODES:
        info["sslmode"] = "require"
    if not str(info.get("application_name") or "").strip():
        info["application_name"] = APPLICATION_NAME
    cleaned = {key: value for key, value in info.items() if value is not None}
    return make_conninfo(**cleaned)


def redact(message: str, *extra: str) -> str:
    """Strip DSNs, endpoint URLs, and password fields before they hit the log."""
    text = message.replace("\n", " ")
    secrets: list[str] = [value for value in extra if value]
    for key in (
        "POSTGRES_DSN",
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ):
        value = os.environ.get(key, "")
        if value:
            secrets.append(value)
    for value in sorted(set(secrets), key=len, reverse=True):
        if len(value) >= 8 and value in text:
            text = text.replace(value, "<redacted>")
    text = _URL_USERINFO.sub(r"://***:***@", text)
    text = _PASSWORD_KV.sub(lambda match: f"{match.group(1)}=***", text)
    return text[:500]


def _ssl_in_use(conn: object) -> bool:
    pgconn = getattr(conn, "pgconn", None)
    if pgconn is None:
        return False
    flag = getattr(pgconn, "ssl_in_use", None)
    if flag is None:
        return False
    if callable(flag):
        flag = flag()
    return bool(flag)


def probe_r2(endpoint: str) -> bool:
    try:
        host, port = r2_tls_target(endpoint)
    except ValueError as exc:
        print(f"R2 FAIL: {redact(str(exc), endpoint)}")
        return False
    try:
        addresses = resolve_host(host, port)
    except OSError as exc:
        print(
            f"R2 DNS FAIL: host={host} port={port} "
            f"error={type(exc).__name__}: {redact(str(exc), endpoint)}"
        )
        print("R2 TLS FAIL: not attempted")
        return False
    print(f"R2 DNS PASS: host={host} port={port} addresses={len(addresses)}")
    try:
        protocol = tls_handshake(host, port)
    except Exception as exc:  # noqa: BLE001 — report the handshake and keep going
        print(
            f"R2 TLS FAIL: host={host} port={port} "
            f"error={type(exc).__name__}: {redact(str(exc), endpoint)}"
        )
        return False
    print(f"R2 TLS PASS: host={host} port={port} protocol={protocol}")
    return True


def probe_neon(dsn: str) -> bool:
    try:
        conninfo = prepare_neon_conninfo(dsn)
    except Exception as exc:  # noqa: BLE001 — bad DSN must fail closed, redacted
        print(f"NEON FAIL: {type(exc).__name__}: {redact(str(exc), dsn)}")
        return False
    try:
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
    except ImportError:
        print("NEON FAIL: psycopg is not installed")
        return False
    sslmode = str(conninfo_to_dict(conninfo).get("sslmode") or "")
    try:
        with psycopg.connect(
            conninfo,
            connect_timeout=CONNECT_TIMEOUT_S,
            prepare_threshold=None,
        ) as conn:
            if not _ssl_in_use(conn):
                print("NEON FAIL: TCP session is up but SSL is not in use")
                return False
            host = str(getattr(conn.info, "host", "") or "")
            with conn.transaction(force_rollback=True):
                conn.execute(SQL_SET_READ_ONLY)
                one = conn.execute(SQL_SELECT_ONE).fetchone()
                ident = conn.execute(SQL_SELECT_IDENTITY).fetchone()
                mode = conn.execute(SQL_SHOW_READ_ONLY).fetchone()
            if one is None or one[0] != 1:
                print("NEON FAIL: SELECT 1 returned an unexpected row")
                return False
            if ident is None or ident[0] is None or ident[1] is None:
                print("NEON FAIL: SELECT current_database(), version() returned an unexpected row")
                return False
            if mode is None or str(mode[0]).strip().lower() != "on":
                print("NEON FAIL: transaction_read_only is not on")
                return False
            database = str(ident[0])
            version = str(ident[1]).split(",")[0][:160]
    except Exception as exc:  # noqa: BLE001 — connectivity failure is a red run
        print(f"NEON FAIL: {type(exc).__name__}: {redact(str(exc), dsn, conninfo)}")
        return False
    print(
        "NEON PASS: "
        f"sslmode={sslmode} ssl=on read_only=on rollback=force "
        f"host={host} database={database} select1=1 server={version}"
    )
    return True


def main() -> int:
    r2_ok = probe_r2(os.environ.get("MINIO_ENDPOINT", ""))
    neon_ok = probe_neon(os.environ.get("POSTGRES_DSN", ""))
    if r2_ok and neon_ok:
        print("PROBE PASS: neon and r2")
        return 0
    failed = []
    if not r2_ok:
        failed.append("r2")
    if not neon_ok:
        failed.append("neon")
    print("PROBE FAIL: " + ",".join(failed))
    return 1


if __name__ == "__main__":
    sys.exit(main())
