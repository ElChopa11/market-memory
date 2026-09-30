# Scope memo: equity close.md print (freeze exception)

**Status:** SCOPE ONLY. No print implementation. No merge. Paper only.
**Date:** 2026-09-30.
**Principal exception:** print the 16 rank-eligible Polygon equities on the Sydney-morning `close.md`. Every other freeze lock stays: Coinglass HELD, Chart STAND_BY, no Entry/SL/TP, message shape A1 (one message), GMGN parked.

This memo is the review packet. It does not enable the print.

## Verdict (read this first)

| Question | Answer |
|---|---|
| Rank-eligible list | **16 names**, `config/ingest/mvp_retain.yaml` `polygon.tickers` minus `QQQ`. Confirmed below. `SPY` is not on that list. |
| Char budget | **Yes, it fits** one A1 close message. Binding cap is 42 characters per pre-block line and 4096 per Telegram `sendMessage`. Modeled lines are 19–21 characters. No second message and no card split. |
| #124 allowlist | **No touch.** The print does not strip or extend the `workflow_dispatch` allowlist and does not change the host dispatch script. |
| Deliver path | The sender can stay as it is **if** the lines are already inside `close.md`. One job-order change inside `brief-and-deliver` is required so the print reads this capture's grouped-daily closes. That is not a send-flag change. |
| `morning.py` core logic | **No-touch.** Fetch, session-date rules, change cells, health, and Hyperliquid lines stay. A separate formatter plus a thin insert in `render.py` is enough. |
| Levels source | Polygon grouped-daily **close already on this capture's row**: `payload.value`, `payload.session_date`, column `market_time`. **Not** `as_of_knowledge` (that clock is ingest time). **Not** a later Neon pull of a newer bar. |
| Set1 vs set2 | Set1 = C1–C3, equity **DEGRADED n=0**, bodies stay. Set2 starts at the first morning whose Actions checkout contains the print. A C4 go-live leaves **8** set2 mornings inside the freeze, not 10. Equity ranks stay DEGRADED until an adjacent weekday **pair** both print the same 16 names. |

## Binding constraints (IC/Risk Skeptic + Quant)

IC accepted Quant adjacency. These binds govern any later build. They are not optional notes.

### IC/Risk Skeptic

1. Levels are as-of the capture's equity session date. A later Neon pull of a newer bar is look-ahead.
2. Do not rewrite set1 bodies (C1–C3, and the DONCAPO A1 Day-7 dry-run). That locked artifact is box path `/workspace/drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md`, sha256 `b5f33450ad9222d031b70cf060949688506dc59e906444dfb01a1930b78e86f1`. It is not in this git checkout. Full pack `425ef905…` and A2 archive `7ddac5e1…` stay separate. The format-freeze dry-run `ops/reports/renders/brief-template-dryrun.txt` (sha256 prefix `c693f077…`) is its own artifact. Set1 stays equity DEGRADED n=0. Set2 is a new print generation.
3. Rank-eligible adds never authorize Entry, SL, or TP, and never clear NO QUALIFIED TRADE.
4. Feed, as-of field, and set1/set2 capture ids are named in this memo before any code is cleared.

### Quant

1. Equity Top5/Bottom5 stay DEGRADED until an adjacent weekday pair both carry printed levels for the same rank-eligible names. The first set2 capture alone does not clear equity ranks.
2. Do not recompute or rewrite set1 ranks with later equity prints.
3. Rank-eligible adds never authorize Entry, SL, or TP, and never clear solitary NQT.
4. When a set2 pair clears equity, MIXED/Option A updates only from recomputed ln-returns on the printed levels. Never from the brief's `%` string. Never by padding a missing name.

The proposed print uses the Polygon closes already stored on that capture's row. It does not refresh Neon after the fact and it does not issue a second Polygon GET at render time.

---

## 1. Exact template / render diff

### What `close.md` is

`lab brief close` writes `briefs/YYYY/MM/DD/close.md` via `artifact_relpath` in `packages/briefing/src/mm_briefing/store.py` (`kind` = `close`). The Sydney job calls that CLI with `--live --no-db` and uploads the file (`.github/workflows/hybrid-sydney-morning.yml`, step "Live US-close brief"). `lab deliver pack --from-markdown` sends that file. It does not re-render the price block.

