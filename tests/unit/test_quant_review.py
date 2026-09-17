"""Quant Review Board: verdicts, promotion gates, language, Track D/C discipline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from mm_research_kit.errors import GateError
from mm_research_kit.quant_review.decide import review_instrument
from mm_research_kit.quant_review.engine import empty_snapshot, run_board, snapshot_from_mapping, write_board
from mm_research_kit.quant_review.language import assert_language_clean, language_violations
from mm_research_kit.quant_review.models import (
    BOARD_FOOTER,
    LABEL_ARBITRAGE,
    LABEL_RELATIVE_VALUE,
    LABEL_UNEXECUTABLE_ARB,
    ArbPackage,
    InstrumentPrint,
    InstrumentSpec,
    QuantReasonCode,
    QuantVerdict,
    ReclaimObservables,
    ReviewSnapshot,
    SeriesOverlay,
    UniverseSpec,
)
from mm_research_kit.quant_review.render import render_card
from mm_research_kit.quant_review.universe import normalize_symbol, universe_from_mapping

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
AS_OF = datetime(2026, 9, 17, 2, 42, tzinfo=UTC)


def _spec(**kwargs) -> InstrumentSpec:
    defaults = dict(
        symbol="AAA",
        raw_symbols=("AAA",),
        asset_class="equity",
        venue="unknown",
        sector="other_us",
        benchmark="SPX",
        peers=("BBB",),
        tracks=("A", "B"),
        post_ipo=False,
    )
    defaults.update(kwargs)
    return InstrumentSpec(**defaults)


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


def _snapshot(*, prints: list[InstrumentPrint], **kwargs) -> ReviewSnapshot:
    return ReviewSnapshot(as_of_knowledge=AS_OF, source="test", prints=tuple(prints), **kwargs)


def _universe(*specs: InstrumentSpec) -> UniverseSpec:
    return UniverseSpec(
        version="test",
        status="test",
        kind="quant_review",
        instruments=specs,
        symbol_map={s.symbol: s.symbol for s in specs},
        peer_groups={},
        arb_pairs=(),
    )


def test_repo_universe_normalizes_screenshot_symbols() -> None:
    data = yaml.safe_load((ROOT / "config/quant_review_universe.yaml").read_text())
    universe = universe_from_mapping(data)
    assert universe.kind == "quant_review"
    assert normalize_symbol("BTCUSDC.P", universe.symbol_map) == "BTC"
    assert normalize_symbol("BTC1!", universe.symbol_map) == "BTC_FUT"
    assert normalize_symbol("NQ1!", universe.symbol_map) == "NQ"
    assert normalize_symbol("SAMSUNGUSDT.F", universe.symbol_map) == "SAMSUNG"
    assert "CRCL" in universe.by_symbol()
    assert universe.by_symbol()["CRCL"].post_ipo is True
    # Do not expand locked ingest membership.
    locked = yaml.safe_load((ROOT / "config/universe.yaml").read_text())
    assert locked["crypto_perps"] == ["BTC", "ETH", "UNI", "AAVE"]
    assert "PONS" not in locked["crypto_perps"]
    assert "SOL" not in locked["crypto_perps"]


def test_no_data_is_insufficient_data() -> None:
    spec = _spec(symbol="ZZZ", peers=())
    result = run_board(_universe(spec), empty_snapshot(as_of_knowledge=AS_OF), review_at=AS_OF, generated_at=AS_OF)
    card = result.cards[0]
    assert card.verdict == QuantVerdict.INSUFFICIENT_DATA.value
    assert QuantReasonCode.STALE_OR_PARTIAL_DATA.value in card.reason_codes
    assert card.reason_codes


def test_stale_data_blocks_promotion() -> None:
    spec = _spec(symbol="AAA", peers=("BBB",))
    overlay = SeriesOverlay(
        symbol="AAA",
        source="test",
        asof="2026-08-01",
        captured_at="2026-08-01T00:00:00Z",
        ret_short=0.2,
        rel_short=0.2,
        n_bars=80,
        data_quality="ok",
        adv=1_000_000,
    )
    snap = ReviewSnapshot(
        as_of_knowledge=datetime(2026, 8, 1, tzinfo=UTC),
        source="test",
        prints=(_print("AAA", 8.0), _print("BBB", 0.1)),
        overlays=(overlay,),
        catalysts={"AAA": "dated filing at T+1"},
        invalidations={"AAA": "daily close back inside peer band"},
        overlooked={"AAA": "no coverage vs peers"},
        liquidity_ok={"AAA": True},
        addressed_warnings={
            "AAA": (
                QuantReasonCode.DUPLICATE_BETA.value,
                QuantReasonCode.CORRELATED_EXPOSURE.value,
                QuantReasonCode.INADEQUATE_LIQUIDITY.value,
            )
        },
        reclaim={"AAA": ReclaimObservables(prior_breakdown_level="12", reclaim_of_level="12", hold_sessions=3)},
    )
    card = review_instrument(
        spec,
        snap,
        universe=_universe(spec, _spec(symbol="BBB", peers=("AAA",))),
        review_at=AS_OF,
        review_date="2026-09-17",
        as_of_knowledge=snap.as_of_knowledge,
        stale_after=timedelta(hours=36),
    )
    assert card.verdict != QuantVerdict.RESEARCH_PRIORITY.value
    assert QuantReasonCode.STALE_OR_PARTIAL_DATA.value in card.reason_codes
    assert card.promotion.fresh_attributable_data is False
    assert card.promotion.all_met is False


def test_ordinary_relative_value_is_not_arbitrage() -> None:
    spec = _spec(symbol="ETH", sector="crypto_perp", benchmark="BTC", peers=("BTC",), tracks=("A", "B", "D"))
    btc = _spec(symbol="BTC", sector="crypto_perp", benchmark="BTC", peers=("ETH",), tracks=("A", "B", "D"))
    universe = UniverseSpec(
        version="t",
        status="t",
        kind="quant_review",
        instruments=(spec, btc),
        symbol_map={"ETH": "ETH", "BTC": "BTC"},
        peer_groups={},
        arb_pairs=(("ETH", "BTC", "not convertible"),),
    )
    snap = _snapshot(prints=[_print("ETH", 0.55, last=2430), _print("BTC", 0.29, last=76399)])
    card = review_instrument(
        spec,
        snap,
        universe=universe,
        review_at=AS_OF,
        review_date="2026-09-17",
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert LABEL_ARBITRAGE not in card.labels
    assert card.executable_arb is False
    assert LABEL_UNEXECUTABLE_ARB in card.labels or QuantReasonCode.UNEXECUTABLE_ARB.value in card.reason_codes
    text = render_card(card)
    assert "relative-value" in text.lower() or LABEL_RELATIVE_VALUE in card.labels or "ordinary" in card.unusual.lower()
    assert "MAKE" not in text


def test_complete_track_d_may_use_arbitrage_label() -> None:
    spec = _spec(symbol="ETH", tracks=("D",), peers=(), sector="crypto_perp")
    universe = UniverseSpec(
        version="t",
        status="t",
        kind="quant_review",
        instruments=(spec,),
        symbol_map={"ETH": "ETH"},
        peer_groups={},
        arb_pairs=(("ETH", "BTC", ""),),
    )
    pkg = ArbPackage(
        venue_a="hl",
        venue_b="other",
        same_or_convertible_exposure=True,
        gross_spread=12.0,
        costs_complete=True,
        fill_size=1.0,
        liquidity_note="top of book covers fill",
        latency_ops_risk="documented",
        net_after_costs=4.0,
    )
    snap = ReviewSnapshot(
        as_of_knowledge=AS_OF,
        source="test",
        prints=(_print("ETH", 0.1),),
        arb_packages={"ETH": pkg},
        catalysts={"ETH": "spread persists after costs for two sessions"},
        invalidations={"ETH": "net after costs <= 0"},
        overlooked={"ETH": "two-venue package rarely assembled"},
        liquidity_ok={"ETH": True},
        addressed_warnings={
            "ETH": (
                QuantReasonCode.DUPLICATE_BETA.value,
                QuantReasonCode.CORRELATED_EXPOSURE.value,
                QuantReasonCode.STALE_OR_PARTIAL_DATA.value,
                QuantReasonCode.INSUFFICIENT_HISTORY.value,
                QuantReasonCode.NO_CATALYST.value,
                QuantReasonCode.THESIS_NOT_FALSIFIABLE.value,
                QuantReasonCode.INADEQUATE_LIQUIDITY.value,
                QuantReasonCode.NO_MISPRICING.value,
            )
        },
    )
    card = review_instrument(
        spec,
        snap,
        universe=universe,
        review_at=AS_OF,
        review_date="2026-09-17",
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert card.executable_arb is True
    assert LABEL_ARBITRAGE in card.labels


def test_post_ipo_underperformance_alone_is_not_research_priority() -> None:
    spec = _spec(symbol="CRCL", tracks=("A", "B", "C"), post_ipo=True, peers=("HOOD",), sector="crypto_equity")
    snap = _snapshot(prints=[_print("CRCL", -6.78), _print("HOOD", -0.2)])
    card = review_instrument(
        spec,
        snap,
        universe=_universe(spec, _spec(symbol="HOOD", peers=("CRCL",))),
        review_at=AS_OF,
        review_date="2026-09-17",
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert card.verdict != QuantVerdict.RESEARCH_PRIORITY.value
    assert QuantReasonCode.NO_CATALYST.value in card.reason_codes
    assert card.post_ipo is True


def test_every_verdict_has_controlled_reason_code() -> None:
    data = yaml.safe_load((ROOT / "config/quant_review_universe.yaml").read_text())
    fixture = yaml.safe_load((ROOT / "tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml").read_text())
    universe = universe_from_mapping(data)
    snapshot = snapshot_from_mapping(fixture, symbol_map=universe.symbol_map)
    result = run_board(universe, snapshot, review_at=AS_OF, generated_at=AS_OF, review_date="2026-09-17")
    allowed = {c.value for c in QuantReasonCode}
    verdicts = {v.value for v in QuantVerdict}
    for card in result.cards:
        assert card.verdict in verdicts
        assert card.reason_codes
        assert set(card.reason_codes) <= allowed
    assert len(result.cards) == len(universe.instruments)
    assert BOARD_FOOTER in result.board_markdown
    assert result.board_markdown.strip().endswith(BOARD_FOOTER)
    priority = [c for c in result.cards if c.verdict == QuantVerdict.RESEARCH_PRIORITY.value]
    assert len(priority) <= 3


def test_output_has_no_call_sizing_or_order_language() -> None:
    data = yaml.safe_load((ROOT / "config/quant_review_universe.yaml").read_text())
    fixture = yaml.safe_load((ROOT / "tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml").read_text())
    universe = universe_from_mapping(data)
    snapshot = snapshot_from_mapping(fixture, symbol_map=universe.symbol_map)
    result = run_board(universe, snapshot, review_at=AS_OF, generated_at=AS_OF, review_date="2026-09-17")
    blob = result.board_markdown + "\n" + "\n".join(render_card(c) for c in result.cards)
    assert language_violations(blob) == []
    assert_language_clean(blob)
    lowered = blob.lower()
    assert "active call" not in lowered
    assert "active-call" not in lowered
    assert "MAKE" not in blob
    assert "buy now" not in lowered
    assert "position size" not in lowered
    for card in result.cards:
        if LABEL_RELATIVE_VALUE in card.labels:
            assert LABEL_ARBITRAGE not in card.labels


def test_one_day_bounce_is_not_a_reclaim() -> None:
    spec = _spec(symbol="VVV", tracks=("A", "B"), peers=("BTC",), sector="crypto_perp", benchmark="BTC")
    snap = _snapshot(prints=[_print("VVV", 2.77), _print("BTC", 0.29)])
    card = review_instrument(
        spec,
        snap,
        universe=_universe(spec, _spec(symbol="BTC", peers=("VVV",), sector="crypto_perp")),
        review_at=AS_OF,
        review_date="2026-09-17",
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert QuantReasonCode.RECLAIM_UNCONFIRMED.value in card.reason_codes
    assert "one-day bounce" in card.relative_and_structure.lower() or "one-day bounce" in card.unusual.lower() or "not a reclaim" in card.relative_and_structure.lower()


def test_priority_cap_demotes_extras(tmp_path: Path) -> None:
    specs = []
    prints = []
    overlays = []
    catalysts = {}
    invalidations = {}
    overlooked = {}
    liquidity_ok = {}
    addressed = {}
    reclaim = {}
    for i, name in enumerate(["W", "X", "Y", "Z"]):
        specs.append(_spec(symbol=name, peers=("SPX",), tracks=("A", "B"), sector="other_us"))
        prints.append(_print(name, 8.0 + i, last=20 + i))
        overlays.append(
            SeriesOverlay(
                symbol=name,
                source="test",
                asof="2026-09-17",
                captured_at=AS_OF.isoformat(),
                rel_short=0.15,
                n_bars=40,
                data_quality="ok",
                adv=9_000_000,
            )
        )
        catalysts[name] = f"dated event {name}"
        invalidations[name] = f"close back through 10 on {name}"
        overlooked[name] = "thin coverage vs peers"
        liquidity_ok[name] = True
        addressed[name] = (
            QuantReasonCode.DUPLICATE_BETA.value,
            QuantReasonCode.CORRELATED_EXPOSURE.value,
            QuantReasonCode.INADEQUATE_LIQUIDITY.value,
            QuantReasonCode.INSUFFICIENT_HISTORY.value,
            QuantReasonCode.NO_CATALYST.value,
            QuantReasonCode.THESIS_NOT_FALSIFIABLE.value,
            QuantReasonCode.NO_MISPRICING.value,
            QuantReasonCode.STALE_OR_PARTIAL_DATA.value,
            QuantReasonCode.RECLAIM_UNCONFIRMED.value,
        )
        reclaim[name] = ReclaimObservables(prior_breakdown_level="8", reclaim_of_level="8", hold_sessions=3)
    prints.append(_print("SPX", 0.1, last=100))
    specs.append(_spec(symbol="SPX", peers=("W",), role="benchmark", tracks=("A", "B"), sector="us_index", benchmark="SPX"))
    snap = ReviewSnapshot(
        as_of_knowledge=AS_OF,
        source="test",
        prints=tuple(prints),
        overlays=tuple(overlays),
        catalysts=catalysts,
        invalidations=invalidations,
        overlooked=overlooked,
        liquidity_ok=liquidity_ok,
        addressed_warnings=addressed,
        reclaim=reclaim,
    )
    result = run_board(_universe(*specs), snap, review_at=AS_OF, generated_at=AS_OF, review_date="2026-09-17")
    priority = [c for c in result.cards if c.verdict == QuantVerdict.RESEARCH_PRIORITY.value]
    assert len(priority) <= 3
    written = write_board(result, research_root=tmp_path)
    text = Path(written["board"]).read_text(encoding="utf-8")
    assert BOARD_FOOTER in text
    assert language_violations(text) == []


def test_language_gate_rejects_make() -> None:
    with pytest.raises(GateError, match="forbidden language"):
        assert_language_clean("MAKE BTC into an active call with position size 2 contracts of ETH")


def test_skeptic_pass_is_not_faked_on_promotion_path() -> None:
    spec = _spec(symbol="SPCX", peers=("CBRS",), sector="other_us")
    snap = ReviewSnapshot(
        as_of_knowledge=AS_OF,
        source="test",
        prints=(_print("SPCX", 5.15), _print("CBRS", 0.2)),
        overlays=(
            SeriesOverlay(
                symbol="SPCX",
                source="test",
                asof="2026-09-17",
                captured_at=AS_OF.isoformat(),
                rel_short=0.12,
                n_bars=50,
                adv=2_000_000,
            ),
        ),
        catalysts={"SPCX": "dated catalyst T+5"},
        invalidations={"SPCX": "close back through 140"},
        overlooked={"SPCX": "not in ingest universe"},
        liquidity_ok={"SPCX": True},
        addressed_warnings={
            "SPCX": (
                QuantReasonCode.DUPLICATE_BETA.value,
                QuantReasonCode.CORRELATED_EXPOSURE.value,
                QuantReasonCode.INADEQUATE_LIQUIDITY.value,
                QuantReasonCode.INSUFFICIENT_HISTORY.value,
                QuantReasonCode.NO_MISPRICING.value,
            )
        },
        reclaim={"SPCX": ReclaimObservables(prior_breakdown_level="140", reclaim_of_level="140", hold_sessions=4)},
    )
    card = review_instrument(
        spec,
        snap,
        universe=_universe(spec, _spec(symbol="CBRS", peers=("SPCX",))),
        review_at=AS_OF,
        review_date="2026-09-17",
        as_of_knowledge=AS_OF,
        stale_after=timedelta(hours=36),
    )
    assert card.promotion.independent_skeptic_review_required is True
    assert card.promotion.independent_skeptic_verdict == "pending"
    rendered = render_card(card)
    assert "not claimed as pass" in rendered.lower()
    assert "skeptic pass" not in rendered.lower()
