"""In-process Telegram send budget. Exhaustion → skip send, never invent."""

from __future__ import annotations

from dataclasses import dataclass

from mm_delivery.config import RateLimitSettings


@dataclass
class RateLimitBudget:
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


def budget_from_settings(settings: RateLimitSettings, *, name: str = "telegram") -> RateLimitBudget:
    return RateLimitBudget(name=name, max_requests_per_minute=settings.max_requests_per_minute)
