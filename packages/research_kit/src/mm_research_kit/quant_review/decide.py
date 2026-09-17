"""Track evaluation and verdicts for the Quant Review Board."""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median

from mm_common.time import as_utc, parse_utc
from mm_research_kit.quant_review.models import (
    BLOCKING_PROMOTION_CODES,
    LABEL_ARBITRAGE,
    LABEL_RECLAIM_CANDIDATE,
    LABEL_RELATIVE_VALUE,
    LABEL_UNEXECUTABLE_ARB,
    UNUSUAL_SESSION_PP,
    ArbPackage,
    EvidenceRow,
    InstrumentPrint,
    InstrumentSpec,
    PromotionChecklist,
    QuantCard,
    QuantReasonCode,
    QuantTrack,
    QuantVerdict,
    ReclaimObservables,
    ReviewSnapshot,
    SeriesOverlay,
    UniverseSpec,
)
from mm_research_kit.quant_review.universe import counterpart

_UNKNOWN = "unknown — not in snapshot; not fabricated"
_PENDING_SKEPTIC = "pending"


def _quality_rank(value: str) -> int:
    return {"ok": 0, "partial": 1, "stale": 2, "contradicted": 3, "rejected": 4}.get(value, 1)


def worst_quality(*values: str | None) -> str:
    worst = "ok"
    for value in values:
        if value is None:
            continue
        if _quality_rank(value) > _quality_rank(worst):
            worst = value
    return worst


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.2f}%"


