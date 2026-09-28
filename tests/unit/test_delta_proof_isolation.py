"""delta_proof isolation. Branch-only proof. Explicit assertions.

The job entry point is ``python -m mm_briefing.delta_proof``. Forbidden writers
raise if called. Market HTTP is a saved Polygon, FRED, and metaAndAssetCtxs
fixture. The BTC line is a read-only observation query, or ``n/a``.
"""

from __future__ import annotations

import collections.abc
import copy
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import yaml

from mm_briefing import delta_proof, render_proof

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "briefing"
JOBS_SNAPSHOT = ROOT / "tests" / "fixtures" / "scheduler" / "hybrid_sydney_morning_d6d35f6_jobs.json"
MAIN_COMMIT = "d6d35f64003f274f51c386f805f981be85b34a10"
AS_OF = datetime(2026, 9, 25, 8, 30, tzinfo=timezone.utc)
SYDNEY = ZoneInfo("Australia/Sydney")
DELTA_FRAGMENT = " && inputs.mode != 'delta_proof'"
CONCURRENCY_GROUP = (
    "${{ (github.event_name == 'workflow_dispatch' && inputs.mode == 'delta_proof') "
    "&& 'delta-proof-never-merge' || 'hybrid-sydney-morning' }}"
)
PRIOR_AT = "2026-09-27T20:30:00+00:00"
LATEST_AT = "2026-09-28T20:30:00+00:00"
POSITIVE_LINE = "BTC vs prior capture: +1.29% since Mon 06:30 capture"
WRITE_VERBS = ("INSERT", "UPDATE", "DELETE", "MERGE", "ALTER", "CREATE", "DROP", "TRUNCATE", "COPY")
FROZEN_BLOBS = {
    "packages/briefing/src/mm_briefing/morning.py": "93415bf9edec5a111a04684ef7df8ce8828fedec",
    "apps/lab-cli/src/mm_lab_cli/deliver.py": "e984a81c8b36e45ecfe7b13bf3632c0a5f4ae946",
    "packages/delivery/src/mm_delivery/deliver.py": "5a2b09cfabfc809a5295da22967148b03c12f8e9",
    "apps/lab-cli/src/mm_lab_cli/deadman.py": "93be1dbb1ec95b2bdc4b5cc41f05d297545305d5",
    "packages/desks/src/mm_desks/deliver_receipt.py": "b2ab1be89ddb4ea367231208fc318a7af1f0145d",
    "packages/ingest/src/mm_ingest/mvp_retain.py": "f2b8ec3aefe20187814a156db57102ff0bee6644",
    "apps/lab-cli/src/mm_lab_cli/completion.py": "9f57c61c13c61c87617e8c0c16a8a877938d31a9",
    "packages/desks/src/mm_desks/scheduler.py": "7d2964b9ed173c9f2bcbda8f07426474ca11caa0",
    "packages/briefing/src/mm_briefing/render.py": "645eb21ac241405095f557b819e16466474fbcd2",
    "packages/briefing/src/mm_briefing/engine.py": "6de3d86ef6315029cf17017c2b58acc2c72810ab",
}
SENTINELS = {
    "TELEGRAM_BOT_TOKEN": "sentinel-telegram-bot-token-not-a-secret",
    "TELEGRAM_CHAT_ID": "sentinel-telegram-group-not-a-secret",
    "TELEGRAM_CHAT_ID_PRINCIPAL_DM": "sentinel-telegram-dm-not-a-secret",
    "HEALTHCHECKS_PING_URL": "sentinel-healthchecks-ping-not-a-secret",
}
LEAK_DSN = "postgresql://secretuser:secretpass@db.example.internal:5432/market"
_REAL_HTTPX_CLIENT = httpx.Client


def _workflow():
    text = WORKFLOW.read_text(encoding="utf-8")
    parsed = yaml.safe_load(text)
    return text, parsed


def _on_block(parsed):
    return parsed[True] if True in parsed else parsed["on"]


def _delta_job_text(text: str) -> str:
    start = text.index("\n  delta-proof:\n")
    end = text.index("\n  capture-proof:\n")
    return text[start:end]


