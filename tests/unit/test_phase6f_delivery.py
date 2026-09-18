"""Phase 6f Ops-owned decay delivery: naming, hash inherit, no live Telegram."""

from __future__ import annotations

from pathlib import Path

from mm_common.naming import DECAY, OPS, QUANT, telegram_header
from mm_common.time import parse_utc
from mm_delivery.config import load_telegram_settings
from mm_delivery.gates import REASON_QUIET_HOURS, evaluate_send_gates
from mm_delivery.present import present_decay
from mm_delivery.decay import deliver_decay
from mm_desks.decay import run_decay_from_fixture
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
MATCH = ROOT / "tests" / "fixtures" / "phase6f" / "match.json"
MISMATCH = ROOT / "tests" / "fixtures" / "phase6f" / "mismatch.json"
SCORECARD = ROOT / "tests" / "fixtures" / "phase6f" / "scorecard.json"


def test_decay_product_is_ops_owned_quant_sleeve() -> None:
    settings = load_telegram_settings(ROOT)
    product = settings.product(DECAY)
    assert product is not None
    assert product.desk == QUANT
    assert product.sleeve == DECAY
    assert product.inherit_content_hash is True
    assert settings.publisher == OPS
    assert settings.thresholds.spec(DECAY) is not None
    assert settings.thresholds.has_numeric(DECAY) is True
    jobs = {job.name: job for job in settings.schedule}
    assert "decay" in jobs
    assert jobs["decay"].local_time.hour == 8
    assert jobs["decay"].local_time.minute == 5
    assert jobs["decay"].timezone.key == "Australia/Sydney"


def test_present_decay_uses_naming_and_keeps_tags_honest() -> None:
    run = run_decay_from_fixture(SCORECARD, repo_root=ROOT)
    text = present_decay(run.canonical())
    header = telegram_header(QUANT, sleeve=DECAY)
    assert text.startswith(header)
    assert "Not a call" in text
    assert "Coord is not the publisher" in text
    assert "NOT_COMPARABLE" in run.markdown
    assert run.content_hash in text
    assert not language_violations(text)


def test_decay_fanout_inherits_content_hash_and_ops_mirror() -> None:
    run = run_decay_from_fixture(MATCH, repo_root=ROOT)
    first = deliver_decay(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    second = deliver_decay(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    assert first.content_hash == run.content_hash
    assert first.content_hash == second.content_hash
    assert first.publisher == OPS
    assert first.primary.payload.desk == QUANT
    assert first.primary.payload.kind == DECAY
    assert first.primary.sent is False
    assert first.primary.reason == "no_send"
    assert first.ops_mirror is not None
    assert first.ops_mirror.payload.desk == OPS
    assert first.ops_mirror.payload.content_hash == first.content_hash
    assert first.coord_mirror is first.ops_mirror
    header = telegram_header(QUANT, sleeve=DECAY)
    assert first.primary.payload.text.startswith(header)


def test_mismatch_delivery_still_dry_run() -> None:
    run = run_decay_from_fixture(MISMATCH, repo_root=ROOT)
    result = deliver_decay(run.canonical(), as_of=run.as_of_knowledge, send=False, repo=ROOT)
    assert result.primary.sent is False
    assert "NOTIFY" in present_decay(run.canonical()) or run.alerted is True


def test_decay_quiet_hours_and_threshold_respected() -> None:
    settings = load_telegram_settings(ROOT)
    quiet = evaluate_send_gates(
        settings,
        kind=DECAY,
        now=parse_utc("2026-09-18T13:00:00Z"),
        completeness_pct=80.0,
    )
    assert quiet.allow is False
    assert quiet.reason == REASON_QUIET_HOURS
    open_ = evaluate_send_gates(
        settings,
        kind=DECAY,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=80.0,
    )
    assert open_.allow is True
    blocked = evaluate_send_gates(
        settings,
        kind=DECAY,
        now=parse_utc("2026-09-18T02:00:00Z"),
        completeness_pct=0.0,
    )
    assert blocked.allow is False
