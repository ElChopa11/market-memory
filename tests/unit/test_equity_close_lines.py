"""Rank-eligible equity closes printed from retain envelopes already in hand.

Named gates: as-of / no look-ahead, set1 bytes untouched, one message within
4096 and 42, and the trade-status line stays free of Entry / SL / TP.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from mm_briefing.divergences import fmt_pct, fmt_px
from mm_briefing.equity_close_lines import (
    PHONE_LINE_MAX,
    RANK_ELIGIBLE_EQUITIES,
    EquityCaptureWriter,
    apply_equity_close,
    equity_close_print,
    load_equity_capture_file,
    write_equity_capture_file,
)
from mm_briefing.morning import PHONE_LINE_MAX as MORNING_PHONE_LINE_MAX
from mm_briefing.morning import render_morning_close
from mm_briefing.render import brief_hash, render_close
from mm_common.enums import SourceKind
from mm_delivery.format import TELEGRAM_MAX_MESSAGE_CHARS, chunk_markdown_v2
from mm_provenance.envelope import build_envelope

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
HEADER = date(2026, 9, 29)
MARKET = "2026-09-29T20:00:00+00:00"
# Ingest clock the next morning. Must not decide the print.
INGEST = "2026-09-30T20:30:00+00:00"

SET1_SHA256 = {
    "ops/reports/scheduler/completions/receipts/grok.sydney_morning__20260927T203000Z.deliver.json":
        "9592b98a317752021025af487078b402ddd9a37cc04893eda8b0d2f1d8245790",
    "ops/reports/scheduler/completions/receipts/grok.sydney_morning__20260928T203000Z.deliver.json":
        "d1bc665d0ce06c28ffd5515e0aba7239c3e341fb0ae122fc04d45f03b6b44497",
    "ops/reports/scheduler/completions/receipts/grok.sydney_morning__20260929T203000Z.deliver.json":
        "8b54f59608c28dc41d678cd65223f6d9e3db7b99e163e02a7a7d6d3df50e55c5",
    "ops/reports/scheduler/completions/grok.sydney_morning__20260927T203000Z__actions-b1-36348252592.json":
        "ac7a506a3b0bef1fae909b50b411e7de7932589996e057bd0828ae7226a80807",
    "ops/reports/scheduler/completions/grok.sydney_morning__20260928T203000Z__actions-b1-36479629926.json":
        "6b723eb062540d09bb5085387b8da1a620e0dfa763432a41cb40004a78ea19b9",
    "ops/reports/scheduler/completions/grok.sydney_morning__20260929T203000Z__actions-b1-36626767952.json":
        "c73f23e1bf7f23e3792f829e8e18fc35348d709dc0d1644c71b87aeaafae2cb7",
}
FORMAT_FREEZE_SHA256 = "c693f077010d84e3f06a75495d3c91289c5ae679f1a702fd7d4b77227d5c413d"
# DONCAPO A1 Day-7 dry-run. Box path, not in this git checkout:
# /workspace/drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md
DONCAPO_A1_SHA256 = "b5f33450ad9222d031b70cf060949688506dc59e906444dfb01a1930b78e86f1"

FENCE = """```
US Close 2026-09-29

EQUITY T-1 BY DESIGN (close 2026-09-29)

SPY 767.81 -0.72%
QQQ 741.21 -0.84%
US10Y 4.25 +5.0bp
BTC 100.00 +1.00%

gaps: VIX
NO QUALIFIED TRADE
```
"""


def _row(
    ticker: str,
    *,
    session: str = "2026-09-29",
    market: str | None = MARKET,
    value: str | None = "10.50",
    resolution: str = "grouped_daily",
    metric: str = "close",
    capture_kind: str = "lab_snapshot",
    source_name: str = "polygon",
    prior_value: str | None = None,
    prior_session_date: str | None = None,
    payload_extra: dict | None = None,
) -> dict:
    payload = {
        "value": value,
        "session_date": session,
        "resolution": resolution,
        "capture_kind": capture_kind,
        "captured_at": INGEST,
    }
    if payload_extra:
        payload.update(payload_extra)
    row = {
        "instrument": ticker,
        "metric": metric,
        "market_time": market,
        "source_name": source_name,
        "source_url_or_id": f"grouped_daily:{ticker}",
        "as_of_knowledge": INGEST,
        "ingested_at": INGEST,
        "payload": payload,
    }
    if prior_value is not None:
        row["prior_value"] = prior_value
    if prior_session_date is not None:
        row["prior_session_date"] = prior_session_date
    return row


def _sixteen(**kwargs) -> list[dict]:
    return [_row(ticker, value=f"{100 + index}.25", **kwargs) for index, ticker in enumerate(RANK_ELIGIBLE_EQUITIES)]


def _fence_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    inside = False
    for line in markdown.splitlines():
        if line.strip() == "```":
            inside = not inside
            continue
        if inside:
            lines.append(line)
    return lines


def test_phone_width_matches_morning() -> None:
    assert PHONE_LINE_MAX == MORNING_PHONE_LINE_MAX == 42


def test_rank_list_is_yaml_tickers_minus_qqq() -> None:
    spec = yaml.safe_load((ROOT / "config/ingest/mvp_retain.yaml").read_text(encoding="utf-8"))
    tickers = [str(item).upper() for item in spec["polygon"]["tickers"]]
    assert tickers[0] == "QQQ"
    assert tuple(ticker for ticker in tickers if ticker != "QQQ") == RANK_ELIGIBLE_EQUITIES
    assert "QQQ" not in RANK_ELIGIBLE_EQUITIES
    assert "SPY" not in RANK_ELIGIBLE_EQUITIES


def test_as_of_uses_session_and_market_time_not_ingest_clock() -> None:
    """Ingest is the next morning. The print still uses the session bar."""
    rows = _sixteen()
    printed = equity_close_print(rows, header_date=HEADER)
    assert printed.missing == ()
    assert [line.split(" ", 1)[0] for line in printed.lines] == list(RANK_ELIGIBLE_EQUITIES)
    for line in printed.lines:
        assert "%" not in line
        assert len(line) <= PHONE_LINE_MAX
    nvda = next(line for line in printed.lines if line.startswith("NVDA "))
    assert nvda == f"NVDA {fmt_px(103.25)}"
    # Poison: only the ingest clock matches the header. Session is the wrong day.
    lookahead = _row("NVDA", session="2026-09-30", market="2026-09-30T20:00:00+00:00", value="999")
    lookahead["as_of_knowledge"] = "2026-09-29T20:00:00+00:00"
    refused = equity_close_print([lookahead], header_date=HEADER)
    assert refused.lines == ()
    assert "NVDA" in refused.missing
    # Session claims the header date, but the vendor bar is the next day.
    mismatched = _row("NVDA", session="2026-09-29", market="2026-09-30T00:00:00+00:00", value="50")
    assert equity_close_print([mismatched], header_date=HEADER).lines == ()
    # Requested date is later. The stored session is the header date. Print.
    walked = _row(
        "AMD",
        resolution="grouped_daily_prior_session",
        payload_extra={"requested_session_date": "2026-09-30"},
    )
    walked_print = equity_close_print([walked], header_date=HEADER)
    assert walked_print.lines == (f"AMD {fmt_px(10.50)}",)
    assert "2026-09-30" not in walked_print.lines[0]


def test_missing_name_is_a_gap_and_does_not_invent_a_percent() -> None:
    rows = [_row("NVDA", value="180.12"), _row("QQQ", value="400")]
    rows.append(_row("TSLA", value=None))
    rows.append(_row("SPCX", resolution="absent_from_grouped_daily"))
    rows.append(_row("BB", capture_kind="proof"))
    rows.append(_row("GLXY", metric="funding"))
    text = apply_equity_close(FENCE, rows, header_date=HEADER)
    fence = _fence_lines(text)
    nvda_at = next(i for i, line in enumerate(fence) if line.startswith("NVDA "))
    qqq_at = next(i for i, line in enumerate(fence) if line.startswith("QQQ "))
    us10y_at = next(i for i, line in enumerate(fence) if line.startswith("US10Y "))
    assert qqq_at < nvda_at < us10y_at
    assert fence[nvda_at] == "NVDA 180.12"
    assert "0.00%" not in text
    assert "%" not in fence[nvda_at]
    assert sum(line.startswith("QQQ ") for line in fence) == 1
    gap_at = next(i for i, line in enumerate(fence) if line.startswith("gaps:"))
    status_at = next(i for i, line in enumerate(fence) if line == "NO QUALIFIED TRADE")
    gap = " ".join(fence[gap_at:status_at])
    tokens = [part.strip() for part in gap.removeprefix("gaps:").split(",") if part.strip()]
    assert "NVDA" not in tokens
    assert "QQQ" not in tokens
    for name in RANK_ELIGIBLE_EQUITIES:
        if name != "NVDA":
            assert name in tokens
    for line in fence:
        assert len(line) <= PHONE_LINE_MAX


def test_prior_close_percent_is_display_only_and_a_later_prior_is_ignored() -> None:
    shown = _row("NVDA", value="110", prior_value="100")
    line = equity_close_print([shown], header_date=HEADER).lines[0]
    assert line == f"NVDA {fmt_px(110)} {fmt_pct(10.0)}"
    level_only = _row("NVDA", value="110", prior_value="100", prior_session_date="2026-09-30")
    bare = equity_close_print([level_only], header_date=HEADER).lines[0]
    assert bare == f"NVDA {fmt_px(110)}"
    assert "0.00%" not in bare
    zero_prior = _row("AMD", value="12", prior_value="0")
    assert "%" not in equity_close_print([zero_prior], header_date=HEADER).lines[0]
    file_prior = {
        "envelopes": [_row("TSLA", value="200")],
        "priors": [
            {
                "instrument": "TSLA",
                "metric": "close",
                "value": "180",
                "session_date": "2026-09-28",
                "market_time": "2026-09-28T20:00:00+00:00",
            },
            {
                "instrument": "TSLA",
                "metric": "close",
                "value": "999",
                "session_date": "2026-09-30",
                "market_time": "2026-09-30T20:00:00+00:00",
            },
        ],
    }
    tsla = equity_close_print(file_prior, header_date=HEADER).lines[0]
    assert tsla == f"TSLA {fmt_px(200)} {fmt_pct((200 - 180) / 180 * 100)}"


def test_first_qualifying_row_wins_over_a_later_bar() -> None:
    first = _row("NVDA", value="10")
    later = _row("NVDA", value="99")
    line = equity_close_print([later, first], header_date=HEADER).lines
    # File order: the later-looking value is first and qualifies, so it wins.
    # A following row does not replace it.
    assert line == (f"NVDA {fmt_px(99)}",)
    bad_then_good = [
        _row("AMD", session="2026-09-30", market="2026-09-30T20:00:00+00:00", value="1"),
        _row("AMD", value="8"),
    ]
    assert equity_close_print(bad_then_good, header_date=HEADER).lines == (f"AMD {fmt_px(8)}",)


def test_insert_keeps_trade_status_and_adds_no_order_levels() -> None:
    text = apply_equity_close(FENCE, _sixteen(prior_value="100"), header_date=HEADER)
    assert text.count("NO QUALIFIED TRADE") == 1
    assert "Entry" not in text
    assert " SL" not in text
    assert "TP" not in text
    fence = _fence_lines(text)
    heads = [line.split(" ", 1)[0] for line in fence if line.split(" ", 1)[0] in RANK_ELIGIBLE_EQUITIES]
    assert heads == list(RANK_ELIGIBLE_EQUITIES)
    qqq = [line for line in fence if line.startswith("QQQ ")]
    assert qqq == ["QQQ 741.21 -0.84%"]
    for line in fence:
        assert len(line) <= PHONE_LINE_MAX
        assert "Entry" not in line
    assert len(text) <= TELEGRAM_MAX_MESSAGE_CHARS
    assert len(chunk_markdown_v2(text)) == 1


def test_absent_envelopes_leave_render_close_byte_identical() -> None:
    from mm_briefing.models import AssetPrint, MacroSnapshot

    as_of = datetime(2026, 9, 30, 20, 30, tzinfo=UTC)
    generated = as_of
    assets = (
        AssetPrint(
            symbol="ES",
            name="SPY",
            last=1.0,
            prior_close=1.0,
            source="polygon",
            as_of=datetime(2026, 9, 29, 20, 0, tzinfo=UTC),
            quoted_symbol="SPY",
        ),
    )
    snap = MacroSnapshot(as_of=as_of, prior_us_close=as_of, assets=assets, data_quality="ok", source="fixture")
    kwargs = dict(
        generated_at=generated,
        as_of=as_of,
        overnight=snap,
        session=snap,
        calendar=(),
        unexpected=(),
        theses=(),
        assumptions=(),
        hl=(),
        data_quality="ok",
    )
    morning = render_morning_close(**kwargs)
    via = render_close(**kwargs)
    assert via.markdown == morning.markdown
    assert via.content_hash == morning.content_hash
    with_rows = render_close(**kwargs, equity_envelopes=_sixteen())
    assert with_rows.markdown != morning.markdown
    assert with_rows.content_hash == brief_hash(with_rows.markdown)
    assert "CRCL " in with_rows.markdown
    assert len(with_rows.markdown) <= TELEGRAM_MAX_MESSAGE_CHARS


def test_writer_dumps_polygon_closes_and_persists_when_the_path_fails(tmp_path: Path) -> None:
    captured = datetime(2026, 9, 30, 20, 30, tzinfo=UTC)
    market = datetime(2026, 9, 29, 20, 0, tzinfo=UTC)
    nvda = build_envelope(
        source_name="polygon",
        source_kind=SourceKind.MACRO,
        source_url_or_id="grouped_daily:NVDA",
        instrument="NVDA",
        metric="close",
        value="180.12",
        published_at=captured,
        ingested_at=captured,
        market_time=market,
        payload={
            "session_date": "2026-09-29",
            "resolution": "grouped_daily",
            "capture_kind": "lab_snapshot",
        },
    )
    hl = build_envelope(
        source_name="hyperliquid",
        source_kind=SourceKind.EXCHANGE,
        source_url_or_id="metaAndAssetCtxs",
        instrument="BTC",
        metric="mid_px",
        value="1",
        published_at=captured,
        ingested_at=captured,
        market_time=None,
        payload={},
        venue="perp",
    )
    qqq = build_envelope(
        source_name="polygon",
        source_kind=SourceKind.MACRO,
        source_url_or_id="grouped_daily:QQQ",
        instrument="QQQ",
        metric="close",
        value="400",
        published_at=captured,
        ingested_at=captured,
        market_time=market,
        payload={
            "session_date": "2026-09-29",
            "resolution": "grouped_daily",
            "capture_kind": "lab_snapshot",
        },
    )
    # as_of_knowledge on the model is the ingest clock, not the session.
    assert nvda.as_of_knowledge == captured
    path = tmp_path / "equity.json"
    write_equity_capture_file(path, [hl, qqq, nvda])
    loaded = load_equity_capture_file(path)
    names = [row["instrument"] for row in loaded["envelopes"]]
    assert names == ["QQQ", "NVDA"]
    printed = equity_close_print(loaded, header_date=HEADER)
    assert printed.lines[0].startswith("NVDA ")
    assert all(not line.startswith("QQQ ") for line in printed.lines)
    assert "0.00%" not in "\n".join(printed.lines)

    class _Inner:
        def __init__(self) -> None:
            self.rows = None

        def persist(self, envelopes):
            self.rows = envelopes
            return "ok"

        def count_for_anchor(self, token):
            return 0

    inner = _Inner()
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    writer = EquityCaptureWriter(inner, blocker / "equity.json")
    assert writer.count_for_anchor("x") == 0
    assert writer.persist([nvda]) == "ok"
    assert inner.rows == [nvda]
    assert not (blocker / "equity.json").exists()


def test_set1_bodies_and_format_freeze_artifact_stay() -> None:
    for rel, digest in SET1_SHA256.items():
        blob = (ROOT / rel).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == digest
    freeze = ROOT / "ops/reports/renders/brief-template-dryrun.txt"
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == FORMAT_FREEZE_SHA256
    assert freeze.read_text(encoding="utf-8").startswith("```\nUS Close unavailable\n")
    assert len(DONCAPO_A1_SHA256) == 64
    assert all(char in "0123456789abcdef" for char in DONCAPO_A1_SHA256)
    # CI cannot read the box file. Pin the digest; do not copy A1 into git.
    assert not (ROOT / "drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md").exists()
    assert list(ROOT.rglob("ping-mvp-a1.md")) == []
    # The format-freeze file is its own artifact. It is not rewritten with the 16 lines.
    assert "CRCL " not in freeze.read_text(encoding="utf-8")


def test_load_rejects_a_non_envelope_object() -> None:
    import pytest

    target = Path("/tmp/equity-close-lines-bad.json")
    target.write_text(json.dumps({"nope": True}), encoding="utf-8")
    try:
        with pytest.raises(ValueError):
            load_equity_capture_file(target)
    finally:
        target.unlink(missing_ok=True)
