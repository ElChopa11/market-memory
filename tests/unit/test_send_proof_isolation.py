"""send_proof isolation. Same bar as render_proof: explicit assertions.

The job entry point is ``python -m mm_briefing.send_proof``. Forbidden writers
raise if called. Market HTTP is a saved Polygon, FRED, and metaAndAssetCtxs
fixture. Telegram is a mock of ``TelegramClient.send_message``.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import yaml

from mm_briefing.render_proof import build_close_proof
from mm_briefing import render_proof, send_proof
from mm_delivery.format import escape_markdown_v2
from mm_delivery.idempotency import DedupeStore
from mm_delivery.telegram import TelegramApiResult
from mm_lab_cli.deliver import append_brief_status_lines

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "briefing"
JOBS_SNAPSHOT = ROOT / "tests" / "fixtures" / "scheduler" / "hybrid_sydney_morning_d6d35f6_jobs.json"
MAIN_COMMIT = "d6d35f64003f274f51c386f805f981be85b34a10"
AS_OF = datetime(2026, 9, 25, 8, 30, tzinfo=timezone.utc)
CAPTURE_LINE = "CAPTURE: n/a (send_proof)"
SEND_PROOF_FRAGMENT = " && inputs.mode != 'send_proof'"
ALLOWED_SECRETS = frozenset(
    {
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID_PRINCIPAL_DM",
        "POLYGON_API_KEY",
        "FRED_API_KEY",
    }
)
FORBIDDEN_SECRET_NAMES = (
    "TELEGRAM_CHAT_ID",
    "HEALTHCHECKS_PING_URL",
    "POSTGRES_DSN",
    "DATABASE_URL",
    "NEON_DATABASE_URL",
)
DM_CHAT = "fixture-principal-dm"
GROUP_CHAT = "fixture-group-chat"
BOT_TOKEN = "fixture-bot-token"
MARKET_TOKEN = "fixture"
_REAL_HTTPX_CLIENT = httpx.Client

STAMP_IF = (
    "github.event_name != 'workflow_dispatch' || "
    "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof') && "
    "inputs.mode != 'send_proof'"
)
BRIEF_IF = (
    "(github.event_name != 'workflow_dispatch' || "
    "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof')) && "
    "(github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && "
    "(inputs.i_mean_it_deliver == true || github.event.inputs.i_mean_it_deliver == 'true')))"
    " && inputs.mode != 'send_proof'"
)
CAPTURE_JOB_IF = "github.event_name == 'workflow_dispatch' && inputs.mode == 'capture_proof'"
RENDER_JOB_IF = "github.event_name == 'workflow_dispatch' && inputs.mode == 'render_proof'"
SEND_JOB_IF = "github.event_name == 'workflow_dispatch' && inputs.mode == 'send_proof'"
SECRET_RE_TEXT = (
    "secrets.TELEGRAM_BOT_TOKEN",
    "secrets.TELEGRAM_CHAT_ID_PRINCIPAL_DM",
    "secrets.POLYGON_API_KEY",
    "secrets.FRED_API_KEY",
)


def _workflow():
    text = WORKFLOW.read_text(encoding="utf-8")
    return text, yaml.safe_load(text)


def _job_runs(expr: str | None, event: str, mode: str | None, *, deliver: bool = False) -> bool:
    """Evaluate a job ``if`` the way the render_proof gating test does."""
    if expr is None:
        raise AssertionError("job has no if")
    if expr == STAMP_IF:
        return event != "workflow_dispatch" or mode not in {"capture_proof", "render_proof", "send_proof"}
    if expr == BRIEF_IF:
        mode_ok = event != "workflow_dispatch" or mode not in {"capture_proof", "render_proof"}
        deliver_ok = event == "schedule" or (event == "workflow_dispatch" and deliver)
        return mode_ok and deliver_ok and mode != "send_proof"
    if expr == CAPTURE_JOB_IF:
        return event == "workflow_dispatch" and mode == "capture_proof"
    if expr == RENDER_JOB_IF:
        return event == "workflow_dispatch" and mode == "render_proof"
    if expr == SEND_JOB_IF:
        return event == "workflow_dispatch" and mode == "send_proof"
    raise AssertionError(f"unrecognised job if: {expr}")


def _secret_names(node) -> set[str]:
    secret_re = re.compile(r"secrets\.([A-Za-z0-9_]+)|secrets\[\s*['\"]([A-Za-z0-9_]+)['\"]\s*\]")
    found: set[str] = set()

    def walk(value) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            for match in secret_re.finditer(value):
                found.add(match.group(1) or match.group(2))

    walk(node)
    return found


def _scoped_secret_names(job: dict) -> set[str]:
    found: set[str] = set()
    if "env" in job:
        found |= _secret_names(job["env"])
    for step in job.get("steps") or []:
        for key in ("env", "with", "run"):
            if key in step:
                found |= _secret_names(step[key])
    return found


def _install_fixture_http(monkeypatch) -> None:
    polygon = json.loads((FIXTURE_DIR / "morning_polygon_aggs.json").read_text(encoding="utf-8"))
    fred = json.loads((FIXTURE_DIR / "morning_fred_rolled.json").read_text(encoding="utf-8"))
    hl_body = json.loads((FIXTURE_DIR / "morning_hl_meta_and_asset_ctxs.json").read_text(encoding="utf-8"))
    original = _REAL_HTTPX_CLIENT

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == "api.telegram.org":
            raise AssertionError("send_proof fixture transport refuses live Telegram")
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
        return httpx.Response(404, json={"error": "fixture transport refuses this host"})

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", factory)


def _forbid(called: list[str], name: str):
    def _inner(*_args, **_kwargs):
        called.append(name)
        raise AssertionError(f"{name} must not run on send_proof")

    return _inner


def _install_forbidden(monkeypatch, called: list[str]) -> None:
    targets = (
        "mm_desks.deliver_receipt.write_deliver_receipt",
        "mm_ingest.mvp_retain.run_morning_capture",
        "mm_ingest.mvp_retain.run_proof_capture",
        "mm_ingest.mvp_retain.persist_mvp_retain",
        "mm_ingest.mvp_retain._neon_session",
        "mm_ingest.pipeline.persist_envelopes",
        "mm_memory.db.make_engine",
        "mm_memory.db.session_scope",
        "mm_lab_cli.completion.stamp_cli_fire",
        "mm_lab_cli.briefing.stamp_cli_fire",
        "mm_lab_cli.deliver.stamp_cli_fire",
        "mm_desks.completions.write_completion",
        "mm_desks.completions.record_cli_completion",
        "mm_lab_cli.deadman.ping_deadman",
        "mm_lab_cli.deadman.ping_deadman_start",
        "mm_lab_cli.deadman.ping_deadman_success",
        "mm_lab_cli.deliver.ping_deadman_start",
        "mm_lab_cli.deliver.ping_deadman_success",
    )
    for target in targets:
        monkeypatch.setattr(target, _forbid(called, target))
    import sys

    deliver_mod = sys.modules["mm_delivery.deliver"]
    monkeypatch.setattr(deliver_mod, "write_payload_files", _forbid(called, "mm_delivery.deliver.write_payload_files"))
    monkeypatch.setattr(
        "mm_ingest.mvp_retain.NeonRetainStore",
        _forbid(called, "mm_ingest.mvp_retain.NeonRetainStore"),
    )
    real_dump = DedupeStore.dump

    def _dump(self) -> None:
        if self.path is not None:
            called.append("DedupeStore.dump")
            raise AssertionError("send_proof dedupe store must not write a file")
        real_dump(self)

    monkeypatch.setattr(DedupeStore, "dump", _dump)
    real_run = subprocess.run

    def _run(args, **kwargs):
        parts = args if isinstance(args, (list, tuple)) else [args]
        flat = " ".join(str(part) for part in parts).lower()
        if "git" in flat and ("commit" in flat or "push" in flat):
            called.append("git")
            raise AssertionError("git commit or push must not run on send_proof")
        return real_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", _run)


def _install_send(monkeypatch, posted: list[dict]) -> None:
    def send_message(self, *, chat_id, text, parse_mode="MarkdownV2", **kwargs):
        posted.append(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "message_thread_id": kwargs.get("message_thread_id"),
            }
        )
        return TelegramApiResult(
            method="sendMessage",
            ok=True,
            error_class="none",
            attempts=1,
            status_code=200,
        )

    monkeypatch.setattr("mm_delivery.telegram.TelegramClient.send_message", send_message)


def _prepare(monkeypatch, tmp_path, *, token: str | None, dm: str | None, polygon: str | None, fred: str | None, group: str | None) -> Path:
    monkeypatch.chdir(ROOT)
    # Expiry uses the system clock, not the brief as-of. Freeze it inside the
    # allowed Sydney window so tests 3–6 stay green after 2026-09-28.
    monkeypatch.setattr(send_proof, "utc_now", lambda: AS_OF)
    monkeypatch.setattr(render_proof, "utcnow", lambda: AS_OF)
    monkeypatch.setattr("mm_briefing.fetchers.time.sleep", lambda *_args, **_kwargs: None)
    _install_fixture_http(monkeypatch)
    for key, value in (
        ("TELEGRAM_BOT_TOKEN", token),
        ("TELEGRAM_CHAT_ID_PRINCIPAL_DM", dm),
        ("POLYGON_API_KEY", polygon),
        ("FRED_API_KEY", fred),
        ("TELEGRAM_CHAT_ID", group),
    ):
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    monkeypatch.delenv("HEALTHCHECKS_PING_URL", raising=False)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    return summary


def _json_result(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("{"):
            return json.loads(line)
    raise AssertionError(f"no JSON result in stdout: {stdout!r}")


def _without_send_proof_gate(job: dict) -> dict:
    cloned = copy.deepcopy(job)
    expr = cloned["if"]
    assert isinstance(expr, str)
    assert expr.count(SEND_PROOF_FRAGMENT) == 1
    cloned["if"] = expr.replace(SEND_PROOF_FRAGMENT, "", 1)
    return cloned


def test_send_proof_secret_allowlist_is_exactly_telegram_dm_polygon_fred() -> None:
    text, parsed = _workflow()
    job = parsed["jobs"]["send-proof"]
    start = text.index("\n  send-proof:\n")
    end = text.index("\n  capture-proof:\n")
    job_text = text[start:end]
    assert _scoped_secret_names(job) == ALLOWED_SECRETS
    assert _secret_names(job) == ALLOWED_SECRETS
    for name in FORBIDDEN_SECRET_NAMES:
        assert name not in _scoped_secret_names(job)
        assert re.search(rf"secrets\.{name}(?![A-Za-z0-9_])", job_text) is None
    assert "POSTGRES_DSN" not in job_text
    assert "HEALTHCHECKS_PING_URL" not in job_text
    assert "TELEGRAM_CHAT_ID:" not in job_text
    assert "TELEGRAM_CHAT_ID }}" not in job_text
    assert job["permissions"] == {"contents": "read"}
    assert set(job["permissions"]) == {"contents"}
    assert "needs" not in job
    assert set(job["env"]) == ALLOWED_SECRETS | {"MM_DELIVERY_ENV_FILE"}
    assert job["env"]["MM_DELIVERY_ENV_FILE"] == "/tmp/mm-actions-brief-no-delivery.env"
    for name in ALLOWED_SECRETS:
        assert job["env"][name] == f"${{{{ secrets.{name} }}}}"
    assert job["steps"][-1]["run"].strip().endswith("uv run python -m mm_briefing.send_proof")
    for needle in SECRET_RE_TEXT:
        assert needle in job_text


def test_send_proof_gating_skips_every_other_job_including_stamp() -> None:
    _text, parsed = _workflow()
    jobs = parsed["jobs"]
    assert set(jobs) == {"stage1-stamp", "brief-and-deliver", "send-proof", "capture-proof", "render-proof"}
    assert jobs["capture-proof"]["if"] == CAPTURE_JOB_IF
    assert jobs["render-proof"]["if"] == RENDER_JOB_IF
    assert jobs["send-proof"]["if"] == SEND_JOB_IF
    for deliver in (False, True):
        for name, job in jobs.items():
            runs = _job_runs(job.get("if"), "workflow_dispatch", "send_proof", deliver=deliver)
            if name == "send-proof":
                assert runs is True
                continue
            assert runs is False, name

    send_if = jobs["send-proof"]["if"]
    for event, mode in (
        ("schedule", None),
        ("schedule", "normal"),
        ("schedule", "send_proof"),
        ("workflow_dispatch", "normal"),
        ("workflow_dispatch", None),
        ("workflow_dispatch", "capture_proof"),
        ("workflow_dispatch", "render_proof"),
        ("workflow_dispatch", "send_proof"),
        ("push", "send_proof"),
    ):
        assert _job_runs(send_if, event, mode) is (event == "workflow_dispatch" and mode == "send_proof")

    assert _job_runs(jobs["stage1-stamp"]["if"], "schedule", None) is True
    assert _job_runs(jobs["brief-and-deliver"]["if"], "schedule", None, deliver=False) is True
    assert _job_runs(jobs["stage1-stamp"]["if"], "workflow_dispatch", "normal") is True
    assert _job_runs(jobs["brief-and-deliver"]["if"], "workflow_dispatch", "normal", deliver=True) is True
    assert _job_runs(jobs["brief-and-deliver"]["if"], "workflow_dispatch", "normal", deliver=False) is False
    assert _job_runs(jobs["send-proof"]["if"], "schedule", "normal") is False
    assert _job_runs(jobs["send-proof"]["if"], "workflow_dispatch", "normal", deliver=True) is False


def test_send_proof_forbidden_writers_raise(monkeypatch, capsys, tmp_path) -> None:
    called: list[str] = []
    posted: list[dict] = []
    summary = _prepare(
        monkeypatch,
        tmp_path,
        token=BOT_TOKEN,
        dm=DM_CHAT,
        polygon=MARKET_TOKEN,
        fred=MARKET_TOKEN,
        group=GROUP_CHAT,
    )
    monkeypatch.setenv("POSTGRES_DSN", "sentinel-postgres-dsn-not-a-secret")
    monkeypatch.setenv("HEALTHCHECKS_PING_URL", "sentinel-healthchecks-not-a-secret")
    _install_forbidden(monkeypatch, called)
    _install_send(monkeypatch, posted)

    rc = send_proof.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert called == []
    assert len(posted) == 1
    payload = _json_result(captured.out)
    assert payload["sent"] is True
    assert payload["http_status"] == 200
    blob = captured.out + captured.err + summary.read_text(encoding="utf-8")
    for secret in (
        BOT_TOKEN,
        DM_CHAT,
        GROUP_CHAT,
        "sentinel-postgres-dsn-not-a-secret",
        "sentinel-healthchecks-not-a-secret",
    ):
        assert secret not in blob


def test_send_proof_uses_deliver_path_escape_and_send_functions(monkeypatch, capsys, tmp_path) -> None:
    posted: list[dict] = []
    escape_args: list[str] = []
    real_escape = escape_markdown_v2

    def spy_escape(text: str) -> str:
        escape_args.append(text)
        return real_escape(text)

    _prepare(
        monkeypatch,
        tmp_path,
        token=BOT_TOKEN,
        dm=DM_CHAT,
        polygon=MARKET_TOKEN,
        fred=MARKET_TOKEN,
        group=GROUP_CHAT,
    )
    monkeypatch.setattr("mm_delivery.format.escape_markdown_v2", spy_escape)
    _install_send(monkeypatch, posted)
    render, _sources = build_close_proof()
    expected_body = append_brief_status_lines(render, capture=CAPTURE_LINE)
    expected = real_escape(expected_body)

    rc = send_proof.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert escape_args
    assert expected_body in escape_args
    assert len(posted) == 1
    assert posted[0]["text"] == expected
    assert posted[0]["parse_mode"] == "MarkdownV2"
    assert posted[0]["chat_id"] == DM_CHAT
    assert "LATE:" not in expected_body
    assert "DEADMAN" not in expected_body
    assert expected_body.rstrip("\n").splitlines()[-1] == CAPTURE_LINE
    payload = _json_result(captured.out)
    assert payload["sent"] is True
    assert payload["message_length"] == len(expected)
    assert len(expected) <= 4096


def test_send_proof_one_message_to_dm_only(monkeypatch, capsys, tmp_path) -> None:
    """TELEGRAM_CHAT_ID is ignored when it differs from the DM id.

    ``deliver`` refuses with ``principal_dm_is_group`` and zero POSTs when the
    two ids are equal. send_proof calls that function and does not add a second route.
    """
    posted: list[dict] = []
    _prepare(
        monkeypatch,
        tmp_path,
        token=BOT_TOKEN,
        dm=DM_CHAT,
        polygon=MARKET_TOKEN,
        fred=MARKET_TOKEN,
        group=GROUP_CHAT,
    )
    _install_send(monkeypatch, posted)
    rc = send_proof.main()
    capsys.readouterr()
    assert rc == 0
    assert len(posted) == 1
    assert posted[0]["chat_id"] == DM_CHAT
    assert posted[0]["chat_id"] != GROUP_CHAT

    posted.clear()
    monkeypatch.setenv("TELEGRAM_CHAT_ID", DM_CHAT)
    monkeypatch.setenv("TELEGRAM_CHAT_ID_PRINCIPAL_DM", DM_CHAT)
    refused = send_proof.main()
    refused_out = capsys.readouterr().out
    assert refused != 0
    assert posted == []
    assert _json_result(refused_out)["sent"] is False
    assert _json_result(refused_out)["reason"] == "principal_dm_is_group"


def test_send_proof_missing_key_fails_before_send(monkeypatch, capsys, tmp_path) -> None:
    cases = (
        {"token": None, "dm": DM_CHAT, "polygon": MARKET_TOKEN, "fred": MARKET_TOKEN},
        {"token": BOT_TOKEN, "dm": None, "polygon": MARKET_TOKEN, "fred": MARKET_TOKEN},
        {"token": BOT_TOKEN, "dm": DM_CHAT, "polygon": None, "fred": MARKET_TOKEN},
        {"token": BOT_TOKEN, "dm": DM_CHAT, "polygon": MARKET_TOKEN, "fred": None},
    )
    for case in cases:
        posted: list[dict] = []
        _prepare(monkeypatch, tmp_path, group=GROUP_CHAT, **case)
        _install_send(monkeypatch, posted)
        rc = send_proof.main()
        captured = capsys.readouterr()
        assert rc != 0
        assert posted == []
        payload = _json_result(captured.out)
        assert payload["sent"] is False
        if case["polygon"] is None or case["fred"] is None:
            assert payload["reason"] == "render_proof_fail"
            assert "RENDER_PROOF FAIL" in captured.out


def test_main_deliver_path_unchanged() -> None:
    _text, parsed = _workflow()
    snap = json.loads(JOBS_SNAPSHOT.read_text(encoding="utf-8"))
    assert snap["commit"] == MAIN_COMMIT
    current = parsed["jobs"]
    for name in ("stage1-stamp", "brief-and-deliver"):
        assert _without_send_proof_gate(current[name]) == snap["jobs"][name]
        assert current[name]["steps"] == snap["jobs"][name]["steps"]


def test_send_proof_refuses_after_expiry(monkeypatch, capsys, tmp_path) -> None:
    from mm_briefing.fetchers import LiveMacroFetcher

    posted: list[dict] = []
    _prepare(
        monkeypatch,
        tmp_path,
        token=BOT_TOKEN,
        dm=DM_CHAT,
        polygon=MARKET_TOKEN,
        fred=MARKET_TOKEN,
        group=GROUP_CHAT,
    )
    _install_send(monkeypatch, posted)
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID_PRINCIPAL_DM", "POLYGON_API_KEY", "FRED_API_KEY"):
        assert os.environ.get(key)

    last_second = datetime(2026, 9, 28, 13, 59, 59, tzinfo=timezone.utc)
    monkeypatch.setattr(send_proof, "utc_now", lambda: last_second)
    rc = send_proof.main()
    capsys.readouterr()
    assert rc == 0
    assert len(posted) == 1

    def _expired(moment: datetime) -> None:
        posted.clear()
        hits: list[str] = []

        def _boom(name: str):
            def _inner(*_args, **_kwargs):
                hits.append(name)
                raise AssertionError(f"{name} must not run after send_proof expiry")

            return _inner

        monkeypatch.setattr(LiveMacroFetcher, "_fetch_polygon", _boom("polygon"))
        monkeypatch.setattr(LiveMacroFetcher, "_fetch_fred", _boom("fred"))
        monkeypatch.setattr("mm_briefing.engine.hl_from_live_info", _boom("hl"))
        monkeypatch.setattr(send_proof, "utc_now", lambda: moment)
        refused = send_proof.main()
        payload = _json_result(capsys.readouterr().out)
        sydney = moment.astimezone(ZoneInfo("Australia/Sydney")).date().isoformat()
        assert refused != 0
        assert posted == []
        assert hits == []
        assert payload["sent"] is False
        assert payload["reason"] == "send_proof_expired"
        assert payload["sydney_date"] == sydney
        assert sydney > "2026-09-28"

    _expired(datetime(2026, 9, 28, 14, 0, 0, tzinfo=timezone.utc))
    _expired(datetime(2099, 1, 1, 0, 0, tzinfo=timezone.utc))
