"""Forward-only MVP retain: allowlists, PRICE-ONLY DRV, no history backfill."""

from __future__ import annotations

import inspect
import json
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest

from mm_common.enums import DataQuality
from mm_common.hashing import claim_hash
from mm_common.http import ERROR_MISSING_ENV
from mm_ingest.config import load_instruments
from mm_ingest.equities.polygon import GROUPED_DAILY_PATH, PolygonEquitiesAdapter
from mm_ingest.hl_info import ALLOWED_INFO_TYPES, FORBIDDEN_INFO_TYPES, HyperliquidInfoClient
from mm_ingest.mvp_retain import (
    HISTORY_BACKFILL_WIRED,
    LIVE_NEON_ENABLED,
    build_retain_envelopes,
    capture_mvp_retain,
    http_plan,
    load_mvp_retain_spec,
    persist_mvp_retain,
)
from mm_lab_cli.cli import main

ROOT = Path(__file__).resolve().parents[2]

BOUND = (
    "BTC",
    "ETH",
    "SOL",
    "JUP",
    "HYPE",
    "LIT",
    "NEAR",
    "ARB",
    "UNI",
    "VVV",
    "ZEC",
    "DOGE",
    "XMR",
    "CASHCAT",
    "PONS",
    "CHIP",
    "LTC",
    "NIL",
    "PURR",
)
EQUITIES = (
    "QQQ",
    "CRCL",
    "TSLA",
    "SPCX",
    "NVDA",
    "BB",
    "GLXY",
    "IBIT",
    "BMNR",
    "MRNA",
    "GOOG",
    "HOOD",
    "NOW",
    "CBRS",
    "MSTR",
    "STRC",
    "AMD",
)
VENUE_QUEUE = {"SPX", "NQ1!", "CL1!", "BTC1!", "SAMSUN", "KOSDA"}
BAR = datetime(2026, 9, 23, 4, 0, tzinfo=timezone.utc)
BAR_MS = int(BAR.timestamp() * 1000)
CAPTURE = datetime(2026, 9, 24, 20, 32, tzinfo=timezone.utc)
PRIOR = datetime(2026, 9, 23, 20, 32, tzinfo=timezone.utc)
OFF_WINDOW = datetime(2026, 9, 24, 1, 15, tzinfo=timezone.utc)


def _perp_payload(*extra: str) -> list:
    names = list(BOUND) + list(extra)
    universe = [{"name": name, "maxLeverage": 3} for name in names]
    ctxs = []
    for i, name in enumerate(names):
        ctxs.append(
            {
                "midPx": str(1000 + i),
                "funding": "0.0001",
                "openInterest": str(5000 + i),
                "markPx": str(9000 + i),
            }
        )
    return [{"universe": universe}, ctxs]


def _spot_payload(*, mid: str | None = "1.25", tokens: list | None = None, name: str = "@700") -> list:
    token_ids = [843, 0] if tokens is None else tokens
    ctx: dict = {"markPx": "1.0", "funding": "0.8", "openInterest": "77"}
    if mid is not None:
        ctx["midPx"] = mid
    else:
        ctx["midPx"] = None
    return [
        {
            "tokens": [
                {"name": "DRV", "index": 843},
                {"name": "USDC", "index": 0},
                {"name": "KNT", "index": 9},
            ],
            "universe": [
                {"name": "OTHER/USDC", "index": 1, "tokens": [1, 0]},
                {"name": name, "index": 700, "tokens": token_ids},
            ],
        },
        [
            {"midPx": "9.9", "markPx": "9.9", "funding": "0.2", "openInterest": "3"},
            ctx,
        ],
    ]


def _grouped(*extra: str) -> dict:
    results = [{"T": ticker, "c": 10 + i, "t": BAR_MS, "o": 1, "h": 2, "l": 0.5} for i, ticker in enumerate(EQUITIES)]
    for ticker in extra:
        results.append({"T": ticker, "c": 999, "t": BAR_MS})
    return {"status": "OK", "resultsCount": len(results), "results": results}


def _build(*, spot=None, prior=PRIOR, captured_at=CAPTURE, extra_perps=(), grouped_error=None, grouped=None):
    spec = load_mvp_retain_spec()
    return build_retain_envelopes(
        spec,
        meta_and_asset_ctxs=_perp_payload(*extra_perps),
        grouped_daily=_grouped("SPX", "AAPL", "NQ1!", "SAMSUN", "KOSDA") if grouped is None else grouped,
        captured_at=captured_at,
        prior_captured_at=prior,
        session_date=date(2026, 9, 23),
        spot_meta_and_asset_ctxs=spot,
        grouped_error=grouped_error,
    )


