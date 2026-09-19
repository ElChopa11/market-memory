"""IMP-039: Principal 2026-09-19 candidate intake. QUANT / HYPOTHESIS. No sizing. No scan-gate."""

from __future__ import annotations

from pathlib import Path

import yaml

from mm_desks.queue import load_queue
from mm_research_kit.lifecycle import SKIP_DIR_NAMES, discover_workspaces
from mm_research_kit.quant_review.language import language_violations

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "research" / "candidates"
QUEUE = ROOT / "ops" / "improvement-queue.md"
LIVE = ROOT / "config" / "risk" / "environments" / "live.yaml"
UNIVERSE = ROOT / "config" / "universe.yaml"
MONITOR = ROOT / "config" / "watchlist" / "monitor.yaml"

SEEDED = (
    "C-001-supply-demand-zone",
    "C-002-triple-rsi-mr",
    "C-003-second-entry-pullback",
)

REQUIRED_CLAIM = ("sample", "window", "instrument_set", "cost_model", "split_method", "payoff_shape")
REQUIRED_PARAMS = ("N", "X", "Y", "Z", "M")


def _cards() -> list[tuple[str, dict, str]]:
    out: list[tuple[str, dict, str]] = []
    for slug in SEEDED:
        ypath = CANDIDATES / f"{slug}.yaml"
        mpath = CANDIDATES / f"{slug}.md"
        data = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        text = mpath.read_text(encoding="utf-8")
        out.append((slug, data, text))
    return out


def test_intake_files_and_failures_archive_exist() -> None:
    assert (CANDIDATES / "README.md").is_file()
    assert (CANDIDATES / "schema.yaml").is_file()
    assert (CANDIDATES / "failures" / "README.md").is_file()
    for slug in SEEDED:
        assert (CANDIDATES / f"{slug}.md").is_file(), slug
        assert (CANDIDATES / f"{slug}.yaml").is_file(), slug
    assert (ROOT / "ops" / "plans" / "IMP-039-candidate-strategy-intake.md").is_file()
    assert not (ROOT / "ops" / "plans" / "IMP-034-candidate-strategy-intake.md").is_file()


def test_readme_has_intake_rules_1_through_7() -> None:
    text = (CANDIDATES / "README.md").read_text(encoding="utf-8")
    for n in range(1, 8):
        assert f"{n}." in text, n
    lowered = text.lower()
    assert "owner quant" in lowered or "**owner quant**" in lowered
    assert "hypothesis" in lowered
    assert "no sizing" in lowered
    assert "no scan-gate" in lowered or "no scan-gate promotion" in lowered
    assert "n=unknown" in lowered
    assert "look-ahead" in lowered
    assert "survivorship" in lowered
    failures = (CANDIDATES / "failures" / "README.md").read_text(encoding="utf-8")
    assert "do not delete" in failures.lower()
    assert "do not silently reopen" in failures.lower()


def test_each_card_is_quant_hypothesis_no_size_no_scan() -> None:
    for slug, data, text in _cards():
        assert data["owner"] == "QUANT", slug
        assert data["status"] == "HYPOTHESIS", slug
        assert data["sizing"] is False, slug
        assert data["scan_gate"] is False, slug
        assert data["promote"] is False, slug
        assert data["live"] is False, slug
        assert data["paper_only"] is True, slug
        assert data["intake_date"] == "2026-09-19", slug
        assert "HYPOTHESIS" in text
        assert "QUANT" in text
        assert "DO NOT SIZE" in text
        assert "Scan gate" in text or "scan gate" in text.lower()


