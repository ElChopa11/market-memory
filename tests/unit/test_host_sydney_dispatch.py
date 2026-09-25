"""External host cron dispatches hybrid-sydney-morning at the catalog Sydney anchor.

No live GitHub HTTP. Curl is a fake. The token must not appear in logs or stdout.
"""

from __future__ import annotations

import os
import stat
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from mm_desks.scheduler import load_catalog

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ops" / "host" / "dispatch-sydney-morning.sh"
CRONTAB = ROOT / "ops" / "host" / "crontab"
RUNBOOK = ROOT / "docs" / "runbooks" / "host-dispatch.md"
WORKFLOW = ROOT / ".github" / "workflows" / "hybrid-sydney-morning.yml"
TOKEN = "ghp_HOSTDISPATCHTESTTOKEN"


def _crontab_job() -> list[str]:
    jobs = []
    for line in CRONTAB.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" in stripped.split()[0]:
            continue
        jobs.append(stripped)
    return jobs


def test_crontab_uses_catalog_sydney_morning_anchor() -> None:
    routine = load_catalog(ROOT).by_id()["grok.sydney_morning"]
    assert routine.timezone == "Australia/Sydney"
    assert (routine.local_time.hour, routine.local_time.minute) == (6, 30)
    assert list(routine.weekdays) == ["Mon", "Tue", "Wed", "Thu", "Fri"]
    text = CRONTAB.read_text(encoding="utf-8")
    assert "CRON_TZ=Australia/Sydney" in text
    assert "does not honour CRON_TZ" in text
    assert "MM_HOST_TOKEN_FILE=/etc/market-memory/github-dispatch.token" in text
    assert "MM_HOST_LOG=/var/log/market-memory/sydney-morning-dispatch.log" in text
    jobs = _crontab_job()
    assert len(jobs) == 1
    fields = jobs[0].split()
    assert int(fields[0]) == routine.local_time.minute
    assert int(fields[1]) == routine.local_time.hour
    assert fields[2:4] == ["*", "*"]
    assert fields[4] == "1-5"
    assert fields[5].endswith("dispatch-sydney-morning.sh")
    assert "30 20" not in text
    assert "30 19" not in text
    assert "30 22" not in text


def test_wall_clock_holds_across_4_oct_2026_dst_start() -> None:
    """Fri 2 Oct is AEST. Mon 5 Oct is AEDT. Both are 06:30 Sydney."""
    tz = ZoneInfo("Australia/Sydney")
    friday = datetime(2026, 10, 2, 6, 30, tzinfo=tz)
    monday = datetime(2026, 10, 5, 6, 30, tzinfo=tz)
    assert friday.isoweekday() == 5
    assert monday.isoweekday() == 1
    assert friday.strftime("%H:%M") == monday.strftime("%H:%M") == "06:30"
    assert friday.utcoffset() == timedelta(hours=10)
    assert monday.utcoffset() == timedelta(hours=11)
    assert friday.astimezone(timezone.utc) == datetime(2026, 10, 1, 20, 30, tzinfo=timezone.utc)
    assert monday.astimezone(timezone.utc) == datetime(2026, 10, 4, 19, 30, tzinfo=timezone.utc)
    # The host expression is the wall clock, not either UTC hour.
    assert "30 6 * * 1-5" in CRONTAB.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "30 20 * * 0-4"' in workflow
    assert 'cron: "30 22 * * 0-4"' in workflow


def test_runbook_matches_merged_124_workflow_dispatch() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "repository_dispatch" in text
    assert "#124" in text or "124" in text
    assert "merged" in text
    assert "unmerged" not in text.lower()
    assert "hybrid-sydney-morning.yml" in text
    assert "i_mean_it_deliver" in text
    assert "CRON_TZ=Australia/Sydney" in text
    assert "06:30" in text
    assert "0600" in text or "600" in text
    assert "--dry-run" in text
    assert "already_delivered" in text
    assert '30 20 * * 0-4' in text
    assert '30 22 * * 0-4' in text
    assert "Fri 2 Oct 2026" in text
    assert "Mon 5 Oct 2026" in text
    assert "fine-grained" in text
    assert "Actions" in text
    assert "vixie" in text
    assert "does not honour `CRON_TZ`" in text
    assert "timedatectl show -p Timezone --value" in text
    assert 'test "$tz" = "Australia/Sydney"' in text
    assert "env -i" in text
    assert "MM_HOST_TOKEN_FILE=/etc/market-memory/github-dispatch.token" in text
    assert "MM_HOST_LOG=/var/log/market-memory/sydney-morning-dispatch.log" in text
    assert "/var/log/market-memory" in text
    assert "90 days" in text
    assert "12 Oct 2026" in text
    assert "$HOME/mm-host" not in text
    script = SCRIPT.read_text(encoding="utf-8")
    assert "workflow_dispatch" in script
    assert "/actions/workflows/${WORKFLOW}/dispatches" in script
    assert script.count("repository_dispatch") == 1
    assert "hybrid-sydney-morning.yml" in script
    assert 'MM_HOST_RETRY_SLEEP:-60' in script
    assert "i_mean_it_deliver" in script
    # Actions cron schedules are untouched by this change: both lines remain once.
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('cron: "30 20 * * 0-4"') == 1
    assert workflow.count('cron: "30 22 * * 0-4"') == 1


def _write_token(path: Path, mode: int) -> None:
    path.write_text(TOKEN + "\n", encoding="utf-8")
    os.chmod(path, mode)


