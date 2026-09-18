"""Phase 6c Telegram fan-out, inbound uid drop, retry_after, coord mirror."""

from __future__ import annotations

from pathlib import Path

import httpx

from mm_common.http import http_post
from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.fanout import coord_mirror_text, fanout_desk
from mm_delivery.inbound import handle_inbound
from mm_delivery.telegram import TelegramClient

ROOT = Path(__file__).resolve().parents[2]
AS_OF = parse_utc("2026-09-18T00:00:00Z")


def test_coord_mirror_keeps_content_hash() -> None:
    settings = load_telegram_settings(ROOT)
    markdown = "desk note BTC (observed)"
    result = fanout_desk(
        markdown,
        desk="research",
        as_of=AS_OF,
        send=False,
        completeness_pct=100.0,
        repo=ROOT,
        settings=settings,
    )
    assert result.coord_mirror is not None
    assert result.coord_mirror.payload.content_hash == result.primary.payload.content_hash
    assert result.content_hash == result.primary.payload.content_hash
    assert "ops mirror" in result.coord_mirror.payload.text
    assert result.primary.payload.text == markdown


def test_unknown_uid_silent_drop_audit() -> None:
    audit: list[dict[str, str]] = []
    reply = handle_inbound("/status", uid="999", allow_uids=("1",), audit_sink=audit)
    assert reply.ok is False
    assert reply.silent is True
    assert reply.text == ""
    assert audit and audit[0]["action"] == "silent_drop"


def test_inbound_new_allowlist_is_read_only() -> None:
    for cmd in ("/idea", "/gaps", "/halt", "/status"):
        reply = handle_inbound(cmd)
        assert reply.ok is True
        assert reply.trading is False


def test_retry_after_is_honoured() -> None:
    sleeps: list[float] = []
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "7"}, text="slow")
        return httpx.Response(200, json={"ok": True})

    http = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    result = http_post(http, "https://telegram.test/x", json_body={"a": 1}, sleep=sleeps.append)
    assert result.ok is True
    assert sleeps and sleeps[0] >= 7
    http.close()


def test_exhausted_retries_write_failed_sink() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"ok": False, "description": "down"})

    http = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    client = TelegramClient("test-token", base_url="https://telegram.test", client=http, max_attempts=2)
    sink: list[dict] = []
    from mm_delivery.deliver import deliver
    from mm_delivery.idempotency import DedupeStore

    result = deliver(
        "ping",
        desk="ops",
        as_of=AS_OF,
        send=True,
        completeness_pct=100.0,
        repo=ROOT,
        client=client,
        environ={"TELEGRAM_CHAT_ID": "1", "TELEGRAM_BOT_TOKEN": "test-token"},
        now=parse_utc("2026-09-18T02:00:00Z"),
        dedupe=DedupeStore(ttl_seconds=1),
        failed_sink=sink,
    )
    assert result.sent is False
    assert sink and sink[0]["status"] == "FAILED"
    assert "never silent drop" in " ".join(sink[0]["notes"]).lower() or "escalation" in sink[0]["escalation"]
    http.close()


def test_mirror_helper_does_not_re_render() -> None:
    body = "alpha"
    mirrored = coord_mirror_text(body, content_hash="abc")
    assert mirrored.startswith(body)
    assert "abc" in mirrored
