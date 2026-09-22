"""Fix 3: HL mid SoR + always-fetch CoinGecko + dual divergence thresholds."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import httpx

from mm_briefing.config import load_briefing_settings
from mm_briefing.engine import generate_preopen
from mm_briefing.fetchers import (
    ASSET_NAMES,
    CRYPTO_PULSE_SOR_NOTE,
    METRIC_CG_VS_HL_ORACLE,
    METRIC_RAW_MID_VS_SPOT,
    SOURCE_DIVERGENCE_CLASS,
    SLOT_SOURCE,
    apply_crypto_pulse_from_hl,
    complete_cross_asset,
    crypto_pulse_max_bps,
    crypto_pulse_source_of_record,
    empty_snapshot,
    live_macro_spec,
    snapshot_from_payload,
    _crypto_divergence_bps,
)
from mm_briefing.hl import hl_from_payload
from mm_briefing.models import HLInstrumentState, HLMetric


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
AS_OF = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
PRIOR = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)
CG_AS_OF = datetime(2026, 3, 10, 11, 59, tzinfo=timezone.utc)

MACRO_CFG = {
    "crypto_pulse": {
        "source_of_record": "hyperliquid",
        "divergence": {"max_bps": 100, "max_bps_raw_mid_vs_spot": 300},
    }
}


def _hl_state(
    instrument: str,
    *,
    mid: float | None,
    oracle: float | None = None,
) -> HLInstrumentState:
    metrics: dict[str, HLMetric] = {}
    if mid is not None:
        metrics["mid_px"] = HLMetric(
            instrument=instrument,
            metric="mid_px",
            value=str(mid),
            observation_id=f"OBS-{instrument}-MID",
            claim_hash=None,
            data_quality="ok",
            as_of_knowledge=AS_OF,
            source_url="https://api.hyperliquid.xyz/info type=metaAndAssetCtxs",
        )
    if oracle is not None:
        metrics["oracle_px"] = HLMetric(
            instrument=instrument,
            metric="oracle_px",
            value=str(oracle),
            observation_id=f"OBS-{instrument}-ORACLE",
            claim_hash=None,
            data_quality="ok",
            as_of_knowledge=AS_OF,
            source_url="https://api.hyperliquid.xyz/info type=metaAndAssetCtxs",
        )
    return HLInstrumentState(
        instrument=instrument,
        metrics=metrics,
        liquidations=(),
        levels=(),
        data_quality="ok" if mid is not None else "unavailable",
        as_of_knowledge=AS_OF,
        source="hyperliquid.info /info",
    )


def _hl(
    *,
    btc_mid: float | None = 85995.0,
    btc_oracle: float | None = 85945.0,
    eth_mid: float | None = 3200.0,
    eth_oracle: float | None = 3198.0,
) -> tuple[HLInstrumentState, ...]:
    return (
        _hl_state("BTC", mid=btc_mid, oracle=btc_oracle),
        _hl_state("ETH", mid=eth_mid, oracle=eth_oracle),
    )


def test_slot_source_crypto_is_hyperliquid() -> None:
    assert SLOT_SOURCE["BTC"] == "hyperliquid"
    assert SLOT_SOURCE["ETH"] == "hyperliquid"
    assert SLOT_SOURCE["ES"] == "polygon"
    assert "not CoinGecko spot" in ASSET_NAMES["BTC"]


def test_config_dual_thresholds() -> None:
    settings = load_briefing_settings(ROOT)
    assert crypto_pulse_source_of_record(settings.macro) == "hyperliquid"
    div = settings.macro["crypto_pulse"]["divergence"]
    assert div["max_bps"] == 100
    assert div["max_bps_raw_mid_vs_spot"] == 300
    assert crypto_pulse_max_bps(settings.macro, "BTC", path="oracle") == 100.0
    assert crypto_pulse_max_bps(settings.macro, "BTC", path="raw") == 300.0


def test_live_macro_spec_always_enables_coingecko() -> None:
    settings = load_briefing_settings(ROOT)
    spec = live_macro_spec(settings.macro)
    assert spec["live"]["coingecko"]["enabled"] is True
    assert spec["live"]["polygon"]["enabled"] is True


def test_empty_crypto_slots_label_hyperliquid() -> None:
    snap = complete_cross_asset(empty_snapshot(AS_OF, PRIOR, reason="off", source="off"))
    assert snap.by_symbol()["BTC"].source == "hyperliquid"
    assert snap.by_symbol()["ETH"].source == "hyperliquid"


def test_never_strips_coingecko_unavailable_notes() -> None:
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "source": "live",
                "notes": ["coingecko unavailable (error_class=rate_limited); no prices invented"],
                "assets": [
                    {
                        "symbol": "BTC",
                        "last": None,
                        "data_quality": "unavailable",
                        "source": "coingecko",
                    }
                ],
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(macro, _hl(), macro_config=MACRO_CFG)
    assert filled.by_symbol()["BTC"].last == 85995.0
    assert any("coingecko unavailable" in note.lower() for note in filled.notes)
    assert any("divergence not computed (coingecko 429)" in note for note in filled.notes)
    assert CRYPTO_PULSE_SOR_NOTE in filled.notes


def test_cg_429_gap_line_when_hl_sor_prints() -> None:
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "source": "live",
                "notes": ["coingecko unavailable (error_class=rate_limited); no prices invented"],
                "assets": [],
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(macro, _hl(), macro_config=MACRO_CFG)
    blob = "\n".join(filled.notes)
    assert "BTC divergence not computed (coingecko 429)" in blob
    assert "ETH divergence not computed (coingecko 429)" in blob
    assert "coingecko unavailable" in blob.lower()
    assert filled.by_symbol()["BTC"].last == 85995.0


def test_cg_timeout_gap_uses_error_class_not_silent() -> None:
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "notes": ["coingecko unavailable (error_class=timeout); no prices invented"],
                "assets": [],
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(macro, _hl(), macro_config=MACRO_CFG)
    assert any("divergence not computed (coingecko timeout)" in note for note in filled.notes)

def test_normal_path_oracle_metric_below_100bps() -> None:
    cg_spot = 85945.0 + 50.0  # ~5.8 bps vs oracle
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "assets": [
                    {
                        "symbol": "BTC",
                        "last": cg_spot,
                        "data_quality": "ok",
                        "source": "coingecko",
                        "as_of": CG_AS_OF.isoformat(),
                    }
                ]
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(
        macro,
        _hl(btc_mid=85995.0, btc_oracle=85945.0),
        macro_config=MACRO_CFG,
    )
    assert filled.by_symbol()["BTC"].last == 85995.0
    assert filled.by_symbol()["BTC"].data_quality == "ok"
    blob = " ".join(filled.notes)
    assert "BTC compare:" in blob
    assert f"metric={METRIC_CG_VS_HL_ORACLE}" in blob
    assert "source=coingecko" in blob
    assert SOURCE_DIVERGENCE_CLASS not in blob


def test_oracle_path_escalates_at_100bps() -> None:
    cg_spot = 85945.0 * 1.02  # ~200 bps vs oracle
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "assets": [
                    {
                        "symbol": "BTC",
                        "last": cg_spot,
                        "data_quality": "ok",
                        "source": "coingecko",
                        "as_of": CG_AS_OF.isoformat(),
                    }
                ]
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(
        macro,
        _hl(btc_mid=85995.0, btc_oracle=85945.0),
        macro_config=MACRO_CFG,
    )
    btc = filled.by_symbol()["BTC"]
    assert btc.last == 85995.0
    assert btc.data_quality == "partial"
    blob = " ".join(filled.notes)
    assert f"error_class={SOURCE_DIVERGENCE_CLASS}" in blob
    assert f"metric={METRIC_CG_VS_HL_ORACLE}" in blob
    assert "max_bps=100" in blob


def test_raw_mid_below_300bps_no_escalate() -> None:
    # ~200 bps vs mid — above oracle 100 but below raw 300; oracle missing.
    cg_spot = 85995.0 * 1.02
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "assets": [
                    {
                        "symbol": "BTC",
                        "last": cg_spot,
                        "data_quality": "ok",
                        "source": "coingecko",
                        "as_of": CG_AS_OF.isoformat(),
                    }
                ]
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(
        macro,
        _hl(btc_mid=85995.0, btc_oracle=None),
        macro_config=MACRO_CFG,
    )
    assert filled.by_symbol()["BTC"].data_quality == "ok"
    blob = " ".join(filled.notes)
    assert f"metric={METRIC_RAW_MID_VS_SPOT}" in blob
    assert "confidence=low" in blob
    assert "basis not subtracted" in blob
    assert SOURCE_DIVERGENCE_CLASS not in blob
    assert "threshold=300bps" in blob


def test_raw_mid_escalates_at_300bps_with_low_confidence() -> None:
    cg_spot = 85995.0 * 1.04  # ~400 bps vs mid
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "assets": [
                    {
                        "symbol": "BTC",
                        "last": cg_spot,
                        "data_quality": "ok",
                        "source": "coingecko",
                        "as_of": CG_AS_OF.isoformat(),
                    }
                ]
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    filled = apply_crypto_pulse_from_hl(
        macro,
        _hl(btc_mid=85995.0, btc_oracle=None),
        macro_config=MACRO_CFG,
    )
    assert filled.by_symbol()["BTC"].data_quality == "partial"
    blob = " ".join(filled.notes)
    assert f"error_class={SOURCE_DIVERGENCE_CLASS}" in blob
    assert f"metric={METRIC_RAW_MID_VS_SPOT}" in blob
    assert "confidence=low" in blob
    assert "basis not subtracted" in blob
    assert "max_bps=300" in blob


def test_oracle_preferred_divergence_math() -> None:
    bps, mode, ref = _crypto_divergence_bps(86000.0, hl_mid=85995.0, hl_oracle=85945.0)
    assert mode == "oracle_adjusted"
    assert ref == 85945.0
    assert bps is not None
    bps2, mode2, _ = _crypto_divergence_bps(86000.0, hl_mid=85995.0, hl_oracle=None)
    assert mode2 == "raw_mid_vs_spot"


def test_fixture_crypto_rows_are_not_overwritten() -> None:
    import json

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    macro = snapshot_from_payload(
        fixture["macro"],
        as_of=AS_OF,
        prior_us_close=PRIOR,
        source="fixture",
    )
    hl = hl_from_payload(fixture["hyperliquid"])
    filled = apply_crypto_pulse_from_hl(complete_cross_asset(macro), hl, macro_config=MACRO_CFG)
    btc = filled.by_symbol()["BTC"]
    assert btc.source == "fixture"
    assert btc.last == 65500.0
    assert CRYPTO_PULSE_SOR_NOTE not in filled.notes


def test_preopen_keeps_cg_unavailable_and_hl_mid() -> None:
    settings = load_briefing_settings(ROOT)
    macro = complete_cross_asset(
        snapshot_from_payload(
            {
                "source": "live",
                "notes": ["coingecko unavailable (error_class=rate_limited); no prices invented"],
                "assets": [
                    {
                        "symbol": "ES",
                        "last": 5750.0,
                        "prior_close": 5720.0,
                        "data_quality": "ok",
                        "source": "polygon",
                    },
                    {
                        "symbol": "BTC",
                        "last": None,
                        "data_quality": "unavailable",
                        "source": "coingecko",
                    },
                ],
            },
            as_of=AS_OF,
            prior_us_close=PRIOR,
            source="live",
        )
    )
    doc = generate_preopen(
        as_of=AS_OF,
        settings=settings,
        macro=macro,
        hl=_hl(),
        generated_at=AS_OF,
        hl_origin="hyperliquid.info /info",
    )
    assert "85995" in doc.markdown
    assert "crypto pulse SoR=hyperliquid" in doc.markdown
    assert "coingecko unavailable" in doc.markdown.lower()


def test_live_fetcher_always_fetches_coingecko() -> None:
    from mm_briefing.fetchers import LiveMacroFetcher

    calls = {"cg": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "coingecko" in str(request.url):
            calls["cg"] += 1
            return httpx.Response(
                200,
                json={
                    "bitcoin": {"usd": 86000.0, "usd_24h_change": 1.0},
                    "ethereum": {"usd": 3200.0, "usd_24h_change": -1.0},
                },
            )
        return httpx.Response(404)

    settings = load_briefing_settings(ROOT)
    spec = live_macro_spec(settings.macro)
    spec["live"]["stooq"]["enabled"] = False
    spec["live"]["fred"]["enabled"] = False
    spec["live"]["polygon"]["enabled"] = False
    client = httpx.Client(transport=httpx.MockTransport(handler))
    snap = LiveMacroFetcher(spec, client=client, sleep=lambda _: None).fetch(AS_OF, prior_us_close=PRIOR)
    assert calls["cg"] == 1
    assert snap.by_symbol()["BTC"].source == "coingecko"
    filled = apply_crypto_pulse_from_hl(complete_cross_asset(snap), _hl(), macro_config=MACRO_CFG)
    assert filled.by_symbol()["BTC"].last == 85995.0
    assert "86000" in " ".join(filled.notes)
