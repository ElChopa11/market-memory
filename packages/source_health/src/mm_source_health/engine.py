"""Generate a standing source-health report. Read-only. No trading imports."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

import httpx

from mm_common.time import utcnow
from mm_ingest.hl_info import HyperliquidInfoClient
from mm_source_health.models import HealthReport
from mm_source_health.probes import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_TIMEOUT,
    ProbeContext,
    load_last_success_from_memory,
    probe_all,
)
from mm_source_health.report import render_report


def generate_source_health(
    *,
    repo_root: Path,
    captured_at: datetime | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    env: Mapping[str, str] | None = None,
    http_client: httpx.Client | None = None,
    hl_client: HyperliquidInfoClient | None = None,
    skip_db: bool = False,
    dsn: str | None = None,
    command: str = "lab data source-health",
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep=None,
) -> HealthReport:
    generated_at = captured_at or utcnow()
    last_success: dict = {}
    resolved_dsn = dsn
    if resolved_dsn is None and env is not None:
        raw = env.get("POSTGRES_DSN")
        resolved_dsn = raw if raw else None
    elif resolved_dsn is None and not skip_db:
        from mm_memory.db import dsn_from_env

        resolved_dsn = dsn_from_env()
    if not skip_db and resolved_dsn:
        try:
            last_success = load_last_success_from_memory(resolved_dsn, timeout=timeout)
        except Exception:  # noqa: BLE001 — last-success is optional
            last_success = {}
    with ProbeContext(
        repo_root=repo_root,
        env=env,
        captured_at=generated_at,
        timeout=timeout,
        http_client=http_client,
        hl_client=hl_client,
        skip_db=skip_db,
        dsn=dsn,
        last_success=last_success,
        max_attempts=max_attempts,
        sleep=sleep,
    ) as ctx:
        sources = probe_all(ctx)
    return render_report(generated_at=generated_at, sources=sources, command=command)
