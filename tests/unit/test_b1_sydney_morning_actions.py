"""B1 hybrid Sydney Morning Actions: Stage 1 stamp + Stage 2 PREP DM pack gate."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
GITIGNORE = ROOT / ".gitignore"
COMPLETIONS_README = ROOT / "ops" / "reports" / "scheduler" / "completions" / "README.md"
SCHEDULER_RUNBOOK = ROOT / "docs" / "runbooks" / "scheduler.md"
TELEGRAM_RUNBOOK = ROOT / "docs" / "runbooks" / "telegram.md"


def _workflow_text() -> str:
    assert WORKFLOW.is_file()
    return WORKFLOW.read_text(encoding="utf-8")


def _split_jobs(text: str) -> tuple[str, str]:
    """Return (stage1 body, stage2 body) by job id markers."""
    assert "stage1-stamp:" in text
    assert "stage2-principal-dm-pack:" in text
    stage1_start = text.index("stage1-stamp:")
    stage2_start = text.index("stage2-principal-dm-pack:")
    assert stage1_start < stage2_start
    return text[stage1_start:stage2_start], text[stage2_start:]


def test_hybrid_sydney_morning_workflow_stage1_contract() -> None:
    text = _workflow_text()
    stage1, _stage2 = _split_jobs(text)
    assert "workflow_dispatch:" in text
    assert "schedule:" in text
    assert 'cron: "30 20 * * 0-4"' in text  # AEST 06:30 → prior-day 20:30 UTC
    assert 'cron: "30 19 * * 0-4"' in text  # AEDT 06:30 → prior-day 19:30 UTC
    assert "lab" in stage1 and "schedule" in stage1 and "heartbeat" in stage1
    assert "grok.sydney_morning" in stage1
    assert "--no-db" in stage1
    assert "github.actions" in stage1
    # Durable commit path (Principal judgement): contents write + push + auditable message
    assert "contents: write" in stage1
    assert "git push" in stage1
    assert "scheduled_for=" in stage1
    assert "delta_seconds=" in stage1
    assert "git pull --rebase" in stage1
    assert "STAMP COMMIT-BACK FAILED" in stage1
    assert "SCOPE VIOLATION" in stage1
    assert 'git add -- "${COMPLETIONS_DIR}/$(basename -- "${COMPLETION_PATH}")"' in stage1 or (
        "COMPLETIONS_DIR" in stage1 and "git add --" in stage1
    )
    # Artifact is secondary
    assert "actions/upload-artifact" in stage1
    assert "secondary" in stage1.lower()
    # Stage 1 job: no live Telegram path, no Telegram secrets wired, no --send
    assert "secrets.TELEGRAM" not in stage1
    assert "TELEGRAM_CHAT_ID" not in stage1
    assert "TELEGRAM_BOT_TOKEN:" not in stage1
    assert "--send" not in stage1
    assert "--i-mean-it" not in stage1
    assert "to-principal-dm" not in stage1


def test_hybrid_sydney_morning_workflow_stage2_prep_contract() -> None:
    text = _workflow_text()
    _stage1, stage2 = _split_jobs(text)
    # Explicit confirmation gate (default false) — accidental dispatch must not send
    assert "i_mean_it_stage2:" in text
    assert "default: false" in text
    assert "inputs.i_mean_it_stage2 == true" in stage2
    assert "workflow_dispatch" in stage2
    # DM-only pack path
    assert "lab deliver pack" in stage2 or ("lab" in stage2 and "deliver" in stage2 and "pack" in stage2)
    assert "--to-principal-dm" in stage2
    assert "--i-mean-it" in stage2
    assert "--no-db" in stage2
    assert "--from-markdown" in stage2
    # Secret NAMES only (Actions second bot; not box telegram.env)
    assert "secrets.TELEGRAM_BOT_TOKEN" in stage2
    assert "secrets.TELEGRAM_CHAT_ID_PRINCIPAL_DM" in stage2
    # Group id must stay unset — never wire the group secret; never --send to group
    assert "TELEGRAM_CHAT_ID: ${{" not in stage2
    assert "secrets.TELEGRAM_CHAT_ID }}" not in stage2  # exact group secret, not _PRINCIPAL_DM
    assert "TELEGRAM_CHAT_ID must remain UNSET" in stage2
    assert "--send" not in stage2
    assert "uv run lab deliver pack" in stage2
    assert "GROUP SEND_FROZEN" in text or "SEND_FROZEN" in text
    # Stage 2 does not rewrite Stage 1 commit-back
    assert "git push" not in stage2
    assert "STAMP COMMIT-BACK FAILED" not in stage2


def test_stage2_runbook_lists_secret_names_and_do_not_run() -> None:
    sched = SCHEDULER_RUNBOOK.read_text(encoding="utf-8")
    tg = TELEGRAM_RUNBOOK.read_text(encoding="utf-8")
    blob = sched + "\n" + tg
    assert "Stage 2" in blob or "stage2" in blob.lower()
    assert "TELEGRAM_BOT_TOKEN" in blob
    assert "TELEGRAM_CHAT_ID_PRINCIPAL_DM" in blob
    assert "do not run" in blob.lower() or "Do not run" in blob or "Do NOT" in blob
    assert "/start" in blob
    assert "i_mean_it_stage2" in blob


def test_completions_are_not_gitignored() -> None:
    gi = GITIGNORE.read_text(encoding="utf-8")
    assert "ops/reports/scheduler/completions/**" not in gi
    readme = COMPLETIONS_README.read_text(encoding="utf-8")
    assert "ARE committed" in readme or "are committed" in readme.lower()
    assert "Do not commit generated JSON" not in readme
