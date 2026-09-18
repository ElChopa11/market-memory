"""Phase 6a mesh: missing/killed desk → Coord assembles FAILED + error_class."""

from __future__ import annotations

from pathlib import Path

from mm_desks.bus import InMemoryBus, InMemoryEnvelopeStore
from mm_desks.cadence import CHANNEL_ASSEMBLE, CHANNEL_DQ, all_channels
from mm_desks.envelope import ERROR_CLASS_KILLED, ERROR_CLASS_MISSING
from mm_desks.mesh import mesh_from_fixture
from mm_desks.protocol import FAILED

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "phase5d" / "frozen_day.json"


def test_mesh_double_run_identical_hashes() -> None:
    first = mesh_from_fixture(FIXTURE, repo_root=ROOT)
    second = mesh_from_fixture(FIXTURE, repo_root=ROOT)
    assert first.content_hash == second.content_hash
    assert len(first.content_hash) == 64
    by_desk = {env.desk: env for env in first.assemble.envelopes}
    assert set(by_desk) == {"intel", "research", "quant", "ic_risk"}
    for env in first.assemble.envelopes:
        assert env.status != FAILED
        assert env.error_class is None
        assert env.regime == "risk_on_usd_mid"
    assert first.assemble.coord.channel == "desk.ops.output"
    assert first.assemble.pack_markdown
    assert "HEADER" in first.assemble.pack_markdown


def test_killed_desk_assemble_failed_error_class() -> None:
    result = mesh_from_fixture(FIXTURE, repo_root=ROOT, killed=("intel",))
    by_desk = {env.desk: env for env in result.assemble.envelopes}
    intel = by_desk["intel"]
    assert intel.status == FAILED
    assert intel.error_class == ERROR_CLASS_KILLED
    assert result.assemble.status == FAILED
    assert result.assemble.health["intel"].error_class == ERROR_CLASS_KILLED
    assert result.assemble.health["intel"].status == FAILED
    pack = result.assemble.pack_markdown
    assert "intel" in pack
    assert ERROR_CLASS_KILLED in pack or "FAILED" in pack
    assert "research" in result.as_public_dict()["desks"]
    assert result.as_public_dict()["desks"]["research"]["status"] != FAILED
    # Double-run still stable while one desk is killed.
    again = mesh_from_fixture(FIXTURE, repo_root=ROOT, killed=("intel",))
    assert again.content_hash == result.content_hash
    assert again.assemble.envelopes[0].error_class == ERROR_CLASS_KILLED or by_desk["intel"].error_class == ERROR_CLASS_KILLED


def test_missing_desk_without_kill_is_desk_missing() -> None:
    store = InMemoryEnvelopeStore()
    bus = InMemoryBus()
    happy = mesh_from_fixture(FIXTURE, repo_root=ROOT, store=store, bus=bus)
    # Drop intel from the store to simulate a vanished publisher.
    store._by_id = {k: v for k, v in store._by_id.items() if v.desk != "intel"}
    store._order = [i for i in store._order if i in store._by_id]
    from mm_desks.fixture import load_frozen_day
    from mm_desks.mesh import CoordMeshWorker
    from mm_desks.protocol import DeskContext

    day = load_frozen_day(FIXTURE, repo_root=ROOT)
    ctx = DeskContext(repo_root=ROOT, fixture=day, thesis=day.thesis)
    worker = CoordMeshWorker(store, bus, repo_root=ROOT)
    assembled = worker.assemble(day.as_of_knowledge, ctx)
    intel = {env.desk: env for env in assembled.envelopes}["intel"]
    assert intel.status == FAILED
    assert intel.error_class == ERROR_CLASS_MISSING
    assert assembled.status == FAILED
    assert happy.content_hash != assembled.content_hash


def test_in_memory_bus_notifies_output_and_dq_on_degraded() -> None:
    from mm_desks.mesh import mesh_from_fixture as run

    missing = ROOT / "tests" / "fixtures" / "phase5d" / "missing_feed.json"
    bus = InMemoryBus()
    store = InMemoryEnvelopeStore()
    result = run(missing, repo_root=ROOT, store=store, bus=bus)
    channels = {event.channel for event in bus.events}
    assert "desk.intel.output" in channels
    assert CHANNEL_DQ in channels
    assert CHANNEL_ASSEMBLE in channels
    intel = {env.desk: env for env in result.assemble.envelopes}["intel"]
    assert intel.status != FAILED
    notify = next(event for event in bus.events if event.channel == "desk.intel.output")
    assert "id" in notify.payload
    assert "content_hash" in notify.payload
    assert "body" not in notify.payload


def test_channels_include_principal_topics() -> None:
    channels = all_channels(ROOT)
    assert "desk.intel.output" in channels
    assert "desk.research.output" in channels
    assert "desk.quant.output" in channels
    assert "desk.ic_risk.output" in channels
    assert "desk.ops.output" in channels
    assert "coord.assemble" in channels
    assert "dq.event" in channels
