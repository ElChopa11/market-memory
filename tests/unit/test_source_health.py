"""Source-health report: missing env degrades; forbidden HL types stay blocked; no prints."""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from mm_ingest.hl_info import ALLOWED_INFO_TYPES, FORBIDDEN_INFO_TYPES, HyperliquidInfoClient, HyperliquidInfoError
from mm_lab_cli.cli import main
from mm_source_health.engine import generate_source_health
from mm_source_health.models import SOURCE_INVENTORY
from mm_source_health.probes import HL_GATE_TYPE, HL_PROBE_TYPE, ProbeContext, probe_all, probe_fred, probe_hyperliquid
from mm_source_health.redact import redact_secrets
from mm_source_health.store import write_source_health_report

ROOT = Path(__file__).resolve().parents[2]
AS_OF = datetime(2026, 9, 17, 4, 50, tzinfo=timezone.utc)

STOOQ_CSV = "Symbol,Date,Time,Open,High,Low,Close,Volume\nes.f,2026-09-16,18:00:00,1,1,1,5750.25,1\n"


def _handler(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if request.method == "POST":
        body = json.loads(request.content)
        info_type = str(body.get("type"))
        if info_type in FORBIDDEN_INFO_TYPES:
            return httpx.Response(200, json={"leaked": True})
        if info_type == HL_PROBE_TYPE:
            return httpx.Response(200, json={"universe": [{"name": "BTC"}]})
        if info_type in ALLOWED_INFO_TYPES:
            return httpx.Response(200, json={})
        return httpx.Response(500, json={"error": "unexpected type"})
    if "/api/v3/ping" in url:
        return httpx.Response(200, json={"gecko_says": "(V3) To the Moon!"})
    if "stooq.com" in url:
        return httpx.Response(200, text=STOOQ_CSV)
    if "stlouisfed.org" in url:
        return httpx.Response(
            200,
            json={"observations": [{"date": "2026-09-16", "value": "4.21"}]},
        )
    return httpx.Response(404, text="no")


def _clients() -> tuple[httpx.Client, HyperliquidInfoClient]:
    transport = httpx.MockTransport(_handler)
    http_client = httpx.Client(transport=transport, timeout=2.0)
    hl_client = HyperliquidInfoClient(transport=transport, timeout=2.0)
    return http_client, hl_client


def _empty_env(**overrides: str) -> dict[str, str]:
    env = {
        "MM_OBJECT_STORE": "none",
    }
    env.update(overrides)
    return env


def test_missing_fred_env_is_unavailable_not_crash() -> None:
    http_client, hl_client = _clients()
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env=_empty_env(),
        http_client=http_client,
        hl_client=hl_client,
        skip_db=True,
    )
    fred = report.by_id()["fred"]
    assert fred.status == "unavailable"
    assert fred.error_class == "missing_env"
    assert fred.credentials_present == "no"
    assert any("FRED_API_KEY" in note for note in fred.notes)
    assert any("never commit" in note for note in fred.notes)
    assert "sk-secret" not in report.markdown


def test_missing_object_store_env_is_unavailable_not_crash() -> None:
    http_client, hl_client = _clients()
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env={},  # no MM_OBJECT_STORE / MinIO keys
        http_client=http_client,
        hl_client=hl_client,
        skip_db=True,
    )
    store = report.by_id()["object_store"]
    assert store.status == "unavailable"
    assert store.error_class == "missing_env"
    assert store.credentials_present == "no"
    postgres = report.by_id()["postgres"]
    assert postgres.status == "degraded"  # --no-db skip via skip_db=True
    assert postgres.error_class == "skipped"


def test_missing_postgres_env_is_unavailable_not_crash() -> None:
    http_client, hl_client = _clients()
    ctx = ProbeContext(
        repo_root=ROOT,
        env=_empty_env(),
        captured_at=AS_OF,
        http_client=http_client,
        hl_client=hl_client,
        skip_db=False,
        timeout=2.0,
    )
    rows = {row.source_id: row for row in probe_all(ctx)}
    assert rows["postgres"].status == "unavailable"
    assert rows["postgres"].error_class == "missing_env"
    assert "postgresql://" not in ("; ".join(rows["postgres"].notes))


