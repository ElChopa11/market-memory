# Halt runbook

Live trading is **hard-gated** in Phase 0. This runbook is the kill-switch procedure for when Execution exists.

## Halt now

1. Principal (or Coordinator under Principal instruction) creates `config/halt.flag` on the execution host (gitignored; do not commit).
2. Execution must refuse **new** orders while the file exists. Existing orders are not silently cancelled by Phase 0 docs; later execution code should log the halt and skip submits.
3. Record the halt in Market Memory / a git note: who, when, why.
4. Optional later: `lab halt` signed CLI that writes the same flag and an audit row.

## Resume

1. Only the Principal removes `config/halt.flag`.
2. Confirm `config/risk/environments/live.yaml` still has the intended `live_trading_enabled` value.
3. Confirm dual control still holds (promotion record + Risk allow).
4. Record resume the same way as halt.

## What halt is not

- Not a substitute for `live_trading_enabled: false`.
- Not a research-package concern. Research never had live credentials.
- Not an LLM decision.