### What decides the equity lines today

| Step | File | What it controls |
|---|---|---|
| Slot list | `packages/briefing/src/mm_briefing/models.py` `ASSET_ORDER` | `ES NQ US10Y DXY CL VIX BTC ETH` only. |
| Polygon tickers the brief fetches | `config/briefing/macro.yaml` `live.polygon.symbols` | `ES→SPY`, `NQ→QQQ`, `DXY→UUP`, `CL→USO`. `VIX` is structural unavailable. |
| Per-ticker range GET | `packages/briefing/src/mm_briefing/fetchers.py` `_fetch_polygon` / `_parse_polygon_aggs` | Last bar close and the prior bar in that range become `AssetPrint.last` / `prior_close`. |
| Morning body | `packages/briefing/src/mm_briefing/morning.py` `render_morning_close` | Assembles the pre block. Calls `_equity_t1_lines` then `_price_rows`. |
| Header | `morning.py` `_equity_t1_lines` (about lines 368–375) | One line: `EQUITY T-1 BY DESIGN (close YYYY-MM-DD)` when ES/NQ/DXY/CL share `expected_equity_session`. |
| Price rows | `morning.py` `_price_rows` (about lines 480–532) | Iterates `ASSET_ORDER` only. Pattern `{display_symbol} {fmt_px} {fmt_pct}` when the line is ≤ `PHONE_LINE_MAX` (42). |
| Display ticker | `models.py` `display_symbol` | Quoted proxy (`SPY`, `QQQ`, `UUP`, `USO`), not the slot id. |
| Call site | `packages/briefing/src/mm_briefing/render.py` `render_close` | Forwards into `render_morning_close`. No equity-name argument today. |
| Freeze | `docs/specs/brief-format-freeze.md` | Captures 1–11. Approved bytes: `ops/reports/renders/brief-template-dryrun.txt`. New panels are otherwise forbidden. This exception is the only add. |

The 16 names are **not** in `ASSET_ORDER` and **not** in `config/briefing/macro.yaml`. `_price_rows` cannot print them from data the brief snapshot does not hold.

### Where the 16 closes already are

`config/ingest/mvp_retain.yaml` `polygon.tickers`:

```
QQQ, CRCL, TSLA, SPCX, NVDA, BB, GLXY, IBIT, BMNR, MRNA, GOOG, HOOD, NOW, CBRS, MSTR, STRC, AMD
```

**Rank-eligible 16** = that list minus `QQQ` (QQQ is already the NQ proxy line):

`CRCL TSLA SPCX NVDA BB GLXY IBIT BMNR MRNA GOOG HOOD NOW CBRS MSTR STRC AMD`

`SPY` is the ES proxy on the brief. It is not a retain ticker and it is not one of the 16.

Those 17 closes (QQQ + 16) are fetched by `lab retain morning`, not by `lab brief close`:

- One Polygon grouped-daily GET: `/v2/aggs/grouped/locale/us/market/stocks/{date}` (`mvp_retain.yaml` call `polygon_grouped_daily`, `adjusted: true`).
- Filter in `packages/ingest/src/mm_ingest/mvp_retain.py` `_equity_envelopes` / `_filter_grouped`.
- One observation per ticker, `metric=close`, `source_name=polygon`, `source_url_or_id=grouped_daily:{ticker}`.
- Close number: grouped-daily field `c`, stored as `payload.value` (`mm_provenance.envelope.build_envelope` sets `payload["value"]`).
- Vendor bar time: grouped-daily field `t` → column `market_time`.
- Session date actually used: `payload.session_date`. If that walk used an earlier weekday, `payload.requested_session_date` is also set and `resolution` is `grouped_daily_prior_session` (row quality `STALE`).

C1–C3 deliver receipts each record `capture_rows: 75`. That is the full product (19 bound perps × 3 metrics + DRV `mid_px` + 17 equity closes). The closes were stored. They were not printed.

### Proposed change (print only)

