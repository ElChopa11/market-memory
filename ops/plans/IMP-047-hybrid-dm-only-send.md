# PLAN — IMP-047 Hybrid Step 5a: DM-only live send

**Report status:** IN_PROGRESS (this PR).  
**Owner:** Ops  
**Scope:** Unlock `lab deliver test --to-principal-dm --i-mean-it` to POST only to `TELEGRAM_CHAT_ID_PRINCIPAL_DM`. Hive group / desk pack `--send` stays `SEND_FROZEN`. Paper only.

## Why

Principal denied a prior Step 5 that would unfreeze the Hive group. This step is DM-only. Group stays frozen. Live acceptance is on-box (cloud VM has no delivery token). Unit tests may mock Telegram HTTP for CI and must not be cited as live acceptance.

## Outcome

- `lab deliver test --to-principal-dm --i-mean-it` POSTs only to env `TELEGRAM_CHAT_ID_PRINCIPAL_DM`.
- Missing that env → refuse. Never falls back to `TELEGRAM_CHAT_ID` (group).
- Blanket group / desk pack `--send` remains `SEND_FROZEN`.
- Preflight still runs. Completion row still written if `--routine-id` is passed.
- Test payload keeps the existing deliver-test envelope (`chat_id_env`, `source`, `as_of_knowledge`, provenance lines).
- Weekly investment review artifact CLI is queue-only BACKLOG (IMP-048). Agents must not author weekly.
- Hybrid clock prompt canonical copies + server read-back is queue-only BACKLOG (IMP-049). Do not build tooling. Step 3 acceptance is Principal panel read-back of saved prompt text, not write-API success.
- Per-channel `send_enabled` config gate is queue-only BACKLOG (IMP-050). `--i-mean-it` is acceptable only for this one-shot DM test. `--i-mean-it` alone does **not** lift group SEND_FROZEN (`GROUP_SEND_FROZEN` / `group_live and not to_dm` — code, not YAML).

## Tests

- `tests/unit/test_imp047_dm_send.py` — mock HTTP; DM-only chat_id; group frozen even with `--i-mean-it`; missing DM refuses; envelope fields; `--routine-id` completion row
- `tests/unit/test_imp047_queue.py` — single IN_PROGRESS; IMP-046 DONE #72; IMP-048/049/050 BACKLOG

## Non-goals

Lift Hive group freeze. Miss-detector edits (IMP-042 / #68). Weekly authoring CLI. Hybrid clock prompt-hash / server read-back tooling. Per-channel `send_enabled` YAML (IMP-050). IMP-044 isolation. IMP-045 topics. Auto-merge. Gate waiver. Claiming live acceptance via mocks. Treating write-API 200 as Step 3 acceptance. Agent merge of this PR.

## Rollback

Revert this PR. Group send stays frozen; DM-only CLI flag disappears. No live path to unwind on the cloud VM.
