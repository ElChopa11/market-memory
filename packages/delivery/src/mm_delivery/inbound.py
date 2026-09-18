"""Read-only inbound command stubs. No trading actions. No live fetch."""

from __future__ import annotations

from dataclasses import dataclass

ALLOWED_COMMANDS = ("/status", "/brief", "/desk")
TRADING_COMMANDS = (
    "/buy",
    "/sell",
    "/order",
    "/trade",
    "/flatten",
    "/size",
    "/close",
    "/long",
    "/short",
    "/execute",
)


@dataclass(frozen=True)
class InboundReply:
    ok: bool
    command: str
    text: str
    trading: bool = False

    def canonical(self) -> dict[str, str | bool]:
        return {
            "ok": self.ok,
            "command": self.command,
            "text": self.text,
            "trading": self.trading,
        }


def _first_token(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    return stripped.split()[0].lower()


def handle_inbound(text: str, *, allowlist: tuple[str, ...] = ALLOWED_COMMANDS) -> InboundReply:
    """Allowlisted read-only replies. Trading verbs are refused. No network."""
    cmd = _first_token(text)
    if cmd in TRADING_COMMANDS:
        return InboundReply(
            ok=False,
            command=cmd,
            text="refused: trading actions are not allowed on inbound Telegram",
            trading=True,
        )
    allowed = tuple(a.lower() for a in allowlist)
    if cmd not in allowed:
        return InboundReply(
            ok=False,
            command=cmd or "(empty)",
            text="refused: command not on allowlist (/status /brief /desk)",
        )
    if cmd == "/status":
        return InboundReply(
            ok=True,
            command=cmd,
            text="lab status (stub): live trading HARD-GATED; delivery default is --no-send",
        )
    if cmd == "/brief":
        return InboundReply(
            ok=True,
            command=cmd,
            text="brief stub: use `lab brief preopen --no-db`; inbound does not fetch markets",
        )
    return InboundReply(
        ok=True,
        command=cmd,
        text="desk stub: use `lab desk run --no-send`; inbound does not run desks or send orders",
    )
