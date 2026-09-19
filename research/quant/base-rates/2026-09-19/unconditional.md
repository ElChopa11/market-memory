# Unconditional event-class base rates (2026-09-19)

- **Desk:** Quant · sleeve `base_rate`
- **as_of_knowledge:** 2025-09-06T00:00:00+00:00
- **ingested_at:** 2025-09-06T00:00:00+00:00 (lockstep)
- **params_hash:** `c4b98fb1c15150e09473e393888663fcbe4bb9a5bd39d57fe66409cdc7a71682`
- **content_hash:** `1e040909719f4a252f14041b54ef70bd439d456c4a7e86862e83174796184949`
- **fixture_id:** imp039-unconditional-v1
- **instrument set:** BTC, NVDA
- **window:** 2022-01-01 .. 2026-09-18 (daily_completed)
- **cost model:** taker_fee*2 + slippage_bps/1e4*2 + funding_rate*(expected_hold_hours/24) (clip is not a size)
- **survivorship:** survivorship_uncontrolled
- **status:** OK

## Rates

- **dip_touch** (no claim) n=6 n_min=20 n_censored=0 hit_rate=n/a median_signed_fwd=n/a mean_R_after_cost=n/a → cites C-002. n below configured minimum; no base-rate claim
- **zone_boundary_touch** (no claim) n=8 n_min=20 n_censored=0 hit_rate=n/a median_signed_fwd=n/a mean_R_after_cost=n/a → cites C-001. n below configured minimum; no base-rate claim
- **pullback_ema_touch** (no claim) n=2 n_min=20 n_censored=0 hit_rate=n/a median_signed_fwd=n/a mean_R_after_cost=n/a → cites C-003. n below configured minimum; no base-rate claim

## How C-001 / C-002 / C-003 cite this pack

- C-001 (supply/demand zone) cites `zone_boundary_touch` as the unconditional range-boundary class. Extra filter: X·ATR departure confirm.
- C-002 (triple RSI MR) cites `dip_touch` as the unconditional SMA20-uptrend dip class. Extra filter: three RSIs ≤ Z.
- C-003 (second-entry pullback) cites `pullback_ema_touch` as the first-entry class. Extra filter: second pullback + trigger.
- A later study records `delta vs event_base_rate.params_hash` + `as_of_knowledge`. It does not recompute these rates.

## Gaps

- none

Unconditional event-class base rates. Paper only. Not a call. DO NOT SIZE. Not a scan-gate. Not a C-001/C-002/C-003 study. n < n_min → no claim. Knowledge clock is as_of_knowledge (lockstep ingested_at). Never published_at / market_time.
