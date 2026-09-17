# Phase 3 Market Pulse (US session briefs) — Principal Phase 2 pre-market DoD

Australia/Sydney is the ops timezone for humans. **US session wall-clock is `America/New_York`.** Fire times are converted with `zoneinfo` (DST-correct). Every timestamp stored in Postgres is `timestamptz` UTC. Point-in-time knowledge uses `ingested_at`, never `published_at` alone.

This runbook does **not** enable live trading, wallets, or signing. Briefing is read-only.

Plan: [ops/plans/IMP-002-us-market-pulse.md](../../ops/plans/IMP-002-us-market-pulse.md).

## What it produces

| Mode | Command | Artifact |
|---|---|---|
| US pre-market | `lab brief preopen` | **DoD:** `briefs/YYYY-MM-DD/us-pre-market.md` **and** legacy `briefs/YYYY/MM/DD/preopen.md` (identical bytes) |
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
# writes both /tmp/market-pulse/briefs/2026-03-10/us-pre-market.md
# and /tmp/market-pulse/briefs/2026/03/10/preopen.md
```

Same for `lab brief close`. Do not edit the golden markdown/`sha256` files unless the renderer change is intentional; update both together.

## Live / operator path

```bash
docker compose up -d
uv sync --all-packages
uv run lab migrate

# 1. Ingest Hyperliquid public info into Market Memory (preferred HL source of truth)
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
# or: uv run lab ingest --window 7d

# 2. Fixture brief (deterministic)
uv run lab brief preopen --as-of 2026-03-10T12:00:00Z --fixture tests/fixtures/briefing/frozen_day.json --no-db

# 3. Live public slice (Principal Phase 2). Missing keys → unavailable/partial; never invented.
#    Uses Stooq + CoinGecko (no key), FRED if FRED_API_KEY is set, HL public /info allowlist.
uv run lab brief preopen --live --no-db
```

Without `--fixture` and without `--live`, HL conditions come from `what_did_we_know(as_of)` when Postgres is available. Macro defaults to `mode: off` (`unavailable`) unless you pass `--fixture`, `--live`, or set `config/briefing/macro.yaml` mode.

```bash
uv run lab brief close --as-of 2026-03-10T20:15:00Z
uv run lab brief alert-check --as-of 2026-03-10T14:00:00Z

uv run briefing-worker next --from 2026-03-06T00:00:00Z --days 5
uv run briefing-worker once --kind preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
```

Schedule (weekdays, `America/New_York` wall clock):

- Pre-open: **08:00**
- Close: **16:15**

Those instants shift by one UTC hour across US DST. Tests cover the 2026-03-08 spring-forward and 2026-11-01 fall-back.

## Macro / calendar sources

- **Fixture** (tests + default deterministic path): JSON/YAML, no network.
- **Live** (`--live` or `config/briefing/macro.yaml` mode: live): Stooq public CSV, FRED (key from `FRED_API_KEY`), CoinGecko public price. Missing keys or HTTP errors set `unavailable`/`partial` and keep going. **Never invent missing prints. Never commit secrets.**
- Calendar is `config/briefing/calendar.yaml` (the approved attributable source). There is no live calendar API; an empty window is printed honestly.

Every market-data section has an as-of timestamp. Pulse display quality is `fresh | stale | partial | unavailable` (`ok` maps to `fresh` in markdown). Snapshot HL fields label capture/`ingested_at`; they do not disguise capture time as exchange `market_time`.

## Config that must stay true

- `config/briefing/alerts.yaml` → `require_threshold_config: true` with numeric thresholds per enabled type.
- `config/schedules/market-pulse.yaml` → timezones `America/New_York` + `Australia/Sydney`.
- No execution, signing, wallets, or risk-service calls from briefing.
- Pre-market footer is informational only (no decision / no order intent).

## Optional DB index

If Postgres is up and you omit `--no-db`, a `brief` row is written (kind, session_date, content_hash, artifact path). Markdown under `briefs/` remains the human artifact. Generated dated files are gitignored except an explicit committed sample on the DoD path.
