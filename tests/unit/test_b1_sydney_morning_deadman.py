"""Healthchecks.io dead-man ping on the Sydney morning Principal DM.

HTTP is mocked. The ping URL is a secret and must not appear in logs, the DM,
or the deliver receipt. A ping failure does not fail the send.
"""

from __future__ import annotations

import importlib
import io
import json
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_common.time import parse_utc
from mm_delivery.telegram import TelegramApiResult
from mm_desks.deliver_receipt import (
    ALREADY_DELIVERED,
    PROCEED,
    accept_delivery,
    assert_receipt_committable,
    decide_deliver,
    write_deliver_receipt,
)
from mm_lab_cli.cli import main
from mm_lab_cli.deadman import (
    DEADMAN_MISSING_LINE,
    DEADMAN_PING_TIMEOUT_SECONDS,
    HEALTHCHECKS_PING_URL_ENV,
    _http_get,
    deadman_receipt_fields,
    ping_success_if_already_delivered,
)
from mm_lab_cli.deliver import sydney_morning_late_line

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
ANCHOR = "2026-09-24T20:30:00Z"
ANCHOR_DT = datetime(2026, 9, 24, 20, 30, tzinfo=UTC)
RUN_ID = "actions-b1-36071921289"
PING_URL = "https://hc-ping.example/secret-uuid-not-for-logs"
PING_AT = datetime(2026, 9, 25, 1, 2, 3, tzinfo=UTC)
BRIEF = "Morning brief body. Not an order.\n"
DM_CHAT = "dm-only-chat"
ROUTINE = "grok.sydney_morning"


def _http(*, start: tuple[int, str] | Exception, success: tuple[int, str] = (200, "OK")):
    calls: list[str] = []

    def http_get(url: str, timeout: float) -> tuple[int, str]:
        assert timeout == DEADMAN_PING_TIMEOUT_SECONDS
        calls.append(url)
        if str(url).endswith("/start"):
            if isinstance(start, Exception):
                raise start
            return start
        return success

    return calls, http_get


def _run(
    monkeypatch,
    capsys,
    tmp_path: Path,
    *,
    sent_at: datetime,
    http_get,
    live: bool = True,
    telegram_ok: bool = True,
    url: str | None = PING_URL,
    calls: list[str] | None = None,
):
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv(PRINCIPAL_DM_CHAT_ID_ENV, DM_CHAT)
    if url is None:
        monkeypatch.delenv(HEALTHCHECKS_PING_URL_ENV, raising=False)
    else:
        monkeypatch.setenv(HEALTHCHECKS_PING_URL_ENV, url)
    monkeypatch.setattr("mm_lab_cli.deliver.utcnow", lambda: sent_at)
    monkeypatch.setattr("mm_lab_cli.deadman.utcnow", lambda: PING_AT)
    monkeypatch.setattr("mm_lab_cli.deadman._http_get", http_get)
    posted: list[dict[str, str]] = []

    class _FakeApi:
        def send_message(self, *, chat_id, text, **kwargs):
            if calls is not None:
                calls.append("telegram")
            posted.append({"chat_id": str(chat_id), "text": str(text)})
            return TelegramApiResult(
                method="sendMessage",
                ok=telegram_ok,
                error_class="none" if telegram_ok else "http_5xx",
                attempts=1,
                status_code=200 if telegram_ok else 500,
                payload={"ok": telegram_ok},
            )

        def close(self) -> None:
            return None

    deliver_module = importlib.import_module("mm_delivery.deliver")
    monkeypatch.setattr(deliver_module.TelegramClient, "from_settings", lambda *args, **kwargs: _FakeApi())
    brief = tmp_path / "brief.md"
    brief.write_text(BRIEF, encoding="utf-8")
    args = [
        "deliver",
        "pack",
        "--from-markdown",
        str(brief),
        "--as-of",
        "2026-09-24T23:16:50Z",
        "--scheduled-for",
        ANCHOR,
        "--run-id",
        RUN_ID,
        "--desk",
        "ops",
        "--to-principal-dm",
        "--repo-root",
        str(ROOT),
        "--out",
        str(tmp_path / "out"),
        "--ignore-quiet-hours",
    ]
    if live:
        args.append("--i-mean-it")
    else:
        args.append("--no-send")
    rc = main(args)
    captured = capsys.readouterr()
    blob = captured.out + captured.err
    assert "test-token" not in blob
    assert PING_URL not in blob
    assert "secret-uuid-not-for-logs" not in blob
    payload_path = tmp_path / "out" / "briefs" / "2026-09-24" / "telegram-payload.json"
    envelope = json.loads(payload_path.read_text(encoding="utf-8")) if payload_path.is_file() else {}
    stdout = json.loads(captured.out)
    return rc, str(envelope.get("text") or ""), posted, stdout, captured


