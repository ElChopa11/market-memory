"""Assemble the Post-IPO / reclaim screen from a screen-only universe + snapshot."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.time import as_utc, utcnow
from mm_research_kit.artifacts import write_text
from mm_research_kit.post_ipo_reclaim.decide import apply_priority_cap, score_instrument
from mm_research_kit.post_ipo_reclaim.models import (
    ENGINE_VERSION,
    MAX_RESEARCH_PRIORITY,
    STALE_AFTER_HOURS_DEFAULT,
    SCREEN_FOOTER,
    ScreenResult,
    ScreenUniverse,
)
from mm_research_kit.post_ipo_reclaim.render import render_screen
from mm_research_kit.quant_review.language import assert_language_clean
from mm_research_kit.quant_review.models import QuantVerdict, ReviewSnapshot


def run_screen(
    universe: ScreenUniverse,
    snapshot: ReviewSnapshot,
    *,
    review_at: datetime | None = None,
    screen_date: str | None = None,
    stale_after_hours: int | None = None,
    generated_at: datetime | None = None,
) -> ScreenResult:
    review = as_utc(review_at or snapshot.as_of_knowledge)
    generated = as_utc(generated_at or utcnow())
    day = screen_date or review.date().isoformat()
    hours = universe.stale_after_hours if stale_after_hours is None else stale_after_hours
    stale_after = timedelta(hours=hours if hours is not None else STALE_AFTER_HOURS_DEFAULT)
    as_of = as_utc(snapshot.as_of_knowledge)

    rows = [
        score_instrument(
            spec,
            snapshot,
            universe=universe,
            review_at=review,
            as_of_knowledge=as_of,
            stale_after=stale_after,
        )
        for spec in universe.candidates()
    ]
    rows = apply_priority_cap(rows, max_priority=MAX_RESEARCH_PRIORITY)
    coverage = _coverage_notes(universe, snapshot, rows)
    params_hash = sha256_hex(
        canonical_json(
            {
                "engine": ENGINE_VERSION,
                "universe_version": universe.version,
                "screen_date": day,
                "as_of_knowledge": as_of.isoformat(),
                "stale_after_hours": hours,
                "symbols": [spec.symbol for spec in universe.candidates()],
                "print_symbols": sorted({row.symbol for row in snapshot.prints}),
                "overlay_symbols": sorted({row.symbol for row in snapshot.overlays}),
            }
        )
    )
    markdown = render_screen(
        screen_date=day,
        as_of_knowledge=as_of.isoformat(),
        generated_at=generated.isoformat(),
        universe_version=universe.version,
        params_hash=params_hash,
        snapshot_source=snapshot.source,
        rows=tuple(rows),
        coverage_notes=coverage,
    )
    assert_language_clean(markdown)
    return ScreenResult(
        screen_date=day,
        as_of_knowledge=as_of.isoformat(),
        generated_at=generated.isoformat(),
        universe_version=universe.version,
        params_hash=params_hash,
        rows=tuple(rows),
        markdown=markdown,
        coverage_notes=coverage,
        snapshot_source=snapshot.source,
    )


def write_screen(result: ScreenResult, *, research_root: Path) -> dict[str, Any]:
    folder = research_root / "screens" / "post-ipo-reclaim"
    path = folder / f"{result.screen_date}.md"
    write_text(path, result.markdown)
    meta = {
        "engine": ENGINE_VERSION,
        "screen_date": result.screen_date,
        "as_of_knowledge": result.as_of_knowledge,
        "generated_at": result.generated_at,
        "universe_version": result.universe_version,
        "params_hash": result.params_hash,
        "snapshot_source": result.snapshot_source,
        "verdicts": {
            row.instrument: {
                "verdict": row.verdict,
                "reason_codes": list(row.reason_codes),
                "data_quality": row.data_quality,
            }
            for row in result.rows
        },
        "footer": SCREEN_FOOTER,
    }
    meta_path = folder / f"{result.screen_date}.meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "screen": path.as_posix(),
        "meta": meta_path.as_posix(),
        "params_hash": result.params_hash,
        "screen_date": result.screen_date,
        "row_count": len(result.rows),
        "verdicts": {row.instrument: row.verdict for row in result.rows},
    }


def _coverage_notes(
    universe: ScreenUniverse,
    snapshot: ReviewSnapshot,
    rows: list,
) -> tuple[str, ...]:
    printed = {row.symbol for row in snapshot.prints}
    missing = sorted({row.instrument for row in rows} - printed)
    context_missing = sorted({ctx.symbol for ctx in universe.context} - printed)
    notes = [
        f"Screen universe {universe.version} ({universe.status} / {universe.kind}): "
        f"{len(universe.candidates())} candidates. Desk={universe.desk}.",
        f"Does not change Principal membership ({universe.locked_membership_file}). "
        "Candidates are screen-only unless a row explicitly records in_universe / watch_only.",
        f"Snapshot source={snapshot.source}; prints={len(snapshot.prints)}; overlays={len(snapshot.overlays)}.",
        f"INSUFFICIENT_DATA count: {sum(1 for r in rows if r.verdict == QuantVerdict.INSUFFICIENT_DATA.value)}.",
        "Equity names are briefing/watchlist overlays, not Market Memory ingest. "
        "No filings/earnings pipeline in this phase.",
        "Drawdown vs reference high is overlay MDD when present; otherwise unavailable (not fabricated).",
    ]
    if missing:
        notes.append("Candidates with no session print: " + ", ".join(missing) + ".")
    if context_missing:
        notes.append("Context names with no session print: " + ", ".join(context_missing) + ".")
    notes.extend(universe.notes)
    notes.extend(snapshot.notes)
    return tuple(notes)


__all__ = ["run_screen", "write_screen"]
