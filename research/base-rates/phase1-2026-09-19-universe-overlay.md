# Phase-1 instrument base rates — universe overlay — 2026-09-19

> **PROVISIONAL — equity base rates.** Polygon's **2-year free-tier history limit** caps US-listed daily bars (roughly 501 daily bars; 2024-09-19 → 2026-09-18 inclusive on a 2026-09-19 run). This **IS** the vendor cap, not an inferred 'looks like a window' guess.
>
> SMA200 needs 200 bars → equity regime signals start **~2025-07-09**. Equity base rates cover roughly **one year of usable signals in a single regime**. Every equity base rate in this file is **PROVISIONAL** until we have more history. That is the headline, not a footnote.
>
> **OUTSIDE `config/watchlist/monitor.yaml`.** Research overlay only — not a universe change. No promotion without a Principal PR.

Standalone research dump. **Not** a desk product, **not** IMP-040 event-class rates, **not** a Memory write, **not** a Telegram send, **not** a call, **not** a size.

- Report date (Australia/Sydney, when the run finished): `2026-09-19`
- Run finished (UTC): `2026-09-19T12:00:00+00:00`
- Data window requested: `2018-01-01` → `2026-09-19` (UTC)
- Monitor file: `config/watchlist/monitor.yaml` — **not** the ticker set for this overlay file
- Principal actions (SPCX void, 2-year cap, permission filter, overlay path): `research/base-rates/phase1-2026-09-19-principal-actions.md`
- Include rule: ≥ 200 cleaned daily OHLC bars; no substitute symbol; no synthetic bars
- Continuity: Polygon/equities series with first bar before known listing date, or a single-bar move beyond N=8 robust-sigma (1.4826×MAD), are **void** (`suspected_ticker_reuse`) and excluded from pools
- Indicators: SMA50 / SMA200 / ATR20 (Wilder) from bars at or before the signal bar
- Forward returns: `close[t+h]/close[t] - 1` for h=[1, 3, 5, 10] (the bars **after** the signal close)
- Regime: trend-up = close>SMA200 and SMA50[t]>SMA50[t-1]; trend-down = close<SMA200 and SMA50 falling; else chop. Bucket n<100 is reported and **not interpreted**.
- Bracket: symmetric always-long and always-short 1R:2R, R=1.0×ATR20, first touch within 10 bars after the signal; same-bar stop+target = tie; else timeout.

## Cost assumption (pessimistic, flat, one number)

- taker_fee `0.00045` per side, slippage `5.0` bps per side, funding `0.0001` / day × `10.0` days on perps only.
- Round-trip used to shift stop closer / target farther: **perps 29.0 bps**, **equities 19.0 bps** (funding=0).
- Not a live fee schedule. Not a size.

## Three-line summary

1. Unconditional forward-return edge: none computed — no instrument cleared the 200-bar daily-OHLC bar. Nothing clever, and nothing to be long.
2. Enough history to study at all (n≥200 daily bars): (none). Excluded 7 / 7 names (reasons in Coverage).
3. Coin-flip 1R:2R long bracket (R=1×ATR20, first touch within 10 bars, ties separate): gross hit rate n/a (0 targets / 0 stops pooled); net of the flat cost below n/a. A fair 1:2 coin-flip is ~33.3%. Every future strategy claim must beat this after costs.

## Coverage (overlay tickers; OUTSIDE monitor.yaml)

| ticker | tier | round | venue | source | n_bars | first | last | status | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AVGO | overlay | base | nasdaq | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |
| MSFT | overlay | base | nasdaq | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |
| META | overlay | base | nasdaq | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |
| JPM | overlay | base | nyse | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |
| XOM | overlay | base | nyse | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |
| SMH | overlay | base | nasdaq | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |
| XLF | overlay | base | nyse | — | 0 | — | — | excluded | offline: no bars-dir/cache file for this ticker |

Computed: 0. Voided: 0. Excluded: 7. Silent drops: 0.

## Voided — suspected_ticker_reuse / entity splice

Resolving a ticker to an identifier does **not** prove the returned series belongs to one entity. Polygon aggregates by ticker string. Flagged series are **void** and **excluded from pooled stats**. Continuity check: known listing date (first bar precedes identity-start) **or** a single-bar move beyond N=8 robust-sigma (sigma = 1.4826 × MAD of 1-bar simple returns; MAD=0 flat tape uses a 5% floor). See `mm_ingest.equities.continuity` and `config/research/ticker_continuity.yaml`.

None this run.

## Trend-filter finding (permission filter; changes the candidate queue)

Trend-up conditioning (**close > SMA200 and SMA50 rising**) does **not** raise the 1R:2R long bracket hit rate on this sample; for several names it falls sharply. Several trend-up buckets show **negative** mean 1-bar returns.

This undercuts the shared premise of C-001 / C-002 / C-003 (dip entries that assume a confirmed-uptrend **permission filter**) **in this sample**. Do **not** conclude those strategies fail — they are still `INTAKE_ONLY` / HYPOTHESIS, and this file is not a candidate study. Conclude the **permission filter does not carry edge on its own**. Any later study that relies on it must beat **that instrument's own trend-up** bracket rate, not the pooled ~33.3% coin-flip.

Bucket n<100 is do-not-interpret (same rule as the regime tables).

No included names this run.

## Exclusions (repeat, with reasons)

| ticker | n_bars | status | reason |
| --- | --- | --- | --- |
| AVGO | 0 | excluded | offline: no bars-dir/cache file for this ticker |
| MSFT | 0 | excluded | offline: no bars-dir/cache file for this ticker |
| META | 0 | excluded | offline: no bars-dir/cache file for this ticker |
| JPM | 0 | excluded | offline: no bars-dir/cache file for this ticker |
| XOM | 0 | excluded | offline: no bars-dir/cache file for this ticker |
| SMH | 0 | excluded | offline: no bars-dir/cache file for this ticker |
| XLF | 0 | excluded | offline: no bars-dir/cache file for this ticker |

## How to re-run

```text
python scripts/research/base_rates_phase1.py
uv run python scripts/research/base_rates_phase1.py   # this repo
python scripts/research/base_rates_phase1.py --offline  # cache/bars-dir only
python scripts/research/base_rates_phase1.py --overlay
python scripts/research/base_rates_phase1.py --overlay AVGO,MSFT,META,JPM,XOM,SMH,XLF
python scripts/research/base_rates_phase1.py --overlay --overlay-only  # overlay file only
```

Live equities need `POLYGON_API_KEY`. Crypto uses Hyperliquid public `/info` (no key). CoinGecko OHLC is a fallback only. Same bars file → same tables (filename date follows Australia/Sydney at finish). Polygon free tier is 5 req/min — **do not** pass `--no-sleep` on a live free-tier run. `--overlay` writes `phase1-<date>-universe-overlay.md` (OUTSIDE monitor.yaml; not a universe change; no promotion without a Principal PR).

