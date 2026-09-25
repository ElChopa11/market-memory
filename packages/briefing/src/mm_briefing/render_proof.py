"""Live close render for workflow mode ``render_proof``.

Same path as ``lab brief close --live --no-db``: ``generate_from_sources(..., live=True)``.
Equities (Polygon SPY/QQQ/UUP/USO) and rates (FRED DGS10) are in scope.
A missing key is ``RENDER_PROOF FAIL`` and a non-zero exit.
HTTP, timeout, or empty data with the key present still renders, and the step
summary names ``SOURCE DOWN``.
No completion stamp, receipt, capture, Neon session, deliver, Telegram send, or ping.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from mm_briefing.config import load_briefing_settings, repo_root
from mm_briefing.engine import default_macro_fetcher, generate_from_sources
from mm_briefing.models import HLInstrumentState, MacroSnapshot
from mm_common.time import utcnow

_POLYGON = (
    ("ES", "Polygon SPY"),
    ("NQ", "Polygon QQQ"),
    ("DXY", "Polygon UUP"),
    ("CL", "Polygon USO"),
)
_FRED = ("US10Y", "FRED DGS10")
_ERROR_CLASS = re.compile(r"error_class=([a-z0-9_]+)")
_HL_REASON = re.compile(r"unavailable \(([^)]+)\)")


@dataclass(frozen=True)
class ProofSource:
    name: str
    status: str
    as_of: str
    reason: str = ""


def render_close_proof(*, root: Path | None = None, generated_at=None) -> str:
    """Return the close markdown. Callers print it. This function does not write a capture."""
    text, _sources = build_close_proof(root=root, generated_at=generated_at)
    return text


def build_close_proof(*, root: Path | None = None, generated_at=None) -> tuple[str, tuple[ProofSource, ...]]:
    base = repo_root(root)
    settings = load_briefing_settings(base)
    as_of = generated_at or utcnow()
    trace: dict = {}
    doc, _decision = generate_from_sources(
        "close",
        settings=settings,
        as_of=as_of,
        macro_fetcher=default_macro_fetcher(settings, None),
        session=None,
        fixture=None,
        generated_at=as_of,
        live=True,
        live_trace=trace,
    )
    if doc is None:
        raise SystemExit("close render produced no document")
    snapshot = trace.get("snapshot")
    hl = trace.get("hl") or ()
    if not isinstance(snapshot, MacroSnapshot):
        raise SystemExit("close render produced no snapshot")
    return doc.markdown, proof_sources(snapshot, hl)


def proof_sources(snapshot: MacroSnapshot, hl: tuple[HLInstrumentState, ...]) -> tuple[ProofSource, ...]:
    notes = snapshot.notes
    blob = " ".join(notes)
    by_symbol = {row.symbol.upper(): row for row in snapshot.assets}
    rows: list[ProofSource] = [_hl_source(hl)]
    polygon_missing = "missing env POLYGON_API_KEY" in blob
    for symbol, label in _POLYGON:
        row = by_symbol.get(symbol)
        if polygon_missing:
            rows.append(ProofSource(label, "missing_env", "none"))
            continue
        if row is not None and row.last is not None:
            rows.append(ProofSource(label, "ok", _day(row.as_of)))
            continue
        rows.append(ProofSource(label, "down", "none", _down_reason(notes, "polygon")))
    fred_missing = "missing env FRED_API_KEY" in blob
    fred = by_symbol.get(_FRED[0])
    if fred_missing:
        rows.append(ProofSource(_FRED[1], "missing_env", "none"))
    elif fred is not None and fred.last is not None and fred.source == "fred":
        rows.append(ProofSource(_FRED[1], "ok", _day(fred.as_of)))
    else:
        rows.append(ProofSource(_FRED[1], "down", "none", _down_reason(notes, "fred")))
    return tuple(rows)


def fail_lines(sources: tuple[ProofSource, ...]) -> tuple[str, ...]:
    lines: list[str] = []
    if any(row.name.startswith("Polygon ") and row.status == "missing_env" for row in sources):
        lines.append("RENDER_PROOF FAIL: polygon missing_env")
    if any(row.name.startswith("FRED ") and row.status == "missing_env" for row in sources):
        lines.append("RENDER_PROOF FAIL: fred missing_env")
    return tuple(lines)


def unavailable_lines(sources: tuple[ProofSource, ...]) -> tuple[str, ...]:
    """Down sources stay in the render. The reason is the HTTP class, timeout, or empty."""
    return tuple(
        f"{row.name} unavailable ({row.reason})" for row in sources if row.status == "down" and row.reason
    )


def down_lines(sources: tuple[ProofSource, ...]) -> tuple[str, ...]:
    return tuple(
        f"SOURCE DOWN: {row.name} {row.reason}" for row in sources if row.status == "down" and row.reason
    )


def status_lines(sources: tuple[ProofSource, ...]) -> tuple[str, ...]:
    return tuple(f"{row.name} {row.status} as-of {row.as_of}" for row in sources)


def emit_render_proof(
    text: str,
    sources: tuple[ProofSource, ...] = (),
) -> None:
    """Print the message and, on Actions, the step summary. Counts are len(text) and splitlines()."""
    shown = text
    extra = unavailable_lines(sources)
    if extra:
        shown = text.rstrip("\n") + "\n" + "\n".join(extra) + "\n"
    chars = len(shown)
    lines = len(shown.splitlines())
    print(shown)
    print(f"characters={chars}")
    print(f"lines={lines}")
    for line in down_lines(sources):
        print(line)
    raw = os.environ.get("GITHUB_STEP_SUMMARY")
    if not raw:
        return
    body = [
        "## Render proof",
        "",
        *fail_lines(sources),
        *down_lines(sources),
        "",
        f"characters={chars}",
        f"lines={lines}",
        "",
        "````",
        shown.rstrip("\n"),
        "````",
        "",
        *status_lines(sources),
        "",
    ]
    Path(raw).write_text("\n".join(body), encoding="utf-8")


def main() -> int:
    text, sources = build_close_proof()
    failed = fail_lines(sources)
    for line in failed:
        print(line)
    emit_render_proof(text, sources)
    return 1 if failed else 0


def _hl_source(hl: tuple[HLInstrumentState, ...]) -> ProofSource:
    if hl and any(_hl_has_mid(state) for state in hl):
        dated = next((state.as_of_knowledge for state in hl if state.as_of_knowledge is not None), None)
        return ProofSource("HL", "ok", _day(dated))
    reason = "unavailable"
    for state in hl:
        match = _HL_REASON.search(state.source or "")
        if match:
            reason = match.group(1).strip() or reason
            break
    return ProofSource("HL", "down", "none", reason)


def _hl_has_mid(state: HLInstrumentState) -> bool:
    metric = state.metric("mid_px")
    return metric is not None and metric.value not in (None, "") and state.data_quality != "unavailable"


def _down_reason(notes: tuple[str, ...], marker: str) -> str:
    for note in notes:
        if marker not in note.lower():
            continue
        match = _ERROR_CLASS.search(note)
        if match is None:
            continue
        klass = match.group(1)
        if klass == "parse_error":
            return "empty"
        if klass == "missing_env":
            continue
        return klass
    return "empty"


def _day(moment) -> str:
    if moment is None:
        return "none"
    return moment.date().isoformat()


if __name__ == "__main__":
    sys.exit(main())
