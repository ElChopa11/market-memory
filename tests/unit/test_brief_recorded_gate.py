"""Approval-gate render from recorded Sydney-morning Actions briefs.

Two consecutive deliveries (runs 35967088240 then 36071921289). The earlier
pair (35931476917 then 35967088240) is the FRED date that did not roll.
Numbers come from tests/fixtures/briefing/recorded_sydney_morning_20260924.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mm_briefing.models import AssetPrint, HLInstrumentState, HLMetric, MacroSnapshot
from mm_briefing.morning import _change_cell, render_morning_close
from mm_briefing.prior import MapPriorCaptureReader, PriorCaptureValue
from mm_briefing.render import render_close_legacy
from mm_delivery.config import load_telegram_settings
from mm_delivery.format import TELEGRAM_MAX_MESSAGE_CHARS, chunk_markdown_v2

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "recorded_sydney_morning_20260924.json"
TEMPLATE = ROOT / "ops" / "reports" / "renders" / "brief-template-dryrun.txt"
CURRENT = ROOT / "ops" / "reports" / "renders" / "brief-current-dryrun.txt"
UTC = timezone.utc


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _load() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _prints(rows: list[dict]) -> tuple[AssetPrint, ...]:
    out: list[AssetPrint] = []
    for row in rows:
        last = row["last"]
        prior = row["prior_close"]
        out.append(
            AssetPrint(
                symbol=row["symbol"],
                name=row["name"],
                last=None if last is None else float(last),
                prior_close=None if prior is None else float(prior),
                unit=row["unit"],
                data_quality=row["data_quality"],
                source=row["source"],
                as_of=_dt(row["as_of"]),
                quoted_symbol=row.get("quoted_symbol"),
                structural_unavailable=bool(row.get("structural_unavailable")),
            )
        )
    return tuple(out)


def _hl(name: str, spec: dict, *, as_of: datetime) -> HLInstrumentState:
    metrics: dict[str, HLMetric] = {}
    for metric, value in (
        ("funding", spec["funding"]),
        ("open_interest", spec["open_interest"]),
        ("mid_px", spec["mid_px"]),
        # The artifact stored basis (mark − oracle), not the two legs.
        ("mark_px", "0"),
        ("oracle_px", str(-float(spec["basis"]))),
    ):
        metrics[metric] = HLMetric(
            instrument=name,
            metric=metric,
            value=value,
            observation_id=None,
            claim_hash=None,
            data_quality="fresh",
            as_of_knowledge=as_of,
        )
    return HLInstrumentState(
        instrument=name,
        metrics=metrics,
        liquidations=(),
        levels=(),
        data_quality="fresh",
        as_of_knowledge=as_of,
        source="hyperliquid.info /info",
    )


def _prior_reader(payload: dict) -> MapPriorCaptureReader:
    prior = payload["gate_prior"]
    captured = _dt(prior["generated_at"])
    values: dict[tuple[str, str], PriorCaptureValue] = {}
    for symbol, spec in prior["closes"].items():
        values[(symbol, "close")] = PriorCaptureValue(
            instrument=symbol,
            metric="close",
            value=float(spec["value"]),
            captured_at=captured,
            prior_captured_at=captured,
            observation_as_of=_dt(spec["observation_as_of"]),
        )
    for name, spec in prior["hl"].items():
        for metric in ("funding", "open_interest", "basis"):
            values[(name, metric)] = PriorCaptureValue(
                instrument=name,
                metric=metric,
                value=float(spec[metric]),
                captured_at=captured,
                prior_captured_at=captured,
            )
    return MapPriorCaptureReader(values)


def gate_markdown(payload: dict | None = None) -> str:
    payload = payload or _load()
    current = payload["gate_current"]
    prior = payload["gate_prior"]
    fred = payload["fred_pair"]
    generated = _dt(current["generated_at"])
    as_of = _dt(current["as_of_knowledge"])
    session = MacroSnapshot(
        as_of=as_of,
        prior_us_close=_dt(prior["generated_at"]),
        assets=_prints(current["rows"]),
        data_quality="unavailable",
        source="recorded",
    )
    hl = tuple(
        _hl(name, spec, as_of=generated)
        for name, spec in current["hl"].items()
    )
    us10y = fred["us10y"]
    fred_row = AssetPrint(
        symbol="US10Y",
        name="US 10Y yield",
        last=float(us10y["last"]),
        prior_close=float(us10y["prior_close"]),
        unit="%",
        data_quality="fresh",
        source="fred",
        as_of=_dt(us10y["as_of"]),
    )
    fred_prior = MapPriorCaptureReader(
        {
            ("US10Y", "close"): PriorCaptureValue(
                instrument="US10Y",
                metric="close",
                value=float(us10y["last"]),
                captured_at=_dt(fred["prior_generated_at"]),
                prior_captured_at=_dt(fred["prior_generated_at"]),
                observation_as_of=_dt(us10y["prior_observation_as_of"]),
            )
        }
    )
    fred_cell = _change_cell(fred_row, fred_prior)
    closing = (
        (
            "Recorded earlier pair, not this session: "
            f"{fred['prior_generated_at']} → {fred['current_generated_at']}. "
            "FRED observation date did not roll."
        ),
        f"{'US10Y':<6} {float(us10y['last']):>10.2f}  {fred_cell}",
    )
    doc = render_morning_close(
        generated_at=generated,
        as_of=as_of,
        overnight=session,
        session=session,
        calendar=(),
        unexpected=(),
        theses=(),
        assumptions=(),
        hl=hl,
        data_quality="unavailable",
        prior_reader=_prior_reader(payload),
        lead_lines=(
            f"Sessions: {prior['generated_at']} → {current['generated_at']}",
            "RECORDED DATA, --no-send",
            "Missing: VIX — no recorded value. Cboe entitlement; structurally unavailable on the Polygon stocks plan.",
        ),
        closing_lines=closing,
    )
    return doc.markdown


def gate_telegram(payload: dict | None = None) -> str:
    chunks = chunk_markdown_v2(gate_markdown(payload))
    assert len(chunks) == 1
    return chunks[0]


def legacy_markdown(payload: dict | None = None) -> str:
    payload = payload or _load()
    current = payload["gate_current"]
    prior = payload["gate_prior"]
    generated = _dt(current["generated_at"])
    as_of = _dt(current["as_of_knowledge"])
    session = MacroSnapshot(
        as_of=as_of,
        prior_us_close=_dt(prior["generated_at"]),
        assets=_prints(current["rows"]),
        data_quality="unavailable",
        source="recorded",
    )
    hl = tuple(_hl(name, spec, as_of=generated) for name, spec in current["hl"].items())
    return render_close_legacy(
        generated_at=generated,
        as_of=as_of,
        overnight=session,
        session=session,
        calendar=(),
        unexpected=(),
        theses=(),
        assumptions=("No named macro assumption flipped vs the overnight tape",),
        hl=hl,
        data_quality="unavailable",
    ).markdown


def test_recorded_gate_matches_committed_telegram_bytes() -> None:
    payload = _load()
    settings = load_telegram_settings(ROOT)
    text = gate_telegram(payload)
    assert settings.parse_mode == "MarkdownV2"
    assert payload["parse_mode"] == "MarkdownV2"
    assert text == TEMPLATE.read_text(encoding="utf-8")
    assert text.startswith("```\n")
    assert text.rstrip().endswith("```")
    assert len(text) <= TELEGRAM_MAX_MESSAGE_CHARS
    assert len(text.splitlines()) < 80
    assert "RECORDED DATA, --no-send" in text
    assert "Sessions: 2026-09-24T06:58:31+00:00 → 2026-09-24T23:17:25+00:00" in text
    assert "no new session since 2026-09-23" in text
    assert "no new print since 2026-09-22" in text
    assert "+15.0bp" in text
    assert "767.81" in text
    assert "84314.50" in text
    assert "11.39% ann" in text
    assert "0.000013" not in text
    assert "As-of knowledge" not in text
    assert "| Symbol |" not in text
    assert "Missing: VIX" in text
    assert "SPY ETF" not in text
    assert CURRENT.read_text(encoding="utf-8") == legacy_markdown(payload)
    assert "Overnight reference" in CURRENT.read_text(encoding="utf-8")