def _write_receipt(tmp_path: Path, stdout: dict):
    repo = tmp_path / "repo"
    completions = repo / "ops" / "reports" / "scheduler" / "completions"
    fields = deadman_receipt_fields(stdout)
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=True,
        delivered_at=PING_AT,
        **fields,
    )
    assert created is True and path is not None
    assert_receipt_committable(path, repo_root=repo)
    body = json.loads(path.read_text(encoding="utf-8"))
    raw = path.read_text(encoding="utf-8")
    assert PING_URL not in raw
    assert "secret-uuid-not-for-logs" not in raw
    return body


def test_start_ok_then_send_then_success_ok_records_receipt(tmp_path: Path, monkeypatch, capsys) -> None:
    calls, http_get = _http(start=(200, "OK"), success=(200, "OK"))
    sent = ANCHOR_DT + timedelta(minutes=10)
    rc, text, posted, stdout, captured = _run(
        monkeypatch,
        capsys,
        tmp_path,
        sent_at=sent,
        http_get=http_get,
        calls=calls,
    )
    assert rc == 0
    assert "DEADMAN:" not in text
    assert DEADMAN_MISSING_LINE not in posted[0]["text"]
    assert len(posted) == 1
    assert posted[0]["chat_id"] == DM_CHAT
    assert calls == [f"{PING_URL}/start", "telegram", PING_URL]
    assert stdout["sent"] is True
    assert stdout["deadman_ping"] == "OK"
    assert stdout["deadman_ping_at"] == PING_AT.isoformat()
    assert "deadman start ping: OK" in captured.err
    assert "deadman success ping: OK" in captured.err
    body = _write_receipt(tmp_path, stdout)
    assert body["deadman_ping"] == "OK"
    assert body["deadman_ping_at"] == PING_AT.isoformat()
    parse_utc(body["deadman_ping_at"])


def test_start_404_not_found_appends_one_deadman_line(tmp_path: Path, monkeypatch, capsys) -> None:
    calls, http_get = _http(start=(404, "not found"), success=(200, "OK"))
    sent = ANCHOR_DT + timedelta(minutes=10)
    rc, text, posted, _stdout, _captured = _run(
        monkeypatch,
        capsys,
        tmp_path,
        sent_at=sent,
        http_get=http_get,
        calls=calls,
    )
    assert rc == 0
    assert text.count(DEADMAN_MISSING_LINE) == 1
    assert len(posted) == 1
    assert posted[0]["text"].count(DEADMAN_MISSING_LINE) == 1
    assert "LATE:" not in posted[0]["text"]
    assert calls[0] == f"{PING_URL}/start"
    assert "telegram" in calls


def test_unset_secret_appends_deadman_and_receipt_is_unset(tmp_path: Path, monkeypatch, capsys) -> None:
    calls: list[str] = []

    def http_get(url: str, timeout: float) -> tuple[int, str]:
        calls.append(url)
        raise AssertionError("unset secret must not open a connection")

    sent = ANCHOR_DT + timedelta(minutes=10)
    rc, text, posted, stdout, _captured = _run(
        monkeypatch,
        capsys,
        tmp_path,
        sent_at=sent,
        http_get=http_get,
        url=None,
        calls=calls,
    )
    assert rc == 0
    assert text.count(DEADMAN_MISSING_LINE) == 1
    assert len(posted) == 1
    assert posted[0]["text"].count(DEADMAN_MISSING_LINE) == 1
    assert calls == ["telegram"]
    assert stdout["deadman_ping"] == "unset"
    body = _write_receipt(tmp_path, stdout)
    assert body["deadman_ping"] == "unset"
    assert body["deadman_ping_at"] == PING_AT.isoformat()
    assert body["sent"] is True


