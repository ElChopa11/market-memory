# Phase 2 — research workspace

Australia/Sydney is the ops timezone for humans (folder year under `research/YYYY/`). **Every timestamp in Postgres is `timestamptz` UTC.** Git artifacts are the source of human review; Market Memory stores thesis indexes, evidence links, and content hashes.

This runbook does **not** enable live trading, wallets, signing, Market Pulse, or backtests.

Research role: read Market Memory + write `research/` artifacts. **No trading credentials. `mm_research_kit` must not import execution or ingest private keys.**

## Prerequisites

- Phase 1 boot: Postgres + `uv run lab migrate` (see [ingest.md](ingest.md))
- [uv](https://docs.astral.sh/uv/) and Python 3.12
- Templates in `templates/` (copied into each thesis workspace)

## Create a thesis from intent (one command)

```bash
uv run lab thesis new \
  --goal "BTC funding mean-reverts after crowded longs" \
  --owner Research \
  --why-now "01ARZ3NDEKTSV4RRFFQ69G5FAV" \
  --instrument BTC \
  --horizon 5d \
  --hypothesis "Crowded longs unwind when funding spikes."
```

Or from an existing intent file:

```bash
uv run lab thesis new --from-intent path/to/intent.md
```

This writes `research/YYYY/THESIS-XXXX/` with:

- `intent.md` (required; thesis is refused without it)
- `thesis.md` (status `in_research`)
- `research-plan.md`
- `evidence/links.md` (empty table until you link observation ids)
- `skeptic-review.md` (verdict placeholder until recorded)

Filesystem-only (no Postgres index): add `--no-db`.

## Link evidence (observation ids)

```bash
uv run lab thesis link-evidence THESIS-0001 \
  --observation 01ARZ3NDEKTSV4RRFFQ69G5FAV \
  --role supports \
  --notes "funding spike vs 30d median"
```

Roles: `supports` | `opposes` | `context`. The observation id must exist in Market Memory when DB sync is on. Git table: `evidence/links.md`.

## Advance lifecycle (DoD gated)

```bash
uv run lab thesis advance THESIS-0001 --to in_skeptic
```

Gates:

| Target | Requires |
|---|---|
| `in_research` | `intent.md` + `thesis.md` |
| `in_skeptic` | research-plan **and** at least one evidence link |
| `rejected` | intent (thesis stays on disk and in DB) |
| `paper` / `live` | **blocked** in Phase 2 |

`./scripts/check-lifecycle.sh` refuses `thesis.md` without `intent.md` and refuses `in_skeptic` without evidence links.

## Skeptic checklist

Open a review (independent reviewer; cannot be the thesis author):

```bash
uv run lab skeptic open THESIS-0001 --reviewer Skeptic
```

Record a verdict. Exactly one of `pass` | `revise` | `reject`:

```bash
uv run lab skeptic record THESIS-0001 --verdict reject --reviewer Skeptic \
  --findings "Invalidation is circular; look-ahead in analogue window."
```

Fill `skeptic-review.md` against the template checklist:

- Bias / leakage / look-ahead
- Crowding / reflexivity
- Liquidity / leverage / slippage
- Alternative explanations
- Already-priced evidence
- Invalidation quality
- Required fixes before paper

| Verdict | Status |
|---|---|
| `pass` | `in_skeptic` (paper is Phase 4) |
| `revise` | back to `in_research` |
| `reject` | `rejected` — **kept as a queryable learning record** |

Revival of a rejected thesis requires a **new intent** (new `THESIS-XXXX`), not a silent status flip.

## Query rejected theses

```bash
uv run lab thesis list
uv run lab thesis list --status rejected
uv run lab thesis show THESIS-0001
```

Rejected rows are not deleted from git or Postgres.

## Lifecycle checker + tests

```bash
./scripts/check-lifecycle.sh
uv run pytest
```

Live remains hard-gated. Do not import `mm_execution` from research tools.
