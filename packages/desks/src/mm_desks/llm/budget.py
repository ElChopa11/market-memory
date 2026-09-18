"""Hard token budgets. Exceeding per_run never silently truncates context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

BUDGETS_REL = Path("config/llm/budgets.yaml")
ERROR_BUDGET_EXCEEDED = "budget_exceeded"
ERROR_DAY_DISABLED = "llm_day_disabled"


@dataclass
class TokenBudget:
    per_call_max_input_tokens: int
    per_call_max_output_tokens: int
    per_run_token_budget: int
    per_day_token_budget: int
    per_desk_share: dict[str, float]
    summary_row_cap: int
    max_retries_on_schema: int
    temperature: float
    provider: str
    disable_flag: str
    used_run: int = 0
    used_day: int = 0
    used_desk: dict[str, int] = field(default_factory=dict)
    cache_hits: int = 0
    cache_lookups: int = 0
    day_disabled: bool = False
    notes: list[str] = field(default_factory=list)

    def cache_hit_rate(self) -> float:
        if self.cache_lookups <= 0:
            return 0.0
        return self.cache_hits / self.cache_lookups

    def remaining_run(self) -> int:
        return max(0, self.per_run_token_budget - self.used_run)

    def remaining_day(self) -> int:
        return max(0, self.per_day_token_budget - self.used_day)

    def desk_cap(self, desk: str) -> int:
        share = float(self.per_desk_share.get(desk, 0.0))
        if share <= 0:
            return self.per_run_token_budget
        return int(self.per_run_token_budget * share)

    def allow_call(self, *, desk: str, input_tokens: int, output_tokens: int) -> tuple[bool, str]:
        if self.day_disabled:
            return False, ERROR_DAY_DISABLED
        if input_tokens > self.per_call_max_input_tokens:
            return False, ERROR_BUDGET_EXCEEDED
        if output_tokens > self.per_call_max_output_tokens:
            return False, ERROR_BUDGET_EXCEEDED
        need = input_tokens + output_tokens
        if self.used_run + need > self.per_run_token_budget:
            return False, ERROR_BUDGET_EXCEEDED
        if self.used_day + need > self.per_day_token_budget:
            return False, ERROR_DAY_DISABLED
        desk_used = self.used_desk.get(desk, 0)
        if desk_used + need > self.desk_cap(desk) and desk in self.per_desk_share:
            return False, ERROR_BUDGET_EXCEEDED
        return True, "ok"

    def record(self, *, desk: str, input_tokens: int, output_tokens: int, cached: int = 0) -> None:
        need = input_tokens + output_tokens
        self.used_run += need
        self.used_day += need
        self.used_desk[desk] = self.used_desk.get(desk, 0) + need
        self.cache_lookups += 1
        if cached:
            self.cache_hits += 1
        if self.used_day >= self.per_day_token_budget:
            self.day_disabled = True
            self.notes.append("per_day_token_budget exhausted; LLM disabled until Principal reset")


def load_token_budget(repo_root: Path | None = None, **overrides: Any) -> TokenBudget:
    root = Path(repo_root or ".")
    path = root / BUDGETS_REL
    data: dict[str, Any] = {}
    if path.is_file():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    share = data.get("per_desk_share") if isinstance(data.get("per_desk_share"), dict) else {}
    budget = TokenBudget(
        per_call_max_input_tokens=int(data.get("per_call_max_input_tokens") or 2000),
        per_call_max_output_tokens=int(data.get("per_call_max_output_tokens") or 400),
        per_run_token_budget=int(data.get("per_run_token_budget") or 4000),
        per_day_token_budget=int(data.get("per_day_token_budget") or 50000),
        per_desk_share={str(k): float(v) for k, v in share.items()},
        summary_row_cap=int(data.get("summary_row_cap") or 12),
        max_retries_on_schema=int(data.get("max_retries_on_schema") or 1),
        temperature=float(data.get("temperature") or 0.1),
        provider=str(data.get("provider") or "none"),
        disable_flag=str(data.get("disable_flag") or "config/llm/disabled.flag"),
    )
    for key, value in overrides.items():
        if hasattr(budget, key) and value is not None:
            setattr(budget, key, value)
    flag = root / budget.disable_flag
    if flag.is_file():
        budget.day_disabled = True
        budget.notes.append("Principal disable flag present; LLM off; deterministic desks keep running")
    return budget


def write_day_disable_flag(repo_root: Path, relpath: str) -> None:
    path = Path(repo_root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("LLM disabled: per_day_token_budget exceeded. Principal reset required.\n", encoding="utf-8")
