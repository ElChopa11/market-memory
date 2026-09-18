# Prompt-hash decay watch (Phase 6f)

Quant-owned SHA-256 watch of versioned prompts and listed strategy/config files. Ops publishes. Not a sixth desk. Not a call.

## Commands

```bash
uv run lab decay watch --fixture tests/fixtures/phase6f/match.json --no-send --no-db
uv run lab deliver decay --fixture tests/fixtures/phase6f/match.json --no-send --no-db
```

`--no-send` is the default. Pytest never hits live Telegram or LLM.

Mismatch fixture (`tests/fixtures/phase6f/mismatch.json`) forces a pinned-hash miss without editing the prompt file. Missing-file fixture stays honest unavailable. Scorecard fixture (`tests/fixtures/phase6f/scorecard.json`) attaches IMP-030 pairs without re-scoring them.

## What is watched

`config/scorecards/decay.yaml` lists versioned prompt files and config files with pinned `expected_sha256`. `watch_enabled: true`.

Per file:

- `MATCH` — present and SHA-256 equals the pin
- `MISMATCH` — present and SHA-256 differs
- `MISSING` — file not on disk (honest unavailable)
- `UNPINNED` — present but no expected hash (fail-closed until pinned)

Overall `MATCH` is status `OK` (output channel only). Any other overall is `DEGRADED` and NOTIFYs `desk.quant.alert`.

## Queue signal

Mismatch emits a queue *signal* (`kind: NOTIFY`) on the artifact. It does **not** write `ops/improvement-queue.md`, auto-merge, waive Skeptic or Risk, auto-disable prompts, or close OPEN incidents. `lab decay watch --waive` / `--merge` is refused.

## Scorecards

When a decay fixture points at an IMP-030 scorecard fixture, pairs are attached as-is. `NOT_COMPARABLE` (including BRIEF-TAG-20260918 90m vs 30m) stays tagged. Completeness delta / hash identity are not invented.

## Naming + delivery

`decay` is a Quant sleeve (`mm_common.naming`). Unknown slug `decay` fails closed as a publishing desk. Ops `lab deliver decay` fans out on the quant route + Ops mirror and inherits `content_hash`. Schedule is 08:05 Sydney; it does **not** close SCHED-001.

## Not this runbook

Live/signing. Redis. Universe promotion. Closing OPEN incidents. Auto-disable of prompts. Waiving Skeptic or Risk. Inventing like-for-like scores for tagged incomparable packs.
