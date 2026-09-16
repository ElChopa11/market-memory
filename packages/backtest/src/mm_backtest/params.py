"""Canonical params_hash for reproducible backtests."""

from __future__ import annotations

from typing import Any

from mm_backtest.bars import Bar, KnowledgeFact
from mm_common.hashing import canonical_json, sha256_hex


def bars_hash(bars: list[Bar] | tuple[Bar, ...]) -> str:
    return sha256_hex(canonical_json([bar.canonical() for bar in bars]))


def facts_hash(facts: list[KnowledgeFact] | tuple[KnowledgeFact, ...]) -> str:
    return sha256_hex(canonical_json([fact.canonical() for fact in facts]))


def params_hash(payload: dict[str, Any]) -> str:
    """SHA-256 of canonical JSON. Same payload → same hash."""
    return sha256_hex(canonical_json(payload))


def result_hash(payload: dict[str, Any]) -> str:
    return sha256_hex(canonical_json(payload))
