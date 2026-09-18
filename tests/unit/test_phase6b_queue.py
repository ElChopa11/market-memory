"""Phase 6b queue hygiene: IMP-014 DONE, IMP-015 this PR, IMP-016 parked."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_014_done_015_in_review_016_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-014" in line and "DONE" in line for line in board_lines)
    assert any("IMP-015" in line and "DONE" in line for line in board_lines)
    assert any("IMP-016" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-016" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-014" in line and "IN_REVIEW" in line for line in board_lines)
    assert "NOTIFY" in queue
    assert "Redis" in queue


def test_phase6b_plan_adr_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-014-phase6a-pg-notify-mesh.md",
        "ops/plans/IMP-015-phase6b-flow-macro-regime.md",
        "ops/plans/IMP-016-phase6c-telegram-fanout.md",
        "ADR/0005-flow-macro-regime.md",
        "config/flow/liquidity.yaml",
        "config/macro/regimes.yaml",
        "packages/flow/src/mm_flow/engine.py",
        "packages/macro/src/mm_macro/regime.py",
        "packages/desks/src/mm_desks/flow.py",
        "packages/desks/src/mm_desks/macro.py",
        "docs/runbooks/flow-desk.md",
        "docs/runbooks/macro-desk.md",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase6_in_progress_6b() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Phase 6" in readme
    assert "6b" in readme
    assert "IMP-015" in readme
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    cadence = (ROOT / "config" / "desks" / "cadence.yaml").read_text(encoding="utf-8")
    assert "desk.flow.output" in cadence
    assert "desk.macro.output" in cadence
    defaults = (ROOT / "config" / "risk" / "defaults.yaml").read_text(encoding="utf-8")
    assert "untradeable_at_size" in defaults
    assert "event_risk" in defaults
    assert "live_trading_enabled: false" in defaults