def test_claim_restated_or_source_slogan_rejected() -> None:
    for slug, data, text in _cards():
        claim = data["claim"]
        assert claim["restated"] is True, slug
        assert claim["source_slogan_status"] == "REJECT", slug
        for key in REQUIRED_CLAIM:
            assert claim.get(key), f"{slug} missing claim.{key}"
        assert "REJECT" in text
        assert "n=unknown" in text.lower() or "`n=unknown`" in text
        assert "survivorship_uncontrolled" in yaml.safe_dump(data)
        assert data["look_ahead"]["pit_clock"] == "available_at"
        assert data["survivorship"]["tag"] == "survivorship_uncontrolled"
        assert data["provenance"]["class"] == "retail_video_substack_reddit"
        assert data["provenance"]["n"] == "unknown"
        assert data["provenance"]["weight"] == "hypothesis"


def test_params_n_x_y_z_m_atr_locked() -> None:
    for slug, data, _text in _cards():
        params = data["params"]
        for key in REQUIRED_PARAMS:
            assert key in params, f"{slug} missing param {key}"
            assert params[key] is not None
        assert params["atr_period"] == 14
        assert data["study"]["strategy_implemented"] is False
        assert data["study"]["inherit_trade_math_sizing"] is False
        assert data["study"]["bind_thesis"] is False


def test_primary_tape_is_locked_membership_only() -> None:
    universe = yaml.safe_load(UNIVERSE.read_text(encoding="utf-8"))
    in_universe = set(universe["in_universe"]["crypto_perps"]) | set(universe["in_universe"]["equities"])
    for slug, data, _text in _cards():
        primary = {row["symbol"] for row in data["claim"]["instrument_set"]["primary"]}
        assert primary <= in_universe, slug
        assert primary == {"BTC", "NVDA"}, slug
        for row in data["claim"]["instrument_set"]["primary"]:
            assert row["watchlist_tier"] == "universe"


def test_candidates_are_not_thesis_workspaces() -> None:
    assert "candidates" in SKIP_DIR_NAMES
    assert "failures" in SKIP_DIR_NAMES
    found = discover_workspaces(ROOT / "research")
    leaked = [path for path in found if "candidates" in path.parts]
    assert leaked == []


def test_language_gate_no_call_or_size_instruction() -> None:
    blobs = [(CANDIDATES / "README.md").read_text(encoding="utf-8")]
    blobs.append((CANDIDATES / "failures" / "README.md").read_text(encoding="utf-8"))
    for _slug, _data, text in _cards():
        blobs.append(text)
    for text in blobs:
        lowered = text.lower()
        assert "active call" not in lowered
        assert "high confidence" not in lowered
        assert "position size" not in lowered
        assert "go long" not in lowered
        assert "go short" not in lowered
        hits = language_violations(text)
        unexpected = [h for h in hits if h not in {"buy language"}]
        assert unexpected == [], unexpected
        if "buy language" in hits:
            assert "buy_hold" in text


def test_live_and_membership_untouched() -> None:
    live = LIVE.read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    universe = UNIVERSE.read_text(encoding="utf-8")
    assert "in_universe:" in universe
    assert "active_calls:" not in universe
    monitor = MONITOR.read_text(encoding="utf-8")
    assert "C-001" not in monitor
    assert "triple-rsi" not in monitor
    assert "second-entry" not in monitor
    # #60 KRX resolutions stay on main's monitor file.
    assert "KRX:005930" in monitor
    assert "KRX:KQ11" in monitor


def test_queue_preserves_fred_krx_and_parks_candidate_studies() -> None:
    queue = QUEUE.read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-033" in line and "DONE" in line for line in board_lines)
    assert any("#59" in line for line in board_lines if "IMP-033" in line)
    assert any("IMP-034" in line and "DONE" in line for line in board_lines)
    assert any("IMP-022" in line and "DONE" in line for line in board_lines)
    assert any("IMP-024" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-039" in line and "READY" in line for line in board_lines)
    assert not any("IMP-033" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-034" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-039" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-024)" in queue
    assert "KRX:005930" in queue
    assert "licence_verdict" in queue
    assert "ELIGIBLE" in queue
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 3
    report = load_queue(ROOT)
    assert report.ok
    assert report.in_progress == ("IMP-024",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    live = LIVE.read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
