"""Missing/stale sources stay visible; provenance links; no-trading boundary."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_from_fixture, generate_preopen, load_fixture_file
from mm_briefing.fetchers import LiveMacroFetcher, complete_cross_asset, empty_snapshot, snapshot_from_payload
from mm_briefing.hl import hl_from_live_info, hl_from_payload
from mm_briefing.models import REQUIRED_SLOTS, pulse_quality
from mm_briefing.render import NO_DECISION_FOOTER
from mm_briefing.store import dod_relpath, write_brief
from mm_ingest.hl_info import ALLOWED_INFO_TYPES, HyperliquidInfoClient


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
HL_WINDOW = ROOT / "tests" / "fixtures" / "hl_window.json"
AS_OF = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
PRIOR = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)


def test_missing_cross_asset_slots_are_unavailable_not_omitted() -> None:
    snap = complete_cross_asset(empty_snapshot(AS_OF, PRIOR, reason="off", source="off"))
    symbols = [row.symbol for row in snap.assets]
    assert symbols[:8] == ["ES", "NQ", "US10Y", "DXY", "CL", "VIX", "BTC", "ETH"]
    assert {row.slot for row in snap.assets} >= set(REQUIRED_SLOTS)
    assert all(row.data_quality == "unavailable" for row in snap.assets)
    assert snap.by_symbol()["US10Y"].source == "fred"
    assert snap.by_symbol()["ES"].source == "stooq"


def test_stale_and_unavailable_appear_in_markdown() -> None:
    settings = load_briefing_settings(ROOT)
    payload = {
        "source": "test",
        "data_quality": "partial",
        "assets": [
            {
                "symbol": "ES",
                "last": 5750.0,
                "prior_close": 5720.0,
                "data_quality": "stale",
                "source": "stooq",
            },
            {"symbol": "BTC", "last": None, "prior_close": None, "data_quality": "unavailable", "source": "none"},
        ],
    }
    macro = complete_cross_asset(snapshot_from_payload(payload, as_of=AS_OF, prior_us_close=PRIOR, source="test"))
    fixture = load_fixture_file(FIXTURE)
    hl = hl_from_payload(fixture["hyperliquid"])
    doc = generate_preopen(as_of=AS_OF, settings=settings, macro=macro, hl=hl, generated_at=AS_OF)
    assert "| ES |" in doc.markdown
    assert "| US10Y |" in doc.markdown
    assert "equity-index proxy" in doc.markdown
    assert "unavailable" in doc.markdown
    assert "stale" in doc.markdown
    assert "n/a" in doc.markdown
    # Do not drop the empty rates slot.
    assert "US10Y" in doc.markdown


def test_provenance_links_and_watermark() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert doc is not None
    assert "Memory watermark (as_of_knowledge): 2026-03-10T12:00:00+00:00" in doc.markdown
    assert "01FROZENBTCFUNDING00000001" in doc.markdown
    assert "source: config/briefing/calendar.yaml" in doc.markdown
    assert "source=fixture" in doc.markdown
    assert "market_time" in doc.markdown
    assert "null (snapshot; capture is as_of_knowledge / ingested_at)" in doc.markdown or "market_time" in doc.markdown
    assert "As-of knowledge:" in doc.markdown
    assert all(line in doc.markdown for line in NO_DECISION_FOOTER)
    for slot in REQUIRED_SLOTS:
        assert slot in doc.markdown


def test_required_slots_listed_when_macro_off() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    hl = hl_from_payload(fixture["hyperliquid"])
    macro = complete_cross_asset(empty_snapshot(AS_OF, PRIOR, reason="off", source="off"))
    doc = generate_preopen(as_of=AS_OF, settings=settings, macro=macro, hl=hl, generated_at=AS_OF)
    for slot in REQUIRED_SLOTS:
        assert slot in doc.markdown
    assert "unavailable" in doc.markdown
    assert "n/a" in doc.markdown


def test_briefing_tree_has_no_execution_or_signing_surface() -> None:
    briefing_root = ROOT / "packages" / "briefing"
    extra = [
        ROOT / "apps" / "lab-cli" / "src" / "mm_lab_cli" / "briefing.py",
        ROOT / "apps" / "briefing-worker" / "src" / "mm_briefing_worker" / "__init__.py",
    ]
    for path in list(briefing_root.rglob("*.py")) + extra:
        text = path.read_text(encoding="utf-8")
        assert "mm_execution" not in text
        assert "hl_trade" not in text
        assert "from mm_execution" not in text


def test_no_trading_language_in_preopen() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert doc is not None
    lowered = doc.markdown.lower()
    for phrase in ("buy now", "sell now", "place order", "increase size", "go long", "go short"):
        assert phrase not in lowered
    assert "informational only" in lowered
    assert "no order intent" in lowered
    assert "active_call" in lowered


def test_dual_write_dod_and_legacy_paths(tmp_path: Path) -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(FIXTURE)
    doc, _ = generate_from_fixture("preopen", fixture, settings=settings)
    assert doc is not None
    canonical = write_brief(doc, root=tmp_path)
    assert canonical == tmp_path / "briefs" / "2026-03-10" / "us-pre-market.md"
    legacy = tmp_path / "briefs" / "2026" / "03" / "10" / "preopen.md"
    assert canonical.is_file() and legacy.is_file()
    assert canonical.read_text(encoding="utf-8") == legacy.read_text(encoding="utf-8")
    assert dod_relpath(doc) == Path("briefs/2026-03-10/us-pre-market.md")


def test_fred_missing_key_does_not_invent_us10y() -> None:
    spec = {
        "live": {
            "enabled": True,
            "fred": {"enabled": True, "api_key_env": "FRED_API_KEY", "series": {"US10Y": "DGS10"}},
            "stooq": {"enabled": False},
            "coingecko": {"enabled": False},
        }
    }
    snap = complete_cross_asset(LiveMacroFetcher(spec, env={}).fetch(AS_OF, prior_us_close=PRIOR))
    us10y = snap.by_symbol()["US10Y"]
    assert us10y.last is None
    assert pulse_quality(us10y.data_quality) == "unavailable"
    assert any("FRED_API_KEY" in note for note in snap.notes)


def test_live_hl_posts_only_allowlisted_types() -> None:
    fixture = json.loads(HL_WINDOW.read_text(encoding="utf-8"))
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(str(body.get("type")))
        info_type = str(body.get("type"))
        if info_type == "metaAndAssetCtxs":
            return httpx.Response(200, json=fixture["metaAndAssetCtxs"])
        if info_type == "recentTrades":
            return httpx.Response(200, json=[])
        return httpx.Response(500, json={"error": "unexpected type"})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(handler))
    states = hl_from_live_info(client, captured_at=AS_OF)
    assert set(seen) <= set(ALLOWED_INFO_TYPES)
    assert "clearinghouseState" not in seen
    assert "userFills" not in seen
    by_inst = {row.instrument: row for row in states}
    assert "BTC" in by_inst
    assert by_inst["BTC"].metric("mid_px") is not None
    assert by_inst["BTC"].metric("mid_px").observation_id is None
    assert by_inst["BTC"].metric("mid_px").source_url is not None
    assert "info" in (by_inst["BTC"].metric("mid_px").source_url or "")
    # ETH OI is null in the fixture — must stay missing, not invented.
    eth_oi = by_inst["ETH"].metric("open_interest")
    assert eth_oi is not None
    assert eth_oi.value is None