def _num(value: float | None) -> str:
    if value is None:
        return "n/a"
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _parse_maybe(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parse_utc(value)
    except (ValueError, TypeError):
        return None


def session_peer_median(symbol: str, spec: InstrumentSpec, snapshot: ReviewSnapshot) -> float | None:
    values: list[float] = []
    wanted = set(spec.peers) | {symbol}
    for peer in wanted:
        if peer == symbol:
            continue
        row = snapshot.print_for(peer)
        if row is not None and row.chg_pct is not None:
            values.append(row.chg_pct)
    if not values:
        return None
    return float(median(values))


def is_stale(
    *,
    data_quality: str,
    as_of_knowledge: datetime,
    review_at: datetime,
    stale_after: timedelta,
    print_ts: str | None = None,
) -> bool:
    if data_quality in {"stale", "contradicted", "rejected"}:
        return True
    knowledge = as_utc(as_of_knowledge)
    review = as_utc(review_at)
    if review - knowledge > stale_after:
        return True
    printed = _parse_maybe(print_ts)
    if printed is not None and review - as_utc(printed) > stale_after:
        return True
    return False


def _has_history(overlay: SeriesOverlay | None) -> bool:
    if overlay is None:
        return False
    if overlay.n_bars is not None and overlay.n_bars >= 20:
        return True
    return overlay.ret_short is not None or overlay.rv_20d is not None


def _arb_package(symbol: str, spec: InstrumentSpec, universe: UniverseSpec, snapshot: ReviewSnapshot) -> ArbPackage | None:
    if QuantTrack.D.value not in spec.tracks:
        return None
    if symbol in snapshot.arb_packages:
        return snapshot.arb_packages[symbol]
    other = counterpart(symbol, universe)
    if other is None:
        return None
    left = snapshot.print_for(symbol)
    right = snapshot.print_for(other)
    if left is None or right is None or left.last is None or right.last is None:
        return ArbPackage(venue_a=spec.venue, venue_b="unknown")
    lo = min(abs(left.last), abs(right.last))
    hi = max(abs(left.last), abs(right.last))
    comparable = lo > 0 and hi / lo <= 2.0
    spread = (left.last - right.last) if comparable else None
    return ArbPackage(
        venue_a=spec.venue or left.raw_symbol,
        venue_b=right.raw_symbol,
        same_or_convertible_exposure=False,
        gross_spread=spread,
        costs_complete=False,
        fill_size=None,
        liquidity_note=None,
        latency_ops_risk="units/convertibility not established" if not comparable else None,
        net_after_costs=None,
    )


def _codes(*items: QuantReasonCode | None) -> tuple[str, ...]:
    out: list[str] = []
    for item in items:
        if item is None:
            continue
        value = item.value if isinstance(item, QuantReasonCode) else str(item)
        if value not in out:
            out.append(value)
    return tuple(out)


def review_instrument(
    spec: InstrumentSpec,
    snapshot: ReviewSnapshot,
    *,
    universe: UniverseSpec,
    review_at: datetime,
    review_date: str,
    as_of_knowledge: datetime,
    stale_after: timedelta,
    ingest_overlap: frozenset[str] = frozenset(),
    deferred_must_cut: frozenset[str] = frozenset(),
) -> QuantCard:
    print_ = snapshot.print_for(spec.symbol)
    overlay = snapshot.overlay_for(spec.symbol)
    memory_rows = tuple(row for row in snapshot.memory if row.symbol == spec.symbol)
    reclaim = snapshot.reclaim.get(spec.symbol, ReclaimObservables())
    arb = _arb_package(spec.symbol, spec, universe, snapshot)

    qualities = [print_.data_quality if print_ else "partial"]
    if overlay is not None:
        qualities.append(overlay.data_quality)
    qualities.extend(row.data_quality for row in memory_rows)
    data_quality = worst_quality(*qualities)
    stale = is_stale(
        data_quality=data_quality,
        as_of_knowledge=as_of_knowledge,
        review_at=review_at,
        stale_after=stale_after,
        print_ts=print_.timestamp if print_ else None,
    )
    if stale and data_quality == "ok":
        data_quality = "stale"
    has_print = print_ is not None and print_.last is not None
    has_history = _has_history(overlay)
    missing = not has_print and overlay is None and not memory_rows

    labels: list[str] = []
    reason: list[QuantReasonCode] = []
    unusual_bits: list[str] = []
    structure_bits: list[str] = []
    evidence: list[EvidenceRow] = []

    if print_ is not None:
        evidence.append(
            EvidenceRow(
                claim=f"session print last={_num(print_.last)} chg={_num(print_.chg)} chg%={_pct(print_.chg_pct)}",
                source=print_.source,
                timestamp=print_.timestamp,
                capture=print_.capture,
                evidence_confidence=print_.evidence_confidence,
                provenance="fixture/watchlist snapshot; not fabricated",
            )
        )
        structure_bits.append(
            f"Session vs last print: {_pct(print_.chg_pct)} (one session; not a structure regime)."
        )
    if overlay is not None:
        evidence.append(
            EvidenceRow(
                claim=(
                    f"overlay last_close={_num(overlay.last_close)} ret_short={_pct((overlay.ret_short or 0) * 100 if overlay.ret_short is not None and abs(overlay.ret_short) <= 2 else overlay.ret_short)} "
                    f"rel_short={_pct((overlay.rel_short or 0) * 100 if overlay.rel_short is not None and abs(overlay.rel_short) <= 2 else overlay.rel_short)} "
                    f"asof={overlay.asof}"
                ),
                source=overlay.source,
                timestamp=overlay.captured_at or overlay.asof,
                capture=overlay.captured_at or overlay.asof,
                evidence_confidence=0.7 if overlay.data_quality == "ok" else 0.3,
                provenance="QUANT pack / series overlay; clocks are not mixed with the screenshot print",
            )
        )
        structure_bits.append(
            "Series overlay is descriptive (raw vs benchmark difference, not alpha, not residual)."
        )
    for row in memory_rows:
        evidence.append(
            EvidenceRow(
                claim=f"memory {row.metric}={row.value or 'n/a'} dq={row.data_quality}",
                source="market_memory.observation",
                timestamp=row.as_of_knowledge,
                capture=row.as_of_knowledge,
                evidence_confidence=0.8 if row.data_quality == "ok" else 0.3,
                provenance=f"observation_id={row.observation_id}; as_of_knowledge lockstep ingested_at",
            )
        )

    # Track A — market structure
    if QuantTrack.A.value in spec.tracks:
        if reclaim.confirmed:
            labels.append(LABEL_RECLAIM_CANDIDATE)
            unusual_bits.append(
                f"Reclaim observables present: prior {reclaim.prior_breakdown_level}; "
                f"reclaimed {reclaim.reclaim_of_level}; held {reclaim.hold_sessions} sessions."
            )
            structure_bits.append("Reclaim candidate (multi-session hold), not a one-day bounce.")
        else:
            reason.append(QuantReasonCode.RECLAIM_UNCONFIRMED)
            structure_bits.append(
                "Bullish reclaim is unconfirmed: needs prior breakdown level, reclaim of that level, "
                f"and hold ≥ {2} sessions. A one-day bounce is not a reclaim."
            )
        if not has_history:
            reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
            structure_bits.append("No native history window in this snapshot — trend/range/vol path unknown.")
        elif overlay is not None:
            structure_bits.append(
                f"Overlay RV20={overlay.rv_20d} RV60={overlay.rv_60d} MDD={overlay.mdd} "
                f"(native series; not cross-asset comparable)."
            )

    # Track B — sector relative value
    unusual_session = False
    peer_med = session_peer_median(spec.symbol, spec, snapshot)
    if QuantTrack.B.value in spec.tracks:
        if print_ is not None and print_.chg_pct is not None and peer_med is not None:
            delta = print_.chg_pct - peer_med
            structure_bits.append(
                f"Session vs peer median ({spec.sector} peers {', '.join(spec.peers) or 'none'}): "
                f"{_pct(print_.chg_pct)} vs median {_pct(peer_med)} (gap {delta:+.2f} pp). "
                "This is a relative-value observation, not ARBITRAGE."
            )
            if abs(delta) >= UNUSUAL_SESSION_PP:
                unusual_session = True
                labels.append(LABEL_RELATIVE_VALUE)
                unusual_bits.append(
                    f"Session print is unusual vs operational peer group ({delta:+.2f} pp vs median)."
                )
            else:
                unusual_bits.append("Session vs peers is ordinary on this one print.")
        elif has_print:
            reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
            unusual_bits.append("Peers lack session prints; relative-value vs sector cannot be scored.")
        if overlay is not None and overlay.rel_short is not None:
            # overlay rel is a simple difference, not alpha
            if abs(overlay.rel_short) >= 0.08:
                unusual_session = True
                if LABEL_RELATIVE_VALUE not in labels:
                    labels.append(LABEL_RELATIVE_VALUE)
                unusual_bits.append(
                    f"Overlay short-window raw vs {overlay.bench or spec.benchmark} "
                    "is large as a descriptive difference (not alpha; relative-value candidate)."
                )
        if not unusual_session and spec.role != "benchmark":
            reason.append(QuantReasonCode.NO_MISPRICING)

    # Track C — post-IPO
    post_ipo_down_only = False
    if QuantTrack.C.value in spec.tracks and spec.post_ipo:
        down = bool(print_ is not None and print_.chg_pct is not None and print_.chg_pct < 0)
        why_now = snapshot.catalysts.get(spec.symbol, "").strip()
        invalidation = snapshot.invalidations.get(spec.symbol, "").strip()
        if down and not (why_now and invalidation):
            post_ipo_down_only = True
            reason.append(QuantReasonCode.NO_CATALYST)
            reason.append(QuantReasonCode.THESIS_NOT_FALSIFIABLE)
            unusual_bits.append(
                "Post-IPO underperformance alone is not a candidate: needs why-now and a single invalidation."
            )
        if spec.listing_date is None:
            reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
            unusual_bits.append("Listing date is not in Market Memory; Track C listing path unverified.")
        if down:
            reason.append(QuantReasonCode.DILUTION_OR_LOCKUP_RISK)

    # Track D — executable arb
    executable_arb = False
    if QuantTrack.D.value in spec.tracks:
        other = counterpart(spec.symbol, universe)
        if arb is not None and arb.complete_executable:
            executable_arb = True
            labels.append(LABEL_ARBITRAGE)
            unusual_bits.append(
                "Track D package complete: two venues, convertible exposure, gross spread, costs, "
                "fill size, latency/ops risk, positive net."
            )
        else:
            reason.append(QuantReasonCode.UNEXECUTABLE_ARB)
            labels.append(LABEL_UNEXECUTABLE_ARB)
            if arb is not None and arb.gross_spread is not None and other:
                unusual_bits.append(
                    f"Two printed marks vs {other} (gross difference {_num(arb.gross_spread)}); "
                    "convertibility, costs, fill size, and net are missing — UNEXECUTABLE_ARB, not ARBITRAGE."
                )
            else:
                unusual_bits.append(
                    "Track D incomplete: two-venue executable package not present."
                )

    if missing:
        reason.append(QuantReasonCode.STALE_OR_PARTIAL_DATA)
        reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
        unusual_bits.append("No print, overlay, or memory row for this name.")
    elif stale:
        reason.append(QuantReasonCode.STALE_OR_PARTIAL_DATA)
    if data_quality in {"partial", "stale", "contradicted", "rejected"}:
        reason.append(QuantReasonCode.STALE_OR_PARTIAL_DATA)

    liq_ok = snapshot.liquidity_ok.get(spec.symbol, False)
    if overlay is not None and overlay.adv is not None and overlay.adv > 0:
        liq_ok = True
    if spec.symbol in {"BTC", "ETH", "NVDA", "SPX", "QQQ", "NQ"} and has_history:
        # majors with history are research-suitable liquidity, not an execution approval
        liq_ok = True
    if not liq_ok:
        reason.append(QuantReasonCode.INADEQUATE_LIQUIDITY)

    duplicate = spec.symbol in {"BTC_FUT", "IBIT"} or spec.sector in {"btc_complex", "crypto_equity"}
    if spec.benchmark == "BTC" and spec.symbol not in {"BTC"} and spec.asset_class in {"crypto_perp", "etf", "future"}:
        duplicate = True
    addressed = tuple(snapshot.addressed_warnings.get(spec.symbol, ()))
    if duplicate and QuantReasonCode.DUPLICATE_BETA.value not in addressed:
        reason.append(QuantReasonCode.DUPLICATE_BETA)
        reason.append(QuantReasonCode.CORRELATED_EXPOSURE)
    elif spec.sector in {"crypto_perp", "us_mega"} and spec.role != "benchmark":
        if QuantReasonCode.CORRELATED_EXPOSURE.value not in addressed:
            reason.append(QuantReasonCode.CORRELATED_EXPOSURE)

    catalyst = snapshot.catalysts.get(spec.symbol, "").strip()
    invalidation = snapshot.invalidations.get(spec.symbol, "").strip()
    overlooked = snapshot.overlooked.get(spec.symbol, "").strip()
    if not catalyst:
        reason.append(QuantReasonCode.NO_CATALYST)
        catalyst = _UNKNOWN
    if not invalidation:
        reason.append(QuantReasonCode.THESIS_NOT_FALSIFIABLE)
        invalidation = _UNKNOWN
    if not overlooked:
        if spec.symbol in deferred_must_cut:
            overlooked = (
                "Also a deferred must-cut on locked ingest universe — parked for ingest/thesis, "
                "still on this screenshot watchlist. Not a popularity add."
            )
        elif spec.symbol in ingest_overlap:
            overlooked = (
                "Already in locked ingest membership; board still requires an anomaly + invalidation "
                "before any thesis pack."
            )
        else:
            overlooked = _UNKNOWN

    if spec.role == "benchmark":
        reason.append(QuantReasonCode.NO_MISPRICING)
        unusual_bits.append("This name is the operational benchmark for its group, not a mispricing candidate.")

    unique_codes = _codes(*reason)
    if not unique_codes:
        unique_codes = _codes(QuantReasonCode.NO_MISPRICING)

    fresh = (not stale) and (not missing) and data_quality == "ok"
    defined_peers = bool(spec.benchmark) and (bool(spec.peers) or spec.role == "benchmark")
    specific_anomaly = bool(unusual_session or reclaim.confirmed or executable_arb)
    dq_or_beta_clear = (
        QuantReasonCode.DUPLICATE_BETA.value not in unique_codes
        and QuantReasonCode.STALE_OR_PARTIAL_DATA.value not in unique_codes
        and QuantReasonCode.CORRELATED_EXPOSURE.value not in unique_codes
    ) or (
        QuantReasonCode.DUPLICATE_BETA.value in addressed
        and QuantReasonCode.CORRELATED_EXPOSURE.value in addressed
        and QuantReasonCode.STALE_OR_PARTIAL_DATA.value not in unique_codes
    )

    residual_ok = {QuantReasonCode.UNEXECUTABLE_ARB.value}
    if not reclaim.confirmed:
        residual_ok.add(QuantReasonCode.RECLAIM_UNCONFIRMED.value)
    blocking_unaddressed = [
        code
        for code in unique_codes
        if code in {c.value for c in BLOCKING_PROMOTION_CODES}
        and code not in addressed
        and code not in residual_ok
    ]

    promotion = PromotionChecklist(
        fresh_attributable_data=fresh,
        defined_benchmark_peers=defined_peers,
        specific_anomaly=specific_anomaly,
        overlooked_reason=bool(overlooked) and overlooked != _UNKNOWN,
        catalyst_or_trigger=bool(snapshot.catalysts.get(spec.symbol, "").strip()),
        single_falsifiable_invalidation=bool(snapshot.invalidations.get(spec.symbol, "").strip()),
        acceptable_liquidity=liq_ok,
        no_unaddressed_duplicate_beta_or_dq=dq_or_beta_clear and not blocking_unaddressed,
        independent_skeptic_review_required=True,
        independent_skeptic_verdict=_PENDING_SKEPTIC,
    )

    if missing:
        verdict = QuantVerdict.INSUFFICIENT_DATA.value
    elif promotion.all_met and not blocking_unaddressed:
        verdict = QuantVerdict.RESEARCH_PRIORITY.value
    elif post_ipo_down_only:
        verdict = QuantVerdict.DEFER.value
    elif not has_history and not unusual_session and not executable_arb:
        verdict = QuantVerdict.INSUFFICIENT_DATA.value
    elif unusual_session or reclaim.confirmed:
        verdict = QuantVerdict.MONITOR.value
    elif spec.role == "benchmark":
        verdict = QuantVerdict.DEFER.value
    elif stale:
        verdict = QuantVerdict.INSUFFICIENT_DATA.value
    else:
        verdict = QuantVerdict.DEFER.value

    if verdict == QuantVerdict.RESEARCH_PRIORITY.value and QuantReasonCode.STALE_OR_PARTIAL_DATA.value in unique_codes:
        verdict = QuantVerdict.MONITOR.value if unusual_session else QuantVerdict.INSUFFICIENT_DATA.value

    what_must_change_bits = [
        f"Promotion checklist: {', '.join(name + '=' + str(getattr(promotion, name)) for name in promotion.as_dict() if name != 'independent_skeptic_verdict')}.",
        "Independent Skeptic review is required before any thesis pack; verdict is pending (not claimed as pass).",
        "RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live.",
    ]
    if unique_codes:
        what_must_change_bits.append("Unaddressed reason codes that block promotion: " + ", ".join(unique_codes) + ".")

    liquidity_text = (
        "Liquidity acceptable for research follow-up (not an execution approval)."
        if liq_ok
        else "Liquidity/ADV not evidenced in this snapshot — INADEQUATE_LIQUIDITY for promotion."
    )

    alternative = (
        "Skeptic case: the session print is noise, peer grouping is operational not fundamental, "
        "and any overlay difference is raw vs benchmark (not alpha). Duplicate crypto/tech beta is the default."
    )

    unusual_text = " ".join(unusual_bits) if unusual_bits else "Nothing objectively unusual in this snapshot."
    structure_text = " ".join(structure_bits) if structure_bits else "Structure not scored."

    return QuantCard(
        instrument=spec.symbol,
        raw_symbols=spec.raw_symbols,
        review_date=review_date,
        as_of_knowledge=as_utc(as_of_knowledge).isoformat(),
        tracks=spec.tracks,
        sector=spec.sector,
        benchmark=spec.benchmark,
        peers=spec.peers,
        data_quality=data_quality if not missing else "partial",
        unusual=unusual_text,
        evidence=tuple(evidence),
        relative_and_structure=structure_text,
        why_overlooked=overlooked,
        alternative_case=alternative,
        catalyst=catalyst,
        invalidation=invalidation,
        liquidity=liquidity_text,
        verdict=verdict,
        reason_codes=unique_codes,
        labels=tuple(dict.fromkeys(labels)),
        what_must_change=" ".join(what_must_change_bits),
        promotion=promotion,
        post_ipo=spec.post_ipo,
        executable_arb=executable_arb,
        addressed_warnings=addressed,
    )


def apply_priority_cap(cards: list[QuantCard], *, max_priority: int) -> list[QuantCard]:
    ranked = [card for card in cards if card.verdict == QuantVerdict.RESEARCH_PRIORITY.value]
    if len(ranked) <= max_priority:
        return cards
    ranked.sort(key=lambda card: (_promotion_score(card), card.instrument), reverse=True)
    keep = {card.instrument for card in ranked[:max_priority]}
    out: list[QuantCard] = []
    for card in cards:
        if card.verdict == QuantVerdict.RESEARCH_PRIORITY.value and card.instrument not in keep:
            codes = card.reason_codes
            extra = QuantReasonCode.ALREADY_PRICED.value
            if extra not in codes:
                codes = codes + (extra,)
            out.append(
                QuantCard(
                    **{
                        **card.__dict__,
                        "verdict": QuantVerdict.MONITOR.value,
                        "reason_codes": codes,
                        "what_must_change": (
                            card.what_must_change
                            + f" Demoted by board cap (≤{max_priority} RESEARCH_PRIORITY)."
                        ),
                    }
                )
            )
        else:
            out.append(card)
    return out


def _promotion_score(card: QuantCard) -> tuple[int, int]:
    met = sum(1 for value in card.promotion.as_dict().values() if value is True)
    return (met, 1 if card.executable_arb else 0)
