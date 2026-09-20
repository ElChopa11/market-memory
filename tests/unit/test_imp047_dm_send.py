"""IMP-047 Hybrid Step 5a: DM-only live path. Group send stays SEND_FROZEN.

Unit tests mock Telegram HTTP. Live acceptance is on-box only (cloud VM has
no delivery token). Do not treat these mocks as Principal acceptance.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_common.time import parse_utc
from mm_delivery.config import chat_id_from_env, load_telegram_settings, principal_dm_chat_id_from_env
from mm_delivery.deliver import deliver
from mm_delivery.idempotency import DedupeStore
from mm_delivery.telegram import TelegramClient
from mm_desks.llm.grounding import GroundingError, assert_no_backfill
from mm_lab_cli.cli import main
from mm_lab_cli.env_preflight import GROUP_SEND_FROZEN, SEND_FROZEN_MSG

ROOT = Path(__file__).resolve().parents[2]
AS_OF = parse_utc("2026-09-18T02:00:00Z")
DM_CHAT = "dm-only-chat"
GROUP_CHAT = "hive-group-chat"


def test_group_send_stays_frozen() -> None:
    assert GROUP_SEND_FROZEN is True
    assert "SEND_FROZEN" in SEND_FROZEN_MSG
    assert "Hive group stays frozen" in SEND_FROZEN_MSG
    assert "--to-principal-dm" in SEND_FROZEN_MSG


def test_lab_deliver_group_send_is_frozen(capsys) -> None:
    """`--i-mean-it` without `--to-principal-dm` still hits SEND_FROZEN."""
    rc = main(["deliver", "test", "--desk", "ops", "--send", "--i-mean-it", "--repo-root", str(ROOT)])
    err = capsys.readouterr().err
    assert rc == 2
    assert "SEND_FROZEN" in err
    assert "Hive group stays frozen" in err


def test_lab_deliver_pack_send_is_frozen(capsys) -> None:
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(ROOT / "tests" / "fixtures" / "phase5e" / "desk-pack.md"),
            "--as-of",
            "2026-09-18T00:00:00Z",
            "--desk",
            "ops",
            "--send",
            "--repo-root",
            str(ROOT),
        ]
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "SEND_FROZEN" in err


def test_dm_chat_id_never_falls_back_to_group() -> None:
    settings = load_telegram_settings(ROOT)
    env = {PRINCIPAL_DM_CHAT_ID_ENV: DM_CHAT, "TELEGRAM_CHAT_ID": GROUP_CHAT}
    assert principal_dm_chat_id_from_env(env) == DM_CHAT
    assert chat_id_from_env("ops", settings, env) == GROUP_CHAT
    assert principal_dm_chat_id_from_env({"TELEGRAM_CHAT_ID": GROUP_CHAT}) is None


def test_dm_send_posts_only_principal_dm_not_group() -> None:
    posted: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        posted.append(str(request.url))
        assert "telegram.test" in str(request.url)
        assert "api.telegram.org" not in str(request.url)
        body = json.loads(request.content.decode("utf-8"))
        chat_id = str(body.get("chat_id") or "")
        assert chat_id == DM_CHAT
        assert chat_id != GROUP_CHAT
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    http = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    client = TelegramClient("test-token", base_url="https://telegram.test", client=http)
    env = {
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_CHAT_ID": GROUP_CHAT,
        PRINCIPAL_DM_CHAT_ID_ENV: DM_CHAT,
    }
    result = deliver(
        "delivery test ping\nsource: lab.deliver.test\n",
        desk="ops",
        as_of=AS_OF,
        send=True,
        kind="test",
        completeness_pct=100.0,
        repo=ROOT,
        client=client,
        environ=env,
        now=AS_OF,
        respect_quiet_hours=False,
        dedupe=DedupeStore(ttl_seconds=1),
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV,
    )
    http.close()
    assert result.sent is True
    assert result.payload.chat_id_env == PRINCIPAL_DM_CHAT_ID_ENV
    assert result.as_public_dict()["chat_id_env"] == PRINCIPAL_DM_CHAT_ID_ENV
    assert result.as_public_dict()["source"] == "lab.deliver"
    assert posted
    assert all("sendMessage" in url for url in posted)


def test_dm_send_refuses_if_principal_dm_missing() -> None:
    result = deliver(
        "delivery test ping\n",
        desk="ops",
        as_of=AS_OF,
        send=True,
        kind="test",
        completeness_pct=100.0,
        repo=ROOT,
        environ={"TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHAT_ID": GROUP_CHAT},
        now=AS_OF,
        respect_quiet_hours=False,
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV,
    )
    assert result.sent is False
    assert result.reason == "missing_principal_dm"
    assert PRINCIPAL_DM_CHAT_ID_ENV in " ".join(result.notes)
    assert "never falls back" in " ".join(result.notes)


def test_dm_send_refuses_if_dm_equals_group() -> None:
    result = deliver(
        "delivery test ping\n",
        desk="ops",
        as_of=AS_OF,
        send=True,
        kind="test",
        completeness_pct=100.0,
        repo=ROOT,
        environ={
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_CHAT_ID": "same-id",
            PRINCIPAL_DM_CHAT_ID_ENV: "same-id",
        },
        now=AS_OF,
        respect_quiet_hours=False,
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV,
    )
    assert result.sent is False
    assert result.reason == "principal_dm_is_group"


def test_lab_deliver_test_to_principal_dm_without_env_refuses(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "test",
            "--desk",
            "ops",
            "--to-principal-dm",
            "--i-mean-it",
            "--ignore-quiet-hours",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 2
    blob = captured.out + captured.err
    assert "SEND_FROZEN" not in captured.err or "to-principal-dm" in captured.err
    assert PRINCIPAL_DM_CHAT_ID_ENV in blob or "missing" in blob.lower() or "preflight" in captured.err.lower()
    payload = json.loads(captured.out) if captured.out.strip().startswith("{") else {}
    if payload:
        assert payload.get("sent") is False
        assert payload.get("chat_id_env") == PRINCIPAL_DM_CHAT_ID_ENV


def test_lab_deliver_test_to_principal_dm_dry_run_envelope(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "test",
            "--desk",
            "ops",
            "--to-principal-dm",
            "--no-send",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
        ]
    )
    out = capsys.readouterr()
    assert rc == 0
    payload = json.loads(out.out)
    assert payload["sent"] is False
    assert payload["test"] is True
    assert payload["to_principal_dm"] is True
    assert payload["chat_id_env"] == PRINCIPAL_DM_CHAT_ID_ENV
    assert payload["source"] == "lab.deliver"
    written = tmp_path / "briefs" / payload["as_of"][:10] / "telegram-payload.json"
    text = written.read_text(encoding="utf-8")
    assert "source: lab.deliver.test" in text
    assert "as_of_knowledge:" in text
    assert "provenance:" in text
    assert PRINCIPAL_DM_CHAT_ID_ENV in text
    assert "TELEGRAM_BOT_TOKEN" not in text
    assert DM_CHAT not in text
    assert "yield" not in text.lower()
    assert "10y" not in text.lower()


def test_lab_deliver_test_to_principal_dm_writes_completion_row(tmp_path: Path, capsys) -> None:
    dest = tmp_path / "completions"
    rc = main(
        [
            "deliver",
            "test",
            "--desk",
            "ops",
            "--to-principal-dm",
            "--no-send",
            "--repo-root",
            str(ROOT),
            "--out",
            str(tmp_path),
            "--routine-id",
            "grok.weekly_investment_review",
            "--as-of",
            "2026-09-18T07:00:00Z",
            "--run-id",
            "hive-weekly-dm-test",
            "--completions-dir",
            str(dest),
        ]
    )
    capsys.readouterr()
    assert rc == 0
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(dest.glob("*.json"))]
    assert any(row["routine_id"] == "grok.weekly_investment_review" for row in rows)
    hit = next(row for row in rows if row["run_id"] == "hive-weekly-dm-test")
    assert hit["exit_status"] == 0
    assert hit["source"] == "lab.deliver"


def test_fred_unavailable_grounding_is_failure_not_degraded_publish() -> None:
    """FRED unavailable + rates figure in body is a logged grounding failure.

    Live acceptance (no Telegram message) is on-box. This unit test does not
    POST and must not be cited as live acceptance.
    """
    try:
        assert_no_backfill(
            "US10Y yield is 4.94",
            missing_feeds=("fred",),
            gaps=("polygon",),
        )
        raise AssertionError("rates figure with FRED unavailable must fail")
    except GroundingError as exc:
        assert "NO BACKFILL" in str(exc)
        assert "FRED" in str(exc)


def test_no_weekly_authoring_cli() -> None:
    cli_src = (ROOT / "apps" / "lab-cli" / "src" / "mm_lab_cli" / "cli.py").read_text(encoding="utf-8")
    assert 'add_parser("weekly' not in cli_src
    assert "weekly-review" not in cli_src
    assert "Weekly Investment Review" not in cli_src
