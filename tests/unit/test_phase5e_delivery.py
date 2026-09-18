"""Phase 5e delivery: dry-run golden hash, idempotency, mock send, no live API."""

from __future__ import annotations

from pathlib import Path

import httpx

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.deliver import deliver
from mm_delivery.idempotency import DedupeStore, idempotency_key
from mm_delivery.payload import SEND_ENABLED, build_payload
from mm_delivery.rate_limit import RateLimitBudget
from mm_delivery.telegram import TELEGRAM_API_BASE, TelegramClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_MD = ROOT / "tests" / "fixtures" / "phase5e" / "desk-pack.md"
GOLDEN_JSON = ROOT / "tests" / "fixtures" / "phase5e" / "frozen_telegram_payload.json"
GOLDEN_SHA = ROOT / "tests" / "fixtures" / "phase5e" / "frozen_telegram_payload.sha256"
AS_OF = parse_utc("2026-09-18T00:00:00Z")


def _payload():
    settings = load_telegram_settings(ROOT)
    markdown = FIXTURE_MD.read_text(encoding="utf-8")
    return build_payload(markdown, desk="coord", as_of=AS_OF, settings=settings, kind="desk_pack")


def test_send_enabled_stays_false() -> None:
    assert SEND_ENABLED is False


def test_telegram_api_base_is_official_host() -> None:
    assert TELEGRAM_API_BASE == "https://api.telegram.org"


def test_dry_run_payload_golden_is_byte_stable() -> None:
    payload = _payload()
    envelope = canonical_json(payload.canonical()) + "\n"
    expected = GOLDEN_JSON.read_text(encoding="utf-8")
    assert envelope == expected
    digest = sha256_hex(envelope.encode("utf-8"))
    assert digest == GOLDEN_SHA.read_text(encoding="utf-8").strip()
    assert payload.payload_hash() == digest
    assert "TELEGRAM_BOT_TOKEN" not in envelope
    assert "bot" not in envelope.lower() or "sendMessage" in envelope
    assert payload.chat_id_env == "TELEGRAM_CHAT_ID"
    assert payload.idempotency_key == idempotency_key(
        desk="coord", as_of=AS_OF, content_hash=payload.content_hash
    )


def test_dry_run_writes_exact_bytes(tmp_path: Path) -> None:
    markdown = FIXTURE_MD.read_text(encoding="utf-8")
    first = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=False,
        completeness_pct=100.0,
        repo=ROOT,
        out_root=tmp_path,
        session_date="2026-09-18",
        now=AS_OF,
    )
    second = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=False,
        completeness_pct=100.0,
        repo=ROOT,
        out_root=tmp_path,
        session_date="2026-09-18",
        now=AS_OF,
    )
    assert first.sent is False
    assert first.reason == "no_send"
    assert first.payload_hash == second.payload_hash
    written = Path(first.written["telegram_payload"])
    assert written.read_text(encoding="utf-8") == GOLDEN_JSON.read_text(encoding="utf-8")
    sha = Path(first.written["telegram_sha256"]).read_text(encoding="utf-8").strip()
    assert sha == GOLDEN_SHA.read_text(encoding="utf-8").strip()


def test_send_without_token_fails_closed(tmp_path: Path) -> None:
    markdown = FIXTURE_MD.read_text(encoding="utf-8")
    result = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=True,
        completeness_pct=100.0,
        repo=ROOT,
        out_root=tmp_path,
        session_date="2026-09-18",
        now=parse_utc("2026-09-18T02:00:00Z"),
        environ={},
    )
    assert result.sent is False
    assert result.reason == "missing_env"
    assert result.payload_hash == _payload().payload_hash()


def test_idempotent_rerun_does_not_double_post() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        assert "telegram.test" in str(request.url)
        assert "api.telegram.org" not in str(request.url)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, timeout=2.0)
    client = TelegramClient("test-token", base_url="https://telegram.test", client=http)
    store = DedupeStore(ttl_seconds=86400)
    env = {"TELEGRAM_CHAT_ID": "111", "TELEGRAM_BOT_TOKEN": "test-token"}
    markdown = FIXTURE_MD.read_text(encoding="utf-8")
    now = parse_utc("2026-09-18T02:00:00Z")
    first = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=True,
        completeness_pct=100.0,
        repo=ROOT,
        client=client,
        dedupe=store,
        environ=env,
        now=now,
        respect_quiet_hours=True,
    )
    second = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=True,
        completeness_pct=100.0,
        repo=ROOT,
        client=client,
        dedupe=store,
        environ=env,
        now=now,
    )
    assert first.sent is True
    assert second.sent is False
    assert second.reason == "dedupe_hit"
    assert len(calls) == len(first.payload.chunks)
    http.close()


def test_rate_limit_skips_send() -> None:
    markdown = FIXTURE_MD.read_text(encoding="utf-8")
    budget = RateLimitBudget(name="telegram", max_requests_per_minute=0)
    env = {"TELEGRAM_CHAT_ID": "111", "TELEGRAM_BOT_TOKEN": "test-token"}
    client = TelegramClient("test-token", base_url="https://telegram.test")
    result = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=True,
        completeness_pct=100.0,
        repo=ROOT,
        client=client,
        environ=env,
        now=parse_utc("2026-09-18T02:00:00Z"),
        budget=budget,
        dedupe=DedupeStore(ttl_seconds=1),
    )
    assert result.sent is False
    assert result.reason == "rate_limited"
    client.close()


def test_thread_id_is_forwarded() -> None:
    settings = load_telegram_settings(ROOT)
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read()
        return httpx.Response(200, json={"ok": True, "result": {}})

    # clone route with thread
    from dataclasses import replace

    route = settings.route("coord")
    assert route is not None
    desks = dict(settings.desks)
    desks["coord"] = replace(route, thread_id=42)
    settings = replace(settings, desks=desks)
    http = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    client = TelegramClient("test-token", base_url="https://telegram.test", client=http)
    markdown = FIXTURE_MD.read_text(encoding="utf-8")
    result = deliver(
        markdown,
        desk="coord",
        as_of=AS_OF,
        send=True,
        completeness_pct=100.0,
        settings=settings,
        repo=ROOT,
        client=client,
        environ={"TELEGRAM_CHAT_ID": "111"},
        now=parse_utc("2026-09-18T02:00:00Z"),
        dedupe=DedupeStore(ttl_seconds=1),
    )
    assert result.sent is True
    assert result.payload.message_thread_id == 42
    assert b"message_thread_id" in captured["body"]
    http.close()


def test_optional_send_document_and_photo_use_mock_transport() -> None:
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(str(request.url))
        return httpx.Response(200, json={"ok": True, "result": {}})

    http = httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0)
    client = TelegramClient("test-token", base_url="https://telegram.test", client=http)
    doc = client.send_document(chat_id="1", document="file-id")
    photo = client.send_photo(chat_id="1", photo="file-id")
    assert doc.ok and photo.ok
    assert any("sendDocument" in u for u in captured)
    assert any("sendPhoto" in u for u in captured)
    http.close()


def test_config_has_no_secret_values() -> None:
    text = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN" in text
    assert "bot" in text.lower()
    for line in text.splitlines():
        if "chat_id" in line.lower() and "env" not in line.lower() and "thread" not in line.lower():
            assert ":" in line
        assert ":" + " " not in line or not line.strip().endswith(("123", "token"))
    assert "123456" not in text
    assert ":" + "ghp_" not in text
