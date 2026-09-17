"""Post-IPO / reclaim screen: closed verdicts, language, honest unavailable data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from mm_research_kit.post_ipo_reclaim.decide import score_instrument
from mm_research_kit.post_ipo_reclaim.engine import run_screen, write_screen
from mm_research_kit.post_ipo_reclaim.models import (
    DATA_QUALITY_VALUES,
    SCREEN_FOOTER,
    ScreenInstrument,
    ScreenUniverse,
)
from mm_research_kit.post_ipo_reclaim.universe import universe_from_mapping
from mm_research_kit.quant_review.engine import empty_snapshot, snapshot_from_mapping
from mm_research_kit.quant_review.language import assert_language_clean, language_violations
from mm_research_kit.quant_review.models import (
    InstrumentPrint,
    QuantReasonCode,
    QuantVerdict,
    ReclaimObservables,
    ReviewSnapshot,
    SeriesOverlay,
)

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
AS_OF = datetime(2026, 9, 17, 2, 42, tzinfo=UTC)


def _spec(**kwargs) -> ScreenInstrument:
    defaults = dict(
        symbol="CRCL",
        raw_symbols=("CRCL",),
        asset_class="equity",
        venue="unknown",
        sector="crypto_equity",
        benchmark="QQQ",
        peers=("HOOD", "GLXY"),
        post_ipo=True,
        listing_date=None,
        role="candidate",
        membership="screen_only",
    )
    defaults.update(kwargs)
    return ScreenInstrument(**defaults)


def _universe(*specs: ScreenInstrument) -> ScreenUniverse:
    return ScreenUniverse(
        version="test",
        status="screen_only",
        kind="post_ipo_reclaim_screen",
        desk="Equities & Post-IPO Desk",
        locked_membership_file="config/universe.yaml",
        instruments=specs,
        context=(),
        symbol_map={s.symbol: s.symbol for s in specs},
    )


def _print(symbol: str, chg_pct: float, last: float = 10.0, dq: str = "ok") -> InstrumentPrint:
    return InstrumentPrint(
        raw_symbol=symbol,
        symbol=symbol,
        last=last,
        chg=0.1,
        chg_pct=chg_pct,
        source="test",
        timestamp=AS_OF.isoformat(),
        capture="test",
        data_quality=dq,
        evidence_confidence=0.5,
    )


def test_screen_universe_is_screen_only_and_does_not_expand_membership() -> None:
    data = yaml.safe_load((ROOT / "config/equities/post_ipo_reclaim.yaml").read_text(encoding="utf-8"))
    universe = universe_from_mapping(data)
    assert universe.kind == "post_ipo_reclaim_screen"
    assert universe.status == "screen_only"
    assert universe.desk == "Equities & Post-IPO Desk"
    symbols = {row.symbol for row in universe.candidates()}
    assert symbols == {"CRCL", "HOOD"}
    locked = yaml.safe_load((ROOT / "config/universe.yaml").read_text(encoding="utf-8"))
    membership = set(locked["crypto_perps"]) | set(locked["equities"])
    in_universe = set(locked["in_universe"]["crypto_perps"]) | set(locked["in_universe"]["equities"])
    watch_only = set(locked["watch_only"]["crypto_perps"]) | set(locked["watch_only"]["equities"])
    assert locked["in_universe"]["equities"] == ["NVDA", "AVGO", "MSFT", "META", "JPM", "XOM"]
    assert "active_calls" not in locked
    assert symbols.isdisjoint(membership)
    assert symbols.isdisjoint(in_universe)
    assert symbols.isdisjoint(watch_only)
    assert "CRCL" not in membership
    assert "HOOD" not in membership


def test_empty_snapshot_is_insufficient_and_unavailable() -> None:
    spec = _spec()
    result = run_screen(_universe(spec), empty_snapshot(as_of_knowledge=AS_OF), review_at=AS_OF, generated_at=AS_OF)
    row = result.rows[0]
    assert row.verdict == QuantVerdict.INSUFFICIENT_DATA.value
    assert QuantReasonCode.STALE_OR_PARTIAL_DATA.value in row.reason_codes
    assert row.data_quality == "unavailable"
    last = next(m for m in row.metrics if m.name == "last")
    assert last.value.startswith("unavailable")
    assert "not fabricated" in last.value
    mdd = next(m for m in row.metrics if m.name == "drawdown_vs_ref_high")
    assert mdd.value.startswith("unavailable")
    assert SCREEN_FOOTER in result.markdown
    assert language_violations(result.markdown) == []


def test_post_ipo_drawdown_alone_is_defer_not_research_priority() -> None:
    spec = _spec()
    hood = _spec(symbol="HOOD", raw_symbols=("HOOD",), peers=("CRCL",), benchmark="QQQ")
    snap = ReviewSnapshot(
        as_of_knowledge=AS_OF,
        source="test",
        prints=(_print("CRCL", -6.78, last=80.45), _print("HOOD", -5.47, last=104.42), _print("QQQ", 0.03, last=704.72)),
    )
    row = score_instrument(
        spec,
        snap,
        universe=_universe(spec, hood),
        review_at=AS_OF,
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert row.verdict != QuantVerdict.RESEARCH_PRIORITY.value
    assert row.verdict == QuantVerdict.DEFER.value
    assert QuantReasonCode.NO_CATALYST.value in row.reason_codes
    assert QuantReasonCode.THESIS_NOT_FALSIFIABLE.value in row.reason_codes
    assert QuantReasonCode.RECLAIM_UNCONFIRMED.value in row.reason_codes
    assert row.data_quality in DATA_QUALITY_VALUES
    last = next(m for m in row.metrics if m.name == "last")
    assert last.value == "80.45"
    assert last.source == "test"


def test_confirmed_reclaim_without_listing_is_not_research_priority() -> None:
    spec = _spec(listing_date=None)
    overlay = SeriesOverlay(
        symbol="CRCL",
        source="test-overlay",
        asof="2026-09-17",
        captured_at=AS_OF.isoformat(),
        last_close=80.45,
        rel_short=0.12,
        mdd=-0.4,
        n_bars=80,
        bench="QQQ",
        data_quality="ok",
        adv=1_000_000,
    )
    snap = ReviewSnapshot(
        as_of_knowledge=AS_OF,
        source="test",
        prints=(_print("CRCL", 2.1, last=80.45), _print("HOOD", -0.2), _print("QQQ", 0.03)),
        overlays=(overlay,),
        reclaim={"CRCL": ReclaimObservables(prior_breakdown_level="90", reclaim_of_level="90", hold_sessions=3)},
        catalysts={"CRCL": "dated lock-up expiry at T+1"},
        invalidations={"CRCL": "daily close back below the reclaimed level"},
        overlooked={"CRCL": "thin coverage vs peers"},
        liquidity_ok={"CRCL": True},
    )
    row = score_instrument(
        spec,
        snap,
        universe=_universe(spec),
        review_at=AS_OF,
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert row.verdict != QuantVerdict.RESEARCH_PRIORITY.value
    assert QuantReasonCode.INSUFFICIENT_HISTORY.value in row.reason_codes
    mdd = next(m for m in row.metrics if m.name == "drawdown_vs_ref_high")
    assert mdd.value == "-0.4"
    assert mdd.source == "test-overlay"
    assert mdd.freshness == "fresh"


def test_fixture_subset_matches_parent_prints_and_does_not_invent() -> None:
    parent = yaml.safe_load((ROOT / "tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml").read_text())
    subset = yaml.safe_load((ROOT / "tests/fixtures/equities/post_ipo_reclaim_snapshot.yaml").read_text())
    parent_by_raw = {row["raw"]: row for row in parent["prints"]}
    for row in subset["prints"]:
        src = parent_by_raw[row["raw"]]
        assert row["last"] == src["last"]
        assert row["chg"] == src["chg"]
        assert row["chg_pct"] == src["chg_pct"]
    assert subset["as_of_knowledge"] == parent["as_of_knowledge"]
    assert "overlays" not in subset or not subset.get("overlays")


def test_repo_fixture_run_uses_closed_vocab_and_footer(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / "config/equities/post_ipo_reclaim.yaml").read_text(encoding="utf-8"))
    fixture = yaml.safe_load((ROOT / "tests/fixtures/equities/post_ipo_reclaim_snapshot.yaml").read_text())
    universe = universe_from_mapping(data)
    snapshot = snapshot_from_mapping(fixture, symbol_map=universe.symbol_map)
    result = run_screen(universe, snapshot, review_at=AS_OF, generated_at=AS_OF, screen_date="2026-09-17")
    allowed_v = {v.value for v in QuantVerdict}
    allowed_c = {c.value for c in QuantReasonCode}
    assert {row.instrument for row in result.rows} == {"CRCL", "HOOD"}
    for row in result.rows:
        assert row.verdict in allowed_v
        assert row.reason_codes
        assert set(row.reason_codes) <= allowed_c
        assert row.data_quality in DATA_QUALITY_VALUES
        assert row.verdict != QuantVerdict.RESEARCH_PRIORITY.value
        assert row.membership == "screen_only"
        listing = next(m for m in row.metrics if m.name == "listing_date")
        assert listing.freshness == "unavailable"
        mdd = next(m for m in row.metrics if m.name == "drawdown_vs_ref_high")
        assert mdd.freshness == "unavailable"
        assert "not fabricated" in mdd.value
    assert SCREEN_FOOTER in result.markdown
    assert "Principal gate still required" in result.markdown
    assert language_violations(result.markdown) == []
    assert_language_clean(result.markdown)
    assert "Start small: Quant-review TV equities" in result.markdown
    assert "{'Start small'" not in result.markdown
    written = write_screen(result, research_root=tmp_path)
    text = Path(written["screen"]).read_text(encoding="utf-8")
    assert "80.45" in text
    assert "104.42" in text
    assert "unavailable — not in this snapshot; not fabricated" in text