Add a pure formatter, for example `packages/briefing/src/mm_briefing/equity_close_lines.py`, that takes the **already built** equity envelopes for this capture and returns pre-block lines. `render.py` `render_close` inserts those lines into the markdown **inside** the fence, after the existing `SPY` / `QQQ` rows and before the Hyperliquid perp block, then recomputes `content_hash`.

Do not add the 16 tickers to `config/briefing/macro.yaml`. That file drives a second per-ticker range fetch. Do not print `QQQ` again in this block.

Insert only when every printed name has, on **this** capture:

- `metric == close`
- `payload.session_date` equal to that row's `market_time` calendar date
- `payload.value` present
- `resolution` in `{grouped_daily, grouped_daily_prior_session}`

If any of the 16 is missing, print the names that have a close and put the absent ticker on the existing `gaps:` line. Do not pad a price. Do not invent `0.00%`.

`%` on the line, when shown, is the change from the **prior capture's stored close** for that same ticker (prior anchor, same `metric=close`) to this capture's `payload.value`. No prior close → print the level only. That `%` is display. Quant does not read it (bind 4).

### Before / after sketch

Pattern source for the existing rows: `tests/unit/test_brief_recorded_gate.py` asserts the recorded line `SPY 767.81 -0.72%`. Width model below uses that shape (`{TICKER} {px} {pct}`). Placeholders are not prices.

**Before** (current A1 price block; VIX stays on `gaps:`):

```
EQUITY T-1 BY DESIGN (close YYYY-MM-DD)
SPY 767.81 -0.72%
QQQ {px} {pct}
US10Y {yield} {bp}
UUP {px} {pct}
USO {px} {pct}
BTC {mid} {pct}
ETH {mid} {pct}
SOL …
… twelve further perp lines …
```

**After** (same header, same SPY/QQQ/macro/perp lines, 16 added lines, yaml order):

```
EQUITY T-1 BY DESIGN (close YYYY-MM-DD)
SPY 767.81 -0.72%
QQQ {px} {pct}
CRCL {px} {pct}
TSLA {px} {pct}
SPCX {px} {pct}
NVDA {px} {pct}
BB {px} {pct}
GLXY {px} {pct}
IBIT {px} {pct}
BMNR {px} {pct}
MRNA {px} {pct}
GOOG {px} {pct}
HOOD {px} {pct}
NOW {px} {pct}
CBRS {px} {pct}
MSTR {px} {pct}
STRC {px} {pct}
AMD {px} {pct}
US10Y {yield} {bp}
UUP {px} {pct}
USO {px} {pct}
BTC {mid} {pct}
ETH {mid} {pct}
SOL …
```

The date in the header remains the shared ES/NQ/DXY/CL bar date from `expected_equity_session`. The 16 lines print only when their `payload.session_date` is that same date. A retain walk that landed on a different session does not get printed as if it were that close.

No Entry, SL, TP, or "qualified trade" line is added. NO QUALIFIED TRADE stays as it is.

---

## 2. Character-budget impact

### Limits that exist in code and docs

| Limit | Where | Applies to |
|---|---|---|
| `PHONE_LINE_MAX = 42` | `morning.py` line 91; `_phone_wrap`; `_price_rows` | Every line inside the ``` fence. |
| `TELEGRAM_MAX_MESSAGE_CHARS = 4096` | `packages/delivery/src/mm_delivery/format.py`; `config/delivery/telegram.yaml` `max_message_chars` | One `sendMessage` after MarkdownV2 escape. |
| One chunk | `docs/specs/brief-v2.md`, `docs/specs/brief-card-split-deferred.md` | Morning path is one message. `chunk_markdown_v2` can split at 4096 with `[i/n]`; the morning product does not use that split. Cards stay deferred through capture 11. |
| Test fence `splitlines() < 80` | `tests/unit/test_brief_recorded_gate.py` | Test only. Not a Telegram cap. |

There is no separate character budget named "Snapshot", "close segment", or "A1 P1" in code. The one-message close shape is `docs/specs/brief-format-freeze.md` plus in-repo dry-run `ops/reports/renders/brief-template-dryrun.txt`. That file is the format-freeze brief bytes. It is not the DONCAPO A1 Day-7 dry-run (bind 2). The retain capture kind is `lab_snapshot` (`packages/provenance/src/mm_provenance/normalize.py` `SNAPSHOT_CAPTURE_KIND`). The close segment is the one pre block plus the `LATE` / `DEADMAN` / `CAPTURE` lines that `append_dm_status_lines` adds **outside** the fence (`apps/lab-cli/src/mm_lab_cli/deliver.py`).

### Measured and modeled

| Body | Characters | Lines |
|---|---|---|
| Format-freeze failure dry-run `brief-template-dryrun.txt` (Polygon/FRED missing; not A1) | 572 | 32 (max fence line 41) |
| Legacy comparison `brief-current-dryrun.txt` | 4923 | 75 — this is the **old** layout, already over 4096, not the format-freeze morning body |
| Recorded pattern line `SPY 767.81 -0.72%` | 17 | 1 |

Modeled rank-eligible line, same shape, 8-character price (`#####.##`) and 7-character percent (`-##.##%`):

