# Promote paper → live (runbook)

Phase 0: live remains off. Do not implement order submission to follow this runbook.

## Preconditions

- Lifecycle checker passes for the thesis.
- Skeptic verdict `pass`.
- Paper artifact has invalidation + max loss + results summary.
- `promotion-decision.md` completed, including live size cap and halt conditions.
- Risk config version pinned.
- Execution host has **no treasury key**. API/agent wallet only, from vault.
- `config/halt.flag` is absent only if Principal intends to allow orders.
- `config/risk/environments/live.yaml` change (if any) went through `principal-review`.

## Steps

1. Coordinator verifies `./scripts/check-lifecycle.sh`.
2. Principal reviews paper vs expected path and the 5% per-thesis budget rule.
3. Principal records approval on `promotion-decision.md` (signed commit or equivalent).
4. Dual control: Risk service would still have to allow each `OrderIntent`.
5. First live size ≤ agreed micro-cap (Phase 6 acceptance). Default committed cap is **zero**.
6. Monitor; halt on the documented conditions.

## Forbidden

- Research or Skeptic promoting their own thesis to live.
- Enabling live to “try a fill”.
- Hot-patching live risk rules without a PR.
