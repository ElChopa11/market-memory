"""B1 hybrid Sydney Morning Actions: Stage 1 stamp + brief-and-deliver gate."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

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
    """Return (stage1 job, brief-and-deliver job). Match the YAML keys, not comments."""
    stage1_key = "\n  stage1-stamp:\n"
    brief_key = "\n  brief-and-deliver:\n"
    assert stage1_key in text
    assert brief_key in text
    stage1_start = text.index(stage1_key)
    brief_start = text.index(brief_key)
    assert stage1_start < brief_start
    return text[stage1_start:brief_start], text[brief_start:]


def test_hybrid_sydney_morning_workflow_stage1_contract() -> None:
    text = _workflow_text()
    stage1, _brief = _split_jobs(text)
    assert "workflow_dispatch:" in text
    assert "schedule:" in text
    assert text.count('cron: "30 20 * * 0-4"') == 1  # AEST 06:30 primary → prior-day 20:30 UTC
    assert text.count('cron: "30 22 * * 0-4"') == 1  # AEST 08:30 prove/backup → prior-day 22:30 UTC
    assert 'cron: "30 19 * * 0-4"' not in text  # AEDT companion cron stays off
    assert "outside_anchor_window" not in text
    assert "FORCE_STAMP" not in text
    assert "i_mean_it_stage2" not in text
    assert "lab" in stage1 and "schedule" in stage1 and "heartbeat" in stage1
    assert "grok.sydney_morning" in stage1
    assert "--no-db" in stage1
    assert "github.actions" in stage1
    # Durable commit path (Principal judgement): contents write + push + auditable message
    assert "contents: write" in text
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
    assert "brief close" not in stage1
    assert "deliver pack" not in stage1


def test_hybrid_sydney_morning_brief_and_deliver_contract() -> None:
    text = _workflow_text()
    stage1, brief = _split_jobs(text)
    assert "needs: stage1-stamp" in brief
    # Both crons live on the workflow schedule, not inside this job.
    assert text.count('cron: "30 20 * * 0-4"') == 1
    assert text.count('cron: "30 22 * * 0-4"') == 1
    assert 'cron: "30 20 * * 0-4"' not in brief
    assert 'cron: "30 22 * * 0-4"' not in brief
    deliver_if = (
        "if: (github.event_name != 'workflow_dispatch' || "
        "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof')) && "
        "(github.event_name == 'schedule' || "
        "(github.event_name == 'workflow_dispatch' && "
        "(inputs.i_mean_it_deliver == true || github.event.inputs.i_mean_it_deliver == 'true')))"
        " && inputs.mode != 'send_proof'"
    )
    assert deliver_if in brief
    assert brief.count("i_mean_it_deliver") >= 1
    # Dispatch input: boolean, default false. Not the retired Stage 2 name.
    assert "i_mean_it_deliver:" in text
    assert "type: boolean" in text
    assert "default: false" in text
    assert text.count("default: false") == 1
    assert "i_mean_it_stage2" not in text
    # Stamp is not gated on i_mean_it_deliver. capture_proof and render_proof skip it.
    assert "i_mean_it_deliver" not in stage1
    assert stage1.count("\n    if:") == 1
    assert "inputs.mode != 'capture_proof'" in stage1
    assert "lab brief close" in brief
    assert "--live" in brief
    assert "--no-db" in brief
    assert "lab deliver pack" in brief
    assert "--to-principal-dm" in brief
    assert "--i-mean-it" in brief
    assert "--ignore-quiet-hours" in brief
    assert "--from-markdown" in brief
    # Secret NAMES only (Actions second bot; not box telegram.env).
    assert "secrets.TELEGRAM_BOT_TOKEN" in brief
    assert "secrets.TELEGRAM_CHAT_ID_PRINCIPAL_DM" in brief
    # Optional equities/rates richness. Empty when absent; not a hard fail.
    assert "POLYGON_API_KEY: ${{ secrets.POLYGON_API_KEY }}" in brief
    assert "FRED_API_KEY: ${{ secrets.FRED_API_KEY }}" in brief
    assert "POLYGON_API_KEY" not in stage1
    assert "FRED_API_KEY" not in stage1
    gate_start = brief.index("- name: Gate —")
    gate_end = brief.index("- uses: actions/checkout@v4")
    gate = brief[gate_start:gate_end]
    assert "POLYGON_API_KEY" not in gate
    assert "FRED_API_KEY" not in gate
    header = text.split("name: hybrid-sydney-morning", 1)[0]
    assert "not required for stamp or DM" in header
    assert "POLYGON_API_KEY" in header and "FRED_API_KEY" in header
    # Group id must stay unset — never wire the group secret.
    assert re.search(r"secrets\.TELEGRAM_CHAT_ID\s*}}", text) is None
    assert "TELEGRAM_CHAT_ID: ${{" not in text
    assert "TELEGRAM_CHAT_ID must remain UNSET" in brief
    assert "ready=false" in brief
    assert "Soft skip" in brief or "soft skip" in brief.lower()
    # No group --send flag (substring-safe: this job must not contain the token).
    assert "--send" not in brief
    assert "--no-send" not in brief
    # Stamp commit-back stays on stage1. Deliver receipt commit-back is a separate hard scope.
    assert "git push" in stage1
    assert "STAMP COMMIT-BACK FAILED" in stage1
    assert "STAMP COMMIT-BACK FAILED" not in brief
    assert "git push" in brief
    assert "DELIVER RECEIPT COMMIT-BACK FAILED" in brief
    assert "contents: write" in brief
    assert 'git add -- "${RECEIPTS_DIR}/$(basename -- "${RECEIPT_PATH}")"' in brief
    assert 'git add -- "${COMPLETIONS_DIR}/$(basename -- "${COMPLETION_PATH}")"' not in brief
    assert "completions/receipts" in brief
    assert "decide_deliver" in brief
    assert "accept_delivery" in brief
    assert "write_deliver_receipt" in brief
    assert "already_delivered" in brief
    assert brief.index("Deliver-receipt gate") < brief.index("Live US-close brief")
    assert brief.index('git fetch origin "${BRANCH}"') < brief.index("decide_deliver")
    assert 'git checkout -B "${BRANCH}" "origin/${BRANCH}"' in brief
    assert brief.index("decide_deliver") < brief.index("uv run lab brief close")
    assert brief.index("uv run lab brief close") < brief.index("uv run lab deliver pack")
    assert brief.index("uv run lab deliver pack") < brief.index("write_deliver_receipt")
    assert "steps.receipt.outputs.already_delivered != 'true'" in brief
    assert "needs.stage1-stamp.outputs.scheduled_for" in brief
    assert "scheduled_for: ${{ steps.stamp.outputs.scheduled_for }}" in stage1
    assert "write_deliver_receipt" not in stage1
    assert "already_delivered" not in stage1
    assert "concurrency:" in text
    assert "group: hybrid-sydney-morning" in text
    assert text.count("cancel-in-progress:") == 1
    assert "cancel-in-progress: false" in text
    assert "repository_dispatch" not in text
    assert "MM_LOG_RATE_LIMIT_HEADERS" in brief
    assert "outside_anchor_window" not in stage1


def test_brief_and_deliver_runbook_lists_secret_names() -> None:
    sched = SCHEDULER_RUNBOOK.read_text(encoding="utf-8")
    tg = TELEGRAM_RUNBOOK.read_text(encoding="utf-8")
    blob = sched + "\n" + tg
    assert "brief-and-deliver" in blob
    assert "i_mean_it_deliver" in blob
    assert "defaults to false" in blob
    assert "TELEGRAM_BOT_TOKEN" in blob
    assert "TELEGRAM_CHAT_ID_PRINCIPAL_DM" in blob
    assert "TELEGRAM_CHAT_ID" in blob
    assert "soft-skip" in blob or "soft skip" in blob.lower() or "Soft skip" in blob
    assert "MM_LOG_RATE_LIMIT_HEADERS" in blob
    # Optional data richness — listed in both runbooks; not required for stamp or DM.
    for book in (sched, tg):
        assert "POLYGON_API_KEY" in book
        assert "FRED_API_KEY" in book
        assert "optional data richness" in book
        assert "not required for stamp or DM" in book
    sentence = (
        "A drifted cron (or second trigger) arriving after a successful deliver "
        "for that anchor is a silent no-op / already_delivered, not a failure or miss."
    )
    assert sentence in sched
    assert sentence in tg
    index = (ROOT / "ops" / "reports" / "scheduler" / "README.md").read_text(encoding="utf-8")
    assert sentence in index
    assert sentence in COMPLETIONS_README.read_text(encoding="utf-8")


def _stamp_runs(event: str, mode: str | None) -> bool:
    return event != "workflow_dispatch" or mode not in {"capture_proof", "render_proof", "send_proof"}


def _brief_runs(event: str, mode: str | None, *, deliver: bool) -> bool:
    mode_ok = event != "workflow_dispatch" or mode not in {"capture_proof", "render_proof"}
    deliver_ok = event == "schedule" or (event == "workflow_dispatch" and deliver)
    return mode_ok and deliver_ok and mode != "send_proof"


def _capture_runs(event: str, mode: str | None) -> bool:
    return event == "workflow_dispatch" and mode == "capture_proof"


def _render_runs(event: str, mode: str | None) -> bool:
    return event == "workflow_dispatch" and mode == "render_proof"


def test_render_proof_skips_stamp_brief_capture_and_has_no_send_secrets() -> None:
    text = _workflow_text()
    parsed = yaml.safe_load(text)
    jobs = parsed["jobs"]
    on_block = parsed[True] if True in parsed else parsed["on"]
    options = on_block["workflow_dispatch"]["inputs"]["mode"]["options"]
    assert options == ["normal", "capture_proof", "render_proof", "send_proof"]
    stamp = jobs["stage1-stamp"]["if"]
    brief = jobs["brief-and-deliver"]["if"]
    capture = jobs["capture-proof"]["if"]
    render = jobs["render-proof"]["if"]
    assert stamp == (
        "github.event_name != 'workflow_dispatch' || "
        "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof') && "
        "inputs.mode != 'send_proof'"
    )
    assert brief == (
        "(github.event_name != 'workflow_dispatch' || "
        "(inputs.mode != 'capture_proof' && inputs.mode != 'render_proof')) && "
        "(github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && "
        "(inputs.i_mean_it_deliver == true || github.event.inputs.i_mean_it_deliver == 'true')))"
        " && inputs.mode != 'send_proof'"
    )
    assert capture == "github.event_name == 'workflow_dispatch' && inputs.mode == 'capture_proof'"
    assert render == "github.event_name == 'workflow_dispatch' && inputs.mode == 'render_proof'"
    assert _stamp_runs("schedule", None) is True
    assert _stamp_runs("workflow_dispatch", "normal") is True
    assert _stamp_runs("workflow_dispatch", "render_proof") is False
    assert _brief_runs("schedule", "normal", deliver=False) is True
    assert _brief_runs("workflow_dispatch", "render_proof", deliver=True) is False
    assert _brief_runs("workflow_dispatch", "render_proof", deliver=False) is False
    assert _capture_runs("workflow_dispatch", "render_proof") is False
    assert _capture_runs("workflow_dispatch", "capture_proof") is True
    assert _render_runs("workflow_dispatch", "render_proof") is True
    assert _render_runs("workflow_dispatch", "capture_proof") is False
    assert _render_runs("schedule", "render_proof") is False
    assert "needs" not in jobs["render-proof"]
    assert jobs["render-proof"].get("needs") is None
    job_text = text[text.index("\n  render-proof:\n") :]
    assert "TELEGRAM" not in job_text
    assert "HEALTHCHECKS" not in job_text
    assert "POSTGRES" not in job_text
    assert "lab deliver" not in job_text
    assert "lab retain" not in job_text
    assert "stamp_cli_fire" not in job_text
    assert "write_deliver_receipt" not in job_text
    assert "git commit" not in job_text
    assert "git push" not in job_text
    assert "lab brief close --live --no-db" in job_text
    assert "--send" not in job_text
    steps = jobs["render-proof"]["steps"]
    envs = [step["env"] for step in steps if "env" in step]
    assert envs == [
        {
            "POLYGON_API_KEY": "${{ secrets.POLYGON_API_KEY }}",
            "FRED_API_KEY": "${{ secrets.FRED_API_KEY }}",
        }
    ]
    assert text.count("group: hybrid-sydney-morning") == 1
    assert text.count("cancel-in-progress:") == 1


def test_completions_are_not_gitignored() -> None:
    gi = GITIGNORE.read_text(encoding="utf-8")
    assert "ops/reports/scheduler/completions/**" not in gi
    readme = COMPLETIONS_README.read_text(encoding="utf-8")
    assert "ARE committed" in readme or "are committed" in readme.lower()
    assert "Do not commit generated JSON" not in readme
    assert "receipts/" in readme
    assert "ops/reports/scheduler/completions/receipts" not in gi
