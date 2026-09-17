# mm-research-kit

Helpers to write research artifacts under `research/YYYY/THESIS-XXXX/`. No secrets.

**Must not:** access trading credentials, ingest private keys, or import live signing / `mm_execution`.

Public helpers:

- `create_thesis_from_intent` — intent → thesis → research-plan → evidence → skeptic-review
- `link_evidence` — observation ids on the git artifact
- `advance_status` — DoD gates (no `in_skeptic` without evidence links; paper needs skeptic pass + invalidation/max loss)
- `open_skeptic_review` / `record_skeptic_verdict` — `pass` | `revise` | `reject`

Coordinator surface: `uv run lab thesis …`, `lab skeptic …`, `lab backtest run`, `lab paper …`, `lab quant-review`. Runbook: [../../docs/runbooks/research-workspace.md](../../docs/runbooks/research-workspace.md). Plan: [../../ops/plans/IMP-001-quant-review-board.md](../../ops/plans/IMP-001-quant-review-board.md).

See [../../docs/founding-brief.md](../../docs/founding-brief.md) and [../../AGENTS.md](../../AGENTS.md).
