# PLAN — IMP-003 Standing data-quality / source-health report

**Report status:** PR READY  
**Owner:** Don/Data (Data & Market Memory Desk)  
**Scope:** read-only source-health / data-quality report for configured Market Memory and Pulse sources. No orders, wallets, live keys in git, Quant Board changes, watchlist MAKE/active-call loops, or risk/execution services.

ID note: IMP-001’s plan mentioned “QUANT pack rewrite (IMP-003)” as a **non-goal placeholder**. Principal assigned **IMP-003** to this Data desk product. QUANT pack rewrite stays a Gap.

## Why

IMP-002’s US pre-market brief ran `data_quality=partial` with Stooq and FRED honestly unavailable. Desk charters already name a standing DQ / source-health artifact; no generator existed. This is P1 reliability and auditability — not a research call loop.

## Path choice

| Role | Path |
|---|---|
| DoD / canonical artifact | `ops/reports/source-health/YYYY-MM-DD.md` |
| Package | `packages/source_health` (`mm_source_health`) |
| Command | `lab data source-health` (alias: `lab dq report`) |

`ops/reports/` is the Data desk standing product (ops cadence, not a thesis workspace). Dated files are gitignored except README + one committed sample. Filename date is the UTC calendar date of generation.

Not `research/data-quality/`: that tree is thesis-scoped. Not `briefs/`: that is Macro Pulse output and would mix health with market copy.

## Reuse (do not fork a briefing stack)

- HL allowlist client: `mm_ingest.hl_info.HyperliquidInfoClient` — public `/info` only
- Ingest URL: `config/ingest.yaml` `info_url`
- Macro endpoints: `config/briefing/macro.yaml` live.* (inventory even when `mode: off`)
- Calendar: `config/briefing/calendar.yaml` as a local file (no live calendar API)
- Postgres: `mm_memory.db` (reachability + last `observation.ingested_at` when schema exists)
- Object store: `object_store_from_env` (env completeness + ping if configured)
- Knowledge clock: last success from `ingested_at` / this probe’s capture time — never `published_at` / `market_time` as “what we knew”

Do **not** import `LiveMacroFetcher` or render Pulse markdown. This report is health/provenance. It never copies prints, yields, or quotes into the artifact.

## Sources (configured inventory — always listed)

| Source id | Pulse role | Probe | Credentials |
|---|---|---|---|
| `hyperliquid.info` | required | POST allowlisted `meta`; local refuse of forbidden types | none (public `/info`) |
| `coingecko` | optional | GET `/api/v3/ping` (no price payload in the report) | none |
| `stooq` | optional | one canary CSV GET; classify timeout/HTTP/parse; **no Close values in the report** | none |
| `fred` | optional | missing `FRED_API_KEY` → unavailable; else series endpoint `limit=1` without printing the yield | env name only |
| `calendar.yaml` | required | file exists + YAML parse | none |
| `postgres` | optional for Pulse (`--no-db` briefs still run) | connect + `SELECT 1`; last HL ingest `ingested_at` when present | DSN env; never printed |
| `object_store` | n/a for Pulse | env completeness; HeadBucket / filesystem path if configured | env names only; never printed |

Status vocabulary: **`ok | degraded | unavailable`**. Overall: `unavailable` if any **Pulse-required** source is unavailable; else `degraded` if any source is not ok; else `ok`.

## Tests

Missing env → unavailable (not crash); forbidden HL types still blocked (local gate + live probe posts only allowlisted types); report always lists the inventory including required Pulse sources when down; `mm_source_health` does not import `mm_execution` / `hl_trade`; markdown has no last/close/yield prints.

## Non-goals

Paid-data purchases; committing `FRED_API_KEY`; Stooq ToS-violating scrape workarounds (report the failure class); Quant Board; watchlist MAKE/active-call loops; execution; `live.yaml`; risk limits; post-IPO reclaim product.

## Limitations

- No live economic-calendar API; YAML presence is the health signal.
- CoinGecko/Stooq/FRED are not written into Market Memory; last success for those is this probe (or unknown).
- Stooq from cloud IPs may be blocked; the report classifies that instead of retrying as a scraper.
- Object-store ping needs env; incomplete MinIO/S3 is `unavailable` / `missing_env`, same fail-closed story as ingest.
- Sample report is one real read-only run in the PR environment, not a frozen golden hash.