def test_start_timeout_appends_deadman_line(tmp_path: Path, monkeypatch, capsys) -> None:
    calls, http_get = _http(start=TimeoutError(PING_URL), success=(200, "OK"))
    sent = ANCHOR_DT + timedelta(minutes=10)
    rc, text, posted, _stdout, captured = _run(
        monkeypatch,
        capsys,
        tmp_path,
        sent_at=sent,
        http_get=http_get,
        calls=calls,
    )
    assert rc == 0
    assert text.count(DEADMAN_MISSING_LINE) == 1
    assert len(posted) == 1
    assert posted[0]["text"].count(DEADMAN_MISSING_LINE) == 1
    assert PING_URL not in captured.err
    assert calls[0] == f"{PING_URL}/start"
    assert "telegram" in calls


def test_failed_send_does_not_success_ping_or_write_a_receipt(tmp_path: Path, monkeypatch, capsys) -> None:
    calls, http_get = _http(start=(200, "OK"), success=(200, "OK"))
    sent = ANCHOR_DT + timedelta(minutes=10)
    rc, _text, posted, stdout, captured = _run(
        monkeypatch,
        capsys,
        tmp_path,
        sent_at=sent,
        http_get=http_get,
        telegram_ok=False,
        calls=calls,
    )
    assert rc != 0
    assert len(posted) == 1
    assert calls == [f"{PING_URL}/start", "telegram"]
    assert "deadman success ping:" not in captured.err
    assert "deadman_ping" not in stdout
    assert accept_delivery(captured.out, rc) is False
    repo = tmp_path / "repo"
    completions = repo / "ops" / "reports" / "scheduler" / "completions"
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=False,
    )
    assert path is None and created is False
    assert list(completions.rglob("*.json")) == []


def test_already_delivered_success_pings_only(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = tmp_path / "repo"
    completions = repo / "ops" / "reports" / "scheduler" / "completions"
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id=ROUTINE,
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=True,
        delivered_at=PING_AT,
    )
    assert created is True and path is not None
    before = path.read_bytes()
    decision = decide_deliver(completions, ROUTINE, ANCHOR)
    assert decision == ALREADY_DELIVERED
    calls, http_get = _http(start=(500, "no"), success=(200, "OK"))
    monkeypatch.setenv(HEALTHCHECKS_PING_URL_ENV, PING_URL)
    monkeypatch.setattr("mm_lab_cli.deadman.utcnow", lambda: PING_AT)
    monkeypatch.setattr("mm_lab_cli.deadman._http_get", http_get)

    def _no_telegram(*args, **kwargs):
        raise AssertionError("already_delivered must not open Telegram")

    deliver_module = importlib.import_module("mm_delivery.deliver")
    monkeypatch.setattr(deliver_module.TelegramClient, "from_settings", _no_telegram)
    ping = ping_success_if_already_delivered(decision)
    captured = capsys.readouterr()
    assert ping is not None
    assert ping.outcome == "OK"
    assert ping.log_line() == "deadman success ping: OK"
    assert "deadman success ping: OK" in captured.err
    assert PING_URL not in captured.out
    assert PING_URL not in captured.err
    assert calls == [PING_URL]
    assert path.read_bytes() == before
    assert "deadman_ping" not in json.loads(path.read_text(encoding="utf-8"))
    assert ping_success_if_already_delivered(PROCEED) is None
    assert calls == [PING_URL]


def test_late_and_deadman_share_one_post_late_first(tmp_path: Path, monkeypatch, capsys) -> None:
    calls, http_get = _http(start=(404, "not found"), success=(200, "OK"))
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    late = sydney_morning_late_line(ANCHOR, sent, RUN_ID)
    assert late is not None
    rc, text, posted, _stdout, _captured = _run(
        monkeypatch,
        capsys,
        tmp_path,
        sent_at=sent,
        http_get=http_get,
        calls=calls,
    )
    assert rc == 0
    assert text.count(late) == 1
    assert text.count(DEADMAN_MISSING_LINE) == 1
    assert text.index(late) < text.index(DEADMAN_MISSING_LINE)
    assert len(posted) == 1
    assert posted[0]["text"].count("LATE:") == 1
    assert posted[0]["text"].count(DEADMAN_MISSING_LINE) == 1
    assert posted[0]["text"].index("LATE:") < posted[0]["text"].index(DEADMAN_MISSING_LINE)
    assert calls.count("telegram") == 1
    assert calls[0].endswith("/start")


