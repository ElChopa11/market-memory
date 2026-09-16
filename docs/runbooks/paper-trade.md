# Phase 4 — paper / shadow ledger

Paper trades are **bound to theses**. They cannot open without **invalidation** and **max loss**. This is a shadow ledger: fills and marks are recorded; nothing is signed or sent to Hyperliquid.

Live trading remains **hard-gated**. There is no risk *service* yet (Phase 5); these two fields are still mandatory.

## Preconditions

- Thesis workspace exists (`lab thesis new`).
- At least one evidence link.
- Independent skeptic verdict `pass`.
- Invalidation is a real condition (not blank / `tbd`).
- Max loss is a positive amount (e.g. `500 USDC`).

## Open

```bash
uv run lab paper open THESIS-0001 \
  --size 0.01 \
  --max-loss "500 USDC" \
  --invalidation "BTC daily close < 60000" \
  --checkpoint "funding mean-reverts within 48h" \
  --fill-price 65000 \
  --mark 64990 \
  --no-db
```

This writes `research/YYYY/THESIS-XXXX/paper/<id>.md` (from `templates/paper-trade.md`) and `<id>.json`, and advances status to `paper`.

Without `--no-db`, a `paper_trade` row is inserted in Market Memory (Alembic revision `0004_phase4`). The DB check constraints also refuse empty invalidation / max loss.

These fail:

```bash
uv run lab paper open THESIS-0001 --size 0.01 --max-loss "500 USDC" --invalidation "" --no-db
uv run lab paper open THESIS-0001 --size 0.01 --max-loss "" --invalidation "close < 60k" --no-db
```

## Close

```bash
uv run lab paper close THESIS-0001 \
  --id <paper-trade-ulid> \
  --exit-reason "invalidation hit" \
  --pnl -120 \
  --slippage-bps 8 \
  --fill-price 59900 \
  --mark 60000
```

`--exit-reason` is required. Record expected vs realised path in the markdown artifact.

## List

```bash
uv run lab paper list
uv run lab paper list THESIS-0001 --status open
```

## Lifecycle

`draft` → `in_research` → `in_skeptic` → **`paper`**. `live` is still refused. `./scripts/check-lifecycle.sh` fails paper artifacts that lack invalidation + max loss, and still refuses thesis without intent.

See [research-lifecycle.md](../research-lifecycle.md) and [backtest.md](backtest.md).
