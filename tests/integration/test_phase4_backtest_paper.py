"""Integration: research_run + paper_trade tables, params_hash, paper gates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect, select

from mm_backtest.harness import run_backtest
from mm_backtest.loaders import load_fixture_file
from mm_backtest.strategy import BuyHoldStrategy
from mm_common.enums import DataQuality, EvidenceType, ResearchRunKind, SourceKind
from mm_common.ids import new_ulid
from mm_common.schemas import ClaimIdentity, ObservationEnvelope
from mm_memory.db import make_engine
from mm_memory.migrate import current_revision
from mm_memory.models import PaperTrade, ResearchRun
from mm_memory.paper_repository import PaperRepository
from mm_memory.repository import ObservationRepository
from mm_memory.run_repository import ResearchRunRepository
from mm_memory.thesis_repository import ThesisRepository
from mm_paper.ledger import open_paper_trade
from mm_research_kit.evidence import link_evidence
from mm_research_kit.skeptic import record_skeptic_verdict
from mm_research_kit.workspace import ThesisSpec, create_thesis_from_intent

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"
CLEAN = ROOT / "tests" / "fixtures" / "backtest" / "clean_bars.json"


def _seed_observation(session) -> str:
    repo = ObservationRepository(session)
    ts = datetime(2026, 9, 16, tzinfo=timezone.utc)
    identity = ClaimIdentity(
        source_name="hyperliquid.info",
        instrument="BTC",
        metric="funding",
        market_time=ts,
        value="0.0001",
    )
    envelope = ObservationEnvelope(
        source_name="hyperliquid.info",
        source_kind=SourceKind.EXCHANGE,
        source_url_or_id="info:funding",
        published_at=ts,
        ingested_at=ts,
        market_time=ts,
        claim_text="BTC funding 0.0001",
        confidence=0.9,
        evidence_type=EvidenceType.METRIC,
        data_quality=DataQuality.OK,
        payload={"value": "0.0001"},
        instrument="BTC",
        metric="funding",
        identity=identity,
    )
    return repo.put_observation(envelope).observation.id


def test_phase4_tables_exist(postgres_dsn: str) -> None:
    engine = make_engine(postgres_dsn)
    tables = set(inspect(engine).get_table_names())
    assert {"research_run", "paper_trade"} <= tables
    assert current_revision(postgres_dsn) == "0006_phase5a_status_events"


def test_research_run_and_paper_trade_persist(db_session, tmp_path: Path) -> None:
    observation_id = _seed_observation(db_session)
    created = create_thesis_from_intent(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        spec=ThesisSpec(goal="BTC funding fade", owner="Research", instrument="BTC"),
        repo_root=tmp_path,
    )
    link_evidence(created.path, observation_id=observation_id, role="supports")
    record_skeptic_verdict(created.path, verdict="pass", reviewer="Skeptic")
    thesis_repo = ThesisRepository(db_session)
    thesis = thesis_repo.upsert(
        slug=created.slug,
        status="in_skeptic",
        author_role="Research",
        artifact_git_path=created.artifact_git_path,
        artifact_content_hash=created.artifact_content_hash,
        instrument="BTC",
    ).thesis

    bars, facts, _ = load_fixture_file(CLEAN)
    first = run_backtest(bars, BuyHoldStrategy(), facts=facts)
    second = run_backtest(bars, BuyHoldStrategy(), facts=facts)
    assert first.params_hash == second.params_hash

    run_repo = ResearchRunRepository(db_session)
    started = datetime(2026, 9, 16, 12, tzinfo=timezone.utc)
    run_repo.record(
        kind=ResearchRunKind.BACKTEST.value,
        params_hash=first.params_hash,
        started_at=started,
        finished_at=started,
        thesis_id=thesis.id,
        result_summary=first.summary(),
        artifact_paths=["backtests/example.json"],
    )
    db_session.flush()
    rows = list(db_session.scalars(select(ResearchRun).where(ResearchRun.params_hash == first.params_hash)).all())
    assert len(rows) == 1
    assert rows[0].thesis_id == thesis.id
    assert rows[0].kind == "backtest"

    opened = open_paper_trade(
        research_root=tmp_path / "research",
        templates_root=TEMPLATES,
        repo_root=tmp_path,
        slug=created.slug,
        size="0.01",
        max_loss="500 USDC",
        invalidation="Close < 60000 on the daily",
        expected_path=["funding fades"],
        thesis_id=thesis.id,
    )
    PaperRepository(db_session).insert(
        trade_id=opened.id,
        thesis_id=thesis.id,
        opened_at=opened.opened_at,
        instrument=opened.instrument,
        size=opened.size,
        invalidation=opened.invalidation,
        max_loss=opened.max_loss,
        max_loss_amount=opened.max_loss_amount,
        intent_json=opened.intent_json(),
        fills_json=[fill.canonical() for fill in opened.fills],
        expected_path=list(opened.expected_path),
        artifact_git_path=opened.artifact_git_path,
        entry_thesis_snapshot_hash=opened.entry_thesis_snapshot_hash,
        slippage_bps=opened.slippage_bps,
        notes=opened.notes or None,
    )
    db_session.commit()
    stored = db_session.get(PaperTrade, opened.id)
    assert stored is not None
    assert stored.invalidation
    assert stored.max_loss_amount > 0
    assert stored.thesis_id == thesis.id
    assert stored.status == "open"


def test_ulid_still_26() -> None:
    assert len(new_ulid()) == 26
