"""Phase 6f Quant decay watch: prompt hashes, mismatch NOTIFY, no invented scorecards."""

from __future__ import annotations

from pathlib import Path

import pytest

from mm_common.naming import (
    DECAY,
    PUBLISHING_DESKS,
    QUANT,
    UnknownNameError,
    desk_display,
    require_publishing_desk,
    sleeve_display,
)
from mm_desks.decay import run_decay_from_fixture
from mm_quant.decay import MATCH, MISMATCH, MISSING, NO_INVENTED_SCORE, decay_watch_payload, refuse_forbidden
from mm_quant.scorecard import NOT_COMPARABLE
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
MATCH_FIXTURE = ROOT / "tests" / "fixtures" / "phase6f" / "match.json"
MISMATCH_FIXTURE = ROOT / "tests" / "fixtures" / "phase6f" / "mismatch.json"
MISSING_FIXTURE = ROOT / "tests" / "fixtures" / "phase6f" / "missing.json"
SCORECARD_FIXTURE = ROOT / "tests" / "fixtures" / "phase6f" / "scorecard.json"


def test_decay_is_quant_sleeve_not_a_sixth_desk() -> None:
    assert PUBLISHING_DESKS == ("intel", "research", "quant", "ic_risk", "ops")
    with pytest.raises(UnknownNameError):
        require_publishing_desk("decay")
    assert sleeve_display(DECAY).startswith("Quant")
    spec = (ROOT / "config" / "scorecards" / "decay.yaml").read_text(encoding="utf-8")
    assert "watch_enabled: true" in spec
    assert "auto_disable: false" in spec
    assert "auto_waive: false" in spec
    assert "alert_path: ops" in spec


def test_decay_watch_is_deterministic_and_quant_envelope() -> None:
    first = run_decay_from_fixture(MATCH_FIXTURE, repo_root=ROOT)
    second = run_decay_from_fixture(MATCH_FIXTURE, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    assert first.run_id == second.run_id
    assert len(first.content_hash) == 64
    assert first.output.slug == QUANT
    assert first.output.desk == desk_display(QUANT)
    assert first.output.op == "observation"
    assert first.envelopes[0].desk == QUANT
    assert first.envelopes[0].channel == "desk.quant.output"
    assert first.overall == MATCH
    assert first.status == "OK"
    assert first.alerted is False
    assert "desk.quant.alert" not in first.notify_channels
    assert first.llm_calls == 0
    assert first.payload["watch_enabled"] is True
    assert first.payload["prompt_hashes"]
    assert all(row["sha256"] for row in first.payload["prompt_hashes"])


def test_mismatch_notifies_alert_channel_without_waiving() -> None:
    result = run_decay_from_fixture(MISMATCH_FIXTURE, repo_root=ROOT)
    assert result.overall == MISMATCH
    assert result.status == "DEGRADED"
    assert result.alerted is True
    assert "desk.quant.output" in result.notify_channels
    assert "desk.quant.alert" in result.notify_channels
    signal = result.payload["queue_signal"]
    assert signal["kind"] == "NOTIFY"
    assert signal["active"] is True
    assert signal["auto_write"] is False
    assert signal["auto_waive"] is False
    assert signal["auto_disable"] is False
    assert signal["item"] is None
    assert any(row["verdict"] == MISMATCH for row in result.payload["rows"])
    assert "official_brief.v1.txt" in result.markdown
    assert result.output.payload["ic_gates"]["skeptic_required"] is True
    assert result.output.payload["ic_gates"]["self_approve"] is False
    assert result.output.payload["promote"] is False


def test_missing_file_is_honest_unavailable() -> None:
    result = run_decay_from_fixture(MISSING_FIXTURE, repo_root=ROOT)
    assert result.overall == MISSING
    assert result.status == "DEGRADED"
    assert result.alerted is True
    assert any(row["verdict"] == MISSING and "does_not_exist" in row["path"] for row in result.payload["rows"])
    assert any(g.startswith("MISSING:") for g in result.gaps)


def test_decay_does_not_invent_comparable_scorecards() -> None:
    result = run_decay_from_fixture(SCORECARD_FIXTURE, repo_root=ROOT)
    pairs = result.payload["scorecard_pairs"]
    tagged = next(
        row
        for row in pairs
        if {row["left_id"], row["right_id"]} == {"BRIEF-TAG-20260918", "preopen-30m-20260918"}
    )
    assert tagged["verdict"] == NOT_COMPARABLE
    assert tagged["comparable"] is False
    assert tagged["completeness_delta"] is None
    assert tagged["hash_identity"] is None
    assert tagged["decay_invented_score"] is False
    assert NO_INVENTED_SCORE in result.markdown or NO_INVENTED_SCORE in tagged["note"]
    assert "| FUTURE-PREOPEN-20260919 |" not in result.markdown
    assert language_violations(result.markdown) == []
    lowered = result.markdown.lower()
    assert "buy" not in lowered
    assert "sell" not in lowered
    assert "active call" not in lowered


def test_decay_payload_records_versioned_prompt_hashes() -> None:
    payload = decay_watch_payload(ROOT)
    assert payload["watch_enabled"] is True
    assert payload["phase"] == "6f"
    assert payload["item"] == "IMP-031"
    assert payload["overall"] == MATCH
    assert payload["auto_disable"] is False
    assert payload["auto_waive"] is False
    prompts = {row["path"]: row for row in payload["rows"] if row["kind"] == "prompt"}
    assert "config/prompts/official_brief.v1.txt" in prompts
    assert prompts["config/prompts/official_brief.v1.txt"]["verdict"] == MATCH
    assert len(prompts["config/prompts/official_brief.v1.txt"]["observed_sha256"]) == 64


def test_refuses_waiver_and_auto_disable() -> None:
    assert refuse_forbidden("waive")
    assert refuse_forbidden("merge")
    assert refuse_forbidden("auto-disable")
    assert refuse_forbidden(None) is None


def test_ic_gates_required() -> None:
    result = run_decay_from_fixture(MATCH_FIXTURE, repo_root=ROOT)
    payload = result.output.payload
    assert payload["ic_gates"]["skeptic_required"] is True
    assert payload["ic_gates"]["risk_required"] is True
    assert payload["ic_gates"]["self_approve"] is False
    assert payload["ic_gates"]["paper_open"] is False
    assert payload["promote"] is False
    assert payload["llm"] is False
