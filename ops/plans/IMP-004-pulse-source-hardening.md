# PLAN — IMP-004 Pulse source hardening

**Report status:** PR READY  
**Owner:** Don/Data+Macro (Data & Market Memory Desk + Macro & Cross-Asset Desk)  
**Scope:** harden read-only Pulse + source-health clients for Stooq and FRED (shared GET helper). Clearer failure classes, bounded idempotent retries, operator notes. No orders, wallets, live keys in git, Quant Board, watchlist recommendation loops, or risk/execution services.

## Why

IMP-002’s US pre-market brief and IMP-003’s standing source-health report both observed **honest unavailability**: Stooq canary/CSV HTTP 404 (and timeouts from some networks), FRED `missing_env` without `FRED_API_KEY`. Operators needed a closed error-class vocabulary, safer retries/timeouts, and runbook steps — without inventing prints, scraping around Stooq ToS, or committing secrets.

IMP-003 classified Stooq 404 as generic `http_error`. This item splits 404 / 5xx / timeout and documents that 404 is terminal.

## Path choice

| Role | Path |
|---|---|
| Shared GET + classification | `packages/common/src/mm_common/http.py` (used by briefing + source_health) |
| Pulse live fetchers | `packages/briefing/src/mm_briefing/fetchers.py` |
| Source-health probes | `packages/source_health/src/mm_source_health/probes.py` |
| Operator notes | `docs/runbooks/market-pulse.md`, `docs/runbooks/source-health.md` |
| Dual-write briefs | unchanged (`briefs/YYYY-MM-DD/us-pre-market.md` + legacy `preopen.md`) |

Do **not** fork a second HTTP stack. Do **not** add alternate Stooq hosts, HTML scrapers, or Yahoo/investing.com fallbacks.

## Error classes (closed vocabulary)

| Class | Meaning | Retry? |
|---|---|---|
| `none` | HTTP 200 + parse ok | n/a |
| `timeout` | connect/read timeout | yes (once) |
| `unreachable` | connect refused / DNS | yes (once) |
| `http_404` | HTTP 404 (Stooq-from-cloud is a known case) | **no** |
| `http_5xx` | HTTP 5xx | yes (once) |
| `rate_limited` | HTTP 429 | yes (once) |
| `tos_or_blocked` | HTTP 401 / 403 / 451 | **no** |
| `http_error` | other 4xx | **no** |
| `parse_error` | body empty, N/D, or unparseable | **no** |
| `missing_env` | required env absent (`FRED_API_KEY`, DSN, object-store) | **no** |

Bounded GET: **max 2 attempts** (one retry), backoff 0.25s × attempt. Default timeout **8s** (Pulse live aligned with source-health; previously Pulse used 20s).

## FRED

- Key remains env-only (`FRED_API_KEY`). Never written to git, reports, or brief `source_url`.
- Missing key → `unavailable` + `error_class=missing_env` + operator hint (local `.env` / CI repository secrets).
- Query-string `api_key=` is redacted if it ever appears in exception text.

## Tests

Classification unit tests (404 terminal, 5xx/timeout retry once then fail, 503 then 200 succeeds). Pulse notes include `error_class`. FRED missing-env copy names the env and forbids committing it. Adversarial: no Stooq HTML scrape URLs; no secrets in notes; no Close/yield prints in source-health.

Frozen fixture hashes stay pinned (live footer pointer is live-macro only).

## Non-goals

Paid-data purchases; committing `FRED_API_KEY`; Stooq ToS-violating scrape workarounds; Quant Board; watchlist recommendation loops; execution; `live.yaml`; risk limits; post-IPO reclaim product; universe membership rename (IMP-005).

## Limitations

- Stooq 404 from cloud IPs remains unavailable. Hardening classifies it; it does not fetch quotes another way.
- FRED without a key remains unavailable. Operators must set the env themselves.
- CoinGecko/Stooq/FRED are still not written into Market Memory.
- Committed IMP-003 sample `ops/reports/source-health/2026-09-17.md` is historical evidence (`http_error` for 404). New runs emit `http_404`.
