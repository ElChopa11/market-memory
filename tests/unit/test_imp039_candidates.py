"""IMP-039: Principal 2026-09-19 candidate intake. QUANT / HYPOTHESIS. No sizing. No scan-gate."""

from __future__ import annotations

import re
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
# Dated C-00x / signal-correlation write-ups are strategy compute. Methodology
# folders (trend-permission-filter/, and similar) may exist while cards stay INTAKE_ONLY.
_CANDIDATE_COMPUTE_STUDY_RE = re.compile(
    r"(?:^|/)(?:C-00[123](?:[-/.]|$)|signal-correlation(?:/|$))"
)


def _looks_like_candidate_compute_study(path: Path, studies_root: Path) -> bool:
    rel = path.relative_to(studies_root).as_posix()
    return _CANDIDATE_COMPUTE_STUDY_RE.search(rel) is not None


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


def test_readme_has_intake_rules_1_through_12() -> None:
    text = (CANDIDATES / "README.md").read_text(encoding="utf-8")
    for n in range(1, 13):
        assert f"{n}." in text, n
    lowered = text.lower()
    assert "owner quant" in lowered or "**owner quant**" in lowered
    assert "hypothesis" in lowered
    assert "no sizing" in lowered
    assert "no scan-gate" in lowered or "no scan-gate promotion" in lowered
    assert "n=unknown" in lowered
    assert "look-ahead" in lowered
    assert "survivorship" in lowered
    assert "cross-candidate correlation" in lowered
    assert "order of work" in lowered
    assert "parameters declared before" in lowered or "params before first run" in lowered or "declared before the first run" in lowered
    assert "what passing means" in lowered
    assert "stop condition" in lowered
    assert "intake_only" in lowered
    assert "paper-eligible" in lowered
    assert "nothing computed" in lowered
    assert "## deliverable" in lowered
    assert "## acceptance" in lowered
    failures = (CANDIDATES / "failures" / "README.md").read_text(encoding="utf-8")
    assert "do not delete" in failures.lower()
    assert "do not silently reopen" in failures.lower()


def test_each_card_is_quant_hypothesis_no_size_no_scan() -> None:
    for slug, data, text in _cards():
        assert data["owner"] == "QUANT", slug
        assert data["status"] == "INTAKE_ONLY", slug
        assert data["hypothesis_status"] == "HYPOTHESIS", slug
        assert data["sizing"] is False, slug
        assert data["scan_gate"] is False, slug
        assert data["promote"] is False, slug
        assert data["live"] is False, slug
        assert data["compute"] is False, slug
        assert data["paper_only"] is True, slug
        assert data["intake_date"] == "2026-09-19", slug
        assert "INTAKE_ONLY" in text
        assert "HYPOTHESIS" in text
        assert "QUANT" in text
        assert "DO NOT SIZE" in text
        assert "Scan gate" in text or "scan gate" in text.lower()
        assert "8." in text and "12." in text
        assert "Deliverable" in text or "deliverable" in text.lower()
        assert "Acceptance" in text or "acceptance" in text.lower()
        assert "permission filter" in text.lower()
        assert data["status"] == "INTAKE_ONLY"
        assert data.get("permission_filter_note", {}).get("status_unchanged") == "INTAKE_ONLY"


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
        assert data["study"]["compute"] is False
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


