"""Phase 6b macro regime + EVENT_RISK library. Research-only. No execution imports."""

from mm_macro.calendar import EVENT_RISK_RULE, event_risk_at
from mm_macro.config import MacroConfig, load_macro_config
from mm_macro.engine import compute_macro
from mm_macro.models import EventRiskTag, MacroSnapshot
from mm_macro.regime import classify_macro_regime

__phase__ = 6
LIVE_TRADING_ENABLED = False

__all__ = [
    "EVENT_RISK_RULE",
    "EventRiskTag",
    "LIVE_TRADING_ENABLED",
    "MacroConfig",
    "MacroSnapshot",
    "classify_macro_regime",
    "compute_macro",
    "event_risk_at",
    "load_macro_config",
]
