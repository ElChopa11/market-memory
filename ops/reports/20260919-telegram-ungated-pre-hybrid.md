# Pre-Hybrid Telegram is ungated

Principal-ordered **record correction** (2026-09-19). Queue/incident/docs only. No feature code. **Do not invent a Telegram archive.**

as_of_knowledge: 2026-09-19 (Australia/Sydney)

## Policy

Every Telegram message published **before the Hybrid architecture change** is tagged **ungated**.

- They did **not** pass lab delivery controls (numeric threshold, quiet hours, idempotency, Ops-owned publisher, Coord orchestration-only).
- They **must not** be treated as evidence that the gated pipeline works.
- Hybrid here = Ops-owned gated Telegram (IMP-013 #44 thresholds / quiet hours / idempotency; IMP-018 #49 five-desk roster, Coord is not a publishing desk; IMP-021 #53 Ops publisher). Standing Grok Bot / Coord-as-publisher fires sit **outside** that path.
- This is a blanket tag on the pre-Hybrid class. Missing a line from an incomplete inventory does not make that line gated.

Queue incident: `TG-UNGATED-PRE-HYBRID` (`OPEN`). Cross-ref BRIEF-TAG-20260918 (scorecard 90m vs 30m) — that tag is comparability; this tag is **pipeline honesty**.

## Known fires (not an archive)

| When (Australia/Sydney) | What | Tag | Notes |
|---|---|---|---|
| 18 Sep 2026 ~22:02 | US pre-market | **ungated** | Also BRIEF-TAG-20260918 (90m vs 30m). Status report / SCHED-001 pack. Quiet hours in lab yaml are 22:00–07:00 Sydney — a 22:02 live post did not pass those controls. |
| 19 Sep 2026 00:03 | cash-open | **ungated** | Operator-known fire. Not a cited `lab deliver` gated send. Also inside quiet hours. No pack in this repo; do not invent one. |
| Publisher audit — Coord lines | Coord-as-publisher | **ungated** | Any Coord (or leftover non-five-desk) lines from the publisher audit. Status 2026-09-19: leftover bots / 7d counts **unverified** — that gap is not a gated ledger. Do not invent message bodies. |

A fire existing on Grok Bot / Coord is **not** a working-pipeline proof.

Paper only. No secrets. No live send in this note.
