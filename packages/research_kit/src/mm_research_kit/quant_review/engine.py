"""Assemble a Quant Review Board from a universe + snapshot."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc, parse_utc, utcnow
from mm_research_kit.artifacts import write_text
from mm_research_kit.quant_review.decide import apply_priority_cap, review_instrument
from mm_research_kit.quant_review.language import assert_language_clean
from mm_research_kit.quant_review.models import (
    ENGINE_VERSION,
    MAX_RESEARCH_PRIORITY,
    STALE_AFTER_HOURS_DEFAULT,
    ArbPackage,
    BoardResult,
    InstrumentPrint,
    MemoryOverlay,
    QuantCard,
    QuantVerdict,
    ReclaimObservables,
    ReviewSnapshot,
    SeriesOverlay,
    UniverseSpec,
)
from mm_research_kit.quant_review.render import render_board, render_card
from mm_research_kit.quant_review.universe import normalize_symbol


def snapshot_from_mapping(data: dict[str, Any], *, symbol_map: dict[str, str]) -> ReviewSnapshot:
    as_of = parse_utc(str(data.get("as_of_knowledge")))
    prints: list[InstrumentPrint] = []
    for row in data.get("prints") or []:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("raw") or row.get("raw_symbol") or row.get("symbol") or "").strip()
        symbol = str(row.get("symbol") or normalize_symbol(raw, symbol_map)).strip().upper()
        prints.append(
            InstrumentPrint(
                raw_symbol=raw or symbol,
                symbol=symbol,
                last=_float(row.get("last")),
                chg=_float(row.get("chg")),
                chg_pct=_float(row.get("chg_pct")),
                source=str(row.get("source") or data.get("source") or "snapshot"),
                timestamp=str(row.get("timestamp") or data.get("as_of_knowledge") or ""),
                capture=str(row.get("capture") or data.get("capture") or ""),
                data_quality=str(row.get("data_quality") or "ok"),
                evidence_confidence=float(row.get("evidence_confidence") or 0.4),
            )
        )
    overlays = tuple(_overlay_from_row(row, symbol_map) for row in (data.get("overlays") or []) if isinstance(row, dict))
    memory = tuple(_memory_from_row(row, symbol_map) for row in (data.get("memory") or []) if isinstance(row, dict))
    reclaim = {
        str(sym).upper(): ReclaimObservables(
            prior_breakdown_level=spec.get("prior_breakdown_level"),
            reclaim_of_level=spec.get("reclaim_of_level"),
            hold_sessions=int(spec.get("hold_sessions") or 0),
            notes=str(spec.get("notes") or ""),
        )
        for sym, spec in (data.get("reclaim") or {}).items()
        if isinstance(spec, dict)
    }
    arb_packages = {
        str(sym).upper(): ArbPackage(
            venue_a=spec.get("venue_a"),
            venue_b=spec.get("venue_b"),
            same_or_convertible_exposure=bool(spec.get("same_or_convertible_exposure")),
            gross_spread=_float(spec.get("gross_spread")),
            costs_complete=bool(spec.get("costs_complete")),
            fill_size=_float(spec.get("fill_size")),
            liquidity_note=spec.get("liquidity_note"),
            latency_ops_risk=spec.get("latency_ops_risk"),
            net_after_costs=_float(spec.get("net_after_costs")),
        )
        for sym, spec in (data.get("arb_packages") or {}).items()
        if isinstance(spec, dict)
    }
    return ReviewSnapshot(
        as_of_knowledge=as_of,
        source=str(data.get("source") or "snapshot"),
        prints=tuple(prints),
        overlays=overlays,
        memory=memory,
        reclaim=reclaim,
        arb_packages=arb_packages,
        catalysts={str(k).upper(): str(v) for k, v in (data.get("catalysts") or {}).items()},
        invalidations={str(k).upper(): str(v) for k, v in (data.get("invalidations") or {}).items()},
        overlooked={str(k).upper(): str(v) for k, v in (data.get("overlooked") or {}).items()},
        liquidity_ok={str(k).upper(): bool(v) for k, v in (data.get("liquidity_ok") or {}).items()},
        addressed_warnings={
            str(k).upper(): tuple(str(x) for x in (v or []))
            for k, v in (data.get("addressed_warnings") or {}).items()
        },
        notes=tuple(str(n) for n in (data.get("notes") or [])),
    )


def empty_snapshot(*, as_of_knowledge: datetime, source: str = "empty") -> ReviewSnapshot:
    return ReviewSnapshot(as_of_knowledge=as_of_knowledge, source=source, prints=())


def merge_overlays(base: ReviewSnapshot, overlays: tuple[SeriesOverlay, ...]) -> ReviewSnapshot:
    existing = {row.symbol: row for row in base.overlays}
    for row in overlays:
        existing[row.symbol] = row
    return ReviewSnapshot(
        as_of_knowledge=base.as_of_knowledge,
        source=base.source,
        prints=base.prints,
        overlays=tuple(existing.values()),
        memory=base.memory,
        reclaim=base.reclaim,
        arb_packages=base.arb_packages,
        catalysts=base.catalysts,
        invalidations=base.invalidations,
        overlooked=base.overlooked,
        liquidity_ok=base.liquidity_ok,
        addressed_warnings=base.addressed_warnings,
        notes=base.notes,
    )


def merge_memory(base: ReviewSnapshot, memory: tuple[MemoryOverlay, ...]) -> ReviewSnapshot:
    return ReviewSnapshot(
        as_of_knowledge=base.as_of_knowledge,
        source=base.source,
        prints=base.prints,
        overlays=base.overlays,
        memory=base.memory + memory,
        reclaim=base.reclaim,
        arb_packages=base.arb_packages,
        catalysts=base.catalysts,
        invalidations=base.invalidations,
        overlooked=base.overlooked,
        liquidity_ok=base.liquidity_ok,
        addressed_warnings=base.addressed_warnings,
        notes=base.notes,
    )


def run_board(
    universe: UniverseSpec,
    snapshot: ReviewSnapshot,
    *,
    review_at: datetime | None = None,
    review_date: str | None = None,
    stale_after_hours: int = STALE_AFTER_HOURS_DEFAULT,
    ingest_overlap: frozenset[str] | None = None,
    deferred_must_cut: frozenset[str] | None = None,
    prior_cards: tuple[QuantCard, ...] = (),
    prior_board: str | None = None,
    generated_at: datetime | None = None,
) -> BoardResult:
    generated = as_utc(generated_at or review_at or utcnow())
    review_clock = as_utc(review_at or snapshot.as_of_knowledge)
    day = review_date or as_utc(snapshot.as_of_knowledge).date().isoformat()
    stale_after = timedelta(hours=stale_after_hours)
    cards: list[QuantCard] = [
        review_instrument(
            spec,
            snapshot,
            universe=universe,
            review_at=review_clock,
            review_date=day,
            as_of_knowledge=snapshot.as_of_knowledge,
            stale_after=stale_after,
            ingest_overlap=ingest_overlap or frozenset(),
            deferred_must_cut=deferred_must_cut or frozenset(),
        )
        for spec in universe.instruments
    ]
    cards = apply_priority_cap(cards, max_priority=MAX_RESEARCH_PRIORITY)
    coverage = _coverage_notes(universe, snapshot, cards, ingest_overlap or frozenset(), deferred_must_cut or frozenset())
    concentration = _concentration_warnings(cards)
    changed = _what_changed(cards, prior_cards)
    params_hash = sha256_hex(
        canonical_json(
            {
                "engine": ENGINE_VERSION,
                "universe_version": universe.version,
                "as_of_knowledge": as_utc(snapshot.as_of_knowledge).isoformat(),
                "review_date": day,
                "stale_after_hours": stale_after_hours,
                "prints": [
                    {"symbol": row.symbol, "last": row.last, "chg_pct": row.chg_pct, "timestamp": row.timestamp}
                    for row in snapshot.prints
                ],
                "overlay_symbols": sorted(row.symbol for row in snapshot.overlays),
            }
        )
    )
    markdown = render_board(
        review_date=day,
        as_of_knowledge=as_utc(snapshot.as_of_knowledge).isoformat(),
        generated_at=generated.isoformat(),
        universe_version=universe.version,
        params_hash=params_hash,
        cards=tuple(cards),
        coverage_notes=coverage,
        concentration_warnings=concentration,
        what_changed=changed,
        prior_board=prior_board,
    )
    assert_language_clean(markdown)
    for card in cards:
        assert_language_clean(render_card(card))
        if not card.reason_codes:
            raise ValueError(f"{card.instrument} missing reason codes")
    return BoardResult(
        review_date=day,
        as_of_knowledge=as_utc(snapshot.as_of_knowledge).isoformat(),
        generated_at=generated.isoformat(),
        universe_version=universe.version,
        params_hash=params_hash,
        cards=tuple(cards),
        board_markdown=markdown,
        coverage_notes=coverage,
        concentration_warnings=concentration,
        what_changed=changed,
        prior_board=prior_board,
    )


def write_board(result: BoardResult, *, research_root: Path) -> dict[str, Any]:
    folder = research_root / "quant" / result.review_date
    cards_dir = folder / "cards"
    board_path = folder / "quant-review-board.md"
    write_text(board_path, result.board_markdown)
    card_paths: list[str] = []
    for card in result.cards:
        path = cards_dir / f"{card.instrument}.md"
        write_text(path, render_card(card))
        card_paths.append(path.as_posix())
    payload = {
        "engine": ENGINE_VERSION,
        "review_date": result.review_date,
        "as_of_knowledge": result.as_of_knowledge,
        "generated_at": result.generated_at,
        "universe_version": result.universe_version,
        "params_hash": result.params_hash,
        "verdicts": {card.instrument: {"verdict": card.verdict, "reason_codes": list(card.reason_codes)} for card in result.cards},
        "footer": "Research only. Not a trade instruction, allocation decision, or execution approval.",
    }
    meta_path = folder / "run_meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "board": board_path.as_posix(),
        "cards": card_paths,
        "meta": meta_path.as_posix(),
        "params_hash": result.params_hash,
        "review_date": result.review_date,
    }


def find_prior_board(research_root: Path, review_date: str) -> Path | None:
    quant = research_root / "quant"
    if not quant.is_dir():
        return None
    dates = sorted(
        path.name
        for path in quant.iterdir()
        if path.is_dir() and (path / "quant-review-board.md").is_file() and path.name < review_date
    )
    if not dates:
        return None
    return quant / dates[-1] / "quant-review-board.md"


def load_prior_verdicts(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file():
        return {}
    meta = path.parent / "run_meta.json"
    if not meta.is_file():
        return {}
    data = json.loads(meta.read_text(encoding="utf-8"))
    verdicts = data.get("verdicts") or {}
    return {str(k): str((v or {}).get("verdict") or "") for k, v in verdicts.items()}


def _coverage_notes(
    universe: UniverseSpec,
    snapshot: ReviewSnapshot,
    cards: list[QuantCard],
    ingest_overlap: frozenset[str],
    deferred_must_cut: frozenset[str],
) -> tuple[str, ...]:
    reviewed = {card.instrument for card in cards}
    printed = {row.symbol for row in snapshot.prints}
    missing_prints = sorted(reviewed - printed)
    notes = [
        f"Universe {universe.version} ({universe.status}): {len(universe.instruments)} approved watchlist names.",
        "This is not locked ingest/thesis membership; config/universe.yaml is unchanged.",
        f"Screenshot/fixture prints: {len(snapshot.prints)}; overlays: {len(snapshot.overlays)}.",
        f"INSUFFICIENT_DATA count: {sum(1 for c in cards if c.verdict == QuantVerdict.INSUFFICIENT_DATA.value)}.",
    ]
    if missing_prints:
        notes.append("Names with no session print: " + ", ".join(missing_prints) + ".")
    if ingest_overlap:
        notes.append("Overlap with locked ingest/thesis membership: " + ", ".join(sorted(ingest_overlap)) + ".")
    if deferred_must_cut:
        notes.append(
            "Screenshot names that are deferred must-cuts on the locked universe: "
            + ", ".join(sorted(deferred_must_cut))
            + " (review only; not ingest expansion)."
        )
    notes.extend(universe.notes)
    notes.extend(snapshot.notes)
    return tuple(notes)


def _concentration_warnings(cards: list[QuantCard]) -> tuple[str, ...]:
    by_sector: dict[str, list[str]] = {}
    for card in cards:
        by_sector.setdefault(card.sector, []).append(card.instrument)
    warnings: list[str] = []
    for sector, names in sorted(by_sector.items()):
        if len(names) >= 4:
            warnings.append(f"{sector}: {len(names)} names ({', '.join(names)}) — duplicate-beta / correlated exposure risk.")
    crypto_beta = [c.instrument for c in cards if c.sector in {"crypto_perp", "btc_complex", "crypto_equity"}]
    if len(crypto_beta) >= 5:
        warnings.append(
            "Broad crypto beta cluster across perps, BTC_FUT, and crypto-equity ETFs/names — not independent books."
        )
    return tuple(warnings)


def _what_changed(cards: list[QuantCard], prior: tuple[QuantCard, ...]) -> str:
    if not prior:
        return "No prior board in research/quant/. First review of this screenshot-derived universe."
    previous = {card.instrument: card.verdict for card in prior}
    changes: list[str] = []
    for card in cards:
        old = previous.get(card.instrument)
        if old and old != card.verdict:
            changes.append(f"{card.instrument}: {old} → {card.verdict}")
    added = [card.instrument for card in cards if card.instrument not in previous]
    dropped = [name for name in previous if name not in {c.instrument for c in cards}]
    if added:
        changes.append("added: " + ", ".join(added))
    if dropped:
        changes.append("dropped: " + ", ".join(dropped))
    return "; ".join(changes) if changes else "No verdict changes vs prior board."


def _overlay_from_row(row: dict[str, Any], symbol_map: dict[str, str]) -> SeriesOverlay:
    raw = str(row.get("symbol") or "")
    return SeriesOverlay(
        symbol=normalize_symbol(raw, symbol_map) if raw else str(row.get("symbol") or "").upper(),
        source=str(row.get("source") or "overlay"),
        asof=str(row.get("asof") or ""),
        captured_at=str(row.get("captured_at") or row.get("asof") or ""),
        last_close=_float(row.get("last_close")),
        ret_short=_float(row.get("ret_short")),
        ret_long=_float(row.get("ret_long")),
        rel_short=_float(row.get("rel_short")),
        rel_long=_float(row.get("rel_long")),
        rv_20d=_float(row.get("rv_20d")),
        rv_60d=_float(row.get("rv_60d")),
        mdd=_float(row.get("mdd")),
        n_bars=int(row["n_bars"]) if row.get("n_bars") is not None else None,
        bench=str(row["bench"]) if row.get("bench") else None,
        data_quality=str(row.get("data_quality") or "ok"),
        notes=str(row.get("notes") or ""),
        adv=_float(row.get("adv")),
    )


def _memory_from_row(row: dict[str, Any], symbol_map: dict[str, str]) -> MemoryOverlay:
    raw = str(row.get("symbol") or "")
    return MemoryOverlay(
        symbol=normalize_symbol(raw, symbol_map),
        observation_id=str(row.get("observation_id") or ""),
        metric=str(row.get("metric") or ""),
        value=None if row.get("value") is None else str(row.get("value")),
        data_quality=str(row.get("data_quality") or "partial"),
        as_of_knowledge=str(row.get("as_of_knowledge") or ""),
        claim_hash=str(row["claim_hash"]) if row.get("claim_hash") else None,
    )


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
