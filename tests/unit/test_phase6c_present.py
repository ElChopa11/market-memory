"""Phase 6c presentation formatter + MarkdownV2 escape property test."""

from __future__ import annotations

from mm_delivery.format import MARKDOWN_V2_SPECIAL, escape_markdown_v2
from mm_delivery.present import (
    UNKNOWN,
    deltas,
    format_notional,
    format_pct,
    format_tick,
    format_z,
    ideas_header,
    monospace_table,
)


def test_escape_property_full_set() -> None:
    special = "".join(sorted(MARKDOWN_V2_SPECIAL))
    escaped = escape_markdown_v2(special)
    for ch in MARKDOWN_V2_SPECIAL:
        assert escaped.count(f"\\{ch}") >= 1
    # Any string of specials is fully escaped; no bare special survives unpaired.
    roundtrip_stripped = escaped.replace("\\", "")
    assert set(roundtrip_stripped) <= MARKDOWN_V2_SPECIAL | set(special)
    assert escape_markdown_v2("plain") == "plain"
    mixed = "A_B*C"
    out = escape_markdown_v2(mixed)
    assert "\\_" in out and "\\*" in out


def test_formatter_units() -> None:
    assert format_pct(0.1234) == "12.34%"
    assert format_pct(None) == UNKNOWN
    assert format_notional(1_200_000) == "$1.2M"
    assert format_notional(3_400_000_000) == "$3.4B"
    assert format_z(1.234) == "1.23"
    assert format_tick(65000.4, tick=0.5).startswith("65000")
    d = deltas(last=12.0, prior=10.0, window_20d=11.0)
    assert d["vs_prior"].startswith("+")
    assert d["vs_20d"].startswith("+")


def test_monospace_unknowns_named_in_gaps() -> None:
    gaps: list[str] = []
    table = monospace_table(("inst", "px"), [("BTC", None)], gaps=gaps)
    assert "```" in table
    assert UNKNOWN in table
    assert "px" in gaps


def test_max_three_ideas_cut_is_stated() -> None:
    assert ideas_header(3, 5) == "3 ideas shown; 2 cut (max 3)"
    assert ideas_header(0, 0) == "no actionable setup"
