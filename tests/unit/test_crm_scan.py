"""Chart's watchlist CRM scan in the Sydney morning brief.

Gates: words, sigma and percent only (no entry / stop / target / R:R / level),
the brief never blocks on the scan, ``None`` leaves the body byte-for-byte,
forming-bar UNREAD and the track-record caveat always render, and every line
fits the 42-character phone fence.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mm_briefing.config import load_briefing_settings
from mm_briefing.crm_scan import (
    COMPACT_MAX_LINES,
    PHONE_LINE_MAX,
    UNAVAILABLE,
    CrmScanError,
    CrmUnavailable,
    apply_crm_scan,
    crm_section_lines,
    level_free,
    load_crm_scan,
    parse_crm_scan,
)
from mm_briefing.engine import generate_from_fixture, load_fixture_file
from mm_briefing.morning import PHONE_LINE_MAX as MORNING_PHONE_LINE_MAX

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "tests" / "fixtures" / "briefing" / "crm_scan_20261009.json"
CLOSE_FIXTURE = ROOT / "tests" / "fixtures" / "briefing" / "frozen_day.json"
# 06:30 AEDT Fri 9 Oct 2026. The scan is stamped 01:35 AEDT the same morning.
GENERATED = datetime(2026, 10, 8, 19, 30, tzinfo=timezone.utc)

EXPECTED_COMPACT = [
    "CRM 1W, DV=deep value (Chart 01:35 AEDT)",
    "DOGE* 42 Neutral -0.81σ 11.2% to DV",
    "XRP* 37 Neutral -0.45σ 13.2% to DV",
    "ETH 66 Neutral +0.29σ 17.4% to DV",
    "BTC 46 Neutral +0.43σ 20.2% to DV",
    "Stretched: QNT-P 73 Elevated, BP +4.78σ",
    "*below realized. Forming bars UNREAD.",
    "Not backtested. Not a trade instruction.",
]


def _raw() -> dict:
    return json.loads(SCAN.read_text(encoding="utf-8"))


def _scan(raw: dict | None = None):
    return parse_crm_scan(raw if raw is not None else _raw())


def _fence(lines: list[str]) -> str:
    return "```\n" + "\n".join(lines) + "\n```\n"


def test_phone_width_in_lockstep_with_morning() -> None:
    assert PHONE_LINE_MAX == MORNING_PHONE_LINE_MAX


def test_compact_section_matches_mockup() -> None:
    lines = crm_section_lines(_scan(), generated_at=GENERATED)
    assert lines == EXPECTED_COMPACT
    assert len(lines) <= COMPACT_MAX_LINES
    assert all(len(line) <= PHONE_LINE_MAX for line in lines)


def test_full_section_fits_and_keeps_caveats() -> None:
    lines = crm_section_lines(_scan(), generated_at=GENERATED, compact=False)
    assert all(len(line) <= PHONE_LINE_MAX for line in lines)
    text = " ".join(lines)
    assert "UNREAD" in text
    assert "not a backtest" in text
    assert "not a trade" in text
    assert all(level_free(line) for line in lines)


@pytest.mark.parametrize("compact", [True, False])
def test_forming_bar_and_track_record_caveat_always_render(compact: bool) -> None:
    raw = _raw()
    for row in raw["nearest"]:
        row["below_realized"] = False
    text = "\n".join(crm_section_lines(_scan(raw), generated_at=GENERATED, compact=compact))
    assert "UNREAD" in text
    assert "backtest" in text.lower()


def test_none_leaves_markdown_byte_for_byte() -> None:
    body = _fence(["US Close 2026-10-08", "", "BTC 62000.00 +1.00%"])
    assert apply_crm_scan(body, None, generated_at=GENERATED) is body


def test_section_is_last_block_inside_the_fence() -> None:
    body = _fence(["US Close 2026-10-08", "", "Catalysts", "", "- x"])
    out = apply_crm_scan(body, _scan(), generated_at=GENERATED)
    assert out.startswith("```\n") and out.endswith("\n```\n")
    inner = out[len("```\n") : -len("\n```\n")].split("\n")
    assert inner[-len(EXPECTED_COMPACT) :] == EXPECTED_COMPACT
    assert inner[-len(EXPECTED_COMPACT) - 1] == ""


def test_missing_file_is_one_unavailable_line(tmp_path: Path) -> None:
    scan = load_crm_scan(tmp_path / "absent.json")
    assert isinstance(scan, CrmUnavailable)
    assert crm_section_lines(scan, generated_at=GENERATED) == [f"{UNAVAILABLE} (missing)"]


def test_malformed_file_is_unavailable(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert crm_section_lines(load_crm_scan(path), generated_at=GENERATED) == [f"{UNAVAILABLE} (malformed)"]


def test_stale_scan_is_unavailable() -> None:
    late = GENERATED + timedelta(hours=12, minutes=1) + (GENERATED - _scan().captured_at)
    assert crm_section_lines(_scan(), generated_at=late) == [f"{UNAVAILABLE} (stale)"]


def test_future_stamp_is_unavailable() -> None:
    early = _scan().captured_at - timedelta(hours=1)
    assert crm_section_lines(_scan(), generated_at=early) == [f"{UNAVAILABLE} (future stamp)"]


def test_forming_bar_must_be_unread() -> None:
    raw = _raw()
    raw["forming_bar"] = "READ"
    with pytest.raises(CrmScanError):
        _scan(raw)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["nearest"][0].__setitem__("label", "Entry 0.21"),
        lambda r: r["nearest"][0].__setitem__("label", "stop zone"),
        lambda r: r["nearest"][0].__setitem__("label", "$ zone"),
        lambda r: r["nearest"][0].__setitem__("cr", 62000),
        lambda r: r["nearest"][0].__setitem__("cr", 42.5),
        lambda r: r["nearest"][0].__setitem__("target", 0.31),
        lambda r: r["nearest"][0].__setitem__("symbol", "DOGE 0.21"),
        lambda r: r["stretched"][0].__setitem__("note", "R:R 3"),
        lambda r: r["stretched"][0].__setitem__("note", "Long Position"),
        lambda r: r["warming"][0].__setitem__("sigma", float("nan")),
    ],
)
def test_level_shaped_input_degrades_to_unavailable(tmp_path: Path, mutate) -> None:
    raw = copy.deepcopy(_raw())
    mutate(raw)
    path = tmp_path / "scan.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    lines = crm_section_lines(load_crm_scan(path), generated_at=GENERATED)
    assert len(lines) == 1 and lines[0].startswith(UNAVAILABLE)


@pytest.mark.parametrize(
    "line, ok",
    [
        ("DOGE* 42 Neutral -0.81σ 11.2% to DV", True),
        (" BUY->26w n6 +32% 50% hit", True),
        ("CRM 1W, DV=deep value (Chart 01:35 AEDT)", True),
        ("BTC 62000.5", False),
        ("ETH 3000", False),
        ("SOL $150", False),
        ("XRP 0.52", False),
        ("XRP entry zone", False),
        ("BTC stop below", False),
        ("ETH target +5%", False),
        ("R:R 3", False),
        ("paper band", False),
        ("Long position", False),
        ("DOGE levels", False),
    ],
)
def test_level_free_guard(line: str, ok: bool) -> None:
    assert level_free(line) is ok


def test_close_brief_unchanged_without_scan_and_never_blocked() -> None:
    settings = load_briefing_settings(ROOT)
    fixture = load_fixture_file(CLOSE_FIXTURE)
    base, _ = generate_from_fixture("close", fixture, settings=settings, generated_at=GENERATED)
    same, _ = generate_from_fixture(
        "close", fixture, settings=settings, generated_at=GENERATED, crm_scan=None
    )
    assert base is not None and same is not None
    assert same.markdown == base.markdown
    assert same.content_hash == base.content_hash

    with_scan, _ = generate_from_fixture(
        "close", fixture, settings=settings, generated_at=GENERATED, crm_scan=_scan()
    )
    assert with_scan is not None
    assert with_scan.markdown.startswith(base.markdown.rstrip("`\n").rstrip())
    for line in EXPECTED_COMPACT:
        assert line in with_scan.markdown
    assert with_scan.content_hash != base.content_hash

    missing, _ = generate_from_fixture(
        "close",
        fixture,
        settings=settings,
        generated_at=GENERATED,
        crm_scan=CrmUnavailable("missing"),
    )
    assert missing is not None
    assert f"{UNAVAILABLE} (missing)" in missing.markdown
    fence = missing.markdown.split("```\n", 1)[1].rsplit("\n```", 1)[0]
    assert all(len(line) <= PHONE_LINE_MAX for line in fence.split("\n"))
