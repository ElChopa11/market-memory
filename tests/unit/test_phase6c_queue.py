"""Phase 6c queue hygiene: IMP-016 DONE (#47), 6c-1 this PR, IMP-017 parked."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_queue_marks_015_done_016_done_017_parked() -> None:
    queue = (ROOT / "ops" / "improvement-queue.md").read_text(encoding="utf-8")
    board_lines = [line for line in queue.splitlines() if line.startswith("| IMP-")]
    assert any("IMP-015" in line and "DONE" in line for line in board_lines)
    assert any("IMP-016" in line and "DONE" in line for line in board_lines)
    assert any("IMP-017" in line and "DONE" in line for line in board_lines)
    assert not any("IMP-017" in line and "IN_PROGRESS" in line for line in board_lines)
    assert not any("IMP-015" in line and "IN_REVIEW" in line for line in board_lines)
    assert not any("IMP-016" in line and "IN_REVIEW" in line for line in board_lines)


def test_phase6c_plan_adr_prompts_and_config_exist() -> None:
    for rel in (
        "ops/plans/IMP-016-phase6c-telegram-fanout.md",
        "ops/plans/IMP-017-phase6d-listings-ipo.md",
        "ADR/0006-phase6c-playbook-telegram.md",
        "config/delivery/telegram.yaml",
        "config/playbook/ladder.yaml",
        "config/quant/trade_math.yaml",
        "config/risk/drawdown.yaml",
        "config/risk/clusters.yaml",
        "config/llm/budgets.yaml",
        "config/prompts/official_brief.v1.txt",
        "config/prompts/edge_scan.v1.txt",
        "docs/runbooks/telegram.md",
        "docs/runbooks/llm-budget.md",
        "docs/playbook.md",
        "templates/post-mortem.md",
        "packages/desks/src/mm_desks/playbook.py",
        "packages/quant/src/mm_quant/trade_math.py",
        "packages/delivery/src/mm_delivery/present.py",
        "packages/memory/src/mm_memory/migrations/versions/0008_phase6c_delivery.py",
    ):
        assert (ROOT / rel).is_file(), rel


def test_readme_phase6_in_progress_6c() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "6c" in readme
    assert "IMP-016" in readme
    live = (ROOT / "config" / "risk" / "environments" / "live.yaml").read_text(encoding="utf-8")
    assert "live_trading_enabled: false" in live
    tg = (ROOT / "config" / "delivery" / "telegram.yaml").read_text(encoding="utf-8")
    assert "TELEGRAM_CHAT_ID_ALERTS" in tg
    assert "/halt" in tg
