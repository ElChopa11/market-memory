"""Context discipline: capped summary rows, envelope+numbers only, no table dumps."""

from __future__ import annotations

from typing import Any, Mapping

from mm_common.hashing import canonical_json, sha256_hex


def cap_rows(rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...], n: int) -> list[dict[str, Any]]:
    capped = [dict(row) for row in list(rows)[: max(0, int(n))]]
    return capped


def envelope_numbers_only(header: Mapping[str, Any], numbers: Mapping[str, Any]) -> dict[str, Any]:
    """Prior desk output enters as ENVELOPE + numbers, never full prose."""
    return {
        "header": {
            "desk": header.get("desk"),
            "as_of_utc": header.get("as_of_utc") or header.get("as_of"),
            "status": header.get("status"),
            "n": header.get("n"),
            "completeness": header.get("completeness") or header.get("completeness_pct"),
            "regime": header.get("regime"),
            "content_hash": header.get("content_hash"),
        },
        "numbers": dict(numbers),
    }


def scoped_retrieval(*, as_of: str, instrument: str, cluster: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("as_of") not in (None, as_of) and str(row.get("as_of_knowledge") or "") != as_of:
            continue
        if instrument and str(row.get("instrument") or "").upper() not in {instrument.upper(), ""}:
            continue
        if cluster and row.get("cluster") not in (None, cluster):
            continue
        out.append(row)
    return out


def static_prefix_hash(text: str) -> str:
    return sha256_hex(text.encode("utf-8"))


def build_writer_payload(
    *,
    prefix: str,
    summary_rows: list[Mapping[str, Any]],
    cap: int,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """No whole config, no full history, no table dumps."""
    if "config" in evidence or "history" in evidence:
        raise ValueError("context discipline: do not pass whole config or full history into prompts")
    return {
        "static_prefix_hash": static_prefix_hash(prefix),
        "summary": cap_rows(summary_rows, cap),
        "evidence_instruments": list(evidence.get("instruments") or []),
        "evidence_sources": list(evidence.get("sources") or []),
        "evidence_dates": list(evidence.get("dates") or []),
        "gaps": list(evidence.get("gaps") or []),
    }


def payload_fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json(dict(payload)))
