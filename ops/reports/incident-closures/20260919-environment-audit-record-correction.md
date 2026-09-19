# Record correction — 2026-09-19 environment audit (Don)

Principal-ordered **record corrections only**. No features. No equity work. No scheduler code.

as_of_knowledge: 2026-09-19 (Australia/Sydney)
auditor: Don (Chief of Staff)
mandate: Principal — (1) do not leave `SRC-FRED-MISSING-ENV` as a simple key-absent close; (2) retitle object_store as a **DOWN SERVICE**; (3) tag pre-Hybrid Telegram as **ungated** (see [20260919-telegram-ungated-pre-hybrid.md](../20260919-telegram-ungated-pre-hybrid.md)).

This note does **not** erase prior packs. Cross-ref the CLOSED persist closure:

- [20260919-101938-aest-fred-fullstack-close.json](20260919-101938-aest-fred-fullstack-close.json)
- run_id `fred-fullstack-20260919-101938-aest` (IMP-022 persist evidence; `--no-db` remains ELIGIBLE only)

## SRC-FRED-MISSING-ENV — reopened / converted OPEN

**Queue status:** `OPEN`  
**Root cause:** **environment-propagation** (config present, run env absent)

Do not treat the persist close as “the key was absent, then it was set, therefore CLOSED.”

2026-09-19 environment audit (Don): `FRED_API_KEY` was present on the Secrets card **and** in process env at audit time. Earlier `missing_env` symptoms are consistent with runs that did **not** inherit box env — the secret can sit on the card/box while a failing run executes without that process env.

IMP-022 stays `DONE` (full-stack persist path exists and is cited). This incident stays `OPEN` until operators show that FRED-using runs inherit the box env, or until a documented propagation control exists. Do not close on “key exists on the Secrets card.”

## SRC-OBJECT-STORE — DOWN SERVICE (not a missing credential)

**Queue status:** `OPEN` (services / infrastructure list; alias `SRC-object_store` / source id `object_store`)  
**Root cause:** **DOWN SERVICE** — MinIO `:9000` connection refused, no container

This is not a missing-env credentials incident. `MINIO_*` keys may still be present as local defaults (`.env.example` / compose `minioadmin`) while the daemon is down. Source-health 2026-09-17 labelled `missing_env` / credentials_present=no; that class misreads a down service.

Do not close by setting `MINIO_*`. Close when `:9000` is reachable (or an operator-chosen durable backend is in use) and a down daemon is not filed as missing credentials.

## TG-UNGATED-PRE-HYBRID — see sibling note

Pre-Hybrid Telegram fires are **ungated** and are not evidence of a working pipeline. Known fires and policy: [20260919-telegram-ungated-pre-hybrid.md](../20260919-telegram-ungated-pre-hybrid.md). This file does not invent a Telegram archive.

Paper only. No secrets in this file.
