"""Read-only Neon + R2 Actions probe: SQL allowlist, SSL policy, no live I/O."""

from __future__ import annotations

import ast
import re
import socket
import ssl
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from psycopg.conninfo import conninfo_to_dict

from probe_neon_r2_connectivity import (
    ALLOWED_SQL,
    SQL_SELECT_IDENTITY,
    SQL_SELECT_ONE,
    SQL_SET_READ_ONLY,
    SQL_SHOW_READ_ONLY,
    main,
    prepare_neon_conninfo,
    probe_neon,
    probe_r2,
    r2_tls_target,
    redact,
    resolve_host,
    tls_handshake,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "probe_neon_r2_connectivity.py"
WORKFLOW = ROOT / ".github" / "workflows" / "probe-neon-r2.yml"
FAKE_PASSWORD = "pw-test-xx"


@pytest.fixture(autouse=True)
def _no_live_store_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests must not inherit a developer or CI DSN and open a database."""
    for key in (
        "POSTGRES_DSN",
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


def test_workflow_is_dispatch_only_and_read_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\nschedule:" not in text
    assert "cron:" not in text
    assert "pull_request:" not in text
    assert "\npush:" not in text
    assert "i_mean_it_probe:" in text
    assert "type: boolean" in text
    assert "default: false" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "persist-credentials: false" in text
    secrets = set(re.findall(r"secrets\.([A-Z0-9_]+)", text))
    assert secrets == {"POSTGRES_DSN", "MINIO_ENDPOINT"}
    jobs = text.split("\njobs:\n", 1)[1]
    assert "S3_REGION" not in jobs
    for banned in (
        "alembic",
        "boto3",
        "migrate",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "PutObject",
        "DeleteObject",
        "ListBuckets",
        "head_bucket",
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "schedule:",
        "cron:",
        "lab ",
        "--no-db",
        "hybrid-sydney-morning",
    ):
        assert banned not in jobs
    assert "uv run --no-project --with 'psycopg[binary]==3.3.5'" in jobs
    assert "python scripts/probe_neon_r2_connectivity.py" in jobs
    assert "PROBE SKIP:" in jobs
    assert "PROBE GATE:" in jobs


def test_executed_sql_is_the_allowlist() -> None:
    assert ALLOWED_SQL == (
        "SET TRANSACTION READ ONLY",
        "SELECT 1",
        "SELECT current_database(), version()",
        "SHOW transaction_read_only",
    )
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    executed: list[str] = []
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute"
        ):
            assert node.args and isinstance(node.args[0], ast.Name)
            executed.append(node.args[0].id)
    assert executed == [
        "SQL_SET_READ_ONLY",
        "SQL_SELECT_ONE",
        "SQL_SELECT_IDENTITY",
        "SQL_SHOW_READ_ONLY",
    ]
    assert imported.isdisjoint(
        {"boto3", "alembic", "sqlalchemy", "mm_execution", "mm_memory", "botocore"}
    )


def test_r2_target_parses_https_and_refuses_plaintext_dev_port() -> None:
    assert r2_tls_target("https://acct.r2.cloudflarestorage.com/bucket") == (
        "acct.r2.cloudflarestorage.com",
        443,
    )
    assert r2_tls_target("acct.r2.cloudflarestorage.com") == (
        "acct.r2.cloudflarestorage.com",
        443,
    )
    assert r2_tls_target("https://acct.r2.cloudflarestorage.com:8443") == (
        "acct.r2.cloudflarestorage.com",
        8443,
    )
    with pytest.raises(ValueError, match="plaintext"):
        r2_tls_target("http://127.0.0.1:9000")
    with pytest.raises(ValueError, match="empty"):
        r2_tls_target("  ")


def test_neon_conninfo_ssl_policy_keeps_password_out_of_the_decision() -> None:
    missing = conninfo_to_dict(
        prepare_neon_conninfo(
            f"postgresql://lab:{FAKE_PASSWORD}@ep.example.neon.tech/market_memory"
        )
    )
    assert missing["sslmode"] == "require"
    assert missing["password"] == FAKE_PASSWORD
    assert missing["application_name"] == "mm-probe-neon-r2"
    preferred = conninfo_to_dict(
        prepare_neon_conninfo(
            "postgresql://lab:pw-test-xx@ep.example.neon.tech/market_memory?sslmode=prefer"
        )
    )
    assert preferred["sslmode"] == "require"
    verified = conninfo_to_dict(
        prepare_neon_conninfo(
            "host=ep.example.neon.tech dbname=market_memory user=lab "
            "password=pw-test-xx sslmode=verify-full"
        )
    )
    assert verified["sslmode"] == "verify-full"
    with pytest.raises(ValueError, match="sslmode=disable"):
        prepare_neon_conninfo(
            "postgresql://lab:pw-test-xx@ep.example.neon.tech/market_memory?sslmode=disable"
        )
    with pytest.raises(ValueError, match="sslmode=allow"):
        prepare_neon_conninfo(
            "postgresql://lab:pw-test-xx@ep.example.neon.tech/market_memory?sslmode=allow"
        )


def test_redact_strips_url_userinfo_and_keyword_password() -> None:
    raw = "failed postgresql://lab:pw-test-xx@ep.example/db password=pw-test-xx"
    cleaned = redact(raw)
    assert "pw-test-xx" not in cleaned
    assert "://***:***@" in cleaned
    assert "password=***" in cleaned


def test_r2_dns_failure_does_not_open_tls(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def _fail(host: str, port: int) -> list[str]:
        raise OSError("name or service not known")

    monkeypatch.setattr("probe_neon_r2_connectivity.resolve_host", _fail)
    monkeypatch.setattr(
        "probe_neon_r2_connectivity.tls_handshake",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("tls attempted")),
    )
    assert probe_r2("https://key:secret-value@acct.r2.cloudflarestorage.com") is False
    out = capsys.readouterr().out
    assert "R2 DNS FAIL: host=acct.r2.cloudflarestorage.com port=443" in out
    assert "R2 TLS FAIL: not attempted" in out
    assert "secret-value" not in out


def test_r2_success_logs_host_not_userinfo(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "probe_neon_r2_connectivity.resolve_host",
        lambda host, port: ["203.0.113.10"],
    )
    monkeypatch.setattr(
        "probe_neon_r2_connectivity.tls_handshake",
        lambda host, port, **kwargs: "TLSv1.3",
    )
    assert probe_r2("https://key:secret-value@acct.r2.cloudflarestorage.com") is True
    out = capsys.readouterr().out
    assert "R2 DNS PASS: host=acct.r2.cloudflarestorage.com port=443 addresses=1" in out
    assert "R2 TLS PASS: host=acct.r2.cloudflarestorage.com port=443 protocol=TLSv1.3" in out
    assert "secret-value" not in out


class _Cursor:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self._row = row

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row


class _Txn:
    def __init__(self, conn: "_FakeConn") -> None:
        self._conn = conn

    def __enter__(self) -> "_Txn":
        self._conn.events.append("BEGIN")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._conn.events.append("ROLLBACK")
        return False


class _FakeConn:
    def __init__(self, *, ssl_on: bool, rows: dict[str, tuple[object, ...] | None]) -> None:
        self.pgconn = SimpleNamespace(ssl_in_use=ssl_on)
        self.info = SimpleNamespace(host="ep.example.neon.tech")
        self.rows = rows
        self.statements: list[str] = []
        self.events: list[str] = []
        self.force_rollback = False

    def __enter__(self) -> "_FakeConn":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.events.append("CLOSE")
        return False

    def execute(self, sql: str) -> _Cursor:
        self.statements.append(sql)
        return _Cursor(self.rows.get(sql))

    def transaction(self, force_rollback: bool = False) -> _Txn:
        self.force_rollback = force_rollback
        return _Txn(self)


def _install_fake_psycopg(monkeypatch: pytest.MonkeyPatch, conn: _FakeConn) -> dict[str, object]:
    seen: dict[str, object] = {}

    def connect(conninfo: str, connect_timeout: int, prepare_threshold: object) -> _FakeConn:
        seen["conninfo"] = conninfo
        seen["connect_timeout"] = connect_timeout
        seen["prepare_threshold"] = prepare_threshold
        return conn

    import psycopg

    monkeypatch.setattr(psycopg, "connect", connect)
    return seen


def test_neon_happy_path_is_ssl_read_only_and_rolled_back(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    conn = _FakeConn(
        ssl_on=True,
        rows={
            SQL_SELECT_ONE: (1,),
            SQL_SELECT_IDENTITY: ("market_memory", "PostgreSQL 16.9 on x86_64, compiled by gcc"),
            SQL_SHOW_READ_ONLY: ("on",),
        },
    )
    seen = _install_fake_psycopg(monkeypatch, conn)
    dsn = f"postgresql://lab:{FAKE_PASSWORD}@ep.example.neon.tech/market_memory"
    assert probe_neon(dsn) is True
    assert conn.statements == [
        SQL_SET_READ_ONLY,
        SQL_SELECT_ONE,
        SQL_SELECT_IDENTITY,
        SQL_SHOW_READ_ONLY,
    ]
    assert conn.force_rollback is True
    assert conn.events == ["BEGIN", "ROLLBACK", "CLOSE"]
    info = conninfo_to_dict(str(seen["conninfo"]))
    assert info["sslmode"] == "require"
    assert info["password"] == FAKE_PASSWORD
    assert seen["prepare_threshold"] is None
    out = capsys.readouterr().out
    assert "NEON PASS: sslmode=require ssl=on read_only=on rollback=force" in out
    assert "host=ep.example.neon.tech database=market_memory select1=1" in out
    assert "server=PostgreSQL 16.9 on x86_64" in out
    assert FAKE_PASSWORD not in out


def test_neon_without_ssl_runs_no_sql(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    conn = _FakeConn(ssl_on=False, rows={})
    _install_fake_psycopg(monkeypatch, conn)
    assert probe_neon("postgresql://lab:pw-test-xx@ep.example.neon.tech/market_memory") is False
    assert conn.statements == []
    assert conn.events == ["CLOSE"]
    assert "NEON FAIL: TCP session is up but SSL is not in use" in capsys.readouterr().out


def test_neon_connect_error_redacts_password(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import psycopg

    def connect(conninfo: str, **kwargs: object) -> object:
        raise RuntimeError(f"connection to server failed using {conninfo}")

    monkeypatch.setattr(psycopg, "connect", connect)
    assert probe_neon(f"postgresql://lab:{FAKE_PASSWORD}@ep.example.neon.tech/market_memory") is False
    out = capsys.readouterr().out
    assert "NEON FAIL: RuntimeError:" in out
    assert FAKE_PASSWORD not in out
    assert "password=***" in out or "<redacted>" in out


def test_neon_disable_does_not_connect(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import psycopg

    def connect(*args, **kwargs):
        raise AssertionError("connect must not run when sslmode is refused")

    monkeypatch.setattr(psycopg, "connect", connect)
    assert (
        probe_neon(
            "postgresql://lab:pw-test-xx@ep.example.neon.tech/market_memory?sslmode=disable"
        )
        is False
    )
    out = capsys.readouterr().out
    assert "NEON FAIL:" in out
    assert "sslmode=disable" in out
    assert "pw-test-xx" not in out


def test_main_pass_and_fail(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "https://acct.r2.cloudflarestorage.com")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://lab:pw-test-xx@ep.example/db")
    monkeypatch.setattr("probe_neon_r2_connectivity.probe_r2", lambda endpoint: True)
    monkeypatch.setattr("probe_neon_r2_connectivity.probe_neon", lambda dsn: True)
    assert main() == 0
    assert capsys.readouterr().out.strip() == "PROBE PASS: neon and r2"

    monkeypatch.setattr("probe_neon_r2_connectivity.probe_r2", lambda endpoint: False)
    monkeypatch.setattr("probe_neon_r2_connectivity.probe_neon", lambda dsn: True)
    assert main() == 1
    assert capsys.readouterr().out.strip() == "PROBE FAIL: r2"


def test_resolve_host_localhost() -> None:
    addresses = resolve_host("localhost", 443)
    assert addresses


def test_tls_handshake_verifies_local_certificate(tmp_path: Path) -> None:
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-days",
            "1",
            "-nodes",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
        ],
        check=True,
        capture_output=True,
    )
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
    bound = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bound.bind(("127.0.0.1", 0))
    bound.listen(1)
    bound.settimeout(5)
    port = bound.getsockname()[1]
    errors: list[BaseException] = []

    def serve() -> None:
        try:
            client, _addr = bound.accept()
            try:
                with server_ctx.wrap_socket(client, server_side=True):
                    pass
            finally:
                client.close()
        except BaseException as exc:  # noqa: BLE001 — surface server-side handshake errors
            errors.append(exc)
        finally:
            bound.close()

    thread = threading.Thread(target=serve)
    thread.start()
    client_ctx = ssl.create_default_context(cafile=str(cert))
    try:
        protocol = tls_handshake("localhost", port, timeout=5, ssl_context=client_ctx)
    finally:
        thread.join(timeout=5)
    assert not errors
    assert protocol.startswith("TLS")
