"""Phase 6c-5 Ops-owned delivery: channel matrix, watchlist fan-out, gates, no live Telegram."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mm_common.naming import (
    OPS,
    PUBLISHING_DESKS,
    RESEARCH,
    RETIRED_DESK_SLUGS,
    ROUTE_SLUGS,
    UnknownNameError,
    WATCHLIST,
    telegram_header,
)
from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.fanout import fanout_desk
from mm_delivery.gates import REASON_QUIET_HOURS, evaluate_send_gates
from mm_delivery.matrix import assert_channel_matrix
from mm_delivery.present import present_watchlist
from mm_delivery.watchlist import deliver_watchlist
from mm_desks.watchlist import run_watchlist_from_fixture
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
LOCKED = ROOT / "tests" / "fixtures" / "phase6c4" / "locked_scan.json"
AS_OF = parse_utc("2026-09-18T00:00:00Z")


def test_channel_matrix_matches_naming_and_is_ops_owned() -> None:
    settings = load_telegram_settings(ROOT)
    assert_channel_matrix(settings)
    assert settings.publisher == OPS
    assert settings.owner == OPS
    assert settings.coordinator == "orchestration_only"
    assert tuple(sorted(settings.desks)) == tuple(sorted(ROUTE_SLUGS))
    for slug in PUBLISHING_DESKS:
        assert slug in settings.desks
    for retired in RETIRED_DESK_SLUGS:
        assert retired not in settings.desks
    product = settings.product(WATCHLIST)
    assert product is not None
    assert product.desk == RESEARCH
    assert product.sleeve == WATCHLIST
    assert product.inherit_content_hash is True
    assert settings.thresholds.spec(WATCHLIST) is not None
    assert settings.thresholds.has_numeric(WATCHLIST) is True


def test_unknown_or_retired_route_fails_closed(tmp_path: Path) -> None:
    settings = load_telegram_settings(ROOT)
    with pytest.raises(UnknownNameError):
        fanout_desk("x", desk="coord", as_of=AS_OF, send=False, repo=ROOT, settings=settings)
    with pytest.raises(UnknownNameError):
        fanout_desk("x", desk="crypto", as_of=AS_OF, send=False, repo=ROOT, settings=settings)
    raw = yaml.safe_load((ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8"))
    raw["desks"]["coord"] = {"enabled": True, "chat_id_env": "TELEGRAM_CHAT_ID", "thread_id": None}
    bad = tmp_path / "bad-telegram.yaml"
    bad.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(UnknownNameError, match="channel matrix"):
        load_telegram_settings(ROOT, path=bad)


def test_present_watchlist_uses_naming_and_does_not_invent_ideas() -> None:
    run = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    text = present_watchlist(run.canonical())
    header = telegram_header(RESEARCH, sleeve=WATCHLIST)
    assert text.startswith(header)
    assert "watchlist monitor" in text
    assert "Not a call" in text
    assert "Coord is not the publisher" in text
    assert "BTC" in text
    assert "ETH" in text
    assert "in_universe" in text
    assert "watch_only" in text
    assert "UNAVAILABLE" in text
    assert "PLAYBOOK setups flagged" in text
    assert "no actionable setup" not in text or "inventory is not an idea list" in text
    assert "ideas shown" not in text
    assert not language_violations(text)
    assert run.content_hash in text


def test_watchlist_fanout_inherits_content_hash_and_ops_mirror() -> None:
    run = run_watchlist_from_fixture(LOCKED, repo_root=ROOT)
    first = deliver_watchlist(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    second = deliver_watchlist(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    assert first.content_hash == run.content_hash
    assert first.content_hash == second.content_hash
    assert first.publisher == OPS
    assert first.primary.payload.desk == RESEARCH
    assert first.primary.payload.kind == WATCHLIST
    assert first.primary.sent is False
    assert first.primary.reason == "no_send"
    assert first.ops_mirror is not None
    assert first.ops_mirror.payload.desk == OPS
    assert first.ops_mirror.payload.content_hash == first.content_hash
    assert "ops mirror" in first.ops_mirror.payload.text
    assert first.coord_mirror is first.ops_mirror
    public = first.as_public_dict()
    assert public["publisher"] == OPS
    assert public["ops_mirror"] is not None
    header = telegram_header(RESEARCH, sleeve=WATCHLIST)
    assert first.primary.payload.text.startswith(header)


def test_watchlist_quiet_hours_and_threshold_respected() -> None:
    settings = load_telegram_settings(ROOT)
    quiet = evaluate_send_gates(
        settings,
        kind=WATCHLIST,
        now=parse_utc("2026-09-18T13:00:00Z"),
        completeness_pct=80.0,
    )
    assert quiet.allow is False
    assert quiet.reason == REASON_QUIET_HOURS
    open_ = evaluate_send_gates(
        settings,
        kind=WATCHLIST,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=80.0,
    )
    assert open_.allow is True
    blocked = evaluate_send_gates(
        settings,
        kind=WATCHLIST,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=0.0,
    )
    assert blocked.allow is False


def test_watchlist_schedule_is_not_sydney_0800_digest() -> None:
    settings = load_telegram_settings(ROOT)
    jobs = {job.name: job for job in settings.schedule}
    assert "watchlist" in jobs
    assert jobs["watchlist"].local_time.hour == 7
    assert jobs["watchlist"].local_time.minute == 45
    assert jobs["watchlist"].timezone.key == "Australia/Sydney"
