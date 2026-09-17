"""IMP-005: Principal membership vocabulary is not a Quant/trade call."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# Canonical membership keys must not reintroduce call-language.
FORBIDDEN_KEY_FRAGMENTS = ("active_call", "active-call")
# Templates must not ship recommendation phrasing. Ban-quoting belongs in ops lessons / language.py.
TEMPLATE_FORBIDDEN = (
    re.compile(r"\bactive[-\s_]?calls?\b", re.IGNORECASE),
    re.compile(r"\bhigh\s+confidence\b", re.IGNORECASE),
    re.compile(r"\bbuy\b", re.IGNORECASE),
    re.compile(r"\bsell\b", re.IGNORECASE),
    re.compile(r"\bMAKE\b"),
)


def test_canonical_universe_uses_membership_keys_not_active_calls() -> None:
    path = ROOT / "config" / "universe.yaml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert "in_universe" in data
    assert "watch_only" in data
    assert "active_calls" not in data
    assert "active_call" not in data
    for key in _walk_keys(data):
        lowered = str(key).lower()
        for fragment in FORBIDDEN_KEY_FRAGMENTS:
            assert fragment not in lowered, f"{path} key {key!r} contains {fragment}"
    # Comments may mention the rename; the live key must be in_universe.
    assert re.search(r"^in_universe:", text, re.MULTILINE)
    assert not re.search(r"^active_calls:", text, re.MULTILINE)


def test_membership_ticker_sets_unchanged() -> None:
    universe = yaml.safe_load((ROOT / "config" / "universe.yaml").read_text(encoding="utf-8"))
    assert universe["in_universe"]["crypto_perps"] == ["BTC"]
    assert universe["in_universe"]["equities"] == ["NVDA", "AVGO", "MSFT", "META", "JPM", "XOM"]
    assert universe["watch_only"]["crypto_perps"] == ["ETH", "UNI", "AAVE"]
    assert universe["watch_only"]["equities"] == ["SMH", "XLF"]
    membership = set(universe["crypto_perps"]) | set(universe["equities"])
    in_universe = set(universe["in_universe"]["crypto_perps"]) | set(universe["in_universe"]["equities"])
    watch_only = set(universe["watch_only"]["crypto_perps"]) | set(universe["watch_only"]["equities"])
    assert in_universe | watch_only == membership
    assert in_universe.isdisjoint(watch_only)


def test_templates_have_no_investment_call_language() -> None:
    hits: list[str] = []
    for path in sorted((ROOT / "templates").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for pattern in TEMPLATE_FORBIDDEN:
            if pattern.search(text):
                hits.append(f"{path.relative_to(ROOT)}:{pattern.pattern}")
    assert hits == []


def test_quant_language_gate_still_bans_active_call() -> None:
    from mm_research_kit.quant_review.language import language_violations

    hits = language_violations("promote BTC as an active call")
    assert "active-call language" in hits


def test_post_ipo_screen_config_is_not_membership_and_has_no_active_calls() -> None:
    path = ROOT / "config" / "equities" / "post_ipo_reclaim.yaml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert data["kind"] == "post_ipo_reclaim_screen"
    assert data["status"] == "screen_only"
    assert "active_calls" not in data
    for key in _walk_keys(data):
        lowered = str(key).lower()
        for fragment in FORBIDDEN_KEY_FRAGMENTS:
            assert fragment not in lowered, f"{path} key {key!r} contains {fragment}"
    assert not re.search(r"^active_calls:", text, re.MULTILINE)
    symbols = {str(row["symbol"]).upper() for row in data["instruments"]}
    universe = yaml.safe_load((ROOT / "config" / "universe.yaml").read_text(encoding="utf-8"))
    membership = set(universe["crypto_perps"]) | set(universe["equities"])
    assert symbols.isdisjoint(membership)


def _walk_keys(node: object) -> list[str]:
    keys: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            keys.append(str(key))
            keys.extend(_walk_keys(value))
    elif isinstance(node, list):
        for item in node:
            keys.extend(_walk_keys(item))
    return keys
