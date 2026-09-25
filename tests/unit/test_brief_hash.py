"""Frozen fixture day produces a stable pre-open and close content hash."""

from __future__ import annotations

from pathlib import Path

from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_from_fixture, load_fixture_file
from mm_briefing.render import brief_hash

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
EXPECTED_PREOPEN = ROOT / "tests" / "fixtures" / "briefing" / "frozen_preopen.sha256"
EXPECTED_CLOSE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_close.sha256"
EXPECTED_PREOPEN_MD = ROOT / "tests" / "fixtures" / "briefing" / "frozen_preopen.md"


def test_frozen_preopen_hash_is_deterministic() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    first, _ = generate_from_fixture("preopen", fixture, settings=settings)
    second, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert first is not None and second is not None
    assert first.content_hash == second.content_hash
    assert first.content_hash == brief_hash(first.markdown)
    assert len(first.content_hash) == 64
    expected = EXPECTED_PREOPEN.read_text(encoding="utf-8").strip()
    assert first.content_hash == expected
    assert "US Pre-Market Brief — 2026-03-10" in first.markdown
    assert "01FROZENBTCFUNDING00000001" in first.markdown
    assert "CPI YoY" in first.markdown
    assert "Watchlist" in first.markdown
    assert "Invalidation" in first.markdown
    assert "Informational only" in first.markdown
    assert "no decision" in first.markdown.lower()
    assert "equity-index proxy" in first.markdown
    assert "Required slots" in first.markdown
    assert first.data_quality in {"ok", "partial", "fresh", "unavailable", "stale"}


def test_frozen_close_hash_is_deterministic() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    first, _ = generate_from_fixture("close", fixture, settings=settings)
    second, _ = generate_from_fixture("close", fixture, settings=settings)
    assert first is not None and second is not None
    assert first.content_hash == second.content_hash
    expected = EXPECTED_CLOSE.read_text(encoding="utf-8").strip()
    assert first.content_hash == expected
    assert "US Close Brief — 2026-03-10" in first.markdown
    assert "THESIS-0001" in first.markdown
    assert "lab wrong (so far)" in first.markdown
    assert "Overnight reference" not in first.markdown
    assert "KEY TAKEAWAY" not in first.markdown
    assert "Monitor into Asia" not in first.markdown


def test_preopen_markdown_matches_committed_golden() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert doc is not None
    golden = EXPECTED_PREOPEN_MD.read_text(encoding="utf-8")
    assert doc.markdown == golden
