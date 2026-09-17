# QUANT-20260917 — Active Calls Pack (Principal / Don)

| Field | Value |
| --- | --- |
| Pack ID | `QUANT-20260917` |
| Repo | `ElChopa11/market-memory` |
| Scope | **ACTIVE CALLS only** (center): BTC, ETH, NVDA, AVGO, MSFT, META, JPM, XLF, XOM |
| Appendix | Watch-only (do not center): UNI, AAVE, SMH |
| Selection | **Conditioned on Principal lock after Skeptic #11/#14 — not an evaluation of the selection rule.** Not a universe quant. |
| Pack written | **2026-09-17 11:18 AEST** (box clock Australia/Sydney) |
| **Pack `as_of_knowledge`** | **`2026-09-17T11:15:47.495030+10:00`** (price/vol run via `research/queue/quant-20260917/build_quant_pack.py`). Names that miss this equity session are **flagged**, not silently lagged. |
| Patch | Methodology patch vs Skeptic **REVISE** ([PR #21](https://github.com/ElChopa11/market-memory/pull/21) · `research/queue/QUANT-20260917-active-calls-skeptic.md`). Numbers below are the **2026-09-17 run of record** (not re-fetched). |
| Disclaimer | **Not a trade. No sizing. No allocation implication. No promotion.** Quant snapshot. Prefer rejection honesty. No fabricated numbers. |

## Clocks / as-of fractures (do not mix)

These stamps are **not concurrent**. Do not read any summary row as a single dashboard moment.

| Clock | Timestamp | What it covers | Concurrent with price/vol? |
| --- | --- | --- | --- |
| Pack `as_of_knowledge` | `2026-09-17T11:15:47.495030+10:00` | When yfinance/Kraken series were read | — (pin) |
| Equity series asof | **2026-09-16** | NVDA, AVGO, MSFT, JPM, XLF, XOM, SMH last native auto-adjusted Close | Native equity end |
| **META lag** | **2026-09-15** | yfinance auto-adjusted Close for 2026-09-16 was **NaN** — last valid **2026-09-15**. **FLAG vs equity peers.** | **No** — 1 session behind NVDA/SPY |
| Crypto series asof | **2026-09-17** | BTC, ETH, UNI, AAVE last native Close | Native crypto end; **not** the equity session |
| Yahoo ADV 5d | **2026-09-17T00:49:39Z** (= 10:49 AEST) | Equity ADV **shares** from universe scan chart API v8 | **No** — different fetch; scan `last` ≠ yfinance last (reconciliation below) |
| HL lab capture | **2026-09-17T00:28:03Z** (= 10:28 AEST) | Stale/partial `metaAndAssetCtxs` | **No** — **appendix only**. Live refresh RQ-20260917-A = HTTP **429** |
| FOMC | 2026-09-16 (~14:00 ET) | +25bp to 3.75–4.00% | **After** corr window end **2026-09-15** |

**HL dayNtl / OI / funding are not in primary one-pagers or summary tables.** See [Appendix: stale lab snapshot](#appendix-stale-lab-snapshot--do-not-size--do-not-treat-as-live).

---

## Methodology TLDR

1. Daily simple returns on auto-adjusted Close (yfinance); UNI from Kraken public OHLC (yfinance UNI-USD stub broken). RV / MDD / trailing returns use **each name’s native series** (`pct_change` on that series alone).
2. Realized vol = sample std(ddof=1) × **√252 (equities)** or **√365 (crypto)** over last **20 / 60 native return bars**. **Not cross-asset comparable** — split panels below.
3. Max drawdown = min peak-to-trough over last **252 equity / 365 crypto native price bars** (bar count, not a calendar year).
4. Trailing returns use **bar counts, not calendar months**: **21d / 63d (equities)** · **30d / 90d (crypto)**. YTD = first native bar with date ≥ 2026-01-01 through **that name’s asof**. YTD is **calendar-year and post-selection descriptive only** — not a lock justification.
5. **Raw outperformance** = name total return − SPY (equities/SMH) or − BTC (ETH/UNI/AAVE). **This is NOT alpha, NOT a residual, NOT β-adjusted.** Do not read as edge.
6. Pearson corr = last **60** complete rows of an **aligned-panel** `pct_change` after `dropna(how="any")` across 9 names. Window **2026-05-28 → 2026-09-15**. **Pre-FOMC** (FOMC 2026-09-16). **Truncated by META asof 2026-09-15.** Point estimate only (no CI / HAC). **No hedge ratio / no stability claim.**
7. Windows are **arbitrary dashboard defaults (20/60/21/63/30/90/252/365) — not a registered research design.** No robustness set in this pack.
8. Corr construction is **not** the native-series return used for RV. Union of crypto calendar ∪ equity sessions then `pct_change` can NaN equity sessions after a gap (weekends in the panel). Inner-join then drops incomplete rows. See corr section.

**Artifacts:** `research/queue/quant-20260917/build_quant_pack.py`, `research/queue/quant-20260917/metrics_active_and_watch.csv`, `research/queue/quant-20260917/metric_windows.csv`, `research/queue/quant-20260917/corr_matrix_60d.csv`, `research/queue/quant-20260917/daily_returns_60d_corr_window.csv`, `research/queue/quant-20260917/vol_mdd_summary.csv`, `research/queue/quant-20260917/equity_adv_5d_from_universe_scan.csv`, `research/queue/quant-20260917/run_meta.json`, `research/queue/quant-20260917/daily_returns_full_panel.csv`.

---

## Registered windows

End date for every trailing native-series metric = **that name’s asof** (table below). Exact start dates for RV / MDD / 21d·63d / 30d·90d are **the date of the Nth last native bar** — native indexes are **not stored** in pack CSVs (only aligned-panel returns). **Do not infer starts from `daily_returns_full_panel.csv`** (that file is the corr alignment, not native RV). Corr start/end **are** stored.

| Metric | Rule | N | End | Start |
| --- | --- | --- | --- | --- |
| RV20 | last 20 **native return** bars; std(ddof=1)×√252 or √365 | 20 | name asof | not in pack CSVs |
| RV60 | last 60 native return bars | 60 | name asof | not in pack CSVs |
| MDD | last 252 equity / 365 crypto **native price** bars | 252 / 365 | name asof | not in pack CSVs |
| Ret short | last **21** (eq) / **30** (crypto) native price steps | 21 / 30 | name asof | not in pack CSVs |
| Ret long | last **63** (eq) / **90** (crypto) native price steps | 63 / 90 | name asof | not in pack CSVs |
| YTD | first native bar with date ≥ **2026-01-01** → asof | path-dependent | name asof | first 2026 native bar (date not stored) |
| Corr 60 | last 60 **aligned-panel** complete rows (all 9 non-null) | 60 | **2026-09-15** | **2026-05-28** |

| Name | Role | Series asof | Ann. factor | Short / long / MDD bars | Bench |
| --- | --- | --- | --- | --- | --- |
| BTC | ACTIVE | 2026-09-17 | √365 | 30 / 90 / 365 | — (absolute) |
| ETH | ACTIVE | 2026-09-17 | √365 | 30 / 90 / 365 | BTC |
| NVDA | ACTIVE | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| AVGO | ACTIVE | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| MSFT | ACTIVE | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| META | ACTIVE | **2026-09-15 (lag)** | √252 | 21 / 63 / 252 | SPY (**vs SPY not contemporaneous** — SPY asof 2026-09-16) |
| JPM | ACTIVE | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| XLF | ACTIVE | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| XOM | ACTIVE | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| UNI | watch | 2026-09-17 | √365 | 30 / 90 / 365 | BTC; Kraken history **starts 2024-09-27** vs peers **2024-09-17** |
| AAVE | watch | 2026-09-17 | √365 | 30 / 90 / 365 | BTC |
| SMH | watch | 2026-09-16 | √252 | 21 / 63 / 252 | SPY |
| SPY | bench | 2026-09-16 | √252 | — | — |

CSV: `research/queue/quant-20260917/metric_windows.csv`.

---

## Macro backdrop (NOT a trade; NOT an allocation)

**Public / crowded macro facts only.** FOMC (12–0) raised FF target **+25bp to 3.75–4.00%** (release ~2026-09-16 14:00 ET); IORB **3.90%**, primary credit **4.00%** effective 2026-09-17; SEP path flags further tightening / higher end-2026 rates. Senate cloture on H.R.3633 rejected **49–50** (2026-09-15).

| Claim | MM obs_id / URL | Source ts |
| --- | --- | --- |
| FOMC +25bp / FF 3.75–4.00% | `01M2PCX90PQAP96J62RR6EWQ35` | 2026-09-16 (Fed statement) |
| IORB 3.90% | `01M2PCX9005R4S8GRPQJP96CRP` | 2026-09-16 |
| Primary credit 4.00% | `01M2PCX90C2J9RPG17CSZDTV3Q` | 2026-09-16 |
| Reuters further-tightening (partial) | `01M2PCX91243QK9V8HCCWQFASY` | 2026-09-16 |
| Primary Fed statement | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm | 2026-09-16 |
| Implementation note | https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a1.htm | 2026-09-16 |
| SEP tables | https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm | 2026-09-16 |
| Senate H.R.3633 cloture fail | https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm | 2026-09-15 |

**Corr window is pre-FOMC (ends 2026-09-15).** Macro obs_ids are **backdrop only**. **No allocation implication from this pack.** **Corr ≠ causation.** Do not read XOM’s sample correlation, financials clustering, or post-hike headlines as a sleeve / NII / energy / crypto-underweight call. Hike + CLARITY setback are **already priced** public narratives, not name-level edge.

---

## Pre-FOMC 60d dependence (ends 2026-09-15)

Window: **60** overlapping aligned-panel daily returns, **2026-05-28 → 2026-09-15**. Source: yfinance via `research/queue/quant-20260917/build_quant_pack.py` · run `2026-09-17T11:15:47.495030+10:00`.

**Construction / truncation:** `DataFrame` union of 9 names + `pct_change` + `dropna(how="any")` + last 60. Inner complete rows in `daily_returns_full_panel.csv`: **387** dates **2024-09-18 → 2026-09-15**. Last 60 of those = this matrix.

- **META truncation:** NVDA/SPY have a **2026-09-16** return bar; META does not (asof **2026-09-15**). That session is the **only** NVDA date missing from the 9-name inner join (`n_obs=60` cannot include 2026-09-16).
- Crypto weekend rows in the panel (BTC weekend return bars in panel: **208**) are dropped when equities are absent.
- Aligned `pct_change` can NaN an equity session after a calendar gap (weekend NaNs in the equity column). **Corr is not native-series RV.** Point estimate only; **n_obs=60**; weekday-aligned by this construction, not by a pre-registered weekday filter. No CIs.

FOMC is **2026-09-16**. **Do not infer a post-hike dependence structure or any allocation from this matrix.**

|      |   BTC |   ETH |   NVDA |   AVGO |   MSFT |   META |   JPM |   XLF |   XOM |
|:-----|------:|------:|-------:|-------:|-------:|-------:|------:|------:|------:|
| BTC  |  1    |  0.89 |   0.26 |   0.03 |   0.25 |   0.13 |  0.04 |  0.25 | -0.12 |
| ETH  |  0.89 |  1    |   0.22 |   0.04 |   0.22 |   0.18 | -0.03 |  0.16 | -0.09 |
| NVDA |  0.26 |  0.22 |   1    |   0.46 |   0.15 |   0.14 |  0.08 |  0.02 | -0.25 |
| AVGO |  0.03 |   0.04 |   0.46 |   1    |   0.12 |  -0.01 | -0.07 | -0.28 | -0.23 |
| MSFT |  0.25 |  0.22 |   0.15 |   0.12 |   1    |  -0.02 |  0.04 |  0.28 | -0.1  |
| META |  0.13 |  0.18 |   0.14 |  -0.01 |  -0.02 |   1    |  0.09 |  0.18 | -0.07 |
| JPM  |  0.04 | -0.03 |   0.08 |  -0.07 |   0.04 |   0.09 |  1    |  0.73 | -0.04 |
| XLF  |  0.25 |  0.16 |   0.02 |  -0.28 |   0.28 |   0.18 |  0.73 |  1    | -0.26 |
| XOM  | -0.12 | -0.09 |  -0.25 |  -0.23 |  -0.1  |  -0.07 | -0.04 | -0.26 |  1    |

**Read (description of this 60-row sample only):** BTC–ETH **0.89**. JPM–XLF **0.73**. XOM negative vs semis/crypto **in this window**. NVDA–AVGO **0.46** (co-movement, not identity — **not** a license to hold both without residual study). **No hedge ratio. No stability claim. Corr ≠ causation. XOM sign is not an energy-sleeve argument under the hawkish Fed.**

CSV: `research/queue/quant-20260917/corr_matrix_60d.csv`, returns: `research/queue/quant-20260917/daily_returns_60d_corr_window.csv`.

---

## Realized vol — crypto (√365 only)

**Do not compare these levels to the equity panel** (different annualization and calendar). Dashboard defaults 20/60 native return bars ending asof. Script does not fetch HL.

| Name | asof | RV20 √365 | RV60 √365 | MDD (365 price bars) |
| --- | --- | --- | --- | --- |
| BTC | 2026-09-17 | 35.6% | 39.1% | -53.1% |
| ETH | 2026-09-17 | 41.7% | 58.9% | -66.6% |

Watch (same convention; not center): UNI 116.3% / 98.2% / -75.1% (asof 2026-09-17; **shorter Kraken sample from 2024-09-27**). AAVE 57.8% / 90.4% / -80.3% (asof 2026-09-17).

---

## Realized vol — equity (√252 only)

**Do not compare these levels to the crypto panel.** META windows end **2026-09-15**.

| Name | asof | RV20 √252 | RV60 √252 | MDD (252 price bars) |
| --- | --- | --- | --- | --- |
| NVDA | 2026-09-16 | 45.5% | 40.4% | -20.2% |
| AVGO | 2026-09-16 | 34.5% | 40.3% | -29.4% |
| MSFT | 2026-09-16 | 21.3% | 42.7% | -34.5% |
| META | **2026-09-15** | 34.2% | 45.8% | -32.5% |
| JPM | 2026-09-16 | 15.9% | 18.0% | -15.5% |
| XLF | 2026-09-16 | 13.7% | 13.0% | -14.8% |
| XOM | 2026-09-16 | 26.2% | 25.7% | -20.1% |

Watch: SMH 32.0% / 45.3% / -24.6% (asof 2026-09-16). MSFT **RV20 21.3% ≪ RV60 42.7% in this sample** — two scalars, **not** a regime identification.

CSV: `research/queue/quant-20260917/vol_mdd_summary.csv`.

---

## Equity ADV (Yahoo stamp — not yfinance last)

Fetched **2026-09-17T00:49:39Z**. Primary field = **ADV 5d shares**. Notional below uses **scan `last` × ADV shares at that stamp**, not yfinance last. **Do not blend into one liquidity story with series Close.**

| Name | ADV 5d shares | Scan last / prevClose | yfinance last (asof) | Same clock? |
| --- | --- | --- | --- | --- |
| NVDA | 102.3M | 212.17 / 223.67 | 213.90 (**2026-09-16**) | No |
| AVGO | 25.1M | 339.27 / 364.38 | 339.51 (**2026-09-16**) | No |
| MSFT | 17.6M | 497.12 / 491.65 | 490.30 (**2026-09-16**) | No |
| META | 18.9M | 670.24 / 653.69 | 670.24 (**2026-09-15**) | No (scan stamp vs META lag) |
| JPM | 8.3M | 352.49 / 354.71 | 348.92 (**2026-09-16**) | No |
| XLF | 36.3M | 56.85 / 57.06 | 55.93 (**2026-09-16**) | No |
| XOM | 13.5M | 169.32 / 164.23 | 163.32 (**2026-09-16**) | No |
| SMH (watch) | 6.9M | 542.11 / 574.29 | 545.56 (**2026-09-16**) | No |

Scan notional ≈ (for reference, same Yahoo stamp only): NVDA $21.70B · AVGO $8.53B · MSFT $8.75B · META $12.66B · JPM $2.92B · XLF $2.06B · XOM $2.29B · SMH $3.74B.

CSV: `research/queue/quant-20260917/equity_adv_5d_from_universe_scan.csv`.

**Crypto ADV/OI:** omitted here. Stale HL → [appendix](#appendix-stale-lab-snapshot--do-not-size--do-not-treat-as-live).

---

## Active calls — native price/vol one-pagers

HL rows **removed** from these tables. Relative prints are **raw outperformance (NOT α)**.


### BTC (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| Last close (spot proxy) | $76,201.02 | yfinance `BTC-USD` · asof **2026-09-17** · `as_of_knowledge` 2026-09-17T11:15:47.495030+10:00 |
| RV 20 / 60 native bars, √365 | 35.6% / 39.1% | last 20 / 60 native return bars ending asof · **not comparable to √252** |
| MDD last 365 price bars | -53.1% | native series ending asof |
| Ret 30d / 90d bars / YTD | 18.1% / 21.2% / -14.1% | bar counts, not months; YTD post-selection descriptive only; absolute (BTC is ETH bench) |

**Skeptic honesty:** Deepest book ≠ mispricing. Public hike / CLARITY fail are **not** a BTC thesis. No thesis until ETF flow series + **fresh** fundingHistory continuity exist. HL omitted (429).


### ETH (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| Last close | $2,415.42 | yfinance `ETH-USD` · asof **2026-09-17** |
| RV 20 / 60 native bars, √365 | 41.7% / 58.9% | **not comparable to √252** |
| MDD last 365 price bars | -66.6% | native series ending asof |
| Ret 30d / 90d bars / YTD | 26.3% / 41.3% / -19.5% | bar counts; YTD descriptive only |
| Raw vs BTC 30d / 90d / YTD | 8.2% / 20.1% / -5.4% | **simple diff, NOT α** (not β-adjusted) |

**Skeptic honesty:** Trailing raw outperformance vs BTC is **not** a trade signal. OI/mark ULIDs missing from known MM set. Flow/L2 gates still required. HL omitted (429).


### NVDA (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 102.3M sh | Yahoo · **2026-09-17T00:49:39Z** (not yfinance clock) |
| Last close (series) | 213.90 | yfinance `NVDA` · asof **2026-09-16** · `as_of_knowledge` 2026-09-17T11:15:47.495030+10:00 |
| Scan last / prevClose | 212.17 / 223.67 | Yahoo stamp above — **≠ series last** |
| RV 20 / 60 native bars, √252 | 45.5% / 40.4% | last 20 / 60 native return bars ending asof |
| MDD last 252 price bars | -20.2% | native series ending asof |
| Ret 21d / 63d bars / YTD | -4.8% / 3.2% / 13.5% | bar counts; YTD descriptive only |
| Raw vs SPY 21d / 63d / YTD | -2.4% / 2.5% / 2.6% | **simple diff, NOT α** |

**Skeptic honesty:** Extremely crowded AI long; Q3 guide public for weeks. Macro obs_ids ≠ name edge. Capex/ROI falsifiers required before thesis.


### AVGO (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 25.1M sh | Yahoo · **2026-09-17T00:49:39Z** |
| Last close (series) | 339.51 | yfinance `AVGO` · asof **2026-09-16** |
| Scan last / prevClose | 339.27 / 364.38 | Yahoo stamp — **≠ series last** |
| RV 20 / 60 native bars, √252 | 34.5% / 40.3% | ending asof |
| MDD last 252 price bars | -29.4% | ending asof |
| Ret 21d / 63d bars / YTD | -13.5% / -9.7% / -2.0% | bar counts; YTD descriptive only |
| Raw vs SPY 21d / 63d / YTD | -11.1% / -10.5% / -12.9% | **simple diff, NOT α** |

**Skeptic honesty:** Satellite to NVDA (same AI-infra bet — do not double-count). Consensus ASIC/networking narrative; backlog conversion unshown. NVDA–AVGO corr 0.46 is **not** a two-name license.


### MSFT (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 17.6M sh | Yahoo · **2026-09-17T00:49:39Z** |
| Last close (series) | 490.30 | yfinance `MSFT` · asof **2026-09-16** |
| Scan last / prevClose | 497.12 / 491.65 | Yahoo stamp — **≠ series last** |
| RV 20 / 60 native bars, √252 | 21.3% / 42.7% | ending asof · **RV20 ≪ RV60 in this sample; not a regime ID** |
| MDD last 252 price bars | -34.5% | ending asof |
| Ret 21d / 63d bars / YTD | 2.3% / 24.7% / 4.3% | bar counts; YTD descriptive only |
| Raw vs SPY 21d / 63d / YTD | 4.7% / 24.0% / -6.6% | **simple diff, NOT α** |

**Skeptic honesty:** Mega-cap duration + AI spend consensus. Large raw vs-SPY 63d print is **not** residual alpha.


### META (ACTIVE) — asof lag FLAG

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 18.9M sh | Yahoo · **2026-09-17T00:49:39Z** |
| Last close (series) | 670.24 | yfinance `META` · asof **2026-09-15** · **misses 2026-09-16 vs peers** |
| Scan last / prevClose | 670.24 / 653.69 | Yahoo stamp |
| RV 20 / 60 native bars, √252 | 34.2% / 45.8% | last 20 / 60 native return bars ending **2026-09-15** |
| MDD last 252 price bars | -32.5% | ending **2026-09-15** |
| Ret 21d / 63d bars / YTD | 13.6% / 12.9% / 3.2% | windows end **2026-09-15** |
| Raw vs SPY 21d / 63d / YTD | 16.0% / 12.2% / -7.7% | **simple diff, NOT α**; **SPY windows end 2026-09-16 — not contemporaneous** |

**Skeptic honesty:** Ads+AI ROI is consensus crowded long. Zero ad ARPU/DAU evidence in shortlist. **Silent-lag vs active peers is not allowed:** this name is flagged, not dropped (vendor NaN). Truncates the 9-name corr end to **2026-09-15**.


### JPM (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 8.3M sh | Yahoo · **2026-09-17T00:49:39Z** |
| Last close (series) | 348.92 | yfinance `JPM` · asof **2026-09-16** |
| Scan last / prevClose | 352.49 / 354.71 | Yahoo stamp — **≠ series last** |
| RV 20 / 60 native bars, √252 | 15.9% / 18.0% | ending asof |
| MDD last 252 price bars | -15.5% | ending asof |
| Ret 21d / 63d bars / YTD | -3.3% / 5.8% / 8.7% | bar counts; YTD descriptive only |
| Raw vs SPY 21d / 63d / YTD | -0.9% / 5.1% / -2.2% | **simple diff, NOT α** |

**Skeptic honesty:** Higher-for-longer NII is a **public crowded narrative**, not an implication of this pack. Need credit/NII primary prints. **No allocation from FOMC backdrop.**


### XLF (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 36.3M sh | Yahoo · **2026-09-17T00:49:39Z** |
| Last close (series) | 55.93 | yfinance `XLF` · asof **2026-09-16** |
| Scan last / prevClose | 56.85 / 57.06 | Yahoo stamp — **≠ series last** |
| RV 20 / 60 native bars, √252 | 13.7% / 13.0% | ending asof |
| MDD last 252 price bars | -14.8% | ending asof |
| Ret 21d / 63d bars / YTD | -2.9% / 3.3% / 2.7% | bar counts; YTD descriptive only |
| Raw vs SPY 21d / 63d / YTD | -0.5% / 2.5% / -8.3% | **simple diff, NOT α** |

**Skeptic honesty:** Diversifier to JPM only; weak/stale secondary blogs are not evidence. Prefer JPM as primary financials name. JPM–XLF 0.73 is sample description, not a pair trade.


### XOM (ACTIVE)

| Metric | Value | Source / ts |
| --- | --- | --- |
| ADV 5d shares | 13.5M sh | Yahoo · **2026-09-17T00:49:39Z** |
| Last close (series) | 163.32 | yfinance `XOM` · asof **2026-09-16** |
| Scan last / prevClose | 169.32 / 164.23 | Yahoo stamp — **≠ series last** |
| RV 20 / 60 native bars, √252 | 26.2% / 25.7% | ending asof |
| MDD last 252 price bars | -20.1% | ending asof |
| Ret 21d / 63d bars / YTD | 1.2% / 15.9% / 35.8% | bar counts; YTD descriptive only — **not a lock justification** |
| Raw vs SPY 21d / 63d / YTD | 3.6% / 15.1% / 24.9% | **simple diff, NOT α** |

**Skeptic honesty:** Fed hike because inflation sticky **≠** XOM upside (**corr ≠ causation**). Negative 60d corr vs semis/crypto is **not** an energy-sleeve argument. Oil supply/refining dominate; pipeline-restoration mean-reversion risk.

---

## Active calls — returns summary (NOT α)

HL-free. Rel column = **raw outperformance (name − bench), NOT alpha**. YTD is post-selection descriptive. META rel vs SPY is **not contemporaneous**.

| Name | asof | 21d or 30d | 63d or 90d | YTD | Raw vs bench (NOT α) | Bench |
| --- | --- | --- | --- | --- | --- | --- |
| BTC | 2026-09-17 | 18.1% (30d) | 21.2% (90d) | -14.1% | — (absolute) | — |
| ETH | 2026-09-17 | 26.3% (30d) | 41.3% (90d) | -19.5% | 8.2% / 20.1% / -5.4% | BTC |
| NVDA | 2026-09-16 | -4.8% (21d) | 3.2% (63d) | 13.5% | -2.4% / 2.5% / 2.6% | SPY |
| AVGO | 2026-09-16 | -13.5% (21d) | -9.7% (63d) | -2.0% | -11.1% / -10.5% / -12.9% | SPY |
| MSFT | 2026-09-16 | 2.3% (21d) | 24.7% (63d) | 4.3% | 4.7% / 24.0% / -6.6% | SPY |
| META | **2026-09-15** | 13.6% (21d) | 12.9% (63d) | 3.2% | 16.0% / 12.2% / -7.7% (**vs SPY asof 2026-09-16**) | SPY |
| JPM | 2026-09-16 | -3.3% (21d) | 5.8% (63d) | 8.7% | -0.9% / 5.1% / -2.2% | SPY |
| XLF | 2026-09-16 | -2.9% (21d) | 3.3% (63d) | 2.7% | -0.5% / 2.5% / -8.3% | SPY |
| XOM | 2026-09-16 | 1.2% (21d) | 15.9% (63d) | 35.8% | 3.6% / 15.1% / 24.9% | SPY |

---

## Appendix — watch-only (do not center)

Not an evaluation of names that were not locked. YTD / raw vs bench are **descriptive only** and **NOT α**. HL omitted (stale appendix). Do not read SMH YTD as “should have kept.”


### UNI (watch)

| Metric | Value | Source |
| --- | --- | --- |
| Spot series | Kraken `UNIUSD` (yfinance `UNI-USD` unavailable/delisted stub) · last 6.7085 · asof **2026-09-17** |
| Sample | **721** bars **2024-09-27 → 2026-09-17** — **shorter than yfinance crypto peers (2024-09-17)**; do not compare MDD/YTD without alignment |
| RV20 / RV60 / MDD | 116.3% / 98.2% / -75.1% | √365 · last 20 / 60 return bars / 365 price bars ending asof |
| Ret 30d / 90d / YTD | 103.8% / 117.3% / 15.8% | **footnote:** 30d includes bounce from ~$3.20 (2026-08-14) — **not** an upside thesis |
| Raw vs BTC (NOT α) | 85.7% / 96.1% / 30.0% | simple diff |

### AAVE (watch)

| Metric | Value | Source |
| --- | --- | --- |
| Last / asof | 120.01 · **2026-09-17** | yfinance `AAVE-USD` |
| RV20 / RV60 / MDD | 57.8% / 90.4% / -80.3% | √365 |
| Ret 30d / 90d / YTD | 34.5% / 60.6% / -19.3% | bar counts; YTD descriptive |
| Raw vs BTC (NOT α) | 16.3% / 39.4% / -5.2% | simple diff |

### SMH (watch)

| Metric | Value | Source |
| --- | --- | --- |
| ADV 5d shares | 6.9M sh | Yahoo · **2026-09-17T00:49:39Z** (notional ≈ $3.74B at **scan** last 542.11, not yfinance 545.56) |
| Last / RV20 / RV60 / MDD | 545.56 / 32.0% / 45.3% / -24.6% | yfinance · asof **2026-09-16** · √252 |
| Ret 21d / 63d / YTD | -8.2% / -11.4% / 46.1% | YTD **post-selection descriptive — not a promotion argument** |
| Raw vs SPY (NOT α) | -5.8% / -12.2% / 35.2% | simple diff |

---

## Appendix: stale lab snapshot — DO NOT SIZE / DO NOT TREAT AS LIVE

```
STALE / PARTIAL HYPERLIQUID CACHE
DO NOT SIZE · DO NOT TREAT AS LIVE · DO NOT PUT NEXT TO YFINANCE RV/RETURNS
Capture: 2026-09-17T00:28:03Z (= 2026-09-17 10:28 AEST)
Live refresh RQ-20260917-A: HTTP 429
fundingHistory 24h: UNAVAILABLE (429)
```

Source: `Intel lab HL cache (file-only; not in-repo)` · PARTIAL top25 same stamp. **Not fetched by `build_quant_pack.py`.**

**docs/ops TSV / Postgres payloads via gh:** **unavailable** this pass (`docs/` has runbooks only; observations.tsv **0 hits**). Numeric fields below are **lab JSON**. Where an MM `obs_id` is listed, **payload bytes were not re-read** — citation without verified bytes. Treat as **unverified lab cache**, not Market Memory-verified.

| Name | dayNtlVlm | OI (coin) | OI$ proxy | funding (instant) | mark / mid / oracle | MM cites (unverified payload) |
| --- | --- | --- | --- | --- | --- | --- |
| BTC | $3.05B | 37,923.56 BTC | $2.90B (= OI × mark) | 0.0000091766 (~0.0009% / period) | 76378.0 / 76377.5 / 76411.2 | funding `01M2PCXAFASC2V0WCGWR0E8MZT`; OI `01M2PCXAFMC3792Y1PQ3H2ACVQ`; mark/mid/oracle `01M2PCXAEE4BRXTPMV56SYN56V` / `01M2PCXACWWCDJRR2GJ20RV7D4` / `01M2PCXAEY18W6290P82NECSM7` |
| ETH | $1.37B | 979,333.98 ETH | $2.37B | 0.0000125000 | 2421.88 / 2421.95 / 2422.6 | funding `01M2PCPEK2ZXFDKPK0TDZZZ5M4`; **no ETH OI/mark ULID in known MM set** |
| UNI (watch) | $31.2M | — | $57.8M | 0.0000125000 | — | **no UNI funding obs_id in known set** |
| AAVE (watch) | $12.9M | — | $67.5M | -0.0000052051 | — | **no AAVE funding obs_id in known set** |

Venue for BTC/ETH rows: Hyperliquid perp (lab). `fundingHistory-btc.json` at lab live path is **null**.

Until a **successful** Intel ingest (fresh `metaAndAssetCtxs` + continuous fundingHistory + verified obs payload bytes), these figures stay appendix-only.

---

## Data gaps / what unlocks a real thesis

| Gap | Why it blocks | What unlocks |
| --- | --- | --- |
| HL live refresh HTTP **429** | fundingHistory, candleSnapshot, fresh metaAndAssetCtxs missing; stale cache **must not** size | Successful Intel ingest with obs_ids + continuous fundingHistory |
| docs/ops TSV / Postgres obs payloads **not readable via gh** this pass | Cannot verify obs_id numeric payloads beyond shortlist cites + lab JSON | Ops export TSV or Research DB read of `01M2PCXAFASC2V0WCGWR0E8MZT` etc. |
| ETH OI/mark ULIDs missing from known set | ETH microstructure not MM-linked | Ingest ETH OI/mark obs_ids |
| Spot BTC/ETH ETF **flow series** | Conditional upside claims unfalsifiable | Primary ETF flow print multi-day |
| Equity name-level fundamentals | Macro obs_ids are backdrop only | 10-Q / transcript extracts + primary series |
| META 2026-09-16 Close NaN in yfinance auto-adjust | As-of lag vs peers; truncates corr to 2026-09-15 | Vendor fix or alternate vendor Close |
| UNI yfinance broken | Watch metrics depend on Kraken public OHLC; shorter history vs peers | Confirm vendor mapping or pin Kraken as source of record |
| Native bar dates not in pack CSVs | RV/MDD/21d start dates cannot be audited from git without re-run | Future `build_quant_pack.py` writes per-metric start/end (do not treat a later run as this pack of record) |
| No must-cuts / no thesis folders in this pack | Per brief rules | Separate Research PR when evidence clears Skeptic bar |

---

## Provenance index

| Artifact | Path |
| --- | --- |
| This pack | `research/queue/QUANT-20260917-active-calls.md` |
| Skeptic review (REVISE) | `research/queue/QUANT-20260917-active-calls-skeptic.md` ([PR #21](https://github.com/ElChopa11/market-memory/pull/21)) |
| Builder script | `research/queue/quant-20260917/build_quant_pack.py` |
| Metrics CSV | `research/queue/quant-20260917/metrics_active_and_watch.csv` |
| Window registry CSV | `research/queue/quant-20260917/metric_windows.csv` |
| Corr CSV | `research/queue/quant-20260917/corr_matrix_60d.csv` |
| Returns (corr window) | `research/queue/quant-20260917/daily_returns_60d_corr_window.csv` |
| Returns (aligned panel — **not** native RV) | `research/queue/quant-20260917/daily_returns_full_panel.csv` |
| Vol/MDD CSV | `research/queue/quant-20260917/vol_mdd_summary.csv` |
| Equity ADV CSV | `research/queue/quant-20260917/equity_adv_5d_from_universe_scan.csv` |
| Run meta | `research/queue/quant-20260917/run_meta.json` |
| Pack README | `research/queue/quant-20260917/README.md` |
| HL raw | `Intel lab HL cache (file-only; not in-repo)` |
| HL PARTIAL top25 | `(lab path omitted)/intel-briefs/20260917-universe-scan-PARTIAL-hl-top25.json` (`hl_capture`: 2026-09-17T00:28:03Z) |
| HL refresh 429 log | `(lab path omitted)/intel-briefs/20260917-rqa-hl-refresh.md` |
| Universe scan (ADV source JSON) | `(lab path omitted)/intel-briefs/20260917-universe-scan-crypto-equity.json` (CSV extract in-repo as Equity ADV CSV) |
| Skeptic frame (universe) | `(lab path omitted)/UNIVERSE-20260917-skeptic-review.md` |

**Hard rules followed:** no fabricated numbers; unavailable labeled with why; no universe expand; no must-cuts; no thesis folders; rejection honesty preferred; **no trades**.
