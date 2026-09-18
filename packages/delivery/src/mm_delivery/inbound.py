"""Read-only inbound command stubs. No trading actions. No live fetch."""

from __future__ import annotations

from dataclasses import dataclass

from mm_common.naming import roster_lines

ALLOWED_COMMANDS = ("/status", "/brief", "/desk", "/idea", "/gaps", "/halt")
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
    silent: bool = False
    uid: str | None = None
    audit: str = ""

    def canonical(self) -> dict[str, str | bool]:
        return {
            "ok": self.ok,
            "command": self.command,
            "text": self.text,
            "trading": self.trading,
            "silent": self.silent,
            "uid": self.uid or "",
            "audit": self.audit,
        }


def _first_token(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    return stripped.split()[0].lower()


def handle_inbound(
    text: str,
    *,
    allowlist: tuple[str, ...] = ALLOWED_COMMANDS,
    uid: str | None = None,
    allow_uids: tuple[str, ...] | None = None,
    audit_sink: list[dict[str, str]] | None = None,
) -> InboundReply:
    """Allowlisted read-only replies. Unknown uid → silent drop + audit. No trading."""
    cmd = _first_token(text)
    if allow_uids is not None:
        if not uid or str(uid) not in set(allow_uids):
            row = {
                "uid": str(uid or ""),
                "command": cmd or "(empty)",
                "action": "silent_drop",
                "reason": "unknown_uid",
            }
            if audit_sink is not None:
                audit_sink.append(row)
            return InboundReply(
                ok=False,
                command=cmd or "(empty)",
                text="",
                silent=True,
                uid=uid,
                audit="unknown uid silent drop",
            )
    if cmd in TRADING_COMMANDS:
        reply = InboundReply(
            ok=False,
            command=cmd,
            text="refused: trading actions are not allowed on inbound Telegram",
            trading=True,
            uid=uid,
            audit="trading_refused",
        )
        if audit_sink is not None:
            audit_sink.append({"uid": str(uid or ""), "command": cmd, "action": "refuse", "reason": "trading"})
        return reply
    allowed = tuple(a.lower() for a in allowlist)
    if cmd not in allowed:
        return InboundReply(
            ok=False,
            command=cmd or "(empty)",
            text="refused: command not on allowlist (/status /desk /brief /idea /gaps /halt)",
            uid=uid,
            audit="not_allowlisted",
        )
    replies = {
        "/status": "lab status: live trading HARD-GATED; delivery default is --no-send",
        "/brief": "lab brief: last OFFICIAL_BRIEF is on disk under briefs/; inbound does not fetch markets",
        "/desk": "desk: "
        + "; ".join(roster_lines())
        + ". Coord is orchestration only. Use `lab desk run --no-send`; inbound does not run desks or send orders",
        "/idea": "idea: last STATE_CARD permission is read-only; inbound never trades",
        "/gaps": "gaps: named unknowns from the last playbook run; never invented",
        "/halt": "halt: read-only; check config/halt.flag — inbound cannot place or cancel orders",
    }
    return InboundReply(ok=True, command=cmd, text=replies.get(cmd, "ok"), uid=uid, audit="allowlisted")
