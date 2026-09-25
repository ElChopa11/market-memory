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
HC_URL = "https://hc-ping.example/host-secret-uuid"


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
    assert "MM_HOST_HC_URL_FILE=/etc/market-memory/healthchecks-host.url" in text
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
printf '%s\\n' "--- invocation ---" >> "$MM_FAKE_CURL_LOG"
printf '%s\\n' "$@" >> "$MM_FAKE_CURL_LOG"
prev=""
for arg in "$@"; do
  if [[ "$arg" == @* ]]; then
    cp "${arg#@}" "$MM_FAKE_CURL_HEADER"
  fi
  if [[ "$prev" == "--config" || "$prev" == "-K" ]]; then
    if [[ -n "${MM_FAKE_CURL_CONFIGS:-}" ]]; then
      printf '\\n---\\n' >> "$MM_FAKE_CURL_CONFIGS"
      cat "$arg" >> "$MM_FAKE_CURL_CONFIGS"
    fi
    # A verbose curl error names the URL. The script must discard that stderr.
    cat "$arg" >&2
  fi
  prev="$arg"
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
            "MM_FAKE_CURL_CONFIGS": str(tmp_path / "curl-configs"),
            "MM_HOST_HC_URL_FILE": str(tmp_path / "hc.url"),
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


def _write_hc(tmp_path: Path, text: str, mode: int = 0o600) -> None:
    path = tmp_path / "hc.url"
    path.write_text(text, encoding="utf-8")
    os.chmod(path, mode)


def _curl_args(tmp_path: Path) -> str:
    path = tmp_path / "curl-args.log"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _curl_configs(tmp_path: Path) -> str:
    path = tmp_path / "curl-configs"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _invocations(tmp_path: Path) -> list[str]:
    parts = _curl_args(tmp_path).split("--- invocation ---\n")
    return [part for part in parts if part.strip()]


def _assert_url_hidden(blob: str, tmp_path: Path, url: str = HC_URL) -> None:
    assert url not in blob
    assert url not in _curl_args(tmp_path)


def test_missing_hc_file_skips_ping_and_leaves_dispatch_unchanged(tmp_path: Path) -> None:
    proc, logged, _header, count, blob = _run(tmp_path, ["204"])
    assert proc.returncode == 0
    assert count == 1
    assert "result=http:204" in logged
    assert "hc=skipped" in logged
    assert "attempt=2" not in logged
    assert _curl_configs(tmp_path) == ""
    assert len(_invocations(tmp_path)) == 1
    assert "api.github.com" in _invocations(tmp_path)[0]
    _assert_url_hidden(blob, tmp_path)
    assert TOKEN not in blob


def test_empty_hc_file_skips_ping(tmp_path: Path) -> None:
    _write_hc(tmp_path, "")
    proc, logged, _header, count, blob = _run(tmp_path, ["204"])
    assert proc.returncode == 0
    assert count == 1
    assert "result=http:204" in logged
    assert "hc=skipped" in logged
    assert _curl_configs(tmp_path) == ""
    _assert_url_hidden(blob, tmp_path)


def test_whitespace_hc_file_skips_ping(tmp_path: Path) -> None:
    _write_hc(tmp_path, "\n  \n")
    proc, logged, _header, count, blob = _run(tmp_path, ["204"])
    assert proc.returncode == 0
    assert count == 1
    assert "hc=skipped" in logged
    assert _curl_configs(tmp_path) == ""
    _assert_url_hidden(blob, tmp_path)


def test_success_ping_after_2xx_hides_url(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["204", "200"])
    assert proc.returncode == 0
    assert count == 2
    assert "result=http:204" in logged
    assert "hc=200" in logged
    assert "attempt=2" not in logged
    invocations = _invocations(tmp_path)
    assert len(invocations) == 2
    assert "api.github.com" in invocations[0]
    assert "--config" not in invocations[0]
    assert "--config" in invocations[1]
    assert "--max-time" in invocations[1]
    assert "\n10\n" in invocations[1]
    assert "--proto" in invocations[1]
    assert "=https" in invocations[1]
    assert "i_mean_it_deliver" not in invocations[1]
    configs = _curl_configs(tmp_path)
    assert f'url = "{HC_URL}"' in configs
    assert "/fail" not in configs
    _assert_url_hidden(blob, tmp_path)
    assert TOKEN not in blob


def test_4xx_pings_fail_and_exits_nonzero(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["422", "200"])
    assert proc.returncode == 1
    assert count == 2
    assert "result=http:422" in logged
    assert "hc=200" in logged
    assert "attempt=2" not in logged
    assert f'url = "{HC_URL}/fail"' in _curl_configs(tmp_path)
    invocations = _invocations(tmp_path)
    assert "api.github.com" in invocations[0]
    assert "--config" in invocations[1]
    _assert_url_hidden(blob, tmp_path)


def test_4xx_fail_url_keeps_query(tmp_path: Path) -> None:
    url = HC_URL + "?rid=1"
    _write_hc(tmp_path, url + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["422", "200"])
    assert proc.returncode == 1
    assert count == 2
    assert f'url = "{HC_URL}/fail?rid=1"' in _curl_configs(tmp_path)
    assert url not in blob
    assert url not in _curl_args(tmp_path)


