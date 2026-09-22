"""B1 Stage 1: GitHub Actions cron stamps grok.sydney_morning without Telegram."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"


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
    assert "actions/upload-artifact" in text
    assert "github.actions" in text
    # Stage 1: no live Telegram path, no secrets refs, no --send
    assert "TELEGRAM_BOT_TOKEN" not in text
    assert "TELEGRAM_CHAT_ID" not in text
    assert "${{ secrets." not in text
    assert "secrets." not in text.replace("No TELEGRAM_* secrets.", "")
    assert "--send" not in text
    assert "--i-mean-it" not in text
    assert "to-principal-dm" not in text
