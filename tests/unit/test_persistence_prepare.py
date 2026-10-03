"""Neon + R2 prepare-only glue. No network. No credentials."""

from __future__ import annotations

from pathlib import Path

import pytest

from mm_lab_cli.cli import main
from mm_memory.db import engine_kwargs_for_dsn, make_engine, normalize_dsn
from mm_memory.migrate import (
    MigrationDsnError,
    alembic_head,
    migration_dsn_problem,
    render_upgrade_sql,
    upgrade_head,
)
from mm_memory.object_store import S3ObjectStore, object_store_from_env, s3_region_from_env
from mm_memory.persistence_env import ACTIONS_SECRET_NAMES, POSTGRES_DSN_ENV

ROOT = Path(__file__).resolve().parents[2]
SQL_PACKET = ROOT / "ops" / "reports" / "persistence" / "2026-09-23-migrate-head.sql"


def test_normalize_dsn_preserves_neon_ssl_query() -> None:
    raw = (
        "postgres://user:p%40ss@ep-plain.us-east-2.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    out = normalize_dsn(raw)
    assert out.startswith("postgresql+psycopg://")
    assert "sslmode=require" in out
    assert "channel_binding=require" in out
    assert "p%40ss" in out


def test_neon_engine_kwargs_disable_prepares_without_connecting() -> None:
    url = normalize_dsn("postgresql://u:p@ep-plain.us-east-2.aws.neon.tech/db?sslmode=require")
    kwargs = engine_kwargs_for_dsn(url)
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["connect_args"] == {"prepare_threshold": None}
    local = engine_kwargs_for_dsn("postgresql+psycopg://lab:lab@localhost:5432/market_memory")
    assert "connect_args" not in local
    assert "pool_pre_ping" not in local
    engine = make_engine("postgresql://u:p@ep-plain.us-east-2.aws.neon.tech/db?sslmode=require")
    try:
        assert engine.pool._pre_ping is True  # type: ignore[attr-defined]
    finally:
        engine.dispose()


def test_migrate_refuses_neon_pooler_without_connecting() -> None:
    dsn = "postgresql://user:secret@ep-example-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
    problem = migration_dsn_problem(dsn)
    assert problem is not None
    assert "pooler" in problem.lower()
    assert "secret" not in problem
    assert "ep-example" not in problem
    with pytest.raises(MigrationDsnError) as excinfo:
        upgrade_head(dsn)
    assert "secret" not in str(excinfo.value)
    assert "ep-example" not in str(excinfo.value)


def test_migrate_refuses_sqlite_before_jsonb_compile() -> None:
    with pytest.raises(MigrationDsnError, match="sqlite"):
        upgrade_head("sqlite:////tmp/market-memory-prepare.db")


def test_render_upgrade_sql_reaches_head_without_dsn() -> None:
    sql = render_upgrade_sql()
    head = alembic_head()
    assert len(head) <= 32
    assert head == "0012_heartbeat_if_not_exists"
    assert "CREATE TABLE" in sql
    assert "JSONB" in sql
    assert "schedule_heartbeat" in sql
    assert "wrong_anchor" in sql
    assert "offline:offline" not in sql
    assert "192.0.2.1" not in sql
    assert "BEGIN;" in sql
    assert sql.strip().endswith("COMMIT;")


def test_committed_sql_packet_matches_renderer() -> None:
    assert SQL_PACKET.is_file()
    assert SQL_PACKET.read_text(encoding="utf-8") == render_upgrade_sql()


def test_lab_migrate_sql_flag_does_not_require_postgres(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["migrate", "--sql"])
    assert code == 0
    out = capsys.readouterr().out
    assert "CREATE TABLE source" in out
    assert "schedule_heartbeat" in out


def test_actions_secret_names_are_the_ones_the_client_reads() -> None:
    assert ACTIONS_SECRET_NAMES[0] == POSTGRES_DSN_ENV == "POSTGRES_DSN"
    assert "MINIO_ENDPOINT" in ACTIONS_SECRET_NAMES
    assert "MINIO_ACCESS_KEY" in ACTIONS_SECRET_NAMES
    assert "MINIO_SECRET_KEY" in ACTIONS_SECRET_NAMES
    assert "MINIO_BUCKET" in ACTIONS_SECRET_NAMES
    assert "S3_REGION" not in ACTIONS_SECRET_NAMES


def test_s3_client_takes_endpoint_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MM_OBJECT_STORE", "s3")
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    monkeypatch.setenv("S3_ENDPOINT", "https://example.r2.cloudflarestorage.com")
    monkeypatch.setenv("S3_BUCKET", "mm-bucket")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_USER", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-access")
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("MINIO_ROOT_PASSWORD", raising=False)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("S3_REGION", "auto")
    captured: dict[str, object] = {}

    def fake_client(service_name: str, **kwargs: object) -> object:
        captured["service"] = service_name
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("boto3.client", fake_client)
    store = object_store_from_env()
    assert isinstance(store, S3ObjectStore)
    assert store.endpoint_url == "https://example.r2.cloudflarestorage.com"
    assert store.region == "auto"
    assert captured["service"] == "s3"
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["endpoint_url"] == "https://example.r2.cloudflarestorage.com"
    assert "minio" not in str(kwargs["endpoint_url"])
    assert kwargs["region_name"] == "auto"
    config = kwargs["config"]
    assert config.s3["addressing_style"] == "path"  # type: ignore[attr-defined]
    assert config.request_checksum_calculation == "when_required"  # type: ignore[attr-defined]
    assert config.response_checksum_validation == "when_required"  # type: ignore[attr-defined]


def test_s3_region_defaults_to_us_east_1_for_local_minio(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("S3_REGION", "MINIO_REGION", "AWS_DEFAULT_REGION"):
        monkeypatch.delenv(name, raising=False)
    assert s3_region_from_env() == "us-east-1"
