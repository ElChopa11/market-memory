"""Phase 5e inbound allowlist stubs: read-only, no trading."""

from __future__ import annotations

from mm_delivery.inbound import handle_inbound


def test_allowlisted_commands_are_read_only() -> None:
    for cmd in ("/status", "/brief", "/desk"):
        reply = handle_inbound(cmd)
        assert reply.ok is True
        assert reply.trading is False
        assert "HARD-GATED" in reply.text or "lab" in reply.text.lower() or "stub" in reply.text


def test_trading_commands_are_refused() -> None:
    for cmd in ("/buy BTC", "/sell", "/order", "/trade", "/flatten"):
        reply = handle_inbound(cmd)
        assert reply.ok is False
        assert reply.trading is True
        assert "refused" in reply.text


def test_unknown_command_is_refused() -> None:
    reply = handle_inbound("/launch")
    assert reply.ok is False
    assert reply.trading is False
    assert "allowlist" in reply.text