def test_forbidden_hl_types_still_blocked() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            body = json.loads(request.content)
            seen.append(str(body.get("type")))
        return _handler(request)

    transport = httpx.MockTransport(handler)
    hl_client = HyperliquidInfoClient(transport=transport, timeout=2.0)
    http_client = httpx.Client(transport=transport, timeout=2.0)
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env=_empty_env(),
        http_client=http_client,
        hl_client=hl_client,
        skip_db=True,
    )
    hl = report.by_id()["hyperliquid.info"]
    assert hl.status == "ok"
    assert any("allowlist gate" in note and "refused locally" in note for note in hl.notes)
    assert set(seen) <= set(ALLOWED_INFO_TYPES)
    assert HL_PROBE_TYPE in seen
    assert HL_GATE_TYPE not in seen
    assert "clearinghouseState" not in seen
    assert "userFills" not in seen
    with pytest.raises(HyperliquidInfoError, match="refusing non-public"):
        hl_client.post({"type": "clearinghouseState", "user": "0x" + "0" * 40})


def test_inventory_always_listed_when_sources_down() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            body = json.loads(request.content)
            if body.get("type") in FORBIDDEN_INFO_TYPES:
                return httpx.Response(200, json={})
            return httpx.Response(503, json={"error": "down"})
        return httpx.Response(503, text="down")

    transport = httpx.MockTransport(handler)
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env={},
        http_client=httpx.Client(transport=transport, timeout=2.0),
        hl_client=HyperliquidInfoClient(transport=transport, timeout=2.0),
        skip_db=True,
        sleep=lambda _: None,
    )
    assert report.source_ids() == SOURCE_INVENTORY
    assert report.by_id()["hyperliquid.info"].pulse_role == "required"
    assert report.by_id()["calendar.yaml"].pulse_role == "required"
    assert report.by_id()["hyperliquid.info"].status == "unavailable"
    assert report.by_id()["calendar.yaml"].status == "ok"  # local file
    assert report.overall == "unavailable"
    for source_id in SOURCE_INVENTORY:
        assert source_id in report.markdown


def test_report_does_not_copy_prints_or_secrets() -> None:
    http_client, hl_client = _clients()
    secret = "fred-super-secret-do-not-print"
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env=_empty_env(FRED_API_KEY=secret),
        http_client=http_client,
        hl_client=hl_client,
        skip_db=True,
    )
    text = report.markdown.lower()
    assert secret not in report.markdown
    # Word-boundary: wall-clock generated_at can contain the substring "4.21"
    # (e.g. ...34.218384+00:00) without copying the FRED print.
    assert re.search(r"\b4\.21\b", report.markdown) is None
    assert "5750" not in report.markdown
    assert "to the moon" not in text
    assert "last:" not in text
    assert "yield" in text  # the limitation sentence is allowed
    assert report.by_id()["fred"].status == "ok"
    assert report.by_id()["fred"].credentials_present == "yes"


def test_redact_dsn_password() -> None:
    text = redact_secrets("postgresql://lab:hunter2@localhost:5432/market_memory FRED_API_KEY=abc")
    assert "hunter2" not in text
    assert "abc" not in text
    assert "FRED_API_KEY=***" in text


def test_redact_fred_query_api_key() -> None:
    leaked = "GET https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=super-secret-fred"
    cleaned = redact_secrets(leaked)
    assert "super-secret-fred" not in cleaned
    assert "api_key=***" in cleaned


def _patch_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    http_client, hl_client = _clients()

    def fake_generate(**kwargs):
        return generate_source_health(
            repo_root=kwargs["repo_root"],
            captured_at=kwargs.get("captured_at") or AS_OF,
            env=_empty_env(),
            http_client=http_client,
            hl_client=hl_client,
            skip_db=True,
            command=kwargs.get("command", "lab data source-health"),
            timeout=kwargs.get("timeout", 2.0),
        )

    monkeypatch.setattr("mm_lab_cli.source_health.generate_source_health", fake_generate)


