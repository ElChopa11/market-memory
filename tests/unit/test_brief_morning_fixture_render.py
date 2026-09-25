"""Fixture render of one morning close. No network.

Polygon, FRED, and Hyperliquid bodies are saved responses. The tokens passed
to the fetcher are the literal string ``fixture``, not Actions secrets.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_close
from mm_briefing.fetchers import LiveMacroFetcher, live_macro_spec
from mm_briefing.hl import hl_from_live_info
from mm_briefing.models import MORNING_HL_PERPS
from mm_briefing.morning import PHONE_LINE_MAX
from mm_briefing.prior import MapPriorCaptureReader, PriorCaptureValue
from mm_delivery.format import TELEGRAM_MAX_MESSAGE_CHARS
from mm_ingest.hl_info import HyperliquidInfoClient

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "briefing"
POLYGON = FIXTURE_DIR / "morning_polygon_aggs.json"
FRED_ROLLED = FIXTURE_DIR / "morning_fred_rolled.json"
FRED_UNROLLED = FIXTURE_DIR / "morning_fred_unrolled.json"
HL_META = FIXTURE_DIR / "morning_hl_meta_and_asset_ctxs.json"
GOLDEN_ROLLED = FIXTURE_DIR / "morning_fixture_rolled.txt"
GOLDEN_UNROLLED = FIXTURE_DIR / "morning_fixture_unrolled.txt"

AS_OF = datetime(2026, 9, 25, 8, 30, tzinfo=timezone.utc)
FRED_AS_OF_ROLLED = "2026-09-24"
FRED_AS_OF_UNROLLED = "2026-09-23"
BAR_DATE = "2026-09-24"
# Not an Actions secret. The fetcher only checks that the string is non-empty.
FIXTURE_TOKEN = "fixture"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_fixture_morning(*, fred_path: Path, prior_reader=None) -> tuple[str, object]:
    """Parse saved Polygon, FRED, and metaAndAssetCtxs bodies. No live HTTP."""
    settings = load_briefing_settings(ROOT)
    spec = live_macro_spec(settings.macro)
    spec["live"]["coingecko"]["enabled"] = False
    spec["live"]["stooq"]["enabled"] = False
    polygon = _load(POLYGON)
    fred = _load(fred_path)
    hl_body = _load(HL_META)
    seen: list[str] = []

    def macro_handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        seen.append(host)
        if host == "api.polygon.io":
            for ticker, body in polygon.items():
                if f"/ticker/{ticker}/" in request.url.path:
                    return httpx.Response(200, json=body)
            return httpx.Response(400, json={"status": "NOT_FOUND"})
        if host == "api.stlouisfed.org":
            return httpx.Response(200, json=fred)
        return httpx.Response(400, json={"error": "fixture transport refuses this host"})

    def hl_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        info_type = str(body.get("type"))
        seen.append(info_type)
        if info_type == "metaAndAssetCtxs":
            return httpx.Response(200, json=hl_body)
        return httpx.Response(400, json={"error": "fixture transport refuses this info type"})

    macro_client = httpx.Client(transport=httpx.MockTransport(macro_handler))
    snap = LiveMacroFetcher(
        spec,
        client=macro_client,
        env={"POLYGON_API_KEY": FIXTURE_TOKEN, "FRED_API_KEY": FIXTURE_TOKEN},
        sleep=lambda _: None,
    ).fetch(AS_OF, prior_us_close=datetime(2026, 9, 24, 20, 0, tzinfo=timezone.utc))
    hl_client = HyperliquidInfoClient(transport=httpx.MockTransport(hl_handler))
    hl = hl_from_live_info(
        hl_client,
        instruments=MORNING_HL_PERPS,
        captured_at=AS_OF,
        include_liquidations=False,
    )
    doc = generate_close(
        as_of=AS_OF,
        settings=settings,
        overnight=snap,
        session=snap,
        hl=hl,
        theses=(),
        generated_at=AS_OF,
        prior_reader=prior_reader,
    )
    assert set(seen) <= {"api.polygon.io", "api.stlouisfed.org", "metaAndAssetCtxs"}
    assert "spotMetaAndAssetCtxs" not in seen
    assert seen.count("metaAndAssetCtxs") == 1
    return doc.markdown, snap


def _fence_lines(text: str) -> list[str]:
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.strip() == "```":
            inside = not inside
            continue
        if inside:
            lines.append(line)
    return lines


def _assert_common(text: str) -> None:
    assert "FIXTURE" not in text
    assert "RECORDED DATA" not in text
    assert len(text) <= TELEGRAM_MAX_MESSAGE_CHARS
    assert text.startswith("```\n")
    assert text.rstrip().endswith("```")
    fence = _fence_lines(text)
    for line in fence:
        assert len(line) <= PHONE_LINE_MAX, line
    assert "US Close 2026-09-24" in text
    assert "EQUITY T-1 BY DESIGN (close 2026-09-24)" in text
    assert "US Close 2026-09-25" not in text
    assert "US Close unavailable" not in text
    for ticker in ("SPY ", "QQQ ", "UUP ", "USO "):
        assert any(line.startswith(ticker) for line in fence)
    for name in MORNING_HL_PERPS:
        assert any(line.startswith(f"{name} ") for line in fence)
    fund_lines = [line for line in fence if " fund " in line]
    assert fund_lines == ["UNI fund 12.26% ann", "ZEC fund 0.88% ann"]
    assert "Funding" not in text
    gap_lines = [line for line in fence if line.startswith("gaps:")]
    assert gap_lines == ["gaps: VIX"]
    assert "KEY TAKEAWAY" not in text
    assert "Earlier pair" not in text


def test_fixture_polygon_fred_hl_rolled_render() -> None:
    text, snap = render_fixture_morning(fred_path=FRED_ROLLED)
    _assert_common(text)
    us10y = snap.by_symbol()["US10Y"]
    assert us10y.source == "fred"
    assert us10y.as_of is not None
    assert us10y.as_of.date().isoformat() == FRED_AS_OF_ROLLED
    assert us10y.last == 4.15
    fence = _fence_lines(text)
    us10y_lines = [line for line in fence if "US10Y" in line]
    assert us10y_lines == [f"US10Y 4.15 +4.0bp"]
    assert FRED_AS_OF_ROLLED not in "\n".join(us10y_lines)
    assert "no new print since" not in text
    sol = next(line for line in fence if line.startswith("SOL "))
    assert sol.startswith("SOL 117.365 ")
    assert text == GOLDEN_ROLLED.read_text(encoding="utf-8")
    assert len(text.splitlines()) == len(GOLDEN_ROLLED.read_text(encoding="utf-8").splitlines())


def test_fixture_fred_did_not_roll_us10y_no_new_print() -> None:
    prior = MapPriorCaptureReader(
        {
            ("US10Y", "close"): PriorCaptureValue(
                instrument="US10Y",
                metric="close",
                value=4.11,
                captured_at=datetime(2026, 9, 24, 23, 17, tzinfo=timezone.utc),
                prior_captured_at=datetime(2026, 9, 23, 20, 30, tzinfo=timezone.utc),
                observation_as_of=datetime(2026, 9, 23, tzinfo=timezone.utc),
            )
        }
    )
    text, snap = render_fixture_morning(fred_path=FRED_UNROLLED, prior_reader=prior)
    _assert_common(text)
    us10y = snap.by_symbol()["US10Y"]
    assert us10y.as_of is not None
    assert us10y.as_of.date().isoformat() == FRED_AS_OF_UNROLLED
    fence = _fence_lines(text)
    us10y_lines = [line for line in fence if "US10Y" in line]
    assert us10y_lines == [f"US10Y 4.11 no new print since {FRED_AS_OF_UNROLLED}"]
    assert text.count("US10Y") == 1
    assert "stale Rates" in text
    assert text == GOLDEN_UNROLLED.read_text(encoding="utf-8")
