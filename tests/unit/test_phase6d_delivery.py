"""Phase 6d Ops-owned listings delivery: naming, hash inherit, no live Telegram."""

from __future__ import annotations

from pathlib import Path

from mm_common.naming import LISTINGS, OPS, RESEARCH, telegram_header
from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.gates import REASON_QUIET_HOURS, evaluate_send_gates
from mm_delivery.listings import deliver_listings
from mm_delivery.present import present_listings
from mm_desks.listings import run_listings_from_fixture
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
LISTING_DAY = ROOT / "tests" / "fixtures" / "phase6d" / "listing_day.json"


def test_listings_product_is_ops_owned_research_sleeve() -> None:
    settings = load_telegram_settings(ROOT)
    product = settings.product(LISTINGS)
    assert product is not None
    assert product.desk == RESEARCH
    assert product.sleeve == LISTINGS
    assert product.inherit_content_hash is True
    assert settings.publisher == OPS
    assert settings.thresholds.spec(LISTINGS) is not None
    assert settings.thresholds.has_numeric(LISTINGS) is True
    jobs = {job.name: job for job in settings.schedule}
    assert "listings" in jobs
    assert jobs["listings"].local_time.hour == 7
    assert jobs["listings"].local_time.minute == 50
    assert jobs["listings"].timezone.key == "Australia/Sydney"


def test_present_listings_uses_naming_and_does_not_invent() -> None:
    run = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    text = present_listings(run.canonical())
    header = telegram_header(RESEARCH, sleeve=LISTINGS)
    assert text.startswith(header)
    assert "listings / IPO" in text.lower() or "listings IPO" in text
    assert "Not a call" in text
    assert "Coord is not the publisher" in text
    assert "CRCL" in text
    assert "FUTUREX" not in text
    assert "GHOST" not in text
    assert run.content_hash in text
    assert not language_violations(text)


def test_listings_fanout_inherits_content_hash_and_ops_mirror() -> None:
    run = run_listings_from_fixture(LISTING_DAY, repo_root=ROOT)
    first = deliver_listings(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    second = deliver_listings(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    assert first.content_hash == run.content_hash
    assert first.content_hash == second.content_hash
    assert first.publisher == OPS
    assert first.primary.payload.desk == RESEARCH
    assert first.primary.payload.kind == LISTINGS
    assert first.primary.sent is False
    assert first.primary.reason == "no_send"
    assert first.ops_mirror is not None
    assert first.ops_mirror.payload.desk == OPS
    assert first.ops_mirror.payload.content_hash == first.content_hash
    assert first.coord_mirror is first.ops_mirror
    header = telegram_header(RESEARCH, sleeve=LISTINGS)
    assert first.primary.payload.text.startswith(header)


def test_listings_quiet_hours_and_threshold_respected() -> None:
    settings = load_telegram_settings(ROOT)
    quiet = evaluate_send_gates(
        settings,
        kind=LISTINGS,
        now=parse_utc("2026-09-18T13:00:00Z"),
        completeness_pct=80.0,
    )
    assert quiet.allow is False
    assert quiet.reason == REASON_QUIET_HOURS
    open_ = evaluate_send_gates(
        settings,
        kind=LISTINGS,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=80.0,
    )
    assert open_.allow is True
    blocked = evaluate_send_gates(
        settings,
        kind=LISTINGS,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=0.0,
    )
    assert blocked.allow is False