def test_allowlist_is_19_plus_drv_plus_17() -> None:
    spec = load_mvp_retain_spec()
    assert spec.bound_symbols == BOUND
    assert spec.bound_metrics == ("open_interest", "funding", "mid_px")
    assert spec.price_only_symbol == "DRV"
    assert spec.price_only_metrics == ("mid_px",)
    assert spec.spot_index == 700
    assert spec.spot_pair == "DRV/USDC"
    assert spec.equity_symbols == EQUITIES
    assert spec.equity_metric == "close"
    assert spec.instrument_count == 37
    assert "PURR" in spec.bound_symbols
    assert "LIT" in spec.bound_symbols and "LTC" in spec.bound_symbols
    assert "KNT" in spec.dropped and "KNTQ" in spec.dropped
    assert "KNT" not in spec.bound_symbols
    assert "DRV" not in spec.bound_symbols
    assert spec.venue_queue == VENUE_QUEUE
    assert spec.blocked == {"CASHCAT", "PONS"}
    assert spec.monitor == {"JUP", "NIL", "DRV"}
    assert HISTORY_BACKFILL_WIRED is False
    assert LIVE_NEON_ENABLED is False
    assert load_instruments() == ["BTC", "ETH", "UNI", "AAVE"]


def test_bound_rows_price_only_drv_and_equity_closes() -> None:
    envelopes = _build(spot=_spot_payload())
    by_inst: dict[str, set[str]] = {}
    for envelope in envelopes:
        by_inst.setdefault(envelope.instrument, set()).add(envelope.metric)
    assert set(by_inst) == set(BOUND) | {"DRV"} | set(EQUITIES)
    assert len(by_inst) == 37
    assert len(envelopes) == 19 * 3 + 1 + 17
    for symbol in BOUND:
        assert by_inst[symbol] == {"open_interest", "funding", "mid_px"}
    assert by_inst["DRV"] == {"mid_px"}
    for ticker in EQUITIES:
        assert by_inst[ticker] == {"close"}
    assert "KNT" not in by_inst and "KNTQ" not in by_inst and "AAVE" not in by_inst
    assert not (VENUE_QUEUE & set(by_inst))
    assert "AAPL" not in by_inst
    purr = next(e for e in envelopes if e.instrument == "PURR" and e.metric == "open_interest")
    assert purr.payload["quadrant_eligible"] is True
    assert purr.market_time is None
    lit = next(e for e in envelopes if e.instrument == "LIT" and e.metric == "mid_px")
    ltc = next(e for e in envelopes if e.instrument == "LTC" and e.metric == "mid_px")
    assert lit.identity.value != ltc.identity.value
    drv = next(e for e in envelopes if e.instrument == "DRV")
    assert drv.identity.value == "1.25"
    assert drv.payload["quadrant_eligible"] is False
    assert drv.payload["resolution"] == "spot_index_700"
    assert drv.payload["watch_tier"] == "monitor"
    assert drv.market_time is None
    cash = next(e for e in envelopes if e.instrument == "CASHCAT" and e.metric == "funding")
    assert cash.payload["watch_tier"] == "blocked"
    assert cash.payload["policy"] == "store_only"
    jup = next(e for e in envelopes if e.instrument == "JUP" and e.metric == "mid_px")
    assert jup.payload["watch_tier"] == "monitor"
    btc = next(e for e in envelopes if e.instrument == "BTC" and e.metric == "mid_px")
    assert btc.payload["watch_tier"] is None
    qqq = next(e for e in envelopes if e.instrument == "QQQ")
    assert qqq.metric == "close"
    assert qqq.market_time == BAR
    assert qqq.published_at == CAPTURE
    assert qqq.ingested_at == CAPTURE
    assert qqq.as_of_knowledge == CAPTURE
    assert qqq.identity.value == "10"


def test_drv_null_mid_does_not_copy_mark_and_skips_oi_funding() -> None:
    envelopes = _build(spot=_spot_payload(mid=None), extra_perps=("DRV", "KNT", "KNTQ", "AAVE"))
    drv_rows = [e for e in envelopes if e.instrument == "DRV"]
    assert [e.metric for e in drv_rows] == ["mid_px"]
    assert drv_rows[0].identity.value is None
    assert drv_rows[0].data_quality is DataQuality.PARTIAL
    assert drv_rows[0].identity.value != "1"
    assert "KNT" not in {e.instrument for e in envelopes}


