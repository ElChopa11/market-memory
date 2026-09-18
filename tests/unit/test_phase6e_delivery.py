"""Phase 6e Ops-owned scorecard delivery: naming, hash inherit, no live Telegram."""

from __future__ import annotations

from pathlib import Path

from mm_common.naming import OPS, QUANT, SCORECARD, telegram_header
from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.gates import REASON_QUIET_HOURS, evaluate_send_gates
from mm_delivery.present import present_scorecard
from mm_delivery.scorecard import deliver_scorecard
from mm_desks.scorecard import run_scorecard_from_fixture
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
PACKS = ROOT / "tests" / "fixtures" / "phase6e" / "packs.json"


def test_scorecard_product_is_ops_owned_quant_sleeve() -> None:
    settings = load_telegram_settings(ROOT)
    product = settings.product(SCORECARD)
    assert product is not None
    assert product.desk == QUANT
    assert product.sleeve == SCORECARD
    assert product.inherit_content_hash is True
    assert settings.publisher == OPS
    assert settings.thresholds.spec(SCORECARD) is not None
    assert settings.thresholds.has_numeric(SCORECARD) is True
    jobs = {job.name: job for job in settings.schedule}
    assert "scorecard" in jobs
    assert jobs["scorecard"].local_time.hour == 7
    assert jobs["scorecard"].local_time.minute == 55
    assert jobs["scorecard"].timezone.key == "Australia/Sydney"


def test_present_scorecard_uses_naming_and_keeps_tag_honest() -> None:
    run = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    text = present_scorecard(run.canonical())
    header = telegram_header(QUANT, sleeve=SCORECARD)
    assert text.startswith(header)
    assert "Not a call" in text
    assert "Coord is not the publisher" in text
    assert "BRIEF-TAG-20260918" in text
    assert "NOT_COMPARABLE" in text
    assert "| FUTURE-PREOPEN-20260919 |" not in text
    assert run.content_hash in text
    assert not language_violations(text)


def test_scorecard_fanout_inherits_content_hash_and_ops_mirror() -> None:
    run = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    first = deliver_scorecard(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    second = deliver_scorecard(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    assert first.content_hash == run.content_hash
    assert first.content_hash == second.content_hash
    assert first.publisher == OPS
    assert first.primary.payload.desk == QUANT
    assert first.primary.payload.kind == SCORECARD
    assert first.primary.sent is False
    assert first.primary.reason == "no_send"
    assert first.ops_mirror is not None
    assert first.ops_mirror.payload.desk == OPS
    assert first.ops_mirror.payload.content_hash == first.content_hash
    assert first.coord_mirror is first.ops_mirror
    header = telegram_header(QUANT, sleeve=SCORECARD)
    assert first.primary.payload.text.startswith(header)


def test_scorecard_quiet_hours_and_threshold_respected() -> None:
    settings = load_telegram_settings(ROOT)
    quiet = evaluate_send_gates(
        settings,
        kind=SCORECARD,
        now=parse_utc("2026-09-18T13:00:00Z"),
        completeness_pct=80.0,
    )
    assert quiet.allow is False
    assert quiet.reason == REASON_QUIET_HOURS
    open_ = evaluate_send_gates(
        settings,
        kind=SCORECARD,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=80.0,
    )
    assert open_.allow is True
    blocked = evaluate_send_gates(
        settings,
        kind=SCORECARD,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=0.0,
    )
    assert blocked.allow is False