def test_config_candidates_intake_only_params_match_and_no_results() -> None:
    desk = yaml.safe_load((ROOT / "config" / "candidates" / "desk.yaml").read_text(encoding="utf-8"))
    assert desk["status"] == "INTAKE_ONLY"
    assert desk["compute"] is False
    assert desk["computation_gates"]["phase1_unconditional_base_rates"]["landed"] is False
    assert desk["computation_gates"]["scorecards_6e_instance_autotrack"]["landed"] is False
    assert desk["overlap_n_bars"] == 5
    assert desk["overlap_threshold_pct"] == 40
    assert desk["promote_at_most_one"] is True
    assert desk["family"] == "dip-in-uptrend"
    for cid, slug in (
        ("C-001", "C-001-supply-demand-zone"),
        ("C-002", "C-002-triple-rsi-mr"),
        ("C-003", "C-003-second-entry-pullback"),
    ):
        locked = yaml.safe_load((ROOT / "config" / "candidates" / f"{cid}.yaml").read_text(encoding="utf-8"))
        card = yaml.safe_load((CANDIDATES / f"{slug}.yaml").read_text(encoding="utf-8"))
        assert locked["status"] == "INTAKE_ONLY", cid
        assert locked["compute"] is False, cid
        assert locked["results"] == [], cid
        assert locked["declared_before_first_run"] is True, cid
        assert locked["version"] == "v1", cid
        for key in REQUIRED_PARAMS:
            assert locked["params"][key] == card["params"][key], f"{cid}.{key}"
        assert "thresholds" in locked["params"]
        assert "horizons" in locked["params"]
        assert card["locked_params"] == f"config/candidates/{cid}.yaml"
    studies = ROOT / "research" / "studies"
    assert (studies / "README.md").is_file()
    dated = [p for p in studies.rglob("*.md") if p.name != "README.md"]
    forbidden = [p for p in dated if _looks_like_candidate_compute_study(p, studies)]
    assert forbidden == [], forbidden
    assert "studies" in SKIP_DIR_NAMES


def test_methodology_studies_allowed_candidate_compute_studies_forbidden() -> None:
    studies = ROOT / "research" / "studies"
    assert _looks_like_candidate_compute_study(studies / "C-001" / "2026-09-19.md", studies)
    assert _looks_like_candidate_compute_study(studies / "C-002" / "2026-09-19.md", studies)
    assert _looks_like_candidate_compute_study(studies / "C-003" / "2026-09-19.md", studies)
    assert _looks_like_candidate_compute_study(
        studies / "signal-correlation" / "2026-09-19.md", studies
    )
    assert _looks_like_candidate_compute_study(
        studies / "C-001-supply-demand-zone" / "2026-09-19.md", studies
    )
    assert _looks_like_candidate_compute_study(studies / "C-002.md", studies)
    assert not _looks_like_candidate_compute_study(
        studies / "trend-permission-filter" / "2026-09-19.md", studies
    )
    assert not _looks_like_candidate_compute_study(
        studies / "permission-filter" / "notes.md", studies
    )
    dated = [p for p in studies.rglob("*.md") if p.name != "README.md"]
    assert any(p.name == "2026-09-19.md" and "trend-permission-filter" in p.parts for p in dated)


def test_candidates_are_not_thesis_workspaces() -> None:
    assert "candidates" in SKIP_DIR_NAMES
    assert "failures" in SKIP_DIR_NAMES
    found = discover_workspaces(ROOT / "research")
    leaked = [path for path in found if "candidates" in path.parts or "studies" in path.parts]
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
    assert any("IMP-024" in line and "DONE" in line for line in board_lines)
    assert any("IMP-039" in line and "READY" in line for line in board_lines)
    assert any("IMP-047" in line and "IN_PROGRESS" in line for line in board_lines)
    assert any("IMP-040" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-033" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-034" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-022" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-039" in line and "IN_PROGRESS" in line for line in board_lines)
    assert "`IN_PROGRESS` count: **1** (IMP-047)" in queue
    assert "KRX:005930" in queue
    assert "licence_verdict" in queue
    assert "ELIGIBLE" in queue
    for item_id in ("SCHED-001", "BRIEF-TAG-20260918", "SRC-STOOQ-404", "SRC-FRED-MISSING-ENV"):
        assert item_id in queue
    assert queue.count("| **Status** | OPEN |") >= 3
    report = load_queue(ROOT)
    assert report.ok
    assert report.in_progress == ("IMP-047",)
    assert report.auto_merge is False
    assert report.auto_waive is False
    live = LIVE.read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
