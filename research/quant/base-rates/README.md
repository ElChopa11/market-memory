# Unconditional event-class base rates

Quant Phase 1 pack (IMP-039). **Paper only. DO NOT SIZE. Not a scan-gate. Not a candidate study.**

Canonical compute:

```bash
uv run lab base-rate compute --fixture tests/fixtures/phase1_base_rates/panel.json --no-db --no-send
```

Writes `research/quant/base-rates/<session_date>/unconditional.{md,json,sha256}`. Market Memory table `event_base_rate` stores the same payload when a DSN is passed.

## Citation for C-001 / C-002 / C-003

| Candidate | Event class | Extra filter the study may add later (not here) |
|---|---|---|
| C-001 supply/demand zone | `zone_boundary_touch` | X·ATR departure confirm + first-return fade |
| C-002 triple RSI MR | `dip_touch` | three RSIs ≤ Z on the same completed bar |
| C-003 second-entry pullback | `pullback_ema_touch` | second pullback + trigger through that extreme |

A study cites **this directory** (or the Memory row) by `params_hash` + `as_of_knowledge`. It must not recompute the unconditional rates and must not treat a source slogan as a sample.

Candidate intake lives in `research/candidates/` (PR #61; INTAKE_ONLY until this pack exists). IMP-034 on main is ticker/licence (#60), not that shelf.

See [docs/runbooks/base-rates.md](../../../docs/runbooks/base-rates.md).
