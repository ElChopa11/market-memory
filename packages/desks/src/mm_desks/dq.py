"""DQ = completeness = fields_populated / fields_required. Letter grades removed."""

from __future__ import annotations

from typing import Any, Mapping

LETTER_GRADES = frozenset({"A", "A+", "A-", "B", "B+", "B-", "C", "C+", "C-", "D", "F"})


def completeness(fields_populated: int, fields_required: int) -> float:
    if fields_required <= 0:
        return 1.0
    return max(0.0, min(1.0, float(fields_populated) / float(fields_required)))


def populated_count(payload: Mapping[str, Any], required: tuple[str, ...] | list[str]) -> tuple[int, int, tuple[str, ...]]:
    missing: list[str] = []
    present = 0
    for key in required:
        value = payload.get(key)
        if value in (None, "", "?", "unknown", []):
            missing.append(str(key))
        else:
            present += 1
    return present, len(tuple(required)), tuple(missing)


def assert_no_letter_grade(payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        if str(key).lower() in {"grade", "letter_grade", "dq_grade"}:
            raise ValueError("letter grades removed; DQ is completeness ratio")
        if isinstance(value, str) and value.strip().upper() in LETTER_GRADES and str(key).lower().endswith("grade"):
            raise ValueError("letter grades removed; DQ is completeness ratio")


def publish_allowed(ratio: float, threshold: float) -> bool:
    return float(ratio) >= float(threshold)
