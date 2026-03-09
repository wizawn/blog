
# =============================================================================
# Copyright (C) 2026 言零 (GOV-HACK)
# All Rights Reserved.
#
# 官方网站：https://www.caowo.de | https://www.wizawn.com
# 技术博客：https://blog.caowo.de | https://blog.wizawn.com
# 软著材料代生成平台：https://ruanzhu.caowo.de | https://ruanzhu.wizawn.com
#
# 开发者：言零
# 微信号：GOV-HACK
# QQ：46333839
#
# 本软件受著作权法保护，未经授权禁止复制、修改、分发或用于商业用途。
# 违反者将承担法律责任。
# =============================================================================

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
