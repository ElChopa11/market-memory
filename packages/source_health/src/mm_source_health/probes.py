"""Read-only probes. Classify failures; never copy market prints into notes."""

from __future__ import annotations

import csv
import io
import os
import time
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import httpx
import yaml
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from mm_common.http import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_TIMEOUT,
    classify_exception as classify_transport,
    classify_http_status,
    http_get,
    missing_env_notes,
)
from mm_common.time import utcnow
from mm_ingest.hl_info import (
    ALLOWED_INFO_TYPES,
    FORBIDDEN_INFO_TYPES,
    HyperliquidInfoClient,
    HyperliquidInfoError,
)
from mm_memory.db import dsn_from_env, normalize_dsn
from mm_memory.models import Observation, Source
from mm_memory.object_store import ObjectStoreConfigError, object_store_from_env
from mm_source_health.config import load_inventory_config
from mm_source_health.models import (
    DISPLAY_NAME,
    PULSE_ROLE,
    SOURCE_INVENTORY,
    STATUS_DEGRADED,
    STATUS_OK,
    STATUS_UNAVAILABLE,
    SourceHealth,
    fallback_row,
)
from mm_source_health.redact import exception_class, redact_secrets

HL_PROBE_TYPE = "meta"
HL_GATE_TYPE = "clearinghouseState"
COINGECKO_PING_PATH = "/api/v3/ping"


class ProbeContext:
    def __init__(
        self,
        *,
        repo_root: Path,
        env: Mapping[str, str] | None = None,
        captured_at: datetime | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
        hl_client: HyperliquidInfoClient | None = None,
        skip_db: bool = False,
        dsn: str | None = None,
        last_success: Mapping[str, datetime] | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        sleep: Any | None = None,
    ) -> None:
        self.repo_root = repo_root
        self._custom_env = env is not None
        self.env = dict(env) if env is not None else dict(os.environ)
        self.captured_at = captured_at or utcnow()
        self.timeout = timeout
        self.http_client = http_client
        self.hl_client = hl_client
        self.skip_db = skip_db
        self.dsn = dsn
        self.last_success = dict(last_success or {})
        self.config = load_inventory_config(repo_root)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)
        self.max_attempts = max_attempts
        self.sleep = sleep if sleep is not None else time.sleep

    def getenv(self, name: str) -> str | None:
        value = self.env.get(name)
        if value is None or str(value).strip() == "":
            return None
        return str(value)

    def http_get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        parse_json: bool = False,
    ):
        return http_get(
            self._http,
            url,
            params=params,
            max_attempts=self.max_attempts,
            sleep=self.sleep,
            parse_json=parse_json,
        )

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> ProbeContext:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def probe_all(ctx: ProbeContext) -> tuple[SourceHealth, ...]:
    rows: list[SourceHealth] = []
    for source_id in SOURCE_INVENTORY:
        probe = _PROBES[source_id]
        try:
            rows.append(probe(ctx))
        except Exception as exc:  # noqa: BLE001 — inventory row must still appear
            rows.append(
                fallback_row(
                    source_id,
                    error_class=_classify_exception(exc),
                    notes=(redact_secrets(f"{exception_class(exc)}: {exc}"),),
                )
            )
    present = {row.source_id for row in rows}
    for source_id in SOURCE_INVENTORY:
        if source_id not in present:
            rows.append(fallback_row(source_id, notes=("probe did not return a row",)))
    order = {sid: i for i, sid in enumerate(SOURCE_INVENTORY)}
    rows.sort(key=lambda row: order.get(row.source_id, len(order)))
    return tuple(rows)


