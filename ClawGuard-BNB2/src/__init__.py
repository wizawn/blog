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
