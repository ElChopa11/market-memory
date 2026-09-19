"""lab env preflight — full found/missing state. Never print values."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

from mm_common.env import (
    BOT_TOKEN_ENV,
    CHAT_ID_ENV,
    PURPOSE_BRIEF,
    PURPOSE_CHECKLIST,
    PURPOSE_DELIVER,
    STATE_FOUND,
    STATE_MISSING,
    PreflightReport,
    format_preflight_lines,
    prepare_cli_env,
    redact_env_values,
)
from mm_delivery.config import repo_root
from mm_delivery.telegram import TelegramClient, redact_telegram

SEND_FROZEN_MSG = (
    "lab: real Telegram send is frozen until Principal step 5 (DM-only). Use --no-send."
)


def add_env_parser(sub) -> None:
    env_p = sub.add_parser(
        "env",
        help="delivery-path env preflight (full found/missing state; never prints values)",
    )
    env_sub = env_p.add_subparsers(dest="env_cmd")
    pre = env_sub.add_parser(
        "preflight",
        help="print every declared var/service found or missing; exit 2 if any required is missing",
    )
    pre.add_argument("--repo-root", type=Path, default=Path("."))


def dispatch_env(args: Namespace) -> int:
    cmd = getattr(args, "env_cmd", None)
    if cmd in {None, "preflight"}:
        return run_preflight_command(Path(getattr(args, "repo_root", Path("."))).resolve())
    print("usage: lab env preflight", file=sys.stderr)
    return 2


def live_get_chat_probe(environ) -> tuple[str, str]:
    """Operator-box getChat. Pytest unsets the token so this is not reached in CI."""
    token = (environ.get(BOT_TOKEN_ENV) or "").strip()
    chat_id = (environ.get(CHAT_ID_ENV) or "").strip()
    try:
        with TelegramClient(token) as api:
            result = api.get_chat(chat_id)
    except Exception as exc:
        name = redact_telegram(type(exc).__name__, token)
        return (
            STATE_MISSING,
            f"getChat failed ({name}); id dead or drifted; fail loud; converting Hive to a "
            "supergroup or enabling topics changes the id to a -100... form",
        )
    if not result.ok:
        return (
            STATE_MISSING,
            "getChat did not resolve TELEGRAM_CHAT_ID (id dead); fail loud; converting Hive "
            "to a supergroup or enabling topics changes the id to a -100... form",
        )
    payload = result.payload or {}
    inner = payload.get("result") if isinstance(payload, dict) else None
    resolved = inner.get("id") if isinstance(inner, dict) else None
    if resolved is not None and str(resolved) != str(chat_id):
        return (
            STATE_MISSING,
            "getChat resolved a different id than TELEGRAM_CHAT_ID "
            "(id dead / possible -100... supergroup conversion); fail loud",
        )
    return STATE_FOUND, "getChat verify each run; configured group id resolved (id not printed)"


def run_preflight_command(root: Path) -> int:
    _merged, report = prepare_cli_env(
        purpose=PURPOSE_CHECKLIST, send=False, apply=True, get_chat=live_get_chat_probe
    )
    emit_preflight(report, root=root)
    return 0 if report.ok else 2


def prepare_brief_or_deliver(*, purpose: str, send: bool = False) -> PreflightReport:
    """Load delivery env file into this CLI process, print full state, return report."""
    _merged, report = prepare_cli_env(
        purpose=purpose, send=send, apply=True, get_chat=live_get_chat_probe
    )
    emit_preflight(report)
    return report


def prepare_deliver(*, send: bool) -> PreflightReport:
    return prepare_brief_or_deliver(purpose=PURPOSE_DELIVER, send=send)


def prepare_brief() -> PreflightReport:
    return prepare_brief_or_deliver(purpose=PURPOSE_BRIEF, send=False)


def emit_preflight(report: PreflightReport, *, root: Path | None = None) -> None:
    if root is not None:
        example = repo_root(root) / ".env.example"
        if example.is_file():
            print(
                redact_env_values(
                    f"env preflight: declared set from {example} + delivery-only Telegram file"
                ),
                file=sys.stderr,
            )
    for line in format_preflight_lines(report):
        print(line, file=sys.stderr)
