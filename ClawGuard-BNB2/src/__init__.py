
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
ClawGuard-BNB 核心模块
"""

__version__ = "2.0.0"
__author__ = "ClawSec"

from .api.binance_client import BinanceClient, BinanceAPIError
from .config.config_manager import ConfigManager
from .security.input_validator import InputValidator, ValidationError, validate_trade_params
from .security.api_auditor import APISecurityAuditor, RiskLevel
from .risk.risk_control import RiskControlEngine

__all__ = [
    'BinanceClient',
    'BinanceAPIError',
    'ConfigManager',
    'InputValidator',
    'ValidationError',
    'validate_trade_params',
    'APISecurityAuditor',
    'RiskLevel',
    'RiskControlEngine',
]
