"""Pack --to-principal-dm: same chat_id_env_override path as deliver.test.

Group/desk pack --send stays SEND_FROZEN. Live pack POST only with
--to-principal-dm --i-mean-it. Unit tests mock Telegram HTTP; live acceptance
is on-box only.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from mm_common.env import PRINCIPAL_DM_CHAT_ID_ENV
from mm_common.time import parse_utc
from mm_delivery.deliver import deliver
from mm_delivery.idempotency import DedupeStore
from mm_delivery.telegram import TelegramClient
from mm_lab_cli.cli import main
from mm_lab_cli.env_preflight import GROUP_SEND_FROZEN, SEND_FROZEN_MSG

ROOT = Path(__file__).resolve().parents[2]
PACK_MD = ROOT / "tests" / "fixtures" / "phase5e" / "desk-pack.md"
AS_OF = "2026-09-18T00:00:00Z"
DM_CHAT = "dm-only-chat"
GROUP_CHAT = "hive-group-chat"


def test_send_frozen_msg_mentions_pack_and_test() -> None:
    assert GROUP_SEND_FROZEN is True
    assert "SEND_FROZEN" in SEND_FROZEN_MSG
    assert "pack|test" in SEND_FROZEN_MSG or ("pack" in SEND_FROZEN_MSG and "test" in SEND_FROZEN_MSG)
    assert "--to-principal-dm" in SEND_FROZEN_MSG


def test_pack_send_without_to_principal_dm_stays_frozen(capsys) -> None:
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            AS_OF,
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


def test_pack_send_i_mean_it_without_to_principal_dm_stays_frozen(capsys) -> None:
    """`--i-mean-it` alone does not lift group freeze for pack."""
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            AS_OF,
            "--desk",
            "ops",
            "--send",
            "--i-mean-it",
            "--repo-root",
            str(ROOT),
        ]
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "SEND_FROZEN" in err


def test_pack_to_principal_dm_send_without_i_mean_it_refuses(capsys) -> None:
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            AS_OF,
            "--desk",
            "ops",
            "--to-principal-dm",
            "--send",
            "--repo-root",
            str(ROOT),
        ]
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "SEND_FROZEN" not in err or "to-principal-dm" in err
    assert "--i-mean-it" in err


def test_pack_to_principal_dm_dry_run_sets_chat_id_env(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            AS_OF,
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
    assert payload["to_principal_dm"] is True
    assert payload["chat_id_env"] == PRINCIPAL_DM_CHAT_ID_ENV
    assert payload["no_send"] is True
    written = tmp_path / "briefs" / "2026-09-18" / "telegram-payload.json"
    assert written.is_file()
    text = written.read_text(encoding="utf-8")
    assert PRINCIPAL_DM_CHAT_ID_ENV in text or payload["chat_id_env"] == PRINCIPAL_DM_CHAT_ID_ENV
    assert "TELEGRAM_BOT_TOKEN" not in text


def test_pack_to_principal_dm_without_env_refuses_live(tmp_path: Path, capsys) -> None:
    rc = main(
        [
            "deliver",
            "pack",
            "--from-markdown",
            str(PACK_MD),
            "--as-of",
            AS_OF,
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
        assert payload.get("to_principal_dm") is True


def test_pack_dm_deliver_posts_only_principal_dm_not_group() -> None:
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
    markdown = PACK_MD.read_text(encoding="utf-8")
    result = deliver(
        markdown,
        desk="ops",
        as_of=parse_utc(AS_OF),
        send=True,
        kind="desk_pack",
        completeness_pct=100.0,
        repo=ROOT,
        client=client,
        environ=env,
        now=parse_utc(AS_OF),
        respect_quiet_hours=False,
        dedupe=DedupeStore(ttl_seconds=1),
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV,
    )
    http.close()
    assert result.sent is True
    assert result.payload.chat_id_env == PRINCIPAL_DM_CHAT_ID_ENV
    assert result.as_public_dict()["chat_id_env"] == PRINCIPAL_DM_CHAT_ID_ENV
    assert posted
    assert all("sendMessage" in url for url in posted)


def test_pack_dm_deliver_refuses_if_dm_equals_group() -> None:
    result = deliver(
        "pack body\n",
        desk="ops",
        as_of=parse_utc(AS_OF),
        send=True,
        kind="desk_pack",
        completeness_pct=100.0,
        repo=ROOT,
        environ={
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_CHAT_ID": "same-id",
            PRINCIPAL_DM_CHAT_ID_ENV: "same-id",
        },
        now=parse_utc(AS_OF),
        respect_quiet_hours=False,
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV,
    )
    assert result.sent is False
    assert result.reason == "principal_dm_is_group"
