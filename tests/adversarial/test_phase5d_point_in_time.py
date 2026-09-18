"""Adversarial PIT: desk runners key off as_of_knowledge, never market_time."""

from __future__ import annotations

from pathlib import Path

from mm_desks.orchestrator import run_from_fixture

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_desk_run_watermark_is_as_of_knowledge() -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT)
    assert result.as_of_knowledge.isoformat() == "2026-09-18T00:05:00+00:00"
    for desk in result.desks:
        assert desk.as_of_knowledge == result.as_of_knowledge
    assert "2026-09-18T00:05:00+00:00" in result.pack_markdown
    assert "published_at" not in result.pack_markdown
    # market_time may appear only as a forbidden-clock reminder; knowledge clock is the watermark field.
    assert "Knowledge watermark (as_of_knowledge)" in result.pack_markdown
    for event in result.events:
        assert event.ts == result.as_of_knowledge