def test_ping_failure_does_not_change_success_exit_or_repost(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["204", "network:28"])
    assert proc.returncode == 0
    assert count == 2
    assert "result=http:204" in logged
    assert "hc=network:28" in logged
    assert "attempt=2" not in logged
    assert "dispatch failed" not in proc.stderr
    assert len(_invocations(tmp_path)) == 2
    assert "api.github.com" in _invocations(tmp_path)[0]
    assert "--config" in _invocations(tmp_path)[1]
    _assert_url_hidden(blob, tmp_path)


def test_ping_failure_after_4xx_keeps_nonzero_exit(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["422", "network:7"])
    assert proc.returncode == 1
    assert count == 2
    assert "result=http:422" in logged
    assert "hc=network:7" in logged
    assert "attempt=2" not in logged
    _assert_url_hidden(blob, tmp_path)


def test_dry_run_does_not_ping_when_url_file_exists(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["204"], args=["--dry-run"])
    assert proc.returncode == 0
    assert count == 0
    assert "dry-run" in logged
    assert "http=skipped" in logged
    assert "hc=skipped" in logged
    assert _curl_configs(tmp_path) == ""
    assert _curl_args(tmp_path) == ""
    _assert_url_hidden(blob, tmp_path)
    assert HC_URL not in proc.stdout
    assert HC_URL not in proc.stderr


def test_non_https_url_is_not_pinged(tmp_path: Path) -> None:
    insecure = "http://hc-ping.example/host-secret-uuid"
    _write_hc(tmp_path, insecure + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["204"])
    assert proc.returncode == 0
    assert count == 1
    assert "result=http:204" in logged
    assert "hc=bad_url" in logged
    assert insecure not in blob
    assert insecure not in _curl_args(tmp_path)
    assert _curl_configs(tmp_path) == ""


def test_loose_url_file_mode_still_pings(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n", mode=0o644)
    proc, logged, _header, count, blob = _run(tmp_path, ["204", "200"])
    assert proc.returncode == 0
    assert count == 2
    assert "hc=200" in logged
    assert "refused" not in logged
    _assert_url_hidden(blob, tmp_path)


def test_retry_pings_success_only_after_final_2xx(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["503", "204", "200"])
    assert proc.returncode == 0
    assert count == 3
    lines = [line for line in logged.splitlines() if line.strip()]
    assert "attempt=1" in lines[0] and "result=http:503" in lines[0]
    assert "hc=" not in lines[0]
    assert "attempt=2" in lines[1] and "result=http:204" in lines[1] and "hc=200" in lines[1]
    invocations = _invocations(tmp_path)
    assert len(invocations) == 3
    assert "api.github.com" in invocations[0]
    assert "api.github.com" in invocations[1]
    assert "--config" not in invocations[0]
    assert "--config" not in invocations[1]
    assert "--config" in invocations[2]
    configs = _curl_configs(tmp_path)
    assert f'url = "{HC_URL}"' in configs
    assert "/fail" not in configs
    _assert_url_hidden(blob, tmp_path)


def test_retry_then_non_2xx_pings_fail(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["503", "503", "200"])
    assert proc.returncode == 1
    assert count == 3
    lines = [line for line in logged.splitlines() if line.strip()]
    assert "hc=" not in lines[0]
    assert "attempt=2" in lines[1] and "result=http:503" in lines[1] and "hc=200" in lines[1]
    assert f'url = "{HC_URL}/fail"' in _curl_configs(tmp_path)
    _assert_url_hidden(blob, tmp_path)


def test_refused_dispatch_does_not_ping(tmp_path: Path) -> None:
    _write_hc(tmp_path, HC_URL + "\n")
    proc, logged, _header, count, blob = _run(tmp_path, ["204"], mode=0o644)
    assert proc.returncode != 0
    assert count == 0
    assert "token_file_mode=644" in logged
    assert "hc=" not in logged
    assert _curl_configs(tmp_path) == ""
    _assert_url_hidden(blob, tmp_path)


def test_runbook_documents_optional_host_healthchecks() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "30 6 * * 1-5" in text
    assert "Australia/Sydney" in text
    assert "15 minutes" in text
    assert "healthchecks-host.url" in text
    assert "MM_HOST_HC_URL_FILE=/etc/market-memory/healthchecks-host.url" in text
    assert "hc=skipped" in text
    assert "git -C /opt/market-memory pull" in text
    assert "crontab /opt/market-memory/ops/host/crontab" in text
    assert "Do not `echo` the URL" in text
    assert "/fail" in text
    assert "#129" in text
    assert "HEALTHCHECKS_PING_URL" in text
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'MM_HOST_HC_URL_FILE:-/etc/market-memory/healthchecks-host.url' in script
    assert "HC_MAX_TIME=10" in script
    assert "--proto '=https'" in script
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert workflow.count('cron: "30 20 * * 0-4"') == 1
    assert workflow.count('cron: "30 22 * * 0-4"') == 1
