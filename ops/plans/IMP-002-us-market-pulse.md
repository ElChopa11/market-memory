# PLAN — IMP-002 US Market Pulse vertical slice

**Report status:** PR READY  
**Owner:** Don (Macro & Cross-Asset Desk)  
**Scope:** read-only US pre-market Pulse on existing `mm_briefing` / `lab brief preopen`. No orders, wallets, live keys, Quant Board rewrite, watchlist recommendation loops, or risk/execution services.

Revives closed PR #29 (`cursor/phase2-us-pre-market-pulse-d645`) onto current `main` (IMP-000 #28 + IMP-001 #31). Repo-phase naming still calls Market Pulse “Phase 3”; this is the **Principal Phase 2** brief DoD on that substrate.

## Why

Pulse exists as code and a runbook, but it was not operated as a Macro desk product with NY/Sydney clocks, DST session status, per-source `fresh|stale|partial|unavailable`, always-listed cross-asset slots, and an explicit no-decision footer.

## Path choice (dual-write, copy not symlink)

| Role | Path |
|---|---|
| DoD / canonical pre-market artifact | `briefs/YYYY-MM-DD/us-pre-market.md` |
| Legacy (tests + close/alert) | `briefs/YYYY/MM/DD/{preopen,close,alert}.md` |

Same markdown bytes in both pre-open files. Close/alert stay on the legacy layout only. Dated output remains gitignored except one committed **sample** on the DoD path.

## Reuse (do not fork a briefing stack)

- Session / DST: `packages/briefing/src/mm_briefing/schedule.py` (`us_session_status`, `prior_us_cash_close`)
- Models / quality: `models.py` — pulse display `fresh|stale|partial|unavailable`; required slots
- Macro: `fetchers.py` — never invent; missing key/HTTP → unavailable/partial
- Calendar: `calendar.py` + `config/briefing/calendar.yaml` (attributable source)
- HL: `hl.py` — memory first (`what_did_we_know`); `--live` fallback via allowlisted `/info` only
- Render / store / engine / CLI: `render.py`, `store.py`, `engine.py`, `lab brief preopen --live`
- Knowledge clock: `as_of_knowledge` lockstep with ingest/capture; never `published_at` / `market_time` as the watermark

## Sources (approved, read-only)

| Slot | Proxy | Source | Credentials |
|---|---|---|---|
| crypto | BTC, ETH | CoinGecko public price (`--live`) | none |
| equity-index proxy | ES, NQ | Stooq public CSV | none |
| rates | US10Y | FRED `DGS10` | `FRED_API_KEY` — else **unavailable** |
| USD | DXY | Stooq `dx.f` | none |
| oil | CL | Stooq `cl.f` | none |
| vol | VIX | Stooq `^vix` | none |
| calendar | events | `config/briefing/calendar.yaml` | none — empty window is honest |
| HL structure | BTC, ETH | Market Memory, else public `/info` allowlist | none |

Default `config/briefing/macro.yaml` `mode: off` is unchanged so fixture hashes stay deterministic.

## Tests

DST session status (spring-forward + fall-back); missing/stale/unavailable display; provenance + watermark + footer; dual-write paths; required slots always listed; HL client refuses user/wallet types; briefing tree does not import `mm_execution` / `hl_trade`. Frozen goldens updated with the renderer.

## Explicit deferral

Standing **cross-asset regime note** (distinct from Pulse) is **deferred**. This slice is the US pre-market brief + desk cadence on Pulse. Regime note is not invented here.

## Non-goals

Quant Board (IMP-001, DONE); watchlist recommendation loops; live.yaml / risk-limit edits; execution/signing; live economic-calendar API; silent FRED default.

## Limitations

- No live calendar API; events come only from the YAML.
- Stooq/CoinGecko/FRED are not written into Market Memory in this slice.
- `--live --no-db` HL capture is not indexed (observation ids `none` + `/info` type URL).
- Watchlist block remains existing substrate; this item does not expand it.