def test_drv_from_perp_name_is_still_price_only() -> None:
    envelopes = _build(spot=None, extra_perps=("DRV", "KNT"))
    drv_rows = [e for e in envelopes if e.instrument == "DRV"]
    assert len(drv_rows) == 1
    assert drv_rows[0].metric == "mid_px"
    assert drv_rows[0].payload["resolution"] == "perp_name_price_only"
    assert drv_rows[0].identity.value is not None
    assert "KNT" not in {e.instrument for e in envelopes}


def test_drv_absent_from_perp_meta_is_partial_mid_only() -> None:
    envelopes = _build(spot=None, extra_perps=())
    drv_rows = [e for e in envelopes if e.instrument == "DRV"]
    assert [e.metric for e in drv_rows] == ["mid_px"]
    assert drv_rows[0].identity.value is None
    assert drv_rows[0].payload["resolution"] == "absent_from_metaAndAssetCtxs"
    assert drv_rows[0].data_quality is DataQuality.PARTIAL


def test_spot_index_uses_universe_position_not_ctx_slot_700() -> None:
    envelopes = _build(spot=_spot_payload(mid="1.25"))
    drv = next(e for e in envelopes if e.instrument == "DRV")
    assert drv.identity.value == "1.25"


def test_lookalike_spot_pair_does_not_bind() -> None:
    payload = _spot_payload(tokens=[9, 0], name="@700")
    envelopes = _build(spot=payload)
    drv = next(e for e in envelopes if e.instrument == "DRV")
    assert drv.identity.value is None
    assert drv.payload["resolution"] == "mismatch"
    assert "KNT" not in {e.instrument for e in envelopes}


def test_consecutive_captures_keep_true_timestamps_and_interval() -> None:
    first = _build(spot=_spot_payload(), prior=None, captured_at=PRIOR)
    second = _build(spot=_spot_payload(), prior=PRIOR, captured_at=CAPTURE)
    assert all("interval_seconds" not in e.payload for e in first)
    assert {e.payload["interval_seconds"] for e in second} == {86400}
    assert {e.payload["pair"] for e in second} == {"consecutive_capture"}
    btc_first = next(e for e in first if e.instrument == "BTC" and e.metric == "open_interest")
    btc_second = next(e for e in second if e.instrument == "BTC" and e.metric == "open_interest")
    assert btc_first.identity.value == btc_second.identity.value
    assert btc_first.claim_hash != btc_second.claim_hash
    assert claim_hash(btc_first.identity.slot_payload()) != claim_hash(btc_second.identity.slot_payload())
    assert "interval_seconds" not in btc_second.identity.extras
    assert btc_second.identity.extras["captured_at"] == CAPTURE.isoformat()
    assert btc_second.published_at == CAPTURE
    assert btc_second.ingested_at == CAPTURE
    assert btc_second.as_of_knowledge == btc_second.ingested_at
    assert btc_second.market_time is None
    assert btc_second.published_at.hour == 20 and btc_second.published_at.minute == 32
    off = _build(spot=_spot_payload(), prior=None, captured_at=OFF_WINDOW)
    assert len(off) == 75
    assert off[0].identity.extras["captured_at"] == OFF_WINDOW.isoformat()
    again = _build(spot=_spot_payload(), prior=PRIOR, captured_at=CAPTURE)
    assert [e.claim_hash for e in again] == [e.claim_hash for e in second]


def test_sydney_capture_is_stored_as_utc() -> None:
    sydney = datetime(2026, 9, 25, 6, 32, tzinfo=ZoneInfo("Australia/Sydney"))
    envelopes = _build(spot=_spot_payload(), prior=None, captured_at=sydney)
    assert envelopes[0].identity.extras["captured_at"] == "2026-09-24T20:32:00+00:00"
    assert envelopes[0].as_of_knowledge == envelopes[0].ingested_at


