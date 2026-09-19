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
      thesis.md              # lifecycle spine
      crypto-thesis-card.md  # Crypto Desk card when instrument is a locked crypto perp (IMP-007)
      equities-thesis-card.md  # Equities desk card when instrument is a locked equity (IMP-007)
      research-plan.md
      evidence/links.md      # observation ids; required before in_skeptic
      backtests/             # Phase 4
      skeptic-review.md
      paper/                 # Phase 4
      promotion.md           # or promotion-decision.md
      post-mortem.md
```

Coordinator queue snapshots (not thesis workspaces) live under `research/queue/`. They are not lifecycle-gated.

Candidate strategy intake (Principal 2026-09-19; Quant **INTAKE_ONLY** / HYPOTHESIS shelf; not a thesis, not a scan-gate) lives under `research/candidates/`. Locked params: `config/candidates/`. Owner QUANT. No sizing. Nothing computed until Phase 1 base rates + 6e instance auto-track. See [candidates/README.md](candidates/README.md). Validation studies are IMP-039 **READY**.

Quant Review Board (IMP-001; not a call generator) lives under `research/quant/YYYY-MM-DD/`:

```bash
uv run lab quant-review \
  --fixture tests/fixtures/quant_review/watchlist_snapshot_20260917.yaml \
  --quant-pack research/queue/quant-20260917 \
  --no-db
```

Locked-membership RESEARCH_PRIORITY pass (IMP-008; not screenshot/TV universe):

```bash
uv run lab quant-review --locked-membership --no-db
```

Writes `research/quant/2026-09-18/` covering `config/universe.yaml` membership only. Membership is not a Quant verdict.

`./scripts/check-lifecycle.sh` refuses a thesis without intent and refuses `in_skeptic` without evidence links. Rejected workspaces stay here as learning records.

Post-IPO / reclaim screen (IMP-006; Equities desk; not a trading decision) lives under `research/screens/post-ipo-reclaim/`:

```bash
uv run lab equities reclaim-screen \
  --fixture tests/fixtures/equities/post_ipo_reclaim_snapshot.yaml \
  --no-db
```

See [docs/research-lifecycle.md](../docs/research-lifecycle.md) and [docs/runbooks/research-workspace.md](../docs/runbooks/research-workspace.md). Dedicated desk cards (IMP-007; Crypto / Equities): [docs/runbooks/thesis-cards.md](../docs/runbooks/thesis-cards.md).
