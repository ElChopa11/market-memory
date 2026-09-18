"""Phase 6a queue hygiene: IMP-013 DONE, IMP-014 this PR, IMP-015 parked."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_013_done_014_in_review_015_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-013" in line and "DONE" in line for line in board_lines)
    assert any("IMP-014" in line and "IN_REVIEW" in line for line in board_lines)
    assert any("IMP-015" in line and ("READY" in line or "PARKED" in line) for line in board_lines)
    assert not any("IMP-015" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-013" in line and "IN_REVIEW" in line for line in board_lines)
    assert "LISTEN/NOTIFY" in queue or "NOTIFY" in queue
    assert "Redis" in queue


def test_phase6a_plan_adr_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-014-phase6a-pg-notify-mesh.md",
        "ops/plans/IMP-015-phase6b-flow-macro-regime.md",
        "ADR/0004-desk-mesh-pg-notify.md",
        "config/desks/cadence.yaml",
        "packages/desks/src/mm_desks/envelope.py",
        "packages/desks/src/mm_desks/mesh.py",
        "packages/desks/src/mm_desks/bus.py",
        "packages/memory/src/mm_memory/notify.py",
        "packages/memory/src/mm_memory/envelope_repository.py",
        "packages/memory/src/mm_memory/migrations/versions/0007_phase6a_desk_mesh.py",
        "apps/lab-cli/src/mm_lab_cli/mesh.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase6_in_progress_6a() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Phase 6" in readme
    assert "6a" in readme
    assert "IMP-014" in readme
    assert "NOTIFY" in readme
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    cadence = (ROOT / "config" / "desks" / "cadence.yaml").read_text(encoding="utf-8")
    assert "unset" in cadence
    assert "coord.assemble" in cadence
    assert "dq.event" in cadence
    adr = (ROOT / "ADR" / "0004-desk-mesh-pg-notify.md").read_text(encoding="utf-8")
    assert "LISTEN/NOTIFY" in adr
    assert "Redis" in adr
    runbook = (ROOT / "docs" / "runbooks" / "desks.md").read_text(encoding="utf-8")
    assert "mesh" in runbook.lower()
    assert "NOTIFY" in runbook


def test_no_redis_dependency_in_workspace() -> None:
    pyprojects = list((ROOT / "packages").glob("*/pyproject.toml")) + list((ROOT / "apps").glob("*/pyproject.toml"))
    pyprojects.append(ROOT / "pyproject.toml")
    for path in pyprojects:
        text = path.read_text(encoding="utf-8").lower()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("description"):
                continue
            if "no redis" in stripped or "not redis" in stripped:
                continue
            assert "redis" not in stripped, path
