# Spec — Brief section: Lab right/wrong hooks

**Owner:** Research (Investment Research)  
**Consumers:** Ops brief renderer (future wire); Coord / Principal review  
**Status:** SPEC ONLY — do not merge into the brief generator, hybrid runner, cron, or `--no-db` Thursday fire path until Principal authorizes a separate PR.  
**Charter:** Research does not acquire data. Intel owns acquisition. This section reads the **instance ledger** once it exists; empty ledger → fallback copy, never invented thesis rows.

Aligned with brief-v2 token discipline (`brief-v2-template.md`): structure only; every value is a `{CURLY_BRACE}` token; missing → `⚪` + literal `unavailable` (or the section empty-ledger fallback below). Colour = data state, never a buy/sell call.

---

## Placement

Fixed heading in the close / morning brief body (already reserved in frozen fixtures and render stubs):

```text
## Lab right/wrong hooks
```

Position: after `## What was unexpected`, before `## Assumption changes`.

---

## Data source (instance ledger)

When the instance ledger exists, each tracked thesis / lab instance supplies one row. Research authors thesis cards against **stored observations**; the ledger is the SoT for open/closed state and scored outcome. No second scrape path.

Required ledger fields per instance (names are logical; physical schema TBD with the ledger PR):

| Field | Token | Notes |
| --- | --- | --- |
| Thesis id | `{THESIS_ID}` | e.g. `THESIS-0001` — stable id, never invented |
| Date opened | `{DATE_OPENED}` | calendar date the instance entered the ledger (ops TZ label OK; stamp must carry zone) |
| Signal | `{SIGNAL}` | short falsifiable claim / direction hook from the thesis card (not a trade instruction) |
| Current state | `{CURRENT_STATE}` | open lifecycle only: `open` \| `in_research` \| `in_skeptic` \| `paper` \| `deferred` \| `unavailable` |
| Outcome (closed) | `{OUTCOME}` | closed instances only: `lab_right` \| `lab_wrong` \| `invalidated` \| `expired` \| `unavailable` |

Optional provenance tokens (emit only when ledger supplies them; else omit the sub-line, do not fabricate):

| Field | Token |
| --- | --- |
| Instrument | `{INSTRUMENT}` |
| Watchlist tier | `{WATCHLIST_TIER}` |
| Invalidation summary | `{INVALIDATION}` |
| Knowledge watermark | `{AS_OF_KNOWLEDGE}` |
| Observation id(s) | `{OBS_IDS}` |

---

## Render layout (tokens only)

### A — Ledger empty / unavailable

Single bullet, fixed copy (matches today’s stub intent; no narrative filler):

```text
## Lab right/wrong hooks

- {LAB_HOOKS_EMPTY_FALLBACK}
```

Canonical fallback string (renderer constant, not LLM prose):

```text
{LAB_HOOKS_EMPTY_FALLBACK} = No indexed theses to score against this session.
```

If the ledger exists but the query fails / is DEGRADED:

```text
- ⚪ Lab hooks unavailable — instance ledger {LEDGER_STATUS}
```

where `{LEDGER_STATUS}` ∈ `unavailable` \| `degraded` \| `empty`.

### B — One or more open instances

```text
## Lab right/wrong hooks

- `{THESIS_ID}` opened {DATE_OPENED} · signal: {SIGNAL} · state: {CURRENT_STATE}[{OPTIONAL_INSTRUMENT_SUFFIX}]
  - Invalidation: {INVALIDATION}          # omit line if missing
  - As-of knowledge: {AS_OF_KNOWLEDGE}    # omit line if missing
```

`{OPTIONAL_INSTRUMENT_SUFFIX}` = ` · {INSTRUMENT}` when present, else empty.

Open rows **must not** emit `{OUTCOME}`. Outcome is closed-only.

### C — Closed instances (scored)

```text
- `{THESIS_ID}` opened {DATE_OPENED} · signal: {SIGNAL} · outcome: {OUTCOME_ICON} {OUTCOME}[{OPTIONAL_INSTRUMENT_SUFFIX}]
  - Closed: {DATE_CLOSED}                 # omit if missing
  - Invalidation: {INVALIDATION}          # omit if missing
  - As-of knowledge: {AS_OF_KNOWLEDGE}    # omit if missing
```

Outcome icons (fixed legend; same brief-v2 rule — colour = data state):

| `{OUTCOME}` | `{OUTCOME_ICON}` |
| --- | --- |
| `lab_right` | ✓ |
| `lab_wrong` | × |
| `invalidated` | 🔴 |
| `expired` | 🟡 |
| `unavailable` | ⚪ |

---

## Ordering and caps

1. Closed instances scored **this session** (if the ledger marks session-scoped closes) first, newest `{DATE_CLOSED}` first.  
2. Then open instances, newest `{DATE_OPENED}` first.  
3. Soft cap: `{LAB_HOOKS_MAX_ROWS}` (default `5`). If truncated, final line:

```text
- … +{LAB_HOOKS_TRUNCATED_COUNT} more in ledger (not shown)
```

---

## Non-goals (explicit)

- No buy/sell/sizing language.  
- No invented thesis ids, signals, or outcomes when the ledger is empty.  
- No Research scrape / generator / second ingest path.  
- No wire into `packages/briefing` render, hybrid, cron, or `--no-db` Stage-1 fire in **this** spec PR.  
- THESIS-0001 defer stands until field-7 Memory observation ids exist; deferred ids may appear only if the ledger itself records them — this spec does not reopen deferred work.

---

## Acceptance (when a later wire PR is authorized)

1. Empty ledger → exactly the `{LAB_HOOKS_EMPTY_FALLBACK}` bullet.  
2. Fixture with two open + one closed instance → three bullets matching layout B/C; closed shows `{OUTCOME}` + icon; open does not.  
3. Missing optional fields → sub-lines omitted, not filled with `unavailable` prose noise (top-level required tokens still show `⚪ unavailable` if the ledger row exists but a required field is null).  
4. Diff touches brief **template/fixture docs** and/or a dedicated renderer helper only after Principal opens that work — not the Thursday schedule path.

---

## Example (illustrative tokens — not live data)

```text
## Lab right/wrong hooks

- `{THESIS_ID}` opened {DATE_OPENED} · signal: {SIGNAL} · state: {CURRENT_STATE} · {INSTRUMENT}
  - Invalidation: {INVALIDATION}
- `{THESIS_ID}` opened {DATE_OPENED} · signal: {SIGNAL} · outcome: ✓ lab_right · {INSTRUMENT}
  - Closed: {DATE_CLOSED}
```

Empty:

```text
## Lab right/wrong hooks

- No indexed theses to score against this session.
```
