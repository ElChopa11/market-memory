"""Thin Grok clock: one repository_dispatch type, deliver hardcoded via workflow_call."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
DISPATCH = WORKFLOWS / "sydney-morning-repo-dispatch.yml"
HYBRID = WORKFLOWS / "hybrid-sydney-morning.yml"
SCHEDULER = ROOT / "docs" / "runbooks" / "scheduler.md"
TELEGRAM = ROOT / "docs" / "runbooks" / "telegram.md"

EVENT_TYPE = "sydney-morning-deliver"
SEALED_PAT = "/home/box/agent-data/infra/github-sm-dispatch.pat"

# The event type is the trigger contract. It may be named in the runbooks
# and in this test. It must not appear in any other workflow.
ALLOWED_EVENT_TYPE_PATHS = {
    ".github/workflows/sydney-morning-repo-dispatch.yml",
    "docs/runbooks/scheduler.md",
    "docs/runbooks/telegram.md",
    "tests/unit/test_sydney_morning_repo_dispatch.py",
    "tests/unit/test_b1_sydney_morning_actions.py",
}

_TEXT_SUFFIXES = {".yml", ".yaml", ".py", ".md", ".sh"}


def _dispatch_text() -> str:
    assert DISPATCH.is_file()
    return DISPATCH.read_text(encoding="utf-8")


def _repo_text_files() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(".git/"):
            continue
        if path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        found.append((rel, path.read_text(encoding="utf-8", errors="ignore")))
    return found


def test_dispatch_workflow_has_exactly_one_event_type() -> None:
    text = _dispatch_text()
    assert "name: sydney-morning-repo-dispatch" in text
    assert "repository_dispatch:" in text
    type_lines = [line.strip() for line in text.splitlines() if "types:" in line]
    assert type_lines == [f"types: [{EVENT_TYPE}]"]
    assert "workflow_dispatch:" not in text
    assert "schedule:" not in text
    assert "cron:" not in text
    assert "workflow_call:" not in text
    # No inputs on this workflow. The called workflow's `with:` is not an input.
    assert "\ninputs:" not in text
    # Documented as ignored. The workflow does not read the payload.
    assert "client_payload is ignored" in text
    assert "github.event.client_payload" not in text
    assert "i_mean_it_deliver: true" in text
    assert "i_mean_it_deliver: false" not in text
    assert "uses: ./.github/workflows/hybrid-sydney-morning.yml" in text
    assert "secrets: inherit" in text
    assert "contents: write" in text
    assert "actions: write" not in text
    assert "pull-requests:" not in text
    assert "id-token:" not in text
    assert "group: hybrid-sydney-morning" in text
    assert "cancel-in-progress: false" in text
    # Group chat secret stays unwired here. Deliver lives in the called workflow.
    assert "TELEGRAM_CHAT_ID:" not in text
    assert "secrets.TELEGRAM_CHAT_ID" not in text
    assert "github-sm-dispatch.pat" not in text
    assert "ghp_" not in text
    assert "github_pat_" not in text


def test_event_type_is_not_on_any_other_workflow() -> None:
    hits: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        body = path.read_text(encoding="utf-8")
        if EVENT_TYPE in body or "repository_dispatch" in body:
            hits.append(path.name)
    assert hits == ["sydney-morning-repo-dispatch.yml"]
    hybrid = HYBRID.read_text(encoding="utf-8")
    assert EVENT_TYPE not in hybrid
    assert "repository_dispatch" not in hybrid
    assert "workflow_call:" in hybrid
    assert "i_mean_it_deliver: true" not in hybrid


def test_event_type_allowlist_and_migrate_backfill_ingest_refuse_it() -> None:
    found = [
        rel
        for rel, body in _repo_text_files()
        if EVENT_TYPE in body
    ]
    assert sorted(found) == sorted(ALLOWED_EVENT_TYPE_PATHS)
    for rel, body in _repo_text_files():
        lowered = rel.lower()
        if not any(token in lowered for token in ("migrate", "backfill", "ingest")):
            continue
        assert EVENT_TYPE not in body, rel
        assert "repository_dispatch" not in body, rel


def test_runbook_contract_names_event_pat_and_caller_retry() -> None:
    sched = SCHEDULER.read_text(encoding="utf-8")
    tg = TELEGRAM.read_text(encoding="utf-8")
    assert EVENT_TYPE in sched
    assert EVENT_TYPE in tg
    assert SEALED_PAT in sched
    assert "0600" in sched
    assert "ElChopa11/market-memory" in sched
    assert "Actions: Read and write" in sched
    assert "Contents: No access" in sched
    assert "GITHUB_TOKEN" in sched
    assert "POST /repos/ElChopa11/market-memory/dispatches" in sched
    assert "event_type" in sched
    assert "3 attempts" in sched
    assert "non-2xx" in sched
    assert "did-not-fire" in sched
    assert "HTTP 500" in sched
    assert "in-window" in sched
    assert "client_payload" in sched
    assert "i_mean_it_deliver: true" in sched
    assert "secrets: inherit" in sched
    # Caller contract only. This change does not implement the Grok routine.
    assert "out of scope" in sched
    for book in (sched, tg):
        assert "ghp_" not in book
        assert "github_pat_" not in book
