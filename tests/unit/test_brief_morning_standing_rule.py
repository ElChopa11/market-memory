"""Morning brief standing rule: a line that repeats every morning is not information.

The eleven-capture send is one Telegram message. Status lines stay last.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_from_fixture, load_fixture_file
from mm_briefing.models import (
    ASSET_ORDER,
    AssetPrint,
    CalendarEvent,
    HLInstrumentState,
    HLMetric,
    MacroSnapshot,
    ThesisHook,
)
from mm_briefing.morning import (
    FORBIDDEN_RENDER_FRAGMENTS,
    HL_FUNDING_BASELINE_HOURLY,
    PHONE_LINE_MAX,
    funding_on_baseline,
)
from mm_briefing.prior import MapPriorCaptureReader, PriorCaptureValue, prior_value_from_retain
from mm_briefing.render import render_close
from mm_delivery.format import TELEGRAM_MAX_MESSAGE_CHARS, chunk_markdown_v2
from mm_delivery.payload import prepare_payload
from mm_ingest.mvp_retain import capture_rows_line
from mm_lab_cli.deadman import DEADMAN_MISSING_LINE
from mm_lab_cli.deliver import append_brief_status_lines

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
AS_OF = datetime(2026, 9, 22, 20, 15, tzinfo=UTC)
GENERATED = AS_OF
PRIOR_CLOSE = datetime(2026, 9, 21, 20, 0, tzinfo=UTC)

LATE = "LATE: grok.sydney_morning fired +2h 46m past anchor. run_id actions-b1-1."
CAPTURE = capture_rows_line(
    rows=75,
    expected_rows=75,
    captured_at="2026-09-24T23:17:25+00:00",
    prior_captured_at="2026-09-24T06:58:31+00:00",
    instruments=37,
)
_ROW_HEADS = {"SPY", "QQQ", "US10Y", "UUP", "USO", "VIX", "BTC", "ETH"}
_SECTION_HEADS = {"Positioning", "Unexpected", "Lab hooks", "Assumptions", "Catalysts"}


def _print(
    symbol: str,
    *,
    last: float | None = 1.0,
    prior: float | None = 1.0,
    source: str = "fixture",
    quality: str = "ok",
    name: str | None = None,
    unit: str = "px",
    as_of: datetime | None = None,
    quoted_symbol: str | None = None,
    observation_id: str | None = None,
    structural: bool = False,
) -> AssetPrint:
    return AssetPrint(
        symbol=symbol,
        name=name or symbol,
        last=last,
        prior_close=prior,
        unit=unit,
        data_quality=quality,
        source=source,
        as_of=as_of or AS_OF,
        quoted_symbol=quoted_symbol,
        observation_id=observation_id,
        structural_unavailable=structural,
    )


def _session(assets: tuple[AssetPrint, ...]) -> MacroSnapshot:
    return MacroSnapshot(
        as_of=AS_OF,
        prior_us_close=PRIOR_CLOSE,
        assets=assets,
        data_quality="ok",
        source="fixture",
    )


def _eight() -> tuple[AssetPrint, ...]:
    rows = []
    for symbol in ASSET_ORDER:
        unit = "%" if symbol == "US10Y" else "px"
        last = 4.25 if symbol == "US10Y" else 100.0
        prior = 4.20 if symbol == "US10Y" else 99.0
        rows.append(
            _print(
                symbol,
                last=last,
                prior=prior,
                unit=unit,
                source="polygon" if symbol not in {"US10Y", "BTC", "ETH"} else ("fred" if symbol == "US10Y" else "hyperliquid"),
                name={
                    "ES": "SPY ETF (proxy for S&P 500; not ES futures)",
                    "NQ": "QQQ ETF (proxy for Nasdaq-100; not NQ futures)",
                    "DXY": "UUP ETF (USD proxy; not DX futures / DXY)",
                    "CL": "USO ETF (WTI oil proxy; not CL futures)",
                }.get(symbol, symbol),
                quoted_symbol={"ES": "SPY", "NQ": "QQQ", "DXY": "UUP", "CL": "USO"}.get(symbol),
            )
        )
    return tuple(rows)


def _hl(
    instrument: str,
    *,
    funding: str | None = "0.000100",
    oi: str | None = "10",
    mid: str | None = "100",
    mark: str | None = "101",
    oracle: str | None = "100",
    liquidations: tuple[str, ...] = (),
    obs: bool = False,
    quality: str = "ok",
) -> HLInstrumentState:
    metrics: dict[str, HLMetric] = {}
    for name, value in (
        ("funding", funding),
        ("open_interest", oi),
        ("mid_px", mid),
        ("mark_px", mark),
        ("oracle_px", oracle),
    ):
        if value is None and name in {"mark_px", "oracle_px"}:
            continue
        metrics[name] = HLMetric(
            instrument=instrument,
            metric=name,
            value=value,
            observation_id=f"obs-{instrument}-{name}" if obs else None,
            claim_hash=None,
            data_quality=quality,
            as_of_knowledge=AS_OF,
        )
    liqs = tuple(
        HLMetric(
            instrument=instrument,
            metric="liquidation",
            value=size,
            observation_id=f"obs-{instrument}-liq" if obs else None,
            claim_hash=None,
            data_quality=quality,
            as_of_knowledge=AS_OF,
        )
        for size in liquidations
    )
    return HLInstrumentState(
        instrument=instrument,
        metrics=metrics,
        liquidations=liqs,
        levels=(),
        data_quality=quality,
        as_of_knowledge=AS_OF,
        source="hyperliquid.info",
    )


def _render(
    *,
    assets: tuple[AssetPrint, ...] | None = None,
    hl: tuple[HLInstrumentState, ...] = (),
    calendar: tuple[CalendarEvent, ...] = (),
    unexpected: tuple[str, ...] = (),
    theses: tuple[ThesisHook, ...] = (),
    assumptions: tuple[str, ...] = ("No named macro assumption flipped vs the overnight tape",),
    prior_reader=None,
) -> str:
    doc = render_close(
        generated_at=GENERATED,
        as_of=AS_OF,
        overnight=_session(assets or _eight()),
        session=_session(assets or _eight()),
        calendar=calendar,
        unexpected=unexpected,
        theses=theses,
        assumptions=assumptions,
        hl=hl,
        data_quality="ok",
        prior_reader=prior_reader,
    )
    return doc.markdown


def _fence_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    in_fence = False
    for line in markdown.splitlines():
        if line.strip() == "```":
            in_fence = not in_fence
            continue
        if in_fence:
            lines.append(line)
    return lines


def _assert_phone(markdown: str) -> None:
    for line in _fence_lines(markdown):
        assert len(line) <= PHONE_LINE_MAX, line
        assert not line.startswith("#")


def _is_continuation(line: str) -> bool:
    if not line or line.startswith("gaps:"):
        return False
    head = line.split(" ", 1)[0]
    if head in _ROW_HEADS or head in _SECTION_HEADS:
        return False
    if head in {"UTC", "NY", "SYD", "Health", "Equities", "Rates", "USD", "Oil", "Vol", "Crypto", "Hyperliquid", "obs"}:
        return False
    return True


def _row_text(markdown: str, symbol: str) -> str:
    lines = _fence_lines(markdown)
    for index, line in enumerate(lines):
        if line.split(" ", 1)[0] != symbol:
            continue
        if index + 1 < len(lines) and _is_continuation(lines[index + 1]):
            return f"{line} {lines[index + 1].strip()}"
        return line
    raise AssertionError(f"missing price row for {symbol}\n{markdown}")


def _price_line(markdown: str, symbol: str) -> str:
    return _row_text(markdown, symbol)


def test_empty_sections_are_omitted_not_rendered_as_none() -> None:
    text = _render(hl=())
    assert "## Unexpected" not in text
    assert "## Lab hooks" not in text
    assert "## Assumptions" not in text
    assert "## Catalysts" not in text
    assert "## Positioning" not in text
    lowered = text.lower()
    assert "none scheduled" not in lowered
    assert "- none" not in lowered
    assert "no configured rule fired" not in lowered


def test_obs_none_is_one_header_state() -> None:
    text = _render(hl=(_hl("BTC", liquidations=()),))
    lines = _fence_lines(text)
    assert lines.count("obs none") == 1
    assert all(line.strip() == "obs none" or "obs none" not in line for line in lines)
    _assert_phone(text)


def test_obs_none_absent_when_an_observation_id_exists() -> None:
    prior = MapPriorCaptureReader(
        {
            ("BTC", "funding"): PriorCaptureValue(
                instrument="BTC",
                metric="funding",
                value=0.0001,
                captured_at=AS_OF,
                prior_captured_at=AS_OF - timedelta(days=1),
            )
        }
    )
    text = _render(hl=(_hl("BTC", obs=True),), prior_reader=prior)
    assert "obs none" not in text
    assert "obs obs-BTC-funding" in text


def test_no_overnight_reference_block() -> None:
    text = _render()
    assert "Overnight reference" not in text
    assert "What changed since prior US close" not in text


def test_zero_metric_moves_to_gaps_and_returns_when_nonzero() -> None:
    zero = _render(hl=(_hl("BTC", funding="0.0000125", oi="0", mid="0", liquidations=()),))
    assert "Liquidations (window sum)" not in zero.split("gaps:", 1)[0]
    assert "fund " not in zero
    assert "gaps:" in zero
    assert "BTC Liquidations (window sum)" in _joined(zero)
    assert "BTC Funding" in _joined(zero)

    back = _render(hl=(_hl("BTC", funding="0.0000125", oi="0", mid="0", liquidations=("2.5",)),))
    assert "BTC Liquidations (window sum) 2.5" in back
    gaps = back.split("gaps:", 1)[1] if "gaps:" in back else ""
    assert "Liquidations (window sum)" not in gaps


def test_basis_omitted_without_prior_and_shown_with_prior_value() -> None:
    bare = _render(hl=(_hl("BTC", mark="110", oracle="100"),))
    assert "Basis" not in bare

    prior = MapPriorCaptureReader(
        {
            ("BTC", "basis"): PriorCaptureValue(
                instrument="BTC",
                metric="basis",
                value=7.5,
                captured_at=AS_OF,
                prior_captured_at=AS_OF - timedelta(days=1),
            )
        }
    )
    shown = _render(hl=(_hl("BTC", mark="110", oracle="100"),), prior_reader=prior)
    assert "BTC basis 10" in shown
    assert " prior 7.5" in shown


def test_unchanged_zero_stays_on_gaps_and_changed_zero_returns() -> None:
    same = PriorCaptureValue(
        instrument="BTC",
        metric="liquidations",
        value=0.0,
        captured_at=AS_OF,
        prior_captured_at=AS_OF - timedelta(days=1),
    )
    quiet = _render(
        hl=(_hl("BTC", funding="0.0001", oi="1", mid="1", liquidations=()),),
        prior_reader=MapPriorCaptureReader({("BTC", "liquidations"): same}),
    )
    assert "Liquidations (window sum)" not in quiet.split("gaps:", 1)[0]
    assert "BTC Liquidations (window sum)" in _joined(quiet)

    changed = PriorCaptureValue(
        instrument="BTC",
        metric="liquidations",
        value=4.0,
        captured_at=AS_OF,
        prior_captured_at=AS_OF - timedelta(days=1),
    )
    moved = _render(
        hl=(_hl("BTC", funding="0.0001", oi="1", mid="1", liquidations=()),),
        prior_reader=MapPriorCaptureReader({("BTC", "liquidations"): changed}),
    )
    assert "BTC Liquidations (window sum) 0" in moved


def test_prior_read_failure_does_not_fail_the_brief() -> None:
    class _Boom:
        def read(self, instrument: str, metric: str):
            raise RuntimeError("neon unavailable")

    text = _render(hl=(_hl("BTC"),), prior_reader=_Boom())
    assert "US Close 2026-09-22" in text
    assert "basis" not in text
    assert "BTC fund " in text
    assert " prior " not in text


def test_capture_one_retain_row_is_no_prior() -> None:
    assert (
        prior_value_from_retain(
            instrument="BTC",
            metric="basis",
            value="10",
            captured_at=AS_OF,
            prior_captured_at=None,
        )
        is None
    )


def test_funding_and_oi_with_prior_are_annualised_and_rounded() -> None:
    prior = MapPriorCaptureReader(
        {
            ("BTC", "funding"): PriorCaptureValue(
                instrument="BTC",
                metric="funding",
                value=0.000001,
                captured_at=AS_OF,
                prior_captured_at=AS_OF - timedelta(days=1),
            ),
            ("BTC", "open_interest"): PriorCaptureValue(
                instrument="BTC",
                metric="open_interest",
                value=36568.77092,
                captured_at=AS_OF,
                prior_captured_at=AS_OF - timedelta(days=1),
            ),
        }
    )
    on_baseline = _render(
        hl=(_hl("BTC", funding="0.000013", oi="38843.42252", mid="1", liquidations=()),),
        prior_reader=prior,
    )
    assert "11.39% ann" not in on_baseline
    assert "0.000013" not in on_baseline
    assert "BTC Funding" in on_baseline.split("gaps:", 1)[1]
    assert "BTC OI 38,843" in on_baseline
    assert " prior 36,569 +6.22%" in on_baseline
    assert "38843.42252" not in on_baseline

    off = _render(
        hl=(_hl("BTC", funding="0.000014", oi="38843.42252", mid="1", liquidations=()),),
        prior_reader=prior,
    )
    assert "BTC fund 12.26% ann" in off
    assert " prior 0.88% ann" in off


def test_no_key_takeaway_and_fixed_lines_absent() -> None:
    text = _render(
        hl=(_hl("BTC"),),
        unexpected=(),
        theses=(),
        assumptions=("No named macro assumption flipped vs the overnight tape",),
    )
    for fragment in FORBIDDEN_RENDER_FRAGMENTS:
        assert fragment not in text
    assert "KEY TAKEAWAY" not in text
    assert "Nothing crossed the unexpected-move rules" not in text
    assert "No indexed theses to score against this session" not in text
    assert "No named macro assumption flipped vs the overnight tape" not in text
    assert "Monitor into Asia" not in text
    assert "Monitor into Europe" not in text


def test_eight_price_rows_keep_symbol_last_and_change_only() -> None:
    text = _render()
    assert "```" in text
    assert "| Symbol |" not in text
    assert "#" not in "".join(_fence_lines(text))
    symbols = []
    for line in _fence_lines(text):
        head = line.split(" ", 1)[0]
        if head in _ROW_HEADS:
            symbols.append(head)
            assert _delta_cell(text, head)
    assert symbols == ["SPY", "QQQ", "US10Y", "UUP", "USO", "VIX", "BTC", "ETH"]
    assert "proxy" not in text
    assert "not ES futures" not in text
    _assert_phone(text)
    labels = (ROOT / "docs/specs/brief-row-labels.md").read_text(encoding="utf-8")
    assert "SPY ETF (proxy for S&P 500; not ES futures)" in labels
    assert "QQQ ETF (proxy for Nasdaq-100; not NQ futures)" in labels


def _joined(markdown: str) -> str:
    return " ".join(line.strip() for line in markdown.splitlines() if line.strip() and line.strip() != "```")


def _delta_cell(markdown: str, symbol: str) -> str:
    parts = _row_text(markdown, symbol).split(" ", 2)
    if len(parts) < 3:
        return ""
    return parts[2]


def _close_prior(symbol: str, *, observation_as_of: datetime | None, value: float | None = 100.0) -> PriorCaptureValue:
    return PriorCaptureValue(
        instrument=symbol,
        metric="close",
        value=value,
        captured_at=AS_OF - timedelta(days=1),
        prior_captured_at=AS_OF - timedelta(days=2),
        observation_as_of=observation_as_of,
    )


def test_same_equity_bar_date_prints_no_new_session() -> None:
    bar = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)
    earlier_same_day = datetime(2026, 9, 22, 13, 30, tzinfo=UTC)
    assets = list(_eight())
    assets[0] = _print(
        "ES",
        last=512.0,
        prior=500.0,
        source="polygon",
        name="SPY ETF (proxy for S&P 500; not ES futures)",
        quoted_symbol="SPY",
        as_of=bar,
    )
    text = _render(
        assets=tuple(assets),
        prior_reader=MapPriorCaptureReader(
            {("ES", "close"): _close_prior("ES", observation_as_of=earlier_same_day)}
        ),
    )
    delta = _delta_cell(text, "SPY")
    assert delta == "no new session since 2026-09-22"
    assert "0.00%" not in delta
    assert "+0.0bp" not in delta


def test_new_equity_bar_date_with_same_close_prints_zero_percent() -> None:
    bar = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)
    assets = list(_eight())
    assets[0] = _print(
        "ES",
        last=512.0,
        prior=512.0,
        source="polygon",
        name="SPY ETF (proxy for S&P 500; not ES futures)",
        quoted_symbol="SPY",
        as_of=bar,
    )
    text = _render(
        assets=tuple(assets),
        prior_reader=MapPriorCaptureReader(
            {("ES", "close"): _close_prior("ES", observation_as_of=bar - timedelta(days=1), value=512.0)}
        ),
    )
    delta = _delta_cell(text, "SPY")
    assert "0.00%" in delta
    assert "no new session since" not in delta


def test_same_fred_observation_date_prints_no_new_print() -> None:
    obs = datetime(2026, 9, 18, 0, 0, tzinfo=UTC)
    assets = list(_eight())
    assets[2] = _print(
        "US10Y",
        last=4.25,
        prior=4.20,
        unit="%",
        source="fred",
        name="US 10Y yield",
        as_of=obs,
    )
    text = _render(
        assets=tuple(assets),
        prior_reader=MapPriorCaptureReader(
            {("US10Y", "close"): _close_prior("US10Y", observation_as_of=obs, value=4.25)}
        ),
    )
    delta = _delta_cell(text, "US10Y")
    assert delta == "no new print since 2026-09-18"
    assert "0.00%" not in delta
    assert "+0.0bp" not in delta


def test_new_fred_observation_date_with_same_yield_prints_zero_bp() -> None:
    obs = datetime(2026, 9, 18, 0, 0, tzinfo=UTC)
    assets = list(_eight())
    assets[2] = _print(
        "US10Y",
        last=4.25,
        prior=4.25,
        unit="%",
        source="fred",
        name="US 10Y yield",
        as_of=obs,
    )
    text = _render(
        assets=tuple(assets),
        prior_reader=MapPriorCaptureReader(
            {("US10Y", "close"): _close_prior("US10Y", observation_as_of=obs - timedelta(days=1), value=4.25)}
        ),
    )
    delta = _delta_cell(text, "US10Y")
    assert delta == "+0.0bp"
    assert "no new print since" not in delta


def test_no_prior_keeps_numeric_change_cell() -> None:
    bar = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)
    assets = list(_eight())
    assets[0] = _print(
        "ES",
        last=512.0,
        prior=512.0,
        source="polygon",
        name="SPY ETF (proxy for S&P 500; not ES futures)",
        quoted_symbol="SPY",
        as_of=bar,
    )
    text = _render(assets=tuple(assets), prior_reader=None)
    delta = _delta_cell(text, "SPY")
    assert "0.00%" in delta
    assert "no new session since" not in text
    assert "no new print since" not in text


def test_crypto_change_cell_ignores_a_repeated_as_of() -> None:
    bar = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)
    assets = list(_eight())
    assets[6] = _print("BTC", last=100.0, prior=100.0, source="hyperliquid", as_of=bar)
    text = _render(
        assets=tuple(assets),
        prior_reader=MapPriorCaptureReader({("BTC", "close"): _close_prior("BTC", observation_as_of=bar)}),
    )
    delta = _delta_cell(text, "BTC")
    assert "0.00%" in delta
    assert "no new session since" not in delta
    assert "no new print since" not in delta


def test_missing_observation_as_of_does_not_infer_a_stall_from_equal_values() -> None:
    bar = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)
    assets = list(_eight())
    assets[0] = _print(
        "ES",
        last=512.0,
        prior=512.0,
        source="polygon",
        name="SPY ETF (proxy for S&P 500; not ES futures)",
        quoted_symbol="SPY",
        as_of=bar,
    )
    text = _render(
        assets=tuple(assets),
        prior_reader=MapPriorCaptureReader({("ES", "close"): _close_prior("ES", observation_as_of=None, value=512.0)}),
    )
    delta = _delta_cell(text, "SPY")
    assert "0.00%" in delta
    assert "no new session since" not in delta


def test_staleness_flag_renders_when_it_fires() -> None:
    assets = list(_eight())
    assets[2] = _print(
        "US10Y",
        last=4.25,
        prior=4.20,
        unit="%",
        source="fred",
        quality="stale",
        as_of=AS_OF - timedelta(days=4),
        name="US 10Y yield",
    )
    text = _render(assets=tuple(assets))
    us10y = _price_line(text, "US10Y")
    assert "stale (4d)" in us10y
    spy = _price_line(text, "SPY")
    assert "stale" not in spy


def test_messages_3_and_4_omitted_message_5_keeps_live_metrics() -> None:
    text = _render(hl=(_hl("BTC", funding="0.000125", liquidations=("1",)), _hl("ETH", funding="0", oi=None, mid="1")))
    assert "MACRO TRANSMISSION" not in text
    assert "CRYPTO TAPE" not in text
    assert "2s10s" not in text
    assert "CLUSTER LEADERSHIP" not in text
    assert "z30d" not in text
    assert "Positioning" in text
    assert "## Positioning" not in text
    assert "BTC fund 109.50% ann" in text
    assert "ETH fund 0.00% ann" in text
    assert "ETH Open interest" in _joined(text)
    assert "Mid" not in text.split("Positioning", 1)[1]


def test_real_varying_sections_still_render() -> None:
    when = AS_OF + timedelta(hours=12)
    text = _render(
        unexpected=("ES session +1.05% vs overnight +0.52%",),
        theses=(
            ThesisHook(
                slug="THESIS-0001",
                status="paper",
                instrument="BTC",
                invalidation_summary="Daily close below 64000",
                expected_direction="short",
                verdict_hook="lab wrong (so far): expected short BTC, session +2.01%",
                hypothesis="Funding fade",
            ),
        ),
        assumptions=("USD overnight direction did not hold into the cash close",),
        calendar=(
            CalendarEvent(
                when=when,
                name="FOMC speaker",
                importance="medium",
                notes="Into the next session",
            ),
        ),
    )
    joined = _joined(text)
    assert "ES session +1.05% vs overnight +0.52%" in joined
    assert "THESIS-0001" in joined
    assert "USD overnight direction did not hold into the cash close" in joined
    assert "FOMC speaker" in joined
    assert "  - Hypothesis: Funding fade" in text
    _assert_phone(text)
    assert "Monitor into Asia" not in text


def test_funding_baseline_boundary() -> None:
    assert HL_FUNDING_BASELINE_HOURLY == 0.0001 / 8
    assert funding_on_baseline(0.0000125)
    assert funding_on_baseline(0.000012)
    assert funding_on_baseline(0.000013)
    assert not funding_on_baseline(0.000014)
    assert not funding_on_baseline(0.000001)
    assert not funding_on_baseline(0.0001)


def test_missing_last_moves_to_gaps() -> None:
    assets = list(_eight())
    assets[5] = _print(
        "VIX",
        last=None,
        prior=None,
        quality="unavailable",
        structural=True,
        name="CBOE VIX",
    )
    text = _render(assets=tuple(assets))
    assert not any(line.startswith("VIX ") or line == "VIX" for line in _fence_lines(text))
    assert "VIX" in text.split("gaps:", 1)[1]
    assert "n/a" not in text
    _assert_phone(text)


def test_repeated_session_is_stale_on_the_health_line_and_not_fresh() -> None:
    bar = datetime(2026, 9, 22, 20, 0, tzinfo=UTC)
    later = bar + timedelta(days=1)
    assets = list(_eight())
    session_slots = {"ES", "NQ", "DXY", "CL"}
    names = {
        "ES": ("SPY ETF (proxy for S&P 500; not ES futures)", "SPY"),
        "NQ": ("QQQ ETF (proxy for Nasdaq-100; not NQ futures)", "QQQ"),
        "DXY": ("UUP ETF (USD proxy; not DX futures / DXY)", "UUP"),
        "CL": ("USO ETF (WTI oil proxy; not CL futures)", "USO"),
    }
    priors = {}
    for index, symbol in enumerate(ASSET_ORDER):
        if symbol in session_slots:
            label, quoted = names[symbol]
            assets[index] = _print(
                symbol,
                last=100.0,
                prior=99.0,
                source="polygon",
                quality="fresh",
                name=label,
                quoted_symbol=quoted,
                as_of=bar,
            )
            priors[(symbol, "close")] = _close_prior(symbol, observation_as_of=bar, value=99.0)
        elif symbol == "US10Y":
            assets[index] = _print(
                "US10Y",
                last=4.25,
                prior=4.20,
                unit="%",
                source="fred",
                quality="fresh",
                name="US 10Y yield",
                as_of=later,
            )
            priors[("US10Y", "close")] = _close_prior("US10Y", observation_as_of=bar, value=4.20)
        elif symbol == "VIX":
            assets[index] = _print(
                "VIX",
                last=None,
                prior=None,
                quality="fresh",
                structural=True,
                name="CBOE VIX",
            )
        elif symbol in {"BTC", "ETH"}:
            assets[index] = _print(symbol, last=100.0, prior=100.0, source="hyperliquid", quality="fresh", as_of=bar)
            priors[(symbol, "close")] = _close_prior(symbol, observation_as_of=bar, value=100.0)
    text = _render(
        assets=tuple(assets),
        hl=(_hl("BTC", funding="0.000013", quality="ok"),),
        prior_reader=MapPriorCaptureReader(priors),
    )
    assert "Health 43%" in text
    assert "Equities stale" in text
    assert "Rates fresh" in text
    assert "USD stale" in text
    assert "Oil stale" in text
    assert "Vol unavailable" in text
    assert "Crypto fresh" in text
    assert "Hyperliquid fresh" in text
    assert "100%" not in text
    assert "Equities fresh" not in text
    assert "no new session since 2026-09-22" in text
    assert "Vol fresh" not in text
    _assert_phone(text)


def test_as_of_knowledge_line_is_not_in_the_morning_message() -> None:
    text = _render()
    assert "As-of knowledge" not in text


def test_eleven_capture_brief_is_one_message_status_lines_last() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("close", fixture, settings=settings)
    assert doc is not None
    message = append_brief_status_lines(
        doc.markdown,
        late=LATE,
        deadman=DEADMAN_MISSING_LINE,
        capture=CAPTURE,
    )
    assert message.rstrip().endswith("\n".join((LATE, DEADMAN_MISSING_LINE, CAPTURE)))
    tail = message.strip().splitlines()[-3:]
    assert tail == [LATE, DEADMAN_MISSING_LINE, CAPTURE]
    assert len(message) <= TELEGRAM_MAX_MESSAGE_CHARS
    payload = prepare_payload(message)
    assert payload.reason == "no_send"
    assert payload.send is False
    chunks = chunk_markdown_v2(message)
    assert chunks == payload.chunks
    assert len(chunks) == 1
    assert len(chunks[0]) <= TELEGRAM_MAX_MESSAGE_CHARS
    sent = chunks[0]
    assert sent.rfind("LATE") < sent.rfind("DEADMAN") < sent.rfind("CAPTURE")
    assert "(37 instruments)" in message
    assert r"\(37 instruments\)" in sent
    assert "DEADMAN: MISSING" in sent
    fence_end = message.rfind("```")
    tail = message[fence_end:]
    assert LATE in tail and DEADMAN_MISSING_LINE in tail and CAPTURE in tail
    _assert_phone(doc.markdown)
