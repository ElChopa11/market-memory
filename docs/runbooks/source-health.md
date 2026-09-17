# Source health / data-quality report

Standing Data & Market Memory Desk product. Read-only. **Not a market brief.**

Plan: [ops/plans/IMP-003-source-health.md](../../ops/plans/IMP-003-source-health.md).

## Command

```bash
uv run lab data source-health
# alias:
uv run lab dq report
```

Writes `ops/reports/source-health/YYYY-MM-DD.md` (UTC date of generation) plus a `.sha256` sidecar. Prints JSON (`path`, `overall`, `content_hash`, per-source status). Does not print secrets, DSN passwords, or market prints.

| Flag | Effect |
|---|---|
| `--repo-root` | Where `config/` lives (default `.`) |
| `--out` | Root to write `ops/reports/` (default `--repo-root`) |
| `--no-db` | Skip Postgres reachability (Pulse can still run without indexing) |
| `--dsn` | Postgres DSN (never printed) |
| `--timeout` | HTTP/DB timeout seconds (default 8) |
| `--as-of` | UTC instant for `generated_at` / filename date |

## What it covers

Configured sources used by Market Memory and Pulse, always listed even when down:

| Source | Pulse role | Probe |
|---|---|---|
| Hyperliquid public `/info` | required | allowlisted `meta`; local refuse of forbidden types |
| CoinGecko | optional | `/api/v3/ping` (no prices) |
| Stooq | optional | one canary CSV; failure class only; no Close values |
| FRED | optional | missing `FRED_API_KEY` → `unavailable`; else series `limit=1` without printing the yield |
| `config/briefing/calendar.yaml` | required | file present + YAML parse |
| Postgres | optional for Pulse | `SELECT 1` + last `observation.ingested_at` |
| Object store | n/a for Pulse | env completeness; HeadBucket / filesystem path if configured |

Status: `ok | degraded | unavailable`. Overall is `unavailable` if any **Pulse-required** source is down; otherwise `degraded` if any row is not ok.

## Rules

- Never invent or copy prints/quotes/yields into the artifact.
- Never print secrets. Missing env is a status, not a crash.
- Hyperliquid stays on the public `/info` allowlist. Forbidden user/wallet types are refused locally (no HTTP).
- Do not treat this report as a Quant verdict or a trading decision.

See also: [ingest runbook](ingest.md), [Market Pulse runbook](market-pulse.md).
