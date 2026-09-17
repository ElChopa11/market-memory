# Skeptic review — UNIVERSE-20260917 call cards

| Field | Value |
|---|---|
| **Artifact under review** | `research/queue/UNIVERSE-20260917-call-cards.md` |
| **Source PR** | https://github.com/ElChopa11/market-memory/pull/13 · branch `cursor/universe-20260917-call-cards-fd40` |
| **Prior skeptic** | `research/queue/UNIVERSE-20260917-skeptic-review.md` (PR #11) — shortlist **0/12/8** |
| **Reviewer** | Skeptic (independent of Research author) |
| **Reviewed at** | 2026-09-17 (Australia/Sydney, AEST) |
| **Scope** | Intent-level call cards for Principal-locked 12 — **not** theses, not orders, not risk. |
| **Stance** | Prefer **revise / reject**. No rubber stamps. No trading credentials. |

## Verdict summary

| Bucket | pass | revise | reject |
|---|---:|---:|---:|
| Crypto (4) | 0 | 2 | 2 |
| Equities (8) | 0 | 7 | 1 |
| **Total (12)** | **0** | **9** | **3** |

**Overall: REVISE the call-card pack** — Research absorbed PR #11 feedback (roles, conf haircuts, single-trigger language, no aggressive longs). That is real progress. It is **not** a pass: several cards still carry already-priced expectations, compound (weak) invalidations, empty evidence packs, or horizon mismatch between “1–5 sessions: no edge” and “this cycle IF…”.

### Rejects (remove from active call pack / demote to deferred note)
- **UNI** — event-gated card with **no dated event**; 90-day fishing clock
- **AAVE** — liquidity trap + rate→credit leap + invalidation baseline missing
- **SMH** — not an independent call while NVDA+AVGO remain; triple-count dressed as basket

### Revise-gated keepers (9)
BTC, ETH, NVDA, AVGO, MSFT, META, JPM, XLF, XOM

---

## Checklist applied (every card)

1. **Already-priced expectation** — is the “expected path” just consensus post-FOMC / post-narrative?
2. **Weak invalidation** — AND-compounds, undefined baselines, non-observable, too hard to trigger
3. **Horizon mismatch** — 1–5 session path vs cycle path vs invalidation window incoherent
4. **Narrative without evidence** — still-need list is the entire thesis
5. **Conflict with hawkish Fed frame** — upside that needs cuts / duration / gold-like behavior under hikes
6. **Overconfident conf** — score above what cited evidence supports

---

## Cross-cutting findings

1. **Progress vs PR #11 (credit, not a pass).** Theme roles (NVDA primary / AVGO satellite / SMH basket; JPM primary / XLF diversifier), conf ≤ shortlist, zero aggressive longs, BTC ≠ RQ-A separation, and numeric invalidation attempts are material upgrades. Skeptic still finds **0 passes**.
2. **AND-compound invalidations = weak kills.** BTC, ETH, META (and SMH’s overlap AND) require multiple conditions simultaneously. That protects the call from dying. Fix: **one primary observable**; move the rest to secondary monitors.
3. **“Speculative / gates empty” on every cycle path.** Honest labeling does not create a call. If field 3 says no near-term edge and field 7 says gates empty, the card is a **watch memo**, not a call — conf should sit in the **0.20–0.35** band unless primary evidence exists.
4. **1–5 session vs cycle horizon mismatch.** Most cards: near-term = drift / already reflected; cycle = conditional upside. Invalidations often sit at next earnings / 20–90 days. Fine if explicit; several still smuggle cycle hope without a mispricing angle (NVDA, MSFT, META, JPM).
5. **Evidence quality unchanged for equities.** Fool/MarketBeat/Yahoo/blog problems are *disclosed* but not *replaced*. Disclosure ≠ cure.
6. **Hawkish frame:** Pack correctly avoids “hawkish = crypto up.” Residual tension: mega-cap AI/quality longs under higher WACC without proving ROI/capex durability (MSFT/META/NVDA).

---

## Crypto — card-by-card

### 1. BTC — **revise**
- **Already-priced:** Correctly states hawkish + CLARITY fail are public. Residual risk: “legislative path after cloture fail” still appears as a falsifiable driver — that is hope after a known fail (same flaw as rejected XRP, diluted).
- **Weak invalidation:** Primary is **triple AND** (≥5d ETF outflows **and** funding ≥ +0.01%/8h **and** OI$ −15%). Hard to trigger; misses clean ETF-outflow kill. Split: primary = ETF outflow streak alone; funding/OI = secondary crowded-unwind monitors.
- **Horizon mismatch:** 1–5 sessions = range (OK) vs cycle path gated on empty ETF/basis series — OK if conf stays low.
- **Narrative-without-evidence:** Gates empty (own field 7) — acceptable for benchmark **only** if call stays watch-only (it mostly does).
- **Hawkish frame:** Passes (explicitly not hawkish-Fed-up).
- **Conf:** 0.45 slightly rich for empty ETF/fundingHistory gates on anything beyond pure benchmark. Prefer **≤0.40** until series exist.
- **Required revise:** (1) Single-trigger primary invalidation. (2) Drop legislative revival from active drivers until dated bill calendar exists. (3) Conf ≤0.40.

### 2. ETH — **revise**
- **Already-priced:** Duration-compression / BTC-beta is consensus; RV frame is the only non-lazy angle.
- **Weak invalidation:** ETH/BTC −8% over 20d **and** ETF outflows ≥5/10 — AND again. Either underperformance **or** flow failure should kill.
- **Horizon mismatch:** Invalidation at 20d vs 1–5 session “tracks BTC” — mild; state that RV edge is **not** a 1–5 session call.
- **Narrative-without-evidence:** OI/mark ULIDs still missing; ETF + L2 still need. RV claim without OI series is half-built.
- **Hawkish frame:** OK (conditional RV, not beta long).
- **Conf:** 0.40 OK-ish; prefer **≤0.35** until ETH OI/mark ingested.
- **Required revise:** Break AND invalidation; ingest OI/mark before any RV promotion language; conf haircut.

### 3. UNI — **reject**
- **Already-priced:** Fee-switch is multi-year recycled (own text) — market has priced delays.
- **Weak invalidation:** “No dated proposal within 90 days” is a clever kill, but starting a 90-day clock **with no proposal on the horizon** is process theater — the base case (indefinite delay) is already true on day 0.
- **Horizon mismatch:** 1–5 sessions = no edge; cycle = binary re-rate on undated catalyst — pure optionality narrative.
- **Narrative-without-evidence:** No dated primary source; no UNI funding obs; HL ranks file-only. Field 7 is the whole card.
- **Hawkish frame:** Not claimed as hawkish-cycle beta (good) — still fails as an active call.
- **Conf:** 0.32 still high for a card that should be **deferred**, not called.
- **Reject reason:** Event-gated call without an event. Demote to deferred governance watch; revive only when a **dated** proposal with executable parameters exists. Do not burn a locked-universe slot on fishing.

### 4. AAVE — **reject**
- **Already-priced:** DeFi credit blue-chip; rate→utilization story not shown in data.
- **Weak invalidation:** Utilization −25% from “latest published dashboard print” — **baseline not cited**. Cannot falsify against a missing print. Bad-debt clause is fine as secondary.
- **Horizon mismatch:** 30d utilization window vs micro dayNtl ~$13M — research size unclear; exit trap (OI$ vs dayNtl) unresolved.
- **Narrative-without-evidence:** Rate→credit leap explicitly still a Skeptic key flaw; dashboards still need; no funding obs.
- **Hawkish frame:** Claims higher-for-longer **helps** crypto credit — conflicts with risk-off crypto under hawkish tape unless utilization proves independence from BTC beta (own “change mind” admits this).
- **Conf:** 0.30 still too high for reject-class liquidity + empty mechanism.
- **Reject reason:** Liquidity trap + unfixed causation leap + non-operational invalidation baseline. Micro-size research note ≠ call card. Cut from active pack until utilization/revenue obs-linked **and** dayNtl tier improves.

---

## Equities — card-by-card

### 5. NVDA — **revise**
- **Already-priced:** Own text: post-FOMC multiple embeds hyperscaler capex; extreme crowded. Expected cycle path still needs “documented mispricing” that **is not present**.
- **Weak invalidation:** Named hyperscaler capex **cut** — good single trigger. Secondary risk: ignores NVDA-specific miss while hyperscalers hold (add secondary, keep primary).
- **Horizon mismatch:** 1–5 sessions = crowded unwind risk (defensive) vs cycle upside without mispricing angle — mismatch.
- **Narrative-without-evidence:** Fool/MarketBeat still the cited pack (disclosed, not replaced). Field 7 still blocks thesis — then conf 0.48 is unsupported.
- **Hawkish frame:** “Survives only if capex holds” = circular under higher WACC.
- **Conf:** **Overconfident** at 0.48 with zero primary filings. Prefer **≤0.38** until 10-Q/transcript extract exists **and** a written mispricing angle (what Street wrong).
- **Required revise:** Replace secondaries; write explicit mispricing sentence or drop cycle upside; conf haircut; keep primary invalidation.

### 6. AVGO — **revise**
- **Already-priced / crowded:** Consensus ASIC+networking; high corr to NVDA admitted.
- **Weak invalidation:** AI semi guide cut — good, independent of NVDA tape (credit).
- **Horizon mismatch:** 1–5 sessions residual vs cycle satellite add — OK if size priority << NVDA (state max relative size).
- **Narrative-without-evidence:** Still shares Fool pack with NVDA; backlog cash-conversion unshown.
- **Hawkish frame:** “Less fatal if backlog converts” unproven.
- **Conf:** 0.42 too close to NVDA primary for a satellite on shared weak evidence. Prefer **≤0.32**.
- **Required revise:** Independent evidence pack mandatory; conf ≪ primary; explicit size cap vs NVDA.

### 7. SMH — **reject** (as an active call)
- **Already-priced:** Street’s default AI-infra ETF — definitional, not edge (own text).
- **Weak invalidation:** NVDA+AVGO weight ≥45% **and** NVDA kill — weight gate is likely already true most of the time, so it collapses to NVDA’s invalidation (OK as auto-link) but does not justify a separate call.
- **Horizon mismatch:** Basket “outperforms if buildout broadens” is vague cycle narrative.
- **Narrative-without-evidence:** Holdings weights / overlap % still need — cannot even measure the double-count you disclose.
- **Hawkish frame:** Same AI-infra WACC tension as NVDA.
- **Conf:** 0.35 still implies an active research object.
- **Reject reason:** With NVDA primary + AVGO satellite locked, SMH is **redundant alpha** (Skeptic xor preference). Keep as optional **overlap monitor appendix**, not a 12th call card. Principal may re-add only under explicit hedge mandate with published overlap % and size ≪ singles.

### 8. MSFT — **revise**
- **Already-priced:** Fortress / Azure AI under higher rates = consensus institutional overweight.
- **Weak invalidation:** Azure CC growth −300 bps QoQ — good numeric single trigger (credit). Ensure definition matches MSFT’s disclosed Azure metric exactly (constant-currency vs other).
- **Horizon mismatch:** 1–5 sessions = quality drift (no edge) vs cycle = multiple holds — already-priced expectation dressed as path.
- **Narrative-without-evidence:** Macro-only cites; no Azure print (own admission).
- **Hawkish frame:** Quality-outperforms-under-hikes is factor folklore without MSFT proof here.
- **Conf:** 0.44 **overconfident** with zero Azure extract. Prefer **≤0.35**.
- **Required revise:** Earnings extract before conf >0.35; state near-term expected path as **no edge / watch earnings** only.

### 9. META — **revise**
- **Already-priced:** Ads + AI ROI 2024–26 consensus.
- **Weak invalidation:** Ad miss **and** capex raise/refuse-to-cut without ROI KPIs — AND compound weakens kill. Prefer: ad guide miss **or** capex up without ROI KPI disclosure.
- **Horizon mismatch:** High-beta 1–5d vs cycle re-rate on beats — standard, but no edge specified vs Street.
- **Narrative-without-evidence:** Zero ARPU/DAU/capex on sheet.
- **Hawkish frame:** Solvency ≠ upside under higher WACC (own text) — then cycle path should not imply re-rate.
- **Conf:** 0.38 still rich. Prefer **≤0.30** until extracts exist.
- **Required revise:** Break AND invalidation; conf haircut; require “beat vs embedded consensus” quantification or drop cycle upside.

### 10. JPM — **revise**
- **Already-priced:** Own text: most obvious post-FOMC/SEP bank read; crowded; 1–5 sessions may already reflect SEP. Cycle upside = NII beats what SEP embeds — **mispricing undefined**.
- **Weak invalidation:** NII miss **or** NCO +20 bps — good OR structure (credit). Keep.
- **Horizon mismatch:** Near-term no residual edge vs cycle residual — honest; then conf should reflect “wait for print,” not candidate leadership.
- **Narrative-without-evidence:** NII guide + charge-offs still need; JPM AM marketing insight ≠ company NII guide.
- **Hawkish frame:** Mechanism OK (FF → NII).
- **Conf:** **0.48 overconfident** for a “likely priced” card with missing NII print. Prefer **≤0.40**.
- **Required revise:** Write explicit SEP-implied vs guide gap test; conf haircut; until print, label **earnings-watch**, not strongest candidate.

### 11. XLF — **revise**
- **Already-priced:** Same financials hike trade as JPM.
- **Weak invalidation:** JPM kill **or** KRE −10% / 20d — workable; KRE leg needs CDS/stress definition tightened (what counts as “rising regional CDS”).
- **Horizon mismatch:** Tracks JPM near-term — diversifier value unproven in 1–5d.
- **Narrative-without-evidence:** April blog still the problem child; aggregate NII series still need.
- **Hawkish frame:** OK if JPM primary carries mechanism.
- **Conf:** 0.36 acceptable only if research priority **explicitly ≪ JPM** with size cap. Else soft double-count.
- **Required revise:** Replace blog; publish size cap vs JPM; tighten KRE/CDS secondary definition. If Principal will not fund dual financials research, demote XLF to monitor-only (same spirit as SMH reject).

### 12. XOM — **revise**
- **Already-priced:** Energy-as-inflation-hedge familiar; crude has own tape (good that hike→XOM is killed).
- **Weak invalidation:** WTI <$60 for 5 sessions **or** buyback cut — good structure. **Missing:** as-of spot/strip at card date to show $60 is a meaningful distance (not arbitrary / already near).
- **Horizon mismatch:** 1–5 sessions track crude (OK) vs cycle FCF/buyback (needs guide).
- **Narrative-without-evidence:** CNBC oil geo piece is weak secondary; production/FCF guide still need.
- **Hawkish frame:** Mostly resolved by crude gate; residual demand-destruction from higher real rates not in invalidation — add secondary monitor (e.g. product demand / crack) optional.
- **Conf:** 0.38 OK-ish pending strip baseline; prefer **≤0.35** until FCF extract + strip as-of logged.
- **Required revise:** Log WTI/Brent as-of card timestamp; justify $60; replace CNBC with strip/inventory primary; FCF/buyback extract before thesis.

---

## What would earn a pass on a call card

All must hold:
1. Expected path states **what is mispriced** (not “IF gates clear”).
2. Primary invalidation is **one** observable with threshold + horizon; no protective ANDs.
3. Near-term vs cycle horizons are coherent; if near-term = no edge, conf ≤0.35 and call type = watch.
4. Name-level primary evidence cited (MM obs_id or filing/transcript) — macro backdrop alone insufficient.
5. Conf ≤ what evidence supports; satellites ≪ primaries.
6. No redundant theme expression without explicit size=0 / monitor-only status.

Until then: **0 passes.**

---

## Recommended call pack after this review

| Active revise-gated calls (9) | Reject / demote from call pack (3) |
|---|---|
| BTC (benchmark), ETH (RV) | **UNI** (no dated event) |
| NVDA (AI primary), AVGO (satellite, size-capped) | **AAVE** (liquidity + causation) |
| MSFT, META (earnings-watch) | **SMH** (redundant vs NVDA+AVGO; appendix only) |
| JPM (financials primary), XLF (size-capped diversifier) | |
| XOM (crude-gated) | |

---

## Explicit non-actions

- No risk approval.
- No trading credentials accessed.
- No orders, no `live.yaml`, no promotion to `thesis.md`.
- Rejects remain learning records.

**Signed:** Skeptic · 2026-09-17 · verdict counts **pass 0 / revise 9 / reject 3** · overall **revise**
