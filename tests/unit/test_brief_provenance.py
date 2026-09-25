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
from mm_briefing.models import MORNING_HL_PERPS, REQUIRED_SLOTS, pulse_quality
from mm_briefing.morning import _named_perp_line
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
    assert snap.by_symbol()["ES"].source == "polygon"
    assert snap.by_symbol()["VIX"].source == "polygon"
    assert snap.by_symbol()["BTC"].source == "hyperliquid"
    assert snap.by_symbol()["ETH"].source == "hyperliquid"


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
    assert "universe membership" in lowered
    assert "active_call" not in lowered
    assert "active call" not in lowered


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
    assert by_inst["BTC"].metric("prev_day_px") is not None
    assert by_inst["BTC"].metric("prev_day_px").value == "64000.0"


def test_close_live_hl_is_one_meta_call() -> None:
    fixture = json.loads(HL_WINDOW.read_text(encoding="utf-8"))
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(str(body.get("type")))
        if body.get("type") == "metaAndAssetCtxs":
            return httpx.Response(200, json=fixture["metaAndAssetCtxs"])
        return httpx.Response(500, json={"error": "unexpected type"})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(handler))
    states = hl_from_live_info(
        client,
        instruments=("BTC", "SOL"),
        captured_at=AS_OF,
        include_liquidations=False,
    )
    assert seen == ["metaAndAssetCtxs"]
    assert [row.instrument for row in states] == ["BTC", "SOL"]
    assert states[0].liquidations == ()
    assert states[0].metric("prev_day_px") is not None


def test_sol_resolves_to_exact_perp_name_not_prefix() -> None:
    """SOL is the perp universe entry named SOL, never a prefix or substring.

    USOL, SOLV, and RESOLV sit both before and after that entry. A substring
    or prefix match would bind one of those ctxs. The close path posts
    metaAndAssetCtxs only.
    """
    # Index 5 is the exact perp name, with decoys on either side.
    names = ["BTC", "ETH", "USOL", "SOLV", "RESOLV", "SOL", "SOLV", "USOL", "RESOLV"]
    assert names.index("SOL") == 5
    mids = {
        2: "1.111",  # USOL before SOL
        3: "2.222",  # SOLV before SOL
        4: "3.333",  # RESOLV before SOL
        5: "117.365",  # exact SOL
        6: "4.444",  # SOLV after SOL
        7: "5.555",  # USOL after SOL
        8: "6.666",  # RESOLV after SOL
    }
    prevs = {idx: f"{idx}.5" for idx in mids}
    prevs[5] = "114.08"
    marks = {idx: f"{idx}.25" for idx in mids}
    marks[5] = "117.19"
    universe = [{"name": name, "maxLeverage": 3} for name in names]
    ctxs = []
    for idx, name in enumerate(names):
        ctxs.append(
            {
                "midPx": mids.get(idx, "9.999"),
                "markPx": marks.get(idx, "9.25"),
                "prevDayPx": prevs.get(idx, "9.5"),
                "oraclePx": "1",
                "funding": "0.0000125",
                "openInterest": "10",
            }
        )
    payload = [{"universe": universe}, ctxs]
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(str(body.get("type")))
        if body.get("type") == "metaAndAssetCtxs":
            return httpx.Response(200, json=payload)
        return httpx.Response(500, json={"error": "spot or other type is not the close path"})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(handler))
    states = hl_from_live_info(
        client,
        instruments=MORNING_HL_PERPS,
        captured_at=AS_OF,
        include_liquidations=False,
    )
    assert seen == ["metaAndAssetCtxs"]
    by_inst = {row.instrument: row for row in states}
    assert list(by_inst) == list(MORNING_HL_PERPS)
    sol = by_inst["SOL"]
    assert sol.instrument == "SOL"
    assert sol.metric("mid_px") is not None
    assert sol.metric("mid_px").value == "117.365"
    assert sol.metric("mark_px") is not None
    assert sol.metric("mark_px").value == "117.19"
    assert sol.metric("prev_day_px") is not None
    assert sol.metric("prev_day_px").value == "114.08"
    for decoy in ("1.111", "2.222", "3.333", "4.444", "5.555", "6.666"):
        assert sol.metric("mid_px").value != decoy
    assert "USOL" not in by_inst
    assert "SOLV" not in by_inst
    assert "RESOLV" not in by_inst
    line, gap = _named_perp_line(sol)
    assert line == "SOL 117.365 +2.88%"
    assert gap is None

    absent = [{"name": name} for name in ("USOL", "SOLV", "RESOLV")]
    absent_ctxs = [
        {"midPx": "1.111", "markPx": "1", "prevDayPx": "1", "funding": "0.0000125", "openInterest": "1"},
        {"midPx": "2.222", "markPx": "2", "prevDayPx": "2", "funding": "0.0000125", "openInterest": "1"},
        {"midPx": "3.333", "markPx": "3", "prevDayPx": "3", "funding": "0.0000125", "openInterest": "1"},
    ]
    seen.clear()

    def absent_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(str(body.get("type")))
        if body.get("type") == "metaAndAssetCtxs":
            return httpx.Response(200, json=[{"universe": absent}, absent_ctxs])
        return httpx.Response(500, json={"error": "unexpected type"})

    client = HyperliquidInfoClient(transport=httpx.MockTransport(absent_handler))
    missing = hl_from_live_info(
        client,
        instruments=("SOL",),
        captured_at=AS_OF,
        include_liquidations=False,
    )
    assert seen == ["metaAndAssetCtxs"]
    assert missing[0].instrument == "SOL"
    assert missing[0].metric("mid_px") is None
    assert missing[0].metric("prev_day_px") is None
    assert _named_perp_line(missing[0]) == (None, "SOL")
