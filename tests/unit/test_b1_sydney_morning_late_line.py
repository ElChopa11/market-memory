"""Sydney morning Principal DM reports its own lateness on the same send.

Delta is send-time UTC minus the scheduled_for anchor. More than 30 minutes
appends one LATE line to that DM. Exactly 30 minutes, less, or early adds
nothing. already_delivered does not send.
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_delivery.format import escape_markdown_v2
from mm_delivery.telegram import TelegramApiResult
from mm_desks.deliver_receipt import ALREADY_DELIVERED, attempt_deliver, write_deliver_receipt
from mm_lab_cli.cli import main
from mm_lab_cli.deliver import apply_sydney_morning_late_line, sydney_morning_late_line

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
ANCHOR = "2026-09-24T20:30:00Z"
ANCHOR_DT = datetime(2026, 9, 24, 20, 30, tzinfo=UTC)
RUN_ID = "actions-b1-36071921289"
LATE_2H46 = (
    "LATE: grok.sydney_morning fired +2h 46m past anchor. "
    f"run_id {RUN_ID}."
)
LATE_0H31 = (
    "LATE: grok.sydney_morning fired +0h 31m past anchor. "
    f"run_id {RUN_ID}."
)
BRIEF = "Morning brief body. Not an order.\n"
DM_CHAT = "dm-only-chat"


def test_late_line_matches_the_observed_anchor() -> None:
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    assert sydney_morning_late_line(ANCHOR, sent, RUN_ID) == LATE_2H46
    assert sydney_morning_late_line(ANCHOR_DT, sent, RUN_ID) == LATE_2H46


def test_exactly_thirty_minutes_adds_no_line() -> None:
    sent = ANCHOR_DT + timedelta(minutes=30)
    assert (sent - ANCHOR_DT).total_seconds() == 30 * 60
    assert sydney_morning_late_line(ANCHOR, sent, RUN_ID) is None


def test_thirty_one_minutes_is_zero_hours_thirty_one_minutes() -> None:
    sent = ANCHOR_DT + timedelta(minutes=31)
    assert sydney_morning_late_line(ANCHOR, sent, RUN_ID) == LATE_0H31


def test_one_second_past_thirty_minutes_floors_display() -> None:
    """Threshold is delta > 30 minutes. Display minutes are floored."""
    sent = ANCHOR_DT + timedelta(minutes=30, seconds=1)
    line = sydney_morning_late_line(ANCHOR, sent, RUN_ID)
    assert line == (
        "LATE: grok.sydney_morning fired +0h 30m past anchor. "
        f"run_id {RUN_ID}."
    )


def test_early_by_411_seconds_adds_no_line() -> None:
    sent = ANCHOR_DT - timedelta(seconds=411)
    assert (sent - ANCHOR_DT).total_seconds() == -411
    assert sydney_morning_late_line(ANCHOR, sent, RUN_ID) is None


def test_late_line_run_id_is_the_receipt_run_id(tmp_path: Path) -> None:
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    line = sydney_morning_late_line(ANCHOR, sent, RUN_ID)
    assert line is not None and RUN_ID in line
    path, created = write_deliver_receipt(
        completions_dir=tmp_path / "completions",
        routine_id="grok.sydney_morning",
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=True,
        delivered_at=sent,
    )
    assert created is True and path is not None
    body = json.loads(path.read_text(encoding="utf-8"))
    assert body["run_id"] == RUN_ID
    assert body["sent"] is True
    assert f"run_id {body['run_id']}." in line


def test_apply_appends_exactly_one_line() -> None:
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    text = apply_sydney_morning_late_line(
        BRIEF,
        scheduled_for=ANCHOR,
        sent_at=sent,
        run_id=RUN_ID,
    )
    assert text.count(LATE_2H46) == 1
    assert text.startswith(BRIEF)
    assert text.strip().endswith(LATE_2H46)
    assert text.count("\n") == BRIEF.count("\n") + 1


def _post_pack(monkeypatch, capsys, tmp_path: Path, *, sent_at: datetime, live: bool) -> tuple[int, str, list[dict[str, str]]]:
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv(PRINCIPAL_DM_CHAT_ID_ENV, DM_CHAT)
    # Isolate the LATE line from the dead-man ping: a stub OK start does not append DEADMAN.
    monkeypatch.setenv("HEALTHCHECKS_PING_URL", "https://hc-ping.example/late-line-stub")
    monkeypatch.setattr("mm_lab_cli.deadman._http_get", lambda url, timeout: (200, "OK"))
    monkeypatch.setattr("mm_lab_cli.deliver.utcnow", lambda: sent_at)
    posted: list[dict[str, str]] = []

    class _FakeApi:
        def send_message(self, *, chat_id, text, **kwargs):
            posted.append({"chat_id": str(chat_id), "text": str(text)})
            return TelegramApiResult(
                method="sendMessage",
                ok=True,
                error_class="none",
                attempts=1,
                status_code=200,
                payload={"ok": True},
            )

        def close(self) -> None:
            return None

    deliver_module = importlib.import_module("mm_delivery.deliver")
    monkeypatch.setattr(deliver_module.TelegramClient, "from_settings", lambda *args, **kwargs: _FakeApi())
    brief = tmp_path / "brief.md"
    brief.write_text(BRIEF, encoding="utf-8")
    completions = ROOT / "ops" / "reports" / "scheduler" / "completions"
    before = {path.name for path in completions.glob("*.json")}
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
    assert "test-token" not in captured.out
    assert "test-token" not in captured.err
    assert "hc-ping.example" not in captured.out
    assert "hc-ping.example" not in captured.err
    payload_path = tmp_path / "out" / "briefs" / "2026-09-24" / "telegram-payload.json"
    assert payload_path.is_file()
    envelope = json.loads(payload_path.read_text(encoding="utf-8"))
    after = {path.name for path in completions.glob("*.json")}
    assert after == before
    return rc, str(envelope["text"]), posted


def test_live_send_appends_late_line_to_the_same_dm(tmp_path: Path, monkeypatch, capsys) -> None:
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, sent_at=sent, live=True)
    assert rc == 0
    assert text.count(LATE_2H46) == 1
    assert text.startswith(BRIEF)
    assert len(posted) == 1
    assert posted[0]["chat_id"] == DM_CHAT
    assert posted[0]["text"].count("LATE:") == 1
    assert escape_markdown_v2(LATE_2H46) in posted[0]["text"]
    assert escape_markdown_v2("Morning brief body.") in posted[0]["text"]


def test_live_send_at_exactly_thirty_minutes_has_no_late_line(tmp_path: Path, monkeypatch, capsys) -> None:
    sent = ANCHOR_DT + timedelta(minutes=30)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, sent_at=sent, live=True)
    assert rc == 0
    assert "LATE:" not in text
    assert text == BRIEF
    assert len(posted) == 1
    assert "LATE:" not in posted[0]["text"]


def test_live_send_at_thirty_one_minutes_names_zero_hours(tmp_path: Path, monkeypatch, capsys) -> None:
    sent = ANCHOR_DT + timedelta(minutes=31)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, sent_at=sent, live=True)
    assert rc == 0
    assert text.count(LATE_0H31) == 1
    assert len(posted) == 1
    assert posted[0]["text"].count("LATE:") == 1


def test_live_send_early_by_411_seconds_has_no_late_line(tmp_path: Path, monkeypatch, capsys) -> None:
    sent = ANCHOR_DT - timedelta(seconds=411)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, sent_at=sent, live=True)
    assert rc == 0
    assert "LATE:" not in text
    assert text == BRIEF
    assert len(posted) == 1
    assert "LATE:" not in posted[0]["text"]


def test_dry_run_does_not_append_a_late_line(tmp_path: Path, monkeypatch, capsys) -> None:
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    rc, text, posted = _post_pack(monkeypatch, capsys, tmp_path, sent_at=sent, live=False)
    assert rc == 0
    assert "LATE:" not in text
    assert "DEADMAN:" not in text
    assert posted == []


def test_already_delivered_sends_nothing(tmp_path: Path) -> None:
    completions = tmp_path / "completions"
    sent = datetime(2026, 9, 24, 23, 16, 50, tzinfo=UTC)
    line = sydney_morning_late_line(ANCHOR, sent, RUN_ID)
    assert line == LATE_2H46
    path, created = write_deliver_receipt(
        completions_dir=completions,
        routine_id="grok.sydney_morning",
        scheduled_anchor_ts=ANCHOR,
        run_id=RUN_ID,
        sent=True,
        delivered_at=sent,
    )
    assert created is True and path is not None
    calls: list[str] = []

    def _send() -> tuple[int, str]:
        calls.append(
            apply_sydney_morning_late_line(
                BRIEF,
                scheduled_for=ANCHOR,
                sent_at=sent,
                run_id=RUN_ID,
            )
        )
        return 0, json.dumps({"sent": True, "reason": "ok"})

    second = attempt_deliver(
        completions_dir=completions,
        routine_id="grok.sydney_morning",
        scheduled_anchor_ts=ANCHOR,
        run_id="actions-b1-later",
        send=_send,
    )
    assert second.outcome == ALREADY_DELIVERED
    assert second.telegram is False
    assert calls == []
    assert json.loads(path.read_text(encoding="utf-8"))["run_id"] == RUN_ID


def test_workflow_passes_anchor_on_the_existing_deliver_command() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    stage1_key = "\n  stage1-stamp:\n"
    brief_key = "\n  brief-and-deliver:\n"
    stage1 = text[text.index(stage1_key) : text.index(brief_key)]
    brief = text[text.index(brief_key) :]
    assert "--scheduled-for" not in stage1
    assert "LATE:" not in stage1
    assert "repository_dispatch" not in text
    command = brief[brief.index("uv run lab deliver pack") : brief.index('> "/tmp/sydney-deliver-')]
    assert "--scheduled-for" in command
    assert '--run-id "${RUN_ID}"' in command
    assert "--to-principal-dm" in command
    assert "--i-mean-it" in command
    assert "--send" not in command
    assert "steps.receipt.outputs.already_delivered != 'true'" in brief
    assert brief.index("uv run lab deliver pack") < brief.index("write_deliver_receipt")
    assert text.count("\n  stage1-stamp:\n") == 1
    assert text.count("\n  brief-and-deliver:\n") == 1
