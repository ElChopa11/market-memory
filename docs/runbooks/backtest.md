# Phase 4 — reproducible backtest

Australia/Sydney is the ops timezone. **Every timestamp in Postgres is `timestamptz` UTC.** Backtests replay fixtures with an explicit knowledge watermark (`available_at`, analogous to `ingested_at`). Same `params_hash` must yield the same `result_hash`.

This runbook does **not** enable live trading, wallets, or signing.

## Prerequisites

- `uv sync --all-packages`
- Optional Market Memory: `docker compose up -d` and `uv run lab migrate` if you want `research_run` rows

## Fixture contract

JSON or parquet candles. Each bar needs:

| Field | Meaning |
|---|---|
| `market_time` | When the bar closed / the event happened |
| `available_at` (or `ingested_at`) | When we could know it — **this** is the replay clock |
| `open`, `high`, `low`, `close`, `volume` | OHLCV |
| `instrument` | BTC or ETH in v1 |

`available_at` must not be before `market_time` (that would mean the close was known early). Fields such as `future_close` / `next_return` are rejected as look-ahead.

Example: `tests/fixtures/backtest/clean_bars.json`.

## Run

```bash
uv run lab backtest run \
  --fixture tests/fixtures/backtest/clean_bars.json \
  --strategy buy_hold \
  --no-db
```

Bind to a thesis (writes `research/YYYY/THESIS-XXXX/backtests/<params_hash>.json` and a `research_run` row when DB is on):

```bash
uv run lab backtest run \
  --fixture tests/fixtures/backtest/clean_bars.json \
  --strategy threshold \
  --param threshold=102 \
  --slippage-bps 5 \
  --thesis THESIS-0001
```

Parquet is accepted (`.parquet` / `.pq`). Strategies: `buy_hold`, `threshold`.

## Reproducibility

The CLI prints `params_hash` and `result_hash`. Re-run with the same fixture + strategy + params; both hashes must match. `params_hash` covers the canonical bars, strategy name/params, instrument, cash, slippage, and resolved start/end as-of stamps. Wall-clock `started_at` is **not** part of the hash.

## Point-in-time / anti-leakage

Replay only exposes bars with `available_at <= clock` and observations with `ingested_at <= clock`. Adversarial tests live in `tests/adversarial/`. Do not fit on future closes.

## Market Memory

`research_run.kind = backtest` stores `params_hash`, `result_summary`, and artifact paths. `thesis_id` is set when `--thesis` is provided and the thesis is indexed.

Live remains **hard-gated**.
