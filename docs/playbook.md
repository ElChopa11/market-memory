# Hive PLAYBOOK (Phase 6c / IMP-016)

One run emits the artifact ladder. All six types share `run_id` + `content_hash`. Trade math is computed **once** by Quant and inherited; mismatch is a failed run.

Architecture: [ADR/0006-phase6c-playbook-telegram.md](../ADR/0006-phase6c-playbook-telegram.md). Token budgets: [runbooks/llm-budget.md](runbooks/llm-budget.md). Telegram: [runbooks/telegram.md](runbooks/telegram.md). Desks: [runbooks/desks.md](runbooks/desks.md).

**Not a call. Not Execution. Live trading remains HARD-GATED.**

## What operators can do

```bash
uv run lab playbook run --fixture tests/fixtures/phase6c/no_setup.json --no-send --out /tmp/playbook
uv run lab playbook run --fixture tests/fixtures/phase6c/ideas.json --no-send --repo-root .
```

`--no-send` is the default. Same fixture twice → identical `content_hash`. A no-setup day makes **zero LLM calls**.

Writes under `--out` `briefs/YYYY-MM-DD/`:

| File | Contents |
|---|---|
| `playbook.json` | Canonical run (artifacts, hashes, ledger rows, gaps) |
| `playbook.sha256` | `content_hash` of the run |
| `<content_hash>.png` | Chart PNG; filename **is** the levels `content_hash` |

## Artifact ladder

Config: [`config/playbook/ladder.yaml`](../config/playbook/ladder.yaml). Max **3** ideas; the cut is stated (`N ideas shown; M cut (max 3)`). Zero ideas → `no actionable setup` (complete, not a failure).

| Type | Role | LLM? |
|---|---|---|
| `DAILY_BIAS` | Instrument / direction / conviction / level | Template |
| `EDGE_SCAN` | SCAN_CARD fields + optional writer prose | Writer only when ideas exist **and** a completer is injected |
| `INTEL_PACKET` | Feeds, missing, idea detail | Template |
| `CHART_ARTIFACT` | Prior H/L, session VWAP+AVWAP, value area, range, gaps; PNG | Template |
| `OFFICIAL_BRIEF` | 30-second executive cut | Writer only when ideas exist **and** a completer is injected |
| `STATE_CARD` | Flat / armed / in / cooling + permission ON/OFF + rearm | Template |

DQ = `fields_populated / fields_required` (completeness ratio). **Letter grades are removed.** Below `dq_publish_threshold` (0.8) the run publishes a no-idea brief (`DEGRADED`), not a confident one. Abstention is correct.

## Quant-owned trade math

`mm_quant.trade_math.compute_trade_math` is the only R calculator. Config: [`config/quant/trade_math.yaml`](../config/quant/trade_math.yaml).

| Quantity | Rule |
|---|---|
| `risk_per_unit` | `\|entry − stop\|` |
| `R_target_n` | `(target_n − entry) / risk_per_unit` |
| Expectancy | `(p_win * avg_R_win) − ((1 − p_win) * 1)` after costs |
| Costs | `taker_fee*2 + est_slippage(clip) + funding_rate * expected_hold` |
| `p_win` provenance | `base_rate(n, window)` / `prior(judgement)` / `model(name, version)` |
| `prior(judgement)` | **Excluded** from expectancy and sizing |
| `n < min_sample` | Desk states it; `size_pct = 0` |
| Sizing | `size_pct = risk_budget_pct / (stop_distance_atr * atr_pct)` (vol-targeted; same logic crypto/equities) |
| Leverage | Ceiling only |

Every artifact carries `trade_math_hash`. Recompute or drift → `error_class=math_mismatch`, failed run.

## Invalidation / concentration / drawdown / post-mortem

- Invalidation lookback ≥ thesis horizon / 2. Daily-print invalidators on multi-day theses are rejected at Skeptic. Flow invalidators use rolling net/z, never a single print.
- Concentration clusters come from trailing-corr YAML ([`config/risk/clusters.yaml`](../config/risk/clusters.yaml)), not a hand-named list in `engine.py`. Risk **nets** the same cluster. Cap `max_cluster_pct`.
- Drawdown ladder ([`config/risk/drawdown.yaml`](../config/risk/drawdown.yaml)): rolling −8% sleeve halves; −15% dry + review. **n=1 changes nothing.**
- Closed idea → fill [`templates/post-mortem.md`](../templates/post-mortem.md) before that instrument publishes a new idea (`PostMortemRequired` otherwise).

## Chart product (Research sleeve)

Levels are computed **once** and quoted by others (`mm_desks.chart.compute_levels`). PNG is a deterministic stdlib encode (no matplotlib). Filename = `{content_hash}.png`. Missing bars stay missing (not invented).

## Grounding + budgets

See [runbooks/llm-budget.md](runbooks/llm-budget.md). Writer prose uses placeholders substituted from provenance-backed rows. FRED unavailable → no rates figure; `rates` in gaps.

## Delivery

`lab deliver fanout --desk research --from-markdown PATH --as-of … --no-send` posts the desk channel and an Ops mirror with the **same** `content_hash` plus footer. Never re-render. Inbound is read-only (`/status` `/desk` `/brief` `/idea` `/gaps` `/halt`). Unknown uid is a silent drop + audit.

## Not this phase

Redis. Live/signing. A live LLM HTTP client. Watchlist inventory is Phase 6c-4 (`lab watchlist scan`) — it does not emit PLAYBOOK types or trade math. Pack scorecards are Phase 6e (`lab scorecard compare`). Prompt-hash decay watch is Phase 6f (`lab decay watch`).
