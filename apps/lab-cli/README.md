# mm-lab-cli

Coordinator surface (`lab` CLI). Must not hold trading credentials.

```bash
uv run lab status
uv run lab migrate
uv run lab ingest --fixture tests/fixtures/hl_window.json --no-objects
uv run lab what-did-we-know --at 2026-09-10T00:00:00Z
uv run lab thesis new --goal "…" --owner Research --instrument BTC
uv run lab thesis link-evidence THESIS-0001 --observation <id> --role supports
uv run lab thesis advance THESIS-0001 --to in_skeptic
uv run lab skeptic open THESIS-0001 --reviewer Skeptic
uv run lab skeptic record THESIS-0001 --verdict reject --reviewer Skeptic
uv run lab thesis list --status rejected
uv run lab brief preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief close --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab brief alert-check --fixture tests/fixtures/briefing/frozen_day.json --no-db
uv run lab backtest run --fixture tests/fixtures/backtest/clean_bars.json --strategy buy_hold --no-db
uv run lab paper open THESIS-0001 --size 0.01 --max-loss "500 USDC" --invalidation "daily close < 60k" --no-db
uv run lab paper list --no-db
uv run lab quant-review --fixture tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml --no-db
```
