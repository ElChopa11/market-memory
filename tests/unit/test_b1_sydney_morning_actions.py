"""B1 Stage 1: GitHub Actions cron stamps grok.sydney_morning without Telegram."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
GITIGNORE = ROOT / ".gitignore"
COMPLETIONS_README = ROOT / "ops" / "reports" / "scheduler" / "completions" / "README.md"


def test_hybrid_sydney_morning_workflow_contract() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert WORKFLOW.is_file()
    assert "workflow_dispatch:" in text
    assert "schedule:" in text
    assert 'cron: "30 20 * * 0-4"' in text  # AEST 06:30 → prior-day 20:30 UTC
    assert 'cron: "30 19 * * 0-4"' in text  # AEDT 06:30 → prior-day 19:30 UTC
    assert "lab" in text and "schedule" in text and "heartbeat" in text
    assert "grok.sydney_morning" in text
    assert "--no-db" in text
    assert "github.actions" in text
    # Durable commit path (Principal judgement): contents write + push + auditable message
    assert "contents: write" in text
    assert "git push" in text
    assert "scheduled_for=" in text
    assert "delta_seconds=" in text
    assert "git pull --rebase" in text
    assert "STAMP COMMIT-BACK FAILED" in text
    assert "SCOPE VIOLATION" in text
    assert 'git add -- "${COMPLETIONS_DIR}/$(basename -- "${COMPLETION_PATH}")"' in text or (
        "COMPLETIONS_DIR" in text and "git add --" in text
    )
    # Artifact is secondary
    assert "actions/upload-artifact" in text
    assert "secondary" in text.lower()
    # Stage 1: no live Telegram path, no Telegram secrets wired, no --send
    assert "secrets.TELEGRAM" not in text
    assert "TELEGRAM_CHAT_ID" not in text
    assert "TELEGRAM_BOT_TOKEN:" not in text  # not an env/secret binding (scan string OK)
    assert "--send" not in text
    assert "--i-mean-it" not in text
    assert "to-principal-dm" not in text
    # ±900s guard is the module, not inline workflow Python.
    assert "decide_sydney_morning_anchor" in text
    assert "mm_desks.sydney_anchor" in text
    assert "ZoneInfo" not in text
    assert "MISS_AFTER = 900" not in text


def test_completions_are_not_gitignored() -> None:
    gi = GITIGNORE.read_text(encoding="utf-8")
    assert "ops/reports/scheduler/completions/**" not in gi
    readme = COMPLETIONS_README.read_text(encoding="utf-8")
    assert "ARE committed" in readme or "are committed" in readme.lower()
    assert "Do not commit generated JSON" not in readme
