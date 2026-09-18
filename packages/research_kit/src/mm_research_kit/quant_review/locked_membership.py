"""IMP-008 desk re-score of locked membership. Not the screenshot engine path.

Membership in config/universe.yaml is not a Quant verdict. This pass prefers
INSUFFICIENT_DATA over invented conviction and zero RESEARCH_PRIORITY over a
forced shortlist.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from mm_common.hashing import canonical_json, sha256_hex
from mm_research_kit.quant_review.language import assert_language_clean
from mm_research_kit.quant_review.models import (
    BOARD_FOOTER,
    BoardResult,
    EvidenceRow,
    PromotionChecklist,
    QuantCard,
    QuantReasonCode as C,
    QuantVerdict as V,
)
from mm_research_kit.quant_review.render import render_board, render_card
from mm_research_kit.quant_review.universe import universe_from_mapping

DESK_ENGINE = "imp-008.locked-membership-desk-pass"
REVIEW_DATE = "2026-09-18"
AS_OF_KNOWLEDGE = "2026-09-18T02:00:00+00:00"  # 12:00 Australia/Sydney (AEST)
GENERATED_AT = AS_OF_KNOWLEDGE
LOCKED_UNIVERSE_CONFIG = "config/quant_review_locked_universe.yaml"
MEMBERSHIP_CONFIG = "config/universe.yaml"
PRIOR_BOARD = "research/quant/2026-09-17/quant-review-board.md"
SEC_PR_2026_90_URL = (
    "https://www.sec.gov/newsroom/press-releases/2026-90-sec-issues-innovation-exemption-"
    "facilitate-trading-tokenized-nms-stock-request-comment"
)
SEC_PR_2026_90_DATE = "2026-09-17"

LOCKED_IN_UNIVERSE = ("BTC", "NVDA", "AVGO", "MSFT", "META", "JPM", "XOM")
LOCKED_WATCH_ONLY = ("ETH", "UNI", "AAVE", "SMH", "XLF")
LOCKED_BOARD_NAMES = LOCKED_IN_UNIVERSE + LOCKED_WATCH_ONLY
DEFERRED_MUST_CUT = ("HYPE", "SOL", "XRP", "ARB", "NEAR", "LINK", "GLD", "LLY")

_PENDING = "pending"


def _promo(**overrides: bool) -> PromotionChecklist:
    fields = dict(
        fresh_attributable_data=False,
        defined_benchmark_peers=True,
        specific_anomaly=False,
        overlooked_reason=True,
        catalyst_or_trigger=False,
        single_falsifiable_invalidation=False,
        acceptable_liquidity=False,
        no_unaddressed_duplicate_beta_or_dq=False,
        independent_skeptic_review_required=True,
        independent_skeptic_verdict=_PENDING,
    )
    fields.update(overrides)
    return PromotionChecklist(**fields)


def _must_change(promotion: PromotionChecklist, codes: tuple[str, ...]) -> str:
    bits = [
        "Promotion checklist: "
        + ", ".join(
            f"{name}={getattr(promotion, name)}"
            for name in promotion.as_dict()
            if name != "independent_skeptic_verdict"
        )
        + ".",
        "Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass).",
        "RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live.",
        "Unaddressed reason codes that block promotion: " + ", ".join(codes) + ".",
    ]
    return " ".join(bits)


def _card(
    *,
    spec_symbol: str,
    raw_symbols: tuple[str, ...],
    tracks: tuple[str, ...],
    sector: str,
    benchmark: str,
    peers: tuple[str, ...],
    data_quality: str,
    unusual: str,
    evidence: tuple[EvidenceRow, ...],
    relative_and_structure: str,
    why_overlooked: str,
    alternative_case: str,
    catalyst: str,
    invalidation: str,
    liquidity: str,
    verdict: str,
    reason_codes: tuple[str, ...],
    labels: tuple[str, ...] = (),
    promotion: PromotionChecklist,
) -> QuantCard:
    if verdict == V.RESEARCH_PRIORITY.value:
        raise ValueError("IMP-008 pass forbids RESEARCH_PRIORITY without a complete promotion checklist")
    return QuantCard(
        instrument=spec_symbol,
        raw_symbols=raw_symbols,
        review_date=REVIEW_DATE,
        as_of_knowledge=AS_OF_KNOWLEDGE,
        tracks=tracks,
        sector=sector,
        benchmark=benchmark,
        peers=peers,
        data_quality=data_quality,
        unusual=unusual,
        evidence=evidence,
        relative_and_structure=relative_and_structure,
        why_overlooked=why_overlooked,
        alternative_case=alternative_case,
        catalyst=catalyst,
        invalidation=invalidation,
        liquidity=liquidity,
        verdict=verdict,
        reason_codes=reason_codes,
        labels=labels,
        what_must_change=_must_change(promotion, reason_codes),
        promotion=promotion,
        post_ipo=False,
        executable_arb=False,
    )


def _ev(claim: str, source: str, timestamp: str, capture: str, conf: float, provenance: str) -> EvidenceRow:
    return EvidenceRow(
        claim=claim,
        source=source,
        timestamp=timestamp,
        capture=capture,
        evidence_confidence=conf,
        provenance=provenance,
    )


def build_locked_membership_cards() -> tuple[QuantCard, ...]:
    """Desk re-score. Does not rubber-stamp the 2026-09-17 screenshot board."""
    btc_codes = (
        C.RECLAIM_UNCONFIRMED.value,
        C.NO_MISPRICING.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.CORRELATED_EXPOSURE.value,
        C.STALE_OR_PARTIAL_DATA.value,
    )
    nvda_codes = (
        C.RECLAIM_UNCONFIRMED.value,
        C.NO_MISPRICING.value,
        C.CORRELATED_EXPOSURE.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.STALE_OR_PARTIAL_DATA.value,
    )
    avgo_codes = (
        C.STALE_OR_PARTIAL_DATA.value,
        C.DUPLICATE_BETA.value,
        C.CORRELATED_EXPOSURE.value,
        C.NO_MISPRICING.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    msft_codes = (
        C.STALE_OR_PARTIAL_DATA.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.NO_MISPRICING.value,
        C.CORRELATED_EXPOSURE.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    meta_codes = (
        C.STALE_OR_PARTIAL_DATA.value,
        C.INSUFFICIENT_HISTORY.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.NO_MISPRICING.value,
        C.CORRELATED_EXPOSURE.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    jpm_codes = (
        C.ALREADY_PRICED.value,
        C.NO_MISPRICING.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.STALE_OR_PARTIAL_DATA.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    xom_codes = (
        C.STALE_OR_PARTIAL_DATA.value,
        C.INSUFFICIENT_HISTORY.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.NO_MISPRICING.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    eth_codes = (
        C.DUPLICATE_BETA.value,
        C.CORRELATED_EXPOSURE.value,
        C.NO_MISPRICING.value,
        C.RECLAIM_UNCONFIRMED.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
    )
    uni_codes = (
        C.EVENT_RISK.value,
        C.NO_MISPRICING.value,
        C.DUPLICATE_BETA.value,
        C.CORRELATED_EXPOSURE.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.STALE_OR_PARTIAL_DATA.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    aave_codes = (
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.DUPLICATE_BETA.value,
        C.CORRELATED_EXPOSURE.value,
        C.STALE_OR_PARTIAL_DATA.value,
        C.INADEQUATE_LIQUIDITY.value,
        C.RECLAIM_UNCONFIRMED.value,
        C.NO_MISPRICING.value,
    )
    smh_codes = (
        C.DUPLICATE_BETA.value,
        C.CORRELATED_EXPOSURE.value,
        C.NO_MISPRICING.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.STALE_OR_PARTIAL_DATA.value,
        C.RECLAIM_UNCONFIRMED.value,
    )
    xlf_codes = (
        C.DUPLICATE_BETA.value,
        C.CORRELATED_EXPOSURE.value,
        C.NO_MISPRICING.value,
        C.NO_CATALYST.value,
        C.THESIS_NOT_FALSIFIABLE.value,
        C.STALE_OR_PARTIAL_DATA.value,
        C.RECLAIM_UNCONFIRMED.value,
    )

    btc_promo = _promo(acceptable_liquidity=True)
    nvda_promo = _promo(acceptable_liquidity=True)
    eth_promo = _promo(
        acceptable_liquidity=True,
        catalyst_or_trigger=True,
        single_falsifiable_invalidation=True,
    )
    uni_promo = _promo(
        catalyst_or_trigger=True,
        single_falsifiable_invalidation=True,
    )

    cards = (
        _card(
            spec_symbol="BTC",
            raw_symbols=("BTC", "BTCUSDC.P"),
            tracks=("A", "B"),
            sector="crypto_perp",
            benchmark="BTC",
            peers=("ETH", "UNI", "AAVE"),
            data_quality="partial",
            unusual=(
                "Nothing that clears promotion. in_universe membership and a methodology PASS on a "
                "benchmark/range expectation are not a structure anomaly. Prior screenshot board "
                "(2026-09-17) was DEFER; this pass stays DEFER after re-score."
            ),
            evidence=(
                _ev(
                    "prior Quant Board BTC=DEFER (screenshot universe, not locked membership)",
                    "research/quant/2026-09-17/cards/BTC.md",
                    "2026-09-17T02:42:00+00:00",
                    "IMP-001 board",
                    0.70,
                    "prior board; overlap name only",
                ),
                _ev(
                    "expectations methodology PASS: range/benchmark path; cycle gates empty",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.80,
                    "process artifact; not a tape print",
                ),
                _ev(
                    "QUANT overlay last_close=76201.0234375 asof=2026-09-17 ret_short=+18.13% (native; not residual)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack run_meta.json",
                    0.55,
                    "yfinance:BTC-USD overlay; clocks not mixed with a 2026-09-18 print",
                ),
                _ev(
                    "HL /info probe ok; no fundingHistory continuity in Memory this pass",
                    "ops/reports/source-health/2026-09-17.md",
                    "2026-09-17T04:51:26+00:00",
                    "IMP-003/004 source-health",
                    0.70,
                    "health/provenance only; no mids copied",
                ),
            ),
            relative_and_structure=(
                "No 2026-09-18 session print in Market Memory. QUANT native series is descriptive. "
                "Reclaim unconfirmed. Track D not scored (no BTC_FUT on this locked board). "
                "Crypto-perp peers are operational, not a residual book."
            ),
            why_overlooked=(
                "Already in_universe membership. Board still requires an anomaly plus invalidation "
                "before a thesis pack. Personal-TV keep on the WATCHLIST-DD cut-review is not this "
                "board's RESEARCH_PRIORITY."
            ),
            alternative_case=(
                "Skeptic case: hawkish-Fed and legislative setbacks are already public; deepest HL "
                "book is a liquidity reference, not mispricing. RQ-A funding/basis remains a separate "
                "workstream and is not auto-promoted here."
            ),
            catalyst=(
                "Monitor only: verified multi-day spot BTC ETF aggregate net inflows plus HL "
                "fundingHistory continuity. Neither series is in this pass's Memory snapshot."
            ),
            invalidation=(
                "Call-card primary remains: ≥5 consecutive US trading days of spot BTC ETF aggregate "
                "net outflows while HL funding stays ≥ +0.01%/8h with OI$ declining ≥15% from a "
                "dated capture baseline. Gates empty on this board — not a live trigger print."
            ),
            liquidity="Liquidity acceptable for research follow-up (not an execution approval).",
            verdict=V.DEFER.value,
            reason_codes=btc_codes,
            promotion=btc_promo,
        ),
        _card(
            spec_symbol="NVDA",
            raw_symbols=("NVDA",),
            tracks=("A", "B"),
            sector="ai_infra",
            benchmark="NVDA",
            peers=("AVGO", "SMH"),
            data_quality="partial",
            unusual=(
                "Nothing that clears promotion. Crowded AI-infra primary with an empty mispricing "
                "gate. Prior screenshot board DEFER; re-score stays DEFER. Equity tape is not in "
                "Market Memory; Stooq was unavailable on the last source-health report."
            ),
            evidence=(
                _ev(
                    "prior Quant Board NVDA=DEFER",
                    "research/quant/2026-09-17/cards/NVDA.md",
                    "2026-09-17T02:42:00+00:00",
                    "IMP-001 board",
                    0.70,
                    "prior board overlap name",
                ),
                _ev(
                    "expectations methodology PASS: crowded/unwind honesty; cycle upside gated on missing mispricing",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.80,
                    "process artifact",
                ),
                _ev(
                    "QUANT overlay last_close=213.89999389648438 asof=2026-09-16 rel_short=-2.42pp vs SPY (simple-diff, not alpha)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.45,
                    "yfinance:NVDA; US session 2026-09-16; stale vs 2026-09-18 Sydney review",
                ),
                _ev(
                    "Stooq unavailable (canary HTTP 404); FRED missing_env; no equity ingest",
                    "ops/reports/source-health/2026-09-17.md",
                    "2026-09-17T04:51:26+00:00",
                    "IMP-003/004",
                    0.80,
                    "equity tape gap; do not invent prints",
                ),
            ),
            relative_and_structure=(
                "No 2026-09-18 equity print. Overlay is one-session-lag descriptive vs SPY, not a "
                "residual. Reclaim unconfirmed. AVGO is satellite; SMH is appendix — correlated "
                "AI-infra exposure, not three independent books."
            ),
            why_overlooked=(
                "Already in_universe as AI-infra primary. Still needs a documented mispricing vs "
                "consensus guide, not a demand-exists narrative. Personal-TV keep is not RESEARCH_PRIORITY."
            ),
            alternative_case=(
                "Skeptic case: hyperscaler capex hopes are already priced; Fool/MarketBeat secondaries "
                "on the call card are weak. A capex scare is unwind risk, not a thesis pack trigger."
            ),
            catalyst=(
                "Next dated hyperscaler capex guide (MSFT / GOOGL / AMZN / META) or NVDA data-center "
                "revenue/GM vs company guide. Not in Memory this pass."
            ),
            invalidation=(
                "Call-card primary: a named hyperscaler cuts AI/data-center capex guide in a dated "
                "earnings print or 8-K vs prior guide. No such extract on this board."
            ),
            liquidity="Liquidity acceptable for research follow-up (not an execution approval).",
            verdict=V.DEFER.value,
            reason_codes=nvda_codes,
            promotion=nvda_promo,
        ),
        _card(
            spec_symbol="AVGO",
            raw_symbols=("AVGO",),
            tracks=("A", "B"),
            sector="ai_infra",
            benchmark="NVDA",
            peers=("NVDA", "SMH"),
            data_quality="partial",
            unusual=(
                "No independent cash-conversion residual vs NVDA is defined. Expectations "
                "methodology was INCONCLUSIVE. Thin equity tape → INSUFFICIENT_DATA rather than a "
                "forced DEFER that pretends the satellite test exists."
            ),
            evidence=(
                _ev(
                    "expectations methodology INCONCLUSIVE: satellite residual named but not specified",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.80,
                    "process artifact",
                ),
                _ev(
                    "call card: independence of evidence pack required; shared weak secondary with NVDA",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "FAIL-patch cross-ref",
                    0.70,
                    "membership card; not a Quant verdict",
                ),
                _ev(
                    "QUANT overlay last_close=339.510009765625 asof=2026-09-16 rel_short=-11.08pp vs SPY (simple-diff, not alpha)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.45,
                    "yfinance:AVGO; not a 2026-09-18 print; raw vs SPY is not a residual vs NVDA",
                ),
                _ev(
                    "no AVGO card on 2026-09-17 screenshot board; Stooq unavailable",
                    "ops/reports/source-health/2026-09-17.md",
                    "2026-09-17T04:51:26+00:00",
                    "source-health + prior board coverage",
                    0.75,
                    "name was absent from screenshot universe",
                ),
            ),
            relative_and_structure=(
                "QUANT NVDA–AVGO 0.46 (pre-FOMC 60d aligned panel, ends 2026-09-15) is a sample "
                "description, not two-name license. No regression window or AI line-item extract. "
                "SMH appendix is not a third expression."
            ),
            why_overlooked="in_universe satellite to NVDA. Satellite status is membership role, not a residual.",
            alternative_case=(
                "Skeptic case: same AI-infra bet as NVDA; backlog cash-conversion under higher WACC "
                "is unshown. Treating overlay underperformance vs SPY as independence would violate rel≠α."
            ),
            catalyst="Next earnings AI semiconductor revenue line-item vs prior company guide. Empty this pass.",
            invalidation=(
                "Call-card primary: next reported earnings AI semiconductor revenue guide cut vs prior "
                "company guide. Guide extract not on this board, so the trigger cannot be scored."
            ),
            liquidity="ADV not evidenced in Memory this pass — do not treat QUANT last_close as liquidity proof.",
            verdict=V.INSUFFICIENT_DATA.value,
            reason_codes=avgo_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="MSFT",
            raw_symbols=("MSFT",),
            tracks=("A", "B"),
            sector="mega_quality",
            benchmark="MSFT",
            peers=("META",),
            data_quality="partial",
            unusual=(
                "Earnings-gated Azure/ROI claim has no Azure extract on sheet. Methodology "
                "INCONCLUSIVE. Thin equity tape. INSUFFICIENT_DATA."
            ),
            evidence=(
                _ev(
                    "expectations methodology INCONCLUSIVE: Azure extract empty so path cannot be scored",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.80,
                    "process artifact",
                ),
                _ev(
                    "call card: sheet evidence is macro-only; no Azure growth print",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "call cards §8",
                    0.70,
                    "membership card",
                ),
                _ev(
                    "QUANT overlay last_close=490.29998779296875 asof=2026-09-16 rel_short=+4.67pp vs SPY (simple-diff, not alpha)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.45,
                    "yfinance:MSFT; large raw vs-SPY is not residual alpha (QUANT honesty)",
                ),
                _ev(
                    "Stooq unavailable; no equity ingest; no MSFT on 2026-09-17 screenshot board",
                    "ops/reports/source-health/2026-09-17.md",
                    "2026-09-17T04:51:26+00:00",
                    "source-health",
                    0.75,
                    "tape gap",
                ),
            ),
            relative_and_structure=(
                "No 2026-09-18 print. Overlay rel vs SPY must not confirm the earnings-gated path. "
                "Peer META has a lagged QUANT asof (2026-09-15), so mega-quality relative structure "
                "is not contemporaneous."
            ),
            why_overlooked="in_universe quality compounder narrative is consensus; Quant still needs Azure extracts.",
            alternative_case=(
                "Skeptic case: fortress/quality-under-higher-rates is already priced folklore without "
                "MSFT-specific proof on sheet."
            ),
            catalyst="Next earnings Azure constant-currency growth / Intelligent Cloud extract. Empty this pass.",
            invalidation=(
                "Call-card primary: Azure constant-currency growth decelerates by ≥300 bps QoQ vs the "
                "prior quarter's disclosed Azure growth. Prior-quarter figure is not extracted here."
            ),
            liquidity="ADV not evidenced in Memory this pass.",
            verdict=V.INSUFFICIENT_DATA.value,
            reason_codes=msft_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="META",
            raw_symbols=("META",),
            tracks=("A", "B"),
            sector="mega_quality",
            benchmark="MSFT",
            peers=("MSFT",),
            data_quality="stale",
            unusual=(
                "Ad ARPU / family DAU / capex-ROI extracts are empty. QUANT asof lags peers "
                "(2026-09-15). Methodology INCONCLUSIVE. INSUFFICIENT_DATA."
            ),
            evidence=(
                _ev(
                    "expectations methodology INCONCLUSIVE: empty fundamental gates + QUANT META lag",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.80,
                    "process artifact",
                ),
                _ev(
                    "QUANT overlay last_close=670.239990234375 asof=2026-09-15 LAG vs equity peers; SPY rel not contemporaneous",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack run_meta asof_flag",
                    0.30,
                    "yfinance:META; asof_note LAG_vs_equity_peers",
                ),
                _ev(
                    "call card: zero ad ARPU / DAU / capex evidence on sheet",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "call cards §9",
                    0.70,
                    "membership card",
                ),
                _ev(
                    "Stooq unavailable; no equity ingest",
                    "ops/reports/source-health/2026-09-17.md",
                    "2026-09-17T04:51:26+00:00",
                    "source-health",
                    0.75,
                    "tape gap",
                ),
            ),
            relative_and_structure=(
                "QUANT short-window rel vs SPY fails as-of discipline until the META lag is fixed "
                "(scorecard). Do not score a 2026-09-18 structure regime from a 2026-09-15 overlay."
            ),
            why_overlooked="in_universe ads+AI ROI story is 2024–26 consensus; Quant has no contemporaneous tape or extracts.",
            alternative_case=(
                "Skeptic case: solvency under higher WACC is not mispriced upside. Crowded ads+AI "
                "narrative is already priced until extracts exist."
            ),
            catalyst="Next earnings ad revenue vs company guide plus infra capex ROI KPIs. Empty this pass.",
            invalidation=(
                "Call-card primary: next earnings ad revenue growth misses company guide and "
                "management raises (or refuses to cut) infra capex without ROI KPIs. Guide lines not extracted."
            ),
            liquidity="ADV not evidenced in Memory this pass.",
            verdict=V.INSUFFICIENT_DATA.value,
            reason_codes=meta_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="JPM",
            raw_symbols=("JPM",),
            tracks=("A", "B"),
            sector="financials",
            benchmark="JPM",
            peers=("XLF",),
            data_quality="partial",
            unusual=(
                "FAIL-patched to earnings-watch only. SEP-implied NII residual remains undefined "
                "(no numeric gap test). Enough process evidence to park the residual frame as DEFER "
                "rather than invent INSUFFICIENT_DATA theater on a missing figure."
            ),
            evidence=(
                _ev(
                    "expectations methodology FAIL: NII beats SEP-implied with no numeric gap",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.85,
                    "process artifact",
                ),
                _ev(
                    "FAIL patch: earnings-watch only; residual empty/speculative until gap test exists — not invented",
                    "research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md",
                    "2026-09-17",
                    "PR #23",
                    0.85,
                    "changelog maps FAIL → patch",
                ),
                _ev(
                    "call card after patch: financials PRIMARY by role; no macro→NII causation without prints",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "call cards §10",
                    0.75,
                    "membership card",
                ),
                _ev(
                    "QUANT overlay last_close=348.9200134277344 asof=2026-09-16 rel_short=-0.93pp vs SPY (simple-diff)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.45,
                    "yfinance:JPM; pre-FOMC corr must not be read as NII",
                ),
            ),
            relative_and_structure=(
                "QUANT JPM–XLF 0.73 (window 2026-05-28 → 2026-09-15, pre-FOMC) is description, not a "
                "pair. Same-day/next-day after FOMC+SEP, bank NIM / higher-for-longer is the crowded "
                "equity read (ALREADY_PRICED). No 2026-09-18 print."
            ),
            why_overlooked="in_universe financials primary. Role ≠ residual long. Gap test still empty.",
            alternative_case=(
                "Skeptic case: FF path → NII is a mechanism family, not a print. Inventing a "
                "SEP-implied NII figure would fail honesty rules."
            ),
            catalyst=(
                "Next company NII / NIM guide (8-K / earnings) as one side of a future gap test. "
                "Not a residual today."
            ),
            invalidation=(
                "FAIL-patch primary: next reported quarter NII misses company guide — kills promotion "
                "from earnings-watch to a higher-for-longer NII residual. Company guide extract not on this board."
            ),
            liquidity="ADV not evidenced in Memory this pass.",
            verdict=V.DEFER.value,
            reason_codes=jpm_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="XOM",
            raw_symbols=("XOM",),
            tracks=("A", "B"),
            sector="energy",
            benchmark="XOM",
            peers=(),
            data_quality="partial",
            unusual=(
                "Crude-gated methodology PASSed, but crude strip / inventory / CL tape are not in "
                "Memory. Stooq CL was unavailable. Prefer INSUFFICIENT_DATA over scoring a crude "
                "gate with no strip as-of."
            ),
            evidence=(
                _ev(
                    "expectations methodology PASS: crude-gated path; hike→XOM shorthand killed",
                    "research/queue/EXPECTATIONS-20260917-methodology-scorecard.md",
                    "2026-09-17",
                    "Skeptic PR #22",
                    0.80,
                    "process artifact; methodology ≠ tape",
                ),
                _ev(
                    "call card: need crude strip + inventory + FCF/buyback primary sources — not hike narrative",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "call cards §12",
                    0.70,
                    "membership card; field 7 still empty",
                ),
                _ev(
                    "QUANT overlay last_close=163.32000732421875 asof=2026-09-16 rel_short=+3.56pp vs SPY (simple-diff, not alpha)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.45,
                    "yfinance:XOM; not a crude strip",
                ),
                _ev(
                    "Stooq CL canary/configured symbol unavailable (http 404 class); FRED missing_env",
                    "ops/reports/source-health/2026-09-17.md",
                    "2026-09-17T04:51:26+00:00",
                    "IMP-003/004",
                    0.80,
                    "oil tape gap",
                ),
            ),
            relative_and_structure=(
                "No energy-future print this pass. QUANT equity overlay is not WTI/Brent. Negative "
                "macro corr is not an energy sleeve (QUANT honesty). Reclaim unconfirmed."
            ),
            why_overlooked="in_universe crude-gated name. Clean methodology does not fill missing strip as-of.",
            alternative_case=(
                "Skeptic case: Fed hikes because inflation is sticky does not imply XOM upside; oil "
                "supply/demand and refining margins dominate. Do not revive hike→energy shorthand."
            ),
            catalyst="WTI/Brent strip levels and EIA/API inventory with source+as-of. Empty in Memory this pass.",
            invalidation=(
                "Call-card primary: front-month WTI settles below $60 for 5 consecutive sessions, or "
                "company withdraws/cuts the repurchase program on an FCF miss in next earnings. "
                "Neither print is on this board."
            ),
            liquidity="ADV not evidenced in Memory this pass.",
            verdict=V.INSUFFICIENT_DATA.value,
            reason_codes=xom_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="ETH",
            raw_symbols=("ETH", "ETHUSDC.P"),
            tracks=("A", "B"),
            sector="crypto_perp",
            benchmark="BTC",
            peers=("BTC", "UNI", "AAVE"),
            data_quality="partial",
            unusual=(
                "Re-score does not keep MONITOR because QUANT raw ETH−BTC was large. FAIL patch "
                "banned α. MONITOR is the BTC-beta desk watch with a single ETF-outflow trigger — "
                "membership watch_only, not an independent residual."
            ),
            evidence=(
                _ev(
                    "prior Quant Board ETH=MONITOR (screenshot overlay rel vs BTC treated as descriptive RV)",
                    "research/quant/2026-09-17/cards/ETH.md",
                    "2026-09-17T02:42:00+00:00",
                    "IMP-001 board",
                    0.60,
                    "prior board; do not rubber-stamp overlay as alpha",
                ),
                _ev(
                    "expectations methodology FAIL then patch: BTC-beta watch; residual empty until β protocol exists",
                    "research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md",
                    "2026-09-17",
                    "PR #23",
                    0.85,
                    "FAIL → demote",
                ),
                _ev(
                    "QUANT overlay last_close=2415.419922 asof=2026-09-17 rel_short=+8.19pp vs BTC (simple-diff, NOT alpha)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.50,
                    "yfinance:ETH-USD; rel_method=simple_diff_NOT_alpha",
                ),
                _ev(
                    "universe.yaml watch_only; ETH = BTC-beta watch (PR #23 / Skeptic PASS on FAIL patch)",
                    "config/universe.yaml",
                    "2026-09-17",
                    "Principal membership",
                    0.90,
                    "membership ≠ Quant verdict",
                ),
            ),
            relative_and_structure=(
                "Raw ETH−BTC is not edge. No named-window β residual and no L2 fee/activity residual. "
                "Prior board MONITOR from overlay magnitude is retired as an α read. Duplicate-beta "
                "vs BTC is the default."
            ),
            why_overlooked="watch_only BTC-beta. Board still watches ETF flows; it does not promote an RV long.",
            alternative_case=(
                "Skeptic case: HL #2 book stamps are stale appendix (DO NOT SIZE). Funding skew without "
                "OI series is incomplete microstructure."
            ),
            catalyst="ETH ETF aggregate net flows (monitor). L2 fee/activity residual still empty.",
            invalidation=(
                "FAIL-patch primary: ETH ETF aggregate net outflows on ≥5 consecutive US trading days "
                "kills promotion from BTC-beta watch to an independent or RV-vs-BTC frame. Raw ETH−BTC "
                "is not this trigger."
            ),
            liquidity="Liquidity acceptable for research follow-up (not an execution approval).",
            verdict=V.MONITOR.value,
            reason_codes=eth_codes,
            promotion=eth_promo,
        ),
        _card(
            spec_symbol="UNI",
            raw_symbols=("UNI", "UNIUSDC.P"),
            tracks=("A", "B"),
            sector="crypto_perp",
            benchmark="BTC",
            peers=("BTC", "ETH", "AAVE"),
            data_quality="partial",
            unusual=(
                "SEC PR 2026-90 (2026-09-17) is a dated public event: temporary Innovation Exemption "
                "for Tokenized Securities Venues using permissioned AMM liquidity pools for tokenized "
                "NMS stock. That does not auto-map to Uniswap protocol revenue. MONITOR only, with a "
                "falsifiable mapping test. Not RESEARCH_PRIORITY. QUANT 30d/90d bounce remains a footnote."
            ),
            evidence=(
                _ev(
                    "SEC PR 2026-90 Innovation Exemption: permissioned TSV AMM pools for tokenized NMS; 5-year term; issuer objection window; LP dealer exemption",
                    SEC_PR_2026_90_URL,
                    SEC_PR_2026_90_DATE,
                    "primary press release",
                    0.85,
                    "as_of_knowledge 2026-09-18 Sydney; order text on SEC.gov",
                ),
                _ev(
                    "Skeptic #14/#22: event-gated fee-switch with no dated Uniswap proposal URL; 90-day fishing removed",
                    "research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md",
                    "2026-09-17",
                    "PR #23 + scorecard PR #22",
                    0.85,
                    "FAIL → deferred governance watch",
                ),
                _ev(
                    "call card: deferred governance watch; watch_only membership; bounce ≠ thesis",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "call cards §3",
                    0.75,
                    "membership card",
                ),
                _ev(
                    "QUANT overlay last_close=6.7085 asof=2026-09-17 rel_short=+85.66pp vs BTC (simple-diff, NOT alpha); shorter Kraken history from 2024-09-27",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack (kraken:UNIUSD)",
                    0.40,
                    "footnote only; do not promote on bounce",
                ),
            ),
            relative_and_structure=(
                "PR 2026-90 conditions that block a naive Uniswap map: access is permissioned; "
                "tokenized NMS must carry the same rights as traditional NMS of an equivalent class; "
                "TSV must post public notice and offer the issuer of third-party tokenized stock a "
                "chance to object; smart contracts sit on a public permissionless ledger but the "
                "venue is not thereby Uniswap. QUANT bounce vs BTC is not a structure regime and is "
                "not ARBITRAGE."
            ),
            why_overlooked=(
                "watch_only deferred governance name. Fresh public-law event exists; protocol mapping "
                "does not. Honest MONITOR rather than narrative upgrade."
            ),
            alternative_case=(
                "Skeptic case: fee-switch / governance optionality is a multi-year recycled narrative. "
                "Permissioned TSV pools can list without Uniswap. Synthetics are outside the order. "
                "HL dayNtl appendix remains DO NOT SIZE."
            ),
            catalyst=(
                "Falsifiable mapping to monitor (not a thesis pack): a dated Uniswap governance "
                "proposal URL with executable fee parameters, or a TSV public notice required by "
                "PR 2026-90, that cites Uniswap contracts or UNI fee parameters for tokenized NMS. "
                "DEX volume share is not a substitute event."
            ),
            invalidation=(
                "Single trigger for the mapping: a TSV public notice (or issuer objection / absence "
                "of Uniswap citation in that notice) that does not name Uniswap contracts or UNI fee "
                "parameters — mapping from PR 2026-90 to UNI protocol revenue is then false for that "
                "venue. Revival of an event-gated UNI frame still requires a new card citing the URL "
                "(date, parameters, source). No 90-day fishing clock."
            ),
            liquidity="HL UNI dayNtl appendix is stale; INADEQUATE for promotion. Not an execution approval.",
            verdict=V.MONITOR.value,
            reason_codes=uni_codes,
            promotion=uni_promo,
        ),
        _card(
            spec_symbol="AAVE",
            raw_symbols=("AAVE", "AAVEUSDC.P"),
            tracks=("A", "B"),
            sector="crypto_perp",
            benchmark="BTC",
            peers=("BTC", "ETH", "UNI"),
            data_quality="partial",
            unusual=(
                "SEC PR 2026-90 LP dealer exemption on TSV AMM pools does not fill an Aave "
                "utilization baseline and does not imply crypto-credit demand. Credit expectation "
                "stays dropped. DEFER. Not MONITOR on narrative adjacency to AMMs."
            ),
            evidence=(
                _ev(
                    "SEC PR 2026-90: conditional dealer exemption for TSV AMM liquidity providers in tokenized NMS — not an Aave utilization print",
                    SEC_PR_2026_90_URL,
                    SEC_PR_2026_90_DATE,
                    "primary press release",
                    0.85,
                    "read as non-mapping unless a dated Aave listing/baseline exists",
                ),
                _ev(
                    "FAIL patch: deferred/micro watch; rate→credit killed; utilization −25% trigger removed as unfalsifiable",
                    "research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md",
                    "2026-09-17",
                    "PR #23",
                    0.85,
                    "credit frame already dropped",
                ),
                _ev(
                    "call card: no obs-linked utilization baseline; HL appendix DO NOT SIZE",
                    "research/queue/UNIVERSE-20260917-call-cards.md",
                    "2026-09-17",
                    "call cards §4",
                    0.75,
                    "membership card",
                ),
                _ev(
                    "QUANT overlay last_close=120.01000213623047 asof=2026-09-17 rel_short=+16.34pp vs BTC (simple-diff, NOT alpha)",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack",
                    0.45,
                    "yfinance:AAVE-USD; not utilization",
                ),
            ),
            relative_and_structure=(
                "Rate path ≠ utilization ≠ revenue (Skeptic #14/#22). TSV dealer exemption ≠ Aave "
                "core-market utilization. No dated Aave governance or listing URL tying tokenized "
                "NMS collateral to protocol revenue. Duplicate crypto beta vs BTC."
            ),
            why_overlooked="watch_only deferred/micro. PR 2026-90 was evaluated and did not supply the blocking baseline.",
            alternative_case=(
                "Skeptic case: higher-for-longer → borrow demand is a causation leap. Thin HL dayNtl "
                "must not be treated as a micro-size license."
            ),
            catalyst=(
                "Blocking revival input: obs-linked core-market utilization print (dashboard URL + "
                "as-of + figure or observation id). Not present."
            ),
            invalidation=(
                "Credit-demand / rate→borrow frame is already dropped. Any revival without an "
                "obs-linked utilization baseline is methodologically invalid. PR 2026-90 does not "
                "replace that baseline."
            ),
            liquidity="HL AAVE appendix thin/stale — INADEQUATE_LIQUIDITY for promotion. Not an execution approval.",
            verdict=V.DEFER.value,
            reason_codes=aave_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="SMH",
            raw_symbols=("SMH",),
            tracks=("A", "B"),
            sector="ai_infra",
            benchmark="NVDA",
            peers=("NVDA", "AVGO"),
            data_quality="partial",
            unusual=(
                "Monitor-only AI-infra basket appendix after FAIL patch. Holdings overlap % vs "
                "NVDA/AVGO unpublished. Not a basket-outperform claim. DEFER (parked duplicate), "
                "not RESEARCH_PRIORITY, not a tape-driven MONITOR."
            ),
            evidence=(
                _ev(
                    "FAIL patch: dropped from in-universe thesis-priority expectations; overlap % required before xor",
                    "research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md",
                    "2026-09-17",
                    "PR #23",
                    0.85,
                    "basket-outperform removed",
                ),
                _ev(
                    "universe.yaml watch_only; redundant vs NVDA+AVGO (Skeptic PR #14 demotion cite)",
                    "config/universe.yaml",
                    "2026-09-17",
                    "Principal membership",
                    0.90,
                    "membership ≠ Quant verdict",
                ),
                _ev(
                    "QUANT overlay last_close=545.5599975585938 asof=2026-09-16 YTD vs SPY flagged watch_YTD_not_promotion",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack asof_note",
                    0.45,
                    "post-selection YTD is not a promotion argument",
                ),
                _ev(
                    "WATCHLIST-DD cut-review: theme-dedupe vs NVDA primary (AMD demoted on the same logic)",
                    "research/queue/WATCHLIST-DD-20260917-personal-skeptic.md",
                    "2026-09-17",
                    "Skeptic cut-review",
                    0.70,
                    "personal-TV pack; not this board's membership expansion",
                ),
            ),
            relative_and_structure=(
                "Triple-count risk: SMH + NVDA + AVGO = one AI-infra theme. Issuer holdings file "
                "(NVDA weight, AVGO weight, combined overlap %) is empty — xor blocked. No 2026-09-18 print."
            ),
            why_overlooked="watch_only appendix. Street already uses SMH for the buildout — definitional, not an edge.",
            alternative_case=(
                "Skeptic case: restoring basket-outperform while NVDA+AVGO remain in_universe fails "
                "theme-dedupe. Do not revive memory-semi names via unpublished weights."
            ),
            catalyst="Published holdings overlap % vs NVDA/AVGO. Empty — blocking for any xor.",
            invalidation=(
                "FAIL-patch primary: NVDA primary invalidation (named hyperscaler capex cut) auto-drops "
                "the SMH appendix. No independent SMH outperform frame."
            ),
            liquidity="ETF ADV not evidenced in Memory this pass.",
            verdict=V.DEFER.value,
            reason_codes=smh_codes,
            promotion=_promo(),
        ),
        _card(
            spec_symbol="XLF",
            raw_symbols=("XLF",),
            tracks=("A", "B"),
            sector="financials",
            benchmark="JPM",
            peers=("JPM",),
            data_quality="partial",
            unusual=(
                "FAIL-patched to monitor-only diversifier with research priority strictly below JPM. "
                "Aggregate bank NII / KRE breadth still empty. DEFER (duplicate of JPM), not an "
                "independent MONITOR sleeve that could be misread as a second financials book."
            ),
            evidence=(
                _ev(
                    "FAIL patch: double-count is the default; corr 0.73 = description not proof; blog removed",
                    "research/queue/EXPECTATIONS-20260917-fail-patch-changelog.md",
                    "2026-09-17",
                    "PR #23",
                    0.85,
                    "diversifier-value claim removed",
                ),
                _ev(
                    "universe.yaml watch_only; XLF = monitor ≪ JPM (FAIL-patch PR #23)",
                    "config/universe.yaml",
                    "2026-09-17",
                    "Principal membership",
                    0.90,
                    "membership ≠ Quant verdict",
                ),
                _ev(
                    "QUANT overlay last_close=55.93000030517578 asof=2026-09-16; JPM–XLF 0.73 pre-FOMC 60d",
                    "research/queue/quant-20260917/metrics_active_and_watch.csv",
                    "2026-09-17T01:15:47+00:00",
                    "QUANT pack + run_meta corr",
                    0.45,
                    "corr ≠ causation; not a pair",
                ),
            ),
            relative_and_structure=(
                "Tracks JPM/financials complex as description. Breadth metrics (FDIC/Fed aggregate "
                "bank NII, KRE vs XLF with a registered window) are not operationalized. No 2026-09-18 print."
            ),
            why_overlooked="watch_only diversifier. Same higher-for-longer theme as JPM — two tickers, one idea.",
            alternative_case=(
                "Skeptic case: treating XLF as independent sector expression double-counts JPM. "
                "Pre-FOMC corr cannot underwrite a diversifier."
            ),
            catalyst="Operational breadth pack (aggregate NII + KRE with sources/as-of). Empty this pass.",
            invalidation=(
                "FAIL-patch primary: JPM NII-miss invalidation auto-drops the XLF sleeve (double-count). "
                "No independent XLF frame to kill."
            ),
            liquidity="ETF ADV not evidenced in Memory this pass.",
            verdict=V.DEFER.value,
            reason_codes=xlf_codes,
            promotion=_promo(),
        ),
    )
    symbols = tuple(card.instrument for card in cards)
    if symbols != LOCKED_BOARD_NAMES:
        raise ValueError(f"board order {symbols} != locked membership {LOCKED_BOARD_NAMES}")
    for card in cards:
        if card.verdict == V.RESEARCH_PRIORITY.value:
            raise ValueError(f"{card.instrument}: RESEARCH_PRIORITY is not allowed on this honest pass")
        if card.instrument in DEFERRED_MUST_CUT:
            raise ValueError(f"{card.instrument}: deferred_must_cut must not appear on the locked board")
        if not card.reason_codes:
            raise ValueError(f"{card.instrument}: missing reason codes")
        if card.promotion.all_met:
            raise ValueError(f"{card.instrument}: promotion checklist must not all be met on this pass")
        assert_language_clean(render_card(card))
    return cards


def coverage_notes() -> tuple[str, ...]:
    return (
        "Locked membership only from config/universe.yaml (version 2026-09-17, status=locked): "
        "12 names (in_universe 7 + watch_only 5).",
        "in_universe (thesis-priority membership, not a Quant verdict): BTC, NVDA, AVGO, MSFT, META, JPM, XOM.",
        "watch_only (still membership): ETH, UNI, AAVE, SMH, XLF.",
        "deferred_must_cut names are excluded (HYPE, SOL, XRP, ARB, NEAR, LINK, GLD, LLY) — learning records, not board members.",
        "Prior board research/quant/2026-09-17/ scored the screenshot/TV universe (36 names). Overlap with locked membership: BTC, ETH, NVDA only. Other locked names were absent there.",
        "Desk re-score (IMP-008); not a rubber-stamp of screenshot-engine MONITOR from overlay rel. QUANT rel = simple-diff, not alpha.",
        "Source-health 2026-09-17: overall degraded. HL /info ok (no mids copied). CoinGecko ping ok. Stooq unavailable (http 404 class). FRED missing_env. Postgres/object_store unavailable. Equity tape is not in Market Memory.",
        "QUANT pack overlays (asof 2026-09-16 equities / 2026-09-17 crypto; META lag 2026-09-15) are cited as dated evidence, not 2026-09-18 prints.",
        "SEC PR 2026-90 (2026-09-17) evaluated for UNI and AAVE only. UNI → MONITOR with a falsifiable TSV/Uniswap mapping test. AAVE → DEFER (exemption ≠ utilization baseline). No narrative auto-upgrade.",
        "WATCHLIST-DD personal-TV keep on BTC/NVDA is not copied as RESEARCH_PRIORITY. Membership ≠ Quant verdict.",
        "Zero RESEARCH_PRIORITY this review (honest empty preferred over a forced shortlist).",
        "No paid-data. No live path. No execution.",
    )


def concentration_warnings() -> tuple[str, ...]:
    return (
        "ai_infra: NVDA (primary) + AVGO (satellite) + SMH (appendix) — one theme; SMH parked as duplicate-beta.",
        "financials: JPM (earnings-watch primary) + XLF (watch_only) — double-count default; XLF parked.",
        "crypto_perp: BTC + ETH + UNI + AAVE — ETH is BTC-beta; UNI/AAVE remain duplicate crypto beta until independent residuals exist.",
        "mega_quality: MSFT + META — both earnings-gated with empty extracts; not independent books this pass.",
    )


def what_changed() -> str:
    return (
        "Universe switched from screenshot/TV watchlist (36) to locked membership (12). "
        "Dropped screenshot-only names and all deferred_must_cut. Added locked names absent from "
        "the 2026-09-17 board: AVGO, MSFT, META, JPM, XOM, UNI, AAVE, SMH, XLF. "
        "BTC: DEFER → DEFER (re-scored; still no anomaly). "
        "NVDA: DEFER → DEFER (re-scored; mispricing still empty; tape thin). "
        "ETH: MONITOR → MONITOR (reason changed: BTC-beta watch after FAIL patch; overlay rel is not alpha). "
        "UNI: (new on this board) MONITOR on SEC PR 2026-90 mapping test, not on bounce. "
        "AAVE: (new) DEFER — PR 2026-90 does not fill utilization baseline. "
        "JPM: (new) DEFER — FAIL-patched earnings-watch; residual undefined. "
        "SMH/XLF: (new) DEFER — duplicate of NVDA+AVGO / JPM. "
        "AVGO/MSFT/META/XOM: (new) INSUFFICIENT_DATA — empty gates and/or missing equity or crude tape."
    )


def params_hash_for(cards: tuple[QuantCard, ...]) -> str:
    return sha256_hex(
        canonical_json(
            {
                "engine": DESK_ENGINE,
                "review_date": REVIEW_DATE,
                "as_of_knowledge": AS_OF_KNOWLEDGE,
                "universe": MEMBERSHIP_CONFIG,
                "locked_review_universe": LOCKED_UNIVERSE_CONFIG,
                "names": [card.instrument for card in cards],
                "verdicts": {card.instrument: card.verdict for card in cards},
                "reason_codes": {card.instrument: list(card.reason_codes) for card in cards},
                "sec_pr_2026_90": SEC_PR_2026_90_URL,
            }
        )
    )


def build_locked_membership_board() -> BoardResult:
    cards = build_locked_membership_cards()
    digest = params_hash_for(cards)
    markdown = render_board(
        review_date=REVIEW_DATE,
        as_of_knowledge=AS_OF_KNOWLEDGE,
        generated_at=GENERATED_AT,
        universe_version="2026-09-17-locked-membership",
        params_hash=digest,
        cards=cards,
        coverage_notes=coverage_notes(),
        concentration_warnings=concentration_warnings(),
        what_changed=what_changed(),
        prior_board=PRIOR_BOARD,
        universe_config=LOCKED_UNIVERSE_CONFIG,
    )
    assert_language_clean(markdown)
    return BoardResult(
        review_date=REVIEW_DATE,
        as_of_knowledge=AS_OF_KNOWLEDGE,
        generated_at=GENERATED_AT,
        universe_version="2026-09-17-locked-membership",
        params_hash=digest,
        cards=cards,
        board_markdown=markdown,
        coverage_notes=coverage_notes(),
        concentration_warnings=concentration_warnings(),
        what_changed=what_changed(),
        prior_board=PRIOR_BOARD,
    )


def expected_counts(cards: tuple[QuantCard, ...] | None = None) -> dict[str, int]:
    cards = cards or build_locked_membership_cards()
    counts: dict[str, int] = {v.value: 0 for v in V}
    for card in cards:
        counts[card.verdict] += 1
    return {k: v for k, v in counts.items() if v}


def assert_locked_universe_pins(repo_root: Path) -> None:
    membership = yaml.safe_load((repo_root / MEMBERSHIP_CONFIG).read_text(encoding="utf-8"))
    locked = universe_from_mapping(yaml.safe_load((repo_root / LOCKED_UNIVERSE_CONFIG).read_text(encoding="utf-8")))
    in_universe = set(membership["in_universe"]["crypto_perps"]) | set(membership["in_universe"]["equities"])
    watch_only = set(membership["watch_only"]["crypto_perps"]) | set(membership["watch_only"]["equities"])
    deferred = set(membership["deferred_must_cut"]["crypto"]) | set(membership["deferred_must_cut"]["equities"])
    reviewed = {spec.symbol for spec in locked.instruments}
    if in_universe | watch_only != reviewed:
        raise ValueError("locked review universe must equal in_universe ∪ watch_only")
    if reviewed & deferred:
        raise ValueError("deferred_must_cut names must not be locked-board members")
    if tuple(spec.symbol for spec in locked.instruments) != LOCKED_BOARD_NAMES:
        raise ValueError("locked review instrument order must match LOCKED_BOARD_NAMES")


def write_locked_membership_pass(repo_root: Path, *, research_root: Path | None = None) -> dict[str, Any]:
    from mm_research_kit.quant_review.engine import write_board

    assert_locked_universe_pins(repo_root)
    result = build_locked_membership_board()
    written = write_board(result, research_root=research_root or (repo_root / "research"))
    meta_path = Path(written["meta"])
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    payload["engine"] = DESK_ENGINE
    payload["desk_pass"] = {
        "imp": "IMP-008",
        "as_of_sydney": "2026-09-18T12:00:00+10:00",
        "membership_config": MEMBERSHIP_CONFIG,
        "locked_review_universe": LOCKED_UNIVERSE_CONFIG,
        "in_universe": list(LOCKED_IN_UNIVERSE),
        "watch_only": list(LOCKED_WATCH_ONLY),
        "deferred_must_cut_excluded": list(DEFERRED_MUST_CUT),
        "research_priority_names": [],
        "counts": expected_counts(result.cards),
        "sec_pr_2026_90": {"date": SEC_PR_2026_90_DATE, "url": SEC_PR_2026_90_URL},
        "disclaimer": BOARD_FOOTER,
    }
    meta_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return written