- Shortest (`BB`, `NOW`): 19 characters.
- Longest (4-letter ticker): 21 characters.
- All 16 are under 42. No wrap, so no extra visual lines.
- 16 lines add about **348** characters including newlines (sum of modeled widths + one newline each).
- Failure dry-run 572 + 348 = **921**, headroom to 4096 of about 3,100 characters.

A full morning is larger than the failure dry-run (SPY/QQQ/US10Y/UUP/USO rows, funding lines that are off baseline, the `CAPTURE:` status line). Those pieces already ship inside 4096 today (`test_brief_recorded_gate.py` and `test_brief_morning_standing_rule.py` assert `len <= 4096` and a single chunk). Adding ~350 characters does not force truncation, a second `sendMessage`, or the card split.

`LATE`, `DEADMAN`, and `CAPTURE` stay outside the fence, in that order. They are not rearranged to make room.

The `< 80` lines assertion in the recorded-gate test should be raised or dropped in the print PR if a fat positioning block plus 16 lines crosses it. That is a test update, not a product restructure.

---

## 3. #124 allowlist / frozen deliver path

[#124](https://github.com/ElChopa11/market-memory/pull/124) is merged. It removed `workflow_dispatch` from `promote-gate.yml` and allowlisted that trigger to `hybrid-sydney-morning.yml` only (`tests/unit/test_workflow_dispatch_allowlist.py`, `docs/runbooks/host-dispatch.md`). The host script refuses any other workflow name.

### This exception does not touch

- `tests/unit/test_workflow_dispatch_allowlist.py`
- `.github/workflows/promote-gate.yml`
- `ops/host/dispatch-sydney-morning.sh`
- `ops/host/crontab`
- `workflow_dispatch` inputs (`i_mean_it_deliver`, `mode`)
- Group send (`TELEGRAM_CHAT_ID` must stay unset; `SEND_FROZEN` / `GROUP_SEND_FROZEN`)
- `lab deliver pack` flags: `--from-markdown`, `--to-principal-dm`, `--i-mean-it`, `--no-db`
- Completion commit scope (completions JSON only) or receipt commit scope (`completions/receipts/*.deliver.json`)
- Coinglass, chart, Entry/SL/TP, GMGN

Editing `hybrid-sydney-morning.yml` **job order** does not fail the #124 test. That test counts which files **declare** `workflow_dispatch`. It is not a path allowlist of edits inside the Sydney file. The print PR must not add `workflow_dispatch` on any other workflow.

### Minimal print-only file list

Required for the print:

| File | Why |
|---|---|
| `packages/briefing/src/mm_briefing/equity_close_lines.py` | **New.** Format lines from envelopes already in hand. |
| `packages/briefing/src/mm_briefing/render.py` | `render_close` inserts those lines and refreshes `content_hash`. |
| `tests/unit/test_equity_close_lines.py` | **New.** Session-date match, missing name → gap, line width ≤ 42, no second QQQ, no Entry/SL/TP. |

Required so the formatter sees **this** capture (see §4). Without it the brief still runs `--no-db` **before** retain, and the row does not exist yet:

| File | Why |
|---|---|
| `.github/workflows/hybrid-sydney-morning.yml` | Run `lab retain morning` **before** `lab brief close`. Pass the in-memory envelopes (temp file on the runner, not a git commit) into the brief. Commit scope stays completions/receipts. |
| `apps/lab-cli/src/mm_lab_cli/briefing.py` | Optional `--equity-from PATH` (still `--no-db`). Absent file → today's body, byte-for-byte. |

Required so the freeze text stays true, and so layout tests accept the new lines only when the equity payload is present:

| File | Why |
|---|---|
| `docs/specs/brief-format-freeze.md` | Record this exception: the 16 lines, nothing else, through capture 11. |
| `tests/unit/test_brief_recorded_gate.py` | Layout lock. No-payload path must still match today's A1. |
| `tests/unit/test_brief_morning_standing_rule.py` | Same. |
| `tests/unit/test_brief_morning_fixture_render.py` | Same. |

### Explicitly not in the minimal PR

- `packages/briefing/src/mm_briefing/morning.py` (core). See §4.
- `packages/briefing/src/mm_briefing/fetchers.py`
- `config/briefing/macro.yaml`
- `config/ingest/mvp_retain.yaml` (list is already correct)
- `packages/ingest/src/mm_ingest/mvp_retain.py` (fetch and row shape stay)
- `apps/lab-cli/src/mm_lab_cli/deliver.py` (status-line append stays; it sends the markdown it is given)
- `packages/delivery/**`
- Rank / scorecard / MIXED / Option A code. Those stay DEGRADED until a set2 pair exists. They are not this PR.

`engine.py` `generate_close` needs a pass-through of the equity envelopes into `render_close` if the CLI flag is wired there. That is argument plumbing, not a new fetch.

---

## 4. `morning.py` surface

**Core logic: no-touch.**

`morning.py` does not fetch. Fetch for the eight slots is `fetchers.py`. Fetch for the 16 is `mvp_retain.py` `capture_mvp_retain`. The live brief never calls `capture_mvp_retain`.

Core that stays unchanged:

- `expected_equity_session`, `_shared_session_date`, `_us_close_line`, `_equity_t1_lines`
- `_change_cell` / `no new session since` / `no new print since` for ES, NQ, DXY, CL, US10Y
- `_assets_for_health` and the health line
- `_price_rows` iteration of `ASSET_ORDER`
- Hyperliquid perp lines, funding baseline, positioning, `gaps:`
- `PHONE_LINE_MAX` and `_phone_wrap`
- `FORBIDDEN_RENDER_FRAGMENTS`

A separate module is enough. `render_close` post-processes the `BriefDocument` that `render_morning_close` already returned: insert lines inside the fence, recompute `content_hash` with `brief_hash`. `morning.py` can stay byte-identical.

Why the data is not already inside `morning.py`'s arguments: `generate_from_sources` builds one `MacroSnapshot` from the macro.yaml Polygon symbols, then `render_morning_close` prints `ASSET_ORDER`. The 16 closes live on the retain envelopes, which the workflow builds **after** the brief (`hybrid-sydney-morning.yml`: brief step, then "Morning MVP retain", then deliver). `lab brief close --no-db` does not open Neon.

### Feed and as-of fields (Skeptic precondition 4)

| Role | Field | What it is |
|---|---|---|
| Feed | Polygon grouped daily, `config/ingest/mvp_retain.yaml` call `polygon_grouped_daily` | One GET. Adjusted. Filtered to the 17 tickers. |
| Close | `payload.value` (from bar field `c`) | The number to print. |
| Equity session date | `payload.session_date` | The grouped-daily date that had bars, after the empty-body walk. |
| Vendor bar clock | column `market_time` (from bar field `t`) | Must be the same calendar date as `payload.session_date`. |
| Knowledge clock | `as_of_knowledge` = `ingested_at` = payload `captured_at` | When the lab stored the row (`docs/runbooks/mvp-retain.md`). **Not** the equity session date. Printing from this clock would be the wrong day. |
| Requested date, if the walk stepped back | `payload.requested_session_date` | Audit only. Do not print this date as the close date. |
| Capture kind | `payload.capture_kind` = `lab_snapshot` | Morning rows. Proof rows (`capture_kind=proof`) are not a morning print. |

`us_cash_session_date` (`mvp_retain.py`) asks for the last completed 16:00 America/New_York session. At 06:30 Australia/Sydney that instant is about 16:30 America/New_York the previous calendar day (AEST, UTC+10, through Fri 2 Oct 2026). `expected_equity_session` (`morning.py`) is the weekday **before** the brief's New York date, because the comment on that function says the just-closed grouped-daily bar is not on this Polygon tier at capture. The empty-body walk (`GROUPED_EMPTY_WALK`) is what lands `payload.session_date` on that earlier weekday. The print keys off `payload.session_date` + `market_time` of the row just built, and it prints only when that date equals the T-1 header date.

Allowed read: the envelopes `capture_mvp_retain` just returned, in the same job, before any later session exists.

Forbidden read: a later `SELECT` of the newest `close` for that ticker, a fresh Polygon GET inside the brief, or any bar whose `market_time` is after this capture's `payload.session_date`.

---

## 5. Scorecard seam (set1 vs set2)

Phase 6e `lab scorecard compare` is a different scorer (`docs/runbooks/scorecards.md`). Do not point it at this seam and do not invent scorecard numbers. The bar below is the capture bar: each set scored on its own mornings, same 3-of-10 rule, logged with the seam date.

### Do not rewrite set1

Set1 bodies stay equity **DEGRADED n=0**. The locked A1 artifact stays. Stored Neon closes for C1–C3 (the 75-row captures) are not a licence to reprint those mornings or to recompute set1 ranks.

Frozen A1 is the DONCAPO A1 Day-7 dry-run, not the format-freeze brief. Principal/Hive lock:

| Artifact | Path | sha256 |
|---|---|---|
| A1 Day-7 dry-run (set1 lock) | `/workspace/drafts/ops/dry-runs/6d5fab42cc6884b4/ping-mvp-a1.md` | `b5f33450ad9222d031b70cf060949688506dc59e906444dfb01a1930b78e86f1` |

That path is the box working surface. It is not in this git checkout (`drafts/` is absent here). Ops confirms the file on the box. Full pack `425ef905…` and A2 archive `7ddac5e1…` stay separate and are not this lock. Format-freeze bytes stay `ops/reports/renders/brief-template-dryrun.txt` (sha256 prefix `c693f077010d84e3`). Do not treat that file as A1. The recorded approval pair in `tests/fixtures/briefing/recorded_sydney_morning_20260924.json` is Actions runs `35967088240` then `36071921289` (those runs are before capture 1).

Morning rows do not get a `capture_id`. `run_morning_capture` sets `capture_id` only for proof (`mvp_retain.py`: `capture_id=capture_id if proof else None`). Set identity is the Sydney anchor plus the deliver receipt `run_id`.

### Set1 — already run (equity DEGRADED n=0)

| Capture | Sydney morning | `scheduled_anchor_ts` | Delivered `run_id` | `capture_rows` |
|---|---|---|---|---|
| C1 | Mon 28 Sep 2026 | `2026-09-27T20:30:00+00:00` | `actions-b1-36348252592` | 75 |
| C2 | Tue 29 Sep 2026 | `2026-09-28T20:30:00+00:00` | `actions-b1-36479629926` | 75 |
| C3 | Wed 30 Sep 2026 | `2026-09-29T20:30:00+00:00` | `actions-b1-36626767952` | 75 |

Receipts: `ops/reports/scheduler/completions/receipts/grok.sydney_morning__20260927T203000Z.deliver.json` (and the `0928` / `0929` siblings). Later stamp files on the same anchor (including `actions-b1-36654724512`) are extra stamps. The delivered receipt is the set1 id.

**Seam log:** set1 closed at C3. Seam date **2026-09-30**. Set1 score uses n=3 mornings, all equity DEGRADED n=0. That is not a 10-morning sample. Do not write it up as 3-of-10 with a denominator of 10.

### Set2 — not started

Set2 is the first `grok.sydney_morning` fire whose checked-out `main` contains the print, and every capture after that. This memo does not land the print, so **C4 is not set2** unless a later implementation is on `main` before that fire.

Freeze window (`brief-format-freeze.md`): capture 1 Mon 28 Sep 2026 through capture 11 Mon 12 Oct 2026. Weekdays only. Mon 5 Oct 2026 (NSW Labour Day) still fires (`docs/runbooks/host-dispatch.md`). DST starts Sun 4 Oct 2026; the host cron stays 06:30 Australia/Sydney.

| Capture | Sydney date | Anchor (UTC) | Inside freeze |
|---|---|---|---|
| C4 | Thu 1 Oct 2026 | `2026-09-30T20:30:00Z` | yes |
| C5 | Fri 2 Oct 2026 | `2026-10-01T20:30:00Z` | yes |
| C6 | Mon 5 Oct 2026 | `2026-10-04T19:30:00Z` (AEDT, UTC+11) | yes |
| C7 | Tue 6 Oct 2026 | `2026-10-05T19:30:00Z` | yes |
| C8 | Wed 7 Oct 2026 | `2026-10-06T19:30:00Z` | yes |
| C9 | Thu 8 Oct 2026 | `2026-10-07T19:30:00Z` | yes |
| C10 | Fri 9 Oct 2026 | `2026-10-08T19:30:00Z` | yes |
| C11 | Mon 12 Oct 2026 | `2026-10-11T19:30:00Z` | yes (last frozen morning) |

### How many set2 mornings

Assumption A — print is on `main` before C4 (Thu 1 Oct 2026 06:30 Australia/Sydney):

- Set2 inside the freeze: **C4–C11 = 8 mornings.**
- First adjacent pair that can clear equity ranks: **C4+C5** (Thu–Fri), and only if both printed all 16 names. C4 alone does not clear.
- A full 10-morning set2 starting at C4 runs C4–C13 and ends **Wed 14 Oct 2026**, which is **after** capture 11. Two of those ten mornings sit outside the freeze window.

Assumption B — merge slips past C4, first set2 morning is C5 (Fri 2 Oct):

- Inside the freeze: **C5–C11 = 7.**
- First possible pair: C5+C6 (Fri–Mon), still only if both print the same 16.
- 10 mornings would end Thu 15 Oct 2026.

Assumption C — first set2 morning is C6 (Mon 5 Oct) or later:

- Inside the freeze: **6 or fewer.** A 10-morning set2 is then entirely past the point where the freeze window can hold it.

**Plain statement:** a 3-of-10 bar needs 10 mornings in the denominator. Set2 does not have 10 mornings left inside the capture-11 window under any of these assumptions. Eight (or fewer) mornings can be logged as their own n. They cannot be scored as 3-of-10 and then compared with a 10-morning set. Set1 is n=3, also not a 10-morning score. Score each set on the mornings it actually has. Do not pad.

Quant adjacency still applies inside whatever set2 exists: one printed morning does not clear Top5/Bottom5. A gap (failed print, missing name, or a capture that did not fire) breaks the pair. MIXED/Option A waits for that pair and then uses ln-returns of the printed closes only.

### Seam capture log (fill when the print actually ships)

| Field | Value |
|---|---|
| Seam date | 2026-09-30 (this scope). Implementation seam date = the Sydney date of the first set2 morning, written when that fire exists. |
| Set1 ids | C1 `actions-b1-36348252592`, C2 `actions-b1-36479629926`, C3 `actions-b1-36626767952` |
| Set1 equity | DEGRADED n=0. Bodies not rewritten. |
| Set1 A1 | `ping-mvp-a1.md` sha256 `b5f33450ad9222d031b70cf060949688506dc59e906444dfb01a1930b78e86f1` (box path, not in git) |
| Set2 ids | empty until the first printed morning |
| Bar | same 3-of-10 rule, scored independently, denominator = mornings in that set |
| Ranks | equity Top5/Bottom5 stay DEGRADED until the first adjacent set2 pair |

---

## Out of scope (stays frozen)

Coinglass HELD. Chart STAND_BY. No Entry/SL/TP. Message shape A1 (one `sendMessage`, cards deferred). GMGN parked. No live trading. No group send. No `workflow_dispatch` outside `hybrid-sydney-morning.yml`. No rewrite of C1–C3 `close.md`. No rank recompute on set1. No sizing. No scan-gate.