def _row(
    source_id: str,
    *,
    status: str,
    error_class: str = "none",
    latency_ms: float | None = None,
    last_success_at: datetime | None = None,
    credentials_present: str = "n/a",
    notes: tuple[str, ...] = (),
    endpoint: str | None = None,
    probe: str | None = None,
) -> SourceHealth:
    return SourceHealth(
        source_id=source_id,
        display_name=DISPLAY_NAME[source_id],
        pulse_role=PULSE_ROLE[source_id],
        status=status,
        latency_ms=latency_ms,
        error_class=error_class,
        last_success_at=last_success_at,
        credentials_present=credentials_present,
        notes=notes,
        endpoint=endpoint,
        probe=probe,
    )


def probe_hyperliquid(ctx: ProbeContext) -> SourceHealth:
    url = str(ctx.config["hl_info_url"])
    notes: list[str] = []
    gate_ok, gate_note = _allowlist_gate()
    notes.append(gate_note)
    if not gate_ok:
        return _row(
            "hyperliquid.info",
            status=STATUS_UNAVAILABLE,
            error_class="allowlist_bypass",
            credentials_present="n/a",
            notes=tuple(notes),
            endpoint=url,
            probe=f"POST type={HL_PROBE_TYPE} (allowlist)",
        )

    client = ctx.hl_client
    owns = False
    if client is None:
        client = HyperliquidInfoClient(url=url, timeout=ctx.timeout)
        owns = True
    started = time.perf_counter()
    try:
        payload = client.post({"type": HL_PROBE_TYPE})
        latency = _ms(started)
        if not isinstance(payload, dict) or not payload:
            return _row(
                "hyperliquid.info",
                status=STATUS_DEGRADED,
                error_class="parse_error",
                latency_ms=latency,
                last_success_at=ctx.last_success.get("hyperliquid.info"),
                credentials_present="n/a",
                notes=tuple(notes + ["meta payload empty or not an object; no prints recorded"]),
                endpoint=url,
                probe=f"POST type={HL_PROBE_TYPE} (allowlist)",
            )
        last = ctx.captured_at
        memory_last = ctx.last_success.get("hyperliquid.info")
        return _row(
            "hyperliquid.info",
            status=STATUS_OK,
            latency_ms=latency,
            last_success_at=memory_last or last,
            credentials_present="n/a",
            notes=tuple(
                notes
                + [
                    f"allowlisted probe type={HL_PROBE_TYPE} HTTP ok",
                    "payload shape recorded only (no mids/marks copied into this report)",
                    f"known allowlist size={len(ALLOWED_INFO_TYPES)}; forbidden types remain blocked",
                ]
            ),
            endpoint=url,
            probe=f"POST type={HL_PROBE_TYPE} (allowlist)",
        )
    except HyperliquidInfoError as exc:
        return _row(
            "hyperliquid.info",
            status=STATUS_UNAVAILABLE,
            error_class=_classify_exception(exc),
            latency_ms=_ms(started),
            last_success_at=ctx.last_success.get("hyperliquid.info"),
            credentials_present="n/a",
            notes=tuple(notes + [redact_secrets(str(exc))]),
            endpoint=url,
            probe=f"POST type={HL_PROBE_TYPE} (allowlist)",
        )
    except Exception as exc:  # noqa: BLE001
        return _row(
            "hyperliquid.info",
            status=STATUS_UNAVAILABLE,
            error_class=_classify_exception(exc),
            latency_ms=_ms(started),
            last_success_at=ctx.last_success.get("hyperliquid.info"),
            credentials_present="n/a",
            notes=tuple(notes + [redact_secrets(f"{exception_class(exc)}")]),
            endpoint=url,
            probe=f"POST type={HL_PROBE_TYPE} (allowlist)",
        )
    finally:
        if owns:
            client.close()


