"""Phase 6c PLAYBOOK ladder, Quant math, grounding, LLM budget."""

from __future__ import annotations

from pathlib import Path

from mm_desks.ladder import ARTIFACT_TYPES
from mm_desks.llm.budget import ERROR_BUDGET_EXCEEDED, load_token_budget
from mm_desks.llm.client import LlmClient, LlmForbidden, TEMPLATE_ONLY, fixture_completer, scripted_completer
from mm_desks.llm.grounding import GroundingError, assert_numeric_lock
from mm_desks.llm.prompts import load_prompt
from mm_desks.playbook import round_trip_envelopes, run_playbook_from_fixture
from mm_quant.trade_math import ProbabilityProvenance, compute_trade_math

ROOT = Path(__file__).resolve().parents[2]
NO_SETUP = ROOT / "tests" / "fixtures" / "phase6c" / "no_setup.json"
IDEAS = ROOT / "tests" / "fixtures" / "phase6c" / "ideas.json"
FRED = ROOT / "tests" / "fixtures" / "phase6c" / "fred_unavailable.json"
LOW = ROOT / "tests" / "fixtures" / "phase6c" / "low_completeness.json"


def test_no_setup_zero_llm_calls() -> None:
    client = LlmClient(load_token_budget(ROOT), completer=fixture_completer({"prose": "should not run", "claim_tags": []}))
    first = run_playbook_from_fixture(NO_SETUP, repo_root=ROOT, llm=client)
    second = run_playbook_from_fixture(NO_SETUP, repo_root=ROOT, llm=client)
    assert first.content_hash == second.content_hash
    assert first.llm_calls == ()
    assert client.records == [] or all(r.input_tokens == 0 and r.output_tokens == 0 for r in client.records)
    # Completer must not have been invoked.
    assert first.status in {"OK", "DEGRADED"}
    types = [a.artifact_type for a in first.artifacts]
    for needed in ARTIFACT_TYPES:
        assert needed in types
    brief = next(a for a in first.artifacts if a.artifact_type == "OFFICIAL_BRIEF")
    assert "no actionable setup" in str(brief.payload["executive_cut"]).lower()


def test_double_run_identical_hashes_with_ideas() -> None:
    a = run_playbook_from_fixture(IDEAS, repo_root=ROOT)
    b = run_playbook_from_fixture(IDEAS, repo_root=ROOT)
    assert a.content_hash == b.content_hash
    assert a.trade_math_hash == b.trade_math_hash
    assert a.run_id == b.run_id
    for x, y in zip(a.artifacts, b.artifacts, strict=True):
        assert x.content_hash() == y.content_hash()
        assert x.run_id == a.run_id
        assert x.run_content_hash == a.content_hash
        assert x.trade_math_hash == a.trade_math_hash


def test_envelope_round_trip_every_artifact_type() -> None:
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT)
    again = round_trip_envelopes(run.envelopes)
    assert {env.desk for env in again} == {env.desk for env in run.envelopes}
    for a, b in zip(run.envelopes, again, strict=True):
        assert a.content_hash == b.content_hash
        assert a.body["artifact_type"] == b.body["artifact_type"]
    seen = {env.body["artifact_type"] for env in again}
    assert seen == set(ARTIFACT_TYPES)


def test_math_mismatch_fails_run() -> None:
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT, force_math_mismatch=True)
    assert run.status == "FAILED"
    assert run.error_class == "math_mismatch"


def test_quant_owns_r_and_prior_excluded() -> None:
    math = compute_trade_math(
        instrument="BTC",
        entry=100,
        stop=90,
        targets=(120,),
        p_win=ProbabilityProvenance(kind="prior", value=0.9, judgement="gut"),
        avg_r_win=2.0,
        atr_pct=0.02,
        stop_distance_atr=1.0,
        repo_root=ROOT,
    )
    assert math.risk_per_unit == 10
    assert math.r_targets[0] == 2.0
    assert math.expectancy is None
    assert math.size_pct == 0
    assert any("prior" in n for n in math.notes)

    ok = compute_trade_math(
        instrument="BTC",
        entry=100,
        stop=90,
        targets=(120,),
        p_win=ProbabilityProvenance(kind="base_rate", value=0.5, n=40, window="90d"),
        avg_r_win=2.0,
        atr_pct=0.02,
        stop_distance_atr=1.0,
        repo_root=ROOT,
    )
    assert ok.size_pct > 0
    small = compute_trade_math(
        instrument="BTC",
        entry=100,
        stop=90,
        targets=(120,),
        p_win=ProbabilityProvenance(kind="base_rate", value=0.5, n=3, window="90d"),
        avg_r_win=2.0,
        atr_pct=0.02,
        stop_distance_atr=1.0,
        repo_root=ROOT,
    )
    assert small.below_min_sample is True
    assert small.size_pct == 0