def _json_line(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise AssertionError(f"no JSON result in stdout: {stdout!r}")


def _install_fixture_http(monkeypatch) -> None:
    polygon = json.loads((FIXTURE_DIR / "morning_polygon_aggs.json").read_text(encoding="utf-8"))
    fred = json.loads((FIXTURE_DIR / "morning_fred_rolled.json").read_text(encoding="utf-8"))
    hl_body = json.loads((FIXTURE_DIR / "morning_hl_meta_and_asset_ctxs.json").read_text(encoding="utf-8"))
    original = _REAL_HTTPX_CLIENT

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host or ""
        if host == "api.telegram.org" or "hc-ping" in host or "healthchecks" in host:
            raise AssertionError(f"delta_proof must not call {host}")
        if host == "api.polygon.io":
            for ticker, body in polygon.items():
                if f"/ticker/{ticker}/" in request.url.path:
                    return httpx.Response(200, json=body)
            return httpx.Response(404, json={"status": "NOT_FOUND"})
        if host == "api.stlouisfed.org":
            return httpx.Response(200, json=fred)
        if host == "api.hyperliquid.xyz":
            payload = json.loads(request.content or b"{}")
            if str(payload.get("type")) == "metaAndAssetCtxs":
                return httpx.Response(200, json=hl_body)
            return httpx.Response(400, json={"error": "fixture transport refuses this info type"})
        if host == "api.coingecko.com":
            return httpx.Response(200, json={"bitcoin": {"usd": 100000}})
        return httpx.Response(404, json={"error": "fixture transport refuses this host"})

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", factory)


def _prepare(monkeypatch, tmp_path: Path) -> Path:
    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(delta_proof, "utc_now", lambda: AS_OF)
    monkeypatch.setattr(render_proof, "utcnow", lambda: AS_OF)
    monkeypatch.setattr("mm_briefing.fetchers.time.sleep", lambda *_args, **_kwargs: None)
    _install_fixture_http(monkeypatch)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    return summary


def _forbid(called: list[str], name: str):
    def _inner(*_args, **_kwargs):
        called.append(name)
        raise AssertionError(f"{name} must not run on delta_proof")

    return _inner


def _install_forbidden(monkeypatch, called: list[str]) -> None:
    targets = (
        "mm_ingest.pipeline.persist_envelopes",
        "mm_ingest.mvp_retain.persist_mvp_retain",
        "mm_ingest.mvp_retain.run_morning_capture",
        "mm_ingest.mvp_retain.run_proof_capture",
        "mm_desks.deliver_receipt.write_deliver_receipt",
        "mm_lab_cli.completion.stamp_cli_fire",
        "mm_lab_cli.briefing.stamp_cli_fire",
        "mm_lab_cli.deliver.stamp_cli_fire",
        "mm_desks.completions.record_cli_completion",
        "mm_desks.completions.write_completion",
        "mm_lab_cli.deadman.ping_deadman_start",
        "mm_lab_cli.deadman.ping_deadman_success",
        "mm_lab_cli.deliver.ping_deadman_start",
        "mm_lab_cli.deliver.ping_deadman_success",
    )
    for target in targets:
        monkeypatch.setattr(target, _forbid(called, target))
    import importlib

    deliver_mod = importlib.import_module("mm_delivery.deliver")
    monkeypatch.setattr(deliver_mod, "deliver", _forbid(called, "mm_delivery.deliver.deliver"))
    monkeypatch.setattr(
        "mm_ingest.mvp_retain.NeonRetainStore",
        _forbid(called, "mm_ingest.mvp_retain.NeonRetainStore"),
    )
    monkeypatch.setattr(
        "mm_delivery.telegram.TelegramClient.send_message",
        _forbid(called, "mm_delivery.telegram.TelegramClient.send_message"),
    )
    real_run = subprocess.run

    def _run(args, **kwargs):
        parts = args if isinstance(args, (list, tuple)) else [args]
        flat = " ".join(str(part) for part in parts).lower()
        if "git" in flat and ("commit" in flat or "push" in flat):
            called.append("subprocess.run")
            raise AssertionError("git commit or push must not run on delta_proof")
        if "api.telegram.org" in flat or "hc-ping" in flat or "healthchecks" in flat:
            called.append("subprocess.run")
            raise AssertionError("telegram or healthchecks subprocess must not run on delta_proof")
        return real_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", _run)


class _EnvironSpy(collections.abc.MutableMapping):
    def __init__(self, real) -> None:
        self._real = real
        self.reads: list[str] = []

    def __getitem__(self, key):
        self.reads.append(str(key))
        return self._real[key]

    def __setitem__(self, key, value) -> None:
        self._real[key] = value

    def __delitem__(self, key) -> None:
        del self._real[key]

    def __iter__(self):
        raise AssertionError("delta_proof must not iterate the environment")

    def __len__(self) -> int:
        return len(self._real)

    def get(self, key, default=None):
        self.reads.append(str(key))
        return self._real.get(key, default)

    def __contains__(self, key) -> bool:
        self.reads.append(str(key))
        return key in self._real


class _RaisingEnviron(collections.abc.MutableMapping):
    def __getitem__(self, key):
        raise AssertionError(f"env read {key}")

    def __setitem__(self, key, value) -> None:
        raise AssertionError(f"env write {key}")

    def __delitem__(self, key) -> None:
        raise AssertionError(f"env del {key}")

    def __iter__(self):
        raise AssertionError("env iter")

    def __len__(self) -> int:
        raise AssertionError("env len")

    def get(self, key, default=None):
        raise AssertionError(f"env read {key}")

    def __contains__(self, key) -> bool:
        raise AssertionError(f"env contains {key}")


class _Mappings:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def mappings(self):
        return self._rows


class _RecordingConn:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.statements: list[str] = []
        self.closed = False

    def execute(self, statement, params=None):
        sql = getattr(statement, "text", None) or str(statement)
        self.statements.append(sql)
        if sql.lstrip().upper().startswith("SELECT"):
            return _Mappings(self.rows)
        return _Mappings([])

    def rollback(self) -> None:
        self.statements.append("ROLLBACK")

    def close(self) -> None:
        self.closed = True


def _captures(*pairs: tuple[str | None, str | None]) -> list[delta_proof.BtcCapture]:
    return [delta_proof.BtcCapture(value=value, captured_at=captured_at) for value, captured_at in pairs]


def _apply_delta_sql(sql: str, table: list[dict]) -> list[dict]:
    """Mirror the morning-capture WHERE clause that the SQL text actually declares."""
    rows = [row for row in table if row.get("instrument") == "BTC" and row.get("metric") == "mid_px"]
    if "retain_series" in sql and "mvp_retain" in sql:
        rows = [row for row in rows if row.get("retain_series") == "mvp_retain"]
    if "NOT IN ('proof', 'render')" in sql:
        rows = [row for row in rows if (row.get("capture_kind") or "") not in {"proof", "render"}]
    rows = [row for row in rows if row.get("captured_at")]
    rows.sort(key=lambda row: str(row["captured_at"]), reverse=True)
    if "LIMIT 2" in sql:
        rows = rows[:2]
    return rows


def _substitute(expr: str, *, event: str, mode: str | None, deliver: bool) -> str:
    mode_token = "null" if mode is None else "'" + mode + "'"
    deliver_bool = "true" if deliver else "false"
    deliver_text = "'true'" if deliver else "'false'"
    out = expr
    out = out.replace("github.event.inputs.i_mean_it_deliver", deliver_text)
    out = out.replace("github.event_name", "'" + event + "'")
    out = out.replace("inputs.i_mean_it_deliver", deliver_bool)
    out = out.replace("inputs.mode", mode_token)
    return out


class _Expr:
    """GitHub Actions ``&&`` / ``||`` return operands. ``&&`` binds tighter than ``||``."""

    def __init__(self, source: str) -> None:
        self.s = source
        self.i = 0

    def parse(self):
        value = self._or()
        self._skip()
        if self.i != len(self.s):
            raise AssertionError(f"unparsed {self.s[self.i:]!r}")
        return value

    def _skip(self) -> None:
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def _starts(self, token: str) -> bool:
        return self.s.startswith(token, self.i)

    def _or(self):
        left = self._and()
        while True:
            self._skip()
            if self._starts("||"):
                self.i += 2
                right = self._and()
                left = left if left else right
                continue
            return left

    def _and(self):
        left = self._cmp()
        while True:
            self._skip()
            if self._starts("&&"):
                self.i += 2
                right = self._cmp()
                left = right if left else left
                continue
            return left

    def _cmp(self):
        self._skip()
        if self._starts("("):
            self.i += 1
            value = self._or()
            self._skip()
            if not self._starts(")"):
                raise AssertionError("missing )")
            self.i += 1
            return value
        left = self._atom()
        self._skip()
        if self._starts("=="):
            self.i += 2
            return left == self._atom()
        if self._starts("!="):
            self.i += 2
            return left != self._atom()
        return left

    def _atom(self):
        self._skip()
        if self._starts("("):
            return self._cmp()
        if self._starts("'"):
            self.i += 1
            end = self.s.index("'", self.i)
            value = self.s[self.i:end]
            self.i = end + 1
            return value
        for word, value in (("true", True), ("false", False), ("null", None)):
            if self._starts(word):
                nxt = self.s[self.i + len(word) : self.i + len(word) + 1]
                if nxt == "" or not nxt.isalnum():
                    self.i += len(word)
                    return value
        raise AssertionError(f"bad atom at {self.s[self.i:]!r}")


def _eval_expr(expr: str, *, event: str, mode: str | None, deliver: bool = False):
    return _Expr(_substitute(expr, event=event, mode=mode, deliver=deliver)).parse()


def _without_delta_gate(job: dict) -> dict:
    cloned = copy.deepcopy(job)
    expr = cloned["if"]
    assert isinstance(expr, str)
    assert expr.count(DELTA_FRAGMENT) == 1
    cloned["if"] = expr.replace(DELTA_FRAGMENT, "", 1)
    return cloned


def _receipt_paths() -> list[Path]:
    found: list[Path] = []
    receipts = ROOT / "ops" / "reports" / "scheduler" / "completions" / "receipts"
    if receipts.is_dir():
        found.extend(receipts.rglob("*"))
    raw = os.environ.get("MM_SCHEDULE_COMPLETIONS_DIR")
    if raw:
        found.extend(Path(raw).rglob("*"))
    return found


def test_delta_read_failure_does_not_change_receipt(monkeypatch, capsys, tmp_path) -> None:
    calls: list[str] = []

    def _write(*_args, **_kwargs):
        calls.append("write_deliver_receipt")
        raise AssertionError("write_deliver_receipt")

    monkeypatch.setattr("mm_desks.deliver_receipt.write_deliver_receipt", _write)
    before = _receipt_paths()
    summary = _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")

    def _ok(_dsn: str):
        return _captures(("10129", LATEST_AT), ("10000", PRIOR_AT))

    def _bad(_dsn: str):
        raise RuntimeError("read failed")

    monkeypatch.setattr(delta_proof, "query_btc_captures", _ok)
    assert delta_proof.main() == 0
    capsys.readouterr()
    monkeypatch.setattr(delta_proof, "query_btc_captures", _bad)
    assert delta_proof.main() == 0
    failed = capsys.readouterr().out
    assert calls == []
    assert _receipt_paths() == before
    assert "BTC vs prior capture: n/a" in failed
    assert "BTC vs prior capture: n/a" in summary.read_text(encoding="utf-8")
    text, _parsed = _workflow()
    marker = '"""Write a deliver receipt only when exit 0 and sent is true."""'
    start = text.index(marker)
    script = text[start : text.index("\n          PY\n", start)]
    assert "DELTA_" not in script
    assert "os.environ" not in script or "DELTA_" not in script
    job = _delta_job_text(text)
    assert "write_deliver_receipt" not in job
    assert "receipts/" not in job


def test_delta_path_never_writes(monkeypatch, capsys, tmp_path) -> None:
    called: list[str] = []
    _prepare(monkeypatch, tmp_path)
    _install_forbidden(monkeypatch, called)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")
    monkeypatch.setattr(
        delta_proof,
        "query_btc_captures",
        lambda _dsn: _captures(("10129", LATEST_AT), ("10000", PRIOR_AT)),
    )
    assert delta_proof.main() == 0
    capsys.readouterr()

    def _bad(_dsn: str):
        raise RuntimeError("read failed")

    monkeypatch.setattr(delta_proof, "query_btc_captures", _bad)
    assert delta_proof.main() == 0
    assert called == []


def test_delta_absent_on_capture_1(monkeypatch, capsys, tmp_path) -> None:
    _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")
    monkeypatch.setattr(
        delta_proof,
        "query_btc_captures",
        lambda _dsn: _captures(("10129", LATEST_AT)),
    )
    assert delta_proof.main() == 0
    out = capsys.readouterr().out
    assert "BTC vs prior capture: n/a" in out
    assert _json_line(out)["delta_state"] == "first"


def test_message_identical_except_delta_line(monkeypatch, capsys, tmp_path) -> None:
    _prepare(monkeypatch, tmp_path)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    plain, _sources = render_proof.build_close_proof()
    assert delta_proof.main() == 0
    body_lines = capsys.readouterr().out.splitlines()
    assert body_lines[-1].startswith("{")
    rendered = body_lines[:-1]
    assert rendered[-1].startswith("BTC vs prior capture: ")
    assert rendered[:-1] == plain.splitlines()
    assert len(rendered) == len(plain.splitlines()) + 1


def test_delta_line_format_btc_vs_prior(monkeypatch, capsys, tmp_path) -> None:
    state, label = delta_proof.describe_delta(_captures(("10129", LATEST_AT), ("10000", PRIOR_AT)))
    assert state == "ok"
    assert f"BTC vs prior capture: {label}" == POSITIVE_LINE
    neg_state, neg_label = delta_proof.describe_delta(_captures(("9800", LATEST_AT), ("10000", PRIOR_AT)))
    assert neg_state == "ok"
    assert neg_label == "-2.00% since Mon 06:30 capture"
    _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")
    monkeypatch.setattr(
        delta_proof,
        "query_btc_captures",
        lambda _dsn: _captures(("10129", LATEST_AT), ("10000", PRIOR_AT)),
    )
    assert delta_proof.main() == 0
    out = capsys.readouterr().out
    assert POSITIVE_LINE in out.splitlines()
    payload = _json_line(out)
    assert payload["delta_state"] == "ok"
    assert payload["ok"] is True
    assert payload["sent"] is False
    assert payload["wrote"] is False
    assert payload["pinged"] is False


def test_delta_ignores_proof_rows(monkeypatch, capsys, tmp_path) -> None:
    table = [
        {
            "instrument": "BTC",
            "metric": "mid_px",
            "retain_series": "mvp_retain",
            "capture_kind": "proof",
            "value": "1",
            "captured_at": "2026-09-29T20:30:00+00:00",
        },
        {
            "instrument": "BTC",
            "metric": "mid_px",
            "retain_series": "mvp_retain",
            "capture_kind": "render",
            "value": "2",
            "captured_at": "2026-09-29T18:00:00+00:00",
        },
        {
            "instrument": "BTC",
            "metric": "mid_px",
            "retain_series": "other",
            "capture_kind": "lab_snapshot",
            "value": "99999",
            "captured_at": "2026-09-29T21:00:00+00:00",
        },
        {
            "instrument": "BTC",
            "metric": "mid_px",
            "retain_series": "mvp_retain",
            "capture_kind": "lab_snapshot",
            "value": "10129",
            "captured_at": LATEST_AT,
        },
        {
            "instrument": "BTC",
            "metric": "mid_px",
            "retain_series": "mvp_retain",
            "capture_kind": "lab_snapshot",
            "value": "10000",
            "captured_at": PRIOR_AT,
        },
    ]
    sql = delta_proof.BTC_DELTA_SQL
    assert "NOT IN ('proof', 'render')" in sql
    picked = _apply_delta_sql(sql, table)
    assert [row["value"] for row in picked] == ["10129", "10000"]
    _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")

    def _query(_dsn: str):
        rows = _apply_delta_sql(delta_proof.BTC_DELTA_SQL, table)
        return _captures(*[(row["value"], row["captured_at"]) for row in rows])

    monkeypatch.setattr(delta_proof, "query_btc_captures", _query)
    assert delta_proof.main() == 0
    assert POSITIVE_LINE in capsys.readouterr().out.splitlines()


def test_delta_null_value_renders_na(monkeypatch, capsys, tmp_path) -> None:
    _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")
    monkeypatch.setattr(
        delta_proof,
        "query_btc_captures",
        lambda _dsn: _captures((None, LATEST_AT), ("10000", PRIOR_AT)),
    )
    assert delta_proof.main() == 0
    out = capsys.readouterr().out
    assert "BTC vs prior capture: n/a" in out.splitlines()
    assert _json_line(out)["delta_state"] == "na"


def test_delta_timeout_renders_na_within_cap(monkeypatch, capsys, tmp_path) -> None:
    real_sleep = time.sleep
    _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://fixture-user:fixture-pass@fixture-host.example/db")
    monkeypatch.setattr(delta_proof, "build_close_proof", lambda: ("Close.\n", ()))

    def _slow(_dsn: str):
        real_sleep(30)
        raise AssertionError("slow read returned")

    monkeypatch.setattr(delta_proof, "query_btc_captures", _slow)
    started = time.perf_counter()
    rc = delta_proof.main()
    elapsed = time.perf_counter() - started
    out = capsys.readouterr().out
    assert rc == 0
    assert delta_proof.QUERY_WALL_S - 0.2 <= elapsed <= delta_proof.QUERY_WALL_S + 0.5
    assert "BTC vs prior capture: n/a" in out.splitlines()
    assert _json_line(out)["delta_state"] == "na"


def test_delta_missing_dsn_renders_na(monkeypatch, capsys, tmp_path) -> None:
    _prepare(monkeypatch, tmp_path)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    calls: list[str] = []

    def _query(_dsn: str):
        calls.append("query")
        raise AssertionError("query without DSN")

    monkeypatch.setattr(delta_proof, "query_btc_captures", _query)
    monkeypatch.setattr(
        "sqlalchemy.create_engine",
        lambda *_args, **_kwargs: calls.append("engine") or (_ for _ in ()).throw(AssertionError("engine")),
    )
    assert delta_proof.main() == 0
    out = capsys.readouterr().out
    assert calls == []
    assert "BTC vs prior capture: n/a" in out.splitlines()
    assert _json_line(out)["delta_state"] == "na"
    assert _json_line(out)["ok"] is True


def test_delta_line_never_contains_dsn_or_host(monkeypatch, capsys, tmp_path) -> None:
    summary = _prepare(monkeypatch, tmp_path)
    monkeypatch.setenv("POSTGRES_DSN", LEAK_DSN)

    def _boom(dsn: str):
        raise RuntimeError(f"could not connect to {dsn}")

    monkeypatch.setattr(delta_proof, "query_btc_captures", _boom)
    assert delta_proof.main() == 0
    blob = capsys.readouterr().out + summary.read_text(encoding="utf-8")
    for needle in (LEAK_DSN, "secretuser", "secretpass", "db.example.internal"):
        assert needle not in blob
    assert "BTC vs prior capture: n/a" in blob.splitlines()


def test_delta_sql_is_select_only_and_session_read_only(monkeypatch) -> None:
    sql = delta_proof.BTC_DELTA_SQL
    assert re.search(r"\bSELECT\b", sql)
    for verb in WRITE_VERBS:
        assert re.search(rf"\b{verb}\b", sql) is None
    assert "payload_json->>'value'" in sql
    assert "instrument = 'BTC'" in sql
    assert "metric = 'mid_px'" in sql
    assert "LIMIT 2" in sql
    conn = _RecordingConn(
        [
            {"value": "10129", "captured_at": LATEST_AT},
            {"value": "10000", "captured_at": PRIOR_AT},
        ]
    )
    created: dict = {}

    def _engine(url, **kwargs):
        created["url"] = url
        created["kwargs"] = kwargs

        class _Engine:
            def connect(self):
                return conn

            def dispose(self) -> None:
                created["disposed"] = True

        return _Engine()

    monkeypatch.setattr("sqlalchemy.create_engine", _engine)
    rows = delta_proof.query_btc_captures("postgresql://fixture-user:fixture-pass@fixture-host.example/db")
    assert [(row.value, row.captured_at) for row in rows] == [("10129", LATEST_AT), ("10000", PRIOR_AT)]
    assert created["kwargs"]["connect_args"]["connect_timeout"] == 5
    assert created["kwargs"]["echo"] is False
    assert created.get("disposed") is True
    assert conn.closed is True
    statements = conn.statements
    read_only = next(i for i, item in enumerate(statements) if "READ ONLY" in item.upper())
    select = next(i for i, item in enumerate(statements) if item.lstrip().upper().startswith("SELECT"))
    rollback = next(i for i, item in enumerate(statements) if item == "ROLLBACK")
    assert read_only < select < rollback
    assert "SET TRANSACTION READ ONLY" in statements
    assert f"SET statement_timeout = {delta_proof.STATEMENT_TIMEOUT_MS}" in statements
    assert statements[select] == sql
    for item in statements:
        if item in {"ROLLBACK"} or item.upper().startswith("SET "):
            continue
        for verb in WRITE_VERBS:
            assert re.search(rf"\b{verb}\b", item) is None
    assert LEAK_DSN not in " ".join(statements)
    assert "fixture-host.example" not in " ".join(statements)


def test_frozen_files_byte_identical_to_main() -> None:
    """Blob SHAs recorded from d6d35f6, which matches origin/main for these paths."""
    for rel, recorded in FROZEN_BLOBS.items():
        digest = subprocess.check_output(["git", "hash-object", rel], cwd=ROOT, text=True).strip()
        assert digest == recorded, rel
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/main:{rel}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            assert probe.stdout.strip() == recorded, rel
        pinned = subprocess.run(
            ["git", "rev-parse", "--verify", f"{MAIN_COMMIT}:{rel}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if pinned.returncode == 0:
            assert pinned.stdout.strip() == recorded, rel


def test_delta_proof_refuses_send_ping_write(monkeypatch, capsys, tmp_path) -> None:
    called: list[str] = []
    summary = _prepare(monkeypatch, tmp_path)
    _install_forbidden(monkeypatch, called)
    for key, value in SENTINELS.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    spy = _EnvironSpy(os.environ)
    monkeypatch.setattr(os, "environ", spy)
    assert delta_proof.main() == 0
    out = capsys.readouterr().out + summary.read_text(encoding="utf-8")
    assert called == []
    for key in SENTINELS:
        assert key not in spy.reads
    for value in SENTINELS.values():
        assert value not in out
    _text, parsed = _workflow()
    env = parsed["jobs"]["delta-proof"]["env"]
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "TELEGRAM_CHAT_ID_PRINCIPAL_DM" not in env
    assert "HEALTHCHECKS_PING_URL" not in env


def test_delta_proof_date_gate(monkeypatch, capsys, tmp_path) -> None:
    _prepare(monkeypatch, tmp_path)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    allowed = datetime(2026, 10, 2, 23, 59, tzinfo=SYDNEY)
    monkeypatch.setattr(delta_proof, "utc_now", lambda: allowed.astimezone(timezone.utc))
    assert delta_proof.main() == 0
    ran = capsys.readouterr().out
    assert "delta_proof_expired" not in ran
    assert "BTC vs prior capture: " in ran
    assert _json_line(ran)["ok"] is True

    hits: list[str] = []
    monkeypatch.setattr(
        delta_proof,
        "build_close_proof",
        lambda: hits.append("render") or (_ for _ in ()).throw(AssertionError("render")),
    )
    monkeypatch.setattr(
        delta_proof,
        "query_btc_captures",
        lambda _dsn: hits.append("query") or (_ for _ in ()).throw(AssertionError("query")),
    )
    refused = datetime(2026, 10, 3, 0, 0, tzinfo=SYDNEY)
    monkeypatch.setattr(delta_proof, "utc_now", lambda: refused.astimezone(timezone.utc))
    real_environ = os.environ
    try:
        os.environ = _RaisingEnviron()  # type: ignore[assignment]
        rc = delta_proof.main()
        payload = json.loads(capsys.readouterr().out.strip())
    finally:
        os.environ = real_environ
    assert rc != 0
    assert hits == []
    assert payload["proof"] == "delta_proof"
    assert payload["ok"] is False
    assert payload["reason"] == "delta_proof_expired"
    assert payload["sydney_date"] == "2026-10-03"


def test_delta_proof_job_secrets_exactly_postgres_dsn() -> None:
    text, parsed = _workflow()
    job = parsed["jobs"]["delta-proof"]
    job_text = _delta_job_text(text)
    names = set(re.findall(r"secrets\.([A-Za-z0-9_]+)", job_text))
    assert names == {"POSTGRES_DSN"}
    assert job["env"]["POSTGRES_DSN"] == "${{ secrets.POSTGRES_DSN }}"
    assert set(job["env"]) == {"POSTGRES_DSN", "MM_DELIVERY_ENV_FILE"}
    assert job["env"]["MM_DELIVERY_ENV_FILE"] == "/tmp/mm-actions-brief-no-delivery.env"
    for forbidden in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "TELEGRAM_CHAT_ID_PRINCIPAL_DM",
        "HEALTHCHECKS_PING_URL",
        "POLYGON_API_KEY",
        "FRED_API_KEY",
        "DATABASE_URL",
        "NEON_DATABASE_URL",
    ):
        assert forbidden not in job_text


def test_delta_proof_job_contents_read() -> None:
    text, parsed = _workflow()
    job = parsed["jobs"]["delta-proof"]
    job_text = _delta_job_text(text)
    assert job["permissions"] == {"contents": "read"}
    assert set(job["permissions"]) == {"contents"}
    assert job["timeout-minutes"] == 5
    assert "contents: write" not in job_text
    assert job["if"] == "github.event_name == 'workflow_dispatch' && inputs.mode == 'delta_proof'"
    assert "needs" not in job
    assert job["steps"][-1]["run"].strip().endswith("uv run python -m mm_briefing.delta_proof")
    uses = [step.get("uses") for step in job["steps"] if step.get("uses")]
    assert uses == ["actions/checkout@v4", "astral-sh/setup-uv@v6"]
    assert any(step.get("run") == "uv sync --all-packages" for step in job["steps"])


def test_delta_proof_skips_stamp_and_deliver_jobs() -> None:
    _text, parsed = _workflow()
    jobs = parsed["jobs"]
    snap = json.loads(JOBS_SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["commit"] == MAIN_COMMIT
    stamp = jobs["stage1-stamp"]["if"]
    brief = jobs["brief-and-deliver"]["if"]
    assert _eval_expr(stamp, event="workflow_dispatch", mode="delta_proof", deliver=True) is False
    assert _eval_expr(brief, event="workflow_dispatch", mode="delta_proof", deliver=True) is False
    unchanged = (
        ("schedule", None, False),
        ("schedule", "normal", False),
        ("schedule", "normal", True),
        ("workflow_dispatch", "normal", False),
        ("workflow_dispatch", "normal", True),
        ("workflow_dispatch", None, True),
        ("workflow_dispatch", "capture_proof", True),
        ("workflow_dispatch", "render_proof", True),
    )
    for event, mode, deliver in unchanged:
        assert _eval_expr(stamp, event=event, mode=mode, deliver=deliver) is _eval_expr(
            snap["jobs"]["stage1-stamp"]["if"], event=event, mode=mode, deliver=deliver
        )
        assert _eval_expr(brief, event=event, mode=mode, deliver=deliver) is _eval_expr(
            snap["jobs"]["brief-and-deliver"]["if"], event=event, mode=mode, deliver=deliver
        )
    options = _on_block(parsed)["workflow_dispatch"]["inputs"]["mode"]["options"]
    assert options == ["normal", "capture_proof", "render_proof", "delta_proof"]
    triggers = set(_on_block(parsed))
    assert triggers == {"schedule", "workflow_dispatch"}


def test_delta_proof_concurrency_group_isolated() -> None:
    text, parsed = _workflow()
    assert parsed["concurrency"]["group"] == CONCURRENCY_GROUP
    assert parsed["concurrency"]["cancel-in-progress"] is False
    assert text.count("cancel-in-progress:") == 1
    inner = CONCURRENCY_GROUP.removeprefix("${{").removesuffix("}}").strip()
    assert _eval_expr(inner, event="workflow_dispatch", mode="delta_proof") == "delta-proof-never-merge"
    for event, mode in (
        ("schedule", None),
        ("schedule", "normal"),
        ("workflow_dispatch", "normal"),
        ("workflow_dispatch", None),
        ("workflow_dispatch", "capture_proof"),
        ("workflow_dispatch", "render_proof"),
        ("workflow_dispatch", ""),
        ("push", "delta_proof"),
    ):
        assert _eval_expr(inner, event=event, mode=mode) == "hybrid-sydney-morning"


def test_stamp_deliver_jobs_identical_to_main() -> None:
    _text, parsed = _workflow()
    snap = json.loads(JOBS_SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["commit"] == MAIN_COMMIT
    current = parsed["jobs"]
    for name in ("stage1-stamp", "brief-and-deliver"):
        assert _without_delta_gate(current[name]) == snap["jobs"][name]
        assert current[name]["steps"] == snap["jobs"][name]["steps"]
