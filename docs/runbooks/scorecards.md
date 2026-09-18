# Pack scorecards (Phase 6e)

Quant-owned like-for-like scoring of desk packs / briefs. Ops publishes. Not a sixth desk. Not a call.

## Commands

```bash
uv run lab scorecard compare --fixture tests/fixtures/phase6e/packs.json --no-send --no-db
uv run lab deliver scorecard --fixture tests/fixtures/phase6e/packs.json --no-send --no-db
uv run lab queue check
uv run lab queue can-start IMP-022
```

`--no-send` is the default. Pytest never hits live Telegram or LLM.

## Like-for-like

Two packs are comparable only when **all** of these match and neither carries an incomparable tag:

- `product` (for example `us-pre-market`)
- `schedule_anchor` (for example `pre_open_30m`)
- `universe`

Otherwise the pair is `NOT_COMPARABLE` with reason codes (`schedule_anchor_mismatch`, `tagged_incomparable`, …). Completeness delta / hash identity are **not** emitted for incomparable pairs.

Provenance on every row: `content_hash`, `as_of_knowledge`, sources. Knowledge clock is `as_of_knowledge` (lockstep with `ingested_at` for Memory-backed packs). Packs after the run clock stay invisible.

## BRIEF-TAG-20260918

Fri 18 Sep pre-market fired ~90m pre-open (`08:00` NY) vs the 30m-pre-open anchor (`09:00` NY). `config/scorecards/tags.yaml` tags that artifact. Scorecards will not treat it as a 30m-pre-open golden. The queue incident stays **OPEN**.

## Queue hygiene

`lab queue check` (and `scripts/check_queue.py`) parse `ops/improvement-queue.md`:

- At most one IMP-* item may be `IN_PROGRESS`.
- OPEN incidents (SCHED-001, BRIEF-TAG, SRC-*) do **not** occupy that slot.
- `lab queue can-start IMP-XXX` reports whether READY→IN_PROGRESS is allowed. It does **not** write the file.
- Refuses `--merge` / `--waive`. No auto-merge. No gate waiver. No auto-close of OPEN incidents.

## Decay watch (Phase 6f)

`config/scorecards/decay.yaml` lists versioned prompt files and listed configs with pinned SHA-256. `watch_enabled: true`. `lab decay watch` alerts Ops on drift (NOTIFY + queue signal). It does not invent like-for-like scores for tagged incomparable packs. See [decay.md](decay.md).

## Naming + delivery

`scorecard` is a Quant sleeve (`mm_common.naming`). Unknown slug `scorecard` fails closed as a publishing desk. Ops `lab deliver scorecard` fans out on the quant route + Ops mirror and inherits `content_hash`.

## Not this runbook

Live/signing. Redis. Universe promotion. Closing OPEN incidents. Auto-disable of prompts. Waiving Skeptic or Risk.
