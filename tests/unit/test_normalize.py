"""Normalize HL public payloads into envelopes."""

from __future__ import annotations

from datetime import datetime, timezone

from mm_common.enums import DataQuality
from mm_common.hashing import claim_hash
from mm_common.time import from_unix_ms
from mm_provenance.normalize import (
    SNAPSHOT_CAPTURE_KIND,
    normalize_all_mids,
    normalize_asset_snapshot,
    normalize_candles,
    normalize_funding_history,
    normalize_liquidations,
)


T0 = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
T5 = datetime(2026, 9, 10, 0, 5, tzinfo=timezone.utc)


def test_asset_snapshot_emits_btc_eth_metrics(fixture_window: dict) -> None:
    envelopes = normalize_asset_snapshot(
        fixture_window["metaAndAssetCtxs"],
        instruments=["BTC", "ETH"],
        ingested_at=T5,
        published_at=T0,
        stale_after_seconds=120,
    )
    metrics = {(e.instrument, e.metric) for e in envelopes}
    assert ("BTC", "mid_px") in metrics
    assert ("ETH", "open_interest") in metrics
    eth_oi = next(e for e in envelopes if e.instrument == "ETH" and e.metric == "open_interest")
    assert eth_oi.data_quality is DataQuality.PARTIAL
    btc_mid = next(e for e in envelopes if e.instrument == "BTC" and e.metric == "mid_px")
    assert btc_mid.data_quality is DataQuality.STALE
    assert btc_mid.market_time is None
    assert btc_mid.identity.extras.get("capture_kind") == SNAPSHOT_CAPTURE_KIND
    assert btc_mid.payload.get("capture_kind") == SNAPSHOT_CAPTURE_KIND
    assert "lab_capture" in btc_mid.claim_text
    assert btc_mid.as_of_knowledge == T5
    assert btc_mid.published_at == T0


def test_all_mids_numeric_normalization_matches_snapshot(fixture_window: dict) -> None:
    mids = normalize_all_mids(
        fixture_window["allMids"],
        instruments=["BTC", "ETH"],
        ingested_at=T5,
        published_at=T0,
    )
    ctx = normalize_asset_snapshot(
        fixture_window["metaAndAssetCtxs"],
        instruments=["BTC"],
        ingested_at=T5,
        published_at=T0,
    )
    mid_from_all = next(e for e in mids if e.instrument == "BTC")
    mid_from_ctx = next(e for e in ctx if e.instrument == "BTC" and e.metric == "mid_px")
    assert mid_from_all.claim_hash == mid_from_ctx.claim_hash
    assert mid_from_all.market_time is None
    assert mid_from_ctx.market_time is None
    assert mid_from_all.identity.extras == {"capture_kind": SNAPSHOT_CAPTURE_KIND}


def test_duplicate_funding_rows_share_claim_hash(fixture_window: dict) -> None:
    rows = fixture_window["fundingHistory"]["BTC"][:2]
    envelopes = normalize_funding_history(rows, ingested_at=T0)
    assert len(envelopes) == 2
    assert envelopes[0].claim_hash == envelopes[1].claim_hash
    assert claim_hash(envelopes[0].identity.hash_payload()) == envelopes[0].claim_hash
    assert envelopes[0].data_quality is DataQuality.OK
    assert envelopes[0].market_time == from_unix_ms(int(rows[0]["time"]))
    assert envelopes[0].published_at == envelopes[0].market_time
    assert "capture_kind" not in envelopes[0].identity.extras


def test_candles_use_exchange_open_time(fixture_window: dict) -> None:
    rows = fixture_window["candles"]["BTC"][:1]
    envelopes = normalize_candles(rows, ingested_at=T0)
    assert envelopes[0].market_time == from_unix_ms(int(rows[0]["t"]))
    assert envelopes[0].published_at == envelopes[0].market_time


def test_liquidations_ignore_ordinary_trades(fixture_window: dict) -> None:
    envelopes = normalize_liquidations(fixture_window["recentTrades"]["BTC"], ingested_at=T0)
    assert len(envelopes) == 1
    assert envelopes[0].metric == "liquidation"
    assert envelopes[0].instrument == "BTC"
    assert envelopes[0].identity.value == "0.5"
    assert envelopes[0].market_time == from_unix_ms(int(fixture_window["recentTrades"]["BTC"][0]["time"]))
