# Source health / data-quality report

Standing Data & Market Memory Desk product. Read-only. **Not a market brief.**

Plan: [ops/plans/IMP-003-source-health.md](../../ops/plans/IMP-003-source-health.md). Hardening: [ops/plans/IMP-004-pulse-source-hardening.md](../../ops/plans/IMP-004-pulse-source-hardening.md).

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
| `--timeout` | HTTP/DB timeout seconds (default 8; aligned with Pulse live GET) |
| `--as-of` | UTC instant for `generated_at` / filename date |

## What it covers

Configured sources used by Market Memory and Pulse, always listed even when down:

| Source | Pulse role | Probe |
|---|---|---|
| Hyperliquid public `/info` | required | allowlisted `meta`; local refuse of forbidden types |
| Hyperliquid structure | optional | allowlisted `l2Book` (shape only; no book copied) |
| CoinGecko | optional | `/api/v3/ping` (no prices); bounded GET retry on timeout/5xx/429 |
| Binance public | optional | `/api/v3/ping` (no prices) |
| Stooq | optional | one canary CSV; `http_404` / `timeout` / `http_5xx` / `parse_error`; no Close values; **no scrape fallback** |
| FRED | optional | missing `FRED_API_KEY` → `unavailable` + `missing_env`; else series `limit=1` without printing the yield |
| Polygon | optional | missing `POLYGON_API_KEY` → `unavailable` + `missing_env`; else reference tickers `limit=1` without OHLCV |
| `config/briefing/calendar.yaml` | required | file present + YAML parse |
| Postgres | optional for Pulse | `SELECT 1` + last `observation.ingested_at` |
| Object store | n/a for Pulse | env completeness; HeadBucket / filesystem path if configured |

Status: `ok | degraded | unavailable`. Overall is `unavailable` if any **Pulse-required** source is down; otherwise `degraded` if any row is not ok.

## Hardened failure modes

Same GET helper as Pulse (`mm_common.http`): default **8s** timeout; **one** retry on `timeout` / `unreachable` / `429` / `http_5xx` only.

| Class | Typical cause | Retry | Operator action |
|---|---|---|---|
| `http_404` | Stooq canary CSV 404 (common from cloud IPs) | no | Leave unavailable. Do **not** scrape HTML or switch hosts. |
| `timeout` / `unreachable` | Slow or blocked egress | once | Re-run later; check network. Still honest if still down. |
| `http_5xx` / `rate_limited` | Upstream | once | Re-run; do not invent prints. |
| `tos_or_blocked` | HTTP 401/403/451 | no | Stop. Do not work around ToS. |
| `parse_error` | Empty / N/D CSV or empty FRED observations | no | Treat as unavailable/degraded; no Close/yield copied. |
| `missing_env` | `FRED_API_KEY`, `POLYGON_API_KEY`, `POSTGRES_DSN`, MinIO/S3 incomplete | no | Set env locally or in CI secrets. Never commit. See [market-pulse.md](market-pulse.md#fred_api_key-operators) and [polygon-hl-structure.md](polygon-hl-structure.md). |
| `skipped` | `--no-db` | n/a | Expected; Pulse can run without indexing. |

IMP-003 sample [`ops/reports/source-health/2026-09-17.md`](../../ops/reports/source-health/2026-09-17.md) is historical (`http_error` for Stooq 404). New runs emit `http_404`.

## Rules

- Never invent or copy prints/quotes/yields into the artifact.
- Never print secrets. Missing env is a status, not a crash. Query-string `api_key=` is redacted if it appears in exception text.
- Hyperliquid stays on the public `/info` allowlist. Forbidden user/wallet types are refused locally (no HTTP).
- Do not treat this report as a Quant verdict or a trading decision.

See also: [ingest runbook](ingest.md), [Market Pulse runbook](market-pulse.md), [Polygon + HL structure](polygon-hl-structure.md). Plan: [ops/plans/IMP-004-pulse-source-hardening.md](../../ops/plans/IMP-004-pulse-source-hardening.md).
