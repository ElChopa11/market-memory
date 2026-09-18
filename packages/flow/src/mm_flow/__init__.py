"""Phase 6b flow / liquidity library. Research-only. No execution imports."""

from mm_flow.config import FlowConfig, load_flow_config
from mm_flow.engine import compute_flow
from mm_flow.models import FlowSnapshot, LiquidityVerdict
from mm_flow.verdict import VERDICT_OK, VERDICT_THIN, VERDICT_UNTRADEABLE, VERDICT_UNAVAILABLE

__phase__ = 6
LIVE_TRADING_ENABLED = False

__all__ = [
    "FlowConfig",
    "FlowSnapshot",
    "LIVE_TRADING_ENABLED",
    "LiquidityVerdict",
    "VERDICT_OK",
    "VERDICT_THIN",
    "VERDICT_UNAVAILABLE",
    "VERDICT_UNTRADEABLE",
    "compute_flow",
    "load_flow_config",
]
