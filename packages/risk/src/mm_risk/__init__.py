"""Phase 5d deterministic allow/block library (Tier 6).

Not the risk *service* (apps/risk-service stays a stub). No LLM. No orders.
"""

from mm_risk.config import RiskConfig, load_risk_config
from mm_risk.engine import evaluate
from mm_risk.models import RiskIntent, RiskResult

__phase__ = 5
LIVE_TRADING_ENABLED = False

__all__ = [
    "LIVE_TRADING_ENABLED",
    "RiskConfig",
    "RiskIntent",
    "RiskResult",
    "evaluate",
    "load_risk_config",
]
