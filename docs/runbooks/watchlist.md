# Watchlist monitor (Phase 6c-4 / IMP-020) + Ops delivery (Phase 6c-5 / IMP-021)

Research (Investment Research) daily scan of the Principal-locked universe. **Not a call. Not a Quant verdict. Not promotion.** Ops publishes the Telegram cut. Coord orchestrates and is **not** the publisher.

Naming: [`config/desks/naming.yaml`](../../config/desks/naming.yaml) sleeve `watchlist`. Publishing desk is still `research`. Desks runbook: [desks.md](desks.md). Telegram: [telegram.md](telegram.md). PLAYBOOK: [../playbook.md](../playbook.md).

## What operators can do

```bash
uv run lab watchlist scan --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --out /tmp/watchlist
uv run lab watchlist scan --fixture tests/fixtures/phase6c/no_setup.json --no-send --repo-root .

# Ops-owned Telegram fan-out of that artifact (inherit content_hash; default --no-send)
uv run lab deliver watchlist --fixture tests/fixtures/phase6c4/locked_scan.json --no-send --out /tmp/watchlist
```

`--no-send` is the default. Same fixture twice → identical `content_hash`. Fixture path makes **zero LLM calls**. Pytest never hits live Telegram.

Writes under `--out` `research/watchlist/YYYY-MM-DD/`:

| File | Contents |
|---|---|
| `watchlist.md` | Human scan (membership, monitor_state, freshness, provenance) |
| `watchlist.json` | Canonical run |
| `watchlist.sha256` | `content_hash` |

`lab deliver watchlist --out` also writes `briefs/YYYY-MM-DD/telegram-payload.json` (env **names** only; no token).

## Universe

Locked set is `in_universe` ∪ `watch_only` from [`config/universe.yaml`](../../config/universe.yaml). `deferred_must_cut` names stay archived learning records. This product does **not** add tickers and does **not** promote watch-only names.

Monitor states: `COVERED` | `PARTIAL` | `UNAVAILABLE`. Missing tape stays unavailable (never invented).

## PLAYBOOK / mesh / delivery

If the frozen-day fixture already lists a PLAYBOOK idea for a name, the row flags `playbook_setup=yes`. Trade math stays on `lab playbook run`. The scan publishes a Research mesh envelope on `desk.research.output` (existing 6a channel).

Phase 6c-5: Ops fans the scan out on the `research` Telegram route plus an Ops mirror of the **same** `content_hash`. Presentation is an inventory cut (no invented ideas). Quiet hours, idempotency, rate limits, and the `watchlist` numeric threshold apply.

## Not this phase

Universe promotion. Live/signing. Redis. Paid data. Live LLM HTTP. Closing OPEN incidents. Decay-watch (6f).
