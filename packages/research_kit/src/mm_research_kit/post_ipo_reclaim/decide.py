"""Score Post-IPO / reclaim screen rows. Closed Quant verdicts. Never invent prints."""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median

from mm_common.time import as_utc, parse_utc
from mm_research_kit.post_ipo_reclaim.models import (
    RECLAIM_MIN_HOLD_SESSIONS,
    UNUSUAL_SESSION_PP,
    MetricCell,
    ScreenDataQuality,
    ScreenInstrument,
    ScreenRow,
    ScreenUniverse,
)
from mm_research_kit.quant_review.decide import is_stale, worst_quality
from mm_research_kit.quant_review.models import (
    LABEL_RECLAIM_CANDIDATE,
    LABEL_RELATIVE_VALUE,
    QuantReasonCode,
    QuantVerdict,
    ReclaimObservables,
    ReviewSnapshot,
    SeriesOverlay,
)

_UNKNOWN = "unknown — not in snapshot; not fabricated"
_UNAVAILABLE = "unavailable — not in this snapshot; not fabricated"


def _pct(value: float | None) -> str:
    if value is None:
        return _UNAVAILABLE
    return f"{value:+.2f}%"


def _num(value: float | None) -> str:
    if value is None:
        return _UNAVAILABLE
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _parse_maybe(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parse_utc(value)
    except (ValueError, TypeError):
        return None


def _codes(*items: QuantReasonCode | None) -> tuple[str, ...]:
    out: list[str] = []
    for item in items:
        if item is None:
            continue
        value = item.value if isinstance(item, QuantReasonCode) else str(item)
        if value not in out:
            out.append(value)
    return tuple(out)


def _quality_from_snapshot(
    *,
    missing: bool,
    stale: bool,
    has_print: bool,
    has_overlay: bool,
    worst: str,
) -> str:
    if missing:
        return ScreenDataQuality.UNAVAILABLE.value
    if stale or worst in {"stale", "contradicted", "rejected"}:
        return ScreenDataQuality.STALE.value
    if has_print and has_overlay and worst == "ok":
        return ScreenDataQuality.FRESH.value
    if has_print or has_overlay:
        return ScreenDataQuality.PARTIAL.value
    return ScreenDataQuality.UNAVAILABLE.value


def _freshness_label(*, stale: bool, timestamp: str, review_at: datetime, stale_after: timedelta) -> str:
    if not timestamp:
        return ScreenDataQuality.UNAVAILABLE.value
    if stale:
        return ScreenDataQuality.STALE.value
    printed = _parse_maybe(timestamp)
    if printed is None:
        return ScreenDataQuality.PARTIAL.value
    if as_utc(review_at) - as_utc(printed) > stale_after:
        return ScreenDataQuality.STALE.value
    return ScreenDataQuality.FRESH.value


def _peer_median(symbol: str, spec: ScreenInstrument, snapshot: ReviewSnapshot, extra: tuple[str, ...]) -> float | None:
    values: list[float] = []
    wanted = set(spec.peers) | set(extra)
    for peer in wanted:
        if peer == symbol:
            continue
        row = snapshot.print_for(peer)
        if row is not None and row.chg_pct is not None:
            values.append(row.chg_pct)
    if not values:
        return None
    return float(median(values))


def _overlay_rel_pct(overlay: SeriesOverlay | None, field: str) -> str:
    if overlay is None:
        return _UNAVAILABLE
    value = getattr(overlay, field)
    if value is None:
        return _UNAVAILABLE
    # Overlays may store fractions (0.08) or already-percent; Quant pack uses fractions.
    scaled = value * 100 if abs(value) <= 2 else value
    return _pct(scaled)


def score_instrument(
    spec: ScreenInstrument,
    snapshot: ReviewSnapshot,
    *,
    universe: ScreenUniverse,
    review_at: datetime,
    as_of_knowledge: datetime,
    stale_after: timedelta,
) -> ScreenRow:
    print_ = snapshot.print_for(spec.symbol)
    overlay = snapshot.overlay_for(spec.symbol)
    reclaim = snapshot.reclaim.get(spec.symbol, ReclaimObservables())
    context_symbols = tuple(row.symbol for row in universe.context)

    qualities = []
    if print_ is not None:
        qualities.append(print_.data_quality)
    if overlay is not None:
        qualities.append(overlay.data_quality)
    worst = worst_quality(*qualities) if qualities else "partial"
    stale = is_stale(
        data_quality=worst if qualities else "partial",
        as_of_knowledge=as_of_knowledge,
        review_at=review_at,
        stale_after=stale_after,
        print_ts=print_.timestamp if print_ else None,
    )
    has_print = print_ is not None and print_.last is not None
    has_overlay = overlay is not None and (
        overlay.last_close is not None or overlay.mdd is not None or overlay.n_bars is not None
    )
    missing = not has_print and overlay is None
    data_quality = _quality_from_snapshot(
        missing=missing,
        stale=stale,
        has_print=has_print,
        has_overlay=has_overlay,
        worst=worst,
    )

    print_ts = print_.timestamp if print_ else ""
    print_source = print_.source if print_ else "none"
    print_fresh = _freshness_label(
        stale=stale or not has_print,
        timestamp=print_ts,
        review_at=review_at,
        stale_after=stale_after,
    )
    overlay_ts = (overlay.captured_at or overlay.asof) if overlay else ""
    overlay_source = overlay.source if overlay else "none"
    overlay_fresh = _freshness_label(
        stale=stale or overlay is None,
        timestamp=overlay_ts,
        review_at=review_at,
        stale_after=stale_after,
    )

    peer_med = _peer_median(spec.symbol, spec, snapshot, extra=context_symbols)
    bench_print = snapshot.print_for(spec.benchmark) if spec.benchmark else None
    session_gap: float | None = None
    if print_ is not None and print_.chg_pct is not None and peer_med is not None:
        session_gap = print_.chg_pct - peer_med
    vs_bench: float | None = None
    if print_ is not None and print_.chg_pct is not None and bench_print is not None and bench_print.chg_pct is not None:
        vs_bench = print_.chg_pct - bench_print.chg_pct

    down = bool(
        (print_ is not None and print_.chg_pct is not None and print_.chg_pct < 0)
        or (overlay is not None and overlay.mdd is not None and overlay.mdd < 0)
    )
    unusual_session = bool(session_gap is not None and abs(session_gap) >= UNUSUAL_SESSION_PP)
    if overlay is not None and overlay.rel_short is not None and abs(overlay.rel_short) >= 0.08:
        unusual_session = True

    catalyst = snapshot.catalysts.get(spec.symbol, "").strip()
    invalidation = snapshot.invalidations.get(spec.symbol, "").strip()
    liq_ok = snapshot.liquidity_ok.get(spec.symbol, False)
    if overlay is not None and overlay.adv is not None and overlay.adv > 0:
        liq_ok = True

    labels: list[str] = []
    reason: list[QuantReasonCode] = []
    unusual_bits: list[str] = []

    if reclaim.confirmed:
        labels.append(LABEL_RECLAIM_CANDIDATE)
        unusual_bits.append(
            f"Reclaim observables present: prior {reclaim.prior_breakdown_level}; "
            f"reclaimed {reclaim.reclaim_of_level}; held {reclaim.hold_sessions} sessions "
            f"(≥{RECLAIM_MIN_HOLD_SESSIONS} required). Multi-session hold, not a one-day bounce."
        )
    else:
        reason.append(QuantReasonCode.RECLAIM_UNCONFIRMED)
        unusual_bits.append(
            "Reclaim unconfirmed: needs prior breakdown level, reclaim of that level, "
            f"and hold ≥ {RECLAIM_MIN_HOLD_SESSIONS} sessions. A one-day bounce is not a reclaim."
        )

    if unusual_session:
        labels.append(LABEL_RELATIVE_VALUE)
        if session_gap is not None:
            unusual_bits.append(
                f"Session vs peer median is unusual ({session_gap:+.2f} pp). "
                "Relative-value observation, not ARBITRAGE."
            )
        else:
            unusual_bits.append("Overlay short-window raw vs benchmark is large as a descriptive difference (not alpha).")
    elif has_print and peer_med is not None:
        unusual_bits.append("Session vs peers is ordinary on this one print.")
    elif has_print and peer_med is None:
        reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
        unusual_bits.append("Peers lack session prints; relative-value vs sector cannot be scored.")

    if spec.listing_date is None:
        reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
        unusual_bits.append("Listing / issuance date is not in Market Memory.")

    post_ipo_down_only = False
    if spec.post_ipo and down and not (catalyst and invalidation):
        post_ipo_down_only = True
        reason.append(QuantReasonCode.NO_CATALYST)
        reason.append(QuantReasonCode.THESIS_NOT_FALSIFIABLE)
        unusual_bits.append(
            "Post-IPO underperformance alone is not a candidate: needs why-now and a single invalidation."
        )
    if spec.post_ipo and down:
        reason.append(QuantReasonCode.DILUTION_OR_LOCKUP_RISK)

    if missing:
        reason.append(QuantReasonCode.STALE_OR_PARTIAL_DATA)
        reason.append(QuantReasonCode.INSUFFICIENT_HISTORY)
        unusual_bits.append("No print or overlay for this name; metrics are unavailable and not fabricated.")
    elif stale or data_quality in {
        ScreenDataQuality.STALE.value,
        ScreenDataQuality.PARTIAL.value,
        ScreenDataQuality.UNAVAILABLE.value,
    }:
        reason.append(QuantReasonCode.STALE_OR_PARTIAL_DATA)

    if not liq_ok:
        reason.append(QuantReasonCode.INADEQUATE_LIQUIDITY)

    if spec.sector in {"crypto_equity"}:
        reason.append(QuantReasonCode.CORRELATED_EXPOSURE)

    if not catalyst:
        reason.append(QuantReasonCode.NO_CATALYST)
        catalyst_text = _UNKNOWN
    else:
        catalyst_text = catalyst
    if not invalidation:
        reason.append(QuantReasonCode.THESIS_NOT_FALSIFIABLE)
        invalidation_text = _UNKNOWN
    else:
        invalidation_text = invalidation

    if not unusual_session and not reclaim.confirmed and not missing:
        reason.append(QuantReasonCode.NO_MISPRICING)

    unique_codes = _codes(*reason)
    if not unique_codes:
        unique_codes = _codes(QuantReasonCode.NO_MISPRICING)

    fresh = (not stale) and (not missing) and data_quality == ScreenDataQuality.FRESH.value
    defined_peers = bool(spec.benchmark) and bool(spec.peers)
    specific_anomaly = bool(reclaim.confirmed or unusual_session)
    has_catalyst = bool(catalyst)
    has_invalidation = bool(invalidation)
    listing_ok = spec.listing_date is not None
    promotion_ready = (
        fresh
        and defined_peers
        and specific_anomaly
        and has_catalyst
        and has_invalidation
        and liq_ok
        and listing_ok
        and reclaim.confirmed
        and not post_ipo_down_only
        and QuantReasonCode.STALE_OR_PARTIAL_DATA.value not in unique_codes
    )

    if missing:
        verdict = QuantVerdict.INSUFFICIENT_DATA.value
    elif promotion_ready:
        verdict = QuantVerdict.RESEARCH_PRIORITY.value
    elif post_ipo_down_only:
        verdict = QuantVerdict.DEFER.value
    elif stale or data_quality == ScreenDataQuality.UNAVAILABLE.value:
        verdict = QuantVerdict.INSUFFICIENT_DATA.value
    elif unusual_session or reclaim.confirmed:
        verdict = QuantVerdict.MONITOR.value
    else:
        verdict = QuantVerdict.DEFER.value

    if verdict == QuantVerdict.RESEARCH_PRIORITY.value and QuantReasonCode.STALE_OR_PARTIAL_DATA.value in unique_codes:
        verdict = QuantVerdict.MONITOR.value if unusual_session or reclaim.confirmed else QuantVerdict.INSUFFICIENT_DATA.value

    what_must = (
        "Hard screen rule: catalyst, benchmark-relative context, liquidity evidence, "
        "and a single falsifiable invalidation are required before RESEARCH_PRIORITY. "
        "Listing/issuance date must be in Market Memory for post-IPO names. "
        f"Unaddressed reason codes: {', '.join(unique_codes)}. "
        "Independent Skeptic review is required before any thesis pack; not claimed as pass. "
        "RESEARCH_PRIORITY means a deeper thesis pack next — never paper or live."
    )
    liquidity_text = (
        "Liquidity acceptable for research follow-up (not an execution approval)."
        if liq_ok
        else "Liquidity/ADV not evidenced in this snapshot — INADEQUATE_LIQUIDITY for promotion."
    )

    metrics = (
        MetricCell(
            name="last",
            value=_num(print_.last if print_ else None),
            source=print_source,
            as_of=print_ts or _UNAVAILABLE,
            freshness=print_fresh if has_print else ScreenDataQuality.UNAVAILABLE.value,
            notes="Session print from snapshot/fixture. Not fabricated.",
        ),
        MetricCell(
            name="session_chg_pct",
            value=_pct(print_.chg_pct if print_ else None),
            source=print_source,
            as_of=print_ts or _UNAVAILABLE,
            freshness=print_fresh if has_print else ScreenDataQuality.UNAVAILABLE.value,
            notes="One session; not a structure regime.",
        ),
        MetricCell(
            name="vs_peer_median_pp",
            value=(f"{session_gap:+.2f} pp" if session_gap is not None else _UNAVAILABLE),
            source="computed from snapshot prints" if session_gap is not None else "none",
            as_of=print_ts or _UNAVAILABLE,
            freshness=print_fresh if session_gap is not None else ScreenDataQuality.UNAVAILABLE.value,
            notes=f"Peers {', '.join(spec.peers) or 'none'}; context {', '.join(context_symbols) or 'none'}. Relative-value, not alpha.",
        ),
        MetricCell(
            name="vs_benchmark_session_pp",
            value=(f"{vs_bench:+.2f} pp" if vs_bench is not None else _UNAVAILABLE),
            source="computed from snapshot prints" if vs_bench is not None else "none",
            as_of=print_ts or _UNAVAILABLE,
            freshness=print_fresh if vs_bench is not None else ScreenDataQuality.UNAVAILABLE.value,
            notes=f"Benchmark {spec.benchmark or 'none'}. Descriptive difference, not residual.",
        ),
        MetricCell(
            name="drawdown_vs_ref_high",
            value=(_num(overlay.mdd) if overlay is not None and overlay.mdd is not None else _UNAVAILABLE),
            source=overlay_source,
            as_of=overlay_ts or _UNAVAILABLE,
            freshness=overlay_fresh if overlay is not None and overlay.mdd is not None else ScreenDataQuality.UNAVAILABLE.value,
            notes="Native-series MDD from overlay when present. Not a reclaim confirmation. Not fabricated if missing.",
        ),
        MetricCell(
            name="rel_short_vs_bench",
            value=_overlay_rel_pct(overlay, "rel_short"),
            source=overlay_source,
            as_of=overlay_ts or _UNAVAILABLE,
            freshness=overlay_fresh if overlay is not None and overlay.rel_short is not None else ScreenDataQuality.UNAVAILABLE.value,
            notes="Simple difference vs overlay bench; not alpha.",
        ),
        MetricCell(
            name="reclaim_hold_sessions",
            value=str(reclaim.hold_sessions) if snapshot.reclaim.get(spec.symbol) else _UNAVAILABLE,
            source="snapshot.reclaim" if snapshot.reclaim.get(spec.symbol) else "none",
            as_of=as_utc(as_of_knowledge).isoformat(),
            freshness=(
                ScreenDataQuality.FRESH.value
                if snapshot.reclaim.get(spec.symbol)
                else ScreenDataQuality.UNAVAILABLE.value
            ),
            notes=reclaim.notes or "Reclaim needs prior breakdown + reclaim of that level + multi-session hold.",
        ),
        MetricCell(
            name="listing_date",
            value=spec.listing_date or _UNAVAILABLE,
            source="screen universe config",
            as_of="config",
            freshness=(
                ScreenDataQuality.FRESH.value if spec.listing_date else ScreenDataQuality.UNAVAILABLE.value
            ),
            notes="Issuance context. Null in config means not in Market Memory.",
        ),
    )

    unusual_text = " ".join(unusual_bits) if unusual_bits else "Nothing objectively unusual in this snapshot."
    return ScreenRow(
        instrument=spec.symbol,
        raw_symbols=spec.raw_symbols,
        as_of_knowledge=as_utc(as_of_knowledge).isoformat(),
        membership=spec.membership,
        post_ipo=spec.post_ipo,
        listing_date=spec.listing_date or _UNAVAILABLE,
        sector=spec.sector,
        benchmark=spec.benchmark,
        peers=spec.peers,
        data_quality=data_quality,
        metrics=metrics,
        verdict=verdict,
        reason_codes=unique_codes,
        labels=tuple(dict.fromkeys(labels)),
        unusual=unusual_text,
        catalyst=catalyst_text,
        invalidation=invalidation_text,
        liquidity=liquidity_text,
        what_must_change=what_must,
    )


def apply_priority_cap(rows: list[ScreenRow], *, max_priority: int) -> list[ScreenRow]:
    ranked = [row for row in rows if row.verdict == QuantVerdict.RESEARCH_PRIORITY.value]
    if len(ranked) <= max_priority:
        return rows
    ranked.sort(key=lambda row: row.instrument)
    keep = {row.instrument for row in ranked[:max_priority]}
    out: list[ScreenRow] = []
    for row in rows:
        if row.verdict == QuantVerdict.RESEARCH_PRIORITY.value and row.instrument not in keep:
            codes = row.reason_codes
            extra = QuantReasonCode.ALREADY_PRICED.value
            if extra not in codes:
                codes = codes + (extra,)
            out.append(
                ScreenRow(
                    **{
                        **row.__dict__,
                        "verdict": QuantVerdict.MONITOR.value,
                        "reason_codes": codes,
                        "what_must_change": (
                            row.what_must_change
                            + f" Demoted by screen cap (≤{max_priority} RESEARCH_PRIORITY)."
                        ),
                    }
                )
            )
        else:
            out.append(row)
    return out