def test_no_quadrant_and_no_backfill_entrypoint() -> None:
    envelopes = _build(spot=_spot_payload())
    assert all(e.metric not in {"quadrant", "quadrant_label", "delta_oi", "delta_price"} for e in envelopes)
    import mm_ingest.mvp_retain as module

    assert module.HISTORY_BACKFILL_WIRED is False
    backfill_names = [name for name in dir(module) if "backfill" in name.lower()]
    assert backfill_names == ["HISTORY_BACKFILL_WIRED"]
    text = Path(module.__file__).read_text(encoding="utf-8")
    assert "history-backfill" not in text
    assert "T20:00:00Z" not in text
    assert "20:30:00" not in text
    assert inspect.signature(build_retain_envelopes).parameters["captured_at"].default is inspect.Parameter.empty
    plan = http_plan(date(2026, 9, 23))
    assert len(plan) == 3
    assert plan[0]["body"] == {"type": "metaAndAssetCtxs"}
    assert plan[1]["path"] == "/v2/aggs/grouped/locale/us/market/stocks/2026-09-23"
    assert plan[2]["body"] == {"type": "spotMetaAndAssetCtxs"}
    blob = json.dumps(plan)
    assert "fundingHistory" not in blob
    assert "candleSnapshot" not in blob


def test_prior_capture_must_be_earlier() -> None:
    with pytest.raises(ValueError, match="strictly earlier"):
        _build(spot=_spot_payload(), prior=CAPTURE, captured_at=CAPTURE)


def test_grouped_daily_is_one_request_and_capture_fetches_spot_meta() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=_grouped("SPX"))

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
    )
    payload, error = adapter.grouped_daily(date(2026, 9, 23))
    assert error == "none"
    assert len(calls) == 1
    assert calls[0].url.path == GROUPED_DAILY_PATH.format(date="2026-09-23")
    assert calls[0].url.params["adjusted"] == "true"
    assert calls[0].url.params["include_otc"] == "false"
    assert len(payload["results"]) == 18

    with pytest.raises(TypeError):
        adapter.grouped_daily(datetime(2026, 9, 23, tzinfo=timezone.utc))

    class _HL:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def meta_and_asset_ctxs(self):
            self.calls.append("metaAndAssetCtxs")
            return _perp_payload("DRV")

        def spot_meta_and_asset_ctxs(self):
            self.calls.append("spotMetaAndAssetCtxs")
            return _spot_payload(mid="1.25")

    hl = _HL()
    envelopes = capture_mvp_retain(
        load_mvp_retain_spec(),
        hl_client=hl,
        polygon_adapter=adapter,
        session_date=date(2026, 9, 23),
        captured_at=CAPTURE,
        prior_captured_at=PRIOR,
    )
    assert hl.calls == ["metaAndAssetCtxs", "spotMetaAndAssetCtxs"]
    assert len(calls) == 2
    drv_rows = [e for e in envelopes if e.instrument == "DRV"]
    assert [e.metric for e in drv_rows] == ["mid_px"]
    assert drv_rows[0].identity.value == "1.25"
    assert drv_rows[0].source_url_or_id == "spotMetaAndAssetCtxs"
    assert drv_rows[0].payload["quadrant_eligible"] is False


def test_missing_polygon_key_does_not_invent_closes() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("missing key must not call Polygon")

    adapter = PolygonEquitiesAdapter(
        env={},
        http_client=httpx.Client(transport=httpx.MockTransport(handler), timeout=2.0),
        sleep=lambda _: None,
    )

    class _HL:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def meta_and_asset_ctxs(self):
            self.calls.append("metaAndAssetCtxs")
            return _perp_payload()

        def spot_meta_and_asset_ctxs(self):
            self.calls.append("spotMetaAndAssetCtxs")
            return _spot_payload(mid=None)

    hl = _HL()
    envelopes = capture_mvp_retain(
        load_mvp_retain_spec(),
        hl_client=hl,
        polygon_adapter=adapter,
        session_date=date(2026, 9, 23),
        captured_at=CAPTURE,
    )
    assert hl.calls == ["metaAndAssetCtxs", "spotMetaAndAssetCtxs"]
    assert adapter.last_error_class == ERROR_MISSING_ENV
    closes = [e for e in envelopes if e.metric == "close"]
    assert len(closes) == 17
    assert all(e.identity.value is None for e in closes)
    assert all(e.data_quality is DataQuality.PARTIAL for e in closes)
    drv = [e for e in envelopes if e.instrument == "DRV"]
    assert [e.metric for e in drv] == ["mid_px"]
    assert drv[0].identity.value is None


def test_persist_delegates_to_existing_pipeline(monkeypatch) -> None:
    seen: dict = {}

    def fake(session, envelopes, **kwargs):
        seen["session"] = session
        seen["n"] = len(envelopes)
        seen["kwargs"] = kwargs
        return {"created": len(envelopes)}

    monkeypatch.setattr("mm_ingest.mvp_retain.persist_envelopes", fake)
    envelopes = _build(spot=_spot_payload(), prior=None)
    assert persist_mvp_retain("sentinel", envelopes, object_store=None) == {"created": 75}
    assert seen == {"session": "sentinel", "n": 75, "kwargs": {"object_store": None}}


