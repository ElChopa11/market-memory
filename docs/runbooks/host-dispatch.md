# External host: Sydney Morning dispatch

Paper only. The host is a clock. It only calls the GitHub API. Fetch, brief, and the Principal DM stay in `.github/workflows/hybrid-sydney-morning.yml`. This runbook does not add a repository secret, does not change that workflow, and does not send to the Hive group.

The catalog anchor is `grok.sydney_morning` in `config/schedules/routines.yaml`: `timezone: Australia/Sydney`, `local_time: "06:30"`, weekdays Mon–Fri. The host crontab uses that wall time. It is not a guessed UTC hour.

## Dispatch mechanism

`workflow_dispatch` on workflow file `hybrid-sydney-morning.yml`.

[#124](https://github.com/ElChopa11/market-memory/pull/124) is merged on `main`. It strips `workflow_dispatch` from `promote-gate.yml` and allowlists that trigger to `hybrid-sydney-morning.yml` only (`tests/unit/test_workflow_dispatch_allowlist.py`). This host uses `workflow_dispatch`, not `repository_dispatch`. The dispatch script refuses any workflow name other than `hybrid-sydney-morning.yml`.

The script POSTs:

`POST /repos/ElChopa11/market-memory/actions/workflows/hybrid-sydney-morning.yml/dispatches`

```json
{"ref":"main","inputs":{"i_mean_it_deliver":"true"}}
```

The GitHub REST API sends workflow inputs as strings. The workflow treats boolean `true` and the string `'true'` as the deliver path. `stage1-stamp` runs on every dispatch. `brief-and-deliver` runs on this dispatch because the input is true, which is the existing fetch / brief / DM path. The schedule crons ignore the input and still deliver when they fire.

## Actions crons stay

Do not remove or edit these lines in `.github/workflows/hybrid-sydney-morning.yml`:

- `30 20 * * 0-4` — weekday 06:30 Australia/Sydney while AEST (UTC+10) is in force
- `30 22 * * 0-4` — weekday 08:30 Australia/Sydney while AEST (UTC+10) is in force

GitHub evaluates `schedule` in UTC. Sydney daylight saving starts Sunday 4 Oct 2026 (02:00 AEST becomes 03:00 AEDT, UTC+11). Those two cron lines then land an hour earlier in Sydney wall time. Leave them. The host cron is the Sydney wall-clock trigger. While AEST is in force, `30 20 * * 0-4` is the same 06:30 Sydney instant as this host. The workflow concurrency group `hybrid-sydney-morning` with `cancel-in-progress: false` queues the second run instead of cancelling it. The queued run checks out the branch tip and calls `decide_deliver` before brief or Telegram. If the first run pushed a deliver receipt for that `scheduled_anchor_ts`, the second logs `already_delivered` and does not POST. Each run still writes its own completion file. A failed send writes no receipt, so the queued run can still deliver once.

## DST wall clock

`CRON_TZ=Australia/Sydney` plus `30 6 * * 1-5` is 06:30 local on both sides of the change:

| Sydney date | Weekday | Offset | UTC instant of 06:30 local |
|---|---|---|---|
| Fri 2 Oct 2026 | Friday (cron dow 5) | AEST UTC+10 | Thu 1 Oct 2026 20:30 UTC |
| Mon 5 Oct 2026 | Monday (cron dow 1) | AEDT UTC+11 | Sun 4 Oct 2026 19:30 UTC |

The crontab expression does not change. Both dates are weekdays (`1-5`). Sunday 4 Oct is the transition and is not a host fire. `zoneinfo` on the repo's test clock shows `2026-10-02 06:30+10:00` and `2026-10-05 06:30+11:00`.

Mon 5 Oct 2026 is also NSW Labour Day (first Monday in October). The host crontab has no holiday list. That Monday matches `30 6 * * 1-5` at 06:30 Australia/Sydney, the same catalog anchor as any other Monday. The stamp, the brief, and the deliver path do not consult a public-holiday calendar.

## What the Principal does

1. **Create the host.** A small Linux VPS (Debian or Ubuntu). No trading credentials. No copy of `live.yaml` secrets. No Telegram bot token on this machine.
2. **Set timezone and NTP.**
   ```bash
   sudo timedatectl set-timezone Australia/Sydney
   sudo timedatectl set-ntp true
   timedatectl
   ```
   `Time zone: Australia/Sydney` and `NTP service: active` (or `System clock synchronized: yes`).
3. **Install cron.**
   ```bash
   sudo apt-get update
   sudo apt-get install -y cron
   sudo systemctl enable --now cron
   ```
4. **Install this repo** at `/opt/market-memory` from `main` after this pull request has merged (the stamp-row fix has to be what Actions checks out). The clone is the script and the crontab. It does not need to run `lab`.
   ```bash
   sudo mkdir -p /opt/market-memory
   sudo chown "$USER" /opt/market-memory
   git clone https://github.com/ElChopa11/market-memory.git /opt/market-memory
   ```
   If the clone path differs, edit the single path in `ops/host/crontab` and nowhere else.
5. **Create a fine-grained personal access token.** Resource owner: the account that can dispatch this repo. Repository access: **only** `ElChopa11/market-memory`. Permissions: **Actions: Read and write**. No Contents, no Secrets, no Administration, no other repositories. This token is not a GitHub Actions secret and is not committed.
6. **Write the token to a 0600 file** owned by the user that will own the crontab.
   ```bash
   sudo mkdir -p /etc/market-memory
   sudo touch /etc/market-memory/github-dispatch.token
   sudo chown "$USER" /etc/market-memory/github-dispatch.token
   chmod 600 /etc/market-memory/github-dispatch.token
   # paste the token with an editor. Do not echo it. Do not pass it on the command line.
   ```
   Confirm mode with `stat -c %a /etc/market-memory/github-dispatch.token` → `600`. The script refuses any other mode and refuses a missing or empty file.
7. **Install the crontab.** `crontab file` replaces that user's crontab. The file in the repo is the whole crontab.
   ```bash
   crontab /opt/market-memory/ops/host/crontab
   crontab -l
   ```
   The listing must show `CRON_TZ=Australia/Sydney` and `30 6 * * 1-5` running `dispatch-sydney-morning.sh`.
8. **Dry test** (no HTTP POST, no workflow run, no DM).
   ```bash
   mkdir -p "$HOME/mm-host"
   MM_HOST_TOKEN_FILE=/etc/market-memory/github-dispatch.token \
   MM_HOST_LOG="$HOME/mm-host/sydney-morning-dispatch.log" \
   /opt/market-memory/ops/host/dispatch-sydney-morning.sh --dry-run
   ```
   Stdout is the event name, workflow file, ref `main`, and `i_mean_it_deliver=true`. The log line contains `dry-run` and `http=skipped`. Neither stdout nor the log contains the token. `crontab -l` still has the real line without `--dry-run`.

A live fire is a separate step from the dry test. Run it once, on a weekday, only when you want a real Principal DM:

```bash
MM_HOST_TOKEN_FILE=/etc/market-memory/github-dispatch.token \
MM_HOST_LOG="$HOME/mm-host/sydney-morning-dispatch.log" \
/opt/market-memory/ops/host/dispatch-sydney-morning.sh
```

Success appends a log line `result=http:204` (or another HTTP 2xx). The log records the UTC timestamp, the attempt number, and the HTTP status. It does not record the token. Network errors and HTTP 5xx sleep 60 seconds and retry once. HTTP 4xx does not retry. A non-2xx exit is nonzero.

Point the installed crontab at the same log if you want the morning fire recorded there:

```
MM_HOST_LOG=/var/log/market-memory/sydney-morning-dispatch.log
```

Create that directory writable by the cron user before relying on the default path `/var/log/market-memory/sydney-morning-dispatch.log`.

## How to verify a fire from GitHub

1. Open Actions → **hybrid-sydney-morning** on `ElChopa11/market-memory`, or:
   ```bash
   gh run list --repo ElChopa11/market-memory --workflow hybrid-sydney-morning.yml --limit 5
   ```
2. The host fire shows event **`workflow_dispatch`** (not `schedule`, not `repository_dispatch`).
3. Open the run. `createdAt` / the run's start time is the Actions server time. Compare it to the host log timestamp on the `result=http:204` line (that timestamp is UTC). They should be within about a minute of each other, plus queue delay.
4. `stage1-stamp` writes a completion whose `run_id` is `actions-b1-<github run id>`. `brief-and-deliver` runs because `i_mean_it_deliver` was `true`. If a receipt for that Sydney anchor already exists, the deliver job logs `already_delivered` and does not POST.
5. The same Sydney day's Actions `schedule` runs, if they fire, are additional completion rows and a no-op DM.

Weekend live fires are the wrong test. Saturday and Sunday are not `grok.sydney_morning` weekdays, so the stamp is refused and no completion row is written.

## Completion rows (stamp-row fix this host depends on)

Commit `db3b106` replaced `ops/reports/scheduler/completions/grok.sydney_morning__20260924T203000Z.json`. The 06:30-path fire `actions-b1-36071921289` (`fired_at_ts` 2026-09-24T23:17:07Z, `delta_seconds` 10027) and the later fire `actions-b1-36078428152` (`fired_at_ts` 2026-09-25T00:38:10Z, `delta_seconds` 14890) shared one anchor-keyed file. Both statuses were `late`, and the writer replaced the file whenever the new rank was greater than or equal to the old rank. The second commit is the only blob that stayed on `main`.

New stamps are `{routine}__{anchor}__{run_id}.json`. An existing file is not rewritten. The first trigger's bytes are restored beside the legacy file as `grok.sydney_morning__20260924T203000Z__actions-b1-36071921289.json`. The legacy file remains the second trigger. The deliver receipt is still one per anchor, so the DM stays one per Sydney day.
