"""Phase 6a / IMP-014: envelope header + content_hash idempotency."""

from __future__ import annotations

from pathlib import Path

from mm_desks.envelope import REGIME_PLACEHOLDER, envelope_from_output, output_from_canonical, stamp_output
from mm_desks.orchestrator import run_from_fixture
from mm_desks.protocol import OK

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_desk_output_header_has_principal_fields() -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT, slugs=("intel",))
    intel = result.desks[0]
    header = intel.header()
    assert header["desk"] == "intel"
    assert header["as_of_utc"].endswith("+00:00")
    assert "Australia/Sydney" in header["as_of_sydney"] or "+10:00" in header["as_of_sydney"] or "+11:00" in header["as_of_sydney"]
    assert header["status"] == OK
    assert header["n"] >= 1
    assert header["completeness"] == 100.0
    assert header["regime"] == REGIME_PLACEHOLDER
    assert header["op"] == "observation"
    assert header["universe"] == "mixed"
    assert "hyperliquid.info" in header["sources"]
    assert header["missing"] == []
    assert intel.cadence == "daily"


def test_double_run_same_as_of_identical_envelope_hash() -> None:
    first = run_from_fixture(FIXTURE, repo_root=ROOT)
    second = run_from_fixture(FIXTURE, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    by_first = {row.slug: row for row in first.desks}
    by_second = {row.slug: row for row in second.desks}
    for slug, row in by_first.items():
        env_a = envelope_from_output(row, repo_root=ROOT)
        env_b = envelope_from_output(by_second[slug], repo_root=ROOT)
        assert env_a.content_hash == env_b.content_hash
        assert env_a.canonical() == env_b.canonical()
        assert env_a.envelope_id != env_b.envelope_id
        notify = env_a.notify_payload()
        assert set(notify) <= {"id", "desk", "as_of", "content_hash", "channel", "status"}
        assert "body" not in notify
        assert len(str(notify)) < 2000


def test_envelope_round_trip_canonical() -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT, slugs=("crypto",))
    crypto = result.desks[0]
    again = output_from_canonical(crypto.canonical())
    assert again.content_hash() == crypto.content_hash()
    assert again.header() == crypto.header()
    assert again.op in {"paper", "observation"}


def test_risk_envelope_op_is_paper() -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT, slugs=("intel", "crypto", "equities", "quant", "skeptic", "risk"))
    risk = {row.slug: row for row in result.desks}["risk"]
    assert risk.op == "paper"
    env = envelope_from_output(risk, repo_root=ROOT)
    assert env.channel == "desk.risk.output"
    assert env.op == "paper"
