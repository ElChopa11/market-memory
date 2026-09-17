"""Live ingest must not treat the operator window clock as exchange event time."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from mm_ingest.pipeline import IngestStats, ingest_from_client
from mm_provenance.normalize import SNAPSHOT_CAPTURE_KIND


class _FakeInfoClient:
    def all_mids(self) -> dict[str, str]:
        return {"BTC": "65000.0"}

    def meta_and_asset_ctxs(self) -> list[object]:
        return [
            {"universe": [{"name": "BTC"}]},
            [
                {
                    "midPx": "65000.0",
                    "markPx": "65010.0",
                    "oraclePx": "64990.0",
                    "funding": "0.0001",
                    "openInterest": "1000.5",
                }
            ],
        ]

    def iter_funding_history(self, coin: str, start_ms: int, end_ms: int) -> list[dict]:
        return [
            {"coin": coin, "fundingRate": "0.0001", "time": 1788912000000},
        ]

    def iter_candles(self, coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict]:
        return [{"s": coin, "t": 1788912000000, "c": "64000.0", "i": interval}]

    def recent_trades(self, coin: str) -> list[dict]:
        return [
            {
                "coin": coin,
                "sz": "0.5",
                "time": 1788955200000,
                "tid": 1,
                "liquidation": {"markPx": "60010.0"},
            }
        ]


def test_live_snapshot_does_not_use_window_end_as_market_time(monkeypatch) -> None:
    captured: dict[str, list] = {}

    def _capture(session, envelopes, *, object_store=None, raw_payloads=None):
        captured["envelopes"] = envelopes
        return IngestStats(envelopes=len(envelopes), object_store="null")

    monkeypatch.setattr("mm_ingest.pipeline.persist_envelopes", _capture)
    window_end = datetime(2026, 9, 10, 0, 0, tzinfo=timezone.utc)
    window_start = datetime(2026, 9, 3, 0, 0, tzinfo=timezone.utc)
    ingest_from_client(
        SimpleNamespace(),
        _FakeInfoClient(),
        instruments=["BTC"],
        start=window_start,
        end=window_end,
        object_store=None,
    )
    envelopes = captured["envelopes"]
    snapshots = [e for e in envelopes if e.payload.get("capture_kind") == SNAPSHOT_CAPTURE_KIND]
    historical = [e for e in envelopes if e.payload.get("capture_kind") != SNAPSHOT_CAPTURE_KIND]
    assert snapshots
    assert historical
    assert all(e.market_time is None for e in snapshots)
    assert all(e.published_at != window_end for e in snapshots)
    assert all(e.identity.extras.get("capture_kind") == SNAPSHOT_CAPTURE_KIND for e in snapshots)
    assert all(e.as_of_knowledge == e.ingested_at for e in snapshots)
    assert all(e.market_time is not None for e in historical)
    assert all(e.market_time != window_end for e in historical)