def test_http_get_maps_ok_and_not_found_without_returning_the_url(monkeypatch) -> None:
    url = PING_URL

    class _OK:
        status = 200

        def read(self, _n: int) -> bytes:
            return b"OK\n"

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> bool:
            return False

    class _Opener:
        def open(self, request, timeout):
            assert request.full_url == url
            assert timeout == DEADMAN_PING_TIMEOUT_SECONDS
            return _OK()

    monkeypatch.setattr("mm_lab_cli.deadman.urllib.request.build_opener", lambda *_a, **_k: _Opener())
    assert _http_get(url, DEADMAN_PING_TIMEOUT_SECONDS) == (200, "OK")

    err = urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=io.BytesIO(b"not found"))

    class _Missing:
        def open(self, request, timeout):
            assert request.full_url == url
            raise err

    monkeypatch.setattr("mm_lab_cli.deadman.urllib.request.build_opener", lambda *_a, **_k: _Missing())
    status, body = _http_get(url, DEADMAN_PING_TIMEOUT_SECONDS)
    assert (status, body) == (404, "not found")
    assert url not in body


def test_workflow_passes_the_secret_only_to_steps_that_ping() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    stage1_key = "\n  stage1-stamp:\n"
    brief_key = "\n  brief-and-deliver:\n"
    stage1 = text[text.index(stage1_key) : text.index(brief_key)]
    brief = text[text.index(brief_key) :]
    assert "HEALTHCHECKS" not in stage1
    assert "repository_dispatch" not in text
    assert text.count("secrets.HEALTHCHECKS_PING_URL") == 2
    assert brief.count("HEALTHCHECKS_PING_URL: ${{ secrets.HEALTHCHECKS_PING_URL }}") == 2
    job_env = brief[brief.index("\n    env:\n") : brief.index("\n    steps:\n")]
    assert "HEALTHCHECKS" not in job_env
    assert "TELEGRAM_CHAT_ID:" not in job_env

    steps = brief.split("\n      - ")
    holders = [step.splitlines()[0] for step in steps if "HEALTHCHECKS_PING_URL" in step]
    assert holders == [
        "name: Deliver-receipt gate (scheduled_anchor, before brief or Telegram)",
        "name: Deliver pack to Principal DM (--to-principal-dm --i-mean-it)",
    ]
    assert "$HEALTHCHECKS_PING_URL" not in text
    assert "${HEALTHCHECKS_PING_URL}" not in text
    for line in text.splitlines():
        if "HEALTHCHECKS" not in line:
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert not stripped.startswith("echo")
        assert "echo " not in stripped
        assert "print(" not in stripped

    command = brief[brief.index("uv run lab deliver pack") : brief.index('> "/tmp/sydney-deliver-')]
    assert "HEALTHCHECKS" not in command
    receipt = next(step for step in steps if step.startswith("name: Deliver-receipt gate"))
    deliver = next(step for step in steps if step.startswith("name: Deliver pack to Principal DM"))
    assert "ping_success_if_already_delivered" in receipt
    assert "ping_success_if_already_delivered" not in deliver
    assert "deadman_receipt_fields" in deliver
    assert "write_deliver_receipt" not in receipt
    assert receipt.index("already_delivered=true") < receipt.index("ping_success_if_already_delivered(decision)")
    assert deliver.index("if not accept_delivery") < deliver.index("fields = deadman_receipt_fields(parsed)")
    assert deliver.index("fields = deadman_receipt_fields(parsed)") < deliver.index("path, created = write_deliver_receipt(")
    assert "steps.receipt.outputs.already_delivered != 'true'" in deliver
    assert text.count("\n  stage1-stamp:\n") == 1
    assert text.count("\n  brief-and-deliver:\n") == 1
