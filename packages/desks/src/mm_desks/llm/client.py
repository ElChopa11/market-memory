"""Deterministic-first LLM client. No live provider in this PR. Never a calculator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from mm_desks.llm.budget import ERROR_BUDGET_EXCEEDED, ERROR_DAY_DISABLED, TokenBudget
from mm_desks.llm.grounding import GroundingError, assert_numeric_lock, validate_llm_payload
from mm_desks.llm.ledger import LlmCallRecord
from mm_desks.llm.prompts import PromptFile
from mm_desks.naming import ARTIFACT_TYPES, require_publishing_desk, require_artifact_type

TEMPLATE_ONLY = frozenset({"DAILY_BIAS", "STATE_CARD", "CHART_ARTIFACT", "SCAN_CARD", "INTEL_PACKET"})


class LlmForbidden(RuntimeError):
    """Raised when a template-only artifact or a calculator role is requested."""


@dataclass(frozen=True)
class LlmResult:
    ok: bool
    prose: str
    claim_tags: tuple[str, ...]
    schema_valid: bool
    retry_count: int
    error_class: str | None
    templated: bool
    record: LlmCallRecord | None
    raw: dict[str, Any] = field(default_factory=dict)


class Completer(Protocol):
    def __call__(self, prompt: str, *, temperature: float) -> dict[str, Any]: ...


def estimate_tokens(text: str) -> int:
    """Closed, deterministic estimator. Not a vendor tokenizer."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


