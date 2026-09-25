"""lab deliver — Phase 5e Telegram delivery. Dry-run default. No live API in pytest."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path

from mm_common.env import CHAT_ID_ENV, PRINCIPAL_DM_CHAT_ID_ENV
from mm_common.naming import require_publishing_desk, require_route_slug, route_slugs_help
from mm_common.time import as_utc, parse_utc, utcnow
from mm_delivery.deliver import deliver
from mm_delivery.inbound import handle_inbound
from mm_delivery.payload import SEND_ENABLED
from mm_desks.orchestrator import PIPELINE, run_from_fixture
from mm_lab_cli.completion import add_completion_args, fired_at_from_args, stamp_cli_fire
from mm_lab_cli.env_preflight import SEND_FROZEN_MSG, prepare_deliver


def add_deliver_parser(sub) -> None:
    deliver_p = sub.add_parser("deliver", help="deliver a desk pack (default --no-send; Telegram Bot API)")
    deliver_sub = deliver_p.add_subparsers(dest="deliver_cmd")

    pack_p = deliver_sub.add_parser("pack", help="build Telegram payload from an Ops pack or markdown")
    _add_pack_args(pack_p)
    _add_principal_dm_args(pack_p, subject="pack")
    _add_scheduled_for_arg(pack_p)

    test_p = deliver_sub.add_parser(
        "test",
        help="manual real send of a one-line ping (operator-only; pytest never hits live API)",
    )
    test_p.add_argument("--desk", default="ops", help=f"desk slug (route + TELEGRAM_CHAT_ID[_DESK]); {route_slugs_help()}")
    test_p.add_argument("--repo-root", type=Path, default=Path("."))
    test_p.add_argument("--out", type=Path, help="write payload under briefs/ (default: repo root)")
    test_p.add_argument("--no-send", action="store_true", help="dry-run (default); write payload under briefs/")
    test_p.add_argument("--send", action="store_true", help="gated live send (requires --i-mean-it)")
    test_p.add_argument("--ignore-quiet-hours", action="store_true")
    _add_principal_dm_args(test_p, subject="test ping")
    test_p.add_argument("--as-of", help="UTC fire time for the completion stamp (catalog local_time + weekday)")
    add_completion_args(test_p)

    inbound_p = deliver_sub.add_parser("inbound", help="read-only inbound stub (/status /brief /desk /idea /gaps /halt)")
    inbound_p.add_argument("text", help="inbound message text")
    inbound_p.add_argument("--uid", help="telegram user id (unknown uid is a silent drop)")

    fan_p = deliver_sub.add_parser("fanout", help="per-desk deliver + Ops mirror (default --no-send)")
    _add_pack_args(fan_p)

    watch_p = deliver_sub.add_parser(
        "watchlist",
        help="Ops-owned fan-out of a Research watchlist scan (default --no-send)",
    )
    watch_p.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON used by lab watchlist scan")
    watch_p.add_argument("--no-send", action="store_true", help="dry-run (default)")
    watch_p.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    watch_p.add_argument("--out", type=Path, help="write watchlist artifacts + telegram payload")
    watch_p.add_argument("--repo-root", type=Path, default=Path("."))
    watch_p.add_argument("--no-db", action="store_true")
    watch_p.add_argument("--ignore-quiet-hours", action="store_true")
    add_completion_args(watch_p)

    list_p = deliver_sub.add_parser(
        "listings",
        help="Ops-owned fan-out of a Research listings / IPO screen (default --no-send)",
    )
    list_p.add_argument("--fixture", type=Path, required=True, help="frozen-day JSON used by lab listings scan")
    list_p.add_argument("--no-send", action="store_true", help="dry-run (default)")
    list_p.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    list_p.add_argument("--out", type=Path, help="write listings artifacts + telegram payload")
    list_p.add_argument("--repo-root", type=Path, default=Path("."))
    list_p.add_argument("--no-db", action="store_true")
    list_p.add_argument("--ignore-quiet-hours", action="store_true")
    add_completion_args(list_p)

    score_p = deliver_sub.add_parser(
        "scorecard",
        help="Ops-owned fan-out of a Quant pack scorecard (default --no-send)",
    )
    score_p.add_argument("--fixture", type=Path, required=True, help="frozen pack JSON used by lab scorecard compare")
    score_p.add_argument("--no-send", action="store_true", help="dry-run (default)")
    score_p.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    score_p.add_argument("--out", type=Path, help="write scorecard artifacts + telegram payload")
    score_p.add_argument("--repo-root", type=Path, default=Path("."))
    score_p.add_argument("--no-db", action="store_true")
    score_p.add_argument("--ignore-quiet-hours", action="store_true")
    add_completion_args(score_p)

    decay_p = deliver_sub.add_parser(
        "decay",
        help="Ops-owned fan-out of a Quant prompt-hash decay watch (default --no-send)",
    )
    decay_p.add_argument("--fixture", type=Path, required=True, help="frozen JSON used by lab decay watch")
    decay_p.add_argument("--no-send", action="store_true", help="dry-run (default)")
    decay_p.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    decay_p.add_argument("--out", type=Path, help="write decay artifacts + telegram payload")
    decay_p.add_argument("--repo-root", type=Path, default=Path("."))
    decay_p.add_argument("--no-db", action="store_true")
    decay_p.add_argument("--ignore-quiet-hours", action="store_true")
    add_completion_args(decay_p)

    _add_pack_args(deliver_p)
    _add_principal_dm_args(deliver_p, subject="pack")
    _add_scheduled_for_arg(deliver_p)


def _add_pack_args(parser) -> None:
    parser.add_argument("--desk", default="ops", help=f"desk slug to route (default ops; {route_slugs_help()})")
    parser.add_argument("--fixture", type=Path, help="frozen-day fixture; runs desk pipeline then delivers pack")
    parser.add_argument("--from-markdown", type=Path, help="deliver this markdown file instead of a fixture pack")
    parser.add_argument("--as-of", help="UTC as_of_knowledge (required with --from-markdown)")
    parser.add_argument("--no-send", action="store_true", help="dry-run (default)")
    parser.add_argument("--send", action="store_true", help="gated live send (requires TELEGRAM_BOT_TOKEN)")
    parser.add_argument("--out", type=Path, help="write exact payload under briefs/YYYY-MM-DD/")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--no-db", action="store_true")
    parser.add_argument("--ignore-quiet-hours", action="store_true")
    add_completion_args(parser)


def _add_scheduled_for_arg(parser) -> None:
    parser.add_argument(
        "--scheduled-for",
        default="",
        help=(
            "UTC catalog anchor for this Principal DM. On an actual "
            "--to-principal-dm --i-mean-it send, append one LATE line to that "
            "same message when send time is more than 30 minutes after the "
            "anchor. The line's run_id is --run-id (the deliver-receipt id)."
        ),
    )


def _add_principal_dm_args(parser, *, subject: str) -> None:
    parser.add_argument(
        "--i-mean-it",
        action="store_true",
        help="required for a live POST to TELEGRAM_CHAT_ID_PRINCIPAL_DM; without it, writes payload only",
    )
    parser.add_argument(
        "--to-principal-dm",
        action="store_true",
        help=f"route this {subject} to TELEGRAM_CHAT_ID_PRINCIPAL_DM only (never TELEGRAM_CHAT_ID group)",
    )


def _dm_route_cmd(cmd: str | None) -> bool:
    """Pack (incl. bare `lab deliver`) and test share the principal-DM route; fanout does not."""
    return cmd in {None, "pack", "test"}


def dispatch_deliver(args: Namespace) -> int:
    cmd = getattr(args, "deliver_cmd", None)
    if cmd == "inbound":
        uid = getattr(args, "uid", None)
        allow_uids = None
        if uid is not None:
            # Explicit uid without allowlist → treat as unknown unless it matches itself via env later.
            allow_uids = ()
        reply = handle_inbound(str(args.text), uid=uid, allow_uids=allow_uids if uid else None)
        print(json.dumps(reply.canonical(), sort_keys=True))
        return 0 if reply.ok or reply.silent else 2
    fired_at = fired_at_from_args(args)
    rc = 2
    payload_path = None
    try:
        rc, payload_path = _dispatch_deliver_body(args, cmd)
    except Exception as exc:
        print(json.dumps({"error": exc.__class__.__name__, "detail": str(exc)}), file=sys.stderr)
        rc = 2
    finally:
        stamp_cli_fire(
            args,
            exit_status=rc,
            payload_path=payload_path,
            deliver_cmd=cmd if cmd not in {None, "pack", "fanout", "test"} else None,
            cli=f"lab deliver {cmd or 'pack'}",
            fired_at=fired_at,
            source="lab.deliver",
        )
    return rc


def _dispatch_deliver_body(args: Namespace, cmd: str | None) -> tuple[int, str | None]:
    send = _want_send(args)
    if send is None:
        return 2, None
    to_dm = _dm_route_cmd(cmd) and bool(getattr(args, "to_principal_dm", False))
    live_confirm = bool(getattr(args, "i_mean_it", False))
    # test: --i-mean-it alone is live intent; pack: --send or --i-mean-it
    group_intent = bool(send) or live_confirm
    group_live = group_intent and not to_dm
    if group_live:
        print(SEND_FROZEN_MSG, file=sys.stderr)
        prepare_deliver(send=False)
        return 2, None
    if to_dm and bool(send) and not live_confirm:
        label = "test" if cmd == "test" else "pack"
        print(
            f"lab deliver {label}: --to-principal-dm live POST requires --i-mean-it",
            file=sys.stderr,
        )
        prepare_deliver(send=False)
        return 2, None
    report = prepare_deliver(send=False)
    # Actions Sydney brief leaves TELEGRAM_CHAT_ID unset (DM-only second bot).
    # Group-route MISSING must not block --to-principal-dm live; deliver() still
    # requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID_PRINCIPAL_DM. Other preflight
    # errors still strip --i-mean-it (no degraded publish).
    dm_preflight_blocks = bool(to_dm and live_confirm and _dm_live_preflight_blocks(report))
    if cmd == "fanout":
        from mm_delivery.fanout import fanout_desk

        loaded = _load_source(args, Path(args.repo_root).resolve(), str(getattr(args, "desk", None) or "ops"))
        if loaded is None:
            return 2, None
        markdown, as_of, completeness, session_date, extra = loaded
        result = fanout_desk(
            markdown,
            desk=str(getattr(args, "desk", None) or "ops"),
            as_of=as_of,
            send=False,
            completeness_pct=completeness,
            repo=Path(args.repo_root).resolve(),
            out_root=Path(args.out).resolve() if getattr(args, "out", None) else Path(args.repo_root).resolve(),
        )
        payload = result.as_public_dict()
        payload.update(extra)
        print(json.dumps(payload, sort_keys=True, indent=2))
        return (2 if not report.ok else 0), _payload_path(payload)
    if cmd == "watchlist":
        rc = _cmd_watchlist(args)
        return (2 if not report.ok else rc), None
    if cmd == "listings":
        rc = _cmd_listings(args)
        return (2 if not report.ok else rc), None
    if cmd == "scorecard":
        rc = _cmd_scorecard(args)
        return (2 if not report.ok else rc), None
    if cmd == "decay":
        rc = _cmd_decay(args)
        return (2 if not report.ok else rc), None
    if cmd == "test":
        if dm_preflight_blocks:
            print(
                "lab deliver test: preflight FAIL; no live DM POST (not degraded publish)",
                file=sys.stderr,
            )
            args.i_mean_it = False
        elif to_dm and live_confirm and not report.ok and CHAT_ID_ENV in report.error_names:
            print(
                "lab deliver test: TELEGRAM_CHAT_ID unset OK for --to-principal-dm "
                "(DM-only; GROUP SEND_FROZEN)",
                file=sys.stderr,
            )
        rc, path = _cmd_test(args)
        # DM-only live may proceed with group chat unset; other missing requireds still fail.
        exit_ok = report.ok or (to_dm and not dm_preflight_blocks and set(report.error_names) <= {CHAT_ID_ENV})
        return (2 if not exit_ok else rc), path
    if cmd in {None, "pack"}:
        if dm_preflight_blocks:
            print(
                "lab deliver pack: preflight FAIL; no live DM POST (not degraded publish)",
                file=sys.stderr,
            )
            args.i_mean_it = False
        elif to_dm and live_confirm and not report.ok and CHAT_ID_ENV in report.error_names:
            print(
                "lab deliver pack: TELEGRAM_CHAT_ID unset OK for --to-principal-dm "
                "(DM-only; GROUP SEND_FROZEN)",
                file=sys.stderr,
            )
        rc, path = _cmd_pack(args)
        exit_ok = report.ok or (to_dm and not dm_preflight_blocks and set(report.error_names) <= {CHAT_ID_ENV})
        return (2 if not exit_ok else rc), path
    print("usage: lab deliver pack|fanout|watchlist|listings|scorecard|decay|test|inbound", file=sys.stderr)
    return 2, None


def _dm_live_preflight_blocks(report) -> bool:
    """True when preflight errors (other than unset group chat) block DM live POST."""
    if report.ok:
        return False
    return any(name != CHAT_ID_ENV for name in report.error_names)


def _payload_path(payload: dict) -> str | None:
    written = payload.get("written") if isinstance(payload, dict) else None
    if isinstance(written, dict):
        for key in ("json", "payload", "telegram-payload.json"):
            if written.get(key):
                return str(written[key])
        for value in written.values():
            if value:
                return str(value)
    return None


_LATE_AFTER = timedelta(minutes=30)
_SYDNEY_MORNING = "grok.sydney_morning"


def sydney_morning_late_line(
    scheduled_for: str | datetime | None,
    sent_at: datetime,
    run_id: str | None,
) -> str | None:
    """One LATE line when a Principal DM send is more than 30 minutes after the anchor.

    Delta is send-time UTC minus ``scheduled_for``. Exactly 30 minutes, any
    smaller delta, and an early (negative) delta return None. Hours are whole
    hours. Remaining minutes are floored. ``run_id`` is the deliver-receipt id.
    """
    raw_anchor = scheduled_for.strip() if isinstance(scheduled_for, str) else scheduled_for
    rid = str(run_id or "").strip()
    if not raw_anchor or not rid:
        return None
    anchor = as_utc(raw_anchor) if isinstance(raw_anchor, datetime) else parse_utc(str(raw_anchor))
    sent = as_utc(sent_at)
    delta_seconds = (sent - anchor).total_seconds()
    if delta_seconds <= _LATE_AFTER.total_seconds():
        return None
    whole_minutes = int(delta_seconds // 60)
    hours, minutes = divmod(whole_minutes, 60)
    return f"LATE: {_SYDNEY_MORNING} fired +{hours}h {minutes}m past anchor. run_id {rid}."


def apply_sydney_morning_late_line(
    markdown: str,
    *,
    scheduled_for: str | datetime | None,
    sent_at: datetime,
    run_id: str | None,
) -> str:
    """Append the LATE line once. The same markdown when this send is not late."""
    try:
        line = sydney_morning_late_line(scheduled_for, sent_at, run_id)
    except ValueError:
        return markdown
    if not line:
        return markdown
    if markdown.endswith("\n"):
        return f"{markdown}{line}\n"
    if markdown:
        return f"{markdown}\n{line}\n"
    return f"{line}\n"


def _want_send(args: Namespace) -> bool | None:
    send = bool(getattr(args, "send", False))
    no_send = bool(getattr(args, "no_send", False))
    if send and no_send:
        print("lab deliver: use --send or --no-send, not both", file=sys.stderr)
        return None
    return send


def _cmd_pack(args: Namespace) -> tuple[int, str | None]:
    send = _want_send(args)
    if send is None:
        return 2, None
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2, None
    root = Path(args.repo_root).resolve()
    desk = str(getattr(args, "desk", None) or "ops")
    loaded = _load_source(args, root, desk)
    if loaded is None:
        return 2, None
    markdown, as_of, completeness, session_date, extra = loaded
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    to_dm = bool(getattr(args, "to_principal_dm", False))
    # Match lab deliver test: live POST only when --to-principal-dm and --i-mean-it.
    live = to_dm and bool(getattr(args, "i_mean_it", False))
    if live:
        # Same DM. Send-time is this clock, immediately before the existing POST.
        markdown = apply_sydney_morning_late_line(
            markdown,
            scheduled_for=getattr(args, "scheduled_for", "") or "",
            sent_at=utcnow(),
            run_id=getattr(args, "run_id", "") or "",
        )
    result = deliver(
        markdown,
        desk=desk,
        as_of=as_of,
        send=live,
        kind="desk_pack",
        completeness_pct=completeness,
        repo=root,
        out_root=out_root,
        session_date=session_date,
        respect_quiet_hours=not bool(getattr(args, "ignore_quiet_hours", False)),
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV if to_dm else None,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not live
    payload["to_principal_dm"] = to_dm
    payload.update(extra)
    print(json.dumps(payload, sort_keys=True, indent=2))
    if live and not result.sent:
        return 2, _payload_path(payload)
    return 0, _payload_path(payload)


def _cmd_watchlist(args: Namespace) -> int:
    send = _want_send(args)
    if send is None:
        return 2
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    from mm_desks.watchlist import run_watchlist_from_fixture, write_watchlist_artifacts
    from mm_delivery.watchlist import deliver_watchlist

    root = Path(args.repo_root).resolve()
    run = run_watchlist_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    if getattr(args, "out", None):
        written = write_watchlist_artifacts(run, out_root=out_root)
    result = deliver_watchlist(
        run.canonical(),
        as_of=run.as_of_knowledge,
        send=bool(send),
        repo=root,
        out_root=out_root,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not send
    payload["send"] = bool(result.primary.sent)
    payload["publisher"] = "ops"
    payload["product"] = "watchlist"
    payload["n_llm_calls"] = run.llm_calls
    payload["watchlist_content_hash"] = run.content_hash
    payload["written"] = written
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and not result.primary.sent:
        return 2
    return 0 if run.status != "FAILED" else 2


def _cmd_listings(args: Namespace) -> int:
    send = _want_send(args)
    if send is None:
        return 2
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    from mm_desks.listings import run_listings_from_fixture, write_listings_artifacts
    from mm_delivery.listings import deliver_listings

    root = Path(args.repo_root).resolve()
    run = run_listings_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    if getattr(args, "out", None):
        written = write_listings_artifacts(run, out_root=out_root)
    result = deliver_listings(
        run.canonical(),
        as_of=run.as_of_knowledge,
        send=bool(send),
        repo=root,
        out_root=out_root,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not send
    payload["send"] = bool(result.primary.sent)
    payload["publisher"] = "ops"
    payload["product"] = "listings"
    payload["n_llm_calls"] = run.llm_calls
    payload["listings_content_hash"] = run.content_hash
    payload["written"] = written
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and not result.primary.sent:
        return 2
    return 0 if run.status != "FAILED" else 2


def _cmd_scorecard(args: Namespace) -> int:
    send = _want_send(args)
    if send is None:
        return 2
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    from mm_desks.scorecard import run_scorecard_from_fixture, write_scorecard_artifacts
    from mm_delivery.scorecard import deliver_scorecard

    root = Path(args.repo_root).resolve()
    run = run_scorecard_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    if getattr(args, "out", None):
        written = write_scorecard_artifacts(run, out_root=out_root)
    result = deliver_scorecard(
        run.canonical(),
        as_of=run.as_of_knowledge,
        send=bool(send),
        repo=root,
        out_root=out_root,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not send
    payload["send"] = bool(result.primary.sent)
    payload["publisher"] = "ops"
    payload["product"] = "scorecard"
    payload["n_llm_calls"] = run.llm_calls
    payload["scorecard_content_hash"] = run.content_hash
    payload["written"] = written
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and not result.primary.sent:
        return 2
    return 0 if run.status != "FAILED" else 2


def _cmd_decay(args: Namespace) -> int:
    send = _want_send(args)
    if send is None:
        return 2
    if SEND_ENABLED:
        print("lab deliver: SEND_ENABLED must stay false; pass --send into deliver()", file=sys.stderr)
        return 2
    from mm_desks.decay import run_decay_from_fixture, write_decay_artifacts
    from mm_delivery.decay import deliver_decay

    root = Path(args.repo_root).resolve()
    run = run_decay_from_fixture(Path(args.fixture), repo_root=root)
    written: dict[str, str] = {}
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    if getattr(args, "out", None):
        written = write_decay_artifacts(run, out_root=out_root)
    result = deliver_decay(
        run.canonical(),
        as_of=run.as_of_knowledge,
        send=bool(send),
        repo=root,
        out_root=out_root,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not send
    payload["send"] = bool(result.primary.sent)
    payload["publisher"] = "ops"
    payload["product"] = "decay"
    payload["n_llm_calls"] = run.llm_calls
    payload["decay_content_hash"] = run.content_hash
    payload["alerted"] = run.alerted
    payload["written"] = written
    print(json.dumps(payload, sort_keys=True, indent=2))
    if send and not result.primary.sent:
        return 2
    return 0 if run.status != "FAILED" else 2


def _cmd_test(args: Namespace) -> tuple[int, str | None]:
    root = Path(args.repo_root).resolve()
    desk = str(args.desk)
    as_of = utcnow()
    to_dm = bool(getattr(args, "to_principal_dm", False))
    live = to_dm and bool(getattr(args, "i_mean_it", False))
    chat_env = PRINCIPAL_DM_CHAT_ID_ENV if to_dm else "TELEGRAM_CHAT_ID"
    lines = [
        "delivery test ping from lab deliver test",
        "source: lab.deliver.test",
        f"as_of_knowledge: {as_of.isoformat()}",
        f"chat_id_env: {chat_env}",
        "provenance: delivery test ping; not an observation; not a FRED rates print",
        "Not an order. Not Execution. Live trading remains HARD-GATED.",
    ]
    if to_dm:
        lines.append("Hive group TELEGRAM_CHAT_ID is not this route.")
    markdown = "\n".join(lines) + "\n"
    out_root = Path(args.out).resolve() if getattr(args, "out", None) else root
    result = deliver(
        markdown,
        desk=desk,
        as_of=as_of,
        send=live,
        kind="test",
        completeness_pct=100.0,
        repo=root,
        out_root=out_root,
        session_date=as_of.date().isoformat(),
        respect_quiet_hours=not bool(getattr(args, "ignore_quiet_hours", False)),
        chat_id_env_override=PRINCIPAL_DM_CHAT_ID_ENV if to_dm else None,
    )
    payload = result.as_public_dict()
    payload["no_send"] = not live
    payload["test"] = True
    payload["to_principal_dm"] = to_dm
    print(json.dumps(payload, sort_keys=True, indent=2))
    if live and not result.sent:
        return 2, _payload_path(payload)
    return 0, _payload_path(payload)


def _load_source(args: Namespace, root: Path, desk: str):
    fixture = getattr(args, "fixture", None)
    from_md = getattr(args, "from_markdown", None)
    if bool(fixture) == bool(from_md):
        print("lab deliver pack: require exactly one of --fixture or --from-markdown", file=sys.stderr)
        return None
    if from_md:
        try:
            require_route_slug(desk)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return None
        path = Path(from_md)
        if not path.is_file():
            print(f"markdown not found: {path}", file=sys.stderr)
            return None
        as_of_raw = getattr(args, "as_of", None)
        if not as_of_raw:
            print("lab deliver --from-markdown requires --as-of", file=sys.stderr)
            return None
        as_of = parse_utc(str(as_of_raw))
        markdown = path.read_text(encoding="utf-8")
        return markdown, as_of, 100.0, as_of.date().isoformat(), {}
    try:
        require_publishing_desk(desk)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return None
    result = run_from_fixture(
        Path(fixture),
        repo_root=root,
        slugs=PIPELINE,
        send=False,
    )
    markdown = result.pack_markdown or ""
    if desk != "ops":
        for row in result.desks:
            if row.slug != desk:
                continue
            for art in row.artifacts:
                if art.kind == "markdown" and art.content:
                    markdown = art.content
                    break
    completeness = 100.0
    for row in result.desks:
        if row.slug == desk or (desk == "ops" and row.slug == "ops"):
            completeness = float(row.completeness_pct)
            break
    extra = {"fixture_id": result.fixture_id, "desk_content_hash": result.content_hash}
    return markdown, result.as_of_knowledge, completeness, result.session_date, extra
