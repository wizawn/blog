"""
交易模块
支持三种交易模式：模拟盘、测试网、实盘
"""

from .paper_trading_engine import PaperTradingEngine, get_paper_trading_engine
from .trading_mode_manager import (
    TradingMode,
    TradingModeManager,
    get_trading_mode_manager,
    get_current_trading_mode,
    is_paper_trading,
    is_testnet,
    is_live_trading
)

__all__ = [
    'PaperTradingEngine',
    'get_paper_trading_engine',
    'TradingMode',
    'TradingModeManager',
    'get_trading_mode_manager',
    'get_current_trading_mode',
    'is_paper_trading',
    'is_testnet',
    'is_live_trading'
]