class LlmClient:
    """WRITER/CRITIC only. Completer is injected (fixture or disabled). No network default."""

    def __init__(
        self,
        budget: TokenBudget,
        *,
        completer: Completer | None = None,
        model: str = "none",
        model_version: str = "none",
        prefix_cache: dict[str, str] | None = None,
    ) -> None:
        self.budget = budget
        self.completer = completer
        self.model = model
        self.model_version = model_version
        self.prefix_cache = prefix_cache if prefix_cache is not None else {}
        self.records: list[LlmCallRecord] = []

    def complete(
        self,
        *,
        artifact_type: str,
        desk_slug: str,
        run_id: str,
        prompt: PromptFile,
        user_payload: dict[str, Any],
        temperature: float | None = None,
        latency_ms: float = 0.0,
        cost: float = 0.0,
    ) -> LlmResult:
        require_publishing_desk(desk_slug)
        if artifact_type in ARTIFACT_TYPES:
            require_artifact_type(artifact_type)
        if artifact_type in TEMPLATE_ONLY:
            raise LlmForbidden(f"{artifact_type} is template-only (zero LLM)")
        if self.completer is None:
            return self._degraded("llm_disabled", run_id, desk_slug, artifact_type, prompt, 0)
        temp = self.budget.temperature if temperature is None else float(temperature)
        static = prompt.text
        cached = 0
        self.budget.cache_lookups += 1
        if static in self.prefix_cache:
            self.budget.cache_hits += 1
            cached = estimate_tokens(static)
        else:
            self.prefix_cache[static] = prompt.prompt_hash
        body = static + "\n" + json.dumps(user_payload, sort_keys=True)
        input_tokens = estimate_tokens(body)
        # Conservative output reservation: refuse before calling if the call cannot fit.
        reserved_out = min(self.budget.per_call_max_output_tokens, max(32, self.budget.remaining_run()))
        allow, reason = self.budget.allow_call(desk=desk_slug, input_tokens=input_tokens, output_tokens=reserved_out)
        if not allow:
            return self._degraded(reason, run_id, desk_slug, artifact_type, prompt, 0)

        retry = 0
        last_error = "schema_fail"
        payload: dict[str, Any] | None = None
        max_retry = self.budget.max_retries_on_schema
        while retry <= max_retry:
            try:
                payload = self.completer(body, temperature=temp)
                prose, tags = validate_llm_payload(payload)
                assert_numeric_lock(prose)
                output_tokens = estimate_tokens(json.dumps(payload, sort_keys=True))
                self.budget.record(desk=desk_slug, input_tokens=input_tokens, output_tokens=output_tokens, cached=cached)
                record = LlmCallRecord(
                    run_id=run_id,
                    desk_slug=desk_slug,
                    artifact_type=artifact_type,
                    prompt_file=prompt.relpath,
                    prompt_hash=prompt.prompt_hash,
                    model=self.model,
                    model_version=self.model_version,
                    temperature=temp,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cached_tokens=cached,
                    latency_ms=latency_ms,
                    cost=cost,
                    schema_valid=True,
                    retry_count=retry,
                )
                self.records.append(record)
                return LlmResult(
                    ok=True,
                    prose=prose,
                    claim_tags=tags,
                    schema_valid=True,
                    retry_count=retry,
                    error_class=None,
                    templated=False,
                    record=record,
                    raw=payload,
                )
            except GroundingError as exc:
                output_tokens = estimate_tokens(str(exc))
                self.budget.record(desk=desk_slug, input_tokens=input_tokens, output_tokens=output_tokens, cached=cached)
                record = LlmCallRecord(
                    run_id=run_id,
                    desk_slug=desk_slug,
                    artifact_type=artifact_type,
                    prompt_file=prompt.relpath,
                    prompt_hash=prompt.prompt_hash,
                    model=self.model,
                    model_version=self.model_version,
                    temperature=temp,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cached_tokens=cached,
                    latency_ms=latency_ms,
                    cost=cost,
                    schema_valid=True,
                    retry_count=retry,
                )
                self.records.append(record)
                return LlmResult(
                    ok=False,
                    prose="",
                    claim_tags=(),
                    schema_valid=True,
                    retry_count=retry,
                    error_class="grounding_failed",
                    templated=False,
                    record=record,
                    raw={"error": str(exc)},
                )
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                last_error = str(exc)
                retry += 1
                if retry > max_retry:
                    break
        output_tokens = estimate_tokens(last_error)
        self.budget.record(desk=desk_slug, input_tokens=input_tokens, output_tokens=output_tokens, cached=cached)
        record = LlmCallRecord(
            run_id=run_id,
            desk_slug=desk_slug,
            artifact_type=artifact_type,
            prompt_file=prompt.relpath,
            prompt_hash=prompt.prompt_hash,
            model=self.model,
            model_version=self.model_version,
            temperature=temp,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached,
            latency_ms=latency_ms,
            cost=cost,
            schema_valid=False,
            retry_count=max(0, retry - 1) if retry else 0,
        )
        self.records.append(record)
        return LlmResult(
            ok=False,
            prose="",
            claim_tags=(),
            schema_valid=False,
            retry_count=record.retry_count,
            error_class="schema_fail",
            templated=True,
            record=record,
            raw={"error": last_error},
        )

    def _degraded(
        self,
        reason: str,
        run_id: str,
        desk_slug: str,
        artifact_type: str,
        prompt: PromptFile,
        retry_count: int,
    ) -> LlmResult:
        record = LlmCallRecord(
            run_id=run_id,
            desk_slug=desk_slug,
            artifact_type=artifact_type,
            prompt_file=prompt.relpath,
            prompt_hash=prompt.prompt_hash,
            model=self.model,
            model_version=self.model_version,
            temperature=self.budget.temperature,
            input_tokens=0,
            output_tokens=0,
            cached_tokens=0,
            latency_ms=0.0,
            cost=0.0,
            schema_valid=False,
            retry_count=retry_count,
        )
        # Budget refusals must not look like a successful call in the ledger of *completions*,
        # but tests require every attempted LLM path to log prompt_hash. Record the refusal.
        self.records.append(record)
        return LlmResult(
            ok=False,
            prose="",
            claim_tags=(),
            schema_valid=False,
            retry_count=retry_count,
            error_class=reason if reason in {ERROR_BUDGET_EXCEEDED, ERROR_DAY_DISABLED} else reason,
            templated=True,
            record=record,
        )


def fixture_completer(payload: dict[str, Any]) -> Completer:
    def _call(_prompt: str, *, temperature: float) -> dict[str, Any]:
        return dict(payload)

    return _call


def scripted_completer(responses: list[Any]) -> Completer:
    state = {"i": 0}

    def _call(_prompt: str, *, temperature: float) -> dict[str, Any]:
        i = state["i"]
        state["i"] = i + 1
        item = responses[min(i, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return dict(item)

    return _call
