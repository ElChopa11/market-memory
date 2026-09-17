# QUANT-20260917 — Active-call pack

| Field | Value |
|---|---|
| **Purpose** | Principal ask — public-data QUANT pack on **active_calls only** so Research can cite measured vol / DD / returns / beta / corr / HL funding+OI. |
| **As-of (fetch start)** | `2026-09-17T01:22:17.638Z` |
| **As-of (fetch end)** | `2026-09-17T01:22:22.964Z` |
| **Timezone** | UTC timestamps on every fetch attempt. Equity session dates from Yahoo unix timestamps converted via UTC date (US cash session timestamps fall on the NY session date). HL daily candles keyed by candle **open** UTC date. |
| **Scope** | `config/universe.yaml` `active_calls` after PR #15: HL **BTC, ETH**; equities **NVDA, AVGO, MSFT, META, JPM, XLF, XOM**. |
| **Excluded** | Watch-only (still universe membership, **not** this pack): UNI, AAVE, SMH. Must-cuts **not reopened**: HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY. |
| **Status** | Snapshot pack / citation tables. **Not** a thesis, **not** orders, **not** risk approval, **not** Market Memory observations (no `obs_id`s). |
| **Sources** | Equities + SPY: Yahoo Finance v8 chart (public; same series yfinance uses). BTC/ETH: Hyperliquid public `/info` (`allMids`, `metaAndAssetCtxs`, `candleSnapshot` 1d, `fundingHistory`). |
| **Scripts / CSVs** | [`research/queue/quant-20260917/`](quant-20260917/) |
| **Coordinate with** | Call cards PR #13 (`research/queue/UNIVERSE-20260917-call-cards.md`); Skeptic PR #14; universe tiers PR #15. RQ-20260917-A (PR #9) remains a **separate** BTC funding/basis workstream. **Path overlap:** Research PR #19 wrote the same `QUANT-20260917-active-calls.md` + `quant-20260917/` prefix — see below. |

**Honesty bar:** numbers below come from this run's CSVs. Empty / `n/a` means insufficient history or a documented fetch failure — **not** a guessed fill. HTTP 429s are counted in the fetch log.

---

## Overlap with Research PR #19

