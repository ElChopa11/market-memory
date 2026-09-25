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
from mm_briefing.morning import FORBIDDEN_RENDER_FRAGMENTS
from mm_briefing.prior import MapPriorCaptureReader, PriorCaptureValue, prior_value_from_retain
from mm_briefing.render import render_close
from mm_delivery.format import TELEGRAM_MAX_MESSAGE_CHARS, chunk_markdown_v2
from mm_delivery.payload import prepare_payload
from mm_lab_cli.deadman import DEADMAN_MISSING_LINE
from mm_lab_cli.deliver import append_brief_status_lines

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
AS_OF = datetime(2026, 9, 22, 20, 15, tzinfo=UTC)
GENERATED = AS_OF
PRIOR_CLOSE = datetime(2026, 9, 21, 20, 0, tzinfo=UTC)

LATE = "LATE: grok.sydney_morning fired +2h 46m past anchor. run_id actions-b1-1."
CAPTURE = "CAPTURE: grok.sydney_morning capture 1 of 11. run_id actions-b1-1."


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


def _price_line(markdown: str, symbol: str) -> str:
    for line in markdown.splitlines():
        if line.startswith(f"| {symbol} |"):
            return line
    raise AssertionError(f"missing price row for {symbol}\n{markdown}")


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
    assert text.count("obs none") == 1
    header, _, table = text.partition("| Symbol |")
    assert "obs none" in header
    assert "obs none" not in table
    for line in table.splitlines():
        if line.startswith("|"):
            assert "obs" not in line


def test_obs_none_absent_when_an_observation_id_exists() -> None:
    text = _render(hl=(_hl("BTC", obs=True),))
    assert "obs none" not in text
    assert "obs obs-BTC-funding" in text


def test_no_overnight_reference_block() -> None:
    text = _render()
    assert "Overnight reference" not in text
    assert "What changed since prior US close" not in text


def test_zero_metric_moves_to_gaps_and_returns_when_nonzero() -> None:
    zero = _render(hl=(_hl("BTC", funding="0", oi="0", mid="0", liquidations=()),))
    assert "Liquidations (window sum): 0" not in zero
    assert "BTC Funding:" not in zero
    assert "gaps: " in zero
    assert "BTC Liquidations (window sum)" in zero.split("gaps: ", 1)[1]

    back = _render(hl=(_hl("BTC", funding="0", oi="0", mid="0", liquidations=("2.5",)),))
    assert "BTC Liquidations (window sum): 2.5" in back
    gaps = back.split("gaps: ", 1)[1] if "gaps: " in back else ""
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
    assert "BTC Basis mark−oracle: 10 (prior 7.5)" in shown


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
    assert "Liquidations (window sum):" not in quiet
    assert "BTC Liquidations (window sum)" in quiet.split("gaps: ", 1)[1]

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
    assert "BTC Liquidations (window sum): 0" in moved


def test_prior_read_failure_does_not_fail_the_brief() -> None:
    class _Boom:
        def read(self, instrument: str, metric: str):
            raise RuntimeError("neon unavailable")

    text = _render(hl=(_hl("BTC"),), prior_reader=_Boom())
    assert "US Close Brief" in text
    assert "Basis" not in text
    assert "BTC Funding:" in text


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


def test_eight_price_rows_carry_source_delta_quality_and_proxy_labels() -> None:
    text = _render()
    assert "| Symbol | Last | Δ | Source | Quality | Label |" in text
    body = [line for line in text.splitlines() if line.startswith("| ") and not line.startswith("| Symbol") and not line.startswith("|---")]
    assert len(body) == 8
    symbols = [line.split("|")[1].strip() for line in body]
    assert symbols == ["SPY", "QQQ", "US10Y", "UUP", "USO", "VIX", "BTC", "ETH"]
    for line in body:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == 6
        _symbol, _last, delta, source, quality, label = cells
        assert delta
        assert source
        assert quality
    spy = _price_line(text, "SPY")
    assert "proxy" in spy
    assert "not ES futures" in spy
    qqq = _price_line(text, "QQQ")
    assert "proxy" in qqq
    assert "| NQ |" not in text
    assert "| ES |" not in text


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
    assert "## Positioning" in text
    assert "BTC Funding: 0.000125" in text
    assert "ETH Funding:" not in text
    assert "ETH Open interest" in text.split("gaps: ", 1)[1]


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
    assert "ES session +1.05% vs overnight +0.52%" in text
    assert "THESIS-0001" in text
    assert "USD overnight direction did not hold into the cash close" in text
    assert "FOMC speaker" in text
    assert "Monitor into Asia" not in text


def test_committed_dry_run_is_the_approved_one_message_render() -> None:
    """The Principal approval gate is the committed dry-run, not a second format."""
    text = (ROOT / "ops/reports/renders/brief-template-dryrun.txt").read_text(encoding="utf-8")
    current = (ROOT / "ops/reports/renders/brief-current-dryrun.txt").read_text(encoding="utf-8")
    assert len(text) <= TELEGRAM_MAX_MESSAGE_CHARS
    assert len(chunk_markdown_v2(text)) == 1
    assert text.count("obs none") == 1
    assert "Overnight reference" not in text
    assert "KEY TAKEAWAY" not in text
    assert "Basis" not in text
    assert "gaps: BTC Liquidations (window sum), ETH Liquidations (window sum)" in text
    assert "Liquidations (window sum): 0" not in text
    for symbol in ("SPY", "QQQ", "US10Y", "UUP", "USO", "VIX", "BTC", "ETH"):
        assert f"| {symbol} |" in text
    for fragment in FORBIDDEN_RENDER_FRAGMENTS:
        assert fragment not in text
    assert "Overnight reference" in current
    assert "Nothing crossed the unexpected-move rules" in current


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
    assert sent.rstrip().endswith("CAPTURE: grok\\.sydney\\_morning capture 1 of 11\\. run\\_id actions\\-b1\\-1\\.")
