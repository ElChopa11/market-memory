"""One-shot Neon migrate workflow. Does not connect and does not migrate."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "migrate-neon.yml"
HYBRID = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
RUNBOOK = ROOT / "docs" / "runbooks" / "migrate-neon.md"
INGEST = ROOT / "docs" / "runbooks" / "ingest.md"

CONFIRM = "i_mean_it_migrate"


def _workflow_text() -> str:
    assert WORKFLOW.is_file()
    return WORKFLOW.read_text(encoding="utf-8")


def _on_block(text: str) -> str:
    marker = "\non:\n"
    assert marker in text
    rest = text.split(marker, 1)[1]
    # Root keys after `on:` resume at column 0.
    match = re.search(r"\n(?=[A-Za-z])", rest)
    assert match is not None
    return rest[: match.start()]


def _job_keys(text: str) -> list[str]:
    assert "\njobs:\n" in text
    jobs = text.split("\njobs:\n", 1)[1]
    return re.findall(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", jobs)


def test_migrate_neon_is_one_dispatch_job() -> None:
    text = _workflow_text()
    on_block = _on_block(text)
    assert "name: migrate-neon" in text
    assert "workflow_dispatch:" in on_block
    assert "confirm:" in on_block
    assert "type: string" in on_block
    assert "required: true" in on_block
    assert CONFIRM in on_block
    assert "type: boolean" not in text
    assert re.search(r"(?m)^[ \t]*schedule:", text) is None
    assert re.search(r"(?m)^[ \t]*cron:", text) is None
    assert "repository_dispatch" not in on_block
    assert re.search(r"(?m)^[ \t]*repository_dispatch:", text) is None
    assert re.search(r"(?m)^[ \t]*push:", text) is None
    assert re.search(r"(?m)^[ \t]*pull_request:", text) is None
    assert "workflow_call" not in text
    assert "workflow_run" not in text
    assert _job_keys(text) == ["migrate"]
    assert "environment:" not in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "permissions:" in text


def test_confirm_mismatch_exits_nonzero_before_secret() -> None:
    text = _workflow_text()
    confirm_step, remainder = text.split("- name: Require confirm string", 1)
    apply_step = remainder.split("- name: Apply Alembic head", 1)[1]
    assert f'!= "{CONFIRM}"' in remainder.split("- name: Apply Alembic head", 1)[0]
    assert "exit 1" in remainder.split("- uses: actions/checkout@v4", 1)[0]
    assert "POSTGRES_DSN was not read" in remainder
    assert "secrets.POSTGRES_DSN" not in confirm_step
    assert "secrets.POSTGRES_DSN" in apply_step
    assert text.count("secrets.POSTGRES_DSN") == 1
    assert "secrets.DATABASE_URL" not in text
    assert "secrets.NEON_API_KEY" not in text
    assert "echo \"$POSTGRES_DSN\"" not in text
    assert "echo ${POSTGRES_DSN}" not in text
    assert "echo \"$CONFIRM\"" not in text
    assert "print(dsn)" not in text
    assert "set -x" not in text
    assert "::add-mask::" in apply_step
    assert "DSN not printed" in apply_step
    assert ".neon.tech" in apply_step
    assert "-pooler" in apply_step
    assert "sslmode=require" in apply_step


def test_job_runs_lab_migrate_once_and_fails_loud() -> None:
    text = _workflow_text()
    assert text.count("uv run lab migrate") == 1
    assert "history-backfill" not in text
    assert "FAIL: lab migrate exited non-zero." in text
    assert "SUCCESS: lab migrate exited 0." in text
    assert "alembic_head=" in text
    assert "TELEGRAM" not in text
    assert "i_mean_it_deliver" not in text
    assert "uses: ./.github/workflows/hybrid-sydney-morning.yml" not in text
    assert "hybrid-sydney-morning" in text  # prohibition comment, not a call
    assert "Do not call hybrid-sydney-morning" in text
    assert "--no-db" not in text
    assert "MINIO_" not in text


def test_hybrid_sydney_morning_flags_unchanged() -> None:
    """This change must not drop the Sydney morning cron or --no-db."""
    text = HYBRID.read_text(encoding="utf-8")
    assert text.count('cron: "30 20 * * 0-4"') == 1
    assert text.count('cron: "30 22 * * 0-4"') == 1
    assert "--no-db" in text
    assert "i_mean_it_deliver:" in text
    assert "brief-and-deliver:" in text
    assert CONFIRM not in text


def _run_script(text: str, step_name: str) -> str:
    chunk = text.split(f"- name: {step_name}\n", 1)[1]
    chunk = chunk.split("run: |\n", 1)[1]
    script_lines: list[str] = []
    for line in chunk.splitlines():
        if line.startswith("      - "):
            break
        script_lines.append(line)
    while script_lines and script_lines[-1].strip() == "":
        script_lines.pop()
    indent = len(script_lines[0]) - len(script_lines[0].lstrip(" "))
    return "\n".join((line[indent:] if line.strip() else "") for line in script_lines) + "\n"


def _preflight_python(script: str) -> str:
    start = script.index("<<'PY'\n") + len("<<'PY'\n")
    end = script.index("\nPY\n", start)
    return script[start:end] + "\n"


def _run_preflight(dsn: str) -> subprocess.CompletedProcess[str]:
    script = _run_script(_workflow_text(), "Apply Alembic head")
    assert script.count("uv run lab migrate") == 1
    return subprocess.run(
        [sys.executable, "-c", _preflight_python(script)],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "POSTGRES_DSN": dsn},
    )


def test_confirm_script_refuses_any_other_string() -> None:
    script = _run_script(_workflow_text(), "Require confirm string")
    assert "uv run lab migrate" not in script
    assert "POSTGRES_DSN" not in script.split("echo", 1)[0]
    wrong = subprocess.run(
        ["bash", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "CONFIRM": "yes"},
    )
    assert wrong.returncode == 1
    assert "REFUSE: confirm is not exactly i_mean_it_migrate" in wrong.stdout
    assert "yes" not in wrong.stdout
    assert "POSTGRES_DSN" not in wrong.stdout or "was not read" in wrong.stdout
    right = subprocess.run(
        ["bash", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "CONFIRM": CONFIRM},
    )
    assert right.returncode == 0
    assert "confirm accepted" in right.stdout


def test_preflight_masks_dsn_and_refuses_bad_hosts() -> None:
    secret = "postgresql://mm_user:super-secret-password@ep-example.ap-southeast-2.aws.neon.tech/market_memory?sslmode=require"
    ok = _run_preflight(secret)
    assert ok.returncode == 0, ok.stderr
    visible = "\n".join(line for line in ok.stdout.splitlines() if not line.startswith("::add-mask::"))
    assert "super-secret-password" not in visible
    assert "mm_user" not in visible
    assert "ep-example" not in visible
    assert "DSN not printed" in visible
    assert secret not in ok.stderr

    empty = _run_preflight("   ")
    assert empty.returncode == 1
    assert "POSTGRES_DSN is empty" in empty.stdout

    pooler = _run_preflight(
        "postgresql://mm_user:super-secret-password@ep-example-pooler.ap-southeast-2.aws.neon.tech/market_memory?sslmode=require"
    )
    assert pooler.returncode == 1
    assert "no -pooler" in pooler.stdout
    assert "super-secret-password" not in "\n".join(
        line for line in pooler.stdout.splitlines() if not line.startswith("::add-mask::")
    )

    local = _run_preflight("postgresql://lab:lab@localhost:5432/market_memory")
    assert local.returncode == 1
    assert "direct Neon host" in local.stdout

    missing_ssl = _run_preflight(
        "postgresql://mm_user:super-secret-password@ep-example.ap-southeast-2.aws.neon.tech/market_memory"
    )
    assert missing_ssl.returncode == 1
    assert "sslmode=require" in missing_ssl.stdout


def test_apply_script_parses_without_running_migrate() -> None:
    script = _run_script(_workflow_text(), "Apply Alembic head")
    parsed = subprocess.run(["bash", "-n"], input=script, check=False, capture_output=True, text=True)
    assert parsed.returncode == 0, parsed.stderr


def test_runbook_is_the_same_sitting_delete_path() -> None:
    from mm_memory.migrate import alembic_head

    text = RUNBOOK.read_text(encoding="utf-8")
    head = alembic_head()
    assert head in text
    assert ".github/workflows/migrate-neon.yml" in text
    assert "workflow_dispatch" in text
    assert "repository_dispatch" in text
    assert CONFIRM in text
    assert "confirm" in text
    assert "POSTGRES_DSN" in text
    assert "DATABASE_URL" in text
    assert "uv run lab migrate" in text
    assert "migrated to" in text
    assert "SUCCESS: lab migrate exited 0" in text
    assert "SELECT version_num FROM alembic_version" in text
    assert "Delete `.github/workflows/migrate-neon.yml`" in text
    assert "same sitting" in text
    assert "#114" in text
    assert "shelved" in text
    assert "history-backfill" in text
    assert "#120" in text
    assert "hybrid-sydney-morning" in text
    assert "No cron" in text
    assert "Paper only" in text
    assert "No Telegram" in text
    assert "winget" not in text.lower()
    assert "Windows" not in text
    ingest = INGEST.read_text(encoding="utf-8")
    assert "docs/runbooks/migrate-neon.md" in ingest