Research already opened [PR #19](https://github.com/ElChopa11/market-memory/pull/19) (`research: QUANT-20260917 active-calls pack`) at the **same citation paths**. Do not merge both blindly.

| | This pack | Research PR #19 |
|---|---|---|
| Paths | `research/queue/QUANT-20260917-active-calls.md` + `quant-20260917/` | same |
| Universe | **active_calls only** (no UNI/AAVE/SMH tables) | active center + watch-only appendix |
| BTC/ETH prices | HL public `candleSnapshot` 1d | yfinance `BTC-USD` / `ETH-USD` |
| HL funding / OI | Live `/info` this run (see fetch log) | Lab cache `2026-09-17T00:28:03Z`, labeled **stale/partial** after HTTP **429**; `fundingHistory` unavailable |
| 9-name corr | Full session inner-join (**n** below) **and** trailing 60d (`corr_matrix_60d.csv`, same filename as #19) | Trailing **60** overlapping days only |
| Equity vs SPY | OLS **beta + Pearson** on full Yahoo overlap | Relative total returns vs SPY; ADV 5d from a prior scan |
| Script | `run_pack.py` (stdlib, backoff) | `build_quant_pack.py` (yfinance/pandas) |

Cite **this pack** for a live HL funding/OI+fundingHistory snapshot and for OLS beta. Cite **#19** for the watch-only appendix, yfinance spot crypto, and ADV 5d. Numbers will not match exactly (HL perp vs Yahoo spot; log vs simple returns on corr; different as-of).

---

## How Research should cite this pack

1. Quote **this file** for tables (human-readable) and the sibling CSVs for exact floats.
2. Always include the **fetch-end timestamp** (`2026-09-17T01:22:22.964Z`) — these are public snapshots, not `what_did_we_know(T)` rows. Ingest into Market Memory before treating them as lab knowledge.
3. Theme roles stay with call cards PR #13: **NVDA primary / AVGO satellite** (SMH watch-only, not here); **JPM primary / XLF diversifier**. Do not treat high cross-corr as independent alpha.
4. BTC card ≠ RQ-20260917-A thesis (PR #9). This pack's BTC/ETH funding+OI is a **point snapshot** plus 72h fundingHistory prints.
5. Do not promote any name to `thesis.md` from these tables alone (Skeptic PR #14: 0 pass / 9 revise keepers).

---

## Methodology (no silent conventions)

| Metric | Definition used here |
|---|---|
| Price | Equities/ETFs: Yahoo **adjclose** when present, else **close**. HL: daily candle **close**. |
| Log return | `ln(P_t / P_{t-1})` on consecutive bars of that series. |
| 20d / 60d realized vol | Sample stdev (`ddof=1`) of the last 20 / 60 log returns, annualized by `√252` (equities) or `√365` (HL 1d candles, 24/7). |
| 1m / 3m return | Simple total return. Equities: 21 / 63 **session** bars. Crypto: 30 / 90 **calendar** daily bars. |
| ~1y max DD | Peak-to-trough on the trailing 252 session closes (equities) or 365 daily closes (crypto), or shorter if history is shorter. Reported as a negative percent. |
| Equity beta / corr vs SPY | OLS slope and Pearson corr of overlapping daily log returns vs SPY on the **inner-join of US session dates for the 7 equities + SPY** (Yahoo history; does not require BTC/ETH). |
| 9-name heatmap | Pearson of session-aligned **log** returns on the **inner-join of the 9 names**. Primary table uses the full overlap. A trailing-**60** session heatmap is also written (`corr_matrix_60d.csv`) so it can be compared with Research PR #19 (which used 60 simple-return days). Weekend/holiday crypto bars are dropped. |
| Funding | HL 8h `funding` from `metaAndAssetCtxs`. "Naive ann." = `rate × 3 × 365` (arithmetic; **not** a forecast). 72h mean uses `fundingHistory` prints in the last 72 hours. |
| Open interest | Snapshot only (`openInterest` in **coin** units). Notional ≈ `markPx × openInterest`. **No public OI history** on `/info`. |

Native-calendar vol/returns (first table) are **not** mixed across 252 vs 365 without reading `ann_factor` / `ret_*_bars` in `metrics_by_name.csv`.

---

## Fetch status

| Item | Value |
|---|---|
| Attempts | 14 |
| HTTP 429 count | 0 |
| Failed attempts | 0 |
| Successful attempts | 14 |

Attempt-level log: [`quant-20260917/fetch_log.json`](quant-20260917/fetch_log.json), [`quant-20260917/fetch_attempts.csv`](quant-20260917/fetch_attempts.csv).

### Failures / 429s

- None recorded in this run.

### Data gaps (observed, not filled)

- Yahoo session lag vs peers (2026-09-16): META ends 2026-09-15. 9-name inner join stops at the earliest of those last dates.
- HL BTC 1d candle for 2026-09-17 is the **in-progress** UTC day (open, not a finished daily bar).
- HL ETH 1d candle for 2026-09-17 is the **in-progress** UTC day (open, not a finished daily bar).
- 9-name heatmap calendar: 2025-08-13 → 2026-09-15 (274 session dates). Limited by HL lookback and any equity session gaps (weekends/holidays dropped).
- Equity–SPY beta calendar: 2024-07-09 → 2026-09-15 (549 session dates). Does **not** require BTC/ETH dates (uses full Yahoo overlap).

---

## HL BTC / ETH funding + OI snapshot

Captured `2026-09-17T01:22:22.964Z`. OI history is **not** in this pack (API limitation, not a skipped download).

| Coin | mid | mark | oracle | funding 8h | naive ann. | OI (coin) | OI notional (mark×OI) | day ntl vol | 72h funding n | 72h mean 8h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 76,359.50 | 76,364.00 | 76,398.00 | 0.00000943 | 1.0% | 37,882.49 | 2,892,858,280 | 3,058,936,877 | 72 | 0.00001161 |
| ETH | 2,421.65 | 2,421.66 | 2,422.61 | 0.00001250 | 1.4% | 980,690.87 | 2,374,899,859 | 1,374,830,013 | 72 | 0.00000763 |

Last `fundingHistory` print per coin is in [`hl_snapshot.csv`](quant-20260917/hl_snapshot.csv); raw prints: [`hl_funding_history_72h.csv`](quant-20260917/hl_funding_history_72h.csv).

---

## Native-calendar vol, drawdown, returns

RV annualization: equities `√252`, crypto `√365`. 1m/3m bar counts differ by class (see methodology).

| Ticker | Class | Last close | Last date | 20d RV | 60d RV | ~1y max DD | 1m return | 3m return | n bars |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| BTC | hl_perp | 76,359.00 | 2026-09-17 | 33.2% | 38.4% | -53.0% | 18.0% | 20.2% | 401 |
| ETH | hl_perp | 2,421.70 | 2026-09-17 | 40.7% | 56.7% | -66.6% | 26.3% | 41.5% | 401 |
| NVDA | us_equity | 213.90 | 2026-09-16 | 44.8% | 40.1% | -20.2% | -4.8% | 3.2% | 550 |
| AVGO | us_equity | 339.51 | 2026-09-16 | 34.7% | 40.3% | -29.4% | -13.5% | -9.7% | 550 |
| MSFT | us_equity | 490.30 | 2026-09-16 | 21.3% | 41.0% | -34.5% | 2.3% | 24.7% | 550 |
| META | us_equity | 670.24 | 2026-09-15 | 33.8% | 45.5% | -32.5% | 13.6% | 12.9% | 549 |
| JPM | us_equity | 348.92 | 2026-09-16 | 15.9% | 18.1% | -15.5% | -3.3% | 5.8% | 550 |
| XLF | us_etf | 55.93 | 2026-09-16 | 13.7% | 13.0% | -14.8% | -2.9% | 3.3% | 550 |
| XOM | us_equity | 163.32 | 2026-09-16 | 26.2% | 25.5% | -20.1% | 1.2% | 15.9% | 550 |

Exact floats + window dates: [`metrics_by_name.csv`](quant-20260917/metrics_by_name.csv).

---

## Equity beta / corr vs SPY

Calendar is **7 equities ∩ SPY** (Yahoo), **not** the 9-name heatmap calendar: **2024-07-09 → 2026-09-15 (549 session dates)**. BTC/ETH are excluded from beta.

| Ticker | vs | n pairs | window | beta | corr |
|---|---|---:|---|---:|---:|
| NVDA | SPY | 548 | 2024-07-10 → 2026-09-15 | 2.01 | 0.70 |
| AVGO | SPY | 548 | 2024-07-10 → 2026-09-15 | 2.00 | 0.62 |
| MSFT | SPY | 548 | 2024-07-10 → 2026-09-15 | 0.93 | 0.55 |
| META | SPY | 548 | 2024-07-10 → 2026-09-15 | 1.36 | 0.60 |
| JPM | SPY | 548 | 2024-07-10 → 2026-09-15 | 0.92 | 0.61 |
| XLF | SPY | 548 | 2024-07-10 → 2026-09-15 | 0.78 | 0.74 |
| XOM | SPY | 548 | 2024-07-10 → 2026-09-15 | 0.20 | 0.14 |

CSV: [`equity_spy_beta_corr.csv`](quant-20260917/equity_spy_beta_corr.csv). Aligned closes: [`aligned_equities_spy_closes.csv`](quant-20260917/aligned_equities_spy_closes.csv).

---

## Cross-correlation heatmap (9 active calls)

Pearson of daily log returns on the 9-name inner-join calendar **2025-08-13 → 2026-09-15 (274 session dates)**. Return pairs **n = 273**. This is correlation, not causation; NVDA/AVGO and JPM/XLF are **theme-linked** in PR #13.

| | BTC | ETH | NVDA | AVGO | MSFT | META | JPM | XLF | XOM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 1.00 | 0.90 | 0.34 | 0.29 | 0.30 | 0.18 | 0.24 | 0.32 | -0.04 |
| ETH | 0.90 | 1.00 | 0.34 | 0.33 | 0.29 | 0.21 | 0.20 | 0.29 | -0.01 |
| NVDA | 0.34 | 0.34 | 1.00 | 0.51 | 0.26 | 0.29 | 0.17 | 0.11 | -0.19 |
| AVGO | 0.29 | 0.33 | 0.51 | 1.00 | 0.18 | 0.19 | 0.11 | 0.01 | -0.17 |
| MSFT | 0.30 | 0.29 | 0.26 | 0.18 | 1.00 | 0.18 | 0.08 | 0.25 | -0.12 |
| META | 0.18 | 0.21 | 0.29 | 0.19 | 0.18 | 1.00 | 0.19 | 0.29 | -0.19 |
| JPM | 0.24 | 0.20 | 0.17 | 0.11 | 0.08 | 0.19 | 1.00 | 0.77 | -0.06 |
| XLF | 0.32 | 0.29 | 0.11 | 0.01 | 0.25 | 0.29 | 0.77 | 1.00 | -0.11 |
| XOM | -0.04 | -0.01 | -0.19 | -0.17 | -0.12 | -0.19 | -0.06 | -0.11 | 1.00 |

Long form: [`cross_corr.csv`](quant-20260917/cross_corr.csv). Matrix: [`cross_corr_matrix.csv`](quant-20260917/cross_corr_matrix.csv). Aligned closes: [`aligned_session_closes.csv`](quant-20260917/aligned_session_closes.csv).

### Trailing 60 session days (comparable filename to PR #19)

Pearson of the last **60** overlapping log returns on **2026-06-22 → 2026-09-15**. PR #19 used simple returns on a 60-day window; do not treat the two matrices as identical.

| | BTC | ETH | NVDA | AVGO | MSFT | META | JPM | XLF | XOM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 1.00 | 0.87 | 0.18 | 0.06 | 0.09 | 0.13 | 0.10 | 0.24 | -0.22 |
| ETH | 0.87 | 1.00 | 0.11 | 0.02 | 0.07 | 0.09 | 0.02 | 0.20 | -0.21 |
| NVDA | 0.18 | 0.11 | 1.00 | 0.56 | 0.03 | 0.09 | 0.15 | -0.07 | -0.25 |
| AVGO | 0.06 | 0.02 | 0.56 | 1.00 | 0.08 | -0.00 | 0.15 | -0.13 | -0.24 |
| MSFT | 0.09 | 0.07 | 0.03 | 0.08 | 1.00 | 0.01 | 0.09 | 0.36 | -0.13 |
| META | 0.13 | 0.09 | 0.09 | -0.00 | 0.01 | 1.00 | 0.13 | 0.27 | -0.23 |
| JPM | 0.10 | 0.02 | 0.15 | 0.15 | 0.09 | 0.13 | 1.00 | 0.69 | -0.09 |
| XLF | 0.24 | 0.20 | -0.07 | -0.13 | 0.36 | 0.27 | 0.69 | 1.00 | -0.26 |
| XOM | -0.22 | -0.21 | -0.25 | -0.24 | -0.13 | -0.23 | -0.09 | -0.26 | 1.00 |

CSV (same basename as #19): [`corr_matrix_60d.csv`](quant-20260917/corr_matrix_60d.csv).

---

## What this pack is not

- Not `config/universe.yaml` membership change (PR #15 already locked active vs watch-only).
- Not a must-cut reopen (HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY stay archived).
- Not live trading, signing, wallet code, or `hl_trade`.
- Not Market Memory ingest (no observation envelopes, no `as_of_knowledge`).
- Not a Skeptic pass and not a paper-trade open.

---

## Reproduce

```bash
python3 research/queue/quant-20260917/run_pack.py
```

Requires outbound HTTPS to `query1.finance.yahoo.com` / `query2.finance.yahoo.com` and `api.hyperliquid.xyz`. Stdlib only. Re-running **overwrites** CSVs and this markdown with a new as-of.

**— End QUANT-20260917 active-calls pack —**
