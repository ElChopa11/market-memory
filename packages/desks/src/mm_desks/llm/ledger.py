"""LLM call ledger. Every call is recorded against run_id. No secrets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mm_common.hashing import canonical_json, sha256_hex
from mm_common.ids import new_ulid


@dataclass(frozen=True)
class LlmCallRecord:
    run_id: str
    desk_slug: str
    artifact_type: str
    prompt_file: str
    prompt_hash: str
    model: str
    model_version: str
    temperature: float
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    latency_ms: float
    cost: float
    schema_valid: bool
    retry_count: int
    call_id: str = field(default_factory=new_ulid)

    def canonical(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "run_id": self.run_id,
            "desk_slug": self.desk_slug,
            "artifact_type": self.artifact_type,
            "prompt_file": self.prompt_file,
            "prompt_hash": self.prompt_hash,
            "model": self.model,
            "model_version": self.model_version,
            "temperature": self.temperature,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "schema_valid": self.schema_valid,
            "retry_count": self.retry_count,
        }

    def content_hash(self) -> str:
        body = dict(self.canonical())
        body.pop("call_id", None)
        return sha256_hex(canonical_json(body))


def weekly_ops_report_shape(rows: tuple[LlmCallRecord, ...] = ()) -> dict[str, Any]:
    """Stub publisher shape. No live send."""
    by_desk: dict[str, int] = {}
    by_artifact: dict[str, int] = {}
    cost = 0.0
    cache_hits = 0
    lookups = 0
    schema_fail = 0
    for row in rows:
        by_desk[row.desk_slug] = by_desk.get(row.desk_slug, 0) + row.input_tokens + row.output_tokens
        by_artifact[row.artifact_type] = by_artifact.get(row.artifact_type, 0) + row.input_tokens + row.output_tokens
        cost += row.cost
        lookups += 1
        if row.cached_tokens:
            cache_hits += 1
        if not row.schema_valid:
            schema_fail += 1
    return {
        "tokens_per_desk": by_desk,
        "tokens_per_artifact": by_artifact,
        "cost_total": cost,
        "cost_per_idea_hit_target_first": None,
        "cache_hit_rate": (cache_hits / lookups) if lookups else 0.0,
        "grounding_failures_by_type": {},
        "degraded_by_error_class": {},
        "vs_prior_week": None,
        "n_calls": lookups,
        "schema_failures": schema_fail,
    }
