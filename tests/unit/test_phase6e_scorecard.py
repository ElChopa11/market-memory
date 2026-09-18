"""Phase 6e Quant pack scorecard: like-for-like, tagged incomparable, PIT, no sixth desk."""

from __future__ import annotations

from pathlib import Path

import pytest

from mm_common.naming import (
    PUBLISHING_DESKS,
    QUANT,
    SCORECARD,
    UnknownNameError,
    desk_display,
    require_publishing_desk,
    sleeve_display,
)
from mm_desks.scorecard import ENGINE_VERSION, NO_INVENTED_SCORE, run_scorecard_from_fixture
from mm_quant.decay_stub import decay_stub_payload
from mm_quant.scorecard import COMPARABLE, NOT_COMPARABLE, REASON_SCHEDULE, REASON_TAGGED
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
PACKS = ROOT / "tests" / "fixtures" / "phase6e" / "packs.json"
EMPTY = ROOT / "tests" / "fixtures" / "phase6e" / "empty.json"


def test_scorecard_is_quant_sleeve_not_a_sixth_desk() -> None:
    assert PUBLISHING_DESKS == ("intel", "research", "quant", "ic_risk", "ops")
    with pytest.raises(UnknownNameError):
        require_publishing_desk("scorecard")
    assert sleeve_display(SCORECARD).startswith("Quant")
    spec = (ROOT / "config" / "scorecards" / "desk.yaml").read_text(encoding="utf-8")
    assert "desk: quant" in spec
    assert "promote: false" in spec
    assert "llm: false" in spec
    assert "send: false" in spec


def test_scorecard_is_deterministic_and_quant_envelope() -> None:
    first = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    second = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    assert first.run_id == second.run_id
    assert len(first.content_hash) == 64
    assert first.output.slug == QUANT
    assert first.output.desk == desk_display(QUANT)
    assert first.output.op == "observation"
    assert first.envelopes[0].desk == QUANT
    assert first.envelopes[0].channel == "desk.quant.output"
    assert first.engine_version == ENGINE_VERSION
    assert first.llm_calls == 0


def test_brief_tag_90m_is_not_like_for_like_vs_30m() -> None:
    result = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    pack_ids = {p.pack_id for p in result.packs}
    assert "BRIEF-TAG-20260918" in pack_ids
    assert "preopen-30m-20260918" in pack_ids
    assert "preopen-30m-20260917" in pack_ids
    assert "FUTURE-PREOPEN-20260919" not in pack_ids
    tagged = next(
        row
        for row in result.pairs
        if {row.left_id, row.right_id} == {"BRIEF-TAG-20260918", "preopen-30m-20260918"}
    )
    assert tagged.verdict == NOT_COMPARABLE
    assert tagged.comparable is False
    assert tagged.completeness_delta is None
    assert tagged.hash_identity is None
    assert REASON_SCHEDULE in tagged.reason_codes
    assert REASON_TAGGED in tagged.reason_codes
    assert "90m" in result.markdown or "BRIEF-TAG-20260918" in result.markdown
    assert NO_INVENTED_SCORE in result.markdown


def test_like_for_like_30m_packs_score_with_provenance() -> None:
    result = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    pair = next(
        row
        for row in result.pairs
        if {row.left_id, row.right_id} == {"preopen-30m-20260918", "preopen-30m-20260917"}
    )
    assert pair.verdict == COMPARABLE
    assert pair.comparable is True
    assert pair.completeness_delta == 15.0
    assert pair.hash_identity is False
    assert pair.status_match is False
    assert pair.left_hash
    assert pair.right_hash
    assert pair.left_as_of
    assert pair.right_as_of


def test_lookahead_pack_stays_invisible() -> None:
    result = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    assert result.status == "DEGRADED"
    assert any(g.startswith("lookahead:") for g in result.gaps)
    assert "| FUTURE-PREOPEN-20260919 |" not in result.markdown
    assert language_violations(result.markdown) == []
    lowered = result.markdown.lower()
    assert "buy" not in lowered
    assert "sell" not in lowered
    assert "active call" not in lowered


def test_empty_fixture_degrades_and_does_not_invent() -> None:
    result = run_scorecard_from_fixture(EMPTY, repo_root=ROOT)
    assert result.packs == ()
    assert result.pairs == ()
    assert result.status == "DEGRADED"
    assert result.completeness == 0.0
    assert result.llm_calls == 0
    assert result.decay_stub is not None
    assert result.decay_stub["watch_enabled"] is False
    assert result.as_public_dict()["decay_watch_enabled"] is False


def test_decay_stub_records_prompt_hashes_without_watching() -> None:
    payload = decay_stub_payload(ROOT)
    assert payload["watch_enabled"] is False
    assert payload["phase"] == "6f-parked"
    assert payload["item"] == "IMP-031"
    assert payload["prompt_hashes"]
    assert all(row["sha256"] for row in payload["prompt_hashes"])


def test_ic_gates_required() -> None:
    result = run_scorecard_from_fixture(PACKS, repo_root=ROOT)
    payload = result.output.payload
    assert payload["ic_gates"]["skeptic_required"] is True
    assert payload["ic_gates"]["risk_required"] is True
    assert payload["ic_gates"]["self_approve"] is False
    assert payload["ic_gates"]["paper_open"] is False
    assert payload["promote"] is False
    assert payload["llm"] is False
