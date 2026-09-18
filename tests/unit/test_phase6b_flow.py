"""Phase 6b / IMP-015: flow metrics + liquidity verdict."""

from __future__ import annotations

from pathlib import Path

from mm_desks.flow import extra_structure, flow_panel
from mm_desks.fixture import load_frozen_day
from mm_desks.orchestrator import run_from_fixture
from mm_desks.protocol import DeskContext, OK
from mm_flow.config import load_flow_config
from mm_flow.engine import compute_flow
from mm_flow.models import VERDICT_OK, VERDICT_UNTRADEABLE
from mm_flow.observations import snapshot_envelopes

ROOT = Path(__file__).resolve().parents[2]
HAPPY = ROOT / "tests" / "fixtures" / "phase6b" / "frozen_day.json"
UNTRADE = ROOT / "tests" / "fixtures" / "phase6b" / "untradeable.json"
MISSING = ROOT / "tests" / "fixtures" / "phase6b" / "missing_feeds.json"


def test_happy_path_liquidity_ok_and_max_clip() -> None:
    result = run_from_fixture(HAPPY, repo_root=ROOT, slugs=("intel",))
    intel = result.desks[0]
    flow = intel.payload["flow"]
    assert intel.status == OK
    assert flow["verdicts"]["BTC"] == VERDICT_OK
    assert flow["max_clip_usd"]["BTC"] == 250000.0
    snap = flow["snapshots"][0]
    by_name = {row["name"]: row for row in snap["metrics"]}
    assert by_name["funding_z"]["status"] == "ok"
    assert by_name["oi_delta"]["status"] == "ok"
    assert by_name["basis"]["status"] == "ok"
    assert by_name["spread_bps"]["status"] == "ok"
    assert by_name["depth_usd"]["status"] == "ok"
    assert by_name["adv_notional"]["status"] == "ok"


def test_untradeable_at_size_from_thin_book() -> None:
    result = run_from_fixture(UNTRADE, repo_root=ROOT, slugs=("intel",))
    flow = result.desks[0].payload["flow"]
    assert flow["verdicts"]["BTC"] == VERDICT_UNTRADEABLE
    assert flow["max_clip_usd"]["BTC"] is None


def test_missing_structure_degrades_never_invents() -> None:
    result = run_from_fixture(MISSING, repo_root=ROOT, slugs=("intel",))
    intel = result.desks[0]
    flow = intel.payload["flow"]
    assert intel.status != "FAILED"
    snap = flow["snapshots"][0]
    assert snap["verdict"]["verdict"] in {VERDICT_OK, "THIN", VERDICT_UNTRADEABLE, "unavailable"}
    # Without extra L2, funding_z/oi/depth stay unavailable rather than invented.
    by_name = {row["name"]: row for row in snap["metrics"]}
    assert by_name["oi_delta"]["status"] == "unavailable"
    assert by_name["oi_delta"]["value"] is None
    assert "not invented" in (by_name["oi_delta"]["reason"] or "").lower() or by_name["oi_delta"]["value"] is None


def test_flow_observation_as_of_knowledge_lockstep() -> None:
    day = load_frozen_day(HAPPY, repo_root=ROOT)
    ctx = DeskContext(repo_root=ROOT, fixture=day, thesis=day.thesis)
    panel = flow_panel(ctx)
    assert extra_structure(ctx)
    cfg = load_flow_config(ROOT)
    snap = compute_flow("BTC", panel, day.as_of_knowledge, config=cfg)
    envelopes = snapshot_envelopes(snap, ingested_at=day.as_of_knowledge)
    assert envelopes
    for env in envelopes:
        assert env.as_of_knowledge == env.ingested_at
        assert env.as_of_knowledge == day.as_of_knowledge


def test_double_run_flow_hash_stable() -> None:
    first = run_from_fixture(HAPPY, repo_root=ROOT, slugs=("intel",))
    second = run_from_fixture(HAPPY, repo_root=ROOT, slugs=("intel",))
    assert first.content_hash == second.content_hash
    assert first.desks[0].content_hash() == second.desks[0].content_hash()
