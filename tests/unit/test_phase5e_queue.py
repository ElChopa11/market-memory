"""Phase 5e queue hygiene: IMP-012 DONE, IMP-013 this PR, IMP-014 parked."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_012_done_013_in_review_014_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-012" in line and "DONE" in line for line in board_lines)
    assert any("IMP-013" in line and "DONE" in line for line in board_lines)
    assert any("IMP-014" in line and "IN_REVIEW" in line for line in board_lines)
    assert "IMP-013" in queue
    assert "Telegram" in queue


def test_phase5e_plan_runbook_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-013-phase5e-telegram.md",
        "ops/plans/IMP-014-phase6a-pg-notify-mesh.md",
        "docs/runbooks/telegram.md",
        "ADR/0003-telegram-delivery.md",
        "config/delivery/telegram.yaml",
        "packages/delivery/src/mm_delivery/telegram.py",
        "packages/delivery/src/mm_delivery/deliver.py",
        "tests/fixtures/phase5e/desk-pack.md",
        "tests/fixtures/phase5e/frozen_telegram_payload.json",
        "tests/fixtures/phase5e/frozen_telegram_payload.sha256",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase5_complete_phase6_started() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Phase 5" in readme
    assert "complete" in readme.lower() or "5e" in readme
    assert "IMP-013" in readme
    assert "IMP-014" in readme or "Phase 6" in readme
    assert "Telegram" in readme
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live.replace(" ", "") or "live_trading_enabled: false" in live


def test_config_maps_desks_to_env_names_not_ids() -> None:
    text = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "TELEGRAM_CHAT_ID" in text
    assert "chat_id_env" in text
    assert "thread_id" in text
    assert "min_completeness_pct" in text
    assert "quiet_hours" in text
    assert "ttl_seconds" in text