def test_cli_retain_is_fixture_only(monkeypatch, tmp_path: Path, capsys) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("session opened")

    monkeypatch.setattr("mm_lab_cli.cli.session_scope", boom)
    monkeypatch.setattr(
        "mm_ingest.mvp_retain.capture_mvp_retain",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("live capture")),
    )
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://lab:lab@127.0.0.1:5432/nope")

    assert main(["retain"]) == 2
    err = capsys.readouterr().err
    assert "DO NOT RUN" in err
    assert "Neon" in err

    path = tmp_path / "capture.json"
    path.write_text(
        json.dumps(
            {
                "captured_at": CAPTURE.isoformat(),
                "prior_captured_at": PRIOR.isoformat(),
                "session_date": "2026-09-23",
                "metaAndAssetCtxs": _perp_payload("KNT", "AAVE"),
                "spotMetaAndAssetCtxs": _spot_payload(),
                "polygon_grouped": _grouped("SPX", "SAMSUN"),
            }
        ),
        encoding="utf-8",
    )
    assert main(["retain", "--fixture", str(path), "--no-db"]) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["instruments"] == 37
    assert body["bound_perps"] == 19
    assert body["price_only"] == 1
    assert body["equities"] == 17
    assert body["envelopes"] == 75
    assert body["calls"] == 3
    assert body["call_plan"][2]["body"] == {"type": "spotMetaAndAssetCtxs"}
    assert body["drv_metrics"] == ["mid_px"]
    assert body["purr_metrics"] == ["open_interest", "funding", "mid_px"]
    assert body["knt_present"] is False
    assert body["venue_queue_present"] is False
    assert body["history_backfill"] is False
    assert body["backfill_wired"] is False
    assert body["sm_slot_window"] is False
    assert body["neon"] is False
    assert body["gated"] is True
    assert body["interval_seconds"] == 86400
    assert body["quadrant_labels"] == 0
    assert body["captured_at"] == CAPTURE.isoformat()
    assert "PURR" in body["symbols"]
    assert "KNT" not in body["symbols"]

    assert main(["retain", "--fixture", str(path)]) == 2
    assert "DO NOT RUN" in capsys.readouterr().err


def test_capture_posts_spot_meta_through_the_info_client() -> None:
    posted: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        posted.append(str(body.get("type")))
        if body.get("type") == "metaAndAssetCtxs":
            return httpx.Response(200, json=_perp_payload("KNT", "DRV"))
        if body.get("type") == "spotMetaAndAssetCtxs":
            return httpx.Response(200, json=_spot_payload(mid="1.25"))
        raise AssertionError(body)

    hl = HyperliquidInfoClient(transport=httpx.MockTransport(handler), sleep=lambda _: None)
    polygon_calls: list[httpx.Request] = []

    def polygon_handler(request: httpx.Request) -> httpx.Response:
        polygon_calls.append(request)
        return httpx.Response(200, json=_grouped("SPX"))

    adapter = PolygonEquitiesAdapter(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(polygon_handler), timeout=2.0),
        sleep=lambda _: None,
    )
    envelopes = capture_mvp_retain(
        load_mvp_retain_spec(),
        hl_client=hl,
        polygon_adapter=adapter,
        session_date=date(2026, 9, 23),
        captured_at=CAPTURE,
    )
    assert posted == ["metaAndAssetCtxs", "spotMetaAndAssetCtxs"]
    assert len(polygon_calls) == 1
    drv = [e for e in envelopes if e.instrument == "DRV"]
    assert [e.metric for e in drv] == ["mid_px"]
    assert drv[0].identity.value == "1.25"
    assert drv[0].payload["hl_type"] == "spotMetaAndAssetCtxs"
    assert "KNT" not in {e.instrument for e in envelopes}


def test_no_cron_or_migrate_workflow_wires_retain() -> None:
    workflows = ROOT / ".github" / "workflows"
    names = [path.name for path in workflows.glob("*.yml")]
    assert "migrate-neon.yml" not in names
    for path in workflows.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "lab retain" not in text
        assert "mvp_retain" not in text
    assert "spotMetaAndAssetCtxs" in ALLOWED_INFO_TYPES
    assert "spotMetaAndAssetCtxs" not in FORBIDDEN_INFO_TYPES
    assert "metaAndAssetCtxs" in ALLOWED_INFO_TYPES
