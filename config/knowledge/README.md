# Desk knowledge base

Principal-locked (2026-09-19). Owner: Principal. Path is source of truth for desk priors, failure modes, and house lessons.

Additions / removals / re-ranking of priors or lessons = **Principal PR only**. Desks may append a dated house lesson only from a filled post-mortem that cites `date` + `run_id`. Paper only. No live path. Not a sixth desk.

| File | What it is |
|---|---|
| [priors.md](priors.md) | Strong / moderate / no-comparable-evidence literature priors |
| [failure-modes.md](failure-modes.md) | How we fail measurement; which test catches each mode |
| [house-lessons.md](house-lessons.md) | Dated lab lessons; compounds from post-mortems |

## Usage (read before a round)

1. **Cached prompt prefix.** These files are the static, cache-keyed prefix for desk writer/critic prompts (`config/prompts/`; see [docs/runbooks/llm-budget.md](../../docs/runbooks/llm-budget.md) “Static prompt prefix is cache-keyed”). Do not dump the whole tree into every call beyond that prefix. Changing a file is a PR (same rule as prompt versioning).
2. **A prior never triggers or sizes.** It does not emit an idea, a PLAYBOOK type, a clip, `size_pct`, or a scan-gate. `prior(judgement)` stays excluded from expectancy and sizing ([docs/playbook.md](../../docs/playbook.md)).
3. **Desk citing a prior must label it** as `strong` / `moderate` / `no-comparable-evidence` plus the prior name. Unlabelled citation is a Skeptic fail.
4. **A house lesson wins over a prior.** Annotate the override with **date + `run_id`**. A lesson without those two fields is a note, not an override.

## Must not

- Strategy instructions, playbooks-as-signals, or candidate compute.
- Paid-data claims. Invented prints. Universe / watchlist promotion.
- Treating this tree as Market Memory evidence or as a Quant verdict.
- Auto-merge, gate waiver, or closing OPEN incidents.

## Related

Permissions: [AGENTS.md](../../AGENTS.md). Charters: [ops/desk-charters.md](../../ops/desk-charters.md). Queue: [ops/improvement-queue.md](../../ops/improvement-queue.md). Post-mortem template: [templates/post-mortem.md](../../templates/post-mortem.md).