def _fake_curl(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$@" >> "$MM_FAKE_CURL_LOG"
for arg in "$@"; do
  if [[ "$arg" == @* ]]; then
    cp "${arg#@}" "$MM_FAKE_CURL_HEADER"
  fi
done
echo x >> "$MM_FAKE_CURL_COUNT"
n=$(wc -l < "$MM_FAKE_CURL_COUNT")
code="$(sed -n "${n}p" "$MM_FAKE_CURL_CODES")"
if [[ "$code" == network:* ]]; then
  exit "${code#network:}"
fi
printf '%s' "$code"
""",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _run(tmp_path: Path, codes: list[str], *, extra_env: dict[str, str] | None = None, args: list[str] | None = None, mode: int = 0o600):
    token = tmp_path / "token"
    _write_token(token, mode)
    fake = tmp_path / "curl"
    _fake_curl(fake)
    log = tmp_path / "dispatch.log"
    env = os.environ.copy()
    env.update(
        {
            "MM_HOST_TOKEN_FILE": str(token),
            "MM_HOST_LOG": str(log),
            "MM_HOST_CURL": str(fake),
            "MM_HOST_RETRY_SLEEP": "0",
            "MM_FAKE_CURL_LOG": str(tmp_path / "curl-args.log"),
            "MM_FAKE_CURL_HEADER": str(tmp_path / "header"),
            "MM_FAKE_CURL_COUNT": str(tmp_path / "count"),
            "MM_FAKE_CURL_CODES": str(tmp_path / "codes"),
        }
    )
    (tmp_path / "codes").write_text("\n".join(codes) + "\n", encoding="utf-8")
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        ["bash", str(SCRIPT), *(args or [])],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    logged = log.read_text(encoding="utf-8") if log.is_file() else ""
    header = (tmp_path / "header").read_text(encoding="utf-8") if (tmp_path / "header").is_file() else ""
    count = (tmp_path / "count").read_text(encoding="utf-8").count("x") if (tmp_path / "count").is_file() else 0
    blob = proc.stdout + proc.stderr + logged
    return proc, logged, header, count, blob


def test_dispatch_script_syntax() -> None:
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_dry_run_does_not_post_or_print_token(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["204"], args=["--dry-run"])
    assert proc.returncode == 0
    assert count == 0
    assert "dry-run" in logged
    assert "workflow_dispatch" in proc.stdout
    assert "i_mean_it_deliver=true" in proc.stdout
    assert TOKEN not in blob


def test_success_logs_status_and_hides_token(tmp_path: Path) -> None:
    proc, logged, header, count, blob = _run(tmp_path, ["204"])
    assert proc.returncode == 0
    assert count == 1
    assert "result=http:204" in logged
    assert "event=workflow_dispatch" in logged
    assert "Authorization: Bearer " + TOKEN in header
    assert TOKEN not in blob


def test_non_2xx_exits_nonzero_without_retry(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["422"])
    assert proc.returncode != 0
    assert count == 1
    assert "result=http:422" in logged
    assert "attempt=2" not in logged
    assert TOKEN not in blob


def test_5xx_retries_once_then_succeeds(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["503", "204"])
    assert proc.returncode == 0
    assert count == 2
    assert "attempt=1" in logged and "result=http:503" in logged
    assert "attempt=2" in logged and "result=http:204" in logged
    assert TOKEN not in blob


def test_network_error_retries_once(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["network:28", "204"])
    assert proc.returncode == 0
    assert count == 2
    assert "result=network:28" in logged
    assert "result=http:204" in logged
    assert TOKEN not in blob


def test_second_network_error_exits_nonzero(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["network:7", "network:7"])
    assert proc.returncode != 0
    assert count == 2
    assert logged.count("result=network:7") == 2
    assert TOKEN not in blob


def test_bad_token_mode_refuses_before_curl(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["204"], mode=0o644)
    assert proc.returncode != 0
    assert count == 0
    assert "token_file_mode=644" in logged
    assert TOKEN not in blob


def test_unwritable_log_still_posts_and_retries(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    blocked.chmod(0o555)
    log = blocked / "nested" / "dispatch.log"
    try:
        proc, logged, _header, count, blob = _run(
            tmp_path,
            ["503", "204"],
            extra_env={"MM_HOST_LOG": str(log)},
        )
    finally:
        blocked.chmod(0o755)
    assert proc.returncode == 0
    assert count == 2
    assert not log.exists()
    assert logged == ""
    assert "attempt=1" in proc.stderr and "result=http:503" in proc.stderr
    assert "attempt=2" in proc.stderr and "result=http:204" in proc.stderr
    assert TOKEN not in blob


def test_unwritable_log_still_reports_refusal(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    blocked.chmod(0o555)
    log = blocked / "nested" / "dispatch.log"
    try:
        proc, logged, _header, count, blob = _run(
            tmp_path,
            ["204"],
            mode=0o644,
            extra_env={"MM_HOST_LOG": str(log)},
        )
    finally:
        blocked.chmod(0o755)
    assert proc.returncode != 0
    assert count == 0
    assert logged == ""
    assert "refused token_file_mode=644" in proc.stderr
    assert TOKEN not in blob


def test_other_workflow_is_refused(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(
        tmp_path,
        ["204"],
        extra_env={"MM_HOST_WORKFLOW": "promote-gate.yml"},
    )
    assert proc.returncode != 0
    assert count == 0
    assert "workflow_not_allowlisted" in logged
    assert TOKEN not in blob