def _allowlist_gate() -> tuple[bool, str]:
    """Refuse a forbidden type locally (no HTTP). Confirms the ingest client still gates."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"leaked": True})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(handler), timeout=1.0)
    try:
        client.post({"type": HL_GATE_TYPE, "user": "0x" + "0" * 40})
    except HyperliquidInfoError as exc:
        if "refusing non-public" in str(exc) and HL_GATE_TYPE in FORBIDDEN_INFO_TYPES:
            return True, f"allowlist gate: {HL_GATE_TYPE} refused locally (no HTTP)"
        return False, redact_secrets(f"allowlist gate unexpected error: {exc}")
    finally:
        client.close()
    return False, f"allowlist gate FAILED: {HL_GATE_TYPE} was not refused"


def probe_coingecko(ctx: ProbeContext) -> SourceHealth:
    spec = ctx.config["coingecko"]
    ping_url = _coingecko_ping_url(spec)
    started = time.perf_counter()
    result = ctx.http_get(ping_url)
    latency = result.latency_ms if result.latency_ms else _ms(started)
    if result.ok:
        # Do not copy gecko_says / any payload text into the report.
        return _row(
            "coingecko",
            status=STATUS_OK,
            latency_ms=latency,
            last_success_at=ctx.captured_at,
            credentials_present="n/a",
            notes=("ping HTTP 200; no price payload requested",),
            endpoint=ping_url,
            probe="GET /api/v3/ping",
        )
    extra = f"attempts={result.attempts}"
    if result.status_code is not None:
        detail = f"ping HTTP {result.status_code} (error_class={result.error_class})"
    else:
        detail = redact_secrets(result.exception_name or result.error_class)
    return _row(
        "coingecko",
        status=STATUS_UNAVAILABLE,
        error_class=result.error_class,
        latency_ms=latency,
        last_success_at=None,
        credentials_present="n/a",
        notes=(detail, extra),
        endpoint=ping_url,
        probe="GET /api/v3/ping",
    )


def probe_stooq(ctx: ProbeContext) -> SourceHealth:
    spec = ctx.config["stooq"]
    symbols = spec.get("symbols") or {}
    if not isinstance(symbols, dict) or not symbols:
        symbols = {"ES": "es.f"}
    canary_symbol, canary_ticker = next(iter(symbols.items()))
    base = str(spec.get("base_url") or "https://stooq.com/q/l/").rstrip("/") + "/"
    query = urlencode({"s": canary_ticker, "f": "sd2t2ohlcv", "h": "", "e": "csv"})
    url = f"{base}?{query}"
    result = ctx.http_get(url)
    shared_notes = (
        f"configured symbols: {', '.join(str(s) for s in symbols)}",
        "no quote values recorded; no scrape fallback (ToS)",
        f"attempts={result.attempts} (retry only timeout/5xx/429; 404 is terminal)",
    )
    if result.status_code is not None and result.status_code != 200:
        return _row(
            "stooq",
            status=STATUS_UNAVAILABLE,
            error_class=result.error_class,
            latency_ms=result.latency_ms,
            credentials_present="n/a",
            notes=(
                f"canary {canary_symbol} HTTP {result.status_code} (error_class={result.error_class})",
                *shared_notes,
            ),
            endpoint=_stooq_endpoint_label(base),
            probe=f"GET canary CSV ({canary_symbol})",
        )
    if not result.ok:
        return _row(
            "stooq",
            status=STATUS_UNAVAILABLE,
            error_class=result.error_class,
            latency_ms=result.latency_ms,
            credentials_present="n/a",
            notes=(
                redact_secrets(result.exception_name or result.error_class),
                *shared_notes,
            ),
            endpoint=_stooq_endpoint_label(base),
            probe=f"GET canary CSV ({canary_symbol})",
        )
    parsed_ok = _stooq_csv_has_close(result.text or "")
    if not parsed_ok:
        return _row(
            "stooq",
            status=STATUS_UNAVAILABLE,
            error_class="parse_error",
            latency_ms=result.latency_ms,
            credentials_present="n/a",
            notes=(
                f"canary {canary_symbol} CSV empty, N/D, or unparseable",
                *shared_notes,
            ),
            endpoint=_stooq_endpoint_label(base),
            probe=f"GET canary CSV ({canary_symbol})",
        )
    return _row(
        "stooq",
        status=STATUS_OK,
        latency_ms=result.latency_ms,
        last_success_at=ctx.captured_at,
        credentials_present="n/a",
        notes=(
            f"canary {canary_symbol} CSV parsed (Close present; value not copied)",
            f"configured symbols: {', '.join(str(s) for s in symbols)}",
            f"attempts={result.attempts}",
        ),
        endpoint=_stooq_endpoint_label(base),
        probe=f"GET canary CSV ({canary_symbol})",
    )


def probe_fred(ctx: ProbeContext) -> SourceHealth:
    spec = ctx.config["fred"]
    env_name = str(spec.get("api_key_env") or "FRED_API_KEY")
    base = str(spec.get("base_url") or "https://api.stlouisfed.org/fred/series/observations")
    series = spec.get("series") or {"US10Y": "DGS10"}
    if not isinstance(series, dict) or not series:
        series = {"US10Y": "DGS10"}
    series_id = next(iter(series.values()))
    key = ctx.getenv(env_name)
    if not key:
        return _row(
            "fred",
            status=STATUS_UNAVAILABLE,
            error_class="missing_env",
            credentials_present="no",
            notes=missing_env_notes(env_name, source="FRED"),
            endpoint=base,
            probe=f"GET series_id={series_id} limit=1",
        )
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    result = ctx.http_get(base, params=params, parse_json=True)
    if result.status_code in {401, 400, 403} or (
        not result.ok and result.status_code is not None and result.status_code != 200
    ):
        return _row(
            "fred",
            status=STATUS_UNAVAILABLE,
            error_class=result.error_class,
            latency_ms=result.latency_ms,
            credentials_present="yes",
            notes=(
                f"HTTP {result.status_code} (error_class={result.error_class}; key present, not printed)",
                f"attempts={result.attempts}",
            ),
            endpoint=base,
            probe=f"GET series_id={series_id} limit=1",
        )
    if not result.ok:
        return _row(
            "fred",
            status=STATUS_UNAVAILABLE,
            error_class=result.error_class,
            latency_ms=result.latency_ms,
            credentials_present="yes",
            notes=(
                redact_secrets(result.exception_name or result.error_class),
                "key value not printed",
                f"attempts={result.attempts}",
            ),
            endpoint=base,
            probe=f"GET series_id={series_id} limit=1",
        )
    payload = result.json_payload if isinstance(result.json_payload, dict) else {}
    observations = payload.get("observations") if isinstance(payload, dict) else None
    if not observations:
        return _row(
            "fred",
            status=STATUS_DEGRADED,
            error_class="parse_error",
            latency_ms=result.latency_ms,
            credentials_present="yes",
            notes=("HTTP 200 but no observations in payload; no yield recorded",),
            endpoint=base,
            probe=f"GET series_id={series_id} limit=1",
        )
    return _row(
        "fred",
        status=STATUS_OK,
        latency_ms=result.latency_ms,
        last_success_at=ctx.captured_at,
        credentials_present="yes",
        notes=("observations endpoint HTTP 200; yield not copied into this report",),
        endpoint=base,
        probe=f"GET series_id={series_id} limit=1",
    )


def probe_calendar(ctx: ProbeContext) -> SourceHealth:
    path: Path = ctx.config["calendar_path"]
    rel = "config/briefing/calendar.yaml"
    if not path.is_file():
        return _row(
            "calendar.yaml",
            status=STATUS_UNAVAILABLE,
            error_class="config_error",
            credentials_present="n/a",
            notes=(f"{rel} missing",),
            endpoint=rel,
            probe="YAML parse",
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return _row(
            "calendar.yaml",
            status=STATUS_UNAVAILABLE,
            error_class="parse_error",
            credentials_present="n/a",
            notes=(redact_secrets(f"{rel} failed to parse: {exception_class(exc)}"),),
            endpoint=rel,
            probe="YAML parse",
        )
    if not isinstance(data, dict):
        return _row(
            "calendar.yaml",
            status=STATUS_DEGRADED,
            error_class="parse_error",
            credentials_present="n/a",
            notes=(f"{rel} is not a mapping",),
            endpoint=rel,
            probe="YAML parse",
        )
    events = data.get("events") or []
    count = len(events) if isinstance(events, list) else 0
    source = str(data.get("source") or "unknown")
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=ctx.captured_at.tzinfo)
    return _row(
        "calendar.yaml",
        status=STATUS_OK,
        last_success_at=mtime,
        credentials_present="n/a",
        notes=(
            f"fixture file present; source={source}; event rows={count}",
            "no live calendar API configured",
        ),
        endpoint=rel,
        probe="YAML parse",
    )


def probe_postgres(ctx: ProbeContext) -> SourceHealth:
    if ctx.skip_db:
        return _row(
            "postgres",
            status=STATUS_DEGRADED,
            error_class="skipped",
            credentials_present=_dsn_present(ctx),
            notes=("--no-db: probe skipped (Pulse can still run without indexing)",),
            endpoint="POSTGRES_DSN",
            probe="SELECT 1",
        )
    if ctx.dsn:
        dsn = ctx.dsn
    elif ctx.getenv("POSTGRES_DSN"):
        dsn = ctx.getenv("POSTGRES_DSN")
    elif ctx._custom_env:
        return _row(
            "postgres",
            status=STATUS_UNAVAILABLE,
            error_class="missing_env",
            credentials_present="no",
            notes=("missing env POSTGRES_DSN; Postgres unavailable", "DSN not printed"),
            endpoint="POSTGRES_DSN",
            probe="SELECT 1",
        )
    else:
        dsn = dsn_from_env()

    started = time.perf_counter()
    engine = None
    try:
        engine = create_engine(
            normalize_dsn(dsn),
            echo=False,
            future=True,
            connect_args={"connect_timeout": max(1, int(ctx.timeout))},
            pool_pre_ping=True,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            last = None
            try:
                last = conn.execute(select(func.max(Observation.ingested_at))).scalar_one_or_none()
            except Exception:  # noqa: BLE001 — schema may be absent
                last = None
        latency = _ms(started)
        notes = ["SELECT 1 ok; DSN not printed"]
        if last is None:
            notes.append("no observation.ingested_at yet (empty or unmigrated)")
        else:
            notes.append("last observation.ingested_at recorded as last success")
            ctx.last_success.setdefault("hyperliquid.info", last)
        return _row(
            "postgres",
            status=STATUS_OK,
            latency_ms=latency,
            last_success_at=last,
            credentials_present="yes",
            notes=tuple(notes),
            endpoint="POSTGRES_DSN",
            probe="SELECT 1",
        )
    except Exception as exc:  # noqa: BLE001
        return _row(
            "postgres",
            status=STATUS_UNAVAILABLE,
            error_class=_classify_exception(exc),
            latency_ms=_ms(started),
            credentials_present=_dsn_present(ctx) if dsn else "no",
            notes=(redact_secrets(exception_class(exc)), "DSN not printed"),
            endpoint="POSTGRES_DSN",
            probe="SELECT 1",
        )
    finally:
        if engine is not None:
            engine.dispose()


def load_last_success_from_memory(dsn: str, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, datetime]:
    engine = create_engine(
        normalize_dsn(dsn),
        echo=False,
        future=True,
        connect_args={"connect_timeout": max(1, int(timeout))},
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    out: dict[str, datetime] = {}
    session: Session | None = None
    try:
        session = factory()
        stmt = (
            select(Source.name, func.max(Observation.ingested_at))
            .join(Observation, Observation.source_id == Source.id)
            .group_by(Source.name)
        )
        for name, ts in session.execute(stmt):
            if name and ts is not None:
                if str(name).startswith("hyperliquid"):
                    out["hyperliquid.info"] = ts
                out[str(name)] = ts
    except Exception:  # noqa: BLE001
        return {}
    finally:
        if session is not None:
            session.close()
        engine.dispose()
    return out


def probe_object_store(ctx: ProbeContext) -> SourceHealth:
    backend = (ctx.getenv("MM_OBJECT_STORE") or "s3").strip().lower()
    creds = _object_store_creds_present(ctx, backend)
    started = time.perf_counter()
    # Isolate object_store_from_env from process os.environ by applying ctx.env.
    restore = _push_env(ctx.env)
    try:
        try:
            store = object_store_from_env(enabled=True)
        except ObjectStoreConfigError:
            return _row(
                "object_store",
                status=STATUS_UNAVAILABLE,
                error_class="missing_env",
                latency_ms=_ms(started),
                credentials_present=creds,
                notes=(
                    "MinIO/S3 env incomplete; fail-closed (same as ingest)",
                    "secret values not printed",
                ),
                endpoint=_object_store_endpoint_label(ctx, backend),
                probe="env + ping",
            )
        ping_note, ping_error = _ping_store(store)
        latency = _ms(started)
        if ping_error:
            return _row(
                "object_store",
                status=STATUS_UNAVAILABLE,
                error_class=ping_error,
                latency_ms=latency,
                credentials_present=creds,
                notes=(ping_note, f"backend={store.backend}", "secret values not printed"),
                endpoint=_object_store_endpoint_label(ctx, backend),
                probe="env + ping",
            )
        status = STATUS_OK
        extra = ping_note
        if store.backend == "memory":
            status = STATUS_DEGRADED
            extra = "backend=memory (development only; not durable)"
        elif store.backend == "null":
            extra = "backend=null (raw objects disabled; honest)"
        return _row(
            "object_store",
            status=status,
            latency_ms=latency,
            last_success_at=ctx.captured_at if status == STATUS_OK else None,
            credentials_present=creds,
            notes=(extra, "secret values not printed"),
            endpoint=_object_store_endpoint_label(ctx, store.backend),
            probe="env + ping",
        )
    except Exception as exc:  # noqa: BLE001
        return _row(
            "object_store",
            status=STATUS_UNAVAILABLE,
            error_class=_classify_exception(exc),
            latency_ms=_ms(started),
            credentials_present=creds,
            notes=(redact_secrets(exception_class(exc)), "secret values not printed"),
            endpoint=_object_store_endpoint_label(ctx, backend),
            probe="env + ping",
        )
    finally:
        _pop_env(restore)


def _ping_store(store: Any) -> tuple[str, str | None]:
    backend = getattr(store, "backend", "")
    if backend == "s3":
        client = getattr(store, "_client", None)
        bucket = getattr(store, "bucket", "")
        if client is None:
            return "s3 client missing", "config_error"
        try:
            client.head_bucket(Bucket=bucket)
            return f"HeadBucket ok bucket={bucket}", None
        except Exception as exc:  # noqa: BLE001
            return f"HeadBucket {exception_class(exc)}", _classify_exception(exc)
    if backend == "filesystem":
        root = getattr(store, "root", None)
        if root is None or not Path(root).exists():
            return "filesystem root missing", "config_error"
        return f"filesystem root present", None
    if backend in {"null", "memory"}:
        return f"backend={backend} (no network ping)", None
    return f"backend={backend}", None


def _push_env(env: Mapping[str, str]) -> dict[str, str | None]:
    """Apply a test env mapping for object_store_from_env (reads os.environ)."""
    keys = (
        "MM_OBJECT_STORE",
        "MM_OBJECT_STORE_PATH",
        "MINIO_ENDPOINT",
        "S3_ENDPOINT",
        "MINIO_BUCKET",
        "S3_BUCKET",
        "MINIO_ACCESS_KEY",
        "MINIO_ROOT_USER",
        "AWS_ACCESS_KEY_ID",
        "MINIO_SECRET_KEY",
        "MINIO_ROOT_PASSWORD",
        "AWS_SECRET_ACCESS_KEY",
    )
    restore: dict[str, str | None] = {}
    for key in keys:
        restore[key] = os.environ.get(key)
        if key in env:
            value = env[key]
            if value == "":
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        else:
            os.environ.pop(key, None)
    return restore


def _pop_env(restore: Mapping[str, str | None]) -> None:
    for key, value in restore.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _object_store_creds_present(ctx: ProbeContext, backend: str) -> str:
    if backend in {"none", "null", "disabled", "off", "memory", "inmemory", "in-memory"}:
        return "n/a"
    if backend in {"filesystem", "fs", "file"}:
        return "yes" if ctx.getenv("MM_OBJECT_STORE_PATH") else "no"
    endpoint = ctx.getenv("MINIO_ENDPOINT") or ctx.getenv("S3_ENDPOINT")
    access = ctx.getenv("MINIO_ACCESS_KEY") or ctx.getenv("MINIO_ROOT_USER") or ctx.getenv("AWS_ACCESS_KEY_ID")
    secret = ctx.getenv("MINIO_SECRET_KEY") or ctx.getenv("MINIO_ROOT_PASSWORD") or ctx.getenv("AWS_SECRET_ACCESS_KEY")
    if endpoint and access and secret:
        return "yes"
    if endpoint or access or secret:
        return "incomplete"
    return "no"


def _object_store_endpoint_label(ctx: ProbeContext, backend: str) -> str:
    if backend in {"filesystem", "fs", "file"}:
        return "MM_OBJECT_STORE_PATH"
    if backend in {"none", "null", "disabled", "off", "memory"}:
        return f"MM_OBJECT_STORE={backend}"
    return "MINIO_ENDPOINT/S3_ENDPOINT"


def _dsn_present(ctx: ProbeContext) -> str:
    if ctx.dsn or ctx.getenv("POSTGRES_DSN"):
        return "yes"
    return "no"


def _coingecko_ping_url(spec: dict[str, Any]) -> str:
    base = str(spec.get("base_url") or "https://api.coingecko.com/api/v3/simple/price")
    parsed = urlparse(base)
    return urlunparse((parsed.scheme or "https", parsed.netloc or "api.coingecko.com", COINGECKO_PING_PATH, "", "", ""))


def _stooq_endpoint_label(base: str) -> str:
    parsed = urlparse(base)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def _stooq_csv_has_close(text: str) -> bool:
    try:
        reader = csv.DictReader(io.StringIO(text.strip()))
        rows = list(reader)
    except csv.Error:
        return False
    if not rows:
        return False
    raw = rows[0].get("Close") or rows[0].get("close")
    if raw is None or str(raw).strip() in {"", "N/D", "N/A", "-"}:
        return False
    try:
        float(raw)
    except (TypeError, ValueError):
        return False
    return True


def _ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 1)


def _http_error_class(status_code: int) -> str:
    return classify_http_status(status_code)


def _classify_exception(exc: BaseException) -> str:
    if isinstance(exc, HyperliquidInfoError):
        msg = str(exc).lower()
        if "refusing" in msg or "allowlist" in msg:
            return "forbidden_type_blocked"
        if "failed:" in msg:
            return "http_error"
        return "http_error"
    if isinstance(exc, ObjectStoreConfigError):
        return "missing_env"
    return classify_transport(exc)


_PROBES = {
    "hyperliquid.info": probe_hyperliquid,
    "coingecko": probe_coingecko,
    "stooq": probe_stooq,
    "fred": probe_fred,
    "calendar.yaml": probe_calendar,
    "postgres": probe_postgres,
    "object_store": probe_object_store,
}

