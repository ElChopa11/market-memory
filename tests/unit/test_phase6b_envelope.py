"""Phase 6b: regime tag on mesh envelopes + Coord assemble if flow/macro fail."""

from __future__ import annotations

from pathlib import Path

from mm_desks.envelope import envelope_from_output
from mm_desks.mesh import mesh_from_fixture
from mm_desks.orchestrator import run_from_fixture
from mm_desks.protocol import FAILED, OK, REGIME_PLACEHOLDER

ROOT = Path(__file__).resolve().parents[2]
HAPPY = ROOT / "tests" / "fixtures" / "phase6b" / "frozen_day.json"
MISSING = ROOT / "tests" / "fixtures" / "phase6b" / "missing_feeds.json"
FIVE_D = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_envelopes_carry_macro_regime_tag() -> None:
    result = run_from_fixture(HAPPY, repo_root=ROOT)
    by = {row.slug: row for row in result.desks}
    assert by["intel"].regime == "risk_on_usd_mid"
    assert by["intel"].payload["regime_tag"] == "risk_on_usd_mid"
    for slug, row in by.items():
        assert row.regime == "risk_on_usd_mid", slug
        env = envelope_from_output(row, repo_root=ROOT)
        assert env.regime == "risk_on_usd_mid"
        assert env.header()["regime"] == "risk_on_usd_mid"
    assert "Regime tag" in result.pack_markdown
    assert "risk_on_usd_mid" in result.pack_markdown


def test_mesh_envelopes_include_flow_and_macro() -> None:
    first = mesh_from_fixture(HAPPY, repo_root=ROOT)
    second = mesh_from_fixture(HAPPY, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    by_desk = {env.desk: env for env in first.assemble.envelopes}
    assert "intel" in by_desk
    assert "flow" not in by_desk
    assert "macro" not in by_desk
    assert by_desk["intel"].status == OK
    intel_body = by_desk["intel"].body.get("payload") or {}
    assert intel_body.get("flow", {}).get("verdicts")
    assert intel_body.get("macro", {}).get("regime_tag") == "risk_on_usd_mid"
    for env in first.assemble.envelopes:
        assert env.regime == "risk_on_usd_mid"
    assert first.assemble.coord.regime == "risk_on_usd_mid"


def test_killed_intel_ops_still_assembles() -> None:
    result = mesh_from_fixture(HAPPY, repo_root=ROOT, killed=("intel",))
    by_desk = {env.desk: env for env in result.assemble.envelopes}
    assert by_desk["intel"].status == FAILED
    assert by_desk["intel"].error_class == "desk_killed"
    assert result.assemble.status == FAILED
    assert by_desk["research"].status != FAILED
    # No successful Intel macro tag → remaining desks keep the placeholder.
    assert by_desk["research"].regime == REGIME_PLACEHOLDER


def test_intel_only_carries_regime_when_macro_inputs_exist() -> None:
    result = run_from_fixture(FIVE_D, repo_root=ROOT, slugs=("intel",))
    assert result.desks[0].regime == "risk_on_usd_mid"
