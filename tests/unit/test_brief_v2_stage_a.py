"""Stage A brief presentation: health score, proxy symbol, card split.

No confidence percentage, no regime label, no Stage B/C math.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mm_briefing.cards import message_texts_for_pulse, split_brief_cards
from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_from_fixture, load_fixture_file
from mm_briefing.health import score_data_health
from mm_briefing.models import AssetPrint, HLInstrumentState, MacroSnapshot
from mm_briefing.render import render_close
from mm_delivery.config import load_telegram_settings
from mm_delivery.payload import build_payload

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
AS_OF = datetime(2026, 3, 10, 20, 15, tzinfo=timezone.utc)
PRIOR = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)


def _print(symbol: str, *, quoted: str | None = None, quality: str = "ok", structural: bool = False) -> AssetPrint:
    return AssetPrint(
        symbol=symbol,
        name=f"{quoted or symbol} label",
        last=1.0,
        prior_close=1.0,
        data_quality=quality,
        source="polygon" if quoted else "fixture",
        as_of=AS_OF,
        observation_id="obs-1",
        quoted_symbol=quoted,
        structural_unavailable=structural,
    )


def test_structural_vix_does_not_zero_the_health_header() -> None:
    assets = (
        _print("ES", quoted="SPY"),
        _print("NQ", quoted="QQQ"),
        _print("US10Y", quality="ok"),
        _print("DXY", quoted="UUP"),
        _print("CL", quoted="USO"),
        AssetPrint(
            symbol="VIX",
            name="CBOE VIX (structurally unavailable without Cboe entitlement)",
            last=None,
            prior_close=None,
            data_quality="unavailable",
            source="polygon",
            as_of=AS_OF,
            structural_unavailable=True,
        ),
        _print("BTC"),
        _print("ETH"),
    )
    hl = (
        HLInstrumentState(
            instrument="BTC",
            metrics={},
            liquidations=(),
            levels=(),
            data_quality="ok",
            source="hyperliquid.info",
        ),
    )
    report = score_data_health(assets, hl)
    assert report.insufficient is False
    assert report.pct == 100
    assert "Vol" in report.structural_excluded
    header = "\n".join(report.header_lines(icons={"fresh": "🟢", "degraded": "🟡", "stale": "🟠", "unavailable": "⚪"}))
    assert header.startswith("Data health: 100%")
    assert "Data quality: unavailable" not in header
    assert "INSUFFICIENT DATA" in header  # regime stub only
    assert "Green is not a direction" in header
    vol = next(row for row in report.domains if row.id == "vol")
    assert vol.excluded is True
    assert vol.state == "unavailable"
    assert "not a Neon gap" in vol.detail


def test_proxy_symbol_column_prints_the_quoted_ticker() -> None:
    assets = (
        _print("DXY", quoted="UUP"),
        _print("CL", quoted="USO"),
    )
    snap = MacroSnapshot(
        as_of=AS_OF,
        prior_us_close=PRIOR,
        assets=assets,
        data_quality="ok",
        source="live",
    )
    doc = render_close(
        generated_at=AS_OF,
        as_of=AS_OF,
        overnight=snap,
        session=snap,
        calendar=(),
        unexpected=(),
        theses=(),
        assumptions=(),
        hl=(),
        data_quality="unavailable",
    )
    assert "| USD | UUP |" in doc.markdown
    assert "| oil | USO |" in doc.markdown
    assert "| USD | DXY |" not in doc.markdown
    assert "| oil | CL |" not in doc.markdown
    assert "slot=DXY" in doc.markdown
    assert "slot=CL" in doc.markdown
    assert not any(line.startswith("Data quality:") for line in doc.markdown.splitlines())
    assert "Data health:" in doc.markdown


def test_fixture_brief_splits_into_ordered_cards_and_skips_empty() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("close", fixture, settings=settings)
    assert doc is not None
    cards = split_brief_cards(doc.markdown)
    ids = [card_id for card_id, _body in cards]
    order = ("executive", "dashboard", "macro", "crypto", "positioning", "catalysts", "scenarios", "audit")
    assert ids == [card_id for card_id in order if card_id in ids]
    assert "positioning" not in ids
    assert "scenarios" not in ids
    assert "executive" in ids and "dashboard" in ids and "audit" in ids
    joined = "\n".join(body for _id, body in cards)
    assert "Regime: INSUFFICIENT DATA" in joined
    assert "01FROZENBTCFUNDING00000001" in joined
    assert "obs " in joined or "obs none" in joined
    assert "as-of=" in joined or "As-of" in joined
    assert "risk-on" not in joined.lower()
    assert "risk-off" not in joined.lower()
    import re

    assert re.search(r"\d+\s*%\s*confidence", joined, flags=re.IGNORECASE) is None
    for _card_id, body in cards:
        assert set(body.strip()) != {"-", "—", " "}


def test_pulse_delivery_uses_cards_not_one_4096_chunk(tmp_path: Path) -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert doc is not None
    texts = message_texts_for_pulse(doc.markdown)
    assert texts is not None
    assert len(texts) >= 4
    assert texts[0].startswith("executive (1/")
    payload = build_payload(
        doc.markdown,
        desk="ops",
        as_of=AS_OF,
        settings=load_telegram_settings(ROOT),
        message_texts=texts,
    )
    # One message per card, plus a safety split only if a single card exceeds 4096 after escape.
    assert len(payload.chunks) >= len(texts)
    assert payload.chunks[0].startswith("executive")
    assert "dashboard" in payload.chunks[1]
    # Desk-pack markdown is not a pulse brief and must not be card-split.
    assert message_texts_for_pulse("# Desk pack\n\nhello\n") is None


def test_lab_deliver_pack_sends_brief_as_cards(tmp_path: Path, capsys) -> None:
    import json

    from mm_lab_cli.cli import main

    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("close", fixture, settings=settings)
    assert doc is not None
    path = tmp_path / "close.md"
    path.write_text(doc.markdown, encoding="utf-8")
    out = tmp_path / "out"
    rc = main(
        [
            "deliver",
            "pack",
            "--desk",
            "ops",
            "--from-markdown",
            str(path),
            "--as-of",
            "2026-03-10T20:15:00Z",
            "--no-send",
            "--no-db",
            "--repo-root",
            str(ROOT),
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sent"] is False
    assert payload["chunks"] >= 4
    envelope = json.loads((out / "briefs" / "2026-03-10" / "telegram-payload.json").read_text(encoding="utf-8"))
    texts = [row["text"] for row in envelope["chunks"]]
    assert texts[0].startswith("executive")
    assert all("positioning (" not in text for text in texts)
    assert any("01FROZENBTCFUNDING00000001" in text for text in texts)
