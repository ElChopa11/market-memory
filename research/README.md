# Research artifacts

Versioned thesis workspaces. Copy files from `templates/` into `research/YYYY/THESIS-XXXX/`.

```text
research/
  YYYY/
    THESIS-XXXX/
      intent.md              # required before thesis
      thesis.md
      research-plan.md
      evidence/
      backtests/
      skeptic-review.md
      paper/
      promotion.md           # or promotion-decision.md
      post-mortem.md
```

`./scripts/check-lifecycle.sh` refuses a thesis (and later stages) without the required predecessors. See [docs/research-lifecycle.md](../docs/research-lifecycle.md).

No thesis workspaces are opened in Phase 0.
