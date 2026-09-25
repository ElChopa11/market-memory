"""Phase 5e MarkdownV2 escape + 4096 chunking."""

from __future__ import annotations

from mm_delivery.format import TELEGRAM_MAX_MESSAGE_CHARS, chunk_markdown_v2, escape_markdown_v2


def test_escape_markdown_v2_covers_reserved_set() -> None:
    raw = r"_*[]()~`>#+-=|{}.!\\"
    escaped = escape_markdown_v2(raw)
    for ch in raw:
        if ch == "\\":
            continue
        assert f"\\{ch}" in escaped
    assert escape_markdown_v2("plain") == "plain"
    assert escape_markdown_v2("BTC 1.0") == "BTC 1\\.0"


def test_fenced_pre_block_keeps_inner_text_literal() -> None:
    raw = "UTC 2026-09-24T23:17:25+00:00\n```\nSPY 767.81  no new session since 2026-09-23\n```\n"
    escaped = escape_markdown_v2(raw)
    assert "```" in escaped
    assert "SPY 767.81  no new session since 2026-09-23" in escaped
    assert r"2026\-09\-24" in escaped
    assert r"767\.81" not in escaped


def test_short_message_is_single_unprefixed_chunk() -> None:
    chunks = chunk_markdown_v2("hello")
    assert chunks == ("hello",)


def test_long_message_is_sequenced_and_within_limit() -> None:
    body = "\n\n".join(f"paragraph {i} " + ("x" * 200) for i in range(40))
    chunks = chunk_markdown_v2(body)
    assert len(chunks) > 1
    for i, chunk in enumerate(chunks, start=1):
        assert len(chunk) <= TELEGRAM_MAX_MESSAGE_CHARS
        assert chunk.startswith("\\[")
        assert f"{i}/{len(chunks)}" in chunk.replace("\\", "")
    assert all(len(c) <= TELEGRAM_MAX_MESSAGE_CHARS for c in chunks)


def test_chunking_is_deterministic() -> None:
    text = ("alpha.\n" * 800) + ("bravo!\n" * 800)
    assert chunk_markdown_v2(text) == chunk_markdown_v2(text)
