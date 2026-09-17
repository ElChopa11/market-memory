# Intent

- **Thesis id:** THESIS-0001-post-fomc-btc-funding
- **Backlog id:** RQ-20260917-A
- **Goal (one sentence):** Determine whether, after the Sep 2026 FOMC +25bp hike to 3.75–4.00% with a further-tightening signal, BTC perp funding and premium still underprice the hawkish path relative to mid alone.
- **Why now / trigger observation ids:**
  Observation IDs below are copied verbatim from `docs/ops/rq-20260917-a-ingest-report.md` (PR #8); that report is the ID source of truth. Do not invent or alter IDs.
  - Macro / policy (durable MM):
    - `01M2PCX8ZJZCKC52NQ03PHNZWE` — Fed FF target range 3.75–4.00%
    - `01M2PCX9005R4S8GRPQJP96CRP` — IORB 3.90%
    - `01M2PCX90C2J9RPG17CSZDTV3Q` — primary credit 4.00%
    - `01M2PCX90PQAP96J62RR6EWQ35` — FOMC +25bp, 12–0
    - `01M2PCX91243QK9V8HCCWQFASY` — Reuters further-tightening coverage (`dq=partial`)
  - BTC Hyperliquid context (durable MM) — latest lab snapshots (`market_time` NULL; `data_quality=contradicted` vs earlier poll, still valid as latest):
    - `01M2PCXAFASC2V0WCGWR0E8MZT` — BTC funding
    - `01M2PCXAFMC3792Y1PQ3H2ACVQ` — BTC open_interest (premium −0.0004837866 in raw)
    - `01M2PCXAEE4BRXTPMV56SYN56V` — BTC mark_px
    - `01M2PCXAEY18W6290P82NECSM7` — BTC oracle_px
    - `01M2PCXACWWCDJRR2GJ20RV7D4` — BTC mid_px
  - Context (not primary trigger): ETH funding `01M2PCPEK2ZXFDKPK0TDZZZ5M4`
  - Series already in the ingest TSV / report (not extra trigger IDs): BTC `fundingHistory` 168×1h and BTC `candleSnapshot` 170×1h. Inventory: `docs/ops/rq-20260917-a-observation-ids.tsv` on PR #8.
- **Draft hypothesis (intent-level only — not a thesis):** After the Sep FOMC +25bp to 3.75–4.00% with a further-tightening signal, BTC perp funding/premium may still underprice the hawkish path vs mid alone.
- **Instrument (v1):** BTC perp (ETH funding as context only)
- **Horizon sketch:** 1–5 sessions
- **Out of scope:**
  - Mid-only mean-reversion theses
  - Live trading / order intent / risk approval
  - Writing `thesis.md`, `research-plan.md`, or evidence packs until a separate thesis assign after DoD-to-thesis gates clear
  - Using provisional `claim_hash_lab` / Intel candidate IDs as if they were Market Memory observation IDs
- **Definition of done for moving to thesis:**
  1. Use the BTC `fundingHistory` 168×1h series (and `candleSnapshot` 170×1h if needed) already inventoried in `docs/ops/rq-20260917-a-ingest-report.md` if the current single funding snapshot is insufficient for a falsifiable claim; do not treat this intent as a new ingest request
  2. Skeptic-ready claim: explicit hypothesis, why market may be wrong/late, catalyst, expected path
  3. Hard invalidation criteria (price/funding/premium conditions)
  4. Instrument, liquidity, and risk plan (size/horizon bounds for paper later — not live)
  5. Separate Coordinator thesis assign (this intent alone does not authorize thesis.md)
- **Owner:** Research
- **opened_at:** 2026-09-17 (Australia/Sydney)
- **deadline:** TBD (Coordinator)
- **Instrument universe (v1 default BTC + ETH perps):** BTC primary; ETH context only
- **Status:** draft
