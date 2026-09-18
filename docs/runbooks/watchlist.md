# Watchlist monitor (Phase 6c-4 / IMP-020)

Research (Investment Research) daily scan of the Principal-locked universe. **Not a call. Not a Quant verdict. Not promotion.**

Naming: [`config/desks/naming.yaml`](../../config/desks/naming.yaml) sleeve `watchlist`. Publishing desk is still `research`. Desks runbook: [desks.md](desks.md). PLAYBOOK: [../playbook.md](../playbook.md).

## What operators can do

```bash
uv run lab watchlist scan --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --out /tmp/watchlist
uv run lab watchlist scan --fixture tests/fixtures/phase6c/no_setup.json --no-send --repo-root .
```

`--no-send` is the default. Same fixture twice → identical `content_hash`. Fixture path makes **zero LLM calls**.

Writes under `--out` `research/watchlist/YYYY-MM-DD/`:

| File | Contents |
|---|---|
| `watchlist.md` | Human scan (membership, monitor_state, freshness, provenance) |
| `watchlist.json` | Canonical run |
| `watchlist.sha256` | `content_hash` |

## Universe

Locked set is `in_universe` ∪ `watch_only` from [`config/universe.yaml`](../../config/universe.yaml). `deferred_must_cut` names stay archived learning records. This product does **not** add tickers and does **not** promote watch-only names.

Monitor states: `COVERED` | `PARTIAL` | `UNAVAILABLE`. Missing tape stays unavailable (never invented).

## PLAYBOOK / mesh

If the frozen-day fixture already lists a PLAYBOOK idea for a name, the row flags `playbook_setup=yes`. Trade math stays on `lab playbook run`. The scan publishes a Research mesh envelope on `desk.research.output` (existing 6a channel). No new Telegram route — that is 6c-5.

## Not this phase

6c-5 delivery expansion. 6d listings/IPO. Universe promotion. Live/signing. Redis. Paid data. Live LLM HTTP.
