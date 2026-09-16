# Research artifacts

Versioned thesis workspaces. Copy files from `templates/` into `research/YYYY/THESIS-XXXX/` — or create them in one command:

```bash
uv run lab thesis new --goal "…" --owner Research --instrument BTC
```

```text
research/
  YYYY/
    THESIS-XXXX/
      intent.md              # required before thesis
      thesis.md
      research-plan.md
      evidence/links.md      # observation ids; required before in_skeptic
      backtests/             # Phase 4
      skeptic-review.md
      paper/                 # Phase 4
      promotion.md           # or promotion-decision.md
      post-mortem.md
```

`./scripts/check-lifecycle.sh` refuses a thesis without intent and refuses `in_skeptic` without evidence links. Rejected workspaces stay here as learning records.

See [docs/research-lifecycle.md](../docs/research-lifecycle.md) and [docs/runbooks/research-workspace.md](../docs/runbooks/research-workspace.md).
