"""In-process rate-limit budget for read-only ingest adapters.

Does not invent prints. Exhaustion → caller degrades with error_class=rate_limited.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RateLimitBudget:
    """Per-source request budget (config/ingest.yaml rate_limits.*)."""

    name: str
    max_requests_per_minute: int
    used: int = 0
    skipped: int = 0

    def remaining(self) -> int:
        return max(0, int(self.max_requests_per_minute) - self.used)

    def allow(self) -> bool:
        if self.used >= max(0, int(self.max_requests_per_minute)):
            self.skipped += 1
            return False
        self.used += 1
        return True


def budget_from_settings(settings: dict, name: str, *, default_rpm: int = 20) -> RateLimitBudget:
    block = settings.get("rate_limits") if isinstance(settings.get("rate_limits"), dict) else {}
    spec = block.get(name) if isinstance(block, dict) else None
    rpm = default_rpm
    if isinstance(spec, dict) and spec.get("max_requests_per_minute") is not None:
        rpm = int(spec["max_requests_per_minute"])
    return RateLimitBudget(name=name, max_requests_per_minute=rpm)


def timeout_from_settings(settings: dict, name: str, *, default: float = 8.0) -> float:
    block = settings.get("rate_limits") if isinstance(settings.get("rate_limits"), dict) else {}
    spec = block.get(name) if isinstance(block, dict) else None
    if isinstance(spec, dict) and spec.get("timeout_seconds") is not None:
        return float(spec["timeout_seconds"])
    return default


def retry_from_settings(settings: dict, name: str) -> tuple[int, float]:
    from mm_common.http import DEFAULT_BACKOFF_S, DEFAULT_MAX_ATTEMPTS

    block = settings.get("rate_limits") if isinstance(settings.get("rate_limits"), dict) else {}
    spec = block.get(name) if isinstance(block, dict) else None
    attempts = DEFAULT_MAX_ATTEMPTS
    backoff = DEFAULT_BACKOFF_S
    if isinstance(spec, dict):
        if spec.get("max_attempts") is not None:
            attempts = int(spec["max_attempts"])
        if spec.get("backoff_s") is not None:
            backoff = float(spec["backoff_s"])
    return attempts, backoff