def test_cli_writes_versioned_artifact(tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_generate(monkeypatch)
    rc = main(
        [
            "data",
            "source-health",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--no-db",
            "--as-of",
            "2026-09-17T04:50:00Z",
            "--timeout",
            "2",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "lab data source-health"
    assert payload["path"] == "ops/reports/source-health/2026-09-17.md"
    written = tmp_path / "ops" / "reports" / "source-health" / "2026-09-17.md"
    assert written.is_file()
    text = written.read_text(encoding="utf-8")
    assert "Source health report" in text
    assert "Informational only" in text
    assert payload["content_hash"] == (tmp_path / "ops" / "reports" / "source-health" / "2026-09-17.sha256").read_text().strip()
    for source_id in SOURCE_INVENTORY:
        assert any(row["id"] == source_id for row in payload["sources"])


def test_dq_report_alias(tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_generate(monkeypatch)
    rc = main(
        [
            "dq",
            "report",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--no-db",
            "--as-of",
            "2026-09-17T04:50:00Z",
            "--timeout",
            "2",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "lab dq report"


def test_package_does_not_import_execution_or_signing() -> None:
    root = ROOT / "packages" / "source_health"
    forbidden = ("mm_execution", "hl_trade", "sign_l1_action", "private_key", "submit_order")
    for path in root.rglob("*.py"):
        blob = path.read_text(encoding="utf-8")
        for snippet in forbidden:
            assert snippet not in blob, f"{path}: {snippet}"
        tree = ast.parse(blob)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "mm_execution" not in alias.name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "mm_execution" not in node.module


def test_write_source_health_creates_parent(tmp_path: Path) -> None:
    http_client, hl_client = _clients()
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env=_empty_env(),
        http_client=http_client,
        hl_client=hl_client,
        skip_db=True,
    )
    path = write_source_health_report(report, root=tmp_path)
    assert path.is_file()
    assert "hyperliquid.info" in path.read_text(encoding="utf-8")


def test_allowlist_gate_uses_forbidden_constant() -> None:
    assert HL_GATE_TYPE in FORBIDDEN_INFO_TYPES
    assert HL_PROBE_TYPE in ALLOWED_INFO_TYPES
    ctx = ProbeContext(
        repo_root=ROOT,
        env=_empty_env(),
        captured_at=AS_OF,
        http_client=httpx.Client(transport=httpx.MockTransport(_handler), timeout=2.0),
        hl_client=HyperliquidInfoClient(transport=httpx.MockTransport(_handler), timeout=2.0),
        skip_db=True,
    )
    row = probe_hyperliquid(ctx)
    assert row.status == "ok"
    fred = probe_fred(ctx)
    assert fred.status == "unavailable"
    assert fred.error_class == "missing_env"
    assert any("never commit" in note for note in fred.notes)


def test_stooq_404_classified_not_retried() -> None:
    stooq_calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "stooq.com" in url:
            stooq_calls["n"] += 1
            return httpx.Response(404, text="no")
        return _handler(request)

    transport = httpx.MockTransport(handler)
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env=_empty_env(),
        http_client=httpx.Client(transport=transport, timeout=2.0),
        hl_client=HyperliquidInfoClient(transport=transport, timeout=2.0),
        skip_db=True,
        sleep=lambda _: None,
    )
    stooq = report.by_id()["stooq"]
    assert stooq.status == "unavailable"
    assert stooq.error_class == "http_404"
    assert stooq_calls["n"] == 1
    assert any("http_404" in note for note in stooq.notes)
    assert any("no scrape fallback" in note for note in stooq.notes)
    assert "5750" not in report.markdown


def test_stooq_503_retries_once() -> None:
    stooq_calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "stooq.com" in url:
            stooq_calls["n"] += 1
            return httpx.Response(503, text="down")
        return _handler(request)

    transport = httpx.MockTransport(handler)
    report = generate_source_health(
        repo_root=ROOT,
        captured_at=AS_OF,
        env=_empty_env(),
        http_client=httpx.Client(transport=transport, timeout=2.0),
        hl_client=HyperliquidInfoClient(transport=transport, timeout=2.0),
        skip_db=True,
        sleep=lambda _: None,
    )
    stooq = report.by_id()["stooq"]
    assert stooq.status == "unavailable"
    assert stooq.error_class == "http_5xx"
    assert stooq_calls["n"] == 2
    assert any("attempts=2" in note for note in stooq.notes)
