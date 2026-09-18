# PLAN — IMP-013 Phase 5e Telegram delivery

**Report status:** DONE (#44).  
**Owner:** Don / Chief of Staff (Coordinator)  
**Scope:** Telegram Bot API send for desk packs, config, dry-run payloads, gates. No live trading. No execution. No `live.yaml`. No Phase 6 mesh.

## Why

Phase 5d prepares `--no-send` payload strings and dry-run files. Delivery still had `SEND_ENABLED = False` with no client. Principal lock: one phase per PR. Principal already has `TELEGRAM_*` on the bot box.

## Outcome

- `mm_delivery` Telegram client over httpx (`sendMessage`; optional `sendDocument` / `sendPhoto`). `message_thread_id` for forum topics.
- `config/delivery/telegram.yaml` maps desk → `chat_id_env` + optional thread id. Secrets from env only.
- MarkdownV2 escape, 4096-char sequenced chunks, idempotency key `(desk, as_of, content_hash)`.
- Threshold / quiet hours / dedupe TTL / rate-limit. Never alert without a numeric threshold.
- `--no-send` writes exact payload under `briefs/YYYY-MM-DD/`. No pytest live API.
- `lab desk run` keeps `--no-send`; `lab deliver pack` / `lab deliver test --desk` for delivery (live only with `--i-mean-it`).
- Inbound `/status` `/brief` `/desk` read-only stubs.
- Runbook + ADR 0003. Phase 5 marked complete. IMP-014 Phase 6a parked.

## Tests

- `tests/unit/test_phase5e_delivery.py` — golden byte-stable hash, idempotency, mock send
- `tests/unit/test_phase5e_format.py` — MarkdownV2 + chunking
- `tests/unit/test_phase5e_gates.py` — threshold / quiet hours
- `tests/unit/test_phase5e_cli.py` — `lab deliver` / desk `--send` fail-closed
- `tests/unit/test_phase5e_inbound.py`
- `tests/unit/test_phase5e_queue.py`
- Autouse pytest fixture blocks `api.telegram.org`

## Gates kept

`live_trading_enabled: false`. risk-config-guard. promote-gate. PIT. degrade-never-invent. No secrets in git. Import walls. No live Telegram in pytest.

## Non-goals

Live trading. Signing. `live.yaml`. Phase 6 PG NOTIFY bus / per-desk worker mesh / Redis. Paid Telegram SDKs. Reopening IMP-012 runners except queue hygiene.

## Status

DONE (#44). IMP-014 Phase 6a is the following implementation thread.
