# Phase 3 — Market Pulse (US session briefs)

Australia/Sydney is the ops timezone for humans. **US session wall-clock is `America/New_York`.** Fire times are converted with `zoneinfo` (DST-correct). Every timestamp stored in Postgres is `timestamptz` UTC. Point-in-time knowledge uses `ingested_at`, never `published_at` alone.

This runbook does **not** enable live trading, wallets, or signing. Briefing is read-only.

## What it produces

| Mode | Command | Artifact |
|---|---|---|
| US pre-open | `lab brief preopen` | `briefs/YYYY/MM/DD/preopen.md` |
| US close | `lab brief close` | `briefs/YYYY/MM/DD/close.md` |
| Intraday alerts | `lab brief alert-check` | `briefs/YYYY/MM/DD/alert.md` **only if a numeric threshold is crossed** |

Alerts **never push** if `config/briefing/alerts.yaml` is missing, `require_threshold_config` is true without numeric thresholds, or no threshold is crossed. There is no free-text commentary path.

## Frozen fixture (deterministic hash)

CI and local tests generate briefs from `tests/fixtures/briefing/frozen_day.json` (session date **2026-03-10**). The pre-open and close SHA-256 hashes are pinned:

```bash
uv run lab brief preopen \
  --fixture tests/fixtures/briefing/frozen_day.json \
  --repo-root . \
  --out /tmp/market-pulse \
  --no-db

# content_hash must match tests/fixtures/briefing/frozen_preopen.sha256
```

Same for `lab brief close`. Do not edit the golden markdown/`sha256` files unless the renderer change is intentional; update both together.

## Live / operator path

```bash
docker compose up -d
uv sync --all-packages
uv run lab migrate

# 1. Ingest Hyperliquid public info into Market Memory (crypto/HL source of truth)
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
# or: uv run lab ingest --window 7d

# 2. Generate a brief. Without --fixture, HL conditions come from what_did_we_know(as_of).
#    Macro defaults to mode: off (data_quality=partial) unless you pass --fixture
#    or set config/briefing/macro.yaml mode: fixture|live.
uv run lab brief preopen --as-of 2026-03-10T12:00:00Z
uv run lab brief close --as-of 2026-03-10T20:15:00Z
uv run lab brief alert-check --as-of 2026-03-10T14:00:00Z

# Worker: print DST-aware fire times, or generate one shot
uv run briefing-worker next --from 2026-03-06T00:00:00Z --days 5
uv run briefing-worker once --kind preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
```

Schedule (weekdays, `America/New_York` wall clock):

- Pre-open: **08:00**
- Close: **16:15**

Those instants shift by one UTC hour across US DST. The fixture test covers the 2026-03-08 spring-forward (Friday 08:00 EST = 13:00 UTC; Monday 08:00 EDT = 12:00 UTC).

## Macro / calendar sources

- **Fixture** (tests + default deterministic path): JSON/YAML, no network.
- **Live** (opt-in in `config/briefing/macro.yaml`): Stooq public CSV, FRED (key from `FRED_API_KEY`), CoinGecko public price. Missing keys or HTTP errors set `data_quality=partial` and keep going. **Never commit secrets.**
- Calendar is `config/briefing/calendar.yaml` (fixture + pluggable later).

## Config that must stay true

- `config/briefing/alerts.yaml` → `require_threshold_config: true` with numeric thresholds per enabled type.
- `config/schedules/market-pulse.yaml` → timezones `America/New_York` + `Australia/Sydney`.
- No execution, signing, wallets, or risk-service calls from briefing.

## Optional DB index

If Postgres is up and you omit `--no-db`, a `brief` row is written (kind, session_date, content_hash, artifact path). Markdown under `briefs/` remains the human artifact. Generated dated files are gitignored; keep the runbook and fixtures in git.
