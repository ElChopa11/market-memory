"""Grounding locks. Blocking. Missing feeds are never filled from model memory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

PLACEHOLDER_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")
# A digit that is not inside a {{placeholder}}.
_DIGIT = re.compile(r"\d")
CLAIM_TAGS = ("observed", "computed", "inference")


class GroundingError(ValueError):
    """Failed run: numeric lock, render assertion, entity lock, or backfill."""


@dataclass(frozen=True)
class ProvenanceRow:
    token: str
    value: str
    provenance_id: str
    kind: str = "computed"

    def canonical(self) -> dict[str, str]:
        return {
            "token": self.token,
            "value": self.value,
            "provenance_id": self.provenance_id,
            "kind": self.kind,
        }


def strip_placeholders(text: str) -> str:
    return PLACEHOLDER_RE.sub("", text)


def assert_numeric_lock(llm_text: str) -> None:
    """Literal digit in LLM output not inside a placeholder = failed run."""
    remainder = strip_placeholders(llm_text)
    if _DIGIT.search(remainder):
        raise GroundingError("NUMERIC LOCK: LLM emitted a literal digit outside a placeholder")


def substitute_placeholders(text: str, rows: Mapping[str, ProvenanceRow]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in rows:
            raise GroundingError(f"RENDER ASSERTION: unresolved placeholder {{{{{key}}}}}")
        return rows[key].value

    return PLACEHOLDER_RE.sub(repl, text)


def numeric_tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"-?\d+(?:\.\d+)?", text))


def assert_render(published: str, rows: Mapping[str, ProvenanceRow]) -> None:
    """Every numeric token in the published body resolves to a provenance_id."""
    allowed = {row.value for row in rows.values()}
    # Also allow the raw placeholder values' numeric forms.
    for token in numeric_tokens(published):
        if token not in allowed and not any(token in row.value for row in rows.values()):
            raise GroundingError(f"RENDER ASSERTION: numeric token {token!r} has no provenance_id")
    for row in rows.values():
        if not row.provenance_id:
            raise GroundingError(f"RENDER ASSERTION: empty provenance_id for {row.token}")


def assert_named_entities(text: str, *, instruments: set[str], sources: set[str], dates: set[str]) -> None:
    upper = {item.upper() for item in instruments}
    # Tickers: 2–5 uppercase letters as whole words.
    for match in re.findall(r"\b[A-Z]{2,5}\b", text):
        if match in {"OK", "ON", "OFF", "VWAP", "ATR", "USD", "FOMC", "N/A"}:
            continue
        if match not in upper and match not in {s.upper() for s in sources}:
            raise GroundingError(f"NAMED-ENTITY LOCK: {match} not in the run evidence set")
    for date in re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text):
        if date not in dates:
            raise GroundingError(f"NAMED-ENTITY LOCK: date {date} not in the run evidence set")


def assert_no_backfill(published: str, *, missing_feeds: tuple[str, ...], gaps: tuple[str, ...]) -> None:
    """FRED unavailable → no rates figure in body; rates named in gaps."""
    blob = published.lower()
    missing = {item.lower() for item in missing_feeds}
    gap_blob = " ".join(gaps).lower()
    if "fred" in missing or any("fred" in m for m in missing):
        if re.search(r"\b(ust|yield|10y|2y|rates?)\b", blob) and re.search(r"\d", blob):
            raise GroundingError("NO BACKFILL: FRED unavailable but rates figure present in body")
        if "rates" not in gap_blob and "fred" not in gap_blob and "yield" not in gap_blob:
            raise GroundingError("NO BACKFILL: FRED unavailable must list rates in gaps")


def assert_hearsay(text: str) -> None:
    lowered = text.lower()
    if "breaking:" in lowered or "confirmed print" in lowered:
        raise GroundingError("HEARSAY BAN: news must be 'source X reported Y at T'")


def assert_claim_tags(tags: list[str] | tuple[str, ...], *, allow_inference_trigger: bool = False) -> None:
    for tag in tags:
        if tag not in CLAIM_TAGS:
            raise GroundingError(f"unknown claim tag {tag!r}")
    if "inference" in tags and allow_inference_trigger:
        raise GroundingError("inference cannot trigger or size")


def validate_llm_payload(payload: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    if not isinstance(payload, dict) or "prose" not in payload:
        raise ValueError("schema fail: missing prose")
    prose = str(payload.get("prose") or "")
    tags = payload.get("claim_tags") or []
    if not isinstance(tags, list):
        raise ValueError("schema fail: claim_tags must be a list")
    return prose, tuple(str(t) for t in tags)
