"""Phase 5c Quant factor library (Tier 4 / IMP-011).

Research-only. No execution imports, no trade language, no live path.
"""

from mm_quant.card import build_quant_card, render_quant_card
from mm_quant.config import QuantConfig, load_quant_config
from mm_quant.factors import FACTOR_NAMES, FactorRegistry
from mm_quant.models import QuantCard
from mm_quant.regime import classify_regime
from mm_quant.sizing import fixed_fractional_budget_pct, vol_targeted_budget_pct
from mm_quant.trade_math import TradeMath, compute_trade_math

__phase__ = 5
LIVE_TRADING_ENABLED = False

__all__ = [
    "FACTOR_NAMES",
    "FactorRegistry",
    "LIVE_TRADING_ENABLED",
    "QuantCard",
    "QuantConfig",
    "TradeMath",
    "build_quant_card",
    "classify_regime",
    "compute_trade_math",
    "fixed_fractional_budget_pct",
    "load_quant_config",
    "render_quant_card",
    "vol_targeted_budget_pct",
]
