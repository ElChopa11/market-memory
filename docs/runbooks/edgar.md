# SEC EDGAR ingest (IMP-024)

Paper only. No API key. **`file_date` is not the knowledge clock.**

Intel owns ticker resolution and lockup watch. Research consumes stored filings. Delivery is Ops-owned and is **not** this command (no Telegram send).

## What it is

Read-only adapter for `data.sec.gov` and `www.sec.gov/Archives/edgar`. Stores the filing, then extracts:

| Metric | When |
|---|---|
| `edgar_filing` | Stored HTML/text present |
| `lockup_extract` | 424B4 / S-1 Shares Eligible / lock-up language |
| `confirmed_earnings` | 8-K **item 2.02** only (no Street estimates) |

Missing body, HTTP 403/blocks, or a missing Shares Eligible section → `unavailable` + `error_class`. Never invent filing text. Never treat blank/zero as a print.

## Fair access

- Declared `User-Agent` in `config/ingest.yaml` (`adapters.edgar.user_agent`).
- ≤10 requests per second (`rate_limits.edgar.max_requests_per_second`).
- Allowed hosts: `data.sec.gov`, `www.sec.gov`, `sec.gov`. Refuses `api.nasdaq.com` and Yahoo RSS.

## Point-in-time

`as_of_knowledge` = `ingested_at` (lab knowledge time). `file_date` / `published_at` / `market_time` are SEC event stamps only. A 2026-05-13 prospectus ingested on 2026-09-19 is **unknown** at 2026-05-13.

## Commands

```bash
# Fixture stored filings (CI). --no-db = ELIGIBLE only.
uv run lab ingest --fixture tests/fixtures/edgar/cbrs-spcx-lockup.json --no-db

# Same envelopes via the data probe (paper; no persist).
uv run lab data edgar --fixture tests/fixtures/edgar/cbrs-spcx-lockup.json --no-db

# Live Archives pull for monitor.yaml lockup_watch (CBRS + SPCX).
# 403 → unavailable. Do not switch to a mirror or nasdaq.com.
uv run lab data edgar --lockups --live --no-db
```

Persist uses `lab ingest` **without** `--no-db` (Postgres + durable object store). The probe never sends Telegram.

## CBRS / SPCX

Targets come from `config/watchlist/monitor.yaml` `lockup_watch` (Intel). Confirmation is from the **stored** 424B4, not from the YAML forever.

| Name | observation_id | Filing |
|---|---|---|
| CBRS | `edgar-CBRS-424b4-20260513` | 424B4 CIK 2021728 |
| SPCX | `edgar-SPCX-424b4-20260611` | 424B4 CIK 1181412 |

Both are **staged** lockups. Do not assume a flat 180 days. `claim_hash` is on each envelope.

## Non-goals

Treasury Fiscal Data (IMP-035). Binance vision (IMP-023). Street consensus. Finnhub estimates. `live.yaml`. Signing.

See also: [ingest.md](ingest.md), [watchlist.md](watchlist.md), [listings.md](listings.md).
