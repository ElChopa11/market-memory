"""Adversarial: intentional look-ahead fixtures must be caught."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mm_backtest.errors import FixtureLookAheadError
from mm_backtest.leakage import has_lookahead, scan_fixture_for_lookahead
from mm_backtest.loaders import load_fixture_file, load_fixture_payload

ROOT = Path(__file__).resolve().parents[2]
LOOKAHEAD = ROOT / "tests" / "fixtures" / "backtest" / "lookahead_bars.json"
CLEAN = ROOT / "tests" / "fixtures" / "backtest" / "clean_bars.json"


def test_scan_flags_intentional_lookahead_fixture() -> None:
    payload = json.loads(LOOKAHEAD.read_text(encoding="utf-8"))
    findings = scan_fixture_for_lookahead(payload)
    messages = " ".join(item.message for item in findings)
    assert findings
    assert has_lookahead(payload)
    assert "future_close" in messages
    assert "next_return" in messages
    assert "available_at" in messages
    assert "before" in messages


def test_load_refuses_lookahead_fixture_by_default() -> None:
    with pytest.raises(FixtureLookAheadError, match="look-ahead"):
        load_fixture_file(LOOKAHEAD)


def test_clean_fixture_has_no_lookahead() -> None:
    payload = json.loads(CLEAN.read_text(encoding="utf-8"))
    assert scan_fixture_for_lookahead(payload) == []
    bars, _facts, meta = load_fixture_payload(payload, strict=True)
    assert len(bars) == 6
    assert meta["lookahead_findings"] == []


def test_strict_false_still_reports_findings() -> None:
    payload = json.loads(LOOKAHEAD.read_text(encoding="utf-8"))
    _bars, _facts, meta = load_fixture_payload(payload, strict=False)
    assert meta["lookahead_findings"]
