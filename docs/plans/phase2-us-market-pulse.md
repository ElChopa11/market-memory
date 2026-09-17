# Principal Phase 2 — US pre-market pulse (vertical slice)

Aligns existing Market Pulse (`mm_briefing`, `lab brief preopen`, briefing-worker) to the Principal Phase 2 DoD. Does **not** reopen watchlists, active_calls, MAKE/WATCH/CUT, risk, or trading. Phase 1 durability/PIT clocks stay untouched.

Repo-phase naming: this tree already calls Market Pulse “Phase 3”. This plan is the **Principal** Phase 2 brief DoD on that substrate — not a parallel stack.

## Path choice

**Dual-write (copy, not symlink):**

| Role | Path |
|---|---|
| DoD / canonical pre-market artifact | `briefs/YYYY-MM-DD/us-pre-market.md` |
| Legacy (keep tests + close/alert) | `briefs/YYYY/MM/DD/{preopen,close,alert}.md` |

Same markdown bytes in both pre-open files. Close/alert stay on the legacy layout only. Dated output remains gitignored except one committed **sample** at the DoD path (Principal asked for a sample in the PR).

## Files (extend, do not fork)

| Area | Files |
|---|---|
| Plan | `docs/plans/phase2-us-market-pulse.md` (this file) |
| Session / DST | `packages/briefing/src/mm_briefing/schedule.py` — `us_session_status`, `prior_us_cash_close` |
| Models | `packages/briefing/src/mm_briefing/models.py` — pulse quality `fresh\|stale\|partial\|unavailable`; per-print as-of/source; required cross-asset slots |
| Macro | `packages/briefing/src/mm_briefing/fetchers.py` — never invent; missing key/HTTP → unavailable/partial; capture time ≠ exchange time |
| Calendar | `packages/briefing/src/mm_briefing/calendar.py` + `config/briefing/calendar.yaml` — attributable source `config/briefing/calendar.yaml` |
| HL | `packages/briefing/src/mm_briefing/hl.py` — memory first (`what_did_we_know`); `--live` fallback via `HyperliquidInfoClient` allowlist only |
| Render / store / engine | `render.py`, `store.py`, `engine.py` |
| CLI | `apps/lab-cli/src/mm_lab_cli/briefing.py` — `lab brief preopen --live` |
| Docs | `docs/runbooks/market-pulse.md`, `briefs/README.md` |
| Tests | `tests/unit/test_brief_*.py`, `tests/unit/test_hl_info_client.py`; refresh frozen goldens |
| Sample | `briefs/<session-date>/us-pre-market.md` (force-added) |

No new agents, no `mm_execution`, no wallet/user HL types, no schema migration (brief `data_quality` storage stays `ok\|stale\|partial\|…`; **display** maps `ok→fresh`, missing→`unavailable`).

## Sources (approved)

| Slot | Source | Credentials |
|---|---|---|
| Crypto (macro print) | CoinGecko public price (opt-in `--live`) | none |
| Equity-index proxy | Stooq public CSV: ES, NQ | none |
| USD | Stooq `dx.f` (DXY) | none |
| Oil | Stooq `cl.f` (CL) | none |
| Volatility | Stooq `^vix` (VIX) | none |
| Rates | FRED `DGS10` (US10Y) | `FRED_API_KEY` — else **unavailable** |
| Calendar | `config/briefing/calendar.yaml` (`source: fixture`) | none — empty window is honest, not invented |
| HL structure | Market Memory observations ingested from public `/info`; live fallback `metaAndAssetCtxs` (+ optional `recentTrades` liqs) | none; client allowlist |

Default `config/briefing/macro.yaml` `mode: off` is unchanged so fixture hashes stay deterministic. `--live` enables the configured public maps (stooq/coingecko) and FRED (degrades without a key).

## Data-model changes (briefing only)

- `AssetPrint`: `as_of`, optional `observation_id`; missing required symbols filled as `unavailable` (not omitted).
- `CalendarEvent.source` attributed in the brief.
- `HLMetric.as_of_knowledge` + `source_url`; snapshots label capture/`ingested_at`, never disguise as `market_time`.
- Brief header: generation clocks in `America/New_York` and `Australia/Sydney`; US session status (pre-market / RTH / after-hours / overnight / weekend) via `zoneinfo` (DST in the tzname).
- Memory watermark = `as_of_knowledge` passed to `what_did_we_know` (or “live /info capture, not indexed” when `--no-db --live`).
- Footer: explicit no-decision / informational only.

## Tests

1. **TZ/DST:** spring-forward 2026-03-08 and fall-back 2026-11-01; session status around 08:00/09:30/16:00 ET; prior close is previous weekday 16:00 ET.
2. **Missing/stale:** omitted source → `unavailable` row still listed; stale labeled; FRED missing key → US10Y unavailable, not invented.
3. **Provenance:** every printed figure has source and as-of; HL lines keep observation ids (or explicit `none` + `/info` type); watermark in header.
4. **No-trading:** `HyperliquidInfoClient` still refuses forbidden types (extended list); live HL helper only POSTs allowlisted types; brief footer present; no buy/sell/size language.
5. **Paths:** preopen writes both DoD and legacy files with identical bytes.
6. Frozen fixture hashes/goldens updated with the renderer (intentional).

## Acceptance

- `lab brief preopen --fixture tests/fixtures/briefing/frozen_day.json --no-db` still deterministic.
- `lab brief preopen --live --no-db` hits real public HL `/info` + configured macro HTTP; missing creds → unavailable/partial; writes `briefs/YYYY-MM-DD/us-pre-market.md`.
- Sample brief committed on the DoD path.
- `uv run pytest` and `./scripts/check-lifecycle.sh` green.
- Live trading remains hard-gated; briefing does not import execution/signing.

## Limitations

- No live economic-calendar API is configured; today’s events come only from the attributable YAML (often empty for a real date — shown, not invented).
- Stooq/CoinGecko/FRED are not written into Market Memory in this slice; only HL ingest is retained observations. Macro prints cite HTTP source + capture/quote as-of.
- Live HL without Postgres is a public `/info` capture (watermark = capture time), not a memory index. With DB, `hl_from_memory` is preferred.
- Watchlist block remains as existing substrate; this PR does not expand it.
