# Watchlist monitor (Phase 6c-4 / IMP-020) + Ops delivery (Phase 6c-5 / IMP-021)

Research (Investment Research) daily scan of the Principal-locked **review list** in [`config/watchlist/monitor.yaml`](../../config/watchlist/monitor.yaml) (Intel-owned resolution; 2026-09-19 lock). Membership still comes from [`config/universe.yaml`](../../config/universe.yaml) and is **not** promoted. **Not a call. Not a Quant verdict. Not promotion.** Ops publishes the Telegram cut. Coord orchestrates and is **not** the publisher.

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

## Review list + membership

The complete review list is [`config/watchlist/monitor.yaml`](../../config/watchlist/monitor.yaml). Intel owns ticker resolution. Additions/removals are Principal PRs only. `lab watchlist scan` walks that list.

Membership (`in_universe` / `watch_only` / `deferred_must_cut`) still comes from [`config/universe.yaml`](../../config/universe.yaml). Names on the monitor that are not in that file default to **monitor** tier. `universe` tier must match locked `in_universe` (today: BTCUSD → BTC, NVDA). Risk-blocked: CASHCAT, PONSUSD (state only). Monitor-by-archive: HYPEUSD, SOLUSD, NEARUSD, ARBUSD.

Principal 2026-09-19 resolutions (IMP-034): **SAMSUN** → `KRX:005930` (Samsung Electronics, KRW); **KOSDA** → `KRX:KQ11` (KOSDAQ Composite, KRW). Unresolved names (none today) render `UNRESOLVED` and are excluded from ideas. Crypto display CHIPIUSD is Principal-confirmed as `HL:CHIP` (perp, USD); do not invent a CHIPI listing. Keep `HL:VVV`, `HL:PURR`, `NASDAQ:SPCX`, `NASDAQ:CBRS`.

Monitor states: `COVERED` | `PARTIAL` | `UNAVAILABLE` | `UNRESOLVED` | `BLOCKED`. Missing tape stays unavailable (never invented).

Tiers on every idea: `universe` (sizeable, cluster-capped) / `monitor` (UNSIZED — "not in locked universe — promotion requires Principal PR") / `blocked` (never idea).

NEW_LISTING (`<200` daily bars): tag + `days_of_history`; SMA200 = `n/a (insufficient history: <n> bars)` — never `?` and never a shorter MA. Route to the listings sleeve. Lockup inside horizon = Skeptic (gate 5) blackout. EDGAR formulas for CBRS / SPCX — do **not** assume a flat 180 days. IMP-024 persists those formulas as Memory observations (`as_of_knowledge` + 424B4 provenance; `--no-db` = ELIGIBLE only).

Verified earnings and other `gate5_relevant` events use the same gate. `mm_desks.event_calendar.load_event_calendar` reads [`config/macro/event_calendar.yaml`](../../config/macro/event_calendar.yaml), and `idea_eligible` blocks a candidate when its horizon crosses the event date (`default_horizon_days` when the candidate states none). That file is the only live event calendar the gate reads. `config/briefing/calendar.yaml` stays the frozen pulse fixture. Lockup blackouts stay on `fail_closed_blackout_until` in the monitor file.

## PLAYBOOK / mesh / delivery

If the frozen-day fixture already lists a PLAYBOOK idea for a name, the row flags `playbook_setup=yes`. Trade math stays on `lab playbook run`. The scan publishes a Research mesh envelope on `desk.research.output` (existing 6a channel).

Phase 6c-5: Ops fans the scan out on the `research` Telegram route plus an Ops mirror of the **same** `content_hash`. Presentation is an inventory cut (no invented ideas). Quiet hours, idempotency, rate limits, and the `watchlist` numeric threshold apply.

## Not this phase

Universe promotion. Live/signing. Redis. Paid data. Live LLM HTTP. Closing OPEN incidents. Decay-watch (6f).
