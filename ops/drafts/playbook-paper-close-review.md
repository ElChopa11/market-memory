# DRAFT playbook — paper close review

**Status:** proposed, not in force. Not for live until reviewed. Does not change `lab paper close`, lifecycle gates, or risk config.

**Why this draft exists:** `lab paper close` currently persists a closed `paper_trade` with only an operator `--exit-reason`. `templates/post-mortem.md` exists, but `check_workspace` never requires it after close. See `ops/proposals/2026-09-17-outcome-scan.md` P1.

## Trigger

A paper trade artifact transitions to `status=closed` (`research/.../paper/<id>.json` and, if used, Market Memory `paper_trade`).

## Required within the same review cycle (proposed)

1. Copy `templates/post-mortem.md` to the thesis workspace as `post-mortem.md` (or `paper/<id>-post-mortem.md` if multiple closes).
2. Fill every section with evidence, not placeholders:
   - Expected vs actual path (from `expected_path` vs `realised_path` plus briefing hooks if any).
   - Expected vs realised P&L / slippage (recomputed from fills/marks, not only `--pnl`).
   - Signal quality (observation ids known at `opened_at`).
   - Risk decision quality (max-loss vs realised; which config version was in force — paper snapshot only, no live.yaml).
   - Invalidation performance (did the stated condition actually occur? when?).
   - Unknowns at entry (partial/stale/missing metrics at `opened_at`).
   - Proposed changes (tests / alerts / data / playbook) — still not auto-applied.
3. Coordinator runs `./scripts/check-lifecycle.sh` (today this will **not** fail a missing post-mortem; that gate is P1).
4. Do not increase size, open a second paper on the same thesis, or draft `promotion-decision.md` until the post-mortem is filled.

## Explicitly out of scope until Principal promotes this draft

- Auto-writing post-mortems from the CLI.
- Blocking `lab paper close` in code.
- Any live trading, signing, or `live.yaml` change.