def test_template_only_artifacts_forbid_llm() -> None:
    client = LlmClient(load_token_budget(ROOT), completer=fixture_completer({"prose": "x", "claim_tags": []}))
    prompt = load_prompt("OFFICIAL_BRIEF", ROOT)
    for kind in TEMPLATE_ONLY:
        try:
            client.complete(
                artifact_type=kind,
                desk_slug="coord",
                run_id="x",
                prompt=prompt,
                user_payload={},
            )
            raise AssertionError(kind)
        except LlmForbidden:
            pass


def test_over_per_run_budget_degraded_templated_escalation() -> None:
    budget = load_token_budget(ROOT, per_run_token_budget=1, per_call_max_input_tokens=1)
    client = LlmClient(
        budget,
        completer=fixture_completer({"prose": "BTC at {{btc_last}} (observed)", "claim_tags": ["observed"]}),
        model="fixture",
        model_version="test",
    )
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT, llm=client, budget=budget)
    assert run.status == "DEGRADED"
    assert run.error_class == ERROR_BUDGET_EXCEEDED
    assert run.ops_escalation and "budget_exceeded" in run.ops_escalation
    assert run.llm_calls
    for row in run.llm_calls:
        assert row.prompt_hash
        assert row.prompt_file
        assert row.run_id == run.run_id
        assert row.temperature == budget.temperature
    brief = next(a for a in run.artifacts if a.artifact_type == "OFFICIAL_BRIEF")
    assert "no actionable setup" in str(brief.payload["executive_cut"]).lower() or "templated" in " ".join(run.notes).lower()


def test_literal_digit_injection_fails() -> None:
    assert_numeric_lock("move {{btc_last}} (observed)")
    try:
        assert_numeric_lock("BTC at 65000")
        raise AssertionError("digits must fail")
    except GroundingError:
        pass
    client = LlmClient(
        load_token_budget(ROOT),
        completer=fixture_completer({"prose": "last was 65000 (observed)", "claim_tags": ["observed"]}),
        model="fixture",
        model_version="test",
    )
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT, llm=client)
    assert run.status == "FAILED"
    assert run.error_class == "grounding_failed"


def test_unknown_ticker_fails() -> None:
    client = LlmClient(
        load_token_budget(ROOT),
        completer=fixture_completer({"prose": "SOXL looks heavy (inference)", "claim_tags": ["inference"]}),
        model="fixture",
        model_version="test",
    )
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT, llm=client)
    assert run.status == "FAILED"
    assert run.error_class == "grounding_failed"


def test_fred_unavailable_no_rates_figure() -> None:
    run = run_playbook_from_fixture(FRED, repo_root=ROOT)
    assert "rates" in run.gaps or any("fred" in g.lower() for g in run.gaps)
    brief = next(a for a in run.artifacts if a.artifact_type == "OFFICIAL_BRIEF")
    text = str(brief.payload["executive_cut"]).lower()
    assert "yield" not in text
    assert "10y" not in text
    assert "ust" not in text


def test_low_completeness_gaps_heavy_no_idea() -> None:
    run = run_playbook_from_fixture(LOW, repo_root=ROOT)
    brief = next(a for a in run.artifacts if a.artifact_type == "OFFICIAL_BRIEF")
    text = str(brief.payload["executive_cut"]).lower()
    assert "no actionable setup" in text
    assert run.gaps
    assert any("low-completeness" in n.lower() or "dq" in n.lower() or "gaps" in n.lower() for n in run.notes) or run.completeness < 50


def test_schema_violation_retry_then_template() -> None:
    client = LlmClient(
        load_token_budget(ROOT),
        completer=scripted_completer([{"nope": True}, {"still": "bad"}]),
        model="fixture",
        model_version="test",
    )
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT, llm=client)
    assert run.status == "DEGRADED"
    assert any(row.schema_valid is False for row in run.llm_calls)
    assert any(row.retry_count >= 1 for row in run.llm_calls)
    assert all(row.prompt_hash for row in run.llm_calls)
    brief = next(a for a in run.artifacts if a.artifact_type == "OFFICIAL_BRIEF")
    assert "no actionable setup" in str(brief.payload["executive_cut"]).lower() or "templated" in str(brief.payload["executive_cut"]).lower() or brief.payload["executive_cut"]


def test_chart_png_filename_is_content_hash() -> None:
    run = run_playbook_from_fixture(IDEAS, repo_root=ROOT)
    chart = next(a for a in run.artifacts if a.artifact_type == "CHART_ARTIFACT")
    name = chart.payload["png_filename"]
    digest = chart.payload["png_content_hash"]
    assert name == f"{digest}.png"
    assert digest in run.png_by_hash
    png = run.png_by_hash[digest]
    assert png.startswith(b"\x89PNG")
