"""Phase 6c-1 desk consolidation: exactly five publishing desks."""

from __future__ import annotations

from pathlib import Path

from mm_desks.orchestrator import PIPELINE, run_from_fixture
from mm_desks.roster import MESH_DESKS, PUBLISHING_DESKS, RETIRED_DESK_SLUGS, SLEEVE_MAP

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_publishing_roster_is_exactly_five() -> None:
    assert PIPELINE == ("intel", "research", "quant", "ic_risk", "ops")
    assert PUBLISHING_DESKS == PIPELINE
    assert MESH_DESKS == ("intel", "research", "quant", "ic_risk")
    assert "coord" in RETIRED_DESK_SLUGS
    assert SLEEVE_MAP["crypto"] == "research"
    assert SLEEVE_MAP["flow"] == "intel"
    assert SLEEVE_MAP["skeptic"] == "ic_risk"


def test_cadence_yaml_lists_only_five_desks() -> None:
    cadence = (ROOT / "config" / "desks" / "cadence.yaml").read_text(encoding="utf-8")
    assert "desk.intel.output" in cadence
    assert "desk.research.output" in cadence
    assert "desk.quant.output" in cadence
    assert "desk.ic_risk.output" in cadence
    assert "desk.ops.output" in cadence
    assert "coord.assemble" in cadence
    for retired in ("desk.crypto.output", "desk.equities.output", "desk.flow.output", "desk.macro.output"):
        assert retired not in cadence


def test_telegram_yaml_five_desk_routes() -> None:
    tg = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    for slug in ("intel", "research", "quant", "ic_risk", "ops"):
        assert f"{slug}:" in tg
    assert "TELEGRAM_CHAT_ID_RESEARCH" in tg
    assert "TELEGRAM_CHAT_ID_IC_RISK" in tg
    assert "TELEGRAM_CHAT_ID_CRYPTO" not in tg
    assert "TELEGRAM_CHAT_ID_CHART" not in tg


def test_pipeline_run_emits_five_desks() -> None:
    result = run_from_fixture(FIXTURE, repo_root=ROOT)
    assert [row.slug for row in result.desks] == list(PIPELINE)
    ic = {row.slug: row for row in result.desks}["ic_risk"]
    assert ic.payload["gates"] == ["skeptic", "risk"]
    intel = {row.slug: row for row in result.desks}["intel"]
    assert "flow" in intel.payload
    assert "macro" in intel.payload
    research = {row.slug: row for row in result.desks}["research"]
    assert research.payload["sleeves"] == ("crypto", "equities", "chart")


def test_unknown_retired_slug_is_rejected() -> None:
    try:
        run_from_fixture(FIXTURE, repo_root=ROOT, slugs=("crypto",))
    except ValueError as exc:
        assert "crypto" in str(exc)
        return
    raise AssertionError("retired slug crypto should not be a publishing desk")
